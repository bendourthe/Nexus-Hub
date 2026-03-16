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
- **MANDATORY: Every Bash command must start with `# Description: <one sentence>` as its first line.** This comment is visible in the approval dialog and is enforced by the `require-description.sh` PreToolUse hook, which blocks any command that omits it. Example: `# Description: Checks whether the installer script has valid bash syntax` on line 1, then the command on line 2+. Applies to all commands including single-liners, pipelines, and heredocs. Bash ignores `#` comment lines at runtime so there is no side effect.
- **MANDATORY: Every Read, Glob, and Grep tool call MUST be preceded by a one-sentence plain-language explanation** of what file or path is being accessed and why. No exceptions.
- Ask clarifying questions before coding if requirements are ambiguous

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

## MCP Integration
{{MCP_STATUS}}
<!-- Optional section. Document active MCP servers and their purpose.
Active servers:
- filesystem: Read/write workspace files (stdio)
- playwright: Browser automation for web tasks (stdio, per-agent instance)

Configuration: .mcp.json at project root
Note: Each parallel agent should have its own Playwright instance to avoid session conflicts.
-->
