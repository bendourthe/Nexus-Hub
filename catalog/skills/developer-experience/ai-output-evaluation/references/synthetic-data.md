# Synthetic Evaluation Data

How to generate evaluation cases from an explicit coverage model instead of unbounded prompting. Read this cold: it assumes no other part of the evaluation skill is in context.

"Generate 200 test questions about our product" produces 200 cases clustered around whatever the generating model finds most salient, with no way to know what is missing. The method below inverts that: decide what the set must cover, then generate against the plan, then verify the result actually covers it.

Synthetic data supplements a real evaluation set. It does not replace one, and it never becomes the held-out test split (see Step 7).

## Step 1: Declare dimensions and allowed values

A dimension is an axis along which cases meaningfully differ - meaningfully meaning the system could plausibly behave differently along it. Enumerate the values; if a dimension is continuous, bucket it.

Worked matrix for a document-QA system:

| Dimension | Allowed values |
|-----------|----------------|
| `query_type` | `factual_lookup`, `comparison`, `multi_hop`, `summarization` |
| `document_age` | `current`, `superseded`, `mixed` |
| `answer_availability` | `fully_answerable`, `partially_answerable`, `unanswerable` |
| `phrasing` | `precise_terminology`, `colloquial`, `misspelled` |

Four dimensions, 4 x 3 x 3 x 3 = 108 full combinations. Two things fall out immediately, and both are the point of doing this before generating:

- `unanswerable` is a dimension value. Unbounded generation almost never produces unanswerable questions, because the generating model is looking at the corpus and writing questions it can answer. A system's behavior on unanswerable queries is usually its worst behavior and its least tested.
- `superseded` documents only matter in combination with `factual_lookup`, which is the kind of interaction a flat list of prompts will not surface.

## Step 2: Add constraints

Not every combination is valid or interesting. Record constraints explicitly so the exclusions are a decision rather than an accident:

```
CONSTRAINT: answer_availability = unanswerable  =>  document_age = any
            (age is irrelevant when nothing answers the query)
CONSTRAINT: query_type = multi_hop  =>  answer_availability != partially_answerable
            (partial multi-hop is a separate confounded case; excluded deliberately)
```

Each constraint removes combinations from the target. State the reason next to it, or a later reader cannot tell an excluded case from a forgotten one.

## Step 3: Choose a coverage target

Full cartesian coverage is rarely worth it and grows multiplicatively. Pick a target and state it:

| Target | Meaning | Cost for the matrix above |
|--------|---------|---------------------------|
| **1-tuple** (each value once) | Every value appears at least once | 4 cases |
| **2-tuple** (pairwise) | Every pair of values from two dimensions appears together at least once | at least 12 (the largest pair product, 4 x 3); typically 13-16 |
| **3-tuple** | Every triple appears | roughly 40-50 |
| **Full cartesian** | Every combination | 108, minus constraint exclusions |

**Pairwise is the default.** Most interaction bugs involve two factors, and pairwise gets there for roughly a tenth of full cartesian. Move to 3-tuple only for a specific interaction you have reason to suspect.

Record the target in the `dataset_manifest` under `coverage_dimensions`, and verify it after generation rather than assuming the generator honored it.

## Step 4: Generate in batches

Generate in batches of 20-30 against explicit cells, not in one large unstructured request.

- **Name the cell in the prompt.** "Write a colloquially-phrased comparison query whose answer is only partially available in the corpus" produces a case for a known cell. "Write some test queries" does not.
- **Use the model or local tooling already authorized for the project.** Nothing here needs a hosted generation service, an additional dependency, or a new credential.
- **Record `generator_config`.** Provenance carries `source: synthetic`, `derived_from` (the corpus or seed cases), and enough configuration to regenerate the batch. A synthetic case whose origin is unrecorded cannot be audited later, and it will be indistinguishable from a human-written one within a month.
- **Batch, then review, then continue.** Reviewing batch one before generating batch two catches a systematic misunderstanding after 25 wasted cases instead of 200.

## Step 5: Filter before promoting

Every generated case passes four checks before it enters the evaluation set. Run them in this order; each is cheaper than the next.

### Duplicate detection

Near-duplicates inflate the case count without adding coverage, and they silently reweight the aggregate toward whatever got duplicated. Compare normalized text (lowercased, punctuation stripped) for exact matches, then check for cases differing only in a substituted entity. Two queries identical apart from a swapped product name are one case, not two, unless the entity is itself a declared dimension.

### Source leakage

A generated case whose answer is quoted verbatim from the corpus tests string matching, not retrieval or reasoning. Flag any case where a long span of the expected answer appears verbatim in the source passage. Either rewrite the case or record the overlap so the score is read with it in mind.

### Difficulty validation

A set where the system scores 100 percent discriminates nothing. Run the current system over the new batch:

- Everything passes: the cases are too easy. Keep a few as regression coverage, generate harder ones.
- Everything fails: check the cases are actually correct before concluding the system is bad. Generated cases with wrong expected answers are common, and they look exactly like system failures.
- A spread: useful. Keep it.

### Human spot check

Review at least 10 percent, or 20 cases, whichever is larger. Confirm the case is answerable as labeled, the expected answer is right, the phrasing is natural, and it sits in the cell it was generated for. Generated cases carry generated labels, and an unreviewed label is a guess with formatting.

Record spot-check results. A batch with a high error rate in the sample is rejected wholesale; the errors are systematic, not scattered.

## Step 6: Verify coverage after the fact

Recompute achieved coverage from the promoted cases and compare against the Step 3 target. Report the gap rather than restating the target:

```
Target: 2-tuple coverage over 4 dimensions
Promoted cases: 31
Pairs required: 63 (after constraint exclusions)
Pairs covered: 58
Uncovered: multi_hop x misspelled (4 pairs), unanswerable x superseded (1 pair)
```

Uncovered pairs are the generation plan for the next batch. This step is what makes the whole method worth the setup: without it you have a coverage target and no idea whether you hit it.

## Step 7: Keep synthetic data out of the held-out test split

This is the rule that protects every number downstream.

- Synthetic cases may go in the **train** and **development** splits freely.
- The **held-out test** split should be human-authored or human-verified real cases. A test split of synthetic cases measures how well the system handles what a generator imagines users do.
- If synthetic cases must appear in a test split because real ones do not exist, mark them and report their proportion with every number computed from that split.
- Never generate cases from the test split's contents. That is leakage with extra steps.

Record the decision in the `split_manifest` so a later reader can weigh the numbers correctly.

## Local-data handling

- Seed corpora, generated cases, and their labels stay local by default; `redaction_status.state` is `raw` and `export_authorized` is `false`.
- Generation from real production content produces synthetic cases that can carry real data through - a "synthetic" query built from a real support ticket may contain the customer's name. Redact before the case is promoted, not after it is committed.
- Every synthetic case is marked as such in `provenance.source`. A synthetic case that loses its marking and gets treated as ground truth is a permanent quiet error in every downstream measurement.
- Any export applies the per-category policy in `[[egress-redaction]]` as an explicit, separately authorized step.

## Verification

- [ ] Dimensions and their allowed values are enumerated before any case is generated
- [ ] Constraints are recorded with the reason each combination is excluded
- [ ] A coverage target is stated (1-tuple, pairwise, 3-tuple, or full) and recorded in the `dataset_manifest`
- [ ] Cases were generated in batches against named cells, not in one unstructured request
- [ ] Every case carries `provenance` with `source: synthetic`, `derived_from`, and `generator_config`
- [ ] Duplicate detection ran, including near-duplicates differing only by a substituted entity
- [ ] Source-leakage checks ran, and verbatim-overlap cases were rewritten or recorded
- [ ] Difficulty was validated against the current system and the batch is neither all-pass nor all-fail
- [ ] At least 10 percent or 20 cases were human spot-checked, and the results were recorded
- [ ] Achieved coverage was recomputed and the uncovered cells were reported, not just the target
- [ ] Synthetic cases are absent from the held-out test split, or their proportion is reported with every number from it
- [ ] No case left the host un-redacted, and no hosted generation service, dependency, or credential was added
