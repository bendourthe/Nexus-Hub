import * as vscode from "vscode";
import type { State } from "./types";
import { summarizePreferences, type ControlView, type RowView, type ViewModel } from "./viewModel";

export const NEXUS_ICON = "$(nexus-hub-icon)";
export const STATUS_PRIORITY = 106;
export const SET_EFFORT_COMMAND = "nexusHubSettings.setEffort";
export const COMPACT_COMMAND = "nexusHubSettings.toggleCompactStatusBar";
export const EFFORT_LABELS: Readonly<Record<string, string>> = { low: "Low", medium: "Medium", high: "High", xhigh: "Extra high", max: "Max", ultra: "Ultra" };
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
  const tooltip = [
    `**Nexus Settings: ${titled} effort**`,
    protection,
    summary.needsAttention ? "$(warning) Review application in Settings." : "New sessions only.",
    open,
  ].join("  \n");
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
    tooltip.isTrusted = { enabledCommands: [this.openCommand] };
    this.item.text = summary.text;
    this.item.tooltip = tooltip;
    this.item.accessibilityInformation = { label: summary.accessibilityLabel, role: "button" };
  }
  dispose(): void { this.configurationListener.dispose(); this.item.dispose(); }
}
