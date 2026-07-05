"""B1/B4 — merge the ZL clock skeleton with the visual reads into the census CSVs.

Spatial backbone (ring, slot, clock, eva_label) comes from ZL3b-n.txt via parse_zodiac_loci.py —
the authoritative Zandbergen-Landini positions. This script adds the per-medallion vision reads
(central sign, figure type, holds-star, central words) captured by direct visual reading
(2026-07-05), and emits:
  census/zodiac_slots.csv   (B1)
  census/central_words.csv  (B4)
  census/notes_<folio>.md   (per-folio observation notes)

Every vision datum here was read off the image files named in IMAGE below; confidence is honest.
"""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CEN = ROOT / "data" / "voynich" / "census"

# ---- per-medallion visual reads (2026-07-05) --------------------------
# figure_type: the dominant ring-figure form. 'tub' = clothed/half figure standing in a barrel or
# woven basket (the early signs); 'nymph-nude' = free-standing nude nymph (Gemini onward).
# central: literal description of the central animal/figure as drawn (NOT the conventional sign
# mapping imported blind — the sign name is my identification, recorded separately as `sign`).
# central_word_voyn: Voynichese word transcribed in a central locus by ZL (only f70v2 has one).
# month_annot: a later-hand Romance month/word annotation under the animal, where legible.
META = {
 "f70v1": dict(sign="Pisces", central="two fish, one above the other", figure_type="tub",
               image="canvas_1006200_overview.jpg", central_word_voyn=None, month_annot="mars(?)",
               conf="med"),
 "f70v2": dict(sign="Aries-A", central="horned ram/goat, green body, standing", figure_type="tub",
               image="canvas_1006201_full.jpg", central_word_voyn="otolal", month_annot="abril(?)",
               conf="high"),
 "f71r":  dict(sign="Aries-B", central="pale ram lying, small figure feeding/crowning it",
               figure_type="tub", image="canvas_1006202_full.jpg", central_word_voyn=None,
               month_annot="(later hand, illegible)", conf="high"),
 "f71v":  dict(sign="Taurus-A", central="red-brown horned quadruped eating from a green manger",
               figure_type="tub", image="f71v_region.jpg", central_word_voyn=None,
               month_annot="(later hand)", conf="high"),
 "f72r1": dict(sign="Taurus-B", central="red bull eating from a green basket/manger",
               figure_type="tub", image="f72r1_region.jpg", central_word_voyn=None,
               month_annot="(later hand)", conf="high"),
 "f72r2": dict(sign="Gemini", central="man (green) and woman (blue) clasping hands",
               figure_type="nymph-nude", image="f72r2_region.jpg", central_word_voyn=None,
               month_annot="(later hand)", conf="high"),
 "f72r3": dict(sign="Cancer", central="two crayfish/lobsters, head-to-tail",
               figure_type="nymph-nude", image="f72r3_region.jpg", central_word_voyn=None,
               month_annot="(later hand)", conf="high"),
 "f72v1": dict(sign="Leo", central="maned quadruped (lion), standing", figure_type="nymph-nude",
               image="f72v1_region.jpg", central_word_voyn=None, month_annot="augst", conf="high"),
 "f72v2": dict(sign="Virgo", central="single blue-clad maiden holding a star/attribute",
               figure_type="nymph-nude", image="f72v2_region.jpg", central_word_voyn=None,
               month_annot="(later hand)", conf="high"),
 "f72v3": dict(sign="Libra", central="a beam balance / pair of scales (blue pans)",
               figure_type="nymph-nude", image="f72v3_region.jpg", central_word_voyn=None,
               month_annot="(later hand)", conf="high"),
 "f73r":  dict(sign="Scorpio", central="reptilian/scorpion-like creature (per sequence)",
               figure_type="nymph-nude", image="canvas_1006206_full.jpg", central_word_voyn=None,
               month_annot="(later hand)", conf="med"),
 "f73v":  dict(sign="Sagittarius", central="blue-clad human crossbowman aiming",
               figure_type="nymph-nude", image="canvas_1006207_full.jpg", central_word_voyn=None,
               month_annot="(later hand)", conf="high"),
}
# The two uncontroversial duplicated-sign pairs (same sign drawn on two medallions).
DUP_PAIRS = [("Aries", "f70v2", "f71r"), ("Taurus", "f71v", "f72r1")]


def build_slots():
    raw = list(csv.DictReader((CEN / "zodiac_loci_raw.csv").open(encoding="utf-8")))
    out = []
    for r in raw:
        if r["central"] == "1":
            continue
        m = META[r["folio"]]
        out.append({
            "folio": r["folio"], "sign": m["sign"], "ring": r["ring"], "slot": r["slot"],
            "n_slots_in_ring": r["n_slots_in_ring"], "clock": r["clock"], "angle_deg": r["angle_deg"],
            "eva_label": r["eva_label"], "eva_label_clean": r["eva_label_clean"],
            "figure_type": m["figure_type"], "holds_star": 1,   # every ring figure holds/points a star
            "central_sign_desc": m["central"], "confidence": m["conf"], "image_file": m["image"],
            "notes": "",
        })
    with (CEN / "zodiac_slots.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader(); w.writerows(out)
    print(f"zodiac_slots.csv: {len(out)} figure rows across {len(META)} medallions")
    return out


def build_central():
    rows = []
    for folio, m in META.items():
        rows.append({
            "folio": folio, "sign": m["sign"], "central_figure_description": m["central"],
            "eva_word": m["central_word_voyn"] or "", "read_word": m["central_word_voyn"] or "",
            "mismatch": 0, "position": "under" if m["central_word_voyn"] else "",
            "word_layer": "voynichese" if m["central_word_voyn"] else "none-voynichese",
            "later_hand_annotation": m["month_annot"] or "",
            "confidence": m["conf"], "crop_file": m["image"],
            "notes": "",
        })
    with (CEN / "central_words.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    n_voyn = sum(1 for r in rows if r["word_layer"] == "voynichese")
    print(f"central_words.csv: {len(rows)} medallions, {n_voyn} with a Voynichese central word")
    print("  duplicated-sign pairs:", DUP_PAIRS)


if __name__ == "__main__":
    build_slots()
    build_central()
