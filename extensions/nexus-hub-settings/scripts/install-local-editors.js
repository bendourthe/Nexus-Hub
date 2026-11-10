/** Install one reviewed Settings VSIX in each locally available Windows editor. */
const fs = require("node:fs");
const path = require("node:path");
const { execFileSync } = require("node:child_process");

const ID = "nexus-hub.nexus-hub-settings";

function discoverEditors(env = process.env) {
  const local = env.LOCALAPPDATA;
  if (!local) { return []; }
  const definitions = [
    ["VS Code", "Microsoft VS Code", "Code.exe"],
    ["Cursor", "cursor", "Cursor.exe"],
    ["Antigravity", "Antigravity IDE", "Antigravity IDE.exe"],
  ];
  const editors = [];
  for (const [name, folder, binary] of definitions) {
    const root = path.join(local, "Programs", folder);
    const exe = path.join(root, binary);
    if (!fs.existsSync(exe)) { continue; }
    const roots = [root, ...fs.readdirSync(root, { withFileTypes: true }).filter((entry) => entry.isDirectory()).map((entry) => path.join(root, entry.name))];
    const cli = roots.map((dir) => path.join(dir, "resources", "app", "out", "cli.js")).find((file) => fs.existsSync(file));
    if (!cli) { throw new Error(`${name} is installed but its extension CLI was not found`); }
    editors.push({ name, exe, cli });
  }
  return editors;
}

function install(vsix, editors, run = execFileSync) {
  const env = Object.fromEntries(Object.entries(process.env).filter(([key]) => !/^VSCODE|^ELECTRON_RUN_AS_NODE$/i.test(key)));
  env.ELECTRON_RUN_AS_NODE = "1";
  return editors.map((editor) => {
    const options = { windowsHide: true, encoding: "utf8", timeout: 120000, maxBuffer: 8 * 1024 * 1024, env };
    run(editor.exe, [editor.cli, "--install-extension", vsix, "--force"], options);
    const listed = run(editor.exe, [editor.cli, "--list-extensions", "--show-versions"], options);
    const registration = listed.split(/\r?\n/).find((line) => line.toLowerCase().startsWith(`${ID}@`));
    if (!registration) { throw new Error(`${editor.name} did not report the Settings installation`); }
    return { editor: editor.name, registration };
  });
}

function main() {
  const [vsixArg, reportArg] = process.argv.slice(2);
  if (!vsixArg || !reportArg) { throw new Error("usage: node scripts/install-local-editors.js <vsix> <new-report.json>"); }
  const vsix = path.resolve(vsixArg);
  const report = path.resolve(reportArg);
  if (!fs.existsSync(vsix)) { throw new Error("VSIX does not exist"); }
  const descriptor = reserveReport(report);
  try {
    const editors = discoverEditors();
    if (!editors.length) { throw new Error("No supported locally installed editor found"); }
    const results = install(vsix, editors);
    const version = require(path.join(__dirname, "..", "package.json")).version;
    if (results.some((entry) => entry.registration.toLowerCase() !== `${ID}@${version}`)) { throw new Error("An editor reported a different Settings version"); }
    fs.writeFileSync(descriptor, JSON.stringify({ vsix, version, results }, null, 2));
    console.log(JSON.stringify({ version, results, report }));
  } catch (error) {
    fs.rmSync(report, { force: true });
    throw error;
  } finally { fs.closeSync(descriptor); }
}

/** Creates the report exclusively before any install runs, so an existing report is never overwritten. */
function reserveReport(report) {
  fs.mkdirSync(path.dirname(report), { recursive: true });
  try { return fs.openSync(report, "wx"); }
  catch (error) { throw error.code === "EEXIST" ? new Error("Use a new delivery-report path") : error; }
}

module.exports = { discoverEditors, install };
if (require.main === module) { try { main(); } catch (error) { console.error(error.message); process.exitCode = 1; } }
