# Docs Cleanup Audit - v3.16

**Mode**: audit only. No file was moved, renamed, or deleted by this pass.
**Run at**: v3.16.3 Phase 1 per-phase audit (2026-08-09), over the v3.16.2 Phase 6 terminal-phase run (2026-08-09), which supersedes the v3.16.0 Phase 2 run. Findings carried forward below.
**Scope**: `docs/v3/v3.16/`, `docs/v3/v3.15/development/` (the two contract documents v3.16.3 amends), the new `docs/incidents/`, plus `docs/policy/` and the repo-root, `scripts/`, and `configs/` surfaces these cycles touched.

## v3.16.3 Phase 6 pass (terminal)

Layout is clean and no file needed to move.

| Check | Result |
|---|---|
| Session histories for this cycle | All six present under `development/history/`, one per phase |
| Probe document | `development/github-entitlement-probe.md`, canonical |
| Legacy or duplicate plan paths for v3.16.3 | None |
| Tracked empty directories | None |
| Orphaned exports in the extension | None; every exported symbol has at least one importer outside its own file |
| Stray docs created by this cycle | None |

**`docs-cleanup-report.md` itself.** The v3.16.2 pass noted that this file is regenerated per phase and that "Phase 5 should reconcile or remove it". It is kept: each per-phase block is short, dated, and additive, and the file reads as the cycle's layout history rather than as a stale snapshot. Removing it would discard the record of decisions such as the `docs/incidents/` placement rationale.

## v3.16.3 Phase 5 pass

Layout is clean and no file needed to move. The phase added one document, at the canonical path.

| Check | Result |
|---|---|
| New session history | `development/history/2026-08-09_github-usage-monitor-ux-phase-5-settings-content.md`, correct |
| Scratch or stray docs created by this phase | None |
| Known-gaps append target | `docs/v3/v3.16/known-gaps.md`, appended within the existing `## v3.16.3` section |
| Resolved-item handling | NI-6 and BG-3 recorded as RESOLVED in place rather than deleted |

## v3.16.3 Phase 4 pass

Layout is clean and no file needed to move. The phase added one document, at the canonical path.

| Check | Result |
|---|---|
| New session history | `development/history/2026-08-09_github-usage-monitor-ux-phase-4-panel-shell.md`, correct |
| Scratch or stray docs created by this phase | None |
| Known-gaps append target | `docs/v3/v3.16/known-gaps.md`, appended within the existing `## v3.16.3` section |
| Orphaned source after the panel merge | None. `SettingsPanel`, `renderSettings`, and the `githubUsageMonitorSettings` webview id are gone from `src/` and `test/`, verified by grep |

## v3.16.3 Phase 3 pass

Layout is clean and no file needed to move. The phase added one document, at the canonical path.

| Check | Result |
|---|---|
| New session history | `development/history/2026-08-09_github-usage-monitor-ux-phase-3-first-run-connection.md`, correct |
| Scratch or stray docs created by this phase | None |
| Known-gaps append target | `docs/v3/v3.16/known-gaps.md`, appended within the existing `## v3.16.3` section |
| Resolved-item handling | MT-1 recorded as RESOLVED in place rather than deleted, so a reader of the Phase 1 entry can still find its disposition |

## v3.16.3 Phase 2 pass

Layout is clean and no file needed to move. The phase added two documents, both at canonical paths.

| Check | Result |
|---|---|
| New probe document | `development/github-entitlement-probe.md`, matching the sibling `github-usage-*-contract.md` and `github-billing-auth-probe.md` convention |
| New session history | `development/history/2026-08-09_github-usage-monitor-ux-phase-2-allowance-and-drawdown-truth.md`, correct |
| Scratch or stray docs created by this phase | None |
| Known-gaps append target | `docs/v3/v3.16/known-gaps.md`, appended as a `### NI-2 ...` block within the existing `## v3.16.3` section rather than opening a second one |

**Probe document placement, noted.** `github-entitlement-probe.md` sits under `docs/v3/v3.16/development/` rather than alongside the two v3.15 contract documents it repeatedly cites. That is correct: it records what was true **when v3.16.3 measured it**, including three superseded conclusions and their corrections, so it is a per-release artifact rather than a contract. The v3.15 contracts remain the durable statements and were amended in place in Phase 1.

## v3.16.3 Phase 1 pass

Layout is clean and no file needed to move. The phase added one document, at the canonical path.

| Check | Result |
|---|---|
| New session history placement | `development/history/2026-08-09_github-usage-monitor-ux-phase-1-rename-to-github-usage-monitor-with-settings-migration.md`, correct |
| Scratch or stray docs created by this phase | None |
| v3.15 contract amendments | Both edited in place with a dated correction block; neither moved, and no duplicate was created |
| Known-gaps append target | `docs/v3/v3.16/known-gaps.md`, the correct per-minor ledger; a `## v3.16.3` section was appended rather than the file replaced |
| Legacy or duplicate plan paths for v3.16.3 | None |

**Cross-version amendment, noted deliberately.** This phase edits two documents under `docs/v3/v3.15/development/` rather than under its own version directory. That is correct rather than a layout violation: both are *contracts* that describe the extension's current behavior, not per-release artifacts, so they are amended in place with a dated correction instead of being forked into a v3.16 copy. Forking would have produced two contract documents disagreeing about the same extension, which is the condition the amendment exists to prevent.

## v3.16.2 pass

Layout is clean and no file needed to move.

| Check | Result |
|---|---|
| Legacy `docs/versions/v*/v*/` tree | Absent |
| Flat `docs/<vSEMVER>/plans/` duplicates | None; every plan is at the canonical `docs/v3/v3.16/plans/` |
| Stray comparison reports outside `comparisons/` | None. Three filename matches were inspected and are false positives: a session history, a plan *about* comparison versioning, and a development CI/CD comparison doc |
| Empty directories | Five found, **all gitignored** (`.antigravitycli`, four under `node_modules`). Nothing tracked to clean |
| Session histories for this cycle | All five present under `development/history/` |

**`docs/incidents/` placement, ratified.** The directory was created at the docs ROOT rather than inside `docs/v3/v3.16/`, and sub-task 6.1 asked for that decision to be recorded explicitly. It is correct and deliberate: an incident is **cross-version by nature**. Both backfilled notes span multiple releases (the v3.11.0 parse error stayed live for four minor versions; the v3.15.6 divergence produced fixes that guard every release since), and filing either under one version directory would bury a lesson that applies to all of them. The placement also matches the existing docs-root convention for cross-version concerns: `policy/`, `security/`, `specs/`, and `git/` all sit there for the same reason. Only per-release artifacts (plans, comparisons, known-gaps, session histories) belong under a version directory.

**One reference repaired.** `docs/v3/v3.16/plans/v3.16.2-loop-longevity-and-doctor-preflight.md` declared `**Slug**: adoption-loopx` and `**Filename**: v3.16.2-adoption-loopx.md` in its own header, naming a file that does not exist. Corrected to match the real slug and filename. This is the plan-metadata half of the drift class the v3.14.2 comparison-versioning work addressed.

## Layout verdict

The version directory follows the canonical `docs/v<MAJOR>/v<MAJOR>.<MINOR>/` scheme with `plans/` and `comparisons/` subdirectories. No legacy flat (`docs/v*/plans/`) or three-level (`docs/versions/v*/v*/plans/`) duplicate of any v3.16 plan exists, so there is no inconsistent-layout condition to report.

| Path | Verdict |
|------|---------|
| `docs/v3/v3.16/plans/` (3 files) | Canonical. Keep. |
| `docs/v3/v3.16/comparisons/` (3 files) | Canonical. Keep. |
| `docs/v3/v3.16/known-gaps.md` | Canonical per-minor ledger. Keep. |
| `docs/archive/v3/v3.16/development/history/` | Created by this phase for the session-history artifact. Expected location. |
| `docs/v3/v3.16/docs-cleanup-report.md` | This file. Regenerated per phase; Phase 5 should reconcile or remove it. |

## Findings

### F-1 - RESOLVED (Phase 5): the loose reference doc was relocated

`github-ci-cd-cost-effective-alternatives.md` moved from the v3.16 version root into a new `research/` subdirectory. Two wrinkles surfaced during the move and are recorded because they shaped how it was done:

1. **No `research/` convention existed.** Across 21 version directories, only `plans` (21), `development` (17), and `comparisons` (17) appear. The subdirectory is new; a future cleanup may prefer to consolidate it.
2. **Two inbound references, handled differently.** The live one in `docs/v3/v3.19/plans/v3.19.0-cost-effective-ci-cd.md` ("Seeded from") was repaired. The one inside a v3.15 session history was **deliberately left unchanged**: a session history is a frozen record of what was true at the time, and rewriting its paths to match a later reorganization would falsify the record. A stale path in a dated historical document is correct.

The original finding is retained below for the record.

### F-1 (original) - LOW: a loose reference doc sits at the version root

`docs/v3/v3.16/github-ci-cd-cost-effective-alternatives.md` is a research/reference document parked directly in the version directory rather than under a subdirectory, unlike every other file in the tree (which lives in `plans/` or `comparisons/`). It predates this phase.

**No action taken.** Moving it would require repairing any inbound references, which is Phase 5's remit under `[[docs-layout-refactor]]` propose-then-apply. Recorded here so that pass does not have to rediscover it.

### F-2 - INFORMATIONAL: no scratch docs were created by this phase

This phase created exactly two documentation artifacts, both intentional and both at canonical paths: the session-history file under `development/history/` and this report. `configs/README.md` is product documentation, not a scratch doc, and is referenced from the code it documents.

Per the audit rule, no cleanup of this phase's own documents is proposed.

### F-3 - INFORMATIONAL: `docs/policy/` now holds two sibling contracts (Phase 2)

Phase 2 added `docs/policy/platform-defaults-levers.md` alongside the existing `platform-read-contracts.md` / `.json` pair. The two are deliberately separate documents with a stated scope boundary (behavioral defaults here, discovery paths and capabilities there), and each names the other in its header so a reader landing on either learns where the other half lives.

**No action taken, and none recommended.** Merging them would create the single overgrown document the boundary exists to prevent. Worth noting for Phase 5's layout pass so the pairing reads as intentional rather than as duplication.

### F-4 - RESOLVED IN-PHASE: `docs/policy/` was excluded from CI

Phase 2's step 8.3 found that `ci.yml`'s `paths-ignore: ['docs/**']` prevented any CI run for a push touching only `docs/policy/`, even though that directory is validator input rather than prose. Fixed within the phase; recorded in full as known gap QG-1. Noted here because it is a docs-layout fact, not only a CI fact: `docs/policy/` is the one subtree of `docs/` that behaves like source.

### F-5 - INFORMATIONAL: the policy pair is now cross-referenced in both directions (Phase 4)

`docs/policy/platform-defaults-levers.md` and `docs/policy/platform-read-contracts.md` each name the other and state the scope boundary, and the `platform-contract-verification` skill now enumerates both in a single re-verification pass while stating which one hard-gates a release. The pairing is intentional and legible from any entry point; no consolidation is warranted.

## Cross-surface check

- `README.md` makes no reference to `configs/`, so the new source needs no README change. Documenting the surface in `AGENTS.md` is explicitly Phase 4.2's sub-task and was deliberately NOT done here, to avoid doing a later phase's work.
- `configs/README.md` did not exist before this phase; it now documents both the pre-existing `permissions/` templates and the new defaults source, so `configs/` is no longer an undocumented directory.

---

## v3.16.5 Phase 1 - fluid layout and readability contract (audit mode, 2026-08-11)

Audit only; no file was moved, renamed, or removed.

- **New artifacts, both permanent and correctly placed**: `catalog/skills/specialized-domains/document-to-interactive-html/references/responsive-typography.md` (a bundled Tier-3 reference, referenced twice from its parent `SKILL.md`, so the orphan-bundle audit is satisfied) and the appended `## v3.16.5 - presentify-visual-overhaul` section of `docs/v3/v3.16/known-gaps.md`. Neither is scratch output.
- **No scratch docs created.** The phase produced no working notes, comparison scratch, or intermediate report, so there is nothing to propose for cleanup.
- **One known misplacement, deliberately left alone**: the calibration fixture `nexus-hub-unit-test-workflow.html` sits untracked at the repository root. Sub-task 1.3 explicitly defers its final location to Phase 7, and moving it here would pre-empt a maintainer decision the plan reserves. Tracked as v3.16.5 MT-1.
- **Cross-surface check**: `README.md` does not enumerate the presentify skill's bundled references, so the new file needs no README change. `AGENTS.md` describes the bundled-resource convention generically and needs no per-file entry.

## v3.16.5 Phase 2 - SVG diagram-quality contract (audit mode, 2026-08-11)

Audit only; no file was moved, renamed, or removed.

- **One new artifact, permanent and correctly placed**: `catalog/skills/specialized-domains/document-to-interactive-html/references/svg-diagram-quality.md`, referenced twice from its parent `SKILL.md` (a Step 6 bullet and the Bundled Resources list) plus reciprocally from `responsive-typography.md` and `visual-qa-rubric.md`. The orphan-bundle audit passes with 0 warnings.
- **The cross-reference debt Phase 1 deliberately took on is now repaid.** Phase 1 wrote and then removed two forward references to this file so it could pass its own gate without a dangling link; Phase 2 restored both, so the two contracts now point at each other and neither claims a file that does not exist.
- **No scratch docs created.** Nothing to propose for cleanup.
- **The one known misplacement is unchanged**: the calibration fixture still sits at the repository root, tracked but not homed, deferred to Phase 7 (MT-1).

## v3.16.5 Phase 3 - real render loop (audit mode, 2026-08-11)

Audit only; no file was moved, renamed, or removed.

- **One new artifact, correctly placed**: `catalog/skills/specialized-domains/document-to-interactive-html/scripts/ensure_render_env.py`, referenced from `SKILL.md` (the Step 9 provisioning bullet and the Bundled Resources list) and from `references/visual-qa-rubric.md`. It is a per-skill bundled script, so it reaches every platform through the existing recursive skill-tree copy with NO installer edit and no `DEV_ONLY_SCRIPTS` entry - it is a distributed artifact, not a repo-internal guard.
- **No `.ps1` sibling is owed**: the parity rule in AGENTS.md applies to `catalog/hooks/<name>.sh` and to `.sh` scripts under a skill's `scripts/`. This is a `.py`, cross-platform by construction, and its Windows browser-detection paths are the primary tested case.
- **No scratch docs committed.** The dogfood render harness and the seeded-regression prover ran from the session scratchpad; the durable half of the latter was promoted into `tests/skills/test_presentify_visual_qa.py` as a parametrized mutation test rather than left as a loose script.
- **The one known misplacement is unchanged**: the calibration fixture still sits at the repository root, tracked, deferred to Phase 7 (MT-1). Phase 3 narrowed MT-1 by half - it is now guarded by two standing tests plus a CI scoring step, so only its LOCATION remains open.

## v3.16.5 errata pass E1-E10 (audit mode, 2026-08-11)

Audit only; no file was moved, renamed, or removed.

- **No new artifacts.** The pass corrected existing contracts, the scorer, the rubric, the command doc, and the calibration fixture. The orphan-bundle audit passes with 0 warnings.
- **The calibration fixture was REPLACED, not edited.** The repo-root copy - verified across four render rounds at 2560x1300 and 1920x1080 - was adopted wholesale as the reference implementation per errata E10, and the Phase 1-3 worktree lineage (diverged by ~3291 lines) was discarded. Recorded here because a 3291-line change to a tracked file with no corresponding feature is otherwise unexplainable to a later reader.
- **No scratch docs committed.** The ground-truth render harness, the E3 recalibration script, and the per-item patch scripts all ran from the session scratchpad. The durable half of the render verification lives in the test suite; the numbers it produced live in the known-gaps BG-E1 entry and the DEVLOG.
- **The fixture's location is still Phase 7's (MT-1).** It remains at the repository root, tracked, now guarded by three standing tests plus a CI scoring step - only its location is open.

## v3.16.5 Phase 4 - intake redesign (audit mode, 2026-08-11)

Audit only; no file was moved, renamed, or removed.

- **One new artifact, correctly placed**: `tests/skills/test_presentify_intake.py`. It sits in the existing pytest root that CI already runs and path-filters, so no workflow edit was needed.
- **Two registry files hand-edited, deliberately**: `data/skills.json` and `data/SKILL_INDEX.md`, because the frontmatter `description`, `summary_l0`, and `overview_l1` changed meaning when procedural visuals became the always-on baseline. The diff is 4 lines. `build_skills_catalog.py` was NOT run: it rewrites the whole tree and would have produced a ~6000-line diff for a three-field change, burying the actual edit.
- **No scratch docs committed.** The per-sub-task patch scripts ran from the session scratchpad.
- **No new bundled resource**, so the orphan-bundle audit is unaffected (it passes with 0 warnings). `design_seed.py` gained a flag rather than a sibling file.
- **The calibration fixture was not touched by this phase** and remains Phase 7's to home (MT-1).

## v3.16.5 Phase 5 - imagery placement intelligence (audit mode, 2026-08-11)

Audit only; no file was moved, renamed, or removed.

- **No new artifacts.** The phase extended three existing files (`references/interactive-features.md`, `references/visual-qa-rubric.md`, `scripts/visual_qa_score.py`), wired the pass into `SKILL.md` Step 9, and added tests to the existing visual-QA suite. The orphan-bundle audit is unaffected and passes with 0 warnings.
- **One pre-existing test fixture was updated rather than worked around**: `_CLEAN` in `test_presentify_visual_qa.py` is scored with `expect_images=1`, i.e. as a consented run, so under the new check it needed the placement record such a run is required to write. The fixture predates the convention; the check is right.
- **No scratch docs committed.** The per-sub-task patch scripts ran from the session scratchpad.
- **A closure note was appended to `docs/v3/v3.15/known-gaps.md`** for MT-2, not a rewrite - the original record and its Phase 3 status note both stand as written, with the closure added beneath them.

## v3.16.5 Phase 6 - cinematic scroll-scrub (audit mode, 2026-08-11)

Audit only; no file was moved, renamed, or removed.

- **Three new artifacts, all correctly placed and all referenced**: `references/scroll-scrub.md` (protocol), `assets/scroll-scrub-engine.js` (the engine - the bundle's first `assets/` JavaScript beyond the Dynamic-Workflow template), and `tests/skills/test_presentify_cinematic.py`. Both bundle files are referenced from `SKILL.md` (Step 6 plus Bundled Resources), so the orphan-bundle audit passes with 0 warnings.
- **No installer edit needed.** Both new bundle files sit under the skill's own `references/` and `assets/`, which both installers copy recursively. The engine is a `.js` asset, not a repo-level `scripts/` entry, so it needs no explicit-name copy step and no `DEV_ONLY_SCRIPTS` entry.
- **No `.ps1` sibling is owed**: the parity rule applies to `.sh` scripts. The engine is browser JavaScript.
- **Attribution is confined to `docs/policy/mcp-reverse-engineering-matrix.md`**, which is the one place the rule permits it. Verified mechanically: 0 occurrences of the upstream project, vendor, or author name across `catalog/` and `templates/`, and a parametrized test now guards the five most likely files.
- **The matrix section preamble was widened rather than contradicted.** It said the skill-native rows are "pure Markdown skills with zero code"; this adoption also ships a zero-dependency browser asset, so the sentence now describes that accurately and classifies the engine half as `re-full`.
- **No scratch docs committed.** The cinematic verification build wrote a temporary page, scored it, rendered it at two motion preferences, and deleted it.

## v3.16.5 Phase 7 - terminal refactor and reconciliation (2026-08-11)

The plan's terminal gate. Unlike the prior six entries this one APPLIED a change rather than only auditing, because sub-task 7.1 owns the one file every earlier phase deferred.

- **The calibration fixture is homed**: `nexus-hub-unit-test-workflow.html` moved from the repository root to `tests/fixtures/presentify/`, by maintainer decision, with `git mv` so history follows it. Both live references were handled: the CI scoring step's path was repaired, and the dual-candidate lookup in `test_presentify_visual_qa.py` was simplified to the single home - it existed only to survive this move, and leaving it would have left a second accepted location nobody maintains. Historical session-history entries were NOT rewritten; they record where the file was at the time, which is correct.
- **One gap the move itself introduced, found and closed in the same pass**: `presentify-extractor.yml` path-filtered `tests/skills/**` but not `tests/fixtures/**`, so a fixture-only edit would no longer have triggered the job that scores it. The standing gate would have silently stopped gating the exact file it guards. `tests/fixtures/presentify/**` was added to both filter lists.
- **Bundle layout: clean, no action.** Seven `references/`, four `assets/`, seven `scripts/`, every one referenced from `SKILL.md` (orphan audit 0 warnings). No empty directories, no duplicates, no stray files. `__pycache__` is gitignored. `SKILL.md` is 292 lines against a 500-line target and an 800-line cap.
- **Docs layout: clean, no action.** `docs/v3/v3.16/` holds `plans/` (5), `comparisons/` (4), `development/` (6 + `history/` 32), and exactly the two conventional root files (`known-gaps.md`, `docs-cleanup-report.md`). Matches the established per-version scheme; nothing to move.
- **No scratch docs committed** across any of the seven phases. Every per-sub-task patch script, the ground-truth render harness, the seeded-regression prover, and the cinematic verification build ran from the session scratchpad; the durable half of each was promoted into the test suite.
- **Prior cleanup entries stand unmodified.** This file is append-only per its own v3.16.3 precedent.

## v3.16.8 Phase 3 - terminal refactor and reconciliation (audit mode, 2026-08-14)

The `adoption-watermark-hygiene` plan's terminal gate. Audit only: no file was moved, renamed, or deleted.

- **Docs layout: clean, no action.** `docs/v3/v3.16/` holds `comparisons/`, `development/` (with `history/`), `plans/`, and exactly the two conventional root files (`known-gaps.md`, `docs-cleanup-report.md`). The v3.16.8 plan and its seeding comparison are co-located, satisfying the co-location rule.
- **Four empty directories, all deliberately left.** `.antigravitycli` and `.claude/worktrees` are gitignored local runtime dirs. `docs/v3/v3.17/development/history` and `docs/v3/v3.20/comparisons` are other versions' scaffolding, and v3.17 has ACTIVE work from a parallel session in this same tree, so cleaning it would be both out of scope and disruptive to another session.
- **One stray root artifact, left rather than deleted.** `pytest-out.log` is gitignored (`*.log`), untracked, dated 2026-05-22, and absent from `MANIFEST.sha256`, so it never ships. It is a local scratch file in the user's working tree, not a repository artifact.
- **No tracked caches**: zero `__pycache__` or `.pyc` under version control.
- **No deferred-work markers**: zero `TODO` / `FIXME` / `XXX` / `HACK` / `# DEVIATION:` across every code and instruction file this version changed.
- **No new artifact needs an installer edit.** This version changed one existing repo-level script (`scripts/validate_unicode_safety.py`, already registered by explicit name in both installers), two `catalog/commands/` files, and one `catalog/skills/` SKILL.md. The two catalog trees are copied recursively, so no installer edit and no registry update is owed. No `.ps1` sibling is owed either: the parity rule covers `catalog/hooks/*.sh`, and nothing here is a hook.
- **No scratch docs committed.** Every smoke test, path probe, and character-histogram script ran from the session scratchpad.
- **Prior cleanup entries stand unmodified**, per this file's append-only v3.16.3 precedent.
