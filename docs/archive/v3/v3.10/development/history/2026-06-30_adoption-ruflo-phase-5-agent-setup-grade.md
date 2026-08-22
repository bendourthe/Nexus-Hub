# Session History - v3.10.0 adoption-ruflo Phase 5: agent-setup grade + regression diff

**Date**: 2026-06-30
**Plan**: [`../../plans/adoption-ruflo.md`](../../plans/adoption-ruflo.md) Phase 5 (A3: agent-setup grade + cross-snapshot regression diff; re-partial, P2)
**Branch**: `develop`
**Outcome**: Complete. All Phase 5 exit-checklist items satisfied; quality gate GO. Phase 5 of 6; not the final phase, so no release-readiness run.

## Goal

Extend `scripts/harness_audit.py` with a single explainable 1-100 agent-setup grade and a cross-snapshot regression diff (did the setup get worse since the last snapshot), surfaced through the `skill-stocktake` skill. Re-partial reverse-engineer build over an owned artifact: strictly local and read-only (the only write is a local snapshot), zero new outbound call, dependency, or credential. The named failure modes are a misweighted rubric and an advisory grade that silently becomes a hidden gate, so the rubric must be defensible and explainable and the grade must stay advisory.

## What shipped

- **`scripts/harness_audit.py`** (extended): added a 1-100 agent-setup grade and snapshot/diff alongside the existing per-integration `audit`. New CLI actions `grade` / `snapshot` / `diff` (positional, default `audit`) plus `--snapshot` / `--diff` flag aliases, `--fail-on-regression`, and `--snapshot-dir`. New dataclasses (`GradeDimension`, `SetupGrade`, `DimensionDelta`, `GradeDiff`), six per-dimension scorers, the `grade()` orchestrator, `write_snapshot()` / `diff_against_snapshot()`, and Markdown/JSON formatters for the grade and the diff. The pre-existing `audit` behavior is unchanged and backward-compatible (the new positional defaults to `audit`).
- **`catalog/skills/workflow/skill-stocktake/SKILL.md`** (edited, body 133 -> 144 lines): new "Agent-setup grade (companion signal)" section documenting the `grade` / `snapshot` / `diff` actions and stating they are advisory by default; two new Related-Skills cross-links (`[[skill-security-scan]]`, `[[skill-eval-loop]]`). No frontmatter change.
- **`tests/integrations/test_harness_audit.py`** (extended): 17 new Phase 5 cases (25 total in the file).
- **`docs/v3/v3.10/known-gaps.md`** (edited): status advanced to Phase 5 complete, Phase 6 pending. No new gaps (Phase 5 built everything; nothing deferred).
- **`docs/v3/v3.10/plans/adoption-ruflo.md`** (edited): Phase 5 exit checklist checked off.
- **`docs/DEVLOG.md`** (edited): Phase 5 entry.

## The rubric (5.1)

The grade is a weighted average over six observable, locally-measurable, deterministic dimensions. Weights live in a single tunable `GRADE_WEIGHTS` constant (mirroring the file's existing `DEFAULT_WEIGHTS` user-contribution slot), summing to 1.0:

| Dimension | Weight | Sub-score derivation |
|---|---:|---|
| `registry_consistency` | 0.25 | Fraction of registries (skills.json `total_skills`, skills.json `skills[]` length, SKILL_INDEX.md rows, marketplace.json category sum) whose count matches the on-disk `catalog/skills/*/*/SKILL.md` count. |
| `skill_frontmatter` | 0.20 | Fraction of SKILL.md files whose frontmatter carries all four Tier-1 fields (`name`, `description`, `summary_l0`, `overview_l1`). |
| `security_hooks` | 0.20 | secret-scan / large-file-guard / git-guardrails: full credit present-and-registered, half present-but-unregistered, zero absent. |
| `instruction_files` | 0.15 | Fraction of the two repo-root surfaces (AGENTS.md, CLAUDE.md) plus the five `base-*.md` templates present. |
| `hook_registration` | 0.10 | Fraction of hook commands referenced in settings.json that resolve to a file on disk (catches orphan references). |
| `data_integrity` | 0.10 | Fraction of the core data registries (skills.json, marketplace.json, bundles.json) that parse as valid JSON. |

Each dimension carries an `applicable` flag; when its inputs are structurally absent (a thin install with no `catalog/skills` source tree), it is excluded and the weights renormalize over the measurable dimensions, so a thin install is not penalized for signals it cannot have. The grade is clamped to [1, 100]. The repo grades 100/100 (all six applicable, all at 1.00).

## Key decisions / troubleshooting

- **Advisory by contract (the named failure mode).** `grade`, `snapshot`, and `diff` all exit 0 regardless of score. The single opt-in gate is `diff --fail-on-regression`, which exits 1 only when the overall grade dropped against the snapshot (and exits 0 on a first run with no baseline). This keeps the grade a health signal, never a hidden install/commit gate.
- **Determinism = a root-independent snapshot payload.** Phase 5.4 requires two `--snapshot` runs over an unchanged setup to produce equivalent snapshots. Two things would break that: a wall-clock timestamp (the sibling `skill-stocktake` results.json has a `generated` date - deliberately omitted here) and the absolute root path. So `SetupGrade` separates `to_dict()` (human report, includes root) from `snapshot_payload()` (baseline, root-free, no timestamp); the snapshot is `json.dumps(..., indent=2, sort_keys=True)`, byte-identical across runs (verified, and asserted by `test_write_snapshot_is_byte_identical`).
- **Snapshot store under `.nexus/`, not `.nexus-hub/`.** The install state lives in `.nexus-hub/`; `.nexus/` is the local-tooling convention the `skill-stocktake` skill already uses, and it is already gitignored (line 84 of `.gitignore`), so snapshots never pollute the repo. Default path `<target>/.nexus/harness-audit/latest.json`, overridable with `--snapshot-dir` (used by the tests against tmp dirs).
- **Single "latest" snapshot = "the most recent snapshot".** Rather than a numbered history, `snapshot` overwrites one `latest.json` and `diff` reads it. This fully satisfies the acceptance criteria (per-dimension improved/unchanged/regressed + grade delta vs the latest snapshot) and stays deterministic.
- **`harness-optimizer` cross-link skipped.** The plan said cross-link `[[harness-optimizer]]` "if present". It is not a skill (it is an agent in the registry only), so linking it would create a dangling wikilink. Linked only the two that resolve (`skill-security-scan`, `skill-eval-loop`).
- **No registry edit.** The `skill-stocktake` edit is body + Related-Skills only; `summary_l0` / `overview_l1` are unchanged, so the three `data/` registries are untouched (the v3.8.0 / v3.9.0 in-scope-refinement precedent). The catalog count stays 259.
- **CLI shape preserves backward compatibility.** A positional `action` defaulting to `audit` plus `--snapshot` / `--diff` aliases means the existing tests (`main(["--target", ..., "--json"])`) and the no-arg default still run the per-integration audit unchanged.

## Verification (quality gate: GO)

`make` is not on PATH (WN-v33-1), so the gate ran via its documented Windows equivalents.

- **Action behavior + exit codes**: `grade` -> 100/100 with the explainable six-dimension breakdown, exit 0; `snapshot` -> wrote `latest.json`, exit 0, byte-identical across two runs; `diff` on an unchanged setup -> all six dimensions `unchanged`, grade delta 0, exit 0; `diff --fail-on-regression` against a strictly-better synthetic baseline -> exit 1; `diff --fail-on-regression` with no baseline -> exit 0.
- **pytest**: 17 new cases in `tests/integrations/test_harness_audit.py` (rubric weights sum to 1.0 + dimension set matches `GRADE_WEIGHTS`; synthetic root grades 100; empty root floors at 1 with all dimensions inapplicable; registry-drift detection; unregistered-security-hook half credit; orphan-hook-reference detection; snapshot payload determinism + byte-identical write; snapshot->diff all-unchanged; regression + improvement classification; CLI grade advisory exit 0, snapshot flag-alias write, fail-on-regression gate, no-snapshot advisory). 25 total in the file, all pass; the 8 pre-existing integration-audit tests still pass.
- **Full `tests/` suite (by subdir, to avoid the 11.5-min integrations run dominating one call)**: integrations 282 passed (includes the harness_audit suite), validators 222 passed, installer 111 passed / 15 skipped / 1 failed -> composite **615 passed / 15 skipped / 1 pre-existing environmental failure**.
- **CI validators**: JSON catalogs OK (259 skills); bundle-audit PASS (the single global warning is the pre-existing stale `demo-capture/scripts/__pycache__/*.pyc`); quality-heuristics 0 warnings; `validate_unicode_safety` / `validate_no_personal_paths` / `scan_supply_chain_iocs` / `validate_workflow_security` exit 0; `check_version_sync` all surfaces match (versions untouched).
- **No-outbound invariant**: the new harness_audit code is stdlib-only and read-only (the only write is the local snapshot); grep for network primitives -> zero.
- **Attribution grep**: zero matches in distributed artifacts for `ruflo` / `MetaHarness` / `AIDefence` / `AgentDB` / `RuVector` / `SONA` / `ReasoningBank` / `rvf` / `rvagent`. (`ruflo` appears in `known-gaps.md` and the DEVLOG only as the cycle/plan identifier, which the attribution rule permits for internal docs.)
- **Norms**: all three changed/added files ASCII-clean; both new wikilinks resolve; `skill-stocktake` body 144 lines under the 500-line norm.

### Pre-existing, out-of-scope finding (not introduced by and not fixed in this phase)

`tests/installer/test_bootstrap.py::test_ps_standalone_extracts_and_hands_off` FAILS with a Windows `tar: unexpected end of file` / `status 128` extraction error. That test stubs out `installer.ps1` and exercises the untouched root `install.ps1` bootstrap (which Phase 5 does not touch). It is the same failure Phase 4 recorded (the WN-v36-1 environmental class on the Windows dev host), not a regression.

## Files changed

- `scripts/harness_audit.py` (grade + snapshot + diff actions, dataclasses, six scorers, formatters)
- `catalog/skills/workflow/skill-stocktake/SKILL.md` (companion-signal section + two cross-links)
- `tests/integrations/test_harness_audit.py` (17 new Phase 5 cases)
- `docs/v3/v3.10/known-gaps.md` (Phase 5 status)
- `docs/v3/v3.10/plans/adoption-ruflo.md` (Phase 5 exit checklist checked off)
- `docs/DEVLOG.md` (Phase 5 entry)
- `docs/archive/v3/v3.10/development/history/2026-06-30_adoption-ruflo-phase-5-agent-setup-grade.md` (this file)

## Next

Phase 6: advisory worker-check hooks + consolidation (re-partial, P3) - the final phase. Select 1-3 ruflo background-worker check ideas that map cleanly to a tool-event hook (strong candidates: a test-gap advisory on edits to source files lacking a sibling test, or a dependency-staleness advisory on manifest edits), implement them as advisory hooks modeled on `workflow-phase-notice.sh` (exit 0 always, disableable via `NEXUS_DISABLED_HOOKS` / the `minimal` profile, pytest each), and register them in `settings.json`. Then the bookkeeping: record the six runtime drops in `docs/policy/mcp-reverse-engineering-matrix.md` (MCP Registry Policy + v3.1.0 / v3.8.0 precedents cited), make the registry-edit decision, add the CHANGELOG `## [Unreleased]` entry (259 skills, 16 commands, 23 + N hooks), and update known-gaps. As the final phase, `/implement` then runs the release-readiness workflow (route the version bump / changelog / tag / push to `/update release`; never auto-tag or auto-push).
