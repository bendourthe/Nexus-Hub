import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * Guards the v3.16.3 Phase 1 rename mechanically.
 *
 * A partial rename does not fail at compile time: a stale `getConfiguration("githubUsage")`
 * still type-checks and still returns a value, it just silently returns the default
 * instead of the user's setting. These assertions are what turn that into a loud
 * failure rather than a monitor that quietly forgets its configuration.
 */

const EXTENSION_ROOT = join(__dirname, "..");
const OLD_COMMAND_PREFIX = "github-usage.";
const OLD_CONFIG_PREFIX = "githubUsage.";

function sourceFiles(directory: string): string[] {
  return readdirSync(directory).flatMap((entry) => {
    const path = join(directory, entry);
    if (statSync(path).isDirectory()) return sourceFiles(path);
    return path.endsWith(".ts") ? [path] : [];
  });
}

const manifest = JSON.parse(readFileSync(join(EXTENSION_ROOT, "package.json"), "utf8")) as {
  displayName: string;
  version: string;
  contributes: {
    commands: Array<{ command: string; title: string; category: string }>;
    configuration: { title: string; properties: Record<string, unknown> };
    views: Record<string, Array<{ id: string; when?: string }>>;
    viewsContainers: { activitybar: Array<{ id: string }> };
  };
};

describe("v3.16.3 rename completeness", () => {
  it("leaves no old command id or configuration prefix anywhere in src/", () => {
    const offenders = sourceFiles(join(EXTENSION_ROOT, "src"))
      .filter((path) => {
        const body = readFileSync(path, "utf8");
        // `migration.ts` is the one file that MUST name the old keys: migrating
        // away from them is its entire job.
        if (path.endsWith("migration.ts")) return false;
        return body.includes(OLD_COMMAND_PREFIX) || body.includes(OLD_CONFIG_PREFIX);
      })
      .map((path) => path.slice(EXTENSION_ROOT.length + 1));
    expect(offenders).toEqual([]);
  });

  it("declares no old command id or configuration key in the contributes block", () => {
    const contributes = JSON.stringify(manifest.contributes);
    expect(contributes).not.toContain(OLD_COMMAND_PREFIX);
    expect(contributes).not.toContain(OLD_CONFIG_PREFIX);
  });

  it("titles every user-visible surface with the reverted name", () => {
    expect(manifest.displayName).toBe("GitHub Usage Monitor");
    expect(manifest.version).toBe("0.2.0");
    expect(manifest.contributes.configuration.title).toBe("GitHub Usage Monitor");
    for (const command of manifest.contributes.commands) {
      expect(command.category).toBe("GitHub Usage Monitor");
      expect(command.title.startsWith("GitHub Usage Monitor: ")).toBe(true);
      expect(command.command.startsWith("githubUsageMonitor.")).toBe(true);
    }
  });

  it("moves the warning view container, view, and when-clause context key together", () => {
    expect(manifest.contributes.viewsContainers.activitybar[0]?.id).toBe("githubUsageMonitorWarning");
    const views = manifest.contributes.views.githubUsageMonitorWarning;
    expect(views?.[0]?.id).toBe("githubUsageMonitorWarningView");
    expect(views?.[0]?.when).toBe("githubUsageMonitor.warningActive");
  });

  it("registers exactly the commands it declares, in both directions", () => {
    const source = readFileSync(join(EXTENSION_ROOT, "src", "extension.ts"), "utf8");
    const registered = [...source.matchAll(/registerCommand\("([^"]+)"/gu)].map((match) => match[1]);
    const declared = manifest.contributes.commands.map((command) => command.command);
    // A declared-but-unregistered id fails at runtime with "command not found";
    // a registered-but-undeclared id is unreachable from the Command Palette.
    expect([...declared].sort()).toEqual([...registered].sort());
  });
});
