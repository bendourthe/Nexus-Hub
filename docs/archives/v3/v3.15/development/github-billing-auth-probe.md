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

**Run the classic-PAT control first, for each level you test.** Without a `200` from it on the same target, a failing result from any other credential class is uninterpretable.

The PAT legs run as a standalone script, no editor needed. From `extensions/github-usage-monitor`, after `npm run compile`:

```powershell
$env:GITHUB_BILLING_PROBE_TOKEN = "ghp_..."
node scripts/probe-billing-auth.js --level organization --name acme --credential classic-pat
```

```bash
GITHUB_BILLING_PROBE_TOKEN=ghp_... node scripts/probe-billing-auth.js --level user --name octocat --credential classic-pat
```

The token comes from the environment so it never lands in shell history as an argument. The script prints the sanitized record plus a paste-ready results row, refuses `enterprise` + `fine-grained-pat` before issuing a request, and never prints the token or a thrown request object.

**The VS Code OAuth leg cannot run from a script**, because a session is obtainable only inside the editor. Run the PAT controls first; the in-editor diagnostic is the remaining piece.

The harness itself is `src/providers/authProbe.ts`: pure and injectable, so `probeWithToken` takes a token and a fetch while `probeVsCodeSession` takes a session provider, and the module never imports `vscode`. `toSanitizedRecord` is the only supported serialization, and `test/auth-probe.test.ts` asserts its output cannot contain a token, an `Authorization` header, or a success body, and that its key set equals the approved set exactly.

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

**Run 2026-08-06** against `/settings/billing/usage`, API version `2026-03-10`, using a GitHub CLI OAuth-app token (`gho_`) carrying `gist, read:org, repo, workflow`.

| Date | Level | Endpoint | Credential class | Requested scopes | Status | `X-OAuth-Scopes` | `X-Accepted-OAuth-Scopes` | `X-Accepted-GitHub-Permissions` | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 2026-08-06 | user | `/users/bendourthe/settings/billing/usage` | `gh-oauth` | - | **404** | gist read:org repo workflow | **user** | - | Scope insufficient, **not** a class rejection |
| 2026-08-06 | organization | `/organizations/Tidal-Medical/settings/billing/usage` | `gh-oauth` | - | **200** | gist read:org repo workflow | **admin:org repo** | - | **SUPPORTED** |
| 2026-08-06 | organization | `/organizations/EMVI-AI/settings/billing/usage` | `gh-oauth` | - | **200** | gist read:org repo workflow | admin:org repo | - | **SUPPORTED** |
| 2026-08-06 | organization | `/organizations/smesh-stanford/settings/billing/usage` | `gh-oauth` | - | **200** | gist read:org repo workflow | admin:org repo | - | **SUPPORTED** |
| - | enterprise | - | - | - | - | - | - | - | Not probed: no enterprise slug on this account |
| - | any | - | `vscode-oauth` | - | - | - | - | - | Not probed: a session requires the editor. See "What remains" |

### What these results establish

1. **OAuth-app tokens ARE accepted by the enhanced billing usage endpoint.** Three independent `200`s. This settles the question the documentary half could not, and it **empirically confirms** the correction to premise 1: the endpoint reference's fine-grained-only token list is not exhaustive, and OAuth's absence from it was never a rejection. Any implementation built on "billing usage is fine-grained-PAT-only" would have been wrong.
2. **The accepted OAuth scopes are now known from GitHub itself**: `user` for user scope, and `admin:org` **or** `repo` for organization scope.
3. **`repo` alone sufficed for organization billing usage.** Worth noting because `repo` is a scope VS Code's provider requests routinely, which is what makes the session path plausible rather than speculative.
4. **The user-scope `404` was a scope insufficiency, diagnosed from the header, not an uninterpretable negative.** The token lacked `user`. GitHub returned `404` rather than `403` for insufficient access, exactly the ambiguity the interpretation table warns about - and the accepted-scope header is what resolved it. No classic-PAT control was needed, because the decision rule requires a control only for a *negative* verdict, and this is a positive-with-diagnosis.
5. **No per-organization variation was observed** across three organizations. That does not falsify the need for per-target resolution: OAuth-app restrictions and SSO enforcement are per-organization settings that can differ on other accounts. It means the risk was not exercised here, not that it is absent.

### What remains

- **VS Code's own OAuth app is still unprobed.** OAuth-app authorization and SSO grants are per-app, so a `gh` result does not transfer to `GitHub for VS Code`. What the `gh` result does establish is that the *token class* is accepted, so the remaining question is narrow: can VS Code's provider obtain `repo` (org) or `user` (user), and is its app authorized for the target organization. That needs the in-editor leg.
- **Enterprise scope is unprobed**, and its fine-grained/App-token rejection remains documentary. OAuth at enterprise scope is untested; `manage_billing:enterprise` is the candidate.
- **A classic-PAT control was not needed for these rows** and was not run. It becomes necessary only if a future OAuth attempt fails and the failure has to be attributed.

## Finding and decision

**Empirical finding, 2026-08-06 (supersedes the interim finding below).** OAuth-app tokens **are** accepted by the enhanced billing usage endpoint: three organization `200`s with a GitHub CLI OAuth token. GitHub's own `X-Accepted-OAuth-Scopes` reports `user` for user scope and `admin:org` or `repo` for organization scope, and `repo` alone was sufficient. The blocking premise is therefore resolved in the **affirmative**: a VS Code session is a viable auth path, not a dead end, and the "fine-grained-PAT-only" reading of the endpoint reference is empirically dead.

The narrow question left is per-app rather than per-class: whether `GitHub for VS Code` can obtain `repo` / `user` and is authorized for the target organization. Enterprise scope is unprobed.

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
