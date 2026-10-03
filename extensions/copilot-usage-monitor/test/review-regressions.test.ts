import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { DashboardPanel } from "../src/dashboardPanel";
import { __resetLog } from "../src/log";
import { CopilotUsageProvider, mapQuota } from "../src/providers/copilot";
import { CopilotOrganizationProvider, ORG_TOKEN_SECRET_KEY, mapOrganizationUsage } from "../src/providers/copilotOrganization";
import { jsonForScript, parseDraft, settingsSectionHtml } from "../src/settingsPanel";
import { StatusBarManager } from "../src/statusBarManager";
import { getColorConfig, getRefreshIntervalMinutes, getThresholdConfig, headlineOf } from "../src/types";
import { UsageController, retainTransient } from "../src/usageController";
import { UsageService } from "../src/usageService";
import { buildUsageState, writeUsageState } from "../src/usageStateFile";
import { UsageStore } from "../src/usageStore";
import {
  FakeGitHubAuth,
  FakeSecretStorage,
  ORG_TOKEN,
  PERSONAL_TOKEN,
  WORK_TOKEN,
  createMemento,
  fixture,
  jsonResponse,
  routedFetch,
} from "./helpers";
import {
  __resetStubState,
  __setAuthentication,
  __setStubConfig,
  configurationUpdates,
  createdStatusBarItems,
  createdWebviewPanels,
} from "./vscode-stub";

const OCT_5 = Date.UTC(2026, 9, 5);
const callbacks = {
  onRefresh() {},
  onOpenUsagePage() {},
  onSignIn() {},
  onSwitchAccount() {},
  onConnectOrganization() {},
  onDisconnectOrganization() {},
};

let dir: string;
beforeEach(() => {
  dir = fs.mkdtempSync(path.join(os.tmpdir(), "copilot-review-"));
});
afterEach(() => {
  for (const panel of createdWebviewPanels) panel.dispose();
  __resetStubState();
  __resetLog();
  fs.rmSync(dir, { recursive: true, force: true });
});

describe("F1: the dashboard webview cannot be scripted through settings", () => {
  function hostileDashboard(): string {
    __setStubConfig("copilotUsage", "thresholds.moderate", '50"><img src=x onerror=alert(1)>');
    __setStubConfig("copilotUsage", "colors.high", '#"><svg onload=alert(2)>');
    __setStubConfig("copilotUsage", "colors.critical", "</script><script>alert(3)</script>");
    DashboardPanel.show(undefined, "now", undefined, { configured: false, connected: false }, callbacks);
    return createdWebviewPanels[0].webview.html;
  }

  it("renders no injected markup from hostile threshold and color settings (reviewer probe)", () => {
    const html = hostileDashboard();
    for (const injected of ["onerror=alert(1)", "onload=alert(2)", "<script>alert(3)", "alert("]) {
      expect(html.includes(injected), injected).toBe(false);
    }
  });

  it("serves a nonce Content-Security-Policy whose nonce matches the only script", () => {
    const html = hostileDashboard();
    const csp = html.match(/<meta http-equiv="Content-Security-Policy" content="([^"]+)">/);
    expect(csp).not.toBeNull();
    expect(csp![1]).toContain("default-src 'none'");
    const nonce = csp![1].match(/script-src 'nonce-([^']+)'/)![1];
    // Case-insensitive so <SCRIPT>, <Script> and friends cannot slip past the count.
    const scripts = [...html.matchAll(/<script\b([^>]*)>/gi)].map((m) => m[1]);
    expect(scripts).toEqual([` nonce="${nonce}"`]);
    // Exactly one closing tag in any case, spacing, or attribute variant (</SCRIPT >, </script foo>).
    expect([...html.matchAll(/<\/script\b[^>]*>/gi)]).toHaveLength(1);
  });

  it("contains no inline event handler attributes", () => {
    expect(hostileDashboard()).not.toMatch(/\son[a-z]+\s*=/i);
    DashboardPanel.updateIfOpen(fixtureData(), "now", { code: "org-token-rejected" });
    expect(DashboardPanel.currentHtml()).not.toMatch(/\son[a-z]+\s*=/i);
  });

  it("validates thresholds and colors where they are read", () => {
    __setStubConfig("copilotUsage", "thresholds.moderate", "50");
    __setStubConfig("copilotUsage", "thresholds.high", 0);
    __setStubConfig("copilotUsage", "thresholds.critical", Number.NaN);
    __setStubConfig("copilotUsage", "colors.moderate", "#12345");
    __setStubConfig("copilotUsage", "colors.high", "none");
    __setStubConfig("copilotUsage", "colors.critical", "#ABCDEF");
    expect(getThresholdConfig()).toEqual({ moderate: 50, high: 75, critical: 95 });
    expect(getColorConfig()).toEqual({ moderate: "#cca700", high: "none", critical: "#ABCDEF" });
  });

  it("validates and escapes values in the markup builder itself, not only on read", () => {
    const hostile = {
      thresholds: { moderate: '50"><img src=x onerror=alert(1)>' as unknown as number, high: 75, critical: 95 },
      colors: { moderate: '#"><svg onload=alert(2)>', high: "#f0643c", critical: "#e05555" },
      compact: false,
    };
    const html = settingsSectionHtml(hostile, { configured: false, connected: false });
    expect(html).not.toContain("onerror");
    expect(html).not.toContain("onload");
    expect(html).toContain('value="50" class="threshold-slider" data-level="moderate"');
    expect(html).toContain('id="picker-moderate" data-level="moderate" value="#cca700"');
  });

  it("escapes < in JSON embedded in the script", () => {
    expect(jsonForScript({ a: "</script><script>x" })).toBe('{"a":"\\u003c/script>\\u003cscript>x"}');
  });

  it.each([
    [undefined],
    ["draft"],
    [{ thresholds: { moderate: 50, high: 75, critical: 95 }, colors: { moderate: "#cca700", high: "#f0643c", critical: "#e05555" } }],
    [{ thresholds: { moderate: "50", high: 75, critical: 95 }, colors: { moderate: "#cca700", high: "#f0643c", critical: "#e05555" }, compact: false }],
    [{ thresholds: { moderate: 0, high: 75, critical: 95 }, colors: { moderate: "#cca700", high: "#f0643c", critical: "#e05555" }, compact: false }],
    [{ thresholds: { moderate: 50, high: 100, critical: 95 }, colors: { moderate: "#cca700", high: "#f0643c", critical: "#e05555" }, compact: false }],
    [{ thresholds: { moderate: 50, high: 75, critical: 95 }, colors: { moderate: '#"><x', high: "#f0643c", critical: "#e05555" }, compact: false }],
    [{ thresholds: { moderate: 50, high: 75 }, colors: { moderate: "#cca700", high: "#f0643c", critical: "#e05555" }, compact: false }],
  ])("rejects a malformed settings draft %#", (draft) => {
    expect(parseDraft(draft)).toBeNull();
  });

  it("accepts a valid draft", () => {
    const draft = { thresholds: { moderate: 40, high: 70, critical: 90 }, colors: { moderate: "#112233", high: "none", critical: "#AABBCC" }, compact: true };
    expect(parseDraft(draft)).toEqual(draft);
  });

  it("writes nothing for forged or malformed webview messages", async () => {
    DashboardPanel.show(fixtureData(), "now", undefined, { configured: false, connected: false }, callbacks);
    const panel = createdWebviewPanels[0];
    for (const message of [null, "save", 42, { command: 1 }, { command: "save" }, { command: "save", draft: { thresholds: "x" } }, { command: "unknown" }]) {
      await panel.webview.__dispatchMessage(message);
    }
    expect(configurationUpdates).toEqual([]);
    expect(panel.webview.postedMessages).toEqual([]);
  });
});

function fixtureData() {
  return {
    personal: { planLabel: "Copilot Free", quotas: [], primary: null, creditsUsed: 0, resetsAt: null },
    lastUpdated: OCT_5,
    dataSource: "api" as const,
  };
}

describe("F2: the pool counts only Copilot AI Credits for the requested month", () => {
  const billing = { plan_type: "business", seat_breakdown: { total: 7, added_this_cycle: 0, pending_cancellation: 0 } };
  const item = (o: Record<string, unknown>) => ({ product: "Copilot", sku: "Copilot AI Credits", unitType: "ai-credits", model: "m", discountQuantity: 1, ...o });

  it("leaves a second SKU out of the sum (reviewer probe)", () => {
    const r = mapOrganizationUsage(billing, { timePeriod: { year: 2026, month: 10 }, usageItems: [item({ discountQuantity: 100 }), item({ sku: "Copilot Promo Credits", discountQuantity: 5000 })] }, OCT_5)!;
    expect(r.used).toBe(100);
  });

  it("leaves negative and non-finite quantities out", () => {
    const r = mapOrganizationUsage(billing, {
      timePeriod: { year: 2026, month: 10 },
      usageItems: [item({ discountQuantity: -500 }), item({ discountQuantity: Number.POSITIVE_INFINITY }), item({ discountQuantity: 3 })],
    }, OCT_5)!;
    expect(r.used).toBe(3);
    expect(r.percent).toBeGreaterThanOrEqual(0);
  });

  it.each([
    [{ year: 2026, month: 9 }],
    [{ year: 2025, month: 10 }],
    [{ year: "2026", month: 10 }],
    [undefined],
  ])("rejects a report for another period %#, so no state file is built from it", (timePeriod) => {
    const r = mapOrganizationUsage(billing, { timePeriod, usageItems: [item({ discountQuantity: 13_000 })] }, OCT_5);
    expect(r).toBeNull();
  });

  it("reports usage-unavailable from the provider for a mismatched month", async () => {
    __setStubConfig("copilotUsage", "organization", "acme-co");
    const secrets = new FakeSecretStorage();
    secrets.values.set(ORG_TOKEN_SECRET_KEY, ORG_TOKEN);
    const fake = routedFetch((url) =>
      url.pathname.endsWith("/copilot/billing") ? jsonResponse(fixture("copilot-billing.json")) : jsonResponse(fixture("ai-credit-usage.json")),
    );
    const result = await new CopilotOrganizationProvider(secrets.asSecretStorage(), fake.fetch).fetchUsage(Date.UTC(2026, 10, 3));
    expect(result).toEqual({ success: false, error: { code: "usage-unavailable" } });
  });

  it("clamps out-of-range served quota values (reviewer probe)", () => {
    expect(mapQuota("chat", { unlimited: false, has_quota: true, entitlement: 50, remaining: -10, percent_remaining: 120 })!.percent).toBe(100);
    expect(mapQuota("chat", { unlimited: false, has_quota: true, entitlement: 50, percent_remaining: 40 })!.percent).toBe(60);
  });
});

type Mode = { personal: number | "throw"; org: number | "throw"; usage?: string };

function harness() {
  let mode: Mode = { personal: 200, org: 200, usage: "ai-credit-usage.near-limit.synthetic.json" };
  const fake = routedFetch((url, authorization) => {
    if (url.pathname === "/copilot_internal/user") {
      if (mode.personal === "throw") return "throw";
      if (mode.personal !== 200) return jsonResponse({}, mode.personal);
      return jsonResponse(fixture(authorization === `token ${WORK_TOKEN}` ? "copilot-internal-user.business-member.json" : "copilot-internal-user.personal.json"));
    }
    if (mode.org === "throw") return "throw";
    if (mode.org !== 200) return jsonResponse({}, mode.org);
    return url.pathname.endsWith("/copilot/billing") ? jsonResponse(fixture("copilot-billing.json")) : jsonResponse(fixture(mode.usage!));
  });
  const auth = new FakeGitHubAuth([{ id: "work", label: "w", token: WORK_TOKEN }]);
  __setAuthentication(auth);
  __setStubConfig("copilotUsage", "organization", "acme-co");
  const secrets = new FakeSecretStorage();
  secrets.values.set(ORG_TOKEN_SECRET_KEY, ORG_TOKEN);
  const store = new UsageStore(createMemento());
  const bar = new StatusBarManager(store, "x");
  const statePath = path.join(dir, "copilot.json");
  const controller = new UsageController(
    store,
    new UsageService(new CopilotUsageProvider(undefined, fake.fetch), new CopilotOrganizationProvider(secrets.asSecretStorage(), fake.fetch)),
    bar,
    statePath,
  );
  const state = () => (fs.existsSync(statePath) ? JSON.parse(fs.readFileSync(statePath, "utf-8")) : null);
  return { setMode: (m: Mode) => (mode = m), controller, store, state, statePath, auth, secrets, item: () => createdStatusBarItems[0] };
}

describe("F3: a transient organization failure keeps the last good pool figure", () => {
  it.each<[string, Mode]>([
    ["429", { personal: 200, org: 429 }],
    ["502", { personal: 200, org: 502 }],
    ["a network error", { personal: 200, org: "throw" }],
  ])("after %s the headline, status bar, and state file keep the pool at 99.25%%, marked stale", async (_name, failing) => {
    const h = harness();
    await h.controller.refresh(OCT_5);
    expect(h.state().windows[0]).toMatchObject({ percent: 99.25, source: "organization" });
    expect(h.state().stale).toBeUndefined();

    h.setMode(failing);
    await h.controller.refresh(OCT_5 + 5 * 60_000);
    const data = h.store.get()!;
    expect(data.organization).toMatchObject({ stale: true, fetchedAt: OCT_5, used: 13_200 });
    expect(headlineOf(data)).toMatchObject({ kind: "percent", source: "organization", stale: true });
    expect(h.item().text).toContain("99.25% (month) $(warning)");
    expect((h.item().tooltip as { value: string }).value).toContain("The last refresh failed");
    expect(h.state()).toMatchObject({ stale: true, fetched_at: "2026-10-05T00:00:00Z" });
    expect(h.state().windows[0].percent).toBe(99.25);
    DashboardPanel.show(data, "now", undefined, { configured: true, connected: true }, callbacks);
    expect(createdWebviewPanels[0].webview.html).toContain("The last refresh failed, so the organization pool figure below is from");
  });

  it("stops rewriting the kept figure once it is older than the probe's 30 minutes", async () => {
    const h = harness();
    await h.controller.refresh(OCT_5);
    h.setMode({ personal: 200, org: 503 });
    await h.controller.refresh(OCT_5 + 5 * 60_000);
    const before = fs.readFileSync(h.statePath, "utf-8");
    await h.controller.refresh(OCT_5 + 31 * 60_000);
    expect(fs.readFileSync(h.statePath, "utf-8")).toBe(before);
    expect(writeUsageState(h.store.get(), h.statePath, OCT_5 + 31 * 60_000)).toBe("skipped");
    expect(buildUsageState(h.store.get(), OCT_5 + 31 * 60_000)).toBe("too-old");
  });

  it.each<[string, Mode]>([
    ["a rejected token", { personal: 200, org: 401 }],
    ["access denied", { personal: 200, org: 403 }],
  ])("drops the pool after %s, falling back to the member view and removing the file", async (_name, failing) => {
    const h = harness();
    await h.controller.refresh(OCT_5);
    h.setMode(failing);
    await h.controller.refresh(OCT_5 + 60_000);
    expect(h.store.get()!.organization).toBeUndefined();
    expect(h.item().text).toContain("--% (month)");
    expect(h.state()).toBeNull();
  });

  it("keeps a personal figure, marked stale, when only the personal half fails transiently", () => {
    const previous = { personal: { planLabel: "Copilot Free", quotas: [], primary: null, creditsUsed: 0, resetsAt: null, fetchedAt: 1 }, lastUpdated: 1, dataSource: "api" as const };
    const next = { personalError: { code: "network-error" }, organization: undefined, lastUpdated: 2, dataSource: "api" as const };
    expect(retainTransient(next, previous).personal).toMatchObject({ stale: true, fetchedAt: 1 });
    expect(retainTransient({ ...next, personalError: { code: "token-invalid" } }, previous).personal).toBeUndefined();
    const noStamp = { ...previous, personal: { ...previous.personal, fetchedAt: undefined } };
    expect(retainTransient(next, noStamp).personal!.fetchedAt).toBe(1);
  });

  it("a fresh success clears the stale mark", async () => {
    const h = harness();
    await h.controller.refresh(OCT_5);
    h.setMode({ personal: 200, org: 429 });
    await h.controller.refresh(OCT_5 + 60_000);
    h.setMode({ personal: 200, org: 200, usage: "ai-credit-usage.json" });
    await h.controller.refresh(OCT_5 + 120_000);
    expect(h.store.get()!.organization!.stale).toBeUndefined();
    expect(h.state().stale).toBeUndefined();
    expect(h.state().windows[0].percent).toBe(0.01);
  });
});

describe("F6: settings scopes and the refresh interval", () => {
  it("scopes the security- and display-relevant settings to the application", () => {
    const pkg = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "package.json"), "utf-8"));
    const props = pkg.contributes.configuration.properties as Record<string, { scope?: string }>;
    for (const key of [
      "copilotUsage.organization",
      "copilotUsage.writeUsageState",
      "copilotUsage.thresholds.moderate",
      "copilotUsage.thresholds.high",
      "copilotUsage.thresholds.critical",
      "copilotUsage.colors.moderate",
      "copilotUsage.colors.high",
      "copilotUsage.colors.critical",
    ]) {
      expect(props[key].scope, key).toBe("application");
    }
  });

  it.each([
    [0, 1],
    [-5, 1],
    [0.5, 1],
    [500, 120],
    [30, 30],
    ["10", 10],
    [Number.NaN, 10],
    [undefined, 10],
  ])("clamps refreshInterval %s to %s minutes", (raw, minutes) => {
    __setStubConfig("copilotUsage", "refreshInterval", raw);
    expect(getRefreshIntervalMinutes()).toBe(minutes);
  });

  it("never schedules a refresh sooner than a minute", () => {
    __setStubConfig("copilotUsage", "refreshInterval", 0);
    const bar = new StatusBarManager(new UsageStore(createMemento()), "x");
    expect(bar.computeRefreshDelayMs()).toBe(60_000);
  });
});

describe("F7: sign-out removes the state file; the rename retries on Windows", () => {
  it.each([
    ["no-credentials", () => new FakeGitHubAuth([])],
    ["choose-account", () => new FakeGitHubAuth([{ id: "a", label: "a", token: WORK_TOKEN }, { id: "b", label: "b", token: PERSONAL_TOKEN }])],
  ])("removes the file on %s when no organization figure is cached", async (_code, makeAuth) => {
    __setAuthentication(new FakeGitHubAuth([{ id: "p", label: "p", token: PERSONAL_TOKEN }]));
    const fake = routedFetch(() => jsonResponse(fixture("copilot-internal-user.personal.json")));
    const store = new UsageStore(createMemento());
    const statePath = path.join(dir, "copilot.json");
    const surface = { refresh() {}, setLastError() {}, applyBackoff() {}, resetBackoff() {} };
    const controller = new UsageController(store, new UsageService(new CopilotUsageProvider(undefined, fake.fetch), new CopilotOrganizationProvider(new FakeSecretStorage().asSecretStorage())), surface, statePath);
    await controller.refresh(OCT_5);
    expect(fs.existsSync(statePath)).toBe(true);
    __setAuthentication(makeAuth());
    await controller.refresh(OCT_5 + 60_000);
    expect(fs.existsSync(statePath)).toBe(false);
  });

  it("removes the file on token-invalid when only a personal figure is cached", async () => {
    __setAuthentication(new FakeGitHubAuth([{ id: "p", label: "p", token: PERSONAL_TOKEN }]));
    let status = 200;
    const fake = routedFetch(() => (status === 200 ? jsonResponse(fixture("copilot-internal-user.personal.json")) : jsonResponse({}, status)));
    const statePath = path.join(dir, "copilot.json");
    const surface = { refresh() {}, setLastError() {}, applyBackoff() {}, resetBackoff() {} };
    const controller = new UsageController(new UsageStore(createMemento()), new UsageService(new CopilotUsageProvider(undefined, fake.fetch), new CopilotOrganizationProvider(new FakeSecretStorage().asSecretStorage())), surface, statePath);
    await controller.refresh(OCT_5);
    expect(fs.existsSync(statePath)).toBe(true);
    status = 503;
    await controller.refresh(OCT_5 + 60_000);
    expect(fs.existsSync(statePath)).toBe(true);
    status = 401;
    await controller.refresh(OCT_5 + 120_000);
    expect(fs.existsSync(statePath)).toBe(false);
  });

  it("keeps the file on token-invalid when a pool figure is cached", async () => {
    const h = harness();
    await h.controller.refresh(OCT_5);
    // Personal 401 and organization 503: the whole fetch fails, the cached pool stays.
    h.setMode({ personal: 401, org: 503 });
    await h.controller.refresh(OCT_5 + 60_000);
    expect(h.controller.lastFetchError?.code).toBe("token-invalid");
    expect(h.state()).not.toBeNull();

    __setStubConfig("copilotUsage", "organization", "");
    await h.controller.organizationRemoved();
    await h.controller.refresh(OCT_5 + 120_000);
    expect(h.state()).toBeNull();
  });

  function eperm(): NodeJS.ErrnoException {
    return Object.assign(new Error("operation not permitted"), { code: "EPERM" });
  }

  it("retries the rename once after EPERM on Windows", () => {
    let calls = 0;
    const file = path.join(dir, "copilot.json");
    const io = {
      platform: "win32" as const,
      rename(from: string, to: string) {
        calls += 1;
        if (calls === 1) throw eperm();
        fs.renameSync(from, to);
      },
    };
    expect(writeUsageState(fixtureDataWithPercent(), file, OCT_5, io)).toBe("written");
    expect(calls).toBe(2);
    expect(fs.readdirSync(dir)).toEqual(["copilot.json"]);
  });

  it("gives up after a second EPERM, and does not retry on other platforms or other errors", () => {
    const file = path.join(dir, "copilot.json");
    let calls = 0;
    const always = { platform: "win32" as const, rename() { calls += 1; throw eperm(); } };
    expect(writeUsageState(fixtureDataWithPercent(), file, OCT_5, always)).toBe("failed");
    expect(calls).toBe(2);
    calls = 0;
    expect(writeUsageState(fixtureDataWithPercent(), file, OCT_5, { ...always, platform: "linux" })).toBe("failed");
    expect(calls).toBe(1);
    calls = 0;
    const enoent = { platform: "win32" as const, rename() { calls += 1; throw Object.assign(new Error("x"), { code: "ENOENT" }); } };
    expect(writeUsageState(fixtureDataWithPercent(), file, OCT_5, enoent)).toBe("failed");
    expect(calls).toBe(1);
    expect(fs.readdirSync(dir)).toEqual([]);
  });
});

function fixtureDataWithPercent() {
  const quota = { id: "chat", label: "Chat", percent: 10, entitlement: 100, remaining: 90 };
  return {
    personal: { planLabel: "Copilot Free", quotas: [quota], primary: quota, creditsUsed: 0, resetsAt: null, fetchedAt: OCT_5 },
    lastUpdated: OCT_5,
    dataSource: "api" as const,
  };
}
