import * as vscode from "vscode";
import type { State } from "./types";
import { summarizePreferences, type ControlView, type RowView, type ViewModel } from "./viewModel";

export const NEXUS_ICON = "$(nexus-hub-icon)";
export const STATUS_PRIORITY = 106;
export const SET_EFFORT_COMMAND = "nexusHubSettings.setEffort";
export const COMPACT_COMMAND = "nexusHubSettings.toggleCompactStatusBar";
export const EFFORT_LABELS: Readonly<Record<string, string>> = { low: "Low", medium: "Medium", high: "High", xhigh: "Extra high" };
const ATTENTION: ReadonlySet<State> = new Set(["overridden-by", "not-covered", "cannot-detect", "unverified-for-version"]);

export function effectiveValue(row: RowView): string | null {
  return row.state === "overridden-by" ? row.layerValue : row.state === "in-effect" || row.state === "not-covered" || row.state === "unverified-for-version" ? row.value : null;
}

export function statusEffort(model: ViewModel): string {
  return summarizePreferences(model).effort || "default";
}

export function attentionRows(model: ViewModel): { control: ControlView; row: RowView }[] {
  return model.controls.filter((control) => control.id === "effort" || ["git_safety", "secret_scan", "edit_preservation", "large_file_warning", "git_guardrails"].includes(control.id)).flatMap((control) => control.rows.filter((row) => ATTENTION.has(row.state)).map((row) => ({ control, row })));
}

export interface StatusSummary {
  text: string;
  accessibilityLabel: string;
  tooltip: string;
}

export function escapeMarkdown(text: string): string {
  return text.replace(/[\\`*_{}[\]()#+\-.!|<>&~]/g, (char) => char === "<" ? "&lt;" : char === ">" ? "&gt;" : char === "&" ? "&amp;" : `\\${char}`);
}

export function summarize(model: ViewModel | undefined, openCommand: string, compact = true): StatusSummary {
  const open = `[Open Nexus Settings](command:${openCommand})`;
  const prefix = compact ? "" : "Nexus Settings: ";
  if (!model || (model.controls.length === 0 && !model.error)) {
    return { text: `${NEXUS_ICON} ${prefix}Reading...`, accessibilityLabel: "Nexus Settings, reading", tooltip: `Reading settings...\n\n${open}` };
  }
  if (model.error) {
    return { text: `${NEXUS_ICON} ${prefix}Unavailable $(error)`, accessibilityLabel: "Nexus Settings, unavailable", tooltip: `${escapeMarkdown(model.error.title)}\n\n${open}` };
  }
  const summary = summarizePreferences(model);
  const effort = summary.effort || "Default";
  const titled = EFFORT_LABELS[effort] || "Default";
  const protection = summary.guardsAvailable ? `Configured guardrails: ${summary.guardsEnabled} of ${summary.guardsAvailable} on` : "Configured guardrails: unavailable";
  const control = model.controls.find((item) => item.id === "effort");
  const options = Object.entries(EFFORT_LABELS).filter(([value]) => control?.choices.includes(value));
  const selected = options.findIndex(([value]) => effort === value);
  const cells = options.map(([value, label], index) => {
    const active = effort === value;
    const target = `command:${SET_EFFORT_COMMAND}?${encodeURIComponent(JSON.stringify([value]))}`;
    const link = (content: string): string => active || model.readOnly || model.busy || !control?.canApply ? content : `[${content}](${target})`;
    const fill = index < selected ? 64 : active ? 32 : 0;
    // Local images keep the native hover's command links while matching the panel's stepped control.
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="64" height="32" viewBox="0 0 64 32"><defs><clipPath id="track"><rect width="64" height="32" rx="16"/></clipPath></defs><rect x="0.5" y="0.5" width="63" height="31" rx="15.5" fill="#808080" fill-opacity="0.2" stroke="#808080"/><rect width="${fill}" height="32" fill="#00d9ed" clip-path="url(#track)"/><circle cx="32" cy="16" r="${active ? 14 : 3}" fill="${active ? "#ffffff" : "#00a8cf"}" stroke="#00a8cf"/></svg>`;
    return { label: link(active ? `$(circle-filled) **${label}**` : label), image: link(`![${active ? "Selected: " : "Set effort: "}${label}](data:image/svg+xml,${encodeURIComponent(svg)})`) };
  });
  const choices = cells.length ? [`| ${cells.map((cell) => cell.label).join(" | ")} |`, `| ${cells.map(() => ":---:").join(" | ")} |`, `| ${cells.map((cell) => cell.image).join(" | ")} |`].join("\n") : "";
  const tooltip = ["**Nexus Settings**", `**Default effort: ${titled}**`, choices, "New sessions only.", "---", `**${protection}**`, summary.effortStatus, ...(summary.needsAttention ? ["$(warning) A default is overridden, unverified, or a guardrail is unavailable. Open Settings to review."] : []), "---", `${open} | [${compact ? "Show full label" : "Use compact label"}](command:${COMPACT_COMMAND})`].filter(Boolean).join("\n\n");
  return { text: `${NEXUS_ICON} ${prefix}${titled} (effort)${summary.needsAttention ? " $(warning)" : ""}`, accessibilityLabel: `Nexus Settings, default effort ${effort}, ${protection.toLowerCase()}${summary.needsAttention ? ", needs attention" : ""}`, tooltip };
}

export class SettingsStatusBar implements vscode.Disposable {
  private readonly item: vscode.StatusBarItem;
  private model: ViewModel | undefined;
  private readonly configurationListener: vscode.Disposable;
  constructor(private readonly openCommand: string) {
    this.item = vscode.window.createStatusBarItem("nexusHubSettings.status", vscode.StatusBarAlignment.Right, STATUS_PRIORITY);
    this.item.name = "Nexus Settings";
    this.item.command = openCommand;
    this.configurationListener = vscode.workspace.onDidChangeConfiguration((event) => {
      if (event.affectsConfiguration("nexusHubSettings.compactStatusBar")) { this.update(this.model); }
    });
    this.update(undefined);
    this.item.show();
  }
  update(model: ViewModel | undefined): void {
    this.model = model;
    const summary = summarize(model, this.openCommand, vscode.workspace.getConfiguration("nexusHubSettings").get<boolean>("compactStatusBar", true));
    const tooltip = new vscode.MarkdownString(summary.tooltip, true);
    tooltip.isTrusted = { enabledCommands: [this.openCommand, SET_EFFORT_COMMAND, COMPACT_COMMAND] };
    this.item.text = summary.text;
    this.item.tooltip = tooltip;
    this.item.accessibilityInformation = { label: summary.accessibilityLabel, role: "button" };
  }
  dispose(): void { this.configurationListener.dispose(); this.item.dispose(); }
}
