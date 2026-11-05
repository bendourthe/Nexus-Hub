# Nexus-Hub Settings

A compact panel for VS Code, Cursor and Antigravity with one shared effort selector and five Nexus-Hub guardrail switches. Changes save automatically through the `nexus-hub settings` engine and are read back before the panel reports the result. The original cyan Nexus logo identifies the extension, dashboard, sidebar and status-bar entry.

## What it controls

- **Default effort**: one preference for supported native defaults and connected Claude Code and Codex sessions.
- **Git safety**: dangerous Git commands and protected-branch checks.
- **Secret scanning**: credential checks before writes.
- **Protect my edits**: checks before overwriting user changes.
- **Large-file warnings**: advisory warnings for unusually large writes.
- **Block Git bypass flags**: checks for skipping hooks or commit signing.

Connected Claude Code and Codex sessions apply effort changes on their next request. A response already running keeps its current effort. Claude Max maps to native `max`; Ultra enables Ultracode with `xhigh` effort. The Codex bridge uses the model's advertised effort values, including native Max and Ultra when supported; older CLI defaults use compatible `xhigh`. Guardrail switches are read on the next hook invocation, including in full-access mode. Copilot, native Cursor and native Antigravity effort have no verified writable integration and are listed in the footer. Native model and approval controls remain available through the CLI.

## Status bar

The status bar shows `High (effort)` by default, or `Nexus Settings: High (effort)` when `nexusHubSettings.compactStatusBar` is off. Its compact hover has a single Nexus Hub Settings title, an Effort Level section with a read-only cyan stepped bar, and a Guardrails section with named on/off indicators. A warning means an available setting failed to synchronize or a guardrail is unavailable. Unsupported editors alone do not produce a warning. Click the status bar to open Settings.

## What the panel shows

One autosaving effort control, five switches and a short application status. Wide panels use a stepped bar; narrow panels use labeled choices in two columns, then one column at the smallest width. The effort control and enabled guardrails use the logo's cyan palette. Use arrow keys, Home or End to select effort, or click a labeled step. Keyboard focus survives a save, and changes are announced to screen readers.

## Live Connection

On Windows, the extension connects installed Claude Code and Codex extensions through their native executable settings. A process that started before the first connection needs an editor reload. The panel identifies missing connections separately in each editor window; another window's native process cannot establish this window's connection. The bridge does not change permissions, sandbox settings or prompts. Existing custom wrappers and workspace launch overrides are preserved and reported when they prevent connection.

Settings 0.4.2 also installs reversible UI adapters for Claude Code 2.1.318 and Codex 26.1021.22027. These vendors do not export an external effort-picker setter. The adapters expose their existing internal setters: Claude applies effort flags, refreshes its cached settings and pushes its normal UI state; Codex updates each open composer's effort through its native model-settings callback while keeping its model and service tier. Repeated synchronization also reaches new tabs. The existing Codex editor-title button uses its native new-tab command and retains the Codex icon. The Settings panel no longer offers replacement agents as a live-update workaround.

Only exact verified source hashes are patched. Original vendor files and a restore receipt are stored under `~/.nexus-hub/native-ui/`; independent changes and unsupported versions are preserved. A restart loads the adapted native extensions and menu. Vendor upgrades require a newly verified adapter. Native process readback, adapter availability and visible picker behavior are distinct checks; see the [0.4.2 evidence](../../docs/releases/v4/v4.15/development/settings-042-native-ui-evidence.md) for the current qualification limits.

The same shared preference is accessible to scripts with `nexus-hub settings set effort high --json`. Other extensions can inspect `(await vscode.extensions.getExtension("nexus-hub.nexus-hub-settings").activate()).getViewModel()`; `liveEffort` describes connected native processes, and `uiEffort` reports adapter installation or reload errors. Neither field by itself proves that every visible picker rendered the change.

The persistent bridge is stored in `~/.nexus-hub/live-effort/` so an extension update does not remove a running session's executable. To disconnect it, disable Settings, then restore `claudeCode.claudeProcessWrapper` and `chatgpt.cliExecutable` to their previous values in User Settings. The extension saves original values in its global state and does not replace a later custom launch setting.

## Requirements

- Updated Nexus-Hub settings-engine modules and hook consumers installed alongside the extension. Updating the VSIX alone cannot add the new runtime controls.
- Python 3 in a standard install location, or its full path in the `nexusHubSettings.pythonPath` user setting. The panel never searches PATH or the workspace for an interpreter.

## Safety

- Disabling a blocking guardrail opens a confirmation. Cancelling writes nothing. Large-file warnings are advisory.
- The command line refuses those changes when it runs inside an agent session, even after you confirm. The panel cannot be used by an agent to turn its own prompts off.
- In an untrusted workspace the panel is read-only.
- The webview runs one nonce-guarded script, loads only the extension's own files, and draws every value with `textContent`. Source links open only for https URLs on vendor documentation hosts.

## Undoing a change

Run `nexus-hub settings reset effort`, or substitute the guardrail control ID. Reset restores what was there before unless the key changed independently afterward. See the [shared preference reference](../../docs/reference/settings-preferences.md), [settings guide](../../guides/NEXUS_HUB_SETTINGS.md) and [settings control contract](../../docs/policy/settings-control-contract.md) for storage, reset, overrides and admission rules.

## Development

```bash
npm ci
npm run compile
npm run test:coverage
npm run package
npm run verify:package
```

The status-bar mark is a one-glyph icon font. After changing `icons/nexus-hub.svg`, run `npm run generate-icons` and commit the regenerated `fonts/nexus-hub-icons.woff2`.
