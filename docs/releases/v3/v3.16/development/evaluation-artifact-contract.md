# Evaluation Artifact Contract (v3.16.1)

**Status**: locked for v3.16.1 Phase 1
**Date**: 2026-08-08
**Applies to**: `catalog/skills/ai-development/rag-implementation/`, `catalog/skills/developer-experience/ai-output-evaluation/`, `catalog/skills/ai-development/eval-pipeline-audit/` (Phase 2), `catalog/skills/workflow/skill-eval-loop/`, `catalog/skills/security/egress-redaction/`

This is the shared vocabulary every v3.16.1 evaluation phase writes against. It exists because the catalog already had five skills touching evaluation with five private vocabularies, so a trace produced under one skill could not be consumed by another without a translation step that nobody had written.

The contract fixes **artifact names, field names, and minimum required metadata**. It deliberately does NOT fix a storage engine, a file format, or a directory layout: a team may hold these as JSON, JSONL, CSV, Parquet, or rows in a local database, provided the named fields survive the choice.

## The problem being fixed

An audit of the current catalog (`ai-output-evaluation`, `rag-implementation`, `skill-eval-loop`, `prompt-engineering`, `egress-redaction`) found three concrete gaps:

1. **No shared artifact vocabulary.** `skill-eval-loop` owns a complete artifact chain (`evals.json`, per-run `grading.json`, aggregated `benchmark.json`, `feedback.json`) that is scoped to skill benchmarking and named for that workflow. `ai-output-evaluation` describes rubric scores and verdicts but names no persisted artifact at all beyond a JSON response shape. `rag-implementation` Step 7 emits an in-memory `RAGEvalResult` dataclass and prints a summary, so nothing is persisted for a later comparison. Three skills, three incompatible shapes, no defined handoff.
2. **Retrieval and generation quality share one bucket.** `rag-implementation` Step 7 lists Faithfulness, Answer Relevance, Context Recall, and Context Precision in a single table with no rule for which to read first. A weak answer therefore has no defined diagnostic path, and retrieval regressions get attributed to the generator.
3. **The local-data rule is stated per skill, not per artifact.** `egress-redaction` correctly defines egress events and a per-category policy, but the evaluation skills that actually produce traces, prompts, and labels do not declare which of their outputs are sensitive by default. The rule has an owner and no subjects.

## Core rules

These apply to every artifact defined below, without exception.

- **Local by default.** Raw prompts, traces, labels, source examples, and human annotations stay on the operator's machine. They are not sent to a third party, logged to an aggregator, or embedded in a report as a side effect of producing a score.
- **Minimize before any authorized export.** When an artifact genuinely must cross a trust boundary, it is first reduced to the smallest excerpt that supports the claim, then classified and acted on per `[[egress-redaction]]`. Export is an explicit, separately authorized step, never an implicit consequence of running an evaluation.
- **Every artifact carries provenance.** An artifact with no recorded origin cannot be reproduced or audited, so `provenance` is required, not optional.
- **Every artifact carries a redaction status.** A consumer must be able to tell whether it is holding raw or reduced content without inspecting the payload.
- **Identifiers are stable.** An `id` field, once assigned, is never reused for different content. Re-running a generation step produces new ids or an explicit new `run_id`, not silently mutated records.
- **Scores travel with their evidence.** A numeric result without the item-level records it aggregates from is a claim, not a measurement. This is the reproducible-receipt discipline `[[skill-eval-loop]]` and `[[ai-output-evaluation]]` already apply, promoted here to a contract-level requirement.

## Cross-cutting metadata blocks

Two blocks are embedded in every artifact rather than existing as standalone files.

### provenance

| Field | Required | Meaning |
|-------|----------|---------|
| `source` | yes | Where the content came from: `human`, `production_trace`, `synthetic`, `public_dataset`, or `derived` |
| `created_at` | yes | ISO 8601 timestamp of creation |
| `created_by` | yes | The producing agent, model identifier, tool, or human role |
| `derived_from` | when `source` is `derived` or `synthetic` | The id or ids of the upstream artifact this was produced from |
| `generator_config` | when `source` is `synthetic` | The parameters that produced the item, enough to regenerate it |

### redaction_status

| Field | Required | Meaning |
|-------|----------|---------|
| `state` | yes | `raw`, `minimized`, or `redacted` |
| `actions_applied` | when `state` is not `raw` | The `[[egress-redaction]]` actions applied, as a list of `BLOCK`, `REDACT`, `HASH` |
| `categories_detected` | when `state` is not `raw` | Sensitive-data categories found, using the `[[egress-redaction]]` taxonomy names |
| `export_authorized` | yes | Boolean. Defaults to `false`. Only an explicit human decision sets it `true` |

An artifact with `state: raw` and `export_authorized: false` is the default state for everything produced locally, and is the state in which almost all evaluation work lives and dies.

## Artifacts

### dataset_manifest

Describes an evaluation dataset as a whole. It is the entry point a later phase reads to know what a set of cases is for.

| Field | Required | Meaning |
|-------|----------|---------|
| `id` | yes | Stable dataset identifier |
| `purpose` | yes | What question this dataset answers |
| `case_count` | yes | Number of cases |
| `case_schema` | yes | The per-case field names present |
| `coverage_dimensions` | no | Named dimensions the cases span, when the set was built from a coverage model |
| `provenance` | yes | See above |
| `redaction_status` | yes | See above |

### split_manifest

Records how a dataset is divided, so a reader can prove a reported score was not measured on data used for tuning.

| Field | Required | Meaning |
|-------|----------|---------|
| `id` | yes | Stable split identifier |
| `dataset_id` | yes | The `dataset_manifest.id` being split |
| `splits` | yes | Named partitions, each with its case ids or a deterministic selection rule |
| `split_method` | yes | `random_seeded`, `stratified`, `temporal`, or `manual` |
| `seed` | when `split_method` is `random_seeded` | The seed, so the split reproduces exactly |
| `holdout_touched_count` | yes | How many times the held-out partition has been evaluated against. A rising count is the leakage signal |
| `provenance` | yes | See above |

### trace_sample

One captured execution of the system under evaluation. This is the unit error analysis works from.

| Field | Required | Meaning |
|-------|----------|---------|
| `id` | yes | Stable trace identifier |
| `input` | yes | The request that produced the trace |
| `output` | yes | What the system returned |
| `steps` | no | Intermediate steps, tool calls, or retrieved context, when captured |
| `sampled_from` | yes | The population sampled: `production`, `staging`, `evaluation_run`, or `synthetic` |
| `sampling_method` | yes | `random`, `stratified`, `failure_biased`, or `exhaustive`. Required because a failure-biased sample must never be reported as a base rate |
| `provenance` | yes | See above |
| `redaction_status` | yes | See above. Trace content is the highest-risk artifact in this contract |

### error_taxonomy

The category system trace failures are classified into. Owned per project, not global.

| Field | Required | Meaning |
|-------|----------|---------|
| `id` | yes | Stable taxonomy identifier |
| `version` | yes | Incremented whenever a category is added, removed, or redefined. Comparing counts across versions without noting this is a reporting error |
| `categories` | yes | Each with `name`, `definition`, `inclusion_criteria`, `exclusion_criteria`, and at least one `example_trace_id` |
| `multi_label` | yes | Boolean. Whether one trace may carry more than one category |
| `provenance` | yes | See above |

### retrieval_result

Retrieval quality for one query, recorded independently of whether an answer was ever generated. This is the artifact that makes the retrieval-versus-generation split operational.

| Field | Required | Meaning |
|-------|----------|---------|
| `id` | yes | Stable result identifier |
| `query_id` | yes | The evaluation case this measures |
| `k` | yes | The cutoff the metrics were computed at |
| `retrieved_ids` | yes | Retrieved document or chunk ids, in rank order |
| `relevant_ids` | yes | The ground-truth relevant ids for this query |
| `metrics` | yes | Named metric values. At minimum one of `recall_at_k`, `precision_at_k`, `mrr`, `ndcg_at_k`, `multi_hop_recall` |
| `retriever_config` | yes | The configuration under test, enough to distinguish one grid-search cell from another |
| `provenance` | yes | See above |

### evaluator_result

One evaluator's judgment of one item, whether the evaluator is a rubric, a model judge, or a deterministic check.

| Field | Required | Meaning |
|-------|----------|---------|
| `id` | yes | Stable result identifier |
| `item_id` | yes | The case, trace, or output being judged |
| `evaluator_id` | yes | Which evaluator produced this, including its version |
| `evaluator_kind` | yes | `rubric`, `model_judge`, `deterministic_check`, or `human` |
| `score` | yes | The value, with its scale declared by the evaluator |
| `evidence` | yes | At least one quote or pointer supporting the score. A score with no evidence does not satisfy this contract |
| `split` | yes | Which `split_manifest` partition the item came from |
| `provenance` | yes | See above |

### human_annotation

A human label on an item, kept distinct from `evaluator_result` because human labels are the ground truth an automated evaluator is validated against.

| Field | Required | Meaning |
|-------|----------|---------|
| `id` | yes | Stable annotation identifier |
| `item_id` | yes | The item labeled |
| `annotator_id` | yes | A pseudonymous stable reviewer identifier, never a real name |
| `label` | yes | The assigned label or score |
| `confidence` | yes | The reviewer's own confidence |
| `abstained` | yes | Boolean. An abstention is a signal about the rubric, not a missing value to be imputed |
| `blind` | yes | Boolean. Whether the reviewer could see the system output's origin or any competing label |
| `annotated_at` | yes | ISO 8601 timestamp |
| `provenance` | yes | See above |
| `redaction_status` | yes | See above |

### adjudication_record

The resolution of a disagreement between two or more labels on the same item.

| Field | Required | Meaning |
|-------|----------|---------|
| `id` | yes | Stable adjudication identifier |
| `item_id` | yes | The disputed item |
| `conflicting_annotation_ids` | yes | The annotations in conflict |
| `resolution` | yes | The final label |
| `resolution_method` | yes | `third_reviewer`, `discussion`, `rubric_clarification`, or `escalation` |
| `rationale` | yes | Why this resolution, in one or two sentences |
| `taxonomy_change_required` | yes | Boolean. A disagreement traced to an ambiguous category is a taxonomy defect, and must be recorded as one |
| `provenance` | yes | See above |

### regression_case

A confirmed failure promoted into a permanent check, so a fixed defect cannot silently return.

| Field | Required | Meaning |
|-------|----------|---------|
| `id` | yes | Stable case identifier |
| `origin_trace_id` | yes | The trace this was derived from |
| `error_category` | yes | The `error_taxonomy` category it exemplifies |
| `input` | yes | The minimized reproducing input |
| `expected_behavior` | yes | The observable condition that must hold |
| `assertion` | yes | The binary check that determines pass or fail |
| `status` | yes | `open`, `fixed`, or `accepted_limitation` |
| `provenance` | yes | See above |
| `redaction_status` | yes | See above. A regression case derived from a production trace is minimized before it enters a committed test suite |

## Ownership map

Each artifact has exactly one owning skill. Ownership means that skill defines the artifact's method in depth; other skills consume it.

| Artifact | Owning skill | Introduced by |
|----------|--------------|---------------|
| `dataset_manifest` | `[[ai-output-evaluation]]` | Phase 1 contract, detailed in Phase 4 |
| `split_manifest` | `[[ai-output-evaluation]]` | Phase 1 contract, detailed in Phase 3 |
| `trace_sample` | `[[ai-output-evaluation]]` | Phase 1 contract, detailed in Phase 3 |
| `error_taxonomy` | `[[ai-output-evaluation]]` | Phase 1 contract, detailed in Phase 3 |
| `retrieval_result` | `[[rag-implementation]]` | Phase 1 |
| `evaluator_result` | `[[ai-output-evaluation]]` | Phase 1 contract, detailed in Phase 3 |
| `human_annotation` | `[[ai-output-evaluation]]` | Phase 1 contract, detailed in Phase 4 |
| `adjudication_record` | `[[ai-output-evaluation]]` | Phase 1 contract, detailed in Phase 4 |
| `regression_case` | `[[ai-output-evaluation]]` | Phase 1 contract, detailed in Phase 3 |
| `provenance` | this contract | Phase 1 |
| `redaction_status` | `[[egress-redaction]]` | Phase 1 |

Two skills consume the whole set without owning any of it:

- `[[eval-pipeline-audit]]` (created in Phase 2) inventories which of these artifacts a project actually has, and reports the missing ones as gaps. It is a router, so it defines no artifact of its own.
- `[[skill-eval-loop]]` keeps its existing workspace artifacts (`evals.json`, `grading.json`, `benchmark.json`, `feedback.json`) unchanged. Those are a concrete instantiation of this contract scoped to skill benchmarking: `evals.json` cases are a `dataset_manifest`, `grading.json` entries are `evaluator_result` records, and the optimizer's 60/40 train/test division is a `split_manifest`. No rename is required or planned.

## Phase map

| Phase | Consumes | Produces |
|-------|----------|----------|
| 1 | audit of existing skills | this contract, `retrieval_result` definition |
| 2 | full contract | audit gap matrix over the artifact set |
| 3 | `trace_sample`, `split_manifest`, `evaluator_result`, `human_annotation` | `error_taxonomy` and `regression_case` methods, evaluator calibration method |
| 4 | `dataset_manifest`, `human_annotation`, `adjudication_record` | synthetic-data and human-review methods |

## Verification

- [ ] Every artifact a v3.16.1 phase introduces is named in the ownership map above
- [ ] Every artifact instance carries `provenance` with a `source` and `created_at`
- [ ] Every artifact instance carries `redaction_status`, defaulting to `state: raw` and `export_authorized: false`
- [ ] No score is reported without the item-level records it aggregates from
- [ ] No held-out partition was evaluated against more than the count recorded in its `split_manifest`
- [ ] No raw trace, prompt, label, or annotation left the host without an explicit authorization step and an `[[egress-redaction]]` pass

## Related Skills

- `[[rag-implementation]]` - owns `retrieval_result` and the retrieval-first diagnostic order
- `[[ai-output-evaluation]]` - owns the trace, taxonomy, evaluator, annotation, adjudication, and regression artifacts
- `[[skill-eval-loop]]` - a concrete instantiation of this contract scoped to skill benchmarking
- `[[egress-redaction]]` - owns `redaction_status` and the per-egress-event policy this contract defers to
- `[[prompt-engineering]]` - consumes `dataset_manifest` and `evaluator_result` when scoring prompt versions
