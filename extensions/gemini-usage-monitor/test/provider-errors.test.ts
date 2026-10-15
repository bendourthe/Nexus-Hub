import { describe, expect, it } from "vitest";
import { describeProviderError, AntigravityUsageProvider } from "../src/providers";

describe("describeProviderError", () => {
  it("explains that the monitor only works inside Antigravity", () => {
    expect(describeProviderError({ code: "not-antigravity" })).toBe(
      "This monitor reads usage from the Antigravity IDE and only works inside Antigravity.",
    );
  });

  it("appends the status code and text for an api-error", () => {
    expect(describeProviderError({ code: "api-error", statusCode: 401, statusText: "Unauthorized" })).toContain(
      "returned an error (401 Unauthorized)",
    );
  });

  it.each([
    ["server-not-found", "Sign in to Antigravity"],
    ["server-unreachable", "Restart Language Server"],
    ["rate-limited", "temporarily unavailable"],
    ["usage-unavailable", "Settings > Models"],
  ] as const)("renders the %s failure", (code, fragment) => {
    expect(describeProviderError({ code })).toContain(fragment);
  });
});

describe("AntigravityUsageProvider", () => {
  it("identifies as the Antigravity provider", () => {
    const provider = new AntigravityUsageProvider("/nonexistent/app");
    expect(provider.id).toBe("antigravity");
    expect(provider.displayName).toBe("Antigravity");
  });

  it("fails soft with not-antigravity when the host does not ship the language server", async () => {
    const result = await new AntigravityUsageProvider("/nonexistent/app").fetchUsage();
    expect(result).toEqual({ success: false, error: { code: "not-antigravity" } });
  });
});
