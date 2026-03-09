import * as vscode from "vscode";
import { UsageData, UsageMetric, UrgencyLevel } from "./types";

const STORAGE_KEY = "claudeUsageData";
const URGENCY_KEY = "claudeLastUrgency";

export class UsageStore {
  constructor(private readonly globalState: vscode.Memento) {}

  get(): UsageData | undefined {
    return this.globalState.get<UsageData>(STORAGE_KEY);
  }

  getWithFreshCountdowns(): UsageData | undefined {
    const data = this.get();
    if (!data) {
      return undefined;
    }
    return {
      ...data,
      session: refreshMetricCountdown(data.session),
      weeklyAllModels: refreshMetricCountdown(data.weeklyAllModels),
      weeklySonnet: refreshMetricCountdown(data.weeklySonnet),
    };
  }

  async save(data: UsageData): Promise<void> {
    await this.globalState.update(STORAGE_KEY, data);
  }

  async clear(): Promise<void> {
    await this.globalState.update(STORAGE_KEY, undefined);
    await this.globalState.update(URGENCY_KEY, undefined);
  }

  getCurrentModel(): string {
    // Primary: read Claude Code's own VS Code setting — updated whenever the user switches
    // models in Claude Code's model picker (claudeCode.selectedModel).
    // Values: "sonnet[1m]", "sonnet", "opus[1m]", "opus", "haiku", "default"
    const selected = vscode.workspace
      .getConfiguration("claudeCode")
      .get<string>("selectedModel");
    if (selected && selected.length > 0) {
      return selected;
    }
    // Fallback if claudeCode.selectedModel is not set
    return "sonnet";
  }

  getLastUrgency(): UrgencyLevel | undefined {
    return this.globalState.get<UrgencyLevel>(URGENCY_KEY);
  }

  async saveLastUrgency(level: UrgencyLevel): Promise<void> {
    await this.globalState.update(URGENCY_KEY, level);
  }

  hasResetExpired(): boolean {
    const data = this.get();
    if (!data) {
      return false;
    }
    const now = Date.now();
    const metrics = [data.session, data.weeklyAllModels, data.weeklySonnet];
    return metrics.some(
      (m) => m.resetsAt != null && m.resetsAt <= now && data.lastUpdated < m.resetsAt
    );
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

function refreshMetricCountdown(metric: UsageMetric): UsageMetric {
  if (metric.resetsAt == null) {
    return metric;
  }
  return { ...metric, resetsIn: formatResetTime(metric.resetsAt) };
}

export function formatResetTime(epochMs: number): string {
  const diffMs = epochMs - Date.now();

  if (diffMs <= 0) {
    return "any moment";
  }

  const diffMinutes = Math.floor(diffMs / 60_000);
  if (diffMinutes < 60) {
    return `${diffMinutes} min`;
  }

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) {
    const remainingMin = diffMinutes % 60;
    return remainingMin > 0 ? `${diffHours}h ${remainingMin}m` : `${diffHours}h`;
  }

  const resetDate = new Date(epochMs);
  return resetDate.toLocaleDateString("en-US", {
    weekday: "short",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}
