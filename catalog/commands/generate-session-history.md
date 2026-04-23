---
description: Document the current development session (or reconstruct history from past sessions) as a comprehensive Markdown file capturing chronological steps, troubleshooting, assumptions, testing results, and next steps.
---

# Generate Session History Command

Generate a comprehensive, standalone Markdown history file that documents everything accomplished in a development session. The file captures what was done, what was troubleshot, what assumptions were made, what was tested, and what remains to be done.

This command operates in two modes:
-   **Session mode** (default): Document the current chat session using live conversation context as the primary source, supplemented by git changes and the implementation plan.
-   **Retrospective mode**: Reconstruct history from archived AI session files, git history, DEVLOG.md, CHANGELOG.md, and planning documents when the original conversation is no longer available.

The command works on all AI platforms — Claude Code, Codex, Gemini CLI, and GitHub Copilot — by adapting its source collection to the tools available in each environment.

## Phase 1: Detect Mode and Scope

1.  **Read the user's invocation** to determine the operating mode:
    *   If invoked with no qualifier, or with "this session", "current session", or at the end of a chat session: set to **session mode** (default).
    *   If invoked with "retrospective", "full history", "all phases", or referencing a past date or phase not worked on in this session: set to **retrospective mode**.
    *   If the prompt references a specific phase by name or number (e.g., "phase 2", "the authentication work"): set to **single-phase mode** within whichever mode applies.
    *   If ambiguous, ask the user:

        ```
        How would you like to generate the session history?

        1. Current session — document what we worked on in this chat session
        2. Single past phase — reconstruct history for one specific phase
        3. Full project history — generate one file per phase from all available sources
        ```

    *   Wait for the user's answer before continuing.

2.  **Session mode inputs** — ask for the following with sensible defaults:

    | Input | Default | Notes |
    |---|---|---|
    | Session title / phase name | Infer from branch name or first commit subject | Used for the file header and filename |
    | Operator name | `git config user.name` | Appears in the file header |
    | Implementation plan path | Search for `*plan*`, `*implementation*` in `docs/`, `tasks/`, project root | Optional; enables TODO tracking and plan cross-referencing |
    | Session start point | "today" | Accept: commit hash, ISO timestamp, "today", or branch creation point |

    Present the defaults and ask: "Are these correct, or would you like to change any?" Wait for confirmation.

3.  **Retrospective mode scope** — determine whether to generate for a single phase or the full project:
    *   If the prompt references a specific phase, set to single-phase mode and skip to Phase 3.
    *   Otherwise, ask:

        ```
        Would you like to generate history for:
        1. Full project — one file per phase for the entire project
        2. Single phase — history for one specific phase only
        ```

## Phase 2: Source Material Collection

Gather every available source before attempting synthesis. Do not skip sources because they seem empty — note their absence explicitly instead.

1.  **Live conversation context** (session mode only):
    *   Review the current chat session for:
        *   Subtasks worked on and their outcomes
        *   Errors encountered and their full error messages or stack traces
        *   Troubleshooting attempts: what was tried, what failed, what ultimately worked
        *   Assumptions stated explicitly ("I'm assuming X") or implied (choosing a version, skipping a step)
        *   Decisions made and alternatives rejected
        *   Test results: pass/fail output, error messages, coverage numbers
        *   Manual steps performed outside the AI session
    *   This is the primary and richest source in session mode.

2.  **AI session files** (retrospective mode, or supplementary in session mode):
    *   **Claude Code**: list `~/.claude/projects/` subdirectories (each is a project hash); for the directory matching the current repository, read all `*.jsonl` files. Extract assistant and user turns, tool calls, and file edits.
    *   **Codex (OpenAI CLI)**: check `~/.codex/` and `~/.openai/` for session logs, history files, or any `codex_history*` file.
    *   **Gemini CLI**: check `~/.gemini/` and `~/.config/gemini/` for session logs or `*.jsonl` history files.
    *   **GitHub Copilot**: check `.vscode/chatHistory.json` and scan the workspace root for `copilot-session*.md` or `copilot-export*.md` files.
    *   For each platform, record: sessions found (count), date range covered, and whether content is readable.

3.  **Git history**:
    *   **Session mode**:
        *   `git log --since="<session-start>" --format="%H|%ai|%an|%s" --reverse` on the current branch
        *   `git diff --stat` for file change summary
        *   `git diff --name-only` for the full list of modified files
        *   `git branch --show-current` and `git log --oneline <base>..HEAD` for branch context
        *   If `gh` CLI is available: `gh pr list --head <branch> --json number,title,url,state` for PR state
    *   **Retrospective mode**:
        *   `git log --format="%H|%ai|%an|%s" --reverse` for the full commit timeline
        *   `git tag -l --sort=version:refname` for version milestones
        *   `git log --all --oneline --graph --decorate` for timeline overview
        *   For merge commits and tagged commits: `git show --stat <hash>` to understand scope

4.  **Existing documentation**:
    *   Read `docs/DEVLOG.md` (if present) — richest source of troubleshooting trails and session summaries
    *   Read `CHANGELOG.md` (if present) — version boundaries and feature summaries
    *   Read `README.md` — project context and stated feature scope
    *   Search for ADR files in `docs/adr/`, `docs/decisions/`, `catalog/memory/decisions.md`, and `.claude/memory/decisions.md`

5.  **Planning and phase files**:
    *   Primary location: plans produced by `/generate-plan` live at `docs/<version>/plans/<slug>.md`. Search `docs/**/plans/*.md`.
    *   Legacy location: pre-rename plans live at `docs/<version>/implementation-plan.md`. Search `docs/**/implementation-plan.md` for backwards compatibility.
    *   Other planning artifacts: `PLAN.md`, `roadmap.md`, and any file matching `*plan*`, `*phase*`, or `*milestone*` under `docs/`, `tasks/`, or the project root.
    *   Read any `docs/*/analysis.md` files (output of the `analyze-codebase` command).
    *   Note each planning file found — these are primary inputs to Phase 3.

6.  **Code annotations**:
    *   **Session mode**: Search for `TODO`, `FIXME`, `HACK`, `WORKAROUND`, `XXX` in files modified during the session (`git diff --name-only` as the file list)
    *   **Retrospective mode**: Search across the entire codebase
    *   These encode decision context and dead-end signals critical for the Troubleshooting and Assumptions sections

7.  **Existing session history files**:
    *   Check `docs/*/development/history/` for prior session files
    *   These provide context for the "Starting State" section and "Prior session reference" field

8.  **Source inventory** — report to the user before continuing:

    ```
    Sources collected:
    - Conversation context:  [available / not available (retrospective mode)]
    - AI session files:      [Claude: N files / Codex: N / Gemini: N / Copilot: N / none found]
    - Git commits:           N commits (session window: YYYY-MM-DD to YYYY-MM-DD)
    - Branches/PRs:          [current branch: <name>, open PRs: <list or none>]
    - DEVLOG.md:             [present / absent]
    - CHANGELOG.md:          [present / absent]
    - Planning files:        [list names, or "none found"]
    - Prior session history: [list files, or "none found"]
    - Code annotations:      N TODO/FIXME/HACK markers in modified files
    ```

## Phase 3: Phase Boundary Detection and Plan Cross-Reference

### Session Mode

1.  If a planning file was found, read it and identify the phase/subtask structure relevant to this session's work.
2.  Present the detected phase and its subtasks to the user for confirmation:

    ```
    I found this implementation plan: [file path]

    Based on today's work, this session appears to cover:
    Phase [N]: [Phase name]

    Subtasks:
    1. [Subtask name] — [status: completed / in progress / not started]
    2. [Subtask name] — [status]
    ...

    Is this correct? (Y / edit the list)
    ```

3.  If no planning file was found, derive structure from conversation topics and git commits. Group related work into logical blocks and present them as the proposed section structure for Chronological Steps.

### Retrospective Mode

1.  **If planning files were found**:
    *   Read each planning file and extract the phase list (names, goals, date ranges if present).
    *   Present the discovered phases to the user for confirmation:

        ```
        I found the following phases in [file name]:

        1. [Phase name] — [brief goal from plan]
        2. [Phase name] — [brief goal from plan]
        ...

        Do these phases look correct?
        A. Yes, use these phases as-is
        B. Edit the list — tell me which phases to add, remove, or rename
        C. Ignore the plan and define phases manually
        ```

    *   Wait for the user's response and apply edits before continuing.

2.  **If no planning files were found**:
    *   Infer phases from git tags and CHANGELOG version boundaries.
    *   If git tags exist, propose one phase per version band (e.g., "v0.1-v0.3: Initial Setup").
    *   If no tags exist, propose phases by calendar quarter or by major commit-theme clusters.
    *   Present the inferred phases using the same confirmation prompt.

3.  **In single-phase mode**: confirm the target phase with the user — show its inferred date range and source commit count. Ask: "Is this the correct phase? If not, describe the correct one."

## Phase 4: Resolve Version and Output Path

1.  **Detect project version** using the standard resolution order:
    *   Check `CHANGELOG.md` for the most recent version heading (e.g., `## [1.2.0]`)
    *   If absent, check `package.json` (`version` field), `pyproject.toml`, `Cargo.toml`, or equivalent manifest
    *   If no version is found anywhere, use `vUnknown` and note the fallback in the output summary

2.  **Construct the output path**:
    *   Base directory: `docs/<version>/development/history/`
    *   **Session mode filename**: `<YYYY-MM>_<kebab-phase-or-session-title>.md`
        *   Example: `docs/v1.2.0/development/history/2026-03_phase-1-security-and-bug-fixes.md`
    *   **Retrospective mode filename**: `<YYYY-MM>_phase-NN-<kebab-phase-name>.md`
        *   Example: `docs/v1.2.0/development/history/2026-03_phase-02-authentication.md`

3.  **Check for existing files**: if any target files already exist, warn the user and ask:

    ```
    The following history files already exist:
    - [list paths]

    How should I handle them?
    O = Overwrite all
    S = Skip existing (only write new files)
    U = Update — merge new content into the existing file
    ```

## Phase 5: Generate Session History File(s)

For each phase or session in scope, synthesize all source material collected in Phase 2 using the template from the `session-history` skill. Work through all sources for the relevant time window.

Produce each file using this exact structure:

```markdown
# Development Log: [Phase Name or Task Name]

**Date**: YYYY-MM-DD [or range: YYYY-MM-DD to YYYY-MM-DD]
**Operator**: [Name]
**Assisted by**: [AI model and platform]
**Objective**: [1-2 sentences from plan or user description]
**Outcome**: [1-2 sentence summary of what was achieved, version tags if applicable]

---

## 1. Starting State

- **Branch**: `<branch>` [ahead of `<base>` by N commits]
- **Starting tag/commit**: `<ref>`
- **Environment**: [OS, runtime versions, relevant tools/containers]
- **Prior session reference**: [path to previous session history file, or "first session"]
- **Plan reference**: [path to implementation plan, or "no plan file"]

Context: [2-3 sentences on what motivated this session's work, referencing reviews, bug reports, or plan objectives]

---

## 2. Chronological Steps

### 2.1 [Subtask name from plan, or descriptive title]

**Branch**: `<branch>` | **PR**: #NNN | **Merged to**: `<target>`

**Plan specification**: [What the plan/task said to do, if a plan exists]

**What happened**: [Narrative of what was implemented, key decisions made]

**Key files changed**: `file1.py`, `file2.ts`

**Troubleshooting**: [If issues occurred]
- **Problem**: [What broke, with actual error messages]
- **Attempted**: [What was tried first]
- **Root cause**: [Why it happened]
- **Resolution**: [What fixed it]

**Verification**:
```bash
[command and output showing success]
```

---

### 2.2 [Next subtask]
...

[Additional subsections for lint fixes, dependency updates, version bumps, and other supporting work that arose during the session]

---

## 3. Verification Gate

| Check | Result |
|---|---|
| [Specific test suite or command] | PASS / FAIL / NOT RUN |
| [Lint check] | PASS / FAIL / NOT RUN |
| [Build check] | PASS / FAIL / NOT RUN |
| [Integration test] | PASS / FAIL / NOT RUN |
| [Custom acceptance check from plan] | PASS / FAIL |

---

## 4. Known Issues

| Issue | Severity | Decision |
|---|---|---|
| [Issue description] | [P0/P1/P2/Cosmetic] | [Deferred to Phase N / Accepted / Workaround applied] |

(or: "None identified during this session.")

---

## 5. Plan Discrepancies

- [Deviation from original plan and why it was necessary]
- [Task that was added/removed/reordered vs the plan]

(or: "None; all work followed the implementation plan.")

---

## 6. Assumptions Made

- **[Assumption]**: [Why it was made and potential impact if wrong]
- **[Implicit assumption]**: [E.g., "Chose library X version Y because Z; not specified in plan"]

---

## 7. Testing Summary

### Automated Tests
- [Test suite name]: X passed, Y failed, Z skipped
- [Other suite]: ...

### Manual Testing Performed
- [What was manually verified and the result]

### Manual Testing Still Needed
- [ ] [Scenario that should be manually verified before declaring the phase complete]
- [ ] [Edge case requiring specific data or environment]
- [ ] [User-facing workflow that should be exercised end-to-end]

---

## 8. TODO Tracker

### Completed This Session
- [x] [Subtask from plan or derived task]
- [x] [Subtask from plan or derived task]

### Remaining (Not Started or Partially Done)
- [ ] [Subtask with notes on current state]
- [ ] [Subtask not yet started]

### Out of Scope (Deferred)
- [ ] [Item explicitly deferred to a later phase, with reason]

---

## 9. Summary and Next Steps

[2-4 sentence summary: what was the objective, what was achieved, what is the state of the codebase now]

**Next session should**:
1. [First priority]
2. [Second priority]
3. [Third priority]
```

**Synthesis rules**:
*   **Cross-reference** conversation context with git commits by timestamp for chronological accuracy.
*   **Populate troubleshooting** from conversation errors, DEVLOG entries, and FIXME/HACK comments introduced during this session.
*   **Flag thin evidence**: *(Inferred from commit messages only)* or *(No conversation data for this step)* or *(Reconstructed from git history; no session data available)*.
*   **Never fabricate**. If a section cannot be populated from evidence, state so explicitly rather than omitting it.
*   **Assumptions**: capture both explicit ("I'm assuming X") and implicit (library version choice, skipped test, environment constraint).
*   **Manual testing suggestions**: prioritize user-facing workflows, external service integration, and data-dependent edge cases that automated tests cannot cover.
*   **TODO tracker**: align with the plan's subtask list; mark items as completed, remaining, or deferred with notes.
*   **Source attribution** (retrospective mode): note the evidence source for each section — *(from git)*, *(from Claude Code session)*, *(from DEVLOG)*, etc.

## Phase 6: Write and Summarize

1.  Create the output directory if it does not exist: `docs/<version>/development/history/`
2.  Write each generated file to its resolved path. If overwriting, confirm the action.
3.  Output a summary in chat:

    ```
    Session history generated:
    - File(s) written:         [full paths]
    - Version:                 <version> (from <source>)
    - Phase/session:           [name]
    - Date range:              YYYY-MM-DD to YYYY-MM-DD
    - Sources used:            [list which sources contributed]
    - Subtasks completed:      N/M
    - Low-confidence sections: [list, or "none"]
    - Known issues documented: N
    - Manual testing items:    N
    ```

4.  Ask: "Would you like to review or refine any section, or are there gaps I should attempt to fill from additional sources?"

## Phase: Iterative Refinement (Loop)

**CRITICAL**: This is an iterative process. You cannot assume the first pass is perfect.
Perform the following refinement loop up to **3 times** (or as specified by the user's input, e.g., "5 iterations"):

1.  **Analyze**: Look at the generated output.
    *   Does every section have content or an explicit "None" / "N/A" note?
    *   Are Chronological Steps in strict chronological order with dates sourced from git?
    *   Does every troubleshooting entry include the actual error message (not just "there was an error")?
    *   Are assumptions written as assumptions — with impact analysis — not just descriptions of choices?
    *   Does the TODO Tracker match the plan's subtask list (if a plan was provided)?
    *   Is the Verification Gate table populated for every check that was actually performed?
    *   Is the file standalone — readable months later without access to the conversation?
    *   Are low-confidence sections explicitly flagged rather than silently omitted?
2.  **Refine**:
    *   Cross-reference thin sections against additional source material not yet consulted.
    *   Merge duplicate timeline entries that represent the same event.
    *   Sharpen troubleshooting entries by rechecking conversation context for exact error messages.
    *   Add missing git commit references to Chronological Steps.
3.  **Stop**:
    *   If you are confident the result is excellent.
    *   OR if you have reached the maximum iteration count.
