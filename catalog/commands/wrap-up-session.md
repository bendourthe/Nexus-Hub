---
description: Wrap up a development session — capture session history while context is live, clean up the codebase, sync documentation, update the devlog, refresh memory, optionally bump the version, and produce a wrap-up commit message.
---

# Wrap-Up Session Command

Close out a development session cleanly. The command triages what happened in the session, runs the right subset of cleanup and documentation steps in the correct order, and ends with a commit message ready for your review.

## Invocation

```
/wrap-up-session             # interactive — triage runs first
/wrap-up-session --quick     # skip refactor-project-layout and version prompt
```

---

## Phase 0: Session Triage

1. **Assess the current state** — run the following read-only checks:
   - `git status` — uncommitted files and staged changes
   - `git log --oneline --since="$(git log -1 --format=%ci HEAD~10 2>/dev/null || echo '24 hours ago')"` — commits made in this session
   - Scan for new directories that may need `.gitignore` entries (build outputs, caches, generated files)
   - Check whether any active implementation plan exists under `docs/`

2. **Build the default scope** — toggle each step based on what was found:

   | Step | Default | Condition |
   |------|---------|-----------|
   | `generate-session-history` | ON | always |
   | `update-gitignore` | ON | always |
   | `refactor-project-layout` | **OFF** | enable only if explicitly requested |
   | `update-documentation` | ON | always |
   | `update-devlog` | ON | always |
   | `known-gaps sweep` | ON | always (skill: `known-gaps-tracker`) |
   | `manage-memory` | ON | always |
   | `update-version` | ON if commits exist since last tag, OFF otherwise | based on git tags |
   | `generate-commit-message` | ON | always |

3. **Display the pre-flight summary** and wait for the user to confirm or adjust:

   ```
   Session wrap-up scope:

     Branch:           main
     Uncommitted:      3 files
     Commits this session: 2

   Steps to run:
     [ON]  generate-session-history   (captures live conversation context — do this first)
     [ON]  update-gitignore           (new artifacts detected: dist/, .cache/)
     [OFF] refactor-project-layout    (opt-in — enable if layout cleanup is needed)
     [ON]  update-documentation       
     [ON]  update-devlog              
     [ON]  known-gaps sweep           (mine session for uncaptured deferred work / bugs / warnings)
     [ON]  manage-memory              (refresh project memory for next session)
     [ON]  update-version             (recommend: PATCH — 4 commits since v0.9.2)
     [ON]  generate-commit-message    (produce a wrap-up commit message for review)

   Proceed with this scope? (confirm, or tell me which steps to add/remove)
   ```

   Do **not** run any command until the user confirms.

---

## Phase 1: Session History (run FIRST — while conversation context is live)

Run `/generate-session-history`.

**Why first**: this skill mines the live conversation. Running it after codebase changes reduces the fidelity of what it can capture. Always execute it before touching any files.

The session history must include:
- What was implemented or changed during this session
- Key decisions and the reasoning behind them
- Deviations from any active implementation plan (if one exists)
- Test results: pass/fail counts and coverage percentage
- Known issues or unresolved blockers
- Explicit decisions and implicit assumptions
- TODOs discovered or deferred during the session
- Recommended starting point for the next session

**Output path logic**:
- If `docs/<version>/development/history/` exists → write to `docs/<version>/development/history/<YYYY-MM-DD>_session.md`
- If `docs/` exists but no versioned history directory → write to `docs/session-history/<YYYY-MM-DD>_session.md`
- If no `docs/` directory → write to `<project-root>/session-history/<YYYY-MM-DD>_session.md`

---

## Phase 2: Codebase Hygiene

Run each enabled step in order. Wait for each to fully complete before starting the next.

### Step 2a: `/update-gitignore` (runs if enabled)

- Audit new build artifacts, cache directories, and generated files created this session.
- Add any missing ignore patterns.
- Report a summary: N patterns added, N already covered.

### Step 2b: `/refactor-project-layout` (runs only if enabled in Phase 0)

- Reorganize root-level files according to standard layout conventions.
- Repair all cross-file references after any moves.
- **Safety check**: if the operation would move more than 10 files, pause and present the full list of proposed moves before executing. Wait for confirmation.

---

## Phase 3: Documentation Sync

Run `/update-documentation`.

- Sync README, API docs, architecture docs, and inline guides with any code changes from this session.
- Flag docs that reference removed, renamed, or significantly changed entities.
- Report: N files updated, N files already in sync.

---

## Phase 4: History and Logs

### Step 4a: `/update-devlog`

- Document: what changed this session, key decisions, any troubleshooting trail, current project status.
- Prepend to the top of `docs/DEVLOG.md` (or append if the existing file uses chronological bottom order — match the existing style).
- Create `docs/DEVLOG.md` if it does not exist.

### Step 4b: Known-gaps sweep (apply the `known-gaps-tracker` skill in Sweep mode)

Resolve the active version (most recent semver tag, or the version that owns the current plan). Open or create `docs/<version>/known-gaps.md` with `Status: in-progress`.

Mine the live session conversation for items not already captured during `/implement-phase`. Look for:

- "we'll come back to", "TODO", "deferred", "skipped", "good enough for now"
- Suppressed warnings, hand-rolled mocks left in production code, stubbed-out functions, commented-out tests
- Partial implementations the user verbally acknowledged as such
- Bugs reproduced but not fixed during the session

Append any new items using the category prefixes `NI` / `DF` / `BG` / `WN` / `MT` / `QG` and the four required fields (`Source phase`, `Plan reference`, `Reason`, `Suggested next step`). Cite the originating session date in `Reason` when an item came from chat rather than a plan deviation. Recompute the Summary table and update `Last updated`. **Do not finalize here** — that happens in Phase 6 only on a version bump.

---

## Phase 5: Memory Update

Run `/manage-memory`.

- Prune stale or contradicted project memories.
- Add new project-level facts learned this session: architectural decisions, constraints, patterns established.
- Update user preference memories if any new feedback was observed during the session.
- Report: N entries added, N updated, N removed.

---

## Phase 6: Version Assessment (conditional)

Skip this phase if `update-version` was toggled OFF in Phase 0.

1. Check `git tag -l` and `git log` to find the last release tag and count commits since it.
2. Classify commits by conventional commit prefix: `feat` → MINOR candidate, `fix` → PATCH candidate, breaking change → MAJOR candidate.
3. Present the recommendation and ask for confirmation:

   ```
   Version assessment:

     Last tag:      v0.9.2
     Commits since: 4  (2 feat, 1 fix, 1 chore)
     Recommendation: MINOR → v0.10.0

   Proceed with version bump? (Y = yes, N = skip, or type a specific version)
   ```

4. If confirmed, run `/update-version`.
5. If the user says N or types "skip", record the decision in the devlog entry and continue.

### Step 6b: Finalize known-gaps (only if `/update-version` ran successfully)

Apply the `known-gaps-tracker` skill in Finalize mode against `docs/<old-version>/known-gaps.md`:

- Edit the `Status:` line from `in-progress` to `finalized`.
- Append a one-line note immediately after the Summary table:

  > Finalized on `<YYYY-MM-DD>` at the `<new-version>` bump. Open items will be ingested by `/generate-plan` when the next version's plan is created.

- Do not delete or move resolved items — the file is now an archived record. Anything still in `## Open Items` remains there for the next-version ingest step.

If the version bump was skipped, leave `Status: in-progress` so the file is picked up by the next `/generate-plan` even before the formal version bump.

---

## Phase 7: Final Commit

Run `/generate-commit-message`.

- **Sectioned-bullet structure (CRITICAL)**: a wrap-up commit usually touches multiple artifact types (session history, devlog, documentation, gitignore, memory, optional version bump), so the body MUST use **labeled sections with bullets**, NOT multiple flowing paragraphs. After the subject line and a 1-2 sentence intro paragraph, organize the body as named sections with headers ending in a colon, each followed by contiguous bullets. Suggested section headers for a wrap-up commit: `Session history:`, `DEVLOG:`, `Documentation:`, `Gitignore:`, `Memory:`, `Version bump:` (only the ones that actually changed). If a version bump happened, add a `Tests:` section after.
- **No hard-wrapping (CRITICAL)**: every paragraph and every bullet point in the commit body and footer MUST be written as a single continuous line in the source, regardless of length. Do NOT insert line breaks at any column width (50, 72, 80, 100, etc.). The 72-char "convention" from older git tooling docs is obsolete - modern Git, GitHub, GitLab, and `git log` all soft-wrap on display. The subject line's 50-char cap is the only exception (a hard limit, not a wrap).
- **Whitespace**: exactly one blank line between sections; never two or more. Within a section, bullets are contiguous.
- Scope the message to the wrap-up artifacts produced by this command: session history file, devlog entry, documentation changes, gitignore additions, memory updates, and optional version bump.
- Suggest a commit subject in this format: `chore: wrap-up session <YYYY-MM-DD>`

The user reviews the generated message and runs `git commit` manually. This command does **not** commit automatically.

---

## Completion Report

After Phase 7, print a final summary:

```
Session wrap-up complete:

  Session history:  docs/v0.9.2/development/history/2026-04-06_session.md
  Devlog:           docs/DEVLOG.md (updated)
  Documentation:    README.md, docs/architecture.md (synced)
  Gitignore:        2 patterns added
  Known gaps:       docs/v0.9.2/known-gaps.md (3 added, status: finalized)
  Memory:           3 entries updated, 1 removed
  Version:          v0.9.2 → v0.10.0  (or: no bump — skipped)
  Commit message:   ready for your review

To start the next session cleanly, open the session history file above
or run /continue-session.
```

---

## Phase: Iterative Refinement (Loop)

**CRITICAL**: This is an iterative process. You cannot assume the first pass is perfect.
Perform the following refinement loop up to **3 times** (or as specified by the user's input, e.g., "5 iterations"):

1. **Analyze**: Look at the generated output.
   - Is it complete?
   - Are there any obvious errors?
   - Does it meet the user's requirements?
2. **Refine**:
   - Fix any issues found.
   - Add missing components.
3. **Stop**:
   - If you are confident the result is excellent.
   - OR if you have reached the maximum iteration count.
