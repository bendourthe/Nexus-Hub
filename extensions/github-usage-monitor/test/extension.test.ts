import { beforeEach, describe, expect, it, vi } from "vitest";
import { activate, deactivate, fetchConfiguredUsage, setDeferToNewerWindow } from "../src/extension";
import { GitHubTokenStore } from "../src/providers/auth";
import { UsageStore } from "../src/usageStore";
import {
  fireConfigChange,
  messages,
  openedExternals,
  queueInput,
  resetVscodeStub,
  runCommand,
  setConfiguration,
  Uri,
  stubExtension,
  webviewPanels
} from "./vscode-stub";

class FakeSecrets {
  public values = new Map<string, string>();

  public async get(key: string): Promise<string | undefined> {
    return this.values.get(key);
  }

  public async store(key: string, value: string): Promise<void> {
    this.values.set(key, value);
  }

  public async delete(key: string): Promise<void> {
    this.values.delete(key);
  }
}

const context = (secretStorage: FakeSecrets) => {
  const values = new Map<string, unknown>();
  return {
    secrets: secretStorage,
    subscriptions: [],
    extension: stubExtension(),
    extensionUri: Uri.file("fixture-extension"),
    globalState: {
      get<T>(key: string, fallback?: T): T | undefined {
        return (values.has(key) ? values.get(key) : fallback) as T | undefined;
      },
      async update(key: string, value: unknown): Promise<void> {
        if (value === undefined) values.delete(key);
        else values.set(key, value);
      }
    }
  };
};

describe("extension authentication commands", () => {
  let secrets: FakeSecrets;

  beforeEach(async () => {
    resetVscodeStub();
    secrets = new FakeSecrets();
    setConfiguration("githubUsageMonitor.billingScope", "user");
    setConfiguration("githubUsageMonitor.billingOwner", "fixture-user");
    setConfiguration("githubUsageMonitor.autoFetch", false);
    await activate(context(secrets) as never);
    vi.stubGlobal("fetch", vi.fn());
  });

  it("registers clear-token and removes only the SecretStorage value", async () => {
    secrets.values.set("githubUsageMonitor.token", "fixture-token-value-123456789");
    await runCommand("githubUsageMonitor.clearToken");
    expect(secrets.values.size).toBe(0);
    expect(messages.information).toContain("GitHub billing token removed from SecretStorage.");
  });

  it("rejects set-token when owner configuration is invalid", async () => {
    resetVscodeStub();
    setConfiguration("githubUsageMonitor.billingScope", "user");
    setConfiguration("githubUsageMonitor.billingOwner", "");
    setConfiguration("githubUsageMonitor.autoFetch", false);
    await activate(context(secrets) as never);
    await runCommand("githubUsageMonitor.setToken");
    expect(messages.errors[0]).toContain("valid GitHub user name");
  });

  it("does nothing when the secret prompt is cancelled", async () => {
    queueInput(undefined);
    await runCommand("githubUsageMonitor.rotateToken");
    expect(secrets.values.size).toBe(0);
    expect(messages.errors).toEqual([]);
  });

  it("reports a missing stored token during validation", async () => {
    await runCommand("githubUsageMonitor.validateToken");
    expect(messages.errors[0]).toContain("No GitHub billing token");
  });

  it("exports a no-op deactivation hook", () => {
    expect(deactivate()).toBeUndefined();
  });
});

describe("activation command surface", () => {
  let secrets: FakeSecrets;
  let host: ReturnType<typeof context>;

  beforeEach(async () => {
    resetVscodeStub();
    secrets = new FakeSecrets();
    setConfiguration("githubUsageMonitor.billingScope", "user");
    setConfiguration("githubUsageMonitor.billingOwner", "fixture-user");
    setConfiguration("githubUsageMonitor.autoFetch", false);
    host = context(secrets);
    await activate(host as never);
    vi.stubGlobal("fetch", vi.fn());
  });

  it("refresh while signed out stays on the connect prompt and does not fetch", async () => {
    await host.globalState.update("githubUsageMonitor.signedOut", true);
    await runCommand("githubUsageMonitor.refresh");
    expect(vi.mocked(fetch).mock.calls).toHaveLength(0);
  });

  it("refresh without a stored token does not throw", async () => {
    await expect(runCommand("githubUsageMonitor.refresh")).resolves.toBeUndefined();
  });

  it("settings reveals the dashboard panel", async () => {
    await runCommand("githubUsageMonitor.settings");
    expect(webviewPanels.length).toBeGreaterThan(0);
  });

  it("clearData empties the current snapshot", async () => {
    await runCommand("githubUsageMonitor.clearData");
    expect(host.globalState.get("githubUsageMonitor.snapshot")).toBeUndefined();
  });

  it("diagnoseAuth is a no-op when no owner is configured", async () => {
    resetVscodeStub();
    secrets = new FakeSecrets();
    setConfiguration("githubUsageMonitor.billingScope", "user");
    setConfiguration("githubUsageMonitor.billingOwner", "");
    setConfiguration("githubUsageMonitor.autoFetch", false);
    await activate(context(secrets) as never);
    await expect(runCommand("githubUsageMonitor.diagnoseAuth")).resolves.toBeUndefined();
  });

  it("openBillingPage opens GitHub's personal billing URL when no owner is resolved", async () => {
    resetVscodeStub();
    secrets = new FakeSecrets();
    setConfiguration("githubUsageMonitor.billingScope", "user");
    setConfiguration("githubUsageMonitor.billingOwner", "");
    setConfiguration("githubUsageMonitor.autoFetch", false);
    await activate(context(secrets) as never);
    await runCommand("githubUsageMonitor.openBillingPage");
    expect(openedExternals[0]).toContain("github.com/settings/billing");
  });

  it("fetchConfiguredUsage reports invalid-scope when no owner can be resolved", async () => {
    resetVscodeStub();
    setConfiguration("githubUsageMonitor.billingScope", "user");
    setConfiguration("githubUsageMonitor.billingOwner", "");
    const tokens = new GitHubTokenStore(secrets);
    const store = new UsageStore(host.globalState);
    const state = await fetchConfiguredUsage(tokens, store);
    expect(state.state).toBe("empty");
    expect(state.error?.code).toBe("invalid-scope");
  });

  it("a billing-owner configuration change triggers refresh without throwing", () => {
    expect(() => fireConfigChange(["githubUsageMonitor.billingOwner"])).not.toThrow();
  });

  it("setDeferToNewerWindow is a no-throw toggle", () => {
    setDeferToNewerWindow(true);
    setDeferToNewerWindow(false);
  });
});
