# Gemini Usage Monitor

An extension for the Google Antigravity IDE that monitors your Antigravity model quotas (the Gemini group and the Claude and GPT group, each with a 5-hour and a weekly limit), shows them in the status bar with a rich SVG tooltip, raises threshold alerts, and provides a full dashboard with pacing recommendations.

> This extension installs into **Antigravity only**. The Nexus-Hub installer passes it to the Antigravity IDE's own command-line launcher and never to VS Code or Cursor. The sibling monitors (`nexus-hub.claude-usage-monitor`, `nexus-hub.codex-usage-monitor`, `nexus-hub.copilot-usage-monitor`, `nexus-hub.cursor-usage-monitor`) cover the other tools and share this one's design.

## Features

- **Local auto-fetch**: Reads the same quota summary that Antigravity's **Settings > Models > Models & Usage** screen shows, straight from Antigravity's local language server on `127.0.0.1`. No sign-in, token file, or setup step.
- **Status bar**: Shows the Gemini group's 5-hour and weekly usage with the Antigravity icon.
- **SVG tooltip**: Hover for theme-aware progress bars (in Google blue, `#4285F4`) for every window of every model group, with reset timers.
- **Dashboard panel**: Click for a full usage dashboard with your plan (for example "Google AI Pro"), both model groups, and throttle / pacing / switch-group recommendations.
- **Alerts**: A warning card opens in the sidebar the first time a threshold is crossed, and closes itself after one minute.
- **Fail-soft**: When the language server is not running yet or the response has no usable data, the monitor keeps cached data and explains what to do instead of erroring.

## Setup

The Nexus-Hub installer builds and installs this extension automatically when it finds the Antigravity IDE. To build it by hand:

1. Open a terminal in this directory:

    ```powershell
    cd extensions/gemini-usage-monitor
    ```

2. Install dependencies and compile:

    ```powershell
    npm ci
    npm run compile
    ```

3. Package and install into Antigravity (the launcher is `antigravity-ide` in recent builds and `antigravity` in older ones):

    ```powershell
    npm run package
    antigravity-ide --install-extension gemini-usage-monitor-0.1.0.vsix --force
    ```

## Usage

### Status Bar

Once activated, a status bar item appears on the right side showing your Gemini usage:

```
$(gemini-icon) Gemini Usage: 12% (current) 5% (week)
```

Percentages are **used**, matching every other Nexus-Hub monitor. Antigravity's own screen shows **remaining**, so 100% remaining there reads as 0% here.

- **Hover** for the tooltip with every model group's windows.
- **Click** to open the full usage dashboard panel.

The status bar background changes color based on urgency:

- No highlight: Healthy (below 50%)
- Yellow: Moderate (50% to 74%)
- Orange / Red: High / Critical (75% and above)

### Commands

Open the Command Palette (`Ctrl+Shift+P`) and search:

| Command | Description |
|---|---|
| `Gemini Usage: Dashboard` | Open the full usage dashboard panel |
| `Gemini Usage: Refresh` | Ask Antigravity to re-read your quotas, then update |
| `Gemini Usage: Recommend` | View recommendation and tips |
| `Gemini Usage: Clear Data` | Reset all stored usage data |
| `Gemini Usage: Settings` | Open the thresholds and colors settings panel |
| `Gemini Usage: Save Raw Usage Response` | Save one redacted copy of the quota response under the extension's global storage (opt-in; see below) |

### Settings

Open Settings (`Ctrl+,`) and search "Gemini Usage":

| Setting | Default | Description |
|---|---|---|
| `geminiUsage.autoFetch` | `true` | Read usage on startup and at intervals |
| `geminiUsage.refreshInterval` | `10` | Minutes between automatic refreshes (1-120) |
| `geminiUsage.showInStatusBar` | `true` | Show/hide the status bar item |
| `geminiUsage.compactStatusBar` | `true` | Drop the "Gemini Usage: " label |
| `geminiUsage.thresholds.*` | `50` / `75` / `95` | Moderate / High / Critical urgency thresholds |
| `geminiUsage.thresholdMetric` | `highest` | `highest` watches every window of every model group; `session` and `weekly` watch the Gemini group only |
| `geminiUsage.colors.*` | `#cca700` / `#f0643c` / `#e05555` | Status bar colors per level, or `none` |
| `geminiUsage.notificationTimeoutSeconds` | `12` | How long refresh notifications stay on screen |

The thresholds and colors are application-scoped: they are read from your user settings only, so a workspace's `.vscode/settings.json` cannot change them. `refreshInterval` is clamped to 1-120 minutes.

## How It Works

### Auto-Fetch

Antigravity runs a local language server that backs its own Models & Usage screen. The monitor:

1. Finds that server among your own running processes (one PowerShell `Get-CimInstance` call on Windows; `ps` and `lsof` on macOS and Linux), keeping only the server that belongs to this Antigravity install and preferring the one owned by the main process, which is the one the settings screen reads.
2. Reads the CSRF token the server was launched with from its command line, and its listening loopback ports.
3. Sends two Connect-protocol JSON requests to `127.0.0.1`: `RetrieveUserQuotaSummary` for the model groups and `GetUserStatus` for the plan name. A port is tried over plain loopback HTTP first, then over HTTPS verified against the certificate Antigravity ships.

The endpoint is cached and rediscovered automatically when Antigravity restarts its server. A manual refresh passes `forceRefresh`, which makes Antigravity re-read your quota from Google exactly as the refresh arrow on its own screen does; automatic refreshes read Antigravity's cached figures.

The Gemini group is the headline pair (status bar, "Current Session" and "Weekly"). Every other group appears as extra rows in the tooltip and dashboard and counts toward alerts when `thresholdMetric` is `highest`.

**Caveat**: the language server's RPC interface is internal to Antigravity and may change between releases. Field names were recorded from Antigravity IDE 2.5.5 (October 2026); the monitor reads them defensively and fails soft if they change.

### Privacy boundary

- The monitor makes **no** internet requests of its own. Every request goes to `127.0.0.1`.
- The CSRF token is held in memory only. It is never logged, stored, or shown.
- The monitor reads only quota and plan data. It cannot change your plan, turn on AI credit overages, or spend credits.

### Recommendations

Antigravity limits are per model group, so when one group runs low and another still has headroom, the advice is to switch the agent to that group:

| Usage % | Level | Action |
|---|---|---|
| Below 50% | Low | Keep working normally |
| 50% to 74% | Moderate | Throttle usage: batch prompts, shorter sessions, or switch model group |
| 75% to 94% | High | Focus on essential tasks until the reset, or switch model group |
| 95% and above | Critical | Pause non-essential work until the reset, or switch model group |

### Save Raw Usage Response

`Gemini Usage: Save Raw Usage Response` sends the same loopback calls as a refresh and writes `raw-usage-response.json` under the extension's global storage. Keys, numbers, booleans, dates, and short lowercase words are kept; every other string (names, emails, ids, group descriptions) is replaced with a placeholder. Nothing is uploaded.

## Data Storage

Usage data is stored in the editor's `globalState` (local to your machine) under Gemini-specific keys. Use `Gemini Usage: Clear Data` to remove it.

## Development

```powershell
npm ci
npm run compile
npm test
npm run test:coverage
npm run package
```

`npm run test:coverage` enforces at least 80% line and statement coverage plus 75% branch and function coverage. To regenerate the status-bar glyph font and the package icon from `icons/google-antigravity.svg`:

```powershell
npm install --no-save --package-lock=false sharp
npm run generate:icons
```
