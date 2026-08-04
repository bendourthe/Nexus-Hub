# Cursor Usage Authentication and Dashboard Probe

**Version:** v3.15.9
**Probe date:** 2026-08-04
**Mode:** Read-only path and public-documentation probe

## Decision

Cursor does not document a public personal-usage API or a supported IDE-session export. The extension may attempt to reuse an existing Cursor session only through a narrowly scoped adapter that never logs, persists, or exposes the credential. If safe session reuse cannot be established, the extension uses VS Code SecretStorage for an explicitly supplied value or falls back to cache/manual data. It never scans browser cookie stores automatically.

The terms `credential-api` and `session-dashboard-json` describe an undocumented authenticated dashboard integration. They must never be presented as a documented Cursor API. Cursor's documented Admin API is team/admin oriented and does not establish a personal included-usage endpoint.

## Officially Documented Surfaces

| Surface | Documented behavior | Contract implication |
|---|---|---|
| `agent login` | Authenticates Cursor Agent and securely stores credentials locally | Prefer the platform's own signed-in state; do not copy it into settings JSON |
| `agent status` | Reports whether the CLI is authenticated | Safe presence check when the CLI is installed |
| `agent logout` | Clears the CLI authentication state | The extension must treat a later `401` as an expired/cleared session |
| `CURSOR_API_KEY` / `--api-key` | Explicit CLI/API-key authentication | Do not read unrelated environment dumps; no documented personal-usage endpoint accepts this as a contract |
| `~/.cursor/cli-config.json` | Default CLI configuration path, with XDG/custom variants | Configuration candidate only; not documented as a credential file |
| macOS Keychain / local credential backend | Cursor documents secure local storage and an opt-in owner-only file backend | Do not assume a filename or export format Cursor has not documented |

## Candidate Local Paths

These are presence candidates, not stable credential contracts. The provider must isolate each platform adapter and fail closed when the expected schema is absent.

| Platform | Candidate | Evidence | Allowed Phase 4 behavior |
|---|---|---|---|
| Windows | `%APPDATA%\Cursor\User\globalStorage\state.vscdb` | Empirical VS Code-compatible application-state location; present on the 2026-08-04 probe host | Open read-only only after explicit user authorization; query an allowlisted key name; never dump tables or values |
| macOS | `~/Library/Application Support/Cursor/User/globalStorage/state.vscdb` | Empirical cross-platform Cursor state location | Same bounded read-only rule |
| Linux | `~/.config/Cursor/User/globalStorage/state.vscdb` | Empirical XDG-default Cursor state location | Same bounded read-only rule |
| All | `~/.cursor/cli-config.json` or XDG/custom config root | Official configuration location | Read only documented non-secret configuration needed to find the active profile |
| All | Cursor SecretStorage / OS credential backend | Official storage concept; physical layout intentionally undocumented | Access only through a supported host API if Cursor exposes one; never scrape OS keychain files |
| All | Portable, Insiders, remote-host, or custom profile roots | Possible deployment variants | Require explicit configured path; do not recursively hunt the filesystem |

Browser and Electron `Cookies`, `Login Data`, `Network Persistent State`, shell history, process memory, and unrelated keychains are outside the automatic probe boundary.

## Local Probe Result

The 2026-08-04 Windows probe checked path existence only:

- `%APPDATA%\Cursor\User\globalStorage\state.vscdb`: present.
- `%USERPROFILE%\.cursor\cli-config.json`: absent.
- `%LOCALAPPDATA%\Programs\cursor\Cursor.exe`: present.

No database, configuration file, cookie store, keychain, or credential value was opened. The result proves only that a candidate state database exists on this host; it does not prove a usable session key, schema, or endpoint contract.

## Dashboard Routes

| Route | Purpose | Safe semantic anchors |
|---|---|---|
| `https://cursor.com/dashboard/spending` | Included pools, remaining allowance, reset, on-demand state/spend/limits | `Spending`, `Cursor Models`, `Other Models`, `Included Usage`, `On-Demand Usage` |
| `https://cursor.com/dashboard/usage` | Request/model/token detail and time range | `Usage`, model/pool names, token/request unit text, billing-cycle date range |

Both routes are authenticated and dynamically rendered. Unauthenticated fetches, login redirects, or empty client shells are expected failure modes. CSS classes, generated IDs, React tree depth, and hashed bundle names are not selectors.

Community tools report private routes such as `/api/usage-summary` and `/api/dashboard/get-current-period-usage`. They are discovery leads only. Their names, methods, fields, units, and availability are unverified and may change without notice. Any implementation must capture a sanitized field-name/units fixture before accepting such a path and must label the source `credential-api`, not `public-api`.

## Source Resolution

1. Use a documented personal API if Cursor publishes one in the future.
2. With explicit user authorization, try one allowlisted session-dashboard JSON request using existing signed-in state.
3. If JSON is unavailable but the authenticated spending/usage HTML is present, parse semantic anchors through an isolated adapter.
4. On authentication, schema, visibility, transport, or rate-limit failure, show last-known-good cache with freshness.
5. Use manual values only when the user enters them; manual values never include a credential.

The extension stores a user-supplied credential only in SecretStorage. It stores normalized usage snapshots in its cache, never raw authenticated responses.

## Bounded Probe Procedure

1. Ask for explicit authorization and state exactly which local candidate and dashboard route will be checked.
2. Confirm path existence without opening content.
3. If authorized, open a candidate database read-only and query only an allowlisted state key. Do not enumerate all keys, tables, or values.
4. Keep the session value in memory for one request. Never print it, pass it in a command argument, write it to disk, or include it in an exception.
5. Request at most one approved JSON candidate and one HTML route.
6. Record only status, redirect classification, top-level field names, numeric aggregates, units, period/reset fields, and source.
7. Redact account names, emails, team IDs, request IDs, free-form activity text, URLs containing identifiers, and every header or session value.
8. Stop on `401`, `403`, or `429`. Do not loop or probe neighboring endpoints.
9. Compare the sanitized shape to `tests/fixtures/cursor-usage/`; never commit the live response.

## Failure Modes and Fallbacks

| Failure | Safe response |
|---|---|
| State path absent, locked, encrypted, remote, or custom | Ask for an explicit path or use SecretStorage/manual |
| Candidate key or schema absent | Do not scan broadly; treat credential reuse as unavailable |
| `401` or login redirect | Ask the user to sign in; retain cache |
| `403` or spending hidden by account role | Explain visibility limitation; do not treat as zero |
| `429` | Honor retry metadata; do not automatically retry in a loop |
| HTML is client-only, localized, or changed | Reject the scrape shape and retain cache/manual |
| JSON fields or units drift | Reject incompatible fields until a fixture and contract update land |
| Reset passes while cache is stale | Label prior-period data and suppress current percentages |

## Security Invariants

- No credential or cookie value appears in logs, errors, fixtures, settings, telemetry, tests, or documentation.
- No recursive search for auth-like filenames.
- No browser cookie database access.
- No plaintext credential setting.
- No automatic mutation of billing, spend limits, teams, or account settings.
- No claim that an undocumented endpoint is public or supported.
- No team shared limit divided into a personal cap.

## Sources

- [Cursor CLI authentication](https://cursor.com/docs/cli/reference/authentication)
- [Cursor CLI configuration](https://cursor.com/docs/cli/reference/configuration)
- [Cursor API overview](https://cursor.com/docs/api)
- [Cursor Admin API](https://cursor.com/docs/account/teams/admin-api)
- [Cursor usage limits](https://cursor.com/help/models-and-usage/usage-limits)
- [Cursor billing](https://cursor.com/help/account-and-billing/billing)
- [Cursor spend limits](https://cursor.com/help/account-and-billing/spend-limits)
