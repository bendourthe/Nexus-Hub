# DevAI Hub
**Production-Grade Brain Upgrades for Your AI Coding Assistant**

> **Turn generic AI into a Senior Engineer.**
> One-click setup for Claude Code (Anthropic), Gemini (Google), and GitHub Copilot (Microsoft).

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
*   **Globally**: Your user profile now has all 63 Claude Skills and Gemini instructions.
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

## 🧩 How to Use (Manual Method)

If you prefer to copy things yourself, here is how the repo is organized:

### 1. Claude Code (Anthropic)
This is the most powerful integration. It adds **autonomous agent capabilities**.
*   **CLAUDE.md**: The "Brain". Copy `catalog/CLAUDE.md` to your project root and customize it.
*   **Skills**: The "Hands". Copy folders from `catalog/skills/` to your project's `.claude/skills/` folder.
    *   *Example*: Copy `catalog/skills/research/trend-research` to enable the "Trend Research" skill.

### 2. Gemini (Google)
Optimized instructions for Google's Gemini models.
*   **Gemini Instructions**: Copy `templates/ai-instructions/generic-instructions.md` to `.gemini/GEMINI.md` in your project or user profile.
*   **Skills & Workflows**: The installer mirrors these to `.gemini/skills` and `.gemini/antigravity/global_workflows` so they appear globally in Antigravity.

### 3. GitHub Copilot (Microsoft)
Instructions for VS Code's Copilot Chat.
*   Copy `templates/ai-instructions/coding-instructions/{language}.md` to `.github/copilot-instructions.md`.

---

## 🧠 Featured Skills

| Skill | What it does |
|-------|--------------|
| **Trend Research** | Researches Reddit/X for the last 30 days to find trends & write prompts. |
| **Code Review** | A 6-step deep dive (Security, Perf, Logic) before you merge. |
| **Test Gen** | Writes comprehensive unit tests using AAA pattern and mocks. |
| **Compliance** | Checks code against SOC2, GDPR, and ISO standards. |

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

## 🤝 Contributing
Found a better prompt? A smarter rule? Open a PR! We want to build the ultimate knowledge base for AI coding.
