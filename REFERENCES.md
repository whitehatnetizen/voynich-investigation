# References and data sources

Everything this project used, where it came from, and how to obtain it. All sources are public and
require no authentication.

## The source video (origin of the project)

- **"Does the Voynich Manuscript pass the Zipf's Law test?"** — Edwin Wagha, YouTube, uploaded
  2026-06-28, duration 8:51. <https://www.youtube.com/watch?v=ciRmkK9Hytg>
  This project began as a replication of this video's Zipf's-law test and then extended it. The video
  is itself a follow-up to the creator's earlier Shannon-entropy video and responds to viewer
  critiques (autocorrelation, too-few data points, the "lazy forger" failure mode). The video
  compares the Voynich EVA transliteration against six natural languages, each trimmed to 30,000
  tokens, and against a deliberately built algorithmic-gibberish control.

## The manuscript

- **Beinecke MS 408 (the Voynich Manuscript)** — Beinecke Rare Book and Manuscript Library, Yale
  University. Page images are public domain, served via IIIF.
  - IIIF Presentation manifest: <https://collections.library.yale.edu/manifests/2002046.json>
  - Image API pattern: `{service}/full/{size}/0/default.jpg`
  - Used for the full-manuscript label-to-image viewer (not part of this text-only replication set).

## Voynich transliterations (committed to `data/voynich/`)

- **Zandbergen-Landini EVA transliteration** (`ZL3b-n.txt`), IVTFF 2.0 format. The primary text used
  throughout, and the transliteration the source video uses. From René Zandbergen's Voynich site.
  - <http://www.voynich.nu/> (see `data/voynich/README_source.txt` for the format description)
  - IVTFF format and the EVA alphabet: <http://www.voynich.nu/transcr.html>
- **v101 transliteration** (`voyn_101.txt`), by Glen Claston. Carried as a robustness check on the
  glyph-segmentation choice. Distributed alongside the EVA files at voynich.nu.

## Comparison corpora (fetched at run time, not committed)

### Six natural languages (Project Gutenberg, public domain)

Fetched by `fetch_corpora.py`. Each language's first work supplies the 30,000-token series; the
second is kept for bootstrap resampling. Plain-text URL pattern:
`https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt`

| Language | Primary work (Gutenberg id) | Extra work (id) |
|---|---|---|
| English | Pride and Prejudice, Austen (1342) | Moby-Dick, Melville (2701) |
| French  | Vingt mille lieues sous les mers, Verne (5097) | Le tour du monde en 80 jours, Verne (800) |
| Spanish | Don Quijote, Cervantes (2000) | Niebla, Unamuno (49836) |
| Italian | I promessi sposi, Manzoni (45334) | L'amore che torna, Zuccoli (38720) |
| German  | Effi Briest, Fontane (5323) | Die Leiden des jungen Werther, Goethe (2407) |
| Latin   | De Bello Gallico I-IV, Caesar (218) | De Bello Gallico V-VIII, Caesar (18837) |

### Additional register and control corpora

- **Hebrew (the paradigm abjad control)** — the Torah (Genesis, Exodus, Leviticus, Numbers,
  Deuteronomy), Hebrew consonantal text with vowel-points and cantillation stripped. Fetched by
  `fetch_hebrew.py` from the Sefaria API: `https://www.sefaria.org/api/v3/texts/{book}?version=hebrew`
  Sefaria texts are released under open licences (this Tanakh text is public domain).
- **Technical Latin (botanical register)** — Pliny the Elder, *Naturalis Historia*, books XII-XXVI
  (trees, plants, garden crops, plant-derived remedies). Fetched by `fetch_technical_latin.py` from
  Latin Wikisource via the MediaWiki parse API: `https://la.wikisource.org/w/api.php` (Wikisource text
  is CC BY-SA / public domain). The Latin Library (<http://www.thelatinlibrary.com/>) only carries
  Pliny books 1-5, hence Wikisource for the botany span.
- **Topical Latin (five distinct subjects, for the section-clustering test)** — Manilius
  *Astronomica* and Cato *De Agri Cultura* (The Latin Library), Vitruvius *De architectura* I (Latin
  Wikisource), combined with the Caesar and Pliny texts already fetched. Fetched by
  `fetch_topical_latin.py`.
- **Linnaean nomenclature (naming register)** — about 33,000 accepted plant-kingdom species canonical
  binomials. Fetched by `fetch_nomenclature.py` from the GBIF species-search API:
  `https://api.gbif.org/v1/species/search` (Plantae, backbone key 6). GBIF data are openly licensed.
- **Esperanto (a meaningful constructed-language control)** — public-domain Esperanto prose from
  Project Gutenberg (Fundamenta Krestomatio and others). Public-domain plain text.

## Key prior work referenced in the analysis

- **T. Timm and A. Schinner (2019), "A possible generating algorithm of the Voynich manuscript",**
  *Cryptologia* 44(1), 1-19. <https://doi.org/10.1080/01611194.2019.1596999>
  The self-citation copy-and-mutate model tested in Step 8 is theirs; this project supplies an
  independent, shuffle-controlled test of it with real null distributions.
- **G. A. Miller (1957), "Some effects of intermittent silence",** *American Journal of Psychology*
  70(2), 311-314. The result that random typing with spaces produces a Zipf-like rank-frequency curve,
  which is why the "monkey text" control matters in Step 1.
- **Zipf's law**: <https://en.wikipedia.org/wiki/Zipf%27s_law>
- **Heaps' law** (vocabulary growth): <https://en.wikipedia.org/wiki/Heaps%27_law>

## Software

Python standard library plus `numpy`, `scipy`, `matplotlib`, `rapidfuzz` (Damerau-Levenshtein edit
distance), and `regex`. See `requirements.txt`. All open-source.
