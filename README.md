<p align="center"><a href="https://github.com/bendourthe/Nexus-Hub"><img src="assets/nexus-hub-banner.png" alt="Nexus Hub" width="640" /></a></p>

# Nexus-Hub

<!-- nexus-hub-version: 4.14.8 -->

Nexus Hub is a backend harness for AI coding tools: skills, commands, rules, hooks, guardrails, and best practices. The installer configures the supported platforms on your machine. Agents use the harness through their existing IDE, terminal, or configured app.

**Catalog:** 340 skills across 23 categories, 21 commands plus 3 permanent aliases, 37 registered hooks, and 23 agents.

[Interactive guide and training](https://www.benjamindourthe.com/nexus-hub/index.html) | [Skills](data/SKILL_INDEX.md) | [Commands](catalog/commands/) | [Platform coverage](docs/policy/platform-read-contracts.md)

## Installation

**Windows PowerShell**

```powershell
irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1 | iex
```

**macOS / Linux Terminal**

```bash
curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash
```

The installer detects supported tools, copies the harness files, and verifies the installation. Reopen your IDE or start a new agent session afterward.

![Terminal mockup: paste the installation command, run the installer, and review verification on Windows, macOS, and Linux](assets/readme/nexus-hub-installation.gif)

[Static preview](assets/readme/nexus-hub-installation.png) | [Install options, updates, and verification](docs/guides/installation-and-platforms.md)

## Development Workflow

`/describe` maps the project, `/review` finds issues, `/plan` defines the changes, `/implement` builds them, `/test` checks behavior, and `/update release` prepares the release.

![Original interactive guide IDE showing the six-command workflow, from project mapping through release preparation](assets/readme/nexus-hub-workflow.gif)

[Static preview](assets/readme/nexus-hub-workflow.png) | [Detailed workflows](docs/guides/development-workflows.md)

## Handoffs

When a usage warning appears, ask for a handoff. Copy the generated prompt into another agent and continue from the recorded next step. The prompt carries verified work, unfinished changes, constraints, and project state.

![Split-screen desktop: Claude offers a handoff at a usage warning, the user copies it into ChatGPT, and ChatGPT continues the unfinished test](assets/readme/nexus-hub-continuity.gif)

Provide the relevant project files to the receiving app. In installed agent integrations, `/handoff` prints in chat unless you explicitly request a file.

[Static preview](assets/readme/nexus-hub-continuity.png) | [Handoff command](catalog/commands/handoff.md)

## Commands

Run **`/skills list`** for the current cheatsheet, arguments, aliases, and common workflows. The guide cards below show command scopes and usage.

![Command cards from the interactive guide, with scopes and lines ready to copy](assets/readme/nexus-hub-commands.gif)

[Static preview](assets/readme/nexus-hub-commands.png) | [Command catalog](catalog/commands/)

## IDE Settings

**4.15.0 preview:** the optional Nexus Hub extension manages shared effort, Fast mode, guardrails, usage alerts, and supported extension controls. Changing global effort updates supported sessions. Manual session choices remain until the next global change or **Apply to all**.

![Nexus Hub settings inside VS Code: change effort and Fast mode, manage guardrails and alerts, and access supported provider controls](assets/readme/nexus-hub-settings.gif)

[Static preview](assets/readme/nexus-hub-settings.png) | [Extension controls](extensions/nexus-hub-settings/README.md)

## Platforms

- **IDEs:** VS Code with Claude Code, Codex, or Copilot; Cursor; Antigravity.
- **Terminal agents:** Claude Code, Codex, and the other [supported integrations](docs/guides/installation-and-platforms.md#supported-agentic-platforms).
- **Desktop chats:** provide the handoff, relevant project files, and Nexus Hub guidance to Claude or ChatGPT. File access, permissions, and hook coverage depend on the receiving tool.

The harness supplies reusable procedures and protections. Project files and explicit handoffs carry the work across tools and models.

## What's New in v4.14.8

- Plain-English guidance and source-labeled hook messages.
- A settings status-bar entry for saved defaults.
- Persistent usage-limit choices and handoffs that continue on another platform without waiting for the old limit to reset.

[Release details and earlier versions](CHANGELOG.md#4148---2026-11-04)

## Documentation

- [Installation and platform reference](docs/guides/installation-and-platforms.md)
- [Development workflows and local checks](docs/guides/development-workflows.md)
- [Skill catalog](data/SKILL_INDEX.md) and [command catalog](catalog/commands/)
- [Security, privacy, and regulated-use considerations](SECURITY.md)
- [Contributing](CONTRIBUTING.md) and [project progress](docs/todos.md)
- [Editable animation sources](assets/readme/README.md)

## License

[MIT](LICENSE). Maintained by [Benjamin Dourthe](https://www.benjamindourthe.com/).
