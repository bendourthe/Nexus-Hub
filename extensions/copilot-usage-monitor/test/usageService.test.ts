import { describe, expect, it } from "vitest";
import type { OrganizationProvider, ProviderFetchResult, UsageProvider } from "../src/providers/types";
import type { OrganizationUsage, PersonalUsage } from "../src/types";
import { UsageController } from "../src/usageController";
import { UsageService } from "../src/usageService";
import { UsageStore } from "../src/usageStore";
import { createMemento } from "./helpers";

const NOW = Date.UTC(2026, 9, 2);
const personalData: PersonalUsage = { planLabel: "Copilot Free", quotas: [], primary: null, creditsUsed: 0, resetsAt: null };
const orgData = { used: 1, total: 100, percent: 1 } as OrganizationUsage;

function personalProvider(result: ProviderFetchResult<PersonalUsage>): UsageProvider {
  return { id: "copilot", displayName: "x", readCredential: async () => ({ ok: true }), fetchUsage: async () => result };
}
function orgProvider(active: boolean, result?: ProviderFetchResult<OrganizationUsage>): OrganizationProvider & { calls: number } {
  const p = {
    calls: 0,
    isActive: () => active,
    fetchUsage: async () => {
      p.calls += 1;
      return result!;
    },
  };
  return p;
}

describe("UsageService", () => {
  it("returns the personal figure alone when no organization is configured", async () => {
    const org = orgProvider(false);
    const result = await new UsageService(personalProvider({ success: true, data: personalData }), org).fetchAll(NOW);
    expect(result).toEqual({ success: true, rateLimited: false, data: { personal: { ...personalData, fetchedAt: NOW }, lastUpdated: NOW, dataSource: "api" } });
    expect(org.calls).toBe(0);
  });

  it("merges both halves, and keeps one when the other fails", async () => {
    const both = await new UsageService(personalProvider({ success: true, data: personalData }), orgProvider(true, { success: true, data: orgData })).fetchAll(NOW);
    expect(both.success && both.data.organization).toEqual({ ...orgData, fetchedAt: NOW });

    const orgFails = await new UsageService(
      personalProvider({ success: true, data: personalData }),
      orgProvider(true, { success: false, error: { code: "org-access-denied", statusCode: 403, statusText: "Forbidden" } }),
    ).fetchAll(NOW);
    expect(orgFails.success && orgFails.data.organizationError).toEqual({ code: "org-access-denied", statusCode: 403 });

    const personalFails = await new UsageService(
      personalProvider({ success: false, error: { code: "rate-limited", statusCode: 429 } }),
      orgProvider(true, { success: true, data: orgData }),
    ).fetchAll(NOW);
    expect(personalFails).toMatchObject({ success: true, rateLimited: true, data: { personalError: { code: "rate-limited", statusCode: 429 } } });
  });

  it("returns the personal error, with the organization one, when both fail", async () => {
    const result = await new UsageService(
      personalProvider({ success: false, error: { code: "no-credentials" } }),
      orgProvider(true, { success: false, error: { code: "rate-limited" } }),
    ).fetchAll(NOW);
    expect(result).toEqual({ success: false, error: { code: "no-credentials" }, organizationError: { code: "rate-limited" }, rateLimited: true });
  });
});

describe("UsageController", () => {
  function surface() {
    const log: string[] = [];
    return {
      log,
      refresh: () => log.push("refresh"),
      setLastError: (e: unknown) => log.push(`error:${(e as { code?: string } | undefined)?.code ?? "none"}`),
      applyBackoff: () => log.push("backoff"),
      resetBackoff: () => log.push("reset"),
    };
  }

  it("shares one fetch between concurrent callers and counts failures", async () => {
    let calls = 0;
    let resolve!: (v: unknown) => void;
    const service = {
      fetchAll: () => {
        calls += 1;
        return new Promise((r) => (resolve = r));
      },
    } as unknown as UsageService;
    const s = surface();
    const controller = new UsageController(new UsageStore(createMemento()), service, s, "/nonexistent/state.json");
    const a = controller.refresh();
    const b = controller.refresh();
    resolve({ success: false, error: { code: "rate-limited" }, rateLimited: true });
    await Promise.all([a, b]);
    expect(calls).toBe(1);
    expect(controller.consecutiveFailures).toBe(1);
    expect(controller.lastFetchError).toEqual({ code: "rate-limited" });
    expect(s.log).toEqual(["backoff", "error:rate-limited", "refresh"]);
  });

  it("resets the failure count and backoff after a success", async () => {
    const service = { fetchAll: async () => ({ success: true, rateLimited: false, data: { lastUpdated: NOW, dataSource: "api" } }) } as unknown as UsageService;
    const s = surface();
    const controller = new UsageController(new UsageStore(createMemento()), service, s, "/nonexistent/dir/state.json");
    controller.consecutiveFailures = 3;
    await controller.refresh();
    expect(controller.consecutiveFailures).toBe(0);
    expect(s.log).toEqual(["reset", "error:none", "refresh"]);
  });
});
