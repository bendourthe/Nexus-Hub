import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import {
  extractVisibleText,
  normalizeHtmlUsage,
  normalizeSnapshotPayload
} from "../src/providers/normalizer";

const fetchedAt = "2026-08-04T16:00:00Z";

function fixture<T = unknown>(name: string): T {
  const path = resolve(__dirname, "../../../tests/fixtures/cursor-usage", name);
  const text = readFileSync(path, "utf8");
  return (name.endsWith(".html") ? text : JSON.parse(text)) as T;
}

describe("normalizeSnapshotPayload", () => {
  it("normalizes both healthy included pools", () => {
    const result = normalizeSnapshotPayload(
      fixture("included-usage-healthy.json"),
      { source: "credential-api" }
    );
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value).toMatchObject({
        source: "credential-api",
        stale: false,
        fetchedAt,
        cursorModels: {
          used: { value: 345000, unit: "tokens" },
          limit: { value: 1000000, unit: "tokens" },
          percentUsed: 34.5,
          percentOrigin: "source"
        },
        otherModels: { percentUsed: 25.5, percentOrigin: "source" }
      });
    }
  });

  it("calculates a same-unit percentage when the source omits it", () => {
    const payload = fixture<Record<string, unknown>>(
      "included-usage-healthy.json"
    );
    const cursorModels = payload.cursorModels as Record<string, unknown>;
    cursorModels.percentUsed = null;
    const result = normalizeSnapshotPayload(payload, {
      source: "credential-api",
      fetchedAt
    });
    expect(result.ok && result.value.cursorModels.percentUsed).toBe(34.5);
    expect(result.ok && result.value.cursorModels.percentOrigin).toBe(
      "calculated"
    );
  });

  it("preserves percentages above 100 without clamping", () => {
    const payload = fixture<Record<string, unknown>>(
      "included-usage-healthy.json"
    );
    const cursorModels = payload.cursorModels as Record<string, unknown>;
    cursorModels.percentUsed = 125.25;
    const result = normalizeSnapshotPayload(payload, {
      source: "credential-api"
    });
    expect(result.ok && result.value.cursorModels.percentUsed).toBe(125.25);
  });

  it("keeps unknown denominators absolute and stale", () => {
    const result = normalizeSnapshotPayload(
      fixture("unknown-denominator.json"),
      { source: "cache", cachedFrom: "credential-api" }
    );
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value.cursorModels).toMatchObject({
        limit: null,
        percentUsed: null,
        percentOrigin: null
      });
      expect(result.value).toMatchObject({
        source: "cache",
        stale: true,
        staleReason: "allowance-unavailable"
      });
    }
  });

  it("accepts an empty period without inventing allowances", () => {
    const result = normalizeSnapshotPayload(fixture("empty-period.json"), {
      source: "credential-api"
    });
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value.cursorModels).toMatchObject({
        used: { value: 0, unit: "tokens" },
        limit: null,
        percentUsed: null
      });
      expect(result.value.teamContext).toEqual({
        sharedSpendLimit: null,
        dynamicSpendLimit: null,
        sharedSpendUsed: null,
        sharedSpendRemaining: null
      });
    }
  });

  it("keeps personal spend separate from shared team context", () => {
    const payload = fixture<Record<string, unknown>>(
      "included-usage-healthy.json"
    );
    const onDemand = fixture<Record<string, unknown>>("on-demand-enabled.json");
    payload.onDemand = onDemand.onDemand;
    payload.teamContext = onDemand.teamContext;
    const result = normalizeSnapshotPayload(payload, {
      source: "credential-api"
    });
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value.onDemand.personalSpend).toEqual({
        amount: 12.5,
        currency: "USD"
      });
      expect(result.value.teamContext.sharedSpendLimit).toEqual({
        amount: 250,
        currency: "USD"
      });
      expect(result.value.teamContext).not.toHaveProperty(
        "personalAllocation"
      );
    }
  });

  it("rejects spend attached to disabled or unknown on-demand state", () => {
    const payload = fixture<Record<string, unknown>>(
      "included-usage-healthy.json"
    );
    payload.onDemand = {
      enabled: false,
      personalSpend: { amount: 1, currency: "USD" }
    };
    const result = normalizeSnapshotPayload(payload, {
      source: "credential-api"
    });
    expect(!result.ok && result.error.code).toBe("invalid-value");
  });

  it("requires a full ISO timestamp rather than permissive Date.parse input", () => {
    const payload = fixture<Record<string, unknown>>(
      "included-usage-healthy.json"
    );
    payload.freshness = {
      fetchedAt: "2026-08-04",
      stale: false,
      staleReason: null
    };
    const result = normalizeSnapshotPayload(payload, {
      source: "credential-api"
    });
    expect(!result.ok && result.error.code).toBe("invalid-value");
  });

  it.each([
    [null, "json-schema-mismatch"],
    [{}, "json-schema-mismatch"],
    [
      {
        ...fixture<Record<string, unknown>>("included-usage-healthy.json"),
        fetchedAt: "not-a-date",
        freshness: undefined
      },
      "invalid-value"
    ]
  ])("rejects malformed envelopes", (payload, code) => {
    const result = normalizeSnapshotPayload(payload, {
      source: "credential-api"
    });
    expect(!result.ok && result.error.code).toBe(code);
  });

  it("rejects mismatched numerator and denominator units", () => {
    const payload = fixture<Record<string, unknown>>(
      "included-usage-healthy.json"
    );
    const cursorModels = payload.cursorModels as Record<string, unknown>;
    cursorModels.limit = { value: 100, unit: "requests" };
    const result = normalizeSnapshotPayload(payload, {
      source: "credential-api"
    });
    expect(!result.ok && result.error.code).toBe("unit-mismatch");
  });
});

describe("normalizeHtmlUsage", () => {
  it("normalizes semantic spending and usage fixtures", () => {
    const result = normalizeHtmlUsage(
      fixture<string>("scrape-spending-page.html"),
      fixture<string>("scrape-usage-page.html"),
      fetchedAt
    );
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value).toMatchObject({
        source: "html-scrape",
        fetchedAt,
        period: {
          startsAt: "2026-08-01T00:00:00.000Z",
          resetsAt: "2026-09-01T00:00:00.000Z"
        },
        cursorModels: {
          used: { value: 144000, unit: "tokens" },
          percentUsed: 34.5,
          percentOrigin: "source"
        },
        otherModels: {
          used: { value: 96000, unit: "tokens" },
          percentUsed: 25.5
        },
        onDemand: {
          enabled: true,
          personalSpend: { amount: 12.5, currency: "USD" }
        },
        teamContext: {
          sharedSpendLimit: { amount: 250, currency: "USD" }
        }
      });
    }
  });

  it("ignores tags, comments, script, style, and fixture attributes", () => {
    const text = extractVisibleText(`
      <style>secret-style</style><!-- hidden -->
      <div data-fixture-test="ignored">Cursor &amp; Usage</div>
      <script>secret-script</script>
    `);
    expect(text).toBe("Cursor & Usage");
    expect(text).not.toContain("fixture");
    expect(text).not.toContain("secret");
  });

  it("rejects login pages before parsing usage", () => {
    const result = normalizeHtmlUsage(
      "<html><body>Sign in to Cursor</body></html>",
      fixture<string>("scrape-usage-page.html"),
      fetchedAt
    );
    expect(!result.ok && result.error.code).toBe("login-redirect");
  });

  it("classifies empty client shells separately from schema drift", () => {
    const empty = normalizeHtmlUsage("<div id='root'></div>", "", fetchedAt);
    expect(!empty.ok && empty.error.code).toBe("client-shell");

    const drift = normalizeHtmlUsage(
      "<main>Spending Cursor Models Other Models content changed completely</main>",
      fixture<string>("scrape-usage-page.html"),
      fetchedAt
    );
    expect(!drift.ok && drift.error.code).toBe("html-schema-mismatch");
  });

  it("rejects invalid fetch timestamps", () => {
    const result = normalizeHtmlUsage(
      fixture<string>("scrape-spending-page.html"),
      fixture<string>("scrape-usage-page.html"),
      "invalid"
    );
    expect(!result.ok && result.error.code).toBe("invalid-value");
  });
});
