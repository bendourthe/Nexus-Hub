import * as vscode from "vscode";
import type { State } from "./types";
import type { ControlView, RowView, ViewModel } from "./viewModel";

/**
 * The status-bar entry: the Nexus-Hub mark, the effort a new session starts with, and a
 * warning count when a default is not the value that applies. The hover lists every
 * tool's defaults; a click opens the full panel. Everything shown comes from the same
 * view model the panel draws, so the two can never disagree.
 */

/** The Nexus-Hub mark, contributed as an icon font in package.json. */
export const NEXUS_ICON = "$(nexus-hub-icon)";
/** An en space: the status bar collapses repeated plain spaces, so this keeps the gap visible. */
const GAP = " ";
/** Right-aligned items with a higher priority sit further left: just left of the usage monitors (105, 103). */
export const STATUS_PRIORITY = 106;

/** States that mean the panel's default is not what a new session gets, or cannot be confirmed. */
const ATTENTION: ReadonlySet<State> = new Set<State>(["overridden-by", "not-covered", "cannot-detect", "unverified-for-version"]);
/** Hover columns, in panel order. A control the engine does not report is left out. */
const TABLE_CONTROLS = ["effort", "model", "posture"];
const COLUMN_TITLE: Record<string, string> = { effort: "Effort", model: "Model", posture: "Approval" };

/** The value a new session starts with for one row, or null when the tool's own default applies or nothing is known. */
export function effectiveValue(row: RowView): string | null {
  if (row.state === "overridden-by") {
    return row.layerValue;
  }
  return row.state === "in-effect" || row.state === "not-covered" || row.state === "unverified-for-version" ? row.value : null;
}

/** One word for the status bar: the effort every settable tool starts with, "mixed" when they differ, "default" when none is set. */
export function statusEffort(model: ViewModel): string {
  const effort = model.controls.find((control) => control.id === "effort");
  const values = (effort?.rows ?? []).filter((row) => row.canSet).map(effectiveValue);
  const known = [...new Set(values.filter((value): value is string => !!value))];
  const [only] = known;
  if (only === undefined) {
    return "default";
  }
  return known.length === 1 && !values.includes(null) ? only : "mixed";
}

export function attentionRows(model: ViewModel): { control: ControlView; row: RowView }[] {
  return model.controls.flatMap((control) => control.rows.filter((row) => ATTENTION.has(row.state)).map((row) => ({ control, row })));
}

export interface StatusSummary {
  text: string;
  accessibilityLabel: string;
  tooltip: string;
}

/** Escape the characters Markdown or the hover's HTML would treat as markup; values come from user files. */
export function escapeMarkdown(text: string): string {
  return text.replace(/[\\`*_{}[\]()#+\-.!|<>&~]/g, (char) => (char === "<" ? "&lt;" : char === ">" ? "&gt;" : char === "&" ? "&amp;" : `\\${char}`));
}

/** A tool none of whose controls can be set says nothing per column, so it moves to one line under the table. */
function unsettable(row: RowView | undefined): boolean {
  return !row || row.state === "not-settable";
}

function cell(row: RowView | undefined): string {
  if (!row) {
    return "-";
  }
  switch (row.state) {
    case "in-effect":
      return escapeMarkdown(row.value ?? "set");
    case "overridden-by":
      return `${escapeMarkdown(row.layerValue ?? "overridden")} $(warning)`;
    case "tool-default":
      return "tool default";
    case "not-settable":
      return "not settable";
    case "tool-not-installed":
      return "not installed";
    case "cannot-detect":
      return "unknown $(warning)";
    default:
      return `${escapeMarkdown(row.value ?? "unconfirmed")} $(warning)`;
  }
}

function rowKey(row: RowView): string {
  return `${row.tool}|${row.surface}`;
}

function rowTitle(row: RowView): string {
  return row.surface === "cli" ? row.toolLabel : `${row.toolLabel} (${row.surfaceLabel})`;
}

function table(model: ViewModel): string[] {
  const controls = TABLE_CONTROLS.flatMap((id) => model.controls.filter((control) => control.id === id));
  if (controls.length === 0) {
    return [];
  }
  const tools: RowView[] = [];
  for (const control of controls) {
    for (const row of control.rows) {
      if (!tools.some((known) => rowKey(known) === rowKey(row))) {
        tools.push(row);
      }
    }
  }
  const cellsOf = (tool: RowView): (RowView | undefined)[] => controls.map((c) => c.rows.find((row) => rowKey(row) === rowKey(tool)));
  const shown = tools.filter((tool) => !cellsOf(tool).every(unsettable));
  const hidden = tools.filter((tool) => cellsOf(tool).every(unsettable));
  const lines: string[] = [];
  if (shown.length > 0) {
    lines.push(`| Tool | ${controls.map((c) => COLUMN_TITLE[c.id] ?? escapeMarkdown(c.label)).join(" | ")} |`, `|:--|${controls.map(() => ":--").join("|")}|`);
    for (const tool of shown) {
      lines.push(`| ${escapeMarkdown(rowTitle(tool))} | ${cellsOf(tool).map(cell).join(" | ")} |`);
    }
  }
  if (hidden.length > 0) {
    lines.push("", `**Not settable here:** ${escapeMarkdown(hidden.map(rowTitle).join(", "))}`);
  }
  return lines;
}

/** Controls outside the table (attribution, git guardrails) as one line each: the states, counted. */
function otherLines(model: ViewModel): string[] {
  return model.controls
    .filter((control) => !TABLE_CONTROLS.includes(control.id))
    .map((control) => {
      const counts = new Map<string, number>();
      for (const row of control.rows) {
        const label = row.badge.text.toLowerCase();
        counts.set(label, (counts.get(label) ?? 0) + 1);
      }
      const parts = [...counts.entries()].map(([label, n]) => (control.rows.length === 1 ? label : `${label} (${n})`));
      return `**${escapeMarkdown(control.label)}:** ${escapeMarkdown(parts.join(", "))}`;
    });
}

export function summarize(model: ViewModel | undefined, openCommand: string): StatusSummary {
  const open = `[Open Nexus-Hub Settings](command:${openCommand})`;
  if (!model || (model.controls.length === 0 && !model.error)) {
    return { text: NEXUS_ICON, accessibilityLabel: "Nexus-Hub Settings, reading", tooltip: `Reading the Nexus-Hub defaults...\n\n${open}` };
  }
  if (model.error) {
    return {
      text: `${NEXUS_ICON}${GAP}$(error)`,
      accessibilityLabel: "Nexus-Hub Settings, cannot be read",
      tooltip: `**${escapeMarkdown(model.error.title)}**\n\n${escapeMarkdown(model.error.message)}\n\n${open}`,
    };
  }
  const effort = statusEffort(model);
  const attention = attentionRows(model);
  const warn = attention.length > 0 ? ` $(warning) ${attention.length}` : "";
  const notes = attention.map(({ control, row }) => `- $(warning) ${escapeMarkdown(`${control.label}, ${rowTitle(row)}: ${row.badge.text}`)}`);
  const tooltip = [
    "**Nexus-Hub defaults** for new sessions",
    "",
    ...table(model),
    "",
    ...otherLines(model).flatMap((line) => [line, ""]),
    ...(notes.length > 0 ? [...notes, ""] : []),
    open,
  ].join("\n");
  const attentionText = attention.length === 0 ? "" : `, ${attention.length} ${attention.length === 1 ? "default needs" : "defaults need"} attention`;
  return { text: `${NEXUS_ICON}${GAP}${effort}${warn}`, accessibilityLabel: `Nexus-Hub Settings, effort ${effort}${attentionText}`, tooltip };
}

export class SettingsStatusBar implements vscode.Disposable {
  private readonly item: vscode.StatusBarItem;

  constructor(private readonly openCommand: string) {
    this.item = vscode.window.createStatusBarItem("nexusHubSettings.status", vscode.StatusBarAlignment.Right, STATUS_PRIORITY);
    this.item.name = "Nexus-Hub Settings";
    this.item.command = openCommand;
    this.update(undefined);
    this.item.show();
  }

  update(model: ViewModel | undefined): void {
    const summary = summarize(model, this.openCommand);
    const tooltip = new vscode.MarkdownString(summary.tooltip, true);
    tooltip.isTrusted = { enabledCommands: [this.openCommand] };
    this.item.text = summary.text;
    this.item.tooltip = tooltip;
    this.item.accessibilityInformation = { label: summary.accessibilityLabel, role: "button" };
  }

  dispose(): void {
    this.item.dispose();
  }
}
