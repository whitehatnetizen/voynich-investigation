"""Parse ZL3b-n.txt zodiac loci into a ring/clock skeleton for the T8 census (B1/C1).

The ZL (Zandbergen-Landini) EVA transcription records, for every zodiac label and circular band,
its clock-face position <!HH:MM> and its locus group. Label loci (@Lz/&Lz) carry one figure's
label; circular loci (@Cc) carry a running ring-text band. A run of label loci bounded by circular
bands (or the folio start/end) is one physical ring of figures. This is the authoritative spatial
assignment B1 asks for; the vision pass verifies it and adds figure attributes.

Output: data/voynich/census/zodiac_loci_raw.csv  (one row per label locus = one figure)
  folio, ring, slot, n_slots_in_ring, clock, angle_deg, eva_label, eva_label_clean, n_tokens, central
Plus a small summary of ring counts + circular-band counts per folio.
"""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZL = ROOT / "data" / "voynich" / "ZL3b-n.txt"
OUT = ROOT / "data" / "voynich" / "census"
OUT.mkdir(parents=True, exist_ok=True)

ZODIAC = ["f70v1", "f70v2", "f71r", "f71v", "f72r1", "f72r2", "f72r3",
          "f72v1", "f72v2", "f72v3", "f73r", "f73v"]

LOCUS_RE = re.compile(r"^<(f\w+?)\.(\d+),([@&])(\w+)>\s*(.*)$")
CLOCK_RE = re.compile(r"<!(\d{2}):(\d{2})>")


def clock_to_angle(h, m):
    """12:00 -> 0 deg (top), clockwise. 3:00 -> 90, 6:00 -> 180, 9:00 -> 270."""
    return ((h % 12) * 30 + m * 0.5) % 360


def clean_label(s):
    """Strip ZL editorial markup, keep glyph stream. Join multi-token label with a space."""
    s = re.sub(r"<![^>]*>", "", s)          # inline comments like <!long gap>
    s = re.sub(r"\{[^}]*\}", "", s)          # {c@162;h} alternate/special
    s = re.sub(r"@\d+;", "", s)              # @197; special glyph codes
    s = re.sub(r"\[([^:\]]*):[^\]]*\]", r"\1", s)  # [ir:is] -> take first alt
    s = s.replace("'", "").replace("?", "")
    return s


def parse():
    text = ZL.read_text(encoding="utf-8", errors="replace").splitlines()
    # collect loci per folio in file order
    per_folio = {f: [] for f in ZODIAC}
    for line in text:
        m = LOCUS_RE.match(line.strip())
        if not m:
            continue
        folio, idx, marker, ltag, rest = m.groups()
        if folio not in per_folio:
            continue
        # extract clock (first HH:MM in rest, before the token stream)
        cm = CLOCK_RE.search(rest)
        clock = f"{cm.group(1)}:{cm.group(2)}" if cm else None
        angle = clock_to_angle(int(cm.group(1)), int(cm.group(2))) if cm else None
        # token stream = rest with the leading clock comment removed
        toks_raw = CLOCK_RE.sub("", rest, count=1).strip()
        per_folio[folio].append({
            "idx": int(idx), "marker": marker, "ltag": ltag,
            "clock": clock, "angle": angle, "raw": toks_raw,
            "is_label": ltag.startswith("L"), "is_circ": ltag.startswith("C"),
        })

    rows = []
    summary = []
    for folio in ZODIAC:
        loci = per_folio[folio]
        # ring segmentation: each @-marked label locus starts a new ring; &-marked continue.
        # circular (C) loci act as separators and are counted, not slotted.
        rings = []            # list of lists of label loci
        cur = None
        n_circ = 0
        central = []          # label loci with no clock => candidate central word
        for lc in loci:
            if lc["is_circ"]:
                n_circ += 1
                cur = None     # a band closes the current ring
                continue
            if not lc["is_label"]:
                cur = None
                continue
            if lc["angle"] is None:
                central.append(lc)     # no clock -> not a ring slot (central/other)
                cur = None
                continue
            if lc["marker"] == "@" or cur is None:
                cur = []
                rings.append(cur)
            cur.append(lc)
        # emit
        for ri, ring in enumerate(rings, start=1):
            ordered = sorted(ring, key=lambda x: x["angle"])
            n = len(ordered)
            for slot, lc in enumerate(ordered, start=1):
                rows.append({
                    "folio": folio, "ring": ri, "slot": slot, "n_slots_in_ring": n,
                    "clock": lc["clock"], "angle_deg": round(lc["angle"], 1),
                    "eva_label": lc["raw"], "eva_label_clean": clean_label(lc["raw"]),
                    "n_tokens": len(clean_label(lc["raw"]).replace(",", " ").split()),
                    "central": 0,
                })
        for lc in central:
            rows.append({
                "folio": folio, "ring": 0, "slot": 0, "n_slots_in_ring": 0,
                "clock": "", "angle_deg": "", "eva_label": lc["raw"],
                "eva_label_clean": clean_label(lc["raw"]),
                "n_tokens": len(clean_label(lc["raw"]).replace(",", " ").split()), "central": 1,
            })
        summary.append((folio, [len(r) for r in rings], n_circ, len(central)))

    with (OUT / "zodiac_loci_raw.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["folio", "ring", "slot", "n_slots_in_ring", "clock",
                                           "angle_deg", "eva_label", "eva_label_clean",
                                           "n_tokens", "central"])
        w.writeheader()
        w.writerows(rows)

    print(f"wrote {OUT/'zodiac_loci_raw.csv'}  ({len(rows)} rows)")
    print(f"\n{'folio':8} {'ring sizes (outer->inner)':28} {'C-bands':8} central")
    for folio, ringsizes, n_circ, n_central in summary:
        print(f"{folio:8} {str(ringsizes):28} {n_circ:<8} {n_central}")


if __name__ == "__main__":
    parse()
