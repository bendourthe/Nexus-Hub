# Cursor Usage Monitor

An independent Nexus-Hub extension for personal Cursor usage. Phase 4 provides the typed provider, normalization, authentication boundary, and cache/store. Status-bar, dashboard, settings, warnings, package artwork, installer host isolation, and CI packaging arrive in Phases 5-6.

## Data Contract

The data layer keeps these surfaces separate:

- Cursor Models included usage.
- Other Models included usage.
- Personal on-demand enabled state and currency spend.
- Optional Teams shared-spend context, never a personal allowance.

Percentages are accepted from a source or calculated only from matching finite units and a positive denominator. Tokens, requests, percentages, and money are never converted into one another.

## Authentication Boundary

User-supplied credentials are stored only through VS Code SecretStorage. Automatic Cursor session reuse is disabled unless a future explicitly authorized adapter is supplied. Phase 4 never opens `state.vscdb`, scans browser cookies, searches credential files, or makes a live dashboard request.

The provider is dependency-injected and fixture-driven. It can normalize a bounded JSON response or the approved spending/usage HTML pair, then falls back to normalized cache or manual data with explicit staleness.

## Development

```bash
npm ci
npm run compile
npm test
npm run test:coverage
```

Node.js 22 or newer is required.

## Current Scope

- Extension id: `nexus-hub.cursor-usage-monitor`
- Reserved command prefix: `cursor-usage`
- Configuration prefix: `cursorUsage`
- Meter color reserved for Phase 5: `#4682B4`

The extension is not affiliated with or endorsed by Cursor. Source-artwork provenance and attribution requirements are recorded in `icons/README.md`.
