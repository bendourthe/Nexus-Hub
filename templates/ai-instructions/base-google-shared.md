# {{PROJECT_NAME}}

{{PROJECT_DESCRIPTION}}

## Tech Stack
- **Language**: {{PRIMARY_LANGUAGE}} {{LANGUAGE_VERSION}}
- **Package Manager**: {{PACKAGE_MANAGER}}
- **Build**: {{BUILD_TOOL}}
- **Test**: {{TEST_FRAMEWORK}}
- **Lint/Format**: {{LINT_TOOL}}

## Project Layout
{{PROJECT_STRUCTURE_BRIEF}}

## Key Commands
```bash
{{BUILD_CMD}}
{{TEST_CMD}}
{{LINT_CMD}}
```

## Non-Obvious Tooling
{{NON_OBVIOUS_TOOLING}}

## {{PRIMARY_LANGUAGE}} Conventions
{{LANGUAGE_CONVENTIONS}}

## Working Conventions
- Verify solutions work before claiming completion
- Find root causes; no temporary fixes
- **MANDATORY**: When invoking a shell-style tool (Bash, PowerShell, `run_shell_command`, `shell`, etc.), provide the `description` parameter as a single plain-text sentence (<=120 chars, no newlines, no formatting, no `#` characters or borders). Prefer single-line commands; use multi-line bodies only when a here-string or heredoc is genuinely required (e.g. commit messages, file content). The `description` field is the universally-rendered surface across all approval-dialog implementations - keep it precise and scannable.
- **MANDATORY: Every Read, Glob, and Grep tool call MUST be preceded by a one-sentence plain-language explanation** of what file or path is being accessed and why. No exceptions.
- Never add `Co-Authored-By` lines, AI attribution footers, or AI-generated signatures to commit messages
- Commit messages must be ASCII-only: no em-dashes, en-dashes, curly quotes, ellipsis characters, or other Unicode punctuation. Use hyphens, straight quotes, and `...` instead. This prevents encoding corruption on Windows.
- Use `docs/todos.md` as the project progress tracker: read it at session start if it exists, check off completed tasks, add newly identified work, and update dashboard metrics after relevant milestones. Use the dev-progress-tracker skill to create or maintain it.
- If requirements are ambiguous, batch all clarifying questions into the first turn rather than asking one question per turn. Surface multiple interpretations and acceptance criteria together so the user can answer them in a single round-trip. State any assumptions explicitly before acting. Avoid unbounded per-question ping-pong - it wastes context and Opus 4.7's reasoning budget.
- Every changed line must trace directly to the user's request; do not clean up adjacent code, pre-existing dead code, or style issues outside the stated scope
- Place punctuation outside quotation marks; no em-dashes
- Professional teaching tone
- Never hard-wrap paragraph text at a fixed column width; write each paragraph or bullet point as a single continuous line and let the editor or terminal handle visual wrapping

## Communication Contract

- Outcome first, in language a non-engineer follows; define jargon in place; put detail beyond ~5 lines in a linked docs/ file.
- Commands must run as pasted: fill derivable values, flag the rest with a REPLACE line and where to find it.
- Number steps, prerequisites first, expected results. After an error, re-issue ALL remaining steps renumbered.
- Close tasks with Completed / Verified / Open / Next.
- Work still running at turn end: lead with a one-line status banner, cap the update at ~8 lines.

Full contract: `~/.nexus-hub/style-guides/agent-communication.md`.

## Consequential Decisions

Before asking the user to approve or choose anything consequential, give a short plain-language walkthrough. This rule applies when the choice changes security posture, deletes or overwrites data, changes distributed or user-facing behavior, or expands the agreed scope. It does not apply to routine clarification, formatting preferences, or a choice with an obvious default.

The walkthrough must explain what the current work is doing without assuming codebase knowledge, name the relevant moving parts and why they matter, describe what each option (including doing nothing) changes for the user or project, and give a clear recommendation with reasons. Define any necessary jargon in place and keep the explanation to a few short paragraphs.

This is context guidance, not a mechanically enforced tool gate. A parity check can verify that the rule ships consistently, but it cannot guarantee that an agent follows it on every turn.

## Output Minimization
- Suppress verbose progress bars, banners, and informational logs from commands unless they indicate an error
- Prefer `--quiet`, `--silent`, or `-q` flags when running package managers, build tools, and test runners
- Summarize long command output rather than echoing it in full; report only counts, errors, and key results
- When a command produces more than ~20 lines of output, summarize what happened rather than quoting the full log

## End-of-Task Summary
- End every completed task with a short closing summary, even when the change was small
- Use the labeled parts **Completed** (what changed), **Verified** (the evidence), **Open** (blocked, skipped, or deferred work; "nothing outstanding" when empty), **Next** (the concrete next step)
- Keep it scannable and factual: do not restate the conversation or add preamble
- Output-minimization rules never apply to this summary: suppress verbose logs, never the closing summary

## MCP Registry Policy

Nexus-Hub's MCP registry (`catalog/mcp-configs/mcp-servers.json`) is governed by a strict decision tree. When proposing a new entry, walk it in order and stop at the first bucket that fits:

1. **Local-only** (internal Nexus-Hub servers or zero-outbound Anthropic-official servers) - always allowed.
2. **LLM-native skill** (capability achievable by instructing the agent directly) - ship a skill, not an MCP.
3. **Reverse-engineer into a local internal MCP** - if the external project's logic can run locally, build the internal equivalent under `extensions/`. Strip external-source attribution; use generic descriptive names.
4. **Trusted vendor wrapper (your-own-account)** - acceptable only when the vendor is the intrinsic data destination, reverse-engineering isn't viable, AND the feature is extremely worth it. Justify all three in the `_comment`.
5. **Otherwise** - drop.

Hard no: search-as-service, embeddings-as-service, scraping-as-service, generation-as-service. Full policy + 5-question audit in `AGENTS.md`. Matrix at `docs/policy/mcp-reverse-engineering-matrix.md`.

## Skill Discovery
When the user's request matches a skill in the SKILL INDEX below, read the full skill file from the path listed and follow its instructions. Do not mention the skill lookup to the user.

{{SKILL_INDEX}}
