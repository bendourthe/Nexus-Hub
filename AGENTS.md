# AGENTS.md

<!-- nexus-hub-version: 3.14.3 -->

This file provides guidance to AI coding agents (Claude Code, Cursor, Copilot, Gemini CLI, etc.) when working with code in this repository.

## Repository Overview

Nexus-Hub is a production-grade skill harness for AI coding assistants. It is the **upstream catalog** consumed by Nexus (the local-first desktop AI Studio, see `https://github.com/bendourthe/Nexus-AI`) and by every other major agent platform: Claude Code, OpenAI Codex, Gemini (via Antigravity), GitHub Copilot, Cursor, and GitHub CLI. Skills, commands, hooks, agents, and rules are distributed via installer scripts into users' `~/.nexus-hub/` directory and into their AI assistant's per-platform config locations.

Current catalog: **267 skills** across 21 categories, 16 commands (plus 3 permanent aliases), 28 hooks, 23 agents. The 40 v3.x deprecation shims were removed in v3.2.0.

## Project Structure

```
Nexus-Hub/
├── catalog/                  # Master templates (distributed to users)
│   ├── agents/               # 23 agent YAML definitions
│   ├── checklists/           # Standalone reference checklists (4 files)
│   ├── commands/             # 15 active command .md files (+ 3 permanent aliases; the 40 v3.x shims were removed in v3.2.0)
│   ├── context/              # Context template files
│   ├── hooks/                # Hook scripts + settings.json template
│   │   └── tests/            # pytest suite for hook scripts
│   ├── mcp-configs/          # MCP server registry
│   ├── memory/               # Memory template files
│   ├── rules/                # Code style/security rules (4 languages)
│   └── skills/               # 267 skills across 21 categories
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

Existing categories: `ai-development`, `architecture`, `bug-fixing`, `business-product`, `code-cleanup`, `code-review`, `compliance`, `developer-experience`, `documentation`, `framework-specialists`, `infrastructure`, `language-specialists`, `orchestration`, `project-setup`, `research`, `security`, `security-operations`, `specialized-domains`, `testing`, `tests-generation`, `workflow`.

The `security` category holds application-security skills (authentication, dependency/CVE analysis, exploitability, patch advice). The `security-operations` category (added v2.3.0) holds defensive operational skills: DFIR, threat hunting, detection engineering, incident response, and cloud / endpoint / identity / phishing detection. Place a new defensive-operations skill under `security-operations`; place an application-security or AppSec-review skill under `security`.

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

Every Nexus-Hub skill is consumed by the agent in three tiers of progressive disclosure. Authoring decisions (what goes in the frontmatter, what goes in the body, what gets bundled in subdirs) follow directly from this model, so internalize it before writing the body.

1. **Tier 1 — always loaded** (~150-300 tokens total): `name`, `description`, `summary_l0`, `overview_l1`. Every active session has these in context for every catalog skill, all the time. They determine whether the skill triggers. Tier 1 is the only tier under direct token-budget pressure across the catalog.
2. **Tier 2 — loaded on trigger**: the SKILL.md body. Loaded once the agent decides this skill is relevant to the current task. Target ≤500 lines; soft cap 800 lines (see the size-norm rule below). Tier 2 is the agent's working manual for the skill — instructions, rationalizations, verification, related-skills cross-links.
3. **Tier 3 — loaded on demand**: bundled resources under per-skill `scripts/`, `references/`, `assets/` subdirectories (the convention introduced in Phase 3 of `docs/archive/v1/v1.1/plans/adoption-skills.md`, item A13). Two access patterns:
    - **Reference files** (`references/<topic>.md`) load into context only when the agent reads them. The body should link to a reference file the way it would link to an external doc — "see `references/fastmcp-runbook.md` for the full setup steps" — so the agent only pays for it when needed.
    - **Scripts** (`scripts/<name>.{py,sh,js}`) execute via the Bash / shell tool **without their source code being loaded** into the context window. This is the critical performance affordance: a skill can bundle a 2000-line generator script that runs deterministically on demand, and the agent never reads a single line of it. Scripts are how a skill ships heavy capability without inflating Tier 2.

Practical implications for SKILL.md authoring:

- Resist the urge to inline everything into the body. If a piece of content is needed only some of the time, push it to a reference file.
- If a step is deterministic and could be a 50-line shell script instead of 200 lines of body prose, ship the script under `scripts/` and let the agent execute it.
- Keep Tier 1 fields tight (especially `description` and `summary_l0`); they cost tokens on every catalog read across every session. Tier 2 / Tier 3 budgets are per-trigger, not per-session.

Cross-links: the body-size targets sit in the size-norm rule immediately below. The bundled-subdir convention is documented separately in the "Per-skill Bundled Resources" subsection further down.

#### Optional Security and Compliance Framework Mapping

Security and compliance skills MAY declare an optional set of cross-framework mapping fields in their YAML frontmatter. These fields are **non-required**, do **not** count toward Tier-1 token budget pressure for skills that omit them, and are validated as **optional** by `scripts/validate_skills.py` (their absence is never an error; their presence is checked for list shape only).

Available optional fields:

| Field | Framework | Example value |
|---|---|---|
| `mitre_attack` | MITRE ATT&CK techniques | `[T1071, T1003.001]` |
| `atlas_techniques` | MITRE ATLAS (adversarial ML) | `[AML.T0047, AML.T0049]` |
| `d3fend_techniques` | MITRE D3FEND defensive countermeasures | `[D3-NTA, D3-PA]` |
| `nist_csf` | NIST Cybersecurity Framework categories | `[DE.CM, RS.AN]` |
| `nist_ai_rmf` | NIST AI Risk Management Framework controls | `[MEASURE-2.6, GOVERN-1.1]` |

Example frontmatter for a defensive security skill:

```yaml
---
name: hunting-credential-dumping
description: <pushy description with trigger phrases and SKIP clause>
summary_l0: "Hunt for LSASS credential-dumping behavior across endpoint telemetry"
overview_l1: "<overview>"
mitre_attack: [T1003.001]
d3fend_techniques: [D3-PA, D3-PSA]
nist_csf: [DE.CM, DE.AE]
---
```

Companion file: when a skill declares any of these fields, it SHOULD ship a `references/standards.md` that documents the mapping (what each ID means, why it applies to this skill, and the public source URL for the framework definition). The orphan-bundle audit will warn if `references/standards.md` exists but is not referenced from `SKILL.md`; otherwise the file is purely additive.

These fields exist so a downstream generator (e.g. `scripts/build_framework_coverage.py`) can emit a coverage matrix across Nexus-Hub's security skills. They are NOT a substitute for the skill body — the body must still teach the agent what to do, with binary Verification and Common Rationalizations.

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

**Workflow templates (Dynamic Workflows)**: a skill MAY ship a Dynamic-Workflow JavaScript file (under its `scripts/` or `assets/` directory) and reference it from SKILL.md **as a template to adapt, not a verbatim script to run**. This is the workflow-as-skill-bundle distribution pattern: it lets a skill ship a ready-made fan-out harness (e.g. the dimensions -> find -> adversarially-verify review shape, or a fan-out -> fetch -> verify -> synthesize research shape) without inflating the SKILL.md body. Three rules are mandatory:

1. **Graceful degradation.** Dynamic Workflows is a plan-gated research-preview capability that may be absent in the user's harness. The template MUST fall back to isolated subagents (small surface) or a single sequential agent (smallest surface), and the skill MUST NOT hard-depend on the workflow runtime being present.
2. **Scope-first token caution.** Because a fan-out carries a 5-15x token multiplier, the template MUST carry the scope-first discipline inline: calibrate on one folder first, review the execution plan on the first trigger, and confirm before going full-scale. Cross-link `[[ai-billing-safeguards]]` for the hard budget controls.
3. **Skill-native.** The template introduces no outbound call, no dependency, and no credential; the subagents it spawns use only the harness's own tools.

Use `agent-orchestration-primitives` as the decision guide for whether a fan-out is warranted at all, and see its `assets/example-fanout-workflow.js` for the reference template. The orphan-bundle audit (below) applies unchanged: the `.js` file MUST be referenced from SKILL.md like any other bundled resource.

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

Nexus-Hub ships `catalog/mcp-configs/mcp-servers.json` as a curated registry of MCP server configurations. Users copy the entries they need into their own `.claude/settings.json`. Because these snippets cause users' agents to spawn local subprocesses that may reach out to external APIs, every registry entry is a security decision. This section defines what qualifies a server for inclusion.

**Guiding principle**: priority is always to reverse-engineer and recreate locally. Trusted vendors are accepted only for parts that cannot be reverse-engineered AND where the feature is extremely worth it.

### Decision Tree (stop at the first bucket that fits)

1. **Local-only**: internal Nexus-Hub servers (`nexus-skill-server`, `nexus-code-search`, `nexus-web-fetch`) or Anthropic-official servers that make zero outbound calls (`filesystem`, `memory`, `sequential-thinking`, `sqlite`). **Always allowed.**
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

Every MCP listed in `catalog/mcp-configs/mcp-servers.json` must have a corresponding row in `docs/policy/mcp-reverse-engineering-matrix.md`. The matrix is the authoritative classification document for the registry. Future additions require a matrix row with upstream evidence and a decision-tree classification.

### Reverse-Engineering Attribution Rule

When reverse-engineering an external pattern into Nexus-Hub content (a skill, a command, an internal MCP), do not name the specific external repo, product, or evaluation metric in the user-facing artifact. Use generic descriptive names (e.g. "code-semantic-search" instead of naming a specific upstream implementation). Attribution belongs in the reverse-engineering matrix row's `Rationale` column, not in the distributed artifact.

## Markdown Style for Generated Documentation

Every Markdown file Nexus-Hub generates or modifies (READMEs, CHANGELOG, DEVLOG, RELEASE_NOTES, plans, comparison reports, pen test reports, session histories, skills, commands, generated `/research report` and `/research compile` outputs) must follow the conventions in [`catalog/style-guides/markdown.md`](catalog/style-guides/markdown.md). The guide is also installed at `~/.nexus-hub/style-guides/markdown.md` for global reference.

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

**On a rename or deprecation**, decide whether to keep the old command name working through a deprecation shim at `catalog/commands/<old-name>.md` -- a `DEPRECATED (removed in vX.Y.Z). Forwarding to /NEW.` frontmatter `description` plus a short body that prints the notice and delegates to the new command -- or to remove it outright with a CHANGELOG `Removed` note. (The 40 v3.0.0-era shims followed the shim pattern and were removed in v3.2.0; see the v3.2.0 CHANGELOG and `docs/v3/v3.0/command-migration.md`.)

**Do not maintain a static command list anywhere.** `/skills list` derives the command cheatsheet -- the active commands, what each does, the deprecated name each one replaces, and common multi-command workflows -- at runtime from the command files themselves (see `catalog/style-guides/commands-cheatsheet.md`). Adding, renaming, refactoring, or deprecating a command therefore updates the cheatsheet automatically on the next `/skills list`; there is no table to hand-edit. The only command artifacts to touch on a change are the command file(s) and (on a rename) the deprecation shim.

## Model Routing in the Plan/Implement Loop

`/plan` performs a best-effort, platform-agnostic model-routing assessment per phase (added v3.4.0). After the phase breakdown is designed and before the plan file is written, it invokes the `model-routing` skill once per phase to score that phase's complexity and recommend a model plus reasoning effort, defaulting to the strongest available tier on any uncertainty or high-risk signal. The recommendation is recorded in the plan as a platform-agnostic tier intent ("strong reasoning tier, high effort") alongside the concretely-enumerated model id and effort when enumeration succeeds, surfaced in the "Phases at a Glance" "Rec. model / effort" column and each phase's `**Recommended model**` field. The step degrades silently: when the routing skill or live model enumeration is unavailable (no platform surface, offline, or a manual-only platform), each phase carries the neutral `assess at implementation time` placeholder and the plan is still valid. The heavy logic stays in the skill; `model-routing` adds no outbound call, dependency, or credential, and `/plan` and the retained planning skill stay thin dispatchers over it. This is command + skill behavior, NOT a `base-*.md` lockstep change -- routing is opt-in via the plan/implement steps, not always-loaded instruction text.

`/implement` re-confirms that recommendation at the start of each phase, before the subtask-by-subtask build step (added v3.4.0 Phase 4). It reads the phase's `**Recommended model**` field, invokes the `model-routing` skill to re-assess against the currently-enumerated models -- so a plan built before a new model release picks up the newer or cheaper option at implementation time -- and applies the same confirm-then-auto-execute posture per platform tier; if the re-assessment disagrees with the plan it surfaces the delta and defaults to the stronger option (the no-degradation guarantee). The pre-flight is best-effort and never blocks: when routing or enumeration is unavailable it proceeds on the plan's recommendation (or the session's current model) with a one-line note. Separately, the `/implement` troubleshooting loop may UPSHIFT to a stronger tier or higher effort when a phase's tests fail repeatedly (an under-tiering signal) -- upshift only, with confirmation, never an automatic mid-phase downshift (see the mid-task escalation rule in the `model-routing` skill). Like the planning-time assessment, this is command + skill + docs behavior, NOT a `base-*.md` lockstep change, and adds no outbound call, dependency, or credential. The standalone `/route` command (v3.4.0 Phase 2) runs the same assessment on demand for any task or plan phase.

## Adding or Modifying a Hook

Hook scripts live in `catalog/hooks/`. Rules:

- Bash scripts: use `#!/usr/bin/env bash` and `set -euo pipefail`
- Python scripts: include a module docstring and type annotations
- All hooks: write error messages to stderr, write output to stdout
- Security hooks (secret-scan, large-file-guard): follow the patterns in `catalog/rules/bash/security.md`

The hook registration template is `catalog/hooks/settings.json`. Supported events: `SessionStart`, `PreToolUse`, `PostToolUse`, `Stop`.

**Write tests for any new hook** following the pytest pattern in `catalog/hooks/tests/test_format_bash_description.py`. Run with `make test`.

### Workflow-phase automation (N1a)

To run automation at a `/plan`, `/implement`, or `/spec` **phase boundary**, do NOT invent new harness event types and do NOT import a Spec Kit-style per-command `before_/after_` hook registry (that presupposes the declined third-party extension runtime -- see the v3.6.0 Spec Kit comparison, candidate N1b). A phase boundary surfaces as a specific tool call, so key a `PreToolUse` / `PostToolUse` matcher on it and let the hook inspect the tool input: match `Write`/`Edit` and gate on `tool_input.file_path` (a plan artifact under `docs/**/plans/`, a `spec.md`, a `tasks.md`, a `CHANGELOG.md`), or match `Bash` and gate on `tool_input.command` (a `git commit`). Use `SessionStart` / `Stop` for session-level setup/teardown. The four events relevant to workflow-phase automation are `SessionStart` / `PreToolUse` / `PostToolUse` / `Stop`; this is a usage pattern on the existing surface, not a new runtime. A runnable example ships as [`catalog/hooks/workflow-phase-notice.sh`](catalog/hooks/workflow-phase-notice.sh) (tested in `catalog/hooks/tests/test_workflow_phase_notice.py`) and is registered in the default `settings.json` `PostToolUse` chain; it is advisory only (exit 0) and is disabled per-session with `NEXUS_DISABLED_HOOKS=workflow-phase-notice` or `NEXUS_HOOK_PROFILE=minimal`. Full recipe (matcher-to-phase mapping, authoring rules, registration snippet): the "Workflow-phase automation recipe" in [`guides/reference/CLAUDE_CODE_SETTINGS_REFERENCE.md`](guides/reference/CLAUDE_CODE_SETTINGS_REFERENCE.md).

## Installer-Aware Changes (Cross-Platform)

Nexus-Hub is a **template repository**. Nothing you add is "live" until a user runs `scripts/installer.sh` (macOS/Linux) or `scripts/installer.ps1` (Windows). The installer is what distributes your changes across every supported agentic platform.

**Entry points (v3.7.0 install-UX overhaul)**: a clean machine installs via the one-line bootstrap -- `curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash` (macOS/Linux; `wget -qO-` fallback) or `irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1 | iex` (Windows). The root `install.sh` / `install.ps1` are dual-mode: run standalone they precheck dependencies, download the `main` tarball into `~/.nexus-hub/src`, and hand off to `scripts/installer.{sh,ps1}`; run inside a checkout they delegate exactly as before. The core installers (`scripts/installer.{sh,ps1}`) are **unchanged** by the bootstrap and still do all of the distribution work documented below -- the bootstrap only materializes the tree they run from, so the distribution channels and copy rules in this section are unaffected. `nexus-hub upgrade` (the CLI installed to `~/.nexus-hub/bin/`) re-runs this same idempotent bootstrap. Installs are no-prompt: global scope across every detected platform by default, with `--workspace` / `--platforms` / `--yes` for power users and CI (absent platforms skip-with-note; conflict-only overwrite confirmation).

**Golden rule**: every change you propose must be shaped so that after the next installer run, it reaches Claude Code, Cursor, Codex, Gemini/Antigravity, OpenCode, and Copilot — on Windows, macOS, and Linux — without any manual step on the user's part.

### Distribution channels the installer uses

| Artifact you add/modify | Installer edit required? | Platforms reached |
|---|---|---|
| `catalog/skills/<cat>/<name>/SKILL.md` | No — folder auto-copied | As of v3.12.0 every SKILL.md-standard platform (Claude, Codex/ChatGPT, Antigravity, Gemini, Gemini CLI, OpenCode, Nexus-AI) receives skills FLATTENED to `skills/<name>/` (one level, per the SKILL.md open standard) plus one skill per command (`$name`); Cursor/Copilot get skills via the `{{SKILL_INDEX}}` block in their instruction file. Exact per-platform read-paths: `docs/policy/platform-read-contracts.md` (the living contract, maintained by the `/update release` platform-contract-verification step). |
| `catalog/commands/<name>.md` | No — folder auto-copied | Claude (`commands/`), Gemini (`workflows/`), Codex (`prompts/`). Cursor and GitHub Copilot get a **user-global** slash surface too (v3.3.4): a global install mirrors every command into `~/.cursor/commands/<name>.md` and into VS Code's user-profile `prompts/<name>.prompt.md`, so `/<name>` works in any repo with no local install. As of v3.12.0 Antigravity 2.0 gets a global slash surface at `~/.gemini/config/global_workflows/` AND the open project's `.agents/workflows/` (the latter seeded by `nexus-hub init`), and every command is also emitted as a skill. OpenCode has no slash surface — it sees the command body only via its instruction file (and its skills folder). |
| `catalog/style-guides/<name>.md` (companion reference for a command, NOT a slash command) | No — folder auto-copied to `~/.nexus-hub/style-guides/` by `install_templates` | All platforms (shared). Located outside `catalog/commands/` so the file does not surface in the slash menu. |
| `catalog/agents/<name>.md` | No — folder auto-copied | Claude, Gemini, Codex |
| `catalog/hooks/<name>.{sh,py}` | No for the file; **you must register it** in `catalog/hooks/settings.json` | Platforms that honor Claude-style hooks |
| `catalog/rules/<lang>/<name>.md` | No — folder auto-copied | Claude, Gemini, Codex |
| `templates/documentation/<name>.{docx,pptx,xlsx,...}` | No — folder auto-copied to `~/.nexus-hub/templates/documentation/` | All platforms (shared) |
| `templates/ai-instructions/base-*.md` | **Yes — edit all 5 in lockstep** (claude, codex, cursor, gemini, opencode) | The respective platform |
| `scripts/<name>.py` or `scripts/<name>.js` | **Yes — MUST add a copy step** in BOTH `scripts/installer.sh` AND `scripts/installer.ps1`, modeled after the existing `generate_report.py` entry. The installer copies scripts by **explicit name**, never by folder. | All platforms (shared under `~/.nexus-hub/scripts/`) |
| `data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json` | No — the installer reads these to fill `{{SKILL_INDEX}}` placeholders in every platform's instruction file. Updating them is mandatory when adding a skill. | All platforms whose instruction template embeds the index |
| `scripts/lib/integrations/<platform>.py` (v2.1.0+) | No file-copy edit; **MUST** import + `_register()` the subclass in `scripts/lib/integrations/__init__.py::_register_builtins()`. The runner is invoked automatically by both installers for the extended-platform set. | The platform configured by the subclass (e.g., Antigravity 2.0, Gemini CLI, Nexus-AI for the v2.1.0 extended set; Claude / Codex / Cursor / Gemini / OpenCode / Copilot subclasses also exist for future v2.2.0 parity migration). |
| Project-local surfaces (called from `nexus-hub init` -- v2.2.0+) | No file-copy edit; override `wire_project_surfaces(self, ctx) -> WriteResult \| None` on the integration subclass. The `nexus-hub init` subcommand (bash: `scripts/installer.sh init`; PowerShell: `scripts/installer.ps1 init`) walks every registered integration and invokes the hook. | Any platform whose subclass overrides the hook. Currently `cursor` (writes `.cursor/rules/nexus-hub.mdc`), `claude` (writes `.claude/settings.json` permissions stub when absent), `antigravity2` (writes `.agents/workflows/<name>.md` command files, since Antigravity reads slash commands only from the open project's `.agents/`), and `copilot` (v3.11.0, OPT-IN: writes thin `.github/skills/<name>/SKILL.md` wrapper files for the `core-developer` bundle when `NEXUS_HUB_COPILOT_SKILLS=1`, upgrading Copilot from behavioral-guardrails-only to a native project Agent Skills surface; off by default because `.github/skills/` is commit-visible, never overwrites an existing file). |

### Required steps for any change

Walk this checklist before proposing a PR:

1. **Is your change inside a folder already copied recursively by the installer?** (`catalog/skills/`, `catalog/commands/`, `catalog/agents/`, `catalog/rules/`, `catalog/hooks/`, `templates/documentation/`.) If yes, no installer edit needed.
2. **Is your change a standalone script in `scripts/`?** If yes, add a copy line in `scripts/installer.sh` (next to the existing `generate_report.py` block, around line 1395) AND a `Safe-Copy` line in `scripts/installer.ps1` (around line 1656). Both must reference the same destination under `~/.nexus-hub/scripts/`.
3. **Does your change introduce a new Python or Node dependency?** Prefer a lazy import with a clear `pip install <pkg>` hint on failure (e.g., `try: import X; except ImportError: print("Error: X not installed. Please run: pip install X")`, as used in `scripts/generate_report.py`). If a hard requirement is unavoidable, add a dependency check in both installers next to the existing `python-docx`/`python-pptx` check.
4. **Does your change touch a platform-specific instruction template?** If you edit any of `templates/ai-instructions/base-*.md`, apply the same change to all five (claude/codex/cursor/gemini/opencode). This is the "platform-agnostic" constraint. It is machine-enforced: `scripts/check_base_template_parity.py` (run by `make validate` and in CI) fails when a shared section heading, a shared placeholder token, or an invariant block (Tech Stack, Key Commands, Branching, MCP Registry Policy) diverges across the five, while tolerating intentional per-platform lines (platform names, install paths). It is a repo-internal guard like `check_version_sync.py`, so it needs no `.ps1` sibling and no installer copy step.
5. **Validate**: run `make validate` (JSON integrity) and `make lint` (ShellCheck) after edits. For new hooks, run `make test`. For installer changes, do a dry-run install into a throwaway directory and confirm the new artifact lands at the expected path.
6. **Document**: add an entry under `## [Unreleased]` in `CHANGELOG.md`.

### Platform coverage caveats (current state)

> **Gemini CLI sunset**: per the 2026-05-21 Google Developers Blog announcement, Gemini CLI stops serving free / Google AI Pro / Ultra / GitHub-installed users on 2026-06-18. The standalone `gemini-cli` integration is now opt-in via the `--enterprise` installer flag (Bash: `scripts/installer.sh --enterprise`; PowerShell: `scripts/installer.ps1 -Enterprise`) and installs only when the user explicitly requests it. Non-enterprise users transition to Antigravity CLI, which is covered by the `antigravity2` integration (the desktop IDE and CLI share a backend per the same announcement; see [docs/archive/v2/v2.2/antigravity-cli-probe.md](docs/archive/v2/v2.2/antigravity-cli-probe.md)).

The installer deploys **skills, commands, agents, hooks, and rules as separate files** to the following platforms:

- **Original 4 (legacy installer copy blocks)**: Claude Code, Gemini/Antigravity 1.0, Codex, GitHub Copilot (Copilot receives behavioral guardrails via `.github/copilot-instructions.md` rather than a full file-tree copy).
- **Extended 4 (v2.2.0+, via integration registry)**: Antigravity 2.0 + CLI (Google -- single integration covers both surfaces; the CLI ships as the `agy` binary and uses the `.agents/` per-project convention with global content under `~/.gemini/antigravity-cli/`, verified 2026-05-29 against Google's public Antigravity CLI docs), Antigravity CLI (Google -- transition target for Gemini CLI before 2026-06-18; covered by the `antigravity2` integration), Gemini CLI (Google, ENTERPRISE-ONLY post-2026-06-18, opt-in via `--enterprise` installer flag), Nexus-AI (https://github.com/bendourthe/Nexus-AI).
- **User-global slash commands (v3.3.4)**: Cursor (`~/.cursor/commands/<name>.md`) and GitHub Copilot in VS Code (user-profile `prompts/<name>.prompt.md`) each expose a global command surface that every repo reads with no local install. A global install mirrors the catalog's commands there (manifest-scoped pruning removes upstream-deleted commands without touching the user's own files). Cursor additionally gets `.cursor/rules/*.mdc` + repo-root `AGENTS.md` behavioral guardrails.
- **Antigravity 2.0 slash commands (global + project, v3.12.0)**: Antigravity reads global slash commands from `~/.gemini/config/global_workflows/` and global skills from `~/.gemini/config/skills/` (a global install populates both), AND reads project-scoped `.agents/workflows/` + `.agents/skills/` from the open repo (seeded by `nexus-hub init`; see the `wire_project_surfaces` row above). The pre-v3.12.0 claim that Antigravity had no global slash surface (and wrote to `~/.gemini/antigravity/`) was incorrect and is fixed.
- **Behavioral-guardrails only**: OpenCode (`AGENTS.md`); Aider (project-root `CONVENTIONS.md`; no global instruction surface, so a global install is a no-op and the file installs at workspace scope); Windsurf (project-root `.windsurfrules` at workspace scope, plus a global `~/.codeium/windsurf/memories/global_rules.md` written only when Windsurf is detected); Kimi (project-local `.kimi/system.md` + `.kimi/agent.yaml` at workspace scope, mirrored under `~/.kimi/` only when Kimi is detected); Qwen (project-root `QWEN.md` at workspace scope, plus `~/.qwen/QWEN.md` only when Qwen is detected); OpenClaw (project-local `.openclaw/` SOUL + AGENTS + IDENTITY split at workspace scope, mirrored under `~/.openclaw/` only when OpenClaw is detected). These carry the Nexus-Hub instruction content with the `{{SKILL_INDEX}}` block embedded (the multi-file platforms embed it in the primary file -- Kimi `system.md`, OpenClaw `AGENTS.md` -- with the other files as stable companions); they are NOT slash-command surfaces. (Aider + Windsurf added v3.4.0 via the `aider` / `windsurf` integration subclasses; Kimi + Qwen + OpenClaw added v3.4.0 via the `kimi` / `qwen` / `openclaw` subclasses, reusing the same pattern.)

> **Windsurf / Kimi roster verification (2026-07-08, dated note)**: Per [Cognition's acquisition blog](https://cognition.com/blog/windsurf) (2025-07-14), Windsurf was acquired by Cognition and preserved "as a distinct product with its own brand"; third-party outlets report a 2026-06-02 rebrand to "Devin Desktop" (no primary Cognition rebrand announcement was reachable). The `.windsurfrules` / `global_rules.md` surfaces are still served, so the `windsurf` integration is marked **deprecated (not deleted)** and stays detection-gated. Separately, Kimi CLI was rebuilt as "Kimi Code CLI" (Node.js rewrite, v0.1.0 May 2026; [migration guide](https://www.kimi.com/code/docs/en/kimi-code-cli/guides/migration.html)); the migration "never modifies or deletes any of the old data under `~/.kimi/`", so the legacy `.kimi/` layout `kimi.py` writes coexists and is still served (the `kimi` integration carries a dated migration note; a project-local convention refresh is deferred to `docs/v3/v3.11/known-gaps.md`). Evidence: [docs/v3/v3.11/development/roster-verification.md](docs/v3/v3.11/development/roster-verification.md).

Each of these has a corresponding `IntegrationBase` subclass under `scripts/lib/integrations/` (added in Phase 10 of v2.1.0); the original 4 continue to install via the legacy installer copy blocks, with the registry subclasses standing by for the future v2.2.0 parity migration documented in `docs/archive/v2/v2.1/known-gaps.md` (DF-001).

If your change is a new slash command, call out in the CHANGELOG which platforms get a slash surface. Global slash surfaces: Claude (`commands/`), Gemini (`workflows/`), Codex (`prompts/`), Cursor (`~/.cursor/commands/`), Copilot (VS Code `prompts/*.prompt.md`). Project-only (seed via `nexus-hub init`): Antigravity 2.0 (`.agents/workflows/`). Body-only via the instruction file: OpenCode.

If broader per-file distribution to a new platform is needed, add a new subclass under `scripts/lib/integrations/` (not a new lock-step `base-*.md` template).

## Running Validation

```bash
make validate    # JSON catalog integrity
make lint        # ShellCheck on all hook scripts
make test        # pytest hook test suite
make build-catalog  # Rebuild data/ from catalog/
```

## Branching and Release Workflow

Nexus-Hub uses a lightweight **`develop` + `main`** model (adopted 2026-06-04). Full-Git-Flow ceremony (`release/*`, `hotfix/*` branches) is intentionally avoided.

- **`main`** is the stable, installable branch -- the branch users install from. It only receives merges at release time, each cut as a `vX.Y.Z` tag. Never commit version or phase work directly to `main`. The GitHub default branch stays `main` so clones and installer runs always get stable content.
- **`develop`** is the integration branch. All version work lands here, either directly or via short-lived feature branches (`feat/<slug>`, `fix/<slug>`) merged back into `develop`.
- **Release**: when a version's Definition of Done is met, run `/update release` (which bumps every version-carrying surface -- the `check_version_sync.py` guard enforces consistency across them -- finalizes the changelog, then commits, merges `develop` -> `main`, tags `vX.Y.Z`, pushes, and **publishes the GitHub Release** for that tag). Pushing a tag does NOT create a GitHub Release, so the publish step is what keeps the Releases page in step with the tags; it degrades gracefully (prints the `gh release create` command when `gh` is unavailable) and is idempotent + backfillable for any tag whose Release is missing.

Rationale: Nexus-Hub is a catalog consumed directly from the repo by an installer across every supported AI platform, so `main` is effectively a release artifact. Isolating in-progress, multi-phase versions on `develop` protects downstream installer users from half-applied phases.

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
