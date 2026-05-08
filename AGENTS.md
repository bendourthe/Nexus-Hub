# AGENTS.md

This file provides guidance to AI coding agents (Claude Code, Cursor, Copilot, Gemini CLI, etc.) when working with code in this repository.

## Repository Overview

DevAI-Hub is a production-grade skill catalog for AI coding assistants. It is a **template repository** — skills, commands, hooks, agents, and rules are distributed via installer scripts into users' `.claude/` directories. The repo itself is the source of truth; it is not deployed as a running application.

Current catalog: **187 skills** across 22 categories, 32 commands, 13 hooks, 10 agents.

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
│   └── skills/               # 187 skills across 22 categories
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

**Description style: combat undertriggering.** The `description` field above is what the AI agent scans when deciding whether to trigger this skill. Claude has a measurable tendency to **under-trigger** when the description is narrow, clean, or implicit. The fix is not a longer description — it is a **pushy** description that lists trigger phrases AND skip phrases explicitly. Rules:

- **List trigger phrases verbatim.** If the user is likely to say "build me a dashboard", "show internal metrics", "visualize the data", put those exact phrases in the description.
- **Add a SKIP clause.** Use `SKIP: ...` or `Do NOT use for: ...` to fence off look-alike requests the skill should not handle. This is what stops over-triggering after you make the description pushier.
- **Cover synonyms and adjacent intents.** A description for a "dashboard" skill should also cover "internal metrics", "data visualization", "company data display" — not just the literal word "dashboard".
- **Lead with the action, then the trigger surface.** First sentence states what the skill does; second sentence lists when to invoke it; third sentence (if needed) lists when to skip.

Before / after example:

- **Before** (narrow, agent under-triggers): "How to build a dashboard."
- **After** (pushy, agent triggers reliably without false positives): "How to build a dashboard. Make sure to use this skill whenever the user mentions dashboards, data visualization, internal metrics, or wants to display any kind of company data, even if they don't explicitly ask for a 'dashboard'. SKIP: standalone chart generation, one-off data exports, or read-only status pages without filtering controls."

The "After" form trades 6 words for 60. Those 60 words pay for themselves the first time the agent would have skipped a relevant invocation under the "Before" form. See `catalog/skills/workflow/create-custom-command/SKILL.md` for the same rule applied to commands.

#### Three-Tier Loading Model

Every DevAI-Hub skill is consumed by the agent in three tiers of progressive disclosure. Authoring decisions (what goes in the frontmatter, what goes in the body, what gets bundled in subdirs) follow directly from this model, so internalize it before writing the body.

1. **Tier 1 — always loaded** (~150-300 tokens total): `name`, `description`, `summary_l0`, `overview_l1`. Every active session has these in context for every catalog skill, all the time. They determine whether the skill triggers. Tier 1 is the only tier under direct token-budget pressure across the catalog.
2. **Tier 2 — loaded on trigger**: the SKILL.md body. Loaded once the agent decides this skill is relevant to the current task. Target ≤500 lines; soft cap 800 lines (see the size-norm rule below). Tier 2 is the agent's working manual for the skill — instructions, rationalizations, verification, related-skills cross-links.
3. **Tier 3 — loaded on demand**: bundled resources under per-skill `scripts/`, `references/`, `assets/` subdirectories (the convention introduced in Phase 3 of `docs/v1.1.5/plans/adoption-skills.md`, item A13). Two access patterns:
    - **Reference files** (`references/<topic>.md`) load into context only when the agent reads them. The body should link to a reference file the way it would link to an external doc — "see `references/fastmcp-runbook.md` for the full setup steps" — so the agent only pays for it when needed.
    - **Scripts** (`scripts/<name>.{py,sh,js}`) execute via the Bash / shell tool **without their source code being loaded** into the context window. This is the critical performance affordance: a skill can bundle a 2000-line generator script that runs deterministically on demand, and the agent never reads a single line of it. Scripts are how a skill ships heavy capability without inflating Tier 2.

Practical implications for SKILL.md authoring:

- Resist the urge to inline everything into the body. If a piece of content is needed only some of the time, push it to a reference file.
- If a step is deterministic and could be a 50-line shell script instead of 200 lines of body prose, ship the script under `scripts/` and let the agent execute it.
- Keep Tier 1 fields tight (especially `description` and `summary_l0`); they cost tokens on every catalog read across every session. Tier 2 / Tier 3 budgets are per-trigger, not per-session.

Cross-links: the body-size targets sit in the size-norm rule immediately below. The bundled-subdir convention is documented separately in the "Per-skill Bundled Resources" subsection further down.

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

**SKILL.md size norm.** Target ≤500 lines for the SKILL.md body. Soft cap 800 lines. Beyond 500 lines, add a `references/` subdirectory with a table of contents and link to it from SKILL.md rather than expanding the body. Beyond 800 lines, the skill MUST be split or refactored before merge. Existing skills that exceed 500 lines are grandfathered — this norm is forward-looking and applies to new and substantially-rewritten skills only.

#### Per-skill Bundled Resources

A skill folder MAY (not MUST) contain three bundled subdirectories alongside `SKILL.md`:

```
catalog/skills/<category>/<skill-name>/
├── SKILL.md
├── scripts/         # optional - executable code for tier-3 deterministic operations
├── references/      # optional - Markdown docs the agent reads on demand
└── assets/          # optional - templates, icons, fonts, fixtures used by scripts or referenced from SKILL.md
```

This convention is the operational expression of Tier 3 in the [Three-Tier Loading Model](#three-tier-loading-model) above. It allows a skill to ship heavy capability (long runbooks, large generator scripts, design templates) without inflating the SKILL.md body or the always-loaded Tier 1 metadata.

**File naming**:

- `scripts/<name>.{py,sh,js,ps1}` - kebab-case, descriptive (e.g., `init-mcp-fastmcp.sh`, `package_skill.py`). PowerShell siblings (`.ps1`) MUST accompany every `.sh` script that ships under `scripts/` so Windows users get the same capability.
- `references/<topic>.md` - kebab-case, scoped by topic (e.g., `references/fastmcp-runbook.md`, `references/schemas.md`). Each reference file should be self-contained — the agent reads it cold without the rest of the skill bundle in context.
- `assets/<descriptive-name>.<ext>` - any extension. Examples: `assets/flow-field.html`, `assets/themes/editorial-serif.json`, `assets/fonts/Inter.woff2`.

**Reference rule**: every file under `scripts/`, `references/`, `assets/` MUST be referenced at least once from the parent SKILL.md (or from another file in the bundle that is itself referenced). The validator enforces this — see "Orphan-bundle detection" below. Empty subdirectories are tolerated only when they hold a single `.gitkeep` placeholder for a future expansion.

**Installer behavior**: both `scripts/installer.sh` and `scripts/installer.ps1` recursively copy the entire skill directory tree (`safe_folder_copy` / `Safe-Folder-Copy` use `rsync -a` / `cp -R` / `robocopy /MIR` respectively). Per-skill `scripts/`, `references/`, `assets/` subdirectories therefore land at the platform target alongside SKILL.md without any installer edit. This is the auto-distribution path called out in row 1 of the [Distribution channels the installer uses](#distribution-channels-the-installer-uses) table; it explicitly does NOT require the explicit-name copy step that repo-level `scripts/<name>.py` artifacts require.

**Orphan-bundle detection**: `make validate` runs `scripts/validate_skills.py`, which now performs a per-skill bundle audit:

1. List every file under `scripts/`, `references/`, `assets/` for each skill.
2. Search the parent SKILL.md (and each `references/*.md`) for the file's basename.
3. Emit a warning for each unreferenced file, with the suggestion: "either reference this file from SKILL.md or remove it." `.gitkeep` is the only filename exempt from the reference check.

The check is a warning (not error) by default so that work-in-progress branches do not break CI. Orphan reports surface in the verbose output (`make validate` prints them at the end of the run when `--verbose` is passed, and pytest's `test_skill_bundles.py` asserts the validator detects an injected orphan in a fixture skill).

**Cross-links**: see [Three-Tier Loading Model](#three-tier-loading-model) for the loading-cost rationale, the [SKILL.md size norm](#skill-md-size-norm) for when to push body content into `references/`, and the v1.1.3 four-hook precedent (`catalog/hooks/{claude,gemini,codex,opencode}-diff-review.sh`) for the parity invariant that applies when a `scripts/` directory ships per-CLI variants.

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

## Markdown Style for Generated Documentation

Every Markdown file DevAI-Hub generates or modifies (READMEs, CHANGELOG, DEVLOG, RELEASE_NOTES, plans, comparison reports, pen test reports, session histories, skills, commands, generated `/generate-report` and `/compile-deep-research` outputs) must follow the conventions in [`catalog/style-guides/markdown.md`](catalog/style-guides/markdown.md). The guide is also installed at `~/.devai-hub/style-guides/markdown.md` for global reference.

The most common rendering bugs that the style guide prevents:

- **No blank line before a list** - the list runs into the preceding paragraph in some renderers
- **Tight lists with multi-sentence items** - the list looks compressed; loose lists (blank lines between items) read better when items have body content
- **2-space indent for nested lists** - fragile across renderers; use 4-space indent
- **Code blocks inside list items without blank lines around the fence** - render as inline preformatted text instead of a code block

Quick reference (full rules and examples in the style guide):

- Blank line before AND after every list, code block, table, and heading.
- `-` for unordered lists, `1. 2. 3.` for ordered. Single space after the marker.
- Nested lists use 4-space indent.
- Code blocks inside list items: blank line before/after the fence; 4-space indent for the fence (top-level item) or 8-space (nested item).
- Headings are ATX-style (`#`), one H1 per document, no level skipping.
- Each paragraph or list item is a single continuous line in source - never hard-wrap.
- English Markdown is ASCII-only (hyphens, straight quotes, `...`). Other-language Markdown uses the language's native punctuation.

Before committing any generated Markdown, the agent should run a quick self-check against the verification list at the end of `catalog/style-guides/markdown.md`.

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
| `catalog/commands/<name>.md` | No — folder auto-copied | Claude (`commands/`), Gemini (`workflows/`), Codex (`prompts/`). Cursor / OpenCode / Copilot do not get a slash surface — they see the command body only if the user invokes it manually. |
| `catalog/style-guides/<name>.md` (companion reference for a command, NOT a slash command) | No — folder auto-copied to `~/.devai-hub/style-guides/` by `install_templates` | All platforms (shared). Located outside `catalog/commands/` so the file does not surface in the slash menu. |
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
