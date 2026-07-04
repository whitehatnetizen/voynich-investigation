"""Currier A/B split — are our aggregate numbers averaging two systems? (2026-07-01)

Prescott Currier (1970s) showed the Voynich is written in (at least) two statistical "languages",
A and B, tied to different scribal hands and sections. Every aggregate we have reported (h2, word
length, affix coverage, self-citation) pools A and B. This splits the structured parse
(`data/voynich/eva_structured.jsonl`, which carries `currier_lang` + hand + section per token) and
re-runs the key discriminators PER SUBSET, so we can ask:

  1. Are A and B genuinely two systems? (h2, word length, affixes)
  2. Is the low-h2 / narrow-word-length anomaly in BOTH, or driven by one?
  3. Is the self-citation (local copy-and-mutate) signal uniform, or is one system more mechanical?

Method. A-stream = all Currier-A tokens in manuscript order (11,607). B-stream = first N of the
Currier-B tokens in order, N = len(A), so entropy/affix numbers are size-matched (h2 and type
counts are sample-size sensitive). The '?' (unlabelled, 3,316) tokens are dropped. Everything is
computed identically to the pooled analyses: char entropy the discriminators.py way (concatenate,
cross-boundary bigrams, eva1 glyphs; evaG reported as a robustness check), affixes the
slot_grammar.py way, self-citation the self_citation.py way (shuffle-controlled).

HONEST CONFOUND. A is almost entirely Herbal + Pharmaceutical (one scribe, Hand 1); B is the
Stars / Biological / Cosmological pages (Hands 2/3/5). So "A vs B" is simultaneously a hand
contrast AND a section contrast — this test cannot separate the two. Disentangling scribe from
subject is a follow-up (section-conditioned split within one Currier language).

Writes results/currier_split.json + figures/currier_split.png.
"""
import json
import random
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from rapidfuzz.distance import DamerauLevenshtein as DL

import seriesio as S
from glyphkit import glyphs, H, cond_H
from slot_grammar import affixes

STRUCT = S.ROOT / "data" / "voynich" / "eva_structured.jsonl"
RES = S.ROOT / "results"
FIG = S.ROOT / "figures"
SEED = 1492

# self-citation core params (mirror self_citation.py)
SC_START = 50
SC_WINDOWS = [5, 25]
SC_REF = 25
SC_NSHUF = 30         # review FIX-1: real null distribution, per-rep seeds SEED+i
NEAR = (1, 5)
FAR = (20, 25)


# ---------- character entropy (discriminators.py method: cross-boundary bigrams) ----------
def char_entropy(tokens, grouped=False):
    seq = []
    for t in tokens:
        seq.extend(glyphs(t, grouped))
    uni = Counter(seq)
    bi = Counter(zip(seq, seq[1:]))
    h1 = H(uni)
    h2 = H(bi) - h1                 # conditional entropy H(c_i | c_{i-1})
    return round(h1, 3), round(h2, 3), len(uni)


# ---------- self-citation core (shuffle-controlled) ----------
def _nearest(tokens, W):
    """mean nearest DL distance to previous W tokens + distance-0/1 fractions, from SC_START on."""
    n = len(tokens)
    raw = 0.0
    d0 = d1 = cnt = 0
    for i in range(SC_START, n):
        ti = tokens[i]
        best = 10 ** 9
        for j in range(i - W, i):
            d = DL.distance(ti, tokens[j])
            if d < best:
                best = d
                if best == 0:
                    break
        raw += best
        if best == 0:
            d0 += 1
        elif best == 1:
            d1 += 1
        cnt += 1
    return raw / cnt, d0 / cnt, d1 / cnt


def _lag_gradient(tokens):
    """mean DL distance at each lag; return near-block and far-block means."""
    def block(lo, hi):
        tot = 0.0
        cntk = 0
        for k in range(lo, hi + 1):
            s = 0.0
            for i in range(k, len(tokens)):
                s += DL.distance(tokens[i], tokens[i - k])
            tot += s / (len(tokens) - k)
            cntk += 1
        return tot / cntk
    return block(*NEAR), block(*FAR)


def self_citation(tokens, rng, nshuf=SC_NSHUF):
    """rng retained for signature compatibility; shuffle reps use per-rep seeds SEED+i (FIX-1)."""
    out = {}
    real = {W: _nearest(tokens, W) for W in SC_WINDOWS}
    shuf = {W: [] for W in SC_WINDOWS}
    d0s = {W: [] for W in SC_WINDOWS}
    d1s = {W: [] for W in SC_WINDOWS}
    grads = []
    for rep in range(nshuf):
        sh = list(tokens)
        random.Random(SEED + rep).shuffle(sh)
        for W in SC_WINDOWS:
            r, a0, a1 = _nearest(sh, W)
            shuf[W].append(r)
            d0s[W].append(a0)
            d1s[W].append(a1)
        ns, fs = _lag_gradient(sh)
        grads.append(fs - ns)
    for W in SC_WINDOWS:
        rr, r0, r1 = real[W]
        sr = float(np.mean(shuf[W]))
        sd = float(np.std(shuf[W], ddof=1)) if nshuf > 1 else 0.0
        out[f"excess_raw_W{W}"] = round(sr - rr, 4)
        out[f"excess_raw_W{W}_z"] = round((sr - rr) / sd, 1) if sd else None
        if W == SC_REF:
            out["excess_d0"] = round(r0 - float(np.mean(d0s[W])), 4)
            out["excess_d1"] = round(r1 - float(np.mean(d1s[W])), 4)
            d0sd = float(np.std(d0s[W], ddof=1)) if nshuf > 1 else 0.0
            d1sd = float(np.std(d1s[W], ddof=1)) if nshuf > 1 else 0.0
            out["excess_d0_z"] = round(out["excess_d0"] / d0sd, 1) if d0sd else None
            out["excess_d1_z"] = round(out["excess_d1"] / d1sd, 1) if d1sd else None
    near_r, far_r = _lag_gradient(tokens)
    out["gradient_real"] = round(far_r - near_r, 4)
    out["gradient_shuf"] = round(float(np.mean(grads)), 4)
    gsd = float(np.std(grads, ddof=1)) if nshuf > 1 else 0.0
    out["gradient_excess_z"] = round((out["gradient_real"] - out["gradient_shuf"]) / gsd, 1) if gsd else None
    out["n_reps"] = nshuf
    return out


# ---------- per-subset bundle ----------
# Order-independent stats (h2/word length/affixes) run on a size-matched RANDOM sample so the
# subset is representative across sections and comparable at equal token count. Self-citation
# needs reading order, so it runs on the FULL ordered stream (it is a per-token rate, essentially
# size-independent at a fixed window, so it does not need the size match).
def count_stats(sample):
    seqs = [glyphs(t) for t in sample]
    af = affixes(seqs)
    lengths = np.array([len(t) for t in sample])
    h1, h2, ntypes = char_entropy(sample)
    _, h2g, _ = char_entropy(sample, grouped=True)
    return {
        "n_sample": len(sample),
        "h1": h1, "h2": h2, "h2_evaG": h2g, "n_glyph_types": ntypes,
        "wordlen_mean": round(float(lengths.mean()), 3),
        "wordlen_std": round(float(lengths.std()), 3),
        "n_word_types": len(set(sample)),
        "prefix2_cov": af["prefix2"]["top10_coverage"],
        "suffix2_cov": af["suffix2"]["top10_coverage"],
        "top_prefix2": af["prefix2"]["top"][:6],
        "top_suffix2": af["suffix2"]["top"][:6],
    }


def analyse_subset(full_ordered, sample, rng):
    return {"n_full": len(full_ordered),
            **count_stats(sample),
            "self_citation": self_citation(full_ordered, rng)}


def main():
    RES.mkdir(exist_ok=True)
    FIG.mkdir(exist_ok=True)
    rows = [json.loads(l) for l in STRUCT.read_text(encoding="utf-8").splitlines() if l.strip()]

    A = [r["token"] for r in rows if r.get("currier_lang") == "A"]
    B_all = [r["token"] for r in rows if r.get("currier_lang") == "B"]
    pooled = [r["token"] for r in rows]  # everything, in reading order (A+B+?)
    N = len(A)

    rng = random.Random(SEED)
    # size-matched representative random samples for the order-independent stats
    A_sample = rng.sample(A, N)            # = permutation of A (order-independent stats only)
    B_sample = rng.sample(B_all, N)        # representative random N across ALL B sections
    pooled_sample = rng.sample(pooled, N)

    # section mix of each Currier stream, for transparency about the hand/section confound
    def sec_mix(pred):
        return dict(Counter(r["section"] for r in rows if pred(r)).most_common())

    out = {
        "_meta": {
            "N_size_matched": N, "A_total": len(A), "B_total": len(B_all),
            "unlabelled_dropped": sum(1 for r in rows if r.get("currier_lang") not in ("A", "B")),
            "seed": SEED,
            "method": "order-independent stats (h2/word length/affixes) on a size-matched random sample of N; self-citation on the FULL ordered stream; h2 discriminators-style (eva1, cross-boundary bigrams); self-citation shuffle-controlled",
            "confound": "A=Herbal/Pharma (Hand 1); B=Stars/Biological/Cosmological (Hands 2/3/5). A-vs-B is a hand AND section contrast at once.",
        },
        "section_mix": {"A": sec_mix(lambda r: r.get("currier_lang") == "A"),
                        "B": sec_mix(lambda r: r.get("currier_lang") == "B")},
        "A": analyse_subset(A, A_sample, rng),
        "B": analyse_subset(B_all, B_sample, rng),
        "pooled_voynich": analyse_subset(pooled, pooled_sample, rng),
    }

    # language band for context (from the existing discriminators run)
    try:
        disc = json.loads((RES / "discriminators.json").read_text(encoding="utf-8"))
        out["language_band"] = {k: {"h2": disc[k]["h2_cond_bits"], "wordlen_std": disc[k]["wordlen_std"]}
                                for k in ("english", "latin", "german") if k in disc}
    except FileNotFoundError:
        out["language_band"] = {}

    (RES / "currier_split.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    # ---- console ----
    print(f"  size-matched N = {N} (order-indep stats)  (A total {len(A)}, B total {len(B_all)}; self-citation on full streams)")
    print(f"  {'subset':16s} {'h2':>5s} {'h2G':>5s} {'wlenMean':>8s} {'wlenStd':>7s} "
          f"{'wTypes':>6s} {'pre2cov':>7s} {'suf2cov':>7s}")
    for k in ("A", "B", "pooled_voynich"):
        d = out[k]
        print(f"  {k:16s} {d['h2']:5.2f} {d['h2_evaG']:5.2f} {d['wordlen_mean']:8.2f} "
              f"{d['wordlen_std']:7.2f} {d['n_word_types']:6d} {d['prefix2_cov']:7.2f} {d['suffix2_cov']:7.2f}")
    print(f"\n  {'subset':16s} {'exW5':>6s} {'exW25':>6s} {'exD0':>6s} {'exD1':>6s} {'grad':>6s} {'gradShuf':>8s}")
    for k in ("A", "B", "pooled_voynich"):
        s = out[k]["self_citation"]
        print(f"  {k:16s} {s['excess_raw_W5']:+6.3f} {s['excess_raw_W25']:+6.3f} "
              f"{s['excess_d0']:+6.3f} {s['excess_d1']:+6.3f} {s['gradient_real']:+6.3f} {s['gradient_shuf']:+8.3f}")
    print("\n  top 2-glyph suffixes:")
    for k in ("A", "B"):
        print(f"    {k}: " + " ".join(f"{g}:{n}" for g, n in out[k]["top_suffix2"]))
    print("  top 2-glyph prefixes:")
    for k in ("A", "B"):
        print(f"    {k}: " + " ".join(f"{g}:{n}" for g, n in out[k]["top_prefix2"]))
    print("\n  section mix A :", out["section_mix"]["A"])
    print("  section mix B :", out["section_mix"]["B"])

    # ---- figure: A vs B vs pooled on the key discriminators + self-citation ----
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    keys = ["A", "B", "pooled_voynich"]
    labels = ["Currier A", "Currier B", "pooled"]
    cols = ["#c44e52", "#4c72b0", "#8c8c8c"]

    # panel 1: h2 with language band
    ax = axes[0]
    ax.bar(labels, [out[k]["h2"] for k in keys], color=cols)
    band = out.get("language_band", {})
    if band:
        lo = min(v["h2"] for v in band.values())
        hi = max(v["h2"] for v in band.values())
        ax.axhspan(lo, hi, color="green", alpha=0.12, label=f"language h2 band ({lo:.2f}-{hi:.2f})")
        ax.legend(fontsize=8)
    ax.set_ylabel("h2 conditional glyph entropy (bits)")
    ax.set_title("(1) Is the low-h2 anomaly in BOTH A and B?")
    ax.grid(True, axis="y", ls=":", alpha=0.3)

    # panel 2: word-length std + affix coverage
    ax = axes[1]
    x = np.arange(len(keys)); w = 0.38
    ax.bar(x - w/2, [out[k]["wordlen_std"] for k in keys], w, label="word-length std", color="#55a868")
    ax.bar(x + w/2, [out[k]["suffix2_cov"] for k in keys], w, label="top-10 2-suffix coverage", color="#dd8452")
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_title("(2) Word-length regularity & affix kit")
    ax.grid(True, axis="y", ls=":", alpha=0.3); ax.legend(fontsize=8)

    # panel 3: self-citation signatures
    ax = axes[2]
    metrics = [("excess_raw_W5", "excess W5"), ("excess_d1", "dist-1 excess"), ("gradient_real", "locality grad")]
    x = np.arange(len(metrics)); w = 0.25
    for i, k in enumerate(keys):
        s = out[k]["self_citation"]
        ax.bar(x + (i - 1) * w, [s[m] for m, _ in metrics], w, label=labels[i], color=cols[i])
    ax.set_xticks(x); ax.set_xticklabels([lbl for _, lbl in metrics], fontsize=9)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_title("(3) Is the copy-and-mutate signal in both?")
    ax.grid(True, axis="y", ls=":", alpha=0.3); ax.legend(fontsize=8)

    fig.suptitle("Currier A vs B — do the anomalies survive the split?", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(FIG / "currier_split.png", dpi=140)
    plt.close(fig)
    print(f"\n  wrote {RES/'currier_split.json'}, figures/currier_split.png")


if __name__ == "__main__":
    main()
