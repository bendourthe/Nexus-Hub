---
name: known-gaps-tracker
description: Maintain docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/known-gaps.md - a per-minor-version unfinished-work register (patch releases append their own subsection) for items that were not implemented, deferred, buggy, suppressed, or left without coverage at the end of each phase. Use for known gaps, deferred work, unresolved bugs, missing coverage, phase leftovers, and next-plan carry-forward. /implement-phase appends, /wrap-up-session sweeps and finalizes, /generate-plan ingests open items into the next plan. Version-bound documentation uses docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/; closed snapshots use docs/archives/.
summary_l0: "Track release-scoped unfinished work with derived counts for the next plan"
overview_l1: "This skill maintains docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/known-gaps.md as a per-minor-version, append-only log of items that did not reach a clean state by the end of a phase: subtasks not implemented, work intentionally deferred, bugs found but not fixed, warnings suppressed, missing tests or coverage gaps, and quality gates the user opted to bypass. Because patch releases share their minor directory, the file is multi-release aware - each patch appends its own subsection rather than overwriting a shared file. /implement-phase appends to it after each phase; /wrap-up-session sweeps the live conversation for any uncaptured gaps and finalizes the file when the version is bumped; /generate-plan reads the immediately prior version's known-gaps.md (and any older still-in-progress files) to seed the discovery interview for the next plan, so unfinished work is automatically pulled forward. Trigger phrases: known gaps, deferred work, carryover, unfinished items, what was left over, prior version gaps, docs/<version>/known-gaps.md. Version-bound documentation uses docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/; closed snapshots use docs/archives/."
---

# Known-Gaps Tracker

Maintain `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/known-gaps.md` as a per-minor-version, append-only record of work that did not reach a clean state by the end of each phase, and pull open items forward into the next version's plan. Patch releases share the minor directory, so the file is multi-release aware: each patch release appends its own `## v<MAJOR>.<MINOR>.<PATCH>` subsection under a single file-level header (see `[[docs-layout-refactor]]`'s Version-directory resolution for the scheme).

## When to Use This Skill

- **Inside `/implement-phase` Phase 8**: after `/update-gitignore`, append any new gaps discovered during the phase.
- **Inside `/wrap-up-session` Phase 4**: after `/update-devlog`, sweep the live conversation for uncaptured gaps; on a version bump in Phase 6, flip the file's `Status` to `finalized`.
- **Inside `/generate-plan` Step 0.6** (right after Step 0.5 From-comparison mode): read the immediately prior version's `known-gaps.md` plus any older still-in-progress files, and offer to ingest open items into the new plan.

**When NOT to use**: do not duplicate forward-looking sprint planning that belongs in `docs/todos.md` (managed by `dev-progress-tracker`). `known-gaps.md` records what slipped during the version that just shipped or is shipping; `docs/todos.md` describes the live forward roadmap. Also distinct from `docs/<next-version>/review/00-known-gaps.md` produced by `/run-deep-review`, which is a one-shot pre-release aggregation across many sources - this file is one of the sources that aggregation should read.

**Out-of-scope is a different surface.** `docs/policy/out-of-scope/` records features we have decided to never do. Known-gaps records work intended for later (`DF` still means "maybe in a future plan"). When the user or the comparison says "we will never do this", "this is a declined feature", or "do not add X", write or update `docs/policy/out-of-scope/<topic-slug>.md` and add it to that directory's README index. Do not append a never-do item here; a `DF` row would invite `/generate-plan` to ingest it as scope.

## Out-of-scope register (never-do, not do-later)

Path: `docs/policy/out-of-scope/README.md`. Each entry is one kebab-case file with (1) a one-line declaration, (2) why it is out of scope, (3) prior requests. If an open known-gaps row is later recognized as never-do, move it to Resolved with `Resolved in: transferred to docs/policy/out-of-scope/<topic-slug>.md` so the two files cannot disagree.

## File Format

Path: `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/known-gaps.md` - **one file per minor version** that has had at least one phase implemented. Patch releases share their minor directory, so the file carries a single file-level header (`Project`, `Status`, `Last updated`) followed by one `## v<MAJOR>.<MINOR>.<PATCH>` subsection per patch release; a new patch appends its subsection rather than overwriting the header or a prior patch's items.

```markdown
# Known Gaps - v3.10

**Project**: <name>
**Status**: in-progress | finalized
**Last updated**: <YYYY-MM-DD>

## v3.10.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | N | N |
| Deferred (DF) | N | N |
| Bugs / regressions (BG) | N | N |
| Warnings (WN) | N | N |
| Missing tests / coverage gaps (MT) | N | N |
| Quality-gate gaps (QG) | N | N |

### Open Items

#### Not Implemented

##### NI-1 - <short title>

- **Source phase**: Phase N - <name>
- **Plan reference**: `docs/releases/v3/v3.10/plans/v3.10.0-<slug>.md` (sub-task N.X)
- **Reason**: <why it was skipped or could not be completed>
- **Suggested next step**: <one-line actionable hint for the next plan>

#### Deferred

(DF-1 ... using the same shape as NI)

#### Bugs / Regressions

(BG-1 ... include reproduction steps and observed-vs-expected behavior when known)

#### Warnings

(WN-1 ... e.g., suppressed lint rules with reason, runtime warnings, dependency deprecation notices)

#### Missing Tests / Coverage Gaps

(MT-1 ... files below the project coverage threshold and which paths are uncovered)

#### Quality-Gate Gaps

(QG-1 ... gates the user opted to bypass with "Proceed anyway", e.g., 75% coverage instead of 80%)

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| NI-3 | Settings panel keyboard shortcuts | Phase 5 | Implemented as part of authentication subtask |

## v3.10.1

(the next patch release appends its own section here with the same Summary / Open Items / Resolved shape; the file-level header above is written once and never rewritten)
```

ID prefixes are stable: `NI-`, `DF-`, `BG-`, `WN-`, `MT-`, `QG-`. Numbers are monotonic per category within the minor file (across all `## v<MAJOR>.<MINOR>.<PATCH>` subsections) - never reuse an ID once written, even after the item is resolved or a later patch adds new items.

## Instructions

### Append (during `/implement-phase` Phase 8)

1. Resolve the minor directory for the active plan per `[[docs-layout-refactor]]`'s Version-directory resolution, then locate or create `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/known-gaps.md`. Within it, locate or create the `## v<MAJOR>.<MINOR>.<PATCH>` subsection for the specific patch release being implemented; append this phase's items under that subsection only, never under a different patch's and never by rewriting the file-level header.
2. If the file does not exist, create it with the file-level header (`Project`, `Status: in-progress`, `Last updated`) followed by the current release's `## v<MAJOR>.<MINOR>.<PATCH>` subsection with empty section scaffolding. If the file exists but has no subsection for the current patch, append a new `## v<MAJOR>.<MINOR>.<PATCH>` subsection rather than editing an existing one.
3. Walk the artifacts produced by Phases 2 through 7 of `/implement-phase`:
    - `# DEVIATION:` markers from Phase 2 - classify as `NI` (skipped), `DF` (intentionally deferred), or `BG` (deviation revealed a bug) based on the deviation reason.
    - Unresolved test failures from Phase 6 when the user picked option A "Skip failing tests" - classify as `BG`.
    - Coverage shortfalls from Phases 4 and 5 (files that ended below 80%) - classify as `MT`.
    - Suppressed lint rules or runtime warnings observed during Phase 3 - classify as `WN`.
    - Any gate the user bypassed with "Proceed anyway" in Phase 7 - classify as `QG`.
4. For each item:
    - Allocate the next ID in its category (e.g., `NI-4` if `NI-3` was the last one used).
    - Write all four required fields: `Source phase`, `Plan reference`, `Reason`, `Suggested next step`.
    - Append under the matching `### Open Items` subsection of the current patch's `## v<MAJOR>.<MINOR>.<PATCH>` section.
5. If this phase resolved any earlier open item (look up by code-change scope or by explicit reference in the deviation log), move that item from `## Open Items` to the `## Resolved` table with `Resolved in: Phase N`.
6. Derive each category's Open count from its item headings under `### Open Items` and its Resolved count from matching IDs under `### Resolved`. Assert that every `### Summary` cell equals the derived total. Hard-stop on any mismatch; do not rewrite or finalize a file whose table cannot be proven from its headings.
7. Update the file-level `Last updated` to today's date.
8. Do **not** finalize the file here - that is `/wrap-up-session`'s job at version bump.

### Sweep (during `/wrap-up-session` Phase 4)

1. Re-read `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/known-gaps.md` and the current patch's `## v<MAJOR>.<MINOR>.<PATCH>` subsection. Create the file (status `in-progress`) and/or the patch subsection if either does not exist.
2. Mine the live session conversation for items not already captured during `/implement-phase`. Look for: "we'll come back to", "TODO", "deferred", "skipped", "good enough for now", suppressed warnings, hand-rolled mocks left in production code, stubbed-out functions, commented-out tests, partial implementations marked as such in chat.
3. Add any new items using the same ID allocation rules as Append. Cite the originating session (date) in the `Reason` field when the item came from chat rather than from a plan deviation.
4. Derive and assert the current patch section's `### Summary` table from the `### Open Items` and `### Resolved` headings. Hard-stop on mismatch.
5. Update the file-level `Last updated` to today's date.

### Finalize (during `/wrap-up-session` Phase 6 if a version bump occurs)

1. After `/update-version` completes successfully, edit the file's `Status:` line to `finalized`.
2. Append a one-line note immediately after the Summary table:

    > Finalized on <YYYY-MM-DD> at the <new-version> bump. Open items will be ingested by `/generate-plan` when the next version's plan is created.

3. Do not delete or move resolved items - the file is now an archived record. Anything still in `## Open Items` remains there for the next-version ingest step to pull forward.

### Ingest (during `/generate-plan` Step 0.6)

1. Resolve the prior version: the immediately previous semver tag (for a `v0.2.0` plan, look at `v0.1.0`).
2. Build the candidate file list:
    - The prior version's `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/known-gaps.md` (resolve its minor dir per the Version-directory resolution) - always include if it exists.
    - Any older in-progress known-gaps file, matching both the two-level `docs/v*/v*/known-gaps.md` and the legacy flat `docs/v*/known-gaps.md` globs, whose `Status:` is still `in-progress` (gaps that lingered across more than one version).
3. Parse all candidate files. Merge their `## Open Items` into a single in-memory list, tagged with the originating version.
4. If the merged list is non-empty, follow the active instruction template's `Consequential Decisions` rule, then show the user a compact summary and ask how to handle them:

    ```
    Found N open items from prior versions:

    From v0.1.0 (finalized):
      [NI-2] Settings panel keyboard shortcuts not wired (Phase 4)
      [BG-1] Token refresh race condition (Phase 6)

    From v0.0.5 (still in-progress):
      [MT-3] tests/integration/payment_flow.py below 60% coverage

    How should I treat these in the new plan?
      A. Ingest all open items as scope (recommended)
      B. Pick a subset to ingest
      C. Skip - I will handle them outside this plan
    ```

5. Selected items are seeded into the discovery interview at Q2 (Scope) and Q3 (Affected Areas). They become tagged sub-tasks in Step 4 with the prefix `[from <prior-version> known-gaps: NI-2]`. Each Step 4 sub-task `Prompt` block must restate the original `Reason` and `Suggested next step` so the executable prompt is self-contained.
6. After the new plan file is written, edit each ingested item in its source `known-gaps.md`: move it from `## Open Items` to the `## Resolved` table with `Resolved in: transferred to <new-version> plan`. Items are not yet *fixed* - just transferred to a different tracking surface.

## Monotonic Scrutiny Across Cycles

Any durable record carried across review, hunt, or implementation cycles may only RAISE attention. It stores no "this was checked and is fine" signal, never deprioritizes an item because a prior cycle placed it out of scope, and never excludes an item from re-examination. Prior work is a PRIORITY and RECHECK signal, never a coverage claim.

This invariant makes stale or wrong memory fail safely. Because a carried signal can only add effort, a bad record can waste budget by causing a redundant recheck, but it cannot silently remove work. The opposite design lets a stale "already handled" entry reduce attention; the skipped re-examination then leaves no visible failure artifact.

Apply the invariant whenever this skill feeds another cycle: an ingested gap may raise ordering or urgency, but the receiving plan must re-establish current scope, coverage, evidence, and disposition from the current revision. Moving an item to `Resolved` records its lifecycle state in this tracker; it does not authorize a later security review to omit the component or finding.

This phase adopts doctrine only. A separate durable cross-run scrutiny store is explicitly deferred on effort and must be tracked as future work; do not build or imply that store as part of this skill change.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll just remember to fix this in the next session" | The next session is in a different conversation; the gap will be lost. The file is the only durable channel between sessions. |
| "It's already in the devlog" | The devlog is chronological narrative. `known-gaps.md` is structured, queryable, and ingested by `/generate-plan` automatically. The two complement each other. |
| "I'll add it to docs/todos.md instead" | `docs/todos.md` is forward-looking and manually maintained; it does not flow into `/generate-plan` automatically. Use `known-gaps.md` for items that came out of an actual implemented phase. |
| "This warning isn't really a gap" | If a future version would benefit from fixing it, it is a gap. Record at the appropriate severity - `WN` is fine for low-impact items. Better to over-record and let `/generate-plan` Step 0.6's "pick a subset" option filter than to lose the signal entirely. |
| "I already wrote this up in the session history" | Session-history files are per-session, not per-version. The known-gaps file aggregates across every phase of a single version and is the only artifact `/generate-plan` reads to pull work forward. |
| "A prior cycle marked this safe, so the next review can skip it" | A prior result may be stale against the current revision or scope. Cross-cycle memory may raise priority and require a recheck, but it can never serve as current coverage or suppress examination. |
| "We will never do this, so I will log it as DF in known-gaps" | Deferred still means later. Never-do belongs in `docs/policy/out-of-scope/<topic-slug>.md`. A DF row here would be ingested by `/generate-plan` as candidate scope. |

## Verification

- [ ] `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/known-gaps.md` exists with a single file-level header (`Project`, `Status`, `Last updated`) and one `## v<MAJOR>.<MINOR>.<PATCH>` subsection per implemented patch release (a new patch appends a subsection, never overwriting the header or a prior patch's items).
- [ ] Every open item has all four fields: `Source phase`, `Plan reference`, `Reason`, `Suggested next step`.
- [ ] Each patch subsection's `### Summary`-table counts match the actual number of items in that subsection (compute, do not estimate).
- [ ] Summary counts were derived from Open Items and Resolved headings and asserted equal; any mismatch stopped the workflow before write or finalization.
- [ ] After `/wrap-up-session` runs on a version bump, `Status:` reads `finalized` and the version-bump note is present immediately after the Summary table.
- [ ] When `/generate-plan` ingests items, the corresponding entries in the source file have moved from `## Open Items` to `## Resolved` with `Resolved in: transferred to <new-version> plan`.
- [ ] Item IDs are not reused: a resolved `NI-3` does not become a new `NI-3` later.
- [ ] Any cross-cycle record is used only to raise priority or require re-examination; no prior "safe", out-of-scope, or resolved state suppresses current coverage work.
- [ ] The durable cross-run scrutiny store is recorded as deferred work and was not built or implied by this doctrine-only change.
- [ ] Never-do items were routed to `docs/policy/out-of-scope/<topic-slug>.md`, not appended as known-gaps `DF` rows.

## Related Skills

- [[dev-progress-tracker]] -- maintains `docs/todos.md` (forward-looking sprint roadmap); known-gaps is the per-version archive companion that records what slipped.
- [[session-history]] -- retrospective per-session record; known-gaps is a structured punch-list aggregated across sessions of the same version.
- [[version-upgrade]] -- the version-bump operation that triggers known-gaps finalization.
- [[implementation-plan]] -- generates the plan that known-gaps eventually feeds into for the next version.
- `docs/policy/docs-retention.md` -- the per-version documentation lifecycle. `known-gaps.md` is explicitly EXEMPT from archival: it is read forward by the next version's plan, so it stays in the active tree even after that version's `development/` subtree is archived.
- [[solution-knowledge-base]] -- when a `BG` (bug) gap is resolved with a non-trivial root cause, or an item is closed with a hard-won insight, graduate it into a durable `docs/solutions/<category>/<slug>.md` entry so the fix becomes grounding for future planning and review. Moving the item to `## Resolved` records *that* it was fixed; the solution doc records *how*, retrievably.
- `docs/policy/out-of-scope/README.md` -- the never-do register. Route declined features there; this tracker stays the do-later log.
