# Nexus Hub 0.7.4 Panel Hierarchy

Nexus Hub 0.7.4 makes main settings sections visually distinct and places provider icons beside the Claude Code and Codex headings. Version remains at the bottom so frequently used controls stay first.

## Changes

- Main section dividers use a two-pixel line at 34 percent of the theme foreground color. Inner dividers remain one pixel at 16 percent. Forced-color mode uses the system text color for the main line.
- Claude Code appears before Codex. Each heading has an 18-pixel decorative provider icon; the readable heading remains its accessible name. Claude uses its orange mark and Codex follows the foreground color in both themes.
- Provider assets are bundled locally and require no network requests. All 22 compiled runtime modules are byte-for-byte identical to 0.7.3.

## Verification

- Compilation passed. Existing panel and packaging checks passed all 48 tests. Package verification passed with 34 required payload files.
- Native VS Code visual inspection at the normal sidebar width confirmed the stronger main dividers, subtle inner line, icons, provider order and Version placement in both dark and Light Modern themes.
- Installed 0.7.4 in VS Code, Cursor and Antigravity. All 34 package payloads matched in every host; installer-added manifest metadata was excluded from the semantic manifest comparison.
- Artifact: `C:/Users/you/Documents/nx-settings074-qualification/nexus-hub-settings-0.7.4.vsix`.
- SHA-256: `f2fa6da292c93bc30f1fdf0e5876558ae061a5a9c2a46eeb01bb872e423ba25a`.
- Working editor windows and saved effort/Fast preferences were unchanged. The visual check used a disposable profile.

## Release Inclusion

The next release must include extension 0.7.4 or newer and the complete settings feature branch, including the runtime and hook dependencies recorded in [the provider recovery evidence](settings-073-recovery-evidence.md). Integration and publication remain pending; this update was installed locally only.
