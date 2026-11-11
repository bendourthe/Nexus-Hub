import * as os from "node:os";
import * as path from "node:path";
import * as vscode from "vscode";
import { readBoundedFile } from "./safeRead";

/** Local index metadata only; conversation content is opened by Codex itself. */
export function historyEntries(index: string): { id: string; label: string; description: string }[] {
  const entries = new Map<string, { id: string; label: string; description: string }>();
  for (const line of index.split("\n")) {
    try {
      const row = JSON.parse(line);
      if (!/^[a-f0-9]{8}(-[a-f0-9]{4}){3}-[a-f0-9]{12}$/i.test(row.id) || typeof row.thread_name !== "string" || typeof row.updated_at !== "string") { continue; }
      entries.set(row.id, { id: row.id, label: row.thread_name.replace(/[\x00-\x1f]/g, " ").slice(0, 160), description: row.updated_at.slice(0, 10) });
    } catch { /* Ignore incomplete or malformed index rows. */ }
  }
  return [...entries.values()].reverse();
}
export async function openCodexHistory(): Promise<void> {
  if (!vscode.workspace.isTrusted || !vscode.extensions.getExtension("openai.chatgpt")) { return; }
  const home = process.env.CODEX_HOME || path.join(os.homedir(), ".codex");
  let entries: ReturnType<typeof historyEntries>;
  try {
    const file = path.join(home, "session_index.jsonl");
    entries = historyEntries(await readBoundedFile(file, 8_000_000, "History index is too large."));
  } catch { await vscode.window.showInformationMessage("Codex history is unavailable. Open the Codex sidebar to browse all sessions."); return; }
  const chosen = await vscode.window.showQuickPick(entries, { title: "Codex History", placeHolder: "Select a session to open in an editor tab", matchOnDescription: true });
  if (chosen) { await vscode.commands.executeCommand("vscode.openWith", vscode.Uri.from({ scheme: "openai-codex", authority: "route", path: "/local/" + chosen.id }), "chatgpt.conversationEditor", { preview: false }); }
}
