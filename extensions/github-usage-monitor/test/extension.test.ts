import { beforeEach, describe, expect, it, vi } from "vitest";
import { activate, deactivate } from "../src/extension";
import {
  messages,
  queueInput,
  resetVscodeStub,
  runCommand,
  setConfiguration,
  Uri,
  stubExtension
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
  const context = (secretStorage: FakeSecrets) => {
    const values = new Map<string, unknown>();
    return {
      secrets: secretStorage,
      subscriptions: [],
      extension: stubExtension(),
      extensionUri: Uri.file("fixture-extension"),
      globalState: {
        get<T>(key: string): T | undefined { return values.get(key) as T | undefined; },
        async update(key: string, value: unknown): Promise<void> { if (value === undefined) values.delete(key); else values.set(key, value); }
      }
    };
  };
