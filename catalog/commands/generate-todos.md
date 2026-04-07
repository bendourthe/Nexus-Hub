---
description: Bootstrap docs/todos.md for an inherited project by analyzing git history, existing docs, and code annotations, then writing a structured progress tracker.
---

# Generate Todos Command

Bootstrap `docs/todos.md` for a project that did not previously use the dev-progress-tracker workflow. This command reconstructs what has already been done, surfaces in-progress work, and seeds a roadmap for what comes next — all without requiring the user to fill in anything manually.

## Phase 1: Pre-flight Check

Before collecting any project context:

1. Check whether `docs/todos.md` already exists.
   - If it **does** exist, stop and ask the user:

     ```
     docs/todos.md already exists.

     O = Overwrite — replace it entirely
     S = Skip — abort and keep the existing file
     ```

     Wait for the user's choice before continuing. If they choose **S**, stop here.

2. Check whether `docs/` exists. Note whether it needs to be created.

## Phase 2: Project Discovery (read-only)

Collect context automatically. Do not ask the user anything yet.

### 2.1 Identity and Version

- Read `package.json` (`.name`, `.version`), `pyproject.toml` (`[project] name`, `version`), `Cargo.toml` (`[package] name`, `version`), or `go.mod` (`module` line) — use whichever is present.
- If none are present, use the repository directory name as the project name and `?` for the version.
- Run `git branch --show-current` to get the active branch.

### 2.2 Recent History

- Run `git log --oneline -30` to read the 30 most recent commit subjects.
- Run `git tag -l --sort=-version:refname` and note the latest tag if any.
- If `CHANGELOG.md` exists, read the first 60 lines for version boundaries and feature summaries.

### 2.3 Existing Documentation

- Read `README.md` (first 80 lines) for stated goals, features, and project scope.
- Read `docs/DEVLOG.md` (first 100 lines) if it exists — DEVLOG is the richest source of in-progress context and known issues.

### 2.4 Pending Work Signals

Search the codebase for in-source annotations:

- Grep for `TODO`, `FIXME`, `HACK`, `XXX` across all source files (exclude `node_modules/`, `.venv/`, `vendor/`, `dist/`, `build/`).
- Collect each hit as a candidate active task: record the file path, line number, and annotation text.
- Cap at 20 results; if more exist, note the count and keep the 20 most recently modified files.

### 2.5 Source Inventory

Report what was found before asking any questions:

```
Sources collected:
- Project name:     <name> (from <source>)
- Version:          <version or ?>
- Branch:           <branch>
- Git commits:      <N> commits scanned (latest: <subject>)
- Latest tag:       <tag or "none">
- CHANGELOG.md:     present / absent
- README.md:        present / absent
- docs/DEVLOG.md:   present / absent
- TODO/FIXME hits:  <N> annotations found
```

## Phase 3: One Focused Question

Ask the user a single question before writing anything:

```
What is the primary metric you want to track for this project?
Examples: test coverage %, features shipped, open bugs, tasks done / total

Press Enter to use the default: "tasks done / total"
```

Wait for the answer. Accept a blank response as "tasks done / total".

## Phase 4: Build `docs/todos.md`

Construct the file following the exact dev-progress-tracker structure.

### Section 1 — Dashboard

```markdown
# <project name> — Progress Dashboard

**Branch:** `<branch>`

---

## Scores (update after each sprint)

| Metric | Current | Target | Delta |
|--------|---------|--------|-------|
| <user-chosen metric> | <inferred value or ?> | <inferred target or ?> | <gap or ?> |
```

Rules:
- Project name comes from the manifest; fall back to the repo directory name.
- For "tasks done / total": count `[x]` tasks as done and `[ ]` tasks as total after Sections 2 is drafted, then fill in.
- For "test coverage %": if a coverage report file exists (`coverage/lcov.info`, `.coverage`, `htmlcov/index.html`), extract the headline number; otherwise use `?`.
- For "open bugs" or "features shipped": use `?` and note the source to check (e.g., "check issue tracker").
- Use `?` rather than leaving any cell blank.

### Section 2 — Task Roadmap

Build three sprint sections from the discovery data:

**Sprint 1 — Completed Work** `[DONE]`

Derive completed tasks from git commit subjects (especially feat/fix/chore prefixed commits) and CHANGELOG entries. Each task must be independently understandable without re-reading the commits.

- Mark every item `[x]`.
- Cap at 15 items; if the git log yields more, group minor commits under a single summary item.
- Do not add items that are not supported by evidence from git log, CHANGELOG, or DEVLOG.

Example:
```markdown
## Sprint 1 — Completed Work [DONE]

- [x] <commit subject rephrased as an imperative task>
- [x] <commit subject rephrased as an imperative task>
```

**Sprint 2 — Active / In Progress**

Populate from TODO/FIXME annotations and any open items mentioned in DEVLOG.

- Mark every item `[ ]`.
- For each TODO/FIXME, write the task as an imperative sentence and append the source reference in parentheses: `(src/auth.py:42)`.
- If DEVLOG mentions known issues or "next steps", include them here.
- If nothing is found, write a single placeholder: `- [ ] Review codebase and define next milestone`.

Example:
```markdown
## Sprint 2 — Active

- [ ] <imperative task> (path/to/file.py:NN)
- [ ] <task from DEVLOG>
```

**Sprint 3 — Upcoming (suggested)**

Infer 2-4 candidate tasks from README goals not yet reflected in the git log, or from the natural continuation of Sprint 2 work. Prefix each item with `*(suggested)*` so the user knows these are not sourced from hard evidence.

```markdown
## Sprint 3 — Upcoming

- [ ] *(suggested)* <next logical task inferred from README or commit direction>
- [ ] *(suggested)* <next logical task>
```

### Section 3 — Functionality Matrix (conditional)

Include this section only when the project has two or more distinct feature dimensions that benefit from coverage tracking (e.g., a CLI with multiple subcommands, a REST API with multiple endpoint groups, a library with distinct modules).

Skip this section entirely for simple or single-purpose projects.

If included, create one table per dimension using the format:

```markdown
## Functionality Matrix

### <Dimension Name>

| Feature | Status | File/Location | Sprint |
|---------|--------|--------------|--------|
| <feature> | ✅ Done | `path/to/file` | — |
| <feature> | ❌ Missing | — | Sprint 2 |
| <feature> | ✅ Partial | `path/to/file` | Sprint 2 |
```

## Phase 5: Write and Confirm

1. Create `docs/` if it does not exist.
2. Write the assembled content to `docs/todos.md`.
3. Print a confirmation summary:

```
docs/todos.md created.

  Project:   <name>
  Branch:    <branch>
  Metric:    <chosen metric>
  Sprints:   3 (1 backfill [DONE], 1 active, 1 upcoming)
  Tasks:     <N> total (<X> done, <Y> pending)
  Sources:   git log, <README / DEVLOG / CHANGELOG / TODO annotations — list which were used>
```

4. Remind the user: "Review Sprint 2 and Sprint 3 — adjust, reorder, or remove tasks before your next session."

## Guidelines

- Never fabricate tasks. Every `[x]` item must trace to a git commit, CHANGELOG entry, or DEVLOG entry. Every `[ ]` item must trace to a TODO/FIXME annotation, DEVLOG note, or README goal.
- Use `?` rather than guessing metric values.
- Keep task descriptions in imperative mood: "Add X", "Fix Y", "Write Z".
- Do not include meeting notes, architecture decisions, or rationale in `docs/todos.md` — those belong in DEVLOG or ADRs.
- Follow all format rules from the dev-progress-tracker skill: pipe tables, `- [ ]` / `- [x]` checkboxes, no hard line wrapping.
