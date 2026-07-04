"""Test harness for scribe-recipe.md — does the BY-HAND recipe reproduce the Voynich fingerprint?

This faithfully simulates a person following the paper recipe in `scribe-recipe.md`: build words
from a small table of syllable-chunks (a start column, a middle column, an end column), keep words
short (2-3 chunks), and MOSTLY copy a nearby recent word and swap its ending. Everything here is
something a scribe could do with three lists and a die — no computer maths, no language.

The chunk menus + length mix are learned from the Voynich once (so the paper tables are grounded),
then generation uses only weighted picks + copy-and-swap. We score the output on the fingerprint
discriminators and compare to the real Voynich to show the recipe is plausible.

Run: python scripts/scribe_recipe_test.py   ->   prints a stats table + a text sample; writes
data samples to results/scribe_recipe_sample.json.
"""
import json
import random
from collections import Counter

import seriesio as S
import generate_model as GM
from currier_split import self_citation
from word_syntax import analyse as word_analyse

RES = S.ROOT / "results"
SEED = 1492
N = 30000

# The paper syllable table (longest-first). Any leftover letter is its own tiny chunk.
CHUNKS = sorted(set([
    "aiin", "aiir", "aiil", "chee", "cheo", "chey", "chor", "chol", "qok", "qot", "qol",
    "cth", "ckh", "cph", "cfh", "aii", "ain", "air", "edy", "eey", "chy", "she", "sho", "shy",
    "dai", "qo", "ol", "or", "al", "ar", "am", "an", "in", "ir", "od", "ok", "ot", "ee", "eo",
    "ch", "sh", "da", "ke", "te", "dy", "ai", "ay", "ey",
]), key=len, reverse=True)

# generation parameters (the recipe's dials)
P_COPY = 0.78        # about four words in five are copied-and-tweaked
W = 20               # look back this many words for something to copy (wide -> gentle locality)
SWAP_END = 0.50      # of tweaks: change the ending chunk
SWAP_START = 0.08    #            change the starting chunk
UNCHANGED = 0.30     #            copy verbatim (repetition -> Zipf, fewer new types)
SWAP_MID = 0.12      #            change a middle chunk
OVERLAP = 0.68       # section flavour: 0.68 of words from the shared kit, 0.32 from a section pool
SECTION_SIZES = [10889, 6386, 3477, 2141, 1167]


def chunk(w):
    out, i = [], 0
    while i < len(w):
        for m in CHUNKS:
            if w.startswith(m, i):
                out.append(m); i += len(m); break
        else:
            out.append(w[i]); i += 1
    return out


def weighted(counter):
    keys = list(counter); wts = [counter[k] for k in keys]
    return keys, wts


def fit_tables(tokens):
    segs = [chunk(w) for w in tokens]
    start = Counter(s[0] for s in segs if s)
    end = Counter(s[-1] for s in segs if len(s) >= 2)
    mid = Counter(c for s in segs for c in s[1:-1])
    nch = Counter(len(s) for s in segs if s)
    return {"start": weighted(start), "mid": weighted(mid), "end": weighted(end),
            "nchunks": weighted(nch)}


def build_word(t, rng, restrict=None):
    """Fresh word: pick a chunk-count, then a start / middles / end from the columns."""
    nk = rng.choices(*t["nchunks"])[0]
    if nk <= 1:
        return rng.choices(*t["start"])[0]
    sK, sW = t["start"]; mK, mW = t["mid"]; eK, eW = t["end"]
    if restrict:                                   # section flavour: bias to a favoured subset
        def bias(keys, wts):
            return keys, [w * (4.0 if k in restrict else 1.0) for k, w in zip(keys, wts)]
        sK, sW = bias(sK, sW); eK, eW = bias(eK, eW)
    w = rng.choices(sK, sW)[0]
    for _ in range(nk - 2):
        w += rng.choices(mK, mW)[0]
    w += rng.choices(eK, eW)[0]
    return w


def tweak(word, t, rng):
    """Copy-and-change: swap the ending chunk (usually), or the start, or a middle, or leave it."""
    c = chunk(word)
    if len(c) < 2:
        return build_word(t, rng)
    r = rng.random()
    if r < UNCHANGED:
        return word
    if r < UNCHANGED + SWAP_END:
        c[-1] = rng.choices(*t["end"])[0]
    elif r < UNCHANGED + SWAP_END + SWAP_START:
        c[0] = rng.choices(*t["start"])[0]
    else:
        c[rng.randrange(len(c))] = rng.choices(*t["mid"])[0]
    return "".join(c)


def scribe(t, rng, n, sizes=None):
    """Follow the recipe. If sizes given, write section by section with a per-section favoured kit."""
    if sizes is None:
        sizes = [n]
        section_pool = [None]
    else:
        # each section gets a favourite handful of end + start chunks (its 'house set')
        endK = t["end"][0]; startK = t["start"][0]
        section_pool = []
        for s in range(len(sizes)):
            fav = set(rng.sample(endK[:14], 4) + rng.sample(startK[:12], 3))
            section_pool.append(fav)
    out, secs = [], []
    for s, m in enumerate(sizes):
        fav = section_pool[s]
        buf = []
        for _ in range(m):
            if len(buf) >= 2 and rng.random() < P_COPY:
                j = rng.randrange(max(0, len(buf) - W), len(buf) - 1) if len(buf) > 1 else 0
                w = tweak(buf[j], t, rng)
            else:
                restrict = None if (fav is None or rng.random() < OVERLAP) else fav
                w = build_word(t, rng, restrict)
            buf.append(w); out.append(w); secs.append(f"S{s}")
    return out, secs


def stats(tokens):
    ev = GM.evaluate(tokens)
    sc = self_citation(tokens, random.Random(SEED))
    wa = word_analyse(tokens, random.Random(SEED))
    return {"h2_cross": ev["h2_cross_bits"], "wordlen_mean": ev["wordlen_mean"],
            "wordlen_std": ev["wordlen_std"], "zipf_slope": ev["zipf_slope"],
            "n_types": ev["n_types"], "sc_d1": sc["excess_d1"], "sc_grad": sc["gradient_real"],
            "order_frac": wa["order_frac"], "adj_repeat": wa["adjacent_repeat_rate"]}


def main():
    rng = random.Random(SEED)
    voy = S.load_tokens("voynich_eva")
    t = fit_tables(voy)
    gen, secs = scribe(t, rng, N, SECTION_SIZES)

    sv, sg = stats(voy), stats(gen)
    keys = ["h2_cross", "wordlen_mean", "wordlen_std", "zipf_slope", "n_types",
            "sc_d1", "sc_grad", "order_frac", "adj_repeat"]
    print("  paper syllable table:")
    for col in ("start", "mid", "end"):
        top = sorted(zip(*t[col]), key=lambda x: -x[1])[:12]
        print(f"    {col:5s}: " + " ".join(k for k, _ in top))
    print(f"\n  {'metric':13s} {'Voynich':>10s} {'scribe':>10s}")
    for k in keys:
        print(f"  {k:13s} {sv[k]:>10} {sg[k]:>10}")
    print("\n  sample of hand-produced 'Voynichese' (first 40 words):")
    print("   " + " ".join(gen[:40]))
    RES.mkdir(exist_ok=True)
    (RES / "scribe_recipe_sample.json").write_text(json.dumps(
        {"params": {"P_COPY": P_COPY, "W": W, "OVERLAP": OVERLAP}, "voynich_stats": sv,
         "scribe_stats": sg, "sample_words": gen[:120]}, indent=2), encoding="utf-8")
    print(f"\n  wrote {RES/'scribe_recipe_sample.json'}")


if __name__ == "__main__":
    main()
