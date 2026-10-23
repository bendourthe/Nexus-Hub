# Decision: Cursor Receives the Global Instructions Through a Local Rules Plugin

Status: implemented - a global install writes a user-level Cursor plugin whose alwaysApply rules carry the instructions and the attribution policy.

Maintainers of the Cursor integration and anyone adding a rule meant for every platform use this record to understand how an always-loaded instruction reaches Cursor, which has no global instruction file. It covers the delivery channel, the live evidence behind it, and the sessionStart route it replaced.

**Date**: 2026-10-22. **Source**: the American-spelling rule reached every installed platform's instruction file except Cursor's, and the maintainer required it to arrive automatically on install.

## Problem

Every other platform receives the rendered instruction template (Writing Discipline, attribution, autonomous operation, and the rest) in a global file it loads on every session. Cursor documents no such file: per cursor.com/docs/context/rules, User Rules are "global preferences defined in Customize" with no documented file path, and `AGENTS.md` and `.cursor/rules` are project-scoped. A global install therefore gave Cursor skills, agents, and hooks but none of the always-loaded rules.

## Decision

A global install writes a user-level local plugin at `~/.cursor/plugins/local/nexus-hub/`: a `.cursor-plugin/plugin.json` manifest (only `name` is required, per cursor.com/docs/reference/plugins) and a `rules/` folder holding two rules with `alwaysApply: true` frontmatter. `nexus-hub-instructions.mdc` carries the rendered `base-cursor.md`, and `nexus-hub-attribution.mdc` carries the git-attribution policy. Cursor discovers plugins in `~/.cursor/plugins/local` (cursor.com/docs/plugins), and an `alwaysApply` rule "will be applied to every chat session" (cursor.com/docs/context/rules). The files are installer-owned generated files, refreshed on every non-interactive install and removed by teardown. The install also deletes `~/.cursor/nexus-hub-instructions.md`, which the replaced sessionStart route wrote. Workspace installs are unchanged, because Cursor reads a project's `AGENTS.md` natively.

Verified live on Cursor 3.24.18 on 2026-10-22: after a window reload with the plugin in place, a new agent chat asked "What spelling convention do your instructions specify?" answered with the rule's wording ("American English ... color, organize, center ... External identifiers, quotes, and URLs keep their original spelling").

## Alternatives considered

- **The sessionStart hook's `additional_context`.** Shipped first in #514 and rejected on live evidence. Cursor documents the field as "Additional context to add to the conversation's initial system context", but Cursor's own hooks log showed the hook loaded ("Loaded 7 user hook(s) for steps: ... sessionStart") and never requested ("Hook step requested: sessionStart" appears zero times across every Cursor log on the machine). A new chat answered that its instructions specify no spelling convention. The sessionStart entry still ships for the attribution policy, in case a Cursor version starts firing it.
- **Write Cursor's User Rules directly.** Rejected: they live in Cursor's internal settings storage with no documented file or API, and writing undocumented storage is the invented-lever pattern AGENTS.md forbids.
- **Ask the user to paste the rule into Customize, Rules.** Rejected by the maintainer: a manual step after install means the rule is missing on every machine where nobody remembers it.
- **Ship the rule as a global Cursor skill.** Rejected: skills load only when the agent judges them relevant, and an always-on writing rule must apply to every reply.

## Consequences

Any rule added to the instruction templates reaches Cursor on the next global install with no Cursor-specific work. Cursor's plugin docs say local plugins load "if local plugin imports are allowed" and that the setting is "off by default" on Enterprise, so on an Enterprise seat with that setting off the rules do not load; the install cannot change that setting. The rule carries the full skill index like every platform's global instruction file (about 80 KB); `NEXUS_HUB_SKILL_INDEX=pointer` shrinks it.
