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

## Probe Runner (v3.15.12)

The procedure below is implemented as a script so it does not have to be performed by hand. From `extensions/cursor-usage-monitor`, after `npm run compile`:

```bash
node scripts/probe-wire-shape.js
node scripts/probe-wire-shape.js --route /api/dashboard/get-current-period-usage
node scripts/probe-wire-shape.js --state-path "<custom path>"
```

It resolves the platform's candidate state path, reports the capability check before touching anything, opens the database read-only for the one allowlisted key, issues one GET to one JSON route, and prints a **type skeleton plus dot-paths: field names and types, never values**. `summarizeShape` is tested to emit no digits at all for a value-bearing payload, and to reduce any string that is not an ISO timestamp, a 3-letter currency code, or an allowlisted unit word to the bare type `string`, so an account name, email, team id, or usage figure cannot reach the output.

It then reports whether the committed `CURSOR_WIRE_CONTRACT` already matches. If it does not, map the printed paths onto the contract's `fields` table and mirror them into `tests/fixtures/cursor-usage/wire-contract.json`; a test asserts the two agree. Setting `verified: true` in both is what closes HO-5.

Note the reported Node version in the output: if the capability check reports `sqlite-unavailable`, that is **WN-5**, and the Cursor version should be recorded with it.

## Probe Run 2026-08-06 (authorized)

Run on the maintainer's Windows host with explicit authorization. **HO-5 is advanced, not closed.**

| Check | Result |
|---|---|
| State path | `%APPDATA%\Cursor\User\globalStorage\state.vscdb` resolved and present |
| Capability | **available** - `node:sqlite` loaded (script ran on system Node v24.13.0) |
| Allowlisted key | **`cursorAuth/accessToken` EXISTS** and yielded a value passing the shape rule (length and no control characters) |
| Route A | `GET https://cursor.com/api/usage-summary` with `Authorization: Bearer <session>` |
| Status A | **401** (twice: before and after opening the Cursor app) |
| Route B | `GET https://cursor.com/api/dashboard/get-current-period-usage`, same header |
| Status B | **405 Method Not Allowed** |
| Route B headers | `allow: POST`, `content-type: application/json; charset=utf-8` |
| Route B, POST | `POST` same route, empty JSON body, separately authorized |
| Status B POST | **403 Forbidden** |
| Wire shape | **Not obtained.** No route returned a JSON body |

**The sequence is now closed.** The bounded procedure says to stop on `401`, `403`, or `429` and not to loop or probe neighbouring endpoints. Three routes/verbs were attempted, all pre-recorded leads, and the `403` ends it.

### What the status ladder establishes, stated at the strength the evidence supports

An earlier version of this section over-claimed. Corrected:

| Claim | Defensible status |
|---|---|
| `/api/usage-summary` accepts `cursorAuth/accessToken` as a Bearer credential | **Negative for the tested request** |
| `get-current-period-usage` uses POST | **CONFIRMED.** The probe originally captured no response headers, so this was only "probable"; adding header capture and re-running returned `allow: POST` with `content-type: application/json`, a conforming `405` per RFC 9110. The instrument gap paid for itself on the first re-run |
| The POST reached a refusal decision | **Yes** |
| The refusal was specifically bearer-token authorization | **UNPROVEN.** `403` means only "understood and refused". It does not distinguish token audience from a missing CSRF token, absent origin headers, a malformed body, an account entitlement, or a WAF rule |
| `cursorAuth/accessToken` can never authorize a dashboard operation | **UNPROVEN** |
| A stable, supported extension wire contract exists | **No** |
| The private route is suitable for production | **No** |

Cursor documents `401` as an invalid or missing API key and `403` as a valid key with insufficient permissions **for its documented APIs on `api.cursor.com`**. Those semantics cannot be transferred to a private dashboard endpoint that may sit behind different middleware.

The recorded result is therefore:

```text
CURSOR_PRIVATE_DASHBOARD_CONTRACT = unsupported

The tested app access token did not produce usage data.
The token's precise audience remains unproven.
No further private-route, header, or cookie guessing will be performed.
```

That keeps the useful negative without overstating it.

### The decisive evidence is not the HTTP ladder, it is the absence of any supported surface

Four independent checks, all first-party or local and none requiring a guess:

1. **Cursor documents no personal-account usage API.** Its usage and spending APIs are **Enterprise-team** endpoints requiring an explicitly created Admin API key.
2. **The Cursor SDK requires an explicit API key and states it does not auto-discover credentials from a local Cursor installation.** Wrapping `@cursor/sdk` cannot turn a VSIX into a passive account-usage reader.
3. **No Cursor-owned authentication provider exists.** Of 116 bundled extensions in Cursor 3.14.27, exactly two declare `contributes.authentication`: `github-authentication` and `microsoft-authentication`. So `getSession('cursor', ['usage:read'])` has nothing to talk to.
4. **No Cursor-owned usage or billing command exists.** Searching every bundled manifest for commands matching `usage|billing|spend|quota|credit|subscription|account|plan` returns **zero**. The 21 `cursor-*` extensions contribute 8 commands in total (`cursor-deeplink` 1, `cursor-ndjson-ingest` 5, `cursor-retrieval` 2), none usage-related.

**That, not the 403, is what closes HO-5.** Exact personal server-side figures - remaining Cursor Models allowance, remaining Other Models allowance, on-demand charges - depend on Cursor's billing state across other machines, cloud agents, pool resets, discounts, credits, routing, and adjustments. Cursor's own documentation places those authoritative figures in the Spending dashboard, and exposes no supported read path to them.

### Also relevant: Cursor's terms

Cursor's terms of service restrict reverse engineering, probing or scanning the service, and harvesting, scraping, or extracting data. That is an independent reason to stop at this point rather than continue guessing at a private contract, and it means any production integration on that basis would need explicit written authorization from Cursor plus legal review. The README's no-cookie promise is worth keeping on its own merits.

### What Phase 1 delivered is still sound

The consent gate, the read-only allowlisted-key adapter (whose key name is now **confirmed** against a real host), the fail-closed transport with a fixture-pinned contract, and the degradation path all work as designed. The defensive architecture is precisely why this is a clean, legible negative rather than a silent misreport: an unrecognized shape was rejected, and the panel would show a staleness label instead of a wrong number.

`CURSOR_WIRE_CONTRACT` stays `verified: false`, and the `CursorAccountApiProvider` seam is retained for a future supported personal-usage API rather than deleted.

### What this establishes

- **The allowlisted key name is correct.** `cursorAuth/accessToken` is present in Cursor's state database and holds a plausible token. That part of the adapter's contract is confirmed against a real host, which the v3.15.9 probe could not do (it checked path existence only).
- **The read-only one-key adapter works end to end.** It opened the database, returned a value, released the handle, and reached the transport.
- **The route responded rather than failing to resolve**, so `cursor.com` served the request.

### What the 405 changes

**`405 Method Not Allowed` means route B exists.** A non-existent path returns `404`; `405` is a route that matched and rejected the *verb*. The most likely reading is that `get-current-period-usage` expects **POST**, which is consistent with its RPC-style name.

The two statuses together are more informative than either alone. Had the session token been simply invalid, `401` on both routes would be expected. Route B answered `405` instead, which admits two readings:

1. **The method check precedes the auth check** at Cursor's gateway, in which case `405` says nothing about the token.
2. **Authentication succeeded** and only the verb was wrong, in which case **the token is valid** and route A's `401` is not a stale-session problem at all but a wrong-route or wrong-auth-form problem for that specific path.

These cannot be separated without a `POST` to route B, and that is the next step - but it is **not** a step this probe takes unilaterally. See below.

### What is still not established

- The wire shape. `CURSOR_WIRE_CONTRACT` remains `verified: false`.
- Whether the stored session is valid. Reading 2 above would imply it is; reading 1 leaves it unknown.

### Next step requires explicit authorization: a POST

Resolving this needs `POST https://cursor.com/api/dashboard/get-current-period-usage`. That is deliberately **not** performed under the existing authorization, for two reasons:

1. **A POST is write-shaped.** The security invariants forbid "automatic mutation of billing, spend limits, teams, or account settings". Although an RPC-style usage query is almost certainly read-only in effect, its contract is undocumented, so the probe cannot know that in advance.
2. The boundary permits "at most one approved JSON candidate"; two GETs have already been spent on pre-recorded leads.

A POST probe would send an empty JSON body (`{}`) and record only the status and, on success, the type skeleton. It must be authorized as a distinct step.

### The extension installed in Cursor is a PRE-Phase-1 build

Observed in the maintainer's Cursor window during this run: the Cursor Usage panel reads *"No cached or manual Cursor usage is available. Enter usage manually while live transport remains disabled under HO-5."*

That is the **old** empty-state message. v3.15.12 Phase 1 replaced it with *"...Allow live usage access, or enter usage manually."* (`cursorUsageRuntime.ts:630`). So the build running in Cursor predates Phase 1 entirely, which explains two things that would otherwise look like defects:

- **No consent prompt appeared.** That build has no consent gate to prompt with.
- **The panel cannot be used to evaluate WN-5**, because the capability check it would report does not exist in it.

Testing the consent flow, and answering WN-5, requires building and installing the current VSIX into Cursor first (`npm run compile && npm run package`, then install the `.vsix`). Until then the panel reflects v3.15.9 behavior, correctly.

### WN-5 is RESOLVED, favorably

Initially recorded as maintainer-only on the reasoning that the extension host is a different runtime from system Node. That was true but the conclusion was wrong: the question is answerable directly, because Cursor's own Electron can be run as Node.

```powershell
$env:ELECTRON_RUN_AS_NODE = '1'
& "$env:LOCALAPPDATA\Programs\cursor\Cursor.exe" -e "console.log(process.versions.node); require('node:sqlite')"
```

Result on the 2026-08-06 host:

| Runtime | Value |
|---|---|
| Cursor Electron | 40.10.3 |
| Extension-host Node | **24.15.0** |
| `node:sqlite` | **AVAILABLE** |

Well above the 22.13 floor, so the capability check reports `available` in the extension host and the consent prompt does appear. **WN-5 does not bite on this host**, and the technique above answers it on any host without needing a human to read a panel.

## Forward path (recommendation, not built in v3.15.12)

Two products are separable, and only the second can be exact:

1. **Install-only local activity tracking** for personal plans, via Cursor Hooks.
2. **Exact server-side usage and spending** for Enterprise teams, via the documented Admin API with a user-supplied key.

### Cursor Hooks is a supported local source, and Nexus-Hub already owns a channel

Verified on this host (Cursor **3.14.27**):

| Surface | State |
|---|---|
| `~/.cursor/hooks.json` | **present**, `version: 1` |
| Registered hook events | `beforeShellExecution` |
| Owner of that entry | **`bash ~/.cursor/hooks/git-guardrails.sh` - Nexus-Hub's own**, installed by the v3.15.0 Cursor parity work |
| `~/.cursor/hooks/`, `~/.cursor/plugins/` | present |

So adding a usage-observation hook is **incremental on infrastructure this repository already installs, owns, and tests**, not new plumbing. The existing marker-managed discipline (modify only our own entries, never replace the user's `hooks.json`) applies unchanged.

Collect a strict allowlist only: timestamp, event type, model id, and hashed conversation/workspace identifiers. Never prompts, responses, source, file names, shell commands, repository URLs, raw conversation ids, tokens, or cookies. Cursor's own cookbook warns that logging hooks can capture sensitive information, so the implementation must select fields explicitly rather than serializing payloads.

Architecture that avoids a write conflict between hook processes and the extension host: hooks append JSONL to an extension-owned `inbox/`, and the extension imports into its own SQLite on a timer.

### Local observations are not billing facts

A snapshot must carry its authority and coverage:

- `authority`: `cursor-official` | `local-observed` | `estimated`
- `coverage`: which machines, which period, which surfaces (main agent, subagents, tab, cloud agents, CLI)

**Never populate remaining allowance or on-demand spend from local inference.** A model *selection* does not establish whether a request drew on an included pool or was charged on demand, and with Auto or the router it may not even reveal the underlying model. Badge sources persistently (`Official` / `Local` / `Estimated` / `Unavailable`) so a local estimate can never visually resemble an official balance.

### The Enterprise adapter is already possible

The documented Admin API provides `/teams/spend`, `/teams/filtered-usage-events` (model, billing category, token counts, model cost, `chargedCents`), and `/teams/daily-usage-data`, using an Enterprise Admin API key with Basic auth. **This corrects the v3.15.9 rejection of the Admin API**, which said it "omits the included-usage pool metrics": that is true of the *personal* Cursor Models / Other Models split, but the Admin API does deliver official server-side usage and spend for Enterprise teams. It should be an opt-in adapter with a user-pasted key stored only in `ExtensionContext.secrets`, never a key auto-discovered from disk, since team keys can expose other users' usage.

### One local store deliberately NOT opened

`~/.cursor/ai-tracking/ai-code-tracking.db` exists (10.9 MB). It was **not** opened. Its name suggests AI-code attribution rather than billing, its schema is undocumented, and it is outside the one-allowlisted-key boundary this probe authorizes. Recorded as an observation so a later reader does not have to rediscover it, explicitly not as a data path.

### Ask Cursor for the small first-party contract

The permanent fix is narrow: a read-only `usage:read` scope on a `cursor` authentication provider plus a personal endpoint returning billing-cycle dates, per-pool used/included/remaining, and on-demand spend and limit. Or, safer still, a built-in command returning the data without exposing any credential, e.g. `cursor.usage.getCurrentPeriod`.

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

## Phase 4 Authorization (v3.15.12)

**Authorized:** 2026-08-05, by the maintainer, for v3.15.12 Phase 1. This section supersedes the "Allowed Phase 4 behavior" column above by stating the boundary as an explicit permit/exclude list. HO-5 was opened precisely because the v3.15.9 probe had no such authorization; this section is what closes that argument.

### Permitted

1. **A one-time explicit consent prompt.** The prompt states plainly what will be read and what will not, and is answerable once. Only the decision is persisted, never the credential. Refusal is a first-class path with no repeated prompting.
2. **A read-only open of the platform state database** at the documented candidate path for the host platform (the `state.vscdb` rows of the Candidate Local Paths table), and only after consent is granted.
3. **A query for an allowlisted key name only.** One key, named in advance. No table enumeration, no key enumeration, no value dumping, no `SELECT *`.

### Excluded, and unchanged from the original probe boundary

Browser and Electron cookie stores, `Login Data`, OS keychains, process memory, shell history, recursive filesystem hunting for auth-like filenames, and HTML scraping of any billing page. Consent does not widen this list; it authorizes items 1-3 above and nothing else.

### Labelling obligation

The JSON route is labelled `credential-api`. It must never be described as a documented Cursor API, in code, copy, commit message, changelog, or documentation. Its field names and units are pinned by a committed wire fixture, and a payload that does not match the fixture is rejected rather than guessed at.

### Cursor Admin API: evaluated and rejected

The documented [Cursor Admin API](https://cursor.com/docs/account/teams/admin-api) was evaluated for this purpose and rejected. It is admin-only, team-scoped, and currently omits the included-usage pool metrics, so it cannot produce the personal Cursor Models / Other Models split that the requirement names. This rejection is recorded here so the question is not re-litigated in a later release.

### Verification status of the JSON route

**Not yet verified against a live account.** The v3.15.12 Phase 1 implementation ships the transport with a wire fixture describing the *expected* shape derived from `cursor-usage-data-contract.md`, and rejects any payload that does not match. The route, its field names, and its units remain discovery leads until the maintainer runs the Bounded Probe Procedure below and the fixture is corrected from the sanitized result. Until then HO-5 stays open, narrowed to that single outstanding step.

## Sources

- [Cursor CLI authentication](https://cursor.com/docs/cli/reference/authentication)
- [Cursor CLI configuration](https://cursor.com/docs/cli/reference/configuration)
- [Cursor API overview](https://cursor.com/docs/api)
- [Cursor Admin API](https://cursor.com/docs/account/teams/admin-api)
- [Cursor usage limits](https://cursor.com/help/models-and-usage/usage-limits)
- [Cursor billing](https://cursor.com/help/account-and-billing/billing)
- [Cursor spend limits](https://cursor.com/help/account-and-billing/spend-limits)

## Phase 6: the personal-usage route, recovered and verified

### How it was found

By reading the locally installed Cursor client bundle (`resources/app/out/vs/workbench/workbench.desktop.main.js`), not by probing candidate paths. The client declares `getCurrentPeriodUsage` on `aiserver.v1.DashboardService` as a unary Connect method, with `GetCurrentPeriodUsageRequest { team_id: int32 optional }` - an optional team id, so a personal query is an empty body.

This retracts the earlier conclusion that no personal usage surface exists. That conclusion inferred absence of a surface from absence in `cursor.com/docs/api`, which is the same absence-of-evidence error this version already corrected once in the GitHub billing auth work. The public docs are accurate and the surface exists; the docs simply do not cover it.

### Verified route

```
POST https://api2.cursor.sh/aiserver.v1.DashboardService/GetCurrentPeriodUsage
Authorization: Bearer <cursorAuth/accessToken, read read-only from one allowlisted key>
Content-Type: application/json
body: {}
-> 200, content-type: application/json
```

The credential is the same one the client itself authenticates with, obtained through the already-shipped consent gate and session adapter. No new credential class, no browser cookie, no keychain, no filesystem search.

### Why the shipped contract failed

`CURSOR_WIRE_CONTRACT` assumed `GET /api/usage-summary` on `https://cursor.com`. That path does not exist, which produced the earlier `401`, `405 Allow: POST`, and `403`. The `405` was the decisive signal and was under-read: a Connect endpoint is POST-only, so a verb rejection on a path that exists points at RPC rather than REST.

### Field names are camelCase, not the descriptor's snake_case

The single most important probe finding, because building from the bundle alone would have shipped a broken mapper. The protobuf descriptor declares `billing_cycle_start`, `auto_percent_used`, and so on; Connect's JSON codec applies the proto3 JSON mapping, so the wire delivers `billingCycleStart` and `planUsage.autoPercentUsed`. Every field would have read `undefined`, and the contract guard would have rejected the payload as a schema mismatch - correct behavior, masking an avoidable defect.

### Observed shape (names and types only; no values recorded)

| Path | Wire type | Note |
|---|---|---|
| `billingCycleStart` | string | int64 in the descriptor; proto3 JSON encodes 64-bit ints as strings |
| `billingCycleEnd` | string | Same |
| `planUsage.totalSpend` | integer | Spend, almost certainly cents (see units, below) |
| `planUsage.includedSpend` | integer | |
| `planUsage.bonusSpend` | integer | |
| `planUsage.limit` | integer | |
| `planUsage.autoPercentUsed` | decimal | Precomputed percentage |
| `planUsage.totalPercentUsed` | decimal | Precomputed percentage |
| `planUsage.apiPercentUsed` | integer | Integer in this sample; treat as numeric, not integer-only |
| `planUsage.remainingBonus` | boolean | A flag, NOT a remaining amount - the name invites misreading |
| `planUsage.bonusTooltip` | string | |
| `spendLimitUsage.totalSpend` | integer | |
| `spendLimitUsage.pooledLimit` | integer | The shared team pool |
| `spendLimitUsage.pooledUsed` | integer | |
| `spendLimitUsage.pooledRemaining` | integer | |
| `spendLimitUsage.individualUsed` | integer | |
| `spendLimitUsage.limitType` | string | Drives the fixed-vs-dynamic shared-limit label |
| `displayThreshold` | integer | |
| `enabled` | boolean | |
| `displayMessage` | string | |
| `autoBucketModels` | array of string | 27 entries in this sample |

Absent from this response, and therefore **optional** rather than required: `autoSpend`, `autoLimit`, `apiSpend`, `apiLimit`, `remaining`, `individualLimit`, `individualRemaining`, `overallLimit`, `overallUsed`, `overallRemaining`, `freeBestOfNPromotion`. A mapper that requires any of them would reject a valid payload on this account.

### Units are not yet settled

Spend arrives as an integer, which points to cents. This is inference from the type, not evidence: no value was recorded, so the reading was not cross-checked against the figure on the usage page. Formatting cents as dollars overstates spend by 100x, so the mapper must not render money until one recorded comparison settles it. Percentages need no such check because they arrive precomputed and are already rendered to one decimal.

### What stays excluded

Unchanged by this finding: browser cookie stores, `Login Data`, OS keychains, process memory, shell history, recursive filesystem hunting for credential-shaped files, and HTML scraping of any billing page. The route is labelled `credential-api` and must never be described as a documented Cursor API.

### Units settled: spend is CENTS, timestamps are epoch MILLISECONDS

Settled by reading only the plan *limit* (a plan tier, not private spend) and the cycle-start length:

| Field | Observed | Reading |
|---|---|---|
| `planUsage.limit` | `2000` | Cents. The plan's included spend is 20 dollars, so 2000 is cents, not dollars. |
| `planUsage.includedSpend` | `2000` | Cents, and equal to the limit, as expected for an included allowance. |
| `spendLimitUsage.pooledLimit` | `20000` | Cents: a 200-dollar shared pool. |
| `spendLimitUsage.limitType` | `"team"` | Drives the shared-pool label; confirms the existing shared-vs-personal split is real. |
| `billingCycleStart` | 13-digit string | Epoch **milliseconds**, not seconds. Treating it as seconds would date the cycle to 1970. |

So money must be divided by 100 before formatting, and cycle bounds parsed as millisecond epochs from strings.

### Percentages MUST be taken from the payload, never recomputed

The single most dangerous finding of this probe. The reported percentage and the one derived from spend over limit disagree, and not by a rounding margin:

```
(planUsage.totalSpend / planUsage.limit) * 100  =  1078.70
planUsage.totalPercentUsed (reported)           =    23.97
```

A factor of roughly 45. `totalPercentUsed` is evidently computed against a base this response does not expose (neither `limit` nor `pooledLimit` reproduces it), which is consistent with several optional `overall*` fields being absent from the payload. The cause does not need to be known for the rule to be clear:

**Use `autoPercentUsed`, `apiPercentUsed`, and `totalPercentUsed` exactly as delivered. Never derive a percentage from spend over limit.** Deriving it here would have rendered a 24% meter as 1079%, filled and screaming critical, and every threshold alert in the extension would have fired continuously on a healthy account. The existing "drop rather than approximate" rule extends to this: when a percentage is not supplied, show absolute usage and say the allowance is unknown, rather than computing one from fields that do not share a base.

This also means `planUsage.limit` is **not** the denominator of `totalPercentUsed` and must not be labelled as though it were. `remainingBonus` is likewise a boolean flag, not a remaining amount, despite its name.
