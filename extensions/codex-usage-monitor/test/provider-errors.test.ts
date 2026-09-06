import { describe, expect, it } from "vitest";
import { describeProviderError, CodexUsageProvider } from "../src/providers";

describe("describeProviderError", () => {
  it("renders Codex-specific messages", () => {
    expect(describeProviderError({ code: "no-credentials" })).toBe(
      "Codex credentials not found (~/.codex/auth.json). Run 'codex' in a terminal to sign in.",
    );
    // v3.14.6: auto-fetch works against the verified endpoint, so the
    // usage-unavailable message no longer points at manual entry; it is a real
    // failure diagnostic that stays actionable (retry / re-auth via `codex`).
    const unavailable = describeProviderError({ code: "usage-unavailable" });
    expect(unavailable.toLowerCase()).not.toContain("manual");
    expect(unavailable).toContain("codex");
  });

  it("appends the status code and text for an api-error", () => {
    expect(
      describeProviderError({ code: "api-error", statusCode: 502, statusText: "Bad Gateway" }),
    ).toBe("The Codex usage endpoint returned an error (502 Bad Gateway).");
  });

  it.each([
    ["invalid-credentials", "could not be read"],
    ["token-expired", "sign-in has expired"],
    ["token-refresh-failed", "Could not refresh"],
    ["token-invalid", "rejected (401)"],
    ["rate-limited", "temporarily unavailable"],
    ["network-error", "Check your internet connection"],
    ["parse-error", "unexpected response"],
  ] as const)("renders the %s failure", (code, fragment) => {
    const error = code === "token-invalid"
      ? { code, statusCode: 401 }
      : { code };
    expect(describeProviderError(error)).toContain(fragment);
  });
});

describe("CodexUsageProvider", () => {
  it("identifies as the Codex provider", () => {
    const provider = new CodexUsageProvider();
    expect(provider.id).toBe("codex");
    expect(provider.displayName).toBe("Codex");
  });
});
