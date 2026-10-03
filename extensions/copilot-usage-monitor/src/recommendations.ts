import { formatPercent, formatResetLabel } from "./usageStore";
import { Headline, PersonalUsage, Recommendation, UrgencyLevel, UsageData, getThresholdConfig, headlineOf, isOrganizationSeat } from "./types";

export function classifyUrgency(percent: number): UrgencyLevel {
  const t = getThresholdConfig();
  if (percent >= t.critical) {
    return "critical";
  }
  if (percent >= t.high) {
    return "high";
  }
  if (percent >= t.moderate) {
    return "moderate";
  }
  return "low";
}

/** Urgency of the status-bar figure. A view with no percentage is always low. */
export function getActiveUrgency(data: UsageData | undefined): UrgencyLevel {
  const headline = headlineOf(data);
  return headline.kind === "percent" ? classifyUrgency(headline.percent) : "low";
}

/** The percentage the thresholds evaluate (the status-bar figure), or -1 when there is none. */
export function triggerPercent(data: UsageData | undefined): number {
  const headline = headlineOf(data);
  return headline.kind === "percent" ? headline.percent : -1;
}

/** A threshold suggestion shared by the warning view and the dashboard. */
export interface UsageSuggestion {
  bucket: number;
  message: string;
  percent: number;
  label: string;
  resetLabel: string;
  advice: string;
}

function percentHeadline(headline: Headline): Extract<Headline, { kind: "percent" }> | null {
  return headline.kind === "percent" ? headline : null;
}

/** Build the suggestion for the status-bar figure, or null below the moderate threshold. */
export function buildUsageSuggestion(data: UsageData | undefined): UsageSuggestion | null {
  const headline = percentHeadline(headlineOf(data));
  const t = getThresholdConfig();
  if (!headline || headline.percent < t.moderate) {
    return null;
  }
  const pct = formatPercent(headline.percent);
  const resetLabel = formatResetLabel(headline.resetsAt);
  const resetClause = headline.resetsAt != null ? ` ${resetLabel.replace(/^Resets/, "It resets")}.` : "";
  const pool = headline.source === "organization";
  const base = { percent: headline.percent, label: headline.label, resetLabel };

  if (headline.percent >= t.critical) {
    const advice = pool
      ? "Pause non-essential Copilot work, or ask an owner about additional usage"
      : "Pause non-essential Copilot work until the reset";
    return { ...base, bucket: t.critical, advice, message: `${headline.label} at ${pct}%. ${advice}.${resetClause}` };
  }
  if (headline.percent >= t.high) {
    const advice = "Keep to essential tasks until the reset";
    return { ...base, bucket: t.high, advice, message: `${headline.label} at ${pct}%. ${advice}.${resetClause}` };
  }
  const advice = "Batch related requests into fewer prompts to stretch the allowance";
  return { ...base, bucket: t.moderate, advice, message: `${headline.label} at ${pct}%. ${advice}.${resetClause}` };
}

/**
 * Why a seat with no personal limit shows `--% (month)`, and the one-time step
 * that fixes it. Never a credit count (v4.13.8 Phase 6).
 */
export const NOT_CONNECTED_HINT =
  "Your organization shares one Copilot pool, so this seat has no percentage of its own. " +
  "An organization owner can show the pool's percentage by running Connect Organization once.";

/** Why a personal plan with no served quota shows `--% (month)`. */
export const NO_PERSONAL_QUOTA_HINT = "GitHub serves no usage limit for this plan, so there is no percentage to show.";

/** The right explanation for a seat with no percentage: Connect for an organization seat only. */
export function noPercentHint(personal: PersonalUsage | undefined): string {
  return personal && !isOrganizationSeat(personal) ? NO_PERSONAL_QUOTA_HINT : NOT_CONNECTED_HINT;
}

export function getRecommendation(data: UsageData | undefined): Recommendation {
  const urgency = getActiveUrgency(data);
  const headline = headlineOf(data);
  if (headline.kind === "no-percent") {
    return headline.reason === "no-pool-total"
      ? {
          urgency: "low",
          message: "GitHub reported no Copilot seats for this organization, so there is no pool percentage.",
          tips: [],
        }
      : headline.reason === "no-personal-quota"
        ? { urgency: "low", message: NO_PERSONAL_QUOTA_HINT, tips: [] }
        : { urgency: "low", message: NOT_CONNECTED_HINT, tips: ["Connect Organization needs an organization owner."] };
  }
  if (headline.kind === "none") {
    return { urgency: "low", message: "No Copilot usage figure yet. Refresh to fetch one.", tips: [] };
  }
  const suggestion = buildUsageSuggestion(data);
  if (suggestion) {
    return {
      urgency,
      message: suggestion.message,
      tips: [
        "Batch related questions into single, well-structured prompts.",
        "Save longer agent sessions for after the reset.",
      ],
    };
  }
  return {
    urgency: "low",
    message: "Copilot usage is healthy. Keep working normally.",
    tips: ["Batch related requests into fewer prompts to conserve your allowance."],
  };
}
