import { describe, expect, it } from "vitest";
import {
  FIRST_RUN_DECLINED_KEY,
  runFirstRunConnection,
  type FirstRunDependencies
} from "../src/providers/firstRun";
import { isNotConnected, buildHoverMarkdown, buildStatusText } from "../src/statusBarManager";
import { renderDashboard } from "../src/dashboardPanel";
import { activate } from "../src/extension";
import { Uri, configurationLog, readUserConfiguration, resetVscodeStub, setUserConfiguration, stubExtension } from "./vscode-stub";
import type { BillingScope, UsageState } from "../src/types";

const SCOPE: BillingScope = "user";

interface Recorded {
  scopes: readonly string[];
  options: { createIfNone?: boolean; silent?: boolean; clearSessionPreference?: boolean };
}

/**
 * Builds dependencies with a scripted session provider.
 *
 * `sessions` is consumed in order, so a test states exactly what the silent peek and
 * the interactive call each return.
 */
function deps(options: {
  sessions?: Array<{ accessToken: string; scopes: string[]; account?: { label: string } } | undefined>;
  stored?: boolean;
  declined?: boolean;
  onCall?: (call: Recorded) => void;
  throwOnInteractive?: boolean;
}): FirstRunDependencies & { calls: Recorded[]; declineWrites: Array<boolean | undefined> } {
  const sessions = [...(options.sessions ?? [])];
  const calls: Recorded[] = [];
  const declineWrites: Array<boolean | undefined> = [];
  let declined = options.declined ?? false;
  return {
    calls,
    declineWrites,
    scope: SCOPE,
    hasStoredToken: async () => options.stored ?? false,
    isDeclined: () => declined,
    recordDecline: async () => { declined = true; declineWrites.push(true); },
    clearDecline: async () => { declined = false; declineWrites.push(undefined); },
    getSession: async (_id, scopes, sessionOptions) => {
      const call = { scopes: [...scopes], options: sessionOptions };
      calls.push(call);
      options.onCall?.(call);
      if (options.throwOnInteractive === true && sessionOptions.createIfNone === true) {
        throw new Error("provider unavailable");
      }
      return sessions.shift() as never;
    }
  };
}

const interactiveCalls = (calls: Recorded[]): Recorded[] =>
  calls.filter((call) => call.options.createIfNone === true);

describe("first-run connection", () => {
  it("connects silently when a session already exists, with ZERO prompts", async () => {
    // Many users are already signed in to GitHub in the editor. Prompting them at
    // all would be a defect, so the assertion is on the count, not on the outcome.
    const dependencies = deps({ sessions: [{ accessToken: "tok", scopes: ["repo"], account: { label: "bendourthe" } }] });
    const result = await runFirstRunConnection(dependencies);

    expect(result.outcome).toMatchObject({ status: "connected", interactive: false });
    expect(result.interactiveAttempts).toBe(0);
    expect(interactiveCalls(dependencies.calls)).toHaveLength(0);
    expect(dependencies.calls[0]?.options).toMatchObject({ createIfNone: false, silent: true });
  });

  it("opens the sign-in flow EXACTLY once when there is no session", async () => {
    // This count is the single number separating correct behaviour from a modal on
    // every VS Code start, so it is asserted directly rather than through a proxy.
    const dependencies = deps({ sessions: [undefined, { accessToken: "tok", scopes: ["repo"] }] });
    const result = await runFirstRunConnection(dependencies);

    expect(result.interactiveAttempts).toBe(1);
    expect(interactiveCalls(dependencies.calls)).toHaveLength(1);
    expect(result.outcome).toMatchObject({ status: "connected", interactive: true });
  });

  it("records a durable decline when the user dismisses the flow", async () => {
    const dependencies = deps({ sessions: [undefined, undefined] });
    const result = await runFirstRunConnection(dependencies);

    expect(result.outcome).toEqual({ status: "declined" });
    expect(dependencies.declineWrites).toEqual([true]);
  });

  it("never prompts again after a decline, across any number of activations", async () => {
    const dependencies = deps({ sessions: [undefined, undefined] });
    await runFirstRunConnection(dependencies);
    const before = interactiveCalls(dependencies.calls).length;

    // Three further activations. A per-session flag would pass a single re-run and
    // fail here, which is the point of looping.
    for (let activation = 0; activation < 3; activation += 1) {
      dependencies.calls.length = 0;
      const again = await runFirstRunConnection(dependencies);
      expect(again.outcome).toEqual({ status: "skipped", reason: "previously-declined" });
      expect(again.interactiveAttempts).toBe(0);
      expect(interactiveCalls(dependencies.calls)).toHaveLength(0);
    }
    expect(before).toBe(1);
  });

  it("suppresses the flow entirely when a token is already stored", async () => {
    // Storing a PAT is a deliberate act that answers the question already.
    const dependencies = deps({ sessions: [undefined], stored: true });
    const result = await runFirstRunConnection(dependencies);

    expect(result.outcome).toEqual({ status: "skipped", reason: "stored-token" });
    expect(result.interactiveAttempts).toBe(0);
  });

  it("clears a previous decline when a connection later succeeds", async () => {
    // A user who changes their mind must not stay in a state that suppresses future
    // automatic connection.
    const dependencies = deps({ sessions: [undefined, { accessToken: "tok", scopes: ["repo"] }], declined: false });
    await runFirstRunConnection(dependencies);
    expect(dependencies.declineWrites).toEqual([undefined]);
  });

  it("requests the account picker on the interactive call", async () => {
    // clearSessionPreference is what makes the billing account able to differ from
    // the account Copilot uses.
    const dependencies = deps({ sessions: [undefined, { accessToken: "tok", scopes: ["repo"] }] });
    await runFirstRunConnection(dependencies);
    expect(interactiveCalls(dependencies.calls)[0]?.options).toMatchObject({ clearSessionPreference: true });
  });

  it("treats a failing auth provider as a decline rather than throwing", async () => {
    // Activation runs alongside this. A throw here would leave the user with no
    // extension at all rather than an unconnected one.
    const dependencies = deps({ sessions: [undefined], throwOnInteractive: true });
    const result = await runFirstRunConnection(dependencies);

    expect(result.outcome).toEqual({ status: "declined" });
    expect(result.interactiveAttempts).toBe(1);
  });

  it("exports a namespaced decline key so it cannot collide with the sibling monitors", () => {
    expect(FIRST_RUN_DECLINED_KEY).toBe("githubUsageMonitor.firstRun.declined");
  });
});

describe("unconnected presentation", () => {
  const notConnected: UsageState = {
    state: "empty",
    error: { code: "not-connected", message: 'Not connected to GitHub. Run "GitHub Usage Monitor: Log In or Switch Account".' }
  };
  const otherFailure: UsageState = {
    state: "empty",
    error: { code: "rate-limited", message: "Rate limited." }
  };

  it("distinguishes no-credential from a failed request", () => {
    expect(isNotConnected(notConnected)).toBe(true);
    expect(isNotConnected(otherFailure)).toBe(false);
    expect(isNotConnected({ state: "empty" })).toBe(false);
  });

  it("says Not connected in the status bar rather than the failed-to-load dashes", () => {
    expect(buildStatusText(undefined, false, false, true)).toContain("Not connected");
    expect(buildStatusText(undefined, false, false, true)).not.toContain("--");
    // A genuine failure keeps the existing treatment.
    expect(buildStatusText(undefined, false, false, false)).toContain("--");
  });

  it("explains in the hover what is read, and that clicking connects", () => {
    const hover = buildHoverMarkdown(notConnected).value;
    expect(hover).toContain("Not connected");
    expect(hover).toContain("never reads your code");
    expect(hover).toContain("connect");
  });

  it("renders a purposeful empty state with one primary action, not an error", () => {
    const html = renderDashboard(notConnected);
    expect(html).toContain('data-command="logIn"');
    expect(html).toContain("What it reads");
    expect(html).toContain("What it does not read");
    // A decline is a valid state. Styling it as a failure is inaccurate and is
    // nagging by other means.
    expect(html).not.toContain("notice error");
    expect(html).not.toContain("No billing data available");
  });

  it("still styles a genuine failure as an error", () => {
    const html = renderDashboard(otherFailure);
    expect(html).toContain("notice error");
    expect(html).toContain("No billing data available");
  });
});

describe("activation ordering (closes v3.16.3 Phase 1 MT-1)", () => {
  it("migrates settings BEFORE anything reads configuration", async () => {
    // Phase 1 made `activate` async precisely so migration could not race the first
    // configuration read. Asserting the final value alone would pass even if the
    // read won the race, so this asserts the SEQUENCE from the stub's access log.
    resetVscodeStub();
    setUserConfiguration("githubUsage.staleAfterMinutes", 5);
    setUserConfiguration("githubUsage.autoFetch", false);

    const state = new Map<string, unknown>();
    await activate({
      secrets: {
        get: async () => undefined,
        store: async () => undefined,
        delete: async () => undefined
      },
      subscriptions: [],
      extension: stubExtension(),
      extensionUri: Uri.file("fixture-extension"),
      globalState: {
        get: <T,>(key: string): T | undefined => state.get(key) as T | undefined,
        update: async (key: string, value: unknown) => {
          if (value === undefined) state.delete(key); else state.set(key, value);
        }
      }
    } as never);

    const migrationWrite = configurationLog.findIndex(
      (entry) => entry.op === "update" && entry.id === "githubUsageMonitor.staleAfterMinutes"
    );
    const firstRead = configurationLog.findIndex(
      (entry) => entry.op === "get" && entry.id === "githubUsageMonitor.staleAfterMinutes"
    );

    expect(migrationWrite).toBeGreaterThanOrEqual(0);
    expect(firstRead).toBeGreaterThanOrEqual(0);
    expect(migrationWrite).toBeLessThan(firstRead);
    // And the read observed the migrated value, not the default.
    expect(readUserConfiguration("githubUsageMonitor.staleAfterMinutes")).toBe(5);
  });
});
