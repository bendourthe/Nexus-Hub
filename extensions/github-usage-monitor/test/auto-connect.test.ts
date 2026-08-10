import { describe, expect, it } from "vitest";
import { resolveCredential, describeCredentialSource } from "../src/providers/credentialResolver";
import { billingPageUrl, resolveEffectiveOwner } from "../src/providers/scope";
import type { BillingAuthCapability } from "../src/providers/capability";
import type { BillingOwner } from "../src/types";

/**
 * Tests for the auto-connect wiring (v3.15.12 follow-on).
 *
 * The defect these guard against is specific and worth naming, because it is the
 * kind that a passing suite hides: Phase 4 built the per-target auth model, tested
 * it thoroughly, and wired it to the settings panel and the diagnostic command
 * ONLY. The refresh path still read SecretStorage directly, so a user signed in to
 * GitHub in the editor saw "No billing data available" forever. Every Phase 4 test
 * passed, because they tested the model rather than its use.
 *
 * So these tests assert the DATA PATH's choice of credential, not the model's
 * opinion about it, and they assert the two things a no-setup connection needs:
 * an owner that can be derived from the session, and a link to the real page.
 */

const ORG: BillingOwner = { scope: "organization", name: "supira" };
const USER: BillingOwner = { scope: "user", name: "bendourthe" };

const UNKNOWN: BillingAuthCapability = { status: "unknown" };

function deps(overrides: {
  stored?: string | undefined;
  session?: { accessToken: string; scopes: string[]; account?: { label: string } } | undefined;
  capability?: BillingAuthCapability;
  onGetSession?: (scopes: readonly string[], options: unknown) => void;
}) {
  const stored = overrides.stored;
  return {
    hasStoredToken: async () => stored !== undefined,
    readStoredToken: async () => stored,
    capability: overrides.capability ?? UNKNOWN,
    getSession: async (_id: string, scopes: readonly string[], options: unknown) => {
      overrides.onGetSession?.(scopes, options);
      return overrides.session as never;
    }
  };
}

describe("resolveCredential", () => {
  it("prefers an explicitly stored token over an available session", async () => {
    // Storing a PAT is a deliberate act. Silently preferring a session would
    // override an explicit choice the user made for a reason (a broader scope).
    const result = await resolveCredential(
      deps({ stored: "pat-value", session: { accessToken: "session-value", scopes: ["repo"] } }),
      ORG
    );
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.source).toBe("stored-pat");
      expect(result.token).toBe("pat-value");
    }
  });

  it("falls back to the editor session so no setup is required", async () => {
    const result = await resolveCredential(
      deps({ session: { accessToken: "session-value", scopes: ["repo", "user"] } }),
      ORG
    );
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.source).toBe("editor-session");
      expect(result.token).toBe("session-value");
      expect(result.scopes).toEqual(["repo", "user"]);
    }
  });

  it("never raises a sign-in dialog from a background refresh", async () => {
    // A monitor that pops a modal on a timer is worse than one that shows nothing.
    let seen: unknown;
    await resolveCredential(
      deps({ session: undefined, onGetSession: (_scopes, options) => { seen = options; } }),
      ORG
    );
    expect(seen).toMatchObject({ createIfNone: false, silent: true });
  });

  it("skips a target already known to be blocked instead of refailing on a timer", async () => {
    let called = false;
    const result = await resolveCredential(
      deps({
        capability: { status: "blocked", reason: "insufficient-scope" } as BillingAuthCapability,
        session: { accessToken: "session-value", scopes: [] },
        onGetSession: () => { called = true; }
      }),
      ORG
    );
    expect(called).toBe(false);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error.message).toContain("insufficient-scope");
    }
  });

  it("reuses the scopes already known to work for a supported target", async () => {
    let requested: readonly string[] = [];
    await resolveCredential(
      deps({
        capability: {
          status: "supported",
          via: "probed-only",
          grantedScopes: ["repo"]
        } as BillingAuthCapability,
        session: { accessToken: "t", scopes: ["repo"] },
        onGetSession: (scopes) => { requested = scopes; }
      }),
      ORG
    );
    expect(requested).toEqual(["repo"]);
  });

  it("names both recovery actions when nothing is available", async () => {
    const result = await resolveCredential(deps({ session: undefined }), ORG);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      // `not-connected`, not `missing-token`: having no credential at all is a
      // different situation from having one that is rejected, and v3.16.3 Phase 3
      // gives them different UI - one is answered by connecting, the other by
      // fixing a permission. Collapsing them made an unconnected install present
      // as a failure rather than as a starting point.
      expect(result.error.code).toBe("not-connected");
      // A dead end is the defect. Both ways forward must be named.
      expect(result.error.message).toContain("Log In or Switch Account");
      expect(result.error.message).toContain("Set Token");
    }
  });

  it("treats a throwing secret store as an absent token rather than a hard failure", async () => {
    const result = await resolveCredential(
      {
        hasStoredToken: async () => { throw new Error("keychain locked"); },
        readStoredToken: async () => undefined,
        capability: UNKNOWN,
        getSession: async () => ({ accessToken: "session-value", scopes: [] }) as never
      },
      ORG
    );
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.source).toBe("editor-session");
  });

  it("describes a source without ever naming the credential", () => {
    expect(describeCredentialSource("stored-pat")).toBe("stored token");
    expect(describeCredentialSource("editor-session")).toBe("the editor's GitHub session");
  });
});

describe("billingPageUrl", () => {
  it("routes personal billing off the signed-in account, not the slug", () => {
    // github.com/users/<name>/settings/billing does not exist; only /settings/billing.
    expect(billingPageUrl(USER)).toBe("https://github.com/settings/billing");
  });

  it("uses the organization and enterprise billing routes", () => {
    expect(billingPageUrl(ORG)).toBe("https://github.com/organizations/supira/settings/billing");
    expect(billingPageUrl({ scope: "enterprise", name: "acme-inc" })).toBe(
      "https://github.com/enterprises/acme-inc/settings/billing"
    );
  });

  it("is always an https github.com url", () => {
    for (const owner of [USER, ORG, { scope: "enterprise", name: "e" } as BillingOwner]) {
      const url = new URL(billingPageUrl(owner));
      expect(url.protocol).toBe("https:");
      expect(url.host).toBe("github.com");
    }
  });
});

describe("resolveEffectiveOwner", () => {
  it("derives a personal owner from the signed-in account when unconfigured", () => {
    const result = resolveEffectiveOwner("user", "", "bendourthe");
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.owner).toEqual({ scope: "user", name: "bendourthe" });
  });

  it("keeps explicit configuration ahead of the session label", () => {
    const result = resolveEffectiveOwner("user", "someone-else", "bendourthe");
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.owner.name).toBe("someone-else");
  });

  it("never guesses an organization or enterprise slug from the account label", () => {
    // A personal account name is not an org slug. Guessing would query the wrong
    // owner and report someone else's spend, or 404 confusingly.
    for (const scope of ["organization", "enterprise"]) {
      expect(resolveEffectiveOwner(scope, "", "bendourthe").ok).toBe(false);
    }
  });

  it("still validates a session-derived name", () => {
    expect(resolveEffectiveOwner("user", "", "not a valid name").ok).toBe(false);
  });

  it("fails cleanly when there is neither configuration nor a session", () => {
    expect(resolveEffectiveOwner("user", "", null).ok).toBe(false);
  });
});
