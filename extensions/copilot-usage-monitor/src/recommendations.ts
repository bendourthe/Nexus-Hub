import { formatPercent, formatResetLabel } from "./usageStore";
import { Headline, Recommendation, UrgencyLevel, UsageData, getThresholdConfig, headlineOf } from "./types";

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

export function getRecommendation(data: UsageData | undefined): Recommendation {
  const urgency = getActiveUrgency(data);
  const headline = headlineOf(data);
  if (headline.kind === "credits") {
    return {
      urgency: "low",
      message: "GitHub sets no personal limit for this seat, so there is no percentage to track.",
      tips: ["An organization owner or billing manager can connect the organization to see the shared pool."],
    };
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
