/**
 * Saturation-aware verdicts over monthly drawdown observations.
 *
 * This module exists because of a specific, repeated mistake. The Actions drawdown
 * model was revised three times, and twice the revision rested on treating a
 * SATURATED meter as a measurement. A meter pinned at its cap reports only "at least
 * the allowance". It can refute a model that predicts below the cap; it can never
 * confirm one that predicts above it, because every model predicting above the cap
 * produces the identical display.
 *
 * The inverse trap cost the second revision: a month whose usage is almost entirely
 * Linux yields the same predicted total under EVERY candidate weighting, because the
 * weights only differ on non-Linux items. Counting such a month as agreement is how
 * an all-1 table was justified against data that never tested it.
 *
 * Pure by construction: no network, no `vscode`, no configuration. A verdict must be
 * reproducible from the numbers alone, or it is not evidence.
 */

/**
 * How far a prediction may sit from an UNSATURATED displayed value and still count
 * as agreement.
 *
 * Declared before any comparison is written, following the precedent of
 * `RECONCILIATION_TOLERANCE` in `drawdown.ts`, and set to the same 1%. The
 * justification carries over unchanged: GitHub displays one decimal place on a
 * three-digit minute figure, so display rounding alone accounts for roughly 0.4%,
 * and per-job minute rounding accounts for the rest. Every structurally wrong
 * candidate this is meant to catch differs by tens of percent, not by one.
 */
export const OBSERVATION_TOLERANCE = 0.01;

/**
 * The minimum share of predicted drawdown that must come from NON-Linux runners
 * before a month can discriminate between candidate weightings.
 *
 * 15%. Justification: candidate weightings differ only on non-Linux items, so a
 * month's discriminating power is bounded by the non-Linux share times the spread
 * between candidates. The two live candidates (price ratios 1.67x / 10.33x versus
 * the legacy published 2x / 10x) differ by about 0.3% of the weighted total, and
 * the unweighted model differs from both by the full weighted excess. At a 15%
 * non-Linux share the unweighted model is off by more than the 1% tolerance and is
 * therefore testable; below it, the month agrees with everything and proves nothing.
 *
 * The 2026-08-09 and 2026-08-10 observations sit at roughly 3%, well under this bar.
 * They were cited as support for the unweighted model. They are not.
 */
export const DISCRIMINATING_NON_LINUX_SHARE = 0.15;

/** Minutes attributed to each runner OS in an observed month. */
export interface OsMix {
  linux: number;
  windows: number;
  macos: number;
}

/** One month of evidence, as recorded in the ledger. */
export interface Observation {
  /** `YYYY-MM`. */
  month: string;
  /** The figure GitHub's own Included-usage panel showed. */
  displayedValue: number;
  /** True when that figure was pinned at the cap, making it a lower bound rather than a measurement. */
  displayedIsSaturated: boolean;
  /** The included allowance for the period. */
  allowance: number;
  /** What the model under test predicts for the period. */
  predicted: number;
  /** Weighted minutes by runner OS, used to judge discriminating power. */
  mixByOs: OsMix;
}

export type Verdict =
  /** The observation is incompatible with the model. */
  | "refutes"
  /** The observation is compatible with the model AND could have been otherwise. */
  | "supports"
  /**
   * The observation cannot distinguish this model from its rivals. Either it is
   * saturated and the model predicts at or above the cap (so every such model looks
   * identical), or its OS mix is too Linux-dominated for any weighting to matter.
   */
  | "non-discriminating";

export interface Classification {
  verdict: Verdict;
  /** Why, in one sentence, so a ledger row carries its own reasoning. */
  reason: string;
  /** Signed relative difference against the displayed value, or null when it is meaningless. */
  relativeDifference: number | null;
  /** The non-Linux share of predicted drawdown, 0 to 1. */
  nonLinuxShare: number;
}

/** The non-Linux share of an OS mix, 0 when the mix is empty. */
export function nonLinuxShare(mix: OsMix): number {
  const total = mix.linux + mix.windows + mix.macos;
  if (!Number.isFinite(total) || total <= 0) return 0;
  return (mix.windows + mix.macos) / total;
}

/**
 * Classify one month against the model that produced `predicted`.
 *
 * Order of tests is deliberate and is the whole point of the module:
 *
 *   1. A SATURATED month is a lower bound. If the model predicts BELOW the cap it is
 *      refuted outright - it cannot produce the display. If it predicts at or above
 *      the cap it is merely consistent, which is not the same as confirmed, and is
 *      reported as `non-discriminating`.
 *   2. A month with too little non-Linux usage cannot separate weightings at all and
 *      is `non-discriminating` regardless of how well the numbers match. This test
 *      runs before the tolerance comparison precisely so a good match cannot be
 *      mistaken for evidence.
 *   3. Only an UNSATURATED month with real OS mix can `support` or `refute` on the
 *      strength of the numbers themselves.
 */
export function classifyObservation(
  observation: Observation,
  tolerance: number = OBSERVATION_TOLERANCE
): Classification {
  const share = nonLinuxShare(observation.mixByOs);

  if (observation.displayedIsSaturated) {
    if (observation.predicted < observation.allowance) {
      return {
        verdict: "refutes",
        reason: `Saturated at ${observation.allowance}, but the model predicts ${round(observation.predicted)}, which cannot produce a pinned meter.`,
        relativeDifference: null,
        nonLinuxShare: share
      };
    }
    return {
      verdict: "non-discriminating",
      reason: `Saturated at ${observation.allowance}. The model predicts ${round(observation.predicted)}, which is consistent but not confirming - every model predicting at or above the cap displays identically.`,
      relativeDifference: null,
      nonLinuxShare: share
    };
  }

  if (share < DISCRIMINATING_NON_LINUX_SHARE) {
    return {
      verdict: "non-discriminating",
      reason: `Only ${(share * 100).toFixed(1)}% of predicted drawdown is non-Linux, below the ${(DISCRIMINATING_NON_LINUX_SHARE * 100).toFixed(0)}% bar, so every candidate weighting yields the same answer within tolerance.`,
      relativeDifference: null,
      nonLinuxShare: share
    };
  }

  if (observation.displayedValue <= 0) {
    return {
      verdict: "non-discriminating",
      reason: "The displayed value is zero or absent, so there is nothing to compare against.",
      relativeDifference: null,
      nonLinuxShare: share
    };
  }

  const difference = (observation.predicted - observation.displayedValue) / observation.displayedValue;
  const within = Math.abs(difference) <= tolerance;
  return {
    verdict: within ? "supports" : "refutes",
    reason: within
      ? `Unsaturated, ${(share * 100).toFixed(1)}% non-Linux, and the prediction sits within ${(tolerance * 100).toFixed(0)}% of the displayed ${observation.displayedValue}.`
      : `Unsaturated, ${(share * 100).toFixed(1)}% non-Linux, and the prediction is ${(difference * 100).toFixed(1)}% from the displayed ${observation.displayedValue}, outside the ${(tolerance * 100).toFixed(0)}% tolerance.`,
    relativeDifference: difference,
    nonLinuxShare: share
  };
}

/**
 * The standing state of the model across every observation recorded so far.
 *
 * A single `refutes` is decisive: one incompatible month is enough, and no number of
 * supporting months repairs it. Absent a refutation, the model is `supported` only
 * if at least one month actually discriminated; otherwise it is `untested`, which is
 * an honest and common state for an account whose CI is Linux-dominated.
 */
export function summarize(classifications: readonly Classification[]): "refuted" | "supported" | "untested" {
  if (classifications.some((entry) => entry.verdict === "refutes")) return "refuted";
  if (classifications.some((entry) => entry.verdict === "supports")) return "supported";
  return "untested";
}

function round(value: number): number {
  return Math.round(value * 100) / 100;
}
