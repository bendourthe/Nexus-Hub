/**
 * Assert the VSIX ships every runtime asset and no developer or credential artifact.
 */
const { execFileSync } = require("node:child_process");
const {
  existsSync,
  readFileSync,
  statSync
} = require("node:fs");
const path = require("node:path");

const EXTENSION_ROOT = path.join(__dirname, "..");

const REQUIRED = [
  "package.json",
  "README.md",
  "LICENSE",
  "THIRD_PARTY_NOTICES.md",
  "icon.png",
  "out/extension.js",
  "fonts/cursor-icons.woff2",
  "icons/cursor.svg",
  "icons/cursor-ai-48.png",
  "icons/warning.svg"
];

const FORBIDDEN_PATTERNS = [
  /^coverage\//,
  /^node_modules\//,
  /^src\//,
  /^test\//,
  /^scripts\//,
  /\.vsix$/,
  /\.map$/,
  /(^|\/)\.env(?:\.|$)/,
  /(^|\/)auth\.json$/i,
  /(^|\/)secrets?[^/]*$/i,
  /\.pem$/i,
  /\.key$/i
];

function listPackagedFiles() {
  const vsce = path.join(EXTENSION_ROOT, "node_modules", "@vscode", "vsce", "vsce");
  const stdout = execFileSync(
    process.execPath,
    [vsce, "ls", "--no-dependencies"],
    { cwd: EXTENSION_ROOT, encoding: "utf8" }
  );
  return stdout
    .split(/\r?\n/u)
    .map((line) => line.trim().replace(/\\/g, "/"))
    .filter((line) => line.length > 0);
}

function collectErrors(files, requiredFiles = REQUIRED) {
  const errors = [];

  for (const required of requiredFiles) {
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

function discoverRuntimeFiles(entryPath, runtimeRoot) {
  const root = path.resolve(runtimeRoot);
  const visited = new Set();

  function visit(file) {
    const resolved = path.resolve(file);
    if (
      resolved !== root &&
      !resolved.startsWith(`${root}${path.sep}`)
    ) {
      throw new Error(`runtime import escapes output directory: ${resolved}`);
    }
    if (visited.has(resolved)) {
      return;
    }
    if (!existsSync(resolved) || !statSync(resolved).isFile()) {
      throw new Error(`runtime module is missing: ${resolved}`);
    }
    visited.add(resolved);

    const source = readFileSync(resolved, "utf8");
    const imports = source.matchAll(
      /\brequire\(\s*["'](\.[^"']+)["']\s*\)/gu
    );
    for (const match of imports) {
      const specifier = match[1];
      if (specifier === undefined) {
        continue;
      }
      const base = path.resolve(path.dirname(resolved), specifier);
      const candidates = path.extname(base)
        ? [base]
        : [`${base}.js`, path.join(base, "index.js")];
      const dependency = candidates.find(
        (candidate) => existsSync(candidate) && statSync(candidate).isFile()
      );
      if (dependency === undefined) {
        throw new Error(
          `runtime import ${specifier} from ${resolved} does not resolve`
        );
      }
      visit(dependency);
    }
  }

  visit(entryPath);
  return [...visited]
    .map((file) => path.relative(root, file).replace(/\\/gu, "/"))
    .sort();
}

function listArchiveEntries(vsixPath) {
  const archive = readFileSync(vsixPath);
  const endSignature = 0x06054b50;
  const centralSignature = 0x02014b50;
  const minimumOffset = Math.max(0, archive.length - 65_557);
  let endOffset = -1;
  for (let offset = archive.length - 22; offset >= minimumOffset; offset -= 1) {
    if (archive.readUInt32LE(offset) === endSignature) {
      endOffset = offset;
      break;
    }
  }
  if (endOffset < 0) {
    throw new Error("VSIX end-of-central-directory record is missing");
  }

  const entryCount = archive.readUInt16LE(endOffset + 10);
  const centralOffset = archive.readUInt32LE(endOffset + 16);
  if (entryCount === 0xffff || centralOffset === 0xffffffff) {
    throw new Error("ZIP64 VSIX archives are not supported");
  }

  const entries = [];
  let offset = centralOffset;
  for (let index = 0; index < entryCount; index += 1) {
    if (
      offset + 46 > archive.length ||
      archive.readUInt32LE(offset) !== centralSignature
    ) {
      throw new Error(`invalid VSIX central-directory entry ${index + 1}`);
    }
    const nameLength = archive.readUInt16LE(offset + 28);
    const extraLength = archive.readUInt16LE(offset + 30);
    const commentLength = archive.readUInt16LE(offset + 32);
    const nameStart = offset + 46;
    const nameEnd = nameStart + nameLength;
    if (nameEnd > archive.length) {
      throw new Error(`truncated VSIX entry name at index ${index + 1}`);
    }
    entries.push(
      archive.subarray(nameStart, nameEnd).toString("utf8").replace(/\\/gu, "/")
    );
    offset = nameEnd + extraLength + commentLength;
  }
  return entries;
}

function packageFilesFromArchiveEntries(entries) {
  return entries
    .filter((entry) => entry.startsWith("extension/") && !entry.endsWith("/"))
    .map((entry) => {
      const file = entry.slice("extension/".length);
      if (file.toLowerCase() === "readme.md") {
        return "README.md";
      }
      return file === "LICENSE.txt" ? "LICENSE" : file;
    })
    .sort();
}

function compareListings(vsceFiles, archiveFiles) {
  const errors = [];
  const listed = new Set(vsceFiles);
  const archived = new Set(archiveFiles);
  for (const file of listed) {
    if (!archived.has(file)) {
      errors.push(`vsce listed file missing from VSIX archive: ${file}`);
    }
  }
  for (const file of archived) {
    if (!listed.has(file)) {
      errors.push(`VSIX archive file missing from vsce listing: ${file}`);
    }
  }
  return errors;
}

function main() {
  const runtimeFiles = discoverRuntimeFiles(
    path.join(EXTENSION_ROOT, "out", "extension.js"),
    path.join(EXTENSION_ROOT, "out")
  ).map((file) => `out/${file}`);
  const requiredFiles = [...new Set([...REQUIRED, ...runtimeFiles])];
  const listedFiles = listPackagedFiles();
  const manifest = JSON.parse(
    readFileSync(path.join(EXTENSION_ROOT, "package.json"), "utf8")
  );
  const vsixPath = path.join(
    EXTENSION_ROOT,
    `${manifest.name}-${manifest.version}.vsix`
  );
  if (!existsSync(vsixPath)) {
    throw new Error(
      `generated VSIX is missing: ${path.basename(vsixPath)}; run npm run package first`
    );
  }
  const archiveFiles = packageFilesFromArchiveEntries(
    listArchiveEntries(vsixPath)
  );
  const errors = [
    ...collectErrors(listedFiles, requiredFiles),
    ...collectErrors(archiveFiles, requiredFiles),
    ...compareListings(listedFiles, archiveFiles)
  ];

  if (errors.length > 0) {
    console.error("VSIX content verification failed:");
    for (const error of errors) {
      console.error(`  - ${error}`);
    }
    process.exit(1);
  }

  console.log(
    `VSIX content verification passed (${archiveFiles.length} archived files; ${runtimeFiles.length} runtime modules).`
  );
}

if (require.main === module) {
  try {
    main();
  } catch (error) {
    console.error(
      `VSIX content verification failed: ${
        error instanceof Error ? error.message : String(error)
      }`
    );
    process.exit(1);
  }
}

module.exports = {
  REQUIRED,
  FORBIDDEN_PATTERNS,
  collectErrors,
  compareListings,
  discoverRuntimeFiles,
  listArchiveEntries,
  listPackagedFiles,
  packageFilesFromArchiveEntries
};
