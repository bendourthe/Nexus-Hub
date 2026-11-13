import * as fs from "node:fs/promises";
import * as os from "node:os";
import * as path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { installVendorUi, restoreVendorUi } from "../src/vendorUiInstall";
import { UI_RECIPES } from "../src/vendorUiPatch";

const UNVERIFIED = "26.9999.1";
const manifest = (overrides: Record<string, unknown> = {}) => JSON.stringify({
  publisher: "openai", name: "chatgpt", version: UNVERIFIED,
  contributes: {
    commands: [{ command: "chatgpt.openSidebar", title: "Open Codex", icon: "$(codex)" }, { command: "chatgpt.newCodexPanel", title: "New Codex Panel" }],
    menus: { "editor/title": [{ command: "chatgpt.openSidebar", group: "navigation" }] },
  },
  ...overrides,
}, null, 2) + "\n";

let scratch: string, root: string, storage: string;
const read = (relative: string) => fs.readFile(path.join(root, relative), "utf8");
beforeEach(async () => {
  scratch = await fs.mkdtemp(path.join(os.tmpdir(), "nexus-codex-menu-"));
  root = await fs.realpath(scratch).then((real) => path.join(real, "openai.chatgpt-" + UNVERIFIED));
  storage = path.join(scratch, "native-ui");
  await fs.mkdir(path.join(root, "out"), { recursive: true });
  await fs.writeFile(path.join(root, "package.json"), manifest());
  await fs.writeFile(path.join(root, "out", "extension.js"), "/* vendor code */\n");
});
afterEach(() => fs.rm(scratch, { recursive: true, force: true }));

describe("installVendorUi on an unverified Codex build", () => {
  it("routes the editor title button and leaves the pinned code files untouched", async () => {
    const result = await installVendorUi("codex", root, storage);
    expect(result).toMatchObject({ changed: true, menuOnly: true });
    const menu = JSON.parse(await read("package.json")).contributes.menus["editor/title"];
    expect(menu).toEqual([{ command: "chatgpt.openSidebar", group: "navigation", when: "!nexusHubSettings.enabled" }, { command: "nexusHubSettings.openCodex", group: "navigation", when: "nexusHubSettings.enabled" }]);
    expect(await read("out/extension.js")).toBe("/* vendor code */\n");
    expect(JSON.parse(await fs.readFile(result.receipt, "utf8"))).toMatchObject({ version: UNVERIFIED, files: [{ relative: "package.json" }] });
  });

  it("is idempotent and restores the exact original manifest", async () => {
    const first = await installVendorUi("codex", root, storage);
    expect((await installVendorUi("codex", root, storage)).changed).toBe(false);
    await restoreVendorUi(first.receipt);
    expect(await read("package.json")).toBe(manifest());
  });

  it("preserves a Codex menu whose structure changed", async () => {
    const changed = manifest({ contributes: { commands: [], menus: { "editor/title": [] } } });
    await fs.writeFile(path.join(root, "package.json"), changed);
    await expect(installVendorUi("codex", root, storage)).rejects.toThrow("The Codex editor menu");
    expect(await read("package.json")).toBe(changed);
  });

  it("rejects a manifest from another publisher", async () => {
    await fs.writeFile(path.join(root, "package.json"), manifest({ publisher: "someone-else" }));
    await expect(installVendorUi("codex", root, storage)).rejects.toThrow("identity is not recognized");
  });

  it("keeps Claude Code pinned to its qualified build", async () => {
    await fs.writeFile(path.join(root, "package.json"), JSON.stringify({ publisher: "anthropic", name: "claude-code", version: UNVERIFIED }));
    expect(UI_RECIPES.claude.version).not.toBe(UNVERIFIED);
    await expect(installVendorUi("claude", root, storage)).rejects.toThrow("has not been verified for this extension version");
  });
});
