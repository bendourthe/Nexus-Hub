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

/**
 * The dashboard's Recommendation and Tips sections, mirroring the Claude and Codex
 * monitors so all three read the same way.
 *
 * Cursor's advice differs from Claude's in one structural respect worth stating:
 * Claude's pools are time-windowed (a session that refills in hours), so its advice
 * is often "wait it out". Cursor's included pools refill only at the billing-cycle
 * boundary, which can be weeks away, so waiting is rarely actionable. The advice
 * therefore centers on what still costs nothing versus what now draws on the shared
 * pool - and on whether that pool has anything left, which is the fact that actually
 * changes a user's next decision.
 */
export interface CursorRecommendation {
  urgency: UrgencyLevel;
  message: string;
  tips: readonly string[];
  /** The pool a user should prefer right now, when one is clearly cheaper. */
  suggestedPool: string | null;
}

const BASE_TIPS: readonly string[] = [
  "Cursor Models and Other Models draw on separate pools; switching between them moves the cost, it does not remove it.",
  "Tab completion and inline edits are far cheaper than long agent runs.",
  "Narrow the context you attach to a request; a whole-repo context costs more per turn.",
  "Batch related questions into one well-structured prompt instead of many small turns."
];

export function getRecommendation(
  snapshot: {
    cursorModels: { percentUsed: number | null };
    otherModels: { percentUsed: number | null };
    // Tri-state: null means the source did not report whether on-demand is on,
    // which is not the same as reporting that it is off.
    onDemand: { enabled: boolean | null };
    teamContext: { sharedSpendRemaining?: { amount: number } | null };
  },
  thresholds: Thresholds = DEFAULT_THRESHOLDS
): CursorRecommendation {
  const cursorPercent = snapshot.cursorModels.percentUsed;
  const otherPercent = snapshot.otherModels.percentUsed;
  const highest = Math.max(cursorPercent ?? 0, otherPercent ?? 0);
  const urgency = classifyUrgency(highest, thresholds);

  // The pool being exhausted is what decides whether the next request is billable,
  // so it outranks any percentage in the advice.
  const remaining = snapshot.teamContext.sharedSpendRemaining ?? null;
  const poolSpent =
    snapshot.onDemand.enabled === true &&
    remaining !== null &&
    remaining.amount <= 0;

  const cheaperPool =
    cursorPercent !== null && otherPercent !== null && Math.abs(cursorPercent - otherPercent) >= 20
      ? cursorPercent < otherPercent
        ? "Cursor Models"
        : "Other Models"
      : null;

  const tips = [...BASE_TIPS];
  if (poolSpent) {
    tips.unshift(
      "The shared on-demand pool is spent, so further usage beyond your included pools may be billed. Confirm with whoever owns the team budget before continuing."
    );
  }
  if (cheaperPool !== null) {
    tips.unshift(
      `${cheaperPool} has noticeably more included usage left; prefer it for routine work.`
    );
  }

  let message: string;
  if (urgency === "critical" && poolSpent) {
    message =
      "Included usage is nearly gone and the shared on-demand pool is spent. Anything further is likely billable.";
  } else if (urgency === "critical") {
    message =
      "Included usage is nearly gone. Remaining work will draw on the shared on-demand pool.";
  } else if (urgency === "high") {
    message =
      "Included usage is high. Reserve the heavier pool for work that needs it and prefer inline edits for the rest.";
  } else if (urgency === "moderate") {
    message =
      "Included usage is moderate. Nothing to change yet; keep an eye on the pool that is filling faster.";
  } else {
    message = "Included usage is low. No action needed.";
  }

  return { urgency, message, tips, suggestedPool: cheaperPool };
}
