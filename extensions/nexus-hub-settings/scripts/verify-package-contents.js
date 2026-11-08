/**
 * Assert the packaged extension ships every runtime file and no developer or credential artifact.
 * Run after `npm run compile`: it asks `vsce ls` what would be packaged.
 */
const { execFileSync } = require("node:child_process");
const { existsSync, readdirSync } = require("node:fs");
const path = require("node:path");

const ROOT = path.join(__dirname, "..");

const STATIC_REQUIRED = [
  "package.json",
  "README.md",
  "LICENSE",
  "icon.png",
  "media/panel.js",
  "media/panel.css",
  "media/logo.png",
  "media/icon.svg",
  "fonts/nexus-hub-icons.woff2"
];

const FORBIDDEN = [
  /^coverage\//,
  /^node_modules\//,
  /^src\//,
  /^test\//,
  /^scripts\//,
  /\.vsix$/,
  /\.map$/,
  /(^|\/)\.env(?:\.|$)/,
  /(^|\/)\.npmrc$/i,
  /(^|\/)auth\.json$/i,
  /(^|\/)secrets?[^/]*$/i,
  /(^|\/)credentials?[^/]*$/i,
  /(^|\/)tokens?\.json$/i,
  /\.(pem|key|p12|pfx)$/i
];

function compiledModules(outDir = path.join(ROOT, "out")) {
  if (!existsSync(outDir)) {
    throw new Error("out/ is missing; run npm run compile first");
  }
  return readdirSync(outDir)
    .filter((name) => name.endsWith(".js"))
    .map((name) => `out/${name}`);
}

function listPackaged() {
  const vsce = path.join(ROOT, "node_modules", "@vscode", "vsce", "vsce");
  const stdout = execFileSync(process.execPath, [vsce, "ls", "--no-dependencies"], { cwd: ROOT, encoding: "utf8", windowsHide: true });
  return stdout
    .split(/\r?\n/u)
    .map((line) => line.trim().replace(/\\/g, "/"))
    .filter((line) => line.length > 0);
}

function collectErrors(files, required) {
  const errors = [];
  for (const file of required) {
    if (!files.includes(file)) {
      errors.push(`missing required packaged file: ${file}`);
    }
  }
  for (const file of files) {
    const hit = FORBIDDEN.find((pattern) => pattern.test(file));
    if (hit !== undefined) {
      errors.push(`forbidden file in package: ${file} (matched ${hit})`);
    }
  }
  return errors;
}

function main() {
  const required = [...new Set([...STATIC_REQUIRED, ...compiledModules()])];
  const files = listPackaged();
  const errors = collectErrors(files, required);
  if (errors.length > 0) {
    console.error("Package content verification failed:");
    for (const error of errors) {
      console.error(`  - ${error}`);
    }
    process.exit(1);
  }
  console.log(`Package content verification passed (${files.length} files; ${required.length} required).`);
}

if (require.main === module) {
  try {
    main();
  } catch (error) {
    console.error(`Package content verification failed: ${error instanceof Error ? error.message : String(error)}`);
    process.exit(1);
  }
}

module.exports = { STATIC_REQUIRED, FORBIDDEN, collectErrors, compiledModules };
