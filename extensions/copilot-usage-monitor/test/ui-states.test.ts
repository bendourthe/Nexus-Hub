import { afterEach, describe, expect, it, vi } from "vitest";
import { DashboardPanel } from "../src/dashboardPanel";
import { mapCopilotUser } from "../src/providers/copilot";
import { mapOrganizationUsage } from "../src/providers/copilotOrganization";
import { StatusBarManager, statusText } from "../src/statusBarManager";
import { BAR_FILL, type UsageData } from "../src/types";
import { UsageStore } from "../src/usageStore";
import { createMemento, fixture } from "./helpers";
import {
  __resetStubState,
  __setStubConfig,
  createdStatusBarItems,
  createdWebviewPanels,
  window,
  type StubWebviewPanel,
} from "./vscode-stub";

const NOW = Date.UTC(2026, 9, 2, 0, 5);
const callbacks = () => ({
  onRefresh: vi.fn(),
  onOpenUsagePage: vi.fn(),
  onSignIn: vi.fn(),
  onSwitchAccount: vi.fn(),
  onConnectOrganization: vi.fn(),
  onDisconnectOrganization: vi.fn(),
});

const personalFree = (): UsageData => ({
  personal: mapCopilotUser(fixture("copilot-internal-user.personal.json"))!,
  lastUpdated: Date.now(),
  dataSource: "api",
});
const businessMember = (): UsageData => ({
  personal: mapCopilotUser(fixture("copilot-internal-user.business-member.json"))!,
  lastUpdated: Date.now(),
  dataSource: "api",
});
const orgPool = (usage: string, billing = "copilot-billing.json"): UsageData => ({
  ...businessMember(),
  organization: mapOrganizationUsage(fixture(billing), fixture(usage), NOW)!,
});

/** The five account states the plan's verification names, with the expected status-bar text. */
const STATES: Array<[string, () => UsageData, string]> = [
  ["personal Copilot Free", personalFree, "0% (month)"],
  ["Business member without billing access", businessMember, "0.00 credits used"],
  ["organization pool 0.907 of 13,300", () => orgPool("ai-credit-usage.json"), "0.01% (pool)"],
  ["organization pool near the limit", () => orgPool("ai-credit-usage.near-limit.synthetic.json"), "99.25% (pool)"],
  ["organization pool exhausted", () => orgPool("ai-credit-usage.over-pool.synthetic.json"), "100% (pool)"],
  ["organization pool, seat added", () => orgPool("ai-credit-usage.json", "copilot-billing.seat-added.synthetic.json"), "~0.01% (pool)"],
];

function storeWith(data: UsageData | undefined): UsageStore {
  const store = new UsageStore(createMemento());
  if (data) void store.save(data);
  return store;
}

function dashboard(data: UsageData | undefined, error?: Parameters<typeof DashboardPanel.show>[2], org = { configured: false, connected: false }) {
  const cb = callbacks();
  DashboardPanel.show(data, "just now", error, org, cb);
  return { html: (createdWebviewPanels.at(-1) as StubWebviewPanel).webview.html, cb, panel: createdWebviewPanels.at(-1)! };
}

afterEach(() => {
  for (const panel of createdWebviewPanels) panel.dispose();
  __resetStubState();
});

describe("status bar per account state", () => {
  it("creates one item at priority 101, to the left of GitHub Copilot's own item", () => {
    new StatusBarManager(storeWith(undefined), "copilot-usage.dashboard");
    expect(createdStatusBarItems).toHaveLength(1);
    expect(createdStatusBarItems[0].priority).toBe(101);
    expect(createdStatusBarItems[0].command).toBe("copilot-usage.dashboard");
  });

  it.each(STATES)("%s", (_name, make, body) => {
    const mgr = new StatusBarManager(storeWith(make()), "copilot-usage.dashboard");
    mgr.refresh();
    expect(createdStatusBarItems[0].text).toBe(`$(copilot-icon)\u2002Copilot Usage: ${body}`);
  });

  it("drops the label in compact mode and shows -- with no data", () => {
    __setStubConfig("copilotUsage", "compactStatusBar", true);
    expect(statusText(orgPool("ai-credit-usage.near-limit.synthetic.json"), true)).toBe("$(copilot-icon)\u200299.25% (pool)");
    const mgr = new StatusBarManager(storeWith(undefined), "x");
    mgr.refresh();
    expect(createdStatusBarItems[0].text).toBe("$(copilot-icon)\u2002--");
  });

  it("never shows a percent sign for the member state", () => {
    const mgr = new StatusBarManager(storeWith(businessMember()), "x");
    mgr.refresh();
    expect(createdStatusBarItems[0].text).not.toContain("%");
    expect((createdStatusBarItems[0].tooltip as { value: string }).value).toContain("No personal limit is set for this seat.");
  });

  it("colors the item by the headline's urgency: critical near the limit, none when low", () => {
    const near = new StatusBarManager(storeWith(orgPool("ai-credit-usage.near-limit.synthetic.json")), "x");
    near.refresh();
    expect(createdStatusBarItems[0].backgroundColor).toEqual({ id: "statusBarItem.errorBackground" });
    const low = new StatusBarManager(storeWith(personalFree()), "x");
    low.refresh();
    expect(createdStatusBarItems[1].backgroundColor).toBeUndefined();
    __setStubConfig("copilotUsage", "colors.critical", "none");
    near.refresh();
    expect(createdStatusBarItems[0].backgroundColor).toBeUndefined();
  });

  it("draws teal tooltip bars, an approximate total, and the reset date", () => {
    window.activeColorTheme = { kind: 2 };
    const mgr = new StatusBarManager(storeWith(orgPool("ai-credit-usage.json", "copilot-billing.seat-added.synthetic.json")), "x");
    mgr.refresh();
    const tooltip = (createdStatusBarItems[0].tooltip as { value: string }).value;
    expect(decodeURIComponent(tooltip)).toContain(`fill="${BAR_FILL}"`);
    expect(tooltip).toContain("0.91 of 15,200 credits used (approximate total)");
    expect(tooltip).toContain("Resets on November 1");
    expect(tooltip).toContain("Copilot Business: 0.00 credits used this month");
  });

  it("lists every personal quota in the tooltip, and the pool without a seat count", () => {
    const data = personalFree();
    data.organization = mapOrganizationUsage({}, fixture("ai-credit-usage.json"), NOW)!;
    const mgr = new StatusBarManager(storeWith(data), "x");
    mgr.refresh();
    const tooltip = (createdStatusBarItems[0].tooltip as { value: string }).value;
    expect(tooltip).toContain("Organization pool: 0.91 credits used (no seat count to compare against)");
    expect(decodeURIComponent(tooltip)).toContain(">Chat<");
    expect(decodeURIComponent(tooltip)).toContain(">Code completions<");
    expect(createdStatusBarItems[0].text).toContain("0% (month)");
  });

  it("marks stale data and explains an empty bar after a sign-in or account error", () => {
    const stale = { ...personalFree(), lastUpdated: Date.now() - 3 * 60 * 60_000 };
    const mgr = new StatusBarManager(storeWith(stale), "x");
    mgr.refresh();
    expect(createdStatusBarItems[0].text).toContain(" $(warning)");
    expect((createdStatusBarItems[0].tooltip as { value: string }).value).toContain("Data may be stale");

    const empty = new StatusBarManager(storeWith(undefined), "x");
    empty.setLastError({ code: "no-credentials" });
    empty.refresh();
    expect(createdStatusBarItems[1].tooltip).toContain("Sign in to GitHub");
    empty.setLastError({ code: "network-error" });
    empty.refresh();
    expect(createdStatusBarItems[1].tooltip).toBe("Click to view the Copilot usage dashboard");
    empty.showLoading();
    expect(createdStatusBarItems[1].text).toContain("Refreshing");
  });

  it("polls every minute near the moderate threshold and backs off when rate-limited", () => {
    const near = new StatusBarManager(storeWith(orgPool("ai-credit-usage.near-limit.synthetic.json")), "x");
    expect(near.computeRefreshDelayMs()).toBe(60_000);
    const member = new StatusBarManager(storeWith(businessMember()), "x");
    expect(member.computeRefreshDelayMs()).toBe(600_000);
    member.applyBackoff();
    expect(member.computeRefreshDelayMs()).toBe(1_200_000);
    member.resetBackoff();
    expect(member.computeRefreshDelayMs()).toBe(600_000);
    member.show();
    member.hide();
    member.dispose();
  });
});

describe("dashboard per account state", () => {
  it("personal Copilot Free: plan name and one teal bar per served quota", () => {
    const { html } = dashboard(personalFree());
    expect(html).toContain("<h2>Copilot Usage Dashboard</h2>");
    expect(html).toContain('<div class="model-name">Copilot Free</div>');
    expect(html).toContain("<h3>Chat</h3>");
    expect(html).toContain("<h3>Code completions</h3>");
    expect(html).toContain("0 of 200 used");
    expect(html).toContain("0 of 2,000 used");
    expect(html).not.toContain("Premium requests");
    expect(html).toContain(`background: ${BAR_FILL};`);
    expect(html).toContain("Resets on November 1");
  });

  it("Business member: credits used, the one-sentence explanation, and no percentage", () => {
    const { html } = dashboard(businessMember());
    expect(html).toContain("<h3>Copilot Business</h3>");
    expect(html).toContain("0.00 credits used this month");
    expect(html).toContain(
      "Your organization shares one pool of AI credits and sets no personal limit for this seat, so there is no percentage to show.",
    );
    expect(html).not.toContain('class="progress-label"');
    expect(html).toContain("GitHub sets no personal limit for this seat");
  });

  it("organization pool: both bars, seat arithmetic, the rounding note, and the scope note", () => {
    const data = { ...orgPool("ai-credit-usage.json"), personal: personalFree().personal };
    const { html } = dashboard(data);
    expect(html).toContain("<h3>Organization Pool</h3>");
    expect(html).toContain('<span class="progress-label">0.01%</span>');
    expect(html).toContain("0.91 of 13,300 credits used");
    expect(html).toContain("7 Business seats x 1,900 credits per seat.");
    expect(html).toContain("rounds its headline to a whole number");
    expect(html).toContain("Covers this organization only.");
    expect(html).toContain("Auto: GPT-6 Luna: 0.91 credits");
    expect(html.indexOf("Organization Pool")).toBeLessThan(html.indexOf("Copilot Free"));
  });

  it("near the limit and exhausted: the percentage and a critical recommendation", () => {
    const near = dashboard(orgPool("ai-credit-usage.near-limit.synthetic.json")).html;
    expect(near).toContain('<span class="progress-label">99.25%</span>');
    expect(near).toContain("13,200.00 of 13,300 credits used");
    expect(near).toContain("urgency-critical");
    expect(near).toContain("Organization pool at 99.25%. Pause non-essential Copilot work, or ask an owner about additional usage. It resets on November 1.");
    const over = dashboard(orgPool("ai-credit-usage.over-pool.synthetic.json")).html;
    expect(over).toContain('<span class="progress-label">100%</span>');
    expect(over).toContain("13,300.00 of 13,300 credits used");
  });

  it("labels an approximate total", () => {
    const { html } = dashboard(orgPool("ai-credit-usage.json", "copilot-billing.seat-added.synthetic.json"));
    expect(html).toContain("<h3>Organization Pool (approximate)</h3>");
    expect(html).toContain('<span class="progress-label">~0.01%</span>');
    expect(html).toContain("0.91 of 15,200 credits used, approximate total");
    expect(html).toContain("GitHub does not publish how an added seat is prorated");
  });

  it("shows a pending-cancellation note and a pool without a seat count", () => {
    const billing = { plan_type: "business", seat_breakdown: { total: 1, pending_cancellation: 1 } };
    const data: UsageData = { organization: mapOrganizationUsage(billing, fixture("ai-credit-usage.json"), NOW)!, lastUpdated: NOW, dataSource: "api" };
    expect(dashboard(data).html).toContain("pending cancellation");
    const noSeats: UsageData = { organization: mapOrganizationUsage({}, { timePeriod: { year: 2026, month: 10 }, usageItems: [] }, NOW)!, lastUpdated: NOW, dataSource: "api" };
    const html = dashboard(noSeats).html;
    expect(html).toContain("GitHub reported no Copilot seats");
    expect(html).not.toContain('class="progress-label"');
  });

  it("renders the empty states with the right primary action", () => {
    expect(dashboard(undefined, { code: "no-credentials" }).html).toContain(">Sign in to GitHub</button>");
    expect(dashboard(undefined, { code: "token-invalid", statusCode: 401 }).html).toContain(">Sign in to GitHub</button>");
    expect(dashboard(undefined, { code: "choose-account" }).html).toContain(">Choose GitHub account</button>");
    expect(dashboard(undefined, { code: "rate-limited" }).html).toContain("rate-limiting usage requests right now");
    expect(dashboard(undefined, undefined).html).toContain("No Copilot usage fetched yet");
    const failing = dashboard(undefined, { code: "api-error", statusCode: 503, statusText: "Unavailable" }).html;
    expect(failing).toContain('class="error-banner"');
    expect(failing).toContain("503 Unavailable");
  });

  it("keeps the personal view when the organization half fails, with the right action", () => {
    const access = { ...personalFree(), organizationError: { code: "org-access-denied", statusCode: 403 } };
    const html = dashboard(access).html;
    expect(html).toContain("This needs a read-only token from an organization owner or billing manager.");
    expect(html).toContain("Copilot Free");
    const rejected = { ...personalFree(), organizationError: { code: "org-token-rejected", statusCode: 401 } };
    expect(dashboard(rejected).html).toContain('data-command="connectOrganization" class="retry-btn">Reconnect');
    const partialPersonal = { ...orgPool("ai-credit-usage.json"), personal: undefined, personalError: { code: "choose-account" } };
    expect(dashboard(partialPersonal).html).toContain(">Choose GitHub account</button>");
    const signIn = { ...orgPool("ai-credit-usage.json"), personal: undefined, personalError: { code: "no-credentials" } };
    expect(dashboard(signIn).html).toContain("class=\"retry-btn\">Sign in to GitHub");
    const network = { ...personalFree(), organizationError: { code: "network-error" } };
    expect(dashboard(network).html).toContain('data-command="refresh" class="retry-btn">Retry');
    // A rate limit with cached data shows no banner.
    expect(dashboard(personalFree(), { code: "rate-limited" }).html).not.toContain('<div class="error-banner">');
  });

  it("settings: Organization section with Connect / Reconnect / Disconnect and the account switch", () => {
    const off = dashboard(personalFree()).html;
    expect(off).toContain("Not connected. The status bar shows your own plan.");
    expect(off).toContain('data-command="connectOrganization">Connect</button>');
    expect(off).toContain('data-command="disconnectOrganization" disabled>Disconnect');
    expect(off).toContain("Switch GitHub account");
    expect(off).not.toContain("metric-select");
    const on = dashboard(personalFree(), undefined, { configured: true, connected: true }).html;
    expect(on).toContain("Connected. The status bar shows the organization's shared pool.");
    expect(on).toContain(">Reconnect</button>");
    expect(dashboard(personalFree(), undefined, { configured: true, connected: false }).html).toContain("no token is stored");
  });

  it("routes every webview message to its callback and reuses the singleton panel", async () => {
    const { cb, panel } = dashboard(personalFree());
    for (const command of ["refresh", "openUsagePage", "signIn", "switchAccount", "connectOrganization", "disconnectOrganization"]) {
      await panel.webview.__dispatchMessage({ command });
    }
    expect(cb.onRefresh).toHaveBeenCalledOnce();
    expect(cb.onOpenUsagePage).toHaveBeenCalledOnce();
    expect(cb.onSignIn).toHaveBeenCalledOnce();
    expect(cb.onSwitchAccount).toHaveBeenCalledOnce();
    expect(cb.onConnectOrganization).toHaveBeenCalledOnce();
    expect(cb.onDisconnectOrganization).toHaveBeenCalledOnce();
    expect(panel.webview.postedMessages).toContainEqual({ command: "setLoading" });

    await panel.webview.__dispatchMessage({ command: "save", draft: { thresholds: { moderate: 40, high: 70, critical: 90 }, colors: { moderate: "#112233", high: "#445566", critical: "none" }, compact: true } });
    await panel.webview.__dispatchMessage({ command: "reset" });
    expect(panel.webview.postedMessages.filter((m) => (m as { command: string }).command === "loadSettings")).toHaveLength(2);

    DashboardPanel.show(businessMember(), "1 min ago", undefined, { configured: false, connected: false }, callbacks(), { path: "/ext" } as never);
    expect(createdWebviewPanels).toHaveLength(1);
    expect(panel.revealCount).toBe(1);
    expect(DashboardPanel.currentHtml()).toContain("Copilot Business");
    DashboardPanel.revealSettings();
    expect(panel.webview.postedMessages).toContainEqual({ command: "openSettings" });
    DashboardPanel.updateIfOpen(personalFree(), "2 min ago", undefined, { configured: true, connected: true });
    expect(DashboardPanel.currentHtml()).toContain("Connected.");
  });

  it("sets theme-adaptive tab icons from the extension folder", () => {
    DashboardPanel.show(personalFree(), "now", undefined, { configured: false, connected: false }, callbacks(), { path: "/ext" } as never);
    expect(createdWebviewPanels[0].iconPath).toEqual({
      light: { path: "/ext/icons/copilot-dark.svg" },
      dark: { path: "/ext/icons/copilot-light.svg" },
    });
    DashboardPanel.updateIfOpen(undefined, "never", undefined);
    expect(DashboardPanel.currentHtml()).toContain("No Usage Data");
  });

  it("updateIfOpen does nothing with no panel open", () => {
    expect(() => DashboardPanel.updateIfOpen(personalFree(), "now", undefined)).not.toThrow();
    expect(DashboardPanel.currentHtml()).toBeUndefined();
  });
});
