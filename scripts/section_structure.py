"""De-confound scribe/system from subject, and test the Montemurro semantic-clustering rival.
(2026-07-01)

The Currier A/B split (`currier_split.py`) found A and B differ (A copies-and-mutates, B repeats
exactly; A `ch-`/`-ol`, B `qo-`/`-dy`) — but A vs B is simultaneously a HAND, SECTION and SYSTEM
contrast, so we could not say which drives the difference. And it left the strongest pro-meaning
argument untested: Montemurro & Zanette (2013) found Voynich words cluster by section like topical
vocabulary, which would imply the text carries meaning. This script attacks both.

PART 1 — de-confound (Herbal is the shared subject: it contains BOTH Currier A and B pages).
  cells:  Herbal-A   (subject=herbal, system=A, hand 1)
          Herbal-B   (subject=herbal, system=B, hands 2/3)   -- same SUBJECT as Herbal-A, diff system
          Stars-B    (subject=stars,  system=B)              -- same SYSTEM as Herbal-B, diff SUBJECT
          Bio-B      (subject=biol.,  system=B)              -- same SYSTEM as Herbal-B, diff SUBJECT
  Size-matched to the smallest cell. If Herbal-A vs Herbal-B reproduces the whole-A vs whole-B
  difference (affixes, copying mode), the A/B difference is SYSTEM, not subject. If Stars-B / Bio-B
  differ from Herbal-B, there is also a subject effect within one system.

PART 2 — Montemurro rival, de-confounded. Word<->section mutual information I(word; section),
  measured against a SHUFFLE null (permute section labels, same marginals -> cancels the
  finite-sample bias; only real-above-shuffle = genuine section structure). Computed:
    pooled    (all tokens, all sections)  -> conflates dialect AND topic
    within-B  (B tokens, B sections)      -> topic only, dialect held fixed  <- THE test
    within-A  (A tokens, A sections)
  The catch Montemurro's critics raise: word-section clustering can be just the Currier A/B
  vocabulary split (qo-/-dy words live in B sections). If the clustering SURVIVES within one
  dialect (within-B excess MI >> 0), that is topical structure meaning would predict; if it
  COLLAPSES to the null, the apparent semantics was only the dialect split.

Writes results/section_structure.json + figures/section_structure.png.
"""
import json
import random
from collections import Counter
from math import log2

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import seriesio as S
from currier_split import analyse_subset   # count_stats + shuffle-controlled self_citation

STRUCT = S.ROOT / "data" / "voynich" / "eva_structured.jsonl"
RES = S.ROOT / "results"
FIG = S.ROOT / "figures"
SEED = 1492
MI_NSHUF = 200        # review FIX-1: real null distribution


def rotation_offsets(n, nrep, seed):
    """Random circular offsets, kept away from 0/n so rotations are non-trivial."""
    rr = random.Random(seed)
    lo, hi = max(1, n // 20), n - max(1, n // 20)
    return [rr.randrange(lo, hi) for _ in range(nrep)]


# ---------- word <-> section mutual information ----------
def mutual_info(words, sections):
    n = len(words)
    wc = Counter(words)
    sc = Counter(sections)
    jc = Counter(zip(words, sections))
    mi = 0.0
    for (w, s), c in jc.items():
        p_ws = c / n
        mi += p_ws * log2(p_ws / ((wc[w] / n) * (sc[s] / n)))
    return mi


def section_entropy(sections):
    return -sum((c / len(sections)) * log2(c / len(sections)) for c in Counter(sections).values())


def mi_vs_shuffle(words, sections, rng, nshuf=MI_NSHUF):
    """Word<->section MI against TWO nulls (review FIX-7):
      permutation — iid token-label permutation. Blind to word BURSTINESS: a bursty but
        meaningless process (our copy-and-mutate generator with zero section bias) scores
        positive excess against it, so it OVERSTATES topical signal.
      rotation — circularly rotate the section-label sequence relative to the token sequence
        (both sequences keep their internal clumping; only the association is broken). This is
        the burstiness-corrected null and the HEADLINE number.
    rng retained for signature compatibility; reps use per-rep seeds SEED+i."""
    real = mutual_info(words, sections)
    sh = []
    for rep in range(nshuf):
        perm = list(sections)
        random.Random(SEED + rep).shuffle(perm)
        sh.append(mutual_info(words, perm))
    rot = []
    for off in rotation_offsets(len(sections), nshuf, SEED + 7):
        rot.append(mutual_info(words, sections[off:] + sections[:off]))
    shuf, shuf_sd = float(np.mean(sh)), float(np.std(sh, ddof=1))
    rmu, rsd = float(np.mean(rot)), float(np.std(rot, ddof=1))
    Hs = section_entropy(sections)
    return {
        "mi_real": round(real, 4),
        "mi_shuffle": round(shuf, 4), "mi_shuffle_sd": round(shuf_sd, 5),
        "excess_mi": round(real - shuf, 4),
        "excess_mi_z": round((real - shuf) / shuf_sd, 1) if shuf_sd else None,
        "mi_rotation": round(rmu, 4), "mi_rotation_sd": round(rsd, 5),
        "excess_mi_rotation": round(real - rmu, 4),
        "excess_mi_rotation_z": round((real - rmu) / rsd, 1) if rsd else None,
        "H_section": round(Hs, 4),
        "excess_frac_of_Hsection": round((real - shuf) / Hs, 4) if Hs else 0.0,
        "excess_rot_frac_of_Hsection": round((real - rmu) / Hs, 4) if Hs else 0.0,
        "n_reps": nshuf,
        "n": len(words), "n_sections": len(set(sections)),
        "n_word_types": len(set(words)),
    }


def main():
    RES.mkdir(exist_ok=True)
    FIG.mkdir(exist_ok=True)
    rows = [json.loads(l) for l in STRUCT.read_text(encoding="utf-8").splitlines() if l.strip()]
    rng = random.Random(SEED)

    def cell(currier, section):
        return [r["token"] for r in rows if r.get("currier_lang") == currier and r["section"] == section]

    # ---------------- PART 1: de-confound ----------------
    cells_raw = {
        "Herbal-A": cell("A", "Herbal"),
        "Herbal-B": cell("B", "Herbal"),
        "Stars-B": cell("B", "Stars"),
        "Bio-B": cell("B", "Biological"),
    }
    M = min(len(v) for v in cells_raw.values())
    part1 = {"_size_matched_M": M, "_raw_sizes": {k: len(v) for k, v in cells_raw.items()}}
    for name, toks in cells_raw.items():
        ordered_M = toks[:M]                    # contiguous, for self-citation
        sample_M = rng.sample(toks, M)          # representative, for order-independent stats
        part1[name] = analyse_subset(ordered_M, sample_M, rng)

    # ---------------- PART 2: Montemurro rival ----------------
    def words_sections(pred, sections_keep=None):
        w, s = [], []
        for r in rows:
            if pred(r) and (sections_keep is None or r["section"] in sections_keep):
                w.append(r["token"]); s.append(r["section"])
        return w, s

    # keep only sections with a reasonable footprint so tiny sections don't add noise
    def big_sections(pred, floor=800):
        c = Counter(r["section"] for r in rows if pred(r))
        return {s for s, n in c.items() if n >= floor}

    isA = lambda r: r.get("currier_lang") == "A"
    isB = lambda r: r.get("currier_lang") == "B"
    anytok = lambda r: True

    pooled_keep = big_sections(anytok)
    A_keep = big_sections(isA)
    B_keep = big_sections(isB)

    wp, sp = words_sections(anytok, pooled_keep)
    wa, sa = words_sections(isA, A_keep)
    wb, sb = words_sections(isB, B_keep)

    part2 = {
        "sections_used": {"pooled": sorted(pooled_keep), "A": sorted(A_keep), "B": sorted(B_keep)},
        "pooled": mi_vs_shuffle(wp, sp, rng),
        "within_A": mi_vs_shuffle(wa, sa, rng),
        "within_B": mi_vs_shuffle(wb, sb, rng),
    }

    out = {
        "_meta": {
            "seed": SEED, "mi_nshuf": MI_NSHUF,
            "part1": "de-confound: Herbal-A/Herbal-B (same subject, diff system) vs Stars-B/Bio-B (same system, diff subject); size-matched to M",
            "part2": "word-section mutual info vs shuffle null; within-B holds dialect fixed to test Montemurro topical clustering de-confounded",
        },
        "part1_deconfound": part1,
        "part2_montemurro": part2,
    }
    (RES / "section_structure.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    # ---------------- console ----------------
    print(f"PART 1 — de-confound (size-matched M={M}; raw {part1['_raw_sizes']})")
    print(f"  {'cell':10s} {'h2':>5s} {'wlenStd':>7s} {'suf2cov':>7s} {'exD0':>6s} {'exD1':>6s} {'grad':>6s}   top-suffix / top-prefix")
    for name in cells_raw:
        d = part1[name]; s = d["self_citation"]
        tsuf = " ".join(f"{g}:{n}" for g, n in d["top_suffix2"][:3])
        tpre = " ".join(f"{g}:{n}" for g, n in d["top_prefix2"][:3])
        print(f"  {name:10s} {d['h2']:5.2f} {d['wordlen_std']:7.2f} {d['suffix2_cov']:7.2f} "
              f"{s['excess_d0']:+6.3f} {s['excess_d1']:+6.3f} {s['gradient_real']:+6.3f}   {tsuf} / {tpre}")

    print(f"\nPART 2 — Montemurro rival (word<->section MI; permutation AND rotation nulls; NSHUF={MI_NSHUF})")
    print(f"  {'scope':10s} {'miReal':>7s} {'excPerm':>8s} {'z':>6s} {'excRot':>8s} {'z':>6s} "
          f"{'exc/Hs':>7s} {'excRot/Hs':>9s} {'sections':>8s}")
    for k in ("pooled", "within_A", "within_B"):
        d = part2[k]
        print(f"  {k:10s} {d['mi_real']:7.3f} {d['excess_mi']:+8.3f} {str(d['excess_mi_z']):>6s} "
              f"{d['excess_mi_rotation']:+8.3f} {str(d['excess_mi_rotation_z']):>6s} "
              f"{d['excess_frac_of_Hsection']:7.3f} {d['excess_rot_frac_of_Hsection']:9.3f} {d['n_sections']:8d}")
    print(f"  sections used: B={part2['sections_used']['B']}")

    # ---------------- figure ----------------
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16.5, 5))
    names = list(cells_raw)
    cols = ["#c44e52", "#4c72b0", "#dd8452", "#55a868"]

    # panel 1: h2 + word-length std per cell
    x = np.arange(len(names)); w = 0.38
    ax1.bar(x - w/2, [part1[n]["h2"] for n in names], w, label="h2 (bits)", color="#4c72b0")
    ax1.bar(x + w/2, [part1[n]["wordlen_std"] for n in names], w, label="word-length std", color="#55a868")
    ax1.set_xticks(x); ax1.set_xticklabels(names, fontsize=9)
    ax1.set_title("(1) De-confound: same subject (Herbal-A vs -B)\nvs same system (B) different subject")
    ax1.grid(True, axis="y", ls=":", alpha=0.3); ax1.legend(fontsize=8)

    # panel 2: copying mode (d0 exact vs d1 mutated excess) per cell
    ax2.bar(x - w/2, [part1[n]["self_citation"]["excess_d0"] for n in names], w, label="dist-0 (exact) excess", color="#8c564b")
    ax2.bar(x + w/2, [part1[n]["self_citation"]["excess_d1"] for n in names], w, label="dist-1 (mutated) excess", color="#e377c2")
    ax2.set_xticks(x); ax2.set_xticklabels(names, fontsize=9)
    ax2.axhline(0, color="k", lw=0.8)
    ax2.set_title("(2) Copying mode by cell\nA=mutate, B=repeat — system or subject?")
    ax2.grid(True, axis="y", ls=":", alpha=0.3); ax2.legend(fontsize=8)

    # panel 3: Montemurro — excess word-section MI, pooled vs within-dialect
    scopes = ["pooled", "within_A", "within_B"]
    vals = [part2[s]["excess_mi"] for s in scopes]
    ax3.bar(scopes, vals, color=["#8c8c8c", "#c44e52", "#4c72b0"])
    ax3.axhline(0, color="k", lw=0.8)
    ax3.set_ylabel("excess word-section MI (bits, over shuffle)")
    ax3.set_title("(3) Montemurro rival: does topical clustering\nsurvive WITHIN one dialect?")
    ax3.grid(True, axis="y", ls=":", alpha=0.3)
    for i, v in enumerate(vals):
        ax3.text(i, v, f"{v:+.3f}", ha="center", va="bottom", fontsize=9)

    fig.suptitle("De-confounding hand/system/subject, and testing topical clustering", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(FIG / "section_structure.png", dpi=140)
    plt.close(fig)
    print(f"\n  wrote {RES/'section_structure.json'}, figures/section_structure.png")


if __name__ == "__main__":
    main()
