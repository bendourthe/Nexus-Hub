/* Qualify the pinned native builds in disposable copies, without altering installed vendors. */
const fs = require("node:fs/promises");
const path = require("node:path");
const assert = require("node:assert/strict");
const ts = require("typescript");
const { installVendorUi, restoreVendorUi } = require("../out/vendorUiInstall");
const { UI_RECIPES, uiHash } = require("../out/vendorUiPatch");

async function main() {
  const [extensions, output] = process.argv.slice(2);
  if (!extensions || !output) { throw Error("Usage: node scripts/verify-vendor-ui-adapters.js EXTENSIONS_DIRECTORY OUTPUT_DIRECTORY"); }
  await fs.mkdir(output, { recursive: true });
  const scratch = await fs.mkdtemp(path.join(output, "vendor-ui-"));
  const report = [];
  const directories = await fs.readdir(extensions);
  for (const vendor of ["claude", "codex"]) {
    const recipe = UI_RECIPES[vendor];
    const prefix = (vendor === "claude" ? "anthropic.claude-code-" : "openai.chatgpt-") + recipe.version + "-";
    const name = directories.find((entry) => entry.startsWith(prefix));
    if (!name) { throw Error("Missing pinned vendor: " + prefix); }
    const root = path.join(scratch, name);
    const originals = new Map();
    for (const relative of [...Object.keys(recipe.files), "package.json"]) {
      const file = path.join(root, relative);
      await fs.mkdir(path.dirname(file), { recursive: true });
      const original = await fs.readFile(path.join(extensions, name, relative), "utf8");
      originals.set(relative, original);
      await fs.writeFile(file, original, { flag: "wx" });
    }
    const installed = await installVendorUi(vendor, root, path.join(scratch, "backups"));
    assert.equal(installed.changed, true);
    for (const relative of Object.keys(recipe.files)) {
      const source = await fs.readFile(path.join(root, relative), "utf8");
      const parsed = ts.createSourceFile(relative, source, ts.ScriptTarget.Latest, true, ts.ScriptKind.JS);
      assert.equal(parsed.parseDiagnostics.length, 0, relative + " must parse");
      assert.notEqual(uiHash(source), uiHash(originals.get(relative)));
    }
    if (vendor === "codex") {
      const manifest = JSON.parse(await fs.readFile(path.join(root, "package.json"), "utf8"));
      assert(manifest.contributes.menus["editor/title"].some((item) => item.command === "nexusHubSettings.openCodex"));
      assert(manifest.contributes.menus["editor/title"].some((item) => item.command === "chatgpt.openSidebar" && item.when.startsWith("!nexusHubSettings.enabled")));
    }
    assert.equal((await installVendorUi(vendor, root, path.join(scratch, "backups"))).changed, false);
    const relative = Object.keys(recipe.files)[0];
    const file = path.join(root, relative);
    const patched = await fs.readFile(file, "utf8");
    const customized = patched + "\n// independent change\n";
    await fs.writeFile(file, customized);
    await assert.rejects(installVendorUi(vendor, root, path.join(scratch, "backups")));
    await assert.rejects(restoreVendorUi(installed.receipt));
    assert.equal(await fs.readFile(file, "utf8"), customized);
    await fs.writeFile(file, patched);
    await restoreVendorUi(installed.receipt);
    for (const [relative, original] of originals) { assert.equal(await fs.readFile(path.join(root, relative), "utf8"), original); }
    // A redirected receipt cannot authorize a restore into another extension directory.
    const receipt = JSON.parse(await fs.readFile(installed.receipt, "utf8"));
    await fs.writeFile(installed.receipt, JSON.stringify({ ...receipt, root: path.dirname(root) }));
    await assert.rejects(restoreVendorUi(installed.receipt));
    report.push({ vendor, version: recipe.version, parse: true, idempotent: true, customizationPreserved: true, restoredExactly: true, redirectedReceiptRejected: true });
  }
  await fs.writeFile(path.join(scratch, "report.json"), JSON.stringify(report, null, 2) + "\n");
  console.log(JSON.stringify({ report: path.join(scratch, "report.json"), vendors: report.length }));
}
main().catch((error) => { console.error(error.message); process.exitCode = 1; });
