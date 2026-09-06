# Error Analysis

How to turn a pile of failing outputs into quantified failure categories and permanent regression coverage. Read this cold: it assumes no other part of the evaluation skill is in context.

The goal is not to fix the failures you looked at. It is to learn which failure modes exist, how often each occurs, and which ones justify work - then to make each confirmed pattern impossible to reintroduce silently. An analysis that ends with "we fixed those three" has produced no reusable knowledge.

## Step 1: Sample traces deliberately

A `trace_sample` is one captured execution: the input, the output, and whatever intermediate steps were recorded. How you select them determines what your numbers mean.

| Sampling method | What it is good for | What it cannot tell you |
|-----------------|---------------------|-------------------------|
| `random` | Base rates: how often does each failure mode occur | Rare failure modes, without a large sample |
| `stratified` | Comparable rates across segments (query type, customer tier, locale) | Overall base rate, unless you reweight |
| `failure_biased` | Discovering what the failure modes ARE | Any rate at all |
| `exhaustive` | Small evaluation sets where everything is reviewed | Nothing; it is the ideal when affordable |

The single most common reporting error in error analysis is running a `failure_biased` sample and then reporting category percentages as if they were base rates. If you sampled 50 known failures and 30 were retrieval problems, you have learned that retrieval problems exist and are common **among failures**. You have learned nothing about how often the system fails. Record `sampling_method` on every trace and repeat it next to every percentage.

Sample size: 30-50 traces is enough to discover the major categories, because category discovery saturates quickly. Measuring their frequencies to a useful precision needs more, and needs a random or stratified sample.

### Minimum metadata per trace

Record enough that a reader can re-find the case and judge whether it generalizes:

- `id`, stable, never reused
- `input` and `output` as captured
- `steps` where available: tool calls, retrieved context, intermediate reasoning
- `sampled_from` (`production`, `staging`, `evaluation_run`, `synthetic`) and `sampling_method`
- `provenance`: when, from where, by what
- `redaction_status`: `raw` by default, `export_authorized: false`

A trace without `sampling_method` cannot be aggregated with any other trace, because you cannot tell whether combining them is legitimate.

## Step 2: Build a non-overlapping taxonomy

Read 20-30 traces before naming a single category. Categories invented in advance describe the failures you expected; categories derived from reading describe the ones you have.

Each category in an `error_taxonomy` needs four things, and the last two are the ones people skip:

- **`name`** - short and specific. "Wrong answer" is not a category.
- **`definition`** - one sentence stating what the failure IS.
- **`inclusion_criteria`** - the observable signal that puts a trace in this category.
- **`exclusion_criteria`** - what looks like this category but is not, and where those cases go instead.

Exclusion criteria are what make the taxonomy non-overlapping. Without them, two reviewers file the same trace differently and the frequency counts stop meaning anything. A worked pair:

```markdown
### Category: unsupported_claim
Definition: The answer asserts a fact that the retrieved context does not support.
Inclusion: A specific factual claim in the output has no sentence in the provided
  context that entails it.
Exclusion: If the needed fact was never retrieved, this is `retrieval_miss`, not
  `unsupported_claim`. Ask whether the context contained the answer BEFORE judging
  the generator.

### Category: retrieval_miss
Definition: The passage containing the answer was not in the retrieved set.
Inclusion: A passage exists in the corpus that answers the query and was not
  returned at the configured k.
Exclusion: If the passage WAS retrieved and the answer still contradicts it, this
  is `unsupported_claim`. If no passage in the corpus answers the query, this is
  `coverage_gap` and is a content problem, not a retrieval problem.
```

That exclusion pair is doing real work: it enforces the retrieval-before-generation order, so a retrieval failure is never filed as a hallucination.

### Multi-label handling

Decide once, record the decision in `multi_label`, and apply it consistently.

- **Single-label** is the default. Assign the **earliest** failure in the causal chain: if retrieval missed and the model then invented an answer, the category is `retrieval_miss`. Fixing the earliest link is what prevents the downstream failure, so single-label counts point at the work.
- **Multi-label** is correct when failures are genuinely independent (an answer is both factually wrong AND in the wrong language). If you allow it, report both the per-category count and the number of distinct traces, or the percentages sum past 100 and confuse every reader.

Do not mix conventions across a taxonomy version. If the convention changes, increment `error_taxonomy.version`; counts from different versions are not comparable.

## Step 3: Quantify

For each category report four numbers, never just the first:

| Field | Meaning |
|-------|---------|
| Count | Traces in this category |
| Share | Count divided by traces reviewed, with the `sampling_method` stated |
| Severity | Worst plausible consequence when it occurs: cosmetic, degraded, wrong-but-detectable, wrong-and-convincing, harmful |
| Tractability | Whether a known change would address it |

Rank by **severity x frequency**, not frequency alone. A 3-percent category that produces confident, wrong, hard-to-detect answers outranks a 40-percent category that produces slightly verbose but correct ones. Ranking by frequency alone is how teams spend a quarter on formatting.

Attach one to three `example_trace_id` values per category, chosen to be **representative rather than dramatic**. The temptation is to pick the most spectacular failure; it is usually an outlier, and it teaches the reader the wrong shape. Pick the median case, and if the category has a wide range, pick one from each end and say so.

## Step 4: Form root-cause hypotheses

A category is a symptom. Write the hypothesis explicitly, with the evidence that would confirm or refute it, before proposing a fix:

```markdown
Category: retrieval_miss (12 of 50 failure-biased traces, severity: wrong-and-convincing)
Hypothesis: Chunk boundaries split procedure steps, so no single chunk contains a
  complete answer.
Confirming evidence: In 9 of the 12, the answer spans two adjacent chunks.
Refuting evidence would be: the answering passage sits wholly inside one chunk that
  simply ranked below k. That would make this a ranking problem, not a chunking one.
Test: re-run retrieval for these 12 queries at a larger chunk size, with the
  evaluation set and corpus snapshot frozen (see the RAG grid-search procedure).
```

The refuting-evidence line is the part that keeps this honest. A hypothesis with no stated way to be wrong is a conclusion.

## Step 5: Promote confirmed patterns to regression cases

This is the step that converts analysis into durable value. For each confirmed pattern, create a `regression_case`:

- `origin_trace_id` - the trace it came from
- `error_category` - the taxonomy category it exemplifies
- `input` - **minimized**: the smallest input that still reproduces the failure
- `expected_behavior` - the observable condition that must hold
- `assertion` - the binary check
- `status` - `open`, `fixed`, or `accepted_limitation`

Minimize before promoting. A regression case carrying a full production trace is expensive to run, awkward to read, and drags real user data into a committed test suite. Reduce until removing one more element makes the failure stop reproducing.

`accepted_limitation` is a real and useful status. A failure mode you have decided not to fix should still be recorded and asserted, so that if it silently gets worse you find out.

A pattern with no regression case is a pattern you will rediscover. That is the whole cost of skipping this step, and it is paid repeatedly.

## Local-data handling

Traces are the highest-risk artifact in evaluation work: they are real user inputs and real system outputs, captured verbatim.

- **Store locally.** Trace collections stay on the host. `redaction_status.state` is `raw` and `export_authorized` is `false` unless a human explicitly decides otherwise.
- **Redact identifiers before a trace appears in any report.** Names, emails, account ids, and tokens become typed markers. If a finding stops making sense after redaction, the excerpt was too large, not the redaction too aggressive.
- **Never upload a full trace by default.** Share the category, the count, and a minimized excerpt. A category name and a frequency carry the finding; the raw trace carries the user's data.
- **Regression cases are committed artifacts.** Anything promoted into a test suite is minimized and redacted first, because it will live in version control indefinitely.
- Any export applies the per-category policy in `[[egress-redaction]]` as an explicit, separately authorized step.

## Verification

- [ ] Every trace records `sampling_method`, and every reported percentage states it
- [ ] No percentage from a `failure_biased` sample is presented as a base rate
- [ ] Every taxonomy category has a definition, inclusion criteria, and exclusion criteria
- [ ] The multi-label convention is recorded, and percentages are reconciled if multi-label is used
- [ ] Each category reports count, share, severity, and tractability
- [ ] Categories are ranked by severity x frequency, not frequency alone
- [ ] Each category cites one to three representative example traces, not the most dramatic ones
- [ ] Each hypothesis states what evidence would refute it
- [ ] Every confirmed pattern has a `regression_case` with a minimized input and a binary assertion
- [ ] Every trace and regression case is redacted, and no full trace left the host without explicit authorization
