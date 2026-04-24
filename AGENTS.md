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

## MCP Registry Policy

DevAI-Hub ships `catalog/mcp-configs/mcp-servers.json` as a curated registry of MCP server configurations. Users copy the entries they need into their own `.claude/settings.json`. Because these snippets cause users' agents to spawn local subprocesses that may reach out to external APIs, every registry entry is a security decision. This section defines what qualifies a server for inclusion.

**Guiding principle**: priority is always to reverse-engineer and recreate locally. Trusted vendors are accepted only for parts that cannot be reverse-engineered AND where the feature is extremely worth it.

### Decision Tree (stop at the first bucket that fits)

1. **Local-only**: internal DevAI-Hub servers (`devai-skill-server`, `devai-code-search`, `devai-web-fetch`) or Anthropic-official servers that make zero outbound calls (`filesystem`, `memory`, `sequential-thinking`, `sqlite`). **Always allowed.**
2. **LLM-native skill** (zero code, zero MCP): if the capability can be achieved by instructing the agent's own LLM (e.g. "generate a React component with these props", "explain this stack trace"), ship a skill in `catalog/skills/`, not an MCP. **Preferred over any external wrapper.**
3. **Reverse-engineerable into a local internal MCP**: if the external project wraps logic that can run locally (HTTP fetch + HTML parsing, tree-sitter chunking, BM25 keyword search, local embeddings), **build the internal equivalent** under `extensions/`. Strip external-source attribution from the implementation and documentation; use generic descriptive names for the package, the registry key, and the tool names.
4. **Trusted vendor wrapper (your-own-account)**: acceptable only when **all three** conditions hold:
   1. The third party is the intrinsic data destination — you are already a customer of the vendor (GitHub, Supabase, Railway, Vercel, Cloudflare, your own Postgres).
   2. The capability cannot be reverse-engineered locally (or reverse-engineering duplicates effort without reducing data-flow surface).
   3. The feature is extremely worth it.
   The `_comment` field on the registry entry must explicitly justify each of the three conditions.
5. **Otherwise**: drop. Do not ship the entry.

### Five-Question Audit Checklist

Every registry entry's `_comment` field must answer these five questions (one sentence each):

1. Who runs the process?
2. What outbound calls does it make and where?
3. What API keys does it require?
4. Does it transmit source code, prompts, or query text to a third party?
5. Does the user already have a commercial relationship with the destination?

### Hard-No List

Search-as-service, embeddings-as-service, scraping-as-service, and generation-as-service are categorically not allowed. Explicit examples that have been considered and rejected: Upstash/context7, Exa, Firecrawl, 21st.dev/magic-ui, Zilliz/claude-context. If a capability in this class has value, reverse-engineer the pattern into an internal MCP or skill (see tiers 2 and 3 above).

### Matrix Requirement

Every MCP listed in `catalog/mcp-configs/mcp-servers.json` must have a corresponding row in `docs/v1.0.0/mcp-reverse-engineering-matrix.md`. The matrix is the authoritative classification document for the registry. Future additions require a matrix row with upstream evidence and a decision-tree classification.

### Reverse-Engineering Attribution Rule

When reverse-engineering an external pattern into DevAI-Hub content (a skill, a command, an internal MCP), do not name the specific external repo, product, or evaluation metric in the user-facing artifact. Use generic descriptive names (e.g. "code-semantic-search" instead of naming a specific upstream implementation). Attribution belongs in the reverse-engineering matrix row's `Rationale` column, not in the distributed artifact.

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

## Installer-Aware Changes (Cross-Platform)

DevAI-Hub is a **template repository**. Nothing you add is "live" until a user runs `scripts/installer.sh` (macOS/Linux) or `scripts/installer.ps1` (Windows). The installer is what distributes your changes across every supported agentic platform.

**Golden rule**: every change you propose must be shaped so that after the next installer run, it reaches Claude Code, Cursor, Codex, Gemini/Antigravity, OpenCode, and Copilot — on Windows, macOS, and Linux — without any manual step on the user's part.

### Distribution channels the installer uses

| Artifact you add/modify | Installer edit required? | Platforms reached |
|---|---|---|
| `catalog/skills/<cat>/<name>/SKILL.md` | No — folder auto-copied | Claude, Gemini, Codex (under `skills/`); Cursor/OpenCode/Copilot via the `{{SKILL_INDEX}}` block in their instruction file |
| `catalog/commands/<name>.md` (+ companion style guide) | No — folder auto-copied | Claude (`commands/`), Gemini (`workflows/`), Codex (`prompts/`). Cursor / OpenCode / Copilot do not get a slash surface — they see the command body only if the user invokes it manually. |
| `catalog/agents/<name>.md` | No — folder auto-copied | Claude, Gemini, Codex |
| `catalog/hooks/<name>.{sh,py}` | No for the file; **you must register it** in `catalog/hooks/settings.json` | Platforms that honor Claude-style hooks |
| `catalog/rules/<lang>/<name>.md` | No — folder auto-copied | Claude, Gemini, Codex |
| `templates/documentation/<name>.{docx,pptx,xlsx,...}` | No — folder auto-copied to `~/.devai-hub/templates/documentation/` | All platforms (shared) |
| `templates/ai-instructions/base-*.md` | **Yes — edit all 5 in lockstep** (claude, codex, cursor, gemini, opencode) | The respective platform |
| `scripts/<name>.py` or `scripts/<name>.js` | **Yes — MUST add a copy step** in BOTH `scripts/installer.sh` AND `scripts/installer.ps1`, modeled after the existing `generate_report.py` entry. The installer copies scripts by **explicit name**, never by folder. | All platforms (shared under `~/.devai-hub/scripts/`) |
| `data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json` | No — the installer reads these to fill `{{SKILL_INDEX}}` placeholders in every platform's instruction file. Updating them is mandatory when adding a skill. | All platforms whose instruction template embeds the index |

### Required steps for any change

Walk this checklist before proposing a PR:

1. **Is your change inside a folder already copied recursively by the installer?** (`catalog/skills/`, `catalog/commands/`, `catalog/agents/`, `catalog/rules/`, `catalog/hooks/`, `templates/documentation/`.) If yes, no installer edit needed.
2. **Is your change a standalone script in `scripts/`?** If yes, add a copy line in `scripts/installer.sh` (next to the existing `generate_report.py` block, around line 1395) AND a `Safe-Copy` line in `scripts/installer.ps1` (around line 1656). Both must reference the same destination under `~/.devai-hub/scripts/`.
3. **Does your change introduce a new Python or Node dependency?** Prefer a lazy import with a clear `pip install <pkg>` hint on failure (e.g., `try: import X; except ImportError: print("Error: X not installed. Please run: pip install X")`, as used in `scripts/generate_report.py`). If a hard requirement is unavoidable, add a dependency check in both installers next to the existing `python-docx`/`python-pptx` check.
4. **Does your change touch a platform-specific instruction template?** If you edit any of `templates/ai-instructions/base-*.md`, apply the same change to all five (claude/codex/cursor/gemini/opencode). This is the "platform-agnostic" constraint.
5. **Validate**: run `make validate` (JSON integrity) and `make lint` (ShellCheck) after edits. For new hooks, run `make test`. For installer changes, do a dry-run install into a throwaway directory and confirm the new artifact lands at the expected path.
6. **Document**: add an entry under `## [Unreleased]` in `CHANGELOG.md`.

### Platform coverage caveats (current state)

The installer currently deploys **skills, commands, agents, hooks, and rules as separate files** only to Claude Code, Gemini/Antigravity, and Codex. Cursor, OpenCode, and Copilot receive **behavioral guardrails only** via their respective instruction files (`AGENTS.md`, `.github/copilot-instructions.md`, `.cursor/rules/`), not a per-command file-tree copy. If your change is a new slash command, call this out in the CHANGELOG so users on those three platforms know they need to either invoke the underlying skill by name or follow the command body as a prompt.

If broader per-file distribution to Cursor/OpenCode/Copilot is needed, that is a cross-cutting installer change — not something to bolt on inside a single feature PR.

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
