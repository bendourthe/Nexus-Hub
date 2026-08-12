import { describe, expect, it } from "vitest";
import {
  AI_CREDIT_PROMOTION_ENDS_UTC,
  aiCreditAllowance,
  aiCreditsPerSeat,
  describeAiCreditProvenance
} from "../src/providers/planEntitlements";
import { fetchCopilotSubscription } from "../src/providers/repositories";

/**
 * The pooled Copilot AI-credit denominator.
 *
 * Verified 2026-08-11 against GitHub's published figures and one live organization:
 * SupiraMedical, 7 billable Copilot Business licences, 21,000 included credits.
 */

const ok = (value: unknown) => Promise.resolve({ ok: true as const, value });
const AUGUST = Date.UTC(2026, 7, 1);
const SEPTEMBER = Date.UTC(2026, 8, 1);

describe("AI credits per seat", () => {
  it("reproduces the live organization's pool exactly", () => {
    expect(aiCreditAllowance("business", 7, AUGUST)).toBe(21_000);
  });

  it("switches to the standard figure the moment the promotion ends", () => {
    // The whole reason this is a function of the period and not a constant. A build
    // that hardcodes either figure is wrong on one side of this boundary.
    expect(aiCreditsPerSeat("business", AUGUST)).toBe(3_000);
    expect(aiCreditsPerSeat("business", AI_CREDIT_PROMOTION_ENDS_UTC - 1)).toBe(3_000);
    expect(aiCreditsPerSeat("business", AI_CREDIT_PROMOTION_ENDS_UTC)).toBe(1_900);
    expect(aiCreditsPerSeat("business", SEPTEMBER)).toBe(1_900);

    expect(aiCreditsPerSeat("enterprise", AUGUST)).toBe(7_000);
    expect(aiCreditsPerSeat("enterprise", SEPTEMBER)).toBe(3_900);
  });

  it("drops the same organization's pool by the published amount in September", () => {
    expect(aiCreditAllowance("business", 7, SEPTEMBER)).toBe(13_300);
  });

  it("refuses to compose a denominator from a missing or nonsensical term", () => {
    // A seat count that failed to load would compose into a confidently SMALL
    // denominator, which reads as "nearly out" - wrong in the direction that changes
    // what the user does.
    expect(aiCreditAllowance("business", 0, AUGUST)).toBeNull();
    expect(aiCreditAllowance("business", -3, AUGUST)).toBeNull();
    expect(aiCreditAllowance("business", 2.5, AUGUST)).toBeNull();
    expect(aiCreditAllowance("business", undefined, AUGUST)).toBeNull();
    expect(aiCreditAllowance("business", "7", AUGUST)).toBeNull();
  });

  it("never falls back to the Business figure for an unrecognized plan", () => {
    // The same rule `resolvePlan` follows: guessing the cheaper tier understates the
    // allowance for whoever is paying the most.
    expect(aiCreditsPerSeat("copilot_business", AUGUST)).toBeNull();
    expect(aiCreditsPerSeat("", AUGUST)).toBeNull();
    expect(aiCreditsPerSeat(null, AUGUST)).toBeNull();
    expect(aiCreditAllowance("free", 7, AUGUST)).toBeNull();
  });

  it("shows its working, because a composed figure needs more provenance not less", () => {
    const line = describeAiCreditProvenance("business", 7, 3_000);

    expect(line).toContain("7 Copilot Business seats");
    expect(line).toContain("3,000");
    expect(line).toContain("not read from your account");
  });
});

describe("fetchCopilotSubscription", () => {
  const org = { scope: "organization", name: "SupiraMedical" };

  it("reads the plan type and assigned seat count", async () => {
    const paths: string[] = [];
    const result = await fetchCopilotSubscription((path) => {
      paths.push(path);
      return ok({ plan_type: "business", seat_breakdown: { total: 7, active_this_cycle: 5 } });
    }, "t", org);

    expect(result).toEqual({ planType: "business", seats: 7 });
    expect(paths).toEqual(["/orgs/SupiraMedical/copilot/billing"]);
  });

  it("never asks for a personal or enterprise owner", async () => {
    let called = false;
    const spy = () => { called = true; return ok({ plan_type: "business", seat_breakdown: { total: 7 } }); };

    expect(await fetchCopilotSubscription(spy, "t", { scope: "user", name: "someone" })).toBeNull();
    expect(await fetchCopilotSubscription(spy, "t", { scope: "enterprise", name: "acme" })).toBeNull();
    expect(called).toBe(false);
  });

  it("returns null rather than a partial subscription", async () => {
    // 404: no Copilot subscription. 403: caller is not an organization owner.
    expect(await fetchCopilotSubscription(() => Promise.resolve({ ok: false as const, status: 404 }), "t", org)).toBeNull();
    expect(await fetchCopilotSubscription(() => Promise.resolve({ ok: false as const, status: 403 }), "t", org)).toBeNull();
    expect(await fetchCopilotSubscription(() => ok(null), "t", org)).toBeNull();
    expect(await fetchCopilotSubscription(() => ok({ plan_type: "business" }), "t", org)).toBeNull();
    expect(await fetchCopilotSubscription(() => ok({ seat_breakdown: { total: 7 } }), "t", org)).toBeNull();
    expect(await fetchCopilotSubscription(() => ok({ plan_type: "unknown_tier", seat_breakdown: { total: 7 } }), "t", org)).toBeNull();
    expect(await fetchCopilotSubscription(() => ok({ plan_type: "business", seat_breakdown: { total: 0 } }), "t", org)).toBeNull();
  });

  it("accepts the plan type however GitHub cases it", async () => {
    const result = await fetchCopilotSubscription(() => ok({ plan_type: " Business ", seat_breakdown: { total: 7 } }), "t", org);

    expect(result).toEqual({ planType: "business", seats: 7 });
  });
});
