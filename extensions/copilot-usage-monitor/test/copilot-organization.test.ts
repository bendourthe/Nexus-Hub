import type * as vscode from "vscode";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  CopilotOrganizationProvider,
  ORG_ROUTE_SECRET_KEY,
  ORG_TOKEN_SECRET_KEY,
  configuredOrganization,
  disconnectOrganization,
  isValidOrganizationLogin,
} from "../src/providers/copilotOrganization";
import { FakeSecretStorage, ORG_TOKEN, fixtureFetch, jsonResponse, routedFetch } from "./helpers";
import { __resetStubState, __setStubConfig, configurationUpdates } from "./vscode-stub";

const OCT_2 = Date.UTC(2026, 9, 2, 0, 5);
const ORG = "acme-co";

function connected(): FakeSecretStorage {
  __setStubConfig("copilotUsage", "organization", ORG);
  const secrets = new FakeSecretStorage();
  secrets.values.set(ORG_TOKEN_SECRET_KEY, ORG_TOKEN);
  return secrets;
}

describe("CopilotOrganizationProvider", () => {
  afterEach(() => __resetStubState());

  it("is inactive while copilotUsage.organization is empty", () => {
    const p = new CopilotOrganizationProvider(new FakeSecretStorage().asSecretStorage());
    expect(p.isActive()).toBe(false);
    __setStubConfig("copilotUsage", "organization", "   ");
    expect(p.isActive()).toBe(false);
    expect(configuredOrganization()).toBe("");
    __setStubConfig("copilotUsage", "organization", ORG);
    expect(p.isActive()).toBe(true);
  });

  it("fetches seats then usage from api.github.com with the documented headers", async () => {
    const secrets = connected();
    const fake = fixtureFetch({ billing: "copilot-billing.json", usage: "ai-credit-usage.json" });
    const result = await new CopilotOrganizationProvider(secrets.asSecretStorage(), fake.fetch).fetchUsage(OCT_2);
    expect(result.success).toBe(true);
    expect(result.success && result.data.total).toBe(13_300);
    expect(fake.calls.map((c) => c.url)).toEqual([
      "https://api.github.com/orgs/acme-co/copilot/billing",
      "https://api.github.com/organizations/acme-co/settings/billing/ai_credit/usage?year=2026&month=10",
    ]);
    for (const call of fake.calls) {
      expect(call.authorization).toBe(`Bearer ${ORG_TOKEN}`);
      expect(call.init.redirect).toBe("error");
      expect(call.init.headers).toMatchObject({
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
      });
    }
  });

  it("reports org-not-connected with no stored token or an invalid login, without a request", async () => {
    __setStubConfig("copilotUsage", "organization", ORG);
    const fake = routedFetch(() => jsonResponse({}));
    const empty = new CopilotOrganizationProvider(new FakeSecretStorage().asSecretStorage(), fake.fetch);
    expect(await empty.fetchUsage()).toEqual({ success: false, error: { code: "org-not-connected" } });

    const broken = { get: () => Promise.reject(new Error("locked")) } as unknown as vscode.SecretStorage;
    expect(await new CopilotOrganizationProvider(broken, fake.fetch).fetchUsage())
      .toEqual({ success: false, error: { code: "org-not-connected" } });

    const secrets = connected();
    __setStubConfig("copilotUsage", "organization", "../evil");
    expect(await new CopilotOrganizationProvider(secrets.asSecretStorage(), fake.fetch).fetchUsage())
      .toEqual({ success: false, error: { code: "org-not-connected" } });
    expect(fake.calls).toHaveLength(0);
  });

  it("deletes an expired or revoked token on 401 and reports org-token-rejected", async () => {
    const secrets = connected();
    const fake = routedFetch(() => jsonResponse({ message: "Bad credentials" }, 401));
    const result = await new CopilotOrganizationProvider(secrets.asSecretStorage(), fake.fetch).fetchUsage(OCT_2);
    expect(!result.success && result.error.code).toBe("org-token-rejected");
    // The token and any token-free marker are both forgotten.
    expect(secrets.deleted).toEqual([ORG_TOKEN_SECRET_KEY, ORG_ROUTE_SECRET_KEY]);
    expect(secrets.values.has(ORG_TOKEN_SECRET_KEY)).toBe(false);
  });

  it("survives a secret-storage delete failure after a 401", async () => {
    const secrets = connected();
    secrets.delete = () => Promise.reject(new Error("locked"));
    const fake = routedFetch(() => jsonResponse({}, 401));
    const result = await new CopilotOrganizationProvider(secrets.asSecretStorage(), fake.fetch).fetchUsage(OCT_2);
    expect(!result.success && result.error.code).toBe("org-token-rejected");
  });

  it.each([
    [403, {}, "org-access-denied"],
    [404, {}, "org-access-denied"],
    [429, {}, "rate-limited"],
    [403, { "x-ratelimit-remaining": "0" }, "rate-limited"],
    [502, {}, "api-error"],
    [422, {}, "usage-unavailable"],
  ])("maps HTTP %i on the seat endpoint to %s and keeps the token", async (status, headers, code) => {
    const secrets = connected();
    const fake = routedFetch(() => jsonResponse({}, status, headers as Record<string, string>));
    const result = await new CopilotOrganizationProvider(secrets.asSecretStorage(), fake.fetch).fetchUsage(OCT_2);
    expect(!result.success && result.error.code).toBe(code);
    expect(secrets.deleted).toEqual([]);
  });

  it("maps a failure or an unexpected body on the usage endpoint", async () => {
    const secrets = connected();
    const forbidden = fixtureFetch({ billing: "copilot-billing.json" });
    const r1 = await new CopilotOrganizationProvider(secrets.asSecretStorage(), forbidden.fetch).fetchUsage(OCT_2);
    expect(!r1.success && r1.error.code).toBe("org-access-denied");

    const notJson = routedFetch((url) =>
      url.pathname.endsWith("/copilot/billing") ? jsonResponse({ seat_breakdown: { total: 1 }, plan_type: "business" }) : new Response("oops"),
    );
    const r2 = await new CopilotOrganizationProvider(secrets.asSecretStorage(), notJson.fetch).fetchUsage(OCT_2);
    expect(r2).toEqual({ success: false, error: { code: "usage-unavailable" } });

    const wrongShape = routedFetch(() => jsonResponse({ usageItems: null }));
    const r3 = await new CopilotOrganizationProvider(secrets.asSecretStorage(), wrongShape.fetch).fetchUsage(OCT_2);
    expect(r3).toEqual({ success: false, error: { code: "usage-unavailable" } });

    const offline = routedFetch(() => "throw");
    const r4 = await new CopilotOrganizationProvider(secrets.asSecretStorage(), offline.fetch).fetchUsage(OCT_2);
    expect(r4).toEqual({ success: false, error: { code: "network-error" } });
  });

  it("uses the global fetch by default", async () => {
    const secrets = connected();
    const spy = vi.fn(async () => jsonResponse({}, 404));
    vi.stubGlobal("fetch", spy);
    try {
      await new CopilotOrganizationProvider(secrets.asSecretStorage()).fetchUsage(OCT_2);
      expect(spy).toHaveBeenCalledOnce();
    } finally {
      vi.unstubAllGlobals();
    }
  });
});

describe("disconnectOrganization", () => {
  afterEach(() => __resetStubState());

  it("deletes the secret and clears the setting", async () => {
    const secrets = connected();
    expect(await disconnectOrganization(secrets.asSecretStorage())).toBe("token");
    expect(secrets.deleted).toEqual([ORG_TOKEN_SECRET_KEY, ORG_ROUTE_SECRET_KEY]);
    // Global, Workspace, and WorkspaceFolder: every scope an extension can write.
    expect(configurationUpdates).toEqual([1, 2, 3].map((target) => ({ section: "copilotUsage", key: "organization", value: undefined, target })));
    expect(configuredOrganization()).toBe("");
  });
});

describe("isValidOrganizationLogin", () => {
  it.each([
    ["acme", true],
    ["a-b-c", true],
    ["A1", true],
    ["a".repeat(39), true],
    ["a".repeat(40), false],
    ["-a", false],
    ["a-", false],
    ["a--b", false],
    ["a/b", false],
    ["", false],
  ])("%s -> %s", (login, valid) => {
    expect(isValidOrganizationLogin(login)).toBe(valid);
  });
});
