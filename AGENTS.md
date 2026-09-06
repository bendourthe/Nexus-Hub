# AGENTS.md

<!-- nexus-hub-version: 4.7.0 -->

This file provides guidance to AI coding agents (Claude Code, Cursor, Copilot, Gemini CLI, etc.) when working with code in this repository.

## Repository Overview

Nexus-Hub is a production-grade skill harness for AI coding assistants. It is the **upstream catalog** consumed by Nexus (the local-first desktop AI Studio, see `https://github.com/bendourthe/Nexus-AI`) and by every other major agent platform: Claude Code, OpenAI Codex, Gemini (via Antigravity), GitHub Copilot, Cursor, and GitHub CLI. Skills, commands, hooks, agents, and rules are distributed via installer scripts into users' `~/.nexus-hub/` directory and into their AI assistant's per-platform config locations.

Current catalog: **329 skills** across 23 categories, 18 commands (plus 3 permanent aliases), 34 hooks, 23 agents. The 40 v3.x deprecation shims were removed in v3.2.0.

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
│   ├── rules/                # Language, security, and artifact rules
|   `-- skills/               # 329 skills across 23 categories
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

The responsive HTML rule family lives under `catalog/rules/html/`. Repository-level detector coverage and its visual fixtures live under `tests/verification/`.

## Adding a New Skill

### 1. Choose the right category

Existing categories: `ai-development`, `architecture`, `bug-fixing`, `business-product`, `code-cleanup`, `code-review`, `compliance`, `developer-experience`, `documentation`, `framework-specialists`, `infrastructure`, `language-specialists`, `orchestration`, `project-setup`, `research`, `security`, `security-operations`, `ot-security`, `mobile-security`, `specialized-domains`, `testing`, `tests-generation`, `workflow`.

The `security` category holds application-security skills (authentication, dependency/CVE analysis, exploitability, patch advice). The `security-operations` category (added v2.3.0) holds defensive operational skills: DFIR, threat hunting, detection engineering, incident response, and cloud / endpoint / identity / phishing detection. The `ot-security` category (added v3.20.1) holds industrial-control and operational-technology skills. The `mobile-security` category (added v3.20.1) holds Android/iOS application and mobile-malware skills. Place a new defensive-operations skill under `security-operations`; place an application-security or AppSec-review skill under `security`; place ICS/SCADA work under `ot-security`; place mobile-app or mobile-malware work under `mobile-security`.

If none fit, discuss with maintainers before creating a new category. A new category also needs `./catalog/skills/<category>` in `.claude-plugin/plugin.json` `skills` (plugin scan is one level). `test_claude_plugin_manifests.py` guards drift.

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

**Description style: combat undertriggering.** The `description` field above is what the AI agent scans when deciding whether to trigger this skill. Claude has a measurable tendency to **under-trigger** when the description is narrow, clean, or implicit. The fix is not a longer description -- it is a **pushy** description that lists trigger phrases AND skip phrases explicitly. Rules:

- **List trigger phrases verbatim.** If the user is likely to say "build me a dashboard", "show internal metrics", "visualize the data", put those exact phrases in the description.
- **Add a SKIP clause.** Use `SKIP: ...` or `Do NOT use for: ...` to fence off look-alike requests the skill should not handle. This is what stops over-triggering after you make the description pushier.
- **Cover synonyms and adjacent intents.** A description for a "dashboard" skill should also cover "internal metrics", "data visualization", "company data display" -- not just the literal word "dashboard".
- **Lead with the action, then the trigger surface.** First sentence states what the skill does; second sentence lists when to invoke it; third sentence (if needed) lists when to skip.

Before / after example:

- **Before** (narrow, agent under-triggers): "How to build a dashboard."
- **After** (pushy, agent triggers reliably without false positives): "How to build a dashboard. Make sure to use this skill whenever the user mentions dashboards, data visualization, internal metrics, or wants to display any kind of company data, even if they don't explicitly ask for a 'dashboard'. SKIP: standalone chart generation, one-off data exports, or read-only status pages without filtering controls."

The "After" form trades 6 words for 60. Those 60 words pay for themselves the first time the agent would have skipped a relevant invocation under the "Before" form. See `catalog/skills/workflow/create-custom-command/SKILL.md` for the same rule applied to commands.

#### Three-Tier Loading Model

Every Nexus-Hub skill is consumed by the agent in three tiers of progressive disclosure. Authoring decisions (what goes in the frontmatter, what goes in the body, what gets bundled in subdirs) follow directly from this model, so internalize it before writing the body.

1. **Tier 1 -- always loaded** (~150-300 tokens total): `name`, `description`, `summary_l0`, `overview_l1`. Every active session has these in context for every catalog skill, all the time. They determine whether the skill triggers. Tier 1 is the only tier under direct token-budget pressure across the catalog.
2. **Tier 2 -- loaded on trigger**: the SKILL.md body. Loaded once the agent decides this skill is relevant to the current task. Target ≤500 lines; soft cap 800 lines (see the size-norm rule below). Tier 2 is the agent's working manual for the skill -- instructions, rationalizations, verification, related-skills cross-links.
3. **Tier 3 -- loaded on demand**: bundled resources under per-skill `scripts/`, `references/`, `assets/` subdirectories (the convention introduced in Phase 3 of `docs/archive/v1/v1.1/plans/adoption-skills.md`, item A13). Two access patterns:
    - **Reference files** (`references/<topic>.md`) load into context only when the agent reads them. The body should link to a reference file the way it would link to an external doc -- "see `references/fastmcp-runbook.md` for the full setup steps" -- so the agent only pays for it when needed.
    - **Scripts** (`scripts/<name>.{py,sh,js}`) execute via the Bash / shell tool **without their source code being loaded** into the context window. This is the critical performance affordance: a skill can bundle a 2000-line generator script that runs deterministically on demand, and the agent never reads a single line of it. Scripts are how a skill ships heavy capability without inflating Tier 2.

Practical implications for SKILL.md authoring:

- Resist the urge to inline everything into the body. If a piece of content is needed only some of the time, push it to a reference file.
- If a step is deterministic and could be a 50-line shell script instead of 200 lines of body prose, ship the script under `scripts/` and let the agent execute it.
- Keep Tier 1 fields tight (especially `description` and `summary_l0`); they cost tokens on every catalog read across every session. Tier 2 / Tier 3 budgets are per-trigger, not per-session.

Treat every SKILL.md body as an operational runbook: actions, decision rules, artifacts, gates, and observable verification that an agent can execute. It is not a fact tutorial; supporting knowledge belongs in Tier-3 `references/` and loads only when the runbook needs it. An external study found procedural anchoring accounts for most successful skill cases.

Cross-links: the body-size targets sit in the size-norm rule immediately below. The bundled-subdir convention is summarized in the "Per-skill Bundled Resources" subsection further down and documented in full in [`guides/reference/SKILL_BUNDLED_RESOURCES.md`](guides/reference/SKILL_BUNDLED_RESOURCES.md).

#### Optional Invocation-Policy Frontmatter

A skill MAY declare two optional strict-boolean frontmatter fields controlling who can invoke it. Both follow the same optional-field contract as the framework-mapping fields below: absence is never an error and costs no Tier-1 tokens.

| Field | Meaning | Default |
|---|---|---|
| `disable-model-invocation` | `true` stops the agent auto-loading the skill; it runs only when the user invokes it explicitly | `false` |
| `user-invocable` | `false` hides the skill from the slash menu, leaving it available to the model as background knowledge | `true` |

`validate_skills.py --bundles-only` (`make validate` / CI) errors on a non-boolean value and on `disable-model-invocation: true` with `user-invocable: false` (nobody can invoke it). A string `"true"` is unset, not true.

Command-derived skills the installer emits are user-invoked: `_synthesize_skill` sets `disable-model-invocation: true`. A user-invoked skill may delegate to model-invoked skills, never to another user-invoked one. `validate_skills.py` warns on a catalog description that starts with `Run the /X command` without the flag.

Installers copy the keys verbatim; platforms that do not recognise them ignore them. Dated per-platform support lives in [`docs/policy/skill-invocation-policy-levers.md`](docs/policy/skill-invocation-policy-levers.md). A lever is VERIFIED only from a fetched official vendor document, or the answer is "none documented".

#### Optional Security and Compliance Framework Mapping

Security and compliance skills MAY declare optional framework-mapping fields. Absence is never an error and costs no Tier-1 tokens; `validate_skills.py` checks list shape only when present.

| Field | Framework | Example value |
|---|---|---|
| `mitre_attack` | MITRE ATT&CK techniques | `[T1071, T1003.001]` |
| `atlas_techniques` | MITRE ATLAS (adversarial ML) | `[AML.T0047, AML.T0049]` |
| `d3fend_techniques` | MITRE D3FEND defensive countermeasures | `[D3-NTA, D3-PA]` |
| `nist_csf` | NIST Cybersecurity Framework categories | `[DE.CM, RS.AN]` |
| `nist_ai_rmf` | NIST AI Risk Management Framework controls | `[MEASURE-2.6, GOVERN-1.1]` |
| `mitre_f3` | MITRE Fight Fraud Framework (F3) | `[F1005.006, F1010]` |

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

These fields exist so a downstream generator (e.g. `scripts/build_framework_coverage.py`) can emit a coverage matrix across Nexus-Hub's security skills. The committed matrix is `docs/framework-coverage.md` (Navigator layer: `docs/attack-navigator-layer.json`); `build_framework_coverage.py --check` fails `make validate` when either file is stale. They are NOT a substitute for the skill body -- the body must still teach the agent what to do, with binary Verification and Common Rationalizations.

#### agentskills.io conformance

Nexus-Hub SKILL.md files target the [agentskills.io](https://agentskills.io) open standard: `name` and `description` are required and non-empty, `name` is 1-64 characters matching `^[a-z0-9]+(-[a-z0-9]+)*$`, and `description` is 1-1024 characters. `scripts/check_agentskills_conformance.py` proves that contract in `make validate` and CI; it is a repo-internal guard (listed in `DEV_ONLY_SCRIPTS`) and is not installer-copied. Extra top-level keys Nexus-Hub adds (`summary_l0`, `overview_l1`, framework-mapping fields, invocation-policy booleans) are permitted by the standard and reported as information, not failures. Thirteen pre-existing pushy descriptions exceed 1024 characters and are grandfathered by name; a new over-long description is a hard error. The guard does not re-check name-equals-directory (already a hard rule in `scripts/validate_skills.py`) and does not ban `<`/`>` in frontmatter (the v3.15.2 placeholder lint is the more precise check).

Required body sections (in order):

```markdown
# Title

Brief intro paragraph.

## When to Use This Skill

Bullet list of trigger scenarios. Include explicit "When NOT to use" guidance.

## Instructions

Step-by-step process. Use numbered steps and code blocks.

## Common Rationalizations

Table of excuses the agent might use to skip this skill -- with rebuttals.

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

- `<skill-name>` -- one sentence on the relationship
```

**SKILL.md size norm.** Target ≤500 lines for the SKILL.md body. Hard cap 800 lines, enforced by `scripts/validate_skills.py` in `--bundles-only` (so `make validate` and CI fail a body over 800). Beyond 500 lines, add a `references/` subdirectory with a table of contents and link to it from SKILL.md rather than expanding the body. Beyond 800 lines, the skill MUST be split or refactored before merge. Existing skills that exceed 500 lines are grandfathered at the warning tier only -- a new or grown body over 800 is a hard error.

#### Rule ownership for overlapping skills

When two or more skills cover adjacent or overlapping territory, the cluster MUST declare a rule-ownership table naming exactly one owning skill per concern. Non-owning skills reference the owner by name and describe only the handoff; they never restate the owned rule. Put the table in the coordinating skill, or in this file if the cluster has none. Tie-break: one skill decides WHEN a constraint applies and how severe a violation is; another owns MEASURING and remediating it. Two skills touching one concern is fine; two skills both stating the rule is not. Without this, a multi-skill review reports the same root cause twice and the user cannot tell whether that is two problems or one.

#### Missing-delegate honesty

When a skill delegates work to another skill and that delegate is unavailable, it MUST mark that portion as not covered, name the missing skill, and continue. It MUST NOT reconstruct the delegate's rules from memory, substitute a neighbour, or claim coverage it did not achieve. The gap MUST be visible in the output, not only in the instructions. An agent that improvises the missing rules produces a report that reads complete while that section is unreviewed. This is the delegation-specific case of `[[verification-before-completion]]`.

#### Review-output restraint

Every review skill inherits two conventions; the canonical contract is `catalog/skills/code-review/multi-agent-code-review/SKILL.md`. (1) **Considered but Rejected**: list real inspected candidates that were not reported, each with a reason; never invent filler; a thin scope says so. Without this, a thorough review that found little looks the same as a shallow one. (2) **Mode-based finding cap**: each depth mode binds a coverage scope AND an output cap (quick = higher severities, small cap; full = whole scope, larger cap). Never pad to the cap; a short or clean result is valid. Without a cap, cosmetic padding buries the finding that mattered.

#### Per-skill Bundled Resources

A skill folder MAY carry four optional subdirectories beside `SKILL.md`: `scripts/` (executed without their source entering context), `references/` (read on demand), `assets/`, and `evals/`. This is the operational form of Tier 3 above, and it is how a skill ships heavy capability without inflating Tier 1 or Tier 2.

Two rules matter even if you read nothing else: every bundled file MUST be referenced from `SKILL.md` (the orphan audit in `make validate` warns otherwise, and `.gitkeep` is the only exemption), and both installers copy the whole skill tree recursively, so a bundled subdirectory needs **no** installer edit.

**Full detail** (naming rules, the `.ps1` sibling requirement, installer behavior, the orphan audit, the placeholder lint, the optional routing evals, and the Dynamic-Workflow template convention): [`guides/reference/SKILL_BUNDLED_RESOURCES.md`](guides/reference/SKILL_BUNDLED_RESOURCES.md).

### 4. Register the skill

After creating SKILL.md, update these three files:

**`data/SKILL_INDEX.md`** -- add one row to the table:
```
| <skill-name> | <Category> | "<summary_l0>" | catalog/skills/<category>/<skill-name>/SKILL.md |
```

**`data/skills.json`** -- add one entry to the `"skills"` array following the existing schema (name, title, description, long_description, summary_l0, overview_l1, version, author, category, language, tags, priority, based_on, tools_required, path, file, size, downloads, status, security).

**`data/marketplace.json`** -- increment `skill_count` in the relevant category entry and update `"total_skills"` in `statistics`.

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
   1. The third party is the intrinsic data destination -- you are already a customer of the vendor (GitHub, Supabase, Railway, Vercel, Cloudflare, your own Postgres).
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

**On a rename or deprecation**, decide whether to keep the old command name working through a deprecation shim at `catalog/commands/<old-name>.md` -- a `DEPRECATED (removed in vX.Y.Z). Forwarding to /NEW.` frontmatter `description` plus a short body that prints the notice and delegates to the new command -- or to remove it outright with a CHANGELOG `Removed` note. (The 40 v3.0.0-era shims followed the shim pattern and were removed in v3.2.0; see the v3.2.0 CHANGELOG and `docs/releases/v3/v3.0/command-migration.md`.)

**Do not maintain a static command list anywhere.** `/skills list` derives the command cheatsheet -- the active commands, what each does, the deprecated name each one replaces, and common multi-command workflows -- at runtime from the command files themselves (see `catalog/style-guides/commands-cheatsheet.md`). Adding, renaming, refactoring, or deprecating a command therefore updates the cheatsheet automatically on the next `/skills list`; there is no table to hand-edit. The only command artifacts to touch on a change are the command file(s) and (on a rename) the deprecation shim.

## Model Routing in the Plan/Implement Loop

`/plan` scores a platform-agnostic tier (`frontier` / `strong` / `standard` / `fast`) and effort level per phase, defaulting to `frontier` at high or max effort on any uncertainty; `/implement` re-confirms that recommendation at the start of each phase against the live model set, defaults upward on disagreement, and may upshift (never silently downshift) when the troubleshooting loop stalls. Concrete model ids live only in the plan's own `## Current model map`, refreshed from official vendor documentation per invocation. This is command + skill behavior, not a `base-*.md` lockstep concern.

**Full detail**: [`docs/policy/model-routing-in-plan-and-implement.md`](docs/policy/model-routing-in-plan-and-implement.md).

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
- **`Stop`** fires when the agent finishes responding, which is the end of EVERY turn, not the end of a task. A hook registered here runs constantly in a session driven by background work. Do not treat it as "task complete" without saying so honestly, and never register a notifier on `SubagentStop` (a sub-task milestone is not a reason to interrupt a human). See `docs/releases/v3/v3.15/development/end-of-task-notification-contract.md`.

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

- `catalog/hooks/settings.json` -- its `effortLevel`, `model`, and `env.CLAUDE_CODE_EFFORT_LEVEL` core keys. The generator updates only those keys **in place**, because this file also carries the entire hook registration block; it is never re-serialized wholesale.
- `scripts/lib/integrations/claude.py` -- the `nexus-hub init` project stub reads the source at runtime and keeps only an offline fallback, which `--check` also verifies so it cannot rot.

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

**Golden rule**: every change you propose must be shaped so that after the next installer run, it reaches Claude Code, Cursor, Codex, Gemini/Antigravity, OpenCode, and Copilot -- on Windows, macOS, and Linux -- without any manual step on the user's part.

### Distribution channels the installer uses

| Artifact you add/modify | Installer edit required? | Platforms reached |
|---|---|---|
| `catalog/skills/<cat>/<name>/SKILL.md` | No -- folder auto-copied | As of v3.12.0 every SKILL.md-standard platform (Claude, Codex/ChatGPT, Antigravity, Gemini, Gemini CLI, OpenCode, Nexus-AI -- and, as of v3.15.0, **Cursor, Qwen Code, and Kimi Code CLI**) receives skills FLATTENED to `skills/<name>/` (one level, per the SKILL.md open standard) plus one skill per command (`$name`); Qwen/Kimi are detection-gated at global scope. Copilot gets the skill index via the `{{SKILL_INDEX}}` block in its instruction file plus an opt-in `.github/skills/` wrapper set (`NEXUS_HUB_COPILOT_SKILLS`, a bundle id or `all`, off by default). Exact per-platform read-paths: `docs/policy/platform-read-contracts.json` (the machine-readable source of truth; human-readable companion in the sibling `.md`), the living contract re-verified and freshness-gated (`check_platform_contract_freshness.py`, run by `make validate` + CI) at every `/update release` by the platform-contract-verification step. |
| `catalog/commands/<name>.md` | No -- folder auto-copied | Claude (`commands/`), Gemini (`workflows/`), Codex (`prompts/`). Cursor and GitHub Copilot get a **user-global** slash surface too (v3.3.4): a global install mirrors every command into `~/.cursor/commands/<name>.md` and into VS Code's user-profile `prompts/<name>.prompt.md`, so `/<name>` works in any repo with no local install. As of v3.12.0 Antigravity 2.0 gets a global slash surface at `~/.gemini/config/global_workflows/` AND the open project's `.agents/workflows/` (the latter seeded by `nexus-hub init`), and every command is also emitted as a skill. OpenCode has no slash surface -- it sees the command body only via its instruction file (and its skills folder). **v3.15.0** added project-scoped command surfaces: Cursor also mirrors commands to the project `.cursor/commands/` (seeded by `nexus-hub init`, in addition to the user-global dir), and Qwen Code mirrors Markdown commands to `~/.qwen/commands/` + `.qwen/commands/` (TOML is deprecated in Qwen); Kimi Code CLI has no separate command format -- each skill and command-skill surfaces as `/skill:<name>`. |
| `catalog/style-guides/<name>.md` (companion reference for a command, NOT a slash command) | No -- folder auto-copied to `~/.nexus-hub/style-guides/` by `install_templates` | All platforms (shared). Located outside `catalog/commands/` so the file does not surface in the slash menu. |
| `catalog/agents/<name>.md` | No -- folder auto-copied | Claude, Gemini, Codex |
| `catalog/hooks/<name>.{sh,py}` | No for the file; **you must register it** in `catalog/hooks/settings.json` | Platforms that honor Claude-style hooks |
| `catalog/rules/<category>/<name>.md` (including `catalog/rules/html/`) | No -- folder auto-copied | Claude, Gemini, Codex |
| `templates/documentation/<name>.{docx,pptx,xlsx,...}` | No -- folder auto-copied to `~/.nexus-hub/templates/documentation/` | All platforms (shared) |
| `templates/ai-instructions/base-*.md` | **Yes -- edit all 5 lockstep files** (claude, codex, cursor, gemini, opencode). **But 5 is not the full set**: 17 template files exist and 13 are substantive. A behavioral rule meant for every agent must also reach `base-google-shared.md` (which covers Antigravity 1.0, Antigravity 2.0, and Gemini CLI by `@`-include, and Antigravity CLI transitively via `@base-antigravity-20.md`), the guardrails-only `base-{aider,kimi,openclaw,qwen,windsurf}.md`, `base-pi.md`, and `generic-instructions.md`. Only the lockstep five are machine-guarded; the other eight are not, so they are the ones a change silently misses. `## Writing Discipline` (v4.5.0) is a lockstep block: byte-identical across the five and asserted present and identical on all thirteen by a companion validator. `## Autonomous Operation` (v4.7.0) follows the same pattern, with its validator deriving the thirteen-template roster from the directory so a new template fails until it carries the block. | The respective platform |
| `scripts/<name>.py` or `scripts/<name>.js` | **Yes -- MUST add a copy step** in BOTH `scripts/installer.sh` AND `scripts/installer.ps1`, modeled after the existing `generate_report.py` entry. The installer copies scripts by **explicit name**, never by folder. | All platforms (shared under `~/.nexus-hub/scripts/`) |
| `configs/platform-defaults.json` (v3.16.0+) | No -- **repo-internal source, NOT a distributed artifact**. It is the single place a per-platform install-time behavioral default is declared. Its effect reaches users two ways: the derived core keys of `catalog/hooks/settings.json` (which the installer already copies), and install-time seeding into each platform's own config by `scripts/lib/integrations/platform_defaults.py`. Never hand-edit a derived artifact. | All platforms with a VERIFIED lever (see below) |
| `scripts/sync_platform_defaults.py` (v3.16.0+) | No -- **repo-internal guard, needs NO installer copy step**. Listed in `DEV_ONLY_SCRIPTS` in `catalog/hooks/tests/test_installer_smoke.py` alongside the other three repo-only guards. `--check` runs in `make validate` and CI; `--apply` regenerates the derived artifacts. | None (maintainer tooling) |
| `scripts/check_required_check_coverage.py` + `docs/policy/required-checks.json` (v3.17.6+) | No - **repo-internal guard plus its declared manifest, needs NO installer copy step**. Listed in `DEV_ONLY_SCRIPTS` in `catalog/hooks/tests/test_installer_smoke.py`. Runs in `make validate` and in CI's existing `validate` job (deliberately not a new job, which would need its own required context). Asserts every required status check is produced by a workflow that triggers unconditionally, so a required check can never sit Pending forever; `--sync` prints the live protection state via the user's own `gh` and never writes. | None (maintainer tooling) |
| `data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json` | No -- the installer reads these to fill `{{SKILL_INDEX}}` placeholders in every platform's instruction file. Updating them is mandatory when adding a skill. | All platforms whose instruction template embeds the index |
| `scripts/lib/integrations/<platform>.py` (v2.1.0+) | No file-copy edit; **MUST** import + `_register()` the subclass in `scripts/lib/integrations/__init__.py::_register_builtins()`. The runner is invoked automatically by both installers for the extended-platform set. | The platform configured by the subclass (e.g., Antigravity 2.0, Gemini CLI, Nexus-AI for the v2.1.0 extended set; Claude / Codex / Cursor / Gemini / OpenCode / Copilot subclasses also exist for future v2.2.0 parity migration). |
| Project-local surfaces (called from `nexus-hub init` -- v2.2.0+) | No file-copy edit; override `wire_project_surfaces(self, ctx) -> WriteResult \| None` on the integration subclass. The `nexus-hub init` subcommand (bash: `scripts/installer.sh init`; PowerShell: `scripts/installer.ps1 init`) walks every registered integration and invokes the hook. | Any platform whose subclass overrides the hook. Currently `cursor` (writes `.cursor/rules/nexus-hub.mdc`), `claude` (writes `.claude/settings.json` permissions stub when absent), `antigravity2` (writes `.agents/workflows/<name>.md` command files, since Antigravity reads slash commands only from the open project's `.agents/`), and `copilot` (v3.11.0, OPT-IN: writes thin `.github/skills/<name>/SKILL.md` wrapper files for the `core-developer` bundle when `NEXUS_HUB_COPILOT_SKILLS=1`, upgrading Copilot from behavioral-guardrails-only to a native project Agent Skills surface; off by default because `.github/skills/` is commit-visible, never overwrites an existing file). |

### Required steps for any change

Walk this checklist before proposing a PR:

1. **Is your change inside a folder already copied recursively by the installer?** (`catalog/skills/`, `catalog/commands/`, `catalog/agents/`, `catalog/rules/`, `catalog/hooks/`, `templates/documentation/`.) If yes, no installer edit needed.
2. **Is your change a standalone script in `scripts/`?** If yes, add a copy line in `scripts/installer.sh` (next to the existing `generate_report.py` block, around line 1395) AND a `Safe-Copy` line in `scripts/installer.ps1` (around line 1656). Both must reference the same destination under `~/.nexus-hub/scripts/`.
3. **Does your change introduce a new Python or Node dependency?** Prefer a lazy import with a clear `pip install <pkg>` hint on failure (e.g., `try: import X; except ImportError: print("Error: X not installed. Please run: pip install X")`, as used in `scripts/generate_report.py`). If a hard requirement is unavoidable, add a dependency check in both installers next to the existing `python-docx`/`python-pptx` check.
4. **Does your change touch a platform-specific instruction template?** If you edit any of `templates/ai-instructions/base-*.md`, apply the same change to all five (claude/codex/cursor/gemini/opencode). This is the "platform-agnostic" constraint. It is machine-enforced: `scripts/check_base_template_parity.py` (run by `make validate` and in CI) fails when a shared section heading, a shared placeholder token, or an invariant block (Tech Stack, Key Commands, Branching, End-of-Task Summary, Construction Discipline, Writing Discipline, Autonomous Operation, MCP Registry Policy) diverges across the five, while tolerating intentional per-platform lines (platform names, install paths). Note that `Output Minimization` is deliberately NOT an invariant block, because `base-claude.md` carries a legitimate extra bullet; `End-of-Task Summary` (added v3.15.10) IS one, because the rule is platform-agnostic by intent and has no valid per-platform variation; `Writing Discipline` (added v4.5.0) IS one for the same reason, since a cliche or an em-dash is a defect on every platform and the block binds the agent's own replies rather than a platform feature. It is a repo-internal guard like `check_version_sync.py`, so it needs no `.ps1` sibling and no installer copy step.
5. **Validate**: run `make validate` (JSON integrity) and `make lint` (ShellCheck) after edits. For new hooks, run `make test`. For installer changes, do a dry-run install into a throwaway directory and confirm the new artifact lands at the expected path.
6. **Document**: add an entry under `## [Unreleased]` in `CHANGELOG.md`.

### Dependency ceiling rationale

Every dependency upper bound MUST carry an adjacent comment that states the unacceptable or unknown newer-version behavior, why it matters, the last verification date, the evidence observed, the newer-version test result when one was run, and the exact condition for lifting the ceiling. When the original reason or newer-version behavior cannot be established, record that uncertainty explicitly instead of inventing a justification; for example, a runtime artifact download can violate the zero-outbound and zero-model-download guarantees even when the package API still appears compatible.

### Platform coverage caveats (current state)

Not every platform receives the same amount of the catalog. Four tiers exist: full file-tree (skills + commands + agents + rules + hooks), skills-bearing, slash-command-only, and behavioral-guardrails-only. Which platform sits in which tier, the dated vendor-verification notes behind each claim, and the deprecation callouts (the Gemini CLI sunset, the Windsurf and Kimi roster changes) all live in one place, because they are the narrative companion to the read/write surface table in the same file.

**Full detail**: the "Platform coverage tiers" section of [`docs/policy/platform-read-contracts.md`](docs/policy/platform-read-contracts.md). Read it before claiming a platform supports something, and before adding a platform to the roster.

## Required Status Checks (v3.17.6)

**A required status check MUST be produced by a job whose workflow triggers unconditionally.** Filter at the JOB level with `if:`, never at the workflow level with `paths:`. GitHub leaves a check from an untriggered workflow **Pending forever**, while a job skipped by an `if:` reports **Success**, so the two look like the same Actions-minute optimization and behave in opposite ways. Shipping v3.17.5 took six administrator bypasses for this one reason.

Two further traps, both fail-open:

- A job-level `if:` is evaluated **before** matrix expansion, so a skipped matrix job publishes only its bare job name and never `job (leg)`. Require an aggregate context (`ci-required`), never a per-leg one; `docs/policy/required-checks.json` is the declared list and `tests/validators/test_ci_required_gate.py` rejects a leg context.
- `needs:` alone fails open, because GitHub skips a job whose dependency failed and a skipped required check reports Success. Gate with `!cancelled() && ... != 'false'`; both halves are load-bearing.

`scripts/check_required_check_coverage.py` enforces this from the manifest inward and `tests/workflows/test_workflow_policy_repo_wide.py` from the workflow outward. Reasoning and rejected alternatives: `docs/decisions/implemented/tooling/2026-08-19-required-checks-must-be-unconditionally-produced.md`.


## Documentation Retention

Per-version docs age out on a stated rule instead of accumulating: a minor two or more behind current has its `development/` subtree archived to `docs/archive/v<MAJOR>/v<MAJOR>.<MINOR>/development/`, while `plans/`, `comparisons/`, `known-gaps.md`, and the non-versioned subtrees never age out. `scripts/check_docs_retention.py` reports drift and always exits 0; `[[docs-layout-refactor]]` performs the move. Full policy: [`docs/policy/docs-retention.md`](docs/policy/docs-retention.md).

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

**Plan lifecycle (v4.0.0).** This repository follows the same lifecycle it distributes. Every plan phase verifies locally and ends with ONE local commit; unrelated dirty-worktree changes are left untouched and only files tracing to the plan are staged. No non-final phase pushes, opens a pull request, or starts remote CI, because a pipeline run per phase bills to validate work the plan itself calls incomplete. A phase records its CI impact and edits `.github/workflows/` only when CI/CD is that phase's stated deliverable. The FINAL phase reconciles the pipeline against the canonical contract via `[[cicd-architect]]`, completes the local gate, then pushes ONCE and opens the integration pull request to `develop` -- the plan's first remote validation, run against the merge result. A red required check reopens that phase and is reproduced locally before any re-push. Post-merge work stays minimal, and `/update release` starts only after the `develop` result is green and merged. A `push`-filtered workflow means "a merge or a release happened" ONLY because `main` and `develop` reject direct pushes; that protection is an external repository setting, verified by hand and never mutated automatically. Contract: [`docs/releases/v4/v4.0/development/ci-cd-lifecycle-contract.md`](docs/releases/v4/v4.0/development/ci-cd-lifecycle-contract.md).

**Capability usage gate (release notes).** A release that introduces or materially changes an OPT-IN capability, installer flag, managed skill, or host surface must document five things per surface in its release notes: the exact activation mechanism, a runnable validation command, the exact disable / rollback path, the authority or privacy boundary that activation does NOT grant, and a canonical documentation link. Nexus-Hub ships an unusually high density of such surfaces (`NEXUS_HUB_COPILOT_SKILLS`, `--enterprise` / `-Enterprise`, `NEXUS_DISABLED_HOOKS`, `NEXUS_HOOK_PROFILE=minimal`), and the fourth element is both the most-skipped and the only one that fails silently rather than loudly. The gate applies ONLY to opt-in surfaces; a release with none satisfies it with a single explicit no-change declaration. Full definition and worked examples: governance step 6 in [`catalog/commands/update.md`](catalog/commands/update.md).

## Decision Records

Non-trivial changes MUST include or update a decision record in the same PR: a new policy, a new supported platform, a new validator or gate, a rename carrying migration cost, or a design that was proposed and declined. Mechanical, local, or single-file edits are exempt.

Records live at `docs/decisions/<lifecycle>/<class>/YYYY-MM-DD-<slug>.md` and require `## Alternatives considered`, because a decision recorded without what it beat invites re-litigation. Check `rejected/` before proposing anything that touches an existing policy or platform surface. Format, lifecycle, and the three-surface split against known-gaps and solutions: [`docs/decisions/README.md`](docs/decisions/README.md).

## Critical Conventions

- **Never edit `data/` files manually** unless registering a new skill -- they are generated. The source of truth is `catalog/skills/`.
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
