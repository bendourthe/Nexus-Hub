import * as vscode from "vscode";

/** The two agent editors whose side-by-side layout can be restored. */
export type AgentKind = "claude" | "codex";
export interface AgentTab { kind: AgentKind; index: number }
/** An editor group that holds at least one agent tab. `index` counts every tab in the group. */
export interface AgentGroup { column: number; tabs: AgentTab[] }
/** What is remembered between sessions: whether the two agents were in different groups, and which was on the right. */
export interface AgentLayout { apart: boolean; rightKind: AgentKind }

export interface SplitHost {
  enabled(): boolean;
  trusted(): boolean;
  snapshot(): AgentGroup[];
  onDidChangeTabs(listener: () => void): { dispose(): unknown };
  read(): AgentLayout | undefined;
  write(layout: AgentLayout): unknown;
  /** Focus the tab, move it into the group to the right of its group, and report whether it was moved. */
  moveRight(column: number, index: number, kind: AgentKind): Promise<boolean>;
}

export const LAYOUT_KEY = "nexusHub.agentSplit";
const CLAUDE_VIEW_SUFFIX = "claudeVSCodePanel";
const CODEX_VIEW_TYPE = "chatgpt.conversationEditor";
const FOCUS_GROUP = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth"].map((name) => `workbench.action.focus${name}EditorGroup`);

function columnsOf(groups: AgentGroup[], kind: AgentKind): number[] {
  return groups.filter((group) => group.tabs.some((tab) => tab.kind === kind)).map((group) => group.column);
}

/** The layout worth remembering, or undefined while either agent has no tab. */
export function describeLayout(groups: AgentGroup[]): AgentLayout | undefined {
  const claude = columnsOf(groups, "claude");
  const codex = columnsOf(groups, "codex");
  if (!claude.length || !codex.length) { return undefined; }
  return { apart: !claude.some((column) => codex.includes(column)), rightKind: Math.min(...codex) > Math.min(...claude) ? "codex" : "claude" };
}

/** The one group that holds every agent tab of both kinds, if the agents have been merged. */
export function mergedGroup(groups: AgentGroup[]): AgentGroup | undefined {
  const [only] = groups;
  return groups.length === 1 && only && only.tabs.some((tab) => tab.kind === "claude") && only.tabs.some((tab) => tab.kind === "codex") ? only : undefined;
}

function sameLayout(a: AgentLayout | undefined, b: AgentLayout): boolean {
  return !!a && a.apart === b.apart && a.rightKind === b.rightKind;
}

/**
 * Remembers whether the Claude Code and Codex tabs sit in different editor groups. When VS Code reopens
 * them merged into one group, it moves the right-hand agent's tab back into its own group, once, after the
 * tabs have stopped changing. Nothing is closed or reopened; the tab itself is moved, so its content stays.
 */
export function installAgentSplit(host: SplitHost, settleMs = 3000, giveUpMs = 60000): { dispose(): void } {
  let restoring = true;
  let settle: ReturnType<typeof setTimeout> | undefined;

  const record = (): void => {
    if (!host.enabled() || !host.trusted()) { return; }
    const layout = describeLayout(host.snapshot());
    if (layout && !sameLayout(host.read(), layout)) { void host.write(layout); }
  };
  const evaluate = async (): Promise<void> => {
    if (!restoring) { return; }
    restoring = false;
    if (settle) { clearTimeout(settle); }
    if (!host.enabled() || !host.trusted()) { return; }
    try {
      const saved = host.read();
      const merged = mergedGroup(host.snapshot());
      const moving = saved?.apart && merged ? merged.tabs.filter((tab) => tab.kind === saved.rightKind).at(-1) : undefined;
      if (merged && moving) { await host.moveRight(merged.column, moving.index, moving.kind); }
    } catch (error) { console.error("Nexus Hub could not restore the agent split", error); }
    record();
  };
  const changed = (): void => {
    if (!restoring) { record(); return; }
    if (settle) { clearTimeout(settle); }
    if (describeLayout(host.snapshot())) { settle = setTimeout(() => void evaluate(), settleMs); }
  };

  const subscription = host.onDidChangeTabs(changed);
  const giveUp = setTimeout(() => void evaluate(), giveUpMs);
  changed();
  return { dispose: () => { subscription.dispose(); clearTimeout(giveUp); if (settle) { clearTimeout(settle); } restoring = false; } };
}

function classify(input: unknown): AgentKind | undefined {
  if (input instanceof vscode.TabInputWebview) { return input.viewType.endsWith(CLAUDE_VIEW_SUFFIX) ? "claude" : undefined; }
  if (input instanceof vscode.TabInputCustom) { return input.viewType === CODEX_VIEW_TYPE ? "codex" : undefined; }
  return undefined;
}

/** The real VS Code host: Tab Groups API for reading, built-in editor commands for the single move. */
export function vscodeSplitHost(state: vscode.Memento): SplitHost {
  const groups = (): readonly vscode.TabGroup[] => vscode.window.tabGroups.all;
  return {
    enabled: () => vscode.workspace.getConfiguration("nexusHubSettings").get<boolean>("restoreAgentSplit", false) === true,
    trusted: () => vscode.workspace.isTrusted,
    snapshot: () => groups().flatMap((group) => {
      const tabs = group.tabs.flatMap((tab, index) => { const kind = classify(tab.input); return kind ? [{ kind, index }] : []; });
      return tabs.length ? [{ column: group.viewColumn, tabs }] : [];
    }),
    onDidChangeTabs: (listener) => vscode.window.tabGroups.onDidChangeTabs(listener),
    read: () => {
      const value = state.get<Partial<AgentLayout>>(LAYOUT_KEY);
      return value && typeof value.apart === "boolean" && (value.rightKind === "claude" || value.rightKind === "codex") ? { apart: value.apart, rightKind: value.rightKind } : undefined;
    },
    write: (layout) => state.update(LAYOUT_KEY, layout),
    async moveRight(column, index, kind) {
      const focus = FOCUS_GROUP[column - 1];
      if (!focus || index > 8) { return false; }
      await vscode.commands.executeCommand(focus);
      await vscode.commands.executeCommand(`workbench.action.openEditorAtIndex${index + 1}`);
      const group = groups().find((candidate) => candidate.viewColumn === column);
      // Never move a tab we did not just select: a wrong active tab means the focus commands missed.
      if (!group?.isActive || !group.activeTab || classify(group.activeTab.input) !== kind) { return false; }
      await vscode.commands.executeCommand("workbench.action.moveEditorToRightGroup");
      await vscode.commands.executeCommand(focus);
      return true;
    },
  };
}
