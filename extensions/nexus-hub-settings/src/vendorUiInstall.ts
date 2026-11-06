import * as fs from "node:fs/promises";
import * as path from "node:path";
import { randomUUID } from "node:crypto";
import { codexTabManifest, patchedUiSource, UI_RECIPES, uiHash, type UiVendor } from "./vendorUiPatch";
import { cursorProductManifest } from "./cursorEffort";

interface SavedFile { relative: string; original: string; written: string }
interface Receipt { schema: 1; vendor: UiVendor; version: string; root: string; files: SavedFile[] }
interface PlannedFile extends SavedFile { before: string; after: string; file: string }
export interface UiInstallResult { changed: boolean; receipt: string }

function validateManifest(vendor: UiVendor, text: string): void {
  const manifest = JSON.parse(text);
  if (vendor === "cursor") {
    if (manifest.name !== "Cursor" || manifest.version !== UI_RECIPES.cursor.version) { throw new Error("This Cursor version has not been qualified for live effort updates."); }
    return;
  }
  const identity = vendor === "claude" ? ["anthropic", "claude-code"] : ["openai", "chatgpt"];
  if (typeof manifest.publisher !== "string" || manifest.publisher.toLowerCase() !== identity[0] || manifest.name !== identity[1] || manifest.version !== UI_RECIPES[vendor].version) { throw new Error(`The ${vendor} live UI adapter has not been verified for this extension version.`); }
}
async function target(root: string, relative: string): Promise<string> {
  const file = path.join(root, relative);
  if ((await fs.lstat(file)).isSymbolicLink() || await fs.realpath(file) !== file) { throw new Error("A native UI target is redirected and was preserved."); }
  return file;
}

async function immutable(file: string, text: string): Promise<void> {
  try { await fs.writeFile(file, text, { flag: "wx" }); }
  catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "EEXIST") { throw error; }
    if (await fs.readFile(file, "utf8") !== text) { throw new Error("A native UI backup was changed and was preserved."); }
  }
}
async function replaceChecked(file: string, before: string, after: string): Promise<void> {
  const temporary = file + ".nexus-" + randomUUID();
  try {
    await fs.writeFile(temporary, after, { flag: "wx" });
    if (await fs.readFile(file, "utf8") !== before) { throw new Error("The native extension changed during installation and was preserved."); }
    await fs.rename(temporary, file);
  } finally { await fs.unlink(temporary).catch(() => undefined); }
}

/** Exact builds only. All targets are validated and backed up before the first replacement. */
export async function installVendorUi(vendor: UiVendor, extension: string, storage: string): Promise<UiInstallResult> {
  const root = await fs.realpath(extension);
  const manifestPath = path.join(root, "package.json");
  const manifestText = await fs.readFile(manifestPath, "utf8");
  const recipe = UI_RECIPES[vendor];
  validateManifest(vendor, manifestText);
  const directory = path.join(storage, vendor + "-" + uiHash(root).slice(0, 20));
  const backups = path.join(directory, "originals");
  const receiptPath = path.join(directory, "receipt.json");
  let saved: Receipt | undefined;
  let savedText: string | undefined;
  try { savedText = await fs.readFile(receiptPath, "utf8"); saved = JSON.parse(savedText) as Receipt; }
  catch (error) { if ((error as NodeJS.ErrnoException).code !== "ENOENT") { throw error; } }
  if (saved && (saved.schema !== 1 || saved.vendor !== vendor || saved.version !== recipe.version || saved.root !== root || !Array.isArray(saved.files))) { throw new Error("The native UI receipt is invalid and was preserved."); }
  const plan: PlannedFile[] = [];
  for (const [relative, originalHash] of Object.entries(recipe.files)) {
    const file = await target(root, relative);
    const current = await fs.readFile(file, "utf8");
    const original = uiHash(current) === originalHash ? current : await fs.readFile(path.join(backups, originalHash), "utf8");
    const after = patchedUiSource(vendor, relative, original);
    const prior = new Set(vendor === "cursor" ? ["e5f988de7ba83d5a5be0d5ec9885016e535ac93dad05f6928c27c4e3724e3e50"] : ["c00182705e37d9252b38c2242b14e302c676d69edf3d7ca3559b53281378d51d", "0fb29035fa289e055929949d32079e20393ac27b8048873482e40a4e85223b5a", "335b71af876a09a7ed7f204ebda3d796a028183aa7caeae159d4611fd167d4fe", "a4ab33595b77c8940a2bbda7e8b4038d78e790570ca93317d1f42ef63ffe978a", "e67e98679c28e285ec0cd80817d43588c155fdaa9ab7bc5100060d13e68e570e", "6a3b6783ed1d802f65deb540202c71cdb9b845379b9ace60be6d4a34ac6ea4c3", "eb20cbb9b45ca16410ed52debb01dd06067ecc787b6150c6d8b60e0a716eb1ba", "f465a08dbe889b5e27f93a868d2da4c5827416b8cd1f6e47f4dc91b7a4f7c006", "1af5b79c4df2a2e8d424b843004aedea2d640ecdad583ef31471b349137ca10c"]);
    if (current !== original && current !== after && !prior.has(uiHash(current))) { throw new Error("A customized native extension file was preserved."); }
    plan.push({ relative, file, before: current, after, original: originalHash, written: uiHash(after) });
  }
  if (vendor === "codex" || vendor === "cursor") {
    const relative = vendor === "cursor" ? "product.json" : "package.json";
    const extraPath = await target(root, relative);
    const before = await fs.readFile(extraPath, "utf8");
    const previous = saved?.files.find((file) => file.relative === relative);
    const knownWritten = previous?.written === uiHash(before);
    const originalHash = knownWritten ? previous!.original : uiHash(before);
    if (!/^[a-f0-9]{64}$/.test(originalHash)) { throw new Error("The native menu backup reference is invalid."); }
    const original = knownWritten ? await fs.readFile(path.join(backups, originalHash), "utf8") : before;
    if (uiHash(original) !== originalHash) { throw new Error("The native menu backup was changed and was preserved."); }
    const after = vendor === "cursor" ? cursorProductManifest(original, plan[0]!.written) : codexTabManifest(original);
    plan.push({ relative, file: extraPath, before, after, original: originalHash, written: uiHash(after) });
  }
  await fs.mkdir(backups, { recursive: true });
  for (const item of plan) {
    if (uiHash(item.before) === item.original) { await immutable(path.join(backups, item.original), item.before); }
  }
  const written: PlannedFile[] = [];
  try {
    for (const item of plan) {
      if (item.before === item.after) { continue; }
      await replaceChecked(item.file, item.before, item.after); written.push(item);
    }
    const receipt: Receipt = { schema: 1, vendor, version: recipe.version, root, files: plan.map(({ relative, original, written }) => ({ relative, original, written })) };
    const text = JSON.stringify(receipt, null, 2) + "\n";
    if (savedText !== undefined) { if (savedText !== text) { await replaceChecked(receiptPath, savedText, text); } }
    else { await immutable(receiptPath, text); }
  } catch (error) {
    for (const item of written.reverse()) {
      if (await fs.readFile(item.file, "utf8") === item.after) { await replaceChecked(item.file, item.after, item.before); }
    }
    throw error;
  }
  return { changed: written.length > 0, receipt: receiptPath };
}

/** Restore only the exact adapter output, preserving any independent vendor or user update. */
export async function restoreVendorUi(receiptPath: string): Promise<void> {
  const receipt = JSON.parse(await fs.readFile(receiptPath, "utf8")) as Receipt;
  if (receipt.schema !== 1 || !Object.hasOwn(UI_RECIPES, receipt.vendor) || !Array.isArray(receipt.files) || typeof receipt.root !== "string" || !path.isAbsolute(receipt.root)) { throw new Error("Invalid native UI receipt"); }
  const root = await fs.realpath(receipt.root);
  const directory = path.dirname(receiptPath);
  const recipe = UI_RECIPES[receipt.vendor];
  if (root !== receipt.root || receipt.version !== recipe.version || path.basename(directory) !== receipt.vendor + "-" + uiHash(root).slice(0, 20)) { throw new Error("Invalid native UI receipt location"); }
  validateManifest(receipt.vendor, await fs.readFile(path.join(root, "package.json"), "utf8"));
  const allowed = new Set([...Object.keys(recipe.files), ...(receipt.vendor === "codex" ? ["package.json"] : receipt.vendor === "cursor" ? ["product.json"] : [])]);
  if (receipt.files.length !== allowed.size || new Set(receipt.files.map((file) => file.relative)).size !== allowed.size) { throw new Error("Incomplete native UI receipt"); }
  const plan: { file: string; current: string; original: string }[] = [];
  for (const entry of receipt.files) {
    if (!allowed.has(entry.relative) || !/^[a-f0-9]{64}$/.test(entry.original) || !/^[a-f0-9]{64}$/.test(entry.written)) { throw new Error("Invalid native UI backup path"); }
    const file = await target(root, entry.relative);
    const original = await fs.readFile(path.join(directory, "originals", entry.original), "utf8");
    if (uiHash(original) !== entry.original) { throw new Error("A native UI backup was changed and was preserved."); }
    const core = receipt.files.find((file) => Object.hasOwn(recipe.files, file.relative));
    const after = entry.relative === "product.json" && receipt.vendor === "cursor" ? cursorProductManifest(original, core!.written) : entry.relative === "package.json" ? codexTabManifest(original) : patchedUiSource(receipt.vendor, entry.relative, original);
    if (uiHash(after) !== entry.written) { throw new Error("Invalid native UI adapter output"); }
    const current = await fs.readFile(file, "utf8");
    if (uiHash(current) !== entry.written) { throw new Error("A native extension update or customization was preserved."); }
    plan.push({ file, current, original });
  }
  const restored: typeof plan = [];
  try {
    for (const entry of plan) { await replaceChecked(entry.file, entry.current, entry.original); restored.push(entry); }
  } catch (error) {
    for (const entry of restored.reverse()) {
      if (await fs.readFile(entry.file, "utf8") === entry.original) { await replaceChecked(entry.file, entry.original, entry.current); }
    }
    throw error;
  }
}
