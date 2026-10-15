import {
  UsageData,
  Recommendation,
  UrgencyLevel,
  getThresholdConfig,
  getThresholdMetric,
  isTracked,
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

/** The usage metric a threshold suggestion is evaluated against, with its display labels. */
export interface TriggerMetric {
  percent: number;
  resetsIn: string;
  /** The window: "Current Session" (5-hour) or "Weekly". */
  label: string;
  /** The Antigravity model group the window belongs to, e.g. "Gemini Models". */
  group: string;
}

/** The headline group's name (the Gemini group, carried in `currentModel`). */
function primaryGroup(data: UsageData): string {
  return data.currentModel || "Gemini Models";
}

/**
 * Every tracked window across every model group. The headline (Gemini) pair
 * comes first; extra groups arrive as "<Group>: <Window>" rows from the provider.
 */
export function allMetrics(data: UsageData): TriggerMetric[] {
  const group = primaryGroup(data);
  const out: TriggerMetric[] = [];
  if (isTracked(data.session)) {
    out.push({ percent: data.session.percent, resetsIn: data.session.resetsIn, label: "Current Session", group });
  }
  if (isTracked(data.weeklyAllModels)) {
    out.push({ percent: data.weeklyAllModels.percent, resetsIn: data.weeklyAllModels.resetsIn, label: "Weekly", group });
  }
  for (const row of data.additionalLimits ?? []) {
    const split = row.label.indexOf(": ");
    out.push({
      percent: row.percent,
      resetsIn: row.resetsIn,
      label: split >= 0 ? row.label.slice(split + 2) : row.label,
      group: split >= 0 ? row.label.slice(0, split) : "Other Models",
    });
  }
  return out;
}

function highest(metrics: TriggerMetric[], fallback: TriggerMetric): TriggerMetric {
  return metrics.reduce((a, b) => (a.percent >= b.percent ? a : b), fallback);
}

const NO_DATA: TriggerMetric = { percent: -1, resetsIn: "N/A", label: "Current Session", group: "Gemini Models" };

/** Urgency across every window of every group (used for recommendations). */
export function getOverallUrgency(data: UsageData): UrgencyLevel {
  return classifyUrgency(highest(allMetrics(data), NO_DATA).percent);
}

/**
 * Returns the urgency level for the metric selected by the user in settings.
 * Used for the status bar highlight and threshold notifications.
 */
export function getActiveUrgency(data: UsageData): UrgencyLevel {
  return classifyUrgency(pickTriggerMetric(data).percent);
}

/**
 * Select the usage metric that threshold notifications and the dashboard
 * suggestion evaluate, honoring the geminiUsage.thresholdMetric setting.
 * "highest" spans BOTH Antigravity model groups, so a Claude/GPT limit running
 * out warns too; "session" and "weekly" follow the headline Gemini group.
 * Shared by the toast policy (extension.ts) and the dashboard (dashboardPanel.ts)
 * so both fire from the same metric under the same conditions.
 */
export function pickTriggerMetric(data: UsageData): TriggerMetric {
  const group = primaryGroup(data);
  switch (getThresholdMetric()) {
    case "highest":
      return highest(allMetrics(data), { ...NO_DATA, group });
    case "weekly":
      return { percent: data.weeklyAllModels.percent, resetsIn: data.weeklyAllModels.resetsIn, label: "Weekly", group };
    default:
      return { percent: data.session.percent, resetsIn: data.session.resetsIn, label: "Current Session", group };
  }
}

/**
 * Another model group whose every tracked window is still below the moderate
 * threshold, so switching the agent to it extends the working session. Null
 * when no such group exists.
 */
export function findSwitchGroup(data: UsageData, exhaustedGroup: string): string | null {
  const moderate = getThresholdConfig().moderate;
  const byGroup = new Map<string, number>();
  for (const m of allMetrics(data)) {
    byGroup.set(m.group, Math.max(byGroup.get(m.group) ?? -1, m.percent));
  }
  for (const [group, peak] of byGroup) {
    if (group !== exhaustedGroup && peak < moderate) {
      return group;
    }
  }
  return null;
}

/** A threshold suggestion: the configured threshold bucket that fired and the full message. */
export interface UsageSuggestion {
  bucket: number;
  message: string;
  percent: number;
  label: string;
  resetsIn: string;
  /** Another Antigravity model group with quota left, or null when none has. */
  switchModel: string | null;
  /** The throttle / wait advice keyed to the fired threshold. */
  effortAdvice: string;
}

/**
 * Build the threshold suggestion shown by both the warning view and the
 * dashboard Recommendation section, so the two always agree. Antigravity limits
 * are per model group, so when another group still has headroom the advice is to
 * switch the agent to it; otherwise it is throttle / pause / wait for the reset.
 * Returns null when usage is below the moderate threshold.
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
  const switchModel = findSwitchGroup(data, trigger.group);
  const switchClause = switchModel ? `, or switch the agent to ${switchModel}` : "";
  const head = `${trigger.group} ${trigger.label} usage at ${pct}% ->`;
  const base = { percent: pct, label: trigger.label, resetsIn: trigger.resetsIn, switchModel };

  if (trigger.percent >= t.critical) {
    return {
      ...base,
      bucket: t.critical,
      message: `${head} Pause non-essential work and wait for the reset${switchClause}, ${resetClause}.`,
      effortAdvice: "Pause non-essential work until the reset",
    };
  }
  if (trigger.percent >= t.high) {
    return {
      ...base,
      bucket: t.high,
      message: `${head} Slow down and focus on essential tasks${switchClause} to avoid hitting your limit ${resetClause}.`,
      effortAdvice: "Focus on essential tasks until the reset",
    };
  }
  return {
    ...base,
    bucket: t.moderate,
    message: `${head} Throttle your usage (batch prompts, shorter sessions)${switchClause} to extend your remaining allowance ${resetClause}.`,
    effortAdvice: "Throttle usage: batch prompts, shorter sessions",
  };
}

/** Throttle / wait advice, plus a model-group switch when another group has headroom. */
export function getRecommendation(data: UsageData): Recommendation {
  const top = highest(allMetrics(data), NO_DATA);
  const overall = classifyUrgency(top.percent);
  const tips = getRelevantTips(data, top);
  const switchModel = overall === "low" ? null : findSwitchGroup(data, top.group);
  const switchSentence = switchModel ? ` Switch the agent to ${switchModel}, which still has quota.` : "";

  if (overall === "critical") {
    return {
      urgency: overall,
      message: `Antigravity usage is critical (${summarize(top)}). Pause non-essential work and wait for the reset.${switchSentence}`,
      suggestedModel: switchModel,
      tips,
    };
  }
  if (overall === "high") {
    return {
      urgency: overall,
      message: `Antigravity usage is high (${summarize(top)}). Slow down and focus on essential tasks until the reset.${switchSentence}`,
      suggestedModel: switchModel,
      tips,
    };
  }
  if (overall === "moderate") {
    return {
      urgency: overall,
      message: `Antigravity usage is moderate. Throttle your usage (batch prompts, shorter sessions) to extend your allowance. ${summarize(top)}.${switchSentence}`,
      suggestedModel: switchModel,
      tips,
    };
  }
  return {
    urgency: "low",
    message: "All Antigravity usage levels are healthy. Keep working normally.",
    suggestedModel: null,
    tips: [
      "Batch related requests into fewer, well-structured prompts to conserve your allowance.",
      "Prefer shorter, focused sessions to spread usage across the 5-hour window.",
    ],
  };
}

function getRelevantTips(data: UsageData, top: TriggerMetric): string[] {
  if (classifyUrgency(top.percent) === "low") {
    return ["Batch related requests into fewer prompts to conserve your Antigravity allowance."];
  }
  const metrics = allMetrics(data);
  const tips: string[] = ["Batch related questions into single, well-structured prompts."];
  if (metrics.some((m) => m.label === "Current Session" && m.percent > 75)) {
    tips.push("Take a short break and resume after the 5-hour window resets.");
  }
  if (metrics.some((m) => m.label === "Weekly" && m.percent > 50)) {
    tips.push("Spread heavier work across days to stay under the weekly limit.");
  }
  tips.push("Each model group has its own limits: when one runs low, pick a model from another group in the agent panel.");
  return tips;
}

function summarize(m: TriggerMetric): string {
  return `Highest: ${m.group} ${m.label} at ${m.percent}% (resets ${m.resetsIn})`;
}
