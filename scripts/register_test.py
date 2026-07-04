"""Register hypothesis — does TECHNICAL Latin move toward the Voynich?

Hypothesis: word length and letter patterns shift with register. The
Voynich is largely a herbal, so the fair comparison may be specialised/technical Latin, not
generic prose. We now have two Latin registers cleaned identically:

  latin       generic narrative prose  — Caesar, De Bello Gallico
  latin_tech  technical botanical/herbal — Pliny, Naturalis Historia XII-XXVI

The controlled comparison is latin vs latin_tech (same language, same alphabet, same
cleaner) — so any shift is a REGISTER effect, not a language or pipeline effect. We then ask
whether that shift points toward the Voynich on the discriminators that actually separate it
(word-length regularity and h2 conditional character entropy).

For each discriminator d with generic=g, technical=t, Voynich=v we report the gap closed:
    gap = (t - g) / (v - g)      >0 toward Voynich, ~1 lands on it, >1 overshoots, <0 away.

Caveat carried through: h2 is glyph-level for the Voynich vs letter-level for Latin, so the
latin-vs-latin_tech h2 delta is the clean signal; the absolute distance to the Voynich's
2.43 bits inherits the segmentation asymmetry already flagged in discriminators.py.

Writes results/register.json + figures/register.png.
"""
import json
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import seriesio as S
from discriminators import heaps_curve, heaps_beta, char_entropy

RES = S.ROOT / "results"
FIG = S.ROOT / "figures"

# baseline first; each further register is measured for movement from the baseline toward
# the Voynich. latin=generic prose, latin_tech=technical prose, latin_nomen=Linnaean names.
BASELINE = "latin"
REGISTERS = ["latin", "latin_tech", "latin_nomen"]
VOY = "voynich_eva"
MAXLEN = 16

COLORS = {"latin": "#17becf", "latin_tech": "#b5651d", "latin_nomen": "#8b0a50", "voynich_eva": "red"}
LABELS = {"latin": "generic Latin (Caesar prose)",
          "latin_tech": "technical Latin (Pliny herbal prose)",
          "latin_nomen": "Linnaean nomenclature (binomials)",
          "voynich_eva": "Voynich (EVA)"}


def ols_slope(tokens):
    counts = np.array(sorted(Counter(tokens).values(), reverse=True), float)
    ranks = np.arange(1, len(counts) + 1, dtype=float)
    x, y = np.log10(ranks), np.log10(counts)
    A = np.vstack([x, np.ones_like(x)]).T
    (slope, _), *_ = np.linalg.lstsq(A, y, rcond=None)
    return float(slope)


def wordlen_hist(tokens):
    lengths = np.clip([len(t) for t in tokens], 0, MAXLEN)
    h = np.bincount(lengths, minlength=MAXLEN + 1)[:MAXLEN + 1].astype(float)
    return h / h.sum()


def profile(name):
    toks = S.load_tokens(name)
    lengths = np.array([len(t) for t in toks])
    h1, h2, alpha = char_entropy(toks)
    xs, ys = heaps_curve(toks)
    return {
        "wordlen_mean": round(float(lengths.mean()), 3),
        "wordlen_std": round(float(lengths.std()), 3),
        "h1_char_bits": round(h1, 4),
        "h2_cond_bits": round(h2, 4),
        "heaps_beta": round(heaps_beta(xs, ys), 4),
        "zipf_ols_slope": round(ols_slope(toks), 4),
        "types_at_30k": int(len(set(toks))),
        "_hist": wordlen_hist(toks),
    }


def hist_rmse(a, b):
    return float(np.sqrt(np.mean((a - b) ** 2)))


def main():
    RES.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)
    series = REGISTERS + [VOY]
    prof = {k: profile(k) for k in series}

    keys = ["wordlen_mean", "wordlen_std", "h1_char_bits", "h2_cond_bits",
            "heaps_beta", "zipf_ols_slope", "types_at_30k"]

    # movement of each non-baseline register from the baseline toward the Voynich
    movement = {}
    for reg in REGISTERS:
        if reg == BASELINE:
            continue
        movement[reg] = {}
        for k in keys:
            b, r, v = prof[BASELINE][k], prof[reg][k], prof[VOY][k]
            gap = (r - b) / (v - b) if v != b else None
            movement[reg][k] = {
                "baseline": b, "register": r, "voynich": v,
                "delta_from_baseline": round(r - b, 4),
                "toward_voynich": (v - b) * (r - b) > 0,
                "gap_closed_frac": round(gap, 3) if gap is not None else None,
            }

    # word-length distribution distance to the Voynich, per register
    wl_rmse = {reg: round(hist_rmse(prof[reg]["_hist"], prof[VOY]["_hist"]), 4)
               for reg in REGISTERS}

    out = {
        "baseline": BASELINE, "registers": REGISTERS, "reference": VOY,
        "profiles": {k: {kk: vv for kk, vv in prof[k].items() if kk != "_hist"}
                     for k in series},
        "movement_from_baseline_toward_voynich": movement,
        "wordlen_hist_rmse_to_voynich": wl_rmse,
        "caveats": [
            "The clean within-Latin signal is the baseline->register delta on h2 and "
            "word length; the absolute distance to the Voynich's h2 (2.43) inherits the "
            "glyph-vs-letter segmentation asymmetry flagged in discriminators.py.",
            "Registers are confounded with author/era/source (Caesar prose vs Pliny "
            "encyclopaedia vs a modern GBIF binomial checklist).",
            "latin_nomen is a name LIST (each pair an independent binomial), not running "
            "text; that is the point (a labelling register), but it means cross-token "
            "bigrams join unrelated names.",
            "This tests whether a register reproduces the Voynich's statistics, not whether "
            "the Voynich contains Latin.",
        ],
    }
    (RES / "register.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    # ---- figure ----
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(13, 5.2))
    for k in series:
        axA.plot(range(MAXLEN + 1), prof[k]["_hist"], marker="o", ms=4,
                 lw=2.4 if k == VOY else 1.8, color=COLORS[k], label=LABELS[k])
    axA.set_xlabel("word length (characters)"); axA.set_ylabel("proportion of tokens")
    axA.set_title("Word-length distribution by register")
    axA.grid(True, ls=":", alpha=0.3); axA.legend(fontsize=8)

    hb = ["wordlen_std", "h2_cond_bits"]
    x = np.arange(len(hb)); w = 0.2
    for i, k in enumerate(series):
        axB.bar(x + (i - 1.5) * w, [prof[k][m] for m in hb], w,
                color=COLORS[k], label=LABELS[k])
    axB.set_xticks(x); axB.set_xticklabels(["word-length std", "h2 (bits)"])
    axB.set_title("The two separating discriminators")
    axB.grid(True, axis="y", ls=":", alpha=0.3); axB.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "register.png", dpi=140); plt.close(fig)

    # ---- console verdict ----
    hdr = f"  {'metric':16s}" + "".join(f"{k.replace('latin_',''):>12s}" for k in series)
    print(hdr)
    for k in keys:
        row = f"  {k:16s}" + "".join(f"{prof[s][k]:12.3f}" for s in series)
        print(row)
    print(f"\n  word-length hist RMSE to Voynich (lower=closer): "
          + "  ".join(f"{reg.replace('latin_','')}={wl_rmse[reg]:.4f}" for reg in REGISTERS))
    print("\n  movement from baseline toward Voynich (gap %):")
    for reg in REGISTERS:
        if reg == BASELINE:
            continue
        gaps = movement[reg]
        for k in ("wordlen_std", "h2_cond_bits"):
            g = gaps[k]["gap_closed_frac"]
            gp = f"{g*100:+.0f}%" if g is not None else "n/a"
            print(f"    {reg:12s} {k:14s} {gp:>7s}  "
                  f"({'toward' if gaps[k]['toward_voynich'] else 'AWAY'})")
    print(f"\n  wrote {RES/'register.json'}, figures/register.png")


if __name__ == "__main__":
    main()
