import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { normalizeUsageResponses } from "../src/providers/normalizer";

const requestedAt = Date.UTC(2026, 7, 15, 12);
const user = { scope: "user" as const, name: "fixture-user" };
const organization = { scope: "organization" as const, name: "fixture-organization" };

function fixture(name: string): unknown {
  const path = resolve(__dirname, "../../../tests/fixtures/github-usage", name);
  return JSON.parse(readFileSync(path, "utf8")) as unknown;
}

describe("normalizeUsageResponses", () => {
  it("normalizes AI credits, Actions minutes, storage, costs, and discounts", () => {
    const result = normalizeUsageResponses(
      fixture("current-ai-credits.json"),
      fixture("actions-minutes-storage.json"),
      { owner: user, copilotEndpoint: "ai-credits", requestedAt, year: 2026, month: 8 }
    );
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value.copilot).toMatchObject({
        kind: "copilot-ai-credits",
        unit: "ai-credits",
        used: 125.5,
        grossAmount: 1.255,
        discountAmount: 1,
        netAmount: 0.255,
        allowance: null,
        percentage: null
      });
      expect(result.value.actionsMinutes).toMatchObject({ used: 1200, unit: "minutes", netAmount: 1.6 });
      expect(result.value.actionsStorage).toMatchObject({ used: 640, unit: "gigabyte-hours", netAmount: 0.06 });
      expect(result.value.periodStart).toBe(Date.UTC(2026, 7, 1));
      expect(result.value.periodEnd).toBe(Date.UTC(2026, 8, 1));
    }
  });

  it("keeps legacy premium requests distinct from AI credits", () => {
    const result = normalizeUsageResponses(
      fixture("legacy-premium-requests.json"),
      fixture("empty-month.json"),
      { owner: user, copilotEndpoint: "premium-requests", requestedAt, year: 2026, month: 8 }
    );
    expect(result.ok && result.value.copilot.kind).toBe("copilot-premium-requests");
    if (result.ok) {
      expect(result.value.copilot).toMatchObject({ unit: "premium-requests", used: 84 });
    }
  });

  it("normalizes managed Copilot credits at organization scope", () => {
    const result = normalizeUsageResponses(
      fixture("managed-copilot.json"),
      fixture("actions-minutes-storage.json"),
      { owner: organization, copilotEndpoint: "ai-credits", requestedAt, year: 2026, month: 8 }
    );
    expect(result.ok && result.value.copilot.used).toBe(3800);
  });

  it("rejects managed Copilot data queried through personal scope", () => {
    const result = normalizeUsageResponses(
      fixture("managed-copilot.json"),
      fixture("empty-month.json"),
      { owner: user, copilotEndpoint: "ai-credits", requestedAt, year: 2026, month: 8 }
    );
    expect(!result.ok && result.error.code).toBe("managed-copilot-personal-scope");
  });

  it("ignores additive fields and preserves numeric zero", () => {
    const result = normalizeUsageResponses(
      fixture("empty-month.json"),
      fixture("additive-fields.json"),
      { owner: user, copilotEndpoint: "ai-credits", requestedAt, year: 2026, month: 8 }
    );
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value.copilot.used).toBe(0);
      expect(result.value.actionsMinutes).toMatchObject({ used: 12, netAmount: 0 });
      expect(result.value.actionsStorage.used).toBe(0);
    }
  });

  it("keeps the unknown-allowance fixture absolute with no percentage", () => {
    const result = normalizeUsageResponses(
      fixture("unknown-allowance.json"),
      fixture("empty-month.json"),
      { owner: user, copilotEndpoint: "ai-credits", requestedAt, year: 2026, month: 8 }
    );
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value.copilot).toMatchObject({
        used: 125.5,
        allowance: null,
        allowanceSource: "unknown",
        percentage: null
      });
    }
  });

  it("falls back to the requested month when timePeriod is absent", () => {
    const payload = { usageItems: [] };
    const result = normalizeUsageResponses(payload, payload, {
      owner: user,
      copilotEndpoint: "ai-credits",
      requestedAt,
      year: 2026,
      month: 9
    });
    expect(result.ok && result.value.periodStart).toBe(Date.UTC(2026, 8, 1));
  });

  it.each([
    [null, { usageItems: [] }],
    [{}, { usageItems: [] }],
    [{ usageItems: [null] }, { usageItems: [] }],
    [{ usageItems: [{ product: "Copilot", sku: "x", unitType: "credits" }] }, { usageItems: [] }],
    [{ usageItems: [{ product: "Copilot", sku: "x", unitType: "minutes", grossQuantity: 1 }] }, { usageItems: [] }],
    [{ usageItems: [] }, { usageItems: [{ product: "Actions", sku: "x", unitType: "widgets", grossQuantity: 1 }] }]
  ])("rejects malformed or incompatible payloads", (copilot, actions) => {
    const result = normalizeUsageResponses(copilot, actions, {
      owner: user,
      copilotEndpoint: "ai-credits",
      requestedAt,
      year: 2026,
      month: 8
    });
    expect(!result.ok && result.error.code).toBe("schema-mismatch");
  });

  it("rejects aggregation across incompatible storage units", () => {
    const actions = {
      usageItems: [
        { product: "Actions", sku: "a", unitType: "gigabyte-hours", grossQuantity: 1 },
        { product: "Actions", sku: "b", unitType: "terabyte-hours", grossQuantity: 1 }
      ]
    };
    const result = normalizeUsageResponses({ usageItems: [] }, actions, {
      owner: user,
      copilotEndpoint: "ai-credits",
      requestedAt,
      year: 2026,
      month: 8
    });
    expect(result.ok).toBe(false);
  });
});
