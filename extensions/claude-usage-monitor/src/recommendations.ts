import {
  UsageData,
  Recommendation,
  UrgencyLevel,
  formatModelName,
  baseModelId,
  is1MContext,
  URGENCY_THRESHOLDS,
} from "./types";

const isOpus   = (m: string): boolean => /opus|default/i.test(m);
const isSonnet = (m: string): boolean => /sonnet/i.test(m);

export function classifyUrgency(percent: number): UrgencyLevel {
  if (percent >= URGENCY_THRESHOLDS.critical) {
    return "critical";
  }
  if (percent >= URGENCY_THRESHOLDS.high) {
    return "high";
  }
  if (percent >= URGENCY_THRESHOLDS.moderate) {
    return "moderate";
  }
  return "low";
}

export function getOverallUrgency(data: UsageData): UrgencyLevel {
  const levels: UrgencyLevel[] = [
    classifyUrgency(data.session.percent),
    classifyUrgency(data.weeklyAllModels.percent),
    classifyUrgency(data.weeklySonnet.percent),
  ];

  const priority: UrgencyLevel[] = ["critical", "high", "moderate", "low"];
  for (const level of priority) {
    if (levels.includes(level)) {
      return level;
    }
  }
  return "low";
}

export function getRecommendation(data: UsageData): Recommendation {
  const sessionUrgency = classifyUrgency(data.session.percent);
  const weeklyUrgency = classifyUrgency(data.weeklyAllModels.percent);
  const sonnetUrgency = classifyUrgency(data.weeklySonnet.percent);
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

  // Weekly all-models is high/critical while using Opus
  if ((weeklyUrgency === "critical" || weeklyUrgency === "high") && isOpus(data.currentModel)) {
    return {
      urgency: overallUrgency,
      message: `Weekly usage is ${data.weeklyAllModels.percent}% (resets ${data.weeklyAllModels.resetsIn}). Switch from ${formatModelName(data.currentModel)} to Sonnet 4.6 until the weekly reset. Sonnet handles most coding tasks effectively.`,
      suggestedModel: "claude-sonnet-4-6",
      tips,
    };
  }

  // Weekly all-models is high/critical while using Sonnet
  if ((weeklyUrgency === "critical" || weeklyUrgency === "high") && isSonnet(data.currentModel)) {
    return {
      urgency: overallUrgency,
      message: `Weekly usage is ${data.weeklyAllModels.percent}% (resets ${data.weeklyAllModels.resetsIn}). Switch to Haiku 4.5 for simple tasks. Save Sonnet for complex logic only.`,
      suggestedModel: "claude-haiku-4-5",
      tips,
    };
  }

  // Sonnet-only limit is high while using Sonnet
  if ((sonnetUrgency === "critical" || sonnetUrgency === "high") && isSonnet(data.currentModel)) {
    return {
      urgency: overallUrgency,
      message: `Sonnet-only limit is ${data.weeklySonnet.percent}% (resets ${data.weeklySonnet.resetsIn}). Switch to Opus for complex tasks or Haiku for simple ones. Neither counts against the Sonnet-only limit.`,
      suggestedModel: "claude-opus-4-6",
      tips,
    };
  }

  // Session is high while using Opus (non-1M, already handled above)
  if (sessionUrgency === "high" && isOpus(data.currentModel)) {
    return {
      urgency: overallUrgency,
      message: `Session usage is ${data.session.percent}% (resets in ${data.session.resetsIn}). Consider switching to Sonnet 4.6 for routine tasks. Reserve Opus for architecture and complex reasoning.`,
      suggestedModel: "claude-sonnet-4-6",
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

  // Moderate catch-all
  return {
    urgency: overallUrgency,
    message: `Usage is moderate. Be mindful of task complexity. ${getHighestMetricSummary(data)}`,
    suggestedModel: null,
    tips,
  };
}

function getHighestMetricSummary(data: UsageData): string {
  const metrics = [
    { name: "Session", percent: data.session.percent, resets: data.session.resetsIn },
    { name: "Weekly (all models)", percent: data.weeklyAllModels.percent, resets: data.weeklyAllModels.resetsIn },
    { name: "Weekly (Sonnet)", percent: data.weeklySonnet.percent, resets: data.weeklySonnet.resetsIn },
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
    tips.push("Use Sonnet 4.6 for standard coding, debugging, and test writing. Reserve Opus for architecture.");
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
