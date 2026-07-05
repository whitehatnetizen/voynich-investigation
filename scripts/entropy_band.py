"""Entropy reference band, widened (red-team T1.2). (2026-07-05)

The original h2 "language band" (3.42-3.60 bits) rested on ONE work per language. A referee can
reasonably ask how wide the band really is: is 2.4 bits merely outside six specific books, or
outside the spread the languages actually produce? This script widens the reference class:

  - 3 works per language for the six band languages (the original primary, plus extras),
    every work scored identically: Gutenberg body -> clean_tokens -> first 30k tokens ->
    conditional bigram entropy h2 (same formula as generate_model.evaluate / discriminators).
  - One small-inventory natural language as a floor probe: HAWAIIAN (about 13 letters), the
    1868 Ka Baibala Hemolele from eBible.org (public domain; USFM markup stripped). A tiny
    alphabet lowers h1 mechanically, so it is the natural language most likely to approach the
    Voynich's h2 from above. Scripture register, noted as such.
  - Works whose body falls short of 30k tokens are skipped (printed), never padded.

Output: per-work h2, per-language mean/min/max, the pooled band across all works, Hawaiian and
the Voynich alongside. Writes results/entropy_band.json + figures/entropy_band.png.

Sources fetched into data/texts/<lang>/raw/ next to the originals (fetch step skips files that
already exist). Latin extras are checked for inline English contamination (Gutenberg Latin
editions often carry English notes): the script prints the frequency of 'the'/'and'/'of' and
refuses works above 0.5%.
"""
import io
import json
import time
import urllib.request
import zipfile
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import seriesio as S
import textkit

RES = S.ROOT / "results"
FIG = S.ROOT / "figures"
TDIR = S.ROOT / "data" / "texts"
N = 30000

# One entry per WORK: (title, [source, ...]) where source = ("gut", gutenberg_id) or
# ("tll", "path-on-thelatinlibrary.com"). Multi-source works are concatenated (Caesar's De Bello
# Gallico spans two Gutenberg files; Sallust's two monographs and De Officiis' three books each
# count as one work). Originals from fetch_corpora.py listed first so the whole reference class is
# rebuilt from one place. Gutenberg's other Latin editions carry inline English notes (checked and
# refused below), so the Latin extras come from The Latin Library, the same clean source used by
# fetch_topical_latin.py.
CORPUS = {
    "english": [("Pride and Prejudice - Austen", [("gut", 1342)]),
                ("Moby-Dick - Melville", [("gut", 2701)]),
                ("The Adventures of Sherlock Holmes - Doyle", [("gut", 1661)])],
    "french":  [("Vingt mille lieues sous les mers - Verne", [("gut", 5097)]),
                ("Le tour du monde en 80 jours - Verne", [("gut", 800)]),
                ("Les trois mousquetaires - Dumas", [("gut", 13951)])],
    "spanish": [("Don Quijote - Cervantes", [("gut", 2000)]),
                ("Niebla - Unamuno", [("gut", 49836)]),
                ("Sangre y arena - Blasco Ibanez", [("gut", 26983)])],
    "italian": [("I promessi sposi - Manzoni", [("gut", 45334)]),
                ("L'amore che torna - Zuccoli", [("gut", 38720)]),
                ("Damiano - Percoto", [("gut", 25178)])],
    "german":  [("Effi Briest - Fontane", [("gut", 5323)]),
                ("Buddenbrooks - Mann", [("gut", 34811)]),
                ("Aus dem Leben eines Taugenichts - Eichendorff", [("gut", 35312)])],
    "latin":   [("De Bello Gallico - Caesar", [("gut", 218), ("gut", 18837)]),
                ("Catilina + Iugurtha - Sallust", [("tll", "sall.1.html"),
                                                   ("tll", "sall.2.html")]),
                ("De Officiis - Cicero", [("tll", "cicero/off1.shtml"),
                                          ("tll", "cicero/off2.shtml"),
                                          ("tll", "cicero/off3.shtml")])],
}
GUT_URL = "https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt"
TLL_URL = "https://www.thelatinlibrary.com/{path}"
HAW_URL = "https://ebible.org/Scriptures/haw1868_usfm.zip"
ENG_MARKERS = ("the", "and", "of")
ENG_LIMIT = 0.005


def H(counter):
    v = np.array(list(counter.values()), float)
    p = v / v.sum()
    return float(-(p * np.log2(p)).sum())


def h2_cross(tokens):
    chars = "".join(tokens)
    return H(Counter(zip(chars, chars[1:]))) - H(Counter(chars))


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


TLL_TAG = None  # lazy import guard for regex


def strip_tll(html_text):
    """The Latin Library page -> body text: drop tags, entities and site boilerplate."""
    import html as H
    import re
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", html_text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = H.unescape(text)
    for phrase in ("The Latin Library", "The Classics Page", "Christmas Nativity Page"):
        text = text.replace(phrase, " ")
    return text


def source_path(lang, src):
    kind, ref = src
    raw = TDIR / lang / "raw"
    if kind == "gut":
        return raw / f"{ref}.txt"
    slug = ref.replace("/", "_").replace(".shtml", "").replace(".html", "")
    return raw / f"tll_{slug}.txt"


def fetch_sources():
    for lang, works in CORPUS.items():
        raw = TDIR / lang / "raw"
        raw.mkdir(parents=True, exist_ok=True)
        for title, sources in works:
            for src in sources:
                path = source_path(lang, src)
                if path.exists():
                    continue
                kind, ref = src
                if kind == "gut":
                    body = textkit.strip_gutenberg(
                        fetch(GUT_URL.format(id=ref)).decode("utf-8", errors="replace"))
                else:
                    body = strip_tll(fetch(TLL_URL.format(path=ref)).decode("latin-1",
                                                                            errors="replace"))
                path.write_text(body, encoding="utf-8")
                print(f"  fetched {lang}/{path.name} ({title}): "
                      f"{len(textkit.clean_tokens(body))} tokens")
                time.sleep(1)


def strip_usfm(text):
    """Drop USFM markers: footnote/xref spans, then every backslash code."""
    import re
    text = re.sub(r"\\f .*?\\f\*", " ", text, flags=re.S)
    text = re.sub(r"\\x .*?\\x\*", " ", text, flags=re.S)
    text = re.sub(r"\\\S+", " ", text)
    return text


def fetch_hawaiian():
    raw = TDIR / "hawaiian" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    path = raw / "haw1868.txt"
    if path.exists():
        return path
    z = zipfile.ZipFile(io.BytesIO(fetch(HAW_URL)))
    parts = []
    for name in sorted(z.namelist()):
        if not name.endswith(".usfm"):
            continue
        up = name.upper()
        if "FRT" in up or "GLO" in up or "BAK" in up:      # front/back matter, often English
            continue
        parts.append(strip_usfm(z.read(name).decode("utf-8", errors="replace")))
    body = "\n".join(parts)
    path.write_text(body, encoding="utf-8")
    print(f"  fetched hawaiian/haw1868 (Ka Baibala Hemolele 1868, eBible.org): "
          f"{len(textkit.clean_tokens(body))} tokens")
    return path


def eng_contamination(tokens):
    c = Counter(tokens)
    return sum(c[m] for m in ENG_MARKERS) / len(tokens)


def main():
    RES.mkdir(exist_ok=True)
    FIG.mkdir(exist_ok=True)
    fetch_sources()
    haw_path = fetch_hawaiian()

    out = {"_meta": {"n": N,
                     "h2": "conditional bigram entropy across the concatenated token stream, "
                           "identical to generate_model.evaluate h2_cross_bits",
                     "hawaiian": "Ka Baibala Hemolele 1868 (eBible.org, public domain), USFM "
                                 "stripped, scripture register, small alphabet floor probe",
                     "exclusions": "works under 30k tokens skipped; Latin works with inline "
                                   "English above 0.5% marker frequency refused"}}
    langs = {}
    allvals = []
    print(f"\n  {'work':52s} {'tokens':>8s} {'h2':>6s}")
    for lang, work_list in CORPUS.items():
        vals = []
        works = []
        for title, sources in work_list:
            body = "\n".join(source_path(lang, s).read_text(encoding="utf-8") for s in sources)
            toks = textkit.clean_tokens(body)
            rec = {"title": title,
                   "sources": [f"{k}:{r}" for k, r in sources], "tokens": len(toks)}
            if len(toks) < N:
                print(f"  {lang} - {title}: only {len(toks)} tokens -- SKIPPED")
                rec.update(h2=None, skipped="under 30k")
                works.append(rec)
                continue
            if lang == "latin":
                cont = eng_contamination(toks)
                if cont > ENG_LIMIT:
                    print(f"  {lang} - {title}: English contamination {cont:.3%} -- REFUSED")
                    rec.update(h2=None, skipped=f"english contamination {cont:.3%}")
                    works.append(rec)
                    continue
            h2 = round(h2_cross(toks[:N]), 3)
            vals.append(h2)
            allvals.append(h2)
            rec["h2"] = h2
            works.append(rec)
            print(f"  {lang + ' - ' + title:52s} {len(toks):8d} {h2:6.3f}")
        langs[lang] = {"works": works, "mean": round(float(np.mean(vals)), 3),
                       "min": min(vals), "max": max(vals), "n_works": len(vals)}
    out["languages"] = langs
    out["band_all_works"] = {"min": min(allvals), "max": max(allvals),
                             "mean": round(float(np.mean(allvals)), 3),
                             "sd": round(float(np.std(allvals, ddof=1)), 3),
                             "n_works": len(allvals)}

    haw_toks = textkit.clean_tokens(haw_path.read_text(encoding="utf-8"))
    out["hawaiian"] = {"tokens": len(haw_toks), "h2": round(h2_cross(haw_toks[:N]), 3),
                       "alphabet": len(set("".join(haw_toks[:N])))}
    voy = S.load_tokens("voynich_eva")
    out["voynich"] = {"h2": round(h2_cross(voy), 3), "n": len(voy)}
    print(f"\n  band across {len(allvals)} works: {min(allvals):.3f}-{max(allvals):.3f} "
          f"(mean {out['band_all_works']['mean']}, sd {out['band_all_works']['sd']})")
    print(f"  hawaiian h2 = {out['hawaiian']['h2']} "
          f"(alphabet {out['hawaiian']['alphabet']} letters)")
    print(f"  voynich  h2 = {out['voynich']['h2']}")

    (RES / "entropy_band.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    # ---- figure: the widened band ----
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    order = list(CORPUS)
    for i, lang in enumerate(order):
        ys = [w["h2"] for w in langs[lang]["works"] if w["h2"]]
        ax.scatter([i] * len(ys), ys, s=60, color="#27632a", zorder=3)
    ax.scatter([len(order)], [out["hawaiian"]["h2"]], s=90, color="#d68910", zorder=3)
    ax.axhspan(min(allvals), max(allvals), color="#27632a", alpha=0.08,
               label=f"band, all {len(allvals)} works")
    ax.axhline(out["voynich"]["h2"], color="#c0392b", lw=2,
               label=f"Voynich {out['voynich']['h2']}")
    ax.set_xticks(range(len(order) + 1))
    ax.set_xticklabels(order + ["hawaiian\n(Bible 1868)"], fontsize=9)
    ax.set_ylabel("h2 (bits) at 30k tokens")
    ax.set_title("The language band, widened: multiple works per language + a "
                 "small-alphabet floor probe")
    ax.grid(True, axis="y", ls=":", alpha=0.3)
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG / "entropy_band.png", dpi=140)
    plt.close(fig)
    print(f"\n  wrote {RES / 'entropy_band.json'}, figures/entropy_band.png")


if __name__ == "__main__":
    main()
