import * as path from "path";
import * as os from "os";
import { afterEach, describe, expect, it, vi } from "vitest";

/**
 * Decision (1b) runtime check, beside the static one in account-selection:
 * during a full refresh (personal and organization fetches, cache, state file,
 * status bar, dashboard) the extension makes no filesystem read and starts no
 * process, so it cannot consult git configuration, a repository remote, or
 * the gh CLI's login. Its only filesystem writes go to the state file's folder.
 */
const io = vi.hoisted(() => ({ recording: false, fs: [] as string[], childProcess: [] as string[] }));

vi.mock("fs", async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>();
  const wrapped: Record<string, unknown> = {};
  for (const [name, value] of Object.entries(real)) {
    wrapped[name] =
      typeof value === "function"
        ? (...args: unknown[]) => {
            if (io.recording) io.fs.push(`${name} ${String(args[0])}`);
            return (value as (...a: unknown[]) => unknown)(...args);
          }
        : value;
  }
  return { ...wrapped, default: wrapped };
});

vi.mock("child_process", async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>();
  const wrapped: Record<string, unknown> = {};
  for (const [name, value] of Object.entries(real)) {
    wrapped[name] =
      typeof value === "function"
        ? (...args: unknown[]) => {
            io.childProcess.push(`${name} ${String(args[0])}`);
            throw new Error("the extension must not start processes");
          }
        : value;
  }
  return { ...wrapped, default: wrapped };
});

import * as fs from "fs";
import { DashboardPanel } from "../src/dashboardPanel";
import { CopilotUsageProvider } from "../src/providers/copilot";
import { CopilotOrganizationProvider, ORG_TOKEN_SECRET_KEY } from "../src/providers/copilotOrganization";
import { StatusBarManager } from "../src/statusBarManager";
import { UsageController } from "../src/usageController";
import { UsageService } from "../src/usageService";
import { UsageStore } from "../src/usageStore";
import { FakeGitHubAuth, FakeSecretStorage, ORG_TOKEN, WORK_TOKEN, createMemento, fixture, jsonResponse, routedFetch } from "./helpers";
import { __resetStubState, __setAuthentication, __setStubConfig, createdWebviewPanels, workspace } from "./vscode-stub";

afterEach(() => {
  for (const panel of createdWebviewPanels) panel.dispose();
  __resetStubState();
});

describe("a full refresh touches no identity source at runtime", () => {
  it("reads no file and starts no process; writes only the state file's folder", async () => {
    // Everything the run needs is loaded before recording starts.
    const bodies = {
      user: fixture("copilot-internal-user.business-member.json"),
      billing: fixture("copilot-billing.json"),
      usage: fixture("ai-credit-usage.near-limit.synthetic.json"),
    };
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "copilot-io-"));
    const repo = path.join(dir, "personal-repo");
    fs.mkdirSync(path.join(repo, ".git"), { recursive: true });
    fs.writeFileSync(path.join(repo, ".git", "config"), "[user]\n\temail = personal@example.invalid\n");
    workspace.workspaceFolders = [{ uri: { fsPath: repo }, name: "personal-repo", index: 0 }];
    __setAuthentication(new FakeGitHubAuth([{ id: "work", label: "w", token: WORK_TOKEN }]));
    __setStubConfig("copilotUsage", "organization", "acme-co");
    const secrets = new FakeSecretStorage();
    secrets.values.set(ORG_TOKEN_SECRET_KEY, ORG_TOKEN);
    const fake = routedFetch((url) =>
      url.pathname === "/copilot_internal/user"
        ? jsonResponse(bodies.user)
        : url.pathname.endsWith("/copilot/billing")
          ? jsonResponse(bodies.billing)
          : jsonResponse(bodies.usage),
    );
    const store = new UsageStore(createMemento());
    const bar = new StatusBarManager(store, "x");
    const stateDir = path.join(dir, "state", "usage-probe");
    const controller = new UsageController(
      store,
      new UsageService(new CopilotUsageProvider(undefined, fake.fetch), new CopilotOrganizationProvider(secrets.asSecretStorage(), fake.fetch)),
      bar,
      path.join(stateDir, "copilot.json"),
    );

    io.recording = true;
    try {
      await controller.refresh(Date.UTC(2026, 9, 5));
      bar.refresh();
      DashboardPanel.show(store.get(), "now", undefined, { configured: true, connected: true }, {
        onRefresh() {}, onOpenUsagePage() {}, onSignIn() {}, onSwitchAccount() {}, onConnectOrganization() {}, onDisconnectOrganization() {},
      });
    } finally {
      io.recording = false;
    }

    expect(io.childProcess).toEqual([]);
    const reads = io.fs.filter((call) => /^(read|exists|stat|lstat|open|access|readdir|readlink|realpath|watch)/i.test(call));
    expect(reads).toEqual([]);
    const touched = io.fs.map((call) => call.split(" ").slice(1).join(" "));
    expect(touched.length).toBeGreaterThan(0);
    for (const target of touched) {
      expect(path.resolve(target).startsWith(path.resolve(stateDir)), target).toBe(true);
    }
    expect(io.fs.some((call) => call.includes(".git"))).toBe(false);
    expect(fs.existsSync(path.join(stateDir, "copilot.json"))).toBe(true);
    fs.rmSync(dir, { recursive: true, force: true });
  });
});
