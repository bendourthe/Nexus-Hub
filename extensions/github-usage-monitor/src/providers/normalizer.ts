import type {
  BillingOwner,
  CopilotMetricKind,
  MoneyBreakdown,
  ProviderError,
  SkuUsageBreakdown,
  UsageMetric,
  UsageSnapshot,
  UsageUnit
} from "../types";
import type { CopilotEndpoint } from "./scope";
import { managedCopilotScopeError } from "./scope";

type NormalizationResult =
  | { ok: true; value: UsageSnapshot }
  | { ok: false; error: ProviderError };

interface NormalizationContext {
  owner: BillingOwner;
  copilotEndpoint: CopilotEndpoint;
  requestedAt: number;
  year: number;
  month: number;
}

interface ParsedItem extends SkuUsageBreakdown {
  model?: string;
}

export function normalizeUsageResponses(
  copilotPayload: unknown,
  actionsPayload: unknown,
  context: NormalizationContext
): NormalizationResult {
  const copilotEnvelope = asRecord(copilotPayload);
  const actionsEnvelope = asRecord(actionsPayload);
  if (copilotEnvelope === null || actionsEnvelope === null) {
    return schemaFailure("GitHub billing responses must be JSON objects.");
  }

  if (context.owner.scope === "user" && typeof copilotEnvelope.organization === "string") {
    return { ok: false, error: managedCopilotScopeError() };
  }

  const copilotItems = parseItems(copilotEnvelope.usageItems, "Copilot");
  if (!copilotItems.ok) {
    return copilotItems;
  }
  const actionsItems = parseItems(actionsEnvelope.usageItems, "Actions");
  if (!actionsItems.ok) {
    return actionsItems;
  }

  const period = resolvePeriod(copilotEnvelope.timePeriod, actionsEnvelope.timePeriod, context);
  const reset = {
    at: period.end,
    kind: "reporting-period" as const,
    label: "Current UTC billing month"
  };

  const copilot = normalizeCopilot(copilotItems.value, context.copilotEndpoint, reset);
  if (!copilot.ok) {
    return copilot;
  }

  const actionMetrics = normalizeActions(actionsItems.value, reset);
  if (!actionMetrics.ok) {
    return actionMetrics;
  }

  return {
    ok: true,
    value: {
      owner: context.owner,
      periodStart: period.start,
      periodEnd: period.end,
      fetchedAt: context.requestedAt,
      source: "api",
      stale: false,
      copilot: copilot.value,
      actionsMinutes: actionMetrics.value.minutes,
      actionsStorage: actionMetrics.value.storage
    }
  };
}

function normalizeCopilot(
  items: ParsedItem[],
  endpoint: CopilotEndpoint,
  reset: UsageMetric["reset"]
): { ok: true; value: UsageMetric } | { ok: false; error: ProviderError } {
  const kind: CopilotMetricKind = endpoint === "ai-credits" ? "copilot-ai-credits" : "copilot-premium-requests";
  const expectedUnit = endpoint === "ai-credits" ? "ai-credits" : "premium-requests";
  const relevant = items.filter((item) => item.product.toLowerCase().includes("copilot"));
  const normalized: ParsedItem[] = [];

  for (const item of relevant) {
    const unit = normalizeCopilotUnit(item.unit, endpoint);
    if (unit === null) {
      return schemaFailure(`Unexpected Copilot unit '${item.unit}'.`);
    }
    normalized.push({ ...item, unit });
  }

  return {
    ok: true,
    value: metricFromItems(kind, expectedUnit, normalized, reset)
  };
}

function normalizeActions(
  items: ParsedItem[],
  reset: UsageMetric["reset"]
):
  | { ok: true; value: { minutes: UsageMetric; storage: UsageMetric } }
  | { ok: false; error: ProviderError } {
  const relevant = items.filter((item) => item.product.toLowerCase() === "actions");
  const minutes = relevant.filter((item) => item.unit.toLowerCase() === "minutes");
  const storage = relevant.filter((item) => isStorageUnit(item.unit));
  const unsupported = relevant.filter(
    (item) => item.unit.toLowerCase() !== "minutes" && !isStorageUnit(item.unit)
  );

  if (unsupported.length > 0) {
    return schemaFailure(`Unexpected Actions unit '${unsupported[0]?.unit ?? "unknown"}'.`);
  }

  const storageUnits = new Set(storage.map((item) => item.unit.toLowerCase()));
  if (storageUnits.size > 1) {
    return schemaFailure("Actions storage records use incompatible units and cannot be combined.");
  }
  const storageUnit = storage[0]?.unit ?? "gigabyte-hours";

  return {
    ok: true,
    value: {
      minutes: metricFromItems("actions-minutes", "minutes", minutes, reset),
      storage: metricFromItems("actions-storage", storageUnit, storage, reset)
    }
  };
}

function metricFromItems(
  kind: UsageMetric["kind"],
  unit: UsageUnit,
  items: ParsedItem[],
  reset: UsageMetric["reset"]
): UsageMetric {
  const money = sumMoney(items);
  return {
    kind,
    unit,
    used: sum(items.map((item) => item.grossQuantity)),
    allowance: null,
    allowanceSource: "unknown",
    percentage: null,
    reset,
    breakdowns: items.map(({ model: _model, ...item }) => item),
    ...money
  };
}

function parseItems(
  value: unknown,
  label: string
): { ok: true; value: ParsedItem[] } | { ok: false; error: ProviderError } {
  if (!Array.isArray(value)) {
    return schemaFailure(`${label} response is missing usageItems.`);
  }

  const items: ParsedItem[] = [];
  for (const valueItem of value) {
    const item = asRecord(valueItem);
    if (item === null) {
      return schemaFailure(`${label} usage item must be an object.`);
    }
    const product = requiredString(item.product);
    const sku = requiredString(item.sku);
    const unit = requiredString(item.unitType);
    const grossQuantity = optionalNumber(item.grossQuantity) ?? optionalNumber(item.quantity);
    if (product === null || sku === null || unit === null || grossQuantity === null) {
      return schemaFailure(`${label} usage item is missing product, sku, unitType, or quantity.`);
    }

    items.push({
      product,
      sku,
      unit,
      grossQuantity,
      grossAmount: optionalNumber(item.grossAmount),
      discountQuantity: optionalNumber(item.discountQuantity),
      discountAmount: optionalNumber(item.discountAmount),
      netQuantity: optionalNumber(item.netQuantity),
      netAmount: optionalNumber(item.netAmount),
      ...(typeof item.model === "string" ? { model: item.model } : {})
    });
  }
  return { ok: true, value: items };
}

function resolvePeriod(
  primary: unknown,
  secondary: unknown,
  context: Pick<NormalizationContext, "year" | "month">
): { start: number; end: number } {
  const period = readPeriod(primary) ?? readPeriod(secondary) ?? context;
  return {
    start: Date.UTC(period.year, period.month - 1, 1),
    end: Date.UTC(period.year, period.month, 1)
  };
}

function readPeriod(value: unknown): { year: number; month: number } | null {
  const period = asRecord(value);
  if (period === null) {
    return null;
  }
  const year = optionalNumber(period.year);
  const month = optionalNumber(period.month);
  if (year === null || month === null || !Number.isInteger(year) || !Number.isInteger(month) || month < 1 || month > 12) {
    return null;
  }
  return { year, month };
}

function normalizeCopilotUnit(unit: string, endpoint: CopilotEndpoint): UsageUnit | null {
  const normalized = unit.toLowerCase();
  if (endpoint === "ai-credits" && (normalized === "credits" || normalized === "ai-credits")) {
    return "ai-credits";
  }
  if (endpoint === "premium-requests" && (normalized === "requests" || normalized === "premium-requests")) {
    return "premium-requests";
  }
  return null;
}

function isStorageUnit(unit: string): boolean {
  const normalized = unit.toLowerCase();
  return normalized.includes("byte") || normalized.includes("storage");
}

function sumMoney(items: ParsedItem[]): MoneyBreakdown {
  return {
    grossAmount: sumNullable(items.map((item) => item.grossAmount)),
    discountAmount: sumNullable(items.map((item) => item.discountAmount)),
    netAmount: sumNullable(items.map((item) => item.netAmount))
  };
}

function sum(values: number[]): number {
  return values.reduce((total, value) => total + value, 0);
}

function sumNullable(values: Array<number | null>): number | null {
  const present = values.filter((value): value is number => value !== null);
  return present.length === 0 ? null : sum(present);
}

function optionalNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function requiredString(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0 ? value : null;
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function schemaFailure(message: string): { ok: false; error: ProviderError } {
  return {
    ok: false,
    error: {
      code: "schema-mismatch",
      message
    }
  };
}
