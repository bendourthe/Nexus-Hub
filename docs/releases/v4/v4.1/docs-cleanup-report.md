# Docs Cleanup Audit - v4.1.0 Skill Trial Records and Typed-Boundary Hygiene

**Date**: 2026-08-27
**Mode**: audit only; no files moved
**Plan**: `docs/releases/v4/v4.1/plans/v4.1.0-adoption-skill-trial-records-and-low-evidence-ts.md`

## Phase 1 - Procedural-Anchor Authoring Rule

### Layout check

`python catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py inventory --root docs` completed and classified the v4.1 plan and comparison under the canonical `docs/releases/v4/v4.1/` tree. Phase 1 adds only the required known-gaps ledger, this audit record, and a session-history entry under that same release directory; no scratch document or move is proposed.

`python catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py lifespan-contradictions --root docs` exited 1 because older release buckets contain post-tag edits from the v4.0 documentation-tree migration. Those findings predate this phase and include no new v4.1 artifact; this audit records the baseline without expanding Phase 1 into historical cleanup.

### New documentation artifacts

| Path | Category | Disposition |
|---|---|---|
| `docs/releases/v4/v4.1/known-gaps.md` | Active release gap ledger | Keep; Phase 1 records zero open or resolved items. |
| `docs/releases/v4/v4.1/docs-cleanup-report.md` | Active release audit record | Keep and append later phase audits until release close. |
| `docs/releases/v4/v4.1/development/history/2026-08-27_v4.1.0-adoption-skill-trial-records-phase-1-procedural-anchor.md` | Active phase evidence | Keep under the current version's development history. |

### Result

No duplicate, orphaned, scratch, or misplaced documentation was created by Phase 1. No file moved, and no cleanup change was approved or applied.

## Phase 2 - Typed-Boundary Hygiene Skill and TypeScript Handoff

### Layout check

Phase 2 adds one catalog skill tree at `catalog/skills/language-specialists/typed-boundary-hygiene/` and one release-scoped session history under `docs/releases/v4/v4.1/development/history/`. The skill's trigger fixture is a bundled resource referenced by the skill body through its trigger-evaluation contract, and the existing recursive installers require no new copy line.

### Registry and documentation placement

The new skill is registered in `data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json`, and the language-specialists module in `data/bundles.json`. Live catalog counts in `README.md` and `AGENTS.md` moved from 325 to 326; v4.0 historical evidence remains unchanged at its recorded count.

### Result

No documentation move, duplicate, scratch artifact, or release-tree contradiction was introduced by Phase 2. The phase adds only its canonical history record and appends this audit.

## Phase 3 - Distillation Labels, Confusability, and Two-Level Triggers

### Layout check

Phase 3 edits four existing catalog skills, their machine-registry Tier-1 text where required, the shared semantic test file, and release-scoped records. No new bundled reference, scratch report, living document root, or installer artifact is introduced.

### Generated and local outputs

The `skill-stocktake` instructions define `.nexus/skill-stocktake/report.md` as a local, gitignored runtime output; the required language-specialists calibration was performed without committing that cache or report. The only durable evidence is the canonical Phase 3 history file under `docs/releases/v4/v4.1/development/history/`.

### Result

No documentation move, duplicate, scratch artifact, or lifespan contradiction was introduced by Phase 3. Existing v4.1 release records remain in the active release tree.

## Phase 4 - Eval-Loop Third Arm

### Layout check

Phase 4 edits the existing `skill-eval-loop` bundle, its two repository-level runtime scripts, the existing eval-loop test module, and release-scoped records. It introduces no new directory outside the established skill bundle, scripts root, test tree, or `docs/releases/v4/v4.1/` evidence tree.

### Runtime artifacts

The optional `raw_memory/` directory exists only inside a user's eval workspace when an eval entry declares a readable source file. Benchmark JSON, Markdown, viewer HTML, comparison JSON, and feedback remain workspace outputs rather than committed project documentation.

### Result

No documentation move, duplicate, scratch artifact, or lifespan contradiction was introduced by Phase 4. The phase adds only its canonical history record and appends this audit.

## Phase 5 - Oxlint Vendor Decision

### Layout check

Phase 5 adds one rejected tooling decision under the living `docs/decisions/rejected/tooling/` tree, one durable out-of-scope policy entry under `docs/policy/out-of-scope/`, and one release-scoped history record. The decision remains living because it may be superseded after v4.1.0; the session evidence remains release-bound.

### No-op implementation branch

The decision chose no, so Phase 5.2 added no catalog skill, bundled asset, package manifest, installer line, workflow step, or runtime dependency. The out-of-scope index links the new policy entry, and the v4.1.0 known-gaps ledger remains empty because rejected work is not deferred work.

### Result

No documentation move, duplicate, scratch artifact, or lifespan contradiction was introduced by Phase 5. The living decision and policy files pass their respective admission tests, and the phase history remains in the active release evidence tree.

## Phase 6 - Terminal Architecture and Documentation Audit

### Documentation layout

The canonical audit reported 387 active documentation files, including 9 under `docs/releases/v4/v4.1/`. Its reference graph contained 102 targets with zero unreferenced targets and zero unreferenced v4.1 targets. The lifespan command retained its historical exit-1 baseline of 1,703 findings from post-tag edits in older release buckets; none mentions `docs/releases/v4/v4.1/`, so no current-plan contradiction was found.

### Repository structure triage

The root contains 24 files. Ignored `.coverage` and `pytest-out.log` are local test outputs, while the remaining root files are repository metadata, manifests, installers, or living project documents. Five obsolete-name candidates were inspected and retained because they are current old-version guards, the active `deprecated-api-updater` skill/agent, or a deliberate legacy marker.

Ten filesystem-empty directories were found. `.antigravitycli/`, `.claude/worktrees/`, extension `.vite-temp/` directories, and benchmark `.work/` subdirectories are host-local or ignored outputs; `docs/decisions/proposed/process/` and `docs/decisions/proposed/tooling/` are untracked empty placeholders under the declared decisions taxonomy. None is a shipped tracked artifact, so no repository deletion is required.

Six duplicate-content groups were inspected: a self-contained bundled checklist, extension license/icon/update-watcher/tsconfig copies, and the parity-locked base templates. Fourteen single-child directories were also inspected across platform configuration roots, package `src/` roots, and ignored benchmark workspaces. These structures encode distribution, package, or generated-workspace boundaries and are not redundant. The only unusually deep tracked file outside the expected catalog, docs, extension, guide, script, template, config, data, and test roots is the intentional organization-bundle schema example.

### Result

No tracked obsolete file, empty directory, redundant directory, misplaced document, or overcomplicated structure warranted a move or deletion. Because the audit proposed no repository mutation, the project-refactor and docs-layout confirmation gate did not activate. Phase 6 adds only its canonical session history and last-phase evidence under `docs/releases/v4/v4.1/development/`.

## v4.1.1 Phase 1 - Scanner-Receipt and Independent-Verification Contract

**Date**: 2026-08-28
**Mode**: audit only; no files moved
**Plan**: `docs/releases/v4/v4.1/plans/v4.1.1-adoption-openworker-security-refinement.md`

### Layout check

Phase 1 adds one version-bound contract at `docs/releases/v4/v4.1/development/v4.1.1-security-audit-contract.md` and one session-history file under `docs/releases/v4/v4.1/development/history/`. The closure-gate script and review-record reference remain inside the existing `security-review` skill tree, which recursive installers already copy.

### New documentation artifacts

| Path | Category | Disposition |
|---|---|---|
| `docs/releases/v4/v4.1/development/v4.1.1-security-audit-contract.md` | Active version-bound contract | Keep; it is the Phase 1 normative record and is not a distributed skill file. |
| `docs/releases/v4/v4.1/development/history/2026-08-28_v4.1.1-adoption-openworker-security-refinement-phase-1-scanner-receipt-contract.md` | Active phase evidence | Keep under the current version's development history. |

### Result

No duplicate, orphaned, scratch, or misplaced documentation was created by v4.1.1 Phase 1. No file moved, and no cleanup change was approved or applied.

## v4.1.1 Phase 2 - Local Scanner Recipes and Rule Ownership

**Date**: 2026-08-28
**Mode**: audit only; no files moved
**Plan**: `docs/releases/v4/v4.1/plans/v4.1.1-adoption-openworker-security-refinement.md`

### Layout check

Phase 2 adds `catalog/skills/code-review/security-review/references/local-scanner-recipes.md`, linked from that skill's body, and edits existing owning skills in place. Recursive skill-tree copy already delivers the new reference. No installer copy line is required.

### Result

No duplicate, orphaned, scratch, or misplaced documentation was created by v4.1.1 Phase 2. No file moved.
