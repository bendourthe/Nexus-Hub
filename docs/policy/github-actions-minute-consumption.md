# When GitHub Actions Minutes Are Actually Consumed

Four kinds of Actions run look identical on a bill and consume the included allowance in four different ways. This document states which is which, so the question is answered once instead of re-derived every time the meter surprises someone.

Every claim below is marked **documented** (with a source URL and the date it was verified) or **inferred** (with the evidence behind it). The distinction matters: GitHub publishes per-minute prices, but it publishes **no** multiplier for included-minute consumption, and no billing endpoint returns the included allowance at all. Anything presented as a multiplier here is a reconstruction.

## The short version

| Run | Appears on the bill? | Draws down included minutes? |
|---|---|---|
| Public repository, standard GitHub-hosted runner | Yes, as a metered line item that is then fully discounted | **No** |
| Private repository, standard GitHub-hosted runner | Yes | **Yes**, weighted by list price |
| Any repository, self-hosted runner | Yes, discounted | **No** |
| Any repository, larger runner | Yes | **No** - included minutes cannot be spent on one at all |

The first row is the one that causes confusion. A public-repository run produces a line item with a real gross amount, and only the discount line cancels it. Read gross consumption and it looks like the allowance is draining; read the discount and it is not.

## Public repositories are free, and still look like consumption

**Documented.** GitHub's report reference defines `discount_amount` as covering "your account's included usage" **and** "GitHub Actions usage for standard GitHub-hosted runners in public repositories and for self-hosted runners".

- Source: <https://docs.github.com/en/billing/reference/billing-and-payments-reports>
- Verified: 2026-08-19

**Inferred, with evidence.** Because the discount cancels the gross amount rather than suppressing the line item, gross Actions minutes overstate the drawdown by the entire public-repository share. Measured on a real account for August 2026: 5,924 gross minutes, of which 4,200 were public-repository runs on `Nexus-Hub` that contributed nothing. This is why the extension reconstructs the drawdown from private-repository items rather than reading the gross figure.

## Private repositories draw down, weighted by list price

**Documented.** GitHub publishes per-minute prices for GitHub-hosted runners and states that Windows and macOS runners cost more than Linux.

- Linux 2-core: $0.006 per minute
- Windows 2-core: $0.010 per minute
- macOS 3/4-core: $0.062 per minute
- Source: <https://docs.github.com/en/billing/concepts/product-billing/github-actions>
- Verified: 2026-08-19

**Not documented, stated plainly.** GitHub publishes **no** multiplier describing how fast each runner consumes *included* minutes. The minute-multiplier reference page was withdrawn; the path now serves runner pricing with no multiplier table, on the dotcom, enterprise-cloud, and enterprise-server variants alike.

**Inferred, with evidence.** The widely-cited legacy multipliers (Linux 1x, Windows 2x, macOS 10x) were never an independent taxonomy. They are exactly the pre-2026 per-minute price ratios:

| Runner | Pre-2026 price | Ratio to Linux | Published multiplier |
|---|---|---|---|
| Linux 2-core | $0.008 | 1.00 | 1x |
| Windows 2-core | $0.016 | 2.00 | 2x |
| macOS 3/4-core | $0.080 | 10.00 | 10x |

On 2026-01-01 GitHub cut runner prices. The same mechanism now yields different numbers:

| Runner | 2026 price | Ratio to Linux |
|---|---|---|
| Linux 2-core | $0.006 | 1.00 |
| Windows 2-core | $0.010 | 1.67 |
| macOS 3/4-core | $0.062 | 10.33 |

The extension therefore derives each line item's weight as its own `pricePerUnit` divided by the standard Linux rate observed in the same billing payload, rather than storing any table. Evidence that weighting happens at all: measured 2026-08-19 against a private repository for August 2026 via the Actions jobs API (73 runs, 527 jobs), usage was 1,457 Linux + 187 Windows + 80 macOS minutes. Unweighted that is 1,724 minutes, and GitHub's own Included-usage panel showed 2,000 of 2,000 consumed. A model predicting 1,724 cannot produce a saturated 2,000-minute meter. Price-weighted it predicts 2,595, which can.

The residual uncertainty, and what would settle it, is recorded in [`docs/v3/v3.18/development/github-drawdown-ledger.md`](../v3/v3.18/development/github-drawdown-ledger.md).

## Self-hosted runners never draw down

**Documented.** Covered by the same `discount_amount` definition quoted above: self-hosted runner usage is discounted in full.

- Source: <https://docs.github.com/en/billing/reference/billing-and-payments-reports>
- Verified: 2026-08-19

## Larger runners cannot use included minutes at all

**Documented.** GitHub's larger-runner documentation states that included minutes do not apply to larger runners; they are billed per minute from the first minute.

- Source: <https://docs.github.com/en/actions/how-tos/manage-runners/larger-runners/manage-larger-runners>
- Verified: 2026-08-19

**Consequence for any reconstruction.** A larger runner must be **excluded**, never weighted. Price-weighting one is a category error: its minutes cannot be spent from the allowance under any weighting, so including it at any weight overstates the drawdown.

## Storage is reported in GB-hours and billed in GB-months

**Documented.** "Your bill reflects the total storage used throughout the month, measured in GB-Hours", and "Your monthly bill converts GB-Hours to GB-Months by dividing by the hours in the month (usually 720 hours for a 30-day month)".

- Source: <https://docs.github.com/en/billing/concepts/product-billing/github-actions>
- Verified: 2026-08-19

The full month's hours are used even mid-month, matching how GitHub states the bill is computed. A partial-month denominator reads higher and does not match the figure the user sees.

## On exhaustion, private runs stop rather than being billed

**Documented.** With no payment method and no spending budget set, GitHub blocks further usage that would exceed the included allowance rather than charging for it.

- Source: <https://docs.github.com/en/billing/tutorials/set-up-budgets>
- Verified: 2026-08-19

**Inferred, with evidence.** The block applies to the usage that draws down - private-repository runs on standard GitHub-hosted runners. Public-repository runs are fully discounted and continue. This is the actionable half of an exhaustion warning, and it is why the extension's exhausted-state recommendation says both things rather than a generic "pause non-essential runs".

## The allowance itself is not readable

**Documented by absence, stated plainly.** No billing endpoint returns the included allowance. The legacy product-specific endpoints that returned `included_minutes` were closed down in September 2025 and now return 404/410. The `/settings/billing/usage` endpoint returns consumption, never the entitlement.

The extension therefore takes the allowance from a plan table (2,000 minutes and 0.5 GB on Free) and offers a manual override as the correction path. Scraping `github.com/settings/billing` is not an alternative: that page requires a browser session cookie, and the extension authenticates with an OAuth Bearer token, so the page is not reachable with the credential it holds. It is also an undocumented surface with no stability contract.

## What this means for reading the meter

The percentage the extension shows is a **reconstruction**, and the panel labels it as one. It is:

- built from private-repository, GitHub-hosted, standard-runner minutes only;
- weighted by each item's own list price relative to the standard Linux rate seen in the same payload;
- divided by a plan-table allowance that no endpoint confirms.

Any of those three can be wrong independently. When a repository's visibility cannot be read - which happens when the token lacks the `repo` scope, and private repositories are precisely the ones that matter - the extension reports the figure as unknown rather than returning a partial sum that reads as a confident low number.

## Related

- [`docs/v3/v3.18/development/github-drawdown-ledger.md`](../v3/v3.18/development/github-drawdown-ledger.md) - per-month evidence and the falsifier for the current model
- [`docs/decisions/implemented/architecture/2026-08-22-derive-actions-drawdown-weights-from-price.md`](../decisions/implemented/architecture/2026-08-22-derive-actions-drawdown-weights-from-price.md) - why weights are derived rather than tabulated
- [`extensions/github-usage-monitor/README.md`](../../extensions/github-usage-monitor/README.md) - the extension itself
