---
name: tasks-to-issues
description: "Convert the strict task checklist in a feature directory's tasks.md (or plan.md) into linked GitHub issues via the local gh CLI. Drives /tasks-to-issues end-to-end - parses every `- [ ] T### [P?] [US?] file_path` line, builds a per-task issue payload with labels (`nexus-hub`, `spec-driven-task`, `parallel`, `user-story-N`), and either dry-runs the gh invocations or executes them sequentially after user confirmation. Use whenever the user wants to convert tasks to issues, create GitHub issues from a plan, file issues from tasks.md, dry-run the conversion to preview gh invocations, fan a plan out to issue tracking, or drive sprint planning from a generated plan. Trigger phrases include 'tasks to issues', 'convert tasks to issues', 'create issues from plan', 'file issues from tasks.md', 'issue tracking from plan', 'gh issue create from tasks', 'fan out tasks to GitHub', 'sprint from plan'. Cross-links to `[[implementation-plan]]`, `[[cross-artifact-analyzer]]`, and `[[project-constitution]]`. SKIP: project boards (use gh directly), milestone management, label creation, free-form issue authoring, plans whose tasks do NOT match the strict `- [ ] T### [P?] [US?] file_path` format (re-run /generate-plan first), or any flow that needs more than one issue per task. Version-bound documentation uses docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/; closed snapshots use docs/archives/."
summary_l0: "Convert canonical release-plan tasks into linked GitHub issues"
overview_l1: "This skill drives the /tasks-to-issues command end-to-end. It locates the active feature directory, parses every `- [ ] T### [P?] [US?] file_path` line against the strict regex, builds a per-task issue payload (title, body with file path + user-story link, labels `nexus-hub` + `spec-driven-task` + optional `parallel` + `user-story-N`), and either prints the resolved `gh issue create` invocations (--dry-run) or invokes them sequentially after user confirmation. It enforces idempotency by appending `[gh#<num>]` to each filed task line so re-runs skip converted tasks. Pre-flight checks verify gh is installed and authenticated and the directory is a GitHub repo. The mechanical parsing lives in scripts/tasks-to-issues.sh and scripts/tasks-to-issues.ps1; references/gh-cli-auth-runbook.md covers gh auth and rate-limits. Trigger phrases: tasks to issues, convert tasks to issues, create issues from plan, file issues from tasks.md, issue tracking from plan, gh issue create from tasks, fan out tasks to GitHub, sprint from plan. Version-bound documentation uses docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/; closed snapshots use docs/archives/."
---

# Tasks to Issues

Convert the strict task checklist in a feature directory's `tasks.md` (or the in-plan task list inside `plan.md`) into linked GitHub issues via the user's local `gh` CLI. The skill parses every `- [ ] T### [P?] [US?] file_path` line, builds a per-task issue payload, and either dry-runs the `gh issue create` invocations or executes them sequentially after user confirmation.

This skill is paired with the `/tasks-to-issues` command. The command file orchestrates the user-facing flow; this skill body documents the parsing rules, the payload schema, idempotency, and the failure modes.

## When to Use This Skill

- When the user wants to **convert a plan's task list into GitHub issues** for sprint planning or distributed execution.
- When the user wants to **dry-run the conversion** to inspect the `gh issue create` invocations before any are filed.
- When the user wants to **resume a partially-converted plan** -- the skill detects `[gh#<num>]` markers and skips already-filed tasks.
- When the user wants to **fan a feature out to issue tracking** so multiple engineers can pick up parallel `[P]` tasks.
- When the user asks **"file these tasks as issues"**, **"create issues from this plan"**, or **"convert tasks.md to GitHub"**.

**When NOT to use**:

- For project boards, milestones, or label creation -- use `gh` directly. This skill only creates issues.
- For free-form issue authoring (no strict task format upstream) -- author the issue directly with `gh issue create`.
- For plans whose tasks do NOT match the Phase 6 strict format (`- [ ] T### [P?] [US?] file_path`) -- re-run `/generate-plan` to regenerate with the strict format before invoking this skill.
- For one-off issues unrelated to a plan or spec -- use `[[code-commit-workflow]]` or `gh issue create` directly.

## Inputs

The skill accepts:

1. **Feature directory** (positional argument, optional). Default resolution order:
    1. `.specify/feature.json` -> `feature_directory` field, set by `/generate-plan --specs-layout`.
    2. Most recent plan under `docs/<version>/plans/` (sorted by mtime).
2. **`--dry-run`** flag (optional). When set, no `gh` invocation is made; the skill only prints the resolved `gh issue create` commands.
3. **`--repo-root`** flag (optional). Defaults to `git rev-parse --show-toplevel` then falls back to the current directory.

## Pre-flight Checks

Before any parsing or `gh` invocation, the skill verifies:

1. `gh auth status` exits 0. If not, abort with: `Install the GitHub CLI from https://cli.github.com and run "gh auth login" before re-trying.`
2. `gh repo view --json nameWithOwner -q .nameWithOwner` exits 0. If not, abort with: `Working directory does not resolve to a GitHub repo. Configure the remote with "gh repo set-default" or run from a GitHub-tracked clone.`
3. The resolved feature directory exists and contains either `tasks.md`, `plan.md`, or a single `<slug>.md` (default layout).
4. The task source file contains at least one line matching the strict regex `^- \[ \] T[0-9]{3,}( \[P\])?( \[US[0-9]+\])? .+$`. If a line starts with `- [ ]` and a `T###` token but does NOT match the regex, abort and list the offending lines so the user can re-run `/generate-plan` with the strict-format validator.

## Parsing the Task Source

Each task line is decomposed into five fields:

| Field | Source | Required? |
|---|---|---|
| Task ID | `T###` token after the checkbox | Yes |
| Parallel marker | `[P]` immediately after the task ID | No |
| User story label | `[US<n>]` immediately after the optional `[P]` | No |
| Description | Free text after the markers up to the file path | Yes |
| File path | Trailing path-like token (e.g., `src/models/user.py`) | Yes (heuristic: a substring matching `[\w./-]+\.[\w]+` or a known directory token) |

The five marker-order rules from Phase 6 apply verbatim: `[P]` precedes `[US#]`; user-story phases require `[US#]`; Setup / Foundational / Polish phases forbid `[US#]`.

When the source is `plan.md`, parse phase blocks in order to preserve the task sequence. When the source is `tasks.md`, the file is already flat -- parse line-by-line.

## Decision tickets

Some tasks hold a QUESTION whose resolution is a decision, not an implementation slice. [[implementation-plan]] marks those with a `decision:` prefix in the description.

- Keep the strict `T###` line format. Example: `- [ ] T014 decision: Which auth provider? docs/decisions/`
- Detect `decision:` at the start of the description (after markers). Add the `decision` label in addition to the usual labels.
- Title stays `[T###] decision: <question> (<file-path>)`. Body adds a line: `Kind: decision (resolve before blocked implementation issues)`.
- Do not skip these lines. They still file as one issue per task. Ordering in GitHub is not a scheduler: the plan's prerequisites remain the authority for "resolve before implementation."
- A `decision:` task may use `docs/decisions/` (or another docs path) as the file-path token. Do not invent a second regex; if the line fails the strict format, abort as today and tell the user to regenerate.

## Issue Payload

For each task, build:

1. **Title**: `[T###] <description> (<file-path>)`. Cap at 200 characters; truncate the description (not the task ID) with an ellipsis if needed.
2. **Body**: a fixed Markdown block:

    ```markdown
    Task: T###
    File: <file-path>
    Parallel: yes | no
    User story: US<n> (linked to spec heading) | n/a
    Source: <path/to/tasks.md or plan.md>

    Generated by /tasks-to-issues
    ```

    When the task carries `[US<n>]` and the feature directory contains a `spec.md` with a matching `### User Story <n>` heading, render the user-story line as a relative Markdown link: `[US<n>](../spec.md#user-story-<n>-<slug>)`.
3. **Labels**: comma-separated. Always include `nexus-hub` and `spec-driven-task`. Add `parallel` when `[P]` is present. Add `user-story-<n>` when `[US<n>]` is present. Add `decision` when the description starts with `decision:`.

The skill does NOT create labels that do not yet exist in the repo. If a label is missing, `gh issue create` emits a warning and the issue is created without the missing label. Document this in the final summary so the user can decide whether to pre-create labels via `gh label create <name>`.

## Dry-Run vs Execution

### Dry-run

When `--dry-run` is set, the skill prints one resolved `gh issue create` invocation per task, in the exact form it would otherwise run. No `gh` call is made. No source file is rewritten. The output is for inspection only.

### Execution

When `--dry-run` is absent:

1. Confirm with the user: `About to create N GitHub issues in <repo>. Continue? [y/N]`. Abort on any answer other than `y` / `Y`.
2. Invoke `gh issue create` sequentially (not parallel). Sequential execution avoids GitHub's secondary rate limit.
3. Capture the URL on stdout and the trailing issue number.
4. After each success, rewrite the source task line to append `[gh#<num>]` immediately after the task description. Save the file atomically (write to a temp file, then move) so a crash mid-rewrite leaves the source intact.
5. On any failure, stop the loop, leave the not-yet-filed tasks unmarked, and surface the failure with the remediation message: `Issue creation for T### failed -- inspect <error>. Already-created issues remain. Re-run /tasks-to-issues to file the rest.`
6. After the loop, emit the summary table: `T### | Created issue URL | Labels`. Add a final count line: `Newly created: M, Skipped (already filed): S, Failed: F.`

## Idempotency

The `[gh#<num>]` marker is the only idempotency primitive. The skill never queries GitHub to check whether an issue exists -- the marker in the local source file is authoritative. This trade-off is explicit:

- **Pro**: re-runs are O(N) local parse with zero network round-trips for already-filed tasks.
- **Con**: if the user deletes an issue in GitHub but leaves the marker in the source file, the skill will skip it. To re-file, remove the `[gh#<num>]` marker from the source line and re-run.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I will skip the dry-run -- it is just preview" | The dry-run is the only safe way to verify labels, titles, and bodies before issues are created. Skipping it means a bad payload becomes N rate-limited GitHub artifacts that have to be deleted manually. |
| "I will run this on a plan with the old free-form task list" | The strict regex from Phase 6 of `docs/archives/v2/v2.1/plans/adoption-spec-kit.md` is non-negotiable. Free-form task lines abort the parse with a list of offending lines. Re-run `/generate-plan` first. |
| "I will create the labels later, after the issues are filed" | `gh issue create` warns when a label is missing; the issue is created without the missing label. After-the-fact label creation does NOT retroactively attach the label to existing issues. Pre-create labels via `gh label create` before running. |
| "I will parallelize the gh invocations to make it faster" | GitHub's secondary rate limit on issue creation is strict. Sequential is the documented contract. Parallel runs trigger the rate limit and turn a 30-second job into a 10-minute job with retries. |
| "If a gh invocation fails I will just skip and continue" | The skill stops on first failure by design. Skipping silently means already-filed issues become orphans referencing a partial plan. The contract is: stop, report, re-run after fixing the underlying cause. |
| "A decision ticket is not a real task, I will omit it from the issue file" | Then the blocking question has no tracker row and implementation issues start without it. Keep the `T###` line, prefix the description `decision:`, add the `decision` label, and resolve it before the issues it unblocks. |

## Verification

- [ ] `gh auth status` exits 0 in the working directory.
- [ ] `gh repo view --json nameWithOwner` returns the expected repo.
- [ ] The resolved feature directory contains `tasks.md` or `plan.md` with at least one task line matching the strict regex.
- [ ] Dry-run output prints one `gh issue create ...` invocation per task; the count matches the strict-regex match count from the source file.
- [ ] In execution mode, every newly-filed task line in the source file ends with `[gh#<num>]` after the run.
- [ ] Re-running the skill on the same source file with all tasks already marked produces: `Newly created: 0, Skipped: N, Failed: 0` and zero `gh` invocations.
- [ ] The final summary table has one row per task (newly created or skipped or failed); the row count matches the strict-regex match count.
- [ ] Every source line whose description starts with `decision:` produced an issue (or dry-run invocation) that includes the `decision` label.

## Related Skills

- `[[implementation-plan]]` -- generates the strict-format task lines this skill consumes; without it, the parse aborts.
- `[[cross-artifact-analyzer]]` -- read-only audit; run it on the feature directory before filing issues to catch coverage gaps that would otherwise become orphan issues.
- `[[project-constitution]]` -- the constitution principles cited in each plan are NOT propagated into the issue bodies (issues are tactical); contributors are expected to read the constitution out-of-band.
- `[[code-commit-workflow]]` -- the commit-message convention referenced inside issue bodies when contributors link a PR back to the issue (`Closes #<num>`).
- `[[known-gaps-tracker]]` -- when an `--dry-run` shows label or coverage problems, record them in `docs/<version>/known-gaps.md` rather than papering over them in the issue body.
