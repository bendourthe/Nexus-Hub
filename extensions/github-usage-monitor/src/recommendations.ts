import type { MetricKind, UsageMetric, UsageSnapshot } from "./types";

export type UrgencyLevel = "low" | "moderate" | "high" | "critical";
export type AlertMetric = "highest" | MetricKind;

export interface Thresholds {
  moderate: number;
  high: number;
  critical: number;
}

export interface TriggerMetric {
  kind: MetricKind;
  label: string;
  metric: UsageMetric;
  percent: number;
}

export interface UsageSuggestion extends TriggerMetric {
  bucket: number;
  urgency: Exclude<UrgencyLevel, "low">;
  message: string;
  recommendation: string;
}

export const DEFAULT_THRESHOLDS: Thresholds = { moderate: 50, high: 75, critical: 95 };

const LABELS: Record<MetricKind, string> = {
  "copilot-ai-credits": "Copilot AI credits",
  "copilot-premium-requests": "Copilot premium requests",
  "actions-minutes": "Actions minutes",
  "actions-storage": "Actions storage"
};

export function classifyUrgency(percent: number, thresholds = DEFAULT_THRESHOLDS): UrgencyLevel {
  if (percent >= thresholds.critical) return "critical";
  if (percent >= thresholds.high) return "high";
  if (percent >= thresholds.moderate) return "moderate";
  return "low";
}

export function pickTriggerMetric(snapshot: UsageSnapshot, selected: AlertMetric): TriggerMetric | null {
  const metrics = [snapshot.copilot, snapshot.actionsMinutes, snapshot.actionsStorage]
    .filter((metric): metric is UsageMetric & { percentage: number } => metric.percentage !== null && Number.isFinite(metric.percentage))
    .map((metric) => ({ kind: metric.kind, label: LABELS[metric.kind], metric, percent: metric.percentage }));
  if (metrics.length === 0) return null;
  if (selected === "highest") return metrics.reduce((left, right) => left.percent >= right.percent ? left : right);
  return metrics.find((candidate) => candidate.kind === selected) ?? null;
}

export function buildUsageSuggestion(
  snapshot: UsageSnapshot,
  selected: AlertMetric,
  thresholds = DEFAULT_THRESHOLDS
): UsageSuggestion | null {
  const trigger = pickTriggerMetric(snapshot, selected);
  if (trigger === null) return null;
  const urgency = classifyUrgency(trigger.percent, thresholds);
  if (urgency === "low") return null;
  const bucket = thresholds[urgency];
  const rounded = Math.round(trigger.percent);
  const recommendation = urgency === "critical"
    ? "Pause non-essential runs and review the billing owner before the next reset."
    : urgency === "high"
      ? "Prioritize essential work and review the highest-cost SKUs."
      : "Batch related work and watch this metric through the reset boundary.";
  return {
    ...trigger,
    bucket,
    urgency,
    message: `${trigger.label} reached ${rounded}% of its verified allowance. ${recommendation}`,
    recommendation
  };
}

export function crossedUnnotifiedThreshold(
  suggestion: UsageSuggestion | null,
  notifiedThresholds: readonly number[]
): boolean {
  return suggestion !== null && !notifiedThresholds.includes(suggestion.bucket);
}
