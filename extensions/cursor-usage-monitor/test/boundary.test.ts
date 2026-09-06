import { readFileSync, readdirSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * Makes the README's no-cookie / no-scrape promise machine-enforced.
 *
 * v3.15.12's Definition of Done requires that claim stay literally true, and the
 * HO-5 probe closed as a negative precisely because the alternatives were reading
 * a cookie store or guessing header forms. A promise in prose is not a guarantee;
 * this test is. It reads the shipped source rather than trusting review.
 */

const SRC = fileURLToPath(new URL("../src", import.meta.url));

/**
 * The disclosure text in `consent.ts` names these on purpose - it is the promise
 * NOT to read them - so that one file is exempt from the string check and gets a
 * dedicated assertion instead.
 */
const DISCLOSURE_FILE = "consent.ts";

/** API surfaces that would actually perform a forbidden read. */
const FORBIDDEN_CALLS: ReadonlyArray<{ pattern: RegExp; why: string }> = [
  { pattern: /Cookies?["'`\s]*\)/i, why: "a cookie store open" },
  { pattern: /Login\s*Data/i, why: "the browser Login Data file" },
  { pattern: /keytar|keychain|credential-?manager|secret-?service/i, why: "an OS keychain" },
  { pattern: /ai-code-tracking/i, why: "Cursor's undocumented ai-tracking database" },
  // Note this forbids FETCHING a billing page, not linking to one. Handing the
  // user their browser via openExternal is the authoritative-figures escape hatch
  // the plan deliberately keeps; scraping is what is out of bounds.
  { pattern: /fetch\([^)]*dashboard\/(spending|usage)/i, why: "a fetch of an HTML billing page" },
  { pattern: /process\.memoryUsage|\/proc\//i, why: "process memory" },
  { pattern: /\.bash_history|\.zsh_history|ConsoleHost_history/i, why: "shell history" }
];

function sourceFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((entry) => {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      return sourceFiles(full);
    }
    return entry.endsWith(".ts") ? [full] : [];
  });
}

describe("privacy boundary is enforced by the source, not by review", () => {
  const files = sourceFiles(SRC);

  it("ships a non-trivial source tree, so the sweep is meaningful", () => {
    // A passing sweep over zero files would be a false guarantee.
    expect(files.length).toBeGreaterThan(8);
  });

  it.each(FORBIDDEN_CALLS)(
    "never performs $why",
    ({ pattern }) => {
      const offenders = files.filter((file) => {
        if (file.endsWith(DISCLOSURE_FILE)) {
          return false;
        }
        return pattern.test(readFileSync(file, "utf8"));
      });
      expect(offenders).toEqual([]);
    }
  );

  it("names every exclusion in the consent disclosure, and only there", () => {
    const disclosure = readFileSync(join(SRC, "providers", DISCLOSURE_FILE), "utf8");
    // The prompt is the only place the user learns what is excluded, so each
    // exclusion must actually appear in it.
    for (const term of [
      "cookies",
      "Login Data",
      "keychain",
      "process memory",
      "shell history",
      "HTML"
    ]) {
      expect(disclosure).toContain(term);
    }
  });

  it("reads the state database only through the allowlisted-key adapter", () => {
    const openers = files.filter((file) =>
      /state\.vscdb|DatabaseSync/.test(readFileSync(file, "utf8"))
    );
    // Exactly two: the adapter that opens it, and the path resolver that names the
    // candidate. A third would be a second, unreviewed read path.
    const names = openers.map((file) => file.split(/[\\/]/).pop()).sort();
    expect(names).toEqual(["auth.ts", "session.ts"]);
  });

  it("labels the undocumented route credential-api and never public-api", () => {
    for (const file of files) {
      expect(readFileSync(file, "utf8")).not.toContain("public-api");
    }
  });

  it("links to the official dashboard rather than fetching it", () => {
    const runtime = readFileSync(join(SRC, "cursorUsageRuntime.ts"), "utf8");
    // The escape hatch to authoritative figures must remain, so its absence is a
    // regression too: a monitor that cannot say "the real numbers are over there"
    // is worse for the user than one that can.
    expect(runtime).toContain("dashboard/usage");
    expect(runtime).toContain("openExternal");
  });
});
