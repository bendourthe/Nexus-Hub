import {
  UsageData,
  Recommendation,
  UrgencyLevel,
  ClaudeModel,
  MODEL_DISPLAY_NAMES,
  URGENCY_THRESHOLDS,
} from "./types";

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

  // Weekly all-models is high/critical while using Opus
  if (
    (weeklyUrgency === "critical" || weeklyUrgency === "high") &&
    data.currentModel === "opus-4.6"
  ) {
    return {
      urgency: overallUrgency,
      message: `Weekly usage is ${data.weeklyAllModels.percent}% (resets ${data.weeklyAllModels.resetsIn}). Switch from ${MODEL_DISPLAY_NAMES[data.currentModel]} to Sonnet 4.5 until the weekly reset. Sonnet handles most coding tasks effectively.`,
      suggestedModel: "sonnet-4.5",
      tips,
    };
  }

  // Weekly all-models is high/critical while using Sonnet
  if (
    (weeklyUrgency === "critical" || weeklyUrgency === "high") &&
    data.currentModel === "sonnet-4.5"
  ) {
    return {
      urgency: overallUrgency,
      message: `Weekly usage is ${data.weeklyAllModels.percent}% (resets ${data.weeklyAllModels.resetsIn}). Switch to Haiku 4.5 for simple tasks. Save Sonnet for complex logic only.`,
      suggestedModel: "haiku-4.5",
      tips,
    };
  }

  // Sonnet-only limit is high while using Sonnet
  if (
    (sonnetUrgency === "critical" || sonnetUrgency === "high") &&
    data.currentModel === "sonnet-4.5"
  ) {
    return {
      urgency: overallUrgency,
      message: `Sonnet-only limit is ${data.weeklySonnet.percent}% (resets ${data.weeklySonnet.resetsIn}). Switch to Opus for complex tasks or Haiku for simple ones. Neither counts against the Sonnet-only limit.`,
      suggestedModel: "opus-4.6",
      tips,
    };
  }

  // Session is high while using Opus
  if (sessionUrgency === "high" && data.currentModel === "opus-4.6") {
    return {
      urgency: overallUrgency,
      message: `Session usage is ${data.session.percent}% (resets in ${data.session.resetsIn}). Consider switching to Sonnet 4.5 for routine tasks. Reserve Opus for architecture and complex reasoning.`,
      suggestedModel: "sonnet-4.5",
      tips,
    };
  }

  // Everything is low/moderate
  if (overallUrgency === "low") {
    return {
      urgency: "low",
      message: `All usage levels are healthy. Continue using ${MODEL_DISPLAY_NAMES[data.currentModel]} freely.`,
      suggestedModel: null,
      tips: [
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

  if (data.currentModel === "opus-4.6" && data.weeklyAllModels.percent > 50) {
    tips.push("Use Sonnet 4.5 for standard coding, debugging, and test writing. Reserve Opus for architecture.");
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
