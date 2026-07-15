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
- Never add AI attribution footers or AI-generated signatures to commit messages
- Commit messages must be ASCII-only: no em-dashes, en-dashes, curly quotes, ellipsis characters, or other Unicode punctuation. Use hyphens, straight quotes, and `...` instead. This prevents encoding corruption on Windows.
- Use `docs/todos.md` as the project progress tracker: read it at session start if it exists, check off completed tasks, add newly identified work, and update dashboard metrics after relevant milestones. Use the dev-progress-tracker skill to create or maintain it.
- If requirements are ambiguous, batch all clarifying questions into the first turn rather than asking one question per turn. Surface multiple interpretations and acceptance criteria together so the user can answer them in a single round-trip. State any assumptions explicitly before acting. Avoid unbounded per-question ping-pong - it wastes context and Opus 4.7's reasoning budget.
- Every changed line must trace directly to the user's request; do not clean up adjacent code, pre-existing dead code, or style issues outside the stated scope
- Place punctuation outside quotation marks; no em-dashes
- Professional teaching tone
- Never hard-wrap paragraph text at a fixed column width; write each paragraph or bullet point as a single continuous line and let the editor or terminal handle visual wrapping

## Branching

- Follow the project's declared branching strategy. Do not commit feature or version work directly to the protected (release) branch -- branch off the integration branch and integrate through it. If the strategy is unstated, infer it (a `develop` branch implies a develop+main model; otherwise assume GitHub Flow) and confirm before branching. See the `git-branching-workflow` skill for the per-model discipline.

## Run and Verify

- When you change how the app behaves, actually run it and observe the change end-to-end before claiming it works - do not rely on tests, type-checks, or a clean build alone. Drive the affected flow (CLI command, endpoint, screen, or script) and confirm the observed behavior matches the intent, especially when working autonomously or asynchronously.
- If a change has no runnable surface (docs or config only), say so plainly instead of implying it was exercised. See the `verification-before-completion` skill for the fresh-evidence rule that must hold before any completion claim.

## Output Minimization
- Suppress verbose progress bars, banners, and informational logs from commands unless they indicate an error
- Prefer `--quiet`, `--silent`, or `-q` flags when running package managers, build tools, and test runners
- Summarize long command output rather than echoing it in full; report only counts, errors, and key results
- When a command produces more than ~20 lines of output, summarize what happened rather than quoting the full log

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

## Context References
- Skills: `.cursor/skills/` (auto-activated by task context)
