import * as vscode from "vscode";
import type { State } from "./types";
import { summarizePreferences, type ControlView, type RowView, type ViewModel } from "./viewModel";

export const NEXUS_ICON = "$(nexus-hub-icon)";
export const STATUS_PRIORITY = 106;
export const SET_EFFORT_COMMAND = "nexusHubSettings.setEffort";
export const COMPACT_COMMAND = "nexusHubSettings.toggleCompactStatusBar";
export const EFFORT_LABELS: Readonly<Record<string, string>> = { low: "Low", medium: "Medium", high: "High", xhigh: "Extra high", max: "Max", ultra: "Ultra" };
export function effortIndicator(value: string, light = false): string {
  const levels = Object.keys(EFFORT_LABELS), selected = levels.indexOf(value);
  const positions = levels.map((_, index) => 13 + index * 47.6);
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="264" height="48"><rect x="4" y="2" width="256" height="22" rx="11" fill="#888" fill-opacity=".2" stroke="#888" stroke-width=".6"/>` +
    (selected < 0 ? "" : `<rect x="4" y="2" width="${positions[selected]! + 6}" height="22" rx="11" fill="#00c9dc"/>`) +
    levels.map((level, index) => `<circle cx="${positions[index]}" cy="13" r="${index === selected ? 9 : 2}" fill="${index === selected ? "#fff" : "#aaa"}"${index === selected ? ' stroke="#007b88" stroke-width="1"' : ""}/><text x="${positions[index]}" y="42" font-family="system-ui,sans-serif" font-size="10" text-anchor="middle" fill="${index === selected ? light ? "#007580" : "#00c9dc" : light ? "#555" : "#bbb"}" font-weight="${index === selected ? "700" : "400"}">${EFFORT_LABELS[level]}</text>`).join("") + "</svg>";
  return `<img src="data:image/svg+xml,${encodeURIComponent(svg)}" width="264" height="48" alt="${EFFORT_LABELS[value] || "Default"} effort"/>`;
}
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

export function summarize(model: ViewModel | undefined, openCommand: string, compact = true, light = false): StatusSummary {
  const open = `[Open Settings](command:${openCommand})`;
  const prefix = compact ? "" : "Nexus Hub: ";
  if (!model || (model.controls.length === 0 && !model.error)) {
    return { text: `${NEXUS_ICON} ${prefix}Reading...`, accessibilityLabel: "Nexus Hub, reading", tooltip: `Reading settings...\n\n${open}` };
  }
  if (model.error) {
    return { text: `${NEXUS_ICON} ${prefix}Unavailable $(error)`, accessibilityLabel: "Nexus Hub, unavailable", tooltip: `${escapeMarkdown(model.error.title)}\n\n${open}` };
  }
  const summary = summarizePreferences(model);
  const attention = summary.needsAttention || !!model.liveEffort?.error;
  const effort = summary.effort || "Default";
  const titled = EFFORT_LABELS[effort] || "Default";
  const protection = summary.guardsAvailable ? `Configured guardrails: ${summary.guardsEnabled} of ${summary.guardsAvailable} on` : "Configured guardrails: unavailable";
  const guards = [["git_safety", "Git safety"], ["secret_scan", "Secrets"], ["edit_preservation", "My edits"], ["large_file_warning", "Large files"], ["git_guardrails", "Git bypass"]].map(([id, label]) => {
    const control = model.controls.find((item) => item.id === id);
    const row = control?.rows.find((item) => item.tool === "internal") ?? control?.rows[0];
    const known = !!control?.canApply && !!row && !["cannot-detect", "unverified-for-version", "not-covered"].includes(row.state);
    const value = row ? effectiveValue(row) : null;
    const on = value === "on" || value === "true" || (row?.state === "tool-default" && id !== "git_guardrails");
    return `$(${!known ? "question" : on ? "check" : "circle-slash"}) ${label}`;
  });
  const links = model.codexAvailable && !model.readOnly ? `${open} | [New Codex agent](command:nexusHubSettings.newCodexAgent)` : open;
  const tooltip = [
    "**Nexus Hub**",
    "",
    "**Effort Level**",
    effortIndicator(effort, light),
    "**Guardrails**",
    guards.slice(0, 3).join(" &nbsp; "),
    guards.slice(3).join(" &nbsp; "),
    attention ? "$(warning) Review application in Settings." : model.liveEffort?.missing?.length ? `Reload to connect ${model.liveEffort.missing.join(" and ")}.` : model.liveEffort ? "Next request in connected sessions." : "New sessions only.",
    links,
  ].join("  \n");
  return { text: `${NEXUS_ICON} ${prefix}${titled} (effort)${attention ? " $(warning)" : ""}`, accessibilityLabel: `Nexus Hub, default effort ${effort}, ${protection.toLowerCase()}${attention ? ", needs attention" : ""}`, tooltip };
}

export class SettingsStatusBar implements vscode.Disposable {
  private readonly item: vscode.StatusBarItem;
  private model: ViewModel | undefined;
  private readonly configurationListener: vscode.Disposable;
  private readonly themeListener: vscode.Disposable | undefined;
  constructor(private readonly openCommand: string) {
    this.item = vscode.window.createStatusBarItem("nexusHubSettings.status", vscode.StatusBarAlignment.Right, STATUS_PRIORITY);
    this.item.name = "Nexus Settings";
    this.item.command = openCommand;
    this.configurationListener = vscode.workspace.onDidChangeConfiguration((event) => {
      if (event.affectsConfiguration("nexusHubSettings.compactStatusBar")) { this.update(this.model); }
    });
    this.themeListener = vscode.window.onDidChangeActiveColorTheme?.(() => this.update(this.model));
    this.update(undefined);
    this.item.show();
  }
  update(model: ViewModel | undefined): void {
    this.model = model;
    const summary = summarize(model, this.openCommand, vscode.workspace.getConfiguration("nexusHubSettings").get<boolean>("compactStatusBar", true), vscode.window.activeColorTheme?.kind === vscode.ColorThemeKind.Light);
    const tooltip = new vscode.MarkdownString(summary.tooltip, true);
    tooltip.supportHtml = true;
    tooltip.isTrusted = { enabledCommands: this.model?.codexAvailable && !this.model.readOnly ? [this.openCommand, "nexusHubSettings.newCodexAgent"] : [this.openCommand] };
    this.item.text = summary.text;
    this.item.tooltip = tooltip;
    this.item.accessibilityInformation = { label: summary.accessibilityLabel, role: "button" };
  }
  dispose(): void { this.configurationListener.dispose(); this.themeListener?.dispose(); this.item.dispose(); }
}
