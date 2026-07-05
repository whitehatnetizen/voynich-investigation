"""Red-team of Timm's SelfCitationTextgenerator (github.com/TorstenTimm/SelfCitationTextgenerator).

Scores the repository's shipped deterministic sample (seed 19, 1200 lines, ~10.8k tokens) through
OUR fingerprint harness, size-matched against the real Voynich and our U2 generator regenerated at
the same token count. Three questions:

  1. Does Timm's generator land on the Voynich fingerprint (h2, word lengths, Zipf, types,
     copy signatures, word order)?
  2. Does it reproduce the suffix->prefix affix agreement (t3) that OUR generator misses?
     (His output has real line structure, so the within-line statistic is directly computable.)
  3. Where does it differ, and is the difference the hand-tuning (his ~20 parameters + hard-coded
     VMS tables) or the mechanism?

No Java runtime is present, so the shipped sample is used as-is; it is the exact output his
config.properties documents (pseudo RNG, seed 19). Size-matching at n=10,832 keeps n-sensitive
metrics (types, Zipf tail, order_frac) comparable.

Run: python scripts/timm_generator_eval.py  ->  prints a table; writes results/timm_generator_eval.json
"""
import json
import random
from collections import defaultdict
from pathlib import Path

import numpy as np

import seriesio as S
import generate_model as GM
import generation_tournament as GT
from currier_split import self_citation
from word_syntax import analyse as word_analyse
from t3_syntax_hunt import agreement, suf, pre

RES = S.ROOT / "results"
TIMM = S.ROOT / "data" / "reference" / "SelfCitationTextgenerator" / "executable" / "generate" / "generated_text.txt"
STRUCT = S.ROOT / "data" / "voynich" / "eva_structured.jsonl"
SEED = 1492


def load_timm():
    lines = []
    for raw in TIMM.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        lines.append(raw.split())
    return lines


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


def typeset(tokens, per_line):
    return [tokens[i:i + per_line] for i in range(0, len(tokens), per_line)]


def u2_at(n, voy):
    """Regenerate the tournament's U2 (W=10, p_copy=0.2, overlap=0.68) at token count n."""
    rng = np.random.default_rng(SEED)
    mk = GM.fit_markov(voy)
    cont = GT.fit_cont(mk)
    GT.VOY_LENS = np.array([len(w) for w in voy])
    sizes = GT._scale_sizes([10889, 6386, 3477, 2141, 1167], n)
    out = GT.gen_u2(mk, cont, rng, sizes, W=10, p_copy=0.2, overlap=0.68)
    return out[0] if isinstance(out, tuple) else out


def stats(tokens):
    ev = GM.evaluate(tokens)
    sc = self_citation(tokens, random.Random(SEED))
    wa = word_analyse(tokens, random.Random(SEED))
    return {"h2_cross": ev["h2_cross_bits"], "wordlen_mean": ev["wordlen_mean"],
            "wordlen_std": ev["wordlen_std"], "zipf_slope": ev["zipf_slope"],
            "n_types": ev["n_types"], "sc_d1": sc["excess_d1"], "sc_grad": sc["gradient_real"],
            "order_frac": wa["order_frac"], "adj_repeat": wa["adjacent_repeat_rate"]}


def main():
    timm_lines = load_timm()
    timm = [t for ln in timm_lines for t in ln]
    n = len(timm)
    voy_full = S.load_tokens("voynich_eva")
    voy = voy_full[:n]
    v_lines = voynich_lines(n)
    u2 = u2_at(n, voy_full)
    per_line = max(2, round(n / len(timm_lines)))
    u2_lines = typeset(u2, per_line)

    rows = {"Voynich": (voy, v_lines), "Timm sample": (timm, timm_lines), "our U2": (u2, u2_lines)}
    out = {"_meta": {"n_tokens": n, "timm_source": "shipped sample, pseudo RNG seed 19",
                     "u2_config": {"W": 10, "p_copy": 0.2, "overlap": 0.68},
                     "note": "all series size-matched at n; agreement = suffix2->prefix2 MI, "
                             "within-line shuffle null, edit-distance<=1 pairs excluded"}}
    for name, (toks, lns) in rows.items():
        st = stats(toks)
        ag = agreement(lns, suf, pre, exclude_copies=True)
        st["affix_agreement"] = ag
        out[name] = st

    keys = ["h2_cross", "wordlen_mean", "wordlen_std", "zipf_slope", "n_types",
            "sc_d1", "sc_grad", "order_frac", "adj_repeat"]
    print(f"  size-matched at n={n} tokens\n")
    print(f"  {'metric':13s} " + "".join(f"{k:>13s}" for k in rows))
    for k in keys:
        print(f"  {k:13s} " + "".join(f"{out[nm][k]:>13} " for nm in rows))
    print("\n  affix agreement (suffix->prefix, copies excluded):")
    for nm in rows:
        print(f"    {nm:12s} {json.dumps(out[nm]['affix_agreement'])}")

    RES.mkdir(exist_ok=True)
    (RES / "timm_generator_eval.json").write_text(json.dumps(out, indent=2, default=float),
                                                  encoding="utf-8")
    print(f"\n  wrote {RES / 'timm_generator_eval.json'}")


if __name__ == "__main__":
    main()
