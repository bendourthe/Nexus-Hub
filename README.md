# DevAI Hub
**Brain Upgrades for Your AI Agents**

*A cross-platform layer of prompt, context, and harness engineering. Skills, commands, hooks, and rules that work the same across Claude Code, Codex, Gemini, Cursor, and GitHub Copilot.*

> **Turn any AI agent into a senior engineer.**
> One-click setup. Local-first by default. No data leaves your machine.

---

## What's New in v1.3.0

**Docs folder cleanup workflow.** MINOR release that introduces a structured way to audit and reorganize a project's `docs/` folder. Every file gets classified into one of four explicit categories (Cat 1 delete / Cat 2 archive / Cat 3 stale-flag / Cat 4 active), the agent proposes a version-first reorganization with a dedicated `docs/archive/` subtree, and changes only apply after explicit user confirmation. The workflow is wired into the existing release commands so docs hygiene happens routinely rather than only at major releases.

### What changed

- **New skill `docs-layout-refactor` and command `/refactor-docs`**: audit-then-confirm-then-apply workflow with eight weighted heuristics for file classification, plus a stdlib-only Python helper ([`audit-docs.py`](catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py)) that emits a JSON inventory and reference graph without inflating the agent's context window. Default is propose-only; the `--apply` flag turns on the confirmation gate.
- **New PreToolUse hook [`old-version-docs-guard`](catalog/hooks/old-version-docs-guard.sh)**: warns when Write or Edit targets a historical `docs/v<old-version>/` path. Non-blocking by default; opt-in hard block via `DEVAI_OLD_DOCS_GUARD=block`. Ships with a PowerShell sibling for Windows parity.
- **New `release-prep` bundle**: groups `docs-layout-refactor`, `project-layout-refactor`, `documentation-consistency`, `version-upgrade`, `release-notes-writer`, `known-gaps-tracker`, and `code-commit-workflow` for one-click release-prep skill installation.
- **Integrations into existing commands**: `/wrap-up-session` Step 2c (audit-only), `/update-version` Step B4 (full apply with gate), `/run-deep-review` subsection 4.11 (audit-only), `/review-codebase` Phase 6f (advisory reference). The `--migrate-known-gaps` flag on `/refactor-docs` auto-promotes Cat 3 findings into `docs/<next-version>/known-gaps.md` via the `known-gaps-tracker` skill.

### Migration

Re-run the installer. The new skill, command, hook, and bundle land at their target paths automatically (the skill bundle is recursively copied; the hook is registered in `catalog/hooks/settings.json` under `PreToolUse` for Write and Edit). No schema change, no installer-flow change. **No breaking changes**: existing user customizations are preserved.

See [CHANGELOG.md](CHANGELOG.md) for the full entry and [docs/v1.3.0/RELEASE_NOTES.md](docs/v1.3.0/RELEASE_NOTES.md) for the release summary.

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
*   **Globally**: Your user profile now has all 203 Claude Skills, 35 Commands, 14 Hooks, 10 Agents, plus Gemini and Codex instructions.
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

## 🗺️ Roadmap

DevAI-Hub evolves in versioned slices. Each upcoming line item below traces to a concrete plan file under `docs/<version>/plans/` (the durable source) and resolves once its `[<version>]` block lands in [CHANGELOG.md](CHANGELOG.md). No star gates, no sponsor tiers, no paid features - the catalog is reverse-engineering-first and stays that way.

| Focus | Target | Status | Source |
|-------|--------|--------|--------|
| Engineering document-template skills (incident postmortems, runbooks, on-call runbooks, PR descriptions, ADRs, test strategies) | v1.4.0 | Shipped | [docs/v1.3.0/plans/adoption-pm-claude-skills.md](docs/v1.3.0/plans/adoption-pm-claude-skills.md) |
| Engineering bundles (`incident-response`, `pr-workflow`, `architecture-docs`) grouping new + existing skills for one-click install | v1.4.0 | Shipped | [docs/v1.3.0/plans/adoption-pm-claude-skills.md](docs/v1.3.0/plans/adoption-pm-claude-skills.md) Phase 4 |
| Cross-OS CI matrix for installer smoke tests (closes the cumulative DF-003 / DF-005 / DF-006 / DF-007 / DF-008 cluster from v1.1.5 known-gaps) | v1.5.0 | Planned | [docs/v1.1.5/](docs/v1.1.5/) known-gaps cluster |
| Skill-eval-loop integration into pre-commit (assertion-graded regression guard for high-traffic skills before they ship) | v1.5.0 | Planned | [catalog/skills/workflow/skill-eval-loop/SKILL.md](catalog/skills/workflow/skill-eval-loop/SKILL.md) |
| MCP registry expansion under the existing 5-step policy (reverse-engineer-first; hard-no on search / embeddings / scraping / generation as a service) | continuous | In progress | [docs/v1.0.0/mcp-reverse-engineering-matrix.md](docs/v1.0.0/mcp-reverse-engineering-matrix.md) |

For narrative-style updates on what changed and why, see [docs/DEVLOG.md](docs/DEVLOG.md). For the formal Keep-a-Changelog log of every release, see [CHANGELOG.md](CHANGELOG.md). For the per-version unfinished-work tracker that the next plan reads to decide what carries forward, see `docs/<version>/known-gaps.md`.

---

## 🤝 Collaboration

DevAI-Hub is a curated open-source project. While Pull Requests (PRs) are typically not accepted from outside contributors, suggestions, feedback and recommendations are more than welcomed. If you have a better prompt, a smarter rule, or a pattern you'd like to see in the catalog, please reach out directly:

- **Email**: [benjamin.dourthe@gmail.com](mailto:benjamin.dourthe@gmail.com)
- **GitHub**: [@bendourthe](https://github.com/bendourthe)

I'm happy to discuss skill / command / hook proposals, integration ideas for new platforms, or specific use cases - especially when the proposal aligns with the policy direction of this project (reverse-engineering-first, no third-party data leaks).
