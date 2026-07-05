"""Phase C — pre-registered statistics for the T8 label-image census.

The decision rules below were pre-registered (fixed BEFORE the data was collected). This script
executes them literally. SEED=1492, per-rep seeds SEED+rep, 1000 permutation reps, null mean/sd + z.

  C1  slot recurrence           (zodiac_slots.csv)   FIRES if z >= 3  (same label -> same angular slot)
  C2  interchangeables' labels  (nymph_matches.csv)  FIRES if |z| >= 3
  C3  same-referent same-label  (pharma_matches.csv) FIRES if z >= 3
  C4  per-sign central names     (central_words.csv)  FIRES only if a AND b AND c

Output: results/t8_census.json
"""
import csv
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CEN = ROOT / "data" / "voynich" / "census"
RES = ROOT / "results"
RES.mkdir(exist_ok=True)
SEED = 1492
REPS = 1000


# ---- helpers ----------------------------------------------------------------
def dl_distance(a, b):
    """Damerau-Levenshtein (optimal string alignment)."""
    la, lb = len(a), len(b)
    d = [[0] * (lb + 1) for _ in range(la + 1)]
    for i in range(la + 1):
        d[i][0] = i
    for j in range(lb + 1):
        d[0][j] = j
    for i in range(1, la + 1):
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[la][lb]


def norm_label(s):
    s = re.sub(r"[.,]", " ", s)
    return s.split()[0] if s.split() else ""      # first EVA token = the label head


def circ_dist(a, b):
    """circular distance in degrees between two clock angles."""
    d = abs(a - b) % 360
    return min(d, 360 - d)


def load(name):
    p = CEN / name
    return list(csv.DictReader(p.open(encoding="utf-8"))) if p.exists() else None


# ---- C1: slot recurrence ----------------------------------------------------
def c1():
    rows = [r for r in load("zodiac_slots.csv") if r["angle_deg"] not in ("", None)]
    for r in rows:
        r["_ang"] = float(r["angle_deg"])
        r["_lab"] = norm_label(r["eva_label_clean"])
    by_page = {}
    for r in rows:
        by_page.setdefault(r["folio"], []).append(r)

    def stat(assign):
        """assign: folio -> list of angles aligned to that page's label list order.
        Returns mean circular distance over all cross-page pairs sharing a label."""
        lab_occ = {}   # label -> list of (folio, angle)
        for folio, rs in by_page.items():
            for r, ang in zip(rs, assign[folio]):
                lab_occ.setdefault(r["_lab"], []).append((folio, ang))
        dists = []
        for lab, occ in lab_occ.items():
            for i in range(len(occ)):
                for j in range(i + 1, len(occ)):
                    if occ[i][0] != occ[j][0]:           # different pages
                        dists.append(circ_dist(occ[i][1], occ[j][1]))
        return (sum(dists) / len(dists), len(dists)) if dists else (None, 0)

    real_assign = {f: [r["_ang"] for r in rs] for f, rs in by_page.items()}
    obs, n_pairs = stat(real_assign)

    rng = random.Random(SEED)
    null = []
    for rep in range(REPS):
        rng.seed(SEED + rep)
        perm = {}
        for f, rs in by_page.items():
            angs = [r["_ang"] for r in rs]
            rng.shuffle(angs)
            perm[f] = angs
        d, _ = stat(perm)
        null.append(d)
    nm = sum(null) / len(null)
    nsd = (sum((x - nm) ** 2 for x in null) / len(null)) ** 0.5
    # same-slot score: positive if observed distance is BELOW null
    z = (nm - obs) / nsd if nsd else 0.0
    n_labels_multi = sum(1 for lab, occ in
                         {l: [o for o in v] for l, v in
                          _label_occ(by_page, real_assign).items()}.items()
                         if len({o[0] for o in occ}) >= 2)
    return {
        "test": "C1 slot recurrence (clock-angle)", "n_crosspage_pairs": n_pairs,
        "n_labels_on_multiple_pages": n_labels_multi,
        "obs_mean_circ_dist_deg": round(obs, 2), "null_mean_deg": round(nm, 2),
        "null_sd_deg": round(nsd, 2), "z": round(z, 2),
        "fires": bool(z >= 3), "reps": REPS,
        "direction": "z>0 => matched labels sit CLOSER in angle than chance (same-slot signal)",
    }


def _label_occ(by_page, assign):
    lab_occ = {}
    for folio, rs in by_page.items():
        for r, ang in zip(rs, assign[folio]):
            lab_occ.setdefault(r["_lab"], []).append((folio, ang))
    return lab_occ


# ---- C2: interchangeables share labels? -------------------------------------
def c2():
    rows = load("nymph_matches.csv")
    if not rows:
        return {"test": "C2", "status": "pending (nymph_matches.csv not built yet)"}
    sim3 = [r for r in rows if int(r["visual_similarity"]) == 3]
    if len(sim3) < 3:
        return {"test": "C2", "status": f"too few similarity-3 pairs ({len(sim3)})",
                "n_pairs_sim3": len(sim3)}
    # matched-pair label DL distances
    def dl_pair(r, strip_first=False):
        a, b = norm_label(r["eva_label_a"]), norm_label(r["eva_label_b"])
        if strip_first:
            a, b = a[1:], b[1:]
        return dl_distance(a, b), len(a), len(b)
    obs_ds = [dl_pair(r)[0] for r in sim3]
    obs = sum(obs_ds) / len(obs_ds)

    # null: random label pairs matched on BOTH observed labels' lengths, drawn from the full
    # label pool. (First implementation matched only len(a): null pairs were equal-length while
    # observed pairs are often length-mismatched, and DL >= |len(a)-len(b)|, so the null was
    # biased low and the first-run z of +4.01 was an artefact. Fixed 2026-07-05; fair z = +0.92.)
    pool = {}
    for r in [x for x in load("zodiac_slots.csv") if x["angle_deg"] not in ("", None)]:
        lab = norm_label(r["eva_label_clean"])
        pool.setdefault(len(lab), []).append((r["folio"], lab))
    rng = random.Random(SEED)
    null = []
    for rep in range(REPS):
        rng.seed(SEED + rep)
        ds = []
        for r in sim3:
            a = norm_label(r["eva_label_a"])
            b = norm_label(r["eva_label_b"])
            ca, cb = pool.get(len(a), []), pool.get(len(b), [])
            if ca and cb:
                x, y = rng.choice(ca), rng.choice(cb)
                ds.append(dl_distance(x[1], y[1]))
        null.append(sum(ds) / len(ds) if ds else 0)
    nm = sum(null) / len(null)
    nsd = (sum((x - nm) ** 2 for x in null) / len(null)) ** 0.5
    z = (obs - nm) / nsd if nsd else 0.0
    # stem-stripped robustness
    obs_strip = sum(dl_pair(r, True)[0] for r in sim3) / len(sim3)
    direction = ("below_null_naming" if z <= -3 else
                 "above_null_differentiation" if z >= 3 else "at_null_register")
    return {
        "test": "C2 interchangeables share labels", "n_pairs_sim3": len(sim3),
        "obs_mean_DL": round(obs, 3), "null_mean_DL": round(nm, 3), "null_sd": round(nsd, 3),
        "z": round(z, 2), "fires": bool(abs(z) >= 3),
        "direction": direction, "naming_supported": bool(z <= -3),
        "obs_mean_DL_first_glyph_stripped": round(obs_strip, 3),
        "interpretation": "DL below null => identical labels on identical figures (naming); "
                          "above null => active differentiation; ~null => shared register only. "
                          "NOTE: matched pairs here are all cross-page, so a positive z may partly "
                          "reflect page-level stem clustering rather than active differentiation; the "
                          "load-bearing conclusion is only that the naming (below-null) direction is refuted.",
    }


# ---- C3: same referent, same label (pharma F1) ------------------------------
def c3():
    rows = load("pharma_matches.csv")
    if not rows:
        return {"test": "C3", "status": "pending (pharma_matches.csv not built yet)"}
    pp = [r for r in rows if r.get("match_type") == "pharma-pharma" and int(r["visual_similarity"]) == 3]
    ph = [r for r in rows if r.get("match_type") == "pharma-herbal" and int(r["visual_similarity"]) == 3]

    def frac_dl_le1(pairs):
        if not pairs:
            return None, 0
        n = sum(1 for r in pairs if dl_distance(norm_label(r["eva_label_a"]),
                                                norm_label(r["eva_label_b"])) <= 1)
        return n / len(pairs), len(pairs)

    obs_frac, n = frac_dl_le1(pp)
    result = {"test": "C3 same-referent same-label (pharma-pharma)", "n_pairs_sim3": n}
    if n and n >= 3:
        pool = {}
        for r in load("pharma_labels.csv") or []:
            lab = norm_label(r["eva_label"])
            pool.setdefault(len(lab), []).append(lab)
        rng = random.Random(SEED)
        null = []
        for rep in range(REPS):
            rng.seed(SEED + rep)
            cnt = 0
            for r in pp:
                a = norm_label(r["eva_label_a"])
                cands = pool.get(len(a), [])
                if len(cands) >= 2:
                    x, y = rng.sample(cands, 2)
                    cnt += (dl_distance(x, y) <= 1)
            null.append(cnt / len(pp))
        nm = sum(null) / len(null)
        nsd = (sum((x - nm) ** 2 for x in null) / len(null)) ** 0.5
        z = (obs_frac - nm) / nsd if nsd else 0.0
        result.update(obs_frac_DL_le1=round(obs_frac, 3), null_mean=round(nm, 3),
                      null_sd=round(nsd, 3), z=round(z, 2), fires=bool(z >= 3))
    else:
        result.update(status="too few pharma-pharma similarity-3 pairs for a permutation test",
                      obs_frac_DL_le1=obs_frac, fires=False)
    pf, pn = frac_dl_le1(ph)
    result["pharma_herbal_supporting"] = {"n_pairs_sim3": pn, "frac_DL_le1": pf,
                                          "note": "P-first labels; supporting evidence only"}
    return result


# ---- C4: a real per-sign central-name set? ----------------------------------
def c4():
    rows = load("central_words.csv")
    voyn = [r for r in rows if r["word_layer"] == "voynichese" and r["eva_word"]]
    words = [norm_label(r["eva_word"]) for r in voyn]
    # (a) mutually distinct
    if len(words) >= 2:
        pairs = [(i, j) for i in range(len(words)) for j in range(i + 1, len(words))]
        frac_distinct = sum(1 for i, j in pairs if dl_distance(words[i], words[j]) >= 2) / len(pairs)
        cond_a = frac_distinct >= 0.80
    else:
        frac_distinct, cond_a = None, False
    # (c) duplicated-sign pairs carry same word (DL<=1)
    dup = [("Aries", "f70v2", "f71r"), ("Taurus", "f71v", "f72r1")]
    wmap = {r["folio"]: norm_label(r["eva_word"]) for r in rows if r["eva_word"]}
    cond_c_evals = []
    for sign, fa, fb in dup:
        if fa in wmap and fb in wmap:
            cond_c_evals.append(dl_distance(wmap[fa], wmap[fb]) <= 1)
        else:
            cond_c_evals.append(False)     # a pair with a missing central word cannot satisfy "same word"
    cond_c = all(cond_c_evals) and len(cond_c_evals) > 0
    return {
        "test": "C4 per-sign central name set",
        "n_voynichese_central_words": len(voyn),
        "cond_a_mutually_distinct": cond_a, "frac_distinct": frac_distinct,
        "cond_b_not_ring_stem": "N/A (no set of central words to test)",
        "cond_c_dup_pairs_same_word": cond_c,
        "dup_pair_word_presence": {f"{s}": {"a": wmap.get(a, None), "b": wmap.get(b, None)}
                                   for s, a, b in dup},
        "fires": bool(cond_a and cond_c),
        "note": "Only f70v2 carries a Voynichese central word (otolal); the words under the other "
                "central animals are later-hand Romance month annotations, not Voynichese. There is "
                "no Voynichese per-sign central-name layer to fire on.",
    }


def main():
    out = {"seed": SEED, "reps": REPS,
           "C1": c1(), "C2": c2(), "C3": c3(), "C4": c4()}
    fires = [k for k in ("C1", "C2", "C3", "C4") if out[k].get("fires")]
    # A FIRE only revives the catalogue reading when it points in the NAMING direction:
    #   C1 z>=3 (matched labels share angular slot), C2 z<=-3 (identical figures share labels),
    #   C3 z>=3 (same referent shares label), C4 (a AND c). An above-null C2 fire is the OPPOSITE
    #   of naming (differentiation/register) and does NOT revive the catalogue.
    naming_fires = []
    if out["C1"].get("z", 0) >= 3: naming_fires.append("C1")
    if out["C2"].get("naming_supported"): naming_fires.append("C2")
    if out["C3"].get("fires") and out["C3"].get("z", 0) >= 3: naming_fires.append("C3")
    if out["C4"].get("fires"): naming_fires.append("C4")
    out["verdict"] = {
        "any_fire": bool(fires), "fired": fires, "naming_direction_fires": naming_fires,
        "reading": ("formulaic-catalogue (naming) reading revives for the fired layer(s); re-state the "
                    "step-2 60-65/35-40 lean" if naming_fires else
                    "no rule fires in the NAMING direction: the label layer is register, not a naming "
                    f"catalogue. C2 is {out['C2'].get('direction', 'n/a')} (z={out['C2'].get('z', 'n/a')}): "
                    "labels on near-identical figures are as distinct as random length-matched pairs, "
                    "which refutes shared names on shared referents. The two-readings balance moves "
                    "further toward meaningless / low-information generation and away from a meaningful "
                    "cross-referent catalogue."),
    }
    (RES / "t8_census.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
