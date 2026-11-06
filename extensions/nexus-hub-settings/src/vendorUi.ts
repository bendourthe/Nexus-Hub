import * as fs from "node:fs/promises";
import * as os from "node:os";
import * as path from "node:path";
import * as vscode from "vscode";
import { installRoot } from "./cliBridge";
import { readEffortPreference } from "./liveEffortProxy";
import { installVendorUi } from "./vendorUiInstall";
import type { UiVendor } from "./vendorUiPatch";
import { CURSOR_EFFORT_COMMAND } from "./cursorEffort";

export interface UiEffortSummary { reloadRequired: boolean; errors: string[] }
interface NativeApi { nexusEffortBridgeVersion: number; applyNexusEffort(value: string, revision: string): unknown }
const providers: { vendor: UiVendor; id: string; label: string }[] = [
  { vendor: "claude", id: "anthropic.claude-code", label: "Claude Code" },
  { vendor: "codex", id: "openai.chatgpt", label: "Codex" },
];

/** Native controls own their displayed state. The stdio bridge alone cannot update composers. */
export async function installNativeUi(context: vscode.ExtensionContext): Promise<{ summary(): UiEffortSummary; synchronize(): Promise<void> } | undefined> {
  if (!vscode.workspace.isTrusted || process.platform !== "win32" || vscode.env.remoteName) { return undefined; }
  const available = providers.flatMap((provider) => {
    const extension = vscode.extensions?.getExtension(provider.id);
    return extension ? [{ ...provider, extension }] : [];
  });
  const cursor = vscode.env.appName === "Cursor";
  if (!available.length && !cursor) { return undefined; }
  const hub = installRoot(process.env, os.homedir());
  const setupErrors: string[] = [];
  const installed = new Set<string>();
  let menuReloadRequired = false;
  let cursorInstalled = false;
  if (cursor) {
    try { await installVendorUi("cursor", vscode.env.appRoot, path.join(hub, "native-ui")); cursorInstalled = true; }
    catch (error) { setupErrors.push(`Cursor: ${error instanceof Error ? error.message : "Native effort installation failed."}`); }
  }
  for (const item of available) {
    try {
      const result = await installVendorUi(item.vendor, item.extension.extensionPath, path.join(hub, "native-ui"));
      if (item.vendor === "codex" && result.changed) { menuReloadRequired = true; }
      installed.add(item.id);
    }
    catch (error) { setupErrors.push(`${item.label}: ${error instanceof Error ? error.message : "Native UI installation failed."}`); }
  }
  let running = false;
  let current: UiEffortSummary = { reloadRequired: false, errors: setupErrors };
  const synchronize = async (): Promise<void> => {
    if (running || !vscode.workspace.isTrusted) { return; }
    running = true;
    try {
      const preference = readEffortPreference(path.join(hub, "preferences.json"));
      if (!preference) { return; }
      const next: UiEffortSummary = { reloadRequired: menuReloadRequired, errors: [...setupErrors] };
      if (cursorInstalled) {
        if (!(await vscode.commands.getCommands(true)).includes(CURSOR_EFFORT_COMMAND)) { next.reloadRequired = true; }
        else {
          try { await vscode.commands.executeCommand(CURSOR_EFFORT_COMMAND, {effort: preference.value, revision: preference.revision}); }
          catch { next.errors.push("Cursor: The native effort update failed."); }
        }
      }
      for (const item of available) {
        if (!installed.has(item.id)) { continue; }
        if (!item.extension.isActive) { continue; }
        const api = item.extension.exports as Partial<NativeApi> | undefined;
        if (api?.nexusEffortBridgeVersion !== 2 || typeof api.applyNexusEffort !== "function") { next.reloadRequired = true; continue; }
        try { await api.applyNexusEffort(preference.value, preference.revision); }
        catch { next.errors.push(`${item.label}: The native effort update failed.`); }
      }
      current = next;
    } finally { running = false; }
  };
  // Revision-aware messages initialize new composers without resetting manual choices. Unopened vendors are not activated.
  const timer = setInterval(() => void synchronize().catch(() => undefined), 1000);
  context.subscriptions.push({ dispose: () => clearInterval(timer) });
  await synchronize();
  return { summary: () => ({ ...current, errors: [...current.errors] }), synchronize };
}
