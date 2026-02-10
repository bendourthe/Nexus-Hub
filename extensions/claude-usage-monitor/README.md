# Claude Usage Monitor

A lightweight VS Code extension that displays your Claude Code usage limits in the status bar and provides smart model-switching recommendations.

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

Once activated, a status bar item appears on the right side:

```
$(check) Claude: --%
```

Click it to enter your current usage data from `claude.ai/settings/usage`.

After entering data, it shows:

```
$(check) Claude: 12% S | 5% W     (green, healthy)
$(warning) Claude: 65% S | 45% W  (yellow, moderate)
$(flame) Claude: 85% S | 78% W    (orange, high)
$(error) Claude: 95% S | 88% W    (red, critical)
```

Hover for a detailed tooltip with breakdown and recommendations.

### Commands

Open the Command Palette (`Ctrl+Shift+P`) and search:

| Command | Description |
|---|---|
| `Claude Usage: Update` | Enter your current usage percentages |
| `Claude Usage: Recommend Model` | View model recommendation and tips |
| `Claude Usage: Clear Data` | Reset all stored usage data |

### Settings

Open Settings (`Ctrl+,`) and search "Claude Usage":

| Setting | Default | Description |
|---|---|---|
| `claudeUsage.currentModel` | `opus-4.6` | Your default Claude model |
| `claudeUsage.reminderInterval` | `15` | Minutes between refresh reminders |
| `claudeUsage.showInStatusBar` | `true` | Show/hide the status bar item |

## How Recommendations Work

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

Usage data is stored in VS Code's `globalState` (persists across sessions, local to your machine). No data is sent externally. Use `Claude Usage: Clear Data` to remove all stored data.
