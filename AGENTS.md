# AGENTS.md

<!-- nexus-hub-version: 3.17.5 -->

This file provides guidance to AI coding agents (Claude Code, Cursor, Copilot, Gemini CLI, etc.) when working with code in this repository.

## Repository Overview

Nexus-Hub is a production-grade skill harness for AI coding assistants. It is the **upstream catalog** consumed by Nexus (the local-first desktop AI Studio, see `https://github.com/bendourthe/Nexus-AI`) and by every other major agent platform: Claude Code, OpenAI Codex, Gemini (via Antigravity), GitHub Copilot, Cursor, and GitHub CLI. Skills, commands, hooks, agents, and rules are distributed via installer scripts into users' `~/.nexus-hub/` directory and into their AI assistant's per-platform config locations.

Current catalog: **273 skills** across 21 categories, 18 commands (plus 3 permanent aliases), 31 hooks, 23 agents. The 40 v3.x deprecation shims were removed in v3.2.0.

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
|   `-- skills/               # 273 skills across 21 categories
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

#### Optional Invocation-Policy Frontmatter

A skill MAY declare two optional strict-boolean frontmatter fields controlling who can invoke it. Both follow the same optional-field contract as the framework-mapping fields below: absence is never an error and costs no Tier-1 tokens.

| Field | Meaning | Default |
|---|---|---|
| `disable-model-invocation` | `true` stops the agent auto-loading the skill; it runs only when the user invokes it explicitly | `false` |
| `user-invocable` | `false` hides the skill from the slash menu, leaving it available to the model as background knowledge | `true` |

`scripts/validate_skills.py` enforces two rules in `--bundles-only`, the mode `make validate` and CI run. A non-boolean value is an error naming the skill and field (`user-invocable: "true"` is a string that reads as correct and behaves as unset). And `disable-model-invocation: true` together with `user-invocable: false` is an error, because it leaves a skill nobody can invoke; that combination is a Nexus-Hub rule, not a vendor one.

Distribution is free for platforms that read these keys from `SKILL.md`, since the installers copy the file verbatim and a platform ignores frontmatter keys it does not recognise. Which platforms document which field, with source URLs and verified dates, is recorded in [`docs/policy/skill-invocation-policy-levers.md`](docs/policy/skill-invocation-policy-levers.md). Any claim that a platform supports a lever is subject to the do-not-invent rule: a fetched official vendor document, or the answer is "none documented".

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
├── assets/          # optional - templates, icons, fonts, fixtures used by scripts or referenced from SKILL.md
└── evals/           # optional - trigger-cases.json routing assertions (consumed by run_trigger_evals.py; see below)
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

**Unfilled-placeholder lint** (v3.15.2): `validate_skills.py` also flags unfilled multi-word angle-bracket template placeholders, so a scaffolded-but-unfinished skill cannot pass validation silently. A placeholder is two or more single-space-separated lowercase words inside angle brackets (for example `<what this skill does>`); it is a HARD ERROR in both the `description` frontmatter field and the SKILL.md body prose, and it runs in the `--bundles-only` mode that `make validate` and CI invoke. Single-word CLI notation (`<path>`, `<name>`), uppercase template tokens (`<MAJOR>`), and HTML tags are NOT flagged (they lack a lowercase-words-with-only-spaces interior), and examples inside fenced code blocks or inline-code spans are exempt (wrap a literal placeholder in backticks to show it as documentation).

**Optional routing evals** (`evals/trigger-cases.json`, v3.15.2): a skill MAY ship a `evals/trigger-cases.json` file declaring how prompts should route to it. `scripts/run_trigger_evals.py` consumes these to assert, for each skill that has cases, that (a) every `should_trigger: true` prompt ranks its own skill first among all skills (else it names the skill it mis-routed to) and (b) the weakest positive clears the strongest near-miss negative by a configurable margin (default 1.15x). Skills WITHOUT a file are reported as a WARN, never a FAIL, so the catalog never blocks on incomplete coverage; the file is entirely optional and authored incrementally. Schema (all keys lowercase):

```json
{
  "skill": "<skill-name>",
  "purpose": "one-line purpose",
  "cases": [
    {"id": "pos-1", "prompt": "real user phrasing", "should_trigger": true,  "assert": "routes to <skill> first", "lexical": true},
    {"id": "neg-1", "prompt": "look-alike request", "should_trigger": false, "assert": "routes to <other>, not here", "lexical": true}
  ]
}
```

Each file needs at least three positive cases (real phrasings a user would type) and three near-miss negatives (look-alike requests drawn from the skill's own SKIP clause). `lexical` is optional (default true); a `lexical: false` case triggers via agent reasoning rather than description vocabulary, so the deterministic runner SKIPS it (it is left for behavioral evals). The `evals/` subdir is consumed by the runner, NOT referenced from SKILL.md, so it is exempt from the orphan-bundle audit above.

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

`/plan` performs a platform-agnostic model-routing assessment per phase (added v3.4.0; cross-provider contract revised in v3.15.9). After the phase breakdown is designed and before the plan file is written, it invokes the `model-routing` skill once per phase to score complexity and record generic `frontier` / `strong` / `standard` / `fast` intent plus `low` / `medium` / `high` / `max` effort, defaulting to `frontier` with high/max effort on any uncertainty or high-risk signal. The "Phases at a Glance" table uses separate `Recommended model tier` and `Recommended effort level` columns, and each phase repeats those fields plus a rationale. Concrete ids live only in a separate `## Current model map` with Anthropic, OpenAI, Google, and Cursor columns. `/plan` refreshes that map from public official documentation on every full invocation and cites its sources. If web access is unavailable, it emits a visibly dated offline snapshot or fills every cell with `assess at implementation time`; it never silently collapses the plan to the host provider. Web research adds no new credential or dependency. This is command + skill behavior, NOT a `base-*.md` lockstep change -- routing is opt-in via the plan/implement steps, not always-loaded instruction text.

`/implement` re-confirms that recommendation at the start of each phase, before the subtask-by-subtask build step (added v3.4.0 Phase 4). It reads the phase's generic tier, effort, and rationale, refreshes or revalidates the Current model map when web access is available, and checks the selected provider's mapped model against the provider's live platform surface. A plan built before a model release therefore picks up the newer equivalent without changing its generic intent. If the mapped model is unavailable or the phase scores higher than planned, `/implement` surfaces the delta and defaults to the same or stronger tier (the no-degradation guarantee). Historical plans with the legacy `**Recommended model**` / `Rec. model / effort` fields remain valid inputs. Separately, the troubleshooting loop may UPSHIFT to a stronger tier or higher effort when tests fail repeatedly -- upshift only, with confirmation, never an automatic mid-phase downshift. The standalone `/route` command remains host-native: it validates and switches only models exposed by the detected platform; the plan map does not grant cross-provider switching capability.

## Adding or Modifying a Hook

Hook scripts live in `catalog/hooks/`. Rules:

- Bash scripts: use `#!/usr/bin/env bash` and `set -euo pipefail`
- Python scripts: include a module docstring and type annotations
- All hooks: write error messages to stderr, write output to stdout
- Security hooks (secret-scan, large-file-guard): follow the patterns in `catalog/rules/bash/security.md`

**PowerShell sibling required (v3.15.6+).** Every `catalog/hooks/<name>.sh` MUST ship a `catalog/hooks/<name>.ps1` with matching behavior, so a Windows user running hooks through PowerShell gets the same guardrail rather than silent non-coverage. This is machine-enforced in BOTH directions by `catalog/hooks/tests/test_hook_sibling_parity.py`, which fails when either file is missing, when a `.ps1` does not parse, or when a pair disagrees on the exit code for the same payload. CI adds an unconditional `.ps1` AST-parse gate in the `shellcheck` job, and the `tests-windows` job runs the suite on Windows PowerShell 5.1.

Two lessons sit behind those gates, both from real defects. `session-summary.ps1` shipped in v3.11.0 with a parse error and was therefore dead on Windows for four minor versions, because nothing parsed catalog `.ps1` files. And the v3.15.6 provenance ledger diverged from its `.sh` sibling in two ways (`Add-Content -Encoding utf8` emitting a UTF-8 BOM on PowerShell 5.1, and `sha256sum` escaping backslash-containing filenames) that a POSIX-only test could not reach. Exit-code parity plus a 5.1 leg is what catches that class.

When authoring a sibling, prefer the native equivalent over emulating shell mechanics: `ConvertFrom-Json` instead of a `jq` dependency, `[System.IO.File]::WriteAllText` with `UTF8Encoding($false)` instead of `Set-Content -Encoding utf8` (which emits a BOM on 5.1), and `[Console]::IsInputRedirected` as the equivalent of `[ ! -t 0 ]`. A sibling that works where the bash version silently no-ops (for example on a host with no `jq`) is an acceptable and documented improvement, provided it acts in the safe direction: warn or block MORE, never less.

The hook registration template is `catalog/hooks/settings.json`. Supported events, as actually registered there: `SessionStart`, `SessionEnd`, `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Notification`, `PreCompact`, and `Stop`. Register the `bash` invocation there; `.ps1` siblings are not registered separately, matching the existing convention.

Two of those are easy to misuse, so pick deliberately:

- **`Notification`** fires when the agent needs permission for a tool, or has been idle waiting for input. It is the only event meaning "blocked on the human", which is why v3.15.10's `notify-attention-required` hook rides it.
- **`Stop`** fires when the agent finishes responding, which is the end of EVERY turn, not the end of a task. A hook registered here runs constantly in a session driven by background work. Do not treat it as "task complete" without saying so honestly, and never register a notifier on `SubagentStop` (a sub-task milestone is not a reason to interrupt a human). See `docs/v3/v3.15/development/end-of-task-notification-contract.md`.

*(This list previously named only four events while the template already registered six; corrected in v3.15.10 along with the addition of `Notification`.)*

**Write tests for any new hook** following the pytest pattern in `catalog/hooks/tests/test_format_bash_description.py`. Prefer a `run` fixture parametrized over both implementations (see `test_escalation_trigger.py` or `test_provenance_ledger.py`) so every behavioral assertion doubles as a parity assertion. Run with `make test`.

#### Test retention policy

`catalog/hooks/tests/` grows every cycle, and a suite with no delete rule accumulates tests that assert history rather than behavior. Both halves of the rule below are needed; the keep half alone is what produces a suite nobody can prune.

**Keep a test when it validates a durable behavior:**

- Shipped CLI or runtime behavior a user can observe.
- A reusable contract (a hook's exit-code protocol, a validator's output shape, an installer's copy guarantee).
- A boundary enforcement (a guard that must block, an allowlist that must reject).
- A regression that previously broke something real, including the pre-existing defects the incident archive records.
- A representative fixture likely to catch a future bug in the same class.

**Do not keep a test whose main purpose is asserting the exact text of a dated note, a transitional decision, or a temporary artifact.** That information belongs in the document itself, where it can be read and revised, not frozen into an assertion that fails on a wording change and teaches nothing when it does. Where several artifacts share one invariant, cover it with a single data-driven aggregate test over the set rather than one near-identical test per artifact.

**Size trigger**: when a test file passes roughly 500 lines, re-check whether it is really one test. Usually it has accreted several concerns, or it is carrying logic that belongs in a product module. Prefer moving the reusable logic into the module under test so the test stays a thin behavior check.

None of this loosens the parity rule above. A behavioral assertion parametrized over both the `.sh` and the `.ps1` is ONE test covering a durable contract, not two tests to consolidate; the aggregate-test advice targets near-identical per-artifact tests, never the two implementations of one behavior.

### Workflow-phase automation (N1a)

To run automation at a `/plan`, `/implement`, or `/spec` **phase boundary**, do NOT invent new harness event types and do NOT import a Spec Kit-style per-command `before_/after_` hook registry (that presupposes the declined third-party extension runtime -- see the v3.6.0 Spec Kit comparison, candidate N1b). A phase boundary surfaces as a specific tool call, so key a `PreToolUse` / `PostToolUse` matcher on it and let the hook inspect the tool input: match `Write`/`Edit` and gate on `tool_input.file_path` (a plan artifact under `docs/**/plans/`, a `spec.md`, a `tasks.md`, a `CHANGELOG.md`), or match `Bash` and gate on `tool_input.command` (a `git commit`). Use `SessionStart` / `Stop` for session-level setup/teardown. The four events relevant to workflow-phase automation are `SessionStart` / `PreToolUse` / `PostToolUse` / `Stop`; this is a usage pattern on the existing surface, not a new runtime. A runnable example ships as [`catalog/hooks/workflow-phase-notice.sh`](catalog/hooks/workflow-phase-notice.sh) (tested in `catalog/hooks/tests/test_workflow_phase_notice.py`) and is registered in the default `settings.json` `PostToolUse` chain; it is advisory only (exit 0) and is disabled per-session with `NEXUS_DISABLED_HOOKS=workflow-phase-notice` or `NEXUS_HOOK_PROFILE=minimal`. Full recipe (matcher-to-phase mapping, authoring rules, registration snippet): the "Workflow-phase automation recipe" in [`guides/reference/CLAUDE_CODE_SETTINGS_REFERENCE.md`](guides/reference/CLAUDE_CODE_SETTINGS_REFERENCE.md).

## Per-Platform Install Defaults (v3.16.0)

`configs/platform-defaults.json` is the **single place a per-platform install-time behavioral default is edited** (reasoning effort, a default-model pin, or an approval policy). Everything that consumes such a default is DERIVED from it. Full schema, rules, and worked procedure: [`configs/README.md`](configs/README.md).

**Do not hand-edit a derived artifact.** These are generated or read from the source, and `python scripts/sync_platform_defaults.py --check` fails `make validate` and CI when one drifts:

- `catalog/hooks/settings.json` — its `effortLevel`, `model`, and `env.CLAUDE_CODE_EFFORT_LEVEL` core keys. The generator updates only those keys **in place**, because this file also carries the entire hook registration block; it is never re-serialized wholesale.
- `scripts/lib/integrations/claude.py` — the `nexus-hub init` project stub reads the source at runtime and keeps only an offline fallback, which `--check` also verifies so it cannot rot.

```bash
python scripts/sync_platform_defaults.py --check    # fail on drift (make validate + CI)
python scripts/sync_platform_defaults.py --apply    # regenerate derived artifacts from the source
```

**The do-not-invent rule (hard).** A platform appears in this file ONLY when a **fetched official vendor document** names the lever, recorded with a `source_url` and a `verified` date, and only when `docs/policy/platform-defaults-levers.md` classifies it VERIFIED. Never seed from a blog post, a forum, an aggregator, or an analogy to a similar-looking platform. Nexus-Hub has already made this mistake: the `.kimi/agent.yaml` companion was **fabricated** rather than found, shipped, and had to be dropped in v3.15.0. "No lever documented" is a valid and expected result. A model id is seeded only where the vendor documents a self-selecting value; otherwise the key goes under `omitted` with its reason, because pinning an id the user's account cannot reach breaks their tool.

`tests/validators/test_platform_defaults_levers.py` enforces this mechanically: the roster is read from the integration registry (so a newly registered platform fails until classified), every VERIFIED row must carry a URL and an ISO date, and **no platform may appear in `configs/platform-defaults.json` without a VERIFIED classification**.

**Install-time seeding.** `scripts/lib/integrations/platform_defaults.py`, hooked into `IntegrationBase.install()` (the dispatcher, not `install_global`, so a subclass that forgets `super()` cannot skip it), seeds each declared default into that platform's own config. It is **seed-if-absent** (never overwrites a value the user set), preserves what it did not write (`tomlkit` for TOML; append-only for existing YAML, since a PyYAML round-trip strips comments), degrades rather than failing, and is gated on `result.detected is not False` so a platform the user does not have installed receives nothing. `tomlkit` and `PyYAML` are optional lazily-imported dependencies checked by both installers.

**Scope boundary.** `docs/policy/platform-defaults-levers.md` owns behavioral defaults; `docs/policy/platform-read-contracts.md` owns file-discovery paths and capabilities. Neither should grow into the other. Both are re-verified in one pass by `[[platform-contract-verification]]`, but only the read-contract **hard-gates** a release; the lever contract rides along advisorily.

## Organization Knowledge Layer (v3.17.4)

Organization content remains outside the Nexus-Hub catalog and connects through `nexus-hub org connect <path-or-url>`. `scripts/lib/integrations/org_knowledge.py` validates the bundle and projects it from the common `IntegrationBase.install()` dispatcher into instruction files and existing rules surfaces. The organization marker block is independent of the Nexus-Hub marker block, and organization rule files are tracked through additive `org_tracked` / `org_shared` manifest ownership lists so doctor, repair, disconnect, teardown, and uninstall can reconcile only organization-owned content.

Do not add organization content to `templates/ai-instructions/`, invent a platform priority setting, or infer ownership from an `org/` path. Preserve the explicit precedence statement, use the manifest as the cleanup source of truth, and keep failures fail-soft during install. Connecting a bundle supplies guidance only: it grants no enforcement authority and transmits no content to Nexus-Hub. The canonical operating and rollback reference is [`guides/ORG_KNOWLEDGE_LAYER.md`](guides/ORG_KNOWLEDGE_LAYER.md).

The `Consequential Decisions` section in every substantive instruction template is behavioral context guidance. Before requesting a choice that changes security posture, deletes or overwrites data, changes distributed or user-facing behavior, or expands scope, the agent must explain the current work, the moving parts, each option including doing nothing, and its recommendation in plain language. Template parity proves that the rule is distributed consistently; it cannot prove runtime adherence. Aider has no global instruction surface, while Windsurf and OpenClaw are detection-gated or project-oriented, so these platforms receive the rule only on the instruction surfaces their integration actually installs. A consuming project's own `CLAUDE.md`, `AGENTS.md`, or equivalent local rules can still override installed guidance.

## Installer-Aware Changes (Cross-Platform)

Nexus-Hub is a **template repository**. Nothing you add is "live" until a user runs `scripts/installer.sh` (macOS/Linux) or `scripts/installer.ps1` (Windows). The installer is what distributes your changes across every supported agentic platform.

**Entry points (v3.7.0 install-UX overhaul)**: a clean machine installs via the one-line bootstrap -- `curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash` (macOS/Linux; `wget -qO-` fallback) or `irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1 | iex` (Windows). The root `install.sh` / `install.ps1` are dual-mode: run standalone they precheck dependencies, download the `main` tarball into `~/.nexus-hub/src`, and hand off to `scripts/installer.{sh,ps1}`; run inside a checkout they delegate exactly as before. The core installers (`scripts/installer.{sh,ps1}`) are **unchanged** by the bootstrap and still do all of the distribution work documented below -- the bootstrap only materializes the tree they run from, so the distribution channels and copy rules in this section are unaffected. `nexus-hub upgrade` (the CLI installed to `~/.nexus-hub/bin/`) re-runs this same idempotent bootstrap. Installs are no-prompt: global scope across every detected platform by default, with `--workspace` / `--platforms` / `--yes` for power users and CI (absent platforms skip-with-note; conflict-only overwrite confirmation).

**Golden rule**: every change you propose must be shaped so that after the next installer run, it reaches Claude Code, Cursor, Codex, Gemini/Antigravity, OpenCode, and Copilot — on Windows, macOS, and Linux — without any manual step on the user's part.

### Distribution channels the installer uses

| Artifact you add/modify | Installer edit required? | Platforms reached |
|---|---|---|
| `catalog/skills/<cat>/<name>/SKILL.md` | No — folder auto-copied | As of v3.12.0 every SKILL.md-standard platform (Claude, Codex/ChatGPT, Antigravity, Gemini, Gemini CLI, OpenCode, Nexus-AI -- and, as of v3.15.0, **Cursor, Qwen Code, and Kimi Code CLI**) receives skills FLATTENED to `skills/<name>/` (one level, per the SKILL.md open standard) plus one skill per command (`$name`); Qwen/Kimi are detection-gated at global scope. Copilot gets the skill index via the `{{SKILL_INDEX}}` block in its instruction file plus an opt-in `.github/skills/` wrapper set (`NEXUS_HUB_COPILOT_SKILLS`, a bundle id or `all`, off by default). Exact per-platform read-paths: `docs/policy/platform-read-contracts.json` (the machine-readable source of truth; human-readable companion in the sibling `.md`), the living contract re-verified and freshness-gated (`check_platform_contract_freshness.py`, run by `make validate` + CI) at every `/update release` by the platform-contract-verification step. |
| `catalog/commands/<name>.md` | No — folder auto-copied | Claude (`commands/`), Gemini (`workflows/`), Codex (`prompts/`). Cursor and GitHub Copilot get a **user-global** slash surface too (v3.3.4): a global install mirrors every command into `~/.cursor/commands/<name>.md` and into VS Code's user-profile `prompts/<name>.prompt.md`, so `/<name>` works in any repo with no local install. As of v3.12.0 Antigravity 2.0 gets a global slash surface at `~/.gemini/config/global_workflows/` AND the open project's `.agents/workflows/` (the latter seeded by `nexus-hub init`), and every command is also emitted as a skill. OpenCode has no slash surface — it sees the command body only via its instruction file (and its skills folder). **v3.15.0** added project-scoped command surfaces: Cursor also mirrors commands to the project `.cursor/commands/` (seeded by `nexus-hub init`, in addition to the user-global dir), and Qwen Code mirrors Markdown commands to `~/.qwen/commands/` + `.qwen/commands/` (TOML is deprecated in Qwen); Kimi Code CLI has no separate command format — each skill and command-skill surfaces as `/skill:<name>`. |
| `catalog/style-guides/<name>.md` (companion reference for a command, NOT a slash command) | No — folder auto-copied to `~/.nexus-hub/style-guides/` by `install_templates` | All platforms (shared). Located outside `catalog/commands/` so the file does not surface in the slash menu. |
| `catalog/agents/<name>.md` | No — folder auto-copied | Claude, Gemini, Codex |
| `catalog/hooks/<name>.{sh,py}` | No for the file; **you must register it** in `catalog/hooks/settings.json` | Platforms that honor Claude-style hooks |
| `catalog/rules/<lang>/<name>.md` | No — folder auto-copied | Claude, Gemini, Codex |
| `templates/documentation/<name>.{docx,pptx,xlsx,...}` | No — folder auto-copied to `~/.nexus-hub/templates/documentation/` | All platforms (shared) |
| `templates/ai-instructions/base-*.md` | **Yes — edit all 5 lockstep files** (claude, codex, cursor, gemini, opencode). **But 5 is not the full set**: 16 template files exist and 12 are substantive. A behavioral rule meant for every agent must also reach `base-google-shared.md` (which covers Antigravity 1.0, Antigravity 2.0, and Gemini CLI by `@`-include, and Antigravity CLI transitively via `@base-antigravity-20.md`), the guardrails-only `base-{aider,kimi,openclaw,qwen,windsurf}.md`, and `generic-instructions.md`. Only the lockstep five are machine-guarded; the other seven are not, so they are the ones a change silently misses. | The respective platform |
| `scripts/<name>.py` or `scripts/<name>.js` | **Yes — MUST add a copy step** in BOTH `scripts/installer.sh` AND `scripts/installer.ps1`, modeled after the existing `generate_report.py` entry. The installer copies scripts by **explicit name**, never by folder. | All platforms (shared under `~/.nexus-hub/scripts/`) |
| `configs/platform-defaults.json` (v3.16.0+) | No — **repo-internal source, NOT a distributed artifact**. It is the single place a per-platform install-time behavioral default is declared. Its effect reaches users two ways: the derived core keys of `catalog/hooks/settings.json` (which the installer already copies), and install-time seeding into each platform's own config by `scripts/lib/integrations/platform_defaults.py`. Never hand-edit a derived artifact. | All platforms with a VERIFIED lever (see below) |
| `scripts/sync_platform_defaults.py` (v3.16.0+) | No — **repo-internal guard, needs NO installer copy step**. Listed in `DEV_ONLY_SCRIPTS` in `catalog/hooks/tests/test_installer_smoke.py` alongside the other three repo-only guards. `--check` runs in `make validate` and CI; `--apply` regenerates the derived artifacts. | None (maintainer tooling) |
| `scripts/check_required_check_coverage.py` + `docs/policy/required-checks.json` (v3.17.6+) | No - **repo-internal guard plus its declared manifest, needs NO installer copy step**. Listed in `DEV_ONLY_SCRIPTS` in `catalog/hooks/tests/test_installer_smoke.py`. Runs in `make validate` and in CI's existing `validate` job (deliberately not a new job, which would need its own required context). Asserts every required status check is produced by a workflow that triggers unconditionally, so a required check can never sit Pending forever; `--sync` prints the live protection state via the user's own `gh` and never writes. | None (maintainer tooling) |
| `data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json` | No — the installer reads these to fill `{{SKILL_INDEX}}` placeholders in every platform's instruction file. Updating them is mandatory when adding a skill. | All platforms whose instruction template embeds the index |
| `scripts/lib/integrations/<platform>.py` (v2.1.0+) | No file-copy edit; **MUST** import + `_register()` the subclass in `scripts/lib/integrations/__init__.py::_register_builtins()`. The runner is invoked automatically by both installers for the extended-platform set. | The platform configured by the subclass (e.g., Antigravity 2.0, Gemini CLI, Nexus-AI for the v2.1.0 extended set; Claude / Codex / Cursor / Gemini / OpenCode / Copilot subclasses also exist for future v2.2.0 parity migration). |
| Project-local surfaces (called from `nexus-hub init` -- v2.2.0+) | No file-copy edit; override `wire_project_surfaces(self, ctx) -> WriteResult \| None` on the integration subclass. The `nexus-hub init` subcommand (bash: `scripts/installer.sh init`; PowerShell: `scripts/installer.ps1 init`) walks every registered integration and invokes the hook. | Any platform whose subclass overrides the hook. Currently `cursor` (writes `.cursor/rules/nexus-hub.mdc`), `claude` (writes `.claude/settings.json` permissions stub when absent), `antigravity2` (writes `.agents/workflows/<name>.md` command files, since Antigravity reads slash commands only from the open project's `.agents/`), and `copilot` (v3.11.0, OPT-IN: writes thin `.github/skills/<name>/SKILL.md` wrapper files for the `core-developer` bundle when `NEXUS_HUB_COPILOT_SKILLS=1`, upgrading Copilot from behavioral-guardrails-only to a native project Agent Skills surface; off by default because `.github/skills/` is commit-visible, never overwrites an existing file). |

### Required steps for any change

Walk this checklist before proposing a PR:

1. **Is your change inside a folder already copied recursively by the installer?** (`catalog/skills/`, `catalog/commands/`, `catalog/agents/`, `catalog/rules/`, `catalog/hooks/`, `templates/documentation/`.) If yes, no installer edit needed.
2. **Is your change a standalone script in `scripts/`?** If yes, add a copy line in `scripts/installer.sh` (next to the existing `generate_report.py` block, around line 1395) AND a `Safe-Copy` line in `scripts/installer.ps1` (around line 1656). Both must reference the same destination under `~/.nexus-hub/scripts/`.
3. **Does your change introduce a new Python or Node dependency?** Prefer a lazy import with a clear `pip install <pkg>` hint on failure (e.g., `try: import X; except ImportError: print("Error: X not installed. Please run: pip install X")`, as used in `scripts/generate_report.py`). If a hard requirement is unavoidable, add a dependency check in both installers next to the existing `python-docx`/`python-pptx` check.
4. **Does your change touch a platform-specific instruction template?** If you edit any of `templates/ai-instructions/base-*.md`, apply the same change to all five (claude/codex/cursor/gemini/opencode). This is the "platform-agnostic" constraint. It is machine-enforced: `scripts/check_base_template_parity.py` (run by `make validate` and in CI) fails when a shared section heading, a shared placeholder token, or an invariant block (Tech Stack, Key Commands, Branching, End-of-Task Summary, MCP Registry Policy) diverges across the five, while tolerating intentional per-platform lines (platform names, install paths). Note that `Output Minimization` is deliberately NOT an invariant block, because `base-claude.md` carries a legitimate extra bullet; `End-of-Task Summary` (added v3.15.10) IS one, because the rule is platform-agnostic by intent and has no valid per-platform variation. It is a repo-internal guard like `check_version_sync.py`, so it needs no `.ps1` sibling and no installer copy step.
5. **Validate**: run `make validate` (JSON integrity) and `make lint` (ShellCheck) after edits. For new hooks, run `make test`. For installer changes, do a dry-run install into a throwaway directory and confirm the new artifact lands at the expected path.
6. **Document**: add an entry under `## [Unreleased]` in `CHANGELOG.md`.

### Platform coverage caveats (current state)

> **Gemini CLI sunset**: per the 2026-05-21 Google Developers Blog announcement, Gemini CLI stops serving free / Google AI Pro / Ultra / GitHub-installed users on 2026-06-18. The standalone `gemini-cli` integration is now opt-in via the `--enterprise` installer flag (Bash: `scripts/installer.sh --enterprise`; PowerShell: `scripts/installer.ps1 -Enterprise`) and installs only when the user explicitly requests it. Non-enterprise users transition to Antigravity CLI, which is covered by the `antigravity2` integration (the desktop IDE and CLI share a backend per the same announcement; see [docs/archive/v2/v2.2/antigravity-cli-probe.md](docs/archive/v2/v2.2/antigravity-cli-probe.md)).

The installer deploys **skills, commands, agents, hooks, and rules as separate files** to the following platforms:

- **Original 4**: Claude Code, Gemini/Antigravity 1.0, Codex, GitHub Copilot (Copilot receives behavioral guardrails via `.github/copilot-instructions.md` rather than a full file-tree copy).

> **Correction (v3.16.0 Phase 3)**: this list previously described the Original 4 as installing via "legacy installer copy blocks" *instead of* the integration registry. That is no longer accurate and was corrected after being verified directly against both installers. **Every** platform is now invoked through the registry runner: `invoke_registry_platform` (bash) and `Invoke-RegistryPlatform` (PowerShell) each call `scripts/lib/integrations/runner.py install --integrations <key>`, at global and workspace scope, for all fourteen default-installed keys. What still differs is how much each call does: several platforms are invoked with `instruction_only`, so the registry renders only the marker-merged instruction file while the installer's own `safe_folder_copy` blocks handle the catalog tree (the DF-001 legacy-block replacement path). The practical consequence, and the reason this matters beyond bookkeeping: a hook added to `IntegrationBase` reaches **every** platform with no installer edit. That is what let v3.16.0 Phase 3 add install-time defaults seeding without touching either installer.
- **Extended 4 (v2.2.0+, via integration registry)**: Antigravity 2.0 + CLI (Google -- single integration covers both surfaces; the CLI ships as the `agy` binary and uses the `.agents/` per-project convention with global content under `~/.gemini/antigravity-cli/`, verified 2026-05-29 against Google's public Antigravity CLI docs), Antigravity CLI (Google -- transition target for Gemini CLI before 2026-06-18; covered by the `antigravity2` integration), Gemini CLI (Google, ENTERPRISE-ONLY post-2026-06-18, opt-in via `--enterprise` installer flag), Nexus-AI (https://github.com/bendourthe/Nexus-AI).
- **User-global slash commands (v3.3.4)**: Cursor (`~/.cursor/commands/<name>.md`) and GitHub Copilot in VS Code (user-profile `prompts/<name>.prompt.md`) each expose a global command surface that every repo reads with no local install. A global install mirrors the catalog's commands there (manifest-scoped pruning removes upstream-deleted commands without touching the user's own files). **Cursor gained full-surface parity in v3.15.0 (Phase 2)**: beyond the global commands + `.cursor/rules/*.mdc` + repo-root `AGENTS.md` guardrails, it now also receives flattened skills (`~/.cursor/skills/` global, `.cursor/skills/` project), subagents (`.cursor/agents/*.md`), project-scoped commands (`.cursor/commands/`, also seeded by `nexus-hub init`), and a Cursor-schema `hooks.json` (the `git-guardrails` guardrail, gated on `hooks_supported`). The global `~/.cursor/commands/` read-path is retained but UNVERIFIED against official docs (community feature-request; known-gap DF-1); the project `.cursor/commands/` path is confirmed.
- **Antigravity 2.0 slash commands (global + project, v3.12.0)**: Antigravity reads global slash commands from `~/.gemini/config/global_workflows/` and global skills from `~/.gemini/config/skills/` (a global install populates both), AND reads project-scoped `.agents/workflows/` + `.agents/skills/` from the open repo (seeded by `nexus-hub init`; see the `wire_project_surfaces` row above). The pre-v3.12.0 claim that Antigravity had no global slash surface (and wrote to `~/.gemini/antigravity/`) was incorrect and is fixed.
- **Skills-bearing integrations (v3.15.0 platform parity)**: OpenCode, Qwen Code, and Kimi Code CLI now receive a flattened skills file-tree (and more), not just an instruction file. **OpenCode** (`~/.config/opencode/` global, `.opencode/` project): skills + commands + rules + agents (agents added v3.15.0 Phase 3); its `plugins/` hooks are a JS/TS Bun runtime, out of scope for Nexus-Hub's shell/py hooks (DF-4). **Qwen Code** (`~/.qwen/` global, detection-gated; `.qwen/` project): flattened skills + subagents + Markdown commands (TOML is deprecated in Qwen, so Markdown is used) + the `QWEN.md` instruction file (v3.15.0 Phase 4). **Kimi Code CLI** (`~/.kimi-code/` global, detection-gated; `.kimi-code/` project): flattened skills (each auto-registers as `/skill:<name>`; no separate command format) + `AGENTS.md` (v3.15.0 Phase 4 -- migrated from the older, separate "Kimi CLI" `~/.kimi/` product; that path and the invented `.kimi/agent.yaml` companion are dropped, and a user still on the old product no longer receives a surface). All three still embed the `{{SKILL_INDEX}}` block in their instruction file. (Qwen + Kimi were added v3.4.0 as guardrails-only via the `qwen` / `kimi` subclasses and reclassified in v3.15.0 Phase 4; OpenCode has installed skills/commands/rules since v3.12.0.)
- **Hermes (v3.15.2 Phase 5, registry-registered)**: `hermes` is a skills-native integration (`~/.hermes/skills/` global, detection-gated on `~/.hermes`; `.hermes/skills/` project) that discovers folder-per-skill `SKILL.md` directly and needs no instruction file (a `SkillsIntegration`, not a `MarkdownIntegration`, so no `base-hermes.md`). It ALSO reads the cross-tool shared `~/.agents/skills/` (owned/written by `codex`) and the project `.agents/skills/` (seeded by `antigravity2`'s `wire_project_surfaces` on `nexus-hub init`); Hermes reads those shared paths but writes ONLY its native `~/.hermes/skills` to avoid an `uninstall --platforms hermes` teardown conflict, the same rule Kimi follows. It is registered in `_register_builtins()` and installable via `scripts/lib/integrations/runner.py install --integrations hermes`; promoting it to a first-class default-installed platform (a `contract_checks` entry + installer `should_install` / `known_platform_keys` wiring) is a tracked v3.15.2 follow-on. See `docs/policy/platform-read-contracts.md`.
- **Behavioral-guardrails only**: Aider (project-root `CONVENTIONS.md`; no global instruction surface, so a global install is a no-op and the file installs at workspace scope); Windsurf (project-root `.windsurfrules` at workspace scope, plus a global `~/.codeium/windsurf/memories/global_rules.md` written only when Windsurf is detected); OpenClaw (project-local `.openclaw/` SOUL + AGENTS + IDENTITY split at workspace scope, mirrored under `~/.openclaw/workspace/` only when OpenClaw is detected). These carry the Nexus-Hub instruction content with the `{{SKILL_INDEX}}` block embedded (OpenClaw embeds it in `AGENTS.md`, with SOUL/IDENTITY as stable companions); they are NOT slash-command or skills surfaces. (Aider + Windsurf added v3.4.0 via the `aider` / `windsurf` integration subclasses; OpenClaw via the `openclaw` subclass, reusing the same pattern.)

> **Windsurf / Kimi roster verification (2026-07-08, dated note)**: Per [Cognition's acquisition blog](https://cognition.com/blog/windsurf) (2025-07-14), Windsurf was acquired by Cognition and preserved "as a distinct product with its own brand"; third-party outlets report a 2026-06-02 rebrand to "Devin Desktop" (no primary Cognition rebrand announcement was reachable). The `.windsurfrules` / `global_rules.md` surfaces are still served, so the `windsurf` integration is marked **deprecated (not deleted)** and stays detection-gated. Separately, Kimi CLI was rebuilt as "Kimi Code CLI" (Node.js rewrite, v0.1.0 May 2026; [migration guide](https://www.kimi.com/code/docs/en/kimi-code-cli/guides/migration.html)); the migration "never modifies or deletes any of the old data under `~/.kimi/`", so the legacy `.kimi/` layout `kimi.py` writes coexists and is still served (the `kimi` integration carries a dated migration note; a project-local convention refresh is deferred to `docs/v3/v3.11/known-gaps.md`). Evidence: [docs/v3/v3.11/development/roster-verification.md](docs/v3/v3.11/development/roster-verification.md).

Each of these has a corresponding `IntegrationBase` subclass under `scripts/lib/integrations/` (added in Phase 10 of v2.1.0); the original 4 continue to install via the legacy installer copy blocks, with the registry subclasses standing by for the future v2.2.0 parity migration documented in `docs/archive/v2/v2.1/known-gaps.md` (DF-001).

If your change is a new slash command, call out in the CHANGELOG which platforms get a slash surface. Global slash surfaces: Claude (`commands/`), Gemini (`workflows/`), Codex (`prompts/`), Cursor (`~/.cursor/commands/`, read-path UNVERIFIED - see DF-1), Copilot (VS Code `prompts/*.prompt.md`). Project-only (seed via `nexus-hub init`): Antigravity 2.0 (`.agents/workflows/`) and Cursor (`.cursor/commands/`, added v3.15.0 Phase 2). Body-only via the instruction file: OpenCode.

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

**Capability usage gate (release notes).** A release that introduces or materially changes an OPT-IN capability, installer flag, managed skill, or host surface must document five things per surface in its release notes: the exact activation mechanism, a runnable validation command, the exact disable / rollback path, the authority or privacy boundary that activation does NOT grant, and a canonical documentation link. Nexus-Hub ships an unusually high density of such surfaces (`NEXUS_HUB_COPILOT_SKILLS`, `--enterprise` / `-Enterprise`, `NEXUS_DISABLED_HOOKS`, `NEXUS_HOOK_PROFILE=minimal`), and the fourth element is both the most-skipped and the only one that fails silently rather than loudly. The gate applies ONLY to opt-in surfaces; a release with none satisfies it with a single explicit no-change declaration. Full definition and worked examples: governance step 6 in [`catalog/commands/update.md`](catalog/commands/update.md).

## Decision Records

Non-trivial changes MUST include or update a decision record in the same PR: a new policy, a new supported platform, a new validator or gate, a rename carrying migration cost, or a design that was proposed and declined. Mechanical, local, or single-file edits are exempt.

Records live at `docs/decisions/<lifecycle>/<class>/YYYY-MM-DD-<slug>.md` and require `## Alternatives considered`, because a decision recorded without what it beat invites re-litigation. Check `rejected/` before proposing anything that touches an existing policy or platform surface. Format, lifecycle, and the three-surface split against known-gaps and solutions: [`docs/decisions/README.md`](docs/decisions/README.md).

## Critical Conventions

- **Never edit `data/` files manually** unless registering a new skill — they are generated. The source of truth is `catalog/skills/`.
- **Never commit secrets.** The `secret-scan.sh` hook checks Write/Edit operations.
- **Destructive git commands require confirmation.** The `git-guardrails.sh` hook enforces this.
- **SKILL.md summaries must be quoted strings.** The MCP server depends on YAML-parseable frontmatter.
- **skills.json security scores** (`structural`, `integrity`, `semantic`) default to 100/100/95 for new skills; adjust if the skill has known limitations.

## Boundaries

**Scope-fit review (before adding, not after):** treat code volume as a cost, especially during a refactor. A good change makes the next change easier to localize, test, and revert; it should not turn a design possibility into unused production structure.

Before adding a new module, builder, protocol field, CLI option, fixture, or abstraction, name the shipped behavior, the active call site, or the explicit compatibility contract that requires it. If the only justification is an uncommitted future runner, a design note, or a hypothetical extension with no validation contract, keep the design in docs or todo state until the real call site appears. "We will need it when X lands" is a plan, not a call site.

This is the complement to [[code-simplification]], which removes complexity after the fact. This gate declines to add it in the first place, which is cheaper and leaves no migration behind.

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
