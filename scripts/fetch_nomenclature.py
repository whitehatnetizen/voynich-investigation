"""Register hypothesis, part 2 — Linnaean NOMENCLATURE (a naming/labelling register).

The technical-prose test (Pliny, register_test.py) found that descriptive botanical Latin
tightens word length toward the Voynich but pushes h2 the WRONG way (up, not down) — its
rare, varied plant names inflate vocabulary and entropy. That leaves the sharper question:
does a systematic *nomenclature* — pure Linnaean binomials with recurring endings
(-us, -a, -um, -ensis, -oides, -folia, -flora) — have the constrained, repetitive character
structure that would LOWER h2 toward the Voynich's 2.43 bits? i.e. is the Voynich's
"too-predictable characters" signature what a labelling system looks like, rather than prose?

Corpus: accepted plant-kingdom (Plantae, GBIF backbone key 6) SPECIES canonical binomials
from the GBIF species search API (public, no-auth). We spread pages across the first 100k of
the taxonomy (the search endpoint's deep-paging cap) so the sample isn't dominated by a few
alphabetically-adjacent genera. Each accepted name is "Genus epithet" -> two tokens; the
shared cleaner (lowercase / split on non-letters / 30k trim) is applied downstream exactly as
for every other series, so any difference is the text, not the pipeline.

Output: data/texts/latin_nomen/raw/names.txt  +  data/texts/latin_nomen/sources.md
"""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import regex as re

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "data" / "texts" / "latin_nomen" / "raw"

API = "https://api.gbif.org/v1/species/search"
PLANTAE = 6
PER = 1000
STEP = 3000          # gap between grabbed pages -> spread across the taxonomy
MAX_OFFSET = 99000   # search endpoint deep-paging cap is 100k (offset+limit)

BINOMIAL = re.compile(r"^\p{Lu}[\p{Ll}]+ [\p{Ll}]+$", re.UNICODE)  # "Genus epithet"


def page(offset: int):
    q = {"rank": "SPECIES", "highertaxonKey": PLANTAE, "status": "ACCEPTED",
         "limit": PER, "offset": offset}
    url = API + "?" + urllib.parse.urlencode(q)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (voynich-zipf research)"})
    d = json.loads(urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "replace"))
    return d["results"]


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    seen = set()
    names = []
    for offset in range(0, MAX_OFFSET + 1, STEP):
        try:
            results = page(offset)
        except Exception as e:
            print(f"  offset {offset:6d} FAILED {e!r}")
            continue
        kept = 0
        for r in results:
            cn = (r.get("canonicalName") or "").strip()
            # keep clean two-word binomials only; dedupe exact repeats
            if BINOMIAL.match(cn) and cn not in seen:
                seen.add(cn)
                names.append(cn)
                kept += 1
        print(f"  offset {offset:6d}  +{kept:4d} binomials  (total {len(names)})")
        time.sleep(0.4)  # be polite to GBIF

    (RAW / "names.txt").write_text("\n".join(names) + "\n", encoding="utf-8")
    ntok = sum(n.count(" ") + 1 for n in names)
    src = [
        "# Botanical nomenclature corpus — Linnaean binomials (GBIF)",
        "",
        f"Source: GBIF species search API, kingdom Plantae (backbone key {PLANTAE}), "
        "rank=SPECIES, status=ACCEPTED.",
        f"Sampled {len(range(0, MAX_OFFSET + 1, STEP))} pages of {PER} spread by {STEP} across "
        f"offsets 0..{MAX_OFFSET} for genus diversity.",
        f"Kept {len(names)} distinct clean two-word binomials (~{ntok} tokens). "
        "Shared cleaning applied downstream.",
        "",
        "Note: modern binomials latinise many roots (person/place names: -ii, -ensis, "
        "-iana); this is Linnaean *nomenclature*, the labelling register, not classical prose.",
    ]
    (RAW.parent / "sources.md").write_text("\n".join(src) + "\n", encoding="utf-8")
    print(f"  kept {len(names)} binomials  (~{ntok} tokens)  ->  wrote raw/names.txt, sources.md")
    # review FIX-17: fail loudly on a silently-partial fetch (target ~30k+ binomials)
    if len(names) < 25000:
        raise SystemExit(f"ERROR: only {len(names)} binomials fetched — corpus incomplete")


if __name__ == "__main__":
    main()
