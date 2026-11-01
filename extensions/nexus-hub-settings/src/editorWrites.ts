import * as fs from "node:fs";
import * as path from "node:path";
import { isDeepStrictEqual } from "node:util";
import * as vscode from "vscode";
import { EditorRestore, EditorWrite, PriorState } from "./types";

/**
 * VS Code-host writes. VS Code `settings.json` is JSON with comments and is stored
 * per profile, so these keys go through the configuration API (never a file edit),
 * always to the user (Global) layer. The engine plans them (`editor_writes`) and
 * keeps the record; this module applies them, reports each previous value back,
 * and applies the engine's `editor_restores` on reset.
 */

export interface EditorLayers {
  key: string;
  /** False when no installed extension contributes the key: `update()` would throw. */
  registered: boolean;
  defaultValue: unknown;
  globalValue: unknown;
  workspaceValue: unknown;
  workspaceFolderValue: unknown;
}

export function inspectKey(key: string): EditorLayers {
  const info = vscode.workspace.getConfiguration().inspect(key);
  return {
    key,
    registered: info?.defaultValue !== undefined,
    defaultValue: info?.defaultValue,
    globalValue: info?.globalValue,
    workspaceValue: info?.workspaceValue,
    workspaceFolderValue: info?.workspaceFolderValue,
  };
}

export interface Skipped {
  write: EditorWrite;
  reason: string;
}

export type Precheck =
  | { ok: true; apply: EditorWrite[]; skipped: Skipped[] }
  | { ok: false; key: string; message: string };

/**
 * Check every planned key before the CLI writes anything. A workspace (or folder)
 * value beats the user value, so one aborts the whole change. A key that no
 * installed extension contributes is skipped, because `update()` throws for it.
 */
export function precheckEditorWrites(writes: EditorWrite[], inspect: (key: string) => EditorLayers = inspectKey): Precheck {
  const apply: EditorWrite[] = [];
  const skipped: Skipped[] = [];
  for (const write of writes) {
    const layers = inspect(write.key);
    if (!layers.registered) {
      skipped.push({ write, reason: `${write.key} is not registered in this VS Code, so the extension that provides it is not installed or is disabled` });
      continue;
    }
    if (layers.workspaceFolderValue !== undefined || layers.workspaceValue !== undefined) {
      const where = layers.workspaceFolderValue !== undefined ? "the workspace folder settings" : "the workspace settings";
      return {
        ok: false,
        key: write.key,
        message: `overridden-by workspace setting: ${write.key} is set in ${where}, and that value beats your user value. Nothing was changed. Remove it from .vscode/settings.json (or the .code-workspace file), then try again.`,
      };
    }
    apply.push(write);
  }
  return { ok: true, apply, skipped };
}

export interface AppliedWrite {
  write: EditorWrite;
  previous: PriorState;
}

export class EditorWriteError extends Error {
  constructor(
    message: string,
    /** The writes that were applied AND recorded before the failure, for the caller's rollback. */
    readonly applied: AppliedWrite[],
  ) {
    super(message);
    this.name = "EditorWriteError";
  }
}

function priorState(layers: EditorLayers): PriorState {
  return layers.globalValue === undefined ? { present: false } : { present: true, value: layers.globalValue };
}

async function setGlobal(key: string, value: unknown): Promise<void> {
  await vscode.workspace.getConfiguration().update(key, value, vscode.ConfigurationTarget.Global);
}

function describe(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

/**
 * Apply each write at the Global layer, then report its previous value through
 * `record`. A failure stops here: a key whose recording failed is put back at once,
 * and the thrown error lists what was applied and recorded so the caller can reset.
 */
export async function applyEditorWrites(
  writes: EditorWrite[],
  record: (write: EditorWrite, previous: PriorState) => Promise<void>,
  inspect: (key: string) => EditorLayers = inspectKey,
): Promise<AppliedWrite[]> {
  const applied: AppliedWrite[] = [];
  for (const write of writes) {
    const previous = priorState(inspect(write.key));
    try {
      await setGlobal(write.key, write.value);
    } catch (error) {
      throw new EditorWriteError(`VS Code refused to save ${write.key}: ${describe(error)}`, applied);
    }
    try {
      await record(write, previous);
    } catch (error) {
      await setGlobal(write.key, previous.present ? previous.value : undefined).catch(() => undefined);
      throw new EditorWriteError(`${write.key} was saved but could not be recorded, so it was put back: ${describe(error)}`, applied);
    }
    applied.push({ write, previous });
  }
  return applied;
}

export interface RestoreReport {
  key: string;
  status: "restored" | "left" | "skipped";
  detail: string;
}

/**
 * Apply the engine's `editor_restores`. A key is restored only while it still holds
 * what Nexus-Hub wrote, and only in the profile that wrote it; otherwise it is left as
 * the user has it and the report says why.
 */
export async function restoreEditorWrites(
  restores: EditorRestore[],
  profile: string,
  inspect: (key: string) => EditorLayers = inspectKey,
): Promise<RestoreReport[]> {
  const reports: RestoreReport[] = [];
  for (const entry of restores) {
    if (entry.profile && entry.profile !== profile) {
      reports.push({ key: entry.key, status: "skipped", detail: `${entry.key} was written in the VS Code profile "${entry.profile}"; switch to it and reset again` });
      continue;
    }
    const layers = inspect(entry.key);
    if (!layers.registered) {
      reports.push({ key: entry.key, status: "skipped", detail: `${entry.key} is not registered in this VS Code, so it was not restored` });
      continue;
    }
    const unchanged = entry.was.present ? isDeepStrictEqual(layers.globalValue, entry.was.value) : layers.globalValue === undefined;
    if (!unchanged) {
      reports.push({ key: entry.key, status: "left", detail: `${entry.key} changed after Nexus-Hub wrote it, so it was left as you have it` });
      continue;
    }
    try {
      await setGlobal(entry.key, entry.restore.present ? entry.restore.value : undefined);
      reports.push({ key: entry.key, status: "restored", detail: `${entry.key} restored` });
    } catch (error) {
      reports.push({ key: entry.key, status: "skipped", detail: `VS Code refused to restore ${entry.key}: ${describe(error)}` });
    }
  }
  return reports;
}

/**
 * The active VS Code profile name. The API does not expose it, so it is derived from
 * the extension's global-storage path (`.../User/profiles/<id>/globalStorage/...` for a
 * named profile) and the profile list VS Code keeps in `storage.json`.
 */
export function profileNameFromStorage(globalStoragePath: string, readFile: (file: string) => string = (f) => fs.readFileSync(f, "utf8")): string {
  const match = /^(.*)[\\/]User[\\/]profiles[\\/]([^\\/]+)[\\/]globalStorage(?:[\\/]|$)/.exec(globalStoragePath);
  if (!match || !match[1] || !match[2]) {
    return "Default";
  }
  const id = match[2];
  try {
    const stored = JSON.parse(readFile(path.join(match[1], "User", "globalStorage", "storage.json"))) as {
      userDataProfiles?: { location?: string; name?: string }[];
    };
    const named = stored.userDataProfiles?.find((profile) => profile.location === id)?.name;
    return named ? asciiOnly(named) : id;
  } catch {
    return id;
  }
}

/** The engine keeps only printable ASCII profile names (at most 100 characters). */
export function asciiOnly(text: string): string {
  return [...text].map((char) => (char >= " " && char <= "~" ? char : "?")).join("").slice(0, 100);
}
