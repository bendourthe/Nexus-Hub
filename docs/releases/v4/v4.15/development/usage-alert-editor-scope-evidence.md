# Usage Alert Editor Scope

Nexus Hub 0.8.1 limits usage-alert controls and master writes to the current editor. This record supports next-release inclusion; integration and publication remain pending.

## Behavior

- VS Code displays one master and individual Claude Code, Codex and GitHub Copilot switches.
- Cursor displays one master for Cursor, with no individual switch list.
- Antigravity displays one master for Gemini / Antigravity, with no individual switch list.
- The master changes only its editor's providers in the shared preference file. It preserves all other editor preferences and unrelated keys.
- Ten-second warning expiry, warning suppression, taskbar colors and the previously verified effort/recovery behavior are unchanged.

## Verification

- `npm test -- --reporter=json --outputFile=<qualification>/scoped-tests.json`: 420 passed, one skipped, zero failures.
- `npm run compile --silent`: passed.
- `npm run package --silent -- --out <qualification>/nexus-hub-settings-0.8.1.vsix`: passed; package-content verification passed with 35 required files.
- Chromium exercised the shipped panel.js and panel.css against the compiled model and preference writer in a disposable home. All three editor scopes rendered the expected controls; master off/on preserved other editors' values; the VS Code individual switch produced a mixed master. No browser runtime errors occurred.
- Browser screenshots and geometry assertions passed at widths 180 and 390. The functional-verification detector passed at widths 180, 390 and 900 for each self-contained rendered model, with zero findings.
- VS Code, Cursor and Antigravity each registered 0.8.1. All 35 package payload files matched each installed copy; installer metadata was excluded from package.json comparison.
- Existing user windows were not reloaded. Editor-specific presentation was exercised in Chromium with each actual host-name mapping, not claimed as a new native editor session proof.

## Artifacts

Local qualification root: `C:/Users/you/Documents/nx-usage-alerts-qualification`.

- `scoped-tests.json`
- `scoped-browser-081/results.json`, screenshots and detector JSON
- `scoped-install-081.json`
- `scoped-payloads-081.json`
- Package SHA256: `66ee975c76a5302dde77975824b8034e1b544ca49b4f3dfe5e61e14db8f27a15`

## Release Inclusion

The next release must include Nexus Hub 0.8.1 or newer plus all five monitor updates from the same feature branch. The [progress tracker](../../../../todos.md) retains the pending integration and installer checks. Reload each open editor to activate this installed update.

## Editor Capabilities

Nexus Hub 0.8.2 adds explicit editor capabilities. Cursor and Antigravity omit the entire Extensions section, including Claude Code and Codex restart buttons and the Codex tabs preference. VS Code retains these controls. Antigravity disables Fast mode with "Not available in this editor"; VS Code also disables Fast mode when neither supported provider extension is installed. Cursor retains Fast mode. Both the disabled control and the controller prevent unsupported Fast writes, preserving the existing shared preference.

- Focused verification: `npx vitest run test/panel.test.ts test/controller.test.ts test/editorCapabilities.test.ts --reporter=json --outputFile=<qualification>/capability-tests-082-final.json` passed all 96 tests.
- Chromium exercised each editor model using the compiled capability mapper and shipped panel. Cursor and Antigravity had no Extensions section; Antigravity's Fast control was disabled with the correct note; existing alert controls and scoped writes still passed. Zero browser errors. Native editor windows were not reloaded or claimed as live-tested in this update.
- Geometry detector passed at widths 180, 390 and 900 for all three editor models; screenshots are in `capability-browser-082/` under the same qualification root.
- Package verification passed for all 36 required files. Version 0.8.2 registered in VS Code, Cursor and Antigravity; 36/36 payloads matched each copy.
- Package SHA256: `6ced95cae86d8375e3e572fc56c5074ccf682fc20cad6d4148260cfbe2871458`.
- Installation and payload receipts: `capability-install-082.json` and `capability-payloads-082.json`.
- The next-release requirement is now 0.8.2 or newer. Integration and publication remain pending.
