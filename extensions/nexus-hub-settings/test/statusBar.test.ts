import { beforeEach, describe, expect, it } from "vitest";
import { SettingsStatusBar, STATUS_PRIORITY, escapeMarkdown, statusEffort, summarize } from "../src/statusBar";
import type { State } from "../src/types";
import { badgeFor, emptyModel, type ControlView, type RowView, type ViewModel } from "../src/viewModel";
import { MarkdownString, StatusBarAlignment, stub } from "./vscode-stub";

const OPEN = "nexusHubSettings.open";

function row(tool: string, state: State, value: string | null = null, layerValue: string | null = null, surface: RowView["surface"] = "cli"): RowView {
  const labels: Record<string, string> = { claude: "Claude Code", codex: "Codex", "copilot-cli": "GitHub Copilot CLI", internal: "Nexus-Hub (all tools)" };
  return {
    tool,
    toolLabel: labels[tool] ?? tool,
    surface,
    surfaceLabel: surface === "cli" ? "command line" : "VS Code",
    state,
    badge: badgeFor(state, null, state === "overridden-by" ? "env CLAUDE_CODE_EFFORT_LEVEL (shell)" : null),
    value,
    layerValue,
    fix: null,
    detail: null,
    caveats: [],
    canSet: state !== "not-settable" && state !== "tool-not-installed",
    removable: null,
  };
}

function control(id: string, label: string, rows: RowView[]): ControlView {
  return {
    id,
    label,
    kind: id === "model" ? "text" : "choice",
    choices: [],
    weakeningChoices: [],
    suggestions: {},
    perTool: id === "model",
    perToolOverride: id === "effort",
    neverWritten: [],
    canApply: true,
    takesEffect: "New sessions only.",
    rows,
    sources: [],
  };
}

function model(controls: ControlView[]): ViewModel {
  return { ...emptyModel("Default", "windows"), controls };
}

/** The machine state that prompted the status bar: Claude's saved effort is overridden by an env var. */
function realistic(): ViewModel {
  return model([
    control("effort", "Default effort", [
      row("claude", "overridden-by", "mixed (claude-opus-5-5=medium)", "high"),
      row("codex", "in-effect", "high"),
      row("copilot-cli", "not-settable"),
    ]),
    control("model", "Default model", [row("claude", "in-effect", "opus"), row("codex", "in-effect", "gpt-6.1-sol"), row("copilot-cli", "not-settable")]),
    control("posture", "Approval posture", [row("claude", "tool-default"), row("codex", "in-effect", "ask/accept-edits"), row("copilot-cli", "not-settable")]),
    control("git_guardrails", "Git guardrails", [row("internal", "tool-default")]),
  ]);
}

describe("statusEffort", () => {
  it("uses the overriding value, because that is what a new session starts with", () => {
    expect(statusEffort(realistic())).toBe("high");
  });

  it("says mixed when the settable tools start with different values", () => {
    const m = model([control("effort", "Default effort", [row("claude", "in-effect", "medium"), row("codex", "in-effect", "high")])]);
    expect(statusEffort(m)).toBe("mixed");
  });

  it("says mixed when one tool is set and another keeps its own default", () => {
    const m = model([control("effort", "Default effort", [row("claude", "tool-default"), row("codex", "in-effect", "high")])]);
    expect(statusEffort(m)).toBe("mixed");
  });

  it("says default when no settable tool has a value, and ignores tools that cannot be set", () => {
    const m = model([control("effort", "Default effort", [row("claude", "tool-default"), row("copilot-cli", "not-settable", "xhigh")])]);
    expect(statusEffort(m)).toBe("default");
  });
});

describe("summarize", () => {
  it("shows the mark, the effort, and one warning per default that is not the value that applies", () => {
    const summary = summarize(realistic(), OPEN);
    expect(summary.text).toBe("$(nexus-hub-icon) high $(warning) 1");
    expect(summary.accessibilityLabel).toBe("Nexus-Hub Settings, effort high, 1 default needs attention");
  });

  it("drops the warning when every default applies", () => {
    const m = model([control("effort", "Default effort", [row("codex", "in-effect", "high")])]);
    expect(summarize(m, OPEN).text).toBe("$(nexus-hub-icon) high");
  });

  it("lists every tool's effort, model and approval in a table, then the other controls and a link to the panel", () => {
    const tooltip = summarize(realistic(), OPEN).tooltip;
    expect(tooltip).toContain("| Tool | Effort | Model | Approval |");
    expect(tooltip).toContain("| Claude Code | high $(warning) | opus | tool default |");
    expect(tooltip).toContain("| Codex | high | gpt\\-6\\.1\\-sol | ask/accept\\-edits |");
    expect(tooltip).not.toContain("| GitHub Copilot CLI |");
    expect(tooltip).toContain("**Not settable here:** GitHub Copilot CLI");
    expect(tooltip).toContain("**Git guardrails:** tool default");
    expect(tooltip).toContain("$(warning) Default effort, Claude Code: Overridden by env CLAUDE\\_CODE\\_EFFORT\\_LEVEL \\(shell\\)");
    expect(tooltip.endsWith(`[Open Nexus-Hub Settings](command:${OPEN})`)).toBe(true);
  });

  it("marks a control that is not part of a tool with a dash instead of an empty cell", () => {
    const m = model([
      control("effort", "Default effort", [row("codex", "in-effect", "high")]),
      control("posture", "Approval posture", [row("codex", "in-effect", "ask"), row("claude", "tool-default", null, null, "vscode-host")]),
    ]);
    expect(summarize(m, OPEN).tooltip).toContain("| Claude Code \\(VS Code\\) | - | tool default |");
  });

  it("escapes a value read from a user file so it cannot break the table or add a link", () => {
    const hostile = "x | y](command:workbench.action.terminal.new)<img src=a>";
    const m = model([control("model", "Default model", [row("claude", "in-effect", hostile)])]);
    const tooltip = summarize(m, OPEN).tooltip;
    expect(tooltip).toContain(escapeMarkdown(hostile));
    expect(tooltip).not.toContain("](command:workbench");
    expect(tooltip).not.toContain("<img");
    expect(tooltip.split("\n").find((line) => line.startsWith("| Claude Code"))?.split(/(?<!\\)\|/).length).toBe(4);
  });

  it("shows an error mark and the error title when the settings cannot be read", () => {
    const m: ViewModel = { ...model([]), status: "error", error: { title: "The Nexus-Hub command line was not found", message: "Install Nexus-Hub.", command: "nexus-hub settings show", fix: "" } };
    const summary = summarize(m, OPEN);
    expect(summary.text).toBe("$(nexus-hub-icon) $(error)");
    expect(summary.tooltip).toContain("**The Nexus\\-Hub command line was not found**");
  });

  it("shows only the mark while the first read is still running", () => {
    expect(summarize(undefined, OPEN).text).toBe("$(nexus-hub-icon)");
    expect(summarize(model([]), OPEN).tooltip).toContain("Reading the Nexus-Hub defaults");
  });
});

describe("SettingsStatusBar", () => {
  beforeEach(() => stub.reset());

  it("sits just left of the usage monitors, opens the panel on click, and trusts only that command", () => {
    const bar = new SettingsStatusBar(OPEN);
    const [item] = stub.statusItems;
    expect(item).toMatchObject({ id: "nexusHubSettings.status", alignment: StatusBarAlignment.Right, priority: STATUS_PRIORITY, command: OPEN, shown: true });
    expect(STATUS_PRIORITY).toBeGreaterThan(105);

    bar.update(realistic());
    expect(item?.text).toBe("$(nexus-hub-icon) high $(warning) 1");
    const tooltip = item?.tooltip as MarkdownString;
    expect(tooltip.supportThemeIcons).toBe(true);
    expect(tooltip.isTrusted).toEqual({ enabledCommands: [OPEN] });
    expect(item?.accessibilityInformation?.role).toBe("button");

    bar.dispose();
    expect(item?.disposed).toBe(true);
  });
});
