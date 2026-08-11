import { afterEach, describe, expect, it } from "vitest";
import { activate } from "../src/extension";
import {
  authenticationAccounts,
  resetVscodeStub,
  runCommand,
  sessionRequests,
  sessionResponses,
  setConfiguration,
  stubExtension,
  Uri
} from "./vscode-stub";

/**
 * Sessions must be requested FOR AN ACCOUNT, not merely for a scope list.
 *
 * The defect every other 2026-08-11 symptom was downstream of. A scope list is a
 * permission grant, not an identity: with two GitHub accounts signed in to the
 * editor, `getSession("github", ["user"], ...)` returns either one and not stably.
 * The panel alternated between a correct reading and a 404 for the SAME configured
 * owner, because `/users/bendourthe/settings/billing/...` succeeds with bendourthe's
 * token and 404s with the other account's.
 */

function context(): Parameters<typeof activate>[0] {
  const store = new Map<string, unknown>();
  return {
    secrets: {
      get: async () => undefined,
      store: async () => undefined,
      delete: async () => undefined
    },
    subscriptions: [],
    extension: stubExtension(),
    extensionUri: Uri.file("fixture-extension"),
    globalState: {
      get: (key: string, fallback?: unknown) => (store.has(key) ? store.get(key) : fallback),
      update: async (key: string, value: unknown) => {
        if (value === undefined) store.delete(key);
        else store.set(key, value);
      },
      keys: () => [...store.keys()]
    }
  } as unknown as Parameters<typeof activate>[0];
}

afterEach(() => resetVscodeStub());

describe("account-pinned session requests", () => {
  it("pins to the recorded account so two signed-in accounts cannot alternate", async () => {
    authenticationAccounts.push({ id: "1", label: "bendourthe" }, { id: "2", label: "benjamin-dourthe" });
    setConfiguration("githubUsageMonitor.autoFetch", false);
    const host = context();
    await host.globalState.update("githubUsageMonitor.boundAccount", "bendourthe");
    await activate(host);

    sessionRequests.length = 0;
    sessionResponses.push(undefined);
    await runCommand("githubUsageMonitor.dashboard");

    const pinned = sessionRequests.find((request) => request.providerId === "github");
    expect(pinned).toBeDefined();
    // The account travels with the request. Without it the provider is free to
    // answer with the other account, which is the whole failure.
    expect((pinned?.options as { account?: { label?: string } }).account?.label).toBe("bendourthe");
  });

  it("does NOT pin when the user is explicitly switching accounts", async () => {
    // `clearSessionPreference` IS the "let me choose" signal. Pinning it to the
    // account already recorded would make the Switch button unable to switch.
    authenticationAccounts.push({ id: "1", label: "bendourthe" });
    setConfiguration("githubUsageMonitor.autoFetch", false);
    const host = context();
    await host.globalState.update("githubUsageMonitor.boundAccount", "bendourthe");
    await activate(host);

    sessionRequests.length = 0;
    sessionResponses.push(undefined);
    await runCommand("githubUsageMonitor.logIn");

    const switching = sessionRequests.find(
      (request) => (request.options as { clearSessionPreference?: boolean }).clearSessionPreference === true
    );
    expect(switching).toBeDefined();
    expect((switching?.options as { account?: unknown }).account).toBeUndefined();
  });

  it("falls back to an unpinned request when the recorded account is gone", async () => {
    // A recorded account the provider no longer knows must not be passed through:
    // the request would fail outright rather than degrade, turning a signed-out
    // account into a broken extension.
    authenticationAccounts.push({ id: "2", label: "benjamin-dourthe" });
    setConfiguration("githubUsageMonitor.autoFetch", false);
    const host = context();
    await host.globalState.update("githubUsageMonitor.boundAccount", "someone-who-left");
    await activate(host);

    sessionRequests.length = 0;
    sessionResponses.push(undefined);
    await runCommand("githubUsageMonitor.dashboard");

    const request = sessionRequests.find((entry) => entry.providerId === "github");
    expect(request).toBeDefined();
    expect((request?.options as { account?: unknown }).account).toBeUndefined();
  });

  it("makes no account lookup when nothing has been recorded", async () => {
    authenticationAccounts.push({ id: "1", label: "bendourthe" });
    setConfiguration("githubUsageMonitor.autoFetch", false);
    const host = context();
    await activate(host);

    sessionRequests.length = 0;
    sessionResponses.push(undefined);
    await runCommand("githubUsageMonitor.dashboard");

    const request = sessionRequests.find((entry) => entry.providerId === "github");
    expect((request?.options as { account?: unknown }).account).toBeUndefined();
  });
});
