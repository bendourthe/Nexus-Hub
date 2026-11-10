# Installation and Platforms

Installation reference for users configuring Nexus Hub: supported platforms, selective installs, updates, pinned releases, verification, and manual setup. Run repository commands from the repository root.

## Supported Agentic Platforms

| Platform | Install target | Path | Per-platform surface |
|---|---|---|---|
| Claude Code (Anthropic) | `~/.claude/` + project `.claude/` | legacy + registry | Full: skills, commands, hooks, agents, rules, MCP configs |
| OpenAI Codex CLI | `~/.codex/` + project `.codex/` + `AGENTS.md` | registry | Full: skills (under `skills/`), commands (under `prompts/`), agents, rules |
| Gemini (IDE / Antigravity 1.0) | `~/.gemini/` + project `.gemini/GEMINI.md` | registry | Full: skills, commands (under `workflows/`), agents, rules |
| **Gemini CLI (Google, ENTERPRISE-ONLY post-2026-06-18)** | `~/.gemini/commands/*.toml` + project `.gemini/commands/*.toml` | **registry (new in v2.1.0; gated behind `--enterprise` / `-Enterprise` flag in v2.2.0)** | TOML-format custom commands generated from `catalog/commands/*.md`. Non-enterprise users transition to Antigravity CLI before 2026-06-18 per the 2026-05-21 Google announcement. |
| **Antigravity 2.0 + CLI (Google)** | `~/.gemini/antigravity-cli/` + project `.agents/` | **registry (new in v2.1.0, CLI coverage added v2.2.0; paths verified v2.3.0)** | Full: skills, commands (under `workflows/`), subagents, rules. Single integration covers both the desktop IDE and the standalone Antigravity CLI (`agy` binary), verified 2026-05-29 against Google's public Antigravity CLI docs. |
| GitHub Copilot (VS Code) | project `.github/copilot-instructions.md` + VS Code user-profile `prompts/` | registry | Personal and repository instructions (skill index embedded as text), native agents and hooks, user-global `/<name>` prompts; opt-in `.github/skills/` wrappers via `NEXUS_HUB_COPILOT_SKILLS` |
| Cursor | project `.cursor/` + `AGENTS.md` | registry | Flattened skills (one command-skill per catalog command), `.cursor/rules/nexus-hub.mdc`, and the `AGENTS.md` guardrails |
| OpenCode | `~/.config/opencode/` + project `.opencode/` + `AGENTS.md` | registry | Skills, commands, rules, and agents |
| Qwen Code | `~/.qwen/` (detection-gated) + project `.qwen/` | registry | Flattened skills, subagents, Markdown commands, and `QWEN.md` |
| Kimi Code CLI | `~/.kimi-code/` (detection-gated) + project `.kimi-code/` | registry | Flattened skills (each surfaces as `/skill:<name>`) and `AGENTS.md` |
| Devin Desktop / Windsurf | `~/.codeium/windsurf/` + project `.devin/` and `.windsurf/` | registry | Native skills, workflows, rules, and hooks; `.windsurfrules` kept for compatibility |
| Hermes | `~/.hermes/skills/` (detection-gated) + project `.hermes/skills/` | registry | Native folder-per-skill `SKILL.md` discovery; no instruction file needed |
| Pi | `~/.pi/agent/` (detection-gated) + project `.pi/` | registry | Flattened skills plus one prompt template per command (Pi's `/name` surface) |
| OpenClaw | the configured OpenClaw workspace | registry | `AGENTS.md`, `SOUL.md`, `IDENTITY.md`, and native skills; no tool-interception hooks |
| Aider | project `CONVENTIONS.md` | registry | Behavioral guardrails only; a global install is a no-op |
| **Nexus-AI (Local Studio)** | `~/.nexus-ai/catalog/` + project `.nexus-ai/catalog/` | **registry (new in v2.1.0)** | Full mirror: skills, commands, agents, rules, hooks, MCP configs, templates, plus a `nexus-hub-version.json` manifest. Isolated under `catalog/` so the app's own data at the `~/.nexus-ai/` root stays outside a catalog refresh. |
| GitHub CLI (`gh`) | via `gh copilot` extension | indirect | Skill / command references via `AGENTS.md` open standard |
| Nexus desktop app | upstream consumer | indirect | Reads the same catalog as its skill feed |
| Nexus VS Code extension | upstream consumer | indirect | Reads the same catalog as its skill feed |

**Coverage caveat**: every platform now installs through the **registry** path, which dispatches install / teardown through `scripts/lib/integrations/runner.py` and supports a `--dry-run` mode. For Claude Code, the one row marked "legacy + registry", the registry renders only the marker-merged instruction file while the installer's own copy blocks write the catalog tree. Coverage differs surface by surface, and the authoritative per-platform read paths and coverage tiers are in [`docs/policy/platform-read-contracts.md`](../../docs/policy/platform-read-contracts.md). The per-platform installer logic lives in [`scripts/installer.sh`](../../scripts/installer.sh), [`scripts/installer.ps1`](../../scripts/installer.ps1), and the per-platform subclasses under [`scripts/lib/integrations/`](../../scripts/lib/integrations/). Per-platform capability specs (install surface, distributed content, instruction file, quirks) are documented under [`docs/specs/`](../../docs/specs/).

**Branch-based install** (v2.4.0): pass `--branch <name>` (Bash) or `-Branch <name>` (PowerShell) to install the catalog from a pushed branch instead of the current checkout. The installer shallow-clones the repo at `<name>` into a deterministic cache directory (`~/.nexus-hub/branches/<sanitized-name>/`) and runs the install from that checkout, so the user's working copy is never touched. The branch name is sanitized for filesystem safety (path-traversal sequences are neutralized). Combine with `--check` / `-Check` for a clone-free probe that prints the resolved cache path and clone source.

---

## Quick Start (one command)

Open a terminal and paste the line for your system. It downloads the catalog from this repo and runs the installer -- no clone, no unzip, no `cd`.

**macOS / Linux** (paste into Terminal):

```bash
curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash
```

No `curl` on the box? Use `wget`:

```bash
wget -qO- https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash
```

**Windows** (paste into PowerShell):

```powershell
irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1 | iex
```

The installer configures the supported assistants it detects. The installer prechecks its dependencies (and tells you exactly what to install if one is missing), then performs a global install across every supported assistant it detects; assistants you do not have are skipped with a note, never an error. For Kimi Code CLI, Qwen Code, Hermes, Pi, Aider, OpenCode, and Nexus AI Studio, "have" means the installer found the tool itself (its command on `PATH`, files the tool wrote, or its application), not a folder an earlier Nexus-Hub install created; the skip note says what it looked for, and `nexus-hub doctor` lists leftover Nexus-Hub files for tools you do not have, which `nexus-hub prune-undetected` removes (preview first, `--yes` to delete). See `docs/policy/platform-detection.md`. Your customizations are preserved (marker-merge), and on a re-install it asks once only if it finds a managed file you changed that it would overwrite, naming the file.

**Done.** The installer writes to `~/.nexus-hub/` (the user-global catalog) and into each supported assistant's per-platform config locations. If a legacy `~/.devai-hub/` install is detected, you will see a single migration prompt at the top of the run -- answer `Y` (default) to migrate in place.

After the installer completes:

- **Globally**: your user profile has all 340 skills, 21 commands, 37 registered hooks, 23 agents, plus Gemini and Codex instructions.
- **Locally**: your project has `copilot-instructions.md` and `AGENTS.md` tailored to your language.

**Power-user flags**: `--workspace <path>` installs into a single repo instead of globally; `--platforms <comma-list>` limits the install to a subset of assistants, and naming one that the installer did not find (for example `--platforms qwen`) installs it anyway; `--yes` runs fully unattended (refreshes managed files with no prompt -- ideal for CI). Prefer to clone first? `git clone` the repo and run `./install.sh` (macOS / Linux) or `install.bat` (Windows) -- the in-repo path still works exactly as before.

### Claude Code plugin (subscribe-style alternative)

The installer above is the primary path: every platform, hooks, and `nexus-hub upgrade`. Claude Code users who only want the catalog as a plugin can subscribe instead:

```
/plugin marketplace add bendourthe/Nexus-Hub
/plugin install nexus-hub@nexus-hub
```

This is not a replacement for the installer. It does not install hooks, other platforms, or the `nexus-hub` CLI.

If Anthropic later lists Nexus-Hub in `claude-plugins-official`, that listing is pinned to a git SHA that can lag tagged releases. Marketplace users may trail `main`. Prefer the installer, or this repo's marketplace added from a release tag, when you need the current release. The maintainer submission draft is [`docs/archives/v3/v3.20/development/claude-marketplace-submission.md`](../../docs/archives/v3/v3.20/development/claude-marketplace-submission.md).

### Installing a subset (selective installation)

By default you get the whole catalog. If you want a smaller install, pick a **profile**, one or more **capability modules**, or one or more **role bundles**. Selectors combine by union.

```bash
# macOS / Linux
bash scripts/installer.sh --profile core
bash scripts/installer.sh --modules ai-engineering,testing
bash scripts/installer.sh --bundles ai-engineer
bash scripts/installer.sh --profile core --modules security-operations   # union
```

```powershell
# Windows
.\scripts\installer.ps1 -Profile core
.\scripts\installer.ps1 -Modules ai-engineering,testing
.\scripts\installer.ps1 -Bundles ai-engineer
```

Profiles are `minimal`, `core`, and `full`. Modules group skills by capability (one per catalog category, so every skill is reachable through at least one). Role bundles are curated cross-category sets like `ai-engineer` or `devops-engineer`. List what is available with `python scripts/lib/installer/selection.py --repo-root . --profile core` , which prints the resolved plan without installing anything.

Three things worth knowing before you narrow an install:

- **Hooks, rules, templates, and settings always install**, under every selection including `minimal`. Narrowing your skill set asks for fewer capabilities, never for fewer guardrails.
- **Commands and agents follow their skills.** A command that is a thin pointer over one skill (for example `/implement` over `implement-phase`) installs only when that skill is selected; everything else installs regardless. So a focused install stays coherent instead of leaving commands that cannot do anything.
- **No selector means the full catalog**, byte-for-byte identical to what you would have got before selective installation existed.

`nexus-hub upgrade` re-applies whatever you selected, so an upgrade never quietly widens a focused install back to everything. To change scope, pass a new selector; to go back to everything, pass `--profile full`.

Selectors need Python to resolve. A full install does not.

### Check the installed version

```bash
nexus-hub version    # prints the installed version
nexus-hub upgrade    # checks for the latest release and updates in place
```

`nexus-hub -v` and `nexus-hub --version` print the same line as `nexus-hub version`.

### Keeping it current

Run `nexus-hub upgrade` -- it reports your installed version against the latest, shows a short what's-new summary, and updates in place on confirmation. Re-running the install command above works too; the installer is idempotent.

### Pinning a version, verifying the download, rolling back

The one-line install above follows the `main` branch, which has no publishable checksum because every commit changes the archive. To install a specific release instead, pin a tag; a pinned install downloads the tarball the project published for that release and verifies it before anything runs.

| Element | Detail |
|---|---|
| **Activation** | macOS / Linux: `curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh \| bash -s -- --ref v4.7.0`. Windows: `&([scriptblock]::Create((irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1))) -Ref v4.7.0`. The `NEXUS_HUB_REF` environment variable does the same. |
| **Validation** | The bootstrap prints `checksum OK (<sha256>)` before extracting; `nexus-hub --version` reports the installed version; `~/.nexus-hub/PINNED_REF` holds the pinned tag. `gh attestation verify Nexus-Hub-4.7.0.tar.gz -R bendourthe/Nexus-Hub` checks the build-provenance attestation of the published tarball. |
| **Rollback** | `nexus-hub upgrade --ref v4.6.0` installs an older tag (any tag that carries the published artifact set, v4.7.0 and later); `nexus-hub upgrade --latest` moves a pinned install to the newest release; installing `main` again removes the pin. |
| **Authority** | Verification proves the download is byte-for-byte what the release workflow published for that tag. It does not audit the catalog's content, grant any platform permission, or protect the host; a pinned install receives no updates until you move it. Tags published before v4.7.0 carry no artifact set and fail closed. |
| **Docs** | `docs/decisions/implemented/policy/2026-09-05-verifiable-pinnable-installs.md`; the bootstrap headers in `install.sh` and `install.ps1`. |

`nexus-hub upgrade` on a pinned install refuses to move and prints those options, so an upgrade never quietly unpins you.

### Verifying your install

Run `nexus-hub verify` to confirm your installed catalog matches the published release. It recomputes the SHA-256 of every file in the catalog tree and diffs the result against the `MANIFEST.sha256` that ships with each release, reporting any file that is modified, missing, or unexpected, then a single `verify: PASS` or `verify: FAIL` line. It is strictly local: it reads only local files, makes no network call, needs no credential, and adds no dependency.

What this does and does not prove: `verify` detects on-disk tampering or corruption AFTER install, relative to the published catalog. It is trustworthy to the extent the manifest itself came from the release you trust (it rides inside the same signed release tag the installer pulls from). It is NOT a code signature and NOT a substitute for verifying the download channel -- an attacker who can rewrite both a file and the manifest in the same tree defeats it. Use it to catch accidental corruption and post-install drift, not to establish first-trust in the bytes.

### Add organization standards

Connect a validated local-directory or Git bundle with `nexus-hub org connect <path-or-url>`, inspect it with `nexus-hub org status`, and then reinstall or repair the target workspace. Nexus-Hub projects the organization's concise core and rule files into existing platform surfaces without uploading the bundle or claiming policy enforcement. See the [Organization Knowledge Layer guide](../../guides/ORG_KNOWLEDGE_LAYER.md) for the bundle contract, lifecycle commands, precedence model, authoring workflow, and rollback procedure.

---

## Manual setup (if you do not want to run the installer)

If you prefer to copy things yourself, here is how the repo is organized.

### Claude Code (Anthropic)

The most powerful integration -- adds **autonomous agent capabilities**.

- **CLAUDE.md**: the "brain". Copy `templates/ai-instructions/base-claude.md` to `CLAUDE.md` at your project root and customize.
- **Skills**: the "hands". Copy folders from `catalog/skills/` to your project's `.claude/skills/` folder.

    *Example*: copy `catalog/skills/research/trend-research` to enable the trend-research skill.

### Gemini (Google) and Antigravity

Optimized instructions for Google's Gemini models, including the Antigravity workspace layout.

- **Gemini instructions**: copy `templates/ai-instructions/base-gemini.md` (or `templates/ai-instructions/generic-instructions.md` for the legacy template) to `.gemini/GEMINI.md` in your project or user profile.
- **Skills and workflows**: the installer mirrors these to `.gemini/skills/` and `.gemini/workflows/`; Antigravity 2.0 receives its own copies under `~/.gemini/config/skills/` and `~/.gemini/config/workflows/`.

### GitHub Copilot (Microsoft)

Instructions for VS Code's Copilot Chat.

- Copy `templates/ai-instructions/coding-instructions/{language}.md` to `.github/copilot-instructions.md`.

### Codex (OpenAI)

OpenAI Codex CLI integration. Codex reads `AGENTS.md` at the project root (the open standard, also honored by Cursor / Aider / Jules) plus its user-level config in `~/.codex/`.

- **AGENTS.md**: copy `templates/ai-instructions/base-codex.md` content into your project's `AGENTS.md`.
- **Skills and prompts**: the installer mirrors `catalog/skills/` to `~/.codex/skills/` and `catalog/commands/` to `~/.codex/prompts/`. For manual setup, copy each tree to those destinations.

### Cursor

Cursor IDE integration.

- **Project rules**: copy `templates/ai-instructions/base-cursor.md` content into `.cursor/rules/nexus-hub.mdc` at your project root. Use `alwaysApply: true` in the frontmatter so Cursor applies the rule on every prompt.
- **Open-standard `AGENTS.md`**: Cursor also reads `AGENTS.md` at the project root, so the Codex setup above covers Cursor too.

### OpenCode

OpenCode IDE integration. OpenCode reads `AGENTS.md` per the open standard.

- Copy `templates/ai-instructions/base-opencode.md` content into your project's `AGENTS.md`.

---
