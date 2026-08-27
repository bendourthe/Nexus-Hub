# Cursor Usage Data Contract

**Version:** v3.15.9
**Verified against official Cursor documentation:** 2026-08-04
**Fixture root:** `tests/fixtures/cursor-usage/`

## Decision

The Cursor Usage Monitor reports personal Cursor Models included usage, personal Other Models included usage, and personal on-demand spend when enabled. Cursor documents those dashboard concepts but does not publish a personal-usage API contract. A credential-backed fetch is therefore an undocumented session-dashboard integration, not a public API claim, and HTML scraping is an explicit fallback with isolated parsing and fixture coverage.

The monitor is read-only. It does not edit spend limits, team settings, billing settings, or account membership. It never reads or logs raw browser cookies, never stores a session credential in settings JSON, and never derives a personal hard cap as `$limit / member_count` from a Teams shared spend limit.

## Scope and Ownership

| Metric | Ownership | Required display |
|---|---|---|
| Cursor Models included usage | Personal monthly pool | Percentage when verified; used/limit and unit when available; reset and freshness context |
| Other Models included usage | Personal monthly pool | Percentage when verified; used/limit and unit when available; reset and freshness context |
| On-demand enabled | Personal account state | `enabled`, `disabled`, or `unknown` |
| Personal on-demand spend | Personal billing usage | Currency amount only when the dashboard identifies it as personal |
| Teams spend limit | Shared team context | Optional shared-pool label; never shown as a personal allowance |
| Dynamic Spend Limit | Shared team context | Optional dynamic label; never divided by seat or member count |

Included usage is per member and non-transferable. Team on-demand limits are shared across the team unless Cursor explicitly exposes an Enterprise member or group override. A Teams value is context, not a denominator for a personal progress bar.

## Source Contract

The normalized top-level `source` is exactly one of:

- `credential-api` - a successful authenticated request made with an existing Cursor session to an undocumented dashboard JSON endpoint. The label means credential-backed integration; it does not claim a documented public API.
- `html-scrape` - authenticated HTML from `https://cursor.com/dashboard/spending` or `https://cursor.com/dashboard/usage`, parsed through isolated semantic anchors.
- `cache` - the last known good normalized snapshot, with its original `fetchedAt` and an explicit stale reason.
- `manual` - user-entered values that contain no recovered credential or hidden dashboard state.

Source priority is `credential-api`, then `html-scrape`, then `cache`, then `manual`. A future documented personal API supersedes both dashboard sources after a contract update and fixture-backed implementation.

## Normalized Model

| Field | Type | Meaning and invariant |
|---|---|---|
| `period.startsAt` | ISO timestamp or `null` | Dashboard period start when supplied |
| `period.resetsAt` | ISO timestamp or `null` | Billing-cycle reset when supplied; never invented |
| `cursorModels.used` | quantity or `null` | Personal Cursor Models consumption |
| `cursorModels.limit` | quantity or `null` | Matching personal denominator |
| `cursorModels.percentUsed` | number or `null` | Verified source percentage, or same-unit `used / limit * 100` |
| `otherModels.used` | quantity or `null` | Personal Other Models consumption |
| `otherModels.limit` | quantity or `null` | Matching personal denominator |
| `otherModels.percentUsed` | number or `null` | Verified source percentage, or same-unit `used / limit * 100` |
| `onDemand.enabled` | `true`, `false`, or `null` | `null` means unknown, not disabled |
| `onDemand.personalSpend` | money or `null` | Personal on-demand amount in source currency |
| `teamContext.sharedSpendLimit` | money or `null` | Team-wide context only |
| `teamContext.dynamicSpendLimit` | boolean or `null` | Whether the shared team limit scales with seats |
| `source` | source enum | Actual successful source |
| `fetchedAt` | ISO timestamp | Time the represented data was fetched |
| `stale` | boolean | True only for cache or explicitly stale source data |
| `staleReason` | string or `null` | Why freshness cannot be guaranteed |

A quantity is `{ "value": number, "unit": "tokens" | "requests" | "percent" }`. Money is `{ "amount": number, "currency": string }`, where currency is an uppercase ISO 4217 code when known.

## Percentage and Unit Rules

- Calculate a percentage only when numerator and denominator use the same unit and the denominator is finite and greater than zero.
- A source-provided percentage may be displayed without raw quantities, but its provenance remains attached to the metric.
- Preserve `tokens`, `requests`, `percent`, and currency as distinct units. Never convert between tokens and requests.
- Never estimate currency from aggregate tokens because model prices differ.
- An unknown denominator is not zero. Show absolute usage or `Allowance unavailable`; do not render `0%`, `100%`, or a fabricated maximum.
- Clamp visual meter fill to `0..100`, but preserve a source percentage above 100 in text so overage remains visible.

## Reset, Freshness, and Cache Rules

- Both personal included pools reset with the billing cycle. Unused usage does not roll over.
- Use a dashboard-supplied reset or period boundary. A calendar estimate may be shown only as `estimated`, never as a verified reset.
- Cache entries retain the original period and `fetchedAt`.
- A cached snapshot must not silently cross a known reset. After `resetsAt`, mark it stale and hide percentages unless the UI labels them as prior-period values.
- A missing period is valid for a new, empty, or partially rolled-out account; it is not an error and not proof of zero allowance.

## Dashboard and Scrape Contract

| Route | Intended fields | Stable semantic anchors | Non-contractual details |
|---|---|---|---|
| `https://cursor.com/dashboard/spending` | Included pool percentages, remaining allowance, reset, on-demand state/spend/limit | `Spending`, `Cursor Models`, `Other Models`, `Included Usage`, `On-Demand Usage` | CSS classes, generated IDs, element depth |
| `https://cursor.com/dashboard/usage` | Request/model/token detail and time period | Usage headings, model labels, token/request unit text, date range | Private endpoint names, hashed selectors, client state keys |

The parser prefers semantic text and embedded JSON field names isolated in one provider module. It never depends on hashed class names. Localization, A/B rollouts, client-only shells, and login redirects are typed scrape failures. The committed HTML fixtures are synthetic and use `data-fixture-*` markers only for test readability; those markers are not claimed as live Cursor selectors.

## Error Contract

| Condition | Classification | User-facing behavior |
|---|---|---|
| `400` or usage-summary disabled | Unsupported dashboard data path | Try HTML once, then cache/manual |
| `401` | Missing or expired session | Ask the user to sign in; retain cache; do not loop |
| `403` | Account role, policy, or dashboard visibility restriction | Explain that spend data may require account/team access; retain cache |
| `404` | Endpoint or rollout unavailable | Do not treat as zero; fall back |
| `429` | Rate limited | Honor retry metadata when present; show stale cache |
| Login redirect or client-only shell | Unauthenticated or unrendered HTML | Stop parsing; never scrape credentials from the login page |
| Schema or unit drift | Undocumented dashboard contract changed | Reject incompatible fields; preserve cache/manual; name the missing field or unit |
| Unknown denominator | Partial data | Show absolute usage; omit percentage |
| Network, proxy, or TLS failure | Transport failure | Fail soft to cache/manual with freshness context |

## Bounded Authorized Probe

The probe is manual, read-only, and opt-in. It never emits credentials, cookies, account identifiers, request headers, or raw live responses.

1. Confirm the user is signed in to Cursor and authorizes one bounded dashboard probe.
2. Resolve only documented configuration paths and explicitly listed application-state candidates from `cursor-usage-auth-probe.md`.
3. Do not inspect browser cookie databases, shell history, process memory, or unrelated credential stores.
4. Request each approved dashboard route or candidate JSON endpoint at most once.
5. Emit only status, redirect classification, top-level field names, units, aggregate numeric values, period/reset fields, and source classification.
6. Redact names, emails, team IDs, request IDs, session values, headers, URLs with account identifiers, and free-form activity text.
7. Stop on `401`, `403`, or `429`; do not retry in a loop.
8. Compare the sanitized shape with committed fixtures. Never commit the live response.

## Fixture Inventory

| Fixture | Contract branch |
|---|---|
| `included-usage-healthy.json` | Both personal included pools have same-unit numerator/denominator and verified percentages |
| `on-demand-enabled.json` | Personal on-demand enabled with spend and shared team context kept separate |
| `on-demand-disabled.json` | On-demand explicitly disabled without a fabricated spend |
| `empty-period.json` | Valid period with no usage and no inferred allowance |
| `unknown-denominator.json` | Absolute usage exists but percentages remain `null` |
| `error-401.json`, `error-403.json` | Typed authentication and visibility failures |
| `scrape-spending-page.html` | Sanitized semantic anchors for included usage and on-demand context |
| `scrape-usage-page.html` | Sanitized semantic anchors for detailed usage and units |

## Sources

- [Cursor models and pricing](https://cursor.com/docs/models-and-pricing)
- [Cursor usage limits](https://cursor.com/help/models-and-usage/usage-limits)
- [Cursor billing](https://cursor.com/help/account-and-billing/billing)
- [Cursor on-demand usage](https://cursor.com/help/account-and-billing/overages)
- [Cursor spend limits](https://cursor.com/help/account-and-billing/spend-limits)
- [Cursor Teams pricing](https://cursor.com/docs/account/teams/pricing)
- [Cursor Admin API](https://cursor.com/docs/account/teams/admin-api)
- [Cursor API overview](https://cursor.com/docs/api)
