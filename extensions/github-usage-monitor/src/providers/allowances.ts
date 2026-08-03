import type {
  AllowanceSource,
  MetricKind,
  UsageMetric,
  UsageSnapshot,
  UsageUnit
} from "../types";

export interface AllowanceValue {
  value: number;
  unit: UsageUnit;
}

export type AllowanceMap = Partial<Record<MetricKind, AllowanceValue>>;

export interface AllowanceInputs {
  api?: AllowanceMap;
  manual?: AllowanceMap;
}

export function applyAllowances(snapshot: UsageSnapshot, inputs: AllowanceInputs): UsageSnapshot {
  return {
    ...snapshot,
    copilot: applyMetricAllowance(snapshot.copilot, inputs),
    actionsMinutes: applyMetricAllowance(snapshot.actionsMinutes, inputs),
    actionsStorage: applyMetricAllowance(snapshot.actionsStorage, inputs)
  };
}

export function applyMetricAllowance(metric: UsageMetric, inputs: AllowanceInputs): UsageMetric {
  const api = validMatchingAllowance(metric, inputs.api?.[metric.kind]);
  const manual = validMatchingAllowance(metric, inputs.manual?.[metric.kind]);
  const allowance = api ?? manual;
  const allowanceSource: AllowanceSource = api !== null ? "api" : manual !== null ? "manual" : "unknown";
  return {
    ...metric,
    allowance,
    allowanceSource,
    percentage: allowance === null ? null : (metric.used / allowance) * 100
  };
}

function validMatchingAllowance(metric: UsageMetric, candidate: AllowanceValue | undefined): number | null {
  if (
    candidate === undefined ||
    candidate.unit.toLowerCase() !== metric.unit.toLowerCase() ||
    !Number.isFinite(candidate.value) ||
    candidate.value <= 0
  ) {
    return null;
  }
  return candidate.value;
}
