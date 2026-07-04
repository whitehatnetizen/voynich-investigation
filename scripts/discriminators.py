"""Phase 2d — the tests that actually SEPARATE the Voynich (where Zipf cannot).

Heaps' law   : distinct types V(n) vs tokens n; fit exponent beta. Vocabulary growth.
word length  : distribution of token lengths; mean + std. Voynich's is famously narrow /
               near-binomial (too regular for a natural language).
entropy      : h1 = char unigram entropy (bits); h2 = conditional entropy H(c_i|c_{i-1}).
               The Voynich's h2 is the known anomaly — much lower than European languages.
               (Glyph-level for Voynich vs letter-level for languages — an asymmetry we
               flag, not hide.)

Writes results/discriminators.json + figures/heaps.png, figures/wordlen.png.
"""
import json
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import seriesio as S

RES = S.ROOT / "results"
FIG = S.ROOT / "figures"
SERIES = S.LANGUAGES + ["latin_tech", "latin_nomen", "hebrew", "voynich_eva"]
COLORS = {"english": "#1f77b4", "french": "#2ca02c", "spanish": "#ff7f0e",
          "italian": "#9467bd", "german": "#8c564b", "latin": "#17becf",
          "latin_tech": "#b5651d", "latin_nomen": "#8b0a50", "hebrew": "#2f4f4f",
          "voynich_eva": "red"}


def heaps_curve(tokens, step=250):
    seen, V, xs, ys = set(), 0, [], []
    for i, t in enumerate(tokens, 1):
        if t not in seen:
            seen.add(t); V += 1
        if i % step == 0:
            xs.append(i); ys.append(V)
    return np.array(xs, float), np.array(ys, float)


def heaps_beta(xs, ys):
    lx, ly = np.log10(xs), np.log10(ys)
    A = np.vstack([lx, np.ones_like(lx)]).T
    (slope, _), *_ = np.linalg.lstsq(A, ly, rcond=None)
    return float(slope)


def char_entropy(tokens):
    chars = "".join(tokens)
    n = len(chars)
    uni = Counter(chars)
    h1 = -sum((c / n) * np.log2(c / n) for c in uni.values())
    bi = Counter(zip(chars, chars[1:]))
    nb = sum(bi.values())
    h_bi = -sum((c / nb) * np.log2(c / nb) for c in bi.values())
    h2 = h_bi - h1  # conditional entropy H(c_i | c_{i-1})
    return float(h1), float(h2), len(uni)


def main():
    RES.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)
    out = {}

    fig_h, ax_h = plt.subplots(figsize=(8, 6))
    fig_w, ax_w = plt.subplots(figsize=(8, 6))

    for name in SERIES:
        toks = S.load_tokens(name)
        xs, ys = heaps_curve(toks)
        beta = heaps_beta(xs, ys)
        lengths = np.array([len(t) for t in toks])
        h1, h2, alpha_size = char_entropy(toks)
        out[name] = {
            "heaps_beta": round(beta, 4),
            "vocab_at_30k": int(ys[-1]),
            "wordlen_mean": round(float(lengths.mean()), 3),
            "wordlen_std": round(float(lengths.std()), 3),
            "h1_char_bits": round(h1, 4),
            "h2_cond_bits": round(h2, 4),
            "alphabet_size": alpha_size,
        }
        lw = 2.6 if name == "voynich_eva" else 1.5
        ax_h.loglog(xs, ys, color=COLORS[name], lw=lw, label=f"{name} (β={beta:.2f})")
        maxlen = 16
        hist = np.bincount(np.clip(lengths, 0, maxlen), minlength=maxlen + 1)[:maxlen + 1]
        ax_w.plot(range(maxlen + 1), hist / hist.sum(), color=COLORS[name], lw=lw,
                  marker="o", ms=3, label=name)

    ax_h.set_xlabel("tokens n (log)"); ax_h.set_ylabel("distinct types V(n) (log)")
    ax_h.set_title("Heaps' Law — vocabulary growth")
    ax_h.grid(True, which="both", ls=":", alpha=0.3); ax_h.legend(fontsize=8)
    fig_h.tight_layout(); fig_h.savefig(FIG / "heaps.png", dpi=140); plt.close(fig_h)

    ax_w.set_xlabel("word length (chars)"); ax_w.set_ylabel("proportion of tokens")
    ax_w.set_title("Word-length distribution (Voynich is unusually narrow/regular)")
    ax_w.grid(True, ls=":", alpha=0.3); ax_w.legend(fontsize=8)
    fig_w.tight_layout(); fig_w.savefig(FIG / "wordlen.png", dpi=140); plt.close(fig_w)

    (RES / "discriminators.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"  {'series':14s} {'beta':>6s} {'wlen_mean':>9s} {'wlen_std':>8s} {'h1':>6s} {'h2':>6s} {'alpha':>5s}")
    for name in SERIES:
        d = out[name]
        print(f"  {name:14s} {d['heaps_beta']:6.3f} {d['wordlen_mean']:9.2f} "
              f"{d['wordlen_std']:8.2f} {d['h1_char_bits']:6.2f} {d['h2_cond_bits']:6.2f} "
              f"{d['alphabet_size']:5d}")
    print(f"  wrote {RES/'discriminators.json'}, figures/heaps.png, figures/wordlen.png")


if __name__ == "__main__":
    main()
