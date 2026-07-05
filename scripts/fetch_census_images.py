"""T8 step 3 census — image acquisition (Phase A of review/T8-CENSUS-PLAN.md).

Fetches the zodiac (f70v2..f73v) and pharmaceutical (f88r..f102v) subfolios from the Beinecke
MS 408 IIIF service at high resolution, region-cropping foldout leaves that share a canvas.

Beinecke Rare Book Library, Yale — MS 408, public domain, IIIF Image API 2.0.
Politeness: >=1.1s between requests, cache everything, never re-download a file that passes QA.

Two-stage use:
  python scripts/fetch_census_images.py --stage overview   # download full canvases + wide-foldout overviews
  (inspect overviews, fill REGIONS below)
  python scripts/fetch_census_images.py --stage regions    # region-crop each foldout subfolio

Outputs: data/voynich/folio_images/*.jpg  and  data/voynich/folio_images/regions.json
"""
import argparse
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VDIR = ROOT / "data" / "voynich"
IMG = VDIR / "folio_images"
IMG.mkdir(parents=True, exist_ok=True)
MANIFEST = json.loads((VDIR / "iiif_manifest.json").read_text(encoding="utf-8"))
FOLIOS = json.loads((ROOT / "dashboard" / "folios.json").read_text(encoding="utf-8"))

UA = "voynich-zipf research (contact: Beinecke public IIIF; <=1 req/s)"
DELAY = 1.15
IIIF = "https://collections.library.yale.edu/iiif/2"


def _label_text(label):
    if isinstance(label, dict):
        for v in label.values():
            if v:
                return (v[0] if isinstance(v, list) else v).strip()
        return ""
    return str(label).strip()


def canvas_table():
    """Return list of {svc, label, w, h} for every canvas in the manifest."""
    out = []
    for c in MANIFEST.get("items", []):
        label = _label_text(c.get("label", ""))
        try:
            body = c["items"][0]["items"][0]["body"]
            svc = (body.get("service") or [{}])[0]
            svcid = (svc.get("@id") or svc.get("id") or "").split("/")[-1]
        except (KeyError, IndexError):
            continue
        if svcid:
            out.append({"svc": svcid, "label": label, "w": c.get("width"), "h": c.get("height")})
    return out


CANVASES = canvas_table()


def canvases_for_leaf(leaf):
    """leaf like '70v' -> canvases whose space-stripped label contains it."""
    return [c for c in CANVASES if leaf in c["label"].replace(" ", "")]


def fetch(url, dest, min_bytes=20000):
    dest = Path(dest)
    if dest.exists() and dest.stat().st_size >= min_bytes:
        print(f"  cached {dest.name} ({dest.stat().st_size//1024}KB)")
        return False
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    data = urllib.request.urlopen(req, timeout=120).read()
    dest.write_bytes(data)
    print(f"  saved  {dest.name} ({len(data)//1024}KB)  <- {url}")
    time.sleep(DELAY)
    return True


# ---- target subfolios -------------------------------------------------------
ZODIAC = [f["folio"] for f in FOLIOS if f.get("is_zodiac")]
PHARMA = [f["folio"] for f in FOLIOS if f.get("section") == "Pharmaceutical"]


def leaf_of(folio):
    """f72r2 -> '72r'; f88v -> '88v'."""
    import re
    m = re.match(r"f(\d+)([rv])", folio)
    return m.group(1) + m.group(2)


# Physical-leaf canvas map: which canvas each leaf lives on, and whether it is a
# wide/multi-subfolio foldout that needs region crops.
def build_plan():
    plan = {}
    for folio in ZODIAC + PHARMA:
        leaf = leaf_of(folio)
        cs = canvases_for_leaf(leaf)
        plan[folio] = {"leaf": leaf, "canvases": [(c["svc"], c["label"], c["w"], c["h"]) for c in cs]}
    return plan


# ---- REGIONS: filled after inspecting overviews -----------------------------
# folio -> {"svc": id, "region": [x,y,w,h] in canvas px, "size": "2000,"}
# Single-canvas folios (one medallion per canvas) do NOT need an entry; they are
# fetched full. Only multi-subfolio foldouts need region crops.
REGIONS_FILE = IMG / "regions.json"
REGIONS = json.loads(REGIONS_FILE.read_text(encoding="utf-8")) if REGIONS_FILE.exists() else {}


def stage_overview():
    """Download every distinct canvas once. Narrow single canvases at full/2500;
    wide foldout canvases at full/2200 overview (for locating subfolio regions)."""
    plan = build_plan()
    (IMG / "census_plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    seen = set()
    for folio, info in plan.items():
        for svc, label, w, h in info["canvases"]:
            if svc in seen:
                continue
            seen.add(svc)
            wide = (w or 0) > 3600
            size = "2200," if wide else "2500,"
            tag = "overview" if wide else "full"
            dest = IMG / f"canvas_{svc}_{tag}.jpg"
            url = f"{IIIF}/{svc}/full/{size}/0/default.jpg"
            try:
                fetch(url, dest)
            except Exception as e:
                print(f"  FAIL {svc} ({label}): {e}")
    print(f"\nDistinct canvases: {len(seen)}. Plan -> census_plan.json")
    print("Wide foldouts needing region crops:")
    for c in CANVASES:
        if c["svc"] in seen and (c["w"] or 0) > 3600:
            print(f"  {c['svc']}  {c['label']!r}  {c['w']}x{c['h']}")


def stage_regions():
    """Region-crop each foldout subfolio per REGIONS (edited after inspection)."""
    if not REGIONS:
        print("REGIONS is empty. Inspect canvas_*_overview.jpg, populate regions.json, rerun.")
        return
    for folio, spec in REGIONS.items():
        svc = spec["svc"]
        x, y, w, h = spec["region"]
        size = spec.get("size", "2000,")
        dest = IMG / f"{folio}_region.jpg"
        url = f"{IIIF}/{svc}/{x},{y},{w},{h}/{size}/0/default.jpg"
        try:
            fetch(url, dest)
        except Exception as e:
            print(f"  FAIL {folio}: {e}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["overview", "regions"], default="overview")
    args = ap.parse_args()
    if args.stage == "overview":
        stage_overview()
    else:
        stage_regions()
