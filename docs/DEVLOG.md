# Development Log

## [2026-04-06] - Release 0.9.3: Agent-Skills Adoption, 9 New Skills, and Session Workflows

*   **Goal**: Ship a minor-content patch release that closes SDLC coverage gaps surfaced by the agent-skills cross-project comparison, introduces a session lifecycle command, and standardizes skill anatomy across 19 priority skills.
*   **What Changed**:
    *   **9 New Skills** (`catalog/skills/`): Added `idea-refine` (developer-experience), `spec-driven-development` (developer-experience), `incremental-implementation` (workflow), `context-engineering` (ai-development), `frontend-ui-engineering` (developer-experience), `browser-testing-with-devtools` (testing), `code-simplification` (code-cleanup), `shipping-and-launch` (workflow), and `using-devai-hub` (workflow, meta-skill). These close the Define and Ship phases of the SDLC that were under-represented relative to the agent-skills catalog. Total: 183 skills.
    *   **`wrap-up-session` Command** (`catalog/commands/wrap-up-session.md`): 7-phase session close-out workflow invoked via `/wrap-up-session` or `/wrap-up-session --quick`. Phases: (1) live session history capture, (2) gitignore hygiene, (3) documentation sync, (4) devlog update, (5) memory refresh, (6) version assessment, (7) commit message generation. Adopted from the agent-skills comparison gap analysis.
    *   **SessionStart Hook** (`catalog/hooks/session-start.sh`): Lightweight hook that injects the `using-devai-hub` meta-skill orientation at every new Claude Code session. Registered as a SessionStart event in `catalog/hooks/settings.json`. Ensures skill catalog awareness without requiring any explicit user action — a pattern directly adopted from agent-skills.
    *   **Skill Anatomy Standardization**: Added Common Rationalizations tables (excuses agents might make to skip a skill + rebuttals) and binary Verification checklists (observable artifact-based criteria) to 19 priority skills. Skills covered: ai-agent-development, prompt-engineering, api-design, architecture-design, bug-localization, semantic-bug-detector, behavior-preservation-checker, code-quality, intent-based-review, security-review, cicd-architect, observability-setup, authentication-patterns, dependency-security-audit, integration-test-generator, unit-tests, code-commit-workflow, plan-before-code, test-driven-development.
    *   **Plugin Marketplace Manifests** (`.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`): Added official Claude Code plugin marketplace support. Enables `claude plugin install devai-hub` as a distribution path alongside the existing shell installer scripts.
    *   **`AGENTS.md`** (root): 187-line guidance document for AI coding agents. Documents the full repository structure (skills, commands, hooks, agents), contribution patterns, required frontmatter fields, and registration workflow for new skills/commands/hooks.
    *   **4 Reference Checklists** (`catalog/checklists/`): Standalone reference documents for api-design, architecture, security, and testing patterns. Adopted from the agent-skills comparison.
    *   **Cross-Project Comparison Report** (`docs/v0.9.2/comparison-agent-skills.md`): Full 12-section analysis of DevAI-Hub vs. Addy Osmani's agent-skills repository. Executive summary, profiles, gap analysis, and prioritized adoption roadmap with 11 adoption candidates across 4 priority tiers.
    *   **Permission Expansion** (`configs/permissions/claude-permissions.json`): Added 40+ new bash allowlist entries: binary inspection (`od`, `hexdump`, `xxd`, `strings`), archive listing (`tar -tf`, `unzip -l`), checksums (`sha256sum`, `sha1sum`, `md5sum`, `shasum`, `cksum`), compression read (`zcat`, `gzip -l`), system info (`uptime`, `hostname`, `id`, `groups`), and xargs variants for all of the above.
    *   **Hook Test Expansion** (`catalog/hooks/tests/test_format_bash_description.py`): 61 new test cases covering all expanded allowlist patterns plus pipeline regression cases and negative tests for destructive `tar` flags (`--delete`, `--remove-files`).
    *   **Infrastructure Docs** (`infrastructure/tools/README.md`, `infrastructure/hooks/README.md`, `infrastructure/integrations/README.md`): Overhauled tools README with current metrics (183 skills, 22 categories, correct project name); fixed stale version footers across infrastructure docs.
    *   **VS Code Extension** (`extensions/claude-usage-monitor/src/extension.ts`): Removed emoji from notification messages for better cross-platform compatibility.
    *   **Version Bump**: Updated `CHANGELOG.md`, `README.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, and `data/marketplace.json` from 0.9.2 to 0.9.3.
*   **Design Rationale**: The agent-skills comparison (`docs/v0.9.2/comparison-agent-skills.md`) identified three structural gaps in DevAI-Hub: (1) no Define-phase skills (`idea-refine`, `spec-driven-development`), (2) no Ship-phase skills (`shipping-and-launch`), and (3) no session lifecycle management (`wrap-up-session`, SessionStart hook). The 9 new skills and session workflow commands directly address all three gaps. The skill anatomy improvements (Common Rationalizations + Verification) adopt the quality pattern that makes agent-skills skills more reliably executed.
*   **Current Status**: Verified. All version references consistent at 0.9.3.

---

## [2026-04-06] - Release 0.9.2: Implementation Plan Workflow and Hook Test Suite

*   **Goal**: Ship a patch release that adds structured implementation-plan tooling (two commands and a workflow skill) and establishes a test suite for the Bash description formatting hook.
*   **What Changed**:
    *   **`generate-implementation-plan` Command** (`catalog/commands/generate-implementation-plan.md`): New 199-line command that walks through a multi-phase planning workflow — research, design, and plan output — so AI agents can produce structured, phased implementation plans before writing any code.
    *   **`implement-phase` Command** (`catalog/commands/implement-phase.md`): New 317-line command for executing a single named phase from a prior implementation plan, scoping context and tooling to just that phase to reduce cognitive load and token consumption.
    *   **`implementation-plan` Skill** (`catalog/skills/workflow/implementation-plan/`): New 292-line workflow skill with an OpenAI agent YAML (`agents/openai.yaml`) providing the same planning capability as a reusable skill rather than a one-off command. Skill index and workflow category README updated accordingly (175 total skills).
    *   **Hook Test Suite** (`catalog/hooks/tests/test_format_bash_description.py`): 763-line comprehensive test suite for the `format-bash-description.py` PreToolUse hook. Covers approval flow branches, description box rendering, allowlist matching edge cases, and multi-line command patterns. Added `catalog/hooks/tests/__init__.py` to make the directory a proper Python package.
    *   **Permission Configuration** (`configs/permissions/claude-permissions.json`): Expanded the bash tool allowlist with additional safe patterns identified during hook hardening and test authoring.
    *   **Setup Project Command** (`catalog/commands/setup-project.md`): Minor clarifications to 13 lines of the setup workflow.
    *   **Version Bump**: Updated `CHANGELOG.md`, `README.md`, `README_zh.md`, and `docs/DEVLOG.md` from 0.9.1 to 0.9.2.
*   **Current Status**: Verified. All version references consistent at 0.9.2.

---

## [2026-04-03] - Release 0.9.1: Hooks Hardening and VS Code Extension Stability

*   **Goal**: Ship a patch release that fixes bugs introduced or surfaced after the 0.9.0 release — primarily tightening the Bash description hook approval flow, fixing a shell-construct parsing regression, and stabilizing the VS Code usage monitor extension.
*   **What Changed**:
    *   **Bash Description Hook** (`catalog/hooks/format-bash-description.py`): Enforced strict 2-case approval logic so only explicit approvals pass through. Expanded the bash tool allowlist. Made the description box rendering conditional on the permission allow list to avoid spurious UI output when the hook is not applicable.
    *   **Require-Description Hook** (`catalog/hooks/require-description.sh`): Fixed a shell-construct parsing bug that caused false negatives on certain bash command patterns, allowing undescribed commands to slip through.
    *   **VS Code Extension — Auto-Switch** (`extensions/claude-usage-monitor/src/extension.ts`): Rewrote the auto-switch module to read and write `settings.json` directly instead of using a deprecated VS Code API, eliminating the repeated notification problem on every status-bar update.
    *   **VS Code Extension — Usage Notifications**: Changed the notification logic so that when usage crosses 90%, only the 90% alert fires — the 50% and 75% notifications are suppressed to avoid alert fatigue.
    *   **VS Code Extension — Store and Types** (`src/usageStore.ts`, `src/types.ts`, `src/dashboardPanel.ts`): Fixed type definition mismatches and store initialization bugs that caused the dashboard to display stale or incorrect session data.
    *   **Permission Configuration** (`configs/permissions/claude-permissions.json`): Expanded the git command allowlist to cover additional legitimate patterns identified during hook hardening.
    *   **Version Bump**: Updated `data/marketplace.json`, `data/templates.json`, `README.md`, and `CHANGELOG.md` from 0.9.0 to 0.9.1.
*   **Current Status**: Verified. All version references consistent at 0.9.1.

---

## [2026-03-26] - Release 0.9.0: Specialist Skills Expansion, Permission System, and Multi-IDE Support

*   **Goal**: Expand the skills catalog with 12 new specialist skills, introduce a permission configuration system for multi-AI-platform security management, add auto-switching capabilities to the VS Code extension, and broaden IDE support to Cursor and OpenCode.
*   **What Changed**:
    *   **12 New Specialist Skills**: Added framework specialists (Astro, Svelte, Vue) in `catalog/skills/framework-specialists/` and specialized domain skills (Android development, iOS development, DOCX/XLSX/PPTX/PDF generation, GIF/sticker maker, GLSL shader development) in `catalog/skills/specialized-domains/`. Added session-history workflow skill in `catalog/skills/workflow/`. Total skills now 174 across 20 categories.
    *   **Permission Configuration System**: Created `configs/permissions/` with pre-built permission files for Claude (`claude-permissions.json`), Codex (`codex-permissions.toml`), Copilot (`copilot-permissions.json`), and Gemini (`gemini-permissions.json`). Added `trusted-domains.json` for cross-platform domain allowlists. Added `scripts/Install-DevAI-Permissions.ps1` for one-click permission deployment. Added supporting documentation in `docs/permissions-research.md` and `docs/permissions-setup.md`.
    *   **Auto-Switcher Extension**: Added `extensions/claude-usage-monitor/src/autoSwitcher.ts` for automatic model/plan switching based on usage thresholds. Enhanced dashboard panel with improved session visualizations. Added TypeScript type definitions (`types.ts`) for session management.
    *   **Developer Tooling**: Added `catalog/hooks/format-bash-description.py` (PreToolUse hook for Bash description formatting), `scripts/validate_skills.py` (automated SKILL.md validation), and React expert reference documents (dependency injection, data fetching, performance, testing patterns) in `catalog/skills/framework-specialists/react-expert/references/`.
    *   **IDE Support**: Added instruction templates for Cursor (`templates/ai-instructions/base-cursor.md`) and OpenCode (`templates/ai-instructions/base-opencode.md`).
    *   **Chinese Documentation**: Added `README_zh.md` with full Chinese translation of the main README.
    *   **Marketplace Metadata**: Added `data/marketplace.json` for plugin registry compatibility with skill counts, platform support, and category metadata.
    *   **Gitignore Cleanup**: Replaced blanket `.github/` ignore with targeted `.github/copilot-instructions.md` to allow tracking of GitHub workflows, PR templates, and dependabot configuration. Removed duplicate `dist/` entry.
    *   **Version Bump**: Updated `data/templates.json`, `data/marketplace.json`, `scripts/installer.ps1`, `scripts/installer.sh`, `docs/CATALOG-COVERAGE.md`, `catalog/skills/README.md`, `README.md`, `README_zh.md`, and `CHANGELOG.md` from 0.8.9 to 0.9.0.
*   **Current Status**: Verified. All version references consistent at 0.9.0.

## [2026-03-23] - Release 0.8.9: Tiered Skill Discovery, MCP Skill Server, and Phased Release Orchestrator

*   **Goal**: Enable programmatic and hierarchical skill discovery by enriching all skills with tiered summaries, shipping an MCP skill server, and maturing the release process into a phased orchestrator.
*   **What Changed**:
    *   **Tiered Skill Summaries**: Added `summary_l0` (one-liner) and `overview_l1` (full context paragraph) frontmatter fields to all 162 SKILL.md files across 20 categories. These allow AI agents to browse skills at increasing detail levels without consuming full skill text, reducing context window pressure during skill selection.
    *   **MCP Skill Server**: Created `extensions/devai-skill-server/`, a Python MCP extension providing `search_skills`, `get_skill`, `list_categories`, `list_bundles`, and `get_bundle` tools. Includes keyword-based and embedding-ready search backends, configuration via environment variables, and a test suite (`conftest.py`, `test_catalog.py`, `test_config.py`, `test_search_keyword.py`). Registered in `catalog/mcp-configs/mcp-servers.json`.
    *   **Compiled Skill Index**: Generated `data/SKILL_INDEX.md` as a static skill catalog table. Added `{{SKILL_INDEX}}` placeholder and Skill Discovery section to `templates/ai-instructions/base-claude.md`, `base-codex.md`, `base-gemini.md`, and `generic-instructions.md` so installed instruction files include the full index automatically.
    *   **Build Tooling**: Added `Makefile` for catalog build automation, `LICENSE` (MIT), and `.pr_agent.toml` for PR Agent configuration. Updated `build_skills_catalog.py` to support the nested `category/skill/` directory structure and extract L0/L1 summaries into `data/skills.json`.
    *   **Pre-commit Hooks**: Added shellcheck and commitizen hooks to `.pre-commit-config.yaml`.
    *   **Release Orchestrator**: Restructured `catalog/commands/update-version.md` from 14 linear steps into five phases (A: Analysis, B: Cleanup, C: Version Bump, D: Documentation Sync, E: Validation) with explicit user confirmation gates between phases and delegation to sub-commands (`/refactor-project-layout`, `/update-gitignore`, `/update-documentation`, `/update-devlog`).
    *   **Installer Updates**: Both `scripts/installer.ps1` and `scripts/installer.sh` updated for the new nested catalog directory structure.
    *   **Documentation Sync**: Updated `catalog/skills/README.md` version to 0.8.9. Updated `docs/CATALOG-COVERAGE.md` version, date, and skill counts (136 to 162, 18 to 20 categories). Added `docs/v0.8.8/comparison-OpenViking.md`.
    *   **Version Bump**: Updated `data/templates.json`, `README.md`, `CHANGELOG.md`, `catalog/skills/README.md`, `docs/CATALOG-COVERAGE.md`, `scripts/installer.ps1`, and `scripts/installer.sh` from 0.8.8 to 0.8.9.
*   **Current Status**: Verified. All version references consistent at 0.8.9.

## [2026-03-20] - Release 0.8.8: Specialist Skills Expansion and Full Catalog Sync

*   **Goal**: Expand the skills catalog with 20 new specialist skills, enforce transparent Bash commands via the `require-description` hook, and fully synchronize all documentation and `skills.json` with the 162 on-disk skills.
*   **What Changed**:
    *   **`require-description` Hook**: Added `catalog/hooks/require-description.sh` (PreToolUse) that enforces bordered description blocks on all Bash, Cmd, and PowerShell commands; blocks execution (exit 2) when the block is absent. Standardized to wider no-pad format in a follow-up refactor.
    *   **20 New Specialist Skills**: Added language specialists (C++, C#, Java, JavaScript, PowerShell, Python, TypeScript) in `catalog/skills/language-specialists/`, infrastructure specialists (Azure infra engineer, network engineer, platform engineer, SRE engineer) in `catalog/skills/infrastructure/`, orchestration (error-coordinator, multi-agent-coordinator) in `catalog/skills/orchestration/`, business-product (business-analyst, scrum-master, product-manager, technical-writer) in `catalog/skills/business-product/`, and fintech-engineer in `catalog/skills/specialized-domains/`.
    *   **18 Category READMEs**: Added README.md files to every `catalog/skills/` subdirectory with skill listings and descriptions.
    *   **Skills Catalog Rebuilt**: `data/skills.json` rebuilt to match all 162 on-disk skills — added 7 missing entries, removed 4 misplaced command entries, sorted by category then name.
    *   **Documentation Sync**: Rewrote `catalog/skills/README.md` (47 to 162 skills, 8 to 20 categories). Updated root `README.md` (134 to 162 skills, added Codex support). Fixed `extensions/claude-usage-monitor/README.md` (corrected defaults, removed ghost settings). Added `CONTRIBUTING.md`.
    *   **Usage Monitor Fix**: Default model updated from Sonnet to Opus 4.6 in usage-display hook.
    *   **Version Bump**: Updated `data/templates.json`, `data/skills.json`, `scripts/installer.ps1`, `scripts/installer.sh`, `docs/CATALOG-COVERAGE.md`, `catalog/skills/README.md`, and `README.md` from 0.8.7 to 0.8.8.
*   **Current Status**: Verified. All version references consistent at 0.8.8.

## [2026-03-16] - Release 0.8.7: Three New Commands and Mandatory File-Access Transparency Rule

*   **Goal**: Expand the command catalog with three high-value utility commands (security audit, gitignore cleanup, and commands cheatsheet) and enforce transparent file-access behavior across all AI instruction templates.
*   **What Changed**:
    *   **`run-security-audit` Command**: Added `catalog/commands/run-security-audit.md` — a 9-phase static security audit (secrets, git hygiene, installer security, input validation, auth/authz, dependency CVEs, configuration hardening, dangerous code patterns) with a `--fix` active remediation loop that patches findings in P0→P3 priority order and re-audits until clean. `data/skills.json` updated with new command entry.
    *   **`commands-cheatsheet` Command**: Added `catalog/commands/commands_cheatsheet.md` — discovers all global and project slash commands, assigns them to logical categories, and renders a live Markdown cheatsheet table with descriptions and usage examples.
    *   **`update-gitignore` Command**: Added `catalog/commands/update-gitignore.md` — audits `.gitignore` against the full git index using a G0–G3 severity scale, identifies wrongly-tracked files and missing patterns, and applies index cleanup and Git LFS recommendations after explicit user confirmation.
    *   **Mandatory File-Access Rule**: Added a one-sentence plain-language explanation requirement before every Read, Glob, and Grep tool call to `templates/ai-instructions/base-claude.md`, `base-codex.md`, `base-gemini.md`, and all four project example CLAUDE.md files (`examples/django-api-CLAUDE.md`, `go-microservice-CLAUDE.md`, `nextjs-saas-CLAUDE.md`, `rust-api-CLAUDE.md`).
    *   **Version Bump**: Updated `data/templates.json`, `scripts/installer.ps1`, `scripts/installer.sh`, `docs/CATALOG-COVERAGE.md`, and `README.md` from 0.8.6 to 0.8.7.
*   **Current Status**: Verified. All version references consistent at 0.8.7.

## [2026-03-13] - Release 0.8.6: Specialist Agents, Language Rules, Auth Logout Fix, Repo Layout Enforcement

*   **Goal**: Expand the catalog with 10 specialist agents, language-specific rule sets, 5 new skills, and 4 new commands; fix the Claude Code daily logout regression caused by the auth monitor's token-refresh race condition; and enforce the documented repository layout by moving catalog files to `data/` and `DEVLOG.md` to `docs/`.
*   **What Changed**:
    *   **Specialist Agents**: Added 10 agent definition files in `catalog/agents/` (architect, build-error-resolver, code-reviewer, doc-updater, harness-optimizer, loop-operator, planner, refactor-cleaner, security-reviewer, tdd-guide); installer Phase 4 updated in `scripts/installer.ps1` and `scripts/installer.sh` to install them.
    *   **Language Rule Sets**: Added coding-style, security, and testing rules for Bash, Go, Python, and TypeScript in `catalog/rules/`; Phase 4 installer step offers rule-set selection.
    *   **MCP Server Configs**: Added `catalog/mcp-configs/mcp-servers.json` with curated server definitions; Phase 4 installs them to `~/.claude/mcp-configs/`.
    *   **New Skills**: Added `ai-billing-safeguards`, `claude-agent-sdk`, `multi-provider-ai`, `project-layout-refactor`, and `temporal-orchestration` to `catalog/skills/`; `data/skills.json` updated.
    *   **New Commands**: Added `refactor-project-layout`, `run-penetration-test`, `tdd`, and `continue-session` to `catalog/commands/`.
    *   **Hook Profiles**: Added `auto-format-on-write.sh`, `large-file-guard.sh`, `lint-on-write.sh`, `notify-on-complete.sh`, and `session-summary.sh` to `catalog/hooks/`.
    *   **Auth Logout Fix**: Deleted `scripts/claude-auth-monitor.ps1` and `scripts/claude-auth-automate.ahk`; removed `Install-AuthMonitor` function from `scripts/installer.ps1`; increased `claudeUsage.refreshInterval` default from 5 to 10 minutes in `extensions/claude-usage-monitor/package.json`.
    *   **Repository Layout**: Moved `skills.json`, `bundles.json`, `templates.json`, `workflows.json`, `report_data.json` to `data/`; moved `DEVLOG.md` to `docs/`.
    *   **Version Bump**: Updated `data/templates.json`, `scripts/installer.ps1`, `scripts/installer.sh`, `docs/CATALOG-COVERAGE.md`, `README.md`, and `extensions/claude-usage-monitor/package.json` from 0.8.5 / 0.3.0 to 0.8.6 / 0.3.1.
*   **Current Status**: Verified. All version references consistent at 0.8.6.

## [2026-03-10] - Release 0.8.5: Extra Credits Tracking, OAuth Auto-Refresh, Auto-Devlog Hook

*   **Goal**: Ship usage-monitor reliability and visibility improvements (extra credits, OAuth refresh, 1M warnings, model classification fixes) alongside the auto-devlog hook and generate-dev-history command, plus a bash installer correctness fix.
*   **What Changed**:
    *   **Extra Credits Dashboard**: Added `ExtraUsageInfo` interface and `extraUsage` field to `UsageData`; `usageFetcher.ts` maps `extra_usage` from the API; `dashboardPanel.ts` renders a progress bar with dollar amounts (fixed cents-to-dollars conversion) and a dynamic "on Month Day" reset label.
    *   **1M Context Warnings**: Added info banner in `dashboardPanel.ts` and tooltip in `statusBarManager.ts` for users on 1M extended-context models; expanded `recommendations.ts` with Sonnet-as-default guidance.
    *   **OAuth Token Auto-Refresh**: `usageFetcher.ts` now performs a token refresh on 401 expiry and 429 rate-limit responses using the `refresh_token` from `~/.claude/.credentials.json`; adds `token-refresh-failed` error code.
    *   **Model Fixes**: `formatModelName` returns "Default (Sonnet)"; `recommendations.ts` treats "default" as Sonnet; 30-second `AbortController` timeout added to all fetch calls; in-flight guard fixed so UI refreshes even during an active fetch.
    *   **Auto-Devlog Hook**: Added `infrastructure/hooks/auto-devlog.sh` (registered in `settings.json` Stop handler) and `catalog/commands/generate-dev-history.md`.
    *   **Bash Installer Fixes**: `scripts/installer.sh` — `read_prompt` and language-selection menu redirected to stderr; npm/code error handling switched to `if !` pattern.
    *   **Version Bump**: Updated `templates.json`, `scripts/installer.ps1`, `scripts/installer.sh`, `infrastructure/hooks/README.md`, `README.md`, and `extensions/claude-usage-monitor/package.json` from 0.8.4 / 0.2.0 to 0.8.5 / 0.3.0.
*   **Current Status**: Verified. All version references consistent at 0.8.5.

## [2026-03-09] - Release 0.8.4: Dynamic Model Detection in Usage Monitor

*   **Goal**: Remove the manual `claudeUsage.currentModel` VS Code setting and replace it with automatic detection from Claude Code's own model picker (`claudeCode.selectedModel`), while making the extension forward-compatible with any model ID format including 1M extended-context variants.
*   **What Changed**:
    *   **Dynamic Model Detection**: Rewrote `getCurrentModel()` in `usageStore.ts` to read `claudeCode.selectedModel` (the VS Code setting maintained by Claude Code's model picker) with a `"sonnet"` fallback. Users no longer need to manually update a second setting when switching models.
    *   **Open Model ID Support**: Replaced the `ClaudeModel` union type and `MODEL_DISPLAY_NAMES` record in `types.ts` with a `string` type and three new utilities: `formatModelName()` (parses any model ID to a human-readable label, handles `[1m]` suffix), `baseModelId()`, and `is1MContext()`. Updated `dashboardPanel.ts`, `extension.ts`, and `recommendations.ts` to use these helpers.
    *   **1M Context Recommendation**: Added a new rule to `recommendations.ts` that triggers when session usage is high and the active model is a `[1m]` extended-context variant, recommending the user switch to the standard context model for tasks that do not require processing large files.
    *   **Live Model Switch Response**: Added a `onDidChangeConfiguration` listener in `extension.ts` for `claudeCode.selectedModel` so the status bar and open dashboard panel refresh immediately when the user switches models — no polling lag.
    *   **Setting Removed**: Deleted the `claudeUsage.currentModel` configuration entry from `package.json`. The extension no longer exposes a manual model selector.
    *   **Version Bump**: Updated `templates.json`, `scripts/installer.ps1`, `scripts/installer.sh`, `infrastructure/hooks/README.md`, `README.md`, and `extensions/claude-usage-monitor/package.json` from 0.8.3 / 0.1.0 to 0.8.4 / 0.2.0.
*   **Current Status**: Verified. All version references consistent at 0.8.4.

## [2026-03-06] - Release 0.8.3: Context Optimization, Live Usage Monitor, Output Minimization

*   **Goal**: Package post-0.8.2 additions under an official release: a new context-optimization skill, a search-skills command, live auto-polling in the usage monitor dashboard, output minimization rules for all AI templates, and supporting governance files and guides.
*   **What Changed**:
    *   **Context Optimization Skill**: Added `catalog/skills/context-optimization/SKILL.md` for token budget management, context pruning, and structured context engineering patterns.
    *   **Search Skills Command**: Added `catalog/commands/search-skills.md` enabling keyword, category, and role-based discovery across the 135-skill catalog.
    *   **Usage Monitor**: Extracted `usageFetcher.ts` module with OAuth token refresh (reads `~/.claude/.credentials.json`); removed `inputCollector.ts` (manual credential input eliminated); added live auto-polling with configurable interval; added refresh indicator to `statusBarManager.ts`; streamlined `extension.ts` (-121 lines).
    *   **AI Instruction Templates**: Added output minimization rules (suppress verbose progress bars, prefer `--quiet` flags, summarize long output) to `base-claude.md`, `base-codex.md`, and `base-gemini.md`.
    *   **Skills Registry**: Updated `skills.json` with new skill entries.
    *   **Governance & Guides**: Added `CODE_OF_CONDUCT.md`, `SECURITY.md`, `guides/RTK_CONTEXT_COMPRESSION.md`, `llms.txt`, and `docs/v0.8.2/` design documentation.
    *   **Version Bump**: Updated `templates.json`, `scripts/installer.ps1`, `scripts/installer.sh`, `infrastructure/hooks/README.md` from 0.8.2 to 0.8.3.
*   **Current Status**: Verified. All version references consistent at 0.8.3.

## [2026-03-05] - Release 0.8.2: 134 Skills, Codex Support, Usage Monitor Overhaul

*   **Goal**: Package the catalog expansion (94 → 134 skills), Codex AGENTS.md installer support, 7 new workflows, 6 new hook templates, and a major usage monitor reliability overhaul under an official version marker.
*   **What Changed**:
    *   **Catalog**: Grew from 94 to 134 skills with new Bug Fixing category (5 skills), enriched all role bundles, added Bug Hunter bundle; 7 new workflows added to `workflows.json`.
    *   **Hooks Catalog**: Added 6 new hook templates to `catalog/hooks/settings.json` (secret-scan, large-file-guard, escalation-trigger, auto-format-on-write, lint-on-write, notify-on-complete, session-summary).
    *   **Codex Support**: `scripts/installer.ps1` and `scripts/installer.sh` now install commands to `prompts/` and render `AGENTS.md` from `templates/ai-instructions/base-codex.md` (open standard for Codex, Jules, Cursor, Aider).
    *   **Usage Monitor**: Refactored `FetchError` to typed object; added retry/backoff for 429 and 5xx; suppressed rate-limit popups; added stale data indicator; added urgency escalation notifications; added concurrency guard (`fetchInFlight`); lowered default refresh from 15 to 5 min.
    *   **Templates**: Strengthened mandatory bash command explanation rule in `base-claude.md` and `base-gemini.md`.
    *   **Documentation**: Added custom agent configuration section to `guides/SUBAGENTS_GUIDE.md`.
    *   **Version Bump**: Updated `templates.json`, `scripts/installer.ps1`, `scripts/installer.sh`, `infrastructure/hooks/README.md`, `README.md` from 0.8.1 to 0.8.2.
*   **Current Status**: Verified. All version references consistent at 0.8.2. Skills total: 134 across 17 categories.

## [2026-03-04] - Release 0.8.1: No-Hard-Wrap Output Formatting Rule

*   **Goal**: Prevent AI assistants from hard-wrapping paragraph text at ~80 characters, which causes text not to reflow with window width in plans, PR descriptions, and other output.
*   **What Changed**:
    *   **Base Templates**: Added no-hard-wrap formatting rule to `base-claude.md` (Communication Style) and `base-gemini.md` (Working Conventions).
    *   **Coding Instructions**: Added rule 4 (Text Wrapping) to the Global Style & Communication Preferences section in all 7 language templates (python, javascript, typescript, java, go, cpp, csharp).
    *   **Version Bump**: Updated `templates.json`, `scripts/installer.ps1`, `scripts/installer.sh`, `infrastructure/hooks/README.md` from 0.8.0 to 0.8.1.
*   **Current Status**: Verified. All version references consistent at 0.8.1.

## [2026-03-03] - Release 0.8.0: 19 New Skills, Bundles, Workflows

*   **Goal**: Close critical skill gaps identified by comparative analysis against antigravity-awesome-skills (970+ skills), adding architecture, AI development, and framework expertise while introducing role-based bundles and goal-based workflows.
*   **What Changed**:
    *   **Architecture Skills** (new category, 5 skills): `architecture-design` (C4, ADRs, fitness functions), `ddd-strategic-design` (bounded contexts, aggregates, event storming), `api-design` (REST/GraphQL/gRPC, versioning, RFC 7807), `microservices-patterns` (saga, circuit breaker, CQRS), `event-driven-architecture` (Kafka, event sourcing, outbox pattern).
    *   **AI Development Skills** (new category, 3 skills): `ai-agent-development` (ReAct, tool use, memory systems, multi-agent), `rag-implementation` (chunking, embeddings, vector stores, evaluation), `prompt-engineering` (chain-of-thought, few-shot, versioning, cost optimization).
    *   **Framework Specialist Skills** (new category, 3 skills): `react-expert` (hooks, state management, React 19), `nextjs-expert` (App Router, Server Components, server actions), `fastapi-expert` (Pydantic v2, dependency injection, async DB).
    *   **Infrastructure Skills** (4 new): `database-design` (schema modeling, indexing, zero-downtime migrations), `data-pipeline-design` (ETL/ELT, Airflow, dbt, Kafka), `observability-setup` (OpenTelemetry, Prometheus, Grafana), `containerization` (multi-stage Dockerfiles, security scanning, BuildKit).
    *   **Testing/Security/DevEx Skills** (4 new): `e2e-testing-automation` (Playwright, page objects, CI sharding), `authentication-patterns` (OAuth 2.0 + PKCE, JWT, passkeys, RBAC), `async-patterns` (async/await, channels, structured concurrency), `graphql-development` (DataLoader, federation, subscriptions).
    *   **Bundles System**: Created `bundles.json` with 10 role-based collections (Core Developer, Frontend Engineer, Backend Engineer, AI Engineer, Architect, DevOps Engineer, Security Specialist, Compliance Auditor, QA Engineer, Tech Lead).
    *   **Workflows System**: Created `workflows.json` with 10 goal-based workflows (Full Code Review, Security Audit, New Project Setup, API Development, Release Preparation, Legacy Modernization, AI Agent Pipeline, Compliance Assessment, Test Coverage Boost, Production Readiness).
    *   **Commit Message Templates**: Removed "Wrap at 72 characters" body rule from `code-commit-workflow` and `generate-commit-message`; replaced with single-line bullet point rule.
    *   **Version Bump**: Updated `templates.json`, `scripts/installer.ps1`, `scripts/installer.sh`, `infrastructure/hooks/README.md` from 0.7.1 to 0.8.0.
*   **Current Status**: Verified. All version references consistent at 0.8.0. Skills total: 94 across 16 categories.

## [2026-03-03] - Release 0.7.1: No-AI-Attribution Rules, Shell Command Clarity

*   **Goal**: Enforce a universal policy preventing AI coding assistants from adding `Co-Authored-By` lines or AI attribution footers to commit messages.
*   **What Changed**:
    *   **Code Commit Workflow Skill**: Removed conflicting `Co-authored-by: Jane Doe` example from footer section, replaced "Add co-authors" with "Add trailer metadata", added blockquote prohibition rule and quality checklist item.
    *   **Generate Commit Message Command**: Added `DO NOT` rule under Footer step and bold warning after the output example.
    *   **Instruction Templates**: Added "no AI attribution" rule to `base-claude.md` (Critical Rules), `base-gemini.md` (Working Conventions), and `generic-instructions.md` (Git Safety). Also added "Shell Command Clarity" rule to all three templates.
    *   **Global/Project CLAUDE.md**: Added no-attribution rule to `~/.claude/CLAUDE.md`, project `CLAUDE.md`, and `catalog/CLAUDE.md` fallback template (gitignored, applied on disk).
    *   **README Fix**: Corrected skills count from 63 to 75 (stale since v0.7.0).
    *   **Version Bump**: Updated `templates.json`, `scripts/installer.ps1`, `scripts/installer.sh`, `infrastructure/hooks/README.md` from 0.7.0 to 0.7.1.
*   **Current Status**: Verified. All version references consistent at 0.7.1.

## [2026-02-27] - Release 0.7.0: Context Engineering Skills, Template Rendering, Report Overhaul

*   **Goal**: Expand the skill library with context engineering capabilities, modernize the installer with template rendering, and harden the report generator.
*   **What Changed**:
    *   **Context Engineering Skills**: Adapted 5 skills from Agent-Skills-for-Context-Engineering (MIT): `context-degradation`, `context-compression`, `tool-design`, `filesystem-context-patterns`, `ai-output-evaluation`. Added 3 developer experience skills: `writing-editing`, `analysis-logic`, `creative-generation`. Skills total now 75.
    *   **Template Rendering System**: Created `base-claude.md` and `base-gemini.md` with `{{PLACEHOLDER}}` substitution. Installer now runs `Render-Template` instead of copying static instruction files, auto-detecting project language, package manager, build tool, and test framework.
    *   **Coding Snippets**: New `templates/ai-instructions/coding-snippets/` directory with per-language convention files for Copilot instruction assembly. Deprecated monolithic language templates to `templates/ai-instructions/legacy/`.
    *   **Skill Upgrades**: Upgraded `context-manager`, `task-coordinator`, `plan-before-code` to v1.1.0 with context fundamentals, multi-agent coordination patterns, and LLM task suitability assessment.
    *   **Report Generator Overhaul**: Added GFM table parsing, horizontal rule handling, Mermaid code block placeholders, `_strip_first_h1()` for title page, PRE-TOC marker support. Renamed command from `generate-word-report` to `generate-report` with 6-step synthesis-first workflow.
    *   **Generate Report Style Guide**: New `catalog/commands/generate-report-style-guide.md` command for report quality metrics.
    *   **Template Fixes**: Fixed tab-corrupted paths and em-dash encoding across 7 language templates.
    *   **Version Bump**: Updated `templates.json`, `scripts/installer.ps1`, `scripts/installer.sh`, `infrastructure/hooks/README.md` from 0.6.3 to 0.7.0. Installers bumped from V8 to V9.
*   **Current Status**: Verified. All version references consistent at 0.7.0.

## [2026-02-20] - Release 0.6.3: Word/PowerPoint Report Generation, Template System

*   **Goal**: Enable users to generate professional Word and PowerPoint documents from Markdown analysis files via a single command, with custom template support.
*   **What Changed**:
    *   **Generate Word Report Command**: Created `catalog/commands/generate-word-report.md` (183 lines, 6-phase workflow) that reads Markdown files, discovers templates from project and global directories, analyzes content structure, and produces formatted .docx or .pptx output.
    *   **Report Generator Extension**: Extended `scripts/generate_report.py` with `--type generic-word` and `--type generic-pptx`. Added ~550 lines covering Markdown-to-DOCX conversion (title page, TOC, headers/footers, page numbers) and Markdown-to-PPTX conversion (slide structure parser, section dividers, content slides, code block text boxes). Fixed existing bug in `add_markdown_paragraph()` where empty code block lines caused IndexError.
    *   **python-pptx Integration**: Added optional `python-pptx` dependency. PowerPoint generation maps H1 headings to section divider slides, H2 headings to content slides with body text frames, code blocks to monospace text boxes with gray backgrounds, and bullet points to structured slide content.
    *   **Installer Phase 4**: Added `Install-Templates` (PS1) and `install_templates` (Bash) as Phase 4 to both installers. Copies bundled templates and `generate_report.py` to `~/.devai-hub/`. PowerShell version uses `System.Windows.Forms.OpenFileDialog` for native multi-file template import. Bash version supports drag-and-drop file paths.
    *   **Template System**: Dual-layer discovery (project `.claude/templates/documentation/` overrides global `~/.devai-hub/templates/documentation/`). Bundled `generic-word-report-template.docx` as default.
    *   **Version Bump**: Updated `templates.json`, `scripts/installer.ps1`, `scripts/installer.sh`, `scripts/generate_report.py` from 0.6.2 to 0.6.3. Installers bumped from V7 to V8. Registered `generate-word-report` in `skills.json` (66 skills total).
*   **Current Status**: Verified. Word and PowerPoint generation tested with single and multiple Markdown files, with and without templates. Backward compatibility confirmed for existing codebase/code-review report types.

## [2026-02-19] - Release 0.6.2: CLI Usage Display, Command Overhaul, Changelog Generator

*   **Goal**: Add automatic CLI usage limits display, overhaul the command catalog for better separation of concerns, and add a changelog generation command.
*   **What Changed**:
    *   **Usage Display Hook**: Created `catalog/hooks/usage-display.sh` (Stop hook) that auto-fetches from the Anthropic OAuth API with 5-minute caching. Updated `catalog/hooks/settings.json`, both installers (`Install-UsageDisplay` / `install_usage_display`), and `infrastructure/hooks/README.md`.
    *   **Command Catalog Overhaul**:
        *   Added `generate-changelog.md` for full CHANGELOG.md reconstruction from git history.
        *   Replaced `run-code-review.md` with `review-codebase.md` (expanded to 596-line senior-level review).
        *   Rewritten `update-documentation.md` to focus on READMEs/guides only (excludes CHANGELOG/DEVLOG, defers to dedicated commands).
        *   Enhanced `update-version.md` (renamed from `updated-version`) with Keep a Changelog formatting, richer DEVLOG entries, and documentation update step (14 steps).
        *   Rewritten `analyze-codebase.md` with 12-section structured analysis and Mermaid diagrams.
        *   Enhanced `check-usage.md` with auto-fetch Phase 0 and cross-references.
    *   **Documentation**: Restructured root README usage monitoring section. Added cross-references across CLI hook, VS Code extension, and `/check-usage` command.
    *   **Version Bump**: Updated `templates.json`, `scripts/installer.ps1`, `scripts/installer.sh` from 0.6.1 to 0.6.2. Installers bumped from V6 to V7.
*   **Current Status**: Verified. All version references consistent at 0.6.2.

## [2026-02-19] - CLI Usage Limits Display (Stop Hook)

*   **Goal**: Address user feedback requesting token limit visibility in the CLI. Users could see tokens consumed but had to navigate to `claude.ai/settings/usage` to see how close they were to their cap.
*   **What Changed**:
    *   **Usage Display Hook**: Created `catalog/hooks/usage-display.sh` (Stop hook, 213 lines) that fetches from the Anthropic OAuth API, caches responses for 5 minutes, and displays a compact color-coded summary to stderr when any metric exceeds 50%. Includes graceful degradation (silent exit) for missing curl/jq, missing credentials, expired tokens, and network errors.
    *   **Hook Config**: Updated `catalog/hooks/settings.json` with Stop hook entry alongside existing PreToolUse.
    *   **Installer Integration**: Added `install_usage_display` (Bash) and `Install-UsageDisplay` (PowerShell) functions to both installers. Installed in both global (Phase 1) and workspace (Phase 2) with idempotent settings.json merge.
    *   **Check-Usage Enhancement**: Added Phase 0 auto-fetch to `catalog/commands/check-usage.md`. The command now reads OAuth credentials and calls the API directly via curl before falling back to manual entry.
    *   **Documentation**: Added "Usage Display (Stop Hook)" section to `infrastructure/hooks/README.md` with configuration, customization, and cross-references to the VS Code extension and `/check-usage` command.
*   **Design Decisions**:
    *   50% smart threshold (silent when healthy, visible when it matters)
    *   5-minute cache TTL to prevent API spam
    *   3-second curl timeout to never block the CLI
    *   Reused the same Anthropic OAuth API endpoint as the VS Code extension (`usageFetcher.ts`)
*   **Current Status**: Implemented. Three complementary usage monitoring features now exist: automatic CLI hook (passive), VS Code extension (visual), and `/check-usage` command (on-demand).

## [2026-02-19] - Release 0.6.1: Git Guardrails, Tracer Bullets, Report Fixes

*   **Goal**: Add deterministic safety enforcement for AI agents running destructive git commands, plus workflow improvements and report generation fixes.
*   **What Changed**:
    *   **Git Guardrails Hook**: Created `catalog/hooks/git-guardrails.sh` (PreToolUse hook) that intercepts Bash commands, matches against 12 dangerous git patterns, and blocks with exit code 2. Includes `catalog/hooks/settings.json` template for Claude Code integration.
    *   **Installer Integration**: Added `Install-GitGuardrails` (PS1) and `install_git_guardrails` (Bash) functions. Both installers now install the hook in global (Phase 1) and workspace (Phase 2) with idempotent JSON merge into `.claude/settings.json`.
    *   **AI Instructions**: Added `### 7. Tracer Bullets` workflow directive and `## Git Safety` soft enforcement section to `generic-instructions.md`, `catalog/CLAUDE.md`, and root `CLAUDE.md`.
    *   **Hooks Documentation**: Added comprehensive "Git Guardrails (PreToolUse Hook)" section to `infrastructure/hooks/README.md` with customization guide and verification steps.
    *   **Report Generation**: Fixed dependency categorization and platform support merging in `scripts/generate_report.py` and `catalog/commands/analyze-codebase.md`.
    *   **Version Bump**: Updated `templates.json`, `scripts/installer.ps1`, `scripts/installer.sh` from 0.6.0 to 0.6.1.
*   **Current Status**: Verified. All version references consistent at 0.6.1.

## [2026-02-10 18:00] - Release 0.6.0: Claude Usage Monitor, Code Review Overhaul, Documentation Fixes

*   **Goal**: Release v0.6.0 encompassing the Claude Usage Monitor VS Code extension, merged code-review-expert methodology, skills registry validation, and comprehensive documentation consistency fixes.
*   **What Changed**:
    *   **Version Bump**: Updated `templates.json`, `scripts/installer.ps1`, `scripts/installer.sh` from 0.5.3 to 0.6.0. Installers renamed from V5 to V6.
    *   **CHANGELOG.md**: Converted `[Unreleased]` section to `[0.6.0] - 2026-02-10` with full Added/Changed entries. Added 0.6.0 row to Version History Summary table. Updated footer compare links.
    *   **Documentation Fixes** (22 issues resolved from `/update-documentation` audit):
        *   Root `README.md`: Removed Codex (OpenAI) references, fixed CLAUDE.md path, fixed Copilot path casing, added VS Code Extension section, updated skill count to 63.
        *   Extension `README.md`: Fully rewritten to match current functionality (5 commands, 4 settings, auto-fetch API, SVG tooltip, dashboard).
        *   `skills.json`: Fixed 34 stale paths, removed 15 deleted skills, added 30 new entries, validated all 65 entries against disk.
        *   `CHANGELOG.md`: Fixed 19 footer URLs (`yourusername` to `bdourthe`), added 4 missing version links.
*   **Lessons Learned**: Running `/update-documentation` before a version release is an effective way to catch stale references and path inconsistencies across the project.
*   **Current Status**: Verified. All version references consistent at 0.6.0.

## [2026-02-10 12:00] - Created Claude Usage Monitor VS Code Extension

*   **Goal**: Build a VS Code extension that monitors Claude Code API usage (session and weekly limits) with auto-fetching, a status bar indicator, rich tooltip, and a full dashboard panel.
*   **Attempted Solutions**:
    *   *Icon Font Generation (fantasticon)*:
        *   *Result*: Failed. fantasticon v4.x reported "No SVGs found" regardless of path format, even in a temp directory without spaces. Version self-reported as "0.0.0".
        *   *Analysis*: fantasticon's glob resolution is broken in v4.x on Windows.
        *   *Solution*: Bypassed fantasticon entirely. Wrote custom `scripts/generate-icon-font.js` using `svgpath` + `svg2ttf` + `ttf2woff2`. Key insight: SVG fonts have Y-axis going UP (opposite of regular SVGs), requiring `svgpath(path).scale(64, -64).translate(0, 1024)` for 16px to 1024 unitsPerEm conversion.
    *   *Tooltip Progress Bars (HTML divs)*:
        *   *Result*: Failed. VS Code MarkdownString tooltips do not render `background` CSS on content-less `<div>` elements. `<table>` width attributes are also ignored.
        *   *Analysis*: VS Code's tooltip renderer has a limited CSS subset. Properties like `background`, `color`, `opacity`, and `font-style` on arbitrary HTML elements are unreliable.
        *   *Solution*: Switched to SVG data URI images via `<img src="data:image/svg+xml,${encodeURIComponent(svg)}">`. This renders reliably when `isTrusted` and `supportHtml` are true.
    *   *Percentage Right-Alignment (HTML tables)*:
        *   *Result*: Failed. HTML `<table width="260">` was not respected by VS Code's tooltip. Percentages appeared next to labels instead of at the far right edge.
        *   *Solution*: Baked label, percentage, AND progress bar into a single SVG image using `text-anchor="end"` for guaranteed pixel-perfect right alignment.
    *   *PowerShell Installer Phase 3*:
        *   *Result*: Initially failed. `$ErrorActionPreference = "Stop"` converted npm/npx stderr output into terminating PowerShell exceptions.
        *   *Solution*: Wrap native CLI tool sections with `$ErrorActionPreference = "Continue"` and restore afterward. Use `2>$null | Out-Null` instead of `2>&1 | Out-Null` for stderr suppression.
*   **Changes**:
    *   Created `extensions/claude-usage-monitor/` (full extension, 22 files):
        *   `src/usageFetcher.ts`: Reads OAuth token from `~/.claude/.credentials.json`, calls `GET https://api.anthropic.com/api/oauth/usage` with `anthropic-beta: oauth-2025-04-20` header, maps response to internal types.
        *   `src/statusBarManager.ts`: Status bar with `$(claude-icon)` custom icon, `X% (current) Y% (week)` format, SVG data URI tooltip with theme-aware colors via `activeColorTheme.kind`, auto-refresh timer.
        *   `src/dashboardPanel.ts`: WebviewPanel with full usage breakdown, model recommendations, optimization tips, theme-aware tab icons via `{ light: Uri, dark: Uri }` iconPath.
        *   `src/extension.ts`: Orchestrates auto-fetch on activation, registers commands (`dashboard`, `refresh`, `update`, `reset`), configures auto-refresh interval.
        *   `src/inputCollector.ts`: Manual input fallback (4-step wizard) when API credentials are unavailable.
        *   `src/recommendations.ts`: Usage-based model switching recommendations (Opus/Sonnet/Haiku).
        *   `scripts/generate-icon-font.js`: Custom SVG-to-WOFF2 font generator.
        *   `icons/claude.svg`, `icons/claude-dark.svg`, `icons/claude-light.svg`: Theme-aware icon variants.
        *   `fonts/claude-icons.woff2`: Generated icon font at codepoint U+E101.
    *   Modified `scripts/installer.ps1`: Added Phase 3 (extension build, VSIX packaging, VS Code installation with Node.js detection).
    *   Modified `scripts/installer.sh`: Added Phase 3 (same logic for macOS/Linux with brew/apt detection).
    *   Created `catalog/commands/check-usage.md`: CLI command for checking usage from the terminal.
    *   Added `catalog/claude_icon.svg`, `catalog/claude_logo.png`: Icon assets.
    *   Modified `skills.json`: Registered `check-usage` command.
*   **Lessons Learned**:
    *   VS Code MarkdownString tooltips support `<img>` tags with `data:image/svg+xml` URIs but do NOT reliably support CSS `background`, `color`, `opacity`, or `font-style` on HTML elements. Tables render but ignore width attributes. The most reliable approach for custom graphics in tooltips is inline SVG data URIs.
    *   fantasticon v4.x is unusable on Windows. A custom script with `svgpath` + `svg2ttf` + `ttf2woff2` is more reliable and produces smaller output.
    *   PowerShell `$ErrorActionPreference = "Stop"` must be temporarily disabled when invoking npm, npx, node, or any native CLI tool that writes to stderr as part of normal operation.
    *   The Claude OAuth usage API lives at `https://api.anthropic.com/api/oauth/usage` (not `claude.ai`), requires the `anthropic-beta: oauth-2025-04-20` header, and returns `five_hour`, `seven_day`, `seven_day_sonnet`, `seven_day_opus`, and `extra_usage` fields each with `utilization` (0-100) and `resets_at` (ISO 8601).
*   **Current Status**: Verified. Extension builds, packages, installs, and runs correctly. Auto-fetch populates status bar on activation. Tooltip shows SVG progress bars with theme-aware colors. Dashboard opens with Claude icon on tab. Manual fallback works when credentials are missing.

## [2026-02-06 14:00] - Merged code-review-expert into run-code-review

*   **Goal**: Merge the methodology from `sanyuan0704/code-review-expert` (GitHub) into the existing `run-deep-review` command and rename to `run-code-review`, creating a unified, comprehensive code review system.
*   **What Changed**:
    *   **New Command**: Created `catalog/commands/run-code-review.md` replacing `run-deep-review.md`. Supports dual-mode (full codebase review and git-changes review), P0-P3 severity classification, review-first paradigm (no changes without user confirmation), and a structured next steps menu.
    *   **New Reference Checklists** (4 files under `catalog/skills/code-review/references/`):
        *   `solid-checklist.md`: SOLID diagnostic questions per principle, 12 code smells with thresholds, 7 refactor heuristics.
        *   `security-checklist.md`: 10-domain security model with diagnostic questions, including race conditions deep-dive (shared state, TOCTOU, DB concurrency, distributed systems).
        *   `code-quality-checklist.md`: Error handling anti-patterns, performance/caching analysis, boundary conditions (null, empty, numeric, string).
        *   `removal-plan.md`: Dead code removal templates (safe-delete-now vs defer-with-plan), 7-item pre-removal checklist.
    *   **Updated Skills** (all 6 SKILL.md files bumped to v2.0.0):
        *   `context-analysis`: Added dual-mode support, git-changes preflight, edge case handling (>500 lines batching), critical path identification.
        *   `code-quality`: Added SOLID analysis with diagnostic questions, dead code removal planning, expanded to 12 code smells, 7 refactor heuristics.
        *   `security-review`: Restructured to 10-domain model, added race conditions deep-dive (4 sub-categories), exploitability + impact assessment, expanded language-specific vulnerability lists (C#, Go).
        *   `performance-review`: Added caching strategy analysis (TTL, invalidation, stampede, key collisions), boundary conditions, 4 diagnostic questions.
        *   `testing-review`: Added P0-P3 severity classification, git-changes mode gap analysis.
        *   `final-report`: Added overall verdict (APPROVE/REQUEST_CHANGES/COMMENT), inline comment format, clean review protocol, next steps confirmation menu, review-first enforcement.
    *   **Deleted**: `catalog/commands/run-deep-review.md` (replaced by `run-code-review.md`).
*   **Key Design Decisions**:
    *   Unified severity on P0-P3 scale (with CRITICAL/HIGH/MEDIUM/LOW as aliases) for consistency across all phases.
    *   Adopted review-first paradigm from code-review-expert: findings are presented first, user must confirm before any changes are implemented.
    *   Integrated SOLID analysis and dead code removal into the existing code-quality phase (Phase 2) rather than adding new phases, keeping the 6-phase structure intact.
    *   Reference checklists are standalone files in `references/` to allow independent maintenance and reuse across skills.
*   **Current Status**: Complete. All files verified. No functional stale references (only historical mentions in DEVLOG.md and CHANGELOG.md).

## [2026-02-04 15:32] - Release 0.5.3: Documentation Fixes & Command Cleanup

*   **Goal**: Simplify the repository by removing deprecated legacy skill definitions, consolidating catalog commands, and fixing critical broken links.
*   **Attempted Solutions**:
    *   **Cleanup Legacy Skills**:
        *   *Action*: Removed `.codex`, `.gemini`, and `.github/copilot-instructions.md` directories containing outdated definitions.
        *   *Result*: Success. Codebase is significantly cleaner.
    *   **Consolidate Commands**:
        *   *Action*: Consolidated `generate-commit-message`. Removed redundant `create-commit-message`, `generate-codebase-report`, `upgrade-version`.
        *   *Result*: Success. Reduced maintenance overhead.
    *   **Installer Logic**:
        *   *Action*: Updated `scripts/installer.ps1` to ensure `$globalAntigravityWorkflows` directory is explicitly created before copying.
        *   *Result*: Verified.
*   **Changes**:
    *   Modified `scripts/installer.ps1`: Enhanced global workflow directory handling.
    *   Modified `scripts/generate_report.py`: Refined report generation logic.
    *   Deleted `.codex/`, `.gemini/`, `.github/copilot-instructions.md`: Removed legacy artifacts.
*   **Lessons Learned**: Always verify destination directory existence in PowerShell before copy operations to prevent runtime errors.
*   **Current Status**: Verified.

## [2026-01-30 16:55] - Release 0.5.2: Enhanced Reporting & Upgrade Automation

*   **Goal**: Improve the codebase reporting capabilities with professional DOCX output and streamline the version upgrade process.
*   **Implementation**:
    *   **Reporting**: Updated `scripts/generate_report.py` to support `python-docx`, automatic TOC updates via Word Interop, and better metadata handling.
    *   **Upgrade Automation**: Enhanced the `/upgrade-version` workflow to perform auto-analysis of git changes, generate context-aware commit messages, and validate version consistency.
    *   **Documentation**: Added a dedicated Claude Skills section to `README.md` and standardized Python template formatting.
*   **Result**: Users can now generate professional-grade codebase reports and manage project versions with significantly less manual effort.

## [2026-01-28 22:15] - Release 0.5.1: Cross-Platform Support

*   **Goal**: Extend the DevAI-Hub installer to support macOS and Linux operating systems.
*   **Implementation**:
    *   **Bash Installer**: Ported the logic from `installer.ps1` to `scripts/installer.sh` using Bash.
    *   **Features Preserved**: Replicated global installation, workspace selection, language detection, and safe overwrite prompts.
    *   **Entry Point**: Created a root-level `install.sh` script for easy execution.
*   **Documentation**: Updated `README.md` to guide non-Windows users.
*   **Result**: The repo now supports Windows, macOS, and Linux with a unified installation experience.

## [2026-01-28 21:35] - Release 0.5.0: Universal Catalog & Installer V5 Refactor

*   **Goal**: Refactor the entire repository to a "Universal Catalog" model to remove duplication between Claude/Gemini and various languages, and build a robust, user-friendly installer.
*   **Challenges & Solutions**:
    *   1.  **Duplicate Templates**: Previous versions had `templates/ai-instructions/claude-code/{lang}` which duplicated content.
        *   *Solution*: Created `catalog/` with `skills`, `commands`, `context`, `memory`. Moved all assets there. Deleted legacy folders.
    *   2.  **Installer Instability**: The minimal `Install-Global` logic was missing providers and crashed due to syntax errors during refactoring.
        *   *Error*: `Unexpected token '}'` in `installer.ps1`.
        *   *Fix*: Restored the deleted function definitions (`Detect-Languages`, etc.) and fixed the brace mismatch.
    *   3.  **Inconsistent Logging**: User reported "Global" phase didn't show details like "Workspace" phase.
        *   *Fix*: Updated `Safe-Copy` to support `CustomMessage`. Added explicit "Global instructions installed at..." logs.
    *   4.  **Overwrite Fatigue**: Users had to press 'Y' for every file.
        *   *Fix*: Added `[A]ll` option to overwrite prompts, setting a global `$script:OverwriteAll` flag.
*   **New Capabilities**:
    *   **Universal Commands**: Created `generate-tests`, `run-deep-review` (renamed from `test`/`review`), `generate-sbom`, `update-devlog`, `create-skill-or-command`.
    *   **Smart Installer**: `installer.ps1` now handles global *and* local config with identical logic.
*   **Current Status**: Verified. Installer V5 is stable. Catalog is live.
