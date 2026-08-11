import { describe, expect, it } from "vitest";
import { renderDashboard } from "../src/dashboardPanel";
import { buildHoverMarkdown, GITHUB_BAR_FILL } from "../src/statusBarManager";
import { SCOPE_CANDIDATES } from "../src/providers/capability";
import { formatResetDateTime } from "../src/usageStore";
import type { UsageMetric, UsageSnapshot, UsageState } from "../src/types";

/**
 * One test per defect reported against the shipped v3.16.3 build.
 *
 * These are kept together deliberately. Every one describes something a user SAW,
 * and five of the six passed their own phase's tests while being visibly wrong. The
 * gap each time was between asserting that markup EXISTS and asserting that it
 * BEHAVES, so these assert behavior wherever that is reachable from a unit test.
 */

function metric(
  kind: UsageMetric["kind"],
  unit: string,
  used: number,
  allowance: number | null,
  drawdown: number | null
): UsageMetric {
  return {
    kind,
    unit,
    used,
    drawdown,
    drawdownBasis: drawdown === null ? "unavailable" : "reconstructed",
    allowance,
    allowanceSource: allowance === null ? "unknown" : "plan-table",
    allowanceState: allowance === null ? "unknown" : drawdown === null ? "unknown" : "verified",
    percentage: allowance === null || drawdown === null ? null : (drawdown / allowance) * 100,
    reset: { at: Date.UTC(2026, 8, 1, 0, 0), kind: "reporting-period", label: "Current UTC billing month" },
    breakdowns: [],
    grossAmount: 1,
    discountAmount: 1,
    netAmount: 0
  };
}

function snapshot(minutes: UsageMetric): UsageSnapshot {
  return {
    owner: { scope: "user", name: "bendourthe" },
    periodStart: Date.UTC(2026, 7, 1),
    periodEnd: Date.UTC(2026, 8, 1),
    fetchedAt: Date.UTC(2026, 7, 10),
    source: "api",
    stale: false,
    copilot: metric("copilot-ai-credits", "ai-credits", 0, null, null),
    actionsMinutes: minutes,
    actionsStorage: metric("actions-storage", "gigabytes", 0.09, 0.5, 0.09)
  };
}

describe("defect 4 - 1,362 minutes rendered as 0%", () => {
  it("never shows a percentage built from a drawdown of zero beside non-zero usage", () => {
    // The shipped panel read "1,362 minutes of 2,000 minutes (0%)": gross usage
    // beside a percentage derived from a drawdown of 0, because the private
    // repository failed to resolve and only public repositories counted.
    const broken = metric("actions-minutes", "minutes", 1362, 2000, null);
    const html = renderDashboard({ state: "fresh", data: snapshot(broken) });
    expect(html).not.toContain(">0%<");
    expect(html).toContain("1,362 minutes");
  });

  it("shows the drawdown, not gross consumption, as the headline when one exists", () => {
    // GitHub's own panel showed 126.7 of 2,000 for this account, so the monitor must
    // agree with that rather than reporting 1,362 minutes of gross consumption.
    const good = metric("actions-minutes", "minutes", 1362, 2000, 126.7);
    const html = renderDashboard({ state: "fresh", data: snapshot(good) });
    expect(html).toContain("126.7 minutes of 2,000 minutes");
    expect(html).toContain("6%");
    expect(html).not.toContain("1,362 minutes of 2,000");
  });
});

describe("defect 1 - hover bars did not match the sibling monitors", () => {
  const state: UsageState = {
    state: "fresh",
    data: snapshot(metric("actions-minutes", "minutes", 1362, 2000, 126.7))
  };

  it("draws an SVG progress bar rather than a run of Unicode blocks", () => {
    const hover = buildHoverMarkdown(state).value;
    expect(hover).toContain("data:image/svg+xml");
    // U+2588 FULL BLOCK - the v3.16.3 rendering, which could not show a rounded
    // track, a partial fill, or any value finer than 10%.
    expect(hover).not.toContain("█");
    expect(hover).not.toContain("&#9608;");
  });

  it("fills the bar with the visual contract's teal", () => {
    const decoded = decodeURIComponent(buildHoverMarkdown(state).value);
    expect(decoded).toContain(GITHUB_BAR_FILL);
    expect(GITHUB_BAR_FILL).toBe("#008080");
  });

  it("labels the bar for anyone who cannot see the image", () => {
    expect(buildHoverMarkdown(state).value).toContain('alt="Actions minutes"');
  });
});

describe("defect 3 - the settings gear did nothing", () => {
  const html = renderDashboard({
    state: "fresh",
    data: snapshot(metric("actions-minutes", "minutes", 10, 2000, 10))
  });

  it("does not rely on an inline handler, which the panel's own CSP blocks", () => {
    // The Claude monitor sets no Content-Security-Policy, so its inline onclick
    // works. This panel sets script-src 'nonce-...', which forbids inline event
    // handlers - so copying that markup shipped a control that could never fire.
    expect(html).toContain("script-src 'nonce-");
    expect(html).not.toContain('onclick="toggleSettings()"');
  });

  it("binds the gear inside the nonced script instead", () => {
    expect(html).toContain("getElementById('settings-toggle')");
    expect(html).toContain("addEventListener('click',()=>toggleSettings())");
  });
});

describe("defect 2 - billing detail was always expanded", () => {
  it("renders billing detail collapsed behind a disclosure", () => {
    const withRows = metric("actions-minutes", "minutes", 10, 2000, 10);
    withRows.breakdowns = [
      {
        product: "Actions",
        sku: "Actions Linux",
        unit: "minutes",
        grossQuantity: 10,
        discountQuantity: null,
        netQuantity: null,
        grossAmount: null,
        discountAmount: null,
        netAmount: null,
        repositoryName: "r"
      }
    ];
    const html = renderDashboard({ state: "fresh", data: snapshot(withRows) });
    expect(html).toContain('<details class="detail"><summary>Billing detail</summary>');
    expect(html).not.toContain('<details class="detail" open');
  });
});

describe("defect 5 - the panel did not match the sibling monitors", () => {
  const html = renderDashboard({
    state: "fresh",
    data: snapshot(metric("actions-minutes", "minutes", 10, 2000, 10))
  });

  it("uses the siblings' 500px centred column and uppercase section labels", () => {
    expect(html).toContain("max-width:500px");
    expect(html).toContain("text-transform:uppercase");
  });

  it("drops the marketing header, tagline, and in-page nav", () => {
    expect(html).not.toContain("<h1>");
    expect(html).not.toContain('class="eyebrow"');
    expect(html).not.toContain("<nav");
    // The same sentence survives inside the COLLAPSED settings section, where it
    // explains what the monitor reads. That is deliberate: the objection was to a
    // tagline occupying the top of the panel on every glance, not to the words
    // existing anywhere in the document.
    const body = html.slice(0, html.indexOf('<section id="settings-section"'));
    expect(body).not.toContain("Actions minutes and storage, plus Copilot billing");
  });
});

describe("defect 6 - reset showed a countdown, not a date", () => {
  it("formats an absolute date and time", () => {
    const formatted = formatResetDateTime(Date.UTC(2026, 8, 1, 0, 0), "en-US");
    expect(formatted).toMatch(/Aug|Sep/u);
    expect(formatted).not.toMatch(/^\d+h/u);
  });

  it("uses the date in the panel rather than a raw hour count", () => {
    const html = renderDashboard({
      state: "fresh",
      data: snapshot(metric("actions-minutes", "minutes", 10, 2000, 10))
    });
    expect(html).toContain("Resets ");
    expect(html).not.toContain("Current UTC billing month");
  });

  it("returns an honest string for an unusable timestamp instead of Invalid Date", () => {
    expect(formatResetDateTime(Number.NaN)).toBe("not reported");
  });
});

describe("private-repository visibility without a broad scope", () => {
  it("keeps the session request narrow", () => {
    // `repo` grants full read/write over every private repository. Requesting it
    // also invalidated the existing session and broke sign-in outright.
    expect(SCOPE_CANDIDATES.user).toEqual(["user"]);
    expect(SCOPE_CANDIDATES.user).not.toContain("repo");
  });

  it("reads a 404 as private, which is what removes the need for that scope", async () => {
    const { RepositoryVisibilityCache } = await import("../src/providers/repositories");
    // GET /repos/{owner}/{repo} answers for a public repository without special
    // permission and 404s for a private one. Every repository in this owner's
    // billing belongs to this owner, so 404 means private.
    const cache = new RepositoryVisibilityCache(async (path: string) =>
      path.includes("private-one")
        ? { ok: false as const, status: 404 }
        : { ok: true as const, value: { private: false } }
    );
    const visibility = await cache.resolve(["private-one", "public-one"], { token: "t", owner: "o" });
    expect(visibility["private-one"]).toBe("private");
    expect(visibility["public-one"]).toBe("public");
  });

  it("leaves any OTHER failure unresolved rather than guessing", async () => {
    const { RepositoryVisibilityCache } = await import("../src/providers/repositories");
    // A 500 or a rate-limit says nothing about visibility, and an unresolved
    // repository withholds the percentage entirely rather than skewing it.
    const cache = new RepositoryVisibilityCache(async () => ({ ok: false as const, status: 500 }));
    const visibility = await cache.resolve(["mystery"], { token: "t", owner: "o" });
    expect(visibility["mystery"]).toBeUndefined();
  });
});

describe("account switching and the trimmed settings panel", () => {
  it("requests repository scope on the switch-account path too", async () => {
    // The logIn command built its own scope list with SCOPE_CANDIDATES[level].slice(0, 1),
    // which requested `user` alone - so switching accounts silently undid private
    // repository visibility on the exact path a user takes to change accounts.
    const source = await import("node:fs/promises").then((fs) =>
      fs.readFile(new URL("../src/extension.ts", import.meta.url), "utf8")
    );
    expect(source).toContain("firstScopeCandidate({ scope: level");
    expect(source).not.toContain("SCOPE_CANDIDATES[level]?.slice(0, 1)");
  });

  it("tells an enterprise-managed account to change scope, not to find a bigger token", async () => {
    const { describeCapability } = await import("../src/providers/capability");
    const text = describeCapability({
      status: "blocked",
      reason: "insufficient-role",
      detail: "",
      checkedAt: 0,
      fingerprint: "f",
      source: "session",
      acceptedScopes: [],
      grantedScopes: []
    } as never);
    expect(text).toContain("organization");
    expect(text).toContain("enterprise");
  });
});

describe("account switching keeps both surfaces in step", () => {
  it("re-renders an OPEN panel on refresh, and does not open a closed one", async () => {
    const { DashboardPanel } = await import("../src/dashboardPanel");
    const { resetVscodeStub, webviewPanels } = await import("./vscode-stub");
    resetVscodeStub();
    const panel = new DashboardPanel();
    const state = { state: "fresh" as const, data: snapshot(metric("actions-minutes", "minutes", 10, 2000, 10)) };

    // A background refresh must never throw a tab in the user's face.
    panel.update(state);
    expect(webviewPanels).toHaveLength(0);

    // Once open, a refresh must reach it. The v3.16.3 build updated only the status
    // bar, so an account switch cleared the status-bar warning while the panel went
    // on showing the previous account's error.
    panel.show(state);
    expect(webviewPanels).toHaveLength(1);
    const before = webviewPanels[0]?.webview.html;
    panel.update({ state: "fresh", data: snapshot(metric("actions-minutes", "minutes", 999, 2000, 999)) });
    expect(webviewPanels[0]?.webview.html).not.toBe(before);
    expect(webviewPanels).toHaveLength(1);
  });

  it("only claims Copilot has no allowance where that is knowable", async () => {
    const { copilotAllowanceIsKnownAbsent } = await import("../src/providers/planEntitlements");
    // A personal Free account genuinely has no AI-credit entitlement.
    expect(copilotAllowanceIsKnownAbsent("user", "free")).toBe(true);
    // An organization seat is billed through Copilot Business or Enterprise, which
    // DOES include a monthly allowance - one this monitor cannot read. Claiming
    // "no allowance included with your plan" there is a false statement.
    expect(copilotAllowanceIsKnownAbsent("organization", "free")).toBe(false);
    expect(copilotAllowanceIsKnownAbsent("user", "pro")).toBe(false);
    expect(copilotAllowanceIsKnownAbsent("user", null)).toBe(false);
  });
});

describe("switching billing owner", () => {
  it("never serves another owner's cached snapshot as a fallback", async () => {
    const { UsageStore } = await import("../src/usageStore");
    const memory = new Map<string, unknown>();
    const store = new UsageStore({
      get: (key: string) => memory.get(key),
      update: async (key: string, value: unknown) => { memory.set(key, value); }
    } as never);

    const personal = snapshot(metric("actions-minutes", "minutes", 1362, 2000, 130));
    await store.resolveFetch({ ok: true, value: personal, rate: EMPTY_RATE } as never);

    const failure = {
      ok: false as const,
      error: { code: "invalid-scope" as const, message: "cannot read billing for this owner" },
      rate: EMPTY_RATE
    };

    // Same owner: the cache is a legitimate last-known-good fallback.
    const same = await store.resolveFetch(failure as never, Date.now(), { scope: "user", name: "bendourthe" });
    expect(same.state).toBe("stale");
    expect(same.data?.actionsMinutes.used).toBe(1362);

    // DIFFERENT owner: serving this would show the personal account's minutes under
    // the organization's name, which is what the maintainer saw after switching.
    const other = await store.resolveFetch(failure as never, Date.now(), { scope: "organization", name: "SupiraMedical" });
    expect(other.state).toBe("empty");
    expect(other.data).toBeUndefined();
  });

  it("refreshes when the billing owner changes by any route", async () => {
    const source = await import("node:fs/promises").then((fs) =>
      fs.readFile(new URL("../src/extension.ts", import.meta.url), "utf8")
    );
    // Refreshing only inside the logIn command left the settings-UI route stale.
    expect(source).toContain("onDidChangeConfiguration");
    expect(source).toContain('affectsConfiguration("githubUsageMonitor.billingOwner")');
  });
});

const EMPTY_RATE = { remaining: null, resetAt: null, retryAfterMs: null };
