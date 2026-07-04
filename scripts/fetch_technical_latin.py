"""Register hypothesis: fetch a TECHNICAL Latin corpus.

The generic Latin in the set is Caesar's *De Bello Gallico* (military narrative prose).
The Voynich is largely a herbal, so the fair comparison may be specialised/technical Latin,
not generic prose. This pulls Pliny the Elder's *Naturalis Historia* botanical + medicinal
books (XII-XXVI: trees, plants, garden crops, and remedies derived from plants — the
herbal/pharmacological core) from Latin Wikisource.

Source note: The Latin Library only carries Pliny NH books 1-5 (cosmology/geography), so
Wikisource is the source for the botany span. We take the rendered HTML via the parse API,
strip tags, and remove the "[ recensere ]" section edit-links (a Wikisource navigation
artifact — left in, it would inject the token "recensere" at every section and wreck the
frequency stats). Cleaning proper (lowercase / split on non-letters / 30k trim) is left to
the SHARED textkit + build_tokens step, identical to every other series — the whole point is
that any register effect comes from the text, not from a bespoke cleaner.

Output: data/texts/latin_tech/raw/<liber>.txt  +  data/texts/latin_tech/sources.md
"""
import html as H
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import regex as re

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "data" / "texts" / "latin_tech" / "raw"

API = "https://la.wikisource.org/w/api.php"
# Roman-numeral books of the botanical/herbal span. XXVII is absent under this title on
# Wikisource, so we stop at XXVI; the span still yields ~150k tokens, ample for 30k + boot.
BOOKS = ["XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX",
         "XX", "XXI", "XXII", "XXIII", "XXIV", "XXV", "XXVI"]
TITLE = "Naturalis Historia/Liber {b}"

# navigation / edit artifacts to strip before saving raw
NAV = [re.compile(r"\[\s*recensere\s*\]", re.I)]
# letters of any script other than Latin: Pliny quotes a little Greek (~39 tok), and
# Wikisource leaks a little Cyrillic (~40 tok) — 0.05% of the stream. Drop them so the
# alphabet is like-for-like with the pure a-z generic Latin (Caesar). Documented, not hidden.
NON_LATIN_LETTER = re.compile(r"\p{L}", re.UNICODE)
_LATIN = re.compile(r"\p{Script=Latin}", re.UNICODE)


def strip_non_latin_letters(text: str) -> str:
    return NON_LATIN_LETTER.sub(lambda m: m.group(0) if _LATIN.match(m.group(0)) else " ", text)


def fetch_book(book: str) -> str | None:
    params = {"action": "parse", "page": TITLE.format(b=book),
              "prop": "text", "format": "json", "disabletoc": 1}
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace"))
    except Exception as e:
        print(f"  Liber {book:6s} FETCH FAILED: {e!r}")
        return None
    if "parse" not in d:
        print(f"  Liber {book:6s} no parse payload (title variant?)")
        return None
    html = d["parse"]["text"]["*"]
    html = re.sub(r"<style.*?</style>", " ", html, flags=re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    txt = H.unescape(html)
    for pat in NAV:
        txt = pat.sub(" ", txt)
    txt = strip_non_latin_letters(txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    lines = ["# Technical Latin corpus — Pliny the Elder, Naturalis Historia (botany/herbal)",
             "", "Source: Latin Wikisource (la.wikisource.org), parse API, HTML stripped,",
             "`[ recensere ]` edit-links removed. Shared cleaning applied downstream.", ""]
    total = 0
    for book in BOOKS:
        txt = fetch_book(book)
        if not txt:
            continue
        (RAW / f"Liber_{book}.txt").write_text(txt, encoding="utf-8")
        # rough token count for the log (final count comes from the shared cleaner)
        n = len(re.findall(r"[^\W\d_]+", txt, re.UNICODE))
        total += n
        print(f"  Liber {book:6s} {n:7d} tok")
        lines.append(f"- Liber {book}: ~{n} tokens")
        time.sleep(0.5)  # be polite to Wikisource
    lines.append("")
    fetched = len(list(RAW.glob("Liber_*.txt")))
    lines.append(f"Total: ~{total} tokens across {fetched}/{len(BOOKS)} books.")
    (RAW.parent / "sources.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  TOTAL ~{total} tok  ->  wrote raw/ and sources.md")
    # review FIX-17: a silent partial corpus must not build — fail loudly if books are missing
    if fetched < len(BOOKS):
        raise SystemExit(f"ERROR: only {fetched}/{len(BOOKS)} books fetched — corpus incomplete")


if __name__ == "__main__":
    main()
