import { describe, expect, it, vi } from "vitest";
import { CLAUDE_UI_API, CODEX_UI_API, CODEX_UI_HOOK, CODEX_NEW_PANEL, codexTabManifest } from "../src/vendorUiPatch";

describe("native UI effort adapters", () => {
  it("opens distinct Codex custom-editor documents while retaining the normal new-chat route", async () => {
    const executeCommand = vi.fn(); let sequence = 0;
    const provider = new Function("Be", "F1", "t", "w8e", `return{${CODEX_NEW_PANEL}}`)(
      { window: { activeTextEditor: { viewColumn: 3 } }, ViewColumn: { Active: -1 }, commands: { executeCommand } },
      (route: string) => new URL("codex://editor" + route), { customEditorViewType: "native-codex-editor" }, { randomUUID: () => String(++sequence) },
    );
    await provider.createNewPanel(); await provider.createNewPanel();
    expect(executeCommand).toHaveBeenCalledTimes(2);
    const first = executeCommand.mock.calls[0]!, second = executeCommand.mock.calls[1]!;
    expect(first[0]).toBe("vscode.openWith"); expect(first[1].pathname).toBe("/extension/panel/new");
    expect(first[1].href).not.toBe(second[1].href);
    expect(first.slice(2)).toEqual(["native-codex-editor", { viewColumn: 3, preserveFocus: false, preview: false }]);
  });
  it("updates Claude through its own effort flags, readback and UI push owner", async () => {
    const write = vi.fn(async () => undefined);
    const comm = { cachedClaudeSettings: { applied: { effort: "high", ultracode: false } }, channels: new Map([["existing", {}], ["draft", {}]]), writeUserSettingsAndPush: write };
    const api = new Function("zre", CLAUDE_UI_API)({ allComms: [comm] });
    await api.applyNexusEffort("ultra");
    expect(write.mock.calls).toEqual([["existing", { effortLevel: "xhigh", ultracode: true }, true], ["draft", { effortLevel: "xhigh", ultracode: true }, true]]);
    await expect(api.applyNexusEffort("full-auto")).rejects.toThrow("Invalid");
    comm.cachedClaudeSettings.applied = { effort: "medium", ultracode: false }; write.mockClear();
    await api.applyNexusEffort("medium"); expect(write).not.toHaveBeenCalled();
  });
  it("broadcasts only an allowlisted Codex effort message", () => {
    const send = vi.fn(); const api = new Function("$e", CODEX_UI_API)({ broadcastToAllViews: send });
    api.applyNexusEffort("max"); expect(send).toHaveBeenCalledWith({ type: "nexus-effort-v1", effort: "max" });
    expect(() => api.applyNexusEffort("<script>")).toThrow("Invalid"); expect(send).toHaveBeenCalledTimes(1);
  });
  it.each(["draft", "existing"])("uses the real UI selection callback for a %s without changing its model", async () => {
    const callbacks = new Set<(event: unknown) => void>(); const cleanups: (() => void)[] = []; const select = vi.fn().mockResolvedValue(true);
    const react = { useRef: () => ({ current: null }), useEffect: (effect: () => () => void) => cleanups.push(effect()) };
    const catalog = { data: { models: [{ model: "same-model", supportedReasoningEfforts: ["low", "medium", "high", "xhigh"].map((reasoningEffort) => ({ reasoningEffort })) }] } };
    const window = { addEventListener: (_: string, cb: (event: unknown) => void) => callbacks.add(cb) };
    const hook = new Function("window", "Rt", "it", CODEX_UI_HOOK + ";return nexusUseEffortBridge;")(window, react, () => catalog);
    hook({ model: "same-model", reasoningEffort: "medium", isLoading: false }, select, "local");
    const event = { data: { type: "nexus-effort-v1", effort: "ultra" }, stopImmediatePropagation: vi.fn() };
    for (const callback of callbacks) { callback(event); }
    await Promise.resolve(); expect(select).toHaveBeenCalledWith("same-model", "xhigh", { persistAsDefault: false });
    for (const cleanup of cleanups) { cleanup(); } select.mockClear();
    for (const callback of callbacks) { callback(event); } await Promise.resolve(); expect(select).not.toHaveBeenCalled();
  });
  it("changes the existing Codex toolbar entry to editor tabs and retains the vendor icon", () => {
    const original = { unrelated: { keep: true }, contributes: { commands: [{ command: "chatgpt.openSidebar", icon: { light: "black.svg", dark: "white.svg" } }, { command: "chatgpt.newCodexPanel", icon: "$(plus)" }], menus: { "editor/title": [{ command: "chatgpt.openSidebar", group: "navigation" }] } } };
    const result = JSON.parse(codexTabManifest(JSON.stringify(original)));
    expect(result.unrelated).toEqual(original.unrelated);
    expect(result.contributes.menus["editor/title"]).toEqual([{ command: "chatgpt.newCodexPanel", group: "navigation" }]);
    expect(result.contributes.commands[1].icon).toEqual(original.contributes.commands[0].icon);
  });
});
