# Command Scope Mechanism (v3.0.0)

This is the authoring contract every consolidated v3.0.0 command follows. The v3.0.0 release collapses 41 slash commands into 14 verb-first commands (`describe`, `plan`, `implement`, `test`, `review`, `update`, `compare`, `research`, `skills`, `spec`, `session`, `setup`, `memory`, `usage`). Each command is a thin dispatcher that resolves a scope and delegates to one or more retained skills, where the real work lives. This guide defines how scope is resolved and how delegation is written, so every command behaves the same way for users.

The full design rationale is in the legacy migration-source path [`docs/releases/v3/v3.0/command-consolidation-design.md`](../../docs/releases/v3/v3.0/command-consolidation-design.md) Section 4 until the repository tree is canonicalized. This file is the distributable, command-author-facing version of that contract. It installs to `~/.nexus-hub/style-guides/command-scope-mechanism.md`.

## Core principle: thin command, fat skill

The 41 existing rich skill bodies are NOT rewritten or deleted. They are retained and become scope modules. Each new command file is a thin dispatcher: it parses arguments, resolves a scope, presents a menu when needed, then delegates to the retained skill(s). This keeps each command file well under 150 lines and preserves every proven behavior.

The scope menu text, the recognized scope tokens, and the delegation targets live in the thin command file. The actual work lives in the retained skill. A command file that grows past 150 lines is almost always doing work that belongs in a skill.

## The uniform scope-resolution contract

Every scoped command resolves its scope with the same five-step contract:

1. **Parse the first positional argument** (`$ARGUMENTS`). If it matches a recognized scope token for this command, set `SCOPE` to that token and skip the menu. If the argument is a path or slug (for example `/implement <plan-slug>`, `/compare <github-url>`, `/plan from-comparison`), route it to the matching scope and pass it through.
2. **If no recognized scope argument is present**, show a short numbered scope menu (the command's scope list), one line per scope, with the recommended default clearly marked. Wait for the user's selection before doing any work.
3. **A `full` or `all` scope runs every focused scope in the correct order** and then synthesizes (for example `/review full` runs structure, then quality, then coverage, then security, then changes, then synthesizes; `/test all` runs unit, then integration, then e2e, then ci, each driven to its threshold).
4. **Delegate** to the resolved scope module (the retained skill body), passing any remaining arguments through unchanged.
5. **Infer scope where it is unambiguous.** Some commands can skip the menu by inferring scope from the input (for example `/compare <github-url>` infers `repo`; `/test` against an existing failing suite starts at `unit`). Inference must be unambiguous; when in doubt, fall back to the menu.

## Scope menu format

When no recognized scope token is supplied, present a numbered menu. Keep it to one line per scope with a short description, and mark the recommended default. For example:

```
What scope?
  1. full       (recommended) - run every lens and synthesize
  2. structure  - module boundaries and dependency map
  3. quality    - SOLID, complexity, maintainability
  4. security   - run-security-audit lens
  5. pentest    - run-penetration-test lens
  6. changes    - multi-agent persona diff review
  7. skill-scan - security-scan a skill or the catalog

Reply with a number or a scope name.
```

Rules for the menu:

- Recognized scope tokens are matched case-insensitively against the first positional argument. Accept both the token (`security`) and the menu number when the user replies.
- Always mark exactly one recommended default and run it if the user presses enter without choosing.
- Never run work before the user has selected a scope (when a menu is shown).

## Delegation block

After resolving the scope, dispatch to the retained skill(s). Make the mapping explicit and one-to-one with the scope tokens:

```
Then dispatch:
  full       -> analyze-codebase (all sections)
  structure  -> analyze-codebase (structure section only)
  deps       -> analyze-codebase (dependency section only)
  ...
```

Heavy logic stays in the retained skill. The command file only names the delegate and the scope-specific entry point.

## Optional dynamic-workflow fan-out (graceful degradation)

Some commands offer an at-scale fan-out path (for example "audit every endpoint for missing auth", "generate tests for every unit", "research every subsystem in parallel"). This path is an opt-in acceleration, never a dependency:

- **Detect availability** of dynamic workflows in the harness. They are a plan-gated research-preview feature, so a command MUST NOT assume they are present and MUST fall back to single-agent execution when they are off or unavailable.
- **Offer, do not impose.** Present the fan-out path as an opt-in with the scope-first token caution (calibrate on a small slice before fanning out across the whole surface).
- **Cross-link** the orchestration decision guide `[[agent-orchestration-primitives]]` rather than re-explaining the primitives in the command body.

This carries zero new outbound calls, dependencies, or credentials: dynamic workflows are an Anthropic-runtime feature, so this is command behavior plus skill-native guidance only.

## Thin-command skeleton template

Copy this skeleton when authoring a new consolidated command. Replace the bracketed placeholders. Keep the body under 150 lines.

```markdown
---
description: <One sentence: what the command does, with trigger phrases.>
---
# /<command> Command

<One-paragraph intro: what this command does and when to reach for it.>

## Scope resolution

Resolve SCOPE from the first positional argument ($ARGUMENTS). Recognized
scopes: <scope-a>, <scope-b>, <scope-c>, full.

- If $ARGUMENTS names a recognized scope, set SCOPE and skip the menu.
- If $ARGUMENTS is a <path/slug> (when applicable), route it to <scope> and
  pass it through.
- Otherwise, present this menu and wait for a selection:

      What scope?
        1. full       (recommended) - <one line>
        2. <scope-a>  - <one line>
        3. <scope-b>  - <one line>
        4. <scope-c>  - <one line>

      Reply with a number or a scope name.

- `full` runs <scope-a>, then <scope-b>, then <scope-c> in order, then
  synthesizes.

## Delegation

Dispatch the resolved scope to the retained skill(s):

  full       -> <skill> (comprehensive)
  <scope-a>  -> <skill-a>
  <scope-b>  -> <skill-b>
  <scope-c>  -> <skill-c>

Pass any remaining arguments through unchanged. Heavy logic stays in the
retained skill; this file only resolves scope and delegates.

## Optional fan-out (only if the command supports it)

For very large surfaces, offer the dynamic-workflow fan-out path with
confirmation and the scope-first token caution; fall back to single-agent
execution when workflows are unavailable. See [[agent-orchestration-primitives]].
```

## Authoring checklist

Before shipping a new consolidated command, confirm:

- [ ] The file is under 150 lines.
- [ ] The first positional argument resolves a recognized scope and skips the menu.
- [ ] A bare invocation shows the numbered menu with one recommended default and does no work until the user selects.
- [ ] `full` (or `all`) runs every focused scope in the documented order, then synthesizes.
- [ ] Every scope token maps to an explicit delegation target (a retained skill).
- [ ] Any optional fan-out path is opt-in, degrades gracefully, and cross-links `[[agent-orchestration-primitives]]`.
- [ ] The body is ASCII-only and follows [`markdown.md`](markdown.md) (blank lines around lists, code blocks, tables, and headings).
