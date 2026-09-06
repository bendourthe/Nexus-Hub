# Session History -- v3.0.0 Phase 3: Core lifecycle commands I (describe, plan, implement, test)

**Date**: 2026-06-03
**Plan**: [`docs/releases/v3/v3.0/plans/command-consolidation-skill-security.md`](../../plans/command-consolidation-skill-security.md)
**Phase**: 3 of 10 -- core lifecycle commands I
**Outcome**: complete; all five sub-tasks (T010-T014) closed, all applicable quality gates green.

## Goal

Ship the first four verb-first lifecycle commands (`/describe`, `/plan`, `/implement`, `/test`) as thin dispatchers over the retained skills, following the Phase 1 scope-mechanism contract. No existing behavior is removed: the rich skill bodies are retained as scope modules, and the eight old command files continue to function unchanged (deprecation shims land in plan-Phase 8). Pure catalog content -- no new code, dependency, credential, or outbound call.

## Subtasks completed

1. **T010 -- /describe.** Created `catalog/commands/describe.md` (58 lines), a thin dispatcher over the `analyze-codebase` skill generalized to describe ANY directory (software or not). Scopes `full` (recommended) / `structure` / `deps` / `architecture` / `onboarding`. A software-vs-non-software detection step routes the skill to adapt its sections (or skip inapplicable ones) and states the detected mode first; a directory-path argument is accepted as the target, defaulting to `full`.
2. **T011 -- /plan.** Created `catalog/commands/plan.md` (62 lines), merging three lineages over `generate-plan` + `implementation-plan` + `product-strategy` + `generate-todos` + `tasks-to-issues` + `agent-orchestration-primitives`. Preserves the full generate-plan behavior (discovery interview, from-comparison RE-first ordering, known-gaps ingest, KB/strategy grounding, Constitution Check + Complexity Tracking, strict T### file format); adds goals framing (a `goals` scope + a goals-first step at the top of every planning scope, and an inline `/plan goals <one-liner>`); and a REQUIRED dynamic-workflows graceful-degradation block (multi-angle drafting / parallel research / workflow-aware phase prompts, all opt-in with the scope-first token caution and single-agent fallback). Scopes: `goals`, `new`, `feature` (recommended), `refactor`, `from-comparison`, `todos`, `issues`.
3. **T012 -- /implement.** Created `catalog/commands/implement.md` (47 lines), the `implement-phase` rename. Argument-driven (`<slug>`, `<slug> phase-N`, `<slug> "Name"`, `<slug> next`, bare `vX.Y.Z`, or bare = discover + ask). The v3.0.0 change: the final-phase auto release-readiness workflow routes its docs / update / version-bump / changelog / tag / push work to the new `/update release` (Phase 4) instead of the old inline `update-*` sequence; resolve-known-gaps and verify-tests/CI stay in-skill; no tag created or pushed automatically.
4. **T013 -- /test.** Created `catalog/commands/test.md` (69 lines), merging `generate-unit-tests` + `generate-tests` + `tdd` behind one per-tier iterative coverage loop (analyze -> generate -> run -> check coverage >= threshold AND 100% pass-rate -> repeat or advance). Scopes `all` (recommended; unit -> integration -> e2e -> ci) / `unit` / `integration` / `e2e` / `ci` / `tdd`. Thresholds standardized (80% line, 100% generated-test pass-rate) and overridable via args; stricter project/CI config wins. Opt-in dynamic-workflow fan-out for very large surfaces, cross-linking `[[agent-orchestration-primitives]]`.
5. **T014 -- Stabilization.** Verified the dispatcher constraints mechanically and emulated `make validate` (all green); reviewed scope resolution against the authoring checklist for each command.

## Key decisions

- **Thin command, fat skill, faithfully.** Every command file resolves scope and delegates only; no analysis, planning, or test-generation logic was duplicated into the command bodies. The one place genuinely-new orchestration was added is `/test`'s per-tier loop and gate -- the command owns the loop, the retained skills own generation -- which keeps the file at 69 lines.
- **`full`/`all` semantics per command.** `/describe full` runs every section then synthesizes; `/test all` runs the tier sequence unit -> integration -> e2e -> ci. `/plan` and `/implement` have no `full` scope by nature (their scopes are distinct modes / a positional plan target, not composable lenses), which is consistent with the contract.
- **Forward-references written as documented intent.** `/implement` and `/plan` reference `/update release` (Phase 4) and the deprecation shims (plan-Phase 8). These do not yet exist; they are written as the plan's intended end-state, and the old commands remain fully functional in the interim. This is expected sequencing, not a gap.
- **Count reconciliation deferred.** `marketplace.json` `total_commands`, the AGENTS.md/README count prose, and the 5 platform templates are NOT updated this phase -- that is plan-Phase 8 (T038), and updating now would be premature while only 4 of 14 commands exist and the originals are still active.

## Test results

- All four files under the 150-line dispatcher cap: describe 58, plan 62, implement 47, test 69. ASCII-only: 0 non-ASCII characters across all four (verified directly).
- Emulated `make validate` (each validator invoked directly, `make` unavailable on host per WN-v30-1): JSON catalogs OK (247 skills, bundles/workflows/templates OK); orphan-bundle audit **PASS 0/0**; quality heuristics **PASS 0 errors / 0 warnings**; no-personal-paths, unicode-safety (pre-existing legacy WARNs only, 0 errors), supply-chain IOCs, workflow-security, solution-frontmatter all clean; `check_version_sync.py` green at 2.4.0 across all six surfaces. **Aggregate: ALL GREEN.**
- None of the four new files appear in the unicode-safety WARN list (the WARNs are pre-existing em-dash/ellipsis debt in `generate-plan.md`, `run-penetration-test.md`, `AGENTS.md`, and legacy templates).
- All delegate skills confirmed present: `analyze-codebase`, `generate-plan`, `implementation-plan`, `product-strategy`, `generate-todos`, `tasks-to-issues`, `agent-orchestration-primitives` (Phase 2), `generate-tests`, `generate-unit-tests`, `tdd`. The `[[agent-orchestration-primitives]]` cross-link resolves.
- Scope-resolution review (per command): bare -> numbered menu with one recommended default; recognized scope token -> skip menu; path/slug -> routed; `full`/`all` -> documented order; every scope token -> explicit one-to-one delegation target. All pass.

## CI/CD edits

- None. GitHub Actions (`ci.yml`) is the active CI; its `validate` job runs the same validators emulated locally. Phase 3 added no new script command, environment variable, or dependency, and the four new command files auto-distribute via the recursive folder copy (no installer edit). 0 workflows touched, 0 proposed edits.

## Deviations

- None. The plan's T010-T013 prompts were followed as written.

## Troubleshooting / environment notes

- `make` and `shellcheck` are unavailable on the Windows dev host (consistent with WN-v30-1), so `make validate` was emulated by invoking each validator directly. No shell scripts were touched this phase, so the ShellCheck pass is not applicable to the diff.
- The unicode-safety WARNs are pre-existing punctuation debt in other files; the four new command files were verified ASCII-only and are not in scope to clean adjacent files.

## Known gaps

See [`docs/releases/v3/v3.0/known-gaps.md`](../../known-gaps.md). No new open items this phase. WN-v30-1 (Phase 1, ShellCheck deferred to CI) and WN-v30-2 (Phase 2, build_skills_catalog.py drift) remain open and unchanged; the summary stays at 2 open WN.

## Next steps

- **Phase 4 -- Review + Update commands**: create `/review` (merges review-codebase, review-changes, run-deep-review, run-security-audit, run-penetration-test, generate-sbom, skill-scan) and `/update` (merges the update-* / refactor-* / changelog / devlog / readme / commit-msg / config families, plus the `release` scope that `/implement` hands off to). `/update version` must use `scripts/check_version_sync.py`.
