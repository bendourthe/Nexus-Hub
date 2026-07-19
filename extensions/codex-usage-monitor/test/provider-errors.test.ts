import { describe, expect, it } from "vitest";
import { describeProviderError, CodexUsageProvider } from "../src/providers";

describe("describeProviderError", () => {
  it("renders Codex-specific messages", () => {
    expect(describeProviderError({ code: "no-credentials" })).toBe(
      "Codex credentials not found. Sign in to the Codex app first.",
    );
    expect(describeProviderError({ code: "usage-unavailable" })).toContain("undocumented");
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
