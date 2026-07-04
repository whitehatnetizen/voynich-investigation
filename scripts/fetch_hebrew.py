"""Add Hebrew, the paradigm ABJAD, as a comparison language.

The T3 obfuscation result (vowel-drop + verbose + affix) reproduced the Voynich's low h2 and
narrow word length. Hebrew is the real-world analogue: an abjad whose normal writing OMITS
vowels, so consonantal Hebrew is naturally short and (plausibly) lower-entropy than a
vowel-full alphabet. Does a real natural abjad already sit closer to the Voynich than our six
vowel-full European languages do? That is a much fairer "is it a language" comparison than
Latin/German.

Source: Sefaria API v3 (public, CC-BY-SA), version=hebrew — the Masoretic Tanakh. We take the
Torah (5 books), flatten verses, strip HTML, strip ALL combining marks (niqqud vowel-points +
cantillation = Unicode category M), and keep only Hebrew consonantal letters. That yields the
KTIV (consonantal skeleton) — the true abjad, which is the point. Word breaks fall out of the
shared cleaner downstream (split on non-letter), exactly as for every other series.

Output: data/texts/hebrew/raw/<book>.txt + data/texts/hebrew/sources.md
"""
import json
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

import regex as re

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "data" / "texts" / "hebrew" / "raw"
API = "https://www.sefaria.org/api/v3/texts/{book}?version=hebrew"
BOOKS = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]


def flatten(x):
    out = []
    if isinstance(x, list):
        for e in x:
            out += flatten(e)
    elif isinstance(x, str):
        out.append(x)
    return out


def fetch_book(book):
    url = API.format(book=urllib.parse.quote(book))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (voynich-zipf research)"})
    d = json.loads(urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "replace"))
    verses = flatten(d["versions"][0]["text"])
    raw = " ".join(verses)
    raw = re.sub(r"<[^>]+>", " ", raw)                       # strip HTML/footnote tags
    raw = "".join(c for c in raw if not unicodedata.category(c).startswith("M"))  # drop niqqud/cantillation
    # keep only Hebrew-letter runs, space-separated (the consonantal skeleton)
    cleaned = re.sub(r"[^א-ת]+", " ", raw).strip()
    return cleaned


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    lines = ["# Hebrew (consonantal Torah) — abjad comparison language",
             "", "Source: Sefaria API v3, version=hebrew (Masoretic Tanakh, CC-BY-SA).",
             "Niqqud (vowel points) + cantillation stripped -> consonantal ktiv skeleton.", ""]
    total = 0
    for book in BOOKS:
        txt = fetch_book(book)
        (RAW / f"{book}.txt").write_text(txt, encoding="utf-8")
        n = len(txt.split())
        total += n
        print(f"  {book:12s} {n:7d} consonantal tokens")
        lines.append(f"- {book}: {n} tokens")
        time.sleep(0.5)
    lines.append("")
    lines.append(f"Total: {total} consonantal tokens across {len(BOOKS)} books.")
    (RAW.parent / "sources.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  TOTAL {total} tokens -> wrote raw/ + sources.md")


if __name__ == "__main__":
    main()
