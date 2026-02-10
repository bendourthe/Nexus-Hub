# Claude Usage Monitor

A VS Code extension that automatically monitors your Claude Code API usage limits, displays them in the status bar with a rich SVG tooltip, and provides a full dashboard with model-switching recommendations.

## Features

- **Auto-fetch**: Reads your OAuth token from `~/.claude/.credentials.json` and fetches usage data from the Anthropic API
- **Status bar**: Shows session and weekly usage percentages with a custom Claude icon
- **SVG tooltip**: Hover for theme-aware progress bars showing per-metric breakdown with reset timers
- **Dashboard panel**: Click for a full usage dashboard with model recommendations and optimization tips
- **Manual fallback**: Enter usage data manually when API credentials are unavailable
- **Auto-refresh**: Configurable interval (default 15 min) to keep data current

## Setup

1. Open a terminal in this directory:
   ```powershell
   cd extensions/claude-usage-monitor
   ```

2. Install dependencies:
   ```powershell
   npm install
   ```

3. Compile:
   ```powershell
   npm run compile
   ```

4. Install locally (one of these methods):

   **Option A: VSIX package**
   ```powershell
   npm run package
   ```
   Then in VS Code: Extensions sidebar > "..." menu > "Install from VSIX" > select the generated `.vsix` file.

   **Option B: Development mode**
   Open this folder in VS Code, press `F5` to launch the Extension Development Host.

## Usage

### Status Bar

Once activated, a status bar item appears on the right side showing your current usage:

```
$(claude-icon) Claude Usage: 12% (current) 5% (week)
```

- The extension auto-fetches usage data on startup using your Claude OAuth credentials
- **Hover** for a detailed SVG tooltip with progress bars for each metric (session, weekly all-models, weekly Sonnet-only) and reset timers
- **Click** to open the full usage dashboard panel

The status bar background changes color based on urgency:
- No highlight: Healthy (0-50%)
- Yellow: Moderate (51-75%)
- Red: High/Critical (76-100%)

### Commands

Open the Command Palette (`Ctrl+Shift+P`) and search:

| Command | Description |
|---|---|
| `Claude Usage: Dashboard` | Open the full usage dashboard panel |
| `Claude Usage: Refresh` | Fetch latest usage data from the API |
| `Claude Usage: Manual Update` | Enter usage percentages manually |
| `Claude Usage: Recommend Model` | View model recommendation and tips |
| `Claude Usage: Clear Data` | Reset all stored usage data |

### Settings

Open Settings (`Ctrl+,`) and search "Claude Usage":

| Setting | Default | Description |
|---|---|---|
| `claudeUsage.currentModel` | `opus-4.6` | Your default Claude model |
| `claudeUsage.autoFetch` | `true` | Auto-fetch usage data from Claude API on startup and at intervals |
| `claudeUsage.refreshInterval` | `15` | Minutes between automatic usage data refreshes (5-120) |
| `claudeUsage.showInStatusBar` | `true` | Show/hide the status bar item |

## How It Works

### Auto-Fetch

The extension reads the OAuth access token from `~/.claude/.credentials.json` (written by Claude Code) and calls:

```
GET https://api.anthropic.com/api/oauth/usage
Authorization: Bearer {token}
anthropic-beta: oauth-2025-04-20
```

The API returns `five_hour` (session), `seven_day` (weekly all-models), `seven_day_sonnet`, `seven_day_opus`, and `extra_usage` fields, each with `utilization` (0-100) and `resets_at` (ISO 8601 timestamp).

If credentials are missing or expired, the extension falls back gracefully and you can use `Claude Usage: Manual Update` instead.

### Model Recommendations

The extension classifies your usage into four levels:

| Usage % | Level | Action |
|---|---|---|
| 0-50% | Low | Continue current model freely |
| 51-75% | Moderate | Be mindful of task complexity |
| 76-90% | High | Model switch recommended |
| 91-100% | Critical | Immediate switch or wait for reset |

Based on your current model and usage level, it recommends:

- **Opus users at high usage**: Switch to Sonnet 4.5 for routine tasks
- **Sonnet users at high usage**: Switch to Haiku 4.5 for simple tasks
- **Sonnet-only limit high**: Switch to Opus or Haiku (neither counts against Sonnet limit)
- **Session near capacity**: Wait for the session reset (typically a few minutes)

## Data Storage

Usage data is stored in VS Code's `globalState` (persists across sessions, local to your machine). The only external call is to the Anthropic API to fetch your own usage data. Use `Claude Usage: Clear Data` to remove all stored data.
