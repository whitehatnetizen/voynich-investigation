"""Shared text utilities — identical cleaning applied to languages, controls and Voynich.

Cleaning mirrors the video ("strip punctuation, lowercase, split into arrays") but is
unicode-aware so accents/umlauts in French/Spanish/Italian/German/Latin survive:
lowercase -> replace every non-letter (Unicode \\p{L}) run with a space -> split.

Note: this also splits elisions (French "l'amour" -> "l","amour"), matching the video's
"strip punctuation" step. A keep-apostrophe variant is a Phase-2 sensitivity test.
"""
import regex as re

_NONLETTER = re.compile(r"[^\p{L}]+", re.UNICODE)

GUT_START = re.compile(r"\*\*\*\s*START OF (THE|THIS) PROJECT GUTENBERG.*?\*\*\*", re.S)
GUT_END = re.compile(r"\*\*\*\s*END OF (THE|THIS) PROJECT GUTENBERG.*?\*\*\*", re.S)


def strip_gutenberg(text: str) -> str:
    """Drop the Project Gutenberg license header and footer, keep the body."""
    m = GUT_START.search(text)
    if m:
        text = text[m.end():]
    m = GUT_END.search(text)
    if m:
        text = text[:m.start()]
    return text


def clean_tokens(text: str) -> list[str]:
    """Lowercase, split on any non-letter run, drop empties."""
    text = text.lower()
    return [t for t in _NONLETTER.split(text) if t]


def trim(tokens: list[str], n: int) -> list[str]:
    """Take the first n tokens (raises if too few, so we never silently under-sample)."""
    if len(tokens) < n:
        raise ValueError(f"only {len(tokens)} tokens, need {n}")
    return tokens[:n]
