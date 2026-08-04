import type {
  FreshUsageSnapshot,
  IncludedUsageMeter,
  UsageState
} from "./types";

export type UrgencyLevel = "low" | "moderate" | "high" | "critical";
export type AlertMetric = "highest" | "cursorModels" | "otherModels";
export type MeterKey = Exclude<AlertMetric, "highest">;

export interface Thresholds {
  moderate: number;
  high: number;
  critical: number;
}

export interface TriggerMetric {
  key: MeterKey;
  label: string;
  meter: IncludedUsageMeter & { percentUsed: number };
  percent: number;
}

export interface UsageSuggestion extends TriggerMetric {
  bucket: number;
  severity: Exclude<UrgencyLevel, "low">;
  message: string;
  recommendation: string;
  notificationKey: string;
}

export type NotifiedSeverity = UsageSuggestion["severity"];

export const DEFAULT_THRESHOLDS: Thresholds = {
  moderate: 50,
  high: 75,
  critical: 95
};

const LABELS: Record<MeterKey, string> = {
  cursorModels: "Cursor Models",
  otherModels: "Other Models"
};

export function classifyUrgency(
  percent: number,
  thresholds = DEFAULT_THRESHOLDS
): UrgencyLevel {
  if (percent >= thresholds.critical) {
    return "critical";
  }
  if (percent >= thresholds.high) {
    return "high";
  }
  if (percent >= thresholds.moderate) {
    return "moderate";
  }
  return "low";
}

export function pickTriggerMetric(
  state: UsageState,
  selected: AlertMetric
): TriggerMetric | null {
  if (state.state !== "fresh") {
    return null;
  }

  const candidates = triggerCandidates(state.data);
  if (selected === "highest") {
    return candidates.length === 0
      ? null
      : candidates.reduce((left, right) =>
          left.percent >= right.percent ? left : right
        );
  }
  return candidates.find((candidate) => candidate.key === selected) ?? null;
}

export function buildUsageSuggestion(
  state: UsageState,
  selected: AlertMetric,
  thresholds = DEFAULT_THRESHOLDS
): UsageSuggestion | null {
  const trigger = pickTriggerMetric(state, selected);
  if (trigger === null || state.state !== "fresh") {
    return null;
  }

  const severity = classifyUrgency(trigger.percent, thresholds);
  if (severity === "low") {
    return null;
  }

  const bucket = thresholds[severity];
  const cycleKey = notificationCycleKey(state.data);
  const policyKey = [
    selected,
    thresholds.moderate,
    thresholds.high,
    thresholds.critical
  ].join(":");

  return {
    ...trigger,
    bucket,
    severity,
    message: `${trigger.label} reached ${Math.round(trigger.percent)}% of included usage.`,
    recommendation: recommendationFor(severity),
    notificationKey: `${cycleKey}:${policyKey}:${trigger.key}`
  };
}

export function crossedUnnotifiedThreshold(
  suggestion: UsageSuggestion | null,
  highestNotified: ReadonlyMap<string, NotifiedSeverity>
): boolean {
  if (suggestion === null) {
    return false;
  }
  const previous = highestNotified.get(suggestion.notificationKey);
  return previous === undefined || severityRank(suggestion.severity) > severityRank(previous);
}

function triggerCandidates(snapshot: FreshUsageSnapshot): TriggerMetric[] {
  return (
    [
      ["cursorModels", snapshot.cursorModels],
      ["otherModels", snapshot.otherModels]
    ] as const
  )
    .filter(
      (
        candidate
      ): candidate is readonly [
        MeterKey,
        IncludedUsageMeter & { percentUsed: number }
      ] =>
        candidate[1].percentUsed !== null &&
        Number.isFinite(candidate[1].percentUsed)
    )
    .map(([key, meter]) => ({
      key,
      label: LABELS[key],
      meter,
      percent: meter.percentUsed
    }));
}

function notificationCycleKey(snapshot: FreshUsageSnapshot): string {
  if (snapshot.period.resetsAt !== null) {
    return `reset:${snapshot.period.resetsAt}`;
  }
  if (snapshot.period.startsAt !== null) {
    return `start:${snapshot.period.startsAt}`;
  }

  const fetchedAt = new Date(snapshot.fetchedAt);
  if (!Number.isFinite(fetchedAt.getTime())) {
    return `fetched:${snapshot.fetchedAt}`;
  }
  return `calendar:${fetchedAt.getUTCFullYear()}-${String(
    fetchedAt.getUTCMonth() + 1
  ).padStart(2, "0")}`;
}

function recommendationFor(
  severity: Exclude<UrgencyLevel, "low">
): string {
  switch (severity) {
    case "critical":
      return "Pause non-essential runs until the included-usage period resets.";
    case "high":
      return "Prioritize essential work and watch this pool through the reset.";
    case "moderate":
      return "Batch related work and monitor this pool before starting long runs.";
  }
}

function severityRank(severity: NotifiedSeverity): number {
  switch (severity) {
    case "moderate":
      return 1;
    case "high":
      return 2;
    case "critical":
      return 3;
  }
}
