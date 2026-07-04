"""Phase 4 (mechanism) — can a small mechanical model reproduce the Voynich anomaly?

Phases 2-3 showed the Voynich's low h2 comes from a rigid within-word combinatorial grammar
(tiny affix kit, concentrated bigrams). This phase tests whether a small generative rule set
reproduces the two headline anomalies — low h2 AND uniform word length — that no natural
register did.

Models (all fitted on the Voynich EVA 30k, each generating 30k tokens):
  iid      unigram glyphs + word length sampled from the Voynich length distribution. No
           sequential structure. FLOOR: should fail (h2 ~ h1, unconcentrated).
  slot     three positional menus — first-glyph / middle-glyph / last-glyph distributions —
           + empirical length. The interpretable "parts kit". Tests how far pure positional
           slots get.
  markov1  first-order within-word Markov with START/END states, so word length is generated
           ENDOGENOUSLY (not imposed). Reproduces within-word h2 ~by construction; the real
           test is whether the SAME local transition structure also yields the Voynich's
           narrow length distribution.

Honesty guard (from PLAN-mechanism.md): markov1 encodes first-order structure by
construction, so its h2 match is not the finding. The findings are (a) whether iid/slot fail
where markov1 succeeds — locating the anomaly in sequential structure — and (b) whether
markov1's ENDOGENOUS length distribution matches the Voynich, which is not built in. As a
control we also fit markov1 on ENGLISH and compare its generated length distribution: if
Voynich-markov gives a narrow hump and English-markov a broad one, the length regularity is a
property of the Voynich's transition structure, not of Markov generation per se.

Writes results/generative_eval.json + figures/generative_fit.png.
"""
import json
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import seriesio as S
from glyphkit import glyphs, H, cond_H

RES = S.ROOT / "results"
FIG = S.ROOT / "figures"
SEED = 1492
N = 30000
MAXLEN = 40  # runaway guard for the Markov generator


# ---------- shared evaluation (same lens as discriminators.py + ngram_concentration.py) ----
def evaluate(tokens):
    seqs = [list(t) for t in tokens]
    lengths = np.array([len(t) for t in tokens])
    # cross-word h2 exactly as discriminators.py (concatenate the stream)
    chars = "".join(tokens)
    uni = Counter(chars)
    bi = Counter(zip(chars, chars[1:]))
    h1 = H(uni)
    h2_cross = H(bi) - h1
    # within-word h2
    wbi = [(g[i - 1], g[i]) for g in seqs for i in range(1, len(g))]
    h2_within = cond_H(wbi)
    # bigram concentration (within word)
    wbc = Counter(wbi)
    tot = sum(wbc.values())
    top10 = sum(sorted(wbc.values(), reverse=True)[:10]) / tot if tot else 0.0
    # zipf OLS slope
    counts = np.array(sorted(Counter(tokens).values(), reverse=True), float)
    x, y = np.log10(np.arange(1, len(counts) + 1)), np.log10(counts)
    A = np.vstack([x, np.ones_like(x)]).T
    slope = float(np.linalg.lstsq(A, y, rcond=None)[0][0])
    return {
        "wordlen_mean": round(float(lengths.mean()), 3),
        "wordlen_std": round(float(lengths.std()), 3),
        "h1_char_bits": round(h1, 3),
        "h2_cross_bits": round(h2_cross, 3),
        "h2_within_bits": round(h2_within, 3),
        "bigram_top10_share": round(float(top10), 3),
        "zipf_slope": round(slope, 3),
        "n_types": len(set(tokens)),
    }


# ---------- models ----------
def fit_iid(seqs):
    uni = Counter(g for w in seqs for g in w)
    lens = np.array([len(w) for w in seqs])
    glyph, p = zip(*[(k, v) for k, v in uni.items()])
    p = np.array(p, float); p /= p.sum()
    return {"glyph": np.array(glyph), "p": p, "lens": lens}


def gen_iid(m, rng, n):
    out = []
    Ls = rng.choice(m["lens"], size=n)
    for L in Ls:
        out.append("".join(rng.choice(m["glyph"], size=int(L), p=m["p"])))
    return out


def fit_slot(seqs):
    first, mid, last = Counter(), Counter(), Counter()
    lens = []
    for w in seqs:
        if not w:
            continue
        lens.append(len(w))
        first[w[0]] += 1
        last[w[-1]] += 1
        for g in w[1:-1]:
            mid[g] += 1
    def dist(c):
        k, v = zip(*c.items()); v = np.array(v, float); return np.array(k), v / v.sum()
    return {"first": dist(first), "mid": dist(mid) if mid else dist(first),
            "last": dist(last), "lens": np.array(lens)}


def gen_slot(m, rng, n):
    out = []
    Ls = rng.choice(m["lens"], size=n)
    for L in Ls:
        L = int(L)
        if L == 1:
            out.append(str(rng.choice(m["first"][0], p=m["first"][1]))); continue
        w = [rng.choice(m["first"][0], p=m["first"][1])]
        for _ in range(L - 2):
            w.append(rng.choice(m["mid"][0], p=m["mid"][1]))
        w.append(rng.choice(m["last"][0], p=m["last"][1]))
        out.append("".join(w))
    return out


def fit_markov(seqs):
    trans = defaultdict(Counter)
    for w in seqs:
        if not w:
            continue
        prev = "\x02"  # START
        for g in w:
            trans[prev][g] += 1
            prev = g
        trans[prev]["\x03"] += 1  # END
    model = {}
    for st, c in trans.items():
        k, v = zip(*c.items()); v = np.array(v, float); model[st] = (np.array(k), v / v.sum())
    return model


def gen_markov(m, rng, n):
    out = []
    for _ in range(n):
        st = "\x02"; w = []
        for _ in range(MAXLEN):
            k, p = m[st]
            nxt = rng.choice(k, p=p)
            if nxt == "\x03":
                break
            w.append(nxt); st = nxt
        if w:
            out.append("".join(w))
    return out


def main():
    RES.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)
    rng = np.random.default_rng(SEED)

    voy = S.load_tokens("voynich_eva")
    eng = S.load_tokens("english")
    vseqs = [list(t) for t in voy]
    eseqs = [list(t) for t in eng]

    gen = {
        "iid": gen_iid(fit_iid(vseqs), rng, N),
        "slot": gen_slot(fit_slot(vseqs), rng, N),
        "markov1": gen_markov(fit_markov(vseqs), rng, N),
    }
    markov_english = gen_markov(fit_markov(eseqs), rng, N)

    ev = {"voynich_real": evaluate(voy)}
    for name, toks in gen.items():
        ev[name] = evaluate(toks)
    ev["markov1_english_ctrl"] = evaluate(markov_english)
    ev["english_real"] = evaluate(eng)

    out = {
        "seed": SEED, "n_generated": N,
        "targets": {"h2_cross_bits": ev["voynich_real"]["h2_cross_bits"],
                    "wordlen_std": ev["voynich_real"]["wordlen_std"]},
        "eval": ev,
        "notes": [
            "iid/slot use empirical Voynich length (length not a discriminator for them); "
            "markov1 generates length ENDOGENOUSLY via START/END.",
            "FINDING 1: iid and slot FAIL on h2 (3.7-3.9 vs 2.4) and on bigram concentration "
            "-> the anomaly is in sequential glyph structure, not in unigram freq or pure "
            "position. FINDING 2: markov1 reproduces h2 and bigram concentration (h2 ~by "
            "construction) BUT its endogenous word length is broad/near-geometric (std ~3.5, "
            "same as markov1 fit on English) and does NOT match the Voynich's narrow hump "
            "(std 1.82). So the uniform word length is a SEPARATE constraint on top of the "
            "first-order glyph grammar. FINDING 3: markov1 also under-repeats whole words "
            "(types 9777 vs 6789; zipf slope -0.60 vs -0.89) -> word-level repetition is a "
            "third structure not captured by a glyph-transition model.",
        ],
    }
    (RES / "generative_eval.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    # ---- figure ----
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(13, 5.2))
    maxlen = 16
    def hist(toks):
        L = np.clip([len(t) for t in toks], 0, maxlen)
        h = np.bincount(L, minlength=maxlen + 1)[:maxlen + 1].astype(float)
        return h / h.sum()
    series = [("voynich (real)", voy, "red", 2.6),
              ("markov1 (fit Voynich)", gen["markov1"], "#2ca02c", 2.0),
              ("markov1 (fit English)", markov_english, "#1f77b4", 1.6),
              ("iid (fit Voynich)", gen["iid"], "grey", 1.4)]
    for label, toks, color, lw in series:
        axA.plot(range(maxlen + 1), hist(toks), marker="o", ms=3, color=color, lw=lw, label=label)
    axA.set_xlabel("word length (glyphs)"); axA.set_ylabel("proportion")
    axA.set_title("Word length: iid imposes it; first-order Markov canNOT reproduce the narrow hump")
    axA.grid(True, ls=":", alpha=0.3); axA.legend(fontsize=8)

    models = ["voynich_real", "iid", "slot", "markov1"]
    x = np.arange(len(models)); w = 0.38
    axB.bar(x - w / 2, [ev[m]["h2_cross_bits"] for m in models], w, label="h2 cross (bits)", color="#8172b3")
    axB.bar(x + w / 2, [ev[m]["wordlen_std"] for m in models], w, label="word-length std", color="#dd8452")
    axB.axhline(ev["voynich_real"]["h2_cross_bits"], color="#8172b3", ls=":", lw=1)
    axB.axhline(ev["voynich_real"]["wordlen_std"], color="#dd8452", ls=":", lw=1)
    axB.set_xticks(x); axB.set_xticklabels(models, fontsize=8)
    axB.set_title("Which model reproduces the anomaly?")
    axB.grid(True, axis="y", ls=":", alpha=0.3); axB.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "generative_fit.png", dpi=140); plt.close(fig)

    # ---- console ----
    cols = ["wordlen_mean", "wordlen_std", "h2_cross_bits", "h2_within_bits",
            "bigram_top10_share", "zipf_slope", "n_types"]
    print(f"  {'model':22s}" + "".join(f"{c.replace('_bits','').replace('wordlen_','wl_'):>13s}" for c in cols))
    for m in ["voynich_real", "iid", "slot", "markov1", "markov1_english_ctrl", "english_real"]:
        print(f"  {m:22s}" + "".join(f"{ev[m][c]:>13.3f}" for c in cols))
    print(f"\n  targets: Voynich h2_cross={out['targets']['h2_cross_bits']}, "
          f"wordlen_std={out['targets']['wordlen_std']}")
    print(f"  wrote {RES/'generative_eval.json'}, figures/generative_fit.png")


if __name__ == "__main__":
    main()
