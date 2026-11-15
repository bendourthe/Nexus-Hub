import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { afterEach, beforeEach, expect, it } from "vitest";
import { initializeInstallationDefaults } from "../src/installationDefaults";
import { readSessionDefaults } from "../src/sessionDefaults";
let hub: string;
beforeEach(() => { hub = fs.mkdtempSync(path.join(os.tmpdir(), "nexus-install-defaults-")); });
afterEach(() => fs.rmSync(hub, {recursive: true, force: true}));
it("seeds Medium, Fast off and Codex tabs on exactly once", () => {
  initializeInstallationDefaults(hub);
  expect(JSON.parse(fs.readFileSync(path.join(hub, "preferences.json"), "utf8"))).toEqual({default_effort: "medium"});
  const first = readSessionDefaults(path.join(hub, "session-defaults.json"));
  expect(first).toMatchObject({fastMode: false, codexTabs: true}); expect(first.fastRevision).not.toBe("");
  initializeInstallationDefaults(hub);
  expect(readSessionDefaults(path.join(hub, "session-defaults.json"))).toEqual(first);
});
it("preserves all existing files byte for byte, including malformed data", () => {
  for (const name of ["preferences.json", "session-defaults.json"]) { fs.writeFileSync(path.join(hub, name), "invalid user data"); }
  initializeInstallationDefaults(hub);
  for (const name of ["preferences.json", "session-defaults.json"]) { expect(fs.readFileSync(path.join(hub, name), "utf8")).toBe("invalid user data"); }
});
it("preserves explicit choices and unrelated keys", () => {
  const effort = '{"default_effort":"ultra","future":42}', speed = '{"fastMode":true,"codexTabs":false,"fastRevision":"manual"}';
  fs.writeFileSync(path.join(hub, "preferences.json"), effort); fs.writeFileSync(path.join(hub, "session-defaults.json"), speed);
  initializeInstallationDefaults(hub);
  expect(fs.readFileSync(path.join(hub, "preferences.json"), "utf8")).toBe(effort);
  expect(fs.readFileSync(path.join(hub, "session-defaults.json"), "utf8")).toBe(speed);
});
