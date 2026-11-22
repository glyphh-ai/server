# Applicant corpus v1: protocol

Written before the generation run. The numbers this protocol asks for are reported in the PR; nothing here is
tuned after seeing them.

## What the corpus is for

It pre-trains the resume-screener template's two Ada gates:

- **fit**: pursue or pass for the role. Labels `strong`, `borderline`, `poor`.
- **generated**: how much of the application an AI wrote. Labels `some`, `mostly`, `fully`.

Every applicant is fictional and every one is written with Claude. There is no human-written class: a human
application is not a fourth label but the absence of a close precedent (see "The human side" below).

## How each label is made

- **fit** comes from the spec in `specs.py`, fixed before any model writes: `strong` has every must-have of the
  posting and the years it asks for; `borderline` has two or three must-haves, a year or two short, from the
  posting's near-miss background; `poor` comes from another field with at most one must-have. The writer is told
  what the applicant has and lacks and may not add a lacked skill. Claude never judges fit afterwards.
- **generated** comes from the pipeline the applicant goes through (`prompts.py`):
  - `some`: Claude drafts the application in the person's own voice (one of twelve, with slips and quirks), then a
    second call makes one light edit (one of five, such as polishing only the summary) and returns the rest as is.
  - `mostly`: the same kind of draft, then a second call rewrites every part, keeping the facts.
  - `fully`: one call writes the whole application from the facts alone.
  Mostly and fully vary the AI tells across four levels, from the stock "thrilled to apply" voice to "told to
  sound natural".

## Balance and split

- 10 roles x 3 fits x 3 generated = 90 cells, 27 applicants per cell, 2,430 in all; each fit and each generated
  class is a third of the corpus.
- In every cell, 5 applicants (18.5%) are marked `split: "test"`, 450 in all. The test split is never used to
  seed or tune a gate; it is only read to measure one.
- Layout (4) x font (6), and which of two models writes (about 30% the larger one), are drawn independently of
  both labels, so neither format nor writer can stand in for a label.
- Applicants whose batch request failed are dropped, and the counts per class and split are reported as built.

## Sanity baseline: can a format tell alone separate "generated"?

On the train split, for each single feature, pick the best rule of the form "two thresholds on the feature, the
three classes in some order" (all six orders tried). Report its accuracy on the test split. No model is fitted;
it is a threshold rule only. Features: characters, words, mean words per sentence, em dashes per 1,000 words,
bullets, layout, font.

- Chance is 33%. **Bar: if any single feature scores 60% or more on the test split**, the generated gate may be
  learning that tell rather than authorship. That is reported as a finding, not fixed by changing the corpus
  after the fact.
- The same rule is run for fit, where length should not separate the classes either.

## The human side: tested by probing

A real person's application is unlike every generated precedent by default. The gate tests that by probing: an
application whose nearest precedent is far counts as human.

- The reference is the nearest-precedent similarity distribution of the **held-out test split** against the
  train split (5th, 25th, 50th, 75th, 95th percentiles). Held-out generated applications should sit inside it;
  a hand-written or real held-out application should come back below it, with no close precedent.
- That distribution must be recorded with the gate's own similarity when the template seeds from this corpus.
  `check.py` records a lexical stand-in (word-set overlap) so the corpus has a reference of its own, labelled as
  not the gate's.

## Integrity

- Every `.docx` and `.pdf` opens and every `.eml` parses; counts of failures are reported.
- 20 applicants, drawn at random, are parsed back from both their `.docx` and `.pdf` and the text is compared with
  the application JSON (the name and the first job title must appear in both).
- The real spend is the sum of the batches' usage at batch prices, under a hard cap of $60, checked before each
  run with a 20-applicant pilot's rate plus a quarter of headroom.
