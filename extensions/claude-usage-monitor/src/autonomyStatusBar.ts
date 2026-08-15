import { execFile } from "node:child_process";
import * as vscode from "vscode";
import {
  AutonomyPresentation,
  parseAutonomyStatus,
  unavailableAutonomyPresentation,
} from "./autonomyStatus";

interface AutonomyStatusBarOptions {
  platform: string;
  command: string;
  priority: number;
  configSection: string;
}
interface ToggleItem extends vscode.QuickPickItem {
  action: "disable" | "revert" | "edits" | "full";
}

function cliExecutable(): string {
  return process.platform === "win32" ? "nexus-hub.cmd" : "nexus-hub";
}

function invokeCli(
  args: string[],
  cwd: string | undefined,
  acceptOutputOnError = false,
): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile(
      cliExecutable(),
      args,
      { cwd, encoding: "utf8", windowsHide: true, maxBuffer: 1024 * 1024 },
      (error, stdout, stderr) => {
        if (!error || (acceptOutputOnError && stdout.trim())) {
          resolve(stdout);
          return;
        }
        reject(new Error(stderr.trim() || error.message));
      },
    );
  });
}

export class AutonomyStatusBar implements vscode.Disposable {
  private readonly item: vscode.StatusBarItem;
  private readonly options: AutonomyStatusBarOptions;
  private presentation: AutonomyPresentation = unavailableAutonomyPresentation();
  private refreshTimer: NodeJS.Timeout | undefined;

  constructor(options: AutonomyStatusBarOptions) {
    this.options = options;
    this.item = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Right,
      options.priority,
    );
    this.item.name = "Nexus-Hub Autonomy";
    this.item.command = options.command;
    this.applyPresentation(this.presentation);
  }

  start(): void {
    this.item.show();
    void this.refresh();
    this.scheduleRefresh();
  }

  async refresh(): Promise<void> {
    const cwd = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    try {
      const raw = await invokeCli(
        ["autonomy", "status", "--json"],
        cwd,
        true,
      );
      this.applyPresentation(parseAutonomyStatus(raw, this.options.platform));
    } catch (error) {
      const detail = error instanceof Error ? error.message : String(error);
      this.applyPresentation(unavailableAutonomyPresentation(detail));
    }
  }

  async toggle(): Promise<void> {
    if (this.presentation.mode === "unavailable") {
      await vscode.window.showWarningMessage(this.presentation.tooltip);
      return;
    }

    const items: ToggleItem[] = [];
    if (this.presentation.mode === "expired") {
      items.push({
        label: "$(discard) Revert expired autonomy",
        description: "Restore the backed-up project configuration",
        action: "revert",
      });
    } else if (this.presentation.mode === "edits" || this.presentation.mode === "full") {
      items.push({
        label: "$(debug-stop) Disable autonomy",
        description: "Restore the backed-up project configuration",
        action: "disable",
      });
    }
    items.push(
      {
        label: "$(edit) Enable edits autonomy",
        description: "Accept file edits; keep shell-command prompts",
        action: "edits",
      },
      {
        label: "$(warning) Enable full autonomy",
        description: "Remove prompts; keep the Nexus-Hub deny hook armed",
        action: "full",
      },
    );

    const selected = await vscode.window.showQuickPick(items, {
      title: "Nexus-Hub Project Autonomy",
      placeHolder: "Choose a time-limited project-scoped posture",
    });
    if (!selected) {
      return;
    }
    if (selected.action === "disable" || selected.action === "revert") {
      await this.runImmediate(selected.action);
      return;
    }
    await this.openEnableTerminal(selected.action);
  }

  dispose(): void {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = undefined;
    }
    this.item.dispose();
  }

  private applyPresentation(presentation: AutonomyPresentation): void {
    this.presentation = presentation;
    this.item.text = presentation.text;
    this.item.tooltip = presentation.tooltip;
    this.item.backgroundColor = presentation.backgroundColor
      ? new vscode.ThemeColor(presentation.backgroundColor)
      : undefined;
  }

  private scheduleRefresh(): void {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
    }
    const configured = vscode.workspace
      .getConfiguration(this.options.configSection)
      .get<number>("autonomyRefreshSeconds", 30);
    const seconds = Math.min(300, Math.max(10, Math.round(configured)));
    this.refreshTimer = setInterval(() => void this.refresh(), seconds * 1000);
  }

  private async runImmediate(action: "disable" | "revert"): Promise<void> {
    const cwd = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    try {
      const output = await invokeCli(
        ["autonomy", action, "--platform", this.options.platform],
        cwd,
      );
      await vscode.window.showInformationMessage(output.trim() || `Autonomy ${action} complete.`);
      await this.refresh();
    } catch (error) {
      const detail = error instanceof Error ? error.message : String(error);
      await vscode.window.showErrorMessage(`Nexus-Hub autonomy ${action} failed: ${detail}`);
    }
  }

  private async openEnableTerminal(tier: "edits" | "full"): Promise<void> {
    if (tier === "full") {
      const proceed = await vscode.window.showWarningMessage(
        "Full autonomy removes approval prompts in this workspace. The terminal will show the exact config diff and require you to type the project directory name before anything changes.",
        { modal: true },
        "Review in Terminal",
      );
      if (proceed !== "Review in Terminal") {
        return;
      }
    }
    const cwd = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    const configured = vscode.workspace
      .getConfiguration(this.options.configSection)
      .get<number>("autonomyTtlMinutes", 60);
    const ttl = Math.min(480, Math.max(1, Math.round(configured)));
    const terminal = vscode.window.createTerminal({
      name: "Nexus-Hub Autonomy",
      cwd,
    });
    terminal.show(true);
    terminal.sendText(
      `nexus-hub autonomy enable --platform ${this.options.platform} --tier ${tier} --ttl ${ttl}`,
      true,
    );
  }
}
