# GitHub Usage Data Contract

**Version:** v3.15.8
**API version:** `2026-03-10`
**Verified against official GitHub documentation:** 2026-08-02
**Fixture root:** `tests/fixtures/github-usage/`

## Decision

GitHub Usage Monitor (see the dated correction below) reads documented GitHub REST billing endpoints only. It selects one explicit billing scope (`user`, `organization`, or `enterprise`), stores a user-supplied credential only in VS Code SecretStorage, and never scrapes GitHub.com, reads browser cookies, or converts absolute consumption into a percentage without a verified denominator. Unsupported access falls back to cached data and optional manual allowances, with source and freshness shown to the user.

> **Correction, 2026-08-09 (v3.16.3 Phase 1).** This paragraph previously opened "GitHub Billing Usage (named 'GitHub Usage Monitor' before v3.15.12; extension id `nexus-hub.github-usage-monitor` unchanged)". v3.16.3 **reverted** the name to **GitHub Usage Monitor**, for consistency with the Claude, Codex, and Cursor usage monitors. The v3.15.12 rename and this reversal are both left visible on purpose: a reader of the older plan must be able to see what happened and why, rather than finding a document silently rewritten to disagree with it. The extension id `nexus-hub.github-usage-monitor` was never changed in either direction. v3.16.3 additionally moved the command ids and configuration keys to the `githubUsageMonitor.*` prefix, with a one-time migration that carries every user-set value across on first activation; the old `githubUsage.*` keys are left readable for one release and their deletion is a v3.17.0 follow-up.

No authorized billing credential or account scope was supplied for Phase 1, so no live billing request was made. The fixture set uses sanitized shapes derived from GitHub's published examples. The bounded probe below is the approved procedure for a later explicitly authorized run.

## Account Scope

| Scope | Endpoint prefix | Authorization | Billing boundary |
|---|---|---|---|
| Personal | `/users/{username}/settings/billing` | Fine-grained PAT or GitHub App user token with user `Plan: read` | Includes only Copilot and Actions usage billed directly to that personal account |
| Organization | `/organizations/{org}/settings/billing` | Fine-grained PAT, GitHub App user token, or installation token with organization `Administration: read`; caller must be an organization administrator | Includes usage billed to the organization; managed Copilot must be queried here or at enterprise scope |
| Enterprise | `/enterprises/{enterprise}/settings/billing` | Enterprise owner or billing manager authorization; billing usage endpoints do not accept fine-grained PATs or GitHub App tokens | Includes enterprise-billed usage and may aggregate cost centers and organizations |

The Authorization column lists the token classes the **REST endpoint reference** names, and it is not exhaustive. Two corrections recorded in v3.15.12 (T022a):

- **Classic PATs are also a valid credential class**, and GitHub's own "Automating usage reporting" tutorial directs users to one, stating that the billing usage endpoints do not support fine-grained PATs. That **conflicts** with the endpoint reference for personal and organization scope. The conflict is recorded rather than resolved in either direction; see [github-billing-auth-probe.md](github-billing-auth-probe.md).
- **OAuth-app tokens are not excluded by that column's silence.** The reference's token section is titled "Fine-grained access tokens for...", so it enumerates fine-grained support only. Whether an OAuth token (such as a VS Code GitHub session) is accepted is determined by the `X-Accepted-OAuth-Scopes` response header, not by absence from that list. Enterprise scope is the one documentary negative, and it applies to fine-grained PATs and GitHub App tokens, not to OAuth.

User endpoints must never be presented as managed Copilot totals. A user whose Copilot license is billed by an organization or enterprise can legitimately receive an empty personal Copilot result.

## Endpoint Contract

| Metric | User | Organization | Enterprise | Availability / query |
|---|---|---|---|---|
| AI credits | `/ai_credit/usage` | `/ai_credit/usage` | `/ai_credit/usage` | Past 24 months; `year`, `month`, optional `day`, `model`; organization also supports `user` and `product` |
| Legacy premium requests | `/premium_request/usage` | `/premium_request/usage` | Not used unless official enterprise documentation exposes it at implementation time | Past 24 months; legacy Copilot Pro and Pro+ annual plans only after June 1, 2026 |
| Detailed metered usage | `/usage` | `/usage` | `/usage` | Enhanced billing platform only; current-month query by `year` and `month`; enterprise may filter by cost center |
| Aggregated usage | `/usage/summary` | `/usage/summary` | `/usage/summary` | Public preview; past 24 months; filter by `year`, `month`, `day`, product/SKU where supported |

Every request sends `Accept: application/vnd.github+json` and `X-GitHub-Api-Version: 2026-03-10`. The provider treats fields not named below as additive and ignores them while preserving the raw fixture for diagnostics.

## Raw Response Shapes

AI-credit and premium-request reports use an account envelope (`user`, `organization`, or `enterprise`), optional `timePeriod`, and `usageItems`. Current items may include `product`, `sku`, `model`, `unitType`, `pricePerUnit`, `grossQuantity`, `grossAmount`, `discountQuantity`, `discountAmount`, `netQuantity`, and `netAmount`.

Detailed metered usage uses `usageItems` containing `date`, `product`, `sku`, `quantity`, `unitType`, amounts, and optional repository or organization dimensions. Summary usage uses the account envelope, optional `timePeriod`, and aggregate quantity/amount fields.

The provider must tolerate:

- Missing optional fields and empty `usageItems`.
- Product and SKU casing differences.
- `credits` and `ai-credits` unit aliases.
- Future top-level and item-level fields.
- Numeric zero as real usage, while distinguishing it from unavailable data.

## Normalized Model

| Field | Meaning | Source rule |
|---|---|---|
| `scope` | `user`, `organization`, or `enterprise` | Explicit configuration only |
| `accountLabel` | Display-safe configured account label | Configuration, never inferred from unrelated payload data |
| `periodStart` / `periodEnd` | Reporting window | API time period when present; otherwise the requested UTC month |
| `copilot.unit` | `ai-credits` or `premium-requests` | Endpoint and normalized `unitType` |
| `copilot.used` | Current-period gross consumption | Sum `grossQuantity`; fall back to `quantity` only for detailed usage |
| `actions.minutesUsed` | Current-period Actions minutes | Sum Actions items whose `unitType` is `minutes` |
| `actions.storageUsed` | Current-period Actions storage | Sum Actions storage items without converting unlike units silently |
| `grossAmount` / `discountAmount` / `netAmount` | Billing amounts | Sum matching numeric fields independently; never derive discount from subtraction when fields are absent |
| `allowance` | Verified limit or budget denominator | API value when explicitly present, otherwise a matching manual setting, otherwise `null` |
| `percentage` | Used divided by allowance | Present only when `allowance` is finite and greater than zero |
| `source` | `api`, `cache`, or `manual` | Actual successful source |
| `fetchedAt` | Data freshness | Successful fetch timestamp or cached snapshot timestamp |

An unknown allowance is not zero. When `allowance` is `null`, the UI shows an absolute meter such as `125 AI credits used` and does not render `0%`, `100%`, or an invented reset date.

## Allowances and Reset Semantics

- GitHub plan allowances vary by product, plan, billing entity, and transition state. Static plan tables are guidance, not a verified account denominator.
- Organization and enterprise AI-credit pools aggregate included credits across assigned licenses. A per-user plan allowance must not be multiplied or inferred without account-level evidence.
- Legacy premium-request counters reset on the first day of each month at `00:00:00 UTC`.
- Actions included minutes are monthly, while storage accounting and billing can use different units. Preserve each returned unit and require an explicit matching allowance.
- The provider uses an API-supplied reset or period boundary when available. Otherwise it may show the requested calendar-month boundary as reporting context, but it must label it as a reporting period rather than an account quota reset.

## Error Contract

| Status | Classification | User-facing behavior |
|---|---|---|
| `401` | Invalid or expired credential | Clear SecretStorage credential guidance; keep last good cache; do not retry automatically in a loop |
| `403` | Missing permission, SSO authorization, account role, enhanced-billing access, or rate limit | Inspect `X-Accepted-GitHub-Permissions`, `X-GitHub-SSO`, and rate-limit headers; preserve cache; explain the scoped requirement |
| `404` | Wrong account slug, hidden private resource, unavailable endpoint, or authorization masking | Do not treat as zero; ask the user to verify scope and authorization |
| `429` | Primary or secondary rate limit | Honor `Retry-After`, otherwise `X-RateLimit-Reset`; show stale cache and next eligible refresh |
| `500` / `503` | GitHub service failure | Fail soft to cache and retry only through bounded backoff |
| Schema mismatch | Public-preview or additive contract drift | Keep the raw response out of telemetry, show a typed degraded state, and retain cache/manual fallback |

## Bounded Authorized Probe

The probe is manual and opt-in. It must never discover credentials from browsers, Git credential stores, shell history, or unrelated environment variables.

1. Obtain explicit authorization for one account scope and confirm the least-privilege token type.
2. Read the token from an interactive secret prompt or VS Code SecretStorage. Never place it in a command argument, file, fixture, log, or environment dump.
3. Request the current UTC year and month from the matching AI-credit, legacy premium-request when relevant, and usage-summary endpoints. Stop after one request per endpoint.
4. Emit only HTTP status, response field names, `product`, `sku`, `unitType`, aggregate quantities, aggregate amounts, `timePeriod`, and rate-limit metadata. Redact account names, repository names, user names, cost-center IDs, request IDs, URLs containing account slugs, and every credential/header value.
5. On `401`, `403`, `404`, or `429`, stop probing that scope. Record the typed limitation and use SecretStorage plus cache/manual fallback.
6. Compare only the sanitized shape with the committed fixtures. Never commit the live response.

Example safe output shape:

```json
{
  "scope": "organization",
  "status": 200,
  "topLevelFields": ["timePeriod", "organization", "usageItems"],
  "itemFields": ["product", "sku", "unitType", "grossQuantity", "netAmount"],
  "aggregates": [{"product": "Actions", "unitType": "minutes", "quantity": 120}],
  "rateLimit": {"remaining": 4998, "resetEpoch": 1785686400}
}
```

## Fixture Inventory

| Fixture | Contract branch |
|---|---|
| `current-ai-credits.json` | Personal current AI-credit response |
| `legacy-premium-requests.json` | Legacy request-based Copilot response |
| `actions-minutes-storage.json` | Actions minutes and storage with gross, discount, and net amounts |
| `managed-copilot.json` | Organization-billed managed Copilot response |
| `unknown-allowance.json` | Consumption exists but denominator is explicitly unknown |
| `empty-month.json` | Valid empty current-month response |
| `error-401.json`, `error-403.json`, `error-404.json`, `error-429.json` | Typed failure envelopes |
| `additive-fields.json` | Unknown top-level and item-level fields are tolerated |

## Sources

- [GitHub REST billing usage](https://docs.github.com/en/rest/billing/usage?apiVersion=2026-03-10)
- [GitHub Enterprise Cloud REST billing usage](https://docs.github.com/en/enterprise-cloud@latest/rest/billing/usage?apiVersion=2026-03-10)
- [Authenticating to the REST API](https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api?apiVersion=2026-03-10)
- [Rate limits for the REST API](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
- [Monitoring GitHub AI Credits usage](https://docs.github.com/en/copilot/how-tos/manage-and-track-spending/monitor-ai-usage)
- [Legacy premium-request monitoring](https://docs.github.com/en/copilot/reference/copilot-billing/request-based-billing-legacy/monitor-premium-requests)
- [Product usage included with each plan](https://docs.github.com/en/billing/reference/product-usage-included)
