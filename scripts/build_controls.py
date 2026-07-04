"""Phase 1/2b — build the control texts.

uniform_pool : the video's forgery control. Build ~1,000 fake words from random
               prefix+root+suffix, then sample UNIFORMLY to 30,000 tokens. Expected to
               flatline then fall off a cliff at rank ~1,000.

monkey       : the honest null (Phase 2b). Random characters drawn from a small alphabet
               WITH a space, space-probability tuned so mean word length matches the
               natural-language set (~5). Expected to PASS Zipf — which is the whole point.

Determinism: seeded RNG so results are reproducible (Date/Random are fine in plain
Python here; only the workflow runtime forbids them).

Outputs: data/tokens/uniform_pool.txt , data/tokens/monkey.txt  (each exactly N tokens)
"""
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "tokens"
N = 30000
POOL_SIZE = 1000
SEED = 1492  # year-ish; any fixed value, just for reproducibility

PREFIXES = ["qo", "ch", "sh", "ok", "ot", "da", "ai", "po", "ke", "yt", "or", "al"]
ROOTS = ["aiin", "edy", "ody", "eey", "ain", "dy", "chy", "kee", "olo", "ar", "or", "al",
         "ee", "oke", "che", "tho", "she", "dar", "eo", "yk"]
SUFFIXES = ["", "y", "n", "s", "ol", "dy", "in", "r", "m", "l", "iin", "ey"]


def build_uniform_pool(rng: random.Random) -> list[str]:
    pool = set()
    while len(pool) < POOL_SIZE:
        w = rng.choice(PREFIXES) + rng.choice(ROOTS) + rng.choice(SUFFIXES)
        pool.add(w)
    pool = sorted(pool)
    return [rng.choice(pool) for _ in range(N)]  # uniform draw -> ~equal frequencies


def build_monkey(rng: random.Random, mean_len: float = 5.0) -> list[str]:
    # random chars + space; P(space) = 1/(mean_len+1) gives ~mean_len char words.
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    p_space = 1.0 / (mean_len + 1.0)
    words, cur = [], []
    while len(words) < N:
        if rng.random() < p_space:
            if cur:
                words.append("".join(cur)); cur = []
        else:
            cur.append(rng.choice(alphabet))
    return words[:N]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    up = build_uniform_pool(rng)
    (OUT / "uniform_pool.txt").write_text("\n".join(up), encoding="utf-8")
    print(f"  uniform_pool : {len(up)} tokens, {len(set(up))} types")
    mk = build_monkey(random.Random(SEED + 1))
    (OUT / "monkey.txt").write_text("\n".join(mk), encoding="utf-8")
    print(f"  monkey       : {len(mk)} tokens, {len(set(mk))} types")


if __name__ == "__main__":
    main()
