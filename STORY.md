# The Voynich investigation: a chain of hypotheses

*An account of how this project unfolded. Each step states a hypothesis in plain language, the test
performed, the result, and the question that opened next. Numbers are the current (2026-07-04,
post-review) values. Where an earlier number was corrected, the correction is noted. Reference
outputs: `results/*.json`. All external sources: `REFERENCES.md`. Collapsible blocks contain the
core algorithms; complete scripts are in `scripts/`. An illustrated version of this narrative is
published as this repository's GitHub Pages site.*

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
(1,000 invented words used equally often, the control from the source video) and a "monkey text" of
random letters with spaces.

**Result: validated, with low discriminating power.** The Voynich lands on the same descending
diagonal as the six languages. The uniform-pool gibberish fails: a near-horizontal line (fitted
slope -0.05) that falls off a cliff at its 1,000-type limit. The monkey text is not on the diagonal:
its curve is stepped, with a shelf of equally common short words at the head, and its descent is
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
    """The source video's control: ~1,000 invented words drawn UNIFORMLY.
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

**Result: refuted.** All three registers cluster at h2 near 3.45 to 3.52, while the Voynich sits
alone at 2.4. Botanical text accumulates rare plant and drug names, which raises entropy; the
naming-heavy registers sit furthest from the Voynich, not nearest. The low-entropy anomaly is not a
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

**Result: validated; the largest effect sizes in the project.** All three signatures fire far above
every language: a nearest-distance excess at z of about 78, a copy spike at z of about 50, and a
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
from real prose, from a real Latin word list, and from enciphered Latin. Several numbers moved
downward: the "~75%" long-range reproduction became "about a third" (Step 10), a "faint
stable-collocation layer" fell to about 1 sigma and was retracted, a "5% Currier-dialect" slice of
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
survives excluding copied words, and the mechanical generator misses it entirely. This localises the
residual word-order signal: a real cross-word rule the current generator does not reproduce. It is
not full syntax, but it is a genuine constraint between words.

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
labels, six visibly different roots carry rhyming variants of the same small stem, and the herbal
pages, where a caption-catalogue would show its clearest plant names, have almost no labels at all.
The labels do not behave like a working naming system. The evidence favours labels-as-register,
moderately rather than decisively. What the pictures exclude with more confidence is a rich,
distinctive catalogue: 30 interchangeable figures and six different roots would not carry rhyming
labels if each named a distinct thing.

An illustration-conditioned generator attacks the same question from the mechanical side. We built a
generator whose method depends on the page's illustrated class: each section gets its own word-form
kit, copy rate and window, and each page's vocabulary drifts slowly from the last. Page-conditioning
moves the long-range excess from the section-only generator's -0.12 to +0.03, a real improvement,
but it reaches only about 15% of the Voynich's value and still does not reproduce the folio-to-folio
drift. The page-level drift is the structure the generators reproduce least, and it is the same
structure the label-to-image test probes from the meaning side.

**Summary.** After Zipf, entropy, register, cipher, mechanism, word order, copying, a 17-metric
generator, long-range information, a six-front red-team, a full statistical re-audit and six
falsification tests: a purely mechanical process reproduces essentially the entire Voynich
fingerprint, and the self-citation copy signal is the strongest single piece of evidence for it. The
text's vocabulary tracks the pictures down to the page in a way no mechanical generator yet fully
reproduces, so a formulaic-but-meaningful reading is not excluded. The visual pass over the labels
points the same way: catalogue layout, filler content. Two readings still stand, but they have
narrowed. The question is no longer "meaningless generation versus a meaningful catalogue" but
"meaningless generation versus a formulaic, low-information label layer", and the pictures have made
the richly-meaningful end the less likely one. Whether even that thin label layer carries real names
is the question the next, deeper visual pass takes up.
