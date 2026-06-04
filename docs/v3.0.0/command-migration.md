# Command Migration Guide -- v3.0.0

**Version**: v3.0.0
**Status**: deprecation shims active for the whole v3.x line; old names removed at v4.0.0

v3.0.0 collapses the 41-command slash surface into **14 verb-first commands** plus **2 permanent convenience aliases**. No behavior was removed. Each consolidated command is a thin dispatcher that resolves a scope and delegates to the same retained skill that did the work before, so every proven behavior is preserved (the design rationale is in [`command-consolidation-design.md`](command-consolidation-design.md)).

Every old command name keeps working for the entire v3.x line through a **deprecation shim**: invoking it prints a one-line notice and then forwards to the new command and scope. Update your scripts, docs, and muscle memory to the new names; the shims are a transition aid, not a permanent surface.

## Deprecation timeline

- **v3.0.0 through v3.x**: all 40 old command names work as deprecation shims. Invoking one prints `/<old> is deprecated and will be removed in v4.0.0. Forwarding to /<new> <scope>.` and then runs the new command identically (same retained skill, same arguments).
- **v4.0.0**: the deprecation shims are removed. Only the 14 consolidated commands and the 2 permanent aliases (`/constitution`, `/commit`) remain. Shim removal is tracked as a v4.0.0 known-gap.

## How scope resolution works

Every consolidated command follows one uniform contract (full version in [`catalog/style-guides/command-scope-mechanism.md`](../../catalog/style-guides/command-scope-mechanism.md)):

- A **bare invocation** (for example `/review`) presents a short numbered scope menu with a recommended default and waits for your selection before doing any work.
- An **optional positional argument** that names a recognized scope skips the menu and runs that scope directly (for example `/review security`).
- A **`full` or `all` scope** runs every focused scope in order and then synthesizes (for example `/review full`, `/test all`).
- A **path or slug** argument is routed and passed through (for example `/implement <plan-slug> phase-3`, `/compare <github-url>`).

A deprecation shim maps the old name straight onto the new command and the scope shown in the table below, so an old invocation behaves exactly as it did before.

## Old to new mapping (grouped by new command)

| Old command | New command + scope | Retained skill |
|---|---|---|
| `/analyze-codebase` | `/describe full` | `analyze-codebase` |
| `/generate-plan` | `/plan` (interactive: `new` / `feature` / `refactor` / `from-comparison`) | `generate-plan` |
| `/generate-todos` | `/plan todos` | `generate-todos` |
| `/tasks-to-issues` | `/plan issues` | `tasks-to-issues` |
| `/implement-phase` | `/implement` (positional `<slug>` / `phase-N` / `next`) | `implement-phase` |
| `/generate-tests` | `/test all` | `generate-tests` |
| `/generate-unit-tests` | `/test unit` | `generate-unit-tests` |
| `/tdd` | `/test tdd` | `tdd` |
| `/review-codebase` | `/review full` | `review-codebase` |
| `/review-changes` | `/review changes` | `review-changes` |
| `/run-deep-review` | `/review full` | `run-deep-review` |
| `/run-security-audit` | `/review security` | `run-security-audit` |
| `/run-penetration-test` | `/review pentest` | `run-penetration-test` |
| `/generate-sbom` | `/review sbom` | `generate-sbom` |
| `/update-documentation` | `/update docs` | `update-documentation` |
| `/generate-readme` | `/update docs` | `generate-readme` |
| `/update-devlog` | `/update devlog` | `update-devlog` |
| `/generate-devlog` | `/update devlog` | `generate-devlog` |
| `/update-gitignore` | `/update gitignore` | `update-gitignore` |
| `/update-version` | `/update version` | `update-version` |
| `/generate-changelog` | `/update changelog` | `generate-changelog` |
| `/generate-commit-message` | `/update commit` | `generate-commit-message` |
| `/refactor-docs` | `/update refactor` | `refactor-docs` |
| `/refactor-project` | `/update refactor` | `refactor-project` |
| `/compare-project` | `/compare` (scope auto-detected from the source type) | `compare-project` |
| `/compile-deep-research` | `/research compile` | `compile-deep-research` |
| `/generate-report` | `/research report` | `generate-report` |
| `/search-skills` | `/skills search` | `search-skills` |
| `/commands-cheatsheet` | `/skills list` | `commands-cheatsheet` |
| `/create-skill-or-command` | `/skills create` | `create-skill-or-command` |
| `/import-skills` | `/skills import` | `import-skills` |
| `/analyze-spec` | `/spec analyze` | `analyze-spec` |
| `/clarify-spec` | `/spec clarify` | `clarify-spec` |
| `/continue-session` | `/session continue` | `continue-session` |
| `/wrap-up-session` | `/session wrap-up` | `wrap-up-session` |
| `/generate-session-history` | `/session history` | `generate-session-history` |
| `/setup-project` | `/setup project` | `setup-project` |
| `/install-pre-commit-review-hook` | `/setup hooks` | `install-pre-commit-review-hook` |
| `/manage-memory` | `/memory` | `manage-memory` |
| `/check-usage` | `/usage` | `check-usage` |

Two scopes are reached by no old command file because they were never standalone commands, only skills: `/update config` (the built-in `update-config` skill) and `/research deep` (the `deep-research` skill).

## Permanent aliases (not deprecated)

These two single-word names are retained for the entire v3.x line and beyond. They are convenience aliases, not deprecation shims: they print no deprecation notice and are not scheduled for removal at v4.0.0.

| Alias | Forwards to | Why kept |
|---|---|---|
| `/constitution` | `/spec constitution` | Heavily cross-referenced by `/plan` (the Constitution Check gate), `analyze-spec`, and the `project-constitution` skill; a single-word entry point is worth keeping. |
| `/commit` | `/update commit` | Committing is a high-frequency mid-development action that deserves a single-word entry point. (An external `commit-commands` plugin may also provide a `/commit`; resolution order decides which runs.) |

## New in v3.0.0 (not renames)

These are new capabilities, surfaced through the consolidated commands rather than as standalone commands:

- **`skill-security-scan` skill + `nexus-skill-scanner` engine** -- a two-stage skill-security scanner (deterministic detector + semantic adjudication), surfaced via `/skills scan` (pre-install) and `/review skill-scan` (audit / catalog dogfood).
- **`agent-orchestration-primitives` skill** -- a decision guide for the four orchestration primitives, cross-linked from the commands that offer an optional dynamic-workflow fan-out path (`/plan`, `/test`, `/review`).

## Notes

- The shims do not change any output, file path, or argument handling: they forward arguments unchanged to the new command and scope.
- The consolidated command surface is documented in [`command-consolidation-design.md`](command-consolidation-design.md) Section 2 (the 14 commands) and Section 4 (the scope mechanism).
- Commands need no `data/*.json` registration; the only count surfaces updated for this release are `data/marketplace.json`, the `AGENTS.md` / `README.md` catalog-count prose, and the `.claude-plugin/plugin.json` description.
