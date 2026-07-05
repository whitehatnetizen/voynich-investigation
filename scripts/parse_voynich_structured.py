"""Phase 1 (mechanism) — structured re-parse of the Voynich, keeping position + metadata.

The flat parse in fetch_voynich.py threw away everything but the token order. The raw IVTFF
(data/voynich/ZL3b-n.txt) carries far more, and we need it for the slot-grammar / positional
work: folio, section, line number, paragraph position, position-in-line, Currier language
(A/B), hand, quire.

Discoveries driving this parser (see scripts/_inspect_format.py):
  * Page header  <f1r>  <! $Q=A $P=A $I=H $L=A $H=1 ...>  gives per-page variables:
      $I = illustration/section code (H herbal, A astronomical, Z zodiac, B biological,
           C cosmological, P pharmaceutical, S stars/recipes, T text-only)  <- authoritative
      $L = Currier language (A/B),  $H = Lisa Fagin Davis hand,  $Q = quire.
  * Data line  <f1r.1,@P0>  <%>fachys.ykal...  gives folio, line number, and a locus
      qualifier: @/* = paragraph-first line, + = continuation, = = paragraph-last/label line.
  * {..} ligatures (439 occ) represent single complex glyphs; the OLD parser left the braces
      in the token. Here we flatten to the inner letters and strip @codes/apostrophes, so the
      EVA alphabet is clean. (For the evaG segmentation in Phase 2, braces are a natural
      single-glyph hint; recorded conceptually, not needed for the flat token here.)

Cleaning otherwise mirrors fetch_voynich.py exactly (ALT [a:b]->a, drop <...>, @nnn;, *?!,
split on . and ,).

Outputs:
  data/voynich/eva_structured.jsonl   one JSON row per token (the new asset)
  data/voynich/eva_tokens_clean.txt   flat token list from the SAME clean pass (for diffing
                                       against the old eva_tokens.txt before we adopt it)
  data/voynich/structured_meta.json   summary counts (Gate 1 sanity)
"""
import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDIR = HERE.parent / "data" / "voynich"
SRC = VDIR / "ZL3b-n.txt"

ALT = re.compile(r"\[([^:\]]*):[^\]]*\]")     # [cth:oto] -> cth
BRACE = re.compile(r"\{([^}]*)\}")            # {ikh} -> ikh ; {c@132;h} -> c@132;h (codes go next)
ANGLE = re.compile(r"<[^>]*>")                # <..tags..> <%> <$> <!comment>
ATCODE = re.compile(r"@\d+;?")               # @254; special-glyph code
UNCERTAIN = set("*?!")

# folio is usually f<num><r|v>[<num>] but also the Rosettes foldout "fRos"; accept f\w+
HEADER = re.compile(r"<(f\w+)>\s+<!\s*(.*?)>\s*$")
LOCUS = re.compile(r"<(f\w+)\.(\d+),([^>]*)>\s*(.*)$")
VAR = re.compile(r"\$(\w)=([^\s>]+)")

SECTION = {"H": "Herbal", "A": "Astronomical", "Z": "Zodiac", "B": "Biological",
           "C": "Cosmological", "P": "Pharmaceutical", "S": "Stars", "T": "Text-only"}
PARA_POS = {"@": "first", "*": "first", "+": "mid", "=": "last"}


def clean_payload(text: str) -> str:
    text = ALT.sub(r"\1", text)
    text = BRACE.sub(lambda m: m.group(1), text)   # flatten ligatures to inner glyphs
    text = ANGLE.sub(" ", text)
    text = ATCODE.sub("", text)
    text = text.replace("'", "")                   # ligature plume marker -> drop
    return text


def tokens_from_line(payload: str) -> list[str]:
    payload = clean_payload(payload)
    for ch in ".,":
        payload = payload.replace(ch, " ")
    raw = payload.replace("-", " ").replace("=", " ").split()
    out = []
    for tok in raw:
        t = "".join(c for c in tok if c not in UNCERTAIN).strip()
        if t:
            out.append(t.lower())
    return out


def main():
    lines = SRC.read_text(encoding="utf-8", errors="replace").splitlines()
    page = {}
    rows = []
    for line in lines:
        if not line.strip() or line.startswith("#"):
            continue
        hm = HEADER.match(line)
        if hm:
            page = dict(VAR.findall(hm.group(2)))
            continue
        lm = LOCUS.match(line)
        if not lm:
            continue
        folio, lineno, locustag, payload = lm.groups()
        qual = locustag[0] if locustag else ""
        ltype = next((c for c in locustag[1:] if c.isalpha()), "")
        toks = tokens_from_line(payload)
        n = len(toks)
        sect = SECTION.get(page.get("I", ""), "unknown")
        for i, t in enumerate(toks):
            rows.append({
                "token": t, "folio": folio, "section": sect, "line": int(lineno),
                "para_pos": PARA_POS.get(qual, "mid"), "locus_type": ltype or "?",
                "pos_in_line": i, "line_len": n,
                "is_first_in_line": i == 0, "is_last_in_line": i == n - 1,
                "currier_lang": page.get("L", "?"), "hand": page.get("H", "?"),
                "quire": page.get("Q", "?"),
            })

    # write structured JSONL
    with (VDIR / "eva_structured.jsonl").open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    # flat token list from the SAME pass (for diffing against old eva_tokens.txt)
    toks = [r["token"] for r in rows]
    (VDIR / "eva_tokens_clean.txt").write_text("\n".join(toks), encoding="utf-8")

    # summary (Gate 1)
    alphabet = Counter("".join(toks))
    meta = {
        "n_tokens": len(toks), "n_types": len(set(toks)),
        "n_folios": len(set(r["folio"] for r in rows)),
        "sections": dict(Counter(r["section"] for r in rows).most_common()),
        "currier_lang": dict(Counter(r["currier_lang"] for r in rows).most_common()),
        "hands": dict(Counter(r["hand"] for r in rows).most_common()),
        "para_pos": dict(Counter(r["para_pos"] for r in rows).most_common()),
        "alphabet_size": len(alphabet),
        "alphabet": "".join(sorted(alphabet)),
        "opening": " ".join(toks[:6]),
    }
    (VDIR / "structured_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False),
                                               encoding="utf-8")
    print(json.dumps(meta, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
