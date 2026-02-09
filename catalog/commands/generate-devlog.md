---
description: Generate a complete DEVLOG.md from the repository's git history, documentation, and code comments.
---

# Generate DevLog Command

Generate a comprehensive `DEVLOG.md` file containing the entire development history of this repository, derived from git commits, existing documentation, and code artifacts.

## Objective

Create a durable knowledge base that enables developers and AI assistants to quickly answer: "Has this been tried before? What happened? What should I try differently?"

Unlike `update-devlog` (which appends a single entry for the most recent session), this command generates the **entire** development log from scratch.

## Process

### Phase 1: Source Material Collection

1.  **Git History Analysis**:
    *   Run `git log --all --oneline --graph --decorate` to get a high-level overview of the project timeline.
    *   Run `git log --format="%H|%ai|%an|%s" --reverse` to get all commits chronologically.
    *   Run `git tag -l --sort=version:refname` to identify version milestones.
    *   For significant commits (merge commits, tagged commits, large diffs), run `git show --stat <hash>` to understand scope.

2.  **Documentation Scan**:
    *   Read `CHANGELOG.md` (if present) for version-based change summaries.
    *   Read `README.md` for project context and evolution clues.
    *   Read any existing `DEVLOG.md` to understand prior format and content.
    *   Read `tasks/todo.md` and `tasks/lessons.md` (if present) for planning history and captured lessons.

3.  **Code Artifact Scan**:
    *   Search for `TODO`, `FIXME`, `HACK`, `WORKAROUND`, `XXX` comments across the codebase. These often encode decision context.
    *   Identify any `docs/`, `guides/`, or `ADR` directories for architectural decision records.

4.  **PR/MR Context** (if accessible):
    *   If the repository is hosted on GitHub, run `gh pr list --state merged --limit 100 --json title,body,mergedAt,number` to gather pull request descriptions and review context.
    *   If not accessible, note this as a gap and proceed with git-only sources.

### Phase 2: Timeline Synthesis

1.  **Group Commits into Logical Units**:
    *   Cluster commits by date and related scope (same files, same feature branch, same tag).
    *   Use merge commits and tags as natural boundaries between logical units.
    *   A single devlog entry should represent a coherent unit of work (e.g., "implemented auth token refresh"), not individual commits.

2.  **Cross-Reference Sources**:
    *   Match CHANGELOG entries to git commit clusters for richer context.
    *   Match PR descriptions to commit ranges for "why" and "decisions" context.
    *   Match TODO/FIXME/HACK comments to the commits that introduced them for troubleshooting context.

3.  **Determine Entry Granularity**:
    *   **Tags/releases**: Always get their own entry.
    *   **Feature branches**: Group into one entry per feature.
    *   **Consecutive small fixes**: May be combined into a single "maintenance" entry if they share a date and theme.
    *   **Large refactors**: Get their own entry even if no tag exists.

### Phase 3: Entry Generation

For each logical unit (reverse chronological order, newest first), generate an entry using the following structure:

```markdown
## [YYYY-MM-DD HH:MM] — [Short Descriptive Title] [category-tag]

### What Changed
Concise summary of changes: features, fixes, refactors, dependency updates.

*   Modified `path/to/file`: Brief description
*   Added `path/to/new-file`: Purpose
*   Deleted `path/to/old-file`: Reason

### Why It Changed
Motivation, triggering issue, or requirement. Reference issue numbers or user reports.

### Decisions Made
*   **Chose X over Y**: Reasoning
*   **Rejected Z**: Reasoning

### Troubleshooting Trail *(if applicable)*

<details>
<summary>Expand troubleshooting details</summary>

*   **Attempt 1**: What was tried
    *   *Result*: Failed
    *   *Error*: `error message`
    *   *Analysis*: Why it failed
*   **Attempt 2 (Solution)**: What worked
    *   *Key Insight*: What made the difference

</details>

### Impact & Context
*   **Affected**: `module-a`, `module-b`
*   **Downstream**: Effects on other parts of the system
```

**Category tags**: `[feature]`, `[bugfix]`, `[refactor]`, `[decision]`, `[infra]`

**Section guidance**:
*   **What Changed**: Map directly to git diffs. List specific files where possible.
*   **Why It Changed**: Capture intent that is often lost in commit messages.
*   **Decisions Made**: Include rejected alternatives with reasoning (lightweight ADR entries).
*   **Troubleshooting Trail**: Use collapsible `<details>` sections. This is the highest-value section for AI assistants trying to avoid repeated dead ends.
*   **Impact & Context**: Scope the blast radius of changes.

### Phase 4: Assembly and Formatting

1.  **File Header**:
    ```markdown
    # Development Log

    > A comprehensive record of this project's development history.
    > For AI assistants: use this file to understand what has been tried, what worked, what failed, and why.
    > Generated by the `generate-devlog` command. Maintained incrementally via `update-devlog`.
    ```

2.  **Assemble Entries**:
    *   Order entries in **reverse chronological** order (newest first).
    *   Ensure date headings use consistent `## [YYYY-MM-DD HH:MM]` format.
    *   For entries where exact time is unknown, use `00:00` as placeholder.

3.  **Write Output**:
    *   Write the complete content to `DEVLOG.md` in the repository root.
    *   If `DEVLOG.md` already exists, **warn the user** before overwriting. Offer to back up the existing file as `DEVLOG.backup.md`.

4.  **Handle Edge Cases**:
    *   **Very large repositories (1000+ commits)**: Focus on tagged releases and merge commits. Group maintenance commits into monthly summaries.
    *   **Repositories without tags**: Use date-based grouping (weekly or bi-weekly clusters).
    *   **Missing context (no CHANGELOG, no PRs)**: Flag entries as `*(Inferred from commit messages only)*`.
    *   **Squash-merged repositories**: Each squash-merge commit becomes one entry.

5.  **Summary**:
    *   After generation, output a chat summary:
        ```
        Generated DEVLOG.md with X entries spanning Y months.
        Covered: Z commits, W tags/releases.
        Sources used: git history, CHANGELOG.md, [other sources found].
        ```


## Phase: Iterative Refinement (Loop)

**CRITICAL**: This is an iterative process. You cannot assume the first pass is perfect.
Perform the following refinement loop up to **3 times** (or as specified by the user's input, e.g., "5 iterations"):

1.  **Analyze**: Look at the generated output.
    *   Is it complete? Does every tagged release have an entry?
    *   Are entries in strict reverse chronological order?
    *   Are category tags consistently applied?
    *   Do troubleshooting trails use collapsible `<details>` sections?
    *   Does the file header include purpose statement and maintenance guidance?
2.  **Refine**:
    *   Fix any issues found.
    *   Add missing components.
    *   Enrich entries with additional context from cross-referenced sources.
3.  **Stop**:
    *   If you are confident the result is excellent.
    *   OR if you have reached the maximum iteration count.
