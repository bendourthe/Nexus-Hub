# Cursor Usage Monitor

An independent Nexus-Hub extension for personal Cursor usage. The runtime shows normalized cache or manual data in a status bar, dashboard, settings panel, and threshold warning view. Cursor Models, Other Models, personal on-demand spend, reset context, source, and freshness stay separate.

## Runtime Behavior

On activation, the extension hydrates normalized live cache first, then manual data, then an explicit empty state. Stale snapshots remain visible but never trigger threshold alerts. Refreshes are coalesced, cancellable with `AbortController`, and reflected across the status bar, open dashboard, and warning view.

The runtime registers these commands:

- `Cursor Usage: Dashboard`
- `Cursor Usage: Refresh`
- `Cursor Usage: Recommendation`
- `Cursor Usage: Settings`
- `Cursor Usage: Enter Usage Manually`
- `Cursor Usage: Clear Data`
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

## Authentication Boundary

User-supplied credentials may be stored only through VS Code SecretStorage. Credentials never enter extension settings, logs, manual snapshots, or notifications.

**HO-5 remains explicit and open.** The production runtime instantiates the provider with no JSON or HTML transport. It never opens `state.vscdb`, reads browser cookies, searches credential files, or makes a live dashboard request. Consequently, `cursorUsage.autoFetch` does not create a polling timer until a separately authorized transport capability is injected. Refresh reports this boundary and keeps cache/manual data visible.

The provider remains dependency-injected and fixture-driven. Authorized future adapters can normalize a bounded JSON response or the approved spending/usage HTML pair, then fall back to normalized cache or manual data with explicit staleness.

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
- Live transport: disabled under HO-5

The extension is not affiliated with or endorsed by Cursor. Source-artwork provenance and attribution requirements are recorded in `icons/README.md`.
