---
description: Analyze all development sessions and produce one structured Markdown history file per implementation phase, saved to docs/<version>/development/history/.
---

# Generate Dev History Command

Reconstruct the full development history of this project by aggregating AI assistant session files, git history, DEVLOG.md, CHANGELOG.md, and planning documents, then generate one structured Markdown file per implementation phase.

Unlike `generate-devlog` (which produces a chronological session log), this command organizes history by **implementation phase**: each output file answers "what did we set out to build, how did we build it, what went wrong, and what was the outcome" for a bounded slice of the project. The command works on all AI platforms — Claude Code, Codex, Gemini CLI, and GitHub Copilot — by aggregating every source available in the current environment.

## Phase 1: Detect Scope

1.  **Read the user's invocation** to determine the requested scope:
    *   If the prompt references a specific phase by name or number (e.g., "phase 2", "authentication phase", "the data pipeline work"), set scope to **single-phase mode** for that phase and skip directly to Phase 3.
    *   If no phase is referenced, ask the user:

        ```
        How would you like to run generate-dev-history?

        1. Full project history — generate one file per phase for the entire project
        2. Single phase — generate history for one specific phase only
        ```

    *   Wait for the user's answer before continuing.

## Phase 2: Source Material Collection

Gather every available source before attempting synthesis. Do not skip sources because they seem empty — note their absence explicitly instead.

1.  **AI Session Files** — search for session history from each platform:
    *   **Claude Code**: list `~/.claude/projects/` subdirectories (each is a project hash); for the directory matching the current repository, read all `*.jsonl` files. Extract assistant and user turns, tool calls, and file edits.
    *   **Codex (OpenAI CLI)**: check `~/.codex/` and `~/.openai/` for session logs, history files, or any `codex_history*` file in those locations.
    *   **Gemini CLI**: check `~/.gemini/` and `~/.config/gemini/` for session logs or `*.jsonl` history files.
    *   **GitHub Copilot**: check `.vscode/chatHistory.json` and scan the workspace root for any `copilot-session*.md` or `copilot-export*.md` files.
    *   For each platform, record: sessions found (count), date range covered, and whether content is readable.

2.  **Git History**:
    *   Run `git log --format="%H|%ai|%an|%s" --reverse` to get all commits chronologically.
    *   Run `git tag -l --sort=version:refname` to identify version milestones.
    *   Run `git log --all --oneline --graph --decorate` for a timeline overview.
    *   For merge commits and tagged commits, run `git show --stat <hash>` to understand scope.

3.  **Existing Documentation**:
    *   Read `DEVLOG.md` (if present) — richest source of troubleshooting trails and session summaries.
    *   Read `CHANGELOG.md` (if present) — version boundaries and feature summaries.
    *   Read `README.md` — project context and stated feature scope.
    *   Search for ADR files in `docs/adr/`, `docs/decisions/`, `catalog/memory/decisions.md`, and `.claude/memory/decisions.md`.

4.  **Code Annotations**:
    *   Search for `TODO`, `FIXME`, `HACK`, `WORKAROUND`, `XXX` comments across the codebase. These encode decision context and dead-end signals that are critical for the Troubleshooting Trail.

5.  **Planning and Phase Files**:
    *   Search for: `PLAN.md`, `implementation-plan.md`, `roadmap.md`, any file matching `*plan*`, `*phase*`, or `*milestone*` under `docs/`, `tasks/`, or the project root.
    *   Read any `docs/*/analysis.md` files (output of the `analyze-codebase` command).
    *   Note each planning file found — these are primary inputs to Phase 3.

6.  **Source Inventory**: after collection, report to the user before continuing:

    ```
    Sources collected:
    - Claude Code sessions: X files (YYYY-MM-DD to YYYY-MM-DD)  [or: not found]
    - Codex sessions:       [found: N files / not found]
    - Gemini sessions:      [found: N files / not found]
    - Copilot sessions:     [found: N files / not found]
    - Git commits:          N commits, M tags (YYYY-MM-DD to YYYY-MM-DD)
    - DEVLOG.md:            [present / absent]
    - CHANGELOG.md:         [present / absent]
    - Planning files:       [list names, or "none found"]
    - ADRs / decision files:[list names, or "none found"]
    ```

## Phase 3: Phase Boundary Detection

1.  **If planning files were found** (from Phase 2, step 5):
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

    *   Wait for the user's response and apply any edits before continuing.

2.  **If no planning files were found**:
    *   Attempt to infer phases from git tags and CHANGELOG version boundaries.
    *   If git tags exist, propose one phase per major version band (e.g., "v0.1–v0.3: Initial Setup", "v0.4–v0.7: Core Features").
    *   If no tags exist, propose phases by calendar quarter or by major commit-theme clusters.
    *   Present the inferred phases to the user using the same confirmation prompt as above.

3.  **In single-phase mode**: confirm the target phase with the user before generating — show its inferred date range and source commit count. Ask: "Is this the correct phase? If not, describe the correct one."

## Phase 4: Resolve Version and Output Path

1.  **Detect project version** using the standard resolution order:
    *   Check `CHANGELOG.md` for the most recent version heading (e.g., `## [1.2.0]`).
    *   If absent, check `package.json` (`version` field), `pyproject.toml`, `Cargo.toml`, or an equivalent manifest.
    *   If no version is found anywhere, use `vUnknown` and note the fallback in the output summary.

2.  **Construct the output path**:
    *   Base directory: `docs/<version>/development/history/`
    *   One file per phase, named: `phase-NN-<kebab-phase-name>.md`
    *   Example: `docs/v1.2.0/development/history/phase-02-authentication.md`

3.  **Check for existing files**: if any target files already exist, warn the user and ask:

    ```
    The following history files already exist:
    - [list paths]

    Overwrite them? (Y = all / N = skip existing / A = ask per file)
    ```

## Phase 5: Generate History File(s)

For each phase in scope, synthesize all source material collected in Phase 2 using the template below. Work through all sources for the phase's time window: session turns, git commits, DEVLOG entries, planning notes, and code annotations.

Produce each file using this exact structure:

```markdown
# Phase NN: [Phase Name] — Development History

**Version scope**: vX.X.X – vY.Y.Y
**Date range**: YYYY-MM-DD to YYYY-MM-DD
**Generated**: [ISO 8601 timestamp]

---

## Overview

[2–4 sentences: what this phase aimed to accomplish and why it was a distinct unit of work.]

## Objectives

*   [Specific goal 1]
*   [Specific goal 2]

## Implementation Timeline

| Date | Event | Source |
|------|-------|--------|
| YYYY-MM-DD | [Commit message or session milestone] | git / Claude / Codex / Gemini / Copilot |

## Technical Decisions

*   **[Decision title]**: [What was decided and the reasoning. Include rejected alternatives where known.]

## Troubleshooting Trail

<details>
<summary>Expand — [N] issues documented</summary>

*   **Issue**: [Description]
    *   *Attempts*: [What was tried]
    *   *Root cause*: [Why it happened]
    *   *Resolution*: [What worked]

</details>

## Key Code Changes

*   `path/to/file`: [What changed and why — new pattern, refactor, integration point]

## Validation and Testing

[How the work in this phase was verified. Reference specific test runs, manual checks, or CI results if available in session logs.]

## Outcome and Status

*   **Achieved**: [What was completed]
*   **Deferred**: [What was scoped out or pushed to a later phase, if any]
*   **Remaining issues**: [Known bugs or gaps left at phase end, if any]
```

**Synthesis rules**:
*   Cross-reference session turns with git commit dates to build the Implementation Timeline table accurately.
*   Populate the Troubleshooting Trail from DEVLOG entries, session error messages, and `FIXME`/`HACK` comments introduced during this phase.
*   Flag sections where evidence is thin: *(Inferred from commit messages only)* or *(No session data available for this phase)*.
*   Never fabricate details. If a section cannot be populated from evidence, state so explicitly rather than omitting it.

## Phase 6: Write and Summarize

1.  Create the output directory if it does not exist: `docs/<version>/development/history/`
2.  Write each generated file to its resolved path. If a file was backed up (overwrite prompt in Phase 4), confirm: `Backed up existing file to <path>.backup.md`.
3.  Output a summary in chat:

    ```
    Generated dev history:
    - Files written: N phase file(s) to docs/<version>/development/history/
    - Version detected: <version> (from <source file>)
    - Phase(s): [list names]
    - Date range covered: YYYY-MM-DD to YYYY-MM-DD
    - Sources used: [list which sources contributed]
    - Low-confidence sections: [list flagged sections, or "none"]
    ```

4.  Ask: "Would you like to review any specific phase file, or are there gaps I should attempt to fill from additional sources?"

## Phase: Iterative Refinement (Loop)

**CRITICAL**: This is an iterative process. You cannot assume the first pass is perfect.
Perform the following refinement loop up to **3 times** (or as specified by the user's input, e.g., "5 iterations"):

1.  **Analyze**: Look at the generated output.
    *   Does every phase file have all eight sections populated or explicitly flagged as unavailable?
    *   Is the Implementation Timeline in strict chronological order with dates sourced from git?
    *   Are Troubleshooting Trail entries inside collapsible `<details>` blocks?
    *   Are Technical Decisions written as decisions — with rationale and rejected alternatives — not just descriptions of what was done?
    *   Are low-confidence sections explicitly flagged rather than silently omitted?
2.  **Refine**:
    *   Cross-reference thin sections against additional source material not yet consulted.
    *   Merge duplicate timeline entries that represent the same event.
    *   Sharpen decision rationale entries by checking adjacent DEVLOG or session context.
3.  **Stop**:
    *   If you are confident the result is excellent.
    *   OR if you have reached the maximum iteration count.
