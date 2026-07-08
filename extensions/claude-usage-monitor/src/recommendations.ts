import {
  UsageData,
  Recommendation,
  UrgencyLevel,
  formatModelName,
  baseModelId,
  is1MContext,
  getThresholdConfig,
  getThresholdMetric,
} from "./types";

// Fable is Opus-class (top tier), so it gets the same switch-down advice.
const isOpus = (m: string): boolean => /opus|fable|default/i.test(m);

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
 * suggestion evaluate, honoring the claudeUsage.thresholdMetric setting.
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
}

/**
 * Build the threshold suggestion shown by both the toast notification and the
 * dashboard Recommendation section, so the two always agree. Advice is
 * model-aware at every level: a switch-down suggestion appears only when the
 * current model has a lower tier to move to (Opus-class → Sonnet, anything
 * but Haiku → Haiku at critical); otherwise only the Effort advice remains.
 * Returns null when usage is below the moderate threshold.
 */
export function buildUsageSuggestion(data: UsageData, trigger: TriggerMetric): UsageSuggestion | null {
  const t = getThresholdConfig();
  if (trigger.percent < t.moderate) {
    return null;
  }

  const pct = Math.round(trigger.percent);
  const opus = isOpus(data.currentModel);
  const haiku = /haiku/i.test(data.currentModel);

  // Long-form weekly resets start with a weekday name ("Tuesday July 7th at ...")
  // and already carry their own parenthetical duration; duration-style values
  // ("2h 48m") read best inside parentheses.
  const resetClause = /^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)/.test(trigger.resetsIn)
    ? `before it resets on ${trigger.resetsIn}`
    : `before it resets (in ${trigger.resetsIn})`;

  if (trigger.percent >= t.critical) {
    return {
      bucket: t.critical,
      message: haiku
        ? `${trigger.label} usage at ${pct}% → Set Effort to Low to avoid hitting your limit ${resetClause}.`
        : `${trigger.label} usage at ${pct}% → Switch to Haiku and set Effort to Low to avoid hitting your limit ${resetClause}.`,
    };
  }
  if (trigger.percent >= t.high) {
    return {
      bucket: t.high,
      message: opus
        ? `${trigger.label} usage at ${pct}% → Switch to Sonnet and reduce Effort to High or Medium to prevent reaching your limit ${resetClause}.`
        : `${trigger.label} usage at ${pct}% → Reduce Effort to High or Medium to prevent reaching your limit ${resetClause}.`,
    };
  }
  return {
    bucket: t.moderate,
    message: opus
      ? `${trigger.label} usage at ${pct}% → Consider switching to Sonnet and reducing Effort to High or Medium to prevent reaching your limit ${resetClause}.`
      : `${trigger.label} usage at ${pct}% → Reduce Effort to High or Medium to extend your remaining usage ${resetClause}.`,
  };
}

export function getRecommendation(data: UsageData): Recommendation {
  const sessionUrgency = classifyUrgency(data.session.percent);
  const weeklyUrgency = classifyUrgency(data.weeklyAllModels.percent);
  const overallUrgency = getOverallUrgency(data);

  const tips = getRelevantTips(data);

  // Session is critical but weekly is fine: just wait
  if (
    sessionUrgency === "critical" &&
    weeklyUrgency !== "critical" &&
    weeklyUrgency !== "high"
  ) {
    return {
      urgency: overallUrgency,
      message: `Session limit near capacity (${data.session.percent}%). It resets in ${data.session.resetsIn}. Wait for the reset before continuing. Your weekly limits are healthy.`,
      suggestedModel: null,
      tips,
    };
  }

  // Session is high/critical while using a 1M context variant: suggest standard context to reduce session consumption
  if (
    (sessionUrgency === "high" || sessionUrgency === "critical") &&
    is1MContext(data.currentModel)
  ) {
    const base = baseModelId(data.currentModel);
    return {
      urgency: overallUrgency,
      message: `Session limit is ${data.session.percent}% (resets in ${data.session.resetsIn}). You are using the 1M context variant, which can consume tokens faster in long conversations. Switch to ${formatModelName(base)} for tasks that do not require large file processing.`,
      suggestedModel: base,
      tips,
    };
  }

  // Critical anywhere: switch to Haiku and drop Effort to Low (matches the toast notification policy).
  if (sessionUrgency === "critical" || weeklyUrgency === "critical") {
    return {
      urgency: overallUrgency,
      message: `Usage is critical (${getHighestMetricSummary(data)}). Switch to Haiku and set Effort to Low to avoid hitting your limit.`,
      suggestedModel: "haiku",
      tips,
    };
  }

  // Weekly all-models is high while using Opus: drop to Sonnet and reduce Effort.
  if (weeklyUrgency === "high" && isOpus(data.currentModel)) {
    return {
      urgency: overallUrgency,
      message: `Weekly usage is ${data.weeklyAllModels.percent}% (resets ${data.weeklyAllModels.resetsIn}). Switch from ${formatModelName(data.currentModel)} to Sonnet and reduce Effort to High or Medium until the weekly reset.`,
      suggestedModel: "sonnet",
      tips,
    };
  }

  // Weekly all-models is high while using Sonnet/Haiku: keep the model, reduce Effort.
  if (weeklyUrgency === "high" && !isOpus(data.currentModel)) {
    return {
      urgency: overallUrgency,
      message: `Weekly usage is ${data.weeklyAllModels.percent}% (resets ${data.weeklyAllModels.resetsIn}). Reduce Effort to High or Medium until the weekly reset.`,
      suggestedModel: null,
      tips,
    };
  }

  // Session is high while using Opus (non-1M, already handled above): drop to Sonnet and reduce Effort.
  if (sessionUrgency === "high" && isOpus(data.currentModel)) {
    return {
      urgency: overallUrgency,
      message: `Session usage is ${data.session.percent}% (resets in ${data.session.resetsIn}). Switch to Sonnet and reduce Effort to High or Medium.`,
      suggestedModel: "sonnet",
      tips,
    };
  }

  // Session is high while using Sonnet/Haiku: keep the model, reduce Effort.
  if (sessionUrgency === "high" && !isOpus(data.currentModel)) {
    return {
      urgency: overallUrgency,
      message: `Session usage is ${data.session.percent}% (resets in ${data.session.resetsIn}). Reduce Effort to High or Medium.`,
      suggestedModel: null,
      tips,
    };
  }

  // Everything is low/moderate
  if (overallUrgency === "low") {
    if (isOpus(data.currentModel)) {
      return {
        urgency: "low",
        message: `All usage levels are healthy. Continue using ${formatModelName(data.currentModel)} freely.`,
        suggestedModel: null,
        tips: [
          "Match model to task: Haiku for lookups, Sonnet for coding, Opus for architecture.",
        ],
      };
    }
    return {
      urgency: "low",
      message: `All usage levels are healthy. Opus (1M context) is the Anthropic default — consider it for most tasks.`,
      suggestedModel: null,
      tips: [
        "Opus (1M context) is the platform default — full capability with standard usage allowance.",
        "Match model to task: Haiku for lookups, Sonnet for coding, Opus for architecture.",
      ],
    };
  }

  // Moderate catch-all: nudge Effort down regardless of model. No model swap yet.
  return {
    urgency: overallUrgency,
    message: `Usage is moderate. Reduce Effort to High or Medium to extend your remaining usage. ${getHighestMetricSummary(data)}`,
    suggestedModel: null,
    tips,
  };
}

function getHighestMetricSummary(data: UsageData): string {
  const metrics = [
    { name: "Session", percent: data.session.percent, resets: data.session.resetsIn },
    { name: "Weekly", percent: data.weeklyAllModels.percent, resets: data.weeklyAllModels.resetsIn },
  ];

  const highest = metrics.reduce((a, b) => (a.percent > b.percent ? a : b));
  return `Highest: ${highest.name} at ${highest.percent}% (resets ${highest.resets}).`;
}

function getRelevantTips(data: UsageData): string[] {
  const tips: string[] = [];
  const overallUrgency = getOverallUrgency(data);

  if (overallUrgency === "low") {
    return ["Match model to task: Haiku for lookups, Sonnet for coding, Opus for architecture."];
  }

  tips.push("Use /compact to reduce context window consumption in long conversations.");

  if (data.session.percent > 75) {
    tips.push("Start new conversations for unrelated tasks instead of extending long threads.");
  }

  if (data.weeklyAllModels.percent > 50) {
    tips.push("Batch related questions into single, well-structured prompts.");
    tips.push("Use plan mode for complex tasks to reduce iteration cycles.");
  }

  if (isOpus(data.currentModel) && data.weeklyAllModels.percent > 50) {
    tips.push("Use Sonnet for standard coding, debugging, and test writing. Reserve Opus for architecture.");
  }

  return tips;
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
