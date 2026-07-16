import { describe, expect, it } from "vitest";
import { describeProviderError, createProvider } from "../src/providers";

describe("describeProviderError", () => {
  it("renders the original Claude messages verbatim", () => {
    expect(describeProviderError({ providerId: "claude", code: "no-credentials" })).toBe(
      "Claude Code credentials not found. Log in to Claude Code first.",
    );
    expect(describeProviderError({ providerId: "claude", code: "rate-limited" })).toBe(
      "Usage API temporarily unavailable. Showing cached data.",
    );
  });

  it("appends the status code and text for a Claude api-error", () => {
    expect(
      describeProviderError({ providerId: "claude", code: "api-error", statusCode: 500, statusText: "Server Error" }),
    ).toBe("The Claude API returned an error (500 Server Error).");
  });

  it("renders Codex-specific messages", () => {
    expect(describeProviderError({ providerId: "codex", code: "no-credentials" })).toBe(
      "Codex credentials not found. Sign in to the Codex app first.",
    );
    expect(describeProviderError({ providerId: "codex", code: "usage-unavailable" })).toContain("undocumented");
  });
});

describe("createProvider", () => {
  it("returns a Codex provider for the codex id", () => {
    expect(createProvider("codex").id).toBe("codex");
    expect(createProvider("codex").displayName).toBe("Codex");
  });

  it("returns a Claude provider for the claude id", () => {
    expect(createProvider("claude").id).toBe("claude");
    expect(createProvider("claude").displayName).toBe("Claude");
  });
});
