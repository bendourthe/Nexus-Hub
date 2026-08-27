# Last-phase evidence - v3.21.0 plan-implement-lifecycle-and-docs-architecture

**Date**: 2026-08-24
**Plan**: `docs/v3/v3.21/plans/v3.21.0-plan-implement-lifecycle-and-docs-architecture.md`
**`is_final_phase`**: true (Phase 5 of 5; Phases 1-4 have session histories and commits `0765a757`, `aa3bf91b`, `3f63375d`, `08713647`)

This file is the fail-closed last-phase pack. Each section quotes a proving command or scan. An empty finding is not a pass unless that scan is quoted.

---

## Architecture refactor

**Detectors**: `[[project-refactor]]` empty-dir / duplicate / orphan / structure (propose-then-apply); `[[docs-layout-refactor]]` layout + retention.

**Empty-directory scan** (Python `os.walk` from repo root, skipping `.git`, `node_modules`, `.venv`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `dist`, `build`, `.next`; `.gitkeep` holders not flagged):

```text
=== EMPTY DIRECTORIES (no files, excluding .gitkeep holders) ===
.antigravitycli
.claude/worktrees
docs/v3/v3.17/development/history
extensions/nexus-code-search/benchmarks/.work/corpus/.nexus/code-index
extensions/nexus-code-search/benchmarks/.work/run-10k3cjf4/corpus/tests
extensions/nexus-code-search/benchmarks/.work/run-nleyqgk5/corpus/tests
count=7
```

**Disposition (no prune applied)**:

- `.antigravitycli` and `.claude/worktrees` are local tool caches, not catalog artifacts.
- `docs/v3/v3.17/development/history` is an empty leftover after retention moved history to `docs/archive/v3/v3.17/development/history/`. Version directory kept; empty history dir reported, not deleted.
- `extensions/nexus-code-search/benchmarks/.work/**` is benchmark scratch.

**Retention**:

```text
  docs retention: nothing due for archival (current v3.20, threshold 2 minors)
```

(Plugin version is still 3.20.3 until `/update release` bumps to 3.21.0. After that bump, v3.19 `development/` becomes due; that move belongs to the release refactor scope.)

**Co-location**:

```text
Enforcing co-location under every major: docs/v3, docs/v4 (docs/archive/** grandfathered)
OK: no comparison / adoption-plan co-location mismatches under docs/v3, docs/v4
```

No layout moves this phase. Living-docs scaffold (`docs/README.md`, `docs/handbooks/`) is recorded under Living docs architecture, not as a detector prune.

---

## Known-gaps reconciliation

**Glob**: `Path('docs').rglob('known-gaps.md')` -> **28 files**.

```text
docs/archive/v1/v1.1/known-gaps.md
docs/archive/v1/v1.3/known-gaps.md
docs/archive/v2/v2.0/known-gaps.md
docs/archive/v2/v2.1/known-gaps.md
docs/archive/v2/v2.2/known-gaps.md
docs/archive/v2/v2.3/known-gaps.md
docs/archive/v2/v2.4/known-gaps.md
docs/v3/v3.0/known-gaps.md
docs/v3/v3.1/known-gaps.md
docs/v3/v3.10/known-gaps.md
docs/v3/v3.11/known-gaps.md
docs/v3/v3.12/known-gaps.md
docs/v3/v3.13/known-gaps.md
docs/v3/v3.14/known-gaps.md
docs/v3/v3.15/known-gaps.md
docs/v3/v3.16/known-gaps.md
docs/v3/v3.17/known-gaps.md
docs/v3/v3.18/known-gaps.md
docs/v3/v3.19/known-gaps.md
docs/v3/v3.2/known-gaps.md
docs/v3/v3.20/known-gaps.md
docs/v3/v3.21/known-gaps.md
docs/v3/v3.3/known-gaps.md
docs/v3/v3.4/known-gaps.md
docs/v3/v3.6/known-gaps.md
docs/v3/v3.7/known-gaps.md
docs/v3/v3.8/known-gaps.md
docs/v3/v3.9/known-gaps.md
```

### This version (`docs/v3/v3.21/known-gaps.md`)

Status in-progress. New deferred items this last phase: DF-1 (no catalog atlas HTML), DF-2 (stale `docs/todos.md` dashboard). See that file.

### Other files with remaining Open Items (not skipped because they are another version)

| File | Status | Disposition |
|---|---|---|
| `docs/v3/v3.20/known-gaps.md` | finalized, Open Items remain | **Defer, stay in source file.** DF-1 (no vendor invocation lever), DF-2 (Claude plugin directory form not submitted), WN-3 (full-tree personal-paths scan too slow on OneDrive). Phase B.5 of this plan named them out of scope. Next `/plan` ingest. |
| `docs/v3/v3.19/known-gaps.md` | was in-progress | **Addressed this phase.** Header Status set to finalized. v3.19.1 BG-1 (published tarball verify FAIL) moved to Resolved; v3.19.2 already shipped the fix. Remaining v3.19.2 DF-2, DF-3, DF-4 stay in that file for next `/plan` ingest. |
| `docs/v3/v3.11` through `v3.18`, `v3.16` leftover IDs | shipped-minor prose Status | **Reviewed, not transferred.** Historical Open Item headings remain in those files. They are not v3.21.0 release blockers. Next `/plan` may ingest; this plan does not rewrite every prior minor. |
| `docs/archive/**/known-gaps.md` | archive | **No action.** Frozen. |
| Remaining `docs/v3/v3.0`..`v3.10` | complete/finalized prose | **No remaining live Open Items** after heading parse of `##### (NI\|DF\|BG\|WN\|MT\|QG)-N` outside Resolved tables, or Status already complete. |

No file was skipped because it belonged to another version.

---

## Living docs architecture

**Scan after last-phase scaffold** (do not invent `docs/testing/` or `docs/validation/`; do not invent a fake atlas HTML):

```text
docs/handbooks: exists=True is_dir=True
docs/handbooks/README.md: exists=True is_dir=False
docs/handbooks/markdown: exists=True is_dir=True
docs/handbooks/html: exists=True is_dir=True
docs/decisions: exists=True is_dir=True
docs/README.md: exists=True is_dir=False
docs/DEVLOG.md: exists=True is_dir=False
docs/todos.md: exists=True is_dir=False
docs/testing: exists=False is_dir=False
docs/validation: exists=False is_dir=False
handbooks markdown children: [WindowsPath('docs/handbooks/markdown/.gitkeep')]
handbooks html children: [WindowsPath('docs/handbooks/html/.gitkeep')]
atlas/companion html count: 0
```

**Evidenced no-op / recorded gap**: this catalog is not an application with a user-facing product walkthrough. Atlas HTML count is 0 by design. `docs/handbooks/README.md` states that `/update release` regenerate-and-fail-on-stale is a no-op while `markdown/` has no authored pages. Recorded as v3.21.0 DF-1 rather than generating a fake walkthrough.

`docs/todos.md` still opens on `feat/presentify-slide-navigation`. Recorded as DF-2; a full dashboard rewrite is out of this plan's Goal.

`docs/decisions/` has 21 markdown files including `2026-08-24-living-docs-handbooks-and-decisions.md`.

---

## Git-tree hygiene

Command: `python scripts/check_release_preconditions.py --branches --repo-settings`

Report only. Nothing was deleted.

```text
Branch hygiene (merged into origin/develop)
  OK: no merged remote branches to clean up
  1 branch(es) survive a CLOSED, unmerged PR:
    - origin/backmerge/v3.20.0
  delete_branch_on_merge does NOT cover these. Review and delete by hand.
  Reporting only -- nothing was deleted.
Repository settings
  OK: delete_branch_on_merge is enabled
  OK: repository description agrees with README.md
```

---

## CI/CD coverage

**New tests this plan**: `tests/skills/test_last_phase_fail_closed.py`, `tests/skills/test_implement_driver_modes.py`, `tests/skills/test_living_docs_architecture.py`.

**Coverage without a new required-check context**: `.github/workflows/ci.yml` job `tests` already runs `python -m pytest tests/skills -v` (line 678). `docs/policy/required-checks.json` still lists only `validate`, `shellcheck`, `ci-required`, `colocation`, `verify` on `main` and `develop`. No new context added.

**No workflow-level `paths:`**: `ci.yml` `on:` is unfiltered (`workflow_dispatch`, `push` to main/develop/tags, `pull_request` to main/develop). Comments at lines 8 and 753 forbid adding a workflow-level `paths:` filter.

**Optimization already present**: `concurrency.cancel-in-progress: true`; path scoping is job-level `if:` via the `changes` job, not a workflow `paths:` filter.

**Installer parity** (hard gate; this repo ships two installers):

```text
installer parity: PASS
```

No CI workflow edit this phase.

---

## Goal-vs-codebase review

**Plan Goal restated**: `/plan` and `/implement` (plus `/setup`, `/update docs`, `/update refactor`, and `/update release`) produce and enforce a fail-closed last phase, a multi-phase implement driver, and the rd-data-dev living-docs architecture so a completed plan means the original goal landed, not only that every phase checkbox was ticked.

**Independent inspection** (as if this agent had not implemented the phases): the following artifacts exist in the catalog and docs tree.

| Goal element | Artifact |
|---|---|
| Fail-closed last phase + evidence file + Goal review | `catalog/skills/workflow/implementation-plan/SKILL.md` (eight duties, `last-phase-evidence.md`); `catalog/skills/workflow/implement-phase/SKILL.md` and `references/implement-phase-runbook.md` (Phase 9 blocked without evidence); `catalog/commands/plan.md` names fail-closed last phase |
| Human QA deferred until last phase | `catalog/skills/workflow/session-history/SKILL.md`; planner Testing continuous guideline; this file's Human/manual section |
| `/implement in-full` and `phase-by-phase` | `catalog/commands/implement.md` lines 21-24; runbook Driver loop; `tests/skills/test_implement_driver_modes.py` |
| Living handbooks + decisions on current paths | `catalog/skills/code-cleanup/docs-layout-refactor/SKILL.md`; `setup-project` Step 4; `catalog/commands/setup.md`, `plan.md`, `update.md`; ADR `docs/decisions/implemented/architecture/2026-08-24-living-docs-handbooks-and-decisions.md` |
| v4.0 consumes handbooks | `docs/v4/v4.0/plans/v4.0.0-docs-lifespan-tree-and-enforcement.md` (no `has no equivalent`); `test_v4_lifespan_plan_consumes_handbooks_equivalent` |
| This last phase itself uses the contract | this file |

**Gaps**:

- Nexus-Hub's own tree has handbook dirs and README but **zero atlas HTML**. Recorded as DF-1. Not a miss of the command/skill Goal (consuming projects are what the commands enforce; this catalog must not invent a fake atlas).
- `docs/todos.md` is stale. Recorded as DF-2. Not a miss of driver modes or last-phase gates.

No unresolved Goal miss without a recorded known-gap.

---

## Human/manual testing suggestions

Last phase only. Automated tests already passed.

- After the next installer run (or a local catalog checkout), confirm `/implement` argument help names `in-full` (alias `full`) and `phase-by-phase`, and that a slug containing the substring `full` is not treated as a mode.
- Confirm `/plan` still presents a thin dispatcher and does not paste the eight-duty template.
- Confirm `docs/handbooks/html/` contains no hand-authored fake atlas, and that `docs/README.md` plus `docs/decisions/` are reachable from the docs root.
- On Claude / Gemini / Codex / Cursor, confirm the updated `implement` command file is the one the slash menu reads. OpenCode has no slash surface; confirm the skill/instruction path instead.
- Do not run `/update release` until this evidence file is present (it is). Tag, push to `main`, and GitHub Release stay behind `/update release` confirmation gates.

---

## Full-suite testing and stabilization

GNU `make` is not on PATH. Equivalents:

```text
python -m pytest tests/skills/test_last_phase_fail_closed.py tests/skills/test_implement_driver_modes.py tests/skills/test_living_docs_architecture.py -q
.................                                                        [100%]
17 passed in 0.24s

python scripts/validate_skills.py --bundles-only
RESULT: PASS (0 errors, 65 warnings)

python scripts/check_agentskills_conformance.py
RESULT: PASS (0 errors, 324 skills scanned)

python scripts/validate_decision_records.py
  20 decision record(s) OK

python scripts/check_installer_parity.py
installer parity: PASS

python scripts/check_doc_colocation.py
OK: no comparison / adoption-plan co-location mismatches under docs/v3, docs/v4

python scripts/check_version_sync.py
canonical version: 3.20.3 (.claude-plugin/plugin.json)
  [      match] data/marketplace.json: matches 3.20.3
  [      match] scripts/installer.sh: matches 3.20.3
  [      match] scripts/installer.ps1: matches 3.20.3
  [      match] CHANGELOG.md: matches 3.20.3
  [      match] README.md: matches 3.20.3
  [      match] AGENTS.md: matches 3.20.3
```

**Not run here**: `python scripts/validate_no_personal_paths.py` default walk (v3.20 WN-3; too slow on this OneDrive host). CI `validate` job still owns that walk.

**Lint**: no new `.sh` files this plan. `make lint` is ShellCheck on installer scripts; skipped locally (`shellcheck` not required for these Markdown/Python edits).

**Model-prompting freshness** (advisory; does not block):

```text
python scripts/check_model_prompting_freshness.py --advisory
[profile-freshness] UNKNOWN: no live roster supplied, so drift cannot be determined.
  Recorded roster (4, last verified 2026-07-27): claude-fable-5, claude-haiku-4-5-20251001, claude-opus-5, claude-sonnet-5
```

Reason: this session is Cursor picker-only; no scriptable live roster. UNKNOWN recorded with that reason, not as IN SYNC.

**Hold for `/update release`**: none from Goal review. Version is still 3.20.3 until the release scope bumps it. This file is complete.
