"""U3: the U2 generator plus three habits borrowed from Timm's SelfCitationTextgenerator.

Why this exists. U2 reproduces the 17-metric fingerprint but scores ~zero on the one cross-word
structure T3 found: suffix->prefix affix agreement (Voynich z ~ 80 at 30k tokens, copies excluded).
The red-team of Timm's generator (results/timm_generator_critique.md) showed his output produces a
real fraction of that agreement mechanically (z = 5.4 at 10.8k tokens). U3 asks one question: can
U2 reach the agreement by adopting Timm's habits, WITHOUT any new parameter fitted to the
agreement statistic?

Discipline. All new constants are taken verbatim from Timm's shipped conf.properties (replace 50%,
combine+split 30% split evenly, reuse-last 10%, same-position-above 28%). U2's four dials stay
untouched (W=10, p_copy=0.2, overlap=0.68, empirical length profile). Line lengths are drawn from
the Voynich's empirical line-length distribution; the agreement null shuffles within lines, so line
geometry cannot create agreement on its own.

The three habits, in scribe terms:
  1. ending swap: after copying a word, sometimes give it the ending of another recent word.
  2. weld and cut: sometimes weld the previous short word onto this one; sometimes cut a long
     word in two and write the halves side by side.
  3. write in lines, and when copying, sometimes take the word directly above (same position,
     previous line).

Success criterion, fixed before running: affix agreement rises from U2's ~0 toward the Voynich's,
while the rest of the panel stays in U2's ballpark. Reported either way.

Run: python scripts/u3_generator.py  ->  prints a table; writes results/u3_generator.json
"""
import json
import random
from collections import Counter, defaultdict

import numpy as np

import seriesio as S
import generate_model as GM
import generation_tournament as GT
from currier_split import self_citation
from word_syntax import analyse as word_analyse
from t3_syntax_hunt import agreement, suf, pre

RES = S.ROOT / "results"
STRUCT = S.ROOT / "data" / "voynich" / "eva_structured.jsonl"
SEED = 1492
N = 30000

# Timm conf.properties, verbatim (see data/reference/SelfCitationTextgenerator/executable/):
P_ENDSWAP = 0.50      # method.morph.replace.probability=50
P_COMBINE = 0.15      # method.morph.combine_split.probability=30, split evenly
P_SPLIT = 0.15        #
P_REUSE_LAST = 0.10   # method.morph.reuse_last.probability=10
P_SAMEPOS = 0.28      # method.sourceChooser.same_position_probability=28

# U2 dials, untouched (results/generation_tournament.json _meta.u2_config):
W, P_COPY, OVERLAP = 10, 0.2, 0.68
SIZES = [10889, 6386, 3477, 2141, 1167]


def voynich_lines(n):
    rows = [json.loads(l) for l in STRUCT.read_text(encoding="utf-8").splitlines() if l.strip()]
    lm = defaultdict(list)
    for r in rows:
        lm[(r["folio"], r["line"])].append(r["token"])
    out, total = [], 0
    for key in lm:
        out.append(lm[key])
        total += len(lm[key])
        if total >= n:
            break
    return out


def typeset(tokens, line_lens, rng):
    """Cut a token stream into lines with lengths drawn from the empirical distribution."""
    lines, i = [], 0
    while i < len(tokens):
        L = int(line_lens[int(rng.integers(0, len(line_lens)))])
        lines.append(tokens[i:i + L])
        i += L
    return [l for l in lines if l]


def gen_u3(mk, cont, rng, sizes, line_lens):
    """U2's skeleton (per-section pools, copy window, Markov mutation) + Timm's three habits,
    emitting real lines."""
    pool = GT.gen_lenlock(mk, rng, sum(sizes), GT.VOY_LENS)
    freq = Counter(pool)
    types = list(freq)
    wts = np.array([freq[t] for t in types], float)
    gp = wts / wts.sum()
    order = sorted(range(len(types)), key=lambda i: -wts[i])
    pools = [[] for _ in sizes]
    mass = [0.0] * len(sizes)
    for i in order:
        z = min(range(len(sizes)), key=lambda q: mass[q])
        pools[z].append(i); mass[z] += wts[i]
    pool_prob = [(np.array(pl), wts[pl] / wts[pl].sum()) for pl in pools]
    kk = np.array([0, 1, 2]); kp = np.array(GT.KDIST) / sum(GT.KDIST)

    lines, out = [], []
    for s, m in enumerate(sizes):
        pl, pp = pool_prob[s]
        buf, cur, prev = [], [], None
        target = int(line_lens[int(rng.integers(0, len(line_lens)))])
        emitted = 0
        while emitted < m:
            copied = False
            if len(buf) >= 2 and rng.random() < P_COPY:
                copied = True
                # habit 3: the word directly above (same position, previous line)
                if prev is not None and len(cur) < len(prev) and rng.random() < P_SAMEPOS:
                    src = prev[len(cur)]
                elif rng.random() < P_REUSE_LAST:
                    src = buf[-1]
                else:
                    lo = max(0, len(buf) - W); hi = len(buf) - 1
                    src = buf[int(rng.integers(lo, hi))] if hi > lo else buf[lo]
                wd = GT.mutate(src, cont, rng, int(rng.choice(kk, p=kp)))
                if not wd:
                    wd = types[int(rng.choice(len(types), p=gp))]
            elif rng.random() < OVERLAP:
                wd = types[int(rng.choice(len(types), p=gp))]
            else:
                wd = types[int(rng.choice(pl, p=pp))]

            # habit 1: give a copied word the ending of another recent word
            if copied and len(wd) >= 4 and len(buf) >= 2 and rng.random() < P_ENDSWAP:
                donor = buf[int(rng.integers(max(0, len(buf) - W), len(buf)))]
                if len(donor) >= 2:
                    wd = wd[:-2] + donor[-2:]

            # habit 2: cut a long word in two, or weld the previous short word onto this one
            emit = [wd]
            if len(wd) >= 6 and rng.random() < P_SPLIT:
                cut = int(rng.integers(2, len(wd) - 1))
                emit = [wd[:cut], wd[cut:]]
            elif cur and len(cur[-1]) <= 4 and len(cur[-1]) + len(wd) <= 9 \
                    and rng.random() < P_COMBINE:
                welded = cur.pop() + wd
                buf.pop(); out.pop(); emitted -= 1
                emit = [welded]

            for w in emit:
                buf.append(w); out.append(w); cur.append(w); emitted += 1
                if len(cur) >= target:
                    lines.append(cur); prev = cur; cur = []
                    target = int(line_lens[int(rng.integers(0, len(line_lens)))])
        if cur:
            lines.append(cur)
    return out[:sum(sizes)], lines


def stats(tokens):
    ev = GM.evaluate(tokens)
    sc = self_citation(tokens, random.Random(SEED))
    wa = word_analyse(tokens, random.Random(SEED))
    return {"h2_cross": ev["h2_cross_bits"], "wordlen_mean": ev["wordlen_mean"],
            "wordlen_std": ev["wordlen_std"], "zipf_slope": ev["zipf_slope"],
            "n_types": ev["n_types"], "sc_d1": sc["excess_d1"], "sc_grad": sc["gradient_real"],
            "order_frac": wa["order_frac"], "adj_repeat": wa["adjacent_repeat_rate"]}


def main():
    rng = np.random.default_rng(SEED)
    voy = S.load_tokens("voynich_eva")[:N]
    v_lines = voynich_lines(N)
    line_lens = np.array([len(l) for l in v_lines if l])

    mk = GM.fit_markov(S.load_tokens("voynich_eva"))
    cont = GT.fit_cont(mk)
    GT.VOY_LENS = np.array([len(w) for w in S.load_tokens("voynich_eva")])

    u2, _ = GT.gen_u2(mk, cont, np.random.default_rng(SEED), SIZES, W, P_COPY, OVERLAP)
    u2_lines = typeset(u2, line_lens, np.random.default_rng(SEED))
    u3, u3_lines = gen_u3(mk, cont, rng, SIZES, line_lens)

    rows = {"Voynich": (voy, v_lines), "U2": (u2, u2_lines), "U3": (u3, u3_lines)}
    out = {"_meta": {"n": N, "seed": SEED,
                     "timm_constants": {"P_ENDSWAP": P_ENDSWAP, "P_COMBINE": P_COMBINE,
                                        "P_SPLIT": P_SPLIT, "P_REUSE_LAST": P_REUSE_LAST,
                                        "P_SAMEPOS": P_SAMEPOS},
                     "u2_dials": {"W": W, "p_copy": P_COPY, "overlap": OVERLAP},
                     "criterion": "affix agreement rises from U2's ~0 toward the Voynich's while "
                                  "the rest of the panel stays in U2's ballpark; no new parameter "
                                  "is fitted to the agreement statistic"}}
    for name, (toks, lns) in rows.items():
        st = stats(toks)
        st["affix_agreement"] = agreement(lns, suf, pre, exclude_copies=True)
        out[name] = st

    keys = ["h2_cross", "wordlen_mean", "wordlen_std", "zipf_slope", "n_types",
            "sc_d1", "sc_grad", "order_frac", "adj_repeat"]
    print(f"  n={N}, seed={SEED}\n")
    print(f"  {'metric':13s} " + "".join(f"{k:>12s}" for k in rows))
    for k in keys:
        print(f"  {k:13s} " + "".join(f"{out[nm][k]:>12} " for nm in rows))
    print("\n  affix agreement (suffix->prefix, copies excluded):")
    for nm in rows:
        print(f"    {nm:8s} {json.dumps(out[nm]['affix_agreement'])}")

    (RES / "u3_generator.json").write_text(json.dumps(out, indent=2, default=float),
                                           encoding="utf-8")
    print(f"\n  wrote {RES / 'u3_generator.json'}")


if __name__ == "__main__":
    main()
