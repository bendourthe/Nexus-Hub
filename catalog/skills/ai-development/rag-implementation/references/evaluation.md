# Retrieval Evaluation

How to measure whether a RAG system's retrieval step is actually finding the right passages, separately from whether the model writes a good answer from them. Read this cold: it assumes no other part of the RAG skill is in context.

The single most common RAG debugging error is blaming the generator for a retrieval failure. A model cannot ground an answer in a passage it never received. Measure retrieval first, always, and only move to generation metrics once retrieval clears its bar.

## Retrieval evaluation is not generation evaluation

These are two different measurements answering two different questions, and they need separate scores.

| Question | Metric family | What it needs | Fails when |
|----------|---------------|---------------|------------|
| Did the retriever find the passages that contain the answer? | Recall@k, Precision@k, MRR, NDCG@k, multi-hop recall | Relevance labels tying queries to passage ids | Chunking, embeddings, index, query formulation, or k are wrong |
| Did the model use those passages correctly? | Faithfulness, answer relevance | The generated answer plus the context it actually received | Prompt construction, context ordering, or model capability are wrong |

The diagnostic order that follows from this:

1. Compute Recall@k on the evaluation set. If the relevant passage is not in the retrieved set, stop. No prompt change will fix it.
2. If recall is acceptable but the answer is wrong, check that the retrieved passages actually reached the prompt. Truncation, context-window overflow, and re-ranking that drops the winner all break this silently between retrieval and generation.
3. Only once the passage is confirmed present in the final prompt does a low faithfulness score implicate generation.

A worked consequence: a system with Recall@5 of 0.42 and faithfulness of 0.91 is not a faithful system. It is a system that faithfully answers from the wrong passages 58 percent of the time. The faithfulness score is measuring grounding in the retrieved context, not correctness against the world.

## Dataset requirements

A retrieval evaluation set is a `dataset_manifest` plus per-query relevance labels. Minimum viable shape:

- **Queries**: real user phrasings, not paraphrases of the document titles. Retrieval evaluated on queries derived from the corpus is measuring lexical overlap, not user-facing quality.
- **Relevance labels**: for each query, the ids of passages that contain the information needed to answer it.
- **Corpus snapshot id**: passage ids are only meaningful against a fixed corpus version. Re-chunking changes ids, which invalidates every label. Record the snapshot and re-label or re-map when it changes.
- **Size**: 50 queries is a working minimum for directional comparisons; below about 30 the confidence intervals are wider than the effects being measured (see the interval example below). 200 or more supports slicing by query type.

### Relevance label conventions

- **Binary labels** (`relevant` / `not relevant`) are the default. They are cheap, have high inter-annotator agreement, and are all that Recall@k, Precision@k, and MRR require.
- **Graded labels** (for example 0 = irrelevant, 1 = partially relevant, 2 = fully answers) are only needed for NDCG. Adopt them when ranking order matters more than set membership.
- **Unjudged is not irrelevant.** If labels were built by pooling the top results of a previous retriever, a new retriever that surfaces a genuinely relevant passage nobody judged is scored as wrong. Either label completely on a small corpus, or record the pooling depth in the `dataset_manifest` and treat cross-retriever comparisons as approximate.
- **Multi-hop queries** carry one label group per required hop, not one flat set. See the multi-hop section.

## The metrics

Shared notation, used throughout:

- `k` is the retrieval cutoff being measured.
- `R` is the set of relevant passage ids for the query.
- `Retrieved_k` is the list of ids returned, in rank order, truncated to k.
- `rank_i` is the 1-based position of the i-th returned item.

### Recall@k

The fraction of the relevant passages that appear in the top k.

```
Recall@k = |R intersect Retrieved_k| / |R|
```

Range 0 to 1, higher is better. This is the primary retrieval metric because it answers the go/no-go question: is the answer even available to the generator?

Edge cases:

- `|R| = 0` (no relevant passage exists). The metric is undefined. Exclude the query from the recall average and report the excluded count separately. Do not score it 0, which understates the retriever, or 1, which overstates it.
- `k >= corpus size`. Recall trivially approaches 1. Recall@k is only meaningful when k is far smaller than the corpus.
- Comparing Recall@5 to Recall@20 across systems is meaningless. Fix k first.

### Precision@k

The fraction of returned passages that are relevant.

```
Precision@k = |R intersect Retrieved_k| / k
```

Range 0 to 1, higher is better. This measures the noise the generator has to read past. It matters because irrelevant context degrades answer quality and costs tokens, but it is secondary to recall: a precise retriever that misses the answer is useless.

Edge cases:

- Fewer than k results returned. Divide by k anyway, not by the number returned, or a retriever that returns one correct result scores a perfect 1.0 while starving the generator.
- Precision and recall trade off against k. Reporting one without the other, at a stated k, is not a result.

### MRR (Mean Reciprocal Rank)

How high the first relevant passage sits, averaged over queries.

```
RR(query)  = 1 / rank of the first relevant item, or 0 if none in top k
MRR        = mean of RR over all queries
```

Range 0 to 1, higher is better. Use it when the system consumes only the top result or two, or when a re-ranker's job is to lift one right answer to the top. It ignores every relevant item after the first, so it is the wrong metric when the generator needs to synthesize across several passages.

### NDCG@k (Normalized Discounted Cumulative Gain)

Rank-weighted gain, normalized against the best achievable ordering. The only metric here that uses graded relevance.

```
DCG@k  = sum over i=1..k of  gain_i / log2(i + 1)
IDCG@k = DCG@k of the ideal ranking (all relevant items sorted by gain, descending)
NDCG@k = DCG@k / IDCG@k
```

With binary labels, `gain_i` is 1 for relevant and 0 otherwise. With graded labels, use the grade, or `2^grade - 1` when strongly rewarding top grades. State which convention was used; the two are not comparable.

Range 0 to 1, higher is better. Use it when ordering within the retrieved set genuinely matters. Its cost is that it needs graded labels to earn its keep, and it is harder to explain to stakeholders than recall.

Edge case: `IDCG@k = 0` when the query has no relevant items. Exclude the query, as with recall.

### Multi-hop recall

A multi-hop query needs facts from two or more distinct passages before any answer is possible. Flat recall hides the failure mode: retrieving 3 of 4 required hops scores 0.75 while producing a system that cannot answer the query at all.

Model each query as a set of required hops `H = {H1, H2, ...}`, where each hop is itself a set of passage ids that would satisfy that hop.

```
hop_covered(Hj)   = 1 if Retrieved_k intersects Hj, else 0
hop_recall(query) = (sum over j of hop_covered(Hj)) / |H|
all_hops_rate     = fraction of queries where hop_recall == 1.0
```

Report both. `hop_recall` shows how close the retriever gets; `all_hops_rate` is the only one that predicts answerability, and it is always the lower number. A system with mean `hop_recall` of 0.80 on two-hop queries can easily have an `all_hops_rate` of 0.50.

### Choosing among them

| Situation | Primary metric | Why |
|-----------|----------------|-----|
| First measurement of a new pipeline | Recall@k | Establishes whether the answer is reachable at all |
| Generator reads all k passages | Recall@k with Precision@k | Coverage first, noise second |
| Only the top 1-2 passages are used | MRR | Position of the first hit is the whole game |
| Tuning a re-ranker | NDCG@k | The change being made is ordering, which is what NDCG measures |
| Graded relevance labels already exist | NDCG@k | Nothing else uses the grades |
| Queries need several passages combined | multi-hop `all_hops_rate` | The only metric that predicts answerability |
| Token cost is the binding constraint | Precision@k | Directly proportional to wasted context |

## Worked example

Corpus of 10 passages, `d1` through `d10`. One query.

- Relevant set `R` = {`d2`, `d5`, `d9`}, so `|R| = 3`.
- Retrieved top 5, in rank order: `d7`, `d2`, `d4`, `d9`, `d1`.
- Hits: `d2` at rank 2, `d9` at rank 4. `d5` was missed.

Computed at k = 5:

```
Recall@5    = 2 / 3            = 0.667
Precision@5 = 2 / 5            = 0.400
RR          = 1 / 2            = 0.500

DCG@5  = 1/log2(3) + 1/log2(5) = 0.6309 + 0.4307 = 1.0616
IDCG@5 = 1/log2(2) + 1/log2(3) + 1/log2(4)
       = 1.0000 + 0.6309 + 0.5000                = 2.1309
NDCG@5 = 1.0616 / 2.1309                         = 0.498
```

The same query at k = 3 (`d7`, `d2`, `d4`):

```
Recall@3    = 1 / 3 = 0.333
Precision@3 = 1 / 3 = 0.333
```

Read the pair: recall halves when k drops from 5 to 3, so this retriever's useful signal is spread across ranks 4 and 5, not concentrated at the top. That is a re-ranking problem, not an embedding problem, and NDCG@5 of 0.498 against a perfect-ordering ceiling of 1.0 says the same thing independently.

### Multi-hop worked example

Query: "Which product did the engineer who wrote the caching module later lead?" Two hops.

- `H1` (who wrote the caching module) = {`d2`, `d3`}
- `H2` (what that person later led) = {`d9`}
- Retrieved top 5: `d7`, `d2`, `d4`, `d9`, `d1`

```
hop_covered(H1) = 1   (d2 retrieved)
hop_covered(H2) = 1   (d9 retrieved)
hop_recall      = 2/2 = 1.0
```

This query is answerable. Had `d9` ranked 6th, `hop_recall` would be 0.5 and `all_hops_rate` would count this query as a failure, even though flat Recall@5 over the union {`d2`, `d3`, `d9`} would report a respectable 0.5. That gap is exactly why multi-hop queries need their own metric.

## Reporting

### Query level

Persist one `retrieval_result` per query per configuration, per the evaluation artifact contract: `query_id`, `k`, `retrieved_ids` in rank order, `relevant_ids`, the computed `metrics`, and the `retriever_config` under test. Query-level records are what make an aggregate reproducible and what let you find the queries a change broke.

### Aggregate

Report the mean of each metric across queries, the query count, the count excluded for having no relevant items, and the value of k. A metric without its k and its n is not interpretable.

Slice the aggregate whenever the set supports it: by query type, by expected hop count, by corpus section. A flat mean routinely hides a retriever that is excellent on single-hop lookups and broken on comparisons.

### Confidence intervals

Aggregate metrics on 50 queries are noisy. Report an interval, or do not claim an improvement.

For **rate-style metrics** (`all_hops_rate`, or any pass/fail proportion), use a Wilson score interval for `x` successes in `n` trials at `z = 1.96` (95 percent):

```
center     = (p + z^2/(2n)) / (1 + z^2/n)          where p = x/n
halfwidth  = z / (1 + z^2/n) * sqrt( p(1-p)/n + z^2/(4n^2) )
interval   = center +/- halfwidth
```

Worked: 14 successes in 20 queries.

```
p          = 0.700
center     = (0.700 + 3.8416/40) / 1.19208 = 0.796 / 1.19208 = 0.668
halfwidth  = 1.6442 * sqrt(0.0105 + 0.0024)        = 1.6442 * 0.11358 = 0.187
interval   = [0.481, 0.855]
```

A "70 percent" headline whose true value plausibly sits anywhere from 48 to 86 percent cannot distinguish two configurations that differ by 10 points. That is the argument for a larger evaluation set, stated as a number.

For **mean-style metrics** (mean Recall@k, mean NDCG@k), the Wilson interval does not apply because the per-query values are not Bernoulli trials. Use a bootstrap over queries (resample the query list with replacement 1000 times, recompute the mean, take the 2.5th and 97.5th percentiles) or a t-interval on the per-query values. Both need only the query-level records already being persisted.

When the sample is too small for a meaningful interval, label the number `preliminary (n = N)` rather than reporting a bare percentage.

## Grid search over chunking and retrieval

Retrieval quality is dominated by a handful of coupled variables. The only way to attribute a change is to move one at a time.

Variables, in the order worth exploring:

| Variable | Typical range | Changes what |
|----------|---------------|--------------|
| Chunk size | 256 - 1024 tokens | Whether a complete answer fits in one chunk |
| Chunk overlap | 0 - 25 percent of chunk size | Whether answers spanning a boundary survive |
| Chunking strategy | fixed, recursive, semantic, document-aware | Whether boundaries fall at meaningful places |
| Embedding model | project-dependent | The similarity function itself |
| Retrieval mode | dense, sparse, hybrid | Which query-document signals are used |
| k | 3 - 20 | The recall/precision/token tradeoff |
| Re-ranker | none, cross-encoder | Ordering within the retrieved set |

Procedure:

1. Freeze the evaluation set and the corpus snapshot. Both must be identical across every cell, or the comparison is meaningless.
2. Establish a baseline: run the current configuration, record `retrieval_result` records, compute aggregates with intervals.
3. Change exactly one variable. Re-run. Record a new `retriever_config` and a new set of `retrieval_result` records; never overwrite the baseline.
4. Compare against the baseline interval, not against the baseline point estimate. A 3-point gain inside overlapping intervals is not a gain.
5. Keep the change only if it improves the metric that matches your consumption pattern, not whichever metric happened to move.
6. Re-baseline and repeat.

Two traps this order avoids. Changing chunk size and k together produces a result nobody can attribute, and it is the most common wasted grid search. And re-chunking invalidates passage ids, so step 1's frozen snapshot is what keeps the relevance labels valid across cells; if re-chunking is the variable under test, re-map the labels to the new ids before running, and record the re-map in the `dataset_manifest` provenance.

## Local-first artifact handling

Everything this reference produces stays on the operator's machine by default.

- Queries, retrieved passages, and relevance labels are typically drawn from real production content and are treated as sensitive by default.
- Each `retrieval_result` carries `provenance` and `redaction_status`, with `state: raw` and `export_authorized: false` unless an explicit authorization step says otherwise.
- Before any evaluation artifact crosses a trust boundary (a shared report, an issue comment, a third-party service), reduce it to the minimum excerpt supporting the claim and apply the per-category policy in `[[egress-redaction]]`.
- Reporting an aggregate score externally does not require exporting the underlying passages. Ship the number and the recompute step, not the corpus.

Nothing here requires a hosted evaluation service, an additional package, or a provider credential. Every metric above is a few lines of arithmetic over records you already have.

## Verification

- [ ] Recall@k was computed and reported before any generation metric was interpreted
- [ ] Every reported metric states its k and its query count n
- [ ] Queries with no relevant passages were excluded and their count reported separately
- [ ] Relevance labels are tied to a recorded corpus snapshot id
- [ ] Multi-hop queries report `all_hops_rate`, not only mean `hop_recall`
- [ ] Each aggregate carries a confidence interval, or an explicit `preliminary (n = N)` label
- [ ] One `retrieval_result` record exists per query per configuration, with `retriever_config` recorded
- [ ] Each grid-search cell changed exactly one variable against a frozen corpus snapshot and evaluation set
- [ ] No raw query, passage, or label left the host without an explicit authorization step and a redaction pass
