# Decision: Cursor Receives the Global Instructions Through Its sessionStart Hook

Status: implemented - a global install renders the instruction template for Cursor and the sessionStart hook returns it as additional context.

Maintainers of the Cursor integration and anyone adding a rule meant for every platform use this record to understand how an always-loaded instruction reaches Cursor, which has no global instruction file. It covers the delivery channel, why it beats the alternatives, and what still needs a live check.

**Date**: 2026-10-22. **Source**: the American-spelling rule reached every installed platform's instruction file except Cursor's, and the maintainer required it to arrive automatically on install.

## Problem

Every other platform receives the rendered instruction template (Writing Discipline, attribution, autonomous operation, and the rest) in a global file it loads on every session. Cursor documents no such file: per cursor.com/docs/context/rules, User Rules are "global preferences defined in Customize" with no documented file path, and `AGENTS.md` and `.cursor/rules` are project-scoped. A global install therefore gave Cursor skills, agents, and hooks but none of the always-loaded rules, so a rule added to the templates silently skipped Cursor.

## Decision

A global install renders `base-cursor.md` into `~/.cursor/nexus-hub-instructions.md` as a managed block, so text the user adds outside the block survives reinstalls. The `sessionStart` entry the installer already writes to `~/.cursor/hooks.json` runs `nexus_git_attribution.py context --instructions <that file>`, which returns one `additional_context` holding the instructions followed by the attribution policy. Cursor documents `sessionStart` output `additional_context` as "Additional context to add to the conversation's initial system context" (cursor.com/docs/agent/hooks, fetched 2026-10-22). A missing instructions file is skipped so the attribution policy still loads. Workspace hooks add no copy, because Cursor reads a project's `AGENTS.md` natively.

## Alternatives considered

- **Write Cursor's User Rules directly.** Rejected: they live in Cursor's internal settings storage with no documented file or API, and writing undocumented storage is exactly the invented-lever pattern AGENTS.md forbids.
- **Ask the user to paste the rule into Customize, Rules.** Rejected by the maintainer: a manual step after install means the rule is missing on every machine where nobody remembers it.
- **Ship the rule as a global Cursor skill.** Rejected: skills load only when the agent judges them relevant, and an always-on writing rule must apply to every reply.
- **A second sessionStart entry for the instructions.** Rejected: Cursor does not document how several `additional_context` responses combine, while one response from the existing entry is unambiguous.

## Consequences

Any rule added to the instruction templates now reaches Cursor on the next global install with no Cursor-specific work. The same docs page says `sessionStart` "runs as fire-and-forget", so whether its context lands on every session must be confirmed in a fresh Cursor session; until that check is recorded, the read contract's Cursor row rests on the documented contract, as the attribution policy already did.
