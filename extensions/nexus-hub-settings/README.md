# Nexus Hub

A compact panel for VS Code, Cursor and Antigravity with one shared effort selector and five Nexus-Hub guardrail switches. Changes save automatically through the `nexus-hub settings` engine and are read back before the panel reports the result. The original cyan Nexus logo identifies the extension, dashboard, sidebar and status-bar entry.

## What it controls

- **Default effort**: one preference for supported native defaults and connected Claude Code and Codex sessions.
- **Fast mode**: an independent shared speed preference for supported Claude Code, Codex and Cursor sessions. Until chosen, existing speeds are preserved. Fast mode may increase usage or cost and follows each provider's model and account restrictions.
- **Open Codex in tabs**: an Editor switch that controls the existing Codex toolbar button. On opens independent editor tabs with Nexus history access; off opens the native activity pane. The preference survives extension and Nexus installer updates. Menu routing validates Codex's `package.json` structure independently of the optional live effort composer adapter. Provider-only recovery registers native lifecycle owners separately. The Codex icon in the activity bar is drawn by VS Code itself and always opens the side pane.
- **Git safety**: dangerous Git commands and protected-branch checks.
- **Secret scanning**: credential checks before writes.
- **Protect my edits**: checks before overwriting user changes.
- **Large-file warnings**: advisory warnings for unusually large writes.
- **Block Git bypass flags**: checks for skipping hooks or commit signing.

Changing the Nexus default updates connected Claude Code, Codex, and qualified Cursor Agent sessions once. A later manual effort selection belongs to that session and is preserved until the Nexus default changes again or you click Apply to all. Newly connected sessions receive the Nexus default within the synchronization interval. The next request uses the selected effort. A response already running keeps its current effort. Claude Max maps to native `max`; Ultra enables Ultracode with `xhigh` effort. Codex and Cursor use each model's advertised effort values, mapping higher Nexus levels to the highest compatible native value while preserving the model and unrelated parameters. Guardrail switches are read on the next hook invocation, including in full-access mode. Copilot and native Antigravity effort require manual selection. Native model and approval controls remain available through the CLI.

## Status bar

Fast mode uses Claude's native session-scoped `fastMode` settings and confirmed state readback, Codex's advertised Fast service tier, and Cursor's advertised Fast model parameter. New Claude processes receive the shared speed in their launch settings. It does not lower effort or choose another model. Manual speed and effort choices are independent and last until the corresponding Nexus preference changes or Apply to all reapplies both. Claude's native model, organization and usage-credit checks remain active; see [Claude Code Fast mode](https://code.claude.com/docs/en/fast-mode). Speed changes apply to the next request, not a response already running. Existing Codex conversations use the native next-turn settings API; draft tabs use the draft setter. A rejected Codex update is attempted once per Nexus revision, with an explicit Apply to all or a changed default allowing another attempt.

The status bar shows a six-segment effort meter and the selected level, with an `Effort: ` prefix when `nexusHubSettings.compactStatusBar` is off. The hover has a cyan stepped bar with all six labels beneath their points. In a trusted, idle workspace, each point and label selects that effort through the same command as the panel; read-only and busy states disable these links. Guardrails use two aligned columns with full names and on/off states. A warning means an available setting failed to synchronize or a guardrail is unavailable. Unsupported optional composer adapters alone do not produce a warning. Click the status bar to open the Nexus panel.

## What the panel shows

The hover previews the chosen level immediately with a saving indicator, then restores the confirmed state when the operation completes. Open local Codex conversations use the native next-turn settings setter; drafts use the native draft setter without replacing the provider default independently. Claude updates existing channels through its native flag setter and verifies effort readback. A later manual session choice is preserved until the next global revision. Current native picker integration discovers unique method and property contracts independently of provider version numbers, validates syntax before installation, and keeps originals under `~/.nexus-hub/native-ui/effort/`. Missing or ambiguous contracts preserve the provider's files and report the issue.

If an effort write reports missing TOML support, Nexus prepares `tomlkit` in its private settings runtime and retries the write once with the same Python interpreter. Dry runs never install dependencies. Matching saved effort defaults remain readable when the standalone provider CLI is absent. A failed hover effort change opens the Nexus panel; Details and the hover identify the provider and reason.

One autosaving effort control, five switches and a short application status. Wide panels use a stepped bar; narrow panels use labeled choices in two columns, then one column at the smallest width. The effort control and enabled guardrails use the logo's cyan palette. Use arrow keys, Home or End to select effort, or click a labeled step. Keyboard focus survives a save, and changes are announced to screen readers.

## Live Connection

On Windows, the extension connects installed Claude Code and Codex extensions through their native executable settings. A process that started before the first connection needs an editor reload. The panel identifies missing connections separately in each editor window; another window's native process cannot establish this window's connection. The bridge does not change permissions, sandbox settings or prompts. Existing custom wrappers and workspace launch overrides are preserved and reported when they prevent connection.

Nexus Hub 0.5.0 installs reversible UI adapters for Claude Code 2.1.318 and Codex 26.1021.22027. These vendors do not export an external effort-picker setter. The adapters expose their existing internal setters: Claude applies effort flags, verifies native readback for connected channels, and updates the picker through its native applied-effort signal owner; Codex updates each open composer's effort through its native model-settings callback while keeping its model and service tier. Revision-aware synchronization initializes new tabs while leaving later manual session choices intact. With the editor preference enabled, the existing Codex editor-title button opens a new native Codex session beside the current editor, splitting the window without closing the current tab. Turning the preference off opens the sidebar. The Codex icon is retained. The Settings panel no longer offers replacement agents as a live-update workaround.

Legacy composer adapters retain their exact source-hash checks. Newer builds use the method-based effort integration described above. Provider-only recovery also registers unique native lifecycle methods without a version allowlist or minified variable names. Registration syntax-checks the modified module and preserves a content-addressed original under `~/.nexus-hub/native-ui/recovery/`; ambiguous or changed method contracts are preserved without patching. Existing native composer backups and restore receipts remain under `~/.nexus-hub/native-ui/`. A normal editor reload loads newly installed registrations and menu changes. Native process readback, adapter availability and visible picker behavior are distinct checks; see the [repair evidence](../../docs/releases/v4/v4.15/development/settings-portability-repair.md).

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

Fresh installations start with Medium effort, Fast mode off, and Open Codex in tabs on. Existing preference files are preserved during upgrades. The Extensions section groups settings by provider. Restart Codex uses its native app-server lifecycle, waits for initialization, and keeps its tabs open. Restart Claude Code restarts idle Claude session processes and schedules busy sessions to restart after their current turn. Neither restart action reloads the window or restarts the shared extension host. A Refresh Codex Tab button beside History rebuilds the current panel when its native refresh adapter is available; otherwise it offers a confirmed Codex-only restart. Refreshing replaces the composer, so send or copy an unsent draft first. Codex restart may interrupt running Codex requests; saved conversations are retained.

## Usage Alerts

Usage warning panels dismiss automatically after 10 seconds. Nexus Hub Settings has a prominent All usage alerts switch scoped to the current editor. VS Code also shows separate Claude Code, Codex, and GitHub Copilot switches. Cursor and Antigravity each show only their single master switch. The master switches only that editor's providers together; a mixed state indicates that only some providers are enabled. Individual choices are shared across local editors in `~/.nexus-hub/usage-alerts.json` and default to enabled. Turning an alert off closes its current warning and suppresses future usage warnings, including fallback urgency notifications. Usage polling, taskbar colors, connection errors and explicit command results remain available.

## Editor Controls

Claude Code and Codex restart controls and the Codex tabs preference appear only in VS Code. Cursor and Antigravity omit the Extensions section. Fast mode is disabled with an availability note in Antigravity and in VS Code when neither Claude Code nor Codex is installed. Cursor retains Fast mode. A disabled control preserves the saved shared preference.

The split route can be qualified in an isolated VS Code extension host with `scripts/codex-split-live.js` as the extension test entry point. It requires the real Codex extension in the private extensions directory and explicit `NEXUS_SPLIT_SOURCE` and `NEXUS_SPLIT_WORK` fixture paths; it opens no conversation prompt and never replaces the live user profile.

## Restore Agent Split

Off by default. Turn on `nexusHubSettings.restoreAgentSplit` ("Restore Agent Split" in VS Code Settings) if your Claude Code tab and Codex tab sit side by side and a restart brings them back in one editor group.

- **What it remembers:** while the setting is on and the workspace is trusted, Settings records, in this workspace's extension storage, whether the Claude Code and Codex tabs are in different editor groups and which one is on the right. It reads tabs through the public Tab Groups API (a Claude Code webview panel and the `chatgpt.conversationEditor` custom editor) and stores no tab content.
- **What it does on startup:** if both agents come back in a single group and the remembered layout was split, it waits until the tabs have stopped changing for three seconds, selects the right-hand agent's tab, and runs VS Code's own Move Editor into Right Group command, then returns focus to the original group. It runs once per window start, gives up after 60 seconds if one agent never appears, and does nothing if a tab cannot be selected.
- **What it never does:** close, reopen or edit a tab, patch Claude Code or Codex, touch another setting, or act in an untrusted workspace. A merge you make yourself during a session is recorded as your choice and is not undone at the next start.
- **Limits:** only one tab per agent moves, a tab in position 10 or later in its group cannot be selected by index and is skipped, and the layout is stored per workspace, not per window. If another extension moves tabs after Settings has acted, it is not corrected a second time.
- **Qualification:** `scripts/restore-split-live.js` runs ordinary VS Code windows in a private profile with the real Claude Code and Codex extensions and the packaged `.vsix`. It builds the split, forces the merge, reopens the window with the setting on and with it off, and checks the first restores the split while the second leaves the merge alone. It requires a new `--work` directory and never touches the live profile.
