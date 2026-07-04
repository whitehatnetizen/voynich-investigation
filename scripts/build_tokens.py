"""Phase 0c — build the analysis-ready token series.

For each of the six languages: concatenate that language's raw texts (in listed order),
clean identically, and trim to exactly N tokens. For languages whose first text already
exceeds N (English, French, Spanish, Italian, German) the N-token series therefore comes
from a single work, mirroring the video; Latin's N tokens span the two halves of the same
Caesar work.

Voynich: trim the parsed eva/v101 token lists to N as well.

Outputs:
  data/tokens/<series>.txt   (exactly N tokens, one per line)   for Phase 1
  data/tokens/<series>.full.txt (entire cleaned stream)         for Phase 2 bootstrap
  data/tokens/meta.json
"""
import json
from pathlib import Path

import textkit
from fetch_corpora import CORPUS

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TDIR = ROOT / "data" / "texts"
VDIR = ROOT / "data" / "voynich"
OUT = ROOT / "data" / "tokens"

N = 30000  # the video's length control


def lang_tokens(lang: str) -> list[str]:
    toks: list[str] = []
    for gid, _ in CORPUS[lang]:
        raw = (TDIR / lang / "raw" / f"{gid}.txt").read_text(encoding="utf-8")
        toks.extend(textkit.clean_tokens(raw))
    return toks


def _natural_key(p: Path):
    """Natural sort incl. Roman numerals in 'Liber XII'-style names (review FIX-17: plain
    lexicographic sort ordered Liber XII < XIII < XIV < XIX < XV...)."""
    import re as _re
    ROMAN = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}
    def roman_val(s):
        total, prev = 0, 0
        for ch in reversed(s.lower()):
            v = ROMAN[ch]
            total = total - v if v < prev else total + v
            prev = max(prev, v)
        return total
    parts = _re.split(r"(\d+|\b[IVXLCDM]+\b)", p.name)
    key = []
    for part in parts:
        if part.isdigit():
            key.append((1, int(part)))
        elif part and all(c in "IVXLCDM" for c in part):
            key.append((1, roman_val(part)))
        else:
            key.append((0, part))
    return key


def dir_tokens(subdir: str) -> list[str]:
    """Concatenate + clean every raw .txt under data/texts/<subdir>/raw (natural-sorted).
    Used for auxiliary series whose sources aren't in CORPUS (e.g. technical Latin)."""
    toks: list[str] = []
    raw_dir = TDIR / subdir / "raw"
    for f in sorted(raw_dir.glob("*.txt"), key=_natural_key):
        toks.extend(textkit.clean_tokens(f.read_text(encoding="utf-8")))
    return toks


# auxiliary series built from a raw dir (same shared cleaner, same 30k trim)
EXTRA = {"latin_tech": "latin_tech", "latin_nomen": "latin_nomen", "hebrew": "hebrew",
         "esperanto": "esperanto"}


def write_series(name: str, full: list[str], meta: dict):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.full.txt").write_text("\n".join(full), encoding="utf-8")
    trimmed = textkit.trim(full, N)
    (OUT / f"{name}.txt").write_text("\n".join(trimmed), encoding="utf-8")
    meta[name] = {"n": N, "full_tokens": len(full),
                  "full_types": len(set(full)), "trim_types": len(set(trimmed))}
    print(f"  {name:14s} full={len(full):7d}  trim={N}  types(30k)={len(set(trimmed)):5d}")


def main():
    meta: dict = {}
    for lang in CORPUS:
        write_series(lang, lang_tokens(lang), meta)
    for name, subdir in EXTRA.items():
        if (TDIR / subdir / "raw").exists():
            write_series(name, dir_tokens(subdir), meta)
    for scheme in ("eva", "v101"):
        f = VDIR / f"{scheme}_tokens.txt"
        if f.exists():
            toks = f.read_text(encoding="utf-8").split("\n")
            toks = [t for t in toks if t]
            write_series(f"voynich_{scheme}", toks, meta)
    (OUT / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"  wrote {OUT / 'meta.json'}")


if __name__ == "__main__":
    main()
