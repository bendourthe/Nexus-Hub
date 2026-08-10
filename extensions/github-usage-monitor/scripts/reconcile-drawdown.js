#!/usr/bin/env node
/**
 * v3.16.3 Phase 2, sub-task 2.3: measure the drawdown numerator against a real
 * account, BEFORE any percentage design is chosen.
 *
 * The monitor currently sums gross Actions minutes. On a real account that read
 * 1,003 minutes for a month in which GitHub's Included-usage panel showed 119.7 of
 * 2,000 consumed. This script computes several candidate reconstructions side by
 * side and prints them next to the figures you read off github.com/settings/billing,
 * so the plan's reconciliation gate is decided by measurement rather than by
 * argument. It selects no winner and tunes nothing.
 *
 * Run from extensions/github-usage-monitor after `npm run compile`. The token comes
 * from the environment so it never reaches shell history as an argument:
 *
 *   # PowerShell
 *   $env:GITHUB_BILLING_PROBE_TOKEN = "ghp_..."
 *   node scripts/reconcile-drawdown.js --level user --name YOUR_USERNAME
 *
 *   # bash
 *   GITHUB_BILLING_PROBE_TOKEN=ghp_... node scripts/reconcile-drawdown.js --level user --name YOUR_USERNAME
 *
 * Use a CLASSIC PAT. GitHub's own usage-reporting tutorial states the billing usage
 * endpoints do not support fine-grained personal access tokens.
 *
 * PRIVACY. Repository names are hashed by default, because the output is meant to be
 * pasted into an issue or a probe document. Pass --reveal-repos only if you intend
 * the real names to be shared. The token is never printed under any flag.
 *
 * NETWORK COST. One billing request, plus one `GET /repos/{owner}/{repo}` per
 * DISTINCT repository in the month, cached in-process. A month touching twenty
 * repositories costs twenty-one requests against a 5,000/hour limit.
 */

"use strict";

const {
  breakdownByRepository,
  classifySku,
  computeCandidates,
  inventorySkus,
  reconcile,
  RECONCILIATION_TOLERANCE
} = require("../out/providers/drawdown.js");
const { createHash } = require("node:crypto");

const TOKEN_VAR = "GITHUB_BILLING_PROBE_TOKEN";
const LEVELS = new Set(["user", "organization", "enterprise"]);
const API = "https://api.github.com";
const HEADERS = (token) => ({
  Accept: "application/vnd.github+json",
  Authorization: `Bearer ${token}`,
  "X-GitHub-Api-Version": "2026-03-10",
  "User-Agent": "nexus-hub-github-usage-monitor-drawdown-probe/0.2.0"
});

function parseArgs(argv) {
  const args = {
    level: "user",
    name: null,
    year: null,
    month: null,
    months: null,
    revealRepos: false,
    displayedMinutes: null,
    displayedAllowance: null,
    displayedIncludedUsd: null
  };
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index];
    const value = argv[index + 1];
    const takeNumber = () => {
      index += 1;
      const parsed = Number(value);
      return Number.isFinite(parsed) ? parsed : null;
    };
    if (flag === "--level" && value) { args.level = value; index += 1; }
    else if (flag === "--name" && value) { args.name = value; index += 1; }
    else if (flag === "--year" && value) { args.year = takeNumber(); }
    else if (flag === "--month" && value) { args.month = takeNumber(); }
    else if (flag === "--displayed-minutes" && value) { args.displayedMinutes = takeNumber(); }
    else if (flag === "--displayed-allowance" && value) { args.displayedAllowance = takeNumber(); }
    else if (flag === "--displayed-included-usd" && value) { args.displayedIncludedUsd = takeNumber(); }
    else if (flag === "--months" && value) { args.months = takeNumber(); }
    else if (flag === "--reveal-repos") { args.revealRepos = true; }
    else if (flag === "--help" || flag === "-h") { args.help = true; }
  }
  return args;
}

function usage() {
  console.log([
    "Usage: node scripts/reconcile-drawdown.js --level <user|organization|enterprise> --name <owner> [options]",
    "",
    "  --year N --month N          Billing month (defaults to the current UTC month)",
    "  --months N                  SWEEP MODE: summarize the N months ending at that",
    "                              month, one row each. Finds a month with enough",
    "                              private non-Linux usage to settle the weighting",
    "                              question. Renders no verdict; use single-month mode",
    "                              with --displayed-* once you have picked a month.",
    "  --displayed-minutes N       The 'used' minutes GitHub's Included-usage panel shows",
    "  --displayed-allowance N     The 'included' minutes that panel shows",
    "  --displayed-included-usd N  The billing overview's 'Current included usage $X'",
    "  --reveal-repos              Print real repository names instead of hashes",
    "",
    `  Token is read from $${TOKEN_VAR}, never from an argument. Use a classic PAT.`,
    "  Requires `npm run compile` first.",
    "",
    "  The three --displayed-* values are what turn this from a dump into a",
    "  reconciliation. Without them the script still prints every candidate, but it",
    "  cannot render a verdict."
  ].join("\n"));
}

function shortHash(value) {
  return `repo-${createHash("sha256").update(value).digest("hex").slice(0, 8)}`;
}

async function getJson(path, token) {
  const response = await fetch(`${API}${path}`, { headers: HEADERS(token) });
  if (!response.ok) {
    return { ok: false, status: response.status, statusText: response.statusText };
  }
  return { ok: true, value: await response.json() };
}

function billingPath(level, name, suffix) {
  const encoded = encodeURIComponent(name);
  if (level === "user") return `/users/${encoded}/settings/billing/${suffix}`;
  if (level === "organization") return `/organizations/${encoded}/settings/billing/${suffix}`;
  return `/enterprises/${encoded}/settings/billing/${suffix}`;
}

/**
 * Resolves visibility for each distinct repository.
 *
 * A failed lookup records "unknown" rather than assuming a default. `computeCandidates`
 * excludes unknown repositories from the private-repository candidates, so an
 * unresolved lookup understates the drawdown - which is the safe direction, since an
 * understated percentage reads as conservative while an overstated one is the exact
 * failure this phase exists to prevent.
 */
async function resolveVisibility(items, owner, token) {
  const names = [...new Set(items.map((item) => item.repositoryName).filter((name) => typeof name === "string" && name.length > 0))];
  const visibility = {};
  const failures = [];
  for (const name of names) {
    const slug = name.includes("/") ? name : `${owner}/${name}`;
    const result = await getJson(`/repos/${slug}`, token);
    if (result.ok) {
      visibility[name] = result.value.private === true ? "private" : "public";
      continue;
    }
    visibility[name] = "unknown";
    failures.push({ name, status: result.status });
  }
  return { visibility, lookupCount: names.length, failures };
}

function formatCandidate(label, candidate, displayName) {
  const value = candidate.unit === "usd" ? `$${candidate.value.toFixed(2)}` : `${candidate.value.toFixed(1)} min`;
  return `  ${label.padEnd(38)} ${value.padStart(12)}   (${candidate.itemCount} items)\n      ${displayName}`;
}

/** Pulls one month and returns the private-repository usage split by runner OS. */
async function summarizeMonth(args, token, year, month, visibilityCache) {
  const query = new URLSearchParams({ year: String(year), month: String(month) });
  const result = await getJson(`${billingPath(args.level, args.name, "usage")}?${query}`, token);
  if (!result.ok) return { year, month, error: `HTTP ${result.status}` };

  const raw = Array.isArray(result.value?.usageItems) ? result.value.usageItems : [];
  const items = raw.map((item) => ({
    date: String(item.date ?? ""),
    product: String(item.product ?? ""),
    sku: String(item.sku ?? ""),
    unitType: String(item.unitType ?? ""),
    quantity: Number(item.quantity ?? item.grossQuantity ?? 0),
    pricePerUnit: typeof item.pricePerUnit === "number" ? item.pricePerUnit : null,
    grossAmount: typeof item.grossAmount === "number" ? item.grossAmount : null,
    discountAmount: typeof item.discountAmount === "number" ? item.discountAmount : null,
    netAmount: typeof item.netAmount === "number" ? item.netAmount : null,
    repositoryName: typeof item.repositoryName === "string" ? item.repositoryName : null
  }));
  if (items.length === 0) return { year, month, empty: true };

  // Visibility is cached ACROSS months: the same repository keeps its visibility, and
  // a sweep over a year would otherwise re-request the same handful of repos monthly.
  const names = [...new Set(items.map((item) => item.repositoryName).filter(Boolean))];
  let failed = 0;
  for (const name of names) {
    if (visibilityCache[name] !== undefined) continue;
    const slug = name.includes("/") ? name : `${args.name}/${name}`;
    const repo = await getJson(`/repos/${slug}`, token);
    if (repo.ok) visibilityCache[name] = repo.value.private === true ? "private" : "public";
    else { visibilityCache[name] = "unknown"; failed += 1; }
  }

  const privateByOs = { linux: 0, windows: 0, macos: 0, unknown: 0 };
  for (const item of items) {
    if (item.product.toLowerCase() !== "actions" || !/^minutes?$/iu.test(item.unitType)) continue;
    if (item.repositoryName === null || visibilityCache[item.repositoryName] !== "private") continue;
    const runner = classifySku(item.sku);
    if (runner.githubHosted !== true || runner.standard !== true) continue;
    privateByOs[runner.os] += item.quantity;
  }
  const candidates = computeCandidates(items, visibilityCache);
  const privateTotal = privateByOs.linux + privateByOs.windows + privateByOs.macos + privateByOs.unknown;
  const nonLinux = privateByOs.windows + privateByOs.macos;
  return {
    year,
    month,
    failed,
    privateByOs,
    privateTotal,
    nonLinux,
    // The share of private minutes whose weighting is undocumented. This is the
    // number that decides whether a month can settle the question: a month that is
    // 3% non-Linux cannot distinguish 1:1 from 2x within rounding noise, and one that
    // is 40% non-Linux separates them decisively.
    nonLinuxShare: privateTotal === 0 ? 0 : nonLinux / privateTotal,
    grossMinutes: candidates.grossMinutes.value
  };
}

/**
 * Sweep mode. Reports each month's private-repository usage split by runner OS, so a
 * month with enough non-Linux private usage can be chosen for a decisive
 * single-month reconciliation.
 *
 * It deliberately renders NO verdict: reconciling needs the figure GitHub displays
 * for that month, which is read off the billing page one month at a time.
 */
async function sweep(args, token, endYear, endMonth) {
  const visibilityCache = {};
  const rows = [];
  console.log(`\n=== Month sweep - ${args.months} months ending ${endYear}-${String(endMonth).padStart(2, "0")} ===`);
  console.log("Looking for a month with substantial PRIVATE non-Linux usage, which is the");
  console.log("only thing that can settle whether Windows and macOS draw down at face value.\n");

  for (let back = 0; back < args.months; back += 1) {
    const date = new Date(Date.UTC(endYear, endMonth - 1 - back, 1));
    const row = await summarizeMonth(args, token, date.getUTCFullYear(), date.getUTCMonth() + 1, visibilityCache);
    rows.push(row);
  }

  console.log("  Month     Private min   Linux   Windows   macOS   non-Linux share   Gross min");
  for (const row of rows) {
    const label = `${row.year}-${String(row.month).padStart(2, "0")}`;
    if (row.error) { console.log(`  ${label}   request failed (${row.error})`); continue; }
    if (row.empty) { console.log(`  ${label}   no usage reported`); continue; }
    console.log(
      `  ${label}   ${String(row.privateTotal.toFixed(0)).padStart(11)}   ` +
      `${String(row.privateByOs.linux.toFixed(0)).padStart(5)}   ` +
      `${String(row.privateByOs.windows.toFixed(0)).padStart(7)}   ` +
      `${String(row.privateByOs.macos.toFixed(0)).padStart(5)}   ` +
      `${(row.nonLinuxShare * 100).toFixed(1).padStart(15)}%   ` +
      `${String(row.grossMinutes.toFixed(0)).padStart(9)}`
    );
  }

  const usable = rows
    .filter((row) => !row.error && !row.empty && row.privateTotal >= 30 && row.nonLinuxShare >= 0.15)
    .sort((left, right) => right.nonLinuxShare - left.nonLinuxShare);

  console.log("");
  if (usable.length === 0) {
    console.log("NO MONTH CAN SETTLE THE QUESTION. Every month is either Linux-only in private");
    console.log("repositories or too small for the difference between 1:1 and weighted drawdown");
    console.log("to exceed rounding noise. That is a real answer, not a failed run: this account");
    console.log("simply has no evidence either way, and the decision has to be made on judgement.");
    return 0;
  }
  const best = usable[0];
  const label = `${best.year}-${String(best.month).padStart(2, "0")}`;
  console.log(`BEST MONTH: ${label} - ${best.privateTotal.toFixed(0)} private minutes, ${(best.nonLinuxShare * 100).toFixed(0)}% non-Linux.`);
  console.log("  1:1 weighting predicts a drawdown of about " + best.privateTotal.toFixed(0) + " minutes.");
  console.log("  Legacy weighting (Windows 2x, macOS 10x) predicts about " +
    (best.privateByOs.linux + best.privateByOs.windows * 2 + best.privateByOs.macos * 10).toFixed(0) + ".");
  console.log("  Those differ enough to tell apart. Read that month's figure off the billing");
  console.log("  page (set Timeframe to it), then run:");
  console.log(`     node scripts/reconcile-drawdown.js --level ${args.level} --name ${args.name} \\`);
  console.log(`       --year ${best.year} --month ${best.month} --displayed-minutes <that month's used minutes> \\`);
  console.log("       --displayed-allowance 2000 --displayed-included-usd <that month's included usage>");
  return 0;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) { usage(); return 0; }
  if (!LEVELS.has(args.level)) { console.error(`--level must be one of: ${[...LEVELS].join(", ")}`); return 2; }
  if (!args.name) { console.error("--name is required (the username, org slug, or enterprise slug)"); return 2; }

  const token = process.env[TOKEN_VAR];
  if (!token) { console.error(`Set $${TOKEN_VAR} to a classic PAT for this account.`); return 2; }

  // Caught before the request, because a placeholder produces a 401 that reads
  // identically to a revoked token and sends you debugging the wrong thing.
  if (/^gh[pousr]_\.\.\.$/u.test(token.trim()) || token.trim().endsWith("...")) {
    console.error(`$${TOKEN_VAR} still holds the placeholder "${token.trim()}".`);
    console.error("Replace it with a real classic PAT. Create one at:");
    console.error("  https://github.com/settings/tokens  ->  Generate new token (classic)");
    console.error("  Scope needed for --level user: 'user' (read:user is enough for billing).");
    return 2;
  }
  if (args.name === "YOUR_USERNAME") {
    console.error("--name is still the placeholder YOUR_USERNAME. Pass your real GitHub login.");
    return 2;
  }

  const now = new Date();
  const year = args.year ?? now.getUTCFullYear();
  const month = args.month ?? now.getUTCMonth() + 1;

  if (args.months !== null && args.months > 1) {
    return sweep(args, token, year, month);
  }

  const query = new URLSearchParams({ year: String(year), month: String(month) });
  const usageResult = await getJson(`${billingPath(args.level, args.name, "usage")}?${query}`, token);
  if (!usageResult.ok) {
    console.error(`Billing usage request failed: ${usageResult.status} ${usageResult.statusText}`);
    // These statuses mean different things and are worth separating: conflating them
    // sends you to fix a permission that was never the problem.
    if (usageResult.status === 401) {
      console.error("401 means the TOKEN is invalid, revoked, or expired. It says nothing about");
      console.error("  whether your token class or role is sufficient. Check that");
      console.error(`  $${TOKEN_VAR} holds a real, current classic PAT and retry.`);
    } else if (usageResult.status === 403) {
      console.error("403 means the token authenticated but is not authorized for this target.");
      console.error("  Check the token CLASS (classic PAT; fine-grained is rejected here), the");
      console.error("  scope, and your role on the owner. Run scripts/probe-billing-auth.js,");
      console.error("  which reads GitHub's X-Accepted-OAuth-Scopes header and names the gap.");
    } else if (usageResult.status === 404) {
      console.error("404 usually means the owner name is wrong, or enhanced billing is not");
      console.error("  enabled for this account. Verify --level and --name first.");
    }
    return 1;
  }

  const rawItems = Array.isArray(usageResult.value?.usageItems) ? usageResult.value.usageItems : [];
  if (rawItems.length === 0) {
    console.error(`No usage items returned for ${year}-${String(month).padStart(2, "0")}. Try an earlier month.`);
    return 1;
  }

  const items = rawItems.map((item) => ({
    date: String(item.date ?? ""),
    product: String(item.product ?? ""),
    sku: String(item.sku ?? ""),
    unitType: String(item.unitType ?? ""),
    quantity: Number(item.quantity ?? item.grossQuantity ?? 0),
    pricePerUnit: typeof item.pricePerUnit === "number" ? item.pricePerUnit : null,
    grossAmount: typeof item.grossAmount === "number" ? item.grossAmount : null,
    discountAmount: typeof item.discountAmount === "number" ? item.discountAmount : null,
    netAmount: typeof item.netAmount === "number" ? item.netAmount : null,
    repositoryName: typeof item.repositoryName === "string" ? item.repositoryName : null,
    organizationName: typeof item.organizationName === "string" ? item.organizationName : null
  }));

  // The `/usage/summary` endpoint is the one surface carrying a `discountQuantity`
  // in the metric's OWN unit rather than in dollars. If GitHub reports the discounted
  // QUANTITY of Actions minutes directly, no reconstruction is needed at all - the
  // drawdown is a field rather than an inference. It carries no `repositoryName`,
  // which is why it cannot replace the per-repository work above, but it costs one
  // request and is the last unmeasured surface.
  const summaryResult = await getJson(`${billingPath(args.level, args.name, "usage/summary")}?${query}`, token);

  const { visibility, lookupCount, failures } = await resolveVisibility(items, args.name, token);
  const candidates = computeCandidates(items, visibility);
  const skus = inventorySkus(items);
  const repositories = breakdownByRepository(items, visibility);

  const label = (name) => (args.revealRepos ? name : shortHash(name));

  console.log(`\n=== Drawdown reconciliation probe - ${year}-${String(month).padStart(2, "0")} ===`);
  console.log(`Scope: ${args.level}   Items: ${items.length}   Repository lookups: ${lookupCount}`);
  console.log(`Repository names are ${args.revealRepos ? "REVEALED (--reveal-repos)" : "hashed; pass --reveal-repos to show them"}.\n`);

  console.log("--- Observed SKU inventory (the rules below are guesses; this is the ground truth) ---");
  for (const observation of skus) {
    const runner = observation.classification;
    const flag = runner.unrecognized ? "  <-- UNRECOGNIZED, needs a rule" : "";
    console.log(
      `  ${observation.product} / ${observation.sku} / ${observation.unitType}` +
      `\n      qty ${observation.totalQuantity} over ${observation.itemCount} items | os=${runner.os} hosted=${runner.githubHosted} standard=${runner.standard}${flag}`
    );
  }

  console.log("\n--- /usage/summary quantity triplet (the only per-quantity discount GitHub serves) ---");
  if (!summaryResult.ok) {
    console.log(`  Request failed: HTTP ${summaryResult.status}. Not fatal; the reconstruction above stands alone.`);
  } else {
    const summaryItems = Array.isArray(summaryResult.value?.usageItems) ? summaryResult.value.usageItems : [];
    if (summaryItems.length === 0) {
      console.log("  No usageItems returned.");
    }
    for (const summaryItem of summaryItems) {
      console.log(
        `  ${String(summaryItem.product ?? "?")} / ${String(summaryItem.sku ?? "?")} / ${String(summaryItem.unitType ?? "?")}` +
        `\n      gross=${summaryItem.grossQuantity ?? "n/a"}  discount=${summaryItem.discountQuantity ?? "n/a"}  net=${summaryItem.netQuantity ?? "n/a"}` +
        `   ($ gross=${summaryItem.grossAmount ?? "n/a"} discount=${summaryItem.discountAmount ?? "n/a"} net=${summaryItem.netAmount ?? "n/a"})`
      );
    }
    console.log("  Read `discount` above in the metric's OWN unit. If an Actions/minutes row's");
    console.log("  discount quantity equals the drawdown GitHub displays, the numerator is a");
    console.log("  served field and no reconstruction is needed.");
  }

  console.log("\n--- Per-repository Actions minutes ---");
  for (const repository of repositories) {
    const skuDetail = Object.entries(repository.minutesBySku)
      .map(([sku, minutes]) => `${sku}=${minutes}`)
      .join(", ");
    console.log(
      `  ${label(repository.repositoryName).padEnd(24)} ${repository.visibility.padEnd(8)} ` +
      `${repository.totalMinutes.toFixed(1).padStart(8)} min   list $${repository.listPriceUsd.toFixed(2)}   ` +
      `discount $${repository.discountUsd.toFixed(2)}   net $${repository.netUsd.toFixed(2)}\n      ${skuDetail}`
    );
  }

  if (failures.length > 0) {
    console.log("\n  !! VISIBILITY LOOKUPS FAILED - the run is NOT a valid reconciliation:");
    for (const failure of failures) {
      console.log(`     ${label(failure.name)} -> HTTP ${failure.status}`);
    }
    console.log("     A 404 here almost always means the token lacks the 'repo' scope, so");
    console.log("     PRIVATE repositories are invisible to it - and those are exactly the");
    console.log("     ones that draw down the allowance. Re-issue the token with 'repo'");
    console.log("     added to 'user' and re-run before drawing any conclusion.");
  }

  console.log("\n--- Candidate reconstructions ---");
  console.log(formatCandidate("CONTROL gross Actions minutes", candidates.grossMinutes, candidates.grossMinutes.caveat));
  console.log(formatCandidate("H1 private+hosted+standard min", candidates.privateHostedStandardMinutes, candidates.privateHostedStandardMinutes.caveat));
  console.log(formatCandidate("H1-Linux subset", candidates.privateHostedStandardLinuxMinutes, candidates.privateHostedStandardLinuxMinutes.caveat));
  console.log(formatCandidate("H2 Actions discount (USD)", candidates.actionsDiscountUsd, candidates.actionsDiscountUsd.caveat));
  console.log(formatCandidate("H2 discount -> minutes", candidates.actionsDiscountDerivedMinutes, candidates.actionsDiscountDerivedMinutes.caveat));
  console.log(formatCandidate("H3 all-product discount (USD)", candidates.allProductsDiscountUsd, candidates.allProductsDiscountUsd.caveat));
  console.log(formatCandidate("H4 private Actions list price (USD)", candidates.privateActionsListPriceUsd, candidates.privateActionsListPriceUsd.caveat));

  if (args.displayedMinutes === null && args.displayedIncludedUsd === null) {
    console.log("\nNo --displayed-* values given, so no verdict was rendered.");
    console.log("Re-run with the figures from github.com/settings/billing to complete the gate.");
    return 0;
  }

  // The period guard. Comparing one month's API data against another month's
  // screenshot produces a mismatch that looks like a formula defect and is not one.
  // This already happened once: an August pull was compared against figures from a
  // month whose gross was 1,003 rather than 1,287.
  if (failures.length > 0) {
    console.log("\nVERDICT WITHHELD: visibility lookups failed, so the private-repository");
    console.log("candidates are structurally understated. Fix the token scope and re-run.");
    return 1;
  }
  console.log(`\n  Confirm before reading the verdict: the --displayed-* figures below must come`);
  console.log(`  from GitHub's billing page for ${year}-${String(month).padStart(2, "0")}, the same period this run queried.`);

  console.log(`\n--- Reconciliation (tolerance ${(RECONCILIATION_TOLERANCE * 100).toFixed(0)}%, declared before the comparison) ---`);
  const verdicts = [];
  if (args.displayedMinutes !== null) {
    for (const key of ["grossMinutes", "privateHostedStandardMinutes", "privateHostedStandardLinuxMinutes", "actionsDiscountDerivedMinutes"]) {
      verdicts.push(reconcile(key, candidates[key].value, args.displayedMinutes));
    }
  }
  if (args.displayedIncludedUsd !== null) {
    for (const key of ["actionsDiscountUsd", "allProductsDiscountUsd", "privateActionsListPriceUsd"]) {
      verdicts.push(reconcile(key, candidates[key].value, args.displayedIncludedUsd));
    }
  }
  for (const verdict of verdicts) {
    const delta = verdict.relativeDifference === null ? "n/a" : `${(verdict.relativeDifference * 100).toFixed(1)}%`;
    console.log(
      `  ${verdict.reconciles ? "RECONCILES" : "no       "}  ${verdict.candidate.padEnd(36)} ` +
      `observed ${verdict.observed.toFixed(2)} vs displayed ${verdict.displayed.toFixed(2)}  (off by ${delta})`
    );
  }

  const winners = verdicts.filter((verdict) => verdict.reconciles && verdict.candidate !== "grossMinutes");
  console.log("");
  if (winners.length === 0) {
    console.log("NO CANDIDATE RECONCILES. That is a valid result: sub-task 2.3's cut line applies,");
    console.log("percentages are dropped from this release, and the explained-absence states ship");
    console.log("instead. Do NOT tune a formula to close the gap - record the finding.");
  } else {
    console.log(`RECONCILED: ${winners.map((winner) => winner.candidate).join(", ")}`);
    console.log("Record this in docs/v3/v3.16/development/github-entitlement-probe.md with both");
    console.log("numbers before promoting the candidate to product behavior.");
  }
  return 0;
}

main()
  .then((code) => { process.exitCode = code; })
  .catch((error) => {
    // Never print the error object: a thrown fetch error can carry the request, and
    // the request carries the Authorization header.
    console.error(`Probe failed: ${error instanceof Error ? error.name : "unknown error"}`);
    process.exitCode = 1;
  });
