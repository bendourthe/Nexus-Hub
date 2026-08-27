# Cursor Usage Monitor

An independent Nexus-Hub extension for personal Cursor usage. The runtime shows normalized cache or manual data in a status bar, dashboard, settings panel, and threshold warning view. Cursor Models, Other Models, personal on-demand spend, reset context, source, and freshness stay separate.

## How live usage is read

Cursor publishes no *public* personal usage API: its documented APIs (administration, analytics, code tracking) are scoped to Enterprise team administrators. Its own client, however, reads personal usage through a unary Connect RPC, and this extension now uses the same one:

```
POST https://api2.cursor.sh/aiserver.v1.DashboardService/GetCurrentPeriodUsage
```

The request body is empty, because the message's team id is optional. Authorization is the session Cursor itself signed you in with, read **read-only** from a single allowlisted key in Cursor's own local state, behind a one-time consent prompt. This is deliberately the same shape as the sibling monitors: the Claude monitor reads `~/.claude/.credentials.json` and calls Anthropic's OAuth usage route, and the Codex monitor reads `~/.codex/auth.json` and calls ChatGPT's backend usage route. None of the three reads a web page.

The route is labelled `credential-api`, never `public-api`, because it is undocumented. A payload that does not match the pinned contract is **rejected rather than coerced**, so schema drift degrades to the previous cache with an explicit staleness label instead of rendering a wrong number as live.

Three properties of the payload are worth knowing, because each is a trap that a reasonable implementation walks into:

- **Field names are camelCase**, not the protobuf descriptor's snake_case, because Connect's JSON codec applies the proto3 JSON mapping. Building from the descriptor alone reads `undefined` for every field.
- **Percentages are used exactly as delivered and never recomputed.** On a live account, spend over limit came to 1078.70 while the reported figure was 23.97, because the reported percentage uses a base the payload does not expose. Deriving it would render a healthy pool as 1079% and fire every threshold alert continuously.
- **Money is minor units and cycle bounds are epoch-millisecond strings.** Spend divides by 100; a cycle read as seconds would date to 1970.

If you decline consent, the extension falls back to figures you enter by hand. Understand what that is: a snapshot frozen at the moment you entered it. It does not follow your usage, so it is a reading you took rather than a live meter. `Cursor Usage: Connect Live Usage Tracking` reopens the prompt whenever you want it; consent is never re-requested automatically.

What will not be done, whatever the convenience: reading browser cookies, hunting the filesystem for credentials, or scraping the HTML billing page.

## Runtime Behavior

On activation, the extension hydrates normalized live cache first, then manual data, then an explicit empty state. Stale snapshots remain visible but never trigger threshold alerts. Refreshes are coalesced, cancellable with `AbortController`, and reflected across the status bar, open dashboard, and warning view.

The runtime registers these commands:

- `Cursor Usage: Dashboard`
- `Cursor Usage: Refresh`
- `Cursor Usage: Recommendation`
- `Cursor Usage: Settings`
- `Cursor Usage: Enter Usage Manually`
- `Cursor Usage: Clear Data`
- `Cursor Usage: Revoke Live Usage Access`
- `Cursor Usage: Open Native Settings`
- `Cursor Usage: Open Cursor Usage Page`

Manual entry accepts a local JSON snapshot matching the two personal included-usage meters, optional personal on-demand spend, and period dates. Clearing data removes both normalized cache and manual data plus in-session alert state.

## Data Contract

The data layer keeps these surfaces separate:

- Cursor Models included usage.
- Other Models included usage.
- Personal on-demand enabled state and currency spend.
- Optional Teams shared-spend context, never a personal allowance.

Percentages are accepted from a source or calculated only from matching finite units and a positive denominator. Tokens, requests, percentages, and money are never converted into one another.

The dashboard renders three bars: Cursor Models and Other Models as percentages of their token allowances, and on-demand spend as **currency against its spend limit**. The on-demand bar always states that the limit is shared across your team and gives the reset date from the payload's billing cycle, because a shared pool is not a personal cap. It is dropped rather than approximated when a fraction would be meaningless (no limit reported, a limit in a different currency, or a non-positive limit), and an over-limit bar clamps at full width and says so. Percentages carry one decimal, so a 1.7% pool is not reported as 2%.

## Authentication Boundary

User-supplied credentials may be stored only through VS Code SecretStorage. Credentials never enter extension settings, logs, manual snapshots, or notifications.

**Live usage requires one explicit consent click, and nothing is read before it.** On first activation, if a Cursor state database is present and the host supports reading it, the extension shows a modal prompt stating exactly what it will and will not read. Only the decision is stored, never a credential. Until consent is granted the extension reads nothing and behaves exactly as the cache/manual build did: `cursorUsage.autoFetch` creates no polling timer, and refresh reports the boundary while keeping stored data visible.

Once granted, the extension opens Cursor's own application state database **read-only**, queries **one allowlisted key** (`cursorAuth/accessToken`) with a bound parameter and a one-row cap, and uses that session for a single JSON request. It still never reads browser cookies, a `Login Data` file, an OS keychain, process memory, or shell history, never searches the filesystem for credential-shaped files, and never scrapes an HTML billing page. `Cursor Usage: Revoke Live Usage Access` clears the decision and any usage cached from it in one action, keeping data you entered manually.

The JSON route is undocumented. It is labelled `credential-api`, never a public Cursor API, and its field names and units are pinned by a committed wire fixture: a payload that does not match is rejected rather than coerced. A `401`, a rate limit, or a schema drift demotes to the previous cache with an explicit staleness label instead of blanking or presenting stale numbers as current. **The route's shape is not yet confirmed against a live account**; see `docs/releases/v3/v3.15/development/cursor-usage-auth-probe.md` for the authorization boundary and the outstanding verification step.

Reading the state database requires the extension host to provide Node's built-in SQLite module (Node 22.13 or newer). On an older host the capability check reports it unavailable and the extension degrades to cache or manual rather than failing. User-supplied credentials remain supported through SecretStorage and take precedence over the session path.

## Development

```bash
npm ci
npm run compile
npm test
npm run test:coverage
npm run package
npm run verify:package
```

Node.js 22 or newer is required.

## Current Scope

- Extension id: `nexus-hub.cursor-usage-monitor`
- Command prefix: `cursor-usage`
- Configuration prefix: `cursorUsage`
- Included-usage meter color: `#4682B4`
- Live transport: consent-gated, `credential-api` source, wire shape not yet confirmed against a live account

The extension is not affiliated with or endorsed by Cursor. Source-artwork provenance and attribution requirements are recorded in `icons/README.md`.
