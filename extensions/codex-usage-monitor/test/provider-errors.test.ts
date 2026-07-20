import { describe, expect, it } from "vitest";
import { describeProviderError, CodexUsageProvider } from "../src/providers";

describe("describeProviderError", () => {
  it("renders Codex-specific messages", () => {
    expect(describeProviderError({ code: "no-credentials" })).toBe(
      "Codex credentials not found. Sign in to the Codex app first.",
    );
    // The usage-unavailable banner must stay honest (undocumented endpoint) AND
    // actionable (point at manual entry), per v3.14.5 Phase 4.3.
    const unavailable = describeProviderError({ code: "usage-unavailable" });
    expect(unavailable).toContain("undocumented");
    expect(unavailable.toLowerCase()).toContain("manual");
  });

  it("appends the status code and text for an api-error", () => {
    expect(
      describeProviderError({ code: "api-error", statusCode: 502, statusText: "Bad Gateway" }),
    ).toBe("The Codex usage endpoint returned an error (502 Bad Gateway).");
  });
});

describe("CodexUsageProvider", () => {
  it("identifies as the Codex provider", () => {
    const provider = new CodexUsageProvider();
    expect(provider.id).toBe("codex");
    expect(provider.displayName).toBe("Codex");
  });
});
