"""T9 — the two missing self-citation controls (red-team T2.3). (2026-07-05)

Plate 8 / paper 6.3-6.6 claim the copy-and-mutate signatures are absent from every real text we
measured. The red-team pass named the two text genres MOST likely to break that claim, because
both produce same-stem-different-ending sequences by construction:

  A. A PARADIGM TABLE — the morphology section of a grammar book. "rosa rosae rosae rosam rosa
     rosae rosarum rosis rosas rosis ..." is literally stem + systematically varied ending, word
     after word. Prediction registered before running: it WILL fire the nearest-distance and
     copy-spike signatures, plausibly the locality gradient too. The question is whether the
     REST of the fingerprint (entropy, Zipf, type growth, word order, lengths) also matches the
     Voynich — the ensemble argument — and that must be shown with numbers, not asserted.
  B. A LITANY — fixed response, varied invocation ("Sancte Petre, ora pro nobis / Sancte Paule,
     ora pro nobis ..."). Exact-repeat mass at short regular lags by construction.

Corpora.
  A is built programmatically from real Latin vocabulary: ~230 nouns (declensions 1-5), ~22
    first/second-declension adjectives, ~140 regular verbs (conjugations 1-4; present system,
    active + passive indicative, present + imperfect subjunctive active, infinitives,
    imperatives). Ordered the way a grammar orders it: by declension/conjugation chapter, the
    full paradigm of each lexeme recited in sequence. That grouping is also the ADVERSARIAL
    choice: consecutive lexemes share their entire ending set. Simplifications (documented, all
    statistically minor): no vocative/locative; third-declension i-stems limited to a marked
    list (gen. pl. -ium); fifth-declension plurals printed in full even where classical usage is
    defective; no deponent, irregular, or third-conjugation -io verbs.
  B is three real litanies concatenated (data/texts/litany/raw/litanies.txt): the Litany of the
    Saints and the Litany of the Sacred Heart (sanctamissa.pl transcriptions of the traditional
    Latin texts) and the Litany of Loreto (Latin text as printed in the Wikipedia article).
    Litanies are short: n ~ 2,000 tokens total. That is the honest size of the genre, so the
    comparison runs size-matched with an explicit small-n caveat rather than being padded.

Method. Each control gets the FULL self-citation battery from self_citation.py (nearest-distance
sweep, distance histogram at W=25, locality gradient, 30 seeded shuffles -> z-scores) plus the
ensemble metrics used by redteam_calibrate.py (h2, word-length mean/sd, Zipf slope, types,
word-order fraction). Because both controls are far smaller than the 30k standard series, the
Voynich AND Latin prose are re-scored trimmed to each control's exact n, so every comparison in
the output is size-matched.

Writes results/t9_paradigm_controls.json + figures/t9_paradigm_controls.png.
"""
import json
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import seriesio as S
import textkit
import generate_model as GM
from self_citation import analyse as sc_analyse
from word_syntax import analyse as word_analyse

RES = S.ROOT / "results"
FIG = S.ROOT / "figures"
LIT = S.ROOT / "data" / "texts" / "litany" / "raw" / "litanies.txt"
SEED = 1492

# ---------------------------------------------------------------- paradigm vocabulary (real Latin)
D1 = ("rosa puella aqua terra via vita causa fortuna natura silva insula fama cura ira lingua "
      "littera mensa patria pecunia poena porta regina sagitta stella victoria femina filia dea "
      "domina epistula fenestra gloria gratia hora iniuria memoria sententia agricola nauta poeta "
      "turba unda villa flamma corona ancilla copia culpa forma fuga herba lacrima luna mora ripa "
      "rota taberna tuba umbra vacca").split()
D2M = ("amicus animus annus campus deus dominus equus filius hortus locus ludus modus mundus "
       "murus numerus oculus populus servus ventus cibus gladius medicus nuntius socius titulus "
       "tribunus vicus digitus lupus taurus corvus asinus barbarus legatus morbus nasus ramus "
       "somnus sonus succus").split()
D2ER = [("puer", "puer"), ("ager", "agr"), ("magister", "magistr"), ("liber", "libr"),
        ("vir", "vir")]
D2N = ("bellum caelum consilium donum exemplum factum ferrum forum imperium ingenium initium "
       "negotium officium oppidum periculum praemium proelium regnum signum templum verbum vinum "
       "aurum argentum folium granum membrum oleum ovum pomum saxum scutum telum vallum").split()
D3MF = [("rex", "reg"), ("lex", "leg"), ("dux", "duc"), ("pax", "pac"), ("vox", "voc"),
        ("homo", "homin"), ("virtus", "virtut"), ("civitas", "civitat"), ("libertas", "libertat"),
        ("veritas", "veritat"), ("mors", "mort"), ("pars", "part"), ("ars", "art"),
        ("mens", "ment"), ("urbs", "urb"), ("nox", "noct"), ("miles", "milit"), ("pater", "patr"),
        ("mater", "matr"), ("frater", "fratr"), ("soror", "soror"), ("princeps", "princip"),
        ("iudex", "iudic"), ("custos", "custod"), ("comes", "comit"), ("eques", "equit"),
        ("pes", "ped"), ("dens", "dent"), ("mons", "mont"), ("fons", "font"), ("pons", "pont"),
        ("gens", "gent"), ("laus", "laud"), ("salus", "salut"), ("aetas", "aetat"),
        ("aestas", "aestat"), ("hiems", "hiem"), ("arbor", "arbor"), ("flos", "flor"),
        ("honor", "honor"), ("labor", "labor"), ("amor", "amor"), ("dolor", "dolor"),
        ("timor", "timor"), ("color", "color"), ("mos", "mor"), ("sol", "sol"), ("leo", "leon")]
D3_ISTEM = {"mors", "pars", "ars", "mens", "urbs", "nox", "dens", "mons", "fons", "pons", "gens"}
D3N = [("corpus", "corpor"), ("tempus", "tempor"), ("genus", "gener"), ("opus", "oper"),
       ("nomen", "nomin"), ("flumen", "flumin"), ("lumen", "lumin"), ("carmen", "carmin"),
       ("agmen", "agmin"), ("caput", "capit"), ("iter", "itiner"), ("vulnus", "vulner"),
       ("pectus", "pector"), ("latus", "later"), ("litus", "litor"), ("munus", "muner"),
       ("onus", "oner"), ("pondus", "ponder"), ("sidus", "sider"), ("scelus", "sceler")]
D4 = ("manus exercitus senatus spiritus usus casus cursus motus fructus gradus metus portus "
      "sensus versus vultus").split()
D4N = ["cornu", "genu"]
D5 = "res dies spes fides acies facies species meridies".split()
ADJ = ("bonus magnus longus altus malus multus parvus novus antiquus clarus carus durus firmus "
       "laetus plenus purus rectus sanctus verus primus medius validus vivus").split()
V1 = ("amo laudo porto voco curo servo specto narro nego opto orno paro pugno puto rogo canto "
      "clamo dono dubito erro habito laboro lavo libero monstro muto navigo occupo oppugno "
      "ambulo aedifico appello armo celo ceno culpo damno delecto desidero exspecto firmo formo "
      "memoro numero nuntio oro probo propero saluto sano spero spiro supero tempto vasto vigilo "
      "vito vulnero").split()
V2 = ("moneo habeo video teneo timeo debeo doceo iubeo maneo moveo respondeo sedeo taceo terreo "
      "valeo caveo deleo exerceo fleo floreo iaceo lateo noceo pareo pateo placeo praebeo studeo "
      "mereo misceo").split()
V3 = ("rego duco dico mitto scribo lego vinco vivo credo cado cedo claudo colo curro defendo "
      "gero ostendo peto pono premo quaero relinquo tollo traho verto ago alo ascendo bibo cano "
      "cerno cingo cognosco condo consumo cresco disco divido emo fallo frango fundo iungo ludo "
      "pello perdo reddo rumpo solvo sumo surgo tango tego tendo trado vendo").split()
V4 = ("audio venio dormio sentio aperio finio invenio munio punio scio servio custodio impedio "
      "nutrio reperio salio sepelio sitio vestio").split()

# case endings: (sg nom..abl, pl nom..abl); None = use the given nominative form
NOUN_END = {
    "d1":  (["a", "ae", "ae", "am", "a"], ["ae", "arum", "is", "as", "is"]),
    "d2m": (["us", "i", "o", "um", "o"], ["i", "orum", "is", "os", "is"]),
    "d2n": (["um", "i", "o", "um", "o"], ["a", "orum", "is", "a", "is"]),
    "d4":  (["us", "us", "ui", "um", "u"], ["us", "uum", "ibus", "us", "ibus"]),
    "d4n": (["u", "us", "u", "u", "u"], ["ua", "uum", "ibus", "ua", "ibus"]),
    "d5":  (["es", "ei", "ei", "em", "e"], ["es", "erum", "ebus", "es", "ebus"]),
}
# verb suffix tables per conjugation, appended to the root (am-, mon-, reg-, audi-):
# pres act, impf act, fut act, pres pass, impf pass, fut pass, pres subj act, impf subj act,
# infinitives (act, pass), imperatives (sg, pl)
VERB_END = {
    1: (["o", "as", "at", "amus", "atis", "ant"],
        ["abam", "abas", "abat", "abamus", "abatis", "abant"],
        ["abo", "abis", "abit", "abimus", "abitis", "abunt"],
        ["or", "aris", "atur", "amur", "amini", "antur"],
        ["abar", "abaris", "abatur", "abamur", "abamini", "abantur"],
        ["abor", "aberis", "abitur", "abimur", "abimini", "abuntur"],
        ["em", "es", "et", "emus", "etis", "ent"],
        ["arem", "ares", "aret", "aremus", "aretis", "arent"],
        ["are", "ari"], ["a", "ate"]),
    2: (["eo", "es", "et", "emus", "etis", "ent"],
        ["ebam", "ebas", "ebat", "ebamus", "ebatis", "ebant"],
        ["ebo", "ebis", "ebit", "ebimus", "ebitis", "ebunt"],
        ["eor", "eris", "etur", "emur", "emini", "entur"],
        ["ebar", "ebaris", "ebatur", "ebamur", "ebamini", "ebantur"],
        ["ebor", "eberis", "ebitur", "ebimur", "ebimini", "ebuntur"],
        ["eam", "eas", "eat", "eamus", "eatis", "eant"],
        ["erem", "eres", "eret", "eremus", "eretis", "erent"],
        ["ere", "eri"], ["e", "ete"]),
    3: (["o", "is", "it", "imus", "itis", "unt"],
        ["ebam", "ebas", "ebat", "ebamus", "ebatis", "ebant"],
        ["am", "es", "et", "emus", "etis", "ent"],
        ["or", "eris", "itur", "imur", "imini", "untur"],
        ["ebar", "ebaris", "ebatur", "ebamur", "ebamini", "ebantur"],
        ["ar", "eris", "etur", "emur", "emini", "entur"],
        ["am", "as", "at", "amus", "atis", "ant"],
        ["erem", "eres", "eret", "eremus", "eretis", "erent"],
        ["ere", "i"], ["e", "ite"]),
    4: (["o", "s", "t", "mus", "tis", "unt"],
        ["ebam", "ebas", "ebat", "ebamus", "ebatis", "ebant"],
        ["am", "es", "et", "emus", "etis", "ent"],
        ["or", "ris", "tur", "mur", "mini", "untur"],
        ["ebar", "ebaris", "ebatur", "ebamur", "ebamini", "ebantur"],
        ["ar", "eris", "etur", "emur", "emini", "entur"],
        ["am", "as", "at", "amus", "atis", "ant"],
        ["rem", "res", "ret", "remus", "retis", "rent"],
        ["re", "ri"], ["", "te"]),
}


def noun_forms(nom, stem, decl, istem=False):
    if decl == "d3mf":
        sg = [nom, stem + "is", stem + "i", stem + "em", stem + "e"]
        pl = [stem + "es", stem + ("ium" if istem else "um"), stem + "ibus",
              stem + "es", stem + "ibus"]
        return sg + pl
    if decl == "d3n":
        sg = [nom, stem + "is", stem + "i", nom, stem + "e"]
        pl = [stem + "a", stem + "um", stem + "ibus", stem + "a", stem + "ibus"]
        return sg + pl
    sg_e, pl_e = NOUN_END[decl]
    if decl == "d2m" and nom is not None:          # puer-type: irregular nominative
        sg = [nom] + [stem + e for e in sg_e[1:]]
        return sg + [stem + e for e in pl_e]
    return [stem + e for e in sg_e] + [stem + e for e in pl_e]


def build_paradigm():
    """Emit the full paradigm text, chapter by chapter, exactly as a grammar recites it."""
    out = []
    for w in D1:
        out += noun_forms(None, w[:-1], "d1")
    for w in D2M:
        out += noun_forms(None, w[:-2], "d2m")
    for nom, stem in D2ER:
        out += noun_forms(nom, stem, "d2m")
    for w in D2N:
        out += noun_forms(None, w[:-2], "d2n")
    for nom, stem in D3MF:
        out += noun_forms(nom, stem, "d3mf", istem=nom in D3_ISTEM)
    for nom, stem in D3N:
        out += noun_forms(nom, stem, "d3n")
    for w in D4:
        out += noun_forms(None, w[:-2], "d4")
    for w in D4N:
        out += noun_forms(None, w[:-1], "d4n")
    for w in D5:
        out += noun_forms(None, w[:-2], "d5")
    # adjectives: recited row-major (bonus bona bonum, boni bonae boni, ...) per case, sg then pl
    for w in ADJ:
        stem = w[:-2]
        m = noun_forms(None, stem, "d2m")
        f = noun_forms(None, stem, "d1")
        n = noun_forms(None, stem, "d2n")
        for i in range(10):
            out += [m[i], f[i], n[i]]
    # verbs: full present-system recitation per lexeme, conjugation by conjugation
    for verbs, conj, strip in ((V1, 1, 1), (V2, 2, 2), (V3, 3, 1), (V4, 4, 1)):
        for v in verbs:
            root = v[:-strip]                     # amo->am, moneo->mon, rego->reg, audio->audi
            for block in VERB_END[conj]:
                out += [root + e for e in block]
    return out


def score(tokens, label):
    rng = random.Random(SEED)
    sc = sc_analyse(tokens, rng)
    ev = GM.evaluate(tokens)
    wa = word_analyse(tokens, random.Random(SEED))
    ens = {"h2_cross_bits": ev["h2_cross_bits"], "wordlen_mean": ev["wordlen_mean"],
           "wordlen_std": ev["wordlen_std"], "zipf_slope": ev["zipf_slope"],
           "n_types": ev["n_types"], "order_frac": wa["order_frac"],
           "adjacent_repeat_rate": wa["adjacent_repeat_rate"]}
    sig = {"excess_raw_z": sc["sweep"]["25"]["excess_raw_z"],
           "excess_d0_d1": sc["signatures"]["excess_d0_d1"],
           "excess_d0_d1_z": sc["hist"]["excess_d0_d1_z"],
           "gradient_excess": sc["signatures"]["gradient_excess"],
           "gradient_excess_z": sc["locality"]["gradient_excess_z"]}
    print(f"  {label:24s} n={len(tokens):6d}  sc_z={sig['excess_raw_z']:>7}  "
          f"d0d1={sig['excess_d0_d1']:+.3f} (z={sig['excess_d0_d1_z']})  "
          f"grad={sig['gradient_excess']:+.3f} (z={sig['gradient_excess_z']})  "
          f"h2={ens['h2_cross_bits']:.2f} wlStd={ens['wordlen_std']:.2f} "
          f"ordFrac={ens['order_frac']:.3f}")
    return {"n": len(tokens), "signatures": sig, "ensemble": ens, "self_citation_full": sc}


def main():
    RES.mkdir(exist_ok=True)
    FIG.mkdir(exist_ok=True)
    paradigm = build_paradigm()
    litany = textkit.clean_tokens(LIT.read_text(encoding="utf-8"))
    voy = S.load_tokens("voynich_eva")
    lat = S.load_tokens("latin")

    out = {"_meta": {
        "seed": SEED,
        "purpose": "red-team T2.3: the two text genres that produce stem+varied-ending sequences "
                   "by construction, run through the full self-citation battery size-matched. "
                   "Registered prediction: the paradigm table fires the copy signatures; the "
                   "question the ensemble columns answer is whether it ALSO matches the rest of "
                   "the Voynich fingerprint.",
        "paradigm_construction": "real Latin stems x real endings, grammar-book chapter order; "
                                 "see script docstring for the simplification list",
        "litany_sources": "Litany of the Saints + Litany of the Sacred Heart (sanctamissa.pl, "
                          "traditional Latin) + Litany of Loreto (Wikipedia, Latin text), "
                          "concatenated; small-n caveat applies",
        "size_matching": "Voynich and Latin prose re-scored trimmed to each control's n"}}

    print("paradigm-table control:")
    out["paradigm"] = score(paradigm, "paradigm table")
    out["voynich_at_paradigm_n"] = score(voy[:len(paradigm)], "Voynich @ same n")
    out["latin_at_paradigm_n"] = score(lat[:len(paradigm)], "Latin prose @ same n")
    print("litany control:")
    out["litany"] = score(litany, "litany (3 concatenated)")
    out["voynich_at_litany_n"] = score(voy[:len(litany)], "Voynich @ same n")
    out["latin_at_litany_n"] = score(lat[:len(litany)], "Latin prose @ same n")

    (RES / "t9_paradigm_controls.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    # ---- figure: signature z-scores + the ensemble separation, size-matched ----
    groups = [("paradigm table", "paradigm", "voynich_at_paradigm_n", "latin_at_paradigm_n"),
              ("litany", "litany", "voynich_at_litany_n", "latin_at_litany_n")]
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.2))
    metrics = [("excess_raw_z", "(A) nearest-distance below shuffle (z)"),
               ("gradient_excess_z", "(B) locality gradient (z)")]
    for ax, (key, title) in zip(axes[:2], metrics):
        labels, vals, cols = [], [], []
        for gname, ctrl, vk, lk in groups:
            for k, lab, c in ((ctrl, gname, "#8e44ad"), (vk, "Voynich @ n", "#c0392b"),
                              (lk, "Latin @ n", "#27632a")):
                labels.append(f"{lab}\n({gname[:8]})" if lab != gname else lab)
                vals.append(out[k]["signatures"][key] or 0)
                cols.append(c)
        ax.bar(range(len(vals)), vals, color=cols)
        ax.set_xticks(range(len(vals)))
        ax.set_xticklabels(labels, fontsize=7, rotation=20, ha="right")
        ax.axhline(0, color="k", lw=0.8)
        ax.axhline(3, color="grey", lw=0.8, ls=":")
        ax.set_title(title, fontsize=10)
        ax.grid(True, axis="y", ls=":", alpha=0.3)
    axC = axes[2]
    for gname, ctrl, vk, lk in groups:
        for k, lab, c, m in ((ctrl, gname, "#8e44ad", "s"), (vk, "Voynich", "#c0392b", "*"),
                             (lk, "Latin prose", "#27632a", "o")):
            e = out[k]["ensemble"]
            axC.scatter(e["order_frac"], e["h2_cross_bits"], color=c, marker=m, s=140,
                        edgecolor="white", zorder=3)
            axC.annotate(f"{lab} ({gname[:8]})", (e["order_frac"], e["h2_cross_bits"]),
                         textcoords="offset points", xytext=(8, 4), fontsize=7)
    axC.set_xlabel("word-order information (order_frac)")
    axC.set_ylabel("h2 (bits)")
    axC.set_title("(C) the ensemble separation:\ncopy signatures alone are not the fingerprint",
                  fontsize=10)
    axC.grid(True, ls=":", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG / "t9_paradigm_controls.png", dpi=140)
    plt.close(fig)
    print(f"\n  wrote {RES / 't9_paradigm_controls.json'}, figures/t9_paradigm_controls.png")


if __name__ == "__main__":
    main()
