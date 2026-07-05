"""B2 join — map each vision-proposed figure (folio, ring, clock) to its ZL label.

The B2 vision agents proposed near-identical figure pairs across pages, BLIND to the text (they never
saw or used the glyph labels). This script joins each proposed figure to the nearest Zandbergen-Landini
label at its stated clock position, so the label distance C2 needs is computed from authoritative
transcription, not from anyone reading glyphs off the scan. Angular residual (deg between the agent's
stated clock and the matched label's ZL clock) is recorded as a join-quality flag.

Input:  data/voynich/census/b2_raw/*.json   (one file per page-pair agent)
Output: data/voynich/census/nymph_matches.csv
"""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CEN = ROOT / "data" / "voynich" / "census"
RAW = CEN / "b2_raw"


def clock_to_angle(cl):
    m = re.match(r"(\d{1,2}):(\d{2})", cl.strip())
    if not m:
        return None
    h, mm = int(m.group(1)), int(m.group(2))
    return ((h % 12) * 30 + mm * 0.5) % 360


def circ(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


def load_skeleton():
    rows = [r for r in csv.DictReader((CEN / "zodiac_loci_raw.csv").open(encoding="utf-8"))
            if r["central"] == "0"]
    by_folio = {}
    for r in rows:
        by_folio.setdefault(r["folio"], []).append(
            {"ring": int(r["ring"]), "angle": float(r["angle_deg"]),
             "label": r["eva_label_clean"], "clock": r["clock"]})
    return by_folio


def nearest(by_folio, folio, clock, ring=None):
    """nearest label locus by clock angle; prefer stated ring but fall back to any ring."""
    cands = by_folio.get(folio, [])
    if not cands:
        return None, None, None
    ang = clock_to_angle(clock)
    if ang is None:
        return None, None, None
    pool = [c for c in cands if ring is None or c["ring"] == ring] or cands
    best = min(pool, key=lambda c: circ(c["angle"], ang))
    return best["label"], round(circ(best["angle"], ang), 1), best["clock"]


def main():
    by_folio = load_skeleton()
    out = []
    for jf in sorted(RAW.glob("*.json")):
        data = json.loads(jf.read_text(encoding="utf-8"))
        fa, fb = data["page_a"], data["page_b"]
        for p in data.get("pairs", []):
            la, ra, ca = nearest(by_folio, fa, p["clock_a"], p.get("ring_a"))
            lb, rb, cb = nearest(by_folio, fb, p["clock_b"], p.get("ring_b"))
            out.append({
                "folio_a": fa, "ring_a": p.get("ring_a"), "clock_a": p["clock_a"],
                "matched_clock_a": ca, "angres_a": ra, "eva_label_a": la or "",
                "folio_b": fb, "ring_b": p.get("ring_b"), "clock_b": p["clock_b"],
                "matched_clock_b": cb, "angres_b": rb, "eva_label_b": lb or "",
                "visual_similarity": p["visual_similarity"],
                "pose_a": p.get("pose_a", ""), "pose_b": p.get("pose_b", ""),
                "note": p.get("note", ""),
            })
    fields = ["folio_a", "ring_a", "clock_a", "matched_clock_a", "angres_a", "eva_label_a",
              "folio_b", "ring_b", "clock_b", "matched_clock_b", "angres_b", "eva_label_b",
              "visual_similarity", "pose_a", "pose_b", "note"]
    with (CEN / "nymph_matches.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader(); w.writerows(out)
    n3 = sum(1 for r in out if int(r["visual_similarity"]) == 3)
    hi_res = sum(1 for r in out if (r["angres_a"] or 0) > 25 or (r["angres_b"] or 0) > 25)
    print(f"nymph_matches.csv: {len(out)} pairs ({n3} at similarity-3); "
          f"{hi_res} with a >25deg clock residual (join-uncertain)")


if __name__ == "__main__":
    main()
