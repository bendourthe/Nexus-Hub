import { beforeEach, describe, expect, it } from "vitest";
import { SettingsStatusBar, STATUS_PRIORITY, escapeMarkdown, statusEffort, summarize } from "../src/statusBar";
import type { State } from "../src/types";
import { badgeFor, emptyModel, summarizePreferences, type ControlView, type RowView, type ViewModel } from "../src/viewModel";
import { MarkdownString, StatusBarAlignment, stub } from "./vscode-stub";
const OPEN = "nexusHubSettings.open";
function row(tool: string, state: State, value: string | null = null, layerValue: string | null = null): RowView {
  return { tool, toolLabel: tool, surface: "cli", surfaceLabel: "command line", state, badge: badgeFor(state), value, layerValue, fix: null, detail: null, caveats: [], canSet: state !== "not-settable" && state !== "tool-not-installed", removable: null };
}
function control(id: string, rows: RowView[]): ControlView {
  return { id, label: id, kind: "choice", choices: id === "effort" ? ["low", "medium", "high", "xhigh"] : ["on", "off"], weakeningChoices: [], suggestions: {}, perTool: false, perToolOverride: false, neverWritten: [], canApply: true, takesEffect: "Next hook run.", rows, sources: [] };
}
function model(controls: ControlView[]): ViewModel { return { ...emptyModel("Default", "windows"), controls }; }
function realistic(): ViewModel {
  return model([
    control("effort", [row("internal", "in-effect", "high"), row("claude", "overridden-by", "medium", "low"), row("codex", "in-effect", "high"), row("copilot-cli", "not-settable")]),
    control("git_safety", [row("internal", "tool-default")]),
    control("secret_scan", [row("internal", "in-effect", "on")]),
    control("git_guardrails", [row("internal", "tool-default")]),
  ]);
}

describe("the configured shared effort", () => {
  it("shows the saved preference even when a platform overrides it", () => {
    expect(statusEffort(realistic())).toBe("high");
    expect(summarizePreferences(realistic()).needsAttention).toBe(true);
  });
  it("does not invent a shared value from mixed native settings", () => {
    expect(statusEffort(model([control("effort", [row("claude", "in-effect", "medium"), row("codex", "in-effect", "high")])]))).toBe("default");
  });
  it("can display a common existing value before the first shared preference is saved", () => {
    expect(statusEffort(model([control("effort", [row("codex", "in-effect", "medium")])]))).toBe("medium");
  });
  it("never renders an arbitrary value from a configuration file in the status bar", () => {
    const m = model([control("effort", [row("internal", "in-effect", "x | [bad](command:bad)")])]);
    expect(statusEffort(m)).toBe("default");
    expect(summarize(m, OPEN).text).not.toContain("bad");
  });
});

describe("compact status summary", () => {
  it("names Nexus and the configured effort, with one attention indicator", () => {
    const summary = summarize(realistic(), OPEN);
    expect(summary.text).toBe("$(nexus-hub-icon) High (effort) $(warning)");
    expect(summary.accessibilityLabel).toContain("default effort high");
    expect(summary.accessibilityLabel).toContain("needs attention");
  });
  it("separates hover sections and offers trusted effort actions without platform tables", () => {
    const tooltip = summarize(realistic(), OPEN).tooltip;
    expect(tooltip).toContain("\n\n---\n\n");
    expect(tooltip).toContain("$(circle-filled) **High**");
    expect(tooltip).toContain("command:nexusHubSettings.setEffort?%5B%22low%22%5D");
    expect(tooltip).toContain("Default effort: High");
    expect(tooltip).toContain("Configured guardrails: 2 of 3 on");
    expect(tooltip).not.toMatch(/\| Tool|Claude|Codex|Copilot|settings\.json|model_reasoning/);
    expect(tooltip).toContain(`[Open Nexus Settings](command:${OPEN})`);
  });
  it("does not show a warning when the known configuration is applied", () => {
    const m = model([control("effort", [row("internal", "in-effect", "low"), row("codex", "in-effect", "low")]), control("git_safety", [row("internal", "in-effect", "on")])]);
    expect(summarize(m, OPEN).text).toBe("$(nexus-hub-icon) Low (effort)");
  });
  it("does not mark a matching project override as a conflicting value", () => {
    const m = model([control("effort", [row("internal", "in-effect", "high"), row("claude", "overridden-by", "medium", "high")])]);
    expect(summarizePreferences(m).needsAttention).toBe(false);
  });
  it("keeps unsupported coverage visible without adding platform rows", () => {
    const summary = summarizePreferences(model([control("effort", [row("internal", "in-effect", "high"), row("copilot", "not-settable")])]));
    expect(summary.needsAttention).toBe(false);
    expect(summary.effortStatus).toContain("Some platforms cannot accept");
  });
  it("treats unreadable guards as unavailable, not as off or enabled", () => {
    const summary = summarizePreferences(model([control("git_safety", [row("internal", "cannot-detect")])]));
    expect(summary.guardsAvailable).toBe(0);
    expect(summary.guardsEnabled).toBe(0);
    expect(summary.needsAttention).toBe(true);
  });
  it("does not warn about platforms that are not installed", () => {
    const absent = { ...row("copilot", "not-settable"), installed: false };
    const summary = summarizePreferences(model([control("effort", [row("internal", "in-effect", "high"), row("codex", "in-effect", "high"), absent])]));
    expect(summary.needsAttention).toBe(false);
    expect(summary.effortStatus).not.toContain("cannot accept");
  });
  it("flags an unreadable shared preference even when native values agree", () => {
    const summary = summarizePreferences(model([control("effort", [row("internal", "cannot-detect"), row("codex", "in-effect", "high")])]));
    expect(summary.needsAttention).toBe(true);
    expect(summary.effortStatus).toContain("cannot be verified");
  });
  it("uses the readable Extra high label", () => {
    expect(summarize(model([control("effort", [row("internal", "in-effect", "xhigh")])]), OPEN).text).toBe("$(nexus-hub-icon) Extra high (effort)");
  });
  it("escapes error text and leaves only the panel command trusted", () => {
    const m: ViewModel = { ...model([]), status: "error", error: { title: "[bad](command:terminal)<img>", message: "secret path", command: "private", fix: "" } };
    const summary = summarize(m, OPEN);
    expect(summary.text).toBe("$(nexus-hub-icon) Unavailable $(error)");
    expect(summary.tooltip).toContain(escapeMarkdown(m.error!.title));
    expect(summary.tooltip).not.toContain("](command:terminal)");
    expect(summary.tooltip).not.toContain("secret path");
  });
  it("has a named reading state", () => {
    expect(summarize(undefined, OPEN).text).toBe("$(nexus-hub-icon) Reading...");
    expect(summarize(model([]), OPEN).tooltip).toContain("Reading settings");
  });
  it("uses the requested prefix only in full mode", () => {
    expect(summarize(realistic(), OPEN, false).text).toBe("$(nexus-hub-icon) Nexus Settings: High (effort) $(warning)");
  });
  it("keeps compatibility notes without a warning and disables hover writes in read-only or busy states", () => {
    const m = model([control("effort", [row("internal", "in-effect", "high"), row("copilot", "not-settable")])]);
    expect(summarize(m, OPEN).text).not.toContain("$(warning)");
    expect(summarize(m, OPEN).tooltip).toContain("Some platforms cannot accept");
    expect(summarize(m, OPEN).tooltip).toContain("data:image/svg+xml,");
    for (const locked of [{ ...m, readOnly: true }, { ...m, busy: true }]) {
      expect(summarize(locked, OPEN).tooltip).not.toContain("](command:nexusHubSettings.setEffort");
    }
  });
});

describe("SettingsStatusBar", () => {
  beforeEach(() => stub.reset());
  it("updates the label immediately when compact mode changes", () => {
    const bar = new SettingsStatusBar(OPEN);
    bar.update(realistic());
    stub.user["nexusHubSettings.compactStatusBar"] = false;
    stub.fireConfig("nexusHubSettings.compactStatusBar");
    expect(stub.statusItems[0]?.text).toContain("Nexus Settings: High (effort)");
    bar.dispose();
  });
  it("opens the settings panel, has an accessible name, and trusts only that command", () => {
    const bar = new SettingsStatusBar(OPEN);
    const [item] = stub.statusItems;
    expect(item).toMatchObject({ id: "nexusHubSettings.status", alignment: StatusBarAlignment.Right, priority: STATUS_PRIORITY, command: OPEN, shown: true });
    expect(STATUS_PRIORITY).toBeGreaterThan(105);
    bar.update(realistic());
    expect(item?.text).toBe("$(nexus-hub-icon) High (effort) $(warning)");
    expect((item?.tooltip as MarkdownString).isTrusted).toEqual({ enabledCommands: [OPEN, "nexusHubSettings.setEffort", "nexusHubSettings.toggleCompactStatusBar"] });
    expect(item?.accessibilityInformation?.role).toBe("button");
    bar.dispose();
    expect(item?.disposed).toBe(true);
  });
});
