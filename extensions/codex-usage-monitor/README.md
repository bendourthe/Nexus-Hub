# Codex Usage Monitor

A VS Code extension that monitors your Codex (ChatGPT / OpenAI) usage limits, displays them in the status bar with a rich SVG tooltip, and provides a full dashboard with pacing recommendations.

> Looking to monitor Claude Code (Anthropic) usage? That lives in the separate **Claude Usage Monitor** extension (`nexus-hub.claude-usage-monitor`). This extension is Codex-only, and the two install and run side by side without collision.

## Features

- **Auto-fetch**: Reads your local Codex-app OAuth token and fetches usage from your own ChatGPT account
- **Status bar**: Shows session and weekly usage percentages with the Codex icon
- **SVG tooltip**: Hover for theme-aware progress bars (in Codex periwinkle, `#5244BB`) showing rate-limit windows and monthly Extra Credits usage with reset timers
- **Dashboard panel**: Click for a full usage dashboard with your plan tier, extra rate-limit windows, an Extra Credits progress bar, and throttle / pacing recommendations
- **Fail-soft**: When credentials are missing or the endpoint is unavailable, shows "usage unavailable" and keeps cached data rather than erroring
- **Auto-refresh**: Configurable interval (default 10 min) to keep data current

## Setup

1. Open a terminal in this directory:
   ```powershell
   cd extensions/codex-usage-monitor
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
$(codex-icon) Codex Usage: 12% (current) 5% (week)
```

- The extension auto-fetches usage data on startup using your Codex-app OAuth credentials
- **Hover** for a detailed SVG tooltip with progress bars for the tracked rate-limit windows and, when available, monthly Extra Credits usage
- **Click** to open the full usage dashboard panel

The status bar background changes color based on urgency:

- No highlight: Healthy (0-50%)
- Yellow: Moderate (51-75%)
- Red: High/Critical (76-100%)

### Commands

Open the Command Palette (`Ctrl+Shift+P`) and search:

| Command | Description |
|---|---|
| `Codex Usage: Dashboard` | Open the full usage dashboard panel |
| `Codex Usage: Refresh` | Fetch latest usage data from the endpoint |
| `Codex Usage: Recommend` | View recommendation and tips |
| `Codex Usage: Clear Data` | Reset all stored usage data |
| `Codex Usage: Settings` | Open the thresholds and colors settings panel |

### Settings

Open Settings (`Ctrl+,`) and search "Codex Usage":

| Setting | Default | Description |
|---|---|---|
| `codexUsage.authPath` | `""` | Optional path to the Codex app credential file. Empty uses `CODEX_HOME/auth.json` or `~/.codex/auth.json` |
| `codexUsage.autoFetch` | `true` | Auto-fetch usage data on startup and at intervals |
| `codexUsage.refreshInterval` | `10` | Minutes between automatic usage data refreshes (1-120) |
| `codexUsage.showInStatusBar` | `true` | Show/hide the status bar item |
| `codexUsage.thresholds.*` | `50` / `75` / `95` | Moderate / High / Critical urgency thresholds |
| `codexUsage.thresholdMetric` | `highest` | Which metric the thresholds evaluate against |

## How It Works

### Auto-Fetch

The extension reads the OAuth access token written by the Codex app and makes a single authenticated request:

```
GET https://chatgpt.com/backend-api/wham/usage
Authorization: Bearer {access_token}
chatgpt-account-id: {account_id}
Accept: application/json
```

The `chatgpt-account-id` header is omitted for a synthetic (`email_` / `local_`) account id. The response's primary and secondary rate-limit windows map to the session and weekly metrics; detailed monthly credit data maps to the Extra Credits progress bar, while simpler balance-only payloads retain the text summary. The plan type and any additional rate limits appear as extra dashboard rows. The endpoint is undocumented, so the payload is parsed defensively: any parse failure, HTTP error, timeout, or missing field yields the fail-soft "usage unavailable" state instead of an error.

The Codex credential is located, most-specific first: the `codexUsage.authPath` setting, then `CODEX_HOME/auth.json` when `CODEX_HOME` is set, otherwise `~/.codex/auth.json`. Set `codexUsage.authPath` if your Codex app stores its credential elsewhere.

**Caveat**: `wham/usage` is an undocumented ChatGPT backend endpoint and may change without notice. The extension fails soft (shows "usage unavailable", keeps cached data) rather than erroring if the endpoint or credential is unavailable.

### Recommendations

Codex has no cheaper model tier to switch to, so recommendations are framed as pacing guidance keyed to the same thresholds:

| Usage % | Level | Action |
|---|---|---|
| 0-50% | Low | Keep working normally |
| 51-75% | Moderate | Throttle usage: batch prompts, shorter sessions |
| 76-95% | High | Pause non-essential tasks until the reset |
| 95-100% | Critical | Wait for the reset, or rotate to another Codex account |

The thresholds (50 / 75 / 95) and the per-bucket guidance can be customized in `Codex Usage: Settings`. Notifications auto-dismiss after `codexUsage.notificationTimeoutSeconds` (default 12 seconds) so they never stack while VS Code is in the background.

## Data Storage

Usage data is stored in VS Code's `globalState` (persists across sessions, local to your machine), under Codex-specific keys that do not collide with the Claude Usage Monitor extension. The only external call is to `chatgpt.com/backend-api/wham/usage` to fetch your own usage data; the OAuth token is read locally and never transmitted anywhere except back to your own account. Use `Codex Usage: Clear Data` to remove all stored data.

## Development

```powershell
npm ci
npm run compile
npm test
npm run test:coverage
npm run package
```

`npm run test:coverage` enforces at least 80% line and statement coverage plus 75% branch and function coverage.
