import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { afterEach, beforeEach, expect, it } from "vitest";
import { readSessionDefaults, writeSessionDefault } from "../src/sessionDefaults";

let root: string, file: string;
beforeEach(() => { root = fs.mkdtempSync(path.join(os.tmpdir(), "nexus-session-defaults-")); file = path.join(root, "defaults.json"); });
afterEach(() => fs.rmSync(root, {recursive: true, force: true}));
it("preserves native speed until chosen and keeps the existing Codex tab behavior", () => {
  expect(readSessionDefaults(file)).toEqual({fastMode: null, fastRevision: "", codexTabs: true});
  writeSessionDefault(file, "applyAll"); expect(fs.existsSync(file)).toBe(false);
});
it("keeps speed revisions independent from Codex navigation and preserves unknown keys", () => {
  fs.writeFileSync(file, JSON.stringify({future: "keep"}));
  writeSessionDefault(file, "fastMode", true); const first = readSessionDefaults(file);
  writeSessionDefault(file, "codexTabs", false);
  expect(readSessionDefaults(file)).toEqual({...first, codexTabs: false});
  writeSessionDefault(file, "fastMode", true); expect(readSessionDefaults(file).fastRevision).toBe(first.fastRevision);
  writeSessionDefault(file, "applyAll"); expect(readSessionDefaults(file).fastRevision).not.toBe(first.fastRevision);
  expect(JSON.parse(fs.readFileSync(file, "utf8")).future).toBe("keep");
});
it("preserves malformed data and another editor's active write lock", () => {
  fs.writeFileSync(file, "invalid");
  expect(() => writeSessionDefault(file, "fastMode", false)).toThrow();
  expect(fs.readFileSync(file, "utf8")).toBe("invalid"); expect(fs.existsSync(file + ".lock")).toBe(false);
  fs.writeFileSync(file + ".lock", "other editor");
  expect(() => writeSessionDefault(file, "codexTabs", false)).toThrow();
  expect(fs.readFileSync(file + ".lock", "utf8")).toBe("other editor");
});
it("rejects invalid values and leaves effort preferences alone", () => {
  fs.writeFileSync(file, JSON.stringify({fastMode: true, fastRevision: "existing", default_effort: "high"}));
  expect(() => writeSessionDefault(file, "fastMode", "true" as never)).toThrow("Invalid");
  writeSessionDefault(file, "fastMode", false);
  expect(readSessionDefaults(file).fastMode).toBe(false);
  expect(JSON.parse(fs.readFileSync(file, "utf8")).default_effort).toBe("high");
});
