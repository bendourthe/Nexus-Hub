import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Cross-extension parity for the threshold-warning surface.
 *
 * All four usage monitors must warn through their styled webview and nothing
 * else. v3.18.1 fixed a case where the GitHub monitor fired a native toast
 * alongside the panel and then auto-dismissed the panel behind it, so the toast
 * was the only surface the user ever saw. The four extensions have different
 * module layouts and different symbol names, so this asserts on source text
 * rather than importing them - an import-based test would couple four
 * independently versioned extensions to each other's internals.
 */

const EXTENSIONS_DIR = join(dirname(fileURLToPath(import.meta.url)), "..", "..");

/** Where each monitor's alert path lives. The GitHub monitor is the subject; the other three are the reference. */
const MONITORS: ReadonlyArray<{ name: string; alertPath: string; warningViewPath: string }> = [
  { name: "claude-usage-monitor", alertPath: "src/extension.ts", warningViewPath: "src/warningView.ts" },
  { name: "codex-usage-monitor", alertPath: "src/extension.ts", warningViewPath: "src/warningView.ts" },
  { name: "cursor-usage-monitor", alertPath: "src/cursorUsageRuntime.ts", warningViewPath: "src/warningView.ts" },
  { name: "github-usage-monitor", alertPath: "src/extension.ts", warningViewPath: "src/warningView.ts" }
];

/**
 * Documented divergences. Empty by design: a monitor that genuinely needs to
 * differ is recorded here with its reason rather than by loosening the patterns
 * below, so the exemption is reviewable instead of invisible.
 */
const DOCUMENTED_EXEMPTIONS: ReadonlyArray<{ monitor: string; assertion: string; reason: string }> = [];

function exempt(monitor: string, assertion: string): boolean {
  return DOCUMENTED_EXEMPTIONS.some((e) => e.monitor === monitor && e.assertion === assertion);
}

function read(monitor: string, relative: string): string | null {
  const path = join(EXTENSIONS_DIR, monitor, relative);
  return existsSync(path) ? readFileSync(path, "utf8") : null;
}

/**
 * The body of the function enclosing `needleIndex`, found by brace balance.
 *
 * Walks outward from the needle to the nearest enclosing `{` whose header line
 * looks like a function or method signature, then forward to its matching `}`.
 */
export function enclosingFunctionBody(source: string, needleIndex: number): string {
  let cursor = needleIndex;
  while (cursor > 0) {
    let depth = 0;
    let open = -1;
    for (let i = cursor - 1; i >= 0; i -= 1) {
      const ch = source[i];
      if (ch === "}") depth += 1;
      else if (ch === "{") {
        if (depth === 0) { open = i; break; }
        depth -= 1;
      }
    }
    if (open === -1) return source.slice(0, needleIndex);
    const headerStart = source.lastIndexOf("\n", open) + 1;
    const header = source.slice(headerStart, open);
    if (/\)\s*(:\s*[^{]+)?\s*$/.test(header) && header.includes("(")) {
      let depthForward = 0;
      for (let i = open; i < source.length; i += 1) {
        if (source[i] === "{") depthForward += 1;
        else if (source[i] === "}") {
          depthForward -= 1;
          if (depthForward === 0) return source.slice(open, i + 1);
        }
      }
      return source.slice(open);
    }
    cursor = open;
  }
  return source.slice(0, needleIndex);
}

/** The index of the call that reveals the warning webview, or -1. */
function warningShowCallIndex(source: string): number {
  return source.search(/\bwarning(View)?\??\.show\(|\bthis\.warningView\.show\(/);
}

describe("cross-extension warning parity", () => {
  for (const monitor of MONITORS) {
    it(`${monitor.name}: the alert path reveals the webview without a competing toast`, () => {
      const source = read(monitor.name, monitor.alertPath);
      if (source === null) {
        console.warn(`skipped: ${monitor.name}/${monitor.alertPath} is absent (partial checkout)`);
        return;
      }
      if (exempt(monitor.name, "no-toast-on-alert-path")) return;

      const index = warningShowCallIndex(source);
      expect(index, `${monitor.name}/${monitor.alertPath} has no warning-view show call; the alert path moved and this test needs its new location`).toBeGreaterThan(-1);

      const body = enclosingFunctionBody(source, index);
      expect(body).not.toMatch(
        /showWarningMessage/
      );
    });

    it(`${monitor.name}: the warning view provider reveals an already-resolved view`, () => {
      const source = read(monitor.name, monitor.warningViewPath);
      if (source === null) {
        console.warn(`skipped: ${monitor.name}/${monitor.warningViewPath} is absent (partial checkout)`);
        return;
      }
      if (exempt(monitor.name, "reveal-resolved-view")) return;

      expect(
        /(this\.)?view\.show\(/.test(source),
        `${monitor.name}/${monitor.warningViewPath} never calls view.show(...); a repeat threshold crossing would rewrite an invisible panel`
      ).toBe(true);
    });
  }
});
