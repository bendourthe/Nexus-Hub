import { describe, expect, it, vi } from "vitest";
import {
  billingUsageProbePath,
  isProbeAllowed,
  probeVsCodeSession,
  probeWithToken,
  splitScopeHeader,
  toMarkdownRow,
  toSanitizedRecord,
  type ProbeFetchLike,
  type ProbeResponseLike
} from "../src/providers/authProbe";
import {
  GITHUB_API_VERSION,
  withAuthorizationDiagnosis
} from "../src/providers/github";
import type { BillingOwner } from "../src/types";

const TOKEN = "ghp_fixtureclassictoken0123456789abcd";
const SESSION_TOKEN = "gho_fixturesessiontoken0123456789abcd";
const NOW = new Date("2026-08-06T12:00:00Z");

const ORG: BillingOwner = { scope: "organization", name: "acme" };
const USER: BillingOwner = { scope: "user", name: "octocat" };
const ENTERPRISE: BillingOwner = { scope: "enterprise", name: "acme-inc" };

/** Billing data a probe must never retain. */
const SUCCESS_BODY = {
  usageItems: [
    { product: "actions", quantity: 1234, netAmount: 56.78, repositoryName: "acme/private-repo" }
  ]
};

function headers(values: Record<string, string> = {}): ProbeResponseLike["headers"] {
  const lower = new Map(
    Object.entries(values).map(([key, value]) => [key.toLowerCase(), value])
  );
  return { get: (name: string) => lower.get(name.toLowerCase()) ?? null };
}

function stubFetch(
  response: Partial<ProbeResponseLike> & { headers?: ProbeResponseLike["headers"] },
  calls: Array<{ url: string; headers: Record<string, string> }> = []
): ProbeFetchLike {
  return async (url, init) => {
    calls.push({ url, headers: { ...init.headers } });
    return {
      ok: response.ok ?? true,
      status: response.status ?? 200,
      statusText: response.statusText ?? "",
      headers: response.headers ?? headers(),
      json: response.json ?? (async () => SUCCESS_BODY)
    };
  };
}

describe("probe boundaries", () => {
  it("refuses the one combination GitHub documentarily rejects", async () => {
    expect(isProbeAllowed("enterprise", "fine-grained-pat")).toBe(false);
    expect(isProbeAllowed("enterprise", "classic-pat")).toBe(true);
    expect(isProbeAllowed("enterprise", "vscode-oauth")).toBe(true);
    expect(isProbeAllowed("organization", "fine-grained-pat")).toBe(true);
    expect(isProbeAllowed("user", "fine-grained-pat")).toBe(true);

    const calls: Array<{ url: string; headers: Record<string, string> }> = [];
    await expect(
      probeWithToken({
        owner: ENTERPRISE,
        token: TOKEN,
        credentialKind: "fine-grained-pat",
        fetch: stubFetch({}, calls),
        now: NOW
      })
    ).rejects.toThrow(/documentarily rejects/iu);
    // Refused before any request: a known-negative must not spend a call.
    expect(calls).toEqual([]);
  });

  it("targets one billing-usage endpoint per level with an explicit period", () => {
    expect(billingUsageProbePath(USER, NOW)).toBe(
      "/users/octocat/settings/billing/usage?year=2026&month=8"
    );
    expect(billingUsageProbePath(ORG, NOW)).toBe(
      "/organizations/acme/settings/billing/usage?year=2026&month=8"
    );
    expect(billingUsageProbePath(ENTERPRISE, NOW)).toBe(
      "/enterprises/acme-inc/settings/billing/usage?year=2026&month=8"
    );
  });

  it("issues exactly one request and pins the current API version", async () => {
    const calls: Array<{ url: string; headers: Record<string, string> }> = [];
    await probeWithToken({
      owner: ORG,
      token: TOKEN,
      credentialKind: "classic-pat",
      fetch: stubFetch({}, calls),
      now: NOW
    });
    expect(calls).toHaveLength(1);
    expect(calls[0]?.headers["X-GitHub-Api-Version"]).toBe(GITHUB_API_VERSION);
    expect(GITHUB_API_VERSION).toBe("2026-03-10");
  });
});

describe("header capture", () => {
  it("splits and trims scope headers, and reports absence as empty", () => {
    expect(splitScopeHeader("repo, read:org , admin:org")).toEqual([
      "repo",
      "read:org",
      "admin:org"
    ]);
    expect(splitScopeHeader("")).toEqual([]);
    expect(splitScopeHeader(null)).toEqual([]);
  });

  it("captures the headers that actually answer the question", async () => {
    const record = await probeWithToken({
      owner: ORG,
      token: TOKEN,
      credentialKind: "vscode-oauth",
      requestedScopes: ["read:org"],
      providerReportedScopes: ["read:org"],
      now: NOW,
      fetch: stubFetch({
        ok: false,
        status: 403,
        statusText: "Forbidden",
        headers: headers({
          "x-oauth-scopes": "repo, read:user",
          "x-accepted-oauth-scopes": "admin:org",
          "x-accepted-github-permissions": "administration=read",
          "x-github-request-id": "FIXTURE:1234"
        }),
        json: async () => ({
          message: "Resource not accessible by integration",
          documentation_url: "https://docs.github.com/rest/billing/usage"
        })
      })
    });

    // The accepted-scope header is the documented discovery mechanism, and it is
    // what turns a bare 403 into an actionable "escalate to admin:org".
    expect(record.acceptedOAuthScopes).toEqual(["admin:org"]);
    expect(record.grantedOAuthScopes).toEqual(["repo", "read:user"]);
    expect(record.acceptedGitHubPermissions).toBe("administration=read");
    expect(record.requestId).toBe("FIXTURE:1234");
    expect(record.error?.message).toBe("Resource not accessible by integration");
  });

  it("keeps provider-reported scopes separate from granted scopes", async () => {
    const record = await probeWithToken({
      owner: ORG,
      token: TOKEN,
      credentialKind: "vscode-oauth",
      // The editor reports what was REQUESTED, which can overstate a narrowed
      // consent. Conflating the two would read a reduced grant as a full one.
      requestedScopes: ["read:org", "admin:org"],
      providerReportedScopes: ["read:org", "admin:org"],
      now: NOW,
      fetch: stubFetch({
        headers: headers({ "x-oauth-scopes": "read:org" })
      })
    });
    expect(record.providerReportedScopes).toEqual(["read:org", "admin:org"]);
    expect(record.grantedOAuthScopes).toEqual(["read:org"]);
    expect(record.grantedOAuthScopes).not.toEqual(record.providerReportedScopes);
  });
});

describe("body handling", () => {
  it("never reads a success body", async () => {
    const json = vi.fn(async () => SUCCESS_BODY);
    const record = await probeWithToken({
      owner: ORG,
      token: TOKEN,
      credentialKind: "classic-pat",
      now: NOW,
      fetch: stubFetch({ ok: true, status: 200, json })
    });
    expect(json).not.toHaveBeenCalled();
    expect(record.error).toBeNull();
    expect(record.status).toBe(200);
  });

  it("keeps only message and documentation_url from a failure body", async () => {
    const record = await probeWithToken({
      owner: ORG,
      token: TOKEN,
      credentialKind: "classic-pat",
      now: NOW,
      fetch: stubFetch({
        ok: false,
        status: 403,
        json: async () => ({
          message: "Must have admin rights",
          documentation_url: "https://docs.github.com/x",
          errors: [{ resource: "Org", field: "secret-field" }],
          organizationId: 4242
        })
      })
    });
    expect(record.error).toEqual({
      message: "Must have admin rights",
      documentationUrl: "https://docs.github.com/x"
    });
    expect(JSON.stringify(record)).not.toContain("secret-field");
    expect(JSON.stringify(record)).not.toContain("4242");
  });

  it.each([
    ["a non-JSON body", async () => { throw new Error("not json"); }],
    ["an array body", async () => [1, 2, 3]],
    ["a null body", async () => null]
  ])("degrades safely on %s", async (_label, json) => {
    const record = await probeWithToken({
      owner: ORG,
      token: TOKEN,
      credentialKind: "classic-pat",
      now: NOW,
      fetch: stubFetch({ ok: false, status: 500, statusText: "Server Error", json })
    });
    expect(record.error?.message).toContain("500");
  });
});

describe("no-leak serialization contract", () => {
  /**
   * The point of this block: the "never record" list in
   * docs/v3/v3.15/development/github-billing-auth-probe.md is enforced here rather
   * than promised in prose, so a probe result cannot be pasted into a document or a
   * chat window carrying a credential.
   */
  async function failingRecord() {
    return probeWithToken({
      owner: ORG,
      token: TOKEN,
      credentialKind: "classic-pat",
      requestedScopes: ["read:org"],
      providerReportedScopes: ["read:org"],
      now: NOW,
      fetch: stubFetch({
        ok: false,
        status: 403,
        headers: headers({ "x-accepted-oauth-scopes": "admin:org" }),
        json: async () => ({ message: "Must have admin rights" })
      })
    });
  }

  it("omits the token from the raw record and its serialization", async () => {
    const record = await failingRecord();
    const raw = JSON.stringify(record);
    const sanitized = JSON.stringify(toSanitizedRecord(record));
    for (const serialized of [raw, sanitized]) {
      expect(serialized).not.toContain(TOKEN);
      expect(serialized).not.toContain("ghp_");
      expect(serialized.toLowerCase()).not.toContain("authorization");
      expect(serialized.toLowerCase()).not.toContain("bearer");
    }
  });

  it("omits any success body from the serialization", async () => {
    const record = await probeWithToken({
      owner: ORG,
      token: TOKEN,
      credentialKind: "classic-pat",
      now: NOW,
      fetch: stubFetch({ ok: true, status: 200 })
    });
    const sanitized = JSON.stringify(toSanitizedRecord(record));
    expect(sanitized).not.toContain("usageItems");
    expect(sanitized).not.toContain("private-repo");
    expect(sanitized).not.toContain("56.78");
  });

  it("emits exactly the approved field set, and nothing else", async () => {
    const record = await failingRecord();
    // Rebuilt field by field on purpose: a field added to ProbeRecord must be added
    // here deliberately before it can reach a report.
    expect(Object.keys(toSanitizedRecord(record)).sort()).toEqual(
      [
        "acceptedGitHubPermissions",
        "acceptedOAuthScopes",
        "apiVersion",
        "checkedAt",
        "credentialKind",
        "endpoint",
        "errorDocumentationUrl",
        "errorMessage",
        "grantedOAuthScopes",
        "level",
        "providerReportedScopes",
        "requestId",
        "requestedScopes",
        "status"
      ].sort()
    );
  });

  it("renders a paste-ready results row without a credential", async () => {
    const row = toMarkdownRow(await failingRecord());
    expect(row.startsWith("|")).toBe(true);
    expect(row).toContain("2026-08-06");
    expect(row).toContain("organization");
    expect(row).toContain("classic-pat");
    expect(row).toContain("403");
    expect(row).toContain("admin:org");
    expect(row).not.toContain(TOKEN);
    expect(row).not.toContain("?year=");
  });
});

describe("withAuthorizationDiagnosis", () => {
  const base = {
    code: "missing-organization-administration-read" as const,
    message: "The token needs organization Administration: read.",
    statusCode: 403
  };

  it("appends GitHub's own accepted-scope answer to the extension's guess", () => {
    const diagnosed = withAuthorizationDiagnosis(
      base,
      headers({
        "x-accepted-oauth-scopes": "admin:org",
        "x-oauth-scopes": "repo, read:user",
        "x-accepted-github-permissions": "administration=read",
        "x-github-request-id": "FIXTURE:9"
      })
    );

    expect(diagnosed.accepted).toEqual({
      acceptedOAuthScopes: ["admin:org"],
      grantedOAuthScopes: ["repo", "read:user"],
      acceptedGitHubPermissions: "administration=read"
    });
    expect(diagnosed.requestId).toBe("FIXTURE:9");
    // The user learns the specific scope to grant, not just "needs permission".
    expect(diagnosed.message).toContain("accepts OAuth scopes: admin:org");
    expect(diagnosed.message).toContain("repo, read:user");
    expect(diagnosed.code).toBe(base.code);
    expect(diagnosed.statusCode).toBe(403);
  });

  it("says so plainly when the credential carries no OAuth scopes", () => {
    const diagnosed = withAuthorizationDiagnosis(
      base,
      headers({ "x-accepted-oauth-scopes": "admin:org" })
    );
    expect(diagnosed.message).toContain("no OAuth scopes");
    expect(diagnosed.accepted?.grantedOAuthScopes).toEqual([]);
  });

  it("leaves the error untouched when GitHub reports nothing", () => {
    const diagnosed = withAuthorizationDiagnosis(base, headers());
    expect(diagnosed).toEqual(base);
  });

  it("records a request id even when no scope headers are present", () => {
    const diagnosed = withAuthorizationDiagnosis(
      base,
      headers({ "x-github-request-id": "FIXTURE:10" })
    );
    expect(diagnosed.requestId).toBe("FIXTURE:10");
    // No scope evidence means no invented scope advice.
    expect(diagnosed.message).toBe(base.message);
  });

  it("does not append advice when the accepted-scope list is empty", () => {
    const diagnosed = withAuthorizationDiagnosis(
      base,
      headers({ "x-accepted-oauth-scopes": "", "x-oauth-scopes": "repo" })
    );
    expect(diagnosed.message).toBe(base.message);
    expect(diagnosed.accepted?.grantedOAuthScopes).toEqual(["repo"]);
  });
});

describe("probeVsCodeSession", () => {
  it("uses the injected provider and never returns the session", async () => {
    const getSession = vi.fn(async () => ({
      accessToken: SESSION_TOKEN,
      scopes: ["read:org"]
    }));
    const calls: Array<{ url: string; headers: Record<string, string> }> = [];
    const record = await probeVsCodeSession(getSession, {
      owner: ORG,
      requestedScopes: ["read:org"],
      now: NOW,
      fetch: stubFetch({ headers: headers({ "x-oauth-scopes": "read:org" }) }, calls)
    });

    expect(getSession).toHaveBeenCalledWith("github", ["read:org"]);
    expect(record?.credentialKind).toBe("vscode-oauth");
    expect(record?.providerReportedScopes).toEqual(["read:org"]);
    expect(calls[0]?.headers.Authorization).toBe(`Bearer ${SESSION_TOKEN}`);
    expect(JSON.stringify(record)).not.toContain(SESSION_TOKEN);
  });

  it("returns null when the user declines the consent prompt", async () => {
    const record = await probeVsCodeSession(async () => undefined, {
      owner: USER,
      requestedScopes: ["read:user"],
      now: NOW,
      fetch: stubFetch({})
    });
    expect(record).toBeNull();
  });
});
