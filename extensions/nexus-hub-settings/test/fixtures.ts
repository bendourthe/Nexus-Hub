import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import type { EditorLayers } from "../src/editorWrites";
import type { ExplainData, ShowReport } from "../src/types";

/**
 * Engine output captured with the real `report` and `explain_data` code on a scratch home
 * (see the phase 4 history file for how it was generated), so panel tests run on real shapes.
 */
const dir = path.join(path.dirname(fileURLToPath(import.meta.url)), "fixtures");

function load<T>(name: string): T {
  return JSON.parse(fs.readFileSync(path.join(dir, name), "utf8")) as T;
}

export const CONTROLS = ["effort", "model", "posture", "attribution", "git_guardrails"] as const;

export function showReport(): ShowReport {
  return load<ShowReport>("show.json");
}

export function explains(): Record<string, ExplainData> {
  return Object.fromEntries(CONTROLS.map((id) => [id, load<ExplainData>(`explain-${id}.json`)]));
}

export function layers(key: string, over: Partial<EditorLayers> = {}): EditorLayers {
  return { key, registered: true, defaultValue: false, globalValue: undefined, workspaceValue: undefined, workspaceFolderValue: undefined, ...over };
}

export const EDITOR_REASON = "read from the editor: the CLI cannot read VS Code settings, so the panel supplies them";

/**
 * A variant where the VS Code Copilot Chat auto-approve write is admitted (as it would be after a
 * manual proof), so the editor path can be exercised. The engine then reports that row as `cannot-detect`.
 */
export function withEditorWriteAdmitted(): { report: ShowReport; explains: Record<string, ExplainData> } {
  const report = showReport();
  const all = explains();
  const write = all.posture!.writes.find((w) => w.id === "vscode-copilot.auto_approve")!;
  write.admission = "admitted";
  delete write.not_settable_reason;
  const record = report.records.find((r) => r.control === "posture" && r.tool === "vscode-copilot")!;
  record.state = "cannot-detect";
  record.detail = EDITOR_REASON;
  return { report, explains: all };
}
