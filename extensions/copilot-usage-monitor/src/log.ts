import * as vscode from "vscode";

/**
 * The extension's only log sink, a VS Code output channel created on first use.
 * Every message is a fixed string or a count: no caller passes a token, login,
 * organization name, or raw response, and the leak test reads this channel.
 */
let channel: vscode.OutputChannel | undefined;
const logged = new Set<string>();

function sink(): vscode.OutputChannel {
  channel ??= vscode.window.createOutputChannel("Copilot Usage Monitor");
  return channel;
}

export function log(message: string): void {
  sink().appendLine(`[${new Date().toISOString()}] ${message}`);
}

/** Log a message the first time `key` is seen in this session, then stay quiet. */
export function logOnce(key: string, message: string): void {
  if (logged.has(key)) {
    return;
  }
  logged.add(key);
  log(message);
}

/** Test seam: forget which one-time messages were logged and drop the channel. */
export function __resetLog(): void {
  logged.clear();
  channel = undefined;
}
