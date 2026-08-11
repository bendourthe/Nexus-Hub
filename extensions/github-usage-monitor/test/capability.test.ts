import { describe, expect, it } from "vitest";
import type { ProbeRecord } from "../src/providers/authProbe";
import {
  CapabilityStore,
  SCOPE_CANDIDATES,
  capabilityFromProbe,
  capabilityKey,
  describeCapability,
  diagnoseBlockedReason,
  firstScopeCandidate,
  nextScopeEscalation,
  sessionFingerprint,
  type CapabilityStateLike
} from "../src/providers/capability";
import type { BillingOwner } from "../src/types";

const USER: BillingOwner = { scope: "user", name: "octocat" };
const ORG: BillingOwner = { scope: "organization", name: "Acme" };
const ENTERPRISE: BillingOwner = { scope: "enterprise", name: "acme-inc" };

function record(overrides: Partial<ProbeRecord> = {}): ProbeRecord {
  return {
    checkedAt: "2026-08-06T12:00:00.000Z",
    apiVersion: "2026-03-10",
    level: "organization",
    endpoint: "/organizations/acme/settings/billing/usage",
    credentialKind: "vscode-oauth",
    requestedScopes: ["repo"],
    providerReportedScopes: ["repo"],
    status: 200,
    grantedOAuthScopes: ["repo"],
    acceptedOAuthScopes: [],
    acceptedGitHubPermissions: null,
    requestId: null,
    error: null,
    ...overrides
  };
}

class FakeState implements CapabilityStateLike {
  public readonly values = new Map<string, unknown>();

  public get<T>(key: string): T | undefined {
    return this.values.get(key) as T | undefined;
  }

  public async update(key: string, value: unknown): Promise<void> {
    if (value === undefined) {
      this.values.delete(key);
    } else {
      this.values.set(key, value);
    }
  }
}

describe("scope candidates encode the T022c evidence", () => {
  it("leads organizations with repo, which was empirically sufficient", () => {
    // Three organizations returned 200 with repo alone, and VS Code's provider
    // requests repo routinely. admin:org is held back for explicit escalation.
    expect(SCOPE_CANDIDATES.organization[0]).toBe("repo");
    expect(SCOPE_CANDIDATES.organization).toContain("admin:org");
  });

  it("also requests read:org, which the Copilot subscription endpoint requires", () => {
    // Added 2026-08-11. `repo` reads billing usage and the organization plan, and
    // reads NOTHING from `GET /orgs/{org}/copilot/billing`, which documents exactly
    // two acceptable scopes: `manage_billing:copilot` or `read:org`. Without this the
    // AI-credit allowance could never be composed, and the panel said "no allowance
    // is known" for an organization that plainly has one.
    expect(firstScopeCandidate(ORG)).toEqual(["repo", "read:org"]);

    // The narrower of the two acceptable scopes, and read-only. `manage_billing:*`
    // carries write semantics this monitor has no business holding, and `admin:org`
    // stays behind an explicit escalation.
    expect(firstScopeCandidate(ORG)).not.toContain("manage_billing:copilot");
    expect(firstScopeCandidate(ORG)).not.toContain("admin:org");
  });

  it("uses the scope GitHub named for user scope", () => {
    expect(firstScopeCandidate(USER)).toEqual(["user"]);
  });

  it("uses the documented billing scope for enterprise", () => {
    expect(firstScopeCandidate(ENTERPRISE)).toEqual(["manage_billing:enterprise"]);
  });
});

describe("nextScopeEscalation", () => {
  it("escalates only when GitHub names a scope the credential lacks", () => {
    expect(
      nextScopeEscalation(ORG, {
        acceptedOAuthScopes: ["admin:org", "repo"],
        grantedOAuthScopes: ["gist", "read:org"]
      })
    ).toEqual(["repo"]);
  });

  it("refuses to escalate on a bare failure with no scope evidence", () => {
    // Retrying broader merely because narrower failed is how an extension ends up
    // holding admin:org it never needed.
    expect(
      nextScopeEscalation(ORG, {
        acceptedOAuthScopes: [],
        grantedOAuthScopes: ["repo"]
      })
    ).toBeNull();
  });

  it("refuses to escalate when the credential already carries an accepted scope", () => {
    expect(
      nextScopeEscalation(ORG, {
        acceptedOAuthScopes: ["admin:org", "repo"],
        grantedOAuthScopes: ["repo"]
      })
    ).toBeNull();
  });

  it("never proposes a scope outside the level's candidate list", () => {
    const escalation = nextScopeEscalation(USER, {
      acceptedOAuthScopes: ["admin:org", "delete_repo"],
      grantedOAuthScopes: []
    });
    expect(escalation).toBeNull();
  });
});

describe("diagnoseBlockedReason", () => {
  it("never blames the token class for a 401", () => {
    // A 401 is about the credential. Reporting it as token-type-unsupported would
    // be the exact misreading the probe's interpretation table warns about.
    expect(
      diagnoseBlockedReason(record({ status: 401, error: { message: "Bad credentials" } }))
    ).toBe("credential-invalid");
  });

  it("detects SSO and OAuth-app refusals from the message, before the scope reading", () => {
    expect(
      diagnoseBlockedReason(
        record({
          status: 403,
          acceptedOAuthScopes: ["admin:org"],
          error: { message: "Resource protected by organization SAML enforcement" }
        })
      )
    ).toBe("sso-authorization-required");

    expect(
      diagnoseBlockedReason(
        record({
          status: 403,
          acceptedOAuthScopes: ["admin:org"],
          error: { message: "Although you appear to have the correct authorization credentials, the organization has enabled OAuth App access restrictions" }
        })
      )
    ).toBe("oauth-app-approval-required");
  });

  it("names a scope gap when GitHub says what it accepts and the token lacks it", () => {
    expect(
      diagnoseBlockedReason(
        record({
          status: 404,
          grantedOAuthScopes: ["gist", "read:org", "repo", "workflow"],
          acceptedOAuthScopes: ["user"],
          error: { message: "Not Found" }
        })
      )
    ).toBe("insufficient-scope");
  });

  it("reads a bare 404 as enhanced billing unavailable, not a scope gap", () => {
    expect(
      diagnoseBlockedReason(
        record({ status: 404, acceptedOAuthScopes: [], error: { message: "Not Found" } })
      )
    ).toBe("enhanced-billing-unavailable");
  });

  it("falls back to insufficient role rather than inventing a cause", () => {
    expect(
      diagnoseBlockedReason(
        record({ status: 403, acceptedOAuthScopes: [], error: { message: "Forbidden" } })
      )
    ).toBe("insufficient-role");
  });
});

describe("capabilityFromProbe", () => {
  it("marks an OAuth success as probed-only, not documented", () => {
    const capability = capabilityFromProbe(record({ status: 200 }));
    expect(capability.status).toBe("supported");
    if (capability.status !== "supported") {
      return;
    }
    // GitHub's endpoint reference enumerates fine-grained support only, so an
    // OAuth 200 is real but undocumented. Recording it as documented would
    // overstate the evidence.
    expect(capability.evidence).toBe("probed-only");
    expect(capability.source).toBe("vscode-oauth");
    expect(capability.grantedScopes).toEqual(["repo"]);
  });

  it("marks a classic-PAT success as documented and probed", () => {
    const capability = capabilityFromProbe(
      record({ status: 200, credentialKind: "classic-pat" })
    );
    expect(capability.status === "supported" && capability.evidence).toBe(
      "documented-and-probed"
    );
  });

  it("carries the accepted scopes into a blocked verdict", () => {
    const capability = capabilityFromProbe(
      record({
        status: 404,
        acceptedOAuthScopes: ["user"],
        grantedOAuthScopes: ["repo"],
        error: { message: "Not Found" }
      })
    );
    expect(capability.status).toBe("blocked");
    if (capability.status !== "blocked") {
      return;
    }
    expect(capability.reason).toBe("insufficient-scope");
    expect(capability.acceptedScopes).toEqual(["user"]);
  });
});

describe("describeCapability", () => {
  it("explains every blocked reason without leaving the user guessing", () => {
    const reasons = [
      "insufficient-scope",
      "insufficient-role",
      "enhanced-billing-unavailable",
      "oauth-app-approval-required",
      "sso-authorization-required",
      "token-type-unsupported",
      "credential-invalid"
    ] as const;
    for (const reason of reasons) {
      const text = describeCapability({
        status: "blocked",
        reason,
        acceptedScopes: [],
        detail: "d",
        observedAt: "2026-08-06T12:00:00.000Z"
      });
      expect(text.length).toBeGreaterThan(20);
      expect(text).not.toContain("undefined");
    }
  });

  it("says a 401 says nothing about token classes", () => {
    const text = describeCapability({
      status: "blocked",
      reason: "credential-invalid",
      acceptedScopes: [],
      detail: "d",
      observedAt: "2026-08-06T12:00:00.000Z"
    });
    expect(text.toLowerCase()).toContain("says nothing about which token classes");
  });

  it("discloses that an OAuth success is undocumented", () => {
    const text = describeCapability(capabilityFromProbe(record({ status: 200 })));
    expect(text).toContain("does not document");
  });

  it("names the accepted scopes on a scope gap", () => {
    const text = describeCapability({
      status: "blocked",
      reason: "insufficient-scope",
      acceptedScopes: ["user"],
      detail: "d",
      observedAt: "2026-08-06T12:00:00.000Z"
    });
    expect(text).toContain("would accept: user");
  });
});

describe("CapabilityStore", () => {
  it("keys per target and treats level as part of the identity", () => {
    expect(capabilityKey(ORG)).toBe("organization:acme");
    // A user and an organization can share a slug, so the level must be in the key.
    expect(capabilityKey({ scope: "user", name: "Acme" })).not.toBe(
      capabilityKey(ORG)
    );
  });

  it("remembers a verdict per target and does not leak across targets", async () => {
    const store = new CapabilityStore(new FakeState());
    const fingerprint = sessionFingerprint("octocat", ["repo"]);
    await store.remember(ORG, fingerprint, capabilityFromProbe(record()));

    expect(store.get(ORG, fingerprint).status).toBe("supported");
    // One user can be supported on org A and blocked on org B; a global default
    // could not express that.
    expect(
      store.get({ scope: "organization", name: "other" }, fingerprint).status
    ).toBe("unknown");
  });

  it("invalidates a verdict when the session changes", async () => {
    const store = new CapabilityStore(new FakeState());
    await store.remember(ORG, sessionFingerprint("octocat", ["repo"]), capabilityFromProbe(record()));

    // A different account, or different scopes, is a different capability question.
    expect(store.get(ORG, sessionFingerprint("someone-else", ["repo"])).status).toBe("unknown");
    expect(store.get(ORG, sessionFingerprint("octocat", ["gist"])).status).toBe("unknown");
  });

  it("forgets one target and clears all", async () => {
    const store = new CapabilityStore(new FakeState());
    const fingerprint = sessionFingerprint("octocat", ["repo"]);
    await store.remember(ORG, fingerprint, capabilityFromProbe(record()));
    await store.remember(USER, fingerprint, capabilityFromProbe(record({ status: 200 })));

    await store.forget(ORG);
    expect(store.get(ORG, fingerprint).status).toBe("unknown");
    expect(store.get(USER, fingerprint).status).toBe("supported");

    await store.clear();
    expect(store.get(USER, fingerprint).status).toBe("unknown");
  });

  it("survives a corrupt stored value", () => {
    const state = new FakeState();
    state.values.set("githubUsageMonitor.authCapability", "not-an-object");
    expect(new CapabilityStore(state).get(ORG, "fp").status).toBe("unknown");
  });
});

describe("sessionFingerprint", () => {
  it("is derived from account and scopes, never from a token", () => {
    const fingerprint = sessionFingerprint("octocat", ["repo", "gist"]);
    expect(fingerprint).toContain("octocat");
    expect(fingerprint).not.toContain("gho_");
    expect(fingerprint).not.toContain("ghp_");
  });

  it("is order-insensitive so a reordered scope list is the same session", () => {
    expect(sessionFingerprint("octocat", ["repo", "gist"])).toBe(
      sessionFingerprint("octocat", ["gist", "repo"])
    );
  });

  it("distinguishes a missing account from a named one", () => {
    expect(sessionFingerprint(undefined, [])).not.toBe(
      sessionFingerprint("octocat", [])
    );
  });
});
