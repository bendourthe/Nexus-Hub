# README Platform Refinement

This record covers the requested README structure, complete Markdown cheatsheet, workflow pacing, simultaneous usage-monitor tour, and realistic platform illustrations for v4.15.0. It records local documentation verification and the remaining integration boundary.

## Changes

- Replaced the eight-card command animation with all 24 HTML-guide command cards in seven collapsible Markdown groups. Scopes, flags, examples, and notes are generated from the guide. The handoff description follows the current chat-only contract, with a file written only when requested. `/skills list` remains the installed command reference.
- Organized IDE controls as a table, handoff instructions as numbered steps, usage actions as bullets, and platform coverage as a table covering VS Code with Claude Code/Codex/Copilot, Cursor, Antigravity, Claude desktop, and ChatGPT desktop.
- Preserved the original workflow story, cursor, and spotlight. Removed the half-speed timeline compression and extended each final result hold to 4.8 seconds.
- Replaced sequential usage scenes with three portrait desktop crops. The pointers approach together; all hovers appear on arrival; a click opens all three original dashboards together.
- Preserved source brand colors in the GIF palette: Claude `#D97757`, Codex `#5244BB`, and Copilot `#0E8A85`. App title bars and taskbar artwork remain above the handoff dimming layer.
- Added Cursor and Antigravity illustrations using native layout references and their installed app artwork. The actual settings webview omits VS Code-only extension controls, disables Fast in Antigravity, and shows one alert master switch per IDE.
- Kept one latest release section. The earlier command GIF/poster remain historical assets and are no longer referenced by the README.

## Verification

| Check | Result |
| --- | --- |
| Existing settings and handoff browser exercises | 121 passed; no browser errors |
| New platform, usage, Markdown, link, color, and interaction checks | 263 passed; no browser errors |
| Responsive widths | 1440, 1000, 768, and 390 pixels |
| Cheatsheet source parity | Exact generated Markdown match; seven groups and 24 commands |
| Markdown rendering | GitHub-flavored Markdown parsed; dark and light screenshots inspected |
| Pointer behavior | Five distinct approach positions; hovers hidden during approach and visible together on arrival |
| Dashboard behavior | Actual sample status-button clicks open the shipped dashboard HTML |
| Offline preview | Both showcase tours load using the checked-in component payload; overview has no missing images |
| Exported brand colors | Exact Claude color in handoff GIF/PNG; exact Codex and Copilot colors in usage GIF/PNG |
| Source checks | Ruff passed for both new Python adapters; Python compilation and JavaScript syntax checks passed |
| Patch checks | `git diff --check` passed |
| Runtime boundary | No changes to extension implementations, original guide, or original training sources |

Local receipts are under `C:/Users/you/Documents/nx-usage-alerts-qualification/`: `readme-platform-checks/results.json`, `readme-platform-checks/final-offline.json`, and `readme-guided-checks/results.json`. The browser exercises use isolated sample data and do not start agents or contact provider accounts. Native Cursor, Antigravity, and Claude windows were inspected as visual references; no native working-session screenshot was added to the repository.

## Media

| Tour | Frames | Duration | Bytes |
| --- | --- | --- | --- |
| Installation, retained | 73 | 30.24 s | 897135 |
| Workflow | 271 | 217.33 s | 2119098 |
| Desktop handoff | 68 | 41.70 s | 359415 |
| Settings, retained | 54 | 38.80 s | 242988 |
| Parallel usage monitors | 9 | 23.65 s | 163755 |
| Cursor and Antigravity | 14 | 23.40 s | 106440 |

Every current GIF has a static poster and is below 4 MiB. The usage frame count reflects merged identical holds; cursor movement, click indication, hover arrival, and dashboard transitions remain visible.

## Reproduction

From the repository root in Windows PowerShell, with the dependencies listed in [README Visuals](../../../../../assets/readme/README.md), choose a new output directory:

```powershell
python scripts/render_readme_demos.py --output "$env:TEMP/nexus-hub-readme-platform-refinement"
```

The renderer exports six tours, posters, keyframes, component payload, full Markdown cheatsheet, and a report. It refuses an existing output directory. Distributed files are replaced only after inspection and edit-guard checks.

## Release Inclusion

These documentation changes are local on `feat/settings-redesign-20261104`. Include the branch's complete extension work and current README media in v4.15.0 as tracked in [the progress dashboard](../../../../todos.md). Integration, remote validation, and publication remain pending. This documentation exercise does not establish new native-provider functionality or release qualification.
