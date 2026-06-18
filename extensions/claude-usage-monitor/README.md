# Claude Usage Monitor

A VS Code extension that automatically monitors your Claude Code API usage limits, displays them in the status bar with a rich SVG tooltip, and provides a full dashboard with model-switching recommendations.

## Features

- **Auto-fetch**: Reads your Claude Code OAuth token (from `~/.claude/.credentials.json` on Windows/Linux, or the macOS Keychain) and fetches usage data from the Anthropic API
- **Status bar**: Shows session and weekly usage percentages with a custom Claude icon
- **SVG tooltip**: Hover for theme-aware progress bars showing per-metric breakdown with reset timers
- **Dashboard panel**: Click for a full usage dashboard with model recommendations and optimization tips
- **Manual fallback**: Enter usage data manually when API credentials are unavailable
- **Auto-refresh**: Configurable interval (default 10 min) to keep data current

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
- **Hover** for a detailed SVG tooltip with progress bars for each metric (session, weekly all-models, weekly Sonnet-only, weekly Opus, extra credits) and reset timers
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
| `Claude Usage: Recommend Model` | View model recommendation and tips |
| `Claude Usage: Clear Data` | Reset all stored usage data |

### Settings

Open Settings (`Ctrl+,`) and search "Claude Usage":

| Setting | Default | Description |
|---|---|---|
| `claudeUsage.autoFetch` | `true` | Auto-fetch usage data from Claude API on startup and at intervals |
| `claudeUsage.refreshInterval` | `10` | Minutes between automatic usage data refreshes (5-120) |
| `claudeUsage.showInStatusBar` | `true` | Show/hide the status bar item |

## How It Works

### Auto-Fetch

The extension reads the OAuth access token written by Claude Code and calls the usage API. The token location is platform-dependent:

- **Windows / Linux**: `~/.claude/.credentials.json`
- **macOS**: the login Keychain (generic password, service `Claude Code-credentials`), read via the `security` CLI. macOS Claude Code does not write the JSON file, so the Keychain is the only source there.

The request:

```
GET https://api.anthropic.com/api/oauth/usage
Authorization: Bearer {token}
anthropic-beta: oauth-2025-04-20
```

The API returns `five_hour` (session), `seven_day` (weekly all-models), `seven_day_sonnet`, `seven_day_opus`, and `extra_usage` fields, each with `utilization` (0-100) and `resets_at` (ISO 8601 timestamp).

If credentials are missing or expired, the extension falls back gracefully to cached data.

### Model Recommendations

The extension classifies your usage into four levels:

| Usage % | Level | Action |
|---|---|---|
| 0-50% | Low | Continue current model freely |
| 51-75% | Moderate | Reduce Effort to High or Medium (no model swap yet) |
| 76-95% | High | Switch to Sonnet 4.6 if on Opus, and reduce Effort to High or Medium |
| 95-100% | Critical | Switch to Haiku 4.5 and set Effort to Low to avoid hitting your limit |

The thresholds (50 / 75 / 95) and the per-bucket guidance can be customized in `Claude Usage: Settings`. Notifications auto-dismiss after `claudeUsage.notificationTimeoutSeconds` (default 12 seconds) so they never stack while VS Code is in the background.

Based on your current model and usage level, the dashboard also shows model-specific guidance:

- **Opus users at high usage**: Switch to Sonnet 4.6 for routine tasks
- **Sonnet users at high usage**: Switch to Haiku 4.5 for simple tasks
- **Sonnet-only limit high**: Switch to Opus or Haiku (neither counts against Sonnet limit)
- **Session near capacity**: Wait for the session reset (typically a few minutes)

## Data Storage

Usage data is stored in VS Code's `globalState` (persists across sessions, local to your machine). The only external call is to the Anthropic API to fetch your own usage data. Use `Claude Usage: Clear Data` to remove all stored data.

## Effort Level - Current State & Roadmap

The Claude Code effort level (`xhigh` / `high` / `max` / `medium` / `low`) is a separate configuration surface owned by the Claude Code harness (`~/.claude/settings.json`), not by this extension. As of v0.9.7, this extension **does not** read, display, or manage the effort level.

### Where the effort level is configured today

- Harness template: [catalog/hooks/settings.json](../../catalog/hooks/settings.json) (`effortLevel: xhigh` is the shipped default)
- User override: `~/.claude/settings.json` (written by the installer on first run; edit directly or via the `/model` slash command in a Claude Code session)
- Decision guidance: [prompt-engineering/SKILL.md - Effort-Level Strategy](../../catalog/skills/ai-development/prompt-engineering/SKILL.md#effort-level-strategy)
- Setting reference: [guides/CLAUDE_CODE_SETTINGS_REFERENCE.md - Effort Levels](../../guides/CLAUDE_CODE_SETTINGS_REFERENCE.md)

### Why this extension does not yet surface the effort level

Two concrete blockers were hit in prior attempts:

1. **Cannot read the current effort level reliably.** The Claude Code process does not expose the currently-active effort level through a stable API, file watch, or IPC channel that a VS Code extension can observe. Reading `~/.claude/settings.json` directly returns the configured value but not the value Claude Code has loaded into the current session (they can differ after a `/model` command or mid-session override).
2. **Edits to `~/.claude/settings.json` do not propagate live** to a running Claude Code session. Claude Code reads the file on session start; mid-session edits have no effect. An auto-switching implementation that writes to the file would change the next session's default but not the current session.

Until both blockers are resolved, surfacing the effort level in this extension would be misleading - operators would see a value that may not match what Claude Code is actually using, and an "auto-switch" that writes to `settings.json` would produce no visible change until the next session.

### Intended future behavior (roadmap, not yet implemented)

Target design if the read/live-update blockers are resolved in a future Claude Code release:

- **Display** the current effort level in the status bar tooltip and dashboard.
- **Auto-band switching** based on current usage percentage (opt-in; PROMOTES above the installed `high` default when usage is low, then reduces as usage rises):

  | Usage % | Effort Level |
  |---------|--------------|
  | 0-50%   | `xhigh`      |
  | 51-75%  | `high`       |
  | 76-95%  | `medium`     |
  | 96-100% | `low`        |

  Note: the top-of-band `xhigh` matches the installed Nexus-Hub default. The intent is cost-aware de-escalation - keep the default when usage headroom is plentiful, then step down as the budget tightens. The feature is opt-in so operators who keep `xhigh` across the board are never surprised by automatic de-escalation.

- **Manual override** via a settings-panel control and a Command Palette entry.
- **Opt-in only** - auto-switching is off by default; operators enable it explicitly.

This section will be updated when the upstream blockers have a known path forward.
