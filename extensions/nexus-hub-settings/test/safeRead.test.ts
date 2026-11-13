import * as fs from "node:fs";
import { syncBuiltinESMExports } from "node:module";
import * as os from "node:os";
import * as path from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { readBoundedFile, readRegularFileSync } from "../src/safeRead";
import { readSessionDefaults } from "../src/sessionDefaults";
import { readUsageAlerts } from "../src/usageAlerts";

let root: string, file: string;
beforeEach(() => { root = fs.mkdtempSync(path.join(os.tmpdir(), "nexus-safe-read-")); file = path.join(root, "data.json"); });
afterEach(() => fs.rmSync(root, { recursive: true, force: true }));
const options = { maxBytes: 100, refuseSymlink: true, refusal: "refused" };

describe("readRegularFileSync", () => {
  it("returns the text of a regular file within the limit", () => {
    fs.writeFileSync(file, "hello");
    expect(readRegularFileSync(file, options)).toBe("hello");
  });
  it("keeps the native ENOENT for a missing file", () => {
    expect(() => readRegularFileSync(file, options)).toThrow(expect.objectContaining({ code: "ENOENT" }));
  });
  it("refuses an oversized file and a directory with the given message", () => {
    fs.writeFileSync(file, "x".repeat(101));
    expect(() => readRegularFileSync(file, options)).toThrow("refused");
    const dir = path.join(root, "dir"); fs.mkdirSync(dir);
    expect(() => readRegularFileSync(dir, options)).toThrow("refused");
  });
  it("refuses a symbolic link when asked and follows it otherwise", (context) => {
    fs.writeFileSync(file, "linked");
    const link = path.join(root, "link.json");
    try { fs.symlinkSync(file, link); } catch { context.skip(); return; }
    expect(() => readRegularFileSync(link, options)).toThrow("refused");
    expect(readRegularFileSync(link, { ...options, refuseSymlink: false })).toBe("linked");
  });
});

describe("readRegularFileSync without O_NOFOLLOW", () => {
  afterEach(() => { vi.restoreAllMocks(); syncBuiltinESMExports(); });
  it.skipIf(!!fs.constants.O_NOFOLLOW)("refuses a path that resolves as a link after the open", () => {
    fs.writeFileSync(file, "linked");
    const mocked = vi.spyOn(require("node:fs"), "readlinkSync").mockReturnValue("elsewhere"); syncBuiltinESMExports();
    expect(() => readRegularFileSync(file, options)).toThrow("refused");
    expect(mocked).toHaveBeenCalledWith(file);
  });
});

describe("readBoundedFile", () => {
  it("reads within the limit, refuses beyond it, and keeps ENOENT", async () => {
    fs.writeFileSync(file, "abc");
    await expect(readBoundedFile(file, 10, "too large")).resolves.toBe("abc");
    await expect(readBoundedFile(file, 2, "too large")).rejects.toThrow("too large");
    await expect(readBoundedFile(path.join(root, "none"), 2, "too large")).rejects.toMatchObject({ code: "ENOENT" });
  });
});

describe("preference readers", () => {
  it("preserve a redirected, oversized, or non-object preference file instead of reading it", (context) => {
    fs.writeFileSync(file, JSON.stringify({ pad: "x".repeat(17000) }));
    expect(() => readUsageAlerts(file)).toThrow("too large");
    expect(() => readSessionDefaults(file)).toThrow("too large");
    fs.writeFileSync(file, "[1]");
    expect(() => readUsageAlerts(file)).toThrow("JSON object");
    expect(() => readSessionDefaults(file)).toThrow("JSON object");
    const target = path.join(root, "target.json"), link = path.join(root, "link.json");
    fs.writeFileSync(target, "{}");
    try { fs.symlinkSync(target, link); } catch { context.skip(); return; }
    expect(() => readUsageAlerts(link)).toThrow("redirected");
    expect(() => readSessionDefaults(link)).toThrow("redirected");
  });
});
