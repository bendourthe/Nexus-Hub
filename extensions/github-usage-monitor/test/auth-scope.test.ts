import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  GitHubTokenStore,
  validateTokenSyntax,
  vscodeGitHubSessionProbe,
  type SecretStorageLike
} from "../src/providers/auth";
import {
  billingEndpoint,
  copilotEndpointSuffix,
  managedCopilotScopeError,
  permissionError,
  requiredPermission,
  resolveBillingOwner
} from "../src/providers/scope";
import type { ProviderResult } from "../src/types";

class FakeSecrets implements SecretStorageLike {
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

const rate = { remaining: 42, resetAt: null, retryAfterMs: null };
const validToken = "fixture-token-value-123456789";

describe("GitHubTokenStore", () => {
  let secrets: FakeSecrets;
  let store: GitHubTokenStore;

  beforeEach(() => {
    secrets = new FakeSecrets();
    store = new GitHubTokenStore(secrets);
  });

  it("stores only a validated normalized token", async () => {
    const validator = vi.fn(async (): Promise<ProviderResult<void>> => ({ ok: true, value: undefined, rate }));
    await expect(store.setToken(`  ${validToken}  `, validator)).resolves.toEqual({ ok: true });
    expect(validator).toHaveBeenCalledWith(validToken);
    expect(secrets.values.get("githubUsage.token")).toBe(validToken);
    await expect(store.hasToken()).resolves.toBe(true);
  });

  it("rejects invalid syntax without invoking the validator", async () => {
    const validator = vi.fn();
    const result = await store.setToken("short token", validator);
    expect(result.ok).toBe(false);
    expect(validator).not.toHaveBeenCalled();
    expect(secrets.values.size).toBe(0);
  });

  it("preserves the prior token when rotation validation fails", async () => {
    secrets.values.set("githubUsage.token", "existing-fixture-value-123456789");
    const error = { code: "missing-plan-read" as const, message: "missing permission" };
    const result = await store.rotateToken(validToken, async () => ({ ok: false, error, rate }));
    expect(result).toEqual({ ok: false, error });
    expect(secrets.values.get("githubUsage.token")).toBe("existing-fixture-value-123456789");
  });

  it("validates and clears an existing token", async () => {
    secrets.values.set("githubUsage.token", validToken);
    await expect(store.validateToken(async () => ({ ok: true, value: undefined, rate }))).resolves.toEqual({ ok: true });
    await store.clearToken();
    await expect(store.hasToken()).resolves.toBe(false);
  });

  it("returns a typed missing-token error without exposing a value", async () => {
    const operation = vi.fn();
    const result = await store.withToken(operation);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error.code).toBe("missing-token");
    }
    expect(operation).not.toHaveBeenCalled();
  });

  it("returns validator failures from validateToken", async () => {
    secrets.values.set("githubUsage.token", validToken);
    const error = { code: "invalid-token" as const, message: "rejected" };
    await expect(store.validateToken(async () => ({ ok: false, error, rate }))).resolves.toEqual({ ok: false, error });
  });
});

describe("token and session policy", () => {
  it.each(["", "tiny", "github token with spaces 123456789", `fixture-token-value-123456789\n`])(
    "rejects unsafe token syntax: %j",
    (token) => expect(validateTokenSyntax(token)?.code).toBe("invalid-token")
  );

  it("accepts evolving opaque token prefixes", () => {
    expect(validateTokenSyntax("future_token_format_1234567890")).toBeNull();
  });

  it("keeps VS Code GitHub sessions disabled until billing acceptance is proven", () => {
    expect(vscodeGitHubSessionProbe()).toEqual(expect.objectContaining({ supported: false }));
  });
});

describe("billing scope", () => {
  it.each([
    ["user", "/users/fixture-user/settings/billing/usage", "Plan: read"],
    ["organization", "/organizations/fixture-org/settings/billing/usage", "Administration: read"],
    ["enterprise", "/enterprises/fixture-enterprise/settings/billing/usage", "enterprise owner"]
  ] as const)("resolves %s scope", (scope, endpoint, permission) => {
    const result = resolveBillingOwner(scope, `fixture-${scope === "organization" ? "org" : scope}`);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(billingEndpoint(result.owner, "usage")).toBe(endpoint);
      expect(requiredPermission(result.owner)).toContain(permission);
      expect(permissionError(result.owner).requiredPermission).toContain(permission);
    }
  });

  it.each([
    ["workspace", "fixture"],
    ["user", ""],
    ["organization", "-bad"],
    ["organization", "bad--slug"],
    ["enterprise", "bad slug"]
  ])("rejects invalid scope input", (scope, name) => {
    expect(resolveBillingOwner(scope, name)).toEqual(expect.objectContaining({ ok: false }));
  });

  it("encodes owner names and maps Copilot endpoints", () => {
    expect(billingEndpoint({ scope: "user", name: "fixture-user" }, "ai_credit/usage")).toContain("fixture-user");
    expect(copilotEndpointSuffix("ai-credits")).toBe("ai_credit/usage");
    expect(copilotEndpointSuffix("premium-requests")).toBe("premium_request/usage");
    expect(managedCopilotScopeError().code).toBe("managed-copilot-personal-scope");
  });
});
