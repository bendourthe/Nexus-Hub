/* Exercise install and restore on disposable copies of the exact installed Cursor build. */
const fs = require("node:fs/promises");
const path = require("node:path");
const assert = require("node:assert/strict");
const { execFileSync } = require("node:child_process");
const { installVendorUi, restoreVendorUi } = require("../out/vendorUiInstall");
const { CURSOR_WORKBENCH_PATH } = require("../out/cursorEffort");
const { uiHash } = require("../out/vendorUiPatch");

async function main() {
  const [source, output] = process.argv.slice(2);
  if (!source || !output) throw Error("Usage: node scripts/verify-cursor-ui-adapter.js CURSOR_APP_ROOT OUTPUT_DIRECTORY");
  await fs.mkdir(output, {recursive: true});
  const scratch = await fs.mkdtemp(path.join(output, "cursor-ui-"));
  const root = path.join(scratch, "app"), storage = path.join(scratch, "backups");
  const originals = new Map();
  for (const relative of ["package.json", "product.json", CURSOR_WORKBENCH_PATH]) {
    const text = await fs.readFile(path.join(source, relative), "utf8");
    originals.set(relative, text);
    const destination = path.join(root, relative);
    await fs.mkdir(path.dirname(destination), {recursive: true});
    await fs.writeFile(destination, text, {flag: "wx"});
  }
  const installed = await installVendorUi("cursor", root, storage);
  assert.equal(installed.changed, true);
  const core = path.join(root, CURSOR_WORKBENCH_PATH);
  execFileSync(process.execPath, ["--check", core], {windowsHide: true, stdio: "pipe"});
  const patched = await fs.readFile(core, "utf8");
  const product = JSON.parse(await fs.readFile(path.join(root, "product.json"), "utf8"));
  assert.equal(product.checksums[CURSOR_WORKBENCH_PATH.slice(4)], Buffer.from(uiHash(patched), "hex").toString("base64").replace(/=+$/, ""));
  assert.equal(Object.keys(product.checksums).length, Object.keys(JSON.parse(originals.get("product.json")).checksums).length);
  assert.equal((await installVendorUi("cursor", root, storage)).changed, false);
  await fs.writeFile(core, patched + "\n// independent edit\n");
  await assert.rejects(installVendorUi("cursor", root, storage));
  await assert.rejects(restoreVendorUi(installed.receipt));
  assert.equal(await fs.readFile(core, "utf8"), patched + "\n// independent edit\n");
  await fs.writeFile(core, patched);
  await restoreVendorUi(installed.receipt);
  for (const [relative, original] of originals) assert.equal(await fs.readFile(path.join(root, relative), "utf8"), original);
  const unknown = JSON.parse(originals.get("package.json")); unknown.version = "unqualified";
  await fs.writeFile(path.join(root, "package.json"), JSON.stringify(unknown));
  await assert.rejects(installVendorUi("cursor", root, storage));
  assert.equal(await fs.readFile(core, "utf8"), originals.get(CURSOR_WORKBENCH_PATH));
  const report = {syntax: true, integrityEntriesRetained: true, idempotent: true, independentEditsPreserved: true, restoredExactly: true, unknownBuildPreserved: true};
  await fs.writeFile(path.join(scratch, "report.json"), JSON.stringify(report, null, 2) + "\n");
  console.log(JSON.stringify({report: path.join(scratch, "report.json"), ...report}));
}
main().catch(error => {console.error(error.message); process.exitCode = 1;});
