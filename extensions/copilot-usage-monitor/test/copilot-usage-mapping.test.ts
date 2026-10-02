import { afterEach, describe, expect, it } from "vitest";
import { mapCopilotUser, mapQuota } from "../src/providers/copilot";
import { CREDITS_PER_SEAT, mapOrganizationUsage } from "../src/providers/copilotOrganization";
import { __resetLog } from "../src/log";
import { headlineOf } from "../src/types";
import { formatPercent } from "../src/usageStore";
import { fixture } from "./helpers";
import { __resetStubState, outputLines } from "./vscode-stub";

const OCT_2 = Date.UTC(2026, 9, 2, 0, 5);

describe("mapCopilotUser (decision item 1)", () => {
  it("maps the captured Copilot Free account to served quotas with chat as the status-bar quota", () => {
    const usage = mapCopilotUser(fixture("copilot-internal-user.personal.json"));
    expect(usage).not.toBeNull();
    expect(usage!.planLabel).toBe("Copilot Free");
    // premium_interactions has has_quota false and entitlement 0: "no allowance", not "exhausted".
    expect(usage!.quotas.map((q) => q.id)).toEqual(["chat", "completions"]);
    expect(usage!.primary).toMatchObject({ id: "chat", label: "Chat", percent: 0, entitlement: 200, remaining: 200 });
    expect(usage!.resetsAt).toBe(Date.UTC(2026, 10, 1));
    expect(usage!.creditsUsed).toBe(0);
  });

  it("maps the captured Business seat to credits used with no quota and no percentage", () => {
    const usage = mapCopilotUser(fixture("copilot-internal-user.business-member.json"));
    expect(usage!.planLabel).toBe("Copilot Business");
    expect(usage!.quotas).toEqual([]);
    expect(usage!.primary).toBeNull();
    expect(usage!.creditsUsed).toBe(0);
    expect(headlineOf({ personal: usage!, lastUpdated: 0, dataSource: "api" })).toEqual({
      kind: "credits",
      creditsUsed: 0,
      label: "Copilot Business",
    });
  });

  it("never copies the login, ids, or organization list into the mapped figure", () => {
    for (const name of ["copilot-internal-user.personal.json", "copilot-internal-user.business-member.json"]) {
      const serialized = JSON.stringify(mapCopilotUser(fixture(name)));
      expect(serialized).not.toContain("example-user");
      expect(serialized).not.toContain("example-org");
      expect(serialized).not.toContain("example-id");
    }
  });

  it("prefers premium requests when that quota is limited and sums credits_used", () => {
    const usage = mapCopilotUser({
      copilot_plan: "individual",
      access_type_sku: "some_paid_sku",
      quota_reset_date: "2026-11-01",
      quota_snapshots: {
        chat: { unlimited: false, has_quota: true, entitlement: 100, remaining: 50, percent_remaining: 50, credits_used: 1.5 },
        premium_interactions: { unlimited: false, has_quota: true, entitlement: 300, remaining: 30, percent_remaining: 10, credits_used: 2 },
        custom_quota: { unlimited: false, has_quota: true, entitlement: 10, remaining: 10, percent_remaining: 100 },
        bad: "not an object",
      },
      unknown_field: { ignored: true },
    });
    expect(usage!.planLabel).toBe("Copilot individual plan");
    expect(usage!.quotas.map((q) => q.id)).toEqual(["premium_interactions", "chat", "custom_quota"]);
    expect(usage!.quotas[2].label).toBe("Custom quota");
    expect(usage!.primary!.id).toBe("premium_interactions");
    expect(usage!.primary!.percent).toBe(90);
    expect(usage!.creditsUsed).toBe(3.5);
    // quota_reset_date at 00:00:00 UTC when quota_reset_date_utc is absent.
    expect(usage!.resetsAt).toBe(Date.UTC(2026, 10, 1));
  });

  it.each([
    [{ copilot_plan: "enterprise", quota_snapshots: {} }, "Copilot Enterprise"],
    [{ quota_snapshots: {} }, "GitHub Copilot"],
  ])("labels the plan %#", (payload, label) => {
    expect(mapCopilotUser(payload)!.planLabel).toBe(label);
  });

  it("returns null when quota_snapshots is missing, and a null reset for unusable dates", () => {
    expect(mapCopilotUser({ login: "x" })).toBeNull();
    expect(mapCopilotUser(null)).toBeNull();
    expect(mapCopilotUser([])).toBeNull();
    expect(mapCopilotUser({ quota_snapshots: {}, quota_reset_date_utc: "garbage", quota_reset_date: "Nov 1" })!.resetsAt).toBeNull();
  });
});

describe("mapQuota", () => {
  const base = { unlimited: false, has_quota: true, entitlement: 200, remaining: 150, percent_remaining: 75 };

  it("uses 100 - percent_remaining when it agrees with the remaining count", () => {
    expect(mapQuota("chat", base)!.percent).toBe(25);
  });

  it.each([
    [{ ...base, unlimited: true }],
    [{ ...base, unlimited: undefined }],
    [{ ...base, has_quota: false }],
    [{ ...base, entitlement: 0 }],
    [{ ...base, entitlement: "200" }],
    [{ unlimited: false, has_quota: true, entitlement: 200 }],
    [null],
  ])("yields no percentage for a quota GitHub does not serve as limited %#", (raw) => {
    expect(mapQuota("chat", raw)).toBeNull();
  });

  it("shows the higher used figure when the two served values disagree by more than a point", () => {
    expect(mapQuota("chat", { ...base, percent_remaining: 90 })!.percent).toBe(25);
    expect(mapQuota("chat", { ...base, remaining: 190 })!.percent).toBe(25);
  });

  it("falls back to whichever served value exists, and clamps to 0..100", () => {
    expect(mapQuota("chat", { unlimited: false, has_quota: true, entitlement: 200, remaining: 50 })!.percent).toBe(75);
    const fromPercent = mapQuota("chat", { unlimited: false, has_quota: true, entitlement: 200, percent_remaining: 40 })!;
    expect(fromPercent.percent).toBe(60);
    expect(fromPercent.remaining).toBe(80);
    expect(mapQuota("chat", { unlimited: false, has_quota: true, entitlement: 10, remaining: -5, percent_remaining: -20 })!.percent).toBe(100);
    expect(mapQuota("chat", { unlimited: false, has_quota: true, entitlement: 10, quota_remaining: 5 })!.percent).toBe(50);
  });
});

describe("mapOrganizationUsage (decision items 2 and 3)", () => {
  afterEach(() => {
    __resetLog();
    __resetStubState();
  });

  it("maps the captured cycle: 0.907 of 13,300 credits, shown as 0.01%", () => {
    const org = mapOrganizationUsage(fixture("copilot-billing.json"), fixture("ai-credit-usage.json"), OCT_2)!;
    expect(org.used).toBeCloseTo(0.9069921, 7);
    expect(org.total).toBe(13_300);
    expect(org.seats).toBe(7);
    expect(org.planType).toBe("business");
    expect(org.creditsPerSeat).toBe(1_900);
    expect(org.approximate).toBe(false);
    expect(org.percent).toBeCloseTo((0.9069921 / 13_300) * 100, 9);
    expect(formatPercent(org.percent!)).toBe("0.01");
    expect(org.resetsAt).toBe(Date.UTC(2026, 10, 1));
    expect(org.models).toEqual([{ model: "Auto: GPT-6 Luna", used: 0.9069921 }]);
  });

  it("maps the near-limit synthetic fixture to 99.25%", () => {
    const org = mapOrganizationUsage(fixture("copilot-billing.json"), fixture("ai-credit-usage.near-limit.synthetic.json"), OCT_2)!;
    expect(org.used).toBe(13_200);
    expect(org.percent).toBeCloseTo(99.2481, 3);
    expect(formatPercent(org.percent!)).toBe("99.25");
  });

  it("caps the over-pool synthetic fixture at the discounted pool: 100%", () => {
    const org = mapOrganizationUsage(fixture("copilot-billing.json"), fixture("ai-credit-usage.over-pool.synthetic.json"), OCT_2)!;
    expect(org.used).toBe(13_300);
    expect(org.percent).toBe(100);
  });

  it("marks the total approximate when a seat was added this cycle", () => {
    const org = mapOrganizationUsage(fixture("copilot-billing.seat-added.synthetic.json"), fixture("ai-credit-usage.json"), OCT_2)!;
    expect(org.seats).toBe(8);
    expect(org.total).toBe(15_200);
    expect(org.approximate).toBe(true);
    expect(org.approximateReasons).toEqual(["seat-added"]);
  });

  it("marks the total approximate when a seat is pending cancellation, and uses the Enterprise rate", () => {
    const billing = { plan_type: "enterprise", seat_breakdown: { total: 2, pending_cancellation: 1, added_this_cycle: 0 } };
    const org = mapOrganizationUsage(billing, fixture("ai-credit-usage.json"), OCT_2)!;
    expect(org.total).toBe(2 * CREDITS_PER_SEAT.enterprise);
    expect(org.approximateReasons).toEqual(["pending-cancellation"]);
  });

  it.each([
    [{ plan_type: "business", seat_breakdown: { total: 0 } }],
    [{ plan_type: "team", seat_breakdown: { total: 7 } }],
    [{}],
    [null],
  ])("shows no pool percentage without a seat count and a known plan %#", (billing) => {
    const org = mapOrganizationUsage(billing, fixture("ai-credit-usage.json"), OCT_2)!;
    expect(org.total).toBe(0);
    expect(org.percent).toBeNull();
    expect(headlineOf({ organization: org, lastUpdated: 0, dataSource: "api" }).kind).toBe("credits");
  });

  it("leaves non-Copilot line items out of the sum and logs that once, without values", () => {
    const usage = {
      timePeriod: { year: 2026, month: 10 },
      usageItems: [
        { product: "Copilot", sku: "Copilot AI Credits", unitType: "ai-credits", model: "", discountQuantity: 2 },
        { product: "Actions", unitType: "minutes", discountQuantity: 500, sku: "Actions Linux" },
        { product: "Copilot", sku: "Copilot AI Credits", unitType: "ai-credits", discountQuantity: "3" },
        "junk",
      ],
    };
    const org = mapOrganizationUsage(fixture("copilot-billing.json"), usage, OCT_2)!;
    mapOrganizationUsage(fixture("copilot-billing.json"), usage, OCT_2);
    expect(org.used).toBe(2);
    expect(org.models).toEqual([{ model: "Other", used: 2 }]);
    expect(outputLines).toHaveLength(1);
    expect(outputLines[0]).toContain("Left 3 usage line item(s) out of the pool");
    expect(outputLines[0]).not.toContain("Actions Linux");
  });

  it("returns null when the usage payload has no usageItems array", () => {
    expect(mapOrganizationUsage(fixture("copilot-billing.json"), { usageItems: "x" })).toBeNull();
    expect(mapOrganizationUsage(fixture("copilot-billing.json"), null)).toBeNull();
  });

  it("never copies the organization name into the mapped pool", () => {
    const org = mapOrganizationUsage(fixture("copilot-billing.json"), fixture("ai-credit-usage.json"), OCT_2);
    expect(JSON.stringify(org)).not.toContain("example-org");
  });
});
