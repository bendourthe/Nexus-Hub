import * as vscode from "vscode";
import type { State } from "./types";
import { effortApplicationIssues, summarizePreferences, type ControlView, type RowView, type ViewModel } from "./viewModel";

export const NEXUS_ICON = "$(nexus-hub-icon)";
export const STATUS_PRIORITY = 106;
export const SET_EFFORT_COMMAND = "nexusHubSettings.setEffort";
export const COMPACT_COMMAND = "nexusHubSettings.toggleCompactStatusBar";
export const EFFORT_LABELS: Readonly<Record<string, string>> = { low: "Low", medium: "Medium", high: "High", xhigh: "Extra high", max: "Max", ultra: "Ultra" };
export function effortIndicator(value: string, light = false, interactive = false): string {
  const levels = Object.keys(EFFORT_LABELS), selected = levels.indexOf(value);
  const positions = levels.map((_, index) => 22 + index * 44);
  const body = `<rect x="4" y="2" width="256" height="22" rx="11" fill="#888" fill-opacity=".2" stroke="#888" stroke-width=".6"/>` +
    (selected < 0 ? "" : `<rect x="4" y="2" width="${positions[selected]! + 6}" height="22" rx="11" fill="#00c9dc"/>`) +
    levels.map((level, index) => `<circle cx="${positions[index]}" cy="13" r="${index === selected ? 9 : 2}" fill="${index === selected ? "#fff" : light ? "#555" : "#aaa"}"${index === selected ? ' stroke="#007b88" stroke-width="1"' : ""}/><text x="${positions[index]}" y="42" font-family="system-ui,sans-serif" font-size="9" text-anchor="middle" fill="${index === selected ? light ? "#007580" : "#00c9dc" : light ? "#555" : "#bbb"}" font-weight="${index === selected ? "700" : "400"}">${EFFORT_LABELS[level]}</text>`).join("");
  const image = (left: number, width: number, label: string): string => {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="48" viewBox="${left} 0 ${width} 48">${body}</svg>`;
    return `<img src="data:image/svg+xml,${encodeURIComponent(svg)}" width="${width}" height="48" alt="${label}"/>`;
  };
  if (!interactive) { return image(0, 264, `${EFFORT_LABELS[value] || "Default"} effort`); }
  return levels.map((level, index) => `[${image(index * 44, 44, `Set ${EFFORT_LABELS[level]} effort`)}](command:${SET_EFFORT_COMMAND}?${encodeURIComponent(JSON.stringify([level]))})`).join("");
}

function guardrailIndicator(guards: { label: string; known: boolean; on: boolean }[], light: boolean): string {
  const foreground = light ? "#333" : "#ccc";
  const rows = guards.map((guard, index) => {
    const x = index % 2 * 136, y = Math.floor(index / 2) * 22 + 16;
    const state = !guard.known ? "?" : guard.on ? "On" : "Off";
    return `<text x="${x}" y="${y}" fill="${foreground}">${guard.label}</text><text x="${x + 124}" y="${y}" text-anchor="end" fill="${guard.known && guard.on ? light ? "#007580" : "#00c9dc" : foreground}">${state}</text>`;
  }).join("");
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="264" height="66"><g font-family="system-ui,sans-serif" font-size="11">${rows}</g></svg>`;
  const description = guards.map(guard => `${guard.label}: ${!guard.known ? "Unknown" : guard.on ? "On" : "Off"}`).join("; ");
  return `<img src="data:image/svg+xml,${encodeURIComponent(svg)}" width="264" height="66" alt="${description}"/>`;
}
const ATTENTION: ReadonlySet<State> = new Set(["overridden-by", "not-covered", "cannot-detect", "unverified-for-version"]);

export function effortMeter(value: string): string {
  const selected = Object.keys(EFFORT_LABELS).indexOf(value);
  return selected < 0 ? "" : Object.keys(EFFORT_LABELS).map((_, index) => index <= selected ? "\u25b0" : "\u25b1").join("");
}

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

export function summarize(model: ViewModel | undefined, openCommand: string, compact = true, light = false, pendingEffort?: string): StatusSummary {
  const prefix = compact ? "" : "Nexus Hub: ";
  if (!model || (model.controls.length === 0 && !model.error)) {
    return { text: `${NEXUS_ICON} ${prefix}Reading...`, accessibilityLabel: "Nexus Hub, reading", tooltip: "Reading settings..." };
  }
  if (model.error) {
    return { text: `${NEXUS_ICON} ${prefix}Unavailable $(error)`, accessibilityLabel: "Nexus Hub, unavailable", tooltip: `**Attention**\n\n${escapeMarkdown(model.error.title)}` };
  }
  const summary = summarizePreferences(model);
  const issues = model.applicationIssues ?? effortApplicationIssues(model);
  const attention = summary.needsAttention || issues.length > 0;
  const effort = pendingEffort || summary.effort || "Default";
  const titled = EFFORT_LABELS[effort] || "Default";
  const protection = summary.guardsAvailable ? `Configured guardrails: ${summary.guardsEnabled} of ${summary.guardsAvailable} on` : "Configured guardrails: unavailable";
  const guards = [["git_safety", "Git safety"], ["secret_scan", "Secrets"], ["edit_preservation", "My edits"], ["large_file_warning", "Large files"], ["git_guardrails", "Git bypass"]].map(([id, label]) => {
    const control = model.controls.find((item) => item.id === id);
    const row = control?.rows.find((item) => item.tool === "internal") ?? control?.rows[0];
    const known = !!control?.canApply && !!row && !["cannot-detect", "unverified-for-version", "not-covered"].includes(row.state);
    const value = row ? effectiveValue(row) : null;
    const on = value === "on" || value === "true" || (row?.state === "tool-default" && id !== "git_guardrails");
    return { label: label!, known, on };
  });
  const issue = issues[0] ? escapeMarkdown(issues[0]) : null;
  const tooltip = [
    `**Effort** ${titled}${pendingEffort ? " (saving...)" : ""}`,
    effortIndicator(effort, light, !model.readOnly && !model.busy),
    "**Guardrails**",
    guardrailIndicator(guards, light),
    ...(issue ? [`**Attention** ${issue}`] : []),
  ].join("\n\n");
  const meter = effortMeter(effort);
  const shown = meter ? `${compact ? "" : "Effort: "}${meter} (${titled.toLowerCase()})` : `${prefix}${titled} (effort)`;
  return { text: `${NEXUS_ICON} ${shown}${attention ? " $(warning)" : ""}`, accessibilityLabel: `Nexus Hub, default effort ${effort}, ${protection.toLowerCase()}${attention ? ", needs attention" : ""}`, tooltip };
}

export class SettingsStatusBar implements vscode.Disposable {
  private readonly item: vscode.StatusBarItem;
  private model: ViewModel | undefined;
  private pendingEffort: string | undefined;
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
    const summary = summarize(model, this.openCommand, vscode.workspace.getConfiguration("nexusHubSettings").get<boolean>("compactStatusBar", true), vscode.window.activeColorTheme?.kind === vscode.ColorThemeKind.Light, this.pendingEffort);
    const tooltip = new vscode.MarkdownString(summary.tooltip, true);
    tooltip.supportHtml = true;
    tooltip.isTrusted = { enabledCommands: this.model && !this.model.readOnly && !this.model.busy ? [SET_EFFORT_COMMAND] : [] };
    this.item.text = summary.text;
    this.item.tooltip = tooltip;
    this.item.accessibilityInformation = { label: summary.accessibilityLabel, role: "button" };
  }
  previewEffort(value?: string): void { this.pendingEffort = value; this.update(this.model); }
  dispose(): void { this.configurationListener.dispose(); this.themeListener?.dispose(); this.item.dispose(); }
}
