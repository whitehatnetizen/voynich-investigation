"""Abbreviated medieval Latin, measured for real (red-team T1.2). (2026-07-05)

The strongest form of the entropy-reference-class objection: a fifteenth-century reader's most
relevant comparison text is not printed classical prose but HEAVILY ABBREVIATED scribal Latin -
and machine-readable editions almost always expand the abbreviations silently, so the band never
contained that register. This script measures it on a real diplomatic corpus:

  CREMMA-Medieval-LAT (HTR-United), 21 Latin manuscripts of the 12th-15th centuries,
  graphemic ground-truth transcription in which "abbreviations are preserved (e.g. pro, pre,
  tironian et, 'est' etc.), as well as abbreviative signs" (their guidelines). ~58k tokens.
  https://github.com/HTR-United/CREMMA-Medieval-LAT (clone under data/reference/, gitignored).

Symbol-model sensitivity. Abbreviative signs are combining Unicode marks, so "what is one
glyph?" needs a convention. We score all three defensible ones:
  codepoints  - every NFC codepoint is a symbol (combining marks count separately);
  clusters    - every extended grapheme cluster is a symbol (base+marks = one glyph,
                closest to what the scribe drew);
  stripped    - marks removed first (lower bound; loses the abbreviation signal entirely).
Tokenisation matches textkit (lowercase, split on non-letters) except that combining marks are
kept inside words for the first two conventions - the shared cleaner would otherwise split a
word at its own abbreviation mark. Documented deviation, applied to this corpus only.

Writes results/medieval_latin_h2.json.
"""
import json
import unicodedata
from collections import Counter
from pathlib import Path

import numpy as np
import regex as re

import seriesio as S

RES = S.ROOT / "results"
SRC = S.ROOT / "data" / "reference" / "CREMMA-Medieval-LAT" / "data"
N = 30000


def H(counter):
    v = np.array(list(counter.values()), float)
    p = v / v.sum()
    return float(-(p * np.log2(p)).sum())


def h2_from_symbols(symbol_stream):
    return H(Counter(zip(symbol_stream, symbol_stream[1:]))) - H(Counter(symbol_stream))


def score(tokens, cluster=False):
    toks = tokens[:N]
    stream = "".join(toks)
    symbols = re.findall(r"\X", stream) if cluster else list(stream)
    wl = np.array([len(re.findall(r"\X", t)) if cluster else len(t) for t in toks])
    return {"n_tokens_total": len(tokens), "n_scored": len(toks),
            "h2": round(h2_from_symbols(symbols), 3),
            "alphabet": len(set(symbols)),
            "wordlen_mean": round(float(wl.mean()), 3),
            "wordlen_std": round(float(wl.std()), 3)}


def main():
    files = sorted(SRC.glob("*/*.txt"))
    if not files:
        raise SystemExit(f"no transcription files under {SRC} - clone CREMMA-Medieval-LAT first")
    raw = unicodedata.normalize("NFC", "\n".join(f.read_text(encoding="utf-8") for f in files))
    low = raw.lower()

    tok_keep = [t for t in re.split(r"[^\p{L}\p{M}]+", low) if t]
    nfd = unicodedata.normalize("NFD", low)
    stripped = "".join(c for c in nfd if not unicodedata.category(c).startswith("M"))
    tok_strip = [t for t in re.split(r"[^\p{L}]+", stripped) if t]

    out = {"_meta": {"source": "CREMMA-Medieval-LAT (HTR-United), 21 mss, 12th-15th c., "
                               "graphemic transcription with abbreviations preserved",
                     "files": len(files), "n": N,
                     "note": "h2 = conditional bigram entropy over the concatenated token "
                             "stream, same formula as the band; symbol conventions per "
                             "docstring"},
           "codepoints": score(tok_keep),
           "clusters": score(tok_keep, cluster=True),
           "stripped": score(tok_strip)}
    (RES / "medieval_latin_h2.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    for k in ("codepoints", "clusters", "stripped"):
        s = out[k]
        print(f"  {k:10s} h2={s['h2']:.3f}  alphabet={s['alphabet']:3d}  "
              f"wlen={s['wordlen_mean']:.2f}+/-{s['wordlen_std']:.2f}  n={s['n_scored']}")
    print(f"  wrote {RES / 'medieval_latin_h2.json'}")


if __name__ == "__main__":
    main()
