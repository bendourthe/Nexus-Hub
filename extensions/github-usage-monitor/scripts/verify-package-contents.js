/**
 * Assert the VSIX ships exactly what it should and nothing it should not.
 *
 * `vsce ls` reports the file list vsce would package, after applying
 * .vscodeignore. Running it as a gate turns two silent packaging failures into
 * build failures: a missing runtime asset (the extension installs but renders a
 * blank glyph or an unbranded alert panel), and an accidentally-included
 * artifact (a coverage report, a nested VSIX, a credential file a contributor
 * left in the working tree).
 */
const { execFileSync } = require("node:child_process");
const path = require("node:path");

const EXTENSION_ROOT = path.join(__dirname, "..");

// Runtime assets. Each is loaded by the installed extension, so its absence is
// a user-visible defect rather than a packaging nicety.
const REQUIRED = [
  "package.json",
  "README.md",
  "LICENSE",
  "icon.png",
  "out/extension.js",
  "fonts/github-icons.woff2",
  "icons/github.svg",
  "icons/github-gradient.png",
  "icons/warning.svg"
];

// Build-time and developer-only artifacts. Anything matching ships bytes that
// the extension never reads, and the credential patterns would ship a secret.
const FORBIDDEN_PATTERNS = [
  /^coverage\//,
  /^node_modules\//,
  /^src\//,
  /^test\//,
  /^scripts\//,
  /\.vsix$/,
  /\.map$/,
  /(^|\/)\.env/,
  /(^|\/)auth\.json$/,
  /(^|\/)secrets?[^/]*$/i,
  /\.pem$/,
  /\.key$/
];

function listPackagedFiles() {
  // Invoke vsce's JS entry point directly rather than through npx: Node refuses
  // to spawn a .cmd shim without a shell on Windows, and going through a shell
  // would make this gate depend on the host's quoting rules.
  const vsce = path.join(EXTENSION_ROOT, "node_modules", "@vscode", "vsce", "vsce");
  const stdout = execFileSync(
    process.execPath,
    [vsce, "ls", "--no-dependencies"],
    { cwd: EXTENSION_ROOT, encoding: "utf8" }
  );
  return stdout
    .split(/\r?\n/)
    .map((line) => line.trim().replace(/\\/g, "/"))
    .filter((line) => line.length > 0);
}

function collectErrors(files) {
  const errors = [];

  for (const required of REQUIRED) {
    if (!files.includes(required)) {
      errors.push(`missing required packaged file: ${required}`);
    }
  }

  for (const file of files) {
    const pattern = FORBIDDEN_PATTERNS.find((candidate) => candidate.test(file));
    if (pattern !== undefined) {
      errors.push(`forbidden file in package: ${file} (matched ${pattern})`);
    }
  }

  return errors;
}

function main() {
  const files = listPackagedFiles();
  const errors = collectErrors(files);

  if (errors.length > 0) {
    console.error("VSIX content verification failed:");
    for (const error of errors) {
      console.error(`  - ${error}`);
    }
    process.exit(1);
  }

  console.log(`VSIX content verification passed (${files.length} files).`);
}

if (require.main === module) {
  main();
}

module.exports = { REQUIRED, FORBIDDEN_PATTERNS, collectErrors, listPackagedFiles };
