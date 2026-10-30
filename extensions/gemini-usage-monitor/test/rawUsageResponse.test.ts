import { describe, expect, it } from "vitest";
import { redactUsagePayload } from "../src/rawUsageResponse";

// A saved capture must tell the quota groups and their windows apart, which is
// the only way to check a changed Antigravity layout, while still hiding anything
// that could identify the account.
describe("redactUsagePayload for the Antigravity quota summary", () => {
  const capture = {
    response: {
      groups: [
        {
          displayName: "Gemini 4 Argon",
          description: "Models within this group: Gemini 4 Argon",
          buckets: [{ bucketId: "b1", displayName: "Gemini 4 Argon Weekly Limit", window: "weekly", remainingFraction: 0.93, resetTime: "2026-11-04T22:10:04Z" }],
        },
        {
          displayName: "Claude and GPT models",
          buckets: [{ bucketId: "b2", displayName: "Five Hour Limit Remaining", window: "5h", resetTime: "2026-10-28T23:10:04Z" }],
        },
      ],
    },
    userStatus: { displayName: "Benjamin Dourthe", email: "someone@example.com", userTier: { description: "Google AI Pro" } },
  };

  it("keeps group and bucket labels and short window ids", () => {
    const out = redactUsagePayload(capture) as { response: { groups: Array<Record<string, unknown> & { buckets: Array<Record<string, unknown>> }> } };
    expect(out.response.groups[0].displayName).toBe("Gemini 4 Argon");
    expect(out.response.groups[0].description).toBe("Models within this group: Gemini 4 Argon");
    expect(out.response.groups[0].buckets[0].displayName).toBe("Gemini 4 Argon Weekly Limit");
    expect(out.response.groups[1].displayName).toBe("Claude and GPT models");
    expect(out.response.groups[1].buckets[0].window).toBe("5h");
    expect(out.response.groups[0].buckets[0].remainingFraction).toBe(0.93);
  });

  it("still hides identity fields, including a display name outside the quota groups", () => {
    const out = redactUsagePayload(capture) as { userStatus: Record<string, unknown>; response: { groups: Array<{ buckets: Array<Record<string, unknown>> }> } };
    expect(out.userStatus.displayName).toBe("<redacted string, 16 chars>");
    expect(out.userStatus.email).toBe("<redacted string, 19 chars>");
    expect(out.response.groups[0].buckets[0].bucketId).toBe("<redacted string, 2 chars>");
  });

  it("hides a quota label that does not look like plain label text", () => {
    const out = redactUsagePayload({ groups: [{ displayName: "owner@example.com", description: "x".repeat(200) }] }) as { groups: Array<Record<string, unknown>> };
    expect(out.groups[0].displayName).toBe("<redacted string, 17 chars>");
    expect(out.groups[0].description).toBe("<redacted string, 200 chars>");
  });

  it("does not keep long token-like values as window ids", () => {
    expect(redactUsagePayload({ window: "5h" })).toEqual({ window: "5h" });
    expect(redactUsagePayload({ window: "123456abcdef0123" })).toEqual({ window: "<redacted string, 16 chars>" });
  });
});
