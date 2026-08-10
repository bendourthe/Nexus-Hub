import { afterEach, describe, expect, it, vi } from "vitest";
import {
  capabilityFromProbe,
  sessionFingerprint
} from "../src/providers/capability";
import {
  bindingFromSession,
  describeBinding,
  isCompleteLogOut,
  logInToMonitor,
  logOutOfMonitor,
  peekBinding,
  type GetSessionLike,
  type GitHubSessionLike,
  type MonitorOwnedState
} from "../src/providers/sessionBinding";
import { activate } from "../src/extension";
import { renderAuthSection, renderSettings, readSettings } from "../src/settingsPanel";
import type { BillingOwner } from "../src/types";
import {
  messages,
  resetVscodeStub,
  runCommand,
  sessionRequests,
  sessionResponses,
  setConfiguration,
  Uri
} from "./vscode-stub";

const ORG: BillingOwner = { scope: "organization", name: "acme" };
const USER: BillingOwner = { scope: "user", name: "octocat" };
const TOKEN = "gho_fixturesessiontoken0123456789abcd";

function session(
  overrides: Partial<GitHubSessionLike> = {}
): GitHubSessionLike {
  return {
    accessToken: TOKEN,
    scopes: ["repo"],
    account: { label: "octocat" },
    ...overrides
  };
}

function ownedState(): {
  owned: MonitorOwnedState;
  calls: string[];
} {
  const calls: string[] = [];
  return {
    calls,
    owned: {
      clearToken: async () => {
        calls.push("clearToken");
      },
      clearCapabilities: async () => {
        calls.push("clearCapabilities");
      },
      clearSessionPreference: async () => {
        calls.push("clearSessionPreference");
      }
    }
  };
}

afterEach(() => resetVscodeStub());

describe("peekBinding", () => {
  it("never prompts during discovery", async () => {
    const getSession = vi.fn<GetSessionLike>(async () => session());
    await peekBinding(getSession, ORG);

    const options = getSession.mock.calls[0]?.[2];
    // Activation must not raise an auth dialog: the user opened an editor.
    expect(options?.createIfNone).toBe(false);
    expect(options?.silent).toBe(true);
  });

  it("asks for the narrowest candidate scope for the level", async () => {
    const getSession = vi.fn<GetSessionLike>(async () => session());
    await peekBinding(getSession, ORG);
    // repo was empirically sufficient for organizations; admin:org is not
    // requested speculatively.
    expect(getSession.mock.calls[0]?.[1]).toEqual(["repo"]);

    getSession.mockClear();
    await peekBinding(getSession, USER);
    expect(getSession.mock.calls[0]?.[1]).toEqual(["user"]);
  });

  it("returns null when no session exists, without throwing", async () => {
    expect(await peekBinding(async () => undefined, ORG)).toBeNull();
  });
});

describe("logInToMonitor", () => {
  it("clears the session preference so GitHub shows the account picker", async () => {
    const getSession = vi.fn<GetSessionLike>(async () => session());
    await logInToMonitor(getSession, ORG);

    const options = getSession.mock.calls[0]?.[2];
    expect(options?.createIfNone).toBe(true);
    // Without this the editor silently reuses the previously chosen account, which
    // defeats the entire point: the billing account may differ from Copilot's.
    expect(options?.clearSessionPreference).toBe(true);
  });

  it("returns null when the user dismisses the picker", async () => {
    expect(await logInToMonitor(async () => undefined, ORG)).toBeNull();
  });

  it("accepts an explicit escalated scope rather than assuming one", async () => {
    const getSession = vi.fn<GetSessionLike>(async () => session());
    await logInToMonitor(getSession, ORG, ["admin:org"]);
    expect(getSession.mock.calls[0]?.[1]).toEqual(["admin:org"]);
  });
});

describe("logOutOfMonitor isolation", () => {
  it("clears exactly this extension's three pieces of state", async () => {
    const { owned, calls } = ownedState();
    const result = await logOutOfMonitor(owned);

    expect(calls.sort()).toEqual([
      "clearCapabilities",
      "clearSessionPreference",
      "clearToken"
    ]);
    expect(isCompleteLogOut(result)).toBe(true);
  });

  it("cannot reach the editor's GitHub session, by construction", () => {
    const { owned } = ownedState();
    // The guarantee is structural, not documentary: the injected surface has no
    // sign-out, revoke, or delete member, so no edit to the body of
    // logOutOfMonitor can end a session that Copilot also uses.
    expect(Object.keys(owned).sort()).toEqual([
      "clearCapabilities",
      "clearSessionPreference",
      "clearToken"
    ]);
    for (const forbidden of [
      "signOut",
      "revoke",
      "removeSession",
      "deleteSession",
      "logout"
    ]) {
      expect(owned).not.toHaveProperty(forbidden);
    }
    // And its call signature takes no session provider at all.
    expect(logOutOfMonitor.length).toBe(1);
  });

  it("still clears the rest when one step fails", async () => {
    const calls: string[] = [];
    const result = await logOutOfMonitor({
      clearToken: async () => {
        throw new Error("secret storage unavailable");
      },
      clearCapabilities: async () => {
        calls.push("clearCapabilities");
      },
      clearSessionPreference: async () => {
        calls.push("clearSessionPreference");
      }
    });

    // A partial log-out that kept the token would be worse than a loud failure.
    expect(result.clearedToken).toBe(false);
    expect(result.clearedCapabilities).toBe(true);
    expect(result.clearedPreference).toBe(true);
    expect(isCompleteLogOut(result)).toBe(false);
    expect(calls).toHaveLength(2);
  });
});

describe("bindingFromSession", () => {
  it("records the account and scopes but never the token", () => {
    const binding = bindingFromSession(session());
    expect(binding.accountLabel).toBe("octocat");
    expect(binding.scopes).toEqual(["repo"]);
    expect(JSON.stringify(binding)).not.toContain(TOKEN);
    expect(JSON.stringify(binding)).not.toContain("gho_");
  });

  it("derives a fingerprint that matches the capability store's", () => {
    expect(bindingFromSession(session()).fingerprint).toBe(
      sessionFingerprint("octocat", ["repo"])
    );
  });

  it("tolerates a session with no account label", () => {
    const binding = bindingFromSession(session({ account: undefined }));
    expect(binding.accountLabel).toBeNull();
    expect(binding.fingerprint).toContain("none");
  });
});

describe("describeBinding", () => {
  it("always names the account, because it may not be Copilot's", () => {
    expect(describeBinding(bindingFromSession(session()))).toContain("octocat");
    expect(describeBinding(bindingFromSession(session()))).toContain(
      "independent of the account Copilot uses"
    );
  });

  it("says so plainly when nothing is bound", () => {
    const text = describeBinding(null);
    expect(text).toContain("Not connected");
    expect(text).toContain("may differ from the account Copilot uses");
  });
});

describe("registered log in / log out commands are not inert", () => {
  /**
   * v3.15.11 shipped a hook that was registered and permanently non-functional
   * (BG-9/BG-10). A registered-but-unexercised command is the same defect class,
   * so these run the real command handlers through activation.
   */
  function context(): Parameters<typeof activate>[0] {
    const secrets = new Map<string, string>();
    const global = new Map<string, unknown>();
    return {
      subscriptions: [],
      extensionUri: Uri.file("ext"),
      secrets: {
        get: async (key: string) => secrets.get(key),
        store: async (key: string, value: string) => void secrets.set(key, value),
        delete: async (key: string) => void secrets.delete(key)
      },
      globalState: {
        get: (key: string) => global.get(key),
        update: async (key: string, value: unknown) => {
          if (value === undefined) global.delete(key); else global.set(key, value);
        }
      }
    } as unknown as Parameters<typeof activate>[0];
  }

  it("registers both commands", async () => {
    setConfiguration("githubUsageMonitor.autoFetch", false);
    setConfiguration("githubUsageMonitor.billingOwner", "acme");
    setConfiguration("githubUsageMonitor.billingScope", "organization");
    await activate(context());
    expect(() => runCommand("githubUsageMonitor.logIn")).not.toThrow();
    expect(() => runCommand("githubUsageMonitor.logOut")).not.toThrow();
  });

  it("log in requests the account picker with the level's candidate scope", async () => {
    setConfiguration("githubUsageMonitor.autoFetch", false);
    setConfiguration("githubUsageMonitor.billingOwner", "acme");
    setConfiguration("githubUsageMonitor.billingScope", "organization");
    await activate(context());

    sessionResponses.push(undefined); // the silent peek inside authDisplay
    sessionResponses.push(session()); // the interactive log-in
    await runCommand("githubUsageMonitor.logIn");

    const interactive = sessionRequests.find(
      (request) => (request.options as { createIfNone?: boolean }).createIfNone === true
    );
    expect(interactive).toBeDefined();
    expect(interactive?.providerId).toBe("github");
    expect(interactive?.scopes).toEqual(["repo"]);
    expect(
      (interactive?.options as { clearSessionPreference?: boolean }).clearSessionPreference
    ).toBe(true);
  });

  it("log out never calls getSession with createIfNone, so no sign-in or sign-out is triggered", async () => {
    setConfiguration("githubUsageMonitor.autoFetch", false);
    setConfiguration("githubUsageMonitor.billingOwner", "acme");
    setConfiguration("githubUsageMonitor.billingScope", "organization");
    await activate(context());
    sessionRequests.length = 0;

    await runCommand("githubUsageMonitor.logOut");

    // Any getSession during log-out must be the silent re-peek for the refreshed
    // panel, never an interactive call. Nothing here can end the shared session.
    for (const request of sessionRequests) {
      const options = request.options as { createIfNone?: boolean; clearSessionPreference?: boolean };
      expect(options.createIfNone).toBe(false);
      expect(options.clearSessionPreference).toBeUndefined();
    }
    expect(messages.information.join(" ")).toContain("Copilot is unaffected");
  });
});

describe("settings panel auth section", () => {
  const probe = {
    checkedAt: "2026-08-06T12:00:00.000Z",
    apiVersion: "2026-03-10",
    level: "organization" as const,
    endpoint: "/organizations/acme/settings/billing/usage",
    credentialKind: "vscode-oauth" as const,
    requestedScopes: ["repo"],
    providerReportedScopes: ["repo"],
    status: 200,
    grantedOAuthScopes: ["repo"],
    acceptedOAuthScopes: [],
    acceptedGitHubPermissions: null,
    requestId: null,
    error: null
  };

  it("names the target, the account, and the verdict", () => {
    const html = renderAuthSection({
      binding: bindingFromSession(session()),
      target: "organization:acme",
      capability: capabilityFromProbe(probe),
      hasStoredToken: false
    });

    expect(html).toContain("Connected");
    expect(html).toContain("organization:acme");
    expect(html).toContain("octocat");
    expect(html).toContain("logIn");
    expect(html).toContain("logOut");
  });

  it("states that logging out leaves Copilot alone", () => {
    const html = renderAuthSection({
      binding: null,
      target: "user:octocat",
      capability: { status: "unknown" },
      hasStoredToken: false
    });
    expect(html).toContain("never signs you out");
    expect(html).toContain("Copilot is unaffected");
    expect(html).toContain("Not checked");
  });

  it("shows a blocked reason rather than only a failure", () => {
    const html = renderAuthSection({
      binding: bindingFromSession(session()),
      target: "organization:acme",
      capability: capabilityFromProbe({
        ...probe,
        status: 404,
        acceptedOAuthScopes: ["user"],
        error: { message: "Not Found" }
      }),
      hasStoredToken: false
    });
    expect(html).toContain("Blocked");
    expect(html).toContain("missing a scope");
    expect(html).toContain("would accept: user");
  });

  it("never renders a token, and escapes what it renders", () => {
    const html = renderAuthSection({
      binding: bindingFromSession(
        session({ account: { label: "<script>alert(1)</script>" } })
      ),
      target: "organization:acme",
      capability: capabilityFromProbe(probe),
      hasStoredToken: true
    });
    expect(html).not.toContain(TOKEN);
    expect(html).not.toContain("<script>");
    expect(html).toContain("&lt;script&gt;");
  });

  it("is omitted entirely when no auth state is supplied", () => {
    const html = renderSettings(readSettings());
    expect(html).not.toContain("Authorization</legend>");
    expect(html).toContain("GitHub Usage Monitor Settings");
  });
});
