import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

/** Shared Nexus preferences affect warning panels only, never usage meters. */
export function usageAlertsFile(): string {
  const override = process.env.NEXUS_HUB_HOME?.trim();
  return path.join(override && path.isAbsolute(override) ? override : path.join(os.homedir(), ".nexus-hub"), "usage-alerts.json");
}
/** Reads the preferences through one open handle so the type and size checks cannot race a swap of the path. */
function readAlertsFile(file: string): string | undefined {
  const noFollow = fs.constants.O_NOFOLLOW || 0;
  const fd = fs.openSync(file, fs.constants.O_RDONLY | noFollow | (fs.constants.O_NONBLOCK || 0));
  try {
    const stat = fs.fstatSync(fd);
    if (!stat.isFile() || stat.size > 16384) { return undefined; }
    // Windows has no O_NOFOLLOW: a link is refused by asking for its target after the open.
    if (!noFollow) { try { fs.readlinkSync(file); return undefined; } catch { /* Not a link. */ } }
    const text = fs.readFileSync(fd, "utf8");
    return Buffer.byteLength(text) > 16384 ? undefined : text;
  } finally { fs.closeSync(fd); }
}
export function usageAlertEnabled(provider: string): boolean {
  try {
    const text = readAlertsFile(usageAlertsFile());
    if (text === undefined) { return true; }
    const data: unknown = JSON.parse(text);
    return !data || typeof data !== "object" || Array.isArray(data) || (data as Record<string, unknown>)[provider] !== false;
  } catch { return true; }
}
export function watchUsageAlerts(provider: string, disabled: () => void): {dispose(): void} {
  const file = usageAlertsFile();
  const changed = (): void => { if (!usageAlertEnabled(provider)) { disabled(); } };
  fs.watchFile(file, {interval: 500, persistent: false}, changed);
  return {dispose: () => fs.unwatchFile(file, changed)};
}
