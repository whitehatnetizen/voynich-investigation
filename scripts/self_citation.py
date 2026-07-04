"""Self-citation / generative-copying test (Timm & Schinner 2019).

The leading mechanistic account of the Voynich's exact profile — low word-order information +
local (near-)repetition + rigid within-word templates all at once — is that each word is
produced by COPYING a nearby earlier word and MUTATING it slightly through the slot grammar.
This script tests that directly.

Metric. For each word i, the minimum edit distance to any of the previous W words (its nearest
recent predecessor). Damerau-Levenshtein (DL) is primary: it counts substitutions, indels AND
adjacent transpositions, so distance-1 = "copy + one scribal change" — the model's core
prediction. Reported raw AND length-normalised (dist / max(len_a, len_b)) because Voynich words
are short, so a raw distance-1 is a large relative change.

THE essential control — SHUFFLE. The slot grammar already makes all Voynich words mutually
edit-similar, so a low raw nearest-distance proves nothing on its own. We reorder the SAME tokens
(identical vocabulary + affixes, sequential copying destroyed) and recompute. Only real-distance
BELOW shuffle is evidence of copying. Averaged over a few seeded shuffles. Every window uses the
same shuffle W, so the excess (shuffle - real) stays honest.

Four signatures (all four = strong support for copying):
  (1) real nearest-distance well below shuffle across the window sweep;
  (2) an EXCESS of near-identical neighbours specifically (mass piled onto edit-distance 0 = an
      exact copy and 1 = a copy+one-mutation, with distance 2/3+ in deficit), not a uniform
      downward shift. The distance-1 (mutated-copy) excess is the copying-SPECIFIC part: exact
      repeats (distance 0) can also come from ordinary word burstiness, but a mutated variant
      landing a few words later is the generative-copying fingerprint;
  (3) a locality gradient — nearer predecessors are more similar (real decays with lag; shuffle
      is flat);
  (4) the Voynich showing all three MORE strongly than the natural-language controls.

Jaro-Winkler is included only as a FLAGGED secondary: its prefix weighting is confounded by the
Voynich's shared prefix kit (qo-/ch-/sh-), so it manufactures false similarity and must not be
read as primary evidence.

Writes results/self_citation.json + figures/self_citation.png.
"""
import json
import random
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from rapidfuzz.distance import DamerauLevenshtein as DL
from rapidfuzz.distance import JaroWinkler as JW

import seriesio as S

RES = S.ROOT / "results"
FIG = S.ROOT / "figures"
SEED = 1492
NSHUF = 30            # review FIX-1: real null distribution (each rep is a mean over ~30k positions)
NSHUF_JW = 5          # the flagged JW secondary keeps a small null
WINDOWS = [1, 3, 5, 10, 25, 50]
REF_W = 25            # window used for the distance histogram + Jaro-Winkler secondary
START = max(WINDOWS)  # score the same token positions across every window (>= largest window)
LAGS = list(range(1, 26))          # per-lag locality curve
NEAR_BLOCK = (1, 5)                # lags 1..5   -> "recent predecessors"
FAR_BLOCK = (20, 25)               # lags 20..25 -> "older predecessors"

SERIES = [("voynich_eva", "Voynich", "red"),
          ("english", "English", "#1f77b4"),
          ("latin", "Latin", "#17becf"),
          ("german", "German", "#8c564b"),
          ("hebrew", "Hebrew", "#2f4f4f"),
          ("monkey", "monkey null", "grey")]


def nearest_sweep(tokens, windows=None):
    """One pass over the largest window serves ALL windows (review FIX-17 perf): for each token
    from START on, scan predecessors nearest-first, tracking the running min DL distance (raw and
    length-normalised); snapshot at each window boundary; early-exit at distance 0 (provably safe —
    the normalised distance is then also 0 and both minima cannot improve).
    Returns {W: (mean_raw, mean_norm)} plus the distance histogram at REF_W."""
    ws = sorted(windows or WINDOWS)
    wmax = ws[-1]
    n = len(tokens)
    raw = {W: 0.0 for W in ws}
    norm = {W: 0.0 for W in ws}
    h = [0, 0, 0, 0]                       # d0/d1/d2/d3plus counts at REF_W
    cnt = n - START

    def record(W, best, bestn):
        raw[W] += best
        norm[W] += bestn
        if W == REF_W:
            h[best if best < 3 else 3] += 1

    for i in range(START, n):
        ti = tokens[i]
        li = len(ti)
        best = 10 ** 9
        bestn = 2.0
        wi = 0
        for k in range(1, wmax + 1):
            tj = tokens[i - k]
            d = DL.distance(ti, tj)        # true distance (no score_cutoff: nd below needs real d)
            if d < best:
                best = d
            m = li if li >= len(tj) else len(tj)
            nd = d / m if m else 0.0
            if nd < bestn:
                bestn = nd
            if best == 0:                  # cannot improve; snapshot all remaining windows
                while wi < len(ws):
                    record(ws[wi], 0, 0.0)
                    wi += 1
                break
            if k == ws[wi]:
                record(ws[wi], best, bestn)
                wi += 1
    hist = {"d0": h[0] / cnt, "d1": h[1] / cnt, "d2": h[2] / cnt, "d3plus": h[3] / cnt}
    return ({W: (raw[W] / cnt, norm[W] / cnt) for W in ws}, hist)


def jw_nearest(tokens, W):
    """Mean of the max Jaro-Winkler similarity to the previous W tokens (flagged secondary)."""
    n = len(tokens)
    s = 0.0
    cnt = 0
    for i in range(START, n):
        ti = tokens[i]
        best = 0.0
        for j in range(i - W, i):
            v = JW.similarity(ti, tokens[j])
            if v > best:
                best = v
        s += best
        cnt += 1
    return s / cnt


def lag_curve(tokens):
    """Mean DL distance between token i and token i-k, for each lag k in LAGS."""
    n = len(tokens)
    out = []
    for k in LAGS:
        s = 0.0
        cnt = 0
        for i in range(k, n):
            s += DL.distance(tokens[i], tokens[i - k])
            cnt += 1
        out.append(s / cnt)
    return out


def block_mean(curve, block):
    lo, hi = block
    vals = [curve[k - 1] for k in range(lo, hi + 1)]
    return float(np.mean(vals))


def analyse(tokens, rng):
    # ---- ONE pass per shuffle serves every window (FIX-17); real null distributions (FIX-1) ----
    real_sweep, hist_real = nearest_sweep(tokens)
    shuf_raw = {W: [] for W in WINDOWS}
    shuf_norm = {W: [] for W in WINDOWS}
    shuf_hists = []
    shuf_curves = []
    for rep in range(NSHUF):
        rep_rng = random.Random(SEED + rep)
        sh = list(tokens)
        rep_rng.shuffle(sh)
        sw, hh = nearest_sweep(sh)
        for W in WINDOWS:
            shuf_raw[W].append(sw[W][0])
            shuf_norm[W].append(sw[W][1])
        shuf_hists.append(hh)
        shuf_curves.append(lag_curve(sh))

    sweep = {}
    for W in WINDOWS:
        r_raw, r_norm = real_sweep[W]
        mu_r, sd_r = float(np.mean(shuf_raw[W])), float(np.std(shuf_raw[W], ddof=1))
        mu_n = float(np.mean(shuf_norm[W]))
        exc = mu_r - r_raw
        entry = {"real_raw": round(r_raw, 4), "shuf_raw": round(mu_r, 4),
                 "excess_raw": round(exc, 4),
                 "shuf_raw_sd": round(sd_r, 5), "n_reps": NSHUF,
                 "excess_raw_z": round(exc / sd_r, 1) if sd_r else None,
                 "real_norm": round(r_norm, 4), "shuf_norm": round(mu_n, 4),
                 "excess_norm": round(mu_n - r_norm, 4)}
        if W == REF_W:
            entry["hist_shuffled"] = {k: round(float(np.mean([h[k] for h in shuf_hists])), 4)
                                      for k in ("d0", "d1", "d2", "d3plus")}
            entry["hist_shuffled_sd"] = {k: round(float(np.std([h[k] for h in shuf_hists], ddof=1)), 5)
                                         for k in ("d0", "d1", "d2", "d3plus")}
        sweep[str(W)] = entry

    # ---- distance histogram excess at the reference window ----
    hist_shuf = sweep[str(REF_W)]["hist_shuffled"]
    hist_sd = sweep[str(REF_W)]["hist_shuffled_sd"]
    hist_block = {
        "window": REF_W,
        "real": {k: round(v, 4) for k, v in hist_real.items()},
        "shuffled": hist_shuf,
        "shuffled_sd": hist_sd,
        "excess_d0": round(hist_real["d0"] - hist_shuf["d0"], 4),
        "excess_d1": round(hist_real["d1"] - hist_shuf["d1"], 4),
        "excess_d2": round(hist_real["d2"] - hist_shuf["d2"], 4),
        "excess_d3plus": round(hist_real["d3plus"] - hist_shuf["d3plus"], 4),
        "excess_d0_d1_z": round((hist_real["d0"] + hist_real["d1"]
                                 - hist_shuf["d0"] - hist_shuf["d1"])
                                / max(float(np.hypot(hist_sd["d0"], hist_sd["d1"])), 1e-9), 1),
    }

    # ---- locality gradient: per-lag curve, real vs the null distribution ----
    real_curve = lag_curve(tokens)
    shuf_curve = [float(np.mean(col)) for col in zip(*shuf_curves)]
    locality = {
        "lags": LAGS,
        "real": [round(x, 4) for x in real_curve],
        "shuffled": [round(x, 4) for x in shuf_curve],
        "near_real": round(block_mean(real_curve, NEAR_BLOCK), 4),
        "far_real": round(block_mean(real_curve, FAR_BLOCK), 4),
        "near_shuf": round(block_mean(shuf_curve, NEAR_BLOCK), 4),
        "far_shuf": round(block_mean(shuf_curve, FAR_BLOCK), 4),
    }
    # gradient = how much MORE similar the near block is than the far block (positive = locality)
    locality["gradient_real"] = round(locality["far_real"] - locality["near_real"], 4)
    locality["gradient_shuf"] = round(locality["far_shuf"] - locality["near_shuf"], 4)
    # per-rep null gradients -> spread of the null gradient (FIX-1)
    rep_grads = [block_mean(c, FAR_BLOCK) - block_mean(c, NEAR_BLOCK) for c in shuf_curves]
    locality["gradient_shuf_sd"] = round(float(np.std(rep_grads, ddof=1)), 5)
    ge = locality["gradient_real"] - locality["gradient_shuf"]
    locality["gradient_excess_z"] = round(ge / locality["gradient_shuf_sd"], 1) \
        if locality["gradient_shuf_sd"] else None

    # ---- Jaro-Winkler secondary (flagged) ----
    jw_real = jw_nearest(tokens, REF_W)
    jw_s = 0.0
    for rep in range(NSHUF_JW):
        rep_rng = random.Random(SEED + 500 + rep)
        sh = list(tokens)
        rep_rng.shuffle(sh)
        jw_s += jw_nearest(sh, REF_W)
    jw_s /= NSHUF_JW
    jw = {"window": REF_W, "real_mean_sim": round(jw_real, 4),
          "shuf_mean_sim": round(jw_s, 4), "excess": round(jw_real - jw_s, 4)}

    # ---- signatures roll-up ----
    sig = {
        "s1_below_shuffle": bool(sweep[str(REF_W)]["excess_raw"] > 0),
        # empirically the copy-spike sits at distance 0 (exact copy) + 1 (one mutation), with
        # d2/d3+ in deficit -- i.e. mass moved toward exact/near-exact, the copy+small-change tell
        "s2_copy_spike": bool(hist_block["excess_d0"] + hist_block["excess_d1"] > 0.02),
        "s3_locality_gradient": bool(locality["gradient_real"] > locality["gradient_shuf"] + 0.02),
        "excess_raw_refW": sweep[str(REF_W)]["excess_raw"],
        "excess_d0_d1": round(hist_block["excess_d0"] + hist_block["excess_d1"], 4),
        "gradient_excess": round(locality["gradient_real"] - locality["gradient_shuf"], 4),
    }
    return {"n": len(tokens), "sweep": sweep, "hist": hist_block,
            "locality": locality, "jaro_winkler_secondary": jw, "signatures": sig}


def main():
    RES.mkdir(exist_ok=True)
    FIG.mkdir(exist_ok=True)
    rng = random.Random(SEED)
    out = {"_meta": {"seed": SEED, "nshuf": NSHUF, "windows": WINDOWS, "ref_window": REF_W,
                     "start_index": START, "metric": "Damerau-Levenshtein",
                     "note": "excess = shuffle - real; positive excess = evidence of sequential "
                             "copying. Nulls are real distributions (per-rep seeds SEED+i); "
                             "excess_raw_z / excess_d0_d1_z / gradient_excess_z report the spread."}}
    for name, label, _ in SERIES:
        toks = S.load_tokens(name)
        out[label] = {"series": name, **analyse(toks, rng)}
        s = out[label]["signatures"]
        print(f"  {label:12s} excess_raw(W{REF_W})={s['excess_raw_refW']:+.3f} "
              f"(z={out[label]['sweep'][str(REF_W)]['excess_raw_z']})  "
              f"d0+d1 excess={s['excess_d0_d1']:+.3f} (z={out[label]['hist']['excess_d0_d1_z']})  "
              f"grad(real/shuf)={out[label]['locality']['gradient_real']:+.3f}/"
              f"{out[label]['locality']['gradient_shuf']:+.3f} "
              f"(z={out[label]['locality']['gradient_excess_z']})  "
              f"[{'/'.join(k for k, v in s.items() if k.startswith('s') and v)}]")
    (RES / "self_citation.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    # ---- figures: (A) excess vs window  (B) distance histogram  (C) locality curves ----
    labels = [lab for _, lab, _ in SERIES]
    colors = {lab: c for _, lab, c in SERIES}
    fig, (axA, axB, axC) = plt.subplots(1, 3, figsize=(17, 5.2))

    for lab in labels:
        ex = [out[lab]["sweep"][str(W)]["excess_raw"] for W in WINDOWS]
        axA.plot(WINDOWS, ex, marker="o", color=colors[lab],
                 lw=2.4 if lab == "Voynich" else 1.3, label=lab)
    axA.axhline(0, color="k", lw=0.8)
    axA.set_xscale("log"); axA.set_xticks(WINDOWS); axA.set_xticklabels(WINDOWS)
    axA.set_xlabel("window W (previous words considered)")
    axA.set_ylabel("excess raw DL distance in edits  (shuffle - real; higher = more copying)")
    axA.set_title("(A) Nearest-predecessor distance below shuffle\nhigher = more sequential copying")
    axA.grid(True, ls=":", alpha=0.3); axA.legend(fontsize=8)

    x = np.arange(4); wbar = 0.35
    v = out["Voynich"]["hist"]
    axB.bar(x - wbar/2, [v["real"][k] for k in ("d0", "d1", "d2", "d3plus")], wbar,
            label="Voynich real", color="red")
    axB.bar(x + wbar/2, [v["shuffled"][k] for k in ("d0", "d1", "d2", "d3plus")], wbar,
            label="Voynich shuffled", color="#f0a0a0")
    axB.set_xticks(x); axB.set_xticklabels(["dist 0\n(exact)", "dist 1", "dist 2", "dist >=3"])
    axB.set_ylabel(f"fraction of words (W={REF_W})")
    axB.set_title("(B) Where the nearest predecessor sits\ncopy(+mutation) = mass at dist 0-1 above shuffle")
    axB.legend(fontsize=8); axB.grid(True, axis="y", ls=":", alpha=0.3)

    for lab in labels:
        loc = out[lab]["locality"]
        axC.plot(loc["lags"], loc["real"], color=colors[lab],
                 lw=2.4 if lab == "Voynich" else 1.3, label=lab)
    vsh = out["Voynich"]["locality"]
    axC.plot(vsh["lags"], vsh["shuffled"], color="red", ls="--", lw=1.2, label="Voynich (shuffled)")
    axC.set_xlabel("lag k (words back)")
    axC.set_ylabel("mean DL distance to word i-k")
    axC.set_title("(C) Locality gradient\nreal copying: nearer words more similar (rises with lag)")
    axC.grid(True, ls=":", alpha=0.3); axC.legend(fontsize=8)

    fig.tight_layout(); fig.savefig(FIG / "self_citation.png", dpi=140); plt.close(fig)
    print(f"\n  wrote {RES/'self_citation.json'}, figures/self_citation.png")


if __name__ == "__main__":
    main()
