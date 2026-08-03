import { beforeEach, describe, expect, it, vi } from "vitest";
import { activate, deactivate } from "../src/extension";
import {
  messages,
  queueInput,
  resetVscodeStub,
  runCommand,
  setConfiguration
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

  beforeEach(() => {
    resetVscodeStub();
    secrets = new FakeSecrets();
    setConfiguration("githubUsage.billingScope", "user");
    setConfiguration("githubUsage.billingOwner", "fixture-user");
    activate({ secrets, subscriptions: [] } as never);
    vi.stubGlobal("fetch", vi.fn());
  });

  it("registers clear-token and removes only the SecretStorage value", async () => {
    secrets.values.set("githubUsage.token", "fixture-token-value-123456789");
    await runCommand("github-usage.clearToken");
    expect(secrets.values.size).toBe(0);
    expect(messages.information).toContain("GitHub billing token removed from SecretStorage.");
  });

  it("rejects set-token when owner configuration is invalid", async () => {
    resetVscodeStub();
    setConfiguration("githubUsage.billingScope", "user");
    setConfiguration("githubUsage.billingOwner", "");
    activate({ secrets, subscriptions: [] } as never);
    await runCommand("github-usage.setToken");
    expect(messages.errors[0]).toContain("valid GitHub user name");
  });

  it("does nothing when the secret prompt is cancelled", async () => {
    queueInput(undefined);
    await runCommand("github-usage.rotateToken");
    expect(secrets.values.size).toBe(0);
    expect(messages.errors).toEqual([]);
  });

  it("reports a missing stored token during validation", async () => {
    await runCommand("github-usage.validateToken");
    expect(messages.errors[0]).toContain("No GitHub billing token");
  });

  it("exports a no-op deactivation hook", () => {
    expect(deactivate()).toBeUndefined();
  });
});
