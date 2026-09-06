# GitHub Entitlement and Drawdown Probe

**Project**: Nexus-Hub
**Extension**: `extensions/github-usage-monitor` (`nexus-hub.github-usage-monitor`)
**Written for**: v3.16.3 Phase 2, sub-task 2.1
**Probe date**: 2026-08-09
**Method**: fetched public GitHub documentation only. No billing credential was used, no live API request was made, and no account data was read.

## Why this document exists

v3.16.3 Phase 2 decides whether the monitor is allowed to render a usage percentage at all. Two findings had to be re-verified before any code was written, because GitHub's billing API has changed twice in eighteen months and one of the findings was itself corrected mid-planning after being checked against a real account.

The negative results are recorded deliberately. A future contributor must be able to see that the Budgets API was checked and rejected, rather than re-checking it.

## Question 1 - does any documented endpoint serve an included allowance?

**Answer: no.** Confirmed field by field on 2026-08-09 against [docs.github.com/en/rest/billing/usage](https://docs.github.com/en/rest/billing/usage).

| Endpoint | Documented response fields |
|---|---|
| `GET /users/{username}/settings/billing/usage` | `usageItems` of `date`, `product`, `sku`, `quantity`, `unitType`, `pricePerUnit`, `grossAmount`, `discountAmount`, `netAmount`, `repositoryName` |
| `GET /organizations/{org}/settings/billing/usage` | same, plus `organizationName` |
| `GET /users/{username}/settings/billing/usage/summary` | envelope `timePeriod`, `user`, `repository`, `product`, `sku`; `usageItems` of `product`, `sku`, `unitType`, `pricePerUnit`, `grossQuantity`, `grossAmount`, `discountQuantity`, `discountAmount`, `netQuantity`, `netAmount` |
| `GET /organizations/{org}/settings/billing/usage/summary` | same, with `organization` |
| `GET /{scope}/settings/billing/ai_credit/usage` | envelope `timePeriod`, `user`/`organization`, `product`, `model`; `usageItems` with the same quantity triplet plus `model` |
| `GET /{scope}/settings/billing/premium_request/usage` | same schema as the AI-credit endpoint |

**No entitlement, quota, included-quantity, or remaining-balance field exists in any of them.**

The Budgets API was checked and **rejected**. It returns `budget_amount`, `effective_budget`, `consumed_amount`, `prevent_further_usage`, and alerting fields. `consumed_amount` is spend against a **user-defined budget**, not usage against an included allowance. Do not conflate them: a user who has set no budget has no `effective_budget`, and a user who has set one has a number unrelated to their plan entitlement.

The legacy product-specific endpoints that did return `included_minutes` are closed. [The 2025-09-26 changelog](https://github.blog/changelog/2025-09-26-product-specific-billing-apis-are-closing-down/) names `/settings/billing/actions`, `/settings/billing/packages`, and `/settings/billing/shared-storage`, and directs callers to "a consolidated usage endpoint that provides usage details about all GitHub metered products". The changelog makes **no** statement that the replacement exposes included allowances, and the field inventory above confirms it does not.

**Consequence**: `AllowanceInputs.api` stays unpopulated. `allowanceSource` must never be `"api"`.

### Correction to the plan's field inventory

The v3.16.3 plan states that `/settings/billing/usage` returns `grossQuantity`. It does not. It returns a single `quantity` field, with `discountAmount` and `netAmount` in **dollars only** - there is no `discountQuantity` or `netQuantity` on that endpoint.

The quantity triplet (`grossQuantity` / `discountQuantity` / `netQuantity`) exists only on `/usage/summary` and the two AI endpoints, and **those endpoints carry no `repositoryName`**. This matters for question 2: the two fields a drawdown reconstruction needs are on different endpoints, and neither endpoint carries both.

The extension is unaffected today because `normalizer.ts` already reads `grossQuantity ?? quantity`, so it handles either shape.

## Question 2 - which usage actually draws down the included allowance?

This is the question the original plan missed, and it is the one that makes a naive percentage wrong by roughly eightfold on real data.

### 2a - public-repository usage is free and excluded. Confirmed.

[Billing and usage](https://docs.github.com/en/actions/concepts/billing-and-usage): "GitHub Actions usage is free for standard GitHub-hosted runners in public repositories." [The 2025-12-16 pricing changelog](https://github.blog/changelog/2025-12-16-coming-soon-simpler-pricing-and-a-better-experience-for-github-actions/) restates that runner usage in public repositories "will remain free" under the 2026 rates.

### 2b - there are THREE exclusions, not one. New finding.

[Billing reports reference](https://docs.github.com/en/billing/reference/billing-reports) defines `discount_amount` as: "Usage that is discounted as part of your account's included usage is reflected in this field. Also includes discounts for GitHub Actions usage for standard GitHub-hosted runners in public repositories and for self-hosted runners."

So a single `discount_amount` conflates:

1. included-allowance drawdown (what we want to measure),
2. public-repository usage (free, excluded from drawdown),
3. self-hosted-runner usage (discounted today).

And separately, [Actions runner pricing](https://docs.github.com/en/billing/reference/actions-runner-pricing) states "Included minutes cannot be used for larger runners", so larger-runner usage is a fourth category that is neither drawdown nor discount.

The plan proposed filtering Actions line items to private repositories. That is **necessary but not sufficient**: a private-repo self-hosted-runner item is private and still not drawdown, and a private-repo larger-runner item is private and cannot consume included minutes either.

### 2c - the drawdown basis is UNDOCUMENTED and has changed. Blocking finding.

The legacy model applied per-operating-system minute multipliers (Linux 1x, Windows 2x, macOS 10x) to included-minute consumption. That table is **no longer served**. `https://docs.github.com/en/billing/reference/actions-minute-multipliers` was fetched on 2026-08-09 and returns runner-pricing content with no multiplier table; the same is true of the `enterprise-cloud@latest` and `enterprise-server@3.17` variants of that path. Search engines still index the legacy sentence, which is how the concept remains discoverable, but the live documentation no longer states it.

What the current documentation says instead, in [the 2025-12-16 changelog](https://github.blog/changelog/2025-12-16-coming-soon-simpler-pricing-and-a-better-experience-for-github-actions/): "self-hosted runners will be included within your free usage quota, and will consume available usage **based on list price** the same way that Linux, Windows, and MacOS standard runners work today."

Read carefully, that sentence says standard runners **already** consume the quota on a list-price basis. Under the January 2026 rates from [Actions runner pricing](https://docs.github.com/en/billing/reference/actions-runner-pricing) the price ratios are:

| Runner | Rate per minute | Ratio to Linux 2-core | Legacy multiplier |
|---|---|---|---|
| Linux 2-core (x64) | $0.006 | 1.00x | 1x |
| Windows 2-core (x64) | $0.010 | 1.67x | 2x |
| macOS 3-4 core | $0.062 | 10.33x | 10x |

**The price ratios do not equal the legacy multipliers.** A reconstruction that hardcodes 2x / 10x would be using retired constants; one that derives ratios from list price would be inferring an undocumented conversion basis. Neither is a documented fact, and the plan forbids inventing one.

Compounding this: the included allowance is published in **minutes** (2,000 for Free), while drawdown is described as list-price-based. The conversion between the two - which runner's rate defines the minute - is not stated anywhere in the public documentation.

### 2d - verdict on question 2

The drawdown numerator **cannot be reconstructed from documented data with confidence**. Three independent gaps, any one of which is disqualifying:

1. Per-repository attribution and per-quantity discount are on different endpoints.
2. The exclusion set is larger than the plan assumed, and two of the exclusions (self-hosted, larger runners) are SKU-shaped rather than repository-shaped, requiring a SKU taxonomy that is not published as a stable machine-readable list.
3. The minutes-to-quota conversion basis is undocumented and demonstrably changed between the legacy multiplier model and the current list-price model.

## Question 3 - storage units. A documented conversion DOES exist.

The plan predicted no documented conversion between the entitlement unit (GB) and the reported consumption unit (GigabyteHours), and expected an explicit unsupported state. **That prediction is wrong.** [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions) states:

- "Storage charges accrue every hour based on your actual usage throughout the month."
- "Your bill reflects the total storage used throughout the month, measured in **GB-Hours**."
- "Your monthly bill converts GB-Hours to GB-Months by dividing by the hours in the month (usually 720 hours for a 30-day month)."

So the relationship is documented and exact:

```
GB-months = GB-hours / hours_in_billing_month
```

Checked against the one real observation available (recorded in the plan's overview): the API reported **63.92 GigabyteHours** of Actions storage while the billing page showed "0 GB used / 0.5 GB included". August 2026 has 744 hours, and `63.92 / 744 = 0.0859` GB-months, which displays as `0` at the billing page's precision. **Consistent.**

This is a single corroborating data point, not a validation. It rules out a gross dimensional error; it does not establish that the numerator is free of the same exclusion problem as Actions minutes.

## Question 4 - the plan-entitlement table, and a correction to the plan's evidence

Sourced from [Product usage included with each plan](https://docs.github.com/en/billing/reference/product-usage-included), fetched 2026-08-09.

**GitHub Actions**

| Plan | Minutes per month | Storage |
|---|---|---|
| GitHub Free | 2,000 | 500 MB |
| GitHub Pro | 3,000 | 1 GB |
| GitHub Free for organizations | 2,000 | 500 MB |
| GitHub Team | 3,000 | 2 GB |
| GitHub Enterprise Cloud | 50,000 | 50 GB |

**Git Large File Storage**

| Plan | Storage per month | Bandwidth per month |
|---|---|---|
| GitHub Free | 10 GB | 10 GB |
| GitHub Pro | 10 GB | 10 GB |
| GitHub Free for organizations | 10 GB | 10 GB |
| GitHub Team | 250 GB | 250 GB |
| GitHub Enterprise Cloud | 250 GB | 250 GB |

**GitHub Codespaces**

| Plan | Core hours per month | Storage per month |
|---|---|---|
| GitHub Free | 120 | 15 GB |
| GitHub Pro | 180 | 20 GB |
| GitHub Free for organizations | **None** | **None** |
| GitHub Team | **None** | **None** |
| GitHub Enterprise Cloud | **None** | **None** |

**Copilot**: the page defers to the Copilot plan documentation and publishes no allowance table here.

### Correction: the 10 GB LFS figure is NOT anomalous

The plan cites the maintainer's account showing "10 GB included Git LFS bandwidth and 10 GB storage" as evidence that "static plan tables are guidance, not a verified account denominator", on the basis that it "does not match the commonly-published free-tier figure".

**It matches exactly.** GitHub currently publishes 10 GB storage and 10 GB bandwidth for GitHub Free. The plan was comparing against an older 1 GB figure that is no longer current.

The conclusion still stands, but it must rest on real reasons rather than a mistaken one:

- Plan resolution from `GET /user`'s `plan.name` can fail or return an unrecognized plan, and a wrong plan yields a wrong denominator that looks authoritative.
- Data packs, legacy grandfathered terms, and negotiated Enterprise agreements are all invisible to the API.
- Codespaces has a documented **None** for three plans, which a naive table lookup would render as a zero-denominator division.

The table is therefore shipped as a **labeled hint only**: it must not prefill an input, must not be written automatically, and must not populate `AllowanceInputs.api`.

## Measured results - account `bendourthe`, 2026-08

Run 2026-08-09 with `scripts/reconcile-drawdown.js` against a classic PAT carrying `user` + `repo`. Repository names are hashed in the output; the two that matter are distinguished only by visibility.

**What GitHub displays** for August 1-31, 2026: Actions minutes **120.7 used / 2,000 included**; Actions storage **0 GB used / 0.5 GB included**; Current included usage **$15.56**; billable **$0**.

**What the API returns**: 64 line items, 4 distinct repositories, 2 resolvable.

| Repository | Visibility | Minutes | By SKU | List price | Discount | Net |
|---|---|---|---|---|---|---|
| repo-6f4a78f5 | public | 1,163.0 | Linux 658, macOS 3-core 111, Windows 394 | $14.77 | $14.77 | $0.00 |
| repo-9ad9a5b2 | private | 124.0 | Linux 120, Windows 4 | $0.76 | $0.76 | $0.00 |

Observed SKU strings, which replace the guessed taxonomy: `Actions Linux`, `Actions Windows`, `Actions macOS 3-core`, `Actions storage` (GigabyteHours), `Git LFS storage` (GigabyteHours). No self-hosted or larger-runner SKU appeared on this account, so those classification rules remain **unvalidated against real strings**.

### The headline finding: a reconciling candidate that is arithmetically impossible

The runner reported `privateHostedStandardLinuxMinutes` (120.0 against a displayed 120.7, off by 0.6%) as RECONCILING. **It is wrong, and the per-repository table disproves it.**

GitHub rounds each job up to a whole minute, so the API's 120 Linux minutes is an **upper bound** on true Linux time. The displayed drawdown is **120.7, which exceeds 120**. A Linux-only model cannot produce a figure larger than its own upper bound. The candidate passed the tolerance test purely because 120 sits near 120.7.

This is the exact failure mode sub-task 2.3 exists to prevent, caught in the act. Shipping on that green verdict would have silently excluded all Windows and macOS drawdown for every user. **A numeric match is not evidence; a bound violation is.**

### August could not test anything, and the reason is methodological

The August comparison was invalid, and not for the reason first recorded here. The initial write-up attributed the 124-versus-120.7 gap to per-job round-up inflation. That explanation is **wrong**: June and July return fractional quantities (`1450.666666667` Linux minutes, `201.6` Windows), so the API does not report whole minutes and there is no round-up to blame.

The actual cause is that **August was still in progress**. The displayed 120.7 was read off the billing page at one moment; the probe ran later and saw 124. Roughly three minutes of CI ran in between. The two figures are snapshots of a moving target.

**Never reconcile against the current month.** Only a completed month holds still. This invalidated the first three runs of this probe.

### The decisive test: July 2026, a completed month

July's Included-usage panel reads **`2,000 min used / 2,000 min included`** with a full bar - saturated. The true drawdown was therefore **at least 2,000 minutes**.

| Model | July prediction | Verdict |
|---|---|---|
| Gross (today's behavior) | 1,686 total, 1,584 private | Meaningless - counts public usage |
| Private, all OS at 1:1 (H1) | **1,584** | **FALSIFIED.** A model cannot predict 1,584 when the truth is at least 2,000 |
| Private, legacy weights (Windows 2x, macOS 10x) | 2,104 | Consistent |
| Private, current list-price ratios (Windows 1.67x, macOS 10.33x) | 2,051 | Consistent |

**Non-Linux minutes draw down faster than Linux minutes.** The multiplier concept GitHub stopped publishing is still in force. This reverses the conclusion drawn from August, and it is the single most important result of the phase: shipping H1 would have understated drawdown on every account that builds on Windows or macOS.

### Cross-checking the weighted model against every month available

| Month | Private raw | Weighted (legacy) | Displayed | Agreement |
|---|---|---|---|---|
| 2026-05 | 4,048 | 5,534 | saturated at 2,000 | Consistent |
| 2026-06 | 1,499 | 2,113 | not readable in the UI | - |
| 2026-07 | 1,584 | 2,104 | saturated at 2,000 | Consistent |
| 2026-08 | 124 | 128 | ~121, month in progress | Consistent within drift |

Nothing contradicts the weighted model. Nothing confirms its exact constants either.

### The two surviving weightings cannot be separated on this account

Legacy (2x / 10x) and current list-price ratios (1.67x / 10.33x) predict 2,104 and 2,051 for July - both above a saturated 2,000, so July cannot separate them. April is the only month low enough to try, and there they predict 1,473 versus 1,469, a 0.3% difference that no reading could resolve.

**Practically the choice does not matter; evidentially it remains unresolved.** Any implementation must therefore state which constants it uses and why, rather than presenting a derived number as GitHub's own.

### Why the account was never billed despite exceeding

May's 4,048 private raw minutes with `net $0.00` initially looked like a falsification of the whole private-repository model. It is not. A GitHub Free account with no payment method does not get billed for exceeding included minutes - **private-repository Actions stop running instead**. The $0 bill is the expected outcome of hitting the cap, not evidence that the usage did not draw down.

### Storage: the documented conversion is confirmed on two independent months

| Month | GB-hours | Hours in month | Derived GB | Displayed | Agreement |
|---|---|---|---|---|---|
| 2026-07 | 432.305 | 744 | **0.581** | saturated at 0.5 GB | Correct - over the allowance |
| 2026-08 | 64.568 | 744 | **0.087** | "0 GB used" | Correct at the panel's precision |

Sub-task 2.4's conversion (`GB-months = GB-hours / hours_in_month`) is documented AND corroborated in both directions - one month under the allowance, one over. This is the only part of Phase 2 that is fully settled.

### `/usage/summary` closes the last surface: the drawdown is not a served field

The summary endpoint is the only one carrying `discountQuantity` in the metric's own unit rather than in dollars. Measured on the same account and period:

| Product / SKU | Unit | gross | discount | net |
|---|---|---|---|---|
| Actions / `actions_linux` | minutes | 778 | **778** | 0 |
| Actions / `actions_windows` | minutes | 398 | **398** | 0 |
| Actions / `actions_macos` | minutes | 111 | **111** | 0 |
| Actions / `actions_storage` | gigabyte-hours | 64.5677 | **64.5677** | 0 |
| Git LFS / `git_lfs_storage` | gigabyte-hours | 121.9423 | **121.9423** | 0 |

`discountQuantity` equals `grossQuantity` on every row. The discount covers 100% of usage and does not separate the public-repository portion from the included-allowance portion. **The drawdown numerator is served by no documented endpoint, in no unit.** Reconstruction is the only route, which is what makes its unverifiability decisive rather than incidental.

**Hazard found in passing**: the two endpoints use different SKU vocabularies. `/usage` returns `Actions Linux`; `/usage/summary` returns `actions_linux`. The current classifier survives both only because its patterns are substring-based. A rule written against either vocabulary alone would silently misclassify the other endpoint's items.

### Secondary results, both clean

- **The monetary numerator is exact.** `sum(discountAmount)` across all products = **$15.56** against a displayed **$15.56**, to the cent. GitHub's "Current included usage" is precisely that sum. Restricted to Actions items it is $15.53 against the Actions tab's $15.55; the difference is Actions storage, which the tab includes and that candidate does not.
- **`quantity` is raw wall-clock minutes, and the published rate table is the one applied.** 778 x $0.006 + 398 x $0.010 + 111 x $0.062 = **$15.530**, matching the observed Actions discount to the cent. No multiplier is baked into `quantity`.
- **The storage conversion holds.** 64.5677 GB-hours / 744 hours in August = **0.0868 GB**, displaying as the panel's "0 GB used" at one significant figure. Git LFS: 121.942 / 744 = 0.164 GB. Sub-task 2.4's documented conversion is corroborated.

### Defects found in the probe itself, and fixed

1. **Token scope.** The first run used a `user`-only PAT, so `GET /repos/{owner}/{repo}` returned 404 for private repositories and every private candidate summed zero. The runner now withholds its verdict entirely when any visibility lookup fails.
2. **SKU misclassification.** The first rule treated any `N-core` SKU as a larger runner, misclassifying `Actions macOS 3-core` - the standard macOS runner - and dropping 111 minutes. Corrected to a per-OS standard core ceiling, with a regression test pinned to the real strings.
3. **Period mismatch.** The first run compared August API data against figures from an earlier month whose gross was 1,003. The runner now prints the queried period directly above the verdict.

## Verdicts

*(Revised 2026-08-09 after the July measurement. The pre-measurement version of this table asserted that reconstruction was impossible; the measurement showed it is possible but its constants are unpublished, which is a different verdict with different consequences.)*

| Question | Verdict | Consequence for Phase 2 |
|---|---|---|
| Does the API serve an entitlement? | **No** | `AllowanceInputs.api` stays unpopulated; `allowanceSource` is never `"api"`. The denominator comes from the plan table, auto-derived from `plan.name`, with a discoverable override. |
| Does any endpoint serve the drawdown numerator? | **No** | `/usage/summary` reports `discountQuantity == grossQuantity` on every row. Reconstruction is the only route. |
| Is gross consumption the drawdown numerator? | **No** | It counts public-repository usage, which is free. On this account gross is 1,287 against a true ~121. |
| Is private-repository usage at 1:1 the numerator? | **No** | Falsified by July: predicts 1,584 where the truth is at least 2,000. |
| Is the numerator OS-weighted? | **Yes** | Confirmed by the July saturation. The weights themselves are no longer published. |
| Can the exact weights be determined? | **No** | Legacy (2x/10x) and list-price (1.67x/10.33x) both fit; they differ by 0.3% and this account cannot separate them. |
| Is there a documented GB-hours to GB conversion? | **Yes, and corroborated** | 2.4 implements it with the source cited. Verified in both directions on two months. |
| Do some products genuinely have no allowance? | **Yes** | Codespaces documents **None** for three plans; the `none` allowance state in 2.5 is real, not hypothetical. |

**Net position for sub-task 2.3**: a reconstruction exists that is consistent with every month this account can offer, but it depends on constants GitHub has withdrawn from its documentation, and no available measurement can pin them. That is neither the clean reconcile the plan hoped for nor the clean impossibility it was prepared to accept.

## What would unblock a percentage in a later release

In rough order of cost:

1. **GitHub publishes an entitlement field.** Cheapest by far. `AllowanceInputs.api` was built for exactly this. Re-run question 1 before every release that touches this area.
2. **GitHub republishes the quota-drawdown basis.** If the minutes-to-quota conversion becomes a documented constant again, reconstruction becomes a bounded engineering problem rather than a guess.
3. **A reconciliation dataset from a real account.** A full `/settings/billing/usage` payload for one month, plus a screenshot of that account's Included-usage panel for the same period, would let a candidate formula be validated rather than fitted. Note that one account is enough to *falsify* a formula and not enough to *confirm* one; the plan's own warning about reverse-fitting applies.

## Re-verification checklist

Re-run this probe before any future release that changes allowance handling:

- [ ] Re-fetch [the billing usage REST reference](https://docs.github.com/en/rest/billing/usage) and diff the field list against the table above.
- [ ] Re-check whether `https://docs.github.com/en/billing/reference/actions-minute-multipliers` serves a multiplier table again.
- [ ] Re-fetch [the billing reports reference](https://docs.github.com/en/billing/reference/billing-reports) and re-read the `discount_amount` definition for a change in what it conflates.
- [ ] Re-fetch [Product usage included with each plan](https://docs.github.com/en/billing/reference/product-usage-included) and diff the hint table.
- [ ] If any answer changed, escalate before writing code: a real denominator does not fix a wrong numerator, and a real numerator does not fix a missing denominator.
