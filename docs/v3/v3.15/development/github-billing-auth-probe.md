# GitHub Billing Authentication Probe

**Version:** v3.15.12 Phase 4 (T022)
**Documentary half (T022a) completed:** 2026-08-06
**Empirical half (T022c):** NOT RUN - maintainer-gated
**Mode:** First-party documentation review, plus a bounded one-read live probe pending

## The question

`extensions/github-usage-monitor/src/providers/auth.ts` records that VS Code GitHub sessions were never proven acceptable to the billing endpoints, and falls back to SecretStorage. T022 asks whether `vscode.authentication.getSession('github', scopes)` can authenticate the enhanced billing endpoints, and therefore whether the session path can be a default.

Endpoints in scope, from `src/providers/scope.ts`:

- `/users/{username}/settings/billing/usage`
- `/organizations/{org}/settings/billing/usage`
- `/enterprises/{enterprise}/settings/billing/usage`
- plus `.../billing/{ai_credit,premium_request}/usage` for Copilot

Test `/settings/billing/usage` first, because Actions usage is the primary feature. **Do not assume a result there transfers** to `ai_credit/usage`, `premium_request/usage`, or the preview `usage/summary` operation.

## Decision rule, fixed BEFORE reading evidence

Written first on purpose, so the evidence cannot be read to fit a preferred answer.

### Positive

A session is `supported` for one target and endpoint when **all** hold:

1. The OAuth call returns `200`.
2. The authenticated user holds the required billing role.
3. The account has enhanced billing where the endpoint requires it.
4. The verdict is recorded against that specific user, organization, or enterprise.

A `200` is decisive positive evidence **for the tested combination only**.

### Negative

A failing OAuth call establishes incompatibility only when **all three** hold:

1. A known-good **classic PAT control** returns `200` for the same account and endpoint.
2. The OAuth call fails.
3. The response headers or error identify a scope, OAuth-app-authorization, or token-class cause.

A single OAuth `403` or `404` is **not** sufficient. GitHub uses both for insufficient permissions, and organization OAuth-app restrictions and SSO authorization can independently block the "GitHub for VS Code" OAuth app.

### Documentary rejection

Where an endpoint reference explicitly states a token class does not work, treat it as unsupported without probing.

### Documentation conflict

Where first-party docs disagree and a live call returns `200`, record it as `empirically supported as of <date>; GitHub documentation is inconsistent` and **keep the fallback**. That is weaker evidence than a consistent documented contract.

## Three premises that were WRONG, and are corrected here

Recorded because each would have produced a wrong implementation, and one was a wrong *rule* rather than a wrong fact.

### 1. The endpoint reference cannot settle OAuth support

The REST reference's token section is titled **"Fine-grained access tokens for..."**. It enumerates fine-grained token support; it is not an exhaustive list of every accepted authentication class. Therefore:

> "OAuth app tokens are absent from that list" does **not** prove OAuth tokens are rejected.

Any rule of the form "the session path is unsupported because the docs do not list OAuth" rejects OAuth on **absence of evidence** and must not be used. The documented mechanism for discovering OAuth compatibility is the `X-Accepted-OAuth-Scopes` response header; `X-OAuth-Scopes` reports what the presented token actually carries.

### 2. A billing-related OAuth scope does exist

GitHub Enterprise Cloud documents:

- `manage_billing:enterprise` - read and write enterprise billing data
- `admin:enterprise` - includes `manage_billing:enterprise`
- `read:enterprise` - reads the enterprise profile, and does not itself claim billing access

For organization and personal billing usage there is no clearly documented billing-specific OAuth scope, which still does not prove OAuth is unsupported: the operation may accept an existing scope such as `read:org`, `admin:org`, `read:user`, or `user`. The accepted-scope header is what determines that, not the prose.

Fine-grained PATs and GitHub Apps use **permissions**; OAuth apps use **scopes**. Separate vocabularies with no guaranteed one-to-one mapping - but one endpoint can support both systems. So the question is not "which OAuth scope equals `Administration: read`", it is "what does this operation report in `X-Accepted-OAuth-Scopes`".

### 3. VS Code's provider has no fixed scope allowlist

VS Code's built-in GitHub authentication provider identifies its client id as a GitHub **OAuth app**. Its session-creation path accepts caller-supplied scopes, sorts and joins them, and passes the string into the GitHub login flow, which forwards it as the `scope` parameter. No fixed allowlist filters it. GitHub may still reject, normalize, or decline the request, and the user may reduce scopes at consent.

The provider still **cannot** mint a fine-grained PAT or a GitHub App token; its internal PAT flow is manual and disabled for supported GitHub.com clients, and is not selectable through `getSession()`.

One further trap: `AuthenticationSession.scopes` reflects the scopes the **extension requested**, not what GitHub granted. Granted scopes must be read from `X-OAuth-Scopes` on an API response.

## Documentary compatibility matrix (T022a)

| Level | Endpoint reference says | Required permission / role | Documentary verdict |
|---|---|---|---|
| User | GitHub App user access tokens and fine-grained PATs work | user `Plan: read` | **Conflicted.** The usage-reporting tutorial says billing usage endpoints do not support fine-grained PATs and directs users to a classic PAT. OAuth: undetermined, must be probed. |
| Organization | GitHub App user access tokens, GitHub App installation tokens, and fine-grained PATs work | organization `Administration: read` **and** an organization administrator role | **Conflicted**, same tutorial contradiction. OAuth: undetermined, must be probed. |
| Enterprise | Explicitly does **not** work with GitHub App user tokens, GitHub App installation tokens, or fine-grained PATs | enterprise owner or billing manager | **Documentary negative for fine-grained and App tokens.** Never offer or probe them. Classic PAT is the documented baseline. OAuth: `manage_billing:enterprise` exists and must be probed. |

**The documentary half does not settle T022 for user or organization scope.** GitHub's own first-party documentation conflicts, so only a live probe with a control can resolve it.

## Probe matrix to run (T022c)

| Level | VS Code OAuth candidates | Classic PAT control | Fine-grained PAT |
|---|---|---|---|
| User | `read:user`, then `user` only if the accepted-scope header requires it | **Required baseline** | `Plan: read` - probe, because the docs conflict |
| Organization | `read:org`, then `admin:org` only if the accepted-scope header requires it | **Required baseline** | `Administration: read` - probe, because the docs conflict |
| Enterprise | `manage_billing:enterprise`, then `admin:enterprise` only if required | **Required baseline** | **Do not offer** - documentary negative |

The OAuth scopes are **probe candidates**, not claims that the endpoint accepts them.

Do **not** immediately retry with the broader scope because the narrower one failed. Inspect `acceptedOAuthScopes`, `grantedOAuthScopes`, and the error first, and escalate only when the evidence says the broader scope is required.

Use an account that holds the correct owner / administrator / billing-manager role, has enhanced billing enabled for `/usage`, and can produce a `200` with the control credential. Otherwise a negative result is ambiguous and must not be recorded as a verdict.

### How to run it

The harness is `extensions/github-usage-monitor/src/providers/authProbe.ts`. It is pure and injectable: `probeWithToken` takes a token and a fetch, and `probeVsCodeSession` takes a session provider so the module never imports `vscode`. `toSanitizedRecord` is the only supported way to serialize a result, and `test/auth-probe.test.ts` asserts that its output cannot contain a token, an `Authorization` header, or a success body.

Record the emitted sanitized fields verbatim in the results table below.

### What is recorded, and what is never recorded

Recorded: timestamp, API version, level, endpoint path, credential class, requested scopes, provider-reported scopes, HTTP status, `X-OAuth-Scopes`, `X-Accepted-OAuth-Scopes`, `X-Accepted-GitHub-Permissions`, `X-GitHub-Request-Id`, `error.message`, `error.documentation_url`.

Never recorded: the access token, the `Authorization` header, any successful response body, organization billing data, repository usage data.

API version: `2026-03-10`, matching `GITHUB_API_VERSION` in `src/providers/github.ts`. Do not copy the older version shown in the tutorial example.

## Interpretation table

| Observation | Verdict |
|---|---|
| Classic PAT `200`, OAuth `200` | Session usable **for this target and endpoint** |
| Classic PAT `200`, OAuth `403`, accepted-scope header names a scope not granted | OAuth may work with a different scope; escalate to that scope only |
| Classic PAT `200`, OAuth error mentions app approval or SSO | Mechanism may work, but the VS Code OAuth app is blocked for this organization |
| Classic PAT `200`, fine-grained `403` with an integration or PAT permission error | Fine-grained path unsupported here, or the permission is misconfigured |
| Both classic PAT and OAuth fail | **Draw no token-class conclusion.** Check role, endpoint, enhanced billing, and the owner name first |
| OAuth `401` | Invalid, revoked, or expired session. **Not** evidence about token classes |
| OAuth `404` | Ambiguous; GitHub uses `404` for insufficient access |
| Enterprise fine-grained | Skipped by documentary rejection |

## Results (T022c)

**Not yet run.** Fill one row per (level, credential class) actually attempted.

| Date | Level | Endpoint | Credential class | Requested scopes | Status | `X-OAuth-Scopes` | `X-Accepted-OAuth-Scopes` | `X-Accepted-GitHub-Permissions` | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | |

## Finding and decision

**Interim finding, 2026-08-06 (documentary half only).** GitHub's endpoint reference and its usage-reporting tutorial currently disagree about fine-grained PAT support for user and organization billing usage. The enterprise endpoint reference explicitly rejects fine-grained PATs and GitHub App tokens. GitHub documents the OAuth scope `manage_billing:enterprise`. VS Code's built-in provider uses a GitHub OAuth app and forwards caller-requested scopes; it cannot mint a fine-grained PAT through `getSession()`. The endpoint reference's fine-grained-token list is **not** sufficient evidence that OAuth is unsupported.

**Decision.** Authentication resolves **per account level and account identity**, not by one global default. A VS Code OAuth session is enabled for a target only after that target and endpoint return `200`. A negative OAuth verdict is conclusive only when a classic-PAT control succeeds on the same target and the headers or error identify a scope, app-authorization, or token-class cause. Enterprise fine-grained PAT authentication is not offered. User and organization fine-grained support remains **conditional** while GitHub's documentation is inconsistent. Failures are surfaced explicitly; credentials are never silently broadened or silently replaced.

This determines T023's shape: **per-target capability resolution with explicit fallback**, not a compile-time auth default.

## Sources

- [GitHub REST: billing usage](https://docs.github.com/en/rest/billing/usage)
- [GitHub REST: billing usage (Enterprise Cloud)](https://docs.github.com/en/enterprise-cloud@latest/rest/billing/usage)
- [Automating usage reporting](https://docs.github.com/en/enterprise-cloud@latest/billing/tutorials/automate-usage-reporting)
- [Scopes for OAuth apps](https://docs.github.com/en/enterprise-cloud@latest/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps)
- [Authenticating to the REST API](https://github.com/github/docs/blob/main/content/rest/authentication/authenticating-to-the-rest-api.md)
- [VS Code built-in GitHub authentication: config](https://github.com/microsoft/vscode/blob/main/extensions/github-authentication/src/config.ts)
- [VS Code built-in GitHub authentication: provider](https://github.com/microsoft/vscode/blob/main/extensions/github-authentication/src/github.ts)
- [VS Code built-in GitHub authentication: flows](https://github.com/microsoft/vscode/blob/main/extensions/github-authentication/src/flows.ts)
