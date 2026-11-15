import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { afterEach, beforeEach } from "vitest";

// Shared alert preferences (usage-alerts.json) must come from an empty home, never the
// developer's real ~/.nexus-hub. A test that needs its own home still sets NEXUS_HUB_HOME.
const previous = process.env.NEXUS_HUB_HOME;
let home: string | undefined;
beforeEach(() => { home = fs.mkdtempSync(path.join(os.tmpdir(), "usage-monitor-home-")); process.env.NEXUS_HUB_HOME = home; });
afterEach(() => {
  if (home) { fs.rmSync(home, { recursive: true, force: true }); }
  if (previous === undefined) { delete process.env.NEXUS_HUB_HOME; } else { process.env.NEXUS_HUB_HOME = previous; }
});
