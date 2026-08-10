# GitHub Usage Monitor

A VS Code extension that shows your current-month GitHub **billing** consumption in the status bar, with a hover breakdown, a full dashboard, and threshold alerts. It covers **Actions minutes and storage plus Copilot billing** for **one** billing owner you configure.

> **This is not a Copilot-only monitor, and it is not an Actions-only monitor.** It reports both, for a single billing owner (`githubUsageMonitor.billingScope` + `githubUsageMonitor.billingOwner`). It is also independent of whichever GitHub account Copilot itself is signed in to, so the billing account it reports may differ from your Copilot account.

> Monitoring Claude Code or Codex instead? Those live in the separate **Claude Usage Monitor** (`nexus-hub.claude-usage-monitor`) and **Codex Usage Monitor** (`nexus-hub.codex-usage-monitor`) extensions. All three share no extension id, command, storage key, or view, and install and run side by side.

## Naming and the extension id (v3.15.12, reverted in v3.16.3)

The extension was renamed from **GitHub Usage Monitor** to **GitHub Billing Usage** in v3.15.12, on the reasoning that the old name invited the reading that it monitored Copilot, or that it monitored Actions only.

**v3.16.3 reverted that.** The name is **GitHub Usage Monitor** again, for consistency with its three siblings (Claude Usage Monitor, Codex Usage Monitor, Cursor Usage Monitor), which a user reads as one family. The v3.15.12 concern is instead addressed where it actually surfaces: the description and the panel subtitle both name Actions minutes and storage *and* Copilot billing explicitly.

v3.16.3 also moved the command ids to `githubUsageMonitor.*` and the configuration prefix to `githubUsageMonitor.*`, with a one-time migration that carries every user-set value across on first activation. The old `githubUsage.*` settings are left readable for one release rather than deleted, so a downgrade still finds them; their deletion is a v3.17.0 follow-up.

**The extension id deliberately did NOT change, in either direction.** It remains `nexus-hub.github-usage-monitor`. A VS Code extension id is `publisher.name`, so renaming `name` would mint a *new* extension rather than update the installed one. Anyone who had already installed the old id would end up with **two** extensions installed, both activating on startup and both writing a status-bar item, with no indication which was which. Avoiding that would have required both installers to uninstall the superseded id before installing the new one, which is teardown logic that has to be exactly right on every platform and every re-run, in exchange for a cosmetic id nobody reads. Renaming only the display surfaces is a non-breaking change: an existing install updates in place and simply shows the new name.

Command Palette search: "GitHub Usage" matches again. "GitHub Billing" no longer does.

## What it shows

- **Copilot**: current-month AI credits, or legacy premium requests on the plans that still bill that way.
- **Actions minutes**: aggregated across runner SKUs, with the per-SKU breakdown retained in the dashboard.
- **Actions storage**: reported in the unit GitHub returns, never silently converted.
- **Costs**: gross, discount, and net amounts kept separate rather than collapsed into one number.
- **Context**: billing owner and scope, reporting period, data source (`api`, `cache`, or `manual`), and how fresh the data is.

Usage bars fill in `#008080`. Severity is always carried by text and iconography as well as color, so the alert level never depends on seeing the teal.

## Setup

The Nexus-Hub installer builds and installs this extension alongside the Claude and Codex monitors:

```bash
bash scripts/installer.sh
```

```powershell
pwsh scripts/installer.ps1
```

Installing does **not** send anything to GitHub on its own. On first refresh the monitor looks for a credential in this order, and stops at the first one it finds:

1. **A token you stored explicitly.** Supplying one is a deliberate act, so it always wins - the monitor will not silently substitute a session for a token you chose.
2. **The editor's own GitHub session**, if you are already signed in. This is what makes the common case zero-setup. The lookup is always *silent*: a background refresh can never raise a sign-in dialog at you.
3. **Nothing**, in which case the panel names both ways forward rather than just reporting that it is empty.

For a personal billing owner the account name is taken from the signed-in session when you have not configured one, so `user` scope usually needs no setup at all. Organization and enterprise slugs are **never** guessed from your account name - a personal account name is not an org slug, and guessing would report a different entity's spend.

To build and install it on its own:

```bash
cd extensions/github-usage-monitor
npm ci
npm run compile
npm run package
code --install-extension github-usage-monitor-*.vsix
```

### 1. Choose the billing owner

Open the Command Palette and run `GitHub Usage Monitor: Settings`, or set these directly:

| Setting | Value |
|---|---|
| `githubUsageMonitor.billingScope` | `user`, `organization`, or `enterprise` |
| `githubUsageMonitor.billingOwner` | your username, the organization slug, or the enterprise slug |

The monitor queries exactly one owner. It never merges scopes or guesses an owner from your repositories.

### 2. Connect, or store a token

If you are signed in to GitHub in the editor, run `GitHub Usage Monitor: Refresh` and you may already be done. `GitHub Usage Monitor: Log In or Switch Account` reaches GitHub's account picker, so the billing account can deliberately differ from the one Copilot uses; `Log Out of This Monitor` clears only this extension's binding and **cannot** sign you out of the editor's shared session.

Some targets need a token instead: enterprise billing accepts classic PATs only, and an organization that has not authorized OAuth apps or that enforces SSO will refuse a session token. The monitor diagnoses each owner independently and tells you which case you are in, so run `GitHub Usage Monitor: Diagnose Authorization` before assuming it is broken.

To store one, run `GitHub Usage Monitor: Set Token` and paste a token of the class your billing scope needs (see the table). It is validated against the billing endpoint before it is saved, and it is stored only in VS Code SecretStorage - never in `settings.json`, never in workspace state, never in a log line.

| Scope | Required authorization |
|---|---|
| `user` | Fine-grained PAT or GitHub App user token with user `Plan: read`. A classic PAT also works and is what GitHub's own usage-reporting tutorial recommends |
| `organization` | Organization `Administration: read`, and the caller must be an organization administrator. A classic PAT also works, per the same tutorial |
| `enterprise` | **Classic PAT** with an enterprise owner or billing manager role. The billing endpoints explicitly do **not** accept fine-grained PATs or GitHub App tokens at this scope |

> **Which token class?** GitHub's first-party docs currently disagree for user and organization scope: the REST endpoint reference says fine-grained PATs work, while the "Automating usage reporting" tutorial says the billing usage endpoints do not support them and directs you to a classic PAT. If a fine-grained token is rejected, try a classic PAT. Enterprise scope is unambiguous: classic PAT only. The conflict and the evidence behind it are recorded in [github-billing-auth-probe.md](../../docs/v3/v3.15/development/github-billing-auth-probe.md).
>
> When a token is refused for permissions, the error now quotes GitHub's own answer from the `X-Accepted-OAuth-Scopes` response header, so it names the scope the operation would accept rather than only what the extension expected.

`GitHub Usage Monitor: Validate Token` re-checks the stored credential, `GitHub Usage Monitor: Rotate Token` replaces it, and `GitHub Usage Monitor: Clear Token` deletes it from SecretStorage.

`GitHub Usage Monitor: Open Billing Page` opens GitHub's own billing page for the resolved owner, which stays the authoritative source for any figure you want to verify.

### 3. Set allowances if you want percentages

GitHub reports what you consumed. It does not guarantee an included allowance, so a percentage is only shown when a denominator is actually known. Supply one per metric with `GitHub Usage Monitor: Enter Allowances` or the `githubUsageMonitor.allowances.*` settings, in the same unit the metric is reported in. Until then the meters show absolute usage, which is the honest reading rather than a fabricated `0%`.

## Commands

| Command | Description |
|---|---|
| `GitHub Usage Monitor: Dashboard` | Open the current-month Copilot and Actions dashboard |
| `GitHub Usage Monitor: Refresh` | Fetch usage now |
| `GitHub Usage Monitor: Settings` | Scope, allowances, refresh, thresholds, and alert colors |
| `GitHub Usage Monitor: Enter Allowances` | Supply verified allowances manually |
| `GitHub Usage Monitor: Clear Data` | Remove the cached snapshot and alert state |
| `GitHub Usage Monitor: Set Token` | Store a validated token in SecretStorage |
| `GitHub Usage Monitor: Validate Token` | Re-check the stored token |
| `GitHub Usage Monitor: Rotate Token` | Replace the stored token |
| `GitHub Usage Monitor: Clear Token` | Delete the stored token |

## Settings

| Setting | Default | Description |
|---|---|---|
| `githubUsageMonitor.billingScope` | `user` | The one billing owner type to query |
| `githubUsageMonitor.billingOwner` | `""` | Username, organization slug, or enterprise slug |
| `githubUsageMonitor.copilotMetric` | `ai-credits` | `ai-credits` or legacy `premium-requests` |
| `githubUsageMonitor.allowances.copilot` | unset | Verified Copilot allowance in the selected metric's unit |
| `githubUsageMonitor.allowances.actionsMinutes` | unset | Verified monthly Actions minutes allowance |
| `githubUsageMonitor.allowances.actionsStorage` | unset | Verified Actions storage allowance in the displayed unit |
| `githubUsageMonitor.autoFetch` | `true` | Fetch on startup and on the refresh interval |
| `githubUsageMonitor.refreshInterval` | `10` | Minutes between automatic refreshes (1-120) |
| `githubUsageMonitor.staleAfterMinutes` | `30` | Age at which cached data is labeled stale |
| `githubUsageMonitor.compactStatusBar` | `false` | Show only the icon and the usage value |
| `githubUsageMonitor.alertMetric` | `highest` | Which verified percentage drives alerts |
| `githubUsageMonitor.thresholds.*` | `50` / `75` / `95` | Moderate, high, and critical thresholds |
| `githubUsageMonitor.notificationTimeoutSeconds` | `12` | Seconds before the warning view auto-dismisses |
| `githubUsageMonitor.requestTimeoutMs` | `10000` | Request timeout |
| `githubUsageMonitor.colors.*` | see settings | Alert colors for each severity |

## Alerts

Threshold alerts evaluate the metric named by `githubUsageMonitor.alertMetric`, or the highest valid percentage across metrics when it is `highest`. A metric with no verified denominator cannot produce a percentage and therefore cannot fire a percentage alert.

Each threshold notifies once per billing cycle. Crossing a threshold opens the branded warning view with the triggering metric, its value or absolute amount, reset and freshness context, and a recommendation; the view auto-dismisses after the configured timeout and can be dismissed manually. A new cycle is only recognized from a proven reset, so the alerts do not re-fire on every refresh.

## How it works

The extension calls documented GitHub REST billing endpoints with `X-GitHub-Api-Version: 2026-03-10`, scoped to the configured owner and the current month:

```
GET /users/{username}/settings/billing/ai_credit/usage
GET /organizations/{org}/settings/billing/usage
GET /enterprises/{enterprise}/settings/billing/usage
```

Requests are bounded by `githubUsageMonitor.requestTimeoutMs`, are cancellable, and carry no telemetry. Rate-limit headers are honored: a `429` shows the next eligible refresh rather than retrying in a loop.

### Failure behavior

An error never becomes a zero. When a request fails:

- with a cached snapshot, the last known good data is shown, labeled stale, alongside the typed error;
- with no data at all, an actionable empty state explains what to fix (missing token, missing permission, wrong owner, preview endpoint unavailable).

Errors are typed and specific: an expired credential, a missing `Plan: read`, a missing organization `Administration: read`, an unavailable enhanced-billing endpoint, and managed Copilot queried through personal scope each say exactly that.

## Limits worth knowing

- **Personal endpoints omit managed Copilot.** A Copilot license paid for by an organization or enterprise is not billed to your personal account, so a personal query can legitimately return nothing. Query the organization or enterprise scope, with authorization, to see that usage. The extension never presents a personal result as a managed total.
- **The billing usage-summary APIs are in public preview.** Their schema can change. Unknown fields are ignored, malformed required fields produce an explicit degraded state, and the raw response stays out of any report.
- **Unknown quotas stay absolute.** No allowance is inferred from a plan name, a screenshot, or a static pricing table.
- **Enterprise legacy premium-request usage is not queried**, because the approved contract does not expose it.

## Privacy and security

- The only outbound calls are to `api.github.com`, for the billing data of the owner you configured.
- The token lives in VS Code SecretStorage. It is never written to settings, never logged, and never echoed back in any panel.
- No website is scraped. `github.com/settings/billing` is never fetched, and browser cookies and sessions are never read.
- Nothing is mutated: no budgets, billing settings, Copilot seats, workflows, repositories, or memberships.
- The cached snapshot lives in VS Code `globalState` on your machine, under keys that do not collide with the Claude or Codex monitors. `GitHub Usage Monitor: Clear Data` removes it.

## Development

```bash
npm ci
npm run compile
npm test
npm run test:coverage
npm run package
npm run verify:package
```

`npm run test:coverage` enforces at least 80% line and statement coverage plus 75% branch and function coverage. `npm run verify:package` asserts the VSIX carries every runtime asset and no coverage report, source tree, or credential-shaped file. Both run in `.github/workflows/github-usage-monitor.yml`, which is path-filtered to this extension.
