import * as vscode from "vscode";
import { DEFAULT_URGENCY_COLORS } from "./embeddedSettings";
import type { UrgencyLevel } from "./recommendations";

/**
 * Status bar background coloring, ported from the sibling Claude monitor.
 *
 * VS Code accepts only two theme color IDs for `StatusBarItem.backgroundColor`:
 * `statusBarItem.warningBackground` and `statusBarItem.errorBackground`. A hex value
 * or any other ID is silently ignored, which is why the user's chosen hex is written
 * into `workbench.colorCustomizations` under those two keys instead. Moderate and
 * High share the warning key, so its hex is swapped to match the active level.
 */
type Level = Exclude<UrgencyLevel, "low">;
export type ColorConfig = Record<Level, string>;

const HEX_COLOR = /^#[0-9a-fA-F]{6}$/u;
const WARNING_KEY = "statusBarItem.warningBackground";
const ERROR_KEY = "statusBarItem.errorBackground";

/** Read the color settings; anything other than `none` or `#rrggbb` falls back to the default. */
export function getColorConfig(): ColorConfig {
  const c = vscode.workspace.getConfiguration("cursorUsage");
  const read = (level: Level): string => {
    const raw = c.get<unknown>(`colors.${level}`);
    return typeof raw === "string" && (raw === "none" || HEX_COLOR.test(raw))
      ? raw
      : DEFAULT_URGENCY_COLORS[level];
  };
  return { moderate: read("moderate"), high: read("high"), critical: read("critical") };
}

/** The theme color for an urgency, or undefined for no highlight. */
export function backgroundColorFor(
  urgency: UrgencyLevel,
  colors: ColorConfig
): vscode.ThemeColor | undefined {
  if (urgency === "low" || colors[urgency] === "none") {
    return undefined;
  }
  return new vscode.ThemeColor(urgency === "critical" ? ERROR_KEY : WARNING_KEY);
}

/**
 * Write the active level's hex into `workbench.colorCustomizations`.
 *
 * Only the key the active level uses is touched, and only when its value changes, so
 * a refresh does not rewrite the user's settings file. At Low nothing is written:
 * the Claude and Codex monitors share these two keys, and overwriting them here
 * would recolor a warning another monitor is showing.
 */
export async function syncActiveColorToWorkbench(
  urgency: UrgencyLevel,
  colors: ColorConfig
): Promise<void> {
  if (urgency === "low") {
    return;
  }
  const key = urgency === "critical" ? ERROR_KEY : WARNING_KEY;
  const hex = colors[urgency];
  const workbench = vscode.workspace.getConfiguration("workbench");
  const existing: Record<string, string> = {
    ...(workbench.get<Record<string, string>>("colorCustomizations") ?? {})
  };
  if (hex === "none" || existing[key] === hex) {
    return;
  }
  existing[key] = hex;
  await workbench.update(
    "colorCustomizations",
    existing,
    vscode.ConfigurationTarget.Global
  );
}
