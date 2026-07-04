"""Shared loaders for Phase 2."""
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
TOK = ROOT / "data" / "tokens"

LANGUAGES = ["english", "french", "spanish", "italian", "german", "latin"]
N = 30000


def load_tokens(name: str, full: bool = False) -> list[str]:
    suf = ".full.txt" if full else ".txt"
    return [t for t in (TOK / f"{name}{suf}").read_text(encoding="utf-8").split("\n") if t]


def rank_freq(tokens):
    counts = np.array(sorted(Counter(tokens).values(), reverse=True), dtype=float)
    ranks = np.arange(1, len(counts) + 1, dtype=float)
    return ranks, counts


def signature(tokens, R: int = 200) -> np.ndarray:
    """log10 relative-frequency at ranks 1..R (padded with the last value if short).
    All series share N tokens, so relative freq = count / N is directly comparable."""
    _, counts = rank_freq(tokens)
    rel = counts / len(tokens)
    v = np.log10(rel[:R])
    if len(v) < R:
        v = np.concatenate([v, np.full(R - len(v), v[-1])])
    return v
