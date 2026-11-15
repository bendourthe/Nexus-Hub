import * as os from "node:os";
import * as path from "node:path";
import * as vscode from "vscode";
import { installRoot } from "./cliBridge";
import { readEffortPreference } from "./liveEffortProxy";
import { installVendorUi } from "./vendorUiInstall";
import type { UiVendor } from "./vendorUiPatch";
import { CURSOR_EFFORT_COMMAND, CURSOR_FAST_COMMAND } from "./cursorEffort";
import { readSessionDefaults, SESSION_DEFAULTS_FILE } from "./sessionDefaults";

export interface UiEffortSummary { reloadRequired: boolean; errors: string[] }
interface NativeApi { nexusEffortBridgeVersion: number; applyNexusEffort(value: string, revision: string): unknown; applyNexusDefaults?(settings: {effort?: string; effortRevision?: string; fastMode?: boolean; fastRevision?: string}): unknown }
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
      // A menu-only build has no effort bridge, so it must not be polled as an outdated adapter.
      if (result.menuOnly) { setupErrors.push(`${item.label}: Live effort updates are not verified for this version. Open Codex in tabs still applies.`); }
      else { installed.add(item.id); }
    }
    catch (error) { setupErrors.push(`${item.label}: ${error instanceof Error ? error.message : "Native UI installation failed."}`); }
  }
  let running = false;
  let current: UiEffortSummary = { reloadRequired: false, errors: setupErrors };
  const pending = new Map<string, Promise<unknown>>();
  const updateProvider = async (id: string, work: () => Promise<unknown>): Promise<void> => {
    let update = pending.get(id);
    if (!update) {
      update = Promise.resolve().then(work); pending.set(id, update);
      void update.then(() => pending.delete(id), () => pending.delete(id));
    }
    let timeout: ReturnType<typeof setTimeout> | undefined;
    try { await Promise.race([update, new Promise((_, reject) => { timeout = setTimeout(() => reject(new Error("The native update timed out.")), 5000); })]); }
    finally { if (timeout) { clearTimeout(timeout); } }
  };
  const synchronize = async (): Promise<void> => {
    if (running || !vscode.workspace.isTrusted) { return; }
    running = true;
    try {
      const preference = readEffortPreference(path.join(hub, "preferences.json"));
      const session = readSessionDefaults(path.join(hub, SESSION_DEFAULTS_FILE));
      if (!preference && session.fastMode === null) { return; }
      const defaults = {effort: preference?.value, effortRevision: preference?.revision, fastMode: session.fastMode ?? undefined, fastRevision: session.fastMode === null ? undefined : String(session.fastMode) + ":" + session.fastRevision};
      const next: UiEffortSummary = { reloadRequired: menuReloadRequired, errors: [...setupErrors] };
      if (cursorInstalled) {
        const commands = await vscode.commands.getCommands(true);
        if (!commands.includes(CURSOR_EFFORT_COMMAND)) { next.reloadRequired = true; }
        else {
          try { if (preference) { await vscode.commands.executeCommand(CURSOR_EFFORT_COMMAND, {effort: preference.value, revision: preference.revision}); } }
          catch { next.errors.push("Cursor: The native effort update failed."); }
        }
        if (session.fastMode !== null) {
          if (!commands.includes(CURSOR_FAST_COMMAND)) { next.reloadRequired = true; }
          else { try { await vscode.commands.executeCommand(CURSOR_FAST_COMMAND, {value: session.fastMode, revision: defaults.fastRevision}); } catch { next.errors.push("Cursor: The native speed update failed."); } }
        }
      }
      await Promise.all(available.map(async (item) => {
        if (!installed.has(item.id)) { return; }
        if (!item.extension.isActive) { return; }
        const api = item.extension.exports as Partial<NativeApi> | undefined;
        if (![2, 3].includes(api?.nexusEffortBridgeVersion ?? 0) || typeof api?.applyNexusEffort !== "function") { next.reloadRequired = true; return; }
        try {
          await updateProvider(item.id, async () => {
            if (api.nexusEffortBridgeVersion === 3 && api.applyNexusDefaults) { await api.applyNexusDefaults(defaults); }
            else { if (preference) { await api.applyNexusEffort!(preference.value, preference.revision); } if (session.fastMode !== null) { next.reloadRequired = true; } }
          });
        }
        catch { next.errors.push(`${item.label}: The native effort update failed.`); }
      }));
      current = next;
    } finally { running = false; }
  };
  // Revision-aware messages initialize new composers without resetting manual choices. Unopened vendors are not activated.
  const timer = setInterval(() => void synchronize().catch(() => undefined), 1000);
  context.subscriptions.push({ dispose: () => clearInterval(timer) });
  await synchronize();
  return { summary: () => ({ ...current, errors: [...current.errors] }), synchronize };
}
