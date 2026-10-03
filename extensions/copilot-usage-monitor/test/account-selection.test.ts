import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { CopilotUsageProvider, switchAccount } from "../src/providers/copilot";
import { CopilotOrganizationProvider } from "../src/providers/copilotOrganization";
import { DashboardPanel } from "../src/dashboardPanel";
import { StatusBarManager } from "../src/statusBarManager";
import { UsageController } from "../src/usageController";
import { UsageService } from "../src/usageService";
import { UsageStore } from "../src/usageStore";
import { FakeGitHubAuth, FakeSecretStorage, PERSONAL_TOKEN, WORK_TOKEN, createMemento, fixtureFetch } from "./helpers";
import { __resetStubState, __setAuthentication, createdStatusBarItems, createdWebviewPanels, workspace } from "./vscode-stub";

/**
 * Decision file v4.13.7, Copilot usage monitor (1b), required acceptance test:
 * the monitor reads the GitHub account pinned for the extension, never the
 * open repository's remote or git identity.
 */
const work = { id: "work-id", label: "work-account", token: WORK_TOKEN };
const personal = { id: "personal-id", label: "personal-account", token: PERSONAL_TOKEN };
const callbacks = {
  onRefresh: () => {},
  onOpenUsagePage: () => {},
  onSignIn: () => {},
  onSwitchAccount: () => {},
  onConnectOrganization: () => {},
  onDisconnectOrganization: () => {},
};

let workspaceDir: string;

beforeEach(() => {
  // A workspace whose git remote and user.email belong to the personal account.
  workspaceDir = fs.mkdtempSync(path.join(os.tmpdir(), "copilot-personal-repo-"));
  fs.mkdirSync(path.join(workspaceDir, ".git"));
  fs.writeFileSync(
    path.join(workspaceDir, ".git", "config"),
    [
      "[remote \"origin\"]",
      "\turl = https://github.com/personal-account/side-project.git",
      "[user]",
      "\temail = personal-account@users.noreply.github.com",
      "",
    ].join("\n"),
  );
  workspace.workspaceFolders = [{ uri: { fsPath: workspaceDir }, name: "side-project", index: 0 }];
});

afterEach(() => {
  for (const panel of createdWebviewPanels) panel.dispose();
  __resetStubState();
  fs.rmSync(workspaceDir, { recursive: true, force: true });
});

function harness(auth: FakeGitHubAuth) {
  __setAuthentication(auth);
  const fake = fixtureFetch({
    personalByToken: {
      [WORK_TOKEN]: "copilot-internal-user.business-member.json",
      [PERSONAL_TOKEN]: "copilot-internal-user.personal.json",
    },
  });
  const store = new UsageStore(createMemento());
  const statusBar = new StatusBarManager(store, "copilot-usage.dashboard");
  const service = new UsageService(
    new CopilotUsageProvider(undefined, fake.fetch),
    new CopilotOrganizationProvider(new FakeSecretStorage().asSecretStorage(), fake.fetch),
  );
  const statePath = path.join(workspaceDir, "state-not-used.json");
  const controller = new UsageController(store, service, statusBar, statePath);
  return { fake, store, controller, item: () => createdStatusBarItems[0] };
}

describe("account selection follows the extension's pinned account (decision 1b)", () => {
  it("shows the work seat's member view in a personal repository, then the Free plan after switching the pin", async () => {
    const auth = new FakeGitHubAuth([personal, work]);
    auth.preference = "work-id";
    const h = harness(auth);

    await h.controller.refresh();
    // The provider asked VS Code without naming an account, so the pin decided.
    expect(auth.calls.every((c) => !("account" in c.options))).toBe(true);
    expect(h.fake.calls).toHaveLength(1);
    expect(h.fake.calls[0].authorization).toBe(`token ${WORK_TOKEN}`);
    expect(JSON.stringify(h.fake.calls)).not.toContain(PERSONAL_TOKEN);
    // A Business seat with no personal limit: no percentage, and never a credit count.
    expect(h.item().text).toBe("$(copilot-icon)\u2002Copilot: --% (month)");
    expect(h.item().text).not.toContain("credits");
    DashboardPanel.show(h.store.get(), "just now", undefined, { configured: false, connected: false }, callbacks);
    const memberHtml = createdWebviewPanels[0].webview.html;
    expect(memberHtml).toContain("Copilot Business");
    expect(memberHtml).toContain("--% (month)");
    expect(memberHtml).toContain("Connect Organization");

    // Switch the pin only; the workspace and its git identity stay the same.
    auth.preference = "personal-id";
    await h.controller.refresh();
    expect(h.fake.calls).toHaveLength(2);
    expect(h.fake.calls[1].authorization).toBe(`token ${PERSONAL_TOKEN}`);
    expect(h.item().text).toBe("$(copilot-icon)\u2002Copilot: 0% (month)");
    DashboardPanel.updateIfOpen(h.store.get(), "just now", undefined);
    expect(createdWebviewPanels[0].webview.html).toContain("Copilot Free");
    expect(workspace.workspaceFolders?.[0].uri.fsPath).toBe(workspaceDir);
  });

  it("the Switch GitHub account command changes the pin through VS Code, then the view follows", async () => {
    const auth = new FakeGitHubAuth([personal, work]);
    auth.preference = "work-id";
    const h = harness(auth);
    await h.controller.refresh();
    expect(h.item().text).toContain("--% (month)");

    auth.pickOnPrompt = "personal-id";
    expect(await switchAccount(auth)).toBe(true);
    await h.controller.refresh();
    expect(h.item().text).toContain("0% (month)");
  });

  it("with two accounts and no pin, shows Choose GitHub account and never prompts on a background refresh", async () => {
    const auth = new FakeGitHubAuth([personal, work]);
    const h = harness(auth);
    await h.controller.refresh();
    expect(h.fake.calls).toHaveLength(0);
    expect(auth.calls.every((c) => c.options.silent === true && !c.options.createIfNone)).toBe(true);
    expect(h.controller.lastFetchError).toEqual({ code: "choose-account" });
    expect(h.item().text).toBe("$(copilot-icon)\u2002Copilot: --% (month)");
    expect(h.item().tooltip).toContain("Choose which GitHub account");
    DashboardPanel.show(undefined, "never", h.controller.lastFetchError, { configured: false, connected: false }, callbacks);
    expect(createdWebviewPanels[0].webview.html).toContain("Choose GitHub account");
  });
});

describe("the extension source reads no other identity source (decision 1b static check)", () => {
  const srcDir = path.join(__dirname, "..", "src");
  const files = fs
    .readdirSync(srcDir, { recursive: true, withFileTypes: true })
    .filter((entry) => entry.isFile() && entry.name.endsWith(".ts"))
    .map((entry) => path.join(entry.parentPath ?? (entry as unknown as { path: string }).path, entry.name));

  it("covers every source file", () => {
    expect(files.length).toBeGreaterThanOrEqual(15);
  });

  it.each([
    [/\.git[\\/]+config/, "a .git/config read"],
    [/git\s+config/, "a git config invocation"],
    [/hosts\.yml/, "the gh CLI's hosts.yml"],
    [/child_process/, "a child process (git or gh invocation)"],
    [/["'`]gh["'`]/, "a gh command"],
    [/\bexecFile|\bspawn\(|\bexec\(/, "a process spawn"],
    [/remote\.origin|user\.email|user\.name/, "git identity keys"],
    [/workspaceFolders/, "the open workspace"],
    [/\baccount\s*:/, "an explicit account passed to getSession"],
    [/getExtension\(\s*["'`]vscode\.git/, "the built-in Git extension's API"],
    [/\brootPath\b/, "the workspace root path"],
    [/\bfindFiles\b/, "a workspace file search"],
    [/hosts\.ya?ml/, "gh CLI hosts files"],
    [/\bimport\(\s*[^"'`\s]/, "a dynamic import with a computed argument"],
    [/\brequire\(\s*[^"'`\s)]/, "a require with a computed argument"],
    [/["'`]\.git["'`]/, "a .git path segment"],
    [/\.gitconfig|GIT_DIR|GIT_CONFIG/, "git configuration locations"],
  ])("contains no %s (%s)", (pattern) => {
    const offenders = files.filter((file) => pattern.test(fs.readFileSync(file, "utf-8")));
    expect(offenders).toEqual([]);
  });
});
