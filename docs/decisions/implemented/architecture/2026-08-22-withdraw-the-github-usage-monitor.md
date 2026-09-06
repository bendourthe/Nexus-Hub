# Decision: Withdraw the GitHub Usage Monitor extension

Status: implemented - `extensions/github-usage-monitor/` is deleted, and both installers now uninstall `nexus-hub.github-usage-monitor` from VS Code and Cursor on every run.

## Problem

The GitHub Usage Monitor existed to show, in the status bar, what `github.com/settings/billing` shows on its Included usage bars:

```
Actions minutes    2,000 min used / 2,000 min included
Actions storage    0.1 GB used / 0.5 GB included
```

On 2026-08-22 a user running the freshly released v3.18.1 reported the monitor showing **0%** while that page showed the minutes allowance **fully exhausted**. The report was reproduced and traced to root cause before this record was written.

The extension was not miscomputing. Its drawdown genuinely evaluated to zero, because every Actions line item that month resolved to a *public* repository, and public-repository minutes on standard runners are free. The number was arithmetically correct and completely wrong, which is the worst failure mode a usage meter has: a confident figure that reads as an answer.

## Why the figure cannot be obtained

**The meter is not served by any API.** The endpoint that once returned it, `GET /{scope}/settings/billing/actions` with `included_minutes` and `total_minutes_used`, was [closed down on 2025-09-26](https://github.blog/changelog/2025-09-26-product-specific-billing-apis-are-closing-down/). Verified 2026-08-22 against live documentation: the [Budgets API](https://docs.github.com/en/rest/billing/enhanced-billing) returns only `budget_amount` and `consumed_amount`; [`/usage` and `/usage/summary`](https://docs.github.com/en/rest/billing/usage) carry no allowance field; GraphQL exposes no billing surface. The page is rendered server-side and is not reachable with an OAuth token.

**The reconstruction needs an input GitHub does not provide.** The billing page states that discounts cover *"Actions usage in public repositories **and** included usage for Actions minutes and storage"* - two distinct reasons summed into one number. The full line-item schema was checked: there is no discount-reason field and no repository-visibility field. The only available discriminator is the repository, and `GET /repos/{owner}/{repo}` reports visibility **as of now**, while billing line items are **historical**. A repository that was private when its minutes ran and is public today has its entire month retroactively reclassified as free.

That dependency cannot be engineered away. It is a property of what is absent from the data.

**The mechanism also moves.** Runner prices were cut on 2026-01-01, and from 2026-03-01 self-hosted runners began consuming the quota "based on list price" ([2026 pricing changes](https://github.com/resources/insights/2026-pricing-changes-for-github-actions)). The second change alone falsified two statements this project shipped in v3.18.1: the `classifySku` exclusion of self-hosted runners, and a policy document asserting they never draw down. Both were written five months after the behavior changed, because the change is not announced anywhere the project watches.

## Decision

Withdraw the extension. Delete the source, its CI workflow, its dedicated tests, and the policy document and ledger that described its model. Uninstall it from users' editors rather than merely unshipping it, since an extension already installed keeps reporting the wrong number forever.

The Claude, Codex, and Cursor monitors are unaffected and stay. They do not share this problem: each reads a **served** usage figure from its vendor's own first-party endpoint (`api.anthropic.com/api/oauth/usage` for Claude, reusing the credential the tool itself stored) and reconstructs nothing.

## Alternatives considered

**Keep reconstructing and improve accuracy.** Persist repository visibility per month on first observation so a later flip cannot rewrite history, and add a manual per-repository override. Rejected: it narrows the failure window without closing it, cannot help a fresh install that never observed the repository while private, and still leaves the number dependent on an unpublished mechanism that has changed twice in eight months. The requirement was reliability for any account without configuration; this cannot deliver it.

**Show only the figures that reconcile exactly.** The dollar values match the billing page to the cent with no inference ($77.74 metered, $77.74 included usage, $77.71 Actions on the reference account). A monitor showing those and linking out for the bars would be permanently correct. Rejected by the maintainer: the included-usage bars are the reason the extension exists, and a monitor that omits them is not the product.

**Show an explained-absence state instead of a number** whenever the reconstruction is not trustworthy. Rejected: honest, but on the reported account it would display "unknown" nearly always, which is a worse status-bar item than none and still carries the full maintenance cost.

**Scrape `github.com/settings/billing`.** Rejected on the same grounds as in the v3.18.1 plan: the page requires a browser session cookie, the extension holds an OAuth Bearer token, and the HTML is an undocumented surface with no stability contract.

**Do nothing and leave v3.18.1 shipped.** Rejected: the extension currently tells users they have consumed 0% of an allowance they have exhausted. Leaving it installed is the most harmful option available.

## Consequences

- Users upgrading past v3.18.2 have the extension uninstalled automatically from both hosts. Settings under `githubUsageMonitor.*` remain in their `settings.json` and are harmless; they are not removed, because deleting keys a user wrote is not the installer's call.
- Nexus-Hub ships three usage monitors instead of four.
- The v3.18.1 work is not wasted as evidence: the price-derived weighting it introduced was independently confirmed by GitHub's own pricing wording, and is recorded in the superseded record beside this one.
- **What would reopen this**: GitHub publishing an API that returns included-usage consumed and included-usage total for a scope. That single endpoint would make the extension trivial and correct, and is the only thing that should.
