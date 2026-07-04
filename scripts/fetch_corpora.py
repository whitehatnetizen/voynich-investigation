"""Phase 0b — download public-domain prose corpora for the six languages.

Primary text per language (first entry) mirrors the video (one text, trimmed to 30k).
Extra entries are kept for the Phase-2 bootstrap. All from Project Gutenberg plain text.
Raw bodies (Gutenberg header/footer stripped) -> data/texts/<lang>/raw/<id>.txt
"""
import time
import urllib.request
from pathlib import Path

import textkit

HERE = Path(__file__).resolve().parent
TDIR = HERE.parent / "data" / "texts"

# lang code -> list of (gutenberg_id, short title). First = primary (prose, not verse).
CORPUS = {
    "english": [(1342, "Pride and Prejudice — Austen"),
                (2701, "Moby-Dick — Melville")],
    "french":  [(5097, "Vingt mille lieues sous les mers — Verne"),
                (800, "Le tour du monde en 80 jours — Verne")],
    "spanish": [(2000, "Don Quijote — Cervantes"),
                (49836, "Niebla — Unamuno")],
    "italian": [(45334, "I promessi sposi — Manzoni"),
                (38720, "L'amore che torna — Zuccoli")],
    # Effi Briest first (95k tok); Werther is only ~18k, too short to trim to 30k alone.
    "german":  [(5323, "Effi Briest — Fontane"),
                (2407, "Die Leiden des jungen Werther — Goethe")],
    # Latin: the complete De Bello Gallico across its two Gutenberg files (same author /
    # work, pure Latin). Books I-IV alone are <30k; with V-VIII the work clears 30k.
    # Gutenberg's other Latin texts carry English notes inline, which would contaminate.
    "latin":   [(218, "De Bello Gallico I-IV — Caesar"),
                (18837, "De Bello Gallico V-VIII — Caesar")],
}

URL = "https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt"


def fetch(gid: int) -> str:
    req = urllib.request.Request(URL.format(id=gid), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")


def main():
    lines = ["# Corpus sources (Project Gutenberg)", ""]
    for lang, items in CORPUS.items():
        raw_dir = TDIR / lang / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        for gid, title in items:
            body = textkit.strip_gutenberg(fetch(gid))
            (raw_dir / f"{gid}.txt").write_text(body, encoding="utf-8")
            ntok = len(textkit.clean_tokens(body))
            tag = "primary" if (gid, title) == items[0] else "extra"
            print(f"  {lang:8s} {gid:6d} {tag:7s} {ntok:7d} tok  {title}")
            lines.append(f"- **{lang}** ({tag}) — Gutenberg #{gid}: {title} — {ntok} tokens")
            time.sleep(1)  # be polite to Gutenberg
    (TDIR / "sources.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  wrote {TDIR / 'sources.md'}")


if __name__ == "__main__":
    main()
