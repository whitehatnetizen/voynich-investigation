"""Phase 0a — parse Voynich transliteration files into clean word-token lists.

Sources (already downloaded by the caller into data/voynich/):
  - ZL3b-n.txt  : Zandbergen-Landini EVA, IVTFF 2.0 format  (PRIMARY, what the video uses)
  - voyn_101.txt: v101 transliteration                       (SECOND scheme, robustness)

Word-boundary rule (documented, drives every downstream number):
  In both files a word break is the dot '.' OR the comma ','. The comma marks a
  *less certain* break in IVTFF but is still a space; we treat '.' and ',' identically
  as token separators. Everything inside <...> (locus ids, inline tags, comments),
  lines beginning with '#', the paragraph marker <%>, special-char codes @nnn; and
  trailing line markers (- = ) are stripped. Alternate readings [a:b] resolve to the
  FIRST reading (the transliterator's preferred), matching common practice.

Output: data/voynich/<scheme>_tokens.txt (one token per line) + meta.json
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDIR = HERE.parent / "data" / "voynich"

# --- shared cleaning of one locus line's text payload ---------------------------------
ANGLE = re.compile(r"<[^>]*>")          # <f1r.1,@P0> , <%> , <!comment> , <$..>
ALT = re.compile(r"\[([^:\]]*):[^\]]*\]")  # [cth:oto] -> cth  (first alternative)
BRACE = re.compile(r"\{([^}]*)\}")      # {ikh} -> ikh ligature (flatten to inner glyphs)
ATCODE = re.compile(r"@\d+;?")          # @254;  special-glyph code
# characters that are not part of a word token in either alphabet
UNCERTAIN = set("*?!")                   # unreadable / uncertain glyph placeholders


def clean_payload(text: str) -> str:
    text = ALT.sub(r"\1", text)         # resolve alternate readings first
    text = BRACE.sub(lambda m: m.group(1), text)  # flatten {..} ligatures, don't leave braces
    text = ANGLE.sub(" ", text)         # drop all <...> tags/comments
    text = ATCODE.sub("", text)
    text = text.replace("'", "")        # ligature plume marker -> drop (was leaking as a glyph)
    return text


def tokens_from_line(payload: str, lower: bool = True) -> list[str]:
    payload = clean_payload(payload)
    # normalise every break char to a single delimiter, then split
    for ch in ".,":
        payload = payload.replace(ch, " ")
    # strip line-continuation / end markers that hug tokens
    raw = payload.replace("-", " ").replace("=", " ").split()
    out = []
    for tok in raw:
        # remove placeholder glyphs; keep the rest of the token's letters
        t = "".join(c for c in tok if c not in UNCERTAIN).strip()
        if t:
            out.append(t.lower() if lower else t)
    return out


def parse_eva(path: Path) -> list[str]:
    """ZL EVA IVTFF: keep only <locus...> data lines; payload follows the tag."""
    toks: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        # a data line starts with a locus tag like <f1r.1,...> ; page headers <f1r> have
        # no text payload after the metadata, so they yield no tokens anyway.
        if not line.startswith("<"):
            continue
        m = re.match(r"<[^>]*>\s*(.*)$", line)
        if not m:
            continue
        toks.extend(tokens_from_line(m.group(1)))
    return toks


def parse_v101(path: Path) -> list[str]:
    """v101: each line is <locus>payload with the same . , breaks.
    Review FIX-15: voyn_101.txt is NOT UTF-8 — its high bytes (0x80-0xFF) are single v101
    glyph codes. The old errors="replace" read baked 339 U+FFFD replacement characters into
    the stream. Decode latin-1 (lossless byte->codepoint). v101 is also CASE-SIGNIFICANT
    (A/a etc. are distinct glyphs), so tokens are not lowercased."""
    toks: list[str] = []
    for line in path.read_text(encoding="latin-1").splitlines():
        if not line or line.startswith("#"):
            continue
        m = re.match(r"<[^>]*>\s*(.*)$", line)
        if not m:
            continue
        toks.extend(tokens_from_line(m.group(1), lower=False))
    return toks


def main():
    jobs = [("eva", VDIR / "ZL3b-n.txt", parse_eva),
            ("v101", VDIR / "voyn_101.txt", parse_v101)]
    meta = {}
    for scheme, path, fn in jobs:
        if not path.exists():
            print(f"  [skip] {scheme}: {path.name} not found")
            continue
        toks = fn(path)
        out = VDIR / f"{scheme}_tokens.txt"
        out.write_text("\n".join(toks), encoding="utf-8")
        types = len(set(toks))
        meta[scheme] = {
            "source_file": path.name,
            "tokens": len(toks),
            "types": types,
            "type_token_ratio": round(types / len(toks), 4) if toks else None,
            "boundary_rule": "split on '.' and ','; resolve [a:b]->a; strip <...>,#,@nnn;,*?!",
        }
        print(f"  {scheme:5s}: {len(toks):6d} tokens, {types:5d} types  -> {out.name}")
    (VDIR / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"  wrote {VDIR / 'meta.json'}")


if __name__ == "__main__":
    main()
