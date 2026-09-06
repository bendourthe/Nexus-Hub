# Session History - v3.16.1 Phase 1: Evaluation contract and RAG metrics

**Date**: 2026-08-08
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.1-evals-and-selective-installation.md](../../plans/v3.16.1-evals-and-selective-installation.md)
**Phase**: 1 of 8 (not the final phase; no release-readiness workflow ran)
**Branch**: `feat/v3.16.1-evals-and-selective-installation`, cut from `develop` at `90cdabd6`
**Outcome**: Complete. Quality gates passed; two gaps recorded for later phases.

## Goal

Give every later v3.16.1 evaluation phase one shared artifact vocabulary, and make RAG retrieval quality measurable independently of answer generation, before any coordinating skill is written.

## Sub-tasks completed

### 1.1 - Evaluation artifact contract (T001, T002)

Audited `ai-output-evaluation`, `rag-implementation`, `skill-eval-loop`, `prompt-engineering`, and `egress-redaction` for current terminology and artifact ownership. The audit found three concrete gaps, all recorded in the contract's opening section rather than asserted abstractly:

- **No shared vocabulary.** `skill-eval-loop` owns a complete artifact chain (`evals.json`, `grading.json`, `benchmark.json`, `feedback.json`) named for skill benchmarking. `ai-output-evaluation` names no persisted artifact at all beyond a JSON response shape. `rag-implementation` Step 7 emits an in-memory `RAGEvalResult` dataclass and prints a summary, persisting nothing.
- **Retrieval and generation share one bucket.** `rag-implementation` Step 7 listed Faithfulness, Answer Relevance, Context Recall, and Context Precision in one flat table with no rule for reading order.
- **The local-data rule had an owner and no subjects.** `egress-redaction` defines egress events correctly, but the skills that actually produce traces and labels never declared which of their outputs are sensitive.

Created `docs/v3/v3.16/development/evaluation-artifact-contract.md` defining nine standalone artifacts (`dataset_manifest`, `split_manifest`, `trace_sample`, `error_taxonomy`, `retrieval_result`, `evaluator_result`, `human_annotation`, `adjudication_record`, `regression_case`) plus two cross-cutting metadata blocks, an ownership map, and a phase map.

### 1.2 - RAG retrieval evaluation reference (T003)

Created `catalog/skills/ai-development/rag-implementation/references/evaluation.md` as a cold-readable Tier-3 reference: formulas and edge cases for Recall@k, Precision@k, MRR, NDCG@k, and multi-hop recall; dataset and relevance-label conventions; a fully computed worked example; a multi-hop worked example; query-level and aggregate reporting; Wilson intervals for rates and bootstrap for means; and a one-variable-at-a-time chunking and retrieval grid-search procedure.

### 1.3 - Parent-skill integration (T004)

Updated `rag-implementation/SKILL.md`: pushier `description` with the new trigger phrases and an explicit SKIP boundary pointing general output scoring at `ai-output-evaluation`; a `When NOT to use` block; the retrieval-before-generation ordering rule and a family column in the Step 7 metric table; the reference linked by basename; two new Common Rationalizations; two new Verification items; and two new Related Skills. No existing content was removed.

### 1.4 - Contract tests (T005)

Added `tests/skills/test_evaluation_methodology.py`, 74 focused semantic assertions, no whole-file snapshots.

### 1.5 - Validation and stabilization (T006)

See Verification below.

## Decisions made

- **`provenance` and `redaction_status` are embedded blocks, not peer artifacts.** Modeling them as standalone files would let a trace sample exist without provenance, which is the exact failure the contract is meant to prevent. Making them required blocks means an artifact cannot be well-formed without them.
- **The contract fixes field names, not a storage engine.** A team may hold these as JSON, JSONL, CSV, Parquet, or database rows. Prescribing a format would have forced Phases 3, 4, and 7 to either comply or fork, for no gain in interoperability.
- **`skill-eval-loop` keeps its existing artifact names.** Renaming `benchmark.json` to fit a new vocabulary would break a working skill to satisfy a document. The contract instead states the mapping explicitly: `evals.json` cases are a `dataset_manifest`, `grading.json` entries are `evaluator_result` records, and the optimizer's 60/40 division is a `split_manifest`. Interoperability came from naming the correspondence, not from a rename.
- **Every test predicate is paired with a mutation test.** Each `test_*_has_teeth` case deletes the target content from an in-memory copy and asserts the predicate then fails. Without them, a predicate that accidentally matched anything would pass forever and guard nothing. The retrieval-first mutation is the sharpest: it leaves both words "retrieval" and "generation" in place and removes only the ordering statement, so a check that merely detected co-occurrence would be caught.
- **The plan header was corrected rather than the file renamed.** The plan declared a filename that does not exist on disk, and two other surfaces repeated it. The user chose to fix the header; the two stale references were repaired in the same pass. Recorded as DF-1 (closed).
- **CI was deliberately not changed.** The new test guards a document under `docs/`, which the workflow's `paths` filter excludes. That is a real gap, but this plan's Lifecycle Contract reserves pipeline edits for Phase 8 unless a phase's explicit deliverable requires them. Recorded as QG-1 with the exact fix.

## Troubleshooting trail

- **`make` is unavailable on this host.** The `make validate` target was replicated by invoking its fourteen underlying commands directly. All passed. Recorded under WN-1 together with the missing `ruff` and `shellcheck`.
- **The description edit was a trigger-collision risk.** Making `rag-implementation`'s `description` pushier adds vocabulary that could collide with a neighboring skill's routing. `run_trigger_evals.py --gate` was run specifically to check this: 0 un-allowlisted collisions across 270 skills, 0 routing failures. The explicit SKIP clause pointing at `ai-output-evaluation` is what keeps the widened surface from over-triggering.

## Verification

- `python -m pytest -q tests/skills/test_evaluation_methodology.py` - 74 passed
- `python -m pytest -q tests/skills tests/validators` - 879 passed, 3 skipped (regression check on the two suites the changed surfaces sit in)
- `python -m pytest -q tests/` - 1 failed, 1818 passed, 20 skipped in 22m09s. The single failure is `tests/installer/test_bootstrap.py::test_ps_standalone_extracts_and_hands_off`, the inherited MSYS `tar` environmental failure recorded as BG-1. This phase touched no installer, shell, or PowerShell file.
- `python scripts/validate_skills.py --bundles-only` - PASS, 0 errors, 0 warnings across 270 skills (the new `references/evaluation.md` is correctly seen as referenced, not an orphan)
- `python scripts/validate_skills.py --quality` - PASS, 0 errors, 6 pre-existing warnings, none on `rag-implementation`
- `python scripts/run_trigger_evals.py --gate` - PASS, 0 un-allowlisted collisions, 0 routing failures
- `python scripts/validate_unicode_safety.py` - 0 errors; no findings in either new document
- `check_version_sync`, `check_base_template_parity`, `verify_platform_contracts`, `check_platform_contract_freshness`, `sync_platform_defaults --check`, `scan_supply_chain_iocs`, `validate_workflow_security`, `validate_no_personal_paths`, `validate_solution_frontmatter` - all PASS
- `git diff --check` - clean

## Files changed

| File | Change |
|---|---|
| `docs/v3/v3.16/development/evaluation-artifact-contract.md` | new |
| `catalog/skills/ai-development/rag-implementation/references/evaluation.md` | new |
| `tests/skills/test_evaluation_methodology.py` | new |
| `catalog/skills/ai-development/rag-implementation/SKILL.md` | description, triggers, Step 7, rationalizations, verification, related skills |
| `docs/v3/v3.16/known-gaps.md` | v3.16.1 section appended (QG-1, WN-1 open; DF-1 closed) |
| `docs/v3/v3.16/plans/v3.16.1-evals-and-selective-installation.md` | header Slug/Filename and Phase 1.1 prompt path corrected |
| `docs/v3/v3.16/comparisons/v3.16.1-comparison-evals-and-selective-installation.md` | stale plan path repaired |
| `docs/todos.md` | stale plan path repaired |
| `docs/DEVLOG.md` | Phase 1 entry |

## Next steps

Phase 2 creates `catalog/skills/ai-development/eval-pipeline-audit/` as a thin coordinating skill, with trigger evals, an OpenAI agent descriptor, and registration into the `ai-engineering` module and `ai-engineer` role bundle. It consumes this contract's full artifact set and produces a gap matrix over it; it owns no artifact of its own, which is what keeps it thin.
