"""Removing doubt, test P1 — the information-capacity argument via long-range mutual information.

Meaning at book length REQUIRES long-range structure (topics, discourse, reference), which in real
language shows up as mutual information I(token_i ; token_{i+d}) that decays SLOWLY with distance d
(Montemurro & Zanette: a heavy, near-power-law tail). A memoryless / locally-generated process has
mutual information that collapses to zero after a few words. So this asks the decisive question: does
the Voynich carry the long-range information a message would need, or does it go 'flat' like a
generator?

For each distance d we estimate I_d over all token pairs at that separation, and subtract a shuffle
baseline (which destroys correlation, leaving only the finite-sample estimation bias). The EXCESS
I_d - I_d^shuffle is the genuine long-range mutual information at distance d. Compared for the
Voynich, our scribe generator, real Latin and real English.

Raw long-range MI is a TRAP: it conflates repetition (same word recurring — predictable, LOW
information) with association (different words predicting each other — where a message's information
would live). So we decompose the excess MI at each distance into:
  SELF  the contribution from identical pairs (x==y) — pure repetition / burstiness / section reuse
  CROSS the contribution from different words (x!=y) — topical/semantic association
Real discourse carries long-range CROSS information. We compare the Voynich to a SECTION-AWARE
meaningless generator (per-section vocabulary bias, like the manuscript's sections): if the Voynich's
long-range structure is repetition-dominated AND matched by the section-aware generator, then it is
mechanical, not a message.

2026-07-04 (review FIX-1/2/3): the estimator is integer-coded and vectorised (~40x), the shuffle
null is a real distribution (NSHUF=200, per-rep seeds derived from the master seed) reported as
null_mean/null_sd/z, and the per-distance excesses are NO LONGER clipped at zero before summing —
the long-range sums are SIGNED. Under the old clipped estimator the language baselines (0.002/0.000)
were floors, not measurements; the honest baselines are slightly negative.

Writes results/long_range_mi.json + figures/long_range_mi.png.
"""
import json
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import seriesio as S
import scribe_recipe_test as SR

RES = S.ROOT / "results"
FIG = S.ROOT / "figures"
SEED = 1492
N = 30000
SECT = [12000, 7000, 5000, 4000, 2000]           # section sizes for the section-aware generator (sum N)
DISTS = [1, 2, 3, 5, 8, 13, 20, 32, 50, 80, 130, 200, 320, 500, 800]
NSHUF = 200
FAR_MIN = 20                                     # 'long range' = d >= FAR_MIN


def encode(tokens):
    """Integer-code a token stream once. Returns (codes int64 array, vocab size)."""
    uniq, inv = np.unique(np.asarray(tokens, dtype=object), return_inverse=True)
    return inv.astype(np.int64), len(uniq)


def mi_parts_coded(codes, V, d):
    """Excess-free MI at distance d on an integer-coded stream, split into SELF (x==y) and
    CROSS (x!=y) contributions (bits). Vectorised: joint counts via unique on a*V+b keys."""
    a = codes[:-d]
    b = codes[d:]
    n = a.size
    ca = np.bincount(a, minlength=V)
    cb = np.bincount(b, minlength=V)
    key = a * V + b
    uk, cc = np.unique(key, return_counts=True)
    x = uk // V
    y = uk % V
    term = (cc / n) * np.log2((cc.astype(float) * n) / (ca[x].astype(float) * cb[y]))
    m = x == y
    return float(term[m].sum()), float(term[~m].sum())


def mi_parts(tokens, d):
    """Back-compatible wrapper: MI parts at distance d from a raw token list."""
    codes, V = encode(tokens)
    return mi_parts_coded(codes, V, d)


def curves(tokens, seed=SEED, nshuf=NSHUF, dists=DISTS):
    """Per-distance SELF/CROSS excess MI with a real null distribution (nshuf reps).
    Excesses and the long-range sums are SIGNED (no clipping)."""
    codes, V = encode(tokens)
    far = [d for d in dists if d >= FAR_MIN]
    real = {d: mi_parts_coded(codes, V, d) for d in dists}
    null_self = {d: np.empty(nshuf) for d in dists}
    null_cross = {d: np.empty(nshuf) for d in dists}
    for rep in range(nshuf):
        rng = np.random.default_rng(seed + rep)
        t = rng.permutation(codes)
        for d in dists:
            s, c = mi_parts_coded(t, V, d)
            null_self[d][rep] = s
            null_cross[d][rep] = c
    self_e = {d: round(real[d][0] - float(null_self[d].mean()), 4) for d in dists}
    cross_e = {d: round(real[d][1] - float(null_cross[d].mean()), 4) for d in dists}
    # long-range sums: signed, with the null spread of the SUM taken across reps
    real_self_sum = sum(real[d][0] for d in far)
    real_cross_sum = sum(real[d][1] for d in far)
    null_self_sums = np.sum([null_self[d] for d in far], axis=0)
    null_cross_sums = np.sum([null_cross[d] for d in far], axis=0)
    def summ(real_sum, null_sums):
        mu, sd = float(null_sums.mean()), float(null_sums.std(ddof=1))
        exc = real_sum - mu
        return round(exc, 4), round(sd, 4), round(exc / sd, 1) if sd else None
    self_sum, self_sd, self_z = summ(real_self_sum, null_self_sums)
    cross_sum, cross_sd, cross_z = summ(real_cross_sum, null_cross_sums)
    return {"self": self_e, "cross": cross_e,
            "self_null_sd": {d: round(float(null_self[d].std(ddof=1)), 5) for d in dists},
            "cross_null_sd": {d: round(float(null_cross[d].std(ddof=1)), 5) for d in dists},
            "self_sum_d>=20": self_sum, "cross_sum_d>=20": cross_sum,
            "self_sum_null_sd": self_sd, "cross_sum_null_sd": cross_sd,
            "self_sum_z": self_z, "cross_sum_z": cross_z,
            "n_reps": nshuf}


def _mi_parts_reference(tokens, d):
    """The original pure-Python estimator, kept ONLY to verify the vectorised one."""
    from collections import Counter
    from math import log2
    a = tokens[:len(tokens) - d]
    b = tokens[d:]
    n = len(a)
    ca, cb = Counter(a), Counter(b)
    cab = Counter(zip(a, b))
    i_self = i_cross = 0.0
    for (x, y), c in cab.items():
        pab = c / n
        term = pab * log2(pab / ((ca[x] / n) * (cb[y] / n)))
        if x == y:
            i_self += term
        else:
            i_cross += term
    return i_self, i_cross


def main():
    RES.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)
    voy = S.load_tokens("voynich_eva")

    # FIX-2 verification: vectorised estimator must match the reference to float precision
    for d in (1, 20, 320):
        ref = _mi_parts_reference(voy, d)
        fast = mi_parts(voy, d)
        assert abs(ref[0] - fast[0]) < 1e-9 and abs(ref[1] - fast[1]) < 1e-9, (d, ref, fast)
    print("  [selftest] vectorised MI matches reference estimator at d=1/20/320")

    tab = SR.fit_tables(voy)
    gen_sec, _ = SR.scribe(tab, random.Random(SEED), N, SECT)      # section-aware generator

    series = [("Voynich", voy, "#c0392b"),
              ("section-aware generator", gen_sec, "#16a085"),
              ("Latin (real)", S.load_tokens("latin"), "#17becf"),
              ("English (real)", S.load_tokens("english"), "#27632a")]
    out = {"_meta": {"seed": SEED, "distances": DISTS, "nshuf": NSHUF, "sections": SECT,
                     "note": "excess MI (bits) at distance d, split SELF (same word = repetition) vs "
                             "CROSS (different words = association/information). SIGNED excess vs a "
                             "200-rep permutation null (no clipping); sums d>=20 reported with the "
                             "null SD of the sum and z. CROSS at long range is what a message needs; "
                             "compare to a section-aware meaningless generator."},
           "series": {}}
    for name, toks, _ in series:
        out["series"][name] = curves(toks)
    (RES / "long_range_mi.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    print("  SELF (repetition) vs CROSS (association) excess MI, SIGNED long-range sum (d>=20):")
    print(f"  {'series':26s} {'self_LR':>8s} {'z':>6s} {'cross_LR':>9s} {'z':>6s}")
    for name, _, _ in series:
        d = out["series"][name]
        print(f"  {name:26s} {d['self_sum_d>=20']:8.3f} {str(d['self_sum_z']):>6s} "
              f"{d['cross_sum_d>=20']:9.3f} {str(d['cross_sum_z']):>6s}")
    print("\n  CROSS excess MI (bits) by distance (the 'information' channel):")
    print(f"  {'series':26s}" + "".join(f"{('d'+str(x)):>8s}" for x in [1, 20, 80, 320]))
    for name, _, _ in series:
        c = out["series"][name]["cross"]
        print(f"  {name:26s}" + "".join(f"{c[x]:8.3f}" for x in [1, 20, 80, 320]))

    # ---- figure: self vs cross, Voynich vs section-aware generator vs language ----
    fig, (axS, axC) = plt.subplots(1, 2, figsize=(15, 6), sharey=True)
    for name, _, col in series:
        s = out["series"][name]
        axS.plot(DISTS, [s["self"][d] for d in DISTS], marker="o", ms=3, color=col,
                 lw=2.4 if name == "Voynich" else 1.5, label=name)
        axC.plot(DISTS, [s["cross"][d] for d in DISTS], marker="o", ms=3, color=col,
                 lw=2.4 if name == "Voynich" else 1.5, label=name)
    for ax, ttl in [(axS, "SELF — repetition (same word recurs)\nLOW information"),
                    (axC, "CROSS — association (different words)\nwhere a MESSAGE's information lives")]:
        ax.set_xscale("log")
        ax.set_yscale("symlog", linthresh=1e-3)
        ax.axhline(0, color="k", lw=0.7)
        ax.set_xlabel("token distance d")
        ax.set_title(ttl); ax.grid(True, which="both", ls=":", alpha=0.3); ax.legend(fontsize=8)
    axS.set_ylabel("excess mutual information (bits, signed, 200-rep permutation null)")
    fig.suptitle("Removing doubt P1 — is the Voynich's long-range structure repetition or information?", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.95)); fig.savefig(FIG / "long_range_mi.png", dpi=140); plt.close(fig)
    print(f"\n  wrote {RES/'long_range_mi.json'}, figures/long_range_mi.png")


if __name__ == "__main__":
    main()
