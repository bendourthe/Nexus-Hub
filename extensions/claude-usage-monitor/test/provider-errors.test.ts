import { describe, expect, it } from "vitest";
import { describeProviderError, ClaudeUsageProvider } from "../src/providers";

describe("describeProviderError", () => {
  it("renders the original Claude messages verbatim", () => {
    expect(describeProviderError({ code: "no-credentials" })).toBe(
      "Claude Code credentials not found. Log in to Claude Code first.",
    );
    expect(describeProviderError({ code: "rate-limited" })).toBe(
      "Usage API temporarily unavailable. Showing cached data.",
    );
  });

  it("appends the status code and text for an api-error", () => {
    expect(
      describeProviderError({ code: "api-error", statusCode: 500, statusText: "Server Error" }),
    ).toBe("The Claude API returned an error (500 Server Error).");
  });
});

describe("ClaudeUsageProvider", () => {
  it("identifies as the Claude provider", () => {
    const provider = new ClaudeUsageProvider();
    expect(provider.id).toBe("claude");
    expect(provider.displayName).toBe("Claude");
  });
});
