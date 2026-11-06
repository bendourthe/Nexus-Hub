# Nexus Hub

A compact panel for VS Code, Cursor and Antigravity with one shared effort selector and five Nexus-Hub guardrail switches. Changes save automatically through the `nexus-hub settings` engine and are read back before the panel reports the result. The original cyan Nexus logo identifies the extension, dashboard, sidebar and status-bar entry.

## What it controls

- **Default effort**: one preference for supported native defaults and connected Claude Code and Codex sessions.
- **Fast mode**: an independent shared speed preference for supported Claude Code, Codex and Cursor sessions. Until chosen, existing speeds are preserved. Fast mode may increase usage or cost and follows each provider's model and account restrictions.
- **Open Codex in tabs**: an Editor switch that controls the existing Codex toolbar button. On opens independent editor tabs with Nexus history access; off opens the native activity pane. The preference survives extension and Nexus installer updates.
- **Git safety**: dangerous Git commands and protected-branch checks.
- **Secret scanning**: credential checks before writes.
- **Protect my edits**: checks before overwriting user changes.
- **Large-file warnings**: advisory warnings for unusually large writes.
- **Block Git bypass flags**: checks for skipping hooks or commit signing.

Changing the Nexus default updates connected Claude Code, Codex, and qualified Cursor Agent sessions once. A later manual effort selection belongs to that session and is preserved until the Nexus default changes again or you click Apply to all. Newly connected sessions receive the Nexus default within the synchronization interval. The next request uses the selected effort. A response already running keeps its current effort. Claude Max maps to native `max`; Ultra enables Ultracode with `xhigh` effort. Codex and Cursor use each model's advertised effort values, mapping higher Nexus levels to the highest compatible native value while preserving the model and unrelated parameters. Guardrail switches are read on the next hook invocation, including in full-access mode. Copilot and native Antigravity effort require manual selection. Native model and approval controls remain available through the CLI.

## Status bar

Fast mode uses Claude's native session-scoped `fastMode` settings and confirmed state readback, Codex's advertised Fast service tier, and Cursor's advertised Fast model parameter. New Claude processes receive the shared speed in their launch settings. It does not lower effort or choose another model. Manual speed and effort choices are independent and last until the corresponding Nexus preference changes or Apply to all reapplies both. Claude's native model, organization and usage-credit checks remain active; see [Claude Code Fast mode](https://code.claude.com/docs/en/fast-mode). Speed changes apply to the next request, not a response already running. Existing Codex conversations use the native next-turn settings API; draft tabs use the draft setter. A rejected Codex update is attempted once per Nexus revision, with an explicit Apply to all or a changed default allowing another attempt.

The status bar shows `High (effort)` by default, or `Nexus Hub: High (effort)` when `nexusHubSettings.compactStatusBar` is off. Its compact hover has a single Nexus Hub title, an Effort Level section with a read-only cyan stepped bar, and a Guardrails section with named on/off indicators. A warning means an available setting failed to synchronize or a guardrail is unavailable. Unsupported editors alone do not produce a warning. Click the status bar to open Settings.

## What the panel shows

One autosaving effort control, five switches and a short application status. Wide panels use a stepped bar; narrow panels use labeled choices in two columns, then one column at the smallest width. The effort control and enabled guardrails use the logo's cyan palette. Use arrow keys, Home or End to select effort, or click a labeled step. Keyboard focus survives a save, and changes are announced to screen readers.

## Live Connection

On Windows, the extension connects installed Claude Code and Codex extensions through their native executable settings. A process that started before the first connection needs an editor reload. The panel identifies missing connections separately in each editor window; another window's native process cannot establish this window's connection. The bridge does not change permissions, sandbox settings or prompts. Existing custom wrappers and workspace launch overrides are preserved and reported when they prevent connection.

Nexus Hub 0.5.0 installs reversible UI adapters for Claude Code 2.1.318 and Codex 26.1021.22027. These vendors do not export an external effort-picker setter. The adapters expose their existing internal setters: Claude applies effort flags, verifies native readback for connected channels, and updates the picker through its native applied-effort signal owner; Codex updates each open composer's effort through its native model-settings callback while keeping its model and service tier. Revision-aware synchronization initializes new tabs while leaving later manual session choices intact. The existing Codex editor-title button uses its native new-tab command and retains the Codex icon. The Settings panel no longer offers replacement agents as a live-update workaround.

Only exact verified source hashes are patched. Original vendor files and a restore receipt are stored under `~/.nexus-hub/native-ui/`; independent changes and unsupported versions are preserved. A restart loads the adapted native extensions and menu. Vendor upgrades require a newly verified adapter. Native process readback, adapter availability and visible picker behavior are distinct checks; see the [0.5.0 evidence](../../docs/releases/v4/v4.15/development/settings-050-session-overrides-evidence.md) for the current qualification limits.

Cursor 3.29.9 requires an exact-build adapter in the IDE's own workbench because its public extension API has no effort setter. The adapter uses Cursor's native model catalog and per-session setter, preserving context size and Fast mode. Installation backs up the workbench and product manifest, then updates only that workbench's checksum while retaining every other integrity entry. Fully exit and restart Cursor after the first installation. `restoreVendorUi(receiptPath)` restores the backed-up bytes when the installed files still match the adapter output. Auto and models without an advertised effort parameter keep their native behavior. Cursor upgrades require a newly qualified build.

The shared effort preference is accessible to scripts with `nexus-hub settings set effort high --json`. Other extensions can inspect `(await vscode.extensions.getExtension("nexus-hub.nexus-hub-settings").activate()).getViewModel()` and call the returned API's `setFastMode(boolean)` or `setCodexTabs(boolean)`. Both actions require a trusted workspace. Shared speed and navigation values live in `~/.nexus-hub/session-defaults.json`; effort and guardrails retain their existing engine-owned preferences. `liveEffort` describes connected native processes, and `uiEffort` reports adapter installation or reload errors. Neither field by itself proves that every visible picker rendered the change.

The persistent bridge is stored in `~/.nexus-hub/live-effort/` so an extension update does not remove a running session's executable. To disconnect it, disable Settings, then restore `claudeCode.claudeProcessWrapper` and `chatgpt.cliExecutable` to their previous values in User Settings. The extension saves original values in its global state and does not replace a later custom launch setting.

## History and Upgrades

The Codex editor toolbar includes a Codex History button. It reads local session titles from the Codex history index and opens the selected conversation in a native Codex editor tab. It does not read conversation content. The Codex sidebar remains available for full history and remote sessions, and through the Open Codex in tabs switch. The installer-delivered adapter retains the native sidebar button as a fallback when Nexus is disabled.

The Settings panel shows the installed Nexus-Hub version. Check for upgrades opens the existing interactive Nexus-Hub CLI upgrade flow in a terminal, where you can review the available update before accepting installation. The extension identifier and existing configuration keys stay unchanged during the Nexus Hub rename.

The Apply Default Effort to All Sessions, Codex History and Check for Upgrades actions are also available through the VS Code command palette as Nexus Hub commands.

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

## Installation Defaults and Restarts

Fresh installations start with Medium effort, Fast mode off, and Open Codex in tabs on. Existing preference files are preserved during upgrades. The Extensions section groups settings by provider. Restart Codex restarts only its app-server and then refreshes its open tabs with their saved conversations. Restart Claude Code restarts idle Claude session processes and schedules busy sessions to restart after their current turn. Neither restarts the shared extension host. A Refresh Codex Tab button beside History rebuilds only the current panel. Refreshing replaces the composer, so send or copy an unsent draft first. Codex restart may interrupt running Codex requests; saved conversations are retained.

## Usage Alerts

Usage warning panels dismiss automatically after 10 seconds. Nexus Hub Settings has a prominent All usage alerts switch and separate Claude Code, Codex, GitHub Copilot, Cursor, and Gemini / Antigravity switches. The master switches every provider together; a mixed state indicates that only some providers are enabled. Individual choices are shared across local editors in `~/.nexus-hub/usage-alerts.json` and default to enabled. Turning an alert off closes its current warning and suppresses future usage warnings, including fallback urgency notifications. Usage polling, taskbar colors, connection errors and explicit command results remain available.
