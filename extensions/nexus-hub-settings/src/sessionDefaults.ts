import * as fs from "node:fs";
import * as path from "node:path";
import { randomUUID } from "node:crypto";
import { readRegularFileSync } from "./safeRead";

export interface SessionDefaults { fastMode: boolean | null; fastRevision: string; codexTabs: boolean }
export const SESSION_DEFAULTS_FILE = "session-defaults.json";

function read(file: string): Record<string, unknown> {
  try {
    const value: unknown = JSON.parse(readRegularFileSync(file, {maxBytes: 16384, refuseSymlink: true, refusal: "The session defaults file is redirected or too large and was preserved."}));
    if (!value || typeof value !== "object" || Array.isArray(value)) { throw new Error("Session defaults must be a JSON object."); }
    return value as Record<string, unknown>;
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") { return {}; }
    throw error;
  }
}

export function readSessionDefaults(file: string): SessionDefaults {
  const data = read(file);
  return { fastMode: typeof data.fastMode === "boolean" ? data.fastMode : null, fastRevision: typeof data.fastRevision === "string" && data.fastRevision.length <= 512 ? data.fastRevision : "", codexTabs: typeof data.codexTabs === "boolean" ? data.codexTabs : true };
}

/** A short exclusive write preserves unrelated keys and prevents two editors losing each other's changes. */
export function writeSessionDefault(file: string, key: "fastMode" | "codexTabs" | "applyAll", value?: boolean): void {
  if (!["fastMode", "codexTabs", "applyAll"].includes(key) || key !== "applyAll" && typeof value !== "boolean") { throw new Error("Invalid session default"); }
  fs.mkdirSync(path.dirname(file), {recursive: true});
  const lock = file + ".lock", temporary = file + "." + randomUUID();
  let descriptor: number | undefined;
  try {
    descriptor = fs.openSync(lock, "wx");
    const data = read(file);
    if (key === "applyAll") { if (typeof data.fastMode !== "boolean") { return; } data.fastRevision = randomUUID(); }
    else {
      if (data[key] === value) { return; }
      data[key] = value;
      if (key === "fastMode") { data.fastRevision = randomUUID(); }
    }
    fs.writeFileSync(temporary, JSON.stringify(data, null, 2) + "\n", {flag: "wx"});
    fs.renameSync(temporary, file);
  } finally {
    try { fs.unlinkSync(temporary); } catch { /* No staged write remains. */ }
    if (descriptor !== undefined) { fs.closeSync(descriptor); fs.unlinkSync(lock); }
  }
}
