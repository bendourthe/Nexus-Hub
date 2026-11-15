import * as fs from "node:fs";
import * as path from "node:path";
import { randomUUID } from "node:crypto";
import { readRegularFileSync } from "./safeRead";

export const ALERT_PROVIDERS = ["claude", "codex", "copilot", "cursor", "gemini"] as const;
export type AlertProvider = typeof ALERT_PROVIDERS[number];
export type UsageAlerts = Record<AlertProvider, boolean>;
export function alertProvidersForEditor(appName: string): AlertProvider[] {
  if (/cursor/i.test(appName)) { return ["cursor"]; }
  if (/antigravity|gemini/i.test(appName)) { return ["gemini"]; }
  return ["claude", "codex", "copilot"];
}
export const USAGE_ALERTS_FILE = "usage-alerts.json";

function read(file: string): Record<string, unknown> {
  try {
    const data: unknown = JSON.parse(readRegularFileSync(file, {maxBytes: 16384, refuseSymlink: true, refusal: "The usage-alert preferences are redirected or too large and were preserved."}));
    if (!data || typeof data !== "object" || Array.isArray(data)) { throw new Error("Usage-alert preferences must be a JSON object."); }
    return data as Record<string, unknown>;
  } catch (error) { if ((error as NodeJS.ErrnoException).code === "ENOENT") { return {}; } throw error; }
}
export function readUsageAlerts(file: string): UsageAlerts {
  const data = read(file);
  return Object.fromEntries(ALERT_PROVIDERS.map(provider => [provider, data[provider] !== false])) as UsageAlerts;
}
export function writeUsageAlert(file: string, provider: AlertProvider | "all", enabled: boolean, scope: readonly AlertProvider[] = ALERT_PROVIDERS): void {
  if (provider !== "all" && !ALERT_PROVIDERS.includes(provider) || typeof enabled !== "boolean") { throw new Error("Invalid usage-alert preference."); }
  if (!scope.length || scope.some(key => !ALERT_PROVIDERS.includes(key)) || provider !== "all" && !scope.includes(provider)) { throw new Error("Invalid usage-alert scope."); }
  fs.mkdirSync(path.dirname(file), {recursive: true});
  const lock = file + ".lock", temporary = file + "." + randomUUID();
  let descriptor: number | undefined;
  try {
    descriptor = fs.openSync(lock, "wx");
    const data = read(file);
    for (const key of provider === "all" ? scope : [provider]) { data[key] = enabled; }
    fs.writeFileSync(temporary, JSON.stringify(data, null, 2) + "\n", {flag: "wx"});
    fs.renameSync(temporary, file);
  } finally {
    try { fs.unlinkSync(temporary); } catch { /* No staged write remains. */ }
    if (descriptor !== undefined) { fs.closeSync(descriptor); fs.unlinkSync(lock); }
  }
}
