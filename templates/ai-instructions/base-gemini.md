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
- **MANDATORY**: When using the Bash tool, always provide a `description` as **plain text only** (a single sentence or short paragraph). Do NOT add borders, boxes, `#` characters, padding, or any manual formatting to the description. A PreToolUse hook (`format-bash-description.py`) handles all formatting automatically.
- **MANDATORY: Every Read, Glob, and Grep tool call MUST be preceded by a one-sentence plain-language explanation** of what file or path is being accessed and why. No exceptions.
- Never add `Co-Authored-By` lines, AI attribution footers, or AI-generated signatures to commit messages
- Commit messages must be ASCII-only: no em-dashes, en-dashes, curly quotes, ellipsis characters, or other Unicode punctuation. Use hyphens, straight quotes, and `...` instead. This prevents encoding corruption on Windows.
- Use `docs/todos.md` as the project progress tracker: read it at session start if it exists, check off completed tasks, add newly identified work, and update dashboard metrics after relevant milestones. Use the dev-progress-tracker skill to create or maintain it.
- Place punctuation outside quotation marks; no em-dashes
- Professional teaching tone
- Never hard-wrap paragraph text at a fixed column width; write each paragraph or bullet point as a single continuous line and let the editor or terminal handle visual wrapping

## Output Minimization
- Suppress verbose progress bars, banners, and informational logs from commands unless they indicate an error
- Prefer `--quiet`, `--silent`, or `-q` flags when running package managers, build tools, and test runners
- Summarize long command output rather than echoing it in full; report only counts, errors, and key results
- When a command produces more than ~20 lines of output, summarize what happened rather than quoting the full log

## Skill Discovery
When the user's request matches a skill in the SKILL INDEX below, read the full skill file from the path listed and follow its instructions. Do not mention the skill lookup to the user.

{{SKILL_INDEX}}
