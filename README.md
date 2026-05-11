# DevAI Hub
**Brain Upgrades for Your AI Agents**

*A cross-platform layer of prompt, context, and harness engineering. Skills, commands, hooks, and rules that work the same across Claude Code, Codex, Gemini, Cursor, and GitHub Copilot.*

> **Turn any AI agent into a senior engineer.**
> One-click setup. Local-first by default. No data leaves your machine.

---

## What's New in v1.2.0

**Adoption of `anthropics/skills` patterns -- 9 new skills, 4 new repo-level scripts, A13 per-skill bundled-resources layout, A16 `.skill` packager.** MINOR release closing the seven-phase v1.1.5 `adoption-skills` plan ([docs/v1.1.5/plans/adoption-skills.md](docs/v1.1.5/plans/adoption-skills.md)). Strictly additive: zero breaking changes, no removals, no schema changes. Catalog grows from 187 -> 196 user-facing skills. Restart your AI agent sessions after re-installing so the new skills and commands become callable.

### 9 new skills

- **`doc-coauthoring`** (workflow) -- 3-stage co-authoring workflow (Context Gathering -> Refinement and Structure -> Reader Testing) for specs, proposals, decision docs, RFCs, ADRs, and long-form internal writeups.
- **`generative-art`** (specialized-domains) -- algorithmic / generative-art workflow: write a Markdown philosophy manifesto, then ship a p5.js sketch with `randomSeed()` and an HTML viewer with parameter sliders. Three starter templates bundled (flow-field, particle-system, l-system).
- **`theme-tokens`** (specialized-domains) -- stable design-token schema (palette, fonts, spacing, radius, shadow) plus 10 brand-neutral curated theme JSONs consumable by the four document-generator skills.
- **`internal-comms`** (business-product) -- six structured templates for internal-audience writing (3P Update, Weekly Status, Leadership Update, Company FAQ, Incident Report, Project Update) with worked placeholder examples.
- **`web-artifacts-builder`** (developer-experience) -- multi-component HTML artifact scaffolder using Vite + React + TypeScript + Tailwind v4 + shadcn/ui. Cross-platform `init-artifact.sh` + `init-artifact.ps1` parallel scripts.
- **`skill-eval-loop`** (workflow) -- closed-loop evaluation workflow against any DevAI-Hub skill (paired with-skill / without-skill runs, assertion-graded outputs, browser-reviewed benchmarks, five named improvement heuristics).
- **`brand-styling`** (specialized-domains) -- token-pattern skill that applies user-supplied brand tokens (palette, typography, logo, voice) to generated artifacts via per-brand `~/.devai-hub/brand/<slug>/tokens.json`. Ships empty placeholders only -- the user MUST supply their own brand.
- **`mcp-builder`** (ai-development) -- walks the agent through building a local MCP server in Python (FastMCP) or Node / TypeScript (the official MCP SDK), with bundled cross-platform scaffolders and reference docs. Enforces the AGENTS.md MCP Registry Policy decision tree before scaffolding.

### 4 new repo-level scripts

- **`scripts/aggregate_benchmark.py`** -- post-processes paired eval runs into `benchmark.json` + `benchmark.md`.
- **`scripts/skill_eval_viewer.py`** -- browser-based eval viewer with server and `--static` modes (for headless CI environments).
- **`scripts/optimize_skill_description.py`** -- description optimizer with 60/40 train-test split and held-out-test selection that prevents overfitting. CLI-agnostic across claude / gemini / codex / opencode (parity invariant enforced by pytest).
- **`scripts/package_skill.py`** -- packages a catalog skill into a portable `.skill` ZIP archive for upload to Claude.ai or the Anthropic API skill-upload endpoint.

All four scripts are registered in BOTH `scripts/installer.sh` and `scripts/installer.ps1` per the AGENTS.md "Installer-Aware Changes" rule.

### A13 per-skill bundled-resources layout

Skill folders MAY now ship `scripts/`, `references/`, `assets/` subdirectories alongside SKILL.md. The recursive-copy installer primitives auto-distribute them; a new `--bundles-only` audit in `scripts/validate_skills.py` flags any bundled file the parent SKILL.md never references. Documented in AGENTS.md; smoke-tested through both installer copy primitives on Windows.

### Five doc-only edits institutionalizing upstream skill-authoring patterns

A14 pushy descriptions (lists trigger phrases AND skip phrases verbatim), A17 three-tier loading model (tier 1 metadata always loaded, tier 2 SKILL.md body on trigger, tier 3 bundled resources on demand -- scripts execute without their source being loaded into context), A15 500-line SKILL.md target with 800-line soft cap, A11 aesthetic-distinctiveness lens in `frontend-ui-engineering`, A12 static-poster workflow in `creative-generation`.

### Migration

Re-run the installer. Skills, scripts, and instruction-template `{{SKILL_INDEX}}` blocks all update automatically. Settings.json / AGENTS.md / .cursor/rules/ are read at session start, not hot-reloaded -- restart any already-running Claude Code / Cursor / Gemini / Codex / OpenCode sessions for the new skills and commands to take effect.

See [CHANGELOG.md](CHANGELOG.md) for the full v1.2.0 entry (Added / Changed / Removed / Verified / Tests / Known gaps subsections) and [docs/v1.0.0/RELEASE_NOTES.md](docs/v1.0.0/RELEASE_NOTES.md) for the v1.0.0 baseline.

---

## 🚀 Quick Start (The 30-Second Setup)

Don't want to copy-paste files manually? We made an installer.

1.  **Clone or Download** this repository.
2.  **Run the installer**:
    *   **Windows**: Double-click **`install.bat`**.
    *   **macOS / Linux**: Run `./install.sh` in your terminal.
3.  **Drag and drop** your target project folder when asked.
4.  **Confirm** to install global skills.
5.  **(Optional) Select a project** to configure workspace-specific rules.

**Done.**
*   **Globally**: Your user profile now has all 196 Claude Skills, 34 Commands, 13 Hooks, 10 Agents, plus Gemini and Codex instructions.
*   **Locally**: Your project has `copilot-instructions.md` tailored to your language.

---

## 📖 What is this?
Most AI assistants (Claude, Copilot, ChatGPT) are "generic junkies", they know everything but master nothing. They write okay code, but often forget edge cases, security, or your specific style.

**DevAI Hub** is a collection of **"System Instructions"** and **"Skills"** that you inject into your AI to make it smarter.

### It gives your AI:
1.  **Behavioral Rules**: "Don't just fix the error, explain *why* it happened and check for security risks."
2.  **Autonomous Skills**: "Run a research task on Reddit to find the best library for this feature, then implement it."
3.  **Workflow Awareness**: "When I ask for a 'Code Review', follow this exact 6-step checklist."

---

## 🎯 Recommended Workflows

DevAI-Hub provides two opinionated end-to-end workflows. Use these as a starting point and adapt to your project.

### New Project Workflow (5 phases)

Build from scratch with an AI coding agent as your primary partner.

#### 1. Planning

Open an AI chatbot (Claude.ai or ChatGPT) and brainstorm: problem, users, core features, tech stack, constraints. End the session by asking the chatbot to produce a structured Markdown implementation plan - phases with subtasks, each subtask carrying a self-contained prompt the agent can execute.

#### 2. Project Setup

1. Create the Git repo with a three-tier branching model: `main` / `develop` / `feature/*`.

2. Install the DevAI-Hub toolkit: `./install.sh` (macOS / Linux) or `install.bat` (Windows).

3. In Claude Code, run `/setup-project` - bootstraps `CLAUDE.md`, the directory structure, `.gitignore`, `README.md`, `DEVLOG.md`, and `CHANGELOG.md` in 8 guided phases.

4. Save the implementation plan from step 1 to `docs/<version>/plans/<slug>.md`.

5. Commit with `/generate-commit-message`.

#### 3. Development (Core Loop)

For each plan phase:

1. Create a feature branch: `feature/phase-N-short-description`.

2. Open a fresh Claude Code session.

3. Run `/implement-phase <slug> <phase>` - walks every subtask, generates and runs tests, applies fixes, runs `/update-gitignore` + `/update-documentation`, generates a session-history file, and produces a commit message.

4. Commit and push the feature branch.

5. Merge into `develop`. Repeat for the next phase.

#### 4. Quality Assurance (pre-release)

1. Run `/run-deep-review` - a 12-phase orchestrator that chains known-gaps collection, health gates, dependency scan, docs / git hygiene, project validators, `/analyze-codebase`, `/run-security-audit`, `/run-penetration-test --depth=deep`, and `/review-codebase`.

2. Read the synthesis report - it produces a P0 / P1 / P2 / P3 ranked list of findings with a GO / GO-WITH-CONDITIONS / NO-GO verdict.

3. Address all P0 and P1 findings before release. P2 findings can be deferred to a follow-up patch release; P3 findings are advisory.

4. Run `/generate-sbom` for compliance documentation.

#### 5. Release

1. Run `/update-version` - orchestrates version detection, layout cleanup, `.gitignore` audit, version-bump across all configuration files, CHANGELOG migration, doc sync, and DEVLOG entry.

2. Merge `develop` into `main`, tag the release, and push.

### Inherited Project Workflow (2 phases)

For projects you've inherited or need to audit.

#### 1. Primary Analysis & Deep Review

1. Clone the repo, open it in VS Code, start a Claude Code session.

2. Run `/run-deep-review` - the same 12-phase orchestrator from Phase 4 of the New Project Workflow. The synthesis report's prioritized roadmap (P0 / P1 / P2 / P3) becomes your initial backlog.

3. If documentation is sparse, backfill it: `/generate-readme` (if missing), `/generate-changelog` (from git history), `/generate-devlog`, `/refactor-project-layout` (only when the repo has structural issues).

4. Establish the `develop` branch if not already present.

5. Commit the analysis artifacts.

#### 2. Making Changes

For each change:

1. Brainstorm in a chatbot, then run `/generate-plan` to produce a structured implementation plan saved to `docs/<version>/plans/<slug>.md`.

2. Run `/implement-phase <slug> <phase>` per phase - identical to the New Project Workflow's development loop.

3. (Optional) Use git worktrees for parallel work (e.g. critical security fix while developing a feature):

    ```bash
    git worktree add ../project-fix feature/security-fix
    # Work in a separate Claude Code session, then:
    git worktree remove ../project-fix
    ```

4. After all changes land on `develop`, run `/run-deep-review` again to verify nothing regressed, then `/update-version` and merge to `main`.

The QA and release steps are identical to the New Project Workflow.

---

## 🧩 How to Use (Manual Method)

If you prefer to copy things yourself, here is how the repo is organized:

### 1. Claude Code (Anthropic)

This is the most powerful integration. It adds **autonomous agent capabilities**.

- **CLAUDE.md**: The "Brain". Copy `catalog/CLAUDE.md` to your project root and customize it.
- **Skills**: The "Hands". Copy folders from `catalog/skills/` to your project's `.claude/skills/` folder.

    *Example*: Copy `catalog/skills/research/trend-research` to enable the "Trend Research" skill.

### 2. Gemini (Google) and Antigravity

Optimized instructions for Google's Gemini models, including the Antigravity workspace layout.

- **Gemini Instructions**: Copy `templates/ai-instructions/base-gemini.md` (or `templates/ai-instructions/generic-instructions.md` for the legacy template) to `.gemini/GEMINI.md` in your project or user profile.
- **Skills & Workflows**: The installer mirrors these to `.gemini/skills/` and `.gemini/antigravity/global_workflows/` so they appear globally in Antigravity.

### 3. GitHub Copilot (Microsoft)

Instructions for VS Code's Copilot Chat.

- Copy `templates/ai-instructions/coding-instructions/{language}.md` to `.github/copilot-instructions.md`.

### 4. Codex (OpenAI)

OpenAI Codex CLI integration. Codex reads `AGENTS.md` at the project root (the open standard, also honored by Cursor / Aider / Jules) plus its user-level config in `~/.codex/`.

- **AGENTS.md**: Copy `templates/ai-instructions/base-codex.md` content into your project's `AGENTS.md`.
- **Skills & Prompts**: The installer mirrors `catalog/skills/` to `~/.codex/skills/` and `catalog/commands/` to `~/.codex/prompts/`. For manual setup, copy each tree to those destinations.

### 5. Cursor

Cursor IDE integration.

- **Project rules**: Copy `templates/ai-instructions/base-cursor.md` content into `.cursor/rules/devai-hub.mdc` at your project root. Use `alwaysApply: true` in the frontmatter so Cursor applies the rule on every prompt.
- **Open-standard `AGENTS.md`**: Cursor also reads `AGENTS.md` at the project root, so the Codex setup above covers Cursor too.

### 6. OpenCode

OpenCode IDE integration. OpenCode reads `AGENTS.md` per the open standard.

- Copy `templates/ai-instructions/base-opencode.md` content into your project's `AGENTS.md`.

---

## 🧠 Featured Skills

| Skill | What it does |
|-------|--------------|
| **Architecture Design** | System decomposition, ADRs, C4 diagrams, and fitness functions. |
| **AI Agent Development** | Build agents with tool use, memory systems, and multi-agent orchestration. |
| **RAG Implementation** | End-to-end RAG pipelines with chunking, embeddings, and evaluation. |
| **API Design** | REST, GraphQL, and gRPC design with versioning and error handling. |
| **Code Review** | A 6-step deep dive (Security, Perf, Logic) before you merge. |
| **Test Gen** | Writes comprehensive unit tests using AAA pattern and mocks. |
| **E2E Testing** | Playwright/Cypress automation with page objects and CI integration. |
| **Compliance** | Checks code against SOC2, GDPR, and ISO standards. |
| **Trend Research** | Researches Reddit/X for the last 30 days to find trends & write prompts. |

[→ View Full Skills Catalog](catalog/skills/README.md)

---

## 🔌 Usage Monitoring

Three complementary ways to track your Claude Code usage limits:

### CLI Usage Display (Automatic)
A Stop hook that shows your usage limits directly in the terminal after each Claude Code response. Color-coded and silent when usage is healthy (below 50%).

```
Usage: Session 72% | Weekly 15% | Sonnet 3%  (Session resets in 28m)
```

Installed automatically by the DevAI-Hub installer. Requires `curl` and `jq`.

### VS Code Extension
Monitor usage from the VS Code status bar with a full dashboard.

*   **Auto-fetch**: Reads your OAuth token and fetches live usage data from the Anthropic API.
*   **Status bar**: Shows session and weekly usage percentages with a custom Claude icon.
*   **SVG tooltip**: Hover for theme-aware progress bars with per-metric breakdown and reset timers.
*   **Dashboard**: Click for a full usage dashboard with model recommendations and optimization tips.

See [extensions/claude-usage-monitor/](extensions/claude-usage-monitor/) for setup instructions.

### `/check-usage` Command
On-demand detailed usage report with model-switching recommendations. Auto-fetches from the API (falls back to manual entry if credentials are unavailable).

---

## 🔒 Safety and Use in Regulated Industries

DevAI-Hub is built on a **reverse-engineering-first** principle: the catalog ships zero third-party data processors, zero outbound calls from skills / commands / hooks, and zero telemetry. The full threat-model breakdown, industry compatibility matrix, and reporting policy is in [SECURITY.md](SECURITY.md).

Short version:

- **Open-source / hobby / internal commercial software**: green. No restrictions.
- **Regulated industries (healthcare, finance, government, life sciences, automotive, industrial)**: green WITH caveats. DevAI-Hub itself is safe; the caveat is that your chosen LLM provider is where prompts go (use a regulated-cloud option like AWS Bedrock, GCP Vertex AI, Azure OpenAI, or a self-hosted model consistent with your data-protection obligations).
- **Defense / classified / air-gapped**: outside DevAI-Hub's threat model. Do your own assessment.

What DevAI-Hub does NOT do: telemetry, analytics, phone-home, third-party data processors, model downloads, API-key requirements. The MCP Registry Policy in [AGENTS.md](AGENTS.md) categorically rejects search-as-service, embeddings-as-service, scraping-as-service, and generation-as-service. The authoritative classification of every MCP server ever shipped or considered is at [docs/v1.0.0/mcp-reverse-engineering-matrix.md](docs/v1.0.0/mcp-reverse-engineering-matrix.md).

What is OUT of DevAI-Hub's control: your chosen LLM provider, any MCP server you add outside the DevAI-Hub registry, user-initiated outbound calls (`gh`, `git push`, `curl`), and your own user-authored hooks and rules. See [SECURITY.md](SECURITY.md) section 3 for the full caveats.

To report a security issue: email [benjamin.dourthe@gmail.com](mailto:benjamin.dourthe@gmail.com) or open a private security advisory at [github.com/bendourthe/DevAI-Hub/security](https://github.com/bendourthe/DevAI-Hub/security).

---

## 🤝 Collaboration

DevAI-Hub is a curated open-source project. While Pull Requests (PRs) are typically not accepted from outside contributors, suggestions, feedback and recommendations are more than welcomed. If you have a better prompt, a smarter rule, or a pattern you'd like to see in the catalog, please reach out directly:

- **Email**: [benjamin.dourthe@gmail.com](mailto:benjamin.dourthe@gmail.com)
- **GitHub**: [@bendourthe](https://github.com/bendourthe)

I'm happy to discuss skill / command / hook proposals, integration ideas for new platforms, or specific use cases - especially when the proposal aligns with the policy direction of this project (reverse-engineering-first, no third-party data leaks).
