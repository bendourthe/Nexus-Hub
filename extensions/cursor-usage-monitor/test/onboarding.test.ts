import { describe, expect, it } from "vitest";
import { isDashboardCommandForTest, renderDashboard } from "../src/dashboardPanel";
import { CONSENT_PROMPT_WILL_NOT_READ } from "../src/providers/consent";
import type { UsageState } from "../src/types";

/**
 * Tests for the first-run screen (v3.15.12 follow-on).
 *
 * The screen this replaces led with "Enter usage manually" as its primary action.
 * That is a dead end dressed as a feature: it asks the user to be the data source
 * without ever saying why, so the only readings available are "this extension is
 * broken" or "I have missed a setting somewhere".
 *
 * Neither is true, and the reason is not the one an earlier draft of this file gave.
 * That draft said no automatic connection was buildable because Cursor's PUBLIC
 * APIs are Enterprise-admin only. Phase 6 falsified it: Cursor's own client reads
 * personal usage through a verified RPC, so the screen's job is to obtain consent
 * for that, not to explain an absence.
 *
 * Manual entry remains for anyone who declines, with its weakness stated - a pasted
 * figure is frozen at the moment it was entered - because the original screen let a
 * stale number look like a live meter.
 *
 * These tests exist because that is a copy-and-affordance decision, and copy
 * regresses silently. They assert the shape of the guidance, not its wording.
 */

const EMPTY: UsageState = {
  state: "empty",
  error: { code: "authorization-required", surface: "credential-api", message: "No live session." }
} as UsageState;

function empty(): string {
  return renderDashboard(EMPTY);
}

describe("first-run screen", () => {
  it("offers connecting live tracking as the primary action", () => {
    // Phase 6 made automatic tracking real, so the headline action is consent, not
    // a link out and not manual entry. Primary means first, not merely present.
    const html = empty();
    const connect = html.indexOf('data-command="connectLive"');
    expect(connect).toBeGreaterThan(-1);
    expect(connect).toBeLessThan(html.indexOf('data-command="openUsagePage"'));
    expect(connect).toBeLessThan(html.indexOf('data-command="manualEntry"'));
  });

  it("no longer presents manual entry as an unexplained instruction", () => {
    // The old label asked the user to supply data with no reason given.
    expect(empty()).not.toContain("Enter usage manually");
  });

  it("still reaches manual entry for someone who declines", () => {
    // Demoted, not deleted: declining live access must not leave a dead end.
    const html = empty();
    expect(html).toContain('data-command="manualEntry"');
    expect(html).toContain("by hand");
  });

  it("explains why it is not connected without claiming it cannot be", () => {
    // Without an explanation, every other affordance reads as a workaround for a
    // bug. But the explanation must not overclaim either: an earlier draft said
    // Cursor "does not offer a personal usage API", which is false of the route
    // its own client calls, and would be a lie the next release has to walk back.
    const html = empty();
    expect(html).toContain("available, and off until you allow it");
    // Must not claim impossibility: the route is verified and works.
    expect(html).not.toContain("does not offer a personal usage API");
    expect(html).not.toContain("cannot connect on its own");
    // Must say consent is required and that nothing is read before it.
    expect(html).toContain("permission");
    expect(html).toContain("Nothing is read before you agree");
  });

  it("states that a pasted figure is a frozen snapshot", () => {
    // The honest weakness of the stopgap. Omitting it lets a stale number be read
    // as a live meter, which is the failure mode the rest of this extension exists
    // to prevent.
    const html = empty().toLowerCase();
    expect(html).toContain("snapshot");
    expect(html).toContain("frozen");
  });

  it("gives ordered steps a non-technical reader can follow", () => {
    const html = empty();
    expect(html).toContain("<ol>");
    expect(html.match(/<li>/gu)?.length ?? 0).toBeGreaterThanOrEqual(2);
  });

  it("renders the privacy claim from its single source of truth", () => {
    // A second copy of this claim is a copy that can drift out of true.
    const html = empty();
    for (const line of CONSENT_PROMPT_WILL_NOT_READ) {
      expect(html).toContain(line);
    }
  });

  it("demotes the raw provider message to a collapsed detail", () => {
    // A code like "authorization-required" is not a first-run headline.
    const html = empty();
    expect(html).toContain("<details");
    const detailsIndex = html.indexOf("<details");
    expect(html.indexOf("No live session.")).toBeGreaterThan(detailsIndex);
  });

  it("keeps every action reachable through the panel's own command guard", () => {
    // A button whose command the guard rejects is silently inert, which is worse
    // than an absent button: it looks like the feature is broken.
    const html = empty();
    for (const command of ["connectLive", "openUsagePage", "manualEntry", "settings"]) {
      expect(html).toContain(`data-command="${command}"`);
      expect(isDashboardCommandForTest(command)).toBe(true);
    }
  });

  it("offers the usage page from the populated dashboard too", () => {
    // The link is not only an onboarding crutch: it is where figures are verified.
    const populated = renderDashboard({
      state: "fresh",
      data: {
        fetchedAt: "2026-08-07T00:00:00.000Z",
        source: "manual",
        cachedFrom: null,
        cursorModels: { used: 10, limit: 100, percentUsed: 10 },
        otherModels: { used: null, limit: null, percentUsed: null },
        period: { startsAt: null, resetsAt: null },
        onDemand: { spend: null, limit: null, currency: null },
        teamContext: { sharedSpendLimit: null, dynamicSpendLimit: null }
      }
    } as unknown as UsageState);
    expect(populated).toContain('data-command="openUsagePage"');
  });
});
