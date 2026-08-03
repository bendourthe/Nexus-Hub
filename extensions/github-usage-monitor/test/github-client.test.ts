import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it, vi } from "vitest";
import {
  GITHUB_ACCEPT,
  GITHUB_API_VERSION,
  GITHUB_USER_AGENT,
  GitHubBillingClient,
  type FetchLike
} from "../src/providers/github";

const owner = { scope: "organization" as const, name: "fixture-org" };
const token = "fixture-token-value-123456789";
const now = Date.UTC(2026, 7, 15);

class FixtureHeaders {
  public constructor(private readonly values: Record<string, string> = {}) {}

  public get(name: string): string | null {
    return this.values[name.toLowerCase()] ?? null;
  }
}

function fixture(name: string): unknown {
  return JSON.parse(
    readFileSync(resolve(__dirname, "../../../tests/fixtures/github-usage", name), "utf8")
  ) as unknown;
}

function response(
  status: number,
  payload: unknown,
  headers: Record<string, string> = {}
): Awaited<ReturnType<FetchLike>> {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? "OK" : "Failure",
    headers: new FixtureHeaders(headers),
    json: async () => payload
  };
}

describe("GitHubBillingClient", () => {
  it("constructs versioned current-month requests and normalizes both responses", async () => {
    const request = vi
      .fn<FetchLike>()
      .mockResolvedValueOnce(response(200, fixture("current-ai-credits.json"), { "x-ratelimit-remaining": "50" }))
      .mockResolvedValueOnce(response(200, fixture("actions-minutes-storage.json"), { "x-ratelimit-remaining": "49" }));
    const client = new GitHubBillingClient(request);
    const result = await client.fetchUsage({ owner, token, copilotEndpoint: "ai-credits", now });

    expect(result.ok).toBe(true);
    expect(request).toHaveBeenCalledTimes(2);
    const [url, init] = request.mock.calls[0] ?? [];
    expect(url).toBe("https://api.github.com/organizations/fixture-org/settings/billing/ai_credit/usage?year=2026&month=8");
    expect(init?.headers).toMatchObject({
      Accept: GITHUB_ACCEPT,
      Authorization: `Bearer ${token}`,
      "X-GitHub-Api-Version": GITHUB_API_VERSION,
      "User-Agent": GITHUB_USER_AGENT
    });
    expect(result.rate.remaining).toBe(49);
  });

  it("validates a credential with one bounded billing request", async () => {
    const request = vi.fn<FetchLike>().mockResolvedValue(response(200, fixture("empty-month.json")));
    const result = await new GitHubBillingClient(request).validateCredential(owner, token);
    expect(result.ok).toBe(true);
    expect(request).toHaveBeenCalledOnce();
  });

  it("rejects invalid token syntax before network access", async () => {
    const request = vi.fn<FetchLike>();
    const result = await new GitHubBillingClient(request).fetchUsage({
      owner,
      token: "bad",
      copilotEndpoint: "ai-credits",
      now
    });
    expect(!result.ok && result.error.code).toBe("invalid-token");
    expect(request).not.toHaveBeenCalled();
  });

  it("rejects unsupported enterprise legacy usage before network access", async () => {
    const request = vi.fn<FetchLike>();
    const result = await new GitHubBillingClient(request).fetchUsage({
      owner: { scope: "enterprise", name: "fixture-enterprise" },
      token,
      copilotEndpoint: "premium-requests",
      now
    });
    expect(!result.ok && result.error.code).toBe("not-found");
    expect(request).not.toHaveBeenCalled();
  });

  it.each([
    [401, "error-401.json", {}, "invalid-token"],
    [403, "error-403.json", {}, "missing-organization-administration-read"],
    [403, "error-403.json", { "x-ratelimit-remaining": "0", "x-ratelimit-reset": "1785686400" }, "rate-limited"],
    [429, "error-429.json", { "retry-after": "60" }, "rate-limited"],
    [500, "error-404.json", {}, "service-error"]
  ] as const)("classifies HTTP %s", async (status, fixtureName, headers, code) => {
    const request = vi.fn<FetchLike>().mockResolvedValue(response(status, fixture(fixtureName), headers));
    const result = await new GitHubBillingClient(request).fetchUsage({ owner, token, copilotEndpoint: "ai-credits", now });
    expect(!result.ok && result.error.code).toBe(code);
  });

  it("distinguishes an unavailable detailed usage endpoint from an unknown Copilot owner", async () => {
    const detailsRequest = vi
      .fn<FetchLike>()
      .mockResolvedValueOnce(response(200, fixture("current-ai-credits.json")))
      .mockResolvedValueOnce(response(404, fixture("error-404.json")));
    const details = await new GitHubBillingClient(detailsRequest).fetchUsage({ owner, token, copilotEndpoint: "ai-credits", now });
    expect(!details.ok && details.error.code).toBe("enhanced-billing-unavailable");

    const copilotRequest = vi.fn<FetchLike>().mockResolvedValue(response(404, fixture("error-404.json")));
    const copilot = await new GitHubBillingClient(copilotRequest).fetchUsage({ owner, token, copilotEndpoint: "ai-credits", now });
    expect(!copilot.ok && copilot.error.code).toBe("not-found");
  });

  it("returns schema mismatch for non-JSON success", async () => {
    const bad = response(200, {});
    bad.json = async () => {
      throw new Error("invalid json");
    };
    const result = await new GitHubBillingClient(vi.fn<FetchLike>().mockResolvedValue(bad)).fetchUsage({
      owner,
      token,
      copilotEndpoint: "ai-credits",
      now
    });
    expect(!result.ok && result.error.code).toBe("schema-mismatch");
  });

  it("returns a network error without including the token", async () => {
    const request = vi.fn<FetchLike>().mockRejectedValue(new Error("offline"));
    const result = await new GitHubBillingClient(request).fetchUsage({ owner, token, copilotEndpoint: "ai-credits", now });
    expect(!result.ok && result.error.code).toBe("network-error");
    if (!result.ok) {
      expect(result.error.message).not.toContain(token);
    }
  });

  it("distinguishes timeout from caller cancellation", async () => {
    const hanging: FetchLike = async (_url, init) => new Promise((_resolve, reject) => {
      init.signal.addEventListener("abort", () => reject(new Error("aborted")), { once: true });
    });
    const timeout = await new GitHubBillingClient(hanging, "https://api.github.com", 1).fetchUsage({
      owner,
      token,
      copilotEndpoint: "ai-credits",
      now
    });
    expect(!timeout.ok && timeout.error.code).toBe("timeout");

    const controller = new AbortController();
    const pending = new GitHubBillingClient(hanging, "https://api.github.com", 10_000).fetchUsage({
      owner,
      token,
      copilotEndpoint: "ai-credits",
      now,
      signal: controller.signal
    });
    controller.abort();
    const cancelled = await pending;
    expect(!cancelled.ok && cancelled.error.code).toBe("cancelled");
  });
});
