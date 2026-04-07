# AGENTS.md

This file provides guidance to AI coding agents (Claude Code, Cursor, Copilot, Gemini CLI, etc.) when working with code in this repository.

## Repository Overview

DevAI-Hub is a production-grade skill catalog for AI coding assistants. It is a **template repository** — skills, commands, hooks, agents, and rules are distributed via installer scripts into users' `.claude/` directories. The repo itself is the source of truth; it is not deployed as a running application.

Current catalog: **184 skills** across 22 categories, 32 commands, 13 hooks, 10 agents.

## Project Structure

```
DevAI-Hub/
├── catalog/                  # Master templates (distributed to users)
│   ├── agents/               # 10 agent YAML definitions
│   ├── checklists/           # Standalone reference checklists (4 files)
│   ├── commands/             # 32 slash command .md files
│   ├── context/              # Context template files
│   ├── hooks/                # Hook scripts + settings.json template
│   │   └── tests/            # pytest suite for hook scripts
│   ├── mcp-configs/          # MCP server registry
│   ├── memory/               # Memory template files
│   ├── rules/                # Code style/security rules (4 languages)
│   └── skills/               # 184 skills across 22 categories
│       └── <category>/
│           └── <skill-name>/
│               └── SKILL.md
├── data/                     # Generated catalog metadata (do not edit manually)
│   ├── SKILL_INDEX.md        # Auto-generated skill index
│   ├── skills.json           # Machine-readable skill catalog
│   ├── marketplace.json      # Plugin registry metadata
│   └── bundles.json          # Skill bundle definitions
├── configs/                  # Permission configs per AI provider
├── docs/                     # Documentation and analysis reports
├── extensions/               # VS Code extension + MCP server
├── guides/                   # Developer guides
├── scripts/                  # Installer scripts (installer.sh, installer.ps1)
└── templates/                # AI instruction templates for multi-IDE support
```

## Adding a New Skill

### 1. Choose the right category

Existing categories: `ai-development`, `architecture`, `bug-fixing`, `business-product`, `code-cleanup`, `code-review`, `compliance`, `developer-experience`, `documentation`, `framework-specialists`, `infrastructure`, `language-specialists`, `orchestration`, `project-setup`, `research`, `security`, `specialized-domains`, `testing`, `tests-generation`, `workflow`.

If none fit, discuss with maintainers before creating a new category.

### 2. Create the skill directory

```
catalog/skills/<category>/<skill-name>/
└── SKILL.md
```

Naming convention: `kebab-case`, descriptive but concise (e.g., `spec-driven-development`, not `how-to-write-specs`).

### 3. Write SKILL.md

Required YAML frontmatter fields:

```yaml
---
name: <skill-name>                    # matches directory name
description: <one sentence>           # trigger phrases + when to use
summary_l0: "<summary in quotes>"    # ≤15 words; loaded in skill index
overview_l1: "<paragraph in quotes>" # ≤150 words; loaded on L1 match
---
```

Required body sections (in order):

```markdown
# Title

Brief intro paragraph.

## When to Use This Skill

Bullet list of trigger scenarios. Include explicit "When NOT to use" guidance.

## Instructions

Step-by-step process. Use numbered steps and code blocks.

## Common Rationalizations

Table of excuses the agent might use to skip this skill — with rebuttals.

| Rationalization | Reality |
|---|---|
| "This is too simple for this skill" | Even simple tasks benefit from... |

Each entry must cite a concrete failure mode, not a generic principle.

## Verification

Binary checklist. Each item must describe an observable artifact or state.

- [ ] The output file exists at <path>
- [ ] All tests pass: `<test command>`
- [ ] No linting errors: `<lint command>`

"The code looks good" is not a valid verification criterion.

## Related Skills

- `<skill-name>` — one sentence on the relationship
```

**Keep SKILL.md under 800 lines.** Put long reference material in a `references/` subdirectory and link to it.

### 4. Register the skill

After creating SKILL.md, update these three files:

**`data/SKILL_INDEX.md`** — add one row to the table:
```
| <skill-name> | <Category> | "<summary_l0>" | catalog/skills/<category>/<skill-name>/SKILL.md |
```

**`data/skills.json`** — add one entry to the `"skills"` array following the existing schema (name, title, description, long_description, summary_l0, overview_l1, version, author, category, language, tags, priority, based_on, tools_required, path, file, size, downloads, status, security).

**`data/marketplace.json`** — increment `skill_count` in the relevant category entry and update `"total_skills"` in `statistics`.

### 5. Validate

Run `make validate` to check JSON catalog integrity. Run `make lint` to check shell scripts with ShellCheck.

## Adding a New Command

Commands are Markdown files in `catalog/commands/`. Each file is a slash command that Claude Code users can invoke with `/<filename-without-extension>`.

File naming: `kebab-case.md`. Commands use the same SKILL.md conventions for instructions but do not need frontmatter.

After adding a command, update `data/marketplace.json` `"total_commands"` if that field is present.

## Adding or Modifying a Hook

Hook scripts live in `catalog/hooks/`. Rules:

- Bash scripts: use `#!/usr/bin/env bash` and `set -euo pipefail`
- Python scripts: include a module docstring and type annotations
- All hooks: write error messages to stderr, write output to stdout
- Security hooks (secret-scan, large-file-guard): follow the patterns in `catalog/rules/bash/security.md`

The hook registration template is `catalog/hooks/settings.json`. Supported events: `SessionStart`, `PreToolUse`, `PostToolUse`, `Stop`.

**Write tests for any new hook** following the pytest pattern in `catalog/hooks/tests/test_format_bash_description.py`. Run with `make test`.

## Running Validation

```bash
make validate    # JSON catalog integrity
make lint        # ShellCheck on all hook scripts
make test        # pytest hook test suite
make build-catalog  # Rebuild data/ from catalog/
```

## Critical Conventions

- **Never edit `data/` files manually** unless registering a new skill — they are generated. The source of truth is `catalog/skills/`.
- **Never commit secrets.** The `secret-scan.sh` hook checks Write/Edit operations.
- **Destructive git commands require confirmation.** The `git-guardrails.sh` hook enforces this.
- **SKILL.md summaries must be quoted strings.** The MCP server depends on YAML-parseable frontmatter.
- **skills.json security scores** (`structural`, `integrity`, `semantic`) default to 100/100/95 for new skills; adjust if the skill has known limitations.

## Boundaries

**Always do:**
- Run `make validate` after modifying any `data/*.json` file
- Include `summary_l0` and `overview_l1` in every SKILL.md (required by the MCP server)
- Write both Common Rationalizations and Verification sections in new skills
- Follow the bash safety rules in `catalog/rules/bash/`

**Ask first:**
- Creating a new skill category
- Modifying installer scripts (`scripts/installer.sh`, `scripts/installer.ps1`)
- Changing hook logic in `catalog/hooks/settings.json`
- Bumping version numbers

**Never do:**
- Delete existing skills without maintainer approval
- Commit node_modules, .env files, or generated build artifacts
- Skip `make validate` when touching `data/*.json`
- Remove the `summary_l0` or `overview_l1` frontmatter fields (breaks MCP discoverability)
