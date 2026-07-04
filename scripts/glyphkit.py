"""Shared glyph segmentation + entropy helpers for the mechanism phase (Phases 2-4).

Glyph-vs-letter is our one soft caveat, so every character analysis runs under two
segmentations:
  eva1  one EVA character = one glyph (default; what the earlier phases used).
  evaG  benched glyphs grouped as single units: cth ckh cph cfh ch sh. These are treated
        as single characters in essentially all Voynich scholarship (the "benched gallows"
        and ch/sh ligatures). Grouping is greedy, longest-first. More aggressive groupings
        (treating the minim strings iin/aiin as single glyphs) would only STRENGTHEN the
        rigidity story; MULTIGRAPHS is a parameter so that lever is easy to pull.

For natural-language series, grouping is a no-op (these multigraphs are EVA-specific), so
evaG changes only the Voynich numbers — exactly the caveat test we want.
"""
from collections import Counter, defaultdict
from math import log2

MULTIGRAPHS = ["cth", "ckh", "cph", "cfh", "ch", "sh"]  # longest-first for greedy match


def glyphs(word: str, grouped: bool = False) -> list[str]:
    if not grouped:
        return list(word)
    out, i, n = [], 0, len(word)
    while i < n:
        for mg in MULTIGRAPHS:
            if word.startswith(mg, i):
                out.append(mg)
                i += len(mg)
                break
        else:
            out.append(word[i])
            i += 1
    return out


def H(counter) -> float:
    """Shannon entropy (bits) of a Counter / dict of counts."""
    n = sum(counter.values())
    if n == 0:
        return 0.0
    return -sum((c / n) * log2(c / n) for c in counter.values() if c)


def cond_H(pairs) -> float:
    """H(symbol | context) in bits, from an iterable of (context, symbol) pairs."""
    ctx = defaultdict(Counter)
    for c, s in pairs:
        ctx[c][s] += 1
    total = sum(sum(cc.values()) for cc in ctx.values())
    if total == 0:
        return 0.0
    return sum((sum(cc.values()) / total) * H(cc) for cc in ctx.values())
