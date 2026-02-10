import * as vscode from "vscode";
import { UsageData, ClaudeModel } from "./types";

const STORAGE_KEY = "claudeUsageData";

export class UsageStore {
  constructor(private readonly globalState: vscode.Memento) {}

  get(): UsageData | undefined {
    return this.globalState.get<UsageData>(STORAGE_KEY);
  }

  async save(data: UsageData): Promise<void> {
    await this.globalState.update(STORAGE_KEY, data);
  }

  async clear(): Promise<void> {
    await this.globalState.update(STORAGE_KEY, undefined);
  }

  getCurrentModel(): ClaudeModel {
    const config = vscode.workspace.getConfiguration("claudeUsage");
    return config.get<ClaudeModel>("currentModel", "opus-4.6");
  }

  getTimeSinceUpdate(): string {
    const data = this.get();
    if (!data) {
      return "never";
    }

    const elapsed = Date.now() - data.lastUpdated;
    const minutes = Math.floor(elapsed / 60_000);

    if (minutes < 1) {
      return "just now";
    }
    if (minutes < 60) {
      return `${minutes} min ago`;
    }

    const hours = Math.floor(minutes / 60);
    if (hours < 24) {
      return `${hours}h ago`;
    }

    return `${Math.floor(hours / 24)}d ago`;
  }
}
