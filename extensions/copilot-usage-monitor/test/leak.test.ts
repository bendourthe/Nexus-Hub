import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { DashboardPanel } from "../src/dashboardPanel";
import { __resetLog } from "../src/log";
import { CopilotUsageProvider } from "../src/providers/copilot";
import { CopilotOrganizationProvider, ORG_TOKEN_SECRET_KEY, connectOrganization, disconnectOrganization } from "../src/providers/copilotOrganization";
import { describeProviderError } from "../src/providers/errors";
import type { ProviderFetchError } from "../src/providers/types";
import { buildUsageSuggestion } from "../src/recommendations";
import { StatusBarManager } from "../src/statusBarManager";
import { UsageController } from "../src/usageController";
import { UsageService } from "../src/usageService";
import { UsageStore } from "../src/usageStore";
import { WarningViewProvider } from "../src/warningView";
import {
  FakeGitHubAuth,
  FakeSecretStorage,
  ORG_TOKEN,
  PERSONAL_TOKEN,
  PLACEHOLDER_IDENTITIES,
  WORK_TOKEN,
  createMemento,
  fixture,
  jsonResponse,
  routedFetch,
  findLeaks,
  tokenSlices,
} from "./helpers";
import {
  __resetStubState,
  __setAuthentication,
  configurationUpdates,
  createdStatusBarItems,
  createdWebviewPanels,
  inputBoxAnswers,
  messageAnswers,
  messageOptions,
  outputLines,
  shownMessages,
} from "./vscode-stub";

/**
 * Plan 2.6 / DoD 3: no GitHub token appears in a log line, error message,
 * rendered view, settings write, cache entry, or the state file, and the
 * organization token is used only against api.github.com. The organization
 * login the user typed may appear only as the value of the
 * `copilotUsage.organization` setting.
 */
const ORG_LOGIN = "acme-co";
const TOKENS = [WORK_TOKEN, PERSONAL_TOKEN, ORG_TOKEN];
/** Whole tokens, their cores, every 12-character window, the identities, and auth-header fragments. */
const NEEDLES = [
  ...TOKENS.flatMap((token) => tokenSlices(token)),
  ...PLACEHOLDER_IDENTITIES,
  "Bearer",
  "token gho_",
  "personal-account",
  "work-id",
  "personal-id",
];

describe("the leak harness itself", () => {
  it("builds slice needles that cover every part of each token", () => {
    for (const token of TOKENS) {
      const slices = tokenSlices(token);
      expect(slices).toContain(token);
      expect(slices.some((s) => /^FAKE[A-Z]+$/.test(s))).toBe(true);
      expect(slices.filter((s) => s.length === 12).length).toBeGreaterThan(10);
    }
  });

  it.each([
    ["a 12-character slice", (t: string) => `prefix ${t.slice(6, 18)} suffix`],
    ["a truncated token", (t: string) => `token ${t.slice(0, 15)}...`],
    ["a masked token", (t: string) => `${t.slice(0, 4)}****${t.slice(4, 16)}`],
    ["the core alone", (t: string) => `id=${t.match(/FAKE[A-Z]+/)![0]}`],
  ])("catches %s planted in a surface", (_name, plant) => {
    for (const token of TOKENS) {
      expect(findLeaks(`clean text ${plant(token)} more text`, NEEDLES).length, token).toBeGreaterThan(0);
    }
    expect(findLeaks("0.91 of 13,300 credits used, Resets on November 1, 00000000000000", NEEDLES)).toEqual([]);
  });
});
const callbacks = {
  onRefresh: () => {},
  onOpenUsagePage: () => {},
  onSignIn: () => {},
  onSwitchAccount: () => {},
  onConnectOrganization: () => {},
  onDisconnectOrganization: () => {},
};

type Mode = { personal: number; billing: number; usage: string | number; offline?: boolean };

let dir: string;
beforeEach(() => {
  dir = fs.mkdtempSync(path.join(os.tmpdir(), "copilot-leak-"));
});
afterEach(() => {
  for (const panel of createdWebviewPanels) panel.dispose();
  __resetStubState();
  __resetLog();
  fs.rmSync(dir, { recursive: true, force: true });
});

describe("no token or identity leaks from any surface", () => {
  it("across sign-in, connect, every fetch outcome, rendering, the state file, and disconnect", async () => {
    let mode: Mode = { personal: 200, billing: 200, usage: "ai-credit-usage.near-limit.synthetic.json" };
    const fake = routedFetch((url, authorization) => {
      if (mode.offline) return "throw";
      if (url.pathname === "/copilot_internal/user") {
        if (mode.personal !== 200) return jsonResponse({ message: `Bad credentials ${authorization}` }, mode.personal);
        return jsonResponse(fixture(authorization === `token ${WORK_TOKEN}` ? "copilot-internal-user.business-member.json" : "copilot-internal-user.personal.json"));
      }
      // The organization refuses the VS Code session (third-party OAuth restricted),
      // so Connect falls back to the guided token on every attempt.
      if (authorization !== `Bearer ${ORG_TOKEN}`) return jsonResponse({ message: `denied ${authorization}` }, 403);
      if (url.pathname.endsWith("/copilot/billing")) {
        return mode.billing === 200 ? jsonResponse(fixture("copilot-billing.json")) : jsonResponse({ message: `denied ${authorization}` }, mode.billing);
      }
      if (typeof mode.usage === "number") return jsonResponse({ message: "nope" }, mode.usage);
      return jsonResponse(fixture(mode.usage));
    });

    const auth = new FakeGitHubAuth([
      { id: "work-id", label: "example-user", token: WORK_TOKEN },
      { id: "personal-id", label: "personal-account", token: PERSONAL_TOKEN },
    ]);
    auth.preference = "work-id";
    __setAuthentication(auth);
    const secrets = new FakeSecretStorage();
    const memento = createMemento();
    const store = new UsageStore(memento);
    const statusBar = new StatusBarManager(store, "copilot-usage.dashboard");
    const statePath = path.join(dir, "state", "usage-probe", "copilot.json");
    const controller = new UsageController(
      store,
      new UsageService(new CopilotUsageProvider(undefined, fake.fetch), new CopilotOrganizationProvider(secrets.asSecretStorage(), fake.fetch)),
      statusBar,
      statePath,
    );
    const warning = new WarningViewProvider();
    const warningWebview = { html: "", options: {}, cspSource: "x", onDidReceiveMessage() {} };
    warning.resolveWebviewView({ webview: warningWebview, onDidDispose() {}, show() {} } as never);

    const rendered: string[] = [];
    const errors: string[] = [];
    const stateFiles: string[] = [];
    const capture = async (): Promise<void> => {
      const item = createdStatusBarItems[0];
      rendered.push(String(item.text), JSON.stringify(item.tooltip));
      DashboardPanel.show(store.get(), "just now", controller.lastFetchError, { configured: true, connected: true }, callbacks);
      rendered.push(createdWebviewPanels[0].webview.html);
      const suggestion = buildUsageSuggestion(store.get());
      if (suggestion) {
        await warning.show(suggestion, "critical", { onOpenDashboard: () => {} });
        rendered.push(warningWebview.html);
      }
      const data = store.get();
      for (const e of [controller.lastFetchError, data?.organizationError, data?.personalError]) {
        if (e) errors.push(JSON.stringify(e), describeProviderError(e as ProviderFetchError));
      }
      if (fs.existsSync(statePath)) stateFiles.push(fs.readFileSync(statePath, "utf-8"));
    };

    // Connect: the work seat lists another organization, so pick Other, type the
    // login, then follow the guided token after the token-free route is refused.
    messageAnswers.push("Other organization", "Open GitHub");
    inputBoxAnswers.push(ORG_LOGIN, ORG_TOKEN);
    expect(await connectOrganization(secrets.asSecretStorage(), fake.fetch)).toBe("connected");
    await controller.refresh();
    await capture();
    expect(stateFiles.at(-1)).toContain('"percent": 99.25');

    // Every failure shape, one at a time.
    const outcomes: Mode[] = [
      { personal: 401, billing: 200, usage: "ai-credit-usage.json" },
      { personal: 429, billing: 403, usage: "ai-credit-usage.json" },
      { personal: 500, billing: 404, usage: "ai-credit-usage.json" },
      { personal: 200, billing: 200, usage: 502 },
      { personal: 200, billing: 200, usage: "ai-credit-usage.json", offline: true },
      { personal: 200, billing: 401, usage: "ai-credit-usage.json" },
    ];
    for (const outcome of outcomes) {
      mode = outcome;
      await controller.refresh();
      await capture();
    }
    expect(secrets.values.has(ORG_TOKEN_SECRET_KEY)).toBe(false);

    // Reconnect, refresh, switch to the personal account, then disconnect.
    mode = { personal: 200, billing: 200, usage: "ai-credit-usage.over-pool.synthetic.json" };
    messageAnswers.push("Other organization", "Open GitHub");
    inputBoxAnswers.push(ORG_LOGIN, ORG_TOKEN);
    await connectOrganization(secrets.asSecretStorage(), fake.fetch);
    await controller.refresh();
    await capture();
    auth.preference = "personal-id";
    await controller.refresh();
    await capture();
    await disconnectOrganization(secrets.asSecretStorage());
    await controller.organizationRemoved();
    await capture();
    // A connect attempt with a bad token stores nothing and says nothing identifying.
    // The personal seat lists no organization, so Connect goes straight to typing.
    mode = { personal: 200, billing: 401, usage: "ai-credit-usage.json" };
    messageAnswers.push("Open GitHub");
    inputBoxAnswers.push(ORG_LOGIN, ORG_TOKEN);
    expect(await connectOrganization(secrets.asSecretStorage(), fake.fetch)).toBe("rejected");

    const cache = JSON.stringify(memento.keys().map((k) => memento.get(k)));
    // Connect's modal confirmation names the seat's organization to the user by
    // design (v4.13.8 Phase 6); it is shown, never stored or logged. Every other
    // message is a leak surface.
    const isConnectConfirm = (i: number): boolean =>
      messageOptions[i]?.modal === true && shownMessages[i].message.startsWith("Connect ");
    expect(shownMessages.some((_m, i) => isConnectConfirm(i))).toBe(true);
    const messages = shownMessages.filter((_m, i) => !isConnectConfirm(i)).map((m) => m.message);
    const settingsOther = configurationUpdates.filter((u) => !(u.section === "copilotUsage" && u.key === "organization"));
    const settingsOrg = configurationUpdates.filter((u) => u.section === "copilotUsage" && u.key === "organization");

    const surfaces: Record<string, string> = {
      logs: outputLines.join("\n"),
      errors: errors.join("\n"),
      messages: messages.join("\n"),
      rendered: rendered.join("\n"),
      settings: JSON.stringify(configurationUpdates),
      cache,
      stateFiles: stateFiles.join("\n"),
    };
    expect(rendered.length).toBeGreaterThan(20);
    expect(errors.length).toBeGreaterThan(5);
    expect(stateFiles.length).toBeGreaterThan(2);
    for (const [surface, text] of Object.entries(surfaces)) {
      expect(findLeaks(text, NEEDLES), `leak in ${surface}`).toEqual([]);
    }
    // The typed organization login lives only in its own setting.
    for (const [surface, text] of Object.entries({ ...surfaces, settings: JSON.stringify(settingsOther) })) {
      expect(text.includes(ORG_LOGIN), `${ORG_LOGIN} found in ${surface}`).toBe(false);
    }
    expect(settingsOrg.map((u) => u.value)).toEqual([ORG_LOGIN, ORG_LOGIN, undefined, undefined, undefined]);
    // Secret storage holds the organization token under its single key, and nothing else.
    expect(new Set(secrets.stored.map((s) => s.key))).toEqual(new Set([ORG_TOKEN_SECRET_KEY]));

    // Tokens travel only to api.github.com: the organization token only to the
    // chosen organization's endpoints, and a session token to those only as the
    // token-free check during Connect.
    for (const call of fake.calls) {
      expect(new URL(call.url).origin).toBe("https://api.github.com");
      expect(call.init.redirect).toBe("error");
      if (call.url === "https://api.github.com/copilot_internal/user") {
        expect(call.authorization).not.toContain(ORG_TOKEN);
      } else {
        expect(call.url).toMatch(/^https:\/\/api\.github\.com\/(orgs|organizations)\/acme-co\//);
        expect(call.authorization?.startsWith("Bearer ")).toBe(true);
      }
    }
    expect(fake.calls.some((c) => c.authorization === `Bearer ${ORG_TOKEN}`)).toBe(true);
  });
});
