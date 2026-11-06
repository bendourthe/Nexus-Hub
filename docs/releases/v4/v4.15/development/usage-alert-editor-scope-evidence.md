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

Local qualification root: `C:/Users/BEDOURTHE/Documents/nx-usage-alerts-qualification`.

- `scoped-tests.json`
- `scoped-browser-081/results.json`, screenshots and detector JSON
- `scoped-install-081.json`
- `scoped-payloads-081.json`
- Package SHA256: `66ee975c76a5302dde77975824b8034e1b544ca49b4f3dfe5e61e14db8f27a15`

## Release Inclusion

The next release must include Nexus Hub 0.8.1 or newer plus all five monitor updates from the same feature branch. The [progress tracker](../../../../todos.md) retains the pending integration and installer checks. Reload each open editor to activate this installed update.
