/* Voynich story: plate data. Prose follows STORY.md (2026-07-04, scientific-voice revision).
   Numbers are the current post-review values (results/*.json). Charts render from `fig`;
   collapsible algorithm blocks render from `algo` (trimmed from the real scripts). */
window.PLATES = [
{
  dwg:"PLATE 01 · ZIPF REPLICATION", sheet:"SHEET 1/13",
  hyp:"If the Voynich is real writing, its words should follow Zipf's law: the commonest word about twice the second, three times the third, the straight line every language shares on log-log axes.",
  test:"Counted every word, ranked by frequency, plotted rank against frequency on log-log axes beside six real languages and two controls: uniform-pool gibberish (1,000 equally-likely invented words, the source video's control) and a 'monkey text' of random letters with spaces.",
  verdict:"v-mix", verdictText:"VALIDATED, LOW POWER",
  res:"The Voynich lands on the same descending diagonal as the six languages. The uniform-pool gibberish fails: a near-horizontal line (slope -0.05) that falls off a cliff at its 1,000-type limit. The monkey text is not on the diagonal: a stepped curve with a shelf of equally common short words at the head, descending more shallowly than the languages (slopes -0.49 to -0.69 vs about -0.9). It nevertheless passes a loose Zipf test. A test that random typing nearly passes cannot separate meaningful text from mechanical production; Zipf conformity constrains word-frequency structure, not meaning.",
  next:"If Zipf cannot separate it from noise, is its shape closer to one particular language?",
  fig:{type:"zipf"},
  algo:[{t:"The two control texts (scripts/build_controls.py)", c:
`SEED = 1492   # fixed seed; both controls are exactly reproducible
N = 30000     # tokens per control, matching the analysis window

def build_uniform_pool(rng):
    """The source video's control: ~1,000 invented words drawn
    UNIFORMLY. Every word has the same probability, so the
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
  dwg:"PLATE 02 · NEAREST LANGUAGE", sheet:"SHEET 2/13",
  hyp:"The exact bend of the rank-frequency curve is language-specific. The Voynich's curve should sit nearest whichever of the six languages it most resembles.",
  test:"Measured the distance from the Voynich curve to each language three ways: by exponent, by curve-shape error, and by distributional divergence.",
  verdict:"v-no", verdictText:"INCONCLUSIVE",
  res:"By slope it is nearest Latin; by whole-curve shape, nearest German. The two answers disagree, and 'nearest' is determined by morphology and tokenisation rather than by content. (A 'German wins 91% of draws' figure was later retired: the bootstrap draws were overlapping windows, a corpus-length artefact.)",
  next:"Rather than which language it most resembles: which of its statistics fall outside the range of every language at once?",
  fig:null
},
{
  dwg:"PLATE 03 · CHARACTER ENTROPY h2", sheet:"SHEET 3/13",
  hyp:"If the surface statistics look normal, a deeper one may be abnormal: how predictable each character is from the one before it.",
  test:"Measured second-order character entropy h2 (uncertainty about the next glyph given the current one) and the spread of word lengths, for the Voynich and every language.",
  verdict:"v-yes", verdictText:"TWO ANOMALIES",
  res:"The Voynich's h2 is about 2.4 bits against 3.42 to 3.60 for the reference languages: its glyphs are far more predictable than any of the real scripts measured. Its word lengths are unusually uniform too (standard deviation 1.82 vs 2.4 to 2.9). These two facts are what the rest of the project has to explain.",
  next:"The manuscript is largely a herbal. Could the low entropy be a specialised-vocabulary effect?",
  fig:{type:"bars", unit:"h2 (bits) · lower = more predictable", baseline:3.5, band:[3.42,3.60], data:[
    ["VOYNICH",2.40,true],["ENGLISH",3.60,false],["LATIN",3.45,false],["GERMAN",3.43,false],["HEBREW",3.89,false]]},
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
  dwg:"PLATE 04 · REGISTER TEST", sheet:"SHEET 4/13",
  hyp:"Technical writing has repetitive vocabulary. The right comparison is a herbal, not a novel, and against that the Voynich might look normal.",
  test:"Added three Latin registers: narrative prose (Caesar), technical botany (Pliny), and pure naming (33,000 Linnaean binomials). Re-measured h2 and word length.",
  verdict:"v-no", verdictText:"REFUTED",
  res:"All three registers cluster at h2 near 3.45 to 3.52 while the Voynich sits alone at 2.4. Botanical text accumulates rare plant and drug names, which raises entropy; the naming-heavy registers sit furthest from the Voynich, not nearest. The anomaly is not a register effect: it is a property of the notation system, not of the subject matter.",
  next:"If it is not a natural register, is it a real language hidden under a cipher?",
  fig:{type:"bars", unit:"h2 (bits) across registers", baseline:3.5, band:[3.42,3.60], data:[
    ["VOYNICH",2.40,true],["PROSE LATIN",3.45,false],["BOTANY LATIN",3.52,false],["PLANT NAMES",3.49,false]]}
},
{
  dwg:"PLATE 05 · CIPHER TESTS", sheet:"SHEET 5/13",
  hyp:"A real language run through a cipher would look alien on the surface but carry a recoverable signal underneath.",
  test:"Three tests: a substitution cipher (excluded by arithmetic, a glyph swap cannot change entropy); a verbose transform with abbreviation and affixes; and 'peeling' the Voynich's affixes to see if a language surfaces.",
  verdict:"v-no", verdictText:"NO SIMPLE CIPHER",
  res:"Substitution is mathematically excluded: it cannot lower h2. The verbose transform reaches low h2 and narrow length but works equally from Latin, English and German, implicating the transform, not a source. Peeling reveals no language. A positive control applied the same method to genuinely-enciphered Latin and recovered 23 of 25 glyphs, so the null result on the Voynich is not a failure of the method.",
  next:"If no simple cipher generates these statistics, what mechanism produces low entropy and uniform length directly?",
  fig:{type:"formula", lines:[
    ["H(swap(X)) = H(X)","a one-for-one substitution cannot change entropy, so it cannot lower h2"],
    ["decode(encipher(Latin)) → 23/25 glyphs","positive control: the method works when a real cipher is present"]]}
},
{
  dwg:"PLATE 06 · SLOT GRAMMAR", sheet:"SHEET 6/13",
  hyp:"The words are built from a small kit of fixed pieces in fixed positions, a slot grammar, so the next glyph is nearly determined by the current one.",
  test:"Measured per-position glyph menus, the coverage of a small affix kit, and whether a simple Markov glyph-transition model reproduces the low h2.",
  verdict:"v-yes", verdictText:"VALIDATED, WITH A REMAINDER",
  res:"A small affix kit covers 66 to 79% of words (vs 33 to 53% for languages), glyph transitions are about twice as concentrated as in any of the languages, and a Markov model reproduces the low h2. Two constraints sit on top and are not consequences of it: the narrow word-length band, and elevated whole-word repetition. An additional process regulates word length and reuses whole words.",
  next:"How are the words arranged in sequence? Is there grammar between words?",
  fig:{type:"bars", unit:"top-10 two-glyph suffix coverage: share of words ending in the kit", baseline:null, pct:true, data:[
    ["VOYNICH",0.79,true],["GERMAN",0.53,false],["LATIN",0.47,false],["ENGLISH",0.34,false]]}
},
{
  dwg:"PLATE 07 · WORD-ORDER INFORMATION", sheet:"SHEET 7/13",
  hyp:"In real language the previous word strongly predicts the next. The Voynich should show the same if it carries sentences.",
  test:"Measured word-order information: how much the previous word reduces uncertainty about the next, with a shuffle control to cancel sample-size bias.",
  verdict:"v-no", verdictText:"ALMOST NONE",
  res:"Word order carries about 1.7% of the word-level uncertainty against 2.6 to 7.4% across the prose languages. (Technical Latin at 1.2% sits just below it, so the statistic is register-relative.) The token stream is nearly unordered: inconsistent with obscured connected prose, consistent with a list, a catalogue, or table-driven generation.",
  next:"If word order is nearly random but words are locally repetitive, is each word copied from a nearby recent word and lightly changed?",
  fig:{type:"bars", unit:"word-order information (% of word entropy) · higher = more grammar", baseline:null, pct:true, data:[
    ["VOYNICH",0.017,true],["TECH LATIN",0.012,false],["ITALIAN",0.026,false],["GERMAN",0.046,false],["ENGLISH",0.072,false]]},
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
  dwg:"PLATE 08 · SELF-CITATION", sheet:"SHEET 8/13",
  hyp:"Each word is produced by copying a recent word and rewriting it with a small change (Timm & Schinner 2019). A word should resemble a recent predecessor more than chance allows, more so for nearer ones.",
  test:"For each word, found the minimum edit distance to the previous few words, compared against a shuffle of the same tokens (identical vocabulary, sequential copying destroyed). Tracked three signatures: below-shuffle nearest distance, an excess of near-identical neighbours, and a locality gradient.",
  verdict:"v-yes", verdictText:"LARGEST EFFECTS",
  res:"All three signatures fire far above every language: nearest-distance excess z≈78, copy spike z≈50, locality gradient z≈23, against 200-shuffle null distributions. Hebrew matches the exact-repeat part but not the local gradient, so the Voynich's copying is specifically local. A single process accounts for the slot grammar, the near-zero word order and the local repetition: copy a nearby word and mutate it.",
  next:"If copying explains the pieces, can one generator reproduce the whole fingerprint at once?",
  fig:{type:"zbars", unit:"signature strength (z vs 200-shuffle null)", data:[
    ["NEAREST DIST",78],["COPY SPIKE",50],["LOCALITY GRAD",23]]},
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
  dwg:"PLATE 09 · GENERATOR TOURNAMENT", sheet:"SHEET 9/13",
  hyp:"A single generator (length-locked word-forms + copy-and-mutate + a mild per-section vocabulary bias) reproduces all the statistics, with no meaning anywhere.",
  test:"A tournament: specialist generators against unified ones, scored on the same 17-metric fingerprint. Copy parameters tuned only on the copying metrics, so the Zipf slope and vocabulary size are free to emerge or not.",
  verdict:"v-yes", verdictText:"MECHANICAL IS SUFFICIENT",
  res:"The four-parameter unified generator reproduces the whole fingerprint (combined error 0.179) better than any specialist (0.274), and the Zipf slope, type count and Heaps growth emerge unfitted (generator Zipf -0.87 vs Voynich -0.89). Nothing in the internal statistics requires meaning. Sufficiency is not necessity: a highly formulaic real text is not excluded.",
  next:"A book-length message needs long-range structure. Does the Voynich carry information across hundreds of words, or go flat?",
  fig:{type:"bars", unit:"combined fit error vs Voynich (lower = better all-rounder)", baseline:null, data:[
    ["U2 UNIFIED",0.179,true],["U1 UNIFIED",0.199,false],["BEST SPECIALIST",0.274,false],["ENGLISH",0.660,false]]},
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
  dwg:"PLATE 10 · LONG-RANGE INFORMATION", sheet:"SHEET 10/13",
  hyp:"If it is meaningless local generation, mutual information between words collapses within a few words. If it carries content, information persists across hundreds of words.",
  test:"Measured mutual information between words d apart, split into repetition (same word) and association (different words predicting each other), out to 800 words, against a 200-shuffle null.",
  verdict:"v-mix", verdictText:"POSITIVE FOR CONTENT",
  res:"The Voynich carries long-range association information (signed excess +0.16 bits, z≈9) that a single real work does not. The mechanical generator reproduces at most about a third of it under a generous accounting, and none under the strict signed accounting (its excess goes negative, like the real languages'), missing the smooth positive decay under both. The information tracks the illustrated content down to the individual page.",
  next:"Two readings now survive, differing almost only in the labels. One test separates them: do the labels match the pictures?",
  fig:{type:"decay"},
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
  dwg:"PLATE 11 · RED-TEAM + RE-AUDIT", sheet:"SHEET 11/13",
  hyp:"Our conclusions might be artefacts of weak controls.",
  test:"A six-front adversarial red-team, then a full statistical review that found the project leaned on 2-to-3-shuffle nulls and re-ran everything against 200-shuffle real null distributions with z-scores.",
  verdict:"v-mix", verdictText:"MAIN FINDINGS HOLD",
  res:"The low h2, narrow length and self-citation signal all hold. The self-citation signal is absent from real prose, a Latin word list and enciphered Latin. Several numbers moved down: '75%' → about a third; a collocation crack fell to 1σ and was retracted; a '5% dialect' slice went to zero; a topical-clustering signal halved. All corrections reduced the strength of previously published claims; most favoured the mechanical reading, while the long-range correction favoured the content reading.",
  next:"With honest nulls in hand, are there tests that could still break the mechanical account, or find meaning we have missed?",
  fig:{type:"corrections", data:[
    ["Long-range reproduction","~75%","~a third"],
    ["Collocation crack","real +0.029","retracted (~1σ)"],
    ["Currier dialect slice","5%","≈0"],
    ["Topical clustering","0.091","0.051"]]}
},
{
  dwg:"PLATE 12 · FALSIFICATION TESTS", sheet:"SHEET 12/13",
  hyp:"Six tests, each specified in advance with an outcome that would count against the leading hypothesis or find meaning where we had not looked.",
  test:"T1 copy source (line above vs stream); T3 syntax hunt + affix agreement; T4 scribal hands; T8 zodiac label recurrence; T6 a constructed-language control (Esperanto); T2 label reuse across sections.",
  verdict:"v-mix", verdictText:"ONE REAL REFINEMENT",
  res:"T1: copying is local but not specifically the line above (a memory-window process). T3: no subset has language-like word order, but a word's ending predicts the next word's beginning as strongly as Latin agreement (z≈80), survives copy-exclusion, and the generator misses it: a real cross-word rule, though not full syntax. T4: all four hands share the fingerprint (consistent with a taught method). T8 (text side): zodiac labels recur as a register effect, not a naming catalogue. T6: Esperanto, a meaningful constructed language, lands with the natural languages, not the Voynich. T2: pharmaceutical labels do not reuse the herbal naming vocabulary (their own diverse register).",
  next:"The one place the account under-reproduces is page-level structure. Two moves aim at that gap.",
  fig:{type:"zbars", unit:"suffix-to-prefix agreement (z, copies excluded): a word's ending predicts the next word's start", data:[
    ["VOYNICH",80],["LATIN",67],["GENERATOR",0]]},
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
  dwg:"PLATE 13 · THE GAP + THE DECISIVE TEST", sheet:"SHEET 13/13",
  hyp:"The mechanical account is sufficient for every internal statistic. The one place it under-reproduces is page-level structure: long-range association tracking the pictures, and folio-to-folio vocabulary drift.",
  test:"Two moves at that gap: the label-to-image test (a full-manuscript viewer pairing Beinecke page scans, 226/227 folios, with the transcription, read directly); and an illustration-conditioned generator whose method depends on the page's illustrated class.",
  verdict:"v-mix", verdictText:"CATALOGUE LAYOUT, FILLER CONTENT",
  res:"Label-to-image (visual pass): the manuscript has catalogue LAYOUT (one label at each star-nymph, one above each pharma root) but filler CONTENT: adjacent interchangeable nymphs carry near-identical labels, six different roots carry rhyming variants, and the herbal has almost no labels. F1 does not fire; the pictures exclude a rich distinctive catalogue. Separately, page-conditioning moves the generator's long-range excess from -0.12 to +0.03 (a real improvement, but ~15% of the Voynich) and still misses the folio-to-folio drift.",
  next:"After thirteen steps: what is established, what is excluded, and what remains open?",
  fig:{type:"bars", unit:"long-range structure budget (signed bits) · negative = flat", baseline:0, data:[
    ["VOYNICH",0.21,true],["PAGE-CONDITIONED",0.03,false],["SECTION-ONLY (U2)",-0.12,false]]}
},
{
  dwg:"PLATE 14 · CONCLUSION", sheet:"SHEET 14/14", kind:"conclusion",
  established:[
    "The text is statistically anomalous in exactly two places: conditional character entropy h2 ≈ 2.4 bits (languages 3.42 to 3.60) and word-length spread σ = 1.82 (languages 2.4 to 2.9). The other headline statistics follow from these plus the copying mechanism.",
    "The anomalies are not a register effect (Latin prose, botanical and naming registers all sit near h2 3.5), not a simple cipher (substitution is excluded by arithmetic; verbose transforms implicate the transform, not a source language; a positive control shows the method does recover genuinely enciphered Latin), and not inventedness with meaning (Esperanto lands with the natural languages).",
    "One mechanism accounts for the profile: a within-word slot grammar plus local copy-and-mutate. The self-citation signatures are the largest effects measured (z ≈ 78, 50 and 23 against 200-shuffle nulls) and are absent from every language control.",
    "A four-parameter mechanical generator reproduces the whole 17-metric fingerprint (combined error 0.179 vs 0.274 for the best specialist), with the Zipf slope, vocabulary size and Heaps growth emerging unfitted. Mechanical generation is sufficient for every internal statistic.",
    "The generator under-reproduces one structure: long-range association information (+0.16 bits, z ≈ 9) that tracks the illustrated content down to the individual page. This is the strongest internal evidence on the content side.",
    "The labels have catalogue layout but filler content: one label per drawn object, yet adjacent interchangeable figures carry near-identical labels, visibly different objects carry rhyming variants of one stem, and the herbal pages are nearly label-free."],
  open:[
    "A word's ending predicts the next word's beginning as strongly as Latin grammatical agreement (z ≈ 80). The rule is real, survives copy-exclusion, and is missing from the generator.",
    "No generator yet reproduces the folio-to-folio vocabulary drift; page-conditioning recovers only about 15% of the long-range budget.",
    "A deeper label-to-image census (full zodiac slot census, same-referent image test, the pharmaceutical sections) is the remaining decisive work."],
  next:"Two readings survive. (1) Meaningless auto-generation by a practiced scribal method, with vocabulary drifting as the pictures change: the account favoured by the internal statistics and by the first visual pass. (2) A formulaic, low-information label layer: real but thin content, so templated that its statistics mimic generation. A richly meaningful catalogue is excluded with reasonable confidence. Sufficiency is not necessity, and internal statistics alone cannot close the remaining gap; the deciding evidence is label-to-image correspondence."
}
];
