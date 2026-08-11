import { describe, expect, it } from "vitest";
import { BOUND_ACCOUNT_KEY, SIGNED_OUT_KEY, isBoundAccount, resetReconciliationBreaker, signedOutState } from "../src/extension";
import { isNotConnected } from "../src/statusBarManager";
import { renderDashboard } from "../src/dashboardPanel";

/**
 * Sign-out has to be a RECORDED fact, not an inferred one.
 *
 * This extension deliberately cannot end VS Code's GitHub session, because Copilot
 * shares it. So the session outlives the log-out, the next silent peek finds it, and
 * before 2026-08-11 the monitor reconnected itself within one refresh - the Log out
 * button appeared to do nothing at all, with the same figures left on screen.
 */
describe("signed-out state", () => {
  it("renders the connect screen, not a failure", () => {
    const state = signedOutState();

    // `isNotConnected` is what routes the panel to the Connect screen; any other
    // error code would render this as a red "no billing data" error instead.
    expect(isNotConnected(state)).toBe(true);
    expect(state.data).toBeUndefined();
    expect(state.error?.code).toBe("not-connected");
  });

  it("says signed out rather than implying a failure", () => {
    const message = signedOutState().error?.message ?? "";

    expect(message).toContain("Signed out");
    expect(message).toContain("Log in");
    expect(message.toLowerCase()).not.toContain("error");
    expect(message.toLowerCase()).not.toContain("failed");
  });

  it("carries no stale figures through to the panel", () => {
    const html = renderDashboard(signedOutState(), Date.UTC(2026, 7, 11));

    expect(html).toContain('data-command="logIn"');
    // The whole point of clearing the store on log-out: a "signed out" panel that
    // still shows last-known-good numbers is the same lie in a different place.
    expect(html).not.toContain("credits of");
    expect(html).not.toContain("minutes of");
  });

  it("uses a namespaced key, so it cannot collide with another extension's state", () => {
    expect(SIGNED_OUT_KEY).toBe("githubUsageMonitor.signedOut");
    expect(BOUND_ACCOUNT_KEY).toBe("githubUsageMonitor.boundAccount");
  });
});

/**
 * The recorded choice, which is what finally stops the oscillation.
 *
 * Scoping the session request was not enough: BOTH of this user's GitHub accounts
 * hold a `user`-scoped session, so the scope set does not identify the account and
 * `getSession` kept answering with whichever one it liked. Only a fact the user
 * established - the account they picked - identifies it.
 */
describe("bound account identity", () => {
  it("accepts only the account the user actually bound", () => {
    expect(isBoundAccount("benjamin-dourthe", "benjamin-dourthe")).toBe(true);
    // The other account's session must not be reconciled against, however often
    // VS Code hands it back.
    expect(isBoundAccount("bendourthe", "benjamin-dourthe")).toBe(false);
  });

  it("compares the way GitHub logins compare", () => {
    expect(isBoundAccount(" BenDourthe ", "bendourthe")).toBe(true);
  });

  it("stays permissive when nothing has been recorded yet", () => {
    // A first run, and an upgrade from a build that stored no label, must behave
    // exactly as before rather than refusing to reconcile at all.
    expect(isBoundAccount("anyone", null)).toBe(true);
    expect(isBoundAccount("anyone", "")).toBe(true);
    expect(isBoundAccount(null, null)).toBe(true);
  });

  it("rejects an absent session once an account IS recorded", () => {
    // Nothing signed in is not the bound account, so no correction may be inferred.
    expect(isBoundAccount(null, "benjamin-dourthe")).toBe(false);
  });

  it("exposes a breaker reset, so an explicit sign-in is never blocked by it", () => {
    // The circuit breaker goes inert after repeated automatic corrections. An
    // explicit sign-in is a fresh question and must not inherit that verdict.
    expect(() => resetReconciliationBreaker()).not.toThrow();
  });

  it("breaks the oscillation that the scope fix alone did not", () => {
    // Replays the alternating logins from the live report. With a recorded account,
    // every foreign answer is discarded, so the pair is judged at most on the rounds
    // that genuinely belong to it.
    const observed = ["bendourthe", "benjamin-dourthe", "bendourthe", "benjamin-dourthe"];
    const acted = observed.filter((login) => isBoundAccount(login, "benjamin-dourthe"));

    expect(acted).toEqual(["benjamin-dourthe", "benjamin-dourthe"]);
  });
});
