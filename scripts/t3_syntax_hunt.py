"""T3 (review/INVESTIGATIONS.md) — subset syntax hunt + affix agreement. [F2 — the direct test]

The working hypothesis predicts NO subset of the running text has language-like word-order
structure; generation-by-copying builds syntax nowhere. If any subset does, the hypothesis is
genuinely hurt. Also answers the queued morphology sub-question: are the affixes
GRAMMATICAL — does a word's affix track its neighbours (agreement/government), or is it
decorative?

Prong 1 — word-order MI per subset. The word_syntax.py statistic (shuffle-corrected
  H(word|prev) reduction) per cell: section, Currier language, hand, locus type, line position.
  Cells under ~2,000 tokens skipped. Order info falls with sample size, so every cell is
  benchmarked against SIZE-MATCHED contiguous Latin prose samples (the yardstick column).

Prong 2 — affix agreement. MI(suffix2_i ; suffix2_{i+1}) for adjacent within-line pairs against
  a WITHIN-LINE shuffle (preserves each line's composition, destroys adjacency). Latin (typeset
  into the same line geometry) is the positive control: real case/number concord produces strong
  suffix-suffix MI. THE TRAP: self-citation copying produces suffix repetition at distance 1 (a
  copied word keeps its suffix), which mimics agreement — so the statistic is also computed
  EXCLUDING edit-distance<=1 pairs, and the U1-style copy-matched generator is run as the null
  text. Repeated for prefix->suffix and suffix->prefix.

Decision rule: any Voynich cell reaching ~half of same-size Latin's order info, or a
suffix-agreement z>=5 that SURVIVES the copy exclusion and exceeds the generator control ->
F2 fires. All flat -> F2 closed as thoroughly as internal statistics allow.

Writes results/t3_syntax_hunt.json + figures/t3_syntax_hunt.png.
"""
import json
import random
from collections import Counter, defaultdict
from math import log2

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from rapidfuzz.distance import DamerauLevenshtein as DL

import seriesio as S
import scribe_recipe_test as SR
from glyphkit import H, cond_H

STRUCT = S.ROOT / "data" / "voynich" / "eva_structured.jsonl"
RES = S.ROOT / "results"
FIG = S.ROOT / "figures"
SEED = 1492
NSHUF = 50
MIN_CELL = 2000
LATIN_SAMPLES = 5


# ---------------- prong 1: word-order info per subset ----------------
def order_info(tokens, nshuf=NSHUF):
    H_w = H(Counter(tokens))
    H_cond = cond_H(zip(tokens, tokens[1:]))
    shuf = []
    for rep in range(nshuf):
        arr = list(tokens)
        random.Random(SEED + rep).shuffle(arr)
        shuf.append(cond_H(zip(arr, arr[1:])))
    mu, sd = float(np.mean(shuf)), float(np.std(shuf, ddof=1))
    info = mu - H_cond
    return {"n": len(tokens), "order_info_bits": round(info, 4),
            "order_frac": round(info / H_w, 4) if H_w else 0.0,
            "z": round(info / sd, 1) if sd else None}


def latin_yardstick(n, latin_full):
    """Mean order_frac of LATIN prose at sample size n (contiguous samples)."""
    vals = []
    step = max(1, (len(latin_full) - n) // LATIN_SAMPLES)
    for k in range(LATIN_SAMPLES):
        seg = latin_full[k * step:k * step + n]
        if len(seg) < n:
            break
        vals.append(order_info(seg, nshuf=10)["order_frac"])
    return round(float(np.mean(vals)), 4) if vals else None


# ---------------- prong 2: affix agreement ----------------
def suf(t):
    return t[-2:] if len(t) >= 2 else t


def pre(t):
    return t[:2] if len(t) >= 2 else t


def pair_mi(pairs):
    n = len(pairs)
    if n == 0:
        return 0.0
    ca = Counter(a for a, _ in pairs)
    cb = Counter(b for _, b in pairs)
    cab = Counter(pairs)
    mi = 0.0
    for (a, b), c in cab.items():
        mi += (c / n) * log2((c * n) / (ca[a] * cb[b]))
    return mi


def agreement(lines_tokens, fa, fb, exclude_copies, nshuf=NSHUF):
    """MI(fa(w_i); fb(w_{i+1})) over adjacent within-line pairs, vs a within-line shuffle.
    exclude_copies: drop pairs with DL(w_i, w_{i+1}) <= 1 (the copying mimic)."""
    def build_pairs(lines):
        out = []
        for ln in lines:
            for a, b in zip(ln, ln[1:]):
                if exclude_copies and DL.distance(a, b) <= 1:
                    continue
                out.append((fa(a), fb(b)))
        return out
    real = pair_mi(build_pairs(lines_tokens))
    shuf = []
    for rep in range(nshuf):
        rr = random.Random(SEED + rep)
        sh = []
        for ln in lines_tokens:
            l2 = list(ln)
            rr.shuffle(l2)
            sh.append(l2)
        shuf.append(pair_mi(build_pairs(sh)))
    mu, sd = float(np.mean(shuf)), float(np.std(shuf, ddof=1))
    exc = real - mu
    npairs = len(build_pairs(lines_tokens))
    return {"n_pairs": npairs, "mi_real": round(real, 4), "mi_shuffle": round(mu, 4),
            "excess": round(exc, 4), "z": round(exc / sd, 1) if sd else None}


def main():
    RES.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)
    rows = [json.loads(l) for l in STRUCT.read_text(encoding="utf-8").splitlines() if l.strip()]
    P = [r for r in rows if r.get("locus_type") == "P"]
    latin_full = S.load_tokens("latin", full=True)

    # ---------- prong 1 cells ----------
    def toks(pred, source=rows):
        return [r["token"] for r in source if pred(r)]

    cells = {}
    for sec in sorted({r["section"] for r in rows}):
        cells[f"section:{sec}"] = toks(lambda r, s=sec: r["section"] == s, P)
    for cl in ("A", "B"):
        cells[f"currier:{cl}"] = toks(lambda r, c=cl: r.get("currier_lang") == c, P)
    for hd in sorted({r.get("hand") for r in rows if r.get("hand")}):
        cells[f"hand:{hd}"] = toks(lambda r, h=hd: r.get("hand") == h, P)
    cells["locus:C (circular)"] = toks(lambda r: True, [r for r in rows if r["locus_type"] == "C"])
    cells["line-initial"] = toks(lambda r: r.get("is_first_in_line"), P)
    cells["mid-line"] = toks(lambda r: not r.get("is_first_in_line") and not r.get("is_last_in_line"), P)
    cells["line-final"] = toks(lambda r: r.get("is_last_in_line"), P)
    cells["ALL running text"] = [r["token"] for r in P]

    prong1 = {}
    for name, tk in cells.items():
        if len(tk) < MIN_CELL:
            continue
        d = order_info(tk)
        d["latin_same_n_order_frac"] = latin_yardstick(len(tk), latin_full)
        d["frac_of_latin"] = round(d["order_frac"] / d["latin_same_n_order_frac"], 3) \
            if d["latin_same_n_order_frac"] else None
        prong1[name] = d

    # ---------- prong 2: affix agreement ----------
    lines_map = defaultdict(list)
    for r in P:
        lines_map[(r["folio"], r["line"])].append(r["token"])
    voy_lines = list(lines_map.values())
    n_p = len(P)

    # controls typeset into the same line geometry
    def typeset(stream):
        out, i = [], 0
        for ln in voy_lines:
            out.append(stream[i:i + len(ln)])
            i += len(ln)
        return out
    lat_lines = typeset(latin_full[:n_p])
    tab = SR.fit_tables([r["token"] for r in P])
    gen, _ = SR.scribe(tab, random.Random(SEED), n_p)
    gen_lines = typeset(gen)

    prong2 = {}
    for label, lns in [("Voynich", voy_lines), ("Latin (positive control)", lat_lines),
                       ("scribe generator (copy-matched null)", gen_lines)]:
        prong2[label] = {
            "suffix->suffix": agreement(lns, suf, suf, exclude_copies=False),
            "suffix->suffix (no copies)": agreement(lns, suf, suf, exclude_copies=True),
            "prefix->suffix (no copies)": agreement(lns, pre, suf, exclude_copies=True),
            "suffix->prefix (no copies)": agreement(lns, suf, pre, exclude_copies=True),
        }

    out = {"_meta": {"seed": SEED, "nshuf": NSHUF, "min_cell": MIN_CELL,
                     "note": "T3. Prong 1: order_frac per subset vs size-matched Latin. Prong 2: "
                             "affix-agreement MI vs within-line shuffle; the (no copies) variants "
                             "exclude DL<=1 pairs to remove the self-citation mimic; the generator "
                             "row is the copy-matched null."},
           "prong1_order_by_subset": prong1, "prong2_affix_agreement": prong2}
    (RES / "t3_syntax_hunt.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    print("  PRONG 1 — word-order info per subset (vs size-matched Latin):")
    print(f"    {'cell':26s} {'n':>6s} {'ordFrac':>8s} {'z':>6s} {'Latin@n':>8s} {'fracLatin':>9s}")
    for name, d in sorted(prong1.items(), key=lambda kv: -(kv[1]['frac_of_latin'] or 0)):
        print(f"    {name:26s} {d['n']:6d} {d['order_frac']:8.4f} {str(d['z']):>6s} "
              f"{d['latin_same_n_order_frac']:8.4f} {str(d['frac_of_latin']):>9s}")
    print("\n  PRONG 2 — affix agreement (MI excess over within-line shuffle):")
    for label, dd in prong2.items():
        print(f"    {label}:")
        for k, d in dd.items():
            print(f"      {k:28s} excess={d['excess']:+.4f} (z={d['z']}, pairs={d['n_pairs']})")

    # ---- figure ----
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(15.5, 5.6))
    names = list(prong1)
    fr = [prong1[n]["frac_of_latin"] or 0 for n in names]
    axA.barh(names, fr, color=["#c0392b" if f >= 0.5 else "#2e86c1" for f in fr])
    axA.axvline(0.5, color="#c0392b", ls="--", lw=1.2, label="F2 threshold (half of Latin)")
    axA.axvline(1.0, color="k", ls=":", lw=1, label="Latin level")
    axA.invert_yaxis(); axA.set_xlabel("order info as fraction of size-matched Latin")
    axA.set_title("Prong 1 — does ANY subset approach language-like word order?")
    axA.grid(True, axis="x", ls=":", alpha=0.3); axA.legend(fontsize=8); axA.tick_params(labelsize=8)

    kinds = ["suffix->suffix", "suffix->suffix (no copies)", "prefix->suffix (no copies)",
             "suffix->prefix (no copies)"]
    x = np.arange(len(kinds)); w = 0.27
    for k, (label, col) in enumerate([("Voynich", "#c0392b"),
                                      ("Latin (positive control)", "#27632a"),
                                      ("scribe generator (copy-matched null)", "#95a5a6")]):
        axB.bar(x + (k - 1) * w, [prong2[label][kk]["excess"] for kk in kinds], w,
                label=label, color=col)
    axB.axhline(0, color="k", lw=0.8)
    axB.set_xticks(x); axB.set_xticklabels(kinds, fontsize=7, rotation=12)
    axB.set_ylabel("agreement MI excess (bits)")
    axB.set_title("Prong 2 — do affixes AGREE with their neighbours?\n(Latin = what real concord looks like)")
    axB.grid(True, axis="y", ls=":", alpha=0.3); axB.legend(fontsize=7)
    fig.suptitle("T3 — the syntax hunt: is there language hiding in any subset?", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(FIG / "t3_syntax_hunt.png", dpi=140); plt.close(fig)
    print(f"\n  wrote {RES/'t3_syntax_hunt.json'}, figures/t3_syntax_hunt.png")


if __name__ == "__main__":
    main()
