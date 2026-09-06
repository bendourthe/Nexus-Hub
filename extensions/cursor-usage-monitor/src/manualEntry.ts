import type {
  FreshUsageSnapshot,
  IncludedUsageMeter,
  Money,
  Quantity,
  UsageUnit
} from "./types";

export interface ManualMeterInput {
  used: number | null;
  limit: number | null;
  unit: UsageUnit;
}

export interface ManualSnapshotInput {
  cursorModels: ManualMeterInput;
  otherModels: ManualMeterInput;
  onDemandEnabled: boolean | null;
  personalSpend: Money | null;
  periodStartsAt: string | null;
  resetsAt: string | null;
}

export type ManualSnapshotResult =
  | { ok: true; value: FreshUsageSnapshot }
  | { ok: false; errors: string[] };

export function manualEntryTemplate(): ManualSnapshotInput {
  return {
    cursorModels: { used: null, limit: null, unit: "requests" },
    otherModels: { used: null, limit: null, unit: "requests" },
    onDemandEnabled: null,
    personalSpend: null,
    periodStartsAt: null,
    resetsAt: null
  };
}

export function parseManualSnapshotInput(
  value: unknown
): ManualSnapshotInput | undefined {
  if (!isRecord(value)) {
    return undefined;
  }

  const cursorModels = parseManualMeter(value.cursorModels);
  const otherModels = parseManualMeter(value.otherModels);
  const onDemandEnabled = parseOptionalBoolean(value.onDemandEnabled);
  const personalSpend = parseMoney(value.personalSpend);
  const periodStartsAt = parseOptionalString(value.periodStartsAt);
  const resetsAt = parseOptionalString(value.resetsAt);
  if (
    cursorModels === undefined ||
    otherModels === undefined ||
    onDemandEnabled === undefined ||
    personalSpend === undefined ||
    periodStartsAt === undefined ||
    resetsAt === undefined
  ) {
    return undefined;
  }

  return {
    cursorModels,
    otherModels,
    onDemandEnabled,
    personalSpend,
    periodStartsAt,
    resetsAt
  };
}

export function buildManualSnapshot(
  input: ManualSnapshotInput,
  now = Date.now()
): ManualSnapshotResult {
  const errors = validateManualSnapshot(input);
  if (errors.length > 0) {
    return { ok: false, errors };
  }

  return {
    ok: true,
    value: {
      source: "manual",
      period: {
        startsAt: normalizeDate(input.periodStartsAt),
        resetsAt: normalizeDate(input.resetsAt)
      },
      cursorModels: buildMeter(input.cursorModels),
      otherModels: buildMeter(input.otherModels),
      onDemand: buildOnDemand(input),
      teamContext: {
        // A hand-entered snapshot carries no team-pool figures: the user is typing
        // their own numbers, not the team's, so these stay null rather than being
        // inferred from personal spend.
        sharedSpendLimit: null,
        dynamicSpendLimit: null,
        sharedSpendUsed: null,
        sharedSpendRemaining: null
      },
      fetchedAt: new Date(now).toISOString(),
      stale: false,
      staleReason: null
    }
  };
}

export function validateManualSnapshot(input: ManualSnapshotInput): string[] {
  const errors = [
    ...validateMeter("Cursor Models", input.cursorModels),
    ...validateMeter("Other Models", input.otherModels)
  ];

  if (isWhollyEmpty(input)) {
    errors.push("Enter at least one usage, on-demand, or period value.");
  }

  if (
    input.personalSpend !== null &&
    (input.onDemandEnabled !== true ||
      !Number.isFinite(input.personalSpend.amount) ||
      input.personalSpend.amount < 0 ||
      !/^[A-Z]{3}$/u.test(input.personalSpend.currency))
  ) {
    errors.push(
      "Personal on-demand spend requires enabled on-demand usage, a non-negative amount, and a three-letter uppercase currency."
    );
  }

  const startsAt = parseOptionalDate(input.periodStartsAt);
  const resetsAt = parseOptionalDate(input.resetsAt);
  if (startsAt === undefined) {
    errors.push("Period start must be a valid date or empty.");
  }
  if (resetsAt === undefined) {
    errors.push("Reset time must be a valid date or empty.");
  }
  if (
    startsAt !== null &&
    startsAt !== undefined &&
    resetsAt !== null &&
    resetsAt !== undefined &&
    resetsAt <= startsAt
  ) {
    errors.push("Reset time must be after the period start.");
  }

  return errors;
}

function isWhollyEmpty(input: ManualSnapshotInput): boolean {
  return (
    input.cursorModels.used === null &&
    input.cursorModels.limit === null &&
    input.otherModels.used === null &&
    input.otherModels.limit === null &&
    input.onDemandEnabled === null &&
    input.personalSpend === null &&
    (input.periodStartsAt === null || input.periodStartsAt.trim() === "") &&
    (input.resetsAt === null || input.resetsAt.trim() === "")
  );
}

function validateMeter(label: string, meter: ManualMeterInput): string[] {
  const errors: string[] = [];
  if (meter.used !== null && (!Number.isFinite(meter.used) || meter.used < 0)) {
    errors.push(`${label} used amount must be a non-negative number or empty.`);
  }
  if (
    meter.limit !== null &&
    (!Number.isFinite(meter.limit) || meter.limit <= 0)
  ) {
    errors.push(`${label} limit must be greater than zero or empty.`);
  }
  if (meter.limit !== null && meter.used === null) {
    errors.push(`${label} cannot have a limit without a used amount.`);
  }
  return errors;
}

function buildMeter(input: ManualMeterInput): IncludedUsageMeter {
  const used = quantity(input.used, input.unit);
  const limit = quantity(input.limit, input.unit);
  const percentUsed =
    input.used !== null && input.limit !== null
      ? (input.used / input.limit) * 100
      : null;
  return {
    used,
    limit,
    percentUsed,
    percentOrigin: percentUsed === null ? null : "calculated"
  };
}

function buildOnDemand(
  input: ManualSnapshotInput
): FreshUsageSnapshot["onDemand"] {
  if (input.onDemandEnabled === true) {
    return { enabled: true, personalSpend: input.personalSpend };
  }
  if (input.onDemandEnabled === false) {
    return { enabled: false, personalSpend: null };
  }
  return { enabled: null, personalSpend: null };
}

function quantity(value: number | null, unit: UsageUnit): Quantity | null {
  return value === null ? null : { value, unit };
}

function parseOptionalDate(value: string | null): number | null | undefined {
  if (value === null || value.trim() === "") {
    return null;
  }
  const parsed = Date.parse(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function normalizeDate(value: string | null): string | null {
  const parsed = parseOptionalDate(value);
  return parsed === null || parsed === undefined
    ? null
    : new Date(parsed).toISOString();
}

function parseManualMeter(
  value: unknown
): ManualSnapshotInput["cursorModels"] | undefined {
  if (!isRecord(value)) {
    return undefined;
  }
  const used = parseOptionalNumber(value.used);
  const limit = parseOptionalNumber(value.limit);
  const unit = value.unit;
  if (
    used === undefined ||
    limit === undefined ||
    (unit !== "tokens" && unit !== "requests" && unit !== "percent")
  ) {
    return undefined;
  }
  return { used, limit, unit };
}

function parseMoney(
  value: unknown
): ManualSnapshotInput["personalSpend"] | undefined {
  if (value === null) {
    return null;
  }
  if (
    !isRecord(value) ||
    typeof value.amount !== "number" ||
    typeof value.currency !== "string"
  ) {
    return undefined;
  }
  return { amount: value.amount, currency: value.currency };
}

function parseOptionalNumber(value: unknown): number | null | undefined {
  return value === null || typeof value === "number" ? value : undefined;
}

function parseOptionalBoolean(value: unknown): boolean | null | undefined {
  return value === null || typeof value === "boolean" ? value : undefined;
}

function parseOptionalString(value: unknown): string | null | undefined {
  return value === null || typeof value === "string" ? value : undefined;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
