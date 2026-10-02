import { afterEach, describe, expect, it, vi } from "vitest";
import {
  BACKGROUND_SCOPES,
  CopilotUsageProvider,
  SIGN_IN_SCOPES,
  signIn,
  switchAccount,
} from "../src/providers/copilot";
import { GITHUB_API_ORIGIN, githubApiUrl, githubGet } from "../src/providers/githubApi";
import { describeProviderError } from "../src/providers";
import type { ProviderFetchErrorCode } from "../src/providers/types";
import { FakeGitHubAuth, PERSONAL_TOKEN, WORK_TOKEN, fixture, jsonResponse, routedFetch } from "./helpers";
import { __resetStubState, __setAuthentication } from "./vscode-stub";

const personal = { id: "personal", label: "personal-account", token: PERSONAL_TOKEN };
const work = { id: "work", label: "work-account", token: WORK_TOKEN };

function provider(status: number, body: unknown = {}, headers: Record<string, string> = {}) {
  const auth = new FakeGitHubAuth([personal]);
  const fake = routedFetch(() => jsonResponse(body, status, headers));
  return { auth, fake, provider: new CopilotUsageProvider(auth, fake.fetch) };
}

describe("CopilotUsageProvider", () => {
  afterEach(() => __resetStubState());

  it("identifies as the Copilot provider", () => {
    const p = new CopilotUsageProvider(new FakeGitHubAuth([]));
    expect(p.id).toBe("copilot");
    expect(p.displayName).toBe("GitHub Copilot");
  });

  it("looks the session up silently with an empty scope list and no account", async () => {
    const { auth, fake, provider: p } = provider(200, fixture("copilot-internal-user.personal.json"));
    const result = await p.fetchUsage();
    expect(result.success).toBe(true);
    expect(auth.calls).toEqual([
      { providerId: "github", scopes: [...BACKGROUND_SCOPES], options: { createIfNone: false, silent: true } },
    ]);
    expect(auth.calls[0].options).not.toHaveProperty("account");
    expect(fake.calls).toHaveLength(1);
    expect(fake.calls[0].url).toBe("https://api.github.com/copilot_internal/user");
    expect(fake.calls[0].authorization).toBe(`token ${PERSONAL_TOKEN}`);
    expect(fake.calls[0].init.redirect).toBe("error");
  });

  it("reports no-credentials when no GitHub session exists, without prompting or fetching", async () => {
    const auth = new FakeGitHubAuth([]);
    const fake = routedFetch(() => jsonResponse({}));
    const p = new CopilotUsageProvider(auth, fake.fetch);
    expect(await p.fetchUsage()).toEqual({ success: false, error: { code: "no-credentials" } });
    expect(await p.readCredential()).toEqual({ ok: false, reason: "missing" });
    expect(fake.calls).toHaveLength(0);
    expect(auth.calls.every((c) => c.options.silent === true && !c.options.createIfNone)).toBe(true);
  });

  it("reports choose-account with several accounts and no stored preference", async () => {
    const auth = new FakeGitHubAuth([personal, work]);
    const p = new CopilotUsageProvider(auth, routedFetch(() => jsonResponse({})).fetch);
    expect(await p.fetchUsage()).toEqual({ success: false, error: { code: "choose-account" } });
    expect(await p.readCredential()).toEqual({ ok: false, reason: "choose-account" });
    auth.preference = "work";
    expect(await p.readCredential()).toEqual({ ok: true });
  });

  it("treats a getSession or getAccounts failure as no session", async () => {
    const auth = {
      getSession: () => Promise.reject(new Error("boom")),
      getAccounts: () => Promise.reject(new Error("boom")),
    };
    const p = new CopilotUsageProvider(auth, routedFetch(() => jsonResponse({})).fetch);
    expect(await p.fetchUsage()).toEqual({ success: false, error: { code: "no-credentials" } });
    const noAccounts = new CopilotUsageProvider({ getSession: () => Promise.resolve(undefined) });
    expect(await noAccounts.readCredential()).toEqual({ ok: false, reason: "missing" });
  });

  it.each<[number, Record<string, string>, ProviderFetchErrorCode]>([
    [401, {}, "token-invalid"],
    [429, {}, "rate-limited"],
    [403, { "x-ratelimit-remaining": "0" }, "rate-limited"],
    [403, {}, "usage-unavailable"],
    [404, {}, "usage-unavailable"],
    [500, {}, "api-error"],
    [503, {}, "api-error"],
  ])("maps HTTP %i to %s", async (status, headers, code) => {
    const result = await provider(status, {}, headers).provider.fetchUsage();
    expect(result.success).toBe(false);
    expect(!result.success && result.error.code).toBe(code);
    expect(!result.success && result.error.statusCode).toBe(status);
  });

  it("fails soft on a network error, a non-JSON body, and an unrecognized payload", async () => {
    const auth = new FakeGitHubAuth([personal]);
    const thrown = new CopilotUsageProvider(auth, routedFetch(() => "throw").fetch);
    expect(await thrown.fetchUsage()).toEqual({ success: false, error: { code: "network-error" } });

    const text = new CopilotUsageProvider(auth, routedFetch(() => new Response("<html>", { status: 200 })).fetch);
    expect(await text.fetchUsage()).toEqual({ success: false, error: { code: "usage-unavailable" } });

    const shape = new CopilotUsageProvider(auth, routedFetch(() => jsonResponse({ login: "x" })).fetch);
    expect(await shape.fetchUsage()).toEqual({ success: false, error: { code: "usage-unavailable" } });
  });

  it("uses the global fetch by default", async () => {
    const spy = vi.fn(async () => jsonResponse(fixture("copilot-internal-user.personal.json")));
    vi.stubGlobal("fetch", spy);
    try {
      const result = await new CopilotUsageProvider(new FakeGitHubAuth([personal])).fetchUsage();
      expect(result.success).toBe(true);
      expect(spy).toHaveBeenCalledOnce();
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("reads vscode.authentication by default", async () => {
    __setAuthentication(new FakeGitHubAuth([work]));
    const fake = routedFetch(() => jsonResponse(fixture("copilot-internal-user.business-member.json")));
    const result = await new CopilotUsageProvider(undefined, fake.fetch).fetchUsage();
    expect(result.success).toBe(true);
    expect(fake.calls[0].authorization).toBe(`token ${WORK_TOKEN}`);
  });
});

describe("signIn and switchAccount", () => {
  it("prompt only with the narrow read:user scope", async () => {
    const auth = new FakeGitHubAuth([personal, work]);
    auth.pickOnPrompt = "work";
    expect(await signIn(auth)).toBe(true);
    expect(auth.calls[0]).toEqual({ providerId: "github", scopes: [...SIGN_IN_SCOPES], options: { createIfNone: true } });
    expect(auth.preference).toBe("work");

    auth.pickOnPrompt = "personal";
    expect(await switchAccount(auth)).toBe(true);
    expect(auth.calls[1].options).toEqual({ clearSessionPreference: true, createIfNone: true });
    expect(auth.preference).toBe("personal");
  });

  it("return false when the user cancels or the call fails", async () => {
    const cancelled = new FakeGitHubAuth([personal, work]);
    expect(await signIn(cancelled)).toBe(false);
    expect(await switchAccount(cancelled)).toBe(false);
    const failing = { getSession: () => Promise.reject(new Error("cancelled")) };
    expect(await signIn(failing)).toBe(false);
    expect(await switchAccount(failing)).toBe(false);
  });
});

describe("githubGet", () => {
  it("builds api.github.com URLs and refuses any other origin", async () => {
    const url = githubApiUrl("/orgs/x/copilot/billing", { year: "2026" });
    expect(url.origin).toBe(GITHUB_API_ORIGIN);
    expect(url.search).toBe("?year=2026");
    const fake = routedFetch(() => jsonResponse({}));
    expect(await githubGet(new URL("https://example.invalid/steal"), "token x", {}, fake.fetch)).toEqual({ kind: "network-error" });
    expect(fake.calls).toHaveLength(0);
  });
});

describe("describeProviderError", () => {
  it.each<[ProviderFetchErrorCode, string]>([
    ["no-credentials", "Sign in to GitHub"],
    ["choose-account", "Choose GitHub account"],
    ["token-invalid", "rejected the VS Code sign-in (401 Unauthorized)"],
    ["rate-limited", "rate-limiting"],
    ["network-error", "api.github.com"],
    ["api-error", "returned an error (502 Bad Gateway)"],
    ["parse-error", "does not recognize"],
    ["usage-unavailable", "does not recognize"],
    ["org-not-connected", "Connect Organization"],
    ["org-access-denied", "organization owner or billing manager"],
    ["org-token-rejected", "Reconnect"],
  ])("renders %s", (code, fragment) => {
    const statusCode = code === "token-invalid" ? 401 : code === "api-error" ? 502 : undefined;
    const statusText = code === "token-invalid" ? "Unauthorized" : code === "api-error" ? "Bad Gateway" : undefined;
    const message = describeProviderError({ code, statusCode, statusText });
    expect(message).toContain(fragment);
    expect(/^[\x20-\x7E]*$/.test(message)).toBe(true);
  });
});
