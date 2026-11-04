# Nexus-Hub Settings

A VS Code panel that sets the defaults new Claude Code, Codex, and GitHub Copilot sessions start with, and shows what stops each default from taking effect. It is a thin panel over the `nexus-hub settings` command line: the command line reads and writes the tool configuration files, and the panel shows its JSON, writes the VS Code-host settings, and asks you to confirm anything that lowers a safety barrier.

## What it controls

- **Default effort**: one value for every tool, with an optional override per tool.
- **Default model**: chosen per tool, because each tool has its own model family.
- **Approval posture**: ask, accept edits, or full auto.
- **Commit attribution off**.
- **Git-guardrails mode**.

Every control is a default for new sessions only. A session that is already running keeps the value it started with. A control appears only where the value was observed changing a fresh session before it shipped. Anything else is shown as "Not settable" with its reason, never as a toggle that silently does nothing.

## Status bar

The Nexus-Hub mark sits in the status bar just left of the usage monitors, followed by the effort a new session starts with: the value every settable tool agrees on, `mixed` when they differ, or `default` when none is set. When a default is overridden, not covered, unverified, or cannot be detected, a warning icon and a count follow. Hover for every tool's effort, model, and approval default, the other controls, and what needs attention; click to open the full panel. The status bar reads the same model the panel draws, once at startup and again whenever a watched settings file changes.

## What the panel shows

Each tool row has exactly one state: in effect, tool default, overridden by a named file, variable, or policy (with a one-line fix), not settable (with the reason), not covered, unverified for the installed version, not installed, or cannot detect. A row that cannot be set folds its reason under "Why it cannot be set"; notes the panel cannot verify, such as a mode the tool remembers, fold under a notes link. Known model ids appear as buttons under the model field. A folded preview at the top states what a new session starts with if you choose High effort and Full auto, built from the same catalog.

## Requirements

- Nexus-Hub installed (the installer puts the command line at `~/.nexus-hub/scripts/nexus_hub_cli.py`).
- Python 3 in a standard install location, or its full path in the `nexusHubSettings.pythonPath` user setting. The panel never searches PATH or the workspace for an interpreter.

## Safety

- Changes that lower a safety barrier (full auto, git guardrails off, removing a safety block) open a confirmation that lists every key to be written, repeats VS Code's own auto-approve warning, and lists what will still prompt. Cancelling writes nothing.
- The command line refuses those changes when it runs inside an agent session, even after you confirm. The panel cannot be used by an agent to turn its own prompts off.
- In an untrusted workspace the panel is read-only.
- The webview runs one nonce-guarded script, loads only the extension's own files, and draws every value with `textContent`. Source links open only for https URLs on vendor documentation hosts.

## Undoing a change

Use "Reset" on a control. It restores what was there before, unless you changed the key since, in which case it leaves your value and says so. See [the settings guide](../../guides/NEXUS_HUB_SETTINGS.md) for what each control means per tool, the override states and their fixes, `remove-override`, and uninstall, and [the settings control contract](../../docs/policy/settings-control-contract.md) for the admission rule and the write rules.

## Development

```bash
npm ci
npm run compile
npm run test:coverage
npm run package
npm run verify:package
```

The status-bar mark is a one-glyph icon font. After changing `icons/nexus-hub.svg`, run `npm run generate-icons` and commit the regenerated `fonts/nexus-hub-icons.woff2`.
