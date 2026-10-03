# Decision: Ship a Copilot usage monitor that shows a percentage only from figures GitHub serves

Status: proposed - a Copilot usage monitor shows a personal quota percentage or an organization pool percentage (documented usage over served seats times the published per-seat rate), and credits used with no percentage everywhere else; data contract verified against paired API and billing-page readings on 2026-10-01 and 2026-10-02

## Problem

The native Copilot Status item in VS Code shows AI credits used with no percentage, so a user cannot see how close they are to their plan quota or to their organization's shared pool. Nexus-Hub withdrew its last GitHub monitor in v3.18.2 ([withdrawal record](../../implemented/architecture/2026-08-22-withdraw-the-github-usage-monitor.md)) because the Actions allowance it showed had to be reconstructed from data GitHub does not serve, and the reconstruction reported 0% on an exhausted allowance. That record permits a GitHub monitor again only "when GitHub publishes an API that returns included-usage consumed and included-usage total for a scope". This record states why a Copilot monitor meets that condition where the Actions monitor did not, and what would force its withdrawal. Evidence and quotes are in `docs/releases/v4/v4.13/development/v4.13.7-decisions.md`, section `## Copilot usage monitor`.

## Proposal

Add `extensions/copilot-usage-monitor/` (extension id `nexus-hub.copilot-usage-monitor`), mirroring the Claude and Codex monitors' status bar, dashboard, and settings. It shows one of three views:

1. **Personal plan**: the percentage of the plan quota, from `GET https://api.github.com/copilot_internal/user` with the user's VS Code GitHub session, the endpoint the Copilot extension's own usage popup reads. The endpoint is undocumented and treated as fragile: unknown fields are ignored, and a response with no quota field shows credits used with no percentage. A percentage is shown only for a quota GitHub marks limited (`unlimited` false, `entitlement` above 0), as the Copilot Free capture of 2026-10-01 serves. The extension reads the GitHub account the user pins for it in VS Code (Accounts > Manage Extension Account Preferences), never passes an account of its own choosing, and never reads the open repository's remote, the git identity, or the `gh` login, so a user whose Copilot seat is on a work account sees that seat's usage while working in a personal repository. Background refreshes call `getSession("github", [], { silent: true })`, which matches the pinned account's existing session of any scope; only the user's own "Sign in" click requests `["read:user"]`.
2. **Organization pool** (opt-in, owner or administrator only): used is the sum of `usageItems[].discountQuantity` for Copilot AI-credit items from the documented `GET /organizations/{org}/settings/billing/ai_credit/usage`; total is `GET /orgs/{org}/copilot/billing` `.seat_breakdown.total` times the per-seat rate GitHub publishes for the plan (1,900 Business, 3,900 Enterprise). The total is labeled approximate whenever a seat was added or is pending cancellation this cycle, because GitHub documents that added seats grow the pool immediately and removed seats do not shrink it until the next cycle. The owner connects once by pasting a read-only fine-grained token, stored in VS Code secret storage and sent only to `api.github.com`.
3. **Member without billing access**: credits used, no percentage. A Business seat's response marks every quota `unlimited` with `entitlement` 0, no documented endpoint lets a member read a user-level budget, and the monitor never divides by the per-seat rate to invent a "fair share".

The monitor writes a percentages-only state file, `~/.nexus-hub/state/usage-probe/copilot.json`, so the v4.13.7 handoff guard can read Copilot usage without ever holding a GitHub token.

**Reopen answer (verified).** Consumed is served by a documented endpoint. Total is a served seat count times a constant GitHub publishes on its own billing page. Unlike the Actions case, no input is inferred from present-day state and applied to historical line items. The condition is therefore met for the organization pool and for a personal plan whose quota GitHub serves, and not met for a member without billing access, who gets no percentage. The paired reading agreed exactly: the usage API at 2026-10-01 23:57 UTC summed 0.907 discounted credits on one `Copilot AI Credits` line item with net 0, and the organization's AI usage page at about 2026-10-02 00:05 UTC showed 0.91 included credits in its breakdown (rounded to "1 / 13,300" in its headline), a 13,300-credit pool (7 seats x 1,900), $0.00 additional usage, and a November 1, 2026 reset. Two verification items stay open and are not failures: the pair was taken on the cycle's first day with under one credit used, so Phase 2 repeats it under real use; and no seat was added this cycle, so the proration of an added seat is still unobserved and stays labeled approximate.

With this monitor Nexus-Hub ships four usage monitors again (Claude, Codex, Cursor, Copilot).

## Alternatives considered

**Divide a member's personal credits by the per-seat rate as a "your share" percentage.** Declined: the pool is shared, so a member's 1,900 is not an allowance they own. The percentage would be a fabricated denominator, the same class of confident wrong number that withdrew the Actions monitor.

**Scrape the billing page.** Declined for the reasons in the withdrawal record: the page needs a browser session cookie that an extension does not hold, and its HTML is an undocumented surface with no stability contract.

**A one-click VS Code GitHub sign-in with organization-admin scope.** Declined for now by the maintainer on 2026-09-28: it asks for broader permission than a read-only fine-grained token, it is untested, and the organization may have to approve VS Code's sign-in application before it works. A pasted fine-grained token with "Administration" read and "GitHub Copilot Business" read is narrower and its expiry is the owner's choice.

**Use only the documented per-user endpoint, `GET /users/{username}/settings/billing/ai_credit/usage`, for the personal view.** Kept as the fallback for the used figure, not chosen as the primary: it serves credits used but no quota, so on its own it cannot produce a percentage.

**Infer the GitHub account from the open repository's remote, the git identity, or the `gh` login.** Declined by the maintainer on 2026-10-01: a user whose Copilot seat is on a work account and whose projects live on a personal account would see the bar change meaning with every repository, and reading the `gh` login means reading a credential store outside VS Code. The per-extension account preference already answers "which account" once, in VS Code's own UI.

**No monitor.** Declined: the native Copilot Status item shows credits used with no percentage, which is the gap this closes; and the handoff guard needs a Copilot percentage to act at the threshold.

## Acceptance criteria

- On a personal account the status bar shows a percentage computed from the quota and used fields GitHub returns, with no constant supplied by Nexus-Hub.
- On a connected organization the status bar shows the pool percentage from the documented usage endpoint and the served seat count, and marks it approximate under the seat-change rule.
- On a member account without billing access the status bar shows credits used and no percentage.
- With a work and a personal GitHub account both signed in and the extension pinned to the work account, opening a repository whose remote and git identity belong to the personal account still shows the work account's usage; switching the pin switches the view with no workspace change. A Phase 2 test asserts this, and a static check finds no read of git config, a remote URL, or the `gh` login in the extension source.
- Used credits display with two decimals, with the percentage computed from the unrounded sum, because GitHub's page headline rounds to whole credits while its breakdown shows two decimals.
- No GitHub token appears in settings, logs, the state file, or the repository, and the organization token is sent only to `api.github.com`.
- `v4.13.7-decisions.md` records, for each figure, the endpoint, the documentation URL or "undocumented", a sanitized sample, and a billing-page reading with both timestamps.

## Risks

- **The personal endpoint is undocumented.** It can change shape or start rejecting the VS Code session without notice. Mitigation: unknown fields ignored, no-quota responses show credits used only, and the documented per-user usage endpoint remains as the used-figure fallback.
- **Discount reason is not in the line-item schema.** If GitHub starts discounting Copilot usage for a second reason (a promotion, a free model), summing `discountQuantity` overstates pool use. Mitigation: sum only Copilot AI-credit SKUs observed in the capture, and compare against the billing page on each fresh capture.
- **Proration and removed seats.** GitHub does not document whether an added seat contributes a full or prorated allowance, and a seat removed this cycle may vanish from `seat_breakdown.total` while still counting toward the pool. Mitigation: the approximate label and a dashboard note; the percentage can read high, never silently low by more than the removed seats' allowance.
- **The published rate changes.** Mitigation: the rate table lives in one place with its source URL and verification date, and is re-checked against the billing page at each release that touches the monitor.
- **What forces withdrawal**: the API sum and the billing page diverge beyond normal use between readings minutes apart, on a reproducible basis; or GitHub stops serving one of the two numbers. The affected view then drops to credits used without a percentage, and if both views lose their percentage the monitor is withdrawn the same way the Actions monitor was.

## Amendment: token-free connect and percent-only display (2026-10-02, v4.13.8 Phase 6)

The maintainer, an owner of a Business organization (7 seats, a 13,300-credit pool), reported on 2026-10-02 that the shipped monitor showed "0.00 credits used this month", "no percentage to show", and "Not connected", and that Connect asked for a typed organization login and a pasted token with no link or steps. The maintainer then decided: ship the fix in v4.13.8; try a token-free route first and accept a token only when no token-free route works, created with the longest expiry GitHub allows because it is read-only; and show only percentages, with `--% (month)` before the organization is connected or for a member who is not an owner. This amendment supersedes three earlier choices in this record: item 3's credits-used member view, the pasted-token-only connect in item 2, and the declined one-click sign-in.

**Facts verified 2026-10-02 against official documentation:**

- Pre-filled fine-grained token page ([GitHub, managing personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)): base `https://github.com/settings/personal-access-tokens/new` with `name` (40 characters at most), `description`, `target_name` (the user or organization), `expires_in` (an integer from 1 to 366, or `none`), and permission parameters set to `read`, `write`, or `admin`, including `organization_administration` ("Administration") and `organization_copilot_seat_management` ("GitHub Copilot Business").
- `GET /orgs/{org}/copilot/billing` ([GitHub, Copilot user management](https://docs.github.com/en/rest/copilot/copilot-user-management)) accepts OAuth app tokens and classic personal access tokens with "either the `manage_billing:copilot` or `read:org` scopes", and only organization owners can read it.
- `GET /organizations/{org}/settings/billing/ai_credit/usage` ([GitHub, billing usage](https://docs.github.com/en/rest/billing/usage)) is limited to organization administrators, and its page does not say which token types or scopes it accepts. Whether VS Code's GitHub session can read it is therefore settled only by the maintainer's owner-account run (T343), not assumed. That reading is recorded in [`v4.13.8-copilot-connect-verification.md`](../../../releases/v4/v4.13/development/v4.13.8-copilot-connect-verification.md); until it is filled in, known gap v4.13.8 QG-9 stays open.
- No GitHub page checked documents a `github-authentication-token-expiration` response header (the token docs, "Authenticating to the REST API", "Troubleshooting the REST API", and "Getting started with the REST API"), so the monitor does not rely on one: an expired or revoked token surfaces as GitHub's 401, which offers a one-click Reconnect.
- VS Code's `authentication.getSession` ([VS Code API](https://code.visualstudio.com/api/references/vscode-api)) returns a session matching the requested scopes and prompts when `createIfNone` is set; it offers no API for an extension to sign out or remove a granted scope. Disconnect therefore clears what the extension stored and tells the user how to remove `read:org`: sign out from VS Code's Accounts menu, or revoke "Visual Studio Code" under GitHub's authorized OAuth apps.

**Connect, as amended.** The organization is detected from the seat's own `copilot_internal/user` payload (`organization_list`; logins and names only, no ids), which supersedes item 1's "the organization list is never read"; one organization is preselected, several give a quick pick, and none falls back to typed entry. Connect first asks VS Code for the GitHub session with `read:org`, which is read-only, and reads both billing endpoints with it; when both answer 200, only the organization login and the route are stored, with no secret. Any other answer falls back to a guided fine-grained token: a button opens the pre-filled page above (`expires_in=366`, `organization_administration=read`, `organization_copilot_seat_management=read`), the token is checked against both endpoints on paste, and failures name their fix. No write scope is ever requested, and the token stays in VS Code secret storage and goes only to `api.github.com`.

**Display, as amended.** Every surface shows a percentage of the month's window: `Copilot: <pct>% (month)` for a connected pool or a personal plan with a served quota, and `Copilot: --% (month)` otherwise, with the hover and dashboard explaining the one-time Connect step and that it needs an organization owner. No status bar, hover, dashboard, or recommendation text shows a used-credit count; the pool size may appear. This supersedes item 3 and the acceptance criterion "On a member account without billing access the status bar shows credits used and no percentage".

### Alternatives considered for the amendment

**Keep the typed login and the plain pasted token.** Rejected for usability: the maintainer, a non-technical owner, could not complete it from a paragraph of text with no link, no steps, and nothing filled in.

**A token-free route only, with no token fallback.** Rejected unless T343 proves the AI-credit endpoint accepts VS Code's session: GitHub does not document OAuth tokens for that endpoint, and an organization that restricts third-party OAuth apps blocks the route outright.

**Request `manage_billing:copilot` or `admin:org` for a guaranteed OAuth route.** Rejected: both are write scopes, and the monitor only reads.

**Keep showing credits used where no percentage exists.** Rejected by the maintainer: a credit count with no denominator does not answer "how close am I", and `--% (month)` with a Connect explanation does.

**Trade-off accepted.** `read:org` on the VS Code session is read-only but broader than a token scoped to one organization: it can read the membership of every organization the account belongs to. The maintainer chose token-free first on 2026-10-02 knowing this; a user who prefers the narrower token can decline VS Code's consent prompt and the guided token flow follows.
