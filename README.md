# DevAI Hub
**Production-Grade Brain Upgrades for Your AI Coding Assistant**

> **Turn generic AI into a Senior Engineer.**
> One-click setup for Claude Code (Anthropic), Gemini (Google), GitHub Copilot (Microsoft), and Codex (OpenAI).

---

## What's New in v1.0.0

**First stable release.** Reverse-engineering-first security hardening - DevAI-Hub is now safe for use in regulated environments where proprietary source code, prompts, and query text must not leak to third-party data processors. Major-version cut from 0.9.7 (skipping 0.9.8) reflects the breadth of policy-level changes.

### 🛡️ Enhanced Security

- **MCP Registry Policy with reverse-engineering-first decision tree** ([AGENTS.md](AGENTS.md) + 7 platform-surface inlines). Every MCP entry now answers a 5-question audit (who runs the process, outbound calls, API keys, data transmitted, vendor relationship) in its `_comment`. Hard-no list: search-as-service, embeddings-as-service, scraping-as-service, generation-as-service.

- **Reverse-Engineering Matrix** ([docs/v1.0.0/mcp-reverse-engineering-matrix.md](docs/v1.0.0/mcp-reverse-engineering-matrix.md)) - authoritative classification of every MCP shipped or considered (18 rows). Drives keep / strip / rebuild decisions.

- **Pre-release security review** found 3 HIGH and 1 MEDIUM-severity findings - all fixed with regression tests before tag. See [docs/security/penetration-test-2026-04-27.md](docs/security/penetration-test-2026-04-27.md) for the full assessment.

- **Pickle deserialization eliminated.** `devai-code-search` now persists indexes as JSON. A maliciously-crafted index file cannot execute code at load time.

- **SSRF defense in depth** in `devai-web-fetch`: per-hop validation on every redirect target, DNS pinning to prevent rebinding, RFC 1918 / loopback / link-local blocked by default.

- **Symlink-safe codebase walker** in `devai-code-search`: indexing an untrusted repository cannot leak files outside the indexed root through symlink-following.

### 🧰 New Internal MCP Servers

Zero outbound calls, zero API keys, zero model downloads. Both ship with the installer.

- [`devai-code-search`](extensions/devai-code-search/) - local-only code search. Keyword retrieval (inverted index + rapidfuzz), content-hash incremental indexing, `.gitignore` + `.devaiignore` respect, symlink-safe walker. Dense / hybrid retrieval planned for v1.1.0.

- [`devai-web-fetch`](extensions/devai-web-fetch/) - local-only HTTP fetch + readability extraction. Per-hop SSRF guard, DNS pinning, manual redirect handling. Single-URL scope; no third-party intermediary.

### 📚 New Skills

- `code-semantic-search` - specialized sibling of `rag-implementation` for code corpora. References the internal `devai-code-search` MCP as the reference implementation (no external attribution).

- `ui-component-generation` - LLM-native replacement for external component-generation services (replaces `magic-ui`-class MCPs).

- `local-docs-lookup` - 7-step grounding sequence for library / API questions (introspect -> vendored README -> shipped docs -> type stubs -> project docs -> man pages -> user-approved single URL via `devai-web-fetch`). Replaces `context7`-class MCPs.

### ⚙️ Command and Workflow Improvements

- **`/run-deep-review` command** - new 12-phase pre-release deep-review orchestrator. Chains known-gaps collection, health gates (test execution + 80% line-coverage threshold), dependency scan, docs / git / CI/CD / release-readiness hygiene, project validators, `/analyze-codebase`, `/run-security-audit`, `/run-penetration-test --depth=deep`, and `/review-codebase`. Synthesizes findings (P0/P1/P2/P3) into one severity-ranked report with a GO / GO-WITH-CONDITIONS / NO-GO verdict.

- **`/compare-project` Section 9 "Security and Risk Assessment"** - mandatory section evaluating threat model, per-item risk scorecard, reverse-engineering viability, and recommendation ordering BEFORE producing any adoption plan. The chain into `/generate-plan` always passes `reverse-engineer-first=true` so generated plans sequence skill-native first, then RE builds, then vendor-intrinsic with justification.

- **Internal MCP benchmark harness** - `make benchmark` runs `scripts/devai_mcp_benchmark.py` against all three internal MCPs (`devai-skill-server`, `devai-code-search`, `devai-web-fetch`). No-network guard refuses outbound sockets during the local-only benchmark phases.

- **Style-guide files relocated** out of `catalog/commands/` to `catalog/style-guides/` (sibling). They no longer surface in the slash menu, removing visual noise from `/compile-deep-research-style-guide` and `/generate-report-style-guide` showing up alongside their parent commands.

- **Markdown style guide for generated documentation** ([catalog/style-guides/markdown.md](catalog/style-guides/markdown.md)) - canonical formatting reference (blank-line rules, nested-indent rules, code-in-list rules, ASCII rule). Referenced from `AGENTS.md` so the agent picks up the rule on every session.

### 💥 Breaking Changes

- **4 third-party MCP registry entries removed**: `context7` (Upstash search-as-service), `exa-web-search` (Exa search-as-service), `firecrawl` (scraping-as-service), `magic-ui` (21st.dev generation-as-service). Users who relied on these can re-add them to their own `.claude/settings.json`; DevAI-Hub no longer ships the snippets.

- **Two slash commands removed from the menu**: `/compile-deep-research-style-guide` and `/generate-report-style-guide`. The parent commands `/compile-deep-research` and `/generate-report` are unaffected.

- **`/generate-implementation-plan` deprecation alias removed**. Use `/generate-plan` directly.

See the full plan at [docs/v1.0.0/plans/security-hardening-v100.md](docs/v1.0.0/plans/security-hardening-v100.md) and detailed release notes at [docs/v1.0.0/RELEASE_NOTES.md](docs/v1.0.0/RELEASE_NOTES.md).

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
*   **Globally**: Your user profile now has all 187 Claude Skills, 34 Commands, 13 Hooks, 10 Agents, plus Gemini and Codex instructions.
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

## 🤝 Collaboration

DevAI-Hub is a curated open-source project. While Pull Requests (PRs) are typically not accepted from outside contributors, suggestions, feedback and recommendations are more than welcomed. If you have a better prompt, a smarter rule, or a pattern you'd like to see in the catalog, please reach out directly:

- **Email**: [benjamin@supiramedical.com](mailto:benjamin@supiramedical.com)
- **GitHub**: [@bendourthe](https://github.com/bendourthe)

I'm happy to discuss skill / command / hook proposals, integration ideas for new platforms, or specific use cases - especially when the proposal aligns with the policy direction of this project (reverse-engineering-first, no third-party data leaks).
