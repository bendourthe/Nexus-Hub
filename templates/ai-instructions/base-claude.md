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

## Communication Style
- Place punctuation outside quotation marks (logical punctuation)
- No em-dashes; use parentheses, commas, or separate sentences
- Professional teaching tone
- Never hard-wrap paragraph text at a fixed column width; write each paragraph or bullet point as a single continuous line and let the editor or terminal handle visual wrapping

## Critical Rules
- Verify work before marking complete
- Find root causes; no temporary fixes
- Destructive git commands require user confirmation (enforced by git-guardrails hook)
- Never add `Co-Authored-By` lines, AI attribution footers, or AI-generated signatures to commit messages
- Commit messages must be ASCII-only: no em-dashes, en-dashes, curly quotes, ellipsis characters, or other Unicode punctuation. Use hyphens, straight quotes, and `...` instead. This prevents encoding corruption on Windows.
- Use `docs/todos.md` as the project progress tracker: read it at session start if it exists, check off completed tasks, add newly identified work, and update dashboard metrics after relevant milestones. Use the dev-progress-tracker skill to create or maintain it.
- **MANDATORY**: When using the Bash tool, always provide a `description` as **plain text only** (a single sentence or short paragraph). Do NOT add borders, boxes, `#` characters, padding, or any manual formatting to the description. A PreToolUse hook (`format-bash-description.py`) handles all formatting automatically. The `require-description.sh` hook blocks commands that omit a description.
- **MANDATORY: Every Read, Glob, and Grep tool call MUST be preceded by a one-sentence plain-language explanation** of what file or path is being accessed and why. No exceptions.
- If requirements are ambiguous, batch all clarifying questions into the first turn rather than asking one question per turn. Surface multiple interpretations and acceptance criteria together so the user can answer them in a single round-trip. State any assumptions explicitly before acting. Avoid unbounded per-question ping-pong - it wastes context and Opus 4.7's reasoning budget.
- Every changed line must trace directly to the user's request; do not clean up adjacent code, pre-existing dead code, or style issues outside the stated scope

## Output Minimization
- Suppress verbose progress bars, banners, and informational logs from commands unless they indicate an error
- Prefer `--quiet`, `--silent`, or `-q` flags when running package managers, build tools, and test runners
- Summarize long command output rather than echoing it in full; report only counts, errors, and key results
- When a command produces more than ~20 lines of output, summarize what happened rather than quoting the full log
- For automated compression of all command output, see `guides/RTK_CONTEXT_COMPRESSION.md` (requires Rust/cargo)

## Context References
- Skills: `.claude/skills/` (auto-activated by task context)
- Architecture: `.claude/context/architecture.md`
- Decisions: `.claude/memory/decisions.md`

## Agent Registry
{{AGENT_REGISTRY}}
<!-- Optional section for projects using autonomous AI agents. Remove if not applicable.
Format:
| Agent ID | Responsibility | Model Tier | Tool Access | Max Budget |
|----------|----------------|------------|-------------|------------|
| research-agent | Gather and summarize information | sonnet | web_search, read_document | $2.00 |
| synthesis-agent | Combine findings into reports | opus | none | $5.00 |
-->

## Spending Controls
{{SPENDING_CONTROLS}}
<!-- Optional section for autonomous agent projects. Remove if not applicable.
- Session budget cap: $XX.XX (set via MAX_BUDGET_USD env var)
- Per-agent budget cap: $X.XX (configured in agent definition)
- Hard stop behavior: BudgetExceededError terminates workflow cleanly
- Alerts: warn at 80% of budget; halt at 100%
- Cost tracking: audit-logs/session-*.jsonl (JSONL, one entry per invocation)
-->

## Environment Variables
{{ENV_VARS_REFERENCE}}
<!-- Optional section. List key env vars with purpose and required/optional status.
| Variable | Purpose | Required |
|----------|---------|----------|
| ANTHROPIC_API_KEY | Anthropic API credentials | Yes |
| AI_PROVIDER | LLM provider: anthropic / bedrock / vertex / openrouter | No (default: anthropic) |
| MODEL_TIER | Model quality: haiku / sonnet / opus | No (default: sonnet) |
| MAX_BUDGET_USD | Hard spending cap per session | Recommended |
-->

## MCP Registry Policy

DevAI-Hub's MCP registry (`catalog/mcp-configs/mcp-servers.json`) is governed by a strict decision tree. When proposing a new entry, walk it in order and stop at the first bucket that fits:

1. **Local-only** (internal DevAI-Hub servers or zero-outbound Anthropic-official servers) - always allowed.
2. **LLM-native skill** (capability achievable by instructing the agent directly) - ship a skill, not an MCP.
3. **Reverse-engineer into a local internal MCP** - if the external project's logic can run locally, build the internal equivalent under `extensions/`. Strip external-source attribution; use generic descriptive names.
4. **Trusted vendor wrapper (your-own-account)** - acceptable only when the vendor is the intrinsic data destination, reverse-engineering isn't viable, AND the feature is extremely worth it. Justify all three in the `_comment`.
5. **Otherwise** - drop.

Hard no: search-as-service, embeddings-as-service, scraping-as-service, generation-as-service. Full policy + 5-question audit in `AGENTS.md`. Matrix at `docs/v1.0.0/mcp-reverse-engineering-matrix.md`.

## MCP Integration
{{MCP_STATUS}}
<!-- Optional section. Document active MCP servers and their purpose.
Active servers:
- filesystem: Read/write workspace files (stdio)
- playwright: Browser automation for web tasks (stdio, per-agent instance)

Configuration: .mcp.json at project root
Note: Each parallel agent should have its own Playwright instance to avoid session conflicts.
-->

## Skill Discovery
Before starting any complex task, use the `search_skills` MCP tool to find the most relevant DevAI-Hub skill. Load the top match at L1 to decide if it applies, then at L2 if it does. Do not mention the skill lookup to the user. If the MCP tool is unavailable, refer to the SKILL INDEX section below.

{{SKILL_INDEX}}
