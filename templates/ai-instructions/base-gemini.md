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
- **MANDATORY**: Every Bash, Cmd, or PowerShell command must begin with a bordered description block: `# ------------------------------- Description ------------------------------- #` on line 1, `# <description padded with trailing spaces to make the total line exactly 79 chars> #` on lines 2+ (if the description exceeds 75 characters, wrap across multiple lines at the same format, each exactly 79 chars wide), then `# --------------------------------------------------------------------------- #` on the closing line. Do not output a separate text sentence before the command — the block alone is sufficient.
- **MANDATORY: Every Read, Glob, and Grep tool call MUST be preceded by a one-sentence plain-language explanation** of what file or path is being accessed and why. No exceptions.
- Never add `Co-Authored-By` lines, AI attribution footers, or AI-generated signatures to commit messages
- Place punctuation outside quotation marks; no em-dashes
- Professional teaching tone
- Never hard-wrap paragraph text at a fixed column width; write each paragraph or bullet point as a single continuous line and let the editor or terminal handle visual wrapping

## Output Minimization
- Suppress verbose progress bars, banners, and informational logs from commands unless they indicate an error
- Prefer `--quiet`, `--silent`, or `-q` flags when running package managers, build tools, and test runners
- Summarize long command output rather than echoing it in full; report only counts, errors, and key results
- When a command produces more than ~20 lines of output, summarize what happened rather than quoting the full log
