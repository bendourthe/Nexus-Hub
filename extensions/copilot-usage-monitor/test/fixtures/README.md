# Copilot usage monitor test fixtures

Sanitized GitHub responses for the Copilot usage monitor's provider tests (plan `v4.13.7`, sub-task 1.2). The settled meaning of every field is in `docs/releases/v4/v4.13/development/v4.13.7-decisions.md`, section `## Copilot usage monitor`.

## Captured fixtures

The maintainer captured these on 2026-10-01 between 23:41 and 23:58 UTC, on the first day of the monthly pool cycle, with a capture script run in a separate PowerShell window. The agent never saw the tokens.

| File | Endpoint | Account | Token that returned HTTP 200 |
|---|---|---|---|
| `copilot-internal-user.personal.json` | `GET https://api.github.com/copilot_internal/user` (undocumented) | Copilot Free personal account (`access_type_sku` `free_limited_copilot`) | Classic personal access token with no scopes, sent as `Authorization: token <value>` |
| `copilot-internal-user.business-member.json` | `GET https://api.github.com/copilot_internal/user` (undocumented) | Copilot Business seat holder (`access_type_sku` `copilot_for_business_seat_quota`) | Classic personal access token with no scopes, sent as `Authorization: token <value>` |
| `ai-credit-usage.json` | `GET https://api.github.com/organizations/{org}/settings/billing/ai_credit/usage?year=2026&month=10` (documented) | Organization owner | Fine-grained token, resource owner the organization, Organization permissions Administration read and GitHub Copilot Business read |
| `copilot-billing.json` | `GET https://api.github.com/orgs/{org}/copilot/billing` (documented) | Organization owner | The same fine-grained token |

The two organization calls used the documented headers `Accept: application/vnd.github+json` and `X-GitHub-Api-Version: 2026-03-10`.

## Synthetic fixtures

Each file whose name contains `.synthetic.` is built by Nexus-Hub from a captured file above, keeping every field name, nesting, and number type, and changing only the quantities listed. They exist because the live capture, taken on day one of the cycle, has a used figure far below the pool.

| File | Built from | Changed values | Exercises |
|---|---|---|---|
| `ai-credit-usage.near-limit.synthetic.json` | `ai-credit-usage.json` | `grossQuantity` and `discountQuantity` 13,200; amounts at 0.01 per credit; net 0 | 13,200 of 13,300 = 99.25%, at the handoff threshold |
| `ai-credit-usage.over-pool.synthetic.json` | `ai-credit-usage.json` | `grossQuantity` 13,450.5; `discountQuantity` 13,300 (the full pool); `netQuantity` 150.5; amounts at 0.01 per credit | Pool exhausted, with metered usage beyond it; used is capped by the discount, so the percentage is 100 |
| `copilot-billing.seat-added.synthetic.json` | `copilot-billing.json` | `added_this_cycle` 1, `total` 8, `active_this_cycle` 5 | The `approximate` flag when a seat was added this cycle |

## Sanitization

- `login` is `example-user` and every organization login is `example-org`.
- Every numeric `id` is `0`, and `analytics_tracking_id` is `example-id`.
- Every URL under `endpoints` is `https://example.invalid/`.
- No token, email address, or real name is present. Every other field is as GitHub returned it.
- The files are compact UTF-8 JSON without a byte-order mark.

The Phase 2 leak test treats `example-user`, `example-org`, and `example-id` as identity placeholders that must never appear in a log line, error message, rendered view, settings write, or state file.
