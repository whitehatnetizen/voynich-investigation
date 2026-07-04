"""Word-level (syntactic) structure: the missing half.

Everything so far is WITHIN words. This measures structure BETWEEN words: does knowing a word
predict the next one, as syntax + collocation do in real language? A table-driven / generated
text has near-independent words.

Metric: word-order information = how much the previous word reduces uncertainty about the next.
  H_w          unigram word entropy (bits)
  H_cond       H(word | previous word), empirical
  H_cond_shuf  same on a SHUFFLED copy of the same tokens (syntax destroyed, vocabulary +
               token counts identical) -> the finite-sample bias floor
  order_info   = H_cond_shuf - H_cond   (bits)   <- bias-cancelled genuine word-order structure
  order_frac   = order_info / H_w                (share of word-uncertainty explained by order)

The shuffle control is essential: H(word|prev) is badly biased low with big vocabularies at
30k tokens, and each language has a different vocabulary size. Shuffling preserves the exact
token multiset and prev-word marginals, so the bias is nearly identical in real vs shuffled and
cancels on subtraction. What's left is real structure.

Also reports adjacent_repeat_rate (share of tokens identical to the one before — the Voynich's
known local repetition) and the top word-bigrams (collocations vs mere frequent co-occurrence).

Writes results/word_syntax.json + figures/word_syntax.png.
"""
import json
import random
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import seriesio as S
from glyphkit import H, cond_H

RES = S.ROOT / "results"
FIG = S.ROOT / "figures"
SEED = 1492
NSHUF = 200           # review FIX-1: real null distribution; cheap statistic, so 200 reps

SERIES = [("voynich_eva", "Voynich", "red"), ("english", "English", "#1f77b4"),
          ("latin", "Latin", "#17becf"), ("german", "German", "#8c564b"),
          ("spanish", "Spanish", "#ff7f0e"), ("italian", "Italian", "#9467bd"),
          ("french", "French", "#2ca02c"), ("latin_tech", "Latin (tech)", "#b5651d"),
          ("hebrew", "Hebrew", "#2f4f4f"), ("monkey", "monkey null", "grey")]


def analyse(tokens, rng, nshuf=NSHUF):
    """rng is retained for signature compatibility; shuffle reps use per-rep seeds SEED+i (FIX-1)."""
    H_w = H(Counter(tokens))
    H_cond = cond_H(zip(tokens, tokens[1:]))
    shuf = []
    for rep in range(nshuf):
        arr = list(tokens)
        random.Random(SEED + rep).shuffle(arr)
        shuf.append(cond_H(zip(arr, arr[1:])))
    H_shuf = float(np.mean(shuf))
    H_shuf_sd = float(np.std(shuf, ddof=1)) if nshuf > 1 else 0.0
    order_info = H_shuf - H_cond
    rep_rate = sum(1 for a, b in zip(tokens, tokens[1:]) if a == b) / (len(tokens) - 1)
    top_bg = Counter(zip(tokens, tokens[1:])).most_common(8)
    return {
        "H_word": round(H_w, 3),
        "H_cond": round(H_cond, 3),
        "H_cond_shuffled": round(H_shuf, 3),
        "H_cond_shuffled_sd": round(H_shuf_sd, 5),
        "n_reps": nshuf,
        "order_info_bits": round(order_info, 3),
        "order_info_z": round(order_info / H_shuf_sd, 1) if H_shuf_sd else None,
        "order_frac": round(order_info / H_w, 4) if H_w else 0.0,
        "adjacent_repeat_rate": round(rep_rate, 4),
        "top_bigrams": [[f"{a} {b}", n] for (a, b), n in top_bg],
        "n_types": len(set(tokens)),
    }


def main():
    RES.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)
    rng = random.Random(SEED)
    out = {}
    for name, label, _ in SERIES:
        out[label] = {"series": name, **analyse(S.load_tokens(name), rng)}
    (RES / "word_syntax.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    # ---- figure: genuine word-order info (bits) + as fraction of word entropy ----
    labels = [lab for _, lab, _ in SERIES]
    colors = [c for _, _, c in SERIES]
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(13, 5.2))
    axA.bar(labels, [out[l]["order_info_bits"] for l in labels], color=colors)
    axA.set_ylabel("bits"); axA.set_title("Genuine word-order information (bias-cancelled)\nhow much the previous word predicts the next")
    axA.tick_params(axis="x", rotation=45, labelsize=8)
    axA.grid(True, axis="y", ls=":", alpha=0.3)
    axB.bar(labels, [out[l]["order_frac"] * 100 for l in labels], color=colors)
    axB.set_ylabel("% of word-entropy explained by previous word")
    axB.set_title("Word-order info as a share of word entropy")
    axB.tick_params(axis="x", rotation=45, labelsize=8)
    axB.grid(True, axis="y", ls=":", alpha=0.3)
    for ax in (axA, axB):
        for i, l in enumerate(labels):
            if l == "Voynich":
                ax.get_xticklabels()[i].set_fontweight("bold")
    fig.tight_layout(); fig.savefig(FIG / "word_syntax.png", dpi=140); plt.close(fig)

    # ---- console ----
    print(f"  {'series':13s} {'H_word':>7s} {'H_cond':>7s} {'H_shuf':>7s} {'orderInfo':>9s} "
          f"{'order%':>7s} {'repeat%':>8s} {'types':>6s}")
    for l in labels:
        d = out[l]
        print(f"  {l:13s} {d['H_word']:7.2f} {d['H_cond']:7.2f} {d['H_cond_shuffled']:7.2f} "
              f"{d['order_info_bits']:9.3f} {d['order_frac']*100:6.1f}% {d['adjacent_repeat_rate']*100:7.2f}% "
              f"{d['n_types']:6d}")
    print("\n  top word-bigrams (Hebrew in JSON only — console can't render it):")
    for l in ["Voynich", "English", "Latin"]:
        pairs = "  ".join(f"{bg}({n})" for bg, n in out[l]["top_bigrams"][:6])
        print(f"    {l:9s} {pairs}")
    print(f"\n  wrote {RES/'word_syntax.json'}, figures/word_syntax.png")


if __name__ == "__main__":
    main()
