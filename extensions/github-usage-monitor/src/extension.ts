import * as vscode from "vscode";
import { DashboardPanel } from "./dashboardPanel";
import { applyAllowances, type AllowanceMap } from "./providers/allowances";
import { GitHubTokenStore, type TokenMutationResult } from "./providers/auth";
import { DEFAULT_TIMEOUT_MS, GitHubBillingClient } from "./providers/github";
import { CapabilityStore, capabilityKey } from "./providers/capability";
import { resolveBillingOwner } from "./providers/scope";
import {
  describeBinding,
  isCompleteLogOut,
  logInToMonitor,
  logOutOfMonitor,
  peekBinding,
  type GetSessionLike,
  type MonitorBinding
} from "./providers/sessionBinding";
import { buildUsageSuggestion, crossedUnnotifiedThreshold, type AlertMetric, type Thresholds } from "./recommendations";
import { SettingsPanel, validateThresholds, type AuthDisplay } from "./settingsPanel";
import { StatusBarManager } from "./statusBarManager";
import type { BillingOwner, ProviderError, ProviderResult, UsageSnapshot, UsageState } from "./types";
import { UsageStore } from "./usageStore";
import { WARNING_VIEW_ID, WarningViewProvider } from "./warningView";

let refreshTimer: ReturnType<typeof setTimeout> | undefined;

export function activate(context: vscode.ExtensionContext): void {
  const tokens = new GitHubTokenStore(context.secrets);
  const store = new UsageStore(context.globalState, configuredStaleAfterMs());
  const dashboard = new DashboardPanel();
  const settings = new SettingsPanel();
  const warning = new WarningViewProvider(context.extensionUri);
  const status = new StatusBarManager("github-usage.dashboard");
  const cached = store.get();
  let currentState: UsageState = cached === undefined ? { state: "empty" } : { state: cached.stale ? "stale" : "fresh", data: cached };

  const capabilities = new CapabilityStore(context.globalState);
  // Adapts VS Code's provider onto the narrow shape `sessionBinding` accepts. That
  // module is given no sign-out capability, so log-out cannot reach the shared
  // GitHub session that Copilot also uses.
  const getSession: GetSessionLike = (providerId, scopes, options) =>
    Promise.resolve(
      vscode.authentication.getSession(providerId, [...scopes], options)
    ) as Promise<Awaited<ReturnType<GetSessionLike>>>;
  let binding: MonitorBinding | null = null;

  const authDisplay = async (): Promise<AuthDisplay | undefined> => {
    const owner = configuredOwner();
    if (owner === null) {
      return undefined;
    }
    binding = await peekBinding(getSession, owner).catch(() => null);
    const stored = await tokens.hasToken().catch(() => false);
    return {
      binding,
      target: capabilityKey(owner),
      capability: capabilities.get(owner, binding?.fingerprint ?? "none"),
      hasStoredToken: stored
    };
  };

  const showDashboard = (): void => dashboard.show(currentState);
  const refresh = async (): Promise<void> => {
    status.showLoading();
    currentState = await fetchConfiguredUsage(tokens, store);
    status.show(currentState);
    if (currentState.data) await maybeShowAlert(currentState.data, store, warning, showDashboard);
    scheduleRefresh(refresh);
  };

  context.subscriptions.push(
    status,
    vscode.window.registerWebviewViewProvider(WARNING_VIEW_ID, warning, { webviewOptions: { retainContextWhenHidden: true } }),
    vscode.commands.registerCommand("github-usage.dashboard", showDashboard),
    vscode.commands.registerCommand("github-usage.refresh", refresh),
    vscode.commands.registerCommand("github-usage.settings", async () => { settings.show(await authDisplay()); }),
    vscode.commands.registerCommand("github-usage.logIn", async () => {
      const owner = configuredOwner(); if (owner === null) return;
      // clearSessionPreference makes GitHub show the account picker, so the billing
      // account can deliberately differ from the one Copilot uses.
      const next = await logInToMonitor(getSession, owner);
      if (next === null) { await vscode.window.showInformationMessage("GitHub Billing: sign-in cancelled; the previous binding is unchanged."); return; }
      binding = next;
      // A new session is a different capability question, so the old verdict goes.
      await capabilities.forget(owner);
      await vscode.window.showInformationMessage(`GitHub Billing: ${describeBinding(next)}`);
      settings.show(await authDisplay());
    }),
    vscode.commands.registerCommand("github-usage.logOut", async () => {
      const owner = configuredOwner();
      const result = await logOutOfMonitor({
        clearToken: () => tokens.clearToken(),
        clearCapabilities: () => owner === null ? capabilities.clear() : capabilities.forget(owner),
        clearSessionPreference: async () => { binding = null; }
      });
      await (isCompleteLogOut(result)
        ? vscode.window.showInformationMessage("GitHub Billing: this monitor's binding was cleared. You are still signed in to the editor's GitHub session, so Copilot is unaffected.")
        : vscode.window.showWarningMessage("GitHub Billing: the binding was only partly cleared. Re-run Log out, or clear the token explicitly."));
      settings.show(await authDisplay());
    }),
    vscode.commands.registerCommand("github-usage.openNativeSettings", () => vscode.commands.executeCommand("workbench.action.openSettings", "@ext:nexus-hub.github-usage-monitor")),
    vscode.commands.registerCommand("github-usage.manualEntry", () => vscode.commands.executeCommand("workbench.action.openSettings", "githubUsage.allowances")),
    vscode.commands.registerCommand("github-usage.clearData", async () => { await store.clear(); currentState = { state: "empty" }; status.show(currentState); showDashboard(); }),
    vscode.commands.registerCommand("github-usage.setToken", async () => { await promptAndStoreToken("Store GitHub billing token", tokens, false); }),
    vscode.commands.registerCommand("github-usage.validateToken", async () => {
      const owner = configuredOwner(); if (owner === null) return;
      const result = await tokens.validateToken((token) => new GitHubBillingClient().validateCredential(owner, token));
      await showMutationResult(result, "Stored GitHub billing token is valid.");
    }),
    vscode.commands.registerCommand("github-usage.rotateToken", async () => { await promptAndStoreToken("Rotate GitHub billing token", tokens, true); }),
    vscode.commands.registerCommand("github-usage.clearToken", async () => { await tokens.clearToken(); await vscode.window.showInformationMessage("GitHub billing token removed from SecretStorage."); })
  );

  void vscode.commands.executeCommand("setContext", "githubUsage.warningActive", false);
  status.show(currentState);
  if (vscode.workspace.getConfiguration("githubUsage").get<boolean>("autoFetch", true)) void refresh();
}

export function deactivate(): void { if (refreshTimer) clearTimeout(refreshTimer); refreshTimer = undefined; }

export async function fetchConfiguredUsage(tokens: GitHubTokenStore, store: UsageStore): Promise<UsageState> {
  const owner = configuredOwner();
  if (owner === null) return { state: "empty", error: { code: "invalid-scope", message: "Configure one valid GitHub billing owner." } };
  const config = vscode.workspace.getConfiguration("githubUsage");
  const timeoutMs = config.get<number>("requestTimeoutMs", DEFAULT_TIMEOUT_MS);
  const client = new GitHubBillingClient(undefined, undefined, timeoutMs);
  const nested = await tokens.withToken((token) => client.fetchUsage({ owner, token, copilotEndpoint: config.get("copilotMetric", "ai-credits") }));
  let result: ProviderResult<UsageSnapshot>;
  if (!nested.ok) result = nested;
  else result = nested.value;
  if (result.ok) result = { ...result, value: applyAllowances(result.value, { manual: configuredAllowances(result.value) }) };
  return store.resolveFetch(result);
}

async function maybeShowAlert(snapshot: UsageSnapshot, store: UsageStore, warning: WarningViewProvider, showDashboard: () => void): Promise<void> {
  const config = vscode.workspace.getConfiguration("githubUsage");
  const thresholds: Thresholds = { moderate: config.get("thresholds.moderate", 50), high: config.get("thresholds.high", 75), critical: config.get("thresholds.critical", 95) };
  const invalid = validateThresholds({ moderate: thresholds.moderate, high: thresholds.high, critical: thresholds.critical });
  if (invalid !== null) return;
  const suggestion = buildUsageSuggestion(snapshot, config.get<AlertMetric>("alertMetric", "highest"), thresholds);
  if (!crossedUnnotifiedThreshold(suggestion, store.getAlertCycle()?.notifiedThresholds ?? []) || suggestion === null) return;
  await store.markThresholdNotified(suggestion.bucket);
  let dismissed = false;
  const dismiss = (): void => { dismissed = true; };
  await warning.show(suggestion, { onOpenDashboard: showDashboard, onDismiss: dismiss });
  const timeout = config.get<number>("notificationTimeoutSeconds", 12) * 1000;
  const timeoutHandle = scheduleWarningDismissal(timeout, () => { if (!dismissed) void warning.dismiss(); });
  void vscode.window.showWarningMessage(suggestion.message, "Open Dashboard", "Dismiss").then((action) => {
    clearTimeout(timeoutHandle);
    if (action === "Open Dashboard") showDashboard();
    if (!dismissed) void warning.dismiss();
  });
}

export function scheduleWarningDismissal(timeoutMs: number, onTimeout: () => void): ReturnType<typeof setTimeout> {
  return setTimeout(onTimeout, timeoutMs);
}

function scheduleRefresh(refresh: () => Promise<void>): void {
  if (refreshTimer) clearTimeout(refreshTimer);
  const config = vscode.workspace.getConfiguration("githubUsage");
  if (!config.get<boolean>("autoFetch", true)) return;
  refreshTimer = setTimeout(() => { void refresh(); }, config.get<number>("refreshInterval", 10) * 60_000);
}

function configuredAllowances(snapshot: UsageSnapshot): AllowanceMap {
  const config = vscode.workspace.getConfiguration("githubUsage");
  const result: AllowanceMap = {};
  const add = (kind: UsageSnapshot["copilot"]["kind"] | "actions-minutes" | "actions-storage", key: string, unit: string): void => {
    const value = config.get<number | undefined>(key); if (value !== undefined) result[kind] = { value, unit };
  };
  add(snapshot.copilot.kind, "allowances.copilot", snapshot.copilot.unit);
  add("actions-minutes", "allowances.actionsMinutes", snapshot.actionsMinutes.unit);
  add("actions-storage", "allowances.actionsStorage", snapshot.actionsStorage.unit);
  return result;
}

function configuredStaleAfterMs(): number { return vscode.workspace.getConfiguration("githubUsage").get<number>("staleAfterMinutes", 30) * 60_000; }

function configuredOwner(): BillingOwner | null {
  const config = vscode.workspace.getConfiguration("githubUsage");
  const resolution = resolveBillingOwner(config.get("billingScope", "user"), config.get("billingOwner", ""));
  if (!resolution.ok) { void vscode.window.showErrorMessage(resolution.error.message); return null; }
  return resolution.owner;
}

async function promptAndStoreToken(prompt: string, tokens: GitHubTokenStore, rotate: boolean): Promise<void> {
  const owner = configuredOwner(); if (owner === null) return;
  const token = await vscode.window.showInputBox({ prompt, password: true, ignoreFocusOut: true, placeHolder: "Fine-grained or account-authorized GitHub token" });
  if (token === undefined) return;
  const validator = (candidate: string) => new GitHubBillingClient().validateCredential(owner, candidate);
  const result = rotate ? await tokens.rotateToken(token, validator) : await tokens.setToken(token, validator);
  await showMutationResult(result, rotate ? "GitHub billing token rotated." : "GitHub billing token stored.");
}

async function showMutationResult(result: TokenMutationResult, successMessage: string): Promise<void> { if (result.ok) await vscode.window.showInformationMessage(successMessage); else await showProviderError(result.error); }
async function showProviderError(error: ProviderError): Promise<void> { await vscode.window.showErrorMessage(error.message); }
