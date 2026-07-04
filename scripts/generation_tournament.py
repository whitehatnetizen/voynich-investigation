"""Capstone — can ONE mechanical generator reproduce the whole Voynich fingerprint? (2026-07-01)

A tournament of generators from single-characteristic SPECIALISTS to a UNIFIED model, each scored on
the full fingerprint (within-word structure / word length / vocabulary / sequential self-citation /
section structure) against the real-Voynich targets. Each (generator, metric) cell is tagged FIT
(a parameter was estimated to match it) vs EMERGENT (it fell out for free). Emergent matches are the
real evidence; the headline question is whether a specialist that nails ONE characteristic reveals a
mechanism that, combined, nails EVERYTHING.

Working hypothesis: the self-citation mechanism (copy a recent word, mutate it slightly) may
reproduce several still-unmet constraints at once — word repetition (directly), Zipf + type count
(preferential copying = Yule-Simon), and, via frequency concentration, a narrowing of word length —
where the independent first-order Markov model (generate_model.py) failed on length + repetition.

Ladder:
  S0 iid          glyphs iid + empirical length                        [reuse generate_model]
  S1 slot         first/mid/last positional menus + empirical length   [reuse]
  S2 markov1      first-order glyph Markov, endogenous length          [reuse]
  S3 markov2      second-order glyph Markov
  S4 lenlock      markov transitions with the empirical length LOCKED  (A + B by construction)
  S5 selfcite     copy-from-last-W + slot-respecting mutation; fresh words from markov1
  U1 unified      selfcite whose fresh source is lenlock (copies inherit narrow length)
  U2 unified+sec  U1 with per-section vocabulary bias (Montemurro divergence ~0.32)

Writes results/generation_tournament.json + figures/generation_tournament.png.
"""
import json
import random
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import seriesio as S
import generate_model as GM
from slot_grammar import affixes, positional
from currier_split import self_citation
from word_syntax import analyse as word_analyse
from section_structure import mi_vs_shuffle

RES = S.ROOT / "results"
FIG = S.ROOT / "figures"
SEED = 1492
N = 30000
MAXLEN = 40


def _scale_sizes(sizes, total):
    """Scale a section-size layout to sum to `total`, preserving proportions (review FIX-6:
    U2 used to emit 24,060 tokens while every other row was scored at 30,000 — n_types,
    zipf_slope, heaps_beta and the self-citation excesses are size-dependent)."""
    f = total / sum(sizes)
    out = [int(round(s * f)) for s in sizes]
    out[-1] += total - sum(out)
    return out


SIZES = _scale_sizes([10889, 6386, 3477, 2141, 1167], N)   # within-B geometry, scaled to N
SECTION_TARGET = 0.090                        # real Voynich within-B excess/H(section)
KDIST = [0.15, 0.55, 0.30]                    # P(k=0 exact / 1 / 2 edits) for mutation
VOY_LENS = None                                # Voynich empirical word lengths (set in main)


# ================= new generators =================
def fit_markov2(seqs):
    trans = defaultdict(Counter)
    for w in seqs:
        if not w:
            continue
        p2, p1 = "\x02", "\x02"
        for g in w:
            trans[(p2, p1)][g] += 1
            p2, p1 = p1, g
        trans[(p2, p1)]["\x03"] += 1
    return {st: (np.array(list(c)), np.array(list(c.values()), float) / sum(c.values()))
            for st, c in trans.items()}


def gen_markov2(m, rng, n):
    out = []
    for _ in range(n):
        p2, p1 = "\x02", "\x02"
        w = []
        for _ in range(MAXLEN):
            st = (p2, p1)
            if st not in m:
                break
            k, p = m[st]
            nxt = rng.choice(k, p=p)
            if nxt == "\x03":
                break
            w.append(nxt); p2, p1 = p1, nxt
        if w:
            out.append("".join(w))
    return out


def fit_cont(mk):
    """END-excluded, renormalised transitions — used to regenerate a word tail without stopping."""
    cont = {}
    for st, (k, p) in mk.items():
        mask = k != "\x03"
        if mask.sum() == 0:
            continue
        pp = p[mask]
        cont[st] = (k[mask], pp / pp.sum())
    return cont


def gen_lenlock(mk, rng, n, lens):
    """Length-lock by REJECTION: resample NATURAL Markov words (full transition structure incl. END,
    so h2 is preserved ~2.45) that match a target length drawn from the empirical distribution.
    Gives both the low-h2 grammar AND the narrow word-length band."""
    pool = GM.gen_markov(mk, rng, max(n * 4, 120000))
    by = defaultdict(list)
    for w in pool:
        by[len(w)].append(w)
    out = []
    Ls = rng.choice(lens, size=n)
    for L in Ls:
        L = int(L)
        cand = by.get(L)
        if not cand:
            for d in range(1, 12):
                cand = by.get(L - d) or by.get(L + d)
                if cand:
                    break
        out.append(cand[int(rng.integers(0, len(cand)))] if cand else pool[0])
    return out


def mutate(word, cont, rng, k):
    """Markov-consistent mutation: keep the prefix, REGENERATE the last 1-2 glyphs via the transition
    model (length preserved). This preserves the within-word bigram structure (h2 stays low) and
    yields prefix-sharing near-copies (the qo-/ch- pattern) at small edit distance."""
    g = list(word)
    for _ in range(k):
        if len(g) < 2:
            break
        cut = max(1, len(g) - 1 - int(rng.integers(0, 2)))      # regenerate last 1-2 glyphs
        st = g[cut - 1]
        tail = []
        for _ in range(len(g) - cut):
            src = cont.get(st)
            if src is None:
                break
            kk, pp = src
            ng = rng.choice(kk, p=pp)
            tail.append(ng); st = ng
        g = g[:cut] + tail
    return "".join(g)


def gen_selfcite(fresh_pool, cont, rng, n, W, p_copy):
    """Each word: with prob p_copy copy a word from the last W emitted and mutate it (k~KDIST);
    else take the next fresh word from the pool."""
    kk = np.array([0, 1, 2]); kp = np.array(KDIST) / sum(KDIST)
    out = []
    fp = 0
    for _ in range(n):
        if len(out) >= 2 and rng.random() < p_copy:
            lo = max(0, len(out) - W)
            hi = len(out) - 1                          # exclude the immediately-preceding word
            j = int(rng.integers(lo, hi)) if hi > lo else lo
            w = mutate(out[j], cont, rng, int(rng.choice(kk, p=kp)))
            if not w:
                w = fresh_pool[fp % len(fresh_pool)]; fp += 1
        else:
            w = fresh_pool[fp % len(fresh_pool)]; fp += 1
        out.append(w)
    return out


def gen_u2(mk, cont, rng, sizes, W, p_copy, overlap):
    """Unified + per-section vocabulary bias: fresh words drawn with prob `overlap` from the global
    pool and (1-overlap) from a section-specific pool; copying stays within the section buffer."""
    pool = gen_lenlock(mk, rng, sum(sizes), VOY_LENS)   # Voynich empirical length profile
    freq = Counter(pool)
    types = list(freq)
    w = np.array([freq[t] for t in types], float)
    gp = w / w.sum()
    order = sorted(range(len(types)), key=lambda i: -w[i])
    pools = [[] for _ in sizes]
    mass = [0.0] * len(sizes)
    for i in order:
        z = min(range(len(sizes)), key=lambda q: mass[q])
        pools[z].append(i); mass[z] += w[i]
    pool_prob = [(np.array(pl), w[pl] / w[pl].sum()) for pl in pools]
    kk = np.array([0, 1, 2]); kp = np.array(KDIST) / sum(KDIST)
    out, secs = [], []
    for s, m in enumerate(sizes):
        pl, pp = pool_prob[s]
        buf = []
        for _ in range(m):
            if len(buf) >= 2 and rng.random() < p_copy:
                lo = max(0, len(buf) - W); hi = len(buf) - 1
                j = int(rng.integers(lo, hi)) if hi > lo else lo
                wd = mutate(buf[j], cont, rng, int(rng.choice(kk, p=kp)))
                if not wd:
                    wd = types[int(rng.choice(len(types), p=gp))]
            elif rng.random() < overlap:
                wd = types[int(rng.choice(len(types), p=gp))]
            else:
                wd = types[int(rng.choice(pl, p=pp))]
            buf.append(wd); out.append(wd); secs.append(f"S{s}")
    return out, secs


# ================= scoring =================
METRICS = ["h1", "h2_cross", "bigram_top10", "suffix2_cov", "prefix2_cov", "pos_ratio",
           "wordlen_mean", "wordlen_std",
           "zipf_slope", "n_types", "heaps_beta",
           "sc_excess_W5", "sc_d1", "sc_grad", "order_frac", "adj_repeat",
           "section_excessH"]
GROUP = {"h1": "A", "h2_cross": "A", "bigram_top10": "A", "suffix2_cov": "A", "prefix2_cov": "A",
         "pos_ratio": "A", "wordlen_mean": "B", "wordlen_std": "B", "zipf_slope": "C",
         "n_types": "C", "heaps_beta": "C", "sc_excess_W5": "D", "sc_d1": "D", "sc_grad": "D",
         "order_frac": "D", "adj_repeat": "D", "section_excessH": "E"}


def heaps_beta(tokens, step=250):
    seen = set(); V = 0; xs = []; ys = []
    for i, t in enumerate(tokens, 1):
        if t not in seen:
            seen.add(t); V += 1
        if i % step == 0:
            xs.append(i); ys.append(V)
    lx, ly = np.log10(xs), np.log10(ys)
    A = np.vstack([lx, np.ones_like(lx)]).T
    return float(np.linalg.lstsq(A, ly, rcond=None)[0][0])


def score_tokens(tokens, sections=None):
    rng = random.Random(SEED)
    ev = GM.evaluate(tokens)
    seqs = [list(t) for t in tokens]
    af = affixes(seqs)
    pos = positional(seqs)
    sc = self_citation(tokens, rng)
    wa = word_analyse(tokens, rng)
    m = {
        "h1": ev["h1_char_bits"], "h2_cross": ev["h2_cross_bits"], "bigram_top10": ev["bigram_top10_share"],
        "suffix2_cov": af["suffix2"]["top10_coverage"], "prefix2_cov": af["prefix2"]["top10_coverage"],
        "pos_ratio": pos["positional_ratio_best"],
        "wordlen_mean": ev["wordlen_mean"], "wordlen_std": ev["wordlen_std"],
        "zipf_slope": ev["zipf_slope"], "n_types": ev["n_types"], "heaps_beta": round(heaps_beta(tokens), 3),
        "sc_excess_W5": sc["excess_raw_W5"], "sc_d1": sc["excess_d1"], "sc_grad": sc["gradient_real"],
        "order_frac": wa["order_frac"], "adj_repeat": wa["adjacent_repeat_rate"],
    }
    if sections is not None:
        m["section_excessH"] = mi_vs_shuffle(tokens, sections, rng)["excess_frac_of_Hsection"]
    return m


def rel_dist(val, tgt):
    if val is None:
        return None
    scale = abs(tgt) if abs(tgt) > 1e-6 else 1.0
    return abs(val - tgt) / scale


# FIT sets: metric-groups a generator directly parameterises (so a match there is not evidence)
FIT = {
    "S0 iid": {"h1", "wordlen_mean", "wordlen_std"},
    "S1 slot": {"suffix2_cov", "prefix2_cov", "pos_ratio", "wordlen_mean", "wordlen_std"},
    "S2 markov1": {"h1", "h2_cross", "bigram_top10"},
    "S3 markov2": {"h1", "h2_cross", "bigram_top10"},
    "S4 lenlock": {"h1", "h2_cross", "bigram_top10", "wordlen_mean", "wordlen_std"},
    "S5 selfcite": {"h1", "h2_cross", "bigram_top10", "sc_excess_W5", "sc_d1", "sc_grad", "adj_repeat"},
    "U1 unified": {"h1", "h2_cross", "bigram_top10", "wordlen_mean", "wordlen_std",
                   "sc_excess_W5", "sc_d1", "sc_grad", "adj_repeat"},
    "U2 unified+sec": {"h1", "h2_cross", "bigram_top10", "wordlen_mean", "wordlen_std",
                       "sc_excess_W5", "sc_d1", "sc_grad", "adj_repeat", "section_excessH"},
}


def combined_fit(scores, target, emergent_only=False, gen_name=None):
    ds = []
    for k in METRICS:
        if scores.get(k) is None or target.get(k) is None:
            continue
        if emergent_only and gen_name and k in FIT.get(gen_name, set()):
            continue
        ds.append(min(rel_dist(scores[k], target[k]), 2.0))
    return float(np.mean(ds)) if ds else float("nan")


def main():
    global VOY_LENS
    RES.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)
    rng = np.random.default_rng(SEED)
    voy = S.load_tokens("voynich_eva")
    eng = S.load_tokens("english")
    vseqs = [list(t) for t in voy]

    # fitted specialists
    sl = GM.fit_slot(vseqs)
    mk = GM.fit_markov(vseqs)
    cont = fit_cont(mk)
    VOY_LENS = np.array([len(w) for w in vseqs if w])
    mk_pool = GM.gen_markov(mk, rng, N)
    lock_pool = gen_lenlock(mk, rng, N, VOY_LENS)

    # ---- parameter sweep for S5 / U1 ----
    # Review FIX-6(a): (W, p_copy) are the COPY parameters, so they are selected ONLY on the
    # self-citation metrics they are meant to fit (sc_excess_W5, sc_d1, sc_grad, adj_repeat).
    # The old sweep minimised the combined fit over ALL 17 metrics — including zipf_slope,
    # n_types, heaps_beta and order_frac, which were then tagged EMERGENT despite having been
    # (weakly, 2 dof) selected for. Under copy-only selection those metrics are genuinely free.
    target = score_tokens(voy)
    target["section_excessH"] = SECTION_TARGET

    COPY_METRICS = ["sc_excess_W5", "sc_d1", "sc_grad", "adj_repeat"]

    def copy_fit(tokens):
        rngl = random.Random(SEED)
        sc = self_citation(tokens, rngl, nshuf=10)
        adj = sum(1 for a, b in zip(tokens, tokens[1:]) if a == b) / (len(tokens) - 1)
        vals = {"sc_excess_W5": sc["excess_raw_W5"], "sc_d1": sc["excess_d1"],
                "sc_grad": sc["gradient_real"], "adj_repeat": adj}
        return float(np.mean([min(rel_dist(vals[k], target[k]), 2.0) for k in COPY_METRICS]))

    sweep = []
    best = {"S5 selfcite": (None, 1e9, None), "U1 unified": (None, 1e9, None)}
    for W in (5, 10, 25):
        for pc in (0.2, 0.35, 0.5):
            s5 = gen_selfcite(mk_pool, cont, rng, N, W, pc)
            u1 = gen_selfcite(lock_pool, cont, rng, N, W, pc)
            fs5 = copy_fit(s5)
            fu1 = copy_fit(u1)
            sweep.append({"W": W, "p_copy": pc, "S5_copyfit": round(fs5, 3), "U1_copyfit": round(fu1, 3)})
            if fs5 < best["S5 selfcite"][1]:
                best["S5 selfcite"] = ((W, pc), fs5, s5)
            if fu1 < best["U1 unified"][1]:
                best["U1 unified"] = ((W, pc), fu1, u1)
    (Wu, pcu), _, u1_best = best["U1 unified"]
    u2, u2_sec = gen_u2(mk, cont, rng, SIZES, Wu, pcu, overlap=0.68)

    # ---- assemble all rows ----
    # Review FIX-6: every row is scored on the SAME 17-metric set. The voynich row carries its
    # real within-B section_excessH; english gets pseudo-sections of the matched geometry (its
    # topical drift at that slicing), so no row averages a different metric count.
    def fake_sections(n, sizes):
        secs = []
        for s, m in enumerate(sizes):
            secs.extend([f"S{s}"] * m)
        return secs[:n]

    rows = {
        "voynich (target)": (voy, None, "voynich (target)"),
        "english (real)": (eng, fake_sections(len(eng), SIZES), "english (real)"),
        "S0 iid": (GM.gen_iid(GM.fit_iid(vseqs), rng, N), None, "S0 iid"),
        "S1 slot": (GM.gen_slot(sl, rng, N), None, "S1 slot"),
        "S2 markov1": (GM.gen_markov(mk, rng, N), None, "S2 markov1"),
        "S3 markov2": (gen_markov2(fit_markov2(vseqs), rng, N), None, "S3 markov2"),
        "S4 lenlock": (gen_lenlock(mk, rng, N, VOY_LENS), None, "S4 lenlock"),
        "S5 selfcite": (best["S5 selfcite"][2], None, "S5 selfcite"),
        "U1 unified": (u1_best, None, "U1 unified"),
        "U2 unified+sec": (u2, u2_sec, "U2 unified+sec"),
    }

    scored, dist = {}, {}
    for name, (toks, secs, gname) in rows.items():
        sc = score_tokens(toks, secs)
        if name == "voynich (target)":
            sc["section_excessH"] = SECTION_TARGET      # its real within-B value
        scored[name] = sc
        dist[name] = {k: rel_dist(sc.get(k), target.get(k)) for k in METRICS}

    combined = {name: combined_fit(scored[name], target) for name in rows}
    combined_emergent = {name: combined_fit(scored[name], target, emergent_only=True, gen_name=name)
                         for name in rows}

    out = {
        "_meta": {"seed": SEED, "n": N, "section_sizes": SIZES, "section_target": SECTION_TARGET,
                  "kdist": KDIST, "best_configs": {k: best[k][0] for k in best},
                  "u2_config": {"W": Wu, "p_copy": pcu, "overlap": 0.68},
                  "sweep_selection": "copy-only (sc_excess_W5, sc_d1, sc_grad, adj_repeat) — review "
                                     "FIX-6a: zipf/types/heaps/order_frac are NOT selected for and "
                                     "are genuinely emergent",
                  "combined_fit_definition": "mean over metrics of |x-t|/max(|t|,1e-6), clipped at "
                                             "2.0 — weights metrics by 1/|target|, so small-|t| "
                                             "metrics dominate (for U2, four small-|t| metrics carry "
                                             "~3/4 of the score); the emergent-only sub-score is the "
                                             "honest headline. Self-fit 0.000 validates harness "
                                             "determinism, not scorer discrimination.",
                  "s5_class": "S5 is a SPECIALIST (single-characteristic: copying); the unified "
                              "family is U1/U2",
                  "note": "target row = real Voynich scored through the same harness; distances are relative error to target; FIT cells (see 'fit') are directly parameterised, EMERGENT are not. Combined-fit lower = better all-rounder. All rows scored on the same 17-metric set (english uses matched pseudo-sections)."},
        "targets": target, "sweep": sweep,
        "scores": scored, "rel_distance": dist,
        "combined_fit": {k: round(v, 3) for k, v in combined.items()},
        "combined_fit_emergent": {k: round(v, 3) for k, v in combined_emergent.items()},
        "fit_sets": {k: sorted(v) for k, v in FIT.items()},
    }
    (RES / "generation_tournament.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    # ---- console ----
    order = ["voynich (target)", "english (real)", "S0 iid", "S1 slot", "S2 markov1", "S3 markov2",
             "S4 lenlock", "S5 selfcite", "U1 unified", "U2 unified+sec"]
    print("Voynich targets:", {k: target[k] for k in METRICS if target.get(k) is not None})
    print("\n  best configs:", {k: best[k][0] for k in best}, " U2:", (Wu, pcu))
    print(f"\n  {'generator':17s} {'combined':>9s} {'emergent':>9s}   key metrics (val)")
    for name in order:
        s = scored[name]
        keys = ["h2_cross", "wordlen_std", "zipf_slope", "n_types", "sc_d1", "order_frac"]
        kv = " ".join(f"{k}={s.get(k)}" for k in keys)
        print(f"  {name:17s} {combined[name]:9.3f} {combined_emergent[name]:9.3f}   {kv}")

    # ---- figure: heatmap (rel distance) + combined-fit bar ----
    gens = [g for g in order]
    D = np.full((len(gens), len(METRICS)), np.nan)
    for i, name in enumerate(gens):
        for j, k in enumerate(METRICS):
            v = dist[name].get(k)
            if v is not None:
                D[i, j] = min(v, 1.0)
    fig, (axH, axB) = plt.subplots(1, 2, figsize=(19, 6.6), gridspec_kw={"width_ratios": [3.4, 1]})
    im = axH.imshow(D, aspect="auto", cmap="RdYlGn_r", vmin=0, vmax=1)
    axH.set_xticks(range(len(METRICS)))
    axH.set_xticklabels([f"{GROUP[k]}:{k}" for k in METRICS], rotation=55, ha="right", fontsize=8)
    axH.set_yticks(range(len(gens))); axH.set_yticklabels(gens, fontsize=9)
    for i, name in enumerate(gens):
        for j, k in enumerate(METRICS):
            if np.isnan(D[i, j]):
                axH.text(j, i, "·", ha="center", va="center", color="grey", fontsize=9)
            elif k in FIT.get(name, set()):
                axH.text(j, i, "f", ha="center", va="center", color="black", fontsize=7)  # FIT marker
    axH.set_title("Fingerprint fit — relative distance to Voynich (green=match, red=off). 'f' = FIT (parameterised); blank cells = EMERGENT")
    fig.colorbar(im, ax=axH, fraction=0.02, pad=0.01, label="relative distance (clipped at 1)")

    ce = [combined_emergent[g] for g in gens]
    yb = np.arange(len(gens))
    axB.barh(yb, ce, color=["#4c72b0" if g.startswith("U") else "#bbbbbb" for g in gens])
    axB.set_yticks(yb); axB.set_yticklabels([g.split()[0] for g in gens], fontsize=8)
    axB.invert_yaxis(); axB.set_xlabel("combined EMERGENT distance (lower=better all-rounder)")
    axB.set_title("All-round fit\n(emergent metrics only)")
    axB.grid(True, axis="x", ls=":", alpha=0.3)

    fig.suptitle("Generator tournament — does one mechanism reproduce the whole Voynich fingerprint?", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(FIG / "generation_tournament.png", dpi=140); plt.close(fig)
    print(f"\n  wrote {RES/'generation_tournament.json'}, figures/generation_tournament.png")


if __name__ == "__main__":
    main()
