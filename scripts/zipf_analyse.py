"""Phase 1 — rank-frequency for every series + a naive log-log slope.

The log-log OLS slope here is the *biased* estimate (it is what eyeballing a "straight
line" approximates). It is fine for the Phase-1 reproduction check; the unbiased MLE
power-law / Zipf-Mandelbrot fits come in Phase 2 (scripts/fit_powerlaw.py).

Writes results/zipf_basic.json with, per series: n_tokens, n_types, top-10 words,
and the OLS slope + R^2 of log10(freq) vs log10(rank).
"""
import json
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
TOK = ROOT / "data" / "tokens"
RES = ROOT / "results"

SERIES = ["english", "french", "spanish", "italian", "german", "latin",
          "voynich_eva", "voynich_v101", "uniform_pool", "monkey"]


def rank_freq(tokens: list[str]):
    counts = np.array(sorted(Counter(tokens).values(), reverse=True), dtype=float)
    ranks = np.arange(1, len(counts) + 1, dtype=float)
    return ranks, counts


def ols_loglog(ranks, counts):
    x, y = np.log10(ranks), np.log10(counts)
    A = np.vstack([x, np.ones_like(x)]).T
    (slope, intercept), *_ = np.linalg.lstsq(A, y, rcond=None)
    yhat = slope * x + intercept
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot else float("nan")
    return float(slope), float(r2)


def load(name: str) -> list[str]:
    return [t for t in (TOK / f"{name}.txt").read_text(encoding="utf-8").split("\n") if t]


def main():
    RES.mkdir(parents=True, exist_ok=True)
    out = {}
    for name in SERIES:
        f = TOK / f"{name}.txt"
        if not f.exists():
            print(f"  [skip] {name}")
            continue
        toks = load(name)
        ranks, counts = rank_freq(toks)
        slope, r2 = ols_loglog(ranks, counts)
        top = Counter(toks).most_common(10)
        out[name] = {
            "n_tokens": len(toks), "n_types": int(len(counts)),
            "ols_slope": round(slope, 4), "ols_r2": round(r2, 4),
            "top10": [[w, c] for w, c in top],
        }
        print(f"  {name:14s} types={len(counts):5d}  slope={slope:+.3f}  R2={r2:.4f}")
    (RES / "zipf_basic.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"  wrote {RES / 'zipf_basic.json'}")


if __name__ == "__main__":
    main()
