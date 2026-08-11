import { beforeEach, describe, expect, it } from "vitest";
import {
  beginOwnerWrite,
  endOwnerWrite,
  ownerWriteInFlight,
  reconcileOwner,
  resetOwnerWriteGuard
} from "../src/providers/ownerReconcile";

/**
 * The scope/owner pair is only meaningful together, and nothing enforced that until
 * v3.16.4. Each case below is a state the extension actually reached.
 */
describe("owner reconciliation", () => {
  it("fixes the state that made the extension look permanently broken", () => {
    // Observed 2026-08-10: an organization was picked, then the VS Code account
    // preference moved back to the personal account. Scope stayed `organization`
    // while the owner became the user, so every fetch asked for
    // /organizations/bendourthe/... - a path that cannot exist.
    const result = reconcileOwner({ scope: "organization", owner: "bendourthe", login: "bendourthe" });
    expect(result.changed).toBe(true);
    expect(result.scope).toBe("user");
    expect(result.owner).toBe("bendourthe");
    expect(result.reason).toContain("not an organization");
  });

  it("follows the account when the user switches identity", () => {
    // Otherwise the monitor reports the previous account's billing under the new one.
    const result = reconcileOwner({ scope: "user", owner: "bendourthe", login: "benjamin-dourthe" });
    expect(result.changed).toBe(true);
    expect(result.owner).toBe("benjamin-dourthe");
  });

  it("records a detected owner when nothing is configured yet", () => {
    const result = reconcileOwner({ scope: "user", owner: "", login: "bendourthe" });
    expect(result.changed).toBe(true);
    expect(result.owner).toBe("bendourthe");
  });

  it("leaves a VALID organization selection alone", () => {
    // Self-healing must not undo a deliberate, working configuration.
    const result = reconcileOwner({
      scope: "organization",
      owner: "SupiraMedical",
      login: "benjamin-dourthe",
      organizations: ["SupiraMedical"]
    });
    expect(result.changed).toBe(false);
  });

  it("corrects an organization the account does not belong to", () => {
    const result = reconcileOwner({
      scope: "organization",
      owner: "SomeOtherOrg",
      login: "bendourthe",
      organizations: ["SupiraMedical"]
    });
    expect(result.changed).toBe(true);
    expect(result.scope).toBe("user");
  });

  it("does NOT treat an unavailable organization list as proof of non-membership", () => {
    // An offline or rate-limited lookup returns nothing. Acting on that would undo a
    // valid organization selection every time the request failed.
    expect(reconcileOwner({ scope: "organization", owner: "SupiraMedical", login: "benjamin-dourthe" }).changed).toBe(false);
    expect(reconcileOwner({ scope: "organization", owner: "SupiraMedical", login: "benjamin-dourthe", organizations: [] }).changed).toBe(false);
  });

  it("does nothing at all when no account is signed in", () => {
    // A signed-out state is not a mismatch, and rewriting configuration on the way
    // to the sign-in prompt would discard the user's choice.
    expect(reconcileOwner({ scope: "organization", owner: "SupiraMedical", login: null }).changed).toBe(false);
  });

  it("ignores case and surrounding whitespace, which GitHub logins do too", () => {
    expect(reconcileOwner({ scope: "user", owner: " BenDourthe ", login: "bendourthe" }).changed).toBe(false);
  });
});

/**
 * The half-written pair, observed 2026-08-11.
 *
 * Choosing organization SupiraMedical wrote `billingScope` first. The configuration
 * listener refreshed on that event alone, the healer judged the still-inconsistent
 * pair, and the explicitly chosen organization was reset to the personal account
 * before the second write had even landed.
 */
describe("owner write guard", () => {
  beforeEach(() => resetOwnerWriteGuard());

  it("marks the window between the pair's two writes", () => {
    expect(ownerWriteInFlight()).toBe(false);
    beginOwnerWrite();
    expect(ownerWriteInFlight()).toBe(true);
    endOwnerWrite();
    expect(ownerWriteInFlight()).toBe(false);
  });

  it("stays raised until the LAST overlapping write finishes", () => {
    // Two flows can write the pair at once - the sign-in picker and the settings UI.
    // A boolean would be cleared by whichever finished first, reopening the window.
    beginOwnerWrite();
    beginOwnerWrite();
    endOwnerWrite();
    expect(ownerWriteInFlight()).toBe(true);
    endOwnerWrite();
    expect(ownerWriteInFlight()).toBe(false);
  });

  it("never goes negative, so a stray end cannot disable the guard", () => {
    endOwnerWrite();
    endOwnerWrite();
    beginOwnerWrite();

    expect(ownerWriteInFlight()).toBe(true);
  });

  it("marks only the self-terminating corrections as safe to apply", () => {
    // The apply-vs-offer split is the structural fix for the flicker. A correction
    // may be written automatically ONLY if its result cannot re-trigger another rule.
    const impossible = reconcileOwner({ scope: "organization", owner: "bendourthe", login: "bendourthe" });
    expect(impossible.kind).toBe("impossible-pair");
    expect(impossible.safeToApply).toBe(true);
    // Its output must match nothing: that is what "self-terminating" means.
    expect(reconcileOwner({ scope: impossible.scope, owner: impossible.owner, login: "bendourthe" }).changed).toBe(false);

    const detected = reconcileOwner({ scope: "user", owner: "", login: "bendourthe" });
    expect(detected.kind).toBe("detected-owner");
    expect(detected.safeToApply).toBe(true);
    expect(reconcileOwner({ scope: detected.scope, owner: detected.owner, login: "bendourthe" }).changed).toBe(false);

    // And the one that cannot be applied, because its output IS another round's input.
    const switched = reconcileOwner({ scope: "user", owner: "benjamin-dourthe", login: "bendourthe" });
    expect(switched.kind).toBe("account-switch");
    expect(switched.safeToApply).toBe(false);

    const notMember = reconcileOwner({ scope: "organization", owner: "OtherOrg", login: "bendourthe", organizations: ["SupiraMedical"] });
    expect(notMember.safeToApply).toBe(false);
  });

  it("phrases an offered correction as a question, not as a done deed", () => {
    // It is no longer applied, so announcing it in the past tense would be false.
    expect(reconcileOwner({ scope: "user", owner: "benjamin-dourthe", login: "bendourthe" }).reason).toContain("?");
    expect(reconcileOwner({ scope: "organization", owner: "bendourthe", login: "bendourthe" }).reason).toContain("Switched");
  });

  it("would oscillate between two accounts if asked about the wrong session", () => {
    // The 2026-08-11 flicker, reproduced as pure logic. Two VS Code sessions exist -
    // a personal one holding `user` and a work one holding `repo, read:org` - and a
    // scopes-`[]` request can return either. Feeding the reconciler whichever came
    // back makes it rewrite the owner each time, and each rewrite fires a
    // configuration event that refreshes and reconciles again.
    let scope: "user" | "organization" = "user";
    let owner = "benjamin-dourthe";
    const logins = ["bendourthe", "benjamin-dourthe", "bendourthe", "benjamin-dourthe"];
    let rewrites = 0;

    for (const login of logins) {
      const result = reconcileOwner({ scope, owner, login });
      if (result.changed) {
        rewrites += 1;
        scope = result.scope as "user" | "organization";
        owner = result.owner;
      }
    }

    // Every single round rewrote it - the pair never settles while the session
    // answering the question keeps changing. The fix is upstream: ask for the
    // session that matches the CONFIGURED owner's scope set, so the answer is stable.
    expect(rewrites).toBe(logins.length);
  });

  it("settles immediately when asked about a single consistent session", () => {
    let scope: "user" | "organization" = "user";
    let owner = "benjamin-dourthe";
    let rewrites = 0;

    for (let round = 0; round < 4; round += 1) {
      const result = reconcileOwner({ scope, owner, login: "bendourthe" });
      if (result.changed) {
        rewrites += 1;
        scope = result.scope as "user" | "organization";
        owner = result.owner;
      }
    }

    expect(rewrites).toBe(1);
    expect(owner).toBe("bendourthe");
  });

  it("describes the exact transient state that must not be judged", () => {
    // This is what the healer saw mid-write, and why it acted: organization scope
    // against the signed-in user's own login is genuinely impossible as a FINAL
    // state. The rule is right; observing it at this moment was not.
    const midWrite = reconcileOwner({ scope: "organization", owner: "benjamin-dourthe", login: "benjamin-dourthe" });

    expect(midWrite.changed).toBe(true);
    expect(midWrite.scope).toBe("user");

    // And the state the user actually chose, which must survive untouched.
    const settled = reconcileOwner({ scope: "organization", owner: "SupiraMedical", login: "benjamin-dourthe" });

    expect(settled.changed).toBe(false);
  });
});
