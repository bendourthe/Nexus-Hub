import * as vscode from "vscode";
import {
  CursorUsageRuntime,
  type RuntimeDependencies
} from "./cursorUsageRuntime";
import { CursorUsageProvider } from "./providers/cursor";

export {
  COMMAND_IDS,
  CursorUsageRuntime,
  type RuntimeDependencies
} from "./cursorUsageRuntime";

let activeRuntime: CursorUsageRuntime | undefined;

export function activate(context: vscode.ExtensionContext): void {
  activeRuntime?.dispose();
  // HO-5: production intentionally injects no JSON or HTML live transport.
  // SecretStorage values, state.vscdb, cookies, and dashboard endpoints remain
  // untouched until a separately authorized adapter is supplied.
  const dependencies: RuntimeDependencies = {
    provider: new CursorUsageProvider({}),
    liveTransportCapable: false
  };
  activeRuntime = new CursorUsageRuntime(context, dependencies);
  context.subscriptions.push(activeRuntime);
  activeRuntime.start();
}

export function deactivate(): void {
  activeRuntime?.dispose();
  activeRuntime = undefined;
}
