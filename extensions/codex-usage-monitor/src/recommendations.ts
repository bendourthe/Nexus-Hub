import {
  UsageData,
  Recommendation,
  UrgencyLevel,
  getThresholdConfig,
  getThresholdMetric,
} from "./types";

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

export function getOverallUrgency(data: UsageData): UrgencyLevel {
  const levels: UrgencyLevel[] = [
    classifyUrgency(data.session.percent),
    classifyUrgency(data.weeklyAllModels.percent),
  ];

  const priority: UrgencyLevel[] = ["critical", "high", "moderate", "low"];
  for (const level of priority) {
    if (levels.includes(level)) {
      return level;
    }
  }
  return "low";
}

/**
 * Returns the urgency level for the metric selected by the user in settings.
 * Used for the status bar highlight and threshold notifications.
 * `getOverallUrgency` (max of all metrics) is still used internally for recommendations.
 */
export function getActiveUrgency(data: UsageData): UrgencyLevel {
  const metric = getThresholdMetric();
  let percent: number;
  switch (metric) {
    case "highest": percent = Math.max(data.session.percent, data.weeklyAllModels.percent); break;
    case "weekly":  percent = data.weeklyAllModels.percent; break;
    default:        percent = data.session.percent; break;
  }
  return classifyUrgency(percent);
}

/** The usage metric a threshold suggestion is evaluated against, with its display label. */
export interface TriggerMetric {
  percent: number;
  resetsIn: string;
  label: string;
}

/**
 * Select the usage metric that threshold notifications and the dashboard
 * suggestion evaluate, honoring the codexUsage.thresholdMetric setting.
 * Shared by the toast policy (extension.ts) and the dashboard (dashboardPanel.ts)
 * so both fire from the same metric under the same conditions.
 */
export function pickTriggerMetric(data: UsageData): TriggerMetric {
  const metric = getThresholdMetric();
  switch (metric) {
    case "highest": {
      const candidates: TriggerMetric[] = [
        { percent: data.session.percent,         resetsIn: data.session.resetsIn,         label: "Current Session" },
        { percent: data.weeklyAllModels.percent, resetsIn: data.weeklyAllModels.resetsIn, label: "Weekly" },
      ];
      return candidates.reduce((a, b) => (a.percent >= b.percent ? a : b));
    }
    case "weekly":
      return { percent: data.weeklyAllModels.percent, resetsIn: data.weeklyAllModels.resetsIn, label: "Weekly" };
    default:
      return { percent: data.session.percent, resetsIn: data.session.resetsIn, label: "Current Session" };
  }
}

/** A threshold suggestion: the configured threshold bucket that fired and the full message. */
export interface UsageSuggestion {
  bucket: number;
  message: string;
  percent: number;
  label: string;
  resetsIn: string;
  /** Codex has no lower model tier to switch to, so this is always null. */
  switchModel: string | null;
  /** The throttle / wait / rotate advice keyed to the fired threshold. */
  effortAdvice: string;
}

/**
 * Build the Codex threshold suggestion shown by both the toast notification and
 * the dashboard Recommendation section, so the two always agree. Codex has no
 * cheaper model tier, so `switchModel` is always null and the advice is
 * throttle / pause / wait-for-reset / rotate-account keyed to the same
 * thresholds. Returns null when usage is below the moderate threshold.
 */
export function buildUsageSuggestion(data: UsageData, trigger: TriggerMetric): UsageSuggestion | null {
  const t = getThresholdConfig();
  if (trigger.percent < t.moderate) {
    return null;
  }

  const pct = Math.round(trigger.percent);
  const resetClause = /^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)/.test(trigger.resetsIn)
    ? `before it resets on ${trigger.resetsIn}`
    : `before it resets (in ${trigger.resetsIn})`;

  if (trigger.percent >= t.critical) {
    return {
      bucket: t.critical,
      message: `${trigger.label} Codex usage at ${pct}% -> Pause non-essential work and wait for the reset, or switch to another Codex account, ${resetClause}.`,
      percent: pct,
      label: trigger.label,
      resetsIn: trigger.resetsIn,
      switchModel: null,
      effortAdvice: "Wait for the reset, or rotate to another Codex account",
    };
  }
  if (trigger.percent >= t.high) {
    return {
      bucket: t.high,
      message: `${trigger.label} Codex usage at ${pct}% -> Slow down and focus on essential tasks to avoid hitting your limit ${resetClause}.`,
      percent: pct,
      label: trigger.label,
      resetsIn: trigger.resetsIn,
      switchModel: null,
      effortAdvice: "Pause non-essential Codex tasks until the reset",
    };
  }
  return {
    bucket: t.moderate,
    message: `${trigger.label} Codex usage at ${pct}% -> Throttle your usage (batch prompts, shorter sessions) to extend your remaining allowance ${resetClause}.`,
    percent: pct,
    label: trigger.label,
    resetsIn: trigger.resetsIn,
    switchModel: null,
    effortAdvice: "Throttle usage: batch prompts, shorter sessions",
  };
}

/** Throttle / wait / rotate advice, no model swap (Codex has no cheaper tier). */
export function getRecommendation(data: UsageData): Recommendation {
  const overall = getOverallUrgency(data);
  const tips = getRelevantTips(data);

  if (overall === "critical") {
    return {
      urgency: overall,
      message: `Codex usage is critical (${getHighestMetricSummary(data)}). Pause non-essential work and wait for the reset, or switch to another Codex account.`,
      suggestedModel: null,
      tips,
    };
  }
  if (overall === "high") {
    return {
      urgency: overall,
      message: `Codex usage is high (${getHighestMetricSummary(data)}). Slow down and focus on essential tasks until the reset.`,
      suggestedModel: null,
      tips,
    };
  }
  if (overall === "moderate") {
    return {
      urgency: overall,
      message: `Codex usage is moderate. Throttle your usage (batch prompts, shorter sessions) to extend your allowance. ${getHighestMetricSummary(data)}`,
      suggestedModel: null,
      tips,
    };
  }
  return {
    urgency: "low",
    message: "All Codex usage levels are healthy. Keep working normally.",
    suggestedModel: null,
    tips: [
      "Batch related requests into fewer, well-structured prompts to conserve your allowance.",
      "Prefer shorter, focused sessions to spread usage across the reset window.",
    ],
  };
}

function getRelevantTips(data: UsageData): string[] {
  const overall = getOverallUrgency(data);
  if (overall === "low") {
    return ["Batch related requests into fewer prompts to conserve your Codex allowance."];
  }

  const tips: string[] = ["Batch related questions into single, well-structured prompts."];
  if (data.session.percent > 75) {
    tips.push("Take a short break and resume after the session window resets.");
  }
  if (data.weeklyAllModels.percent > 50) {
    tips.push("Spread heavier work across days to stay under the weekly limit.");
  }
  tips.push("If you have a second Codex account, switch to it while this one resets.");
  return tips;
}

function getHighestMetricSummary(data: UsageData): string {
  const metrics = [
    { name: "Session", percent: data.session.percent, resets: data.session.resetsIn },
    { name: "Weekly", percent: data.weeklyAllModels.percent, resets: data.weeklyAllModels.resetsIn },
  ];

  const highest = metrics.reduce((a, b) => (a.percent > b.percent ? a : b));
  return `Highest: ${highest.name} at ${highest.percent}% (resets ${highest.resets}).`;
}

export function getUrgencyColor(urgency: UrgencyLevel): string {
  switch (urgency) {
    case "low":
      return "statusBarItem.prominentBackground";
    case "moderate":
      return "statusBarItem.warningBackground";
    case "high":
      return "statusBarItem.errorBackground";
    case "critical":
      return "statusBarItem.errorBackground";
  }
}

export function getUrgencyEmoji(urgency: UrgencyLevel): string {
  switch (urgency) {
    case "low":
      return "$(check)";
    case "moderate":
      return "$(warning)";
    case "high":
      return "$(flame)";
    case "critical":
      return "$(error)";
  }
}
