---
name: dev-progress-tracker
description: Maintain docs/todos.md as the project's living progress tracker. Use at session start (read current state), when tasks complete (check them off), when new work is identified (add tasks), or when starting a multi-phase project (create the file).
summary_l0: "Maintain docs/todos.md as a living project progress tracker across sessions"
overview_l1: "This skill maintains docs/todos.md as a living project progress tracker. Use it at the start of any multi-session development work to read current progress, check off completed tasks, add newly identified work, and update metrics. When the file does not exist and the project spans multiple sessions or phases, create it following the dashboard + sprint/phase structure defined here. Key capabilities include session start progress review, task status updates, metrics dashboard maintenance, sprint planning, and structured multi-track progress tracking. Trigger phrases: check todos, update todos, track progress, what are we working on, where did we leave off, what's next, docs/todos.md, progress tracker."
---

# Dev Progress Tracker

Maintain `docs/todos.md` as a living, project-level progress tracker that persists across sessions and AI platforms.

## When to Use This Skill

- **Session start**: a `docs/todos.md` file exists -- read it before doing any work
- **Task completes**: check off the finished item and update any metrics at the top
- **New work identified**: add it to the appropriate section rather than keeping it in the conversation
- **New multi-phase project**: `docs/todos.md` does not yet exist -- create it following the structure below
- **Milestone reached**: update the dashboard scores/metrics to reflect current state

**Trigger phrases**: "check todos", "update todos", "where did we leave off", "what's next", "track progress", "progress dashboard", `docs/todos.md`

## What This Skill Does

`docs/todos.md` is the single source of truth for ongoing project work. It is:
- **Forward-looking only** -- completed sprints/phases belong in history files, not here
- **Platform-agnostic** -- any AI agent on any platform reads and writes the same file
- **Manually triggered** -- agents update it when explicitly asked or when the session-start rule fires; they do not rewrite it on every response

## Structure

Every `docs/todos.md` follows this three-section layout:

### Section 1 -- Dashboard (always at top)

A metrics table that is updated after each sprint, push, or milestone. Customize columns for the project type.

```markdown
# [Project Name] -- Progress Dashboard

**Branch:** `<active branch>`

---

## Scores (update after each sprint)

| Metric | Current | Target | Delta |
|--------|---------|--------|-------|
| <metric 1> | <value> | <target> | <gap> |
| <metric 2> | <value> | <target> | <gap> |
```

Common metrics by project type:
- Software/testing: code coverage %, passing test count, CI score
- Feature work: tasks done / total, open bugs, blocked items
- Research/analysis: data processed, models evaluated, accuracy

### Section 2 -- Task Roadmap

Checkboxes organized by sprint, phase, or theme. Completed items are struck through or the section header is marked `[DONE]` and collapsed.

```markdown
## Sprint / Phase N -- [short description] (target: <metric delta>)

- [ ] Task description -- specific, actionable, one sentence
- [ ] Task description
- [x] Completed task

## Sprint / Phase N+1 -- [short description]

- [ ] Task description
```

Rules for tasks:
- Each task must be independently completable in one session
- Never nest tasks more than one level deep
- Write tasks in imperative mood ("Read X", "Write Y", "Fix Z")
- Include the file or module affected when relevant

### Section 3 -- Functionality Matrix (optional)

Use when the project has multiple feature dimensions that need coverage tracking. A table per dimension, with columns for tested/untested status.

```markdown
## Functionality Matrix

### [Dimension Name]

| Feature | Tested? | File/Location | Sprint |
|---------|---------|--------------|--------|
| Feature A | ✅ Done | `path/to/file.py` | -- |
| Feature B | ❌ Missing | -- | Sprint N |
| Feature C | ✅ Partial | `path/to/file.py` | -- |
```

## Instructions

### At Session Start

1. Run: does `docs/todos.md` exist?
   - Yes: read it now before doing anything else. Note the current sprint and any blocked tasks.
   - No: ask the user if they want one created before proceeding.
2. Briefly summarize where things stand (2-3 sentences max) so the user knows you have context.
3. Do not repeat the full file contents back to the user -- just the relevant current state.

### Checking Off Completed Tasks

1. Change `- [ ]` to `- [x]` for each task completed in this session.
2. If the task completion changes a dashboard metric (e.g., test count, coverage), update the dashboard table too.
3. If an entire sprint/phase is done, add `[DONE]` to its heading.

### Adding New Tasks

1. Identify the correct sprint or phase section based on scope and priority.
2. Add the task as `- [ ] <imperative description>` with enough context to be actionable without re-reading the full conversation.
3. If a new sprint/phase section is needed, add it after the last existing one with a clear goal and target metric.

### Creating the File from Scratch

When `docs/todos.md` does not exist:

1. Ask the user: "Should I create `docs/todos.md` to track this project? If so, what metric are we optimizing for (e.g., test coverage, features shipped, bug count)?"
2. Create `docs/` if it does not exist.
3. Write the file with Section 1 (dashboard) and Section 2 (first sprint/phase tasks). Add Section 3 only if the project has multiple coverage dimensions.
4. Populate the dashboard with whatever current metrics the user provides -- use `?` for unknown values rather than leaving cells empty.
5. Confirm the file was created and show the dashboard table.

### Keeping It Focused

- Do not bloat the file with meeting notes, decisions, or rationale -- those belong in a decision record or ADR.
- Do not move completed items to a "done" archive at the bottom -- just mark them `[x]` and leave them in place. The file stays readable.
- Do not auto-update the file on every assistant turn -- only update when something actually changed.

## Format Rules

- File path: `docs/todos.md` (always this exact path)
- Heading level 1: project name + "Progress Dashboard"
- Heading level 2: major sections (Scores, Sprint N, Functionality Matrix)
- Tables: GitHub-flavored markdown pipe tables
- Checkboxes: `- [ ]` (pending), `- [x]` (done)
- Status emoji: ✅ Done, ❌ Missing, ✅ Partial (for functionality matrices only)
- No hard line wrapping inside table cells or bullet points

## References

- [references/sdk-triggers.md](references/sdk-triggers.md) -- background-task triggers in agent SDKs (time-based and event-based) as prior art for the `/loop` and `/schedule` workflows: the same "work that fires without a human prompt" mental model at a different runtime layer.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I will remember what is left to do, a tracker is overhead" | Across multi-session work the next session starts cold with no memory; without `docs/todos.md` the agent re-discovers state from scratch and silently drops half-finished items. |
| "I will update todos.md at the end once everything is done" | Batching updates to the end means a crashed or interrupted session loses the record of what was completed; check off tasks as they finish, not in one deferred sweep. |
| "Putting the decision rationale here keeps everything in one place" | Mixing rationale and meeting notes into the tracker bloats it until it is unreadable; rationale belongs in a decision record or ADR, the tracker stays a scannable checklist. |

## Verification

- [ ] The file exists at exactly `docs/todos.md`
- [ ] Section 1 contains a dashboard table with the optimized metric (no empty cells; use `?` for unknowns)
- [ ] Completed tasks are marked `- [x]` in place, not deleted or moved to an archive block
- [ ] No meeting notes, ADR-style rationale, or per-turn churn was added to the file

## Related Skills

- [[session-history]] -- captures what happened in a session (retrospective); todos.md is forward-looking
- [[code-commit-workflow]] -- after committing, check off the relevant tasks in todos.md
- [[implementation-plan]] -- produces the initial sprint breakdown that populates todos.md Section 2
- [[known-gaps-tracker]] -- the per-version archive companion that records deferred items todos.md no longer tracks
- [[session-teach-back]] -- uses the same checkbox-file pattern this skill applies to tasks, but to track confirmed mastery of a session rather than forward-looking work
