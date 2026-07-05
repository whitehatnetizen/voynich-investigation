# The Voynich investigation: a chain of hypotheses

*An account of how this project unfolded. Each step states a hypothesis in plain language, the test
performed, the result, and the question that opened next. Numbers are the current (2026-07-05,
post-review) values. Where an earlier number was corrected, the correction is noted. Source data:
`results/*.json`. Full detail: `FINDINGS.md` and `review/FINDINGS-UPDATE-2026-07-04.md`. Collapsible
blocks contain the core algorithms; complete scripts are in `scripts/`.*

The Voynich Manuscript is a roughly 240-page illustrated book in an unknown script that no one has
read in 600 years. This project does not attempt to read it. It asks a narrower, answerable
question: what kind of thing is this text, statistically? The evidence is then followed one
hypothesis at a time.

---

## Step 1: Does it behave like language at all?

**Hypothesis.** If the Voynich is real writing, its words should follow Zipf's law. The most common
word appears about twice as often as the second, three times as often as the third, and so on: the
straight-line-on-a-log-log-plot signature every natural language shares.

**How we tested it.** We counted every word, ranked them by frequency, and plotted rank against
frequency on log-log axes, next to six real languages and two controls: uniform-pool gibberish
(a fixed pool of 1,000 invented words used equally often) and a "monkey text" of
random letters with spaces.

**Result: validated, with low discriminating power.** The Voynich lies on the same descending
diagonal as the six languages. The uniform-pool gibberish fails: a near-horizontal line (fitted
slope -0.05) that drops abruptly at its 1,000-type limit. The monkey text is not on the diagonal:
its curve is stepped, with a plateau of equally common short words at the lowest ranks, and its descent is
shallower than the languages' (fitted slopes -0.49 to -0.69 depending on rank range, against about
-0.9 for the languages and the Voynich). It nevertheless passes a loose Zipf test. A test that
random typing nearly passes cannot separate meaningful text from mechanical text production; Zipf
conformity constrains word-frequency structure, not meaning.

<details>
<summary>Algorithm: the two control texts (scripts/build_controls.py)</summary>

```python
SEED = 1492   # fixed seed; both controls are exactly reproducible
N = 30000     # tokens per control, matching the analysis window

def build_uniform_pool(rng):
    """Control 1: ~1,000 invented words drawn UNIFORMLY.
    Every word has the same probability, so the rank-frequency curve is
    flat until the pool runs out, then drops off a cliff."""
    pool = set()
    while len(pool) < 1000:
        w = rng.choice(PREFIXES) + rng.choice(ROOTS) + rng.choice(SUFFIXES)
        pool.add(w)
    pool = sorted(pool)
    return [rng.choice(pool) for _ in range(N)]

def build_monkey(rng, mean_len=5.0):
    """Random typing: characters drawn i.i.d. from a 26-letter alphabet
    plus a space, P(space) = 1/(mean_len+1) so mean word length ~5,
    matching the natural-language set. Shorter strings are exponentially
    more likely, which produces a descending rank-frequency curve
    (Miller 1957) with no meaning present."""
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
```
</details>

**Next question.** If Zipf cannot separate it from noise, is its shape closer to one particular
language?

---

## Step 2: Is its word-frequency curve nearest a specific language?

**Hypothesis.** The exact bend of the rank-frequency curve is language-specific. The Voynich's curve
should sit nearest whichever of the six languages it is most like.

**How we tested it.** We measured the distance from the Voynich's curve to each language's curve
three ways: by exponent, by curve-shape error, and by distributional divergence.

**Result: inconclusive.** By slope it is nearest Latin. By whole-curve shape, nearest German. The
two answers disagree, and the "nearest" is determined by morphology and tokenisation rather than by
content. (A "German wins 91% of bootstrap draws" figure from this step was later retired: the draws
were overlapping windows, an artefact of corpus length rather than a real margin.)

**Next question.** Rather than which language it most resembles: which of its statistics fall
outside the range of every language at once?

---

## Step 3: What is actually anomalous about the script?

**Hypothesis.** If the surface statistics look normal, a deeper one may be abnormal, specifically
how predictable each character is from the one before it.

**How we tested it.** We measured second-order character entropy, h2: the uncertainty about the
next glyph given the current one. We also measured the spread of word lengths, for the Voynich and
every language.

**Result: two anomalies outside the language range.** The Voynich's h2 is about 2.4 bits, against
3.42 to 3.60 for the reference languages: its glyphs are far more predictable than any of the real
scripts measured. Its word lengths are also unusually uniform, with a standard deviation of 1.82
against 2.4 to 2.9 for languages. These two facts are what the rest of the project has to explain.

<details>
<summary>Algorithm: second-order character entropy h2 (scripts/discriminators.py)</summary>

```python
def char_entropy(tokens):
    """h1 = entropy of single characters; h2 = conditional entropy
    H(c_i | c_{i-1}) = H(bigram) - H(unigram). Low h2 means the current
    character strongly determines the next one."""
    chars = "".join(tokens)
    n = len(chars)
    uni = Counter(chars)
    h1 = -sum((c / n) * np.log2(c / n) for c in uni.values())
    bi = Counter(zip(chars, chars[1:]))
    nb = sum(bi.values())
    h_bi = -sum((c / nb) * np.log2(c / nb) for c in bi.values())
    h2 = h_bi - h1
    return h1, h2, len(uni)
```
</details>

**Next question.** The manuscript is largely a herbal. Could the low entropy be a
specialised-vocabulary effect?

---

## Step 4: Is the anomaly just a technical register?

**Hypothesis.** Botanical or technical writing has repetitive vocabulary. The right comparison is
not a novel but a herbal, and against that the Voynich might look normal.

**How we tested it.** We added three Latin "registers": narrative prose (Caesar), technical
botanical prose (Pliny's *Natural History*), and pure naming (33,000 Linnaean plant binomials). Then
we re-measured h2 and word length.

**Result: refuted.** All three registers cluster at h2 near 3.45 to 3.52, while the Voynich is
isolated at 2.4. Botanical text accumulates rare plant and drug names, which raises entropy; the
naming-heavy registers are furthest from the Voynich, not nearest. The low-entropy anomaly is not a
register effect. It is a property of the notation system, not of the subject matter.

**Next question.** If it is not a natural register, is it a real language hidden under a cipher?

---

## Step 5: Is it an enciphered natural language?

**Hypothesis.** A real language run through a cipher would look alien on the surface but carry a
recoverable signal underneath.

**How we tested it.** Three tests. First, a substitution cipher, though a one-for-one glyph swap
cannot change entropy at all, so it is excluded by arithmetic. Second, a verbose transform with
abbreviation and affixes, pushed from each language toward the Voynich's statistics. Third,
"peeling" the Voynich's affixes off to see whether a language surfaces underneath.

**Result: no simple cipher fits.** Substitution is mathematically excluded, since it cannot lower
h2. The verbose transform reaches the low h2 and the narrow word length, but it does so equally from
Latin, English and German, which implicates the transform rather than any source language, and it
still misses other statistics. Peeling reveals no language underneath. A positive control applied
the same method to genuinely enciphered Latin and recovered 23 of 25 glyphs, so the null result on
the Voynich is not a failure of the method.

**Next question.** If no simple cipher generates these statistics, what mechanism produces low
entropy and uniform word length directly?

---

## Step 6: What within-word mechanism produces the low entropy?

**Hypothesis.** The words are built from a small kit of fixed pieces in fixed positions, a "slot
grammar", so the next glyph is nearly determined by the current one.

**How we tested it.** We measured per-position glyph menus, the coverage of a small affix kit, and
whether a simple Markov glyph-transition model reproduces the low h2.

**Result: validated, with a remainder.** A small affix kit covers 66 to 79% of all words, against
33 to 53% for languages. Glyph transitions are about twice as concentrated as in any of the
languages, and a Markov model reproduces the low h2. Two constraints sit on top of this and are not
consequences of the slot grammar: the narrow word-length band, which no glyph model reproduces, and
elevated whole-word repetition. An additional process regulates word length and reuses whole words.

**Next question.** How are the words arranged in sequence? Is there grammar between words?

---

## Step 7: Is there language-like word order?

**Hypothesis.** In real language the previous word strongly predicts the next, through syntax and
collocation. The Voynich should show the same if it carries sentences.

**How we tested it.** We measured word-order information, how much the previous word reduces
uncertainty about the next, with a shuffle control to cancel sample-size bias.

**Result: almost none.** Word order carries about 1.7% of the word-level uncertainty, against 2.6 to
7.4% across the prose languages. (Technical Latin, at 1.2%, sits just below it, so the statistic is
register-relative.) The token stream is nearly unordered. This is inconsistent with obscured
connected prose and consistent with a list, a catalogue, or table-driven generation.

<details>
<summary>Algorithm: word-order information with a shuffle control (scripts/word_syntax.py)</summary>

```python
def order_info(tokens, nshuf=200):
    """How much does the previous word reduce uncertainty about the next?
    order_info = H(w_i | w_{i-1}) on SHUFFLED text minus the same on real
    text. The shuffle term cancels the finite-sample bias that makes raw
    conditional entropy look informative on any corpus."""
    H_cond = cond_H(zip(tokens, tokens[1:]))
    shuf = []
    for rep in range(nshuf):
        arr = list(tokens)
        random.Random(SEED + rep).shuffle(arr)
        shuf.append(cond_H(zip(arr, arr[1:])))
    H_shuf, sd = mean(shuf), std(shuf)
    return H_shuf - H_cond, (H_shuf - H_cond) / sd   # bits, z-score
```
</details>

**Next question.** If word order is nearly random but the words are locally repetitive, is each word
copied from a nearby recent word and lightly changed?

---

## Step 8: Is the text generated by copying and mutating recent words?

**Hypothesis (the "self-citation" model, Timm & Schinner 2019).** Each word is produced by copying
a recent word and rewriting it with a small change. If so, a word should resemble one of its recent
predecessors more than chance allows, and more so for nearer predecessors.

**How we tested it.** For each word we found the minimum edit distance to the previous few words,
and compared it against a shuffle of the same tokens, which destroys sequential copying but keeps
the vocabulary and affix kit identical. We tracked three signatures: a below-shuffle nearest
distance, an excess of near-identical neighbours, and a locality gradient in which nearer means
more similar.

**Result: validated; the largest effect sizes in the project.** All three signatures exceed their null distributions by wide
margins: a nearest-distance excess at z of about 78, a copy spike at z of about 50, and a
locality gradient at z of about 23, all against 200-shuffle null distributions. Hebrew, repetitive
scripture in a short abjad, matches the exact-repeat part but not the local gradient, so the
Voynich's copying is specifically local. A single process accounts for the slot grammar, the
near-zero word order and the local repetition: copy a nearby word and mutate it.

<details>
<summary>Algorithm: the shuffle-controlled copy test (scripts/self_citation.py)</summary>

```python
def nearest_distance(tokens, W):
    """For each word, the minimum Damerau-Levenshtein edit distance to
    any of the previous W words. Distance 0 = exact copy; distance 1 =
    copy plus one change (the model's core prediction)."""
    out = []
    for i in range(W, len(tokens)):
        out.append(min(DL.distance(tokens[i], tokens[i - k])
                       for k in range(1, W + 1)))
    return mean(out)

# THE essential control: the slot grammar alone makes all Voynich words
# mutually similar, so a low raw distance proves nothing. Reorder the
# SAME tokens (identical vocabulary, copying destroyed) and recompute.
# Only distance BELOW the shuffle is evidence of copying.
real = nearest_distance(tokens, W)
null = [nearest_distance(shuffled(tokens, seed=SEED + rep), W)
        for rep in range(NSHUF)]
excess = mean(null) - real          # positive = copying
z = excess / std(null)
```
</details>

**Next question.** If copying explains the pieces, can one generator reproduce the whole statistical
fingerprint at once?

---

## Step 9: Can one mechanical generator reproduce everything?

**Hypothesis.** A single generator combining length-locked word-forms, copy-and-mutate, and a mild
per-section vocabulary bias reproduces all the Voynich's statistics, with no meaning anywhere.

**How we tested it.** A "tournament": specialist generators, each targeting one trait, against
unified ones, all scored on the same 17-metric fingerprint against the real Voynich. The copy
parameters were tuned only on the copying metrics, so traits like the Zipf slope and vocabulary size
are free to emerge or not.

**Result: mechanical generation is sufficient.** The four-parameter unified generator reproduces the
whole fingerprint (combined error 0.179) better than any specialist (best specialist 0.274), and the
Zipf slope, type count and Heaps growth emerge without being fitted (generator Zipf -0.87 against
Voynich -0.89). Nothing in the internal statistics requires meaning. Sufficiency is not necessity,
so a highly formulaic real text is not excluded, but no meaning is needed.

<details>
<summary>Algorithm: the unified generator U2 (scripts/generation_tournament.py)</summary>

```python
def gen_u2(markov_model, rng, sizes, W, p_copy, overlap):
    """Four-parameter generator. Word forms come from a glyph-level
    Markov model, length-locked by rejection to the Voynich's empirical
    length profile (gives low h2 + the narrow length band). The token
    stream then mixes three moves per word:
      p_copy        copy one of the last W words and mutate it
                    (regenerate the last 1-2 glyphs via the same Markov
                    model, so mutations stay in-grammar)
      overlap       draw a fresh word from the global pool
      otherwise     draw from this section's sub-pool (mild topic bias)
    Zipf slope, type count and Heaps growth are NOT fitted; they emerge."""
    pool = gen_lenlock(markov_model, rng, sum(sizes), VOY_LENS)
    section_pools = split_by_frequency(pool, len(sizes))
    out = []
    for sec, m in enumerate(sizes):
        buf = []
        for _ in range(m):
            if len(buf) >= 2 and rng.random() < p_copy:
                w = mutate(rng.choice(buf[-W:]), markov_model, rng)
            elif rng.random() < overlap:
                w = draw(pool, rng)
            else:
                w = draw(section_pools[sec], rng)
            buf.append(w); out.append(w)
    return out
```
</details>

**Next question.** A book-length message must carry long-range structure: topics, reference. Does
the Voynich carry information across long distances, or does it go flat like a memoryless generator?

---

## Step 10: Does it carry the long-range information a message needs?

**Hypothesis.** If it is meaningless local generation, mutual information between words should
collapse within a few words. If it carries content, information should persist across hundreds of
words.

**How we tested it.** We measured mutual information between words d apart, split into repetition
(the same word recurring) and association (different words predicting each other, which is where a
message's information lives), out to 800 words, against a 200-shuffle null.

**Result: positive; this weighs against the pure-generation account.** The Voynich carries
long-range association information, at a signed excess of +0.16 bits and z of about 9, which a
single real work does not. The mechanical generator reproduces at most about a third of it under a
generous accounting, and none of it under the strict signed accounting, where its excess comes out
negative like the real languages'. Under both accountings it misses the smooth positive decay. The information tracks the illustrated
content down to the individual page, since adjacent folios share vocabulary that decays with
distance.

<details>
<summary>Algorithm: long-range mutual information, split self/cross (scripts/long_range_mi.py)</summary>

```python
def mi_parts_coded(codes, V, d):
    """Mutual information between the word at position i and the word at
    i+d, on an integer-coded stream. Split into SELF (the same word
    recurring: burstiness) and CROSS (different words predicting each
    other: where a message's information lives)."""
    a, b = codes[:-d], codes[d:]
    n = a.size
    ca = np.bincount(a, minlength=V)
    cb = np.bincount(b, minlength=V)
    uk, cc = np.unique(a * V + b, return_counts=True)   # joint counts
    x, y = uk // V, uk % V
    term = (cc / n) * np.log2((cc * n) / (ca[x] * cb[y]))
    same = x == y
    return term[same].sum(), term[~same].sum()          # self, cross

# Null: 200 seeded permutations of the stream. The reported budget is
# the SIGNED sum of (real - null_mean) over d >= 32: no clipping at
# zero.
```
</details>

**Interpretation.** Two readings survive, and they differ almost only in the labels.

1. Meaningless auto-generation: a scribe following a practiced word-building habit, with
   vocabulary drifting slowly as the pictures change. This is the reading favoured by the internal
   statistics.
2. A meaningful but highly formulaic catalogue or label text: real content, but so templated that
   its statistics mimic generation.

Internal statistics cannot cap the information further. One test separates them: do the labels
match the pictures they sit beside?

---

## Step 11: Adversarial review, then a statistical re-audit

**Hypothesis.** Our conclusions might be artefacts of weak controls.

**How we tested it.** Two rounds. First an adversarial red-team (R1 to R6): is the pattern unique to
meaningless text, is it Latin-derived, does it survive a different transcription and aggressive glyph
re-segmentation? Then a full statistical review found that the project leaned on 2-to-3-shuffle
nulls, and re-ran everything against 200-shuffle real null distributions with z-scores.

**Result: the main findings hold; several sub-claims were corrected.** The low h2, the narrow word
length, and the self-citation copy signal all hold under attack. The self-citation signal is absent
from real prose, from a real Latin word list, and from enciphered Latin. Several figures were revised
downward: the "~75%" long-range reproduction became "about a third" (Step 10), a "faint
stable-collocation layer" was retracted at about 1 sigma, and a "5% Currier-dialect" component of
the structure became statistically zero, and the topical-clustering signal halved under a
burstiness-robust null. All corrections reduced the strength of previously published claims; most
favoured the mechanical reading, while the long-range correction favoured the content reading.

**Next question.** With honest nulls in hand, are there hypothesis tests that could still break the
mechanical account, or find meaning where we have not looked?

---

## Step 12: Targeted falsification tests

Six tests, each specified in advance with an outcome that would count against the leading
hypothesis.

**T1: Is the copy source the line above (physical page-copying)?** We compared each word's similarity
to the previous words in the stream against the words directly above it on the page. Both beat the
folio-vocabulary control by a wide margin, and vertical came out about level with linear. The
copying is local but not specifically visual: a memory-window process, which no natural language
process produces in either direction.

**T3: Is there language-like structure in any subset? (the direct falsifier).** We measured word
order in every section, scribal hand and locus type, and tested whether affixes agree across word
boundaries. No subset has language-like word order. One statistic fired: a word's ending predicts
the next word's beginning as strongly as Latin's grammatical agreement does (z of about 80), it
survives excluding copied words, and the mechanical generator as first built missed it entirely.
This localised the residual word-order signal: a real cross-word rule, not full syntax, but a
genuine constraint between words. A follow-up later recovered about 40% of it mechanically: adding
habits taken unchanged from Timm's generator implementation, an ablation shows one habit carries
the whole effect, sometimes cutting a written word in two. The cut halves of a real word meet at a
genuine glyph transition, and that seam, seen from outside, is exactly "ending predicts beginning"
(`results/u3_report.md`). How often the scribes actually cut words, and the remaining 60% of the
signal, stay open.

<details>
<summary>Algorithm: cross-word affix agreement (scripts/t3_syntax_hunt.py)</summary>

```python
def agreement(lines_tokens, fa, fb, exclude_copies, nshuf=200):
    """MI between fa(word_i) and fb(word_{i+1}) over adjacent within-line
    pairs, against a within-line shuffle. fa/fb extract affixes, e.g.
    fa = last two glyphs (suffix), fb = first two glyphs (prefix).
    exclude_copies drops pairs with edit distance <= 1, so the copying
    mechanism cannot mimic agreement."""
    def build_pairs(lines):
        out = []
        for ln in lines:
            for a, b in zip(ln, ln[1:]):
                if exclude_copies and DL.distance(a, b) <= 1:
                    continue
                out.append((fa(a), fb(b)))
        return out
    real = pair_mi(build_pairs(lines_tokens))
    null = [pair_mi(build_pairs(shuffle_within_lines(lines_tokens, SEED + r)))
            for r in range(nshuf)]
    return real - mean(null), (real - mean(null)) / std(null)
```
</details>

**T4: One scribe's habit, or a taught method?** All four legible scribal hands carry the same
fingerprint of low h2, narrow length and local copying. No hand writes normal language. This is
consistent with a shared, taught method across a workshop.

**T6: Can a meaningful invented language explain the profile?** Esperanto, a real constructed
language with deliberately regular morphology, run through the same pipeline: it lands with the
natural languages (h2 3.44, broad word lengths, strong word order, no local copying gradient), far
from the Voynich. Inventedness with meaning does not produce the profile.

**T2: Do the same plants get the same names?** Plants drawn in both the herbal and pharmaceutical
sections should share label vocabulary if labels are names. Text-side, the pharmaceutical labels
reuse the herbal name-slot vocabulary less than random draws would: the labels are their own diverse
register, with no shared naming vocabulary.

**T8, step 1: Do the zodiac star-labels behave like a naming catalogue?** The labels recur across the
12 zodiac pages more than fresh random draws would, and they copy locally, but not more than their
own frequency distribution scattered at random would. The recurrence is a register effect, not a
page-specific naming catalogue. The decisive separation still requires the pictures.

---

## Step 13: The remaining decisive test, and a generator aimed at the gap

**Where it stands.** The mechanical account is sufficient for every internal statistic. The one
place it under-reproduces is page-level structure: the long-range association that tracks the
illustrated content, and the folio-to-folio vocabulary drift. That is the axis on which "meaningless
generation in front of the pictures" and "meaningful text about the pictures" are hardest to tell
apart.

Two moves aim at that gap.

The label-to-image test now has a first-pass answer. We built a full-manuscript viewer pairing
Beinecke's page scans (226 of 227 folios) with the transcription line by line, then read the zodiac,
herbal and pharmaceutical pages directly. The result splits along a layout-versus-content seam. The
layout is a catalogue: one label sits at each star-holding nymph in the zodiac wheels, and one above
each root fragment on the pharmaceutical page, so the makers did place text at the objects it
belongs to. But the content is filler: two adjacent, interchangeable nymphs carry near-identical
labels, six visibly different roots carry minor variants of the same small stem, and the herbal
pages, where a caption-catalogue would show its clearest plant names, have almost no labels at all.
The labels do not behave like a working naming system. The evidence favours labels-as-register,
moderately rather than decisively. What the pictures exclude with more confidence is a rich,
distinctive catalogue: 30 interchangeable figures and six different roots would not carry near-identical
labels if each named a distinct thing.

An illustration-conditioned generator attacks the same question from the mechanical side. We built a
generator whose method depends on the page's illustrated class: each section gets its own word-form
kit, copy rate and window, and each page's vocabulary drifts slowly from the last. Page-conditioning
moves the long-range excess from the section-only generator's -0.12 to +0.03, a real improvement,
but it reaches only about 15% of the Voynich's value and still does not reproduce the folio-to-folio
drift. The page-level drift is the structure the generators reproduce least, and it is the same
structure the label-to-image test probes from the meaning side.

**Next question.** The labels get their own examination: do they name anything at all?

---

## Step 14: The label-image census

**Hypothesis.** If meaning survives anywhere, it is in the labels, and a naming layer has visible
signatures: the same referent carries the same label, a recurring label keeps its position, and
special objects carry special words.

**How we tested it.** A census of the label layer made the first visual reading quantitative,
under four decision rules fixed before the data was collected, so the statistics could not be
chosen to flatter the hypothesis: slot recurrence across the twelve zodiac medallions (298 ring
figures), label distance on near-identical nymph pairs, label identity on recurring pharmaceutical
root drawings, and the words under the central zodiac animals. 1,000-rep permutation nulls
throughout.

**Result: register, not a naming catalogue.** C1: labels that recur across zodiac pages do not re-occupy the same angular slot
(z = -1.4 against a within-page permutation null; a star catalogue in fixed order would). C2: across
18 pairs of near-identical star-nymphs, the labels are exactly as distinct as random pairs from the
label pool (z = +0.9, matched on both labels' lengths): a shared register, not shared names. C3: the
pharmaceutical root drawings turn out to be a diverse set with almost no genuine same-referent
repeats (itself evidence against a cross-referenced catalogue), and the one clear repeated root
(f89r1/f89r2) carries two different labels. C4: only one of twelve zodiac medallions has a
Voynichese word under its central animal; the words under the others are month names in a later
hand, so there is no per-sign name set to test. No rule fired in the naming direction. The label
layer is a register, not a naming catalogue.

**Next question.** Before closing, the hypothesis this project tested owes its origin a test of
its own: score the published implementation of the self-citation idea on the same instruments.

---

## Step 15: The prior-art test

**Hypothesis.** The self-citation hypothesis is Timm and Schinner's, and they published a working
generator implementation. Scored on this project's instruments, it should match the Voynich where
its mechanisms overlap ours, and its design differences should appear as measurable deviations.

**How we tested it.** We cloned the published implementation (MIT-licensed, the paper's
additional-materials repository) and scored its shipped deterministic sample (pseudorandom seed
19; 10,832 tokens) through the same harness as every other text in this project, size-matched
against the Voynich and our U2 at the same token count (`scripts/timm_generator_eval.py`).

**Result: shared core, measured deviations.** Where it matches: mean word length (4.71 vs the
Voynich's 4.69), word-order information (0.0106 vs 0.0102; our U2 measures 0.0007, so its
line-and-paragraph machinery captures word-order structure U2 lacks) and adjacent repetition.
Where it deviates: too much exact copying (excess 0.064 vs 0.035), too weak a locality gradient
(0.023 vs 0.086), a vocabulary that is too small (2,228 types vs 3,154, size-matched) with a
correspondingly steep Zipf slope (-0.98 vs -0.83), and over-uniform word lengths (sd 1.56 vs
1.80). The design difference behind the deviations: it fixes about 20 configured constants plus
hand-coded glyph-legality tables, where U2 fixes four parameters; the two implementations answer
different questions (available fidelity versus minimal sufficient machinery). One deviation is
diagnostic rather than a defect: its output shows suffix-to-prefix agreement at z = 5.4 where our
U2 shows none (z = -1.1; the Voynich measures 22.9 at this sample size), so something in its rule
set produces the Step 12 agreement structure mechanically.

**Next question.** Which of its rules produces the agreement? Transplant them into U2 one family
at a time and measure.

---

## Step 16: The split-word test

**Hypothesis.** One grammar-like structure resisted the mechanical account: a word's ending
predicts the next word's beginning about as strongly as Latin agreement (Step 12), and Timm's
implementation produces a measurable part of it (Step 15). Some specific rule in that
implementation must generate the structure without meaning.

**How we tested it.** We extended our generator to U3: U2's four parameters unchanged, plus five
moves transplanted from Timm's implementation at the probabilities in his shipped configuration
(give a copied word the ending of another recent word; write a long word as two consecutive
tokens; join two short neighbours; derive the next word from the one just written; when copying,
prefer the word directly above). Nothing was fitted to the agreement statistic and the success
criterion was fixed before the first run. Then single-move ablations: disable one move at a time,
regenerate, re-measure. Stability checked across four random seeds.

**Result: the split move accounts for it.** U3 raises the agreement excess from U2's 0.002 bits
(z = 0.5) to 0.084 bits (z = 24.2; z = 21 to 24 across four seeds), which is 42% of the Voynich's
0.198 bits (z = 61.6) on the same 30,000-token harness. The other fingerprint metrics stay within
U2's range, except the exact-copy excess, which falls from 0.025 to 0.013 (Voynich: 0.048).
Single-move ablations isolate the source: with the token-splitting move disabled the excess drops
to -0.003 bits (z = -0.8), while disabling any other move leaves z between 17 and 20. The
splitting move writes a token of six or more glyphs as two consecutive tokens, cut at a random
interior point. Each such pair spans a transition that was word-internal, and word-internal
transitions are where the script's predictability is concentrated (h2 = 2.4 bits, Step 3), so the
suffix-to-prefix statistic registers that transition as cross-token dependence: relocating a word
boundary converts within-word structure into measured between-word structure. Independent support
for the move: split and joined variants of the same string occur on adjacent lines (`olchedy`,
f75v line 19; `ol chedy`, line 18), and EVA word boundaries are known to be uncertain.
Unexplained remainder: 58% of the agreement excess, the reduced exact-copy excess, and the
manuscript's actual splitting rate, which is countable and was not measured here. Details:
`results/u3_report.md`, `results/u3_generator.json`.

---

## Conclusion

The results support a specific account of the Voynichese text. Its two statistical anomalies, a
conditional character entropy near 2.4 bits and a word-length standard deviation of 1.82, are
reproduced, together with the rest of the 17-metric fingerprint, by a four-parameter process of
local copying with small mutations; the copy signatures that identify this process are the largest
effects measured in the project and appear in no reference language. The strongest apparently
grammatical structure, cross-word affix agreement, is 42% attributable to word-boundary placement
rather than to syntax. The label layer, tested under decision rules fixed before the images were
examined, shows none of the positional, referential or lexical behaviour of a naming system.

Two interpretations remain compatible with these results: production of text without semantic
content by a practised generation procedure, with vocabulary drifting as the illustrations change;
or a formulaic text layer of very low information content whose statistics imitate such a
procedure. Every test reported here favours the first. The second cannot be excluded from internal
evidence alone, because a mechanism shown to be sufficient is not thereby shown to have operated.

Three residual structures define what any future account, mechanical or linguistic, must explain:
the unattributed 58% of the affix agreement, the folio-to-folio vocabulary drift that no generator
reproduces, and the long-range association excess. Distinguishing the two remaining
interpretations requires external evidence: codicology, pigment and ink analysis, provenance, or a
demonstrated decipherment of some subset of the text.
