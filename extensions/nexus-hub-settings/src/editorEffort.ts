import { isDeepStrictEqual } from "node:util";
import * as vscode from "vscode";
import type { ShowRecord } from "./types";

const ENVIRONMENT_KEY = "claudeCode.environmentVariables";
const EFFORT_VARIABLE = "CLAUDE_CODE_EFFORT_LEVEL";
const CLAUDE_EFFORTS = new Set(["low", "medium", "high", "xhigh", "max"]);

export interface EditorEffortResult {
  changed: string[];
  issues: string[];
}

interface EffortEntry {
  index: number;
  value: unknown;
}

function effortEntries(value: unknown[]): EffortEntry[] {
  return value.flatMap((entry, index) => {
    if (!entry || typeof entry !== "object" || Array.isArray(entry)) { return []; }
    const variable = entry as Record<string, unknown>;
    return variable.name === EFFORT_VARIABLE ? [{ index, value: variable.value }] : [];
  });
}

/**
 * Reconcile existing Claude editor launch overrides with the engine's native
 * mapping. Other environment entries, including credentials, are never backed up
 * or changed. The engine owns the shared settings.json effort variable, so an
 * absent editor override does not need a new array here.
 *
 * Copilot's public model API omits the per-model effort schema. A native model
 * configuration file exists, but guessing its supported values would make the
 * same invalid-value bug appear under a different key. Report that gap instead.
 */
export async function syncEditorEffort(
  records: ShowRecord[],
  saveBackup: (key: string, value: unknown) => Promise<void>,
): Promise<EditorEffortResult> {
  const result: EditorEffortResult = { changed: [], issues: [] };
  if (!vscode.workspace.isTrusted) {
    return result;
  }
  const claude = records.find((record) => record.control === "effort" && record.tool === "claude" && record.mapped_effort);
  if (claude?.mapped_effort) {
    const native = claude.mapped_effort;
    if (!CLAUDE_EFFORTS.has(native)) {
      result.issues.push("Claude Code effort mapping is not valid; editor launch settings were preserved.");
    } else {
      const resources = (vscode.workspace.workspaceFolders ?? []).map((folder) => folder.uri).filter((uri) => uri.scheme === "file");
      const resource = resources[0];
      const config = vscode.workspace.getConfiguration(undefined, resource);
      const initial = config.inspect<unknown>(ENVIRONMENT_KEY);
      if (initial?.defaultValue !== undefined) {
        const location = vscode.workspace.workspaceFile?.toString() ?? resource?.toString() ?? "empty-window";
        const layers = [
          { label: "user", target: vscode.ConfigurationTarget.Global, value: initial.globalValue, key: "globalValue" as const, location: "profile", config },
          { label: "workspace", target: vscode.ConfigurationTarget.Workspace, value: initial.workspaceValue, key: "workspaceValue" as const, location, config },
          ...resources.map((uri) => {
            const folderConfig = vscode.workspace.getConfiguration(undefined, uri);
            return { label: "folder", target: vscode.ConfigurationTarget.WorkspaceFolder, value: folderConfig.inspect<unknown>(ENVIRONMENT_KEY)?.workspaceFolderValue, key: "workspaceFolderValue" as const, location: uri.toString(), config: folderConfig };
          }),
        ];
        for (const layer of layers) {
          if (layer.value === undefined) { continue; }
          if (!Array.isArray(layer.value)) {
            result.issues.push(`Claude Code ${layer.label} environment settings are malformed and were preserved.`);
            continue;
          }
          const entries = effortEntries(layer.value);
          if (!entries.length || entries.every((entry) => entry.value === native)) { continue; }
          if (entries.some((entry) => typeof entry.value !== "string")) {
            result.issues.push(`Claude Code ${layer.label} effort override is malformed and was preserved.`);
            continue;
          }
          const updated = layer.value.map((entry, index) => entries.some((effort) => effort.index === index)
            ? { ...entry as Record<string, unknown>, value: native }
            : entry);
          try {
            await saveBackup(`editorEffort.claude.${layer.label}:${layer.location}`, { entries, written: native });
            if (!isDeepStrictEqual(layer.config.inspect<unknown>(ENVIRONMENT_KEY)?.[layer.key], layer.value)) {
              result.issues.push(`Claude Code ${layer.label} environment settings changed while saving and were preserved.`);
              continue;
            }
            await layer.config.update(ENVIRONMENT_KEY, updated, layer.target);
            result.changed.push(`Claude Code ${layer.label} effort override synchronized`);
          } catch (error) {
            const detail = error instanceof Error ? error.message : String(error);
            result.issues.push(`Claude Code ${layer.label} effort override could not be synchronized: ${detail}`);
          }
        }
      }
    }
  }
  return result;
}
