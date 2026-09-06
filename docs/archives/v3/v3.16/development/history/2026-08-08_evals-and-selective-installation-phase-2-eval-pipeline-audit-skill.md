# Session History - v3.16.1 Phase 2: Evaluation pipeline audit skill

**Date**: 2026-08-08
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.1-evals-and-selective-installation.md](../../plans/v3.16.1-evals-and-selective-installation.md)
**Phase**: 2 of 8 (not the final phase; no release-readiness workflow ran)
**Branch**: `feat/v3.16.1-evals-and-selective-installation`
**Outcome**: Complete. Quality gates passed; two pre-existing catalog defects found and recorded.

## Goal

Create one thin local-first entry point that audits an evaluation pipeline and routes specialized work to the skills that own each method, then register it into the full catalog and both AI selections.

## Sub-tasks completed

### 2.1 - The coordinating skill (T007, T008)

Created `catalog/skills/ai-development/eval-pipeline-audit/SKILL.md` (151 lines, inside the 500-line Tier-2 target). It owns exactly one method - a fixed ten-concern inventory (objectives, datasets, split provenance, evaluators, thresholds, traces, human labels, regression cases, feedback loops, deployment gates), each mapped to an artifact from the Phase 1 contract - then a severity-ranked gap matrix, then a routing table. Every specialist method is delegated.

Local-data safeguards are stated as four rules: local by default, bounded excerpts only, identifiers redacted in the report, explicit authorization before any egress via `[[egress-redaction]]`.

### 2.2 - Routing evals and platform descriptor (T009, T010)

Added `evals/trigger-cases.json` with 4 lexical positives and 5 near-miss negatives. Every negative is drawn from the skill's own SKIP clause and names the skill it should route to instead, which a test enforces - a negative that only says "not here" cannot be acted on.

Added `agents/openai.yaml`, and repaired the three truncated descriptors in the same category (see Decisions).

### 2.3 - Registration (T011, T012)

`data/bundles.json`: added to the `ai-engineering` module (5 -> 6 skills) and the `ai-engineer` role bundle (12 -> 13). `data/SKILL_INDEX.md`: one row plus the total 270 -> 271. `data/skills.json`: one entry inserted after its `model-prompting-research` sibling, plus a recomputed `statistics` block. `data/marketplace.json`: ai-development 12 -> 13.

### 2.4 - Tests and stabilization (T013)

Added `tests/skills/test_eval_pipeline_audit.py`, 59 assertions.

## Decisions made

- **Registered by hand rather than by `make build-catalog`, on measured evidence.** The plan's T012 says to run the builder. `make` is unavailable here, and the repository's standing rule says the builder rewrites the whole tree. That was measured rather than assumed: an accidental invocation produced a 6695-line `skills.json` diff and 174 lines of `SKILL_INDEX.md`, which was reverted. The hand-edit is 56 lines. Recorded as DF-2 and confirmed by the user.
- **The non-duplication boundary is enforced by test, not by intent.** `test_does_not_duplicate_specialist_formulas` fails if `Recall@k =`, an NDCG formula, a Wilson interval, or confusion-matrix arithmetic appears in the body. A coordinating skill degrades by helpfully inlining a method it should route, and that is a change a reviewer waves through. Naming a metric while routing passes; defining it fails.
- **The inventory order is asserted, not just the inventory.** `test_inventory_concerns_appear_in_the_documented_order` requires all ten in sequence. Objectives and datasets come before evaluators and thresholds so a threshold is judged against a stated objective rather than the reverse.
- **Severity is defined by consequence and tested for it.** A test reads the text following `BLOCKING` and requires it to describe a pipeline reporting a passing score while the system is broken. Severity assigned by distance-from-best-practice reorders the work wrongly, and teams then fix the easy MEDIUM items while a BLOCKING gap keeps shipping regressions.
- **Recomputed `skills.json` statistics rather than incrementing them.** Once the block had to be touched, recomputation is the only method producing a value that matches the field's contract. Recorded as DF-3 with the drift measurements.
- **Fixed three truncated agent descriptors, not all 121.** The user approved fixing "the three siblings" when the defect was believed to be three files; measurement then showed 121 of 139 catalog-wide. Fixed the three in scope, recorded the remaining 118 as NI-2 rather than silently expanding the phase or silently dropping the finding.

## Troubleshooting trail

- **A probing mistake ran a mutating script.** `build_skills_catalog.py --help` is not supported, so the probe executed a full rebuild and modified two tracked files. Caught immediately with `git status`, reverted with `git checkout --`, and the tree verified clean before continuing. The accident produced the measurement that justifies DF-2, but the correct approach was to read the script first.
- **The first `skills.json` entry was corrupted, and the tests caught it.** A frontmatter parser used the lookahead `(?=\n[a-z_]+: )`, which never matches `summary_l0` or `overview_l1` because those keys contain digits. The `description` field therefore ran on and swallowed all three fields - 2011 characters instead of 906. `test_description_declares_triggers_and_a_skip_boundary` failed on the identical bug in the test's own copy of the regex, which is what surfaced it. Both were fixed to `[a-z_0-9]+` and the entry rewritten.
- **Three registry-consistency tests failed on a derived block the hand-edit missed.** `statistics.total_skills` and `statistics.categories` are maintained by the builder and asserted by `tests/validators/test_registry_consistency.py`. This is the concrete cost of the DF-2 trade-off, and it is why that decision is recorded rather than assumed safe.
- **Two pre-existing catalog defects surfaced from tests written for something else.** The bundle-resolution test, written to verify the two AI selections, swept every bundle and found four references to skills that do not exist (NI-1). The descriptor test found the 121-file truncation (NI-2). Neither is caused by this phase.
- **NI-1 was then fixed at the user's direction, and the third case needed research rather than a guess.** `add-strategic-comments` and `cleanup-javascript` are past renames with obvious targets. `release-management` is not: it never existed as a skill at any point in git history, so there was nothing to reverse. It entered `bundles.json` via `927e5af5` as a forward reference that was never created. Every naive repair fails on inspection, because `devops-engineer` already lists `release-notes-writer` and `rollback-strategy-advisor` and `tech-lead` already lists `version-upgrade`. It maps to `shipping-and-launch`, the skill that actually provides release execution and was absent from both bundles. The test allowlist was deleted rather than shrunk, so the check now runs with no exceptions.

## Verification

- `python -m pytest -q tests/skills/test_eval_pipeline_audit.py` - 59 passed
- `python -m pytest -q tests/skills/test_eval_pipeline_audit.py tests/skills/test_evaluation_methodology.py` - 133 passed
- `python -m pytest -q tests/validators/test_registry_consistency.py` - 9 passed (after the DF-3 fix)
- `python scripts/run_trigger_evals.py --gate` - PASS, 271 skills, 0 un-allowlisted collisions, 0 routing failures across 10 skills with cases (72 lexical cases)
- `python scripts/validate_skills.py --bundles-only` - PASS, 0 errors, 0 warnings across 271 skills
- `python scripts/validate_skills.py --quality` - PASS, 0 errors, 6 pre-existing warnings, none on the new skill
- `python scripts/scan_skill_security.py catalog/skills/ai-development/eval-pipeline-audit --fail-on high` - 3 files scanned, 0 findings
- All five `data/*.json` files parse; catalog counts agree at 271 across `skills.json`, `SKILL_INDEX.md` rows, the `SKILL_INDEX` total line, and the marketplace category sum
- Ten remaining `validate` guards - all PASS
- `git diff --check` - clean

## Files changed

| File | Change |
|---|---|
| `catalog/skills/ai-development/eval-pipeline-audit/SKILL.md` | new |
| `catalog/skills/ai-development/eval-pipeline-audit/evals/trigger-cases.json` | new |
| `catalog/skills/ai-development/eval-pipeline-audit/agents/openai.yaml` | new |
| `tests/skills/test_eval_pipeline_audit.py` | new |
| `catalog/skills/ai-development/{ai-agent-development,prompt-engineering,rag-implementation}/agents/openai.yaml` | truncated descriptions repaired (NI-2, partial) |
| `data/bundles.json` | ai-engineering module + ai-engineer bundle |
| `data/skills.json` | one entry; statistics recomputed |
| `data/SKILL_INDEX.md` | one row; total 270 -> 271 |
| `data/marketplace.json` | ai-development 12 -> 13 |
| `docs/v3/v3.16/known-gaps.md` | NI-1, NI-2 open; DF-2, DF-3 closed |
| `docs/DEVLOG.md`, `docs/todos.md` | Phase 2 entry and tracker |

## Next steps

Phase 3 adds `references/error-analysis.md` and `references/evaluator-validation.md` under `ai-output-evaluation` and links them from that skill. Both are already named as owners in the Phase 1 contract and in this skill's routing table, so Phase 3 fills in targets that already have inbound references. NI-1 needs a decision before Phase 6 makes selection operational.
