import { afterEach, describe, expect, it, vi } from "vitest";
import type { ProbeRecord } from "../src/providers/authProbe";
import {
  diagnoseTarget,
  summarizeOutcome,
  type ProbeWithTokenLike
} from "../src/providers/diagnose";
import type { GetSessionLike } from "../src/providers/sessionBinding";
import type { BillingOwner } from "../src/types";
import { resetVscodeStub } from "./vscode-stub";

const ORG: BillingOwner = { scope: "organization", name: "acme" };
const USER: BillingOwner = { scope: "user", name: "octocat" };
const TOKEN = "gho_fixturesessiontoken0123456789abcd";

function probeRecord(overrides: Partial<ProbeRecord> = {}): ProbeRecord {
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

function deps(
  record: ProbeRecord,
  session: Parameters<never> | undefined = undefined
): {
  getSession: ReturnType<typeof vi.fn>;
  probeWithToken: ReturnType<typeof vi.fn>;
} {
  void session;
  return {
    getSession: vi.fn<GetSessionLike>(async () => ({
      accessToken: TOKEN,
      scopes: ["repo"],
      account: { label: "octocat" }
    })),
    probeWithToken: vi.fn<ProbeWithTokenLike>(async () => record)
  };
}

afterEach(() => resetVscodeStub());

describe("diagnoseTarget", () => {
  it("acquires a session interactively, because the point is whether one CAN work", async () => {
    const dependencies = deps(probeRecord());
    await diagnoseTarget(dependencies, ORG);

    const options = dependencies.getSession.mock.calls[0]?.[2];
    expect(options?.createIfNone).toBe(true);
    expect(dependencies.getSession.mock.calls[0]?.[1]).toEqual(["repo", "read:org"]);
  });

  it("requests the level's candidate scope, not a broad one", async () => {
    const dependencies = deps(probeRecord({ level: "user" }));
    await diagnoseTarget(dependencies, USER);
    expect(dependencies.getSession.mock.calls[0]?.[1]).toEqual(["user"]);
  });

  it("records the capability and labels an OAuth success as probed-only", async () => {
    const outcome = await diagnoseTarget(deps(probeRecord()), ORG);
    expect(outcome.status).toBe("probed");
    if (outcome.status !== "probed") {
      return;
    }
    expect(outcome.capability.status).toBe("supported");
    expect(
      outcome.capability.status === "supported" && outcome.capability.evidence
    ).toBe("probed-only");
    expect(outcome.escalation).toBeNull();
  });

  it("keeps provider-reported scopes distinct from granted scopes", async () => {
    const dependencies = deps(
      probeRecord({ grantedOAuthScopes: ["repo"], providerReportedScopes: ["repo", "admin:org"] })
    );
    await diagnoseTarget(dependencies, ORG);
    // The editor reports what was REQUESTED. Passing it as granted would read a
    // narrowed consent as a full grant.
    const passed = dependencies.probeWithToken.mock.calls[0]?.[0];
    expect(passed?.providerReportedScopes).toEqual(["repo"]);
    expect(passed?.credentialKind).toBe("vscode-oauth");
  });

  it("reports no-session when the user declines, without probing", async () => {
    const probe = vi.fn<ProbeWithTokenLike>();
    const outcome = await diagnoseTarget(
      { getSession: async () => undefined, probeWithToken: probe },
      ORG
    );
    expect(outcome.status).toBe("no-session");
    expect(probe).not.toHaveBeenCalled();
  });

  it("offers an escalation only when GitHub's header names a missing scope", async () => {
    const blocked = await diagnoseTarget(
      deps(
        probeRecord({
          status: 403,
          grantedOAuthScopes: ["gist"],
          acceptedOAuthScopes: ["admin:org", "repo"],
          error: { message: "Forbidden" }
        })
      ),
      ORG
    );
    expect(blocked.status === "probed" && blocked.escalation).toEqual(["repo"]);

    const noEvidence = await diagnoseTarget(
      deps(
        probeRecord({
          status: 403,
          grantedOAuthScopes: ["repo"],
          acceptedOAuthScopes: [],
          error: { message: "Forbidden" }
        })
      ),
      ORG
    );
    // No scope evidence means no offer. Retrying broader on a bare failure is the
    // silent-broadening this whole path exists to avoid.
    expect(noEvidence.status === "probed" && noEvidence.escalation).toBeNull();
  });

  it("never returns the token in its outcome", async () => {
    const outcome = await diagnoseTarget(deps(probeRecord()), ORG);
    const serialized = JSON.stringify(outcome);
    expect(serialized).not.toContain(TOKEN);
    expect(serialized).not.toContain("gho_");
  });

  it("honours an explicitly escalated scope on a second run", async () => {
    const dependencies = deps(probeRecord());
    await diagnoseTarget(dependencies, ORG, ["admin:org"]);
    expect(dependencies.getSession.mock.calls[0]?.[1]).toEqual(["admin:org"]);
  });
});

describe("summarizeOutcome", () => {
  it("says nothing was checked and nothing changed when no session is granted", () => {
    const text = summarizeOutcome({ status: "no-session" }, ORG);
    expect(text).toContain("nothing was checked");
    expect(text).toContain("unchanged");
  });

  it("names the target on success", async () => {
    const outcome = await diagnoseTarget(deps(probeRecord()), ORG);
    const text = summarizeOutcome(outcome, ORG);
    expect(text).toContain("organization acme");
    expect(text).toContain("works");
  });

  it("names the accepted scope and the retry offer when blocked", async () => {
    const outcome = await diagnoseTarget(
      deps(
        probeRecord({
          status: 403,
          grantedOAuthScopes: ["gist"],
          acceptedOAuthScopes: ["repo"],
          error: { message: "Forbidden" }
        })
      ),
      ORG
    );
    const text = summarizeOutcome(outcome, ORG);
    expect(text).toContain("would accept: repo");
    expect(text).toContain("retry requesting repo");
    // A bare "blocked" is what sends a user hunting for a broader credential.
    expect(text).not.toBe("blocked");
  });

  it("never claims a recorded verdict for an inconclusive result", async () => {
    const outcome = await diagnoseTarget(deps(probeRecord()), ORG);
    if (outcome.status !== "probed") {
      return;
    }
    const text = summarizeOutcome(
      { ...outcome, capability: { status: "unknown" } },
      ORG
    );
    expect(text).toContain("inconclusive");
    expect(text).toContain("not been recorded");
  });
});
