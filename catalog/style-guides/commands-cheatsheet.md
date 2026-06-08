# Commands Cheatsheet (v3.1.1)

This is the procedure `/skills list` follows to render the command cheatsheet. It is **generated at runtime from the command files themselves**, never hand-maintained. That is the whole point: every time a command is added, renamed, refactored, or deprecated, the cheatsheet reflects the change automatically on the next `/skills list`, because the command files are the single source of truth. There is no static command table to keep in sync anywhere in the repo. This file installs to `~/.nexus-hub/style-guides/commands-cheatsheet.md`.

## Source of truth: the command files

Every Nexus-Hub command is a Markdown file with YAML frontmatter carrying a `description`. Active commands describe what they do; deprecation shims carry a `DEPRECATED (removed in vX.Y.Z). Forwarding to /NEW.` description and a body line `... forwards to /NEW`. The cheatsheet is built by reading these files.

Locate the command surface in this order (use the first that exists):

1. **Installed surface** (when running inside a user project / global config): the per-platform command directory -- `~/.claude/commands/` (Claude Code), `~/.codex/prompts/` (Codex), or `~/.gemini/**/workflows/` (Gemini / Antigravity). Use the one matching the active platform.
2. **Repo surface** (when running inside the Nexus-Hub repo): `catalog/commands/`.

Read every `*.md` file in that directory. Do not rely on memory or a hard-coded list -- always read the files so the output matches what is actually installed.

## Classification

For each command file, classify it from its frontmatter `description` and body:

- **Active command** -- description does not begin with `DEPRECATED`. These are the verb-first commands (`describe`, `plan`, `implement`, `test`, `review`, `update`, `compare`, `research`, `skills`, `spec`, `session`, `setup`, `memory`, `usage`).
- **Permanent alias** -- a non-deprecated command whose **own H1 heading ends with `(permanent alias)`** (for example `# /commands Command (permanent alias)`); its first body line states `/NAME is a permanent ... alias for /TARGET`, which gives the forwarding target. Detect by that heading suffix, NOT by any mention of the words "permanent alias" -- scoped commands such as `/spec` and `/update` describe their aliases in passing (".../constitution is a permanent alias for /spec constitution") and must not be misclassified as aliases themselves. This heading-based rule needs no fixed list, so a future alias is picked up automatically. Currently `/constitution` -> `/spec constitution`, `/commit` -> `/update commit`, and `/commands` -> `/skills list`. Treat an alias as active; mark it as an alias and show its forwarding target.
- **Deprecation shim** -- description begins with `DEPRECATED`, or the body contains `Forwarding to /NEW` / `forwards to /NEW`. Capture the old name and the `/NEW` target.

Build a **replaces map**: for each active command, collect the set of shim names that forward to it (directly, or via a scope such as `/test all`). A shim forwards to a command + optional scope; group the shim under the target command.

## Output format

Render three sections, in this order. Follow the Markdown style guide (blank line before and after every table; ASCII-only; one continuous line per cell).

### 1. Active commands

A table of the active commands and aliases, sorted with the 14 verbs first (in the canonical order above) then the aliases:

```
| Command | What it does | Replaces |
|---|---|---|
| /plan | <first sentence of its description> | /generate-plan, /generate-todos, /tasks-to-issues |
| /implement | <first sentence> | /implement-phase |
| ... | ... | ... |
| /constitution (alias) | -> /spec constitution | -- |
```

- **What it does**: the first sentence of the command's `description` (trim trigger-phrase and SKIP clauses; keep it to one scannable line).
- **Replaces**: the deprecated command names that forward here, comma-separated, from the replaces map. `--` if none.

### 2. Deprecated -> new (migration map)

A table of every shim and where it forwards, so a user with old muscle memory is corrected:

```
| Deprecated (removed v4.0.0) | Use instead |
|---|---|
| /generate-plan | /plan |
| /run-penetration-test | /review pentest |
| ... | ... |
```

State once, above the table, that deprecated names still work through the whole v3.x line and are removed at v4.0.0.

### 3. Common workflows

A short bullet list of multi-command flows, so the cheatsheet guides the user through real tasks rather than just listing verbs. Derive these from the active command set; keep to the highest-value flows. For example:

- **Greenfield build**: `/setup` -> `/spec` -> `/plan` -> `/implement` (per phase) -> `/review` -> `/update release`
- **Adopt from an external source**: `/compare` -> `/plan` (from-comparison) -> `/implement` (per phase) -> `/update release`
- **Quality pass before merge**: `/review` -> `/update docs` -> `/update changelog` -> `/update commit`
- **Work with the catalog**: `/skills search` -> `/skills scan` -> `/skills import`; or `/skills create` to author a new skill or command

## Optional argument

`/skills list <term>` filters to commands whose name or description matches `<term>` (for example `/skills list test` or `/skills list security`). With no argument, render the full cheatsheet. Always render section 1; render sections 2 and 3 only when no filter is applied (a filtered view is about finding one command, not migrating or learning workflows).

## Self-maintenance (for contributors)

Do **not** create or update a static command list when adding, renaming, or deprecating a command. The only artifacts to touch are the command files in `catalog/commands/` (the new command, and -- on a rename -- a deprecation shim for the old name, per the "Adding a New Command" rules in `AGENTS.md`). `/skills list` derives everything from those files, so the cheatsheet is correct by construction. This guide changes only if the *format* of the cheatsheet changes, not its contents.

## Verification

The rendered cheatsheet is correct when:

- Every non-deprecated file in the command surface appears exactly once in section 1.
- Every deprecation shim appears in section 2 with the correct `/NEW` target read from its file (not guessed).
- The `Replaces` column in section 1 accounts for every shim in section 2 (each shim maps to exactly one active command).
- No command is listed that does not have a file in the surface that was read.
