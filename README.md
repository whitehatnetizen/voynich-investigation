# Voynich Manuscript: a statistical characterisation

**Illustrated walkthrough: <https://whitehatnetizen.github.io/voynich-investigation/>** (the whole
investigation, plate by plate, with charts, collapsible algorithms and a conclusion sheet).

A reproducible statistical study of the text of the Voynich Manuscript (Beinecke MS 408). It began
as a replication of a YouTube video's Zipf's-law test and grew into a full characterisation of what
*kind of thing* the text is. It does not attempt to read or decode the manuscript.

**Headline finding.** A purely mechanical generation process reproduces essentially every internal
statistic of the Voynich text. The strongest single piece of evidence is a self-citation copy signal
(each word resembles a nearby recent word, mutated), which is absent from real prose, a real Latin
word list, and enciphered Latin. Two anomalies drive the result: unusually low second-order
character entropy (h2 about 2.4 bits, versus 3.42 to 3.60 for six reference languages) and unusually
uniform word length. One thing a mechanical generator does not fully reproduce is long-range
structure: the vocabulary tracks the illustrated content down to the individual page. So a
formulaic-but-meaningful reading is not excluded, though a rich, distinctive catalogue is.

The full plain-language narrative, one hypothesis at a time, is in **[STORY.md](STORY.md)**.

## What is in this repository

```
scripts/       all analysis code (Python), one concern per file
data/voynich/  the Voynich transliteration inputs (public research data)
results/       reference JSON outputs for the headline analyses (expected numbers)
docs/          the illustrated walkthrough (served as the GitHub Pages site)
STORY.md       the investigation as a chain of hypotheses (markdown source of the walkthrough)
REFERENCES.md  every external source, dataset and download, with URLs
```

The language corpora, derived token files, and figures are **not** committed (they are large and, for
the modern-edition texts, better fetched than redistributed). The fetch scripts below regenerate them
from their public sources.

## Requirements

Python 3.10 or newer. Install the dependencies:

```
pip install -r requirements.txt
```

(`numpy`, `scipy`, `matplotlib`, `rapidfuzz`, `regex`.)

## Reproducing the pipeline

Every script is runnable from the `scripts/` directory and writes to `data/` or `results/`. Run them
in this order. Steps 0 and 1 build the data; steps 2 onward are the analyses, each independent.

### 0. Fetch the source texts

```
cd scripts
python fetch_voynich.py            # parse data/voynich/*.txt -> eva/v101 token lists
python fetch_corpora.py            # 6 language prose corpora from Project Gutenberg
python fetch_hebrew.py             # Torah (Hebrew, the paradigm abjad control) from Sefaria
python fetch_technical_latin.py    # Pliny, Naturalis Historia (technical botany register)
python fetch_nomenclature.py       # 33k Linnaean plant binomials (naming register) from GBIF
python fetch_topical_latin.py      # five distinct-topic Latin works (for the section test)
```

All sources are public and require no authentication. The fetchers are polite (rate-limited) and
document their exact sources in [REFERENCES.md](REFERENCES.md).

### 1. Build the analysis-ready token series

```
python build_tokens.py             # clean + trim every series to 30,000 tokens
python build_controls.py           # the two null-model controls (uniform pool, monkey text)
```

Both write to `data/tokens/<series>.txt`. Every downstream analysis reads from there.

### 2. The analyses

Each script maps to a step in [STORY.md](STORY.md) and writes a JSON into `results/`. The `results/`
folder in this repository already holds the reference outputs, so you can compare your run against
the published numbers.

| Script | Story step | What it measures |
|---|---|---|
| `zipf_analyse.py` | 1, 2 | rank-frequency (Zipf) curves; nearest-language distances |
| `discriminators.py` | 3 | second-order character entropy h2; word-length spread |
| `register_test.py` | 4 | h2 across Latin registers (prose, technical, naming) |
| `slot_grammar.py` | 6 | affix-kit coverage; within-word glyph slots |
| `word_syntax.py` | 7 | word-order information, with a shuffle control |
| `self_citation.py` | 8 | copy-and-mutate signal vs a 200-shuffle null |
| `generation_tournament.py` | 9 | one mechanical generator scored on 17 metrics |
| `long_range_mi.py` | 10 | cross-word mutual information out to 800 words |

Determinism: every stochastic step is seeded (`SEED = 1492`), so results are exactly reproducible.
Null distributions use 200 seeded shuffles (`random.Random(SEED + rep)`) and report z-scores against
the null spread.

## Method notes

- **Tokenisation.** In the IVTFF transliteration a word break is a `.` or a `,`; both are treated as
  spaces. Tags, comments and uncertain-glyph markers are stripped. This rule drives every number and
  is documented at the top of `fetch_voynich.py`.
- **Length control.** Every series is trimmed to exactly 30,000 tokens, matching the source video, so
  vocabulary-growth statistics are comparable across languages.
- **Two transliterations.** The primary analysis uses the Zandbergen-Landini EVA transliteration; the
  v101 scheme is carried as a robustness check, since a glyph-vs-letter segmentation choice could in
  principle drive the entropy result. It does not: the anomaly survives both.
- **The essential control.** The slot grammar already makes all Voynich words mutually edit-similar,
  so any copy or similarity statistic is meaningless without a control that keeps the vocabulary and
  affixes identical but destroys word order. Throughout, that control is a shuffle of the same tokens,
  and only a real-versus-shuffle *excess* is reported as evidence.

## Scope and honesty

This is sufficiency, not necessity. Showing that a mechanical process *can* reproduce the statistics
does not prove the manuscript is meaningless; a sufficiently formulaic real text is not excluded by
internal statistics alone. The one measurement that leans the other way is long-range information,
which the best mechanical generator only partly reproduces. Separating the two remaining readings
requires the pictures, not the text: whether the labels match the images they sit beside. That work
is summarised at the end of STORY.md and is not part of this text-only replication set.

## Licence

The code is released under the MIT Licence (see `LICENSE`). The data are not covered by that licence;
see [REFERENCES.md](REFERENCES.md) for the provenance and terms of each source. The Voynich
transliteration files are freely available research data; the modern-edition comparison texts are
fetched from their public repositories at run time rather than redistributed here.
