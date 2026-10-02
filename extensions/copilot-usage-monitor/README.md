# Copilot Usage Monitor

A VS Code and Cursor extension that shows your GitHub Copilot usage in the status bar, with a hover tooltip and a dashboard. It displays a percentage only when GitHub serves the figures behind it: your own plan's quota, or your organization's shared AI-credit pool once an owner or billing manager connects a read-only token. It never estimates an allowance GitHub does not report.

> The Claude, Codex, and Cursor usage monitors are separate extensions (`nexus-hub.claude-usage-monitor`, `nexus-hub.codex-usage-monitor`, `nexus-hub.cursor-usage-monitor`). This one is Copilot-only, and all four run side by side.

## What you see

The status bar shows one figure, chosen in this order:

| Account state | Status bar | Source |
|---|---|---|
| Organization connected | `Copilot Usage: 0.01% (pool)` | Pool used over pool total |
| Personal plan with a quota (Free, Pro, Pro+) | `Copilot Usage: 0% (month)` | Your plan's quota, as GitHub serves it |
| Business or Enterprise seat, no billing access | `Copilot Usage: 0.00 credits used` | Credits used; no percentage, because GitHub sets no personal limit for the seat |

A leading `~` (for example `~0.01% (pool)`) marks an approximate pool total; the dashboard says why. Hover for teal progress bars, click for the dashboard.

## Setup

### Your own usage

The extension reads the GitHub account VS Code has signed in for it. If the GitHub Copilot extension is signed in, nothing else is needed. Otherwise select **Sign in to GitHub** in the dashboard.

With several GitHub accounts signed in, the extension reads the account you choose for it, whatever repository is open. Change it with **Copilot Usage: Switch GitHub Account**, or from the Accounts menu: your account > **Manage Extension Account Preferences**. The extension never reads a repository remote, your git identity, or the `gh` CLI login.

### Your organization's pool (owners and billing managers)

Run **Copilot Usage: Connect Organization**, enter the organization login, and paste a fine-grained personal access token created at `github.com/settings/personal-access-tokens/new` with:

- Resource owner: the organization
- Organization permissions: Administration (read-only) and GitHub Copilot Business (read-only)
- Repository access: public repositories (read-only)
- A short expiry

The token is checked with one request, then stored in VS Code secret storage and sent only to `api.github.com`. **Copilot Usage: Disconnect Organization** deletes it. A token that expires or is revoked is deleted on the next refresh, and the dashboard offers **Reconnect**.

## How the figures are computed

| Figure | Request | Notes |
|---|---|---|
| Personal quota and reset date | `GET https://api.github.com/copilot_internal/user` with your VS Code GitHub session | Undocumented; the endpoint the Copilot extension's own usage popup reads. A quota gives a percentage only when GitHub marks it limited with an entitlement above 0. |
| Pool used | `GET /organizations/{org}/settings/billing/ai_credit/usage` | Sum of `discountQuantity` over Copilot AI-credit line items, shown with two decimals. GitHub's AI usage page rounds its headline to a whole number, so 0.91 here can read 1 there. |
| Pool total | `GET /orgs/{org}/copilot/billing` | Seats times GitHub's published included credits per seat: 1,900 for Business, 3,900 for Enterprise. |

The pool total is labelled approximate when a seat was added this cycle (GitHub does not publish how an added seat is prorated) or a seat is pending cancellation. A seat removed outright this cycle still counts toward the pool but no longer appears in the seat count, so the total can read low. The pool resets at 00:00 UTC on the first day of each month.

`copilot_internal/user` is undocumented and may change without notice. If it does, the monitor shows "unrecognized response" and keeps your cached figures rather than guessing.

## Usage-guard state file

So the Nexus-Hub `usage-guard` hook can hand off work before a limit is reached, the extension writes `~/.nexus-hub/state/usage-probe/copilot.json` (or under `NEXUS_HOME` when set) after each successful refresh. It holds percentages, reset times, the figure's source (`personal` or `organization`), and the approximate flag: no login, organization name, account id, email, or token. The file is written atomically and is not written for a seat with no percentage, or after you sign out. When a refresh fails briefly (a rate limit, a GitHub error, a network drop), the last good figure stays on screen with a warning icon and in the file with `"stale": true` and its original fetch time, so the guard stops using it after 30 minutes. Turn the file off with `copilotUsage.writeUsageState`.

## Commands

| Command | Description |
|---|---|
| `Copilot Usage: Dashboard` | Open the usage dashboard |
| `Copilot Usage: Refresh` | Fetch the latest usage from GitHub |
| `Copilot Usage: Recommend` | View the recommendation and tips |
| `Copilot Usage: Clear Data` | Clear cached usage and the state file (the organization connection is kept) |
| `Copilot Usage: Settings` | Open the dashboard's settings section |
| `Copilot Usage: Connect Organization` | Store a read-only organization token |
| `Copilot Usage: Disconnect Organization` | Delete the organization token |
| `Copilot Usage: Sign in to GitHub` | Sign in, or choose an account when several are signed in |
| `Copilot Usage: Switch GitHub Account` | Choose a different GitHub account for this extension |

## Settings

| Setting | Default | Description |
|---|---|---|
| `copilotUsage.organization` | `""` | Organization login for the pool view; set by Connect Organization |
| `copilotUsage.writeUsageState` | `true` | Write the percentages-only state file for the usage guard |
| `copilotUsage.autoFetch` | `true` | Fetch on startup and at intervals |
| `copilotUsage.refreshInterval` | `10` | Minutes between refreshes (1-120); one minute near the moderate threshold |
| `copilotUsage.showInStatusBar` | `true` | Show or hide the status bar item |
| `copilotUsage.compactStatusBar` | `false` | Drop the "Copilot Usage: " label |
| `copilotUsage.thresholds.*` | `50` / `75` / `95` | Moderate, high, and critical thresholds |
| `copilotUsage.colors.*` | `#cca700` / `#f0643c` / `#e05555` | Status bar background per level, or `none` |
| `copilotUsage.notificationTimeoutSeconds` | `12` | How long notifications stay on screen |

`organization`, `writeUsageState`, the thresholds, and the colors are application-scoped: set them in your user settings, because a workspace's `.vscode/settings.json` cannot change them.

## Data storage and privacy

Usage figures are cached in VS Code's `globalState` on your machine. The only network requests go to `api.github.com`, redirects are refused, and the extension writes no token to settings, logs, the cache, or the state file. The organization token lives only in VS Code secret storage.

## Development

```powershell
npm ci
npm run compile
npm test
npm run test:coverage
npm run package
```

`npm run test:coverage` enforces at least 80% line and statement coverage plus 75% branch and function coverage. The status-bar glyph font is generated from `icons/copilot.svg` with `npm run generate:icons`.
