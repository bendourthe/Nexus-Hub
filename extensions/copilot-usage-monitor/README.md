# Copilot Usage Monitor

A VS Code and Cursor extension that shows your GitHub Copilot usage in the status bar, with a hover tooltip and a dashboard. It displays a percentage only when GitHub serves the figures behind it: your own plan's quota, or your organization's shared AI-credit pool once an organization owner connects it. It never estimates an allowance GitHub does not report, and it never shows a count of credits used.

> The Claude, Codex, and Cursor usage monitors are separate extensions (`nexus-hub.claude-usage-monitor`, `nexus-hub.codex-usage-monitor`, `nexus-hub.cursor-usage-monitor`). This one is Copilot-only, and all four run side by side.

## What you see

The status bar shows one percentage of the current month's window, chosen in this order:

| Account state | Status bar | Source |
|---|---|---|
| Organization connected | `Copilot: 0.01% (month)` | Pool used over pool total |
| Personal plan with a quota (Free, Pro, Pro+) | `Copilot: 0% (month)` | Your plan's quota, as GitHub serves it |
| Business or Enterprise seat, organization not connected | `Copilot: --% (month)` | No percentage: the seat draws on the organization's shared pool and has no limit of its own. The hover and dashboard explain the one-time Connect step |

Every Copilot window resets monthly, at 00:00 UTC on the first day of the month. A leading `~` (for example `~0.01% (month)`) marks an approximate pool total; the dashboard says why. The dashboard may show the pool's size (for example "Pool: 13,300 credits"), but never how many credits were used. Hover for teal progress bars, click for the dashboard.

## Setup

### Your own usage

The extension reads the GitHub account VS Code has signed in for it. If the GitHub Copilot extension is signed in, nothing else is needed. Otherwise select **Sign in to GitHub** in the dashboard.

With several GitHub accounts signed in, the extension reads the account you choose for it, whatever repository is open. Change it with **Copilot Usage: Switch GitHub Account**, or from the Accounts menu: your account > **Manage Extension Account Preferences**. The extension never reads a repository remote, your git identity, or the `gh` CLI login.

### Your organization's pool (organization owners)

Run **Copilot Usage: Connect Organization**, or select **Connect Organization** in the dashboard. Connect does as much as it can for you:

1. **It finds the organization.** It reads the organizations your Copilot seat belongs to. With one, it asks you to confirm it; with several, it offers a list; with none, it asks you to type the organization's login.
2. **It tries without a token first.** VS Code asks you once to let the extension read your organizations (GitHub's read-only `read:org` permission). If GitHub then serves both pool figures, you are connected and no token is stored.
3. **Otherwise it guides you through a read-only token.** Select **Open GitHub**: GitHub's token page opens with everything filled in (the name, your organization, read-only Administration and GitHub Copilot Business permissions, and the longest expiry GitHub allows, 366 days). Click **Generate token**, then **Copy**, and paste it into the box that opens in VS Code.

Connect checks the result with GitHub before saving anything. If GitHub refuses a token, the message names the fix: the token's resource owner must be the organization, both permissions must be read-only, and an organization that requires approval needs an owner to approve the request under the organization's **Settings** > **Personal access tokens** > **Pending requests**.

A token is stored in VS Code secret storage and sent only to `api.github.com`. No write permission is ever requested. A token that expires or is revoked is deleted on the next refresh, and the dashboard offers **Reconnect**.

**Copilot Usage: Disconnect Organization** deletes any stored token and clears the organization. VS Code gives an extension no way to give back the `read:org` permission it was granted; to remove it, sign out of GitHub from VS Code's Accounts menu, or revoke **Visual Studio Code** under GitHub **Settings** > **Applications** > **Authorized OAuth Apps**.

## How the figures are computed

| Figure | Request | Notes |
|---|---|---|
| Personal quota and reset date | `GET https://api.github.com/copilot_internal/user` with your VS Code GitHub session | Undocumented; the endpoint the Copilot extension's own usage popup reads. A quota gives a percentage only when GitHub marks it limited with an entitlement above 0. |
| Pool used | `GET /organizations/{org}/settings/billing/ai_credit/usage` | Sum of `discountQuantity` over Copilot AI-credit line items, used only to compute the percentage. GitHub's AI usage page rounds its headline to whole credits, so the two can differ by a fraction of a percent. |
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
| `Copilot Usage: Connect Organization` | Connect your organization's pool: token-free first, then a guided read-only token |
| `Copilot Usage: Disconnect Organization` | Delete any organization token and clear the organization |
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

Usage figures are cached in VS Code's `globalState` on your machine. The only network requests go to `api.github.com`, redirects are refused, and the extension writes no token to settings, logs, the cache, or the state file. An organization token, when one is needed, lives only in VS Code secret storage. Connect reads your seat's organization list to offer a choice and never stores it.

## Development

```powershell
npm ci
npm run compile
npm test
npm run test:coverage
npm run package
```

`npm run test:coverage` enforces at least 80% line and statement coverage plus 75% branch and function coverage. The status-bar glyph font is generated from `icons/copilot.svg` with `npm run generate:icons`.
