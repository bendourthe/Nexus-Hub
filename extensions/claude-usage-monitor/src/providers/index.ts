import * as vscode from "vscode";
import { UsageProvider, ProviderId } from "./types";
import { ClaudeUsageProvider } from "./claude";
import { CodexUsageProvider } from "./codex";

export * from "./types";
export { describeProviderError } from "./errors";

/**
 * Read the configured provider id from the `usageMonitor.provider` setting,
 * defaulting to `claude` for backward compatibility with existing installs.
 */
export function getConfiguredProviderId(): ProviderId {
  const raw = vscode.workspace
    .getConfiguration("usageMonitor")
    .get<string>("provider", "claude");
  return raw === "codex" ? "codex" : "claude";
}

/** Instantiate the provider for the given id. */
export function createProvider(id: ProviderId): UsageProvider {
  switch (id) {
    case "codex":
      return new CodexUsageProvider();
    case "claude":
    default:
      return new ClaudeUsageProvider();
  }
}
