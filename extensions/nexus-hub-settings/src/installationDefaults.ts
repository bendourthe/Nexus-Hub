import * as fs from "node:fs";
import * as path from "node:path";
import { randomUUID } from "node:crypto";

/** Seed only absent files. Upgrades and concurrent editors never replace saved choices. */
export function initializeInstallationDefaults(hub: string): void {
  fs.mkdirSync(hub, {recursive: true});
  for (const [name, value] of [
    ["preferences.json", {default_effort: "medium"}],
    ["session-defaults.json", {fastMode: false, fastRevision: randomUUID(), codexTabs: true}],
  ] as const) {
    try { fs.writeFileSync(path.join(hub, name), JSON.stringify(value, null, 2) + "\n", {flag: "wx"}); }
    catch (error) { if ((error as NodeJS.ErrnoException).code !== "EEXIST") { throw error; } }
  }
}
