# Nexus-Hub Settings

A compact panel for VS Code, Cursor and Antigravity with one shared effort selector and five Nexus-Hub guardrail switches. Changes save automatically through the `nexus-hub settings` engine and are read back before the panel reports the result. The original cyan Nexus logo identifies the extension, dashboard, sidebar and status-bar entry.

## What it controls

- **Default effort**: one preference, applied to supported native settings for new sessions.
- **Git safety**: dangerous Git commands and protected-branch checks.
- **Secret scanning**: credential checks before writes.
- **Protect my edits**: checks before overwriting user changes.
- **Large-file warnings**: advisory warnings for unusually large writes.
- **Block Git bypass flags**: checks for skipping hooks or commit signing.

Effort applies to new sessions; guardrail switches are read on the next hook invocation, including in full-access mode. Claude Max maps to native `max`; Ultra enables native Ultracode with `xhigh` effort. Codex maps both to its compatible `xhigh`, with a lower mapping when a model requires it. Supported defaults and existing effort overrides are synchronized with the saved preference. Copilot, native Cursor and native Antigravity effort remain unavailable through a verified public setting; managed policies and existing session state remain outside user-default control. Native model and approval controls remain available through the CLI rather than separate selectors in the panel.

## Status bar

The status bar shows `High (effort)` by default, or `Nexus Settings: High (effort)` when `nexusHubSettings.compactStatusBar` is off. The compact native Markdown hover shows the effort scale, configured guardrail count and named guardrail states. It links to Settings and, when Codex is installed, a fresh Codex agent. The panel uses a rounded stepped control without a duplicate selected-value label. Unsupported effort controls are listed in the footer. A warning means an available setting failed to synchronize or a guardrail is unavailable. Click the status bar to open Settings. Existing Codex conversations and drafts retain their effort choice. Use New Codex agent after changing the default to open a fresh composer with the current configuration.

## What the panel shows

One autosaving stepped effort control, five switches and a short application status. The effort control and enabled guardrails use the logo's cyan palette. Use arrow keys, Home or End to select effort, or click a labeled step. The main view contains no model fields, platform selectors, diagnostic tables or scenario previews. Failed changes expose technical details only when needed. Keyboard focus survives a save, and changes are announced to screen readers.

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
