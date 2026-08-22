/**
 * Candidate reconstructions of the quantity GitHub counts against an included
 * allowance ("drawdown"), computed side by side so they can be MEASURED against a
 * real account rather than chosen in advance.
 *
 * Why this module exists. The monitor sums `quantity` across Actions line items and
 * calls it usage. That is gross consumption, and gross consumption is not drawdown:
 * on a real account it read 1,003 minutes for a month in which GitHub's own
 * Included-usage panel showed 119.7 of 2,000 minutes consumed. Dividing gross by the
 * allowance renders 50% where the truth is 6%.
 *
 * Why candidates rather than an answer. The v3.16.3 Phase 2 probe
 * (docs/v3/v3.16/development/github-entitlement-probe.md) established that GitHub
 * documents neither the drawdown basis nor a machine-readable SKU taxonomy:
 *
 *   - `discount_amount` conflates included-allowance drawdown with public-repository
 *     usage AND self-hosted-runner usage, so it cannot be read as drawdown directly.
 *   - The per-OS minute multipliers (Linux 1x, Windows 2x, macOS 10x) are no longer
 *     served on any documentation path; the current wording says the quota is
 *     consumed "based on list price", whose ratios (1.67x, 10.33x) differ from them.
 *   - Only the Linux case is stated outright: ten Linux minutes consume ten allowance
 *     minutes.
 *
 * So every candidate below is a HYPOTHESIS. `scripts/reconcile-drawdown.js` runs them
 * all against one real account and reports which, if any, reconciles with the figure
 * GitHub itself displays. A candidate is promoted to product behavior only after it
 * reconciles - never by looking plausible, and never by being tuned until it matches.
 *
 * This module is deliberately pure: no network, no `vscode`, no configuration. It is
 * unit-testable against fixtures, and the probe script supplies the live data.
 */

/**
 * One line item from `GET /{scope}/settings/billing/usage`.
 *
 * Note the field set: this endpoint carries `repositoryName` and `quantity`, with
 * `discountAmount` / `netAmount` in DOLLARS. It has no `discountQuantity`. The
 * quantity triplet exists only on `/usage/summary`, which in turn has no
 * `repositoryName` - which is why no single endpoint answers this question.
 */
export interface UsageLineItem {
  date: string;
  product: string;
  sku: string;
  unitType: string;
  quantity: number;
  pricePerUnit: number | null;
  grossAmount: number | null;
  discountAmount: number | null;
  netAmount: number | null;
  repositoryName: string | null;
  organizationName?: string | null;
}

export type RepositoryVisibility = "public" | "private" | "unknown";

/** Resolved visibility per repository name, as fetched from `GET /repos/{owner}/{repo}`. */
export type VisibilityMap = Readonly<Record<string, RepositoryVisibility>>;

export type RunnerOs = "linux" | "windows" | "macos" | "unknown";

/**
 * What a SKU string appears to describe.
 *
 * Every field can be `unknown`, and that is the point. The classification rules below
 * are pattern guesses against strings GitHub does not publish as a stable taxonomy,
 * so an unrecognized SKU must surface as unknown rather than being silently bucketed
 * into whichever category happens to be the default. The probe prints the distinct
 * SKU inventory for a real account precisely so these rules can be replaced with
 * observed strings.
 */
export interface RunnerClassification {
  os: RunnerOs;
  /** False for self-hosted runners, which are discounted and do not draw down. */
  githubHosted: boolean | "unknown";
  /** False for larger runners, which documentation says cannot use included minutes. */
  standard: boolean | "unknown";
  /** True when no rule matched with confidence; the SKU needs a real-world sample. */
  unrecognized: boolean;
}

/**
 * SKU classification patterns.
 *
 * HAZARD: the two billing endpoints use DIFFERENT SKU vocabularies for the same
 * runner. `/settings/billing/usage` returns `Actions Linux`; `/usage/summary`
 * returns `actions_linux`. Both were observed on a real account on 2026-08-09 and
 * both are pinned in `drawdown.test.ts`.
 *
 * Every pattern below is therefore substring-based and separator-tolerant. A rule
 * written against either vocabulary alone would silently misclassify the other
 * endpoint's items, and a misclassified runner is dropped from the drawdown without
 * a trace. If you add a rule, add a fixture in BOTH spellings.
 */
const SELF_HOSTED_PATTERN = /self[\s_-]?hosted/iu;
const CORE_COUNT_PATTERN = /(\d+)\s*-?\s*core/iu;
const EXPLICIT_LARGER_PATTERN = /larger|xlarge|\bgpu\b/iu;
const LINUX_PATTERN = /linux|ubuntu/iu;
const WINDOWS_PATTERN = /windows/iu;
const MACOS_PATTERN = /mac\s?os|macos|osx/iu;

/**
 * Largest core count that is still a STANDARD runner, per operating system.
 *
 * Corrected 2026-08-09 against a real account. The first version of this rule
 * treated any `N-core` SKU as a larger runner, which misclassified
 * `Actions macOS 3-core` - the standard macOS runner - and silently dropped every
 * macOS minute from the private-repository candidates.
 *
 * Sourced from GitHub's Actions runner pricing table, which lists Linux 2-core and
 * Windows 2-core among the standard rates and prices macOS at "3-4 core". Anything
 * above these counts is a larger runner, and documentation states included minutes
 * cannot be used for larger runners.
 *
 * This remains an inferred boundary rather than a published taxonomy, which is why
 * the probe prints the observed SKU inventory with its classification: the rule is
 * meant to be checked against real strings, not trusted on sight.
 */
const STANDARD_MAX_CORES: Readonly<Record<Exclude<RunnerOs, "unknown">, number>> = {
  linux: 2,
  windows: 2,
  macos: 4
};

/**
 * Best-effort SKU classification.
 *
 * Deliberately conservative: anything that does not match a positive OS pattern is
 * `unknown` rather than assumed Linux, because assuming Linux is exactly the
 * assumption that would make a wrong number look right on a Linux-heavy account.
 */
export function classifySku(sku: string): RunnerClassification {
  const selfHosted = SELF_HOSTED_PATTERN.test(sku);
  const os: RunnerOs = LINUX_PATTERN.test(sku)
    ? "linux"
    : WINDOWS_PATTERN.test(sku)
      ? "windows"
      : MACOS_PATTERN.test(sku)
        ? "macos"
        : "unknown";
  const cores = Number(CORE_COUNT_PATTERN.exec(sku)?.[1] ?? Number.NaN);
  const overStandardCores =
    os !== "unknown" && Number.isFinite(cores) && cores > STANDARD_MAX_CORES[os];
  const larger = EXPLICIT_LARGER_PATTERN.test(sku) || overStandardCores;
  return {
    os,
    githubHosted: selfHosted ? false : os === "unknown" ? "unknown" : true,
    standard: larger ? false : os === "unknown" ? "unknown" : true,
    unrecognized: os === "unknown" && !selfHosted
  };
}

export interface CandidateTotal {
  /** The reconstructed figure. */
  value: number;
  /** The unit the figure is in, so a comparison cannot silently cross dimensions. */
  unit: "minutes" | "usd";
  /** Line items that contributed. */
  itemCount: number;
  /** Why this candidate might be wrong, stated up front rather than discovered later. */
  caveat: string;
}

export interface DrawdownCandidates {
  /**
   * The control: what the extension reports today. Known to be wrong - it is the
   * 1,003 in the 1,003-versus-119.7 discrepancy - and included so the probe output
   * carries the error's size rather than only the proposed fix.
   */
  grossMinutes: CandidateTotal;
  /**
   * H1 - drawdown is private-repository, GitHub-hosted, standard-runner minutes,
   * counted 1:1. Exact IF all qualifying usage is Linux, since that is the only
   * conversion GitHub documents.
   */
  privateHostedStandardMinutes: CandidateTotal;
  /**
   * H1-Linux - the subset of H1 whose SKU is unambiguously Linux. Where H1 and this
   * agree, no undocumented conversion was needed to produce the number.
   */
  privateHostedStandardLinuxMinutes: CandidateTotal;
  /**
   * H2 - the monetary hypothesis: the allowance is applied as a dollar discount, so
   * summed `discountAmount` over Actions items is the drawdown in dollars.
   */
  actionsDiscountUsd: CandidateTotal;
  /**
   * H2-minutes - H2 converted back to minutes per item via `pricePerUnit`. If the
   * allowance is monetary, this should land on the displayed minute figure without
   * any OS weighting, which would make the multiplier question moot.
   */
  actionsDiscountDerivedMinutes: CandidateTotal;
  /**
   * H3 - the account-wide discount across every product, to compare against the
   * billing overview's single "Current included usage $X" figure.
   */
  allProductsDiscountUsd: CandidateTotal;
  /**
   * H4 - the list-price value of PRIVATE-repository Actions minutes only.
   *
   * The sharpest test of the monetary hypothesis. If GitHub expresses included usage
   * in dollars and excludes public repositories from it, this is the figure the
   * billing overview's "Current included usage $X" should equal. It is the H2 dollar
   * candidate minus the public-repository portion, which H2 cannot separate.
   */
  privateActionsListPriceUsd: CandidateTotal;
}

const MINUTES_UNIT = /^minutes?$/iu;

function isActionsMinutes(item: UsageLineItem): boolean {
  return item.product.toLowerCase() === "actions" && MINUTES_UNIT.test(item.unitType);
}

function total(
  items: UsageLineItem[],
  pick: (item: UsageLineItem) => number | null,
  unit: CandidateTotal["unit"],
  caveat: string
): CandidateTotal {
  let value = 0;
  let itemCount = 0;
  for (const item of items) {
    const contribution = pick(item);
    if (contribution === null || !Number.isFinite(contribution)) continue;
    value += contribution;
    itemCount += 1;
  }
  return { value, unit, itemCount, caveat };
}

/**
 * Computes every candidate over one month of line items.
 *
 * `visibility` maps repository name to visibility. A name absent from the map is
 * treated as `unknown` and EXCLUDED from the private-repository candidates, so an
 * unresolved lookup understates rather than overstates. Understating is the safe
 * direction here: it produces a percentage that is too low, which reads as
 * conservative, where overstating reads as alarming and is the failure this phase
 * exists to prevent.
 */
export function computeCandidates(
  items: readonly UsageLineItem[],
  visibility: VisibilityMap
): DrawdownCandidates {
  const actionsMinutes = items.filter(isActionsMinutes);
  const qualifying = actionsMinutes.filter((item) => {
    if (item.repositoryName === null) return false;
    if (visibility[item.repositoryName] !== "private") return false;
    const runner = classifySku(item.sku);
    return runner.githubHosted === true && runner.standard === true;
  });
  const linuxOnly = qualifying.filter((item) => classifySku(item.sku).os === "linux");

  return {
    grossMinutes: total(
      actionsMinutes,
      (item) => item.quantity,
      "minutes",
      "Gross consumption, including public-repository and self-hosted usage that never draws down the allowance. Known wrong; kept as the control."
    ),
    privateHostedStandardMinutes: total(
      qualifying,
      (item) => item.quantity,
      "minutes",
      "Assumes 1:1 drawdown for every runner OS. Documented only for Linux; the Windows and macOS basis is unpublished."
    ),
    privateHostedStandardLinuxMinutes: total(
      linuxOnly,
      (item) => item.quantity,
      "minutes",
      "The subset needing no undocumented conversion. If this equals the previous candidate, the account is Linux-only and the OS question does not arise."
    ),
    actionsDiscountUsd: total(
      actionsMinutes,
      (item) => item.discountAmount,
      "usd",
      "Includes public-repository and self-hosted discounts, which are not allowance drawdown. Compare against the Actions tab's discount figure, not the minute figure."
    ),
    actionsDiscountDerivedMinutes: total(
      actionsMinutes,
      (item) =>
        item.discountAmount === null || item.pricePerUnit === null || item.pricePerUnit === 0
          ? null
          : item.discountAmount / item.pricePerUnit,
      "minutes",
      "Discount dollars converted back to minutes at each item's own rate. Carries the same conflation as the dollar figure."
    ),
    allProductsDiscountUsd: total(
      [...items],
      (item) => item.discountAmount,
      "usd",
      "Every product, for comparison against the billing overview's single included-usage dollar figure."
    ),
    privateActionsListPriceUsd: total(
      actionsMinutes.filter(
        (item) => item.repositoryName !== null && visibility[item.repositoryName] === "private"
      ),
      (item) => item.grossAmount,
      "usd",
      "List-price value of private-repository Actions minutes. The sharpest test of the monetary hypothesis; excludes an unresolved repository, so it understates."
    )
  };
}

/** One repository's contribution, so the public/private split is visible rather than inferred. */
export interface RepositoryBreakdown {
  repositoryName: string;
  visibility: RepositoryVisibility;
  minutesBySku: Record<string, number>;
  totalMinutes: number;
  listPriceUsd: number;
  discountUsd: number;
  netUsd: number;
}

/**
 * Per-repository Actions-minute totals.
 *
 * The candidate figures are aggregates, and an aggregate that misses cannot say
 * WHERE it missed. This breakdown is what turns "off by 31%" into "the public
 * repositories account for exactly the difference", which is the difference between
 * a failed measurement and a diagnosis.
 */
export function breakdownByRepository(
  items: readonly UsageLineItem[],
  visibility: VisibilityMap
): RepositoryBreakdown[] {
  const byRepo = new Map<string, RepositoryBreakdown>();
  for (const item of items.filter(isActionsMinutes)) {
    const name = item.repositoryName ?? "(no repository reported)";
    const existing = byRepo.get(name) ?? {
      repositoryName: name,
      visibility: visibility[name] ?? "unknown",
      minutesBySku: {},
      totalMinutes: 0,
      listPriceUsd: 0,
      discountUsd: 0,
      netUsd: 0
    };
    existing.minutesBySku[item.sku] = (existing.minutesBySku[item.sku] ?? 0) + item.quantity;
    existing.totalMinutes += item.quantity;
    existing.listPriceUsd += item.grossAmount ?? 0;
    existing.discountUsd += item.discountAmount ?? 0;
    existing.netUsd += item.netAmount ?? 0;
    byRepo.set(name, existing);
  }
  return [...byRepo.values()].sort((left, right) => right.totalMinutes - left.totalMinutes);
}

/**
 * The standard Linux runner's list price per minute, in USD.
 *
 * Used ONLY as a denominator of last resort, when a period contains no standard
 * GitHub-hosted Linux item to observe one from. Verified 2026-08-19 against
 * GitHub's Actions runner pricing table.
 *
 * It is a fallback rather than the primary source on purpose. GitHub cut runner
 * prices on 2026-01-01 (Linux $0.008 -> $0.006, Windows $0.016 -> $0.010, macOS
 * $0.080 -> $0.062), which is precisely the event that made every hardcoded
 * multiplier table in this file's history go stale. A constant that is only ever
 * a denominator for a period with nothing to measure has a bounded blast radius;
 * a constant that is the primary source does not.
 */
export const PUBLISHED_LINUX_RATE_USD_PER_MINUTE = 0.006;

/**
 * Historical note ONLY. Not read by any code path.
 *
 * GitHub's published minute multipliers were Linux 1x, Windows 2x, macOS 10x.
 * Those were never an independent taxonomy: they are exactly the pre-2026
 * per-minute price ratios ($0.008, $0.016, $0.080). The 2026-01-01 price cut
 * moved the same mechanism to 1x, 1.67x, and 10.33x, which is why this number was
 * revised three times - each revision hardcoded a snapshot of a price list that
 * had already moved or was about to.
 *
 * The code now implements the MECHANISM (weight = this item's price / the standard
 * Linux price observed in the same payload) rather than any snapshot of its output,
 * so a future price change, a new runner type, or an ARM variant needs no edit here.
 *
 * Retained as a comment rather than a constant so that nothing can accidentally
 * read it again. See `docs/policy/github-actions-minute-consumption.md`.
 */

/** Which denominator `resolveLinuxReferenceRate` ended up using. */
export type LinuxRateSource = "observed" | "published-fallback";

export interface LinuxReferenceRate {
  /** USD per minute for the standard Linux runner. */
  rate: number;
  /** Where that figure came from, so the panel can label the provenance. */
  source: LinuxRateSource;
}

/**
 * The denominator every drawdown weight is expressed against.
 *
 * Selection is deliberate, not `min`. A period may legitimately contain more than
 * one Linux rate (a sub-2-core variant priced below the standard 2-core runner),
 * and picking the cheapest would inflate every other item's weight by the ratio
 * between them. Larger runners are already excluded by `classifySku`, so the
 * standard set's CEILING is the 2-core baseline: taking the highest qualifying
 * Linux rate selects it without needing to parse core counts a second time.
 *
 * A non-positive or absent price never qualifies. Zero is the dangerous value: as a
 * denominator it produces infinities, and as a numerator it would silently drop an
 * item from the drawdown rather than marking the reconstruction incomplete.
 */
export function resolveLinuxReferenceRate(items: readonly UsageLineItem[]): LinuxReferenceRate {
  let observed: number | null = null;
  for (const item of items) {
    if (!isActionsMinutes(item)) continue;
    const runner = classifySku(item.sku);
    if (runner.os !== "linux" || runner.githubHosted !== true || runner.standard !== true) continue;
    const price = item.pricePerUnit;
    if (price === null || !Number.isFinite(price) || price <= 0) continue;
    if (observed === null || price > observed) observed = price;
  }
  return observed === null
    ? { rate: PUBLISHED_LINUX_RATE_USD_PER_MINUTE, source: "published-fallback" }
    : { rate: observed, source: "observed" };
}

/** One repository's contribution to the drawdown, as the panel shows it. */
export interface RepositoryContribution {
  repositoryName: string;
  visibility: RepositoryVisibility;
  /** Every Actions minute reported for this repository, free or not. */
  rawMinutes: number;
  /**
   * Minutes actually counted against the allowance after exclusions and weighting.
   * Zero for a public repository, which is the fact the panel exists to show.
   */
  weightedMinutes: number;
}

/**
 * Per-repository contributions, sorted by what each actually costs the allowance.
 *
 * `breakdownByRepository` above answers "where did the minutes go"; this answers
 * "which of them counted", which is a different question and the one a user asking
 * why 366 public-repository runs cost nothing is actually asking.
 */
export function contributionsByRepository(
  items: readonly UsageLineItem[],
  visibility: VisibilityMap
): RepositoryContribution[] {
  const reference = resolveLinuxReferenceRate(items);
  const byRepo = new Map<string, RepositoryContribution>();
  for (const item of items.filter(isActionsMinutes)) {
    const name = item.repositoryName ?? "(no repository reported)";
    const entry = byRepo.get(name) ?? {
      repositoryName: name,
      visibility: visibility[name] ?? "unknown",
      rawMinutes: 0,
      weightedMinutes: 0
    };
    entry.rawMinutes += item.quantity;
    const runner = classifySku(item.sku);
    const price = item.pricePerUnit;
    const counts =
      entry.visibility === "private" &&
      runner.githubHosted === true &&
      runner.standard === true &&
      runner.os !== "unknown" &&
      price !== null &&
      Number.isFinite(price) &&
      price > 0;
    if (counts) entry.weightedMinutes += item.quantity * ((price as number) / reference.rate);
    byRepo.set(name, entry);
  }
  return [...byRepo.values()].sort(
    (left, right) => right.weightedMinutes - left.weightedMinutes || right.rawMinutes - left.rawMinutes
  );
}

export interface DrawdownResult {
  /** Minutes counted against the allowance, or null when it could not be established. */
  minutes: number | null;
  /** Line items that contributed. */
  itemCount: number;
  /** Repositories whose visibility could not be resolved, and were therefore excluded. */
  unresolvedRepositories: string[];
  /**
   * The distinct weights actually applied, ascending.
   *
   * Replaces the former `usedWeighting` boolean, which asked whether any weight
   * differed from a hardcoded 1 - a question that stops meaning anything once the
   * weights are derived per item. The set of weights survives the change and says
   * strictly more: `[1]` is a single-rate period, `[1, 1.67, 10.33]` names the mix.
   */
  appliedWeights: number[];
  /** The denominator every weight above is expressed against. */
  linuxReferenceRate: LinuxReferenceRate;
}

/**
 * The product-facing reconstruction: minutes counted against the included allowance.
 *
 * Three exclusions, all confirmed against GitHub's own report reference, which
 * defines `discount_amount` as covering "your account's included usage" AND
 * "GitHub Actions usage for standard GitHub-hosted runners in public repositories
 * and for self-hosted runners":
 *
 *   1. Public repositories - free, never draws down.
 *   2. Self-hosted runners - discounted, does not draw down.
 *   3. Larger runners - documentation states included minutes cannot be used for them.
 *
 * Returns `null` rather than a partial figure when NO repository could be resolved,
 * because zero-from-total-failure and zero-from-genuinely-no-private-usage are
 * different facts and must not render identically. An individually unresolved
 * repository is excluded and named, which understates - the safe direction, since an
 * understated bar reads as conservative while an overstated one raises a false alarm.
 */
export function computeDrawdownMinutes(
  items: readonly UsageLineItem[],
  visibility: VisibilityMap
): DrawdownResult {
  const actionsMinutes = items.filter(isActionsMinutes);
  const unresolved = new Set<string>();
  const linuxReferenceRate = resolveLinuxReferenceRate(items);
  const weights = new Set<number>();
  let minutes = 0;
  let itemCount = 0;
  let resolvedAny = false;

  for (const item of actionsMinutes) {
    if (item.repositoryName === null) continue;
    const state = visibility[item.repositoryName];
    if (state === undefined || state === "unknown") {
      unresolved.add(item.repositoryName);
      continue;
    }
    resolvedAny = true;
    if (state !== "private") continue;
    const runner = classifySku(item.sku);
    // Order matters. A DEFINITE exclusion (self-hosted, larger runner) is a known
    // fact and is simply skipped. An UNRECOGNIZED SKU is not a fact at all, and must
    // be reported rather than quietly dropped - weighting it as Linux would
    // understate a macOS runner tenfold, and skipping it silently hides that the
    // classification rules have fallen behind GitHub's SKU vocabulary.
    if (runner.githubHosted === false || runner.standard === false) continue;
    if (runner.os === "unknown") {
      unresolved.add(item.sku);
      continue;
    }
    // The weight is this item's own list price relative to the standard Linux rate
    // observed in the same payload. No table, so nothing to go stale when GitHub
    // moves prices, adds a runner type, or ships an ARM variant.
    //
    // An item that PASSED every exclusion above but carries no usable price is a
    // hole in the reconstruction, not a zero. Treating it as zero would quietly
    // shrink the drawdown; reporting it alongside the unresolved repositories makes
    // the same partial-data guard below fire, so the meter reads unknown instead of
    // confidently low.
    const price = item.pricePerUnit;
    if (price === null || !Number.isFinite(price) || price <= 0) {
      unresolved.add(item.sku);
      continue;
    }
    const weight = price / linuxReferenceRate.rate;
    weights.add(weight);
    minutes += item.quantity * weight;
    itemCount += 1;
  }

  const unresolvedRepositories = [...unresolved];

  // A partial resolution is UNKNOWN, not a smaller number.
  //
  // v3.16.3 returned the partial sum whenever ANY repository resolved. Public
  // repositories resolve without extra permission while private ones 404 without
  // `repo` scope, so an account whose usage was mostly public produced
  // resolvedAny=true with a sum of 0 - rendered as a confident 0% against a
  // 2,000-minute allowance. Understating is only "the safe direction" when the
  // result is still recognizably a usage figure; zero is not, and neither is any
  // total that silently omits the repositories that actually consume the quota.
  // No line items at all is a different fact from a partial resolution: GitHub
  // reported no Actions usage for the period, so the drawdown is genuinely zero and
  // a 0% meter is the truth rather than a guess. The guard above exists for items
  // that FAILED to resolve; an empty set has nothing to fail. Without this, a month
  // with no Actions runs rendered "could not be reconstructed" against a perfectly
  // good allowance - observed 2026-08-11 on an organization at 0 minutes.
  const noUsageReported = actionsMinutes.length === 0;
  const complete = noUsageReported || (unresolvedRepositories.length === 0 && resolvedAny);
  return {
    minutes: complete ? minutes : null,
    itemCount,
    unresolvedRepositories,
    appliedWeights: [...weights].sort((left, right) => left - right),
    linuxReferenceRate
  };
}

/**
 * Converts a storage figure reported in GigabyteHours into the GB-months unit that
 * GitHub's entitlement is expressed in.
 *
 * DOCUMENTED, not inferred. GitHub's Actions billing page states: "Your bill
 * reflects the total storage used throughout the month, measured in GB-Hours" and
 * "Your monthly bill converts GB-Hours to GB-Months by dividing by the hours in the
 * month (usually 720 hours for a 30-day month)".
 * https://docs.github.com/en/billing/concepts/product-billing/github-actions
 *
 * Corroborated in both directions on a real account: July 432.305 GB-hours / 744 =
 * 0.581 GB against a 0.5 GB allowance, which the billing page showed as saturated;
 * August 64.568 / 744 = 0.087 GB, which it showed as "0 GB used".
 *
 * The full month's hours are used even mid-month, matching how GitHub states the
 * bill is computed. A partial-month denominator would read higher and would not
 * match the figure the user sees.
 */
export function gigabyteHoursToGigabyteMonths(gigabyteHours: number, hoursInMonth: number): number | null {
  if (!Number.isFinite(gigabyteHours) || !Number.isFinite(hoursInMonth) || hoursInMonth <= 0) return null;
  return gigabyteHours / hoursInMonth;
}

/** Hours in the UTC month containing `timestamp`. */
export function hoursInUtcMonth(timestamp: number): number {
  const date = new Date(timestamp);
  const start = Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), 1);
  const end = Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + 1, 1);
  return (end - start) / 3_600_000;
}

/** Distinct SKU inventory, so the classification rules can be checked against reality. */
export interface SkuObservation {
  product: string;
  sku: string;
  unitType: string;
  itemCount: number;
  totalQuantity: number;
  classification: RunnerClassification;
}

/**
 * Every distinct (product, sku, unitType) triple observed, with how the rules above
 * classified it.
 *
 * This is the probe's most valuable output. The classification rules are pattern
 * guesses against strings GitHub does not publish; this table is what replaces the
 * guess with observation, and any row whose `unrecognized` is true is a rule that
 * needs writing before the reconstruction can be trusted.
 */
export function inventorySkus(items: readonly UsageLineItem[]): SkuObservation[] {
  const byKey = new Map<string, SkuObservation>();
  for (const item of items) {
    const key = `${item.product} ${item.sku} ${item.unitType}`;
    const existing = byKey.get(key);
    if (existing === undefined) {
      byKey.set(key, {
        product: item.product,
        sku: item.sku,
        unitType: item.unitType,
        itemCount: 1,
        totalQuantity: item.quantity,
        classification: classifySku(item.sku)
      });
      continue;
    }
    existing.itemCount += 1;
    existing.totalQuantity += item.quantity;
  }
  return [...byKey.values()].sort((left, right) =>
    left.product === right.product ? left.sku.localeCompare(right.sku) : left.product.localeCompare(right.product)
  );
}

export interface ReconciliationVerdict {
  candidate: keyof DrawdownCandidates;
  observed: number;
  displayed: number;
  /** Absolute relative difference, or null when `displayed` is zero. */
  relativeDifference: number | null;
  reconciles: boolean;
}

/**
 * The tolerance, declared BEFORE any comparison is run, as sub-task 2.3 requires.
 *
 * 1% (0.01). Justification: GitHub's own panel displays one decimal place on a
 * three-digit minute figure, so display rounding alone can account for roughly 0.4%.
 * A 1% band absorbs that plus per-item minute rounding ("GitHub rounds the minutes
 * and partial minutes each job uses up to the nearest whole minute") without being
 * loose enough to admit a structurally wrong formula: the defect this phase exists to
 * catch is an eightfold error, and every plausible wrong candidate differs by tens of
 * percent, not by one.
 */
export const RECONCILIATION_TOLERANCE = 0.01;

/** Compares one candidate against the figure GitHub itself displays. */
export function reconcile(
  candidate: keyof DrawdownCandidates,
  observed: number,
  displayed: number,
  tolerance: number = RECONCILIATION_TOLERANCE
): ReconciliationVerdict {
  if (displayed === 0) {
    return {
      candidate,
      observed,
      displayed,
      relativeDifference: null,
      reconciles: observed === 0
    };
  }
  const relativeDifference = Math.abs(observed - displayed) / Math.abs(displayed);
  return {
    candidate,
    observed,
    displayed,
    relativeDifference,
    reconciles: relativeDifference <= tolerance
  };
}
