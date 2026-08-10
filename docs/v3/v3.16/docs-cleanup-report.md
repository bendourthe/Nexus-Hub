# Docs Cleanup Audit - v3.16

**Mode**: audit only. No file was moved, renamed, or deleted by this pass.
**Run at**: v3.16.3 Phase 1 per-phase audit (2026-08-09), over the v3.16.2 Phase 6 terminal-phase run (2026-08-09), which supersedes the v3.16.0 Phase 2 run. Findings carried forward below.
**Scope**: `docs/v3/v3.16/`, `docs/v3/v3.15/development/` (the two contract documents v3.16.3 amends), the new `docs/incidents/`, plus `docs/policy/` and the repo-root, `scripts/`, and `configs/` surfaces these cycles touched.

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
| `docs/v3/v3.16/development/history/` | Created by this phase for the session-history artifact. Expected location. |
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
