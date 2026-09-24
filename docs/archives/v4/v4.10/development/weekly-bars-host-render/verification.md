# v4.10 weekly bars - installed VS Code host verification

This frozen record closes v4.10 MT-2's host-rendering boundary. The account-response mapping and markup tests remain separate evidence; this run proves that a packaged extension paints the two weekly bars in a running VS Code host.

## Test boundary

- Date: 2026-09-24.
- Source revision: `a92f0a3756388433f7be75b017ae8ac129351e4a` (`origin/develop` before this evidence change).
- Host: Windows VS Code 1.139.0, isolated user-data and extensions directories under a disposable temporary profile.
- Artifact: `nexus-hub.claude-usage-monitor@0.10.0`, built with `npm ci`, `npm run compile`, `npm test`, and `npm run package`; VSIX SHA-256 `7e9ca29545ac79f5d3fb5ebdf6d2756f4cbe9984d0f09f8535d6e587698e1ba6`.
- Fixture: synthetic extension global state only, with current session 12%, all-models weekly 34%, Fable weekly 56%, and current model `claude-fable-5`. `claudeUsage.autoFetch` was false; no account credential or live API request was used.

## Observed result

- The VSIX installed successfully into the isolated extensions directory. The running workbench showed `Claude Usage: 12% (current) 34% (week)` in the status bar, retaining the intended omission of the scoped metric from status text.
- Hovering that status item painted Current Session 12%, Weekly (All Models) 34%, and Weekly (Fable) 56%, with three visible SVG fills and no clipping. The [hover screenshot](status-hover-vsix.png) is from the installed VSIX, not extension-development mode.
- Opening `Claude Usage: Dashboard` through the command palette painted the same three labels and fills. The [dashboard screenshot](dashboard-scoped-vsix.png) is from the installed VSIX.
- On the dashboard's 449-pixel tracks, the orange fills measured 54, 153, and 252 pixels, matching 12.0%, 34.1%, and 56.1%. On the hover's 281-pixel tracks, they measured 34, 95, and 155 pixels, matching 12.1%, 33.8%, and 55.2%. The main workbench reported no page or console errors during these interactions.
- The extension's six test files passed all 20 tests before packaging. These tests cover data mapping and markup behavior; the screenshots and measured paint close the separate host-rendering risk.

This is not evidence that a live account currently returns a scoped limit, that account fetching works in this disposable profile, or that every VS Code version renders identically. The earlier account-response mapping evidence remains the source for account-label behavior. No production source file changed for this closure.
