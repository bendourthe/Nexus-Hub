import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { beforeEach, afterEach, it, expect } from "vitest";
import { alertProvidersForEditor, readUsageAlerts, writeUsageAlert } from "../src/usageAlerts";
let root: string, file: string;
beforeEach(() => {root = fs.mkdtempSync(path.join(os.tmpdir(), "nexus-alerts-")); file = path.join(root, "usage-alerts.json");});
afterEach(() => fs.rmSync(root, {recursive: true, force: true}));
it("defaults all providers on, applies all, and preserves individual overrides", () => {
  expect(Object.values(readUsageAlerts(file))).toEqual([true,true,true,true,true]);
  writeUsageAlert(file, "all", false); expect(Object.values(readUsageAlerts(file))).toEqual([false,false,false,false,false]);
  writeUsageAlert(file, "codex", true); expect(readUsageAlerts(file)).toEqual({claude:false,codex:true,copilot:false,cursor:false,gemini:false});
  writeUsageAlert(file, "all", true); expect(Object.values(readUsageAlerts(file))).toEqual([true,true,true,true,true]);
});
it("preserves unrelated preferences and refuses malformed files or invalid providers", () => {
  fs.writeFileSync(file, JSON.stringify({future: 42, claude: false}));
  writeUsageAlert(file, "codex", false); expect(JSON.parse(fs.readFileSync(file,"utf8")).future).toBe(42);
  expect(() => writeUsageAlert(file, "other" as never, false)).toThrow("Invalid");
  fs.writeFileSync(file,"invalid"); expect(() => writeUsageAlert(file,"all",false)).toThrow(); expect(fs.readFileSync(file,"utf8")).toBe("invalid");
});
it("preserves another editor's write lock", () => {
  fs.writeFileSync(file + ".lock", "busy"); expect(() => writeUsageAlert(file,"all",false)).toThrow();
  expect(fs.readFileSync(file + ".lock","utf8")).toBe("busy"); expect(fs.existsSync(file)).toBe(false);
});

it.each([
  ["Visual Studio Code", ["claude", "codex", "copilot"]],
  ["Visual Studio Code - Insiders", ["claude", "codex", "copilot"]],
  ["Cursor", ["cursor"]],
  ["Antigravity", ["gemini"]],
])("scopes %s alerts without changing other editors", (editor, expected) => {
  const scope = alertProvidersForEditor(editor);
  expect(scope).toEqual(expected);
  writeUsageAlert(file, "all", false, scope);
  const values = readUsageAlerts(file);
  for (const key of Object.keys(values) as (keyof typeof values)[]) {
    expect(values[key]).toBe(!scope.includes(key));
  }
  writeUsageAlert(file, "all", true, scope);
  expect(Object.values(readUsageAlerts(file))).toEqual([true,true,true,true,true]);
});
it("rejects preferences outside the editor scope", () => {
  expect(() => writeUsageAlert(file, "claude", false, ["cursor"])).toThrow("scope");
  expect(() => writeUsageAlert(file, "all", false, [])).toThrow("scope");
});
