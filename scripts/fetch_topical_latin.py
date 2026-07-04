"""Montemurro adjudication (2026-07-01) — fetch a multi-TOPIC Latin corpus.

The Montemurro test needs a real, strongly-topical reference: several Latin works on genuinely
DIFFERENT subjects, each treated as a "section", so we can see what section<->word clustering looks
like when the topics really are distinct. We already have military prose (Caesar, `data/texts/latin`)
and botany (Pliny, `data/texts/latin_tech`) on disk. This adds three more distinct topics:

  astronomy    — Manilius, *Astronomica*        (The Latin Library)
  agriculture  — Cato, *De Agri Cultura*         (The Latin Library)
  architecture — Vitruvius, *De architectura* I  (Latin Wikisource — ONE polite call)

Five distinct topical vocabularies (military / botany / astronomy / agriculture / architecture)
mirror the Voynich's herbal/stars/biological/cosmological spread. Cleaning proper (lowercase / split
on non-letters) is left to the SHARED textkit downstream, identical to every other series — same as
`fetch_technical_latin.py`. We only strip markup + navigation + non-Latin letters here.

Output: data/texts/latin_topical/<topic>/raw/<name>.txt  +  data/texts/latin_topical/sources.md
"""
import html as H
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import regex as re

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "data" / "texts" / "latin_topical"

WS_API = "https://la.wikisource.org/w/api.php"
TLL = "http://www.thelatinlibrary.com/"

# navigation / edit artifacts + The Latin Library boilerplate to strip before saving raw
NAV = [re.compile(r"\[\s*recensere\s*\]", re.I),
       re.compile(r"The Latin Library", re.I),
       re.compile(r"The Classics Page", re.I)]
_ANY_LETTER = re.compile(r"\p{L}", re.UNICODE)
_LATIN = re.compile(r"\p{Script=Latin}", re.UNICODE)

WORKS = [
    {"topic": "astronomy", "label": "Manilius, Astronomica (books 1-2)", "src": "tll",
     "items": ["manilius1.html", "manilius2.html"]},
    {"topic": "agriculture", "label": "Cato, De Agri Cultura", "src": "tll",
     "items": ["cato/cato.agri.html"]},
    {"topic": "architecture", "label": "Vitruvius, De architectura (liber I, Latin only)", "src": "ws",
     "items": ["De architectura/Liber I"], "keep_first_tokens": 5000},
]
# NOTE: the Wikisource "De architectura/Liber I" page appends a full ITALIAN translation in its
# back half (Latin is the first ~5,900 tokens). keep_first_tokens caps each fetched item to its
# Latin front so no Italian leaks into the architecture "section". Deterministic + reproducible.


def strip_non_latin(text: str) -> str:
    return _ANY_LETTER.sub(lambda m: m.group(0) if _LATIN.match(m.group(0)) else " ", text)


def get(url: str) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        return urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    except Exception as e:
        print(f"    FETCH FAILED {url}: {e!r}")
        return None


def clean_html(html: str) -> str:
    html = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<a\b[^>]*>.*?</a>", " ", html, flags=re.S | re.I)  # drop nav links
    txt = H.unescape(re.sub(r"<[^>]+>", " ", html))
    for pat in NAV:
        txt = pat.sub(" ", txt)
    txt = strip_non_latin(txt)
    return re.sub(r"\s+", " ", txt).strip()


def fetch_tll(item: str) -> str | None:
    r = get(TLL + item)
    return clean_html(r) if r else None


def fetch_ws(page: str, retries: int = 1) -> str | None:
    params = {"action": "parse", "page": page, "prop": "text", "format": "json", "disabletoc": 1}
    url = WS_API + "?" + urllib.parse.urlencode(params)
    for attempt in range(retries + 1):
        r = get(url)
        if r:
            try:
                d = json.loads(r)
            except Exception:
                d = {}
            if "parse" in d:
                return clean_html(d["parse"]["text"]["*"])
            print(f"    no parse payload for {page!r} (err={d.get('error', {}).get('code')})")
        if attempt < retries:
            print("    retrying Wikisource after a longer pause (rate limit?)...")
            time.sleep(20)
    return None


def toks(t: str) -> int:
    return len(re.findall(r"[^\W\d_]+", t, re.UNICODE))


def main():
    lines = ["# Multi-topic Latin corpus — Montemurro adjudication reference",
             "", "Distinct-subject Latin works, each a 'section', to benchmark real topical",
             "word<->section clustering. Military (Caesar) + botany (Pliny) come from the",
             "existing `latin` / `latin_tech` corpora; the three below are fetched here.",
             "Sources: The Latin Library (plain HTML) + Latin Wikisource parse API. Markup,",
             "navigation, and non-Latin letters stripped; shared textkit cleaning downstream.", ""]
    grand = 0
    for w in WORKS:
        raw = OUT / w["topic"] / "raw"
        raw.mkdir(parents=True, exist_ok=True)
        wtot = 0
        for item in w["items"]:
            txt = fetch_ws(item) if w["src"] == "ws" else fetch_tll(item)
            if not txt:
                continue
            cap = w.get("keep_first_tokens")
            if cap:
                words = re.findall(r"\S+", txt)[:cap]   # keep the Latin front, drop any trailing translation
                txt = " ".join(words)
            name = item.replace("/", "_").replace(".html", "") + ".txt"
            (raw / name).write_text(txt, encoding="utf-8")
            n = toks(txt)
            wtot += n
            print(f"  {w['topic']:12s} {item:30s} {n:7d} tok")
            if w["src"] == "ws":
                time.sleep(0.5)  # be polite to Wikisource
        grand += wtot
        lines.append(f"- **{w['topic']}** — {w['label']}: ~{wtot} tokens ({w['src']})")
    lines += ["", f"Total fetched: ~{grand} tokens across {len(WORKS)} topics.",
              "On-disk topics reused: military (Caesar, data/texts/latin), botany (Pliny, data/texts/latin_tech)."]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "sources.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  TOTAL fetched ~{grand} tok  ->  wrote {OUT}/ and sources.md")
    # review FIX-17: a silent partial corpus must not build — fail loudly if any topic is empty
    empty = [w["topic"] for w in WORKS if not any((OUT / w["topic"] / "raw").glob("*.txt"))]
    if empty:
        raise SystemExit(f"ERROR: topics with no fetched files: {empty} — corpus incomplete")


if __name__ == "__main__":
    main()
