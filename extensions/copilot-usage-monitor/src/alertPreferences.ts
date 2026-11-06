import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

/** Shared Nexus preferences affect warning panels only, never usage meters. */
export function usageAlertsFile(): string {
  const override = process.env.NEXUS_HUB_HOME?.trim();
  return path.join(override && path.isAbsolute(override) ? override : path.join(os.homedir(), ".nexus-hub"), "usage-alerts.json");
}
export function usageAlertEnabled(provider: string): boolean {
  try {
    const file = usageAlertsFile(), stat = fs.lstatSync(file);
    if (!stat.isFile() || stat.isSymbolicLink() || stat.size > 16384) { return true; }
    const data: unknown = JSON.parse(fs.readFileSync(file, "utf8"));
    return !data || typeof data !== "object" || Array.isArray(data) || (data as Record<string, unknown>)[provider] !== false;
  } catch { return true; }
}
export function watchUsageAlerts(provider: string, disabled: () => void): {dispose(): void} {
  const file = usageAlertsFile();
  const changed = (): void => { if (!usageAlertEnabled(provider)) { disabled(); } };
  fs.watchFile(file, {interval: 500, persistent: false}, changed);
  return {dispose: () => fs.unwatchFile(file, changed)};
}
