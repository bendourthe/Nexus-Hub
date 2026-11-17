import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { describeLayout, installAgentSplit, LAYOUT_KEY, mergedGroup, vscodeSplitHost, type AgentGroup, type AgentLayout, type SplitHost } from "../src/agentSplit";
import { TabInputCustom, TabInputWebview, Uri, stub, type StubTabGroup } from "./vscode-stub";

const claude = (index: number) => ({ kind: "claude" as const, index });
const codex = (index: number) => ({ kind: "codex" as const, index });
const split: AgentGroup[] = [{ column: 1, tabs: [claude(0)] }, { column: 2, tabs: [codex(0)] }];
const merged: AgentGroup[] = [{ column: 1, tabs: [claude(0), codex(1)] }];

describe("layout description", () => {
  it("needs both agents and tells a split from a merge", () => {
    expect(describeLayout([])).toBeUndefined();
    expect(describeLayout([{ column: 1, tabs: [claude(0)] }])).toBeUndefined();
    expect(describeLayout(split)).toEqual({ apart: true, rightKind: "codex" });
    expect(describeLayout([{ column: 1, tabs: [codex(0)] }, { column: 3, tabs: [claude(0)] }])).toEqual({ apart: true, rightKind: "claude" });
    expect(describeLayout(merged)?.apart).toBe(false);
  });
  it("finds a merge only when one group holds both agents", () => {
    expect(mergedGroup(merged)).toBe(merged[0]);
    expect(mergedGroup(split)).toBeUndefined();
    expect(mergedGroup([{ column: 1, tabs: [claude(0)] }])).toBeUndefined();
  });
});

describe("agent split restore", () => {
  let groups: AgentGroup[];
  let saved: AgentLayout | undefined;
  let tabListeners: (() => void)[];
  let enabled: boolean;
  let trusted: boolean;
  let moves: [number, number, string][];
  let host: SplitHost;
  const fire = (): void => tabListeners.forEach((listener) => listener());

  beforeEach(() => {
    vi.useFakeTimers();
    groups = [];
    saved = undefined;
    tabListeners = [];
    enabled = true;
    trusted = true;
    moves = [];
    host = {
      enabled: () => enabled,
      trusted: () => trusted,
      snapshot: () => groups,
      onDidChangeTabs: (listener) => { tabListeners.push(listener); return { dispose: () => void tabListeners.splice(tabListeners.indexOf(listener), 1) }; },
      read: () => saved,
      write: (layout) => { saved = layout; },
      moveRight: async (column, index, kind) => { moves.push([column, index, kind]); groups = split; return true; },
    };
  });
  afterEach(() => vi.useRealTimers());

  it("moves the remembered right-hand agent back once the restored tabs settle", async () => {
    saved = { apart: true, rightKind: "codex" };
    const watcher = installAgentSplit(host);
    groups = merged;
    fire();
    await vi.advanceTimersByTimeAsync(2999);
    expect(moves).toEqual([]);
    await vi.advanceTimersByTimeAsync(1);
    expect(moves).toEqual([[1, 1, "codex"]]);
    expect(saved).toEqual({ apart: true, rightKind: "codex" });
    fire();
    await vi.advanceTimersByTimeAsync(10000);
    expect(moves).toHaveLength(1);
    watcher.dispose();
  });
  it("waits while tabs keep changing and while only one agent is present", async () => {
    saved = { apart: true, rightKind: "claude" };
    installAgentSplit(host);
    groups = [{ column: 1, tabs: [codex(0)] }];
    fire();
    await vi.advanceTimersByTimeAsync(10000);
    expect(moves).toEqual([]);
    groups = [{ column: 1, tabs: [codex(0), claude(1)] }];
    fire();
    await vi.advanceTimersByTimeAsync(2000);
    fire();
    await vi.advanceTimersByTimeAsync(2000);
    expect(moves).toEqual([]);
    await vi.advanceTimersByTimeAsync(1000);
    expect(moves).toEqual([[1, 1, "claude"]]);
  });
  it("leaves a layout that is already split alone and records it", async () => {
    saved = { apart: true, rightKind: "codex" };
    groups = split;
    installAgentSplit(host);
    await vi.advanceTimersByTimeAsync(3000);
    expect(moves).toEqual([]);
  });
  it("does not restore a merge the user made, and records the merge only after startup", async () => {
    saved = { apart: false, rightKind: "codex" };
    groups = merged;
    installAgentSplit(host);
    await vi.advanceTimersByTimeAsync(3000);
    expect(moves).toEqual([]);
    groups = split;
    fire();
    expect(saved).toEqual({ apart: true, rightKind: "codex" });
    groups = merged;
    fire();
    expect(saved?.apart).toBe(false);
  });
  it("never overwrites the remembered split with the merged startup state", async () => {
    saved = { apart: true, rightKind: "codex" };
    installAgentSplit(host);
    groups = merged;
    fire();
    expect(saved).toEqual({ apart: true, rightKind: "codex" });
  });
  it("does nothing when disabled or untrusted, and records nothing", async () => {
    for (const [on, trust] of [[false, true], [true, false]] as const) {
      enabled = on; trusted = trust; saved = { apart: true, rightKind: "codex" }; groups = merged;
      const watcher = installAgentSplit(host);
      await vi.advanceTimersByTimeAsync(5000);
      watcher.dispose();
      expect(moves).toEqual([]);
      expect(saved).toEqual({ apart: true, rightKind: "codex" });
    }
  });
  it("gives up after the startup window if the agents never both appear", async () => {
    saved = { apart: true, rightKind: "codex" };
    installAgentSplit(host);
    await vi.advanceTimersByTimeAsync(60000);
    groups = merged;
    fire();
    await vi.advanceTimersByTimeAsync(10000);
    expect(moves).toEqual([]);
  });
  it("keeps the failure of a move from stopping later recording", async () => {
    const error = vi.spyOn(console, "error").mockImplementation(() => undefined);
    saved = { apart: true, rightKind: "codex" };
    host.moveRight = async () => { throw new Error("boom"); };
    installAgentSplit(host);
    groups = merged;
    fire();
    await vi.advanceTimersByTimeAsync(3000);
    expect(error).toHaveBeenCalled();
    groups = split;
    fire();
    expect(saved).toEqual({ apart: true, rightKind: "codex" });
    error.mockRestore();
  });
  it("stops everything when disposed", async () => {
    saved = { apart: true, rightKind: "codex" };
    const watcher = installAgentSplit(host);
    groups = merged;
    fire();
    watcher.dispose();
    await vi.advanceTimersByTimeAsync(70000);
    expect(moves).toEqual([]);
    expect(tabListeners).toEqual([]);
  });
});

describe("VS Code host", () => {
  const webview = (viewType = "mainThreadWebview-claudeVSCodePanel") => ({ input: new TabInputWebview(viewType) });
  const custom = (viewType = "chatgpt.conversationEditor") => ({ input: new TabInputCustom(Uri.parse("openai-codex://route/extension/panel/new"), viewType) });
  const memento = () => { const store = new Map<string, unknown>(); return { get: (key: string) => store.get(key), update: async (key: string, value: unknown) => void store.set(key, value), store }; };
  beforeEach(() => { stub.reset(); stub.defaults["nexusHubSettings.restoreAgentSplit"] = false; });

  it("reads only the two agent editors from the tab groups", () => {
    const text = { input: { uri: Uri.file("a.txt") } };
    stub.tabGroups = [{ viewColumn: 1, isActive: true, tabs: [text, webview(), webview("mainThreadWebview-other")] }, { viewColumn: 2, isActive: false, tabs: [custom("other.editor"), custom()] }, { viewColumn: 3, isActive: false, tabs: [text] }];
    expect(vscodeSplitHost(memento() as never).snapshot()).toEqual([{ column: 1, tabs: [claude(1)] }, { column: 2, tabs: [codex(1)] }]);
  });
  it("reads the opt-in setting and workspace trust", () => {
    const host = vscodeSplitHost(memento() as never);
    expect(host.enabled()).toBe(false);
    stub.user["nexusHubSettings.restoreAgentSplit"] = true;
    expect(host.enabled()).toBe(true);
    stub.trusted = false;
    expect(host.trusted()).toBe(false);
  });
  it("persists a valid layout and ignores a corrupt one", async () => {
    const state = memento();
    const host = vscodeSplitHost(state as never);
    expect(host.read()).toBeUndefined();
    await host.write({ apart: true, rightKind: "codex" });
    expect(host.read()).toEqual({ apart: true, rightKind: "codex" });
    state.store.set(LAYOUT_KEY, { apart: "yes", rightKind: "other" });
    expect(host.read()).toBeUndefined();
  });
  it("focuses the tab, verifies it, then moves it right and returns focus", async () => {
    const claudeTab = webview(), codexTab = custom();
    const group: StubTabGroup = { viewColumn: 1, isActive: true, tabs: [claudeTab, codexTab], activeTab: codexTab };
    stub.tabGroups = [group];
    stub.commands.set("workbench.action.moveEditorToRightGroup", () => undefined);
    expect(await vscodeSplitHost(memento() as never).moveRight(1, 1, "codex")).toBe(true);
    expect(stub.executed).toEqual(["workbench.action.focusFirstEditorGroup", "workbench.action.openEditorAtIndex2", "workbench.action.moveEditorToRightGroup", "workbench.action.focusFirstEditorGroup"]);
  });
  it("refuses to move a tab it could not select", async () => {
    const claudeTab = webview(), codexTab = custom();
    const host = vscodeSplitHost(memento() as never);
    stub.tabGroups = [{ viewColumn: 1, isActive: true, tabs: [claudeTab, codexTab], activeTab: claudeTab }];
    expect(await host.moveRight(1, 1, "codex")).toBe(false);
    stub.tabGroups = [{ viewColumn: 1, isActive: false, tabs: [claudeTab, codexTab], activeTab: codexTab }];
    expect(await host.moveRight(1, 1, "codex")).toBe(false);
    expect(await host.moveRight(9, 0, "codex")).toBe(false);
    expect(await host.moveRight(1, 9, "codex")).toBe(false);
    expect(stub.executed).not.toContain("workbench.action.moveEditorToRightGroup");
  });
});
