/* Voynich story: plate data. Prose follows STORY.md (2026-07-05: census results + plain-terms
   revision). Numbers are the current post-review values (results/*.json; census
   results/t8_census.json). Charts render from `fig` (+ optional `fig2`); collapsible plain-language
   blocks render from `plain` (HTML bodies); algorithm blocks from `algo` (trimmed real scripts). */
window.PLATES = [
{
  dwg:"PLATE 01 · ZIPF'S LAW TEST", sheet:"SHEET 1/17",
  hyp:"If the Voynich is real writing, its words should follow Zipf's law: the commonest word about twice the second, three times the third, the straight line every language shares on log-log axes.",
  test:"Counted every word, ranked by frequency, plotted rank against frequency on log-log axes beside six real languages and two controls: uniform-pool gibberish (a fixed pool of 1,000 invented words, each used with equal probability) and a 'monkey text' of random letters with spaces.",
  verdict:"v-mix", verdictText:"VALIDATED, LOW POWER",
  res:"The Voynich lies on the same descending diagonal as the six languages. The uniform-pool gibberish fails: a near-horizontal line (slope -0.05) that drops abruptly at its 1,000-type limit. The monkey text is not on the diagonal: a stepped curve with a plateau of equally common short words at the lowest ranks, descending more shallowly than the languages (slopes -0.49 to -0.69 vs about -0.9). It nevertheless passes a loose Zipf test. A test that random typing nearly passes cannot separate meaningful text from mechanical production; Zipf conformity constrains word-frequency structure, not meaning.",
  next:"If Zipf cannot separate it from noise, is its shape closer to one particular language?",
  fig:{type:"zipf"},
  plain:[{t:"What the gibberish controls are, and what they do not cover", h:
`<p>Both controls are mathematical, not human. The <span class="hl">uniform-pool control</span> is a fixed pool of 1,000 invented words, each used with equal probability. The <span class="hl">monkey text</span> models random typing: every keystroke is an independent draw from 26 letters plus a space. Both are fully specified, so anyone can regenerate them exactly (the code is in the ALGORITHM block below).</p>
<p>A fair objection: gibberish written by an actual person would look different, and would differ from person to person. True. But these controls have one narrow job: to show that a loose Zipf pass is cheap, that a curve of roughly the right shape appears with no meaning present. One mechanical gibberish source settles that. Adding more people or more nonsense would not change it.</p>
<p>Human gibberish is the more interesting object. People drift into habits, repeat themselves, reuse what they just wrote. That behaviour is modelled in this project too, just not on this plate: it is the copy-and-mutate process of Plates 8 and 9, the actual candidate here for how the manuscript was produced.</p>`}],
  algo:[{t:"The two control texts (scripts/build_controls.py)", c:
`SEED = 1492   # fixed seed; both controls are exactly reproducible
N = 30000     # tokens per control, matching the analysis window

def build_uniform_pool(rng):
    """Control 1: ~1,000 invented words drawn UNIFORMLY.
    Every word has the same probability, so the
    rank-frequency curve is flat until the pool runs out,
    then drops off a cliff."""
    pool = set()
    while len(pool) < 1000:
        w = rng.choice(PREFIXES) + rng.choice(ROOTS) + rng.choice(SUFFIXES)
        pool.add(w)
    pool = sorted(pool)
    return [rng.choice(pool) for _ in range(N)]

def build_monkey(rng, mean_len=5.0):
    """Random typing: characters drawn i.i.d. from a 26-letter
    alphabet plus a space, P(space) = 1/(mean_len+1) so mean word
    length ~5, matching the natural-language set. Shorter strings
    are exponentially more likely, which produces a descending
    rank-frequency curve (Miller 1957) with no meaning present."""
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    p_space = 1.0 / (mean_len + 1.0)
    words, cur = [], []
    while len(words) < N:
        if rng.random() < p_space:
            if cur:
                words.append("".join(cur)); cur = []
        else:
            cur.append(rng.choice(alphabet))
    return words[:N]`}]
},
{
  dwg:"PLATE 02 · NEAREST LANGUAGE", sheet:"SHEET 2/17",
  hyp:"The exact bend of the rank-frequency curve is language-specific. The Voynich's curve should sit nearest whichever of the six languages it most resembles.",
  test:"Measured the distance from the Voynich curve to each language three ways: by exponent, by curve-shape error, and by distributional divergence.",
  verdict:"v-no", verdictText:"INCONCLUSIVE",
  res:"By slope it is nearest Latin; by whole-curve shape, nearest German. The two answers disagree, and 'nearest' is determined by morphology and tokenisation rather than by content. (A 'German wins 91% of draws' figure was later retired: the bootstrap draws were overlapping windows, a corpus-length artefact.)",
  next:"Rather than which language it most resembles: which of its statistics fall outside the range of every language at once?",
  fig:null
},
{
  dwg:"PLATE 03 · CHARACTER ENTROPY h2", sheet:"SHEET 3/17",
  hyp:"If the surface statistics look normal, a deeper one may be abnormal: how predictable each character is from the one before it.",
  test:"Measured second-order character entropy h2 (uncertainty about the next glyph given the current one) and the spread of word lengths, for the Voynich and every language.",
  verdict:"v-yes", verdictText:"TWO ANOMALIES",
  res:"The Voynich's h2 is about 2.4 bits against 3.42 to 3.60 for the reference languages: its glyphs are far more predictable than any of the real scripts measured. Its word lengths are unusually uniform too (standard deviation 1.82 vs 2.4 to 2.9). These two facts are what the rest of the project has to explain.",
  next:"The manuscript is largely a herbal. Could the low entropy be a specialised-vocabulary effect?",
  fig:{type:"bars", unit:"h2 (bits) · lower = more predictable", baseline:3.5, band:[3.42,3.60], data:[
    ["VOYNICH",2.40,true],["ENGLISH",3.60,false],["LATIN",3.45,false],["GERMAN",3.43,false],["HEBREW",3.89,false]]},
  plain:[{t:"What '2.4 bits' means", h:
`<p>h2 asks one question, averaged over a whole text: <span class="hl">given the glyph you just read, how uncertain is the next one?</span> Bits are a currency of uncertainty: each bit is one halving. An uncertainty of 2.4 bits feels like choosing among about 5 equally likely options (2<sup>2.4</sup> &asymp; 5.3); 3.5 bits feels like choosing among about 11.</p>
<p>English has both kinds of position. After <span class="hl">q</span> the next letter is almost always <span class="hl">u</span>: nearly zero uncertainty. After <span class="hl">e</span>, dozens of continuations are live: high uncertainty. Averaged out, English and the other reference scripts land between 3.4 and 3.6 bits.</p>
<p>The Voynich script reads as if almost every position were closer to the <span class="hl">q</span> situation: at each step, the current glyph strongly constrains the next. No natural script we measured behaves this way, which is why this number, together with the too-uniform word lengths, is what the rest of the investigation has to explain.</p>`}],
  algo:[{t:"Second-order character entropy h2 (scripts/discriminators.py)", c:
`def char_entropy(tokens):
    """h1 = entropy of single characters; h2 = conditional entropy
    H(c_i | c_{i-1}) = H(bigram) - H(unigram). Low h2 means the
    current character strongly determines the next one."""
    chars = "".join(tokens)
    n = len(chars)
    uni = Counter(chars)
    h1 = -sum((c / n) * np.log2(c / n) for c in uni.values())
    bi = Counter(zip(chars, chars[1:]))
    nb = sum(bi.values())
    h_bi = -sum((c / nb) * np.log2(c / nb) for c in bi.values())
    h2 = h_bi - h1
    return h1, h2, len(uni)`}]
},
{
  dwg:"PLATE 04 · REGISTER TEST", sheet:"SHEET 4/17",
  hyp:"Technical writing has repetitive vocabulary. The right comparison is a herbal, not a novel, and against that the Voynich might look normal.",
  test:"Added three Latin registers: narrative prose (Caesar), technical botany (Pliny), and pure naming (33,000 Linnaean binomials). Re-measured h2 and word length.",
  verdict:"v-no", verdictText:"REFUTED",
  res:"All three registers cluster at h2 near 3.45 to 3.52 while the Voynich is isolated at 2.4. Botanical text accumulates rare plant and drug names, which raises entropy; the naming-heavy registers are furthest from the Voynich, not nearest. The anomaly is not a register effect: it is a property of the notation system, not of the subject matter.",
  next:"If it is not a natural register, is it a real language hidden under a cipher?",
  fig:{type:"bars", unit:"h2 (bits) across registers", baseline:3.5, band:[3.42,3.60], data:[
    ["VOYNICH",2.40,true],["PROSE LATIN",3.45,false],["BOTANY LATIN",3.52,false],["PLANT NAMES",3.49,false]]}
},
{
  dwg:"PLATE 05 · CIPHER TESTS", sheet:"SHEET 5/17",
  hyp:"A real language run through a cipher would look alien on the surface but carry a recoverable signal underneath.",
  test:"Three tests: a substitution cipher (excluded by arithmetic, a glyph swap cannot change entropy); a verbose transform with abbreviation and affixes; and 'peeling' the Voynich's affixes to see if a language surfaces.",
  verdict:"v-no", verdictText:"NO SIMPLE CIPHER",
  res:"Substitution is mathematically excluded: it cannot lower h2. The verbose transform reaches low h2 and narrow length but works equally from Latin, English and German, implicating the transform, not a source. Peeling reveals no language. A positive control applied the same method to genuinely-enciphered Latin and recovered 23 of 25 glyphs, so the null result on the Voynich is not a failure of the method.",
  next:"If no simple cipher generates these statistics, what mechanism produces low entropy and uniform length directly?",
  fig:{type:"formula", lines:[
    ["H(swap(X)) = H(X)","a one-for-one substitution cannot change entropy, so it cannot lower h2"],
    ["decode(encipher(Latin)) → 23/25 glyphs","positive control: the method works when a real cipher is present"]]},
  plain:[{t:"Why a verbose cipher is hard to square with the short words", h:
`<p>A <span class="hl">verbose cipher</span> writes one plaintext letter as a group of glyphs. It is the standard explanation for low h2: if every letter becomes a stock glyph-group, the glyph stream turns predictable. But it predicts the opposite of what the words do. Expanding letters into groups makes cipher words <span class="hl">longer</span> than the plaintext words; Voynich words are short (about 5 glyphs) and unusually uniform.</p>
<p>The only way out is to re-cut the word boundaries, so the spaces no longer mark plaintext words. We built exactly such a transform (abbreviate, add affixes, re-segment). It does reach Voynich-like h2 and word lengths, but it reaches them from Latin, English and German alike: the statistics come from the transform itself, not from any message underneath. And once the boundaries have been re-cut, the "words" are no longer message units, which sits badly with everything the labels and the word-level statistics show elsewhere in this investigation.</p>
<p>The peeling test approaches from the other side: strip the Voynich's repetitive prefixes and suffixes and ask whether the remaining cores behave like a language. They do not. The positive control matters here: applied to genuinely enciphered Latin, the same pipeline recovers 23 of 25 glyph assignments, so the failure on the Voynich is a fact about the Voynich, not about the method.</p>`}]
},
{
  dwg:"PLATE 06 · SLOT GRAMMAR", sheet:"SHEET 6/17",
  hyp:"The words are built from a small kit of fixed pieces in fixed positions, a slot grammar, so the next glyph is nearly determined by the current one.",
  test:"Measured per-position glyph menus, the coverage of a small affix kit, and whether a simple Markov glyph-transition model reproduces the low h2.",
  verdict:"v-yes", verdictText:"VALIDATED, WITH A REMAINDER",
  res:"A small affix kit covers 66 to 79% of words (vs 33 to 53% for languages), glyph transitions are about twice as concentrated as in any of the languages, and a Markov model reproduces the low h2. Two further constraints are not consequences of it: the narrow word-length band, and elevated whole-word repetition. An additional process regulates word length and reuses whole words.",
  next:"How are the words arranged in sequence? Is there grammar between words?",
  fig:{type:"bars", unit:"top-10 two-glyph suffix coverage: share of words ending in the kit", baseline:null, pct:true, data:[
    ["VOYNICH",0.79,true],["GERMAN",0.53,false],["LATIN",0.47,false],["ENGLISH",0.34,false]]}
},
{
  dwg:"PLATE 07 · WORD-ORDER INFORMATION", sheet:"SHEET 7/17",
  hyp:"In real language the previous word strongly predicts the next. The Voynich should show the same if it carries sentences.",
  test:"Measured word-order information: how much the previous word reduces uncertainty about the next, with a shuffle control to cancel sample-size bias.",
  verdict:"v-no", verdictText:"ALMOST NONE",
  res:"Word order carries about 1.7% of the word-level uncertainty against 2.6 to 7.4% across the prose languages. (Technical Latin at 1.2% is just below it, so the statistic is register-relative.) The token stream is nearly unordered: inconsistent with obscured connected prose, consistent with a list, a catalogue, or table-driven generation.",
  next:"If word order is nearly random but words are locally repetitive, is each word copied from a nearby recent word and lightly changed?",
  fig:{type:"bars", unit:"word-order information (% of word entropy) · higher = more grammar", baseline:null, pct:true, data:[
    ["VOYNICH",0.017,true],["TECH LATIN",0.012,false],["ITALIAN",0.026,false],["GERMAN",0.046,false],["ENGLISH",0.072,false]]},
  plain:[{t:"Two different predictabilities, pointing opposite ways", h:
`<p>This plate and Plate 3 measure predictability at two different levels, and they give opposite answers. That is not a contradiction; the combination is the finding.</p>
<ul>
<li><span class="hl">Inside words, glyph by glyph (h2, Plate 3):</span> the Voynich is far MORE predictable than any language. The word-builder is rigid.</li>
<li><span class="hl">Between words (this plate):</span> the Voynich is far LESS predictable than prose. Knowing the current word tells you almost nothing about the next. There is no detectable sentence structure.</li>
</ul>
<p>A real language is the mirror image: flexible inside words (many different letter sequences occur) and constrained between them (grammar). The Voynich is a rigid word-machine with the words then laid down in nearly free order, which is what a list, a catalogue, or table-driven generation looks like, and what connected prose does not.</p>
<p>The register comparison concerns this plate's word-level statistic only: technical Latin also has weak word order (1.2%), but its glyph-level h2 is normal (3.5 bits, Plate 4). No register we measured is anomalous at both levels at once.</p>`}],
  algo:[{t:"Word-order information with a shuffle control (scripts/word_syntax.py)", c:
`def order_info(tokens, nshuf=200):
    """How much does the previous word reduce uncertainty about
    the next? order_info = H(w_i | w_{i-1}) on SHUFFLED text minus
    the same on real text. The shuffle term cancels the
    finite-sample bias that makes raw conditional entropy look
    informative on any corpus."""
    H_cond = cond_H(zip(tokens, tokens[1:]))
    shuf = []
    for rep in range(nshuf):
        arr = list(tokens)
        random.Random(SEED + rep).shuffle(arr)
        shuf.append(cond_H(zip(arr, arr[1:])))
    H_shuf, sd = mean(shuf), std(shuf)
    return H_shuf - H_cond, (H_shuf - H_cond) / sd  # bits, z`}]
},
{
  dwg:"PLATE 08 · SELF-CITATION", sheet:"SHEET 8/17",
  hyp:"Each word is produced by copying a recent word and rewriting it with a small change (Timm & Schinner 2019). A word should resemble a recent predecessor more than chance allows, more so for nearer ones.",
  test:"For each word, found the minimum edit distance to the previous few words, compared against a shuffle of the same tokens (identical vocabulary, sequential copying destroyed). Tracked three signatures: below-shuffle nearest distance, an excess of near-identical neighbours, and a locality gradient.",
  verdict:"v-yes", verdictText:"LARGEST EFFECTS",
  res:"All three signatures exceed their null distributions by wide margins: nearest-distance excess z≈78, copy spike z≈50, locality gradient z≈23, against 200-shuffle null distributions. No language shows the ensemble. Hebrew, the closest runner-up, matches the exact-repeat spike (for a known linguistic reason: a consonant-only script repeats short forms constantly) but has only half the locality gradient and none of the entropy or word-length anomalies; the prose languages' gradients are negative. The Voynich's copying is specifically local. A single process accounts for the slot grammar, the near-zero word order and the local repetition: copy a nearby word and mutate it.",
  next:"If copying explains the pieces, can one generator reproduce the whole fingerprint at once?",
  fig:{type:"zbars", unit:"signature strength (z vs 200-shuffle null)", data:[
    ["NEAREST DIST",78],["COPY SPIKE",50],["LOCALITY GRAD",23]]},
  fig2:{type:"bars", unit:"locality gradient (z) · positive = words resemble what was JUST written", baseline:0, data:[
    ["VOYNICH",23.1,true],["HEBREW",10.4,false],["MONKEY TEXT",0.8,false],["GERMAN",-2.7,false],["LATIN",-6.2,false],["ENGLISH",-9.8,false]]},
  plain:[{t:"How big is z = 78, and who is the runner-up?", h:
`<p>A z-score answers: <span class="hl">how far is the real text from what shuffling produces, measured in units of the shuffles' own spread?</span> We reorder the same words 200 times, measure each reordering, and get a bell of "no copying" values. z = 3 (three spreads out) is the usual discovery threshold; z = 78 means the real manuscript sits 78 spreads beyond a bell that never once came close. Chance is not a candidate explanation at that distance; the only live question is what the structure is, not whether it exists.</p>
<p>In the manuscript itself, 15% of words are an exact copy of one of the previous 25 words (shuffled expectation: 7%), and another 31% are one edit away (shuffled: 26%). Nearly half of all words sit within one small change of something just written.</p>
<p>The runner-up matters, and it is Hebrew (an unvowelled Torah text). Its exact-repeat spike is actually stronger than the Voynich's, because a consonant-only script with short words repeats exact forms constantly, and its locality gradient is genuinely positive (z &asymp; 10; liturgical repetition and parallelism are local). What separates the Voynich is the pattern across all the measures at once: a locality gradient twice Hebrew's, while prose languages run NEGATIVE (a word resembles the last few words slightly less than words further back), and, unlike Hebrew, glyph entropy and word lengths that are themselves anomalous (Plate 3; Hebrew's h2 is 3.89, the highest in the panel). Hebrew mimics one signature for a known linguistic reason; nothing mimics the ensemble.</p>`},
  {t:"What copy-and-mutate looks like on the page", h:
`<p>Timm and Schinner's papers illustrate the process directly on the manuscript: sequences of similar words descending line by line, each derivable from the one before by one small edit. Two of their published chains (EVA transcription, one word per line of the page):</p>
<div class="chain">folio f53r, lines 5 to 8
  ykody
  yk<b>ch</b>dy    <i>o removed, ch added</i>
  ykch<b>o</b>dy   <i>the removed o returns</i>
  yk<b>ee</b>od    <i>ch becomes ee, final y dropped</i>

folio f104r, lines 33 to 36
  qokal
  qokal     <i>copied unchanged</i>
  qo<b>d</b>al     <i>k becomes d</i>
  qo<b>t</b>al<b>y</b>    <i>d becomes t, y added</i></div>
<span class="src">chains from Timm 2014 (arXiv:1407.6639) figs. 3 and 5; the same relations are visible in the folio scans</span>
<p>This plate's statistics test that impression manuscript-wide: measure how close each word is to its recent predecessors, then ask whether shuffling the same words away destroys the closeness. It does, massively, and only in the Voynich. The shuffle is the essential control: the slot grammar (Plate 6) makes ALL Voynich words look alike, so raw similarity proves nothing; only similarity beyond the shuffled level counts as copying.</p>`}],
  algo:[{t:"The shuffle-controlled copy test (scripts/self_citation.py)", c:
`def nearest_distance(tokens, W):
    """For each word, the minimum Damerau-Levenshtein edit distance
    to any of the previous W words. Distance 0 = exact copy;
    distance 1 = copy plus one change (the model's prediction)."""
    out = []
    for i in range(W, len(tokens)):
        out.append(min(DL.distance(tokens[i], tokens[i - k])
                       for k in range(1, W + 1)))
    return mean(out)

# THE essential control: the slot grammar alone makes all Voynich
# words mutually similar, so a low raw distance proves nothing.
# Reorder the SAME tokens (identical vocabulary, copying destroyed)
# and recompute. Only distance BELOW the shuffle = copying.
real = nearest_distance(tokens, W)
null = [nearest_distance(shuffled(tokens, seed=SEED + rep), W)
        for rep in range(NSHUF)]
excess = mean(null) - real          # positive = copying
z = excess / std(null)`}]
},
{
  dwg:"PLATE 09 · GENERATOR TOURNAMENT", sheet:"SHEET 9/17",
  hyp:"A single generator (length-locked word-forms + copy-and-mutate + a mild per-section vocabulary bias) reproduces all the statistics, with no meaning anywhere.",
  test:"A tournament: specialist generators against unified ones, scored on the same 17-metric fingerprint. Copy parameters tuned only on the copying metrics, so the Zipf slope and vocabulary size are free to emerge or not.",
  verdict:"v-yes", verdictText:"MECHANICAL IS SUFFICIENT",
  res:"The four-parameter unified generator reproduces the whole fingerprint (combined error 0.179) better than any specialist (0.274), and the Zipf slope, type count and Heaps growth emerge unfitted (generator Zipf -0.87 vs Voynich -0.89). Nothing in the internal statistics requires meaning. Sufficiency is not necessity: a highly formulaic real text is not excluded.",
  next:"A book-length message needs long-range structure. Does the Voynich carry information across hundreds of words, or go flat?",
  fig:{type:"bars", unit:"combined fit error vs Voynich (lower = better all-rounder)", baseline:null, data:[
    ["U2 UNIFIED",0.179,true],["U1 UNIFIED",0.199,false],["BEST SPECIALIST",0.274,false],["ENGLISH",0.660,false]]},
  plain:[{t:"The generator, as a recipe (no computer required)", h:
`<p>"Algorithmically generated" tends to suggest a computer. An algorithm is just a fixed set of steps repeated over and over; a kitchen recipe is one. Stripped of code, this generator is a writing habit. To produce each new word:</p>
<ol>
<li><span class="hl">Usually (about four times in five): copy.</span> Glance back over the last ten to twenty words you wrote, pick one, and write it again with one small change: swap a glyph for a similar one, or add or drop an ending.</li>
<li><span class="hl">Otherwise: build a fresh word.</span> Start with a common opening glyph and keep appending whichever glyph habitually follows the one you just wrote, stopping when the word reaches a normal length. The "Markov model" in the code is nothing more than that habit written as a table: which glyph tends to follow which, the same kind of knowledge as "q is usually followed by u".</li>
<li><span class="hl">Keep a mild section habit.</span> Favour the handful of words you have been using in this part of the book, so the vocabulary drifts as the book moves from plants to stars to recipes.</li>
</ol>
<p>To see it work, run the copy step on English letters. Seed with a five-word picture caption, then derive each new word from a recent one, every step checkable:</p>
<div class="chain">seed      elephant eating bananas outside alone
  eleph<b>i</b>nt   <i>copy elephant, one letter changed</i>
  elephi<b>nd</b>   <i>copy elephint, ending changed</i>
  eat<b>ind</b>     <i>copy eating, give it the -ind ending just used</i>
  ban<b>u</b>nas    <i>copy bananas, one letter changed</i>
  el<b>o</b>phind   <i>copy elephind, one letter changed</i>
  outs<b>o</b>de    <i>copy outside, one letter changed</i>
  eatind     <i>copied unchanged</i>
  al<b>u</b>ne      <i>copy alone, one letter changed</i></div>
<p>Meaning is gone by the first derived word, but notice what survives: each word is a near-copy of a neighbour, the same forms keep resurfacing, and every new word inherits the LENGTH of the word it copied, so word lengths stay tightly clustered instead of spreading out the way real vocabulary does (the Voynich's word-length spread is 1.82 around a mean of about 4.9 glyphs, against 2.4 to 2.9 for the languages). Run this habit for two hundred pages and you get text whose words closely resemble their neighbours, drift slowly, and say nothing: the two headline anomalies of Plate 3 are side effects of the copying itself.</p>
<p>Four numbers tune the whole thing: how often to copy, how far back to look, how strong the section habit is, and the word-length profile. Everything else emerges. In particular there is no stored dictionary anywhere: the vocabulary accumulates on the page as a side effect of copying, and that is precisely why the Zipf curve, the vocabulary size and its growth rate come out right without being fitted.</p>
<p>Could a fifteenth-century scribe do this? Nothing in it requires more than pen, page and habit; we wrote the method out as literal pen-and-paper instructions and executed it, and the output lands in the Voynich's anomalous zone on every axis we scored (scripts/scribe_recipe_test.py in the repository). The two standard objections dissolve the same way. Long-term memory: none is needed, because <span class="hl">the manuscript itself is the memory</span>; the scribe copies what is already on the page, and rare words recur on consecutive sheets exactly as copying from the last finished sheet predicts. Several scribal hands: all four usable hands share the same statistical fingerprint (Plate 12, T4), which is what a taught habit looks like; a private improvisation would differ from hand to hand, and it does not.</p>`}],
  algo:[{t:"The unified generator U2 (scripts/generation_tournament.py)", c:
`def gen_u2(markov_model, rng, sizes, W, p_copy, overlap):
    """Four-parameter generator. Word forms come from a glyph-level
    Markov model, length-locked by rejection to the Voynich's
    empirical length profile (gives low h2 + the narrow length
    band). The token stream mixes three moves per word:
      p_copy     copy one of the last W words and mutate it
                 (regenerate the last 1-2 glyphs via the same
                 Markov model, so mutations stay in-grammar)
      overlap    draw a fresh word from the global pool
      otherwise  draw from this section's sub-pool (topic bias)
    Zipf slope, type count and Heaps growth are NOT fitted."""
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
    return out`}]
},
{
  dwg:"PLATE 10 · LONG-RANGE INFORMATION", sheet:"SHEET 10/17",
  hyp:"If it is meaningless local generation, mutual information between words collapses within a few words. If it carries content, information persists across hundreds of words.",
  test:"Measured mutual information between words d apart, split into repetition (same word) and association (different words predicting each other), out to 800 words, against a 200-shuffle null.",
  verdict:"v-mix", verdictText:"POSITIVE FOR CONTENT",
  res:"The Voynich carries long-range association information (signed excess +0.16 bits, z≈9) that a single real work does not. The mechanical generator reproduces at most about a third of it under a generous accounting, and none under the strict signed accounting (its excess turns negative, like the real languages'), and reproduces the smooth positive decay under neither. The information tracks the illustrated content down to the individual page.",
  next:"Two readings now survive, differing almost only in the labels. One test separates them: do the labels match the pictures?",
  fig:{type:"decay"},
  plain:[{t:"How to read the decay figure", h:
`<p>The horizontal axis is separation: pick two words d positions apart, for d from a few words up to 800. The vertical axis is how much the first word tells you about the second, AFTER subtracting what the same text tells you when shuffled. So the zero line means "nothing beyond chance", and only the height above zero is evidence of structure. Same-word repetition (burstiness) is split out and excluded; the curves show different words predicting each other, which is where a message's content would live.</p>
<p>The surprise runs opposite to the intuitive guess. If the Voynich were locally generated noise, its curve should die to zero within a page. Instead the <span class="hl">Voynich stays positive out to hundreds of words</span>, while a <span class="hl">single real work</span> (one continuous book by one author, our comparison so that topic jumps between different works cannot fake the effect) sits at or slightly below zero at those distances, and the <span class="hl">mechanical generator</span> reproduces at most about a third of the Voynich's budget before drifting negative like the languages.</p>
<p>So the Voynich is not "less organised" than a real book at long range; it is MORE organised, and differently. The extra structure is vocabulary tracking the illustrated content: which section you are in, and even which page (adjacent pages share vocabulary, fading with distance). That is why this plate scores FOR the content side of the ledger: it is the one statistic a simple generation account under-reproduces, and equally what a text genuinely about its pictures would show. Both readings of that fact are still open, which is what Plates 13 and 14 take up.</p>`}],
  algo:[{t:"Long-range mutual information, split self/cross (scripts/long_range_mi.py)", c:
`def mi_parts_coded(codes, V, d):
    """Mutual information between the word at position i and the
    word at i+d, on an integer-coded stream. Split into SELF (the
    same word recurring: burstiness) and CROSS (different words
    predicting each other: where a message's information lives)."""
    a, b = codes[:-d], codes[d:]
    n = a.size
    ca = np.bincount(a, minlength=V)
    cb = np.bincount(b, minlength=V)
    uk, cc = np.unique(a * V + b, return_counts=True)  # joint
    x, y = uk // V, uk % V
    term = (cc / n) * np.log2((cc * n) / (ca[x] * cb[y]))
    same = x == y
    return term[same].sum(), term[~same].sum()  # self, cross

# Null: 200 seeded permutations of the stream. The reported budget
# is the SIGNED sum of (real - null_mean) over d >= 32: no clipping
# at zero.`}]
},
{
  dwg:"PLATE 11 · RED-TEAM + RE-AUDIT", sheet:"SHEET 11/17",
  hyp:"Our conclusions might be artefacts of weak controls.",
  test:"A six-front adversarial red-team, then a full statistical review that found the project leaned on 2-to-3-shuffle nulls and re-ran everything against 200-shuffle real null distributions with z-scores.",
  verdict:"v-mix", verdictText:"MAIN FINDINGS HOLD",
  res:"The low h2, narrow length and self-citation signal all hold. The self-citation signal is absent from real prose, a Latin word list and enciphered Latin. Several figures were revised downward: '75%' to about a third; a claimed stable-collocation signal was retracted at about 1σ; the '5% dialect' component measured zero; a topical-clustering signal halved. All corrections reduced the strength of previously published claims; most favoured the mechanical reading, while the long-range correction favoured the content reading.",
  next:"With honest nulls in hand, are there tests that could still break the mechanical account, or find meaning we have missed?",
  fig:{type:"corrections", data:[
    ["Long-range reproduction","~75%","~a third"],
    ["Stable-collocation signal","real +0.029","retracted (~1σ)"],
    ["Currier dialect component","5%","≈0"],
    ["Topical clustering","0.091","0.051"]]}
},
{
  dwg:"PLATE 12 · FALSIFICATION TESTS", sheet:"SHEET 12/17",
  hyp:"Six tests, each specified in advance with an outcome that would count against the leading hypothesis or find meaning where we had not looked.",
  test:"T1 copy source (line above vs stream); T3 syntax hunt + affix agreement; T4 scribal hands; T8 zodiac label recurrence; T6 a constructed-language control (Esperanto); T2 label reuse across sections.",
  verdict:"v-mix", verdictText:"ONE REAL REFINEMENT",
  res:"T1: copying is local but not specifically the line above (a memory-window process). T3: no subset has language-like word order, but a word's ending predicts the next word's beginning as strongly as Latin agreement (z≈80), survives copy-exclusion, and the generator as first built missed it entirely: a real cross-word rule, though not full syntax. (Plates 15 and 16 return to this rule.) T4: all four hands share the fingerprint (consistent with a taught method). T8 (text side): zodiac labels recur as a register effect, not a naming catalogue. T6: Esperanto, a meaningful constructed language, lands with the natural languages, not the Voynich. T2: pharmaceutical labels do not reuse the herbal naming vocabulary (their own diverse register).",
  next:"The one place the account under-reproduces is page-level structure. Two moves aim at that gap.",
  fig:{type:"zbars", unit:"suffix-to-prefix agreement (z, copies excluded): a word's ending predicts the next word's start", data:[
    ["VOYNICH",80],["LATIN",67],["GENERATOR",0]]},
  plain:[{t:"Which word gets copied, and what 'register' means here", h:
`<p><span class="hl">Which word does the scribe copy?</span> T1 says: one drawn from recent memory, the last ten to twenty-five words, roughly the line being written and the couple of lines above it, with nearer words favoured. It is NOT specifically the word directly above (a plausible guess, since similar words often do stack vertically): the vertical alignment turns out to be a by-product of lines being about one memory-window long, not a rule of its own. Languages show no such window at all.</p>
<p><span class="hl">'Register' here means a restricted, formulaic mode of writing</span>, the way ship's logs, account books or plant catalogues restrict themselves to a small stock of forms, as opposed to open prose. When Plate 12 says the zodiac labels recur "as a register effect", it means their repetition is what a shared restricted stock produces, not what a naming system produces (the same star keeping the same name wherever it appears).</p>`}],
  algo:[{t:"Cross-word affix agreement (scripts/t3_syntax_hunt.py)", c:
`def agreement(lines_tokens, fa, fb, exclude_copies, nshuf=200):
    """MI between fa(word_i) and fb(word_{i+1}) over adjacent
    within-line pairs, against a within-line shuffle. fa/fb extract
    affixes, e.g. fa = last two glyphs (suffix), fb = first two
    glyphs (prefix). exclude_copies drops pairs with edit distance
    <= 1, so the copying mechanism cannot mimic agreement."""
    def build_pairs(lines):
        out = []
        for ln in lines:
            for a, b in zip(ln, ln[1:]):
                if exclude_copies and DL.distance(a, b) <= 1:
                    continue
                out.append((fa(a), fb(b)))
        return out
    real = pair_mi(build_pairs(lines_tokens))
    null = [pair_mi(build_pairs(shuffle_within_lines(lines_tokens,
                                                     SEED + r)))
            for r in range(nshuf)]
    return real - mean(null), (real - mean(null)) / std(null)`}]
},
{
  dwg:"PLATE 13 · THE GAP", sheet:"SHEET 13/17",
  hyp:"The mechanical account is sufficient for every internal statistic. The one place it under-reproduces is page-level structure: long-range association tracking the pictures, and folio-to-folio vocabulary drift.",
  test:"Two moves at that gap: a first label-to-image reading (a full-manuscript viewer pairing Beinecke page scans, 226/227 folios, with the transcription, read directly); and an illustration-conditioned generator whose method depends on the page's illustrated class.",
  verdict:"v-mix", verdictText:"CATALOGUE LAYOUT, FILLER CONTENT",
  res:"The manuscript has catalogue LAYOUT (one label at each star-nymph, one above each pharma root) but filler CONTENT: adjacent interchangeable nymphs carry near-identical labels, six visibly different roots carry minor variants of one stem, and the herbal pages, where a caption catalogue would show its clearest plant names, have almost no labels. On the mechanical side, page-conditioning moves the generator's long-range excess from -0.12 to +0.03 (a real improvement, but ~15% of the Voynich) and still does not reproduce the folio-to-folio drift. So the pictures exclude a rich, distinctive catalogue, but the first reading was qualitative: it needed to be made quantitative, with the rules set in advance.",
  next:"The labels get their own examination: do they name anything at all?",
  fig:{type:"bars", unit:"long-range structure budget (signed bits) · negative = flat", baseline:0, data:[
    ["VOYNICH",0.21,true],["PAGE-CONDITIONED",0.03,false],["SECTION-ONLY (U2)",-0.12,false]]}
},
{
  dwg:"PLATE 14 · THE LABEL-IMAGE CENSUS", sheet:"SHEET 14/17",
  hyp:"If meaning survives anywhere, it is in the labels, and a naming layer has visible signatures: the same referent carries the same label, a recurring label keeps its position, and special objects carry special words.",
  test:"A census of the label layer under four decision rules fixed BEFORE the data was collected: the position, label and figure type of all 298 ring figures across the twelve zodiac medallions; 18 pairs of near-identical star-nymphs matched across pages; the recurring root drawings of the pharmaceutical section; and the word written under each central zodiac animal. 1,000-rep permutation nulls throughout.",
  verdict:"v-no", verdictText:"REGISTER, NOT A NAMING CATALOGUE",
  res:"None of the four rules fired. Labels that recur across zodiac pages do not re-occupy the same angular slot (z=-1.4), so there is no star catalogue in fixed order. Labels on near-identical nymphs are exactly as distinct as random pairs drawn from the label pool (z=+0.9): a shared register, not shared names. The root drawings barely repeat at all, which itself argues against a cross-referenced catalogue, and the one clear repeated root (f89r1/f89r2) carries two different labels. Eleven of twelve central words are month names added by a later hand; only one medallion (f70v2) has a Voynichese word under its animal, so there is no per-sign name set to test. In every location where a naming system would be detectable, the labels behave like the running text instead.",
  next:"Before closing, the hypothesis this project tested owes its origin a test of its own: score the published implementation of the self-citation idea on the same instruments.",
  fig:{type:"rules", title:"Four rules, fixed before the data was collected", cols:"52px 1fr 130px", rows:[
    ["C1","Do labels that recur across zodiac pages re-occupy the same angular slot (a star catalogue in fixed order)?","NULL (z=-1.4)"],
    ["C2","Do near-identical figures carry near-identical labels (same referent, same name)?","AT NULL (z=+0.9)"],
    ["C3","Does the same root drawing carry the same label when it recurs (pharma)?","NO (1 pair, differs)"],
    ["C4","Do the words under the central zodiac animals form a distinct, consistent per-sign name set?","NULL (1 of 12)"]]},
  plain:[{t:"Why the rules were fixed before looking", h:
`<p>By this point in the investigation the temptation is obvious: we had a leading hypothesis, and a mass of unexplored images. Choose the statistics after seeing the pictures and you can (honestly, without noticing) pick the ones that flatter the hypothesis. So the four rules above, including the exact firing thresholds and what each direction of each result would mean, were written down and frozen before any image was measured. The census then executed them literally.</p>
<p>What each rule was listening for: <span class="hl">C1</span>: real star catalogues list stars in a fixed order, so a label that recurs should recur in roughly the same position on the ring. <span class="hl">C2</span>: names track referents, so two figures drawn as near-twins should carry the same or nearly the same label if labels name what is drawn. <span class="hl">C3</span>: the same test where it is sharpest, on the pharmacy pages' root drawings, where each drawing has exactly one label above it. <span class="hl">C4</span>: the one candidate layer the first reading had flagged as possibly special, the word written under each central zodiac animal.</p>
<p>Every rule came back empty, and C3 failed in an instructive way: genuinely repeated drawings are rare, the opposite of what a cross-referenced catalogue produces. A naming layer had four independent chances to show itself where naming is easiest to detect, and did not.</p>`},
  {t:"What the labels actually look like", h:
`<p>Two patterns carry the verdict, and both are visible without statistics. First, the labels around one zodiac wheel are variations of a single stem, not thirty different names. These are the ring labels of folio f70v2 (the ram medallion):</p>
<div class="chain">around one wheel (f70v2)
  otar  otar  otar  otald  otaldar  otaly
  otalar  otalam  otaldy  okaram  dolaram  otolal</div>
<p>Second, the same interchangeable figure, a star-holding nymph standing at the top of the outer ring, gets an unrelated word on each of five consecutive wheels:</p>
<div class="chain">the figure at 12 o'clock, five wheels
  f72r2 okaly &middot; f72r3 oraiinam &middot; f72v1 oy
  f72v2 okeoram &middot; f72v3 okey</div>
<p>The Beinecke scans show both patterns directly. Below, the top of the outer ring on each of those five folios (Beinecke MS 408, public domain): the same repeated figure, each with its own short word, and within each page the words visibly sharing that page's stem.</p>
<figure class="crops">
  <img src="img/f72r2_topring.jpg" alt="Top of the outer ring, folio f72r2: near-identical star-holding nymphs, each with a short label" loading="lazy">
  <figcaption>f72r2 &middot; anchor label <span class="mono">okaly</span></figcaption>
  <img src="img/f72r3_topring.jpg" alt="Top of the outer ring, folio f72r3" loading="lazy">
  <figcaption>f72r3 &middot; anchor label <span class="mono">oraiinam</span></figcaption>
  <img src="img/f72v1_topring.jpg" alt="Top of the outer ring, folio f72v1" loading="lazy">
  <figcaption>f72v1 &middot; anchor label <span class="mono">oy</span></figcaption>
  <img src="img/f72v2_topring.jpg" alt="Top of the outer ring, folio f72v2" loading="lazy">
  <figcaption>f72v2 &middot; anchor label <span class="mono">okeoram</span></figcaption>
  <img src="img/f72v3_topring.jpg" alt="Top of the outer ring, folio f72v3" loading="lazy">
  <figcaption>f72v3 &middot; anchor label <span class="mono">okey</span></figcaption>
</figure>
<p>A naming catalogue predicts the reverse: variety within a page (thirty stars, thirty names) and stability across pages (the same star keeps its name). The labels have it exactly backwards, and backwards in precisely the way a copy-and-mutate register produces: heavy local stem-reuse, no cross-page identity. That, in one picture, is why the census reads the label layer as register rather than names.</p>`}]
},
{
  dwg:"PLATE 15 · THE PRIOR-ART TEST", sheet:"SHEET 15/17",
  hyp:"The self-citation hypothesis is Timm and Schinner's, and they published a working generator implementation. Scored on this project's instruments, it should match the Voynich where its mechanisms overlap ours, and its design differences should appear as measurable deviations.",
  test:"Cloned the published implementation (MIT-licensed, the paper's additional-materials repository) and scored its shipped deterministic sample (pseudorandom seed 19; 10,832 tokens) through the same harness as every other text in this project, size-matched against the Voynich and our U2 at the same token count.",
  verdict:"v-mix", verdictText:"SHARED CORE, MEASURED DEVIATIONS",
  res:"Where it matches: mean word length (4.71 vs the Voynich's 4.69), word-order information (0.0106 vs 0.0102; our U2 measures 0.0007, so its line-and-paragraph machinery captures word-order structure U2 lacks) and adjacent repetition. Where it deviates: it produces too much exact copying (excess 0.064 vs 0.035) and too weak a locality gradient (0.023 vs 0.086), the graded decline of similarity with distance that its own papers emphasise; its vocabulary is too small (2,228 types vs 3,154, size-matched) with a correspondingly steep Zipf slope (-0.98 vs -0.83) and over-uniform word lengths (sd 1.56 vs 1.80). Design difference behind the deviations: it fixes ~20 configured constants plus hand-coded glyph-legality tables, where U2 fixes four parameters; the two implementations answer different questions (available fidelity versus minimal sufficient machinery). One deviation is diagnostic rather than a defect: its output shows suffix-to-prefix agreement at z = 5.4 where our U2 shows none (z = -1.1; Voynich 22.9 at this sample size), so something in its rule set produces the Plate 12 agreement structure mechanically.",
  next:"Which of its rules produces the agreement? Transplant them into U2 one family at a time and measure.",
  fig:{type:"bars", unit:"affix agreement (z, copies excluded, 10.8k tokens)", baseline:0, data:[
    ["VOYNICH",22.9,true],["TIMM SAMPLE",5.4,false],["OUR U2",-1.1,false]]},
  fig2:{type:"bars", unit:"locality gradient (copy excess, near minus far) · the deviation", baseline:0, data:[
    ["VOYNICH",0.086,true],["OUR U2",0.072,false],["TIMM SAMPLE",0.023,false]]},
  plain:[{t:"What this project takes from Timm, and what it adds", h:
`<p>Credit where it is due: the self-citation hypothesis, the catalogue of copying rules, and the observation that similar words cluster line-by-line are Timm and Schinner's. This project did not discover the mechanism; it measured it. The additions are three. First, shuffle-controlled quantification: because the slot grammar makes every Voynich word resemble every other, raw similarity proves nothing, so each signature is measured as an excess over reshuffled text (Plate 8). Second, a minimal version: a four-parameter generator that reproduces the fingerprint with the vocabulary, Zipf curve and growth left free (Plate 9), which shows how little machinery the hypothesis actually needs. Third, this harness itself: any proposed generator, theirs or ours, can now be scored on the same instruments, which is what this plate does.</p>
<p>The comparison also shows what their implementation does better. It writes in lines, paragraphs and pages, with paragraph-initial conventions and a preference for copying from the same position one line up, and that layout machinery produces word-order statistics and layout effects our token-stream generator ignores. The two implementations fail in opposite directions, which is useful: it locates which properties come from the copying core (shared) and which from the packaging around it.</p>
<p>Its deviations should also be read fairly: a deterministic sample at one seed and 10,832 tokens, scored on our instruments, not theirs. The type count, slope and gradient deviations are real at this sample size, but none of them touch the shared claim, which is that local copy-and-mutate produces Voynich-like text. The agreement trace (z = 5.4) is the productive finding: it is the one statistic where their implementation exceeds ours, and the next plate isolates its source.</p>`}],
  algo:[{t:"Scoring the shipped sample (scripts/timm_generator_eval.py)", c:
`# The published implementation ships a deterministic sample:
#   executable/generate/generated_text.txt  (pseudo RNG, seed 19,
#   1,200 lines, 10,832 tokens; conf.properties documents the run)
# github.com/TorstenTimm/SelfCitationTextgenerator (MIT)

timm  = load_lines(TIMM_SAMPLE)          # his lines, as shipped
voy   = voynich_tokens[:len(timm_tokens)] # size-matched
u2    = gen_u2(...)[:len(timm_tokens)]    # our generator, same n

for series in (voy, timm, u2):
    fingerprint(series)                   # h2, lengths, Zipf, types,
                                          # copy signatures, word order
    agreement(lines(series), suf, pre,    # suffix->prefix MI vs
              exclude_copies=True)        # within-line shuffle null`}]
},
{
  dwg:"PLATE 16 · THE SPLIT-WORD TEST", sheet:"SHEET 16/17",
  hyp:"One grammar-like structure resisted the mechanical account: a word's ending predicts the next word's beginning about as strongly as Latin agreement (Plate 12), and Timm's implementation produces a measurable part of it (Plate 15). Some specific rule in that implementation must generate the structure without meaning.",
  test:"Extended our generator to U3: U2's four parameters unchanged, plus five moves transplanted from Timm's implementation at the probabilities in his shipped configuration (nothing was fitted to the agreement statistic; the success criterion was fixed before the first run). Then single-move ablations: disable one move at a time, regenerate, re-measure. Stability checked across four random seeds.",
  verdict:"v-yes", verdictText:"THE SPLIT MOVE ACCOUNTS FOR IT",
  res:"U3 raises the agreement excess from U2's 0.002 bits (z = 0.5) to 0.084 bits (z = 24.2; z = 21 to 24 across four seeds), which is 42% of the Voynich's 0.198 bits (z = 61.6) on the same 30,000-token harness. The other fingerprint metrics stay within U2's range, except the exact-copy excess, which falls from 0.025 to 0.013 (Voynich: 0.048). Single-move ablations isolate the source: with the token-splitting move disabled the excess drops to -0.003 bits (z = -0.8), while disabling any other move leaves z between 17 and 20. The splitting move writes a token of six or more glyphs as two consecutive tokens, cut at a random interior point. Each such pair spans a transition that was word-internal, and word-internal transitions are exactly where the script's predictability is concentrated (h2 = 2.4 bits, Plate 3), so the suffix-to-prefix statistic registers that transition as cross-token dependence. In short: relocating a word boundary converts within-word structure into measured between-word structure. Independent support for the move: split and joined variants of the same string occur on adjacent lines (olchedy, f75v line 19; ol chedy, line 18), and EVA word boundaries are known to be uncertain. Unexplained remainder: 58% of the agreement excess, the reduced exact-copy excess, and the manuscript's actual splitting rate, which is countable and was not measured here.",
  next:"After sixteen steps: what is established, what is excluded, and what remains open?",
  fig:{type:"bars", unit:"affix agreement (z, copies excluded, same harness, 30k tokens)", baseline:0, data:[
    ["VOYNICH",61.6,true],["U3 (+ SPLIT MOVE)",24.2,false],["U2",0.5,false]]},
  fig2:{type:"bars", unit:"U3 agreement (z) with one move disabled · the ablation", baseline:0, data:[
    ["FULL U3",24.2,true],["NO SAME-POSITION",19.8,false],["NO JOIN",19.7,false],["NO ENDING SWAP",19.1,false],["NO DERIVE-LAST",17.1,false],["NO SPLIT",-0.8,false]]},
  plain:[{t:"Why cutting a word in two manufactures 'grammar'", h:
`<p>Recall Plate 3: inside a Voynich word, each glyph strongly constrains the next, the way <span class="hl">q</span> constrains <span class="hl">u</span> in English. Now cut a written word somewhere in the middle and put a space there. The glyphs on either side of the new space used to be neighbours inside one word, so they still obey the word-internal habits. Measured from outside, the first piece's ending now genuinely predicts the second piece's beginning. That is the whole trick: a space inserted into a rule-bound word converts word-internal structure into what looks like agreement between words.</p>
<p>The same thing happens in English if you write "handwriting" as "hand writing" often enough: a statistician who trusts your spaces will find that certain endings attract certain beginnings, and might read it as grammar. No grammar was added; spaces were moved.</p>
<p>Two disciplines keep this result honest. The five borrowed habits run at Timm's shipped probabilities, not values we chose, and nothing was tuned to the agreement statistic; the pass/fail criterion was fixed before the first run. And the numbers are compared on one harness: at this plate's matched 30,000-token measurement the Voynich scores z = 61.6 (the z ≈ 80 on Plate 12 is the full-corpus figure), U3 scores 24.2, and the cut habit accounts for all of it. What U3 does NOT show: that the manuscript's scribes actually cut words this often. That is a countable follow-up (the split and joined variants, like olchedy against ol chedy, can be tallied per folio), and until it is done the remaining 60% of the signal stays honestly open.</p>`}],
  algo:[{t:"The split move inside U3 (scripts/u3_generator.py)", c:
`# Timm conf.properties, verbatim -- no constant below was fitted by us:
P_ENDSWAP   = 0.50   # give a copied word the ending of another recent word
P_COMBINE   = 0.15   # weld the previous short word onto this one
P_SPLIT     = 0.15   # cut a long word in two            <-- carries the effect
P_REUSE_LAST= 0.10   # derive the next word from the one just written
P_SAMEPOS   = 0.28   # when copying, prefer the word directly above

# ... U2's copy/fresh-word machinery produces wd, then:
emit = [wd]
if len(wd) >= 6 and rng.random() < P_SPLIT:
    cut = rng.integers(2, len(wd) - 1)      # both halves keep >= 2 glyphs
    emit = [wd[:cut], wd[cut:]]             # the seam is a REAL glyph
                                            # transition: measured from
                                            # outside, ending predicts
                                            # beginning
elif cur_line and len(cur_line[-1]) <= 4 and rng.random() < P_COMBINE:
    emit = [cur_line.pop() + wd]            # the inverse habit (weld)

# Ablation (results/u3_generator.json): full U3 z=24.2; removing any
# other habit leaves z in 17-20; removing P_SPLIT alone -> z=-0.8.`}]
},
{
  dwg:"PLATE 17 · CONCLUSION", sheet:"SHEET 17/17", kind:"conclusion",
  established:[
    "The text is statistically anomalous in exactly two places: conditional character entropy h2 ≈ 2.4 bits (languages 3.42 to 3.60) and word-length spread σ = 1.82 (languages 2.4 to 2.9). The other headline statistics follow from these plus the copying mechanism.",
    "The anomalies are not a register effect (Latin prose, botanical and naming registers all sit near h2 3.5), not a simple cipher (substitution is excluded by arithmetic; verbose transforms implicate the transform, not a source language; a positive control shows the method does recover genuinely enciphered Latin), and not inventedness with meaning (Esperanto lands with the natural languages).",
    "One mechanism accounts for the profile: a within-word slot grammar plus local copy-and-mutate. The self-citation signatures are the largest effects measured (z ≈ 78, 50 and 23 against 200-shuffle nulls), and no language control shows the ensemble: Hebrew, the runner-up, reproduces the exact-repeat spike alone, for a known linguistic reason, with half the locality gradient and normal entropy.",
    "A four-parameter mechanical generator reproduces the whole 17-metric fingerprint (combined error 0.179 vs 0.274 for the best specialist), with the Zipf slope, vocabulary size and Heaps growth emerging unfitted. Mechanical generation is sufficient for every internal statistic.",
    "The generator under-reproduces one structure: long-range association information (+0.16 bits, z ≈ 9) that tracks the illustrated content down to the individual page. This is the strongest internal evidence on the content side.",
    "The labels have catalogue layout but filler content: one label per drawn object, yet adjacent interchangeable figures carry near-identical labels, visibly different objects carry minor variants of one stem, and the herbal pages are nearly label-free.",
    "The label-to-image census, run under four decision rules fixed before the data was collected, found no naming signal in any of the four tests: recurring labels hold no angular slot across pages, near-identical figures carry labels no more alike than chance, the one repeated root drawing carries two different labels, and eleven of twelve central zodiac words are later-hand month names, not Voynichese. The label layer is a register, not a naming catalogue."],
  open:[
    "A word's ending predicts the next word's beginning as strongly as Latin grammatical agreement. A token-splitting move transplanted from Timm's implementation accounts for 42% of it mechanically (Plate 16); the remaining 58%, and the manuscript's actual splitting rate, stay open.",
    "No generator yet reproduces the folio-to-folio vocabulary drift; page-conditioning recovers only about 15% of the long-range budget.",
    "The internal programme is complete: with the census done, no further test on the text alone looks capable of separating the two remaining readings. Movement now would have to come from outside the statistics: codicology, pigments, provenance, or a demonstration that some subset decodes."],
  next:"The results support a specific account of the Voynichese text. Its two statistical anomalies, a conditional character entropy near 2.4 bits and a word-length standard deviation of 1.82, are reproduced, together with the rest of the 17-metric fingerprint, by a four-parameter process of local copying with small mutations; the copy signatures that identify this process are the largest effects measured in the project and appear in no reference language. The strongest apparently grammatical structure, cross-word affix agreement, is 42% attributable to word-boundary placement rather than to syntax. The label layer, tested under decision rules fixed before the images were examined, shows none of the positional, referential or lexical behaviour of a naming system.\n\nTwo interpretations remain compatible with these results: production of text without semantic content by a practised generation procedure, with vocabulary drifting as the illustrations change; or a formulaic text layer of very low information content whose statistics imitate such a procedure. Every test reported here favours the first. The second cannot be excluded from internal evidence alone, because a mechanism shown to be sufficient is not thereby shown to have operated.\n\nThree residual structures define what any future account, mechanical or linguistic, must explain: the unattributed 58% of the affix agreement, the folio-to-folio vocabulary drift that no generator reproduces, and the long-range association excess. Distinguishing the two remaining interpretations requires external evidence: codicology, pigment and ink analysis, provenance, or a demonstrated decipherment of some subset of the text."
}
];
