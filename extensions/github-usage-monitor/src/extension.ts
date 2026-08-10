import * as vscode from "vscode";
import { DashboardPanel } from "./dashboardPanel";
import { migrateSettings } from "./migration";
import { type AllowanceMap } from "./providers/allowances";
import { enrichSnapshot } from "./providers/enrich";
import {
  RepositoryVisibilityCache,
  fetchAccountPlanName,
  repositoryNamesIn,
  type JsonFetch
} from "./providers/repositories";
import { GitHubTokenStore, type TokenMutationResult } from "./providers/auth";
import { DEFAULT_TIMEOUT_MS, GitHubBillingClient } from "./providers/github";
import { probeWithToken, toMarkdownRow, toSanitizedRecord } from "./providers/authProbe";
import { CapabilityStore, SCOPE_CANDIDATES, capabilityKey } from "./providers/capability";
import { diagnoseTarget, summarizeOutcome } from "./providers/diagnose";
import { billingPageUrl, resolveBillingOwner, resolveEffectiveOwner } from "./providers/scope";
import { resolveCredential } from "./providers/credentialResolver";
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

/**
 * Repository visibility, cached for the session.
 *
 * Module-scoped so a repeating refresh does not re-resolve the same handful of
 * repositories every interval. Visibility rarely changes, and the cost of getting
 * it wrong for one session is a bar that reads conservatively, not one that reads
 * alarmingly.
 */
const visibilityCache = new RepositoryVisibilityCache((path, token, signal) =>
  new GitHubBillingClient().getJson(path, token, signal)
);

export async function activate(context: vscode.ExtensionContext): Promise<void> {
  // Awaited before anything reads configuration or storage. v3.16.3 moved every
  // key into the `githubUsageMonitor.*` namespace, so a read that races the
  // migration would see defaults and present a user's configured monitor as a
  // freshly-installed one. VS Code awaits this promise before marking the
  // extension active, so the cost is paid once, on the first launch after upgrade.
  // The old names live only in `migration.ts`, which `rename.test.ts` exempts.
  // The diagnosis writes its sanitized record here rather than to a log line, so it
  // is copyable without a credential ever reaching the output. The migration shares
  // it, so a partial migration is inspectable in the same place.
  const diagnostics = vscode.window.createOutputChannel("GitHub Usage Monitor");
  await migrateSettings(context, vscode.workspace.getConfiguration(), (line) => diagnostics.appendLine(line));

  const tokens = new GitHubTokenStore(context.secrets);
  const store = new UsageStore(context.globalState, configuredStaleAfterMs());
  const dashboard = new DashboardPanel();
  const settings = new SettingsPanel();
  const warning = new WarningViewProvider(context.extensionUri);
  const status = new StatusBarManager("githubUsageMonitor.dashboard");
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
    const owner = await resolveOwnerForFetch(getSession);
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
    currentState = await fetchConfiguredUsage(tokens, store, { getSession, capabilities });
    status.show(currentState);
    if (currentState.data) await maybeShowAlert(currentState.data, store, warning, showDashboard);
    scheduleRefresh(refresh);
  };

  context.subscriptions.push(
    status,
    diagnostics,
    vscode.window.registerWebviewViewProvider(WARNING_VIEW_ID, warning, { webviewOptions: { retainContextWhenHidden: true } }),
    vscode.commands.registerCommand("githubUsageMonitor.dashboard", showDashboard),
    vscode.commands.registerCommand("githubUsageMonitor.refresh", refresh),
    vscode.commands.registerCommand("githubUsageMonitor.settings", async () => { settings.show(await authDisplay()); }),
    vscode.commands.registerCommand("githubUsageMonitor.logIn", async () => {
      // Deliberately does NOT require a resolved owner. With nothing configured there
      // is no session yet, so the owner cannot be detected yet, so demanding one here
      // would deadlock the very first connection. The scope candidates come from the
      // configured LEVEL, which always has a value.
      const level = vscode.workspace.getConfiguration("githubUsageMonitor").get("billingScope", "user") as BillingOwner["scope"];
      const scopes = SCOPE_CANDIDATES[level]?.slice(0, 1) ?? ["user"];
      // clearSessionPreference makes GitHub show the account picker, so the billing
      // account can deliberately differ from the one Copilot uses.
      const next = await logInToMonitor(getSession, { scope: level, name: "pending" }, scopes);
      if (next === null) { await vscode.window.showInformationMessage("GitHub Usage Monitor: sign-in cancelled; the previous binding is unchanged."); return; }
      binding = next;
      const resolved = await resolveOwnerForFetch(getSession);
      // A new session is a different capability question, so the old verdict goes.
      if (resolved !== null) await capabilities.forget(resolved);
      await vscode.window.showInformationMessage(`GitHub Usage Monitor: ${describeBinding(next)}`);
      void refresh();
      settings.show(await authDisplay());
    }),
    vscode.commands.registerCommand("githubUsageMonitor.diagnoseAuth", async () => {
      const owner = configuredOwner(); if (owner === null) return;
      const outcome = await diagnoseTarget({ getSession, probeWithToken }, owner);
      if (outcome.status === "probed") {
        binding = outcome.binding;
        await capabilities.remember(owner, outcome.binding.fingerprint, outcome.capability);
        // The sanitized record only: its key set is asserted by test, so it can be
        // pasted into the probe doc or an issue without carrying a credential.
        diagnostics.appendLine(JSON.stringify(toSanitizedRecord(outcome.record), null, 2));
        diagnostics.appendLine(toMarkdownRow(outcome.record));
        diagnostics.show(true);
      }
      const summary = summarizeOutcome(outcome, owner);
      // A broader scope is offered ONLY when GitHub's accepted-scope header says it
      // is required, and always as an explicit choice rather than a silent retry.
      const retry = outcome.status === "probed" && outcome.escalation !== null
        ? await vscode.window.showWarningMessage(summary, `Retry with ${outcome.escalation.join(", ")}`)
        : (await vscode.window.showInformationMessage(summary), undefined);
      if (retry !== undefined && outcome.status === "probed" && outcome.escalation !== null) {
        const escalated = await diagnoseTarget({ getSession, probeWithToken }, owner, outcome.escalation);
        if (escalated.status === "probed") {
          binding = escalated.binding;
          await capabilities.remember(owner, escalated.binding.fingerprint, escalated.capability);
          diagnostics.appendLine(toMarkdownRow(escalated.record));
          await vscode.window.showInformationMessage(summarizeOutcome(escalated, owner));
        }
      }
      settings.show(await authDisplay());
    }),
    vscode.commands.registerCommand("githubUsageMonitor.logOut", async () => {
      const owner = configuredOwner();
      const result = await logOutOfMonitor({
        clearToken: () => tokens.clearToken(),
        clearCapabilities: () => owner === null ? capabilities.clear() : capabilities.forget(owner),
        clearSessionPreference: async () => { binding = null; }
      });
      await (isCompleteLogOut(result)
        ? vscode.window.showInformationMessage("GitHub Usage Monitor: this monitor's binding was cleared. You are still signed in to the editor's GitHub session, so Copilot is unaffected.")
        : vscode.window.showWarningMessage("GitHub Usage Monitor: the binding was only partly cleared. Re-run Log out, or clear the token explicitly."));
      settings.show(await authDisplay());
    }),
    vscode.commands.registerCommand("githubUsageMonitor.openBillingPage", async () => {
      const owner = await resolveOwnerForFetch(getSession);
      // Authoritative figures live on GitHub's own billing page. When no owner is
      // resolved yet, the personal page is still the right destination.
      const url = owner === null ? "https://github.com/settings/billing" : billingPageUrl(owner);
      await vscode.env.openExternal(vscode.Uri.parse(url));
    }),
    vscode.commands.registerCommand("githubUsageMonitor.openNativeSettings", () => vscode.commands.executeCommand("workbench.action.openSettings", "@ext:nexus-hub.github-usage-monitor")),
    vscode.commands.registerCommand("githubUsageMonitor.manualEntry", () => vscode.commands.executeCommand("workbench.action.openSettings", "githubUsageMonitor.allowances")),
    vscode.commands.registerCommand("githubUsageMonitor.clearData", async () => { await store.clear(); currentState = { state: "empty" }; status.show(currentState); showDashboard(); }),
    vscode.commands.registerCommand("githubUsageMonitor.setToken", async () => { await promptAndStoreToken("Store GitHub billing token", tokens, false); }),
    vscode.commands.registerCommand("githubUsageMonitor.validateToken", async () => {
      const owner = configuredOwner(); if (owner === null) return;
      const result = await tokens.validateToken((token) => new GitHubBillingClient().validateCredential(owner, token));
      await showMutationResult(result, "Stored GitHub billing token is valid.");
    }),
    vscode.commands.registerCommand("githubUsageMonitor.rotateToken", async () => { await promptAndStoreToken("Rotate GitHub billing token", tokens, true); }),
    vscode.commands.registerCommand("githubUsageMonitor.clearToken", async () => { await tokens.clearToken(); await vscode.window.showInformationMessage("GitHub billing token removed from SecretStorage."); })
  );

  void vscode.commands.executeCommand("setContext", "githubUsageMonitor.warningActive", false);
  status.show(currentState);
  if (vscode.workspace.getConfiguration("githubUsageMonitor").get<boolean>("autoFetch", true)) void refresh();
}

export function deactivate(): void { if (refreshTimer) clearTimeout(refreshTimer); refreshTimer = undefined; }

export async function fetchConfiguredUsage(
  tokens: GitHubTokenStore,
  store: UsageStore,
  auth?: { getSession: GetSessionLike; capabilities: CapabilityStore }
): Promise<UsageState> {
  const owner = await resolveOwnerForFetch(auth?.getSession);
  if (owner === null) {
    return {
      state: "empty",
      error: {
        code: "invalid-scope",
        message:
          'Set githubUsageMonitor.billingScope and githubUsageMonitor.billingOwner, then Refresh. For a personal account, connect with "GitHub Usage Monitor: Log In or Switch Account" and the owner is detected for you.'
      }
    };
  }
  const config = vscode.workspace.getConfiguration("githubUsageMonitor");
  const timeoutMs = config.get<number>("requestTimeoutMs", DEFAULT_TIMEOUT_MS);
  const client = new GitHubBillingClient(undefined, undefined, timeoutMs);

  // The wiring v3.15.12 Phase 4 originally missed: prefer a stored PAT, otherwise
  // use the editor's GitHub session. Without this the auth model was complete and
  // inert, and a user with a working session still saw "no token stored".
  let result: ProviderResult<UsageSnapshot>;
  // Captured so the two non-billing lookups the percentage needs (repository
  // visibility and the account plan) reuse the SAME credential the billing call
  // succeeded with, rather than re-resolving and possibly picking a different one.
  let credentialToken: string | null = null;
  if (auth !== undefined) {
    const binding = await peekBinding(auth.getSession, owner).catch(() => null);
    const resolved = await resolveCredential(
      {
        hasStoredToken: () => tokens.hasToken(),
        readStoredToken: () => Promise.resolve(undefined),
        getSession: auth.getSession,
        capability: auth.capabilities.get(owner, binding?.fingerprint ?? "none")
      },
      owner
    );
    if (!resolved.ok) {
      return store.resolveFetch({ ok: false, error: resolved.error, rate: EMPTY_RATE });
    }
    if (resolved.source === "stored-pat") {
      const nested = await tokens.withToken((token) => { credentialToken = token; return client.fetchUsage({ owner, token, copilotEndpoint: config.get("copilotMetric", "ai-credits") }); });
      result = nested.ok ? nested.value : nested;
    } else {
      credentialToken = resolved.token;
      result = await client.fetchUsage({ owner, token: resolved.token, copilotEndpoint: config.get("copilotMetric", "ai-credits") });
      // Remember what the session proved, so the panel can explain itself and the
      // next refresh does not re-probe a target already known to work.
      if (binding !== null) {
        await auth.capabilities.remember(owner, binding.fingerprint, result.ok
          ? { status: "supported", source: "vscode-oauth", evidence: "probed-only", grantedScopes: resolved.scopes, verifiedAt: new Date().toISOString() }
          : { status: "blocked", reason: "insufficient-role", acceptedScopes: result.error.accepted?.acceptedOAuthScopes ?? [], detail: result.error.message, observedAt: new Date().toISOString() });
      }
    }
  } else {
    const nested = await tokens.withToken((token) => { credentialToken = token; return client.fetchUsage({ owner, token, copilotEndpoint: config.get("copilotMetric", "ai-credits") }); });
    result = nested.ok ? nested.value : nested;
  }
  if (result.ok) {
    result = { ...result, value: await enrichWithAllowances(result.value, client, credentialToken, owner) };
  }
  return store.resolveFetch(result);
}

async function maybeShowAlert(snapshot: UsageSnapshot, store: UsageStore, warning: WarningViewProvider, showDashboard: () => void): Promise<void> {
  const config = vscode.workspace.getConfiguration("githubUsageMonitor");
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
  const config = vscode.workspace.getConfiguration("githubUsageMonitor");
  if (!config.get<boolean>("autoFetch", true)) return;
  refreshTimer = setTimeout(() => { void refresh(); }, config.get<number>("refreshInterval", 10) * 60_000);
}

/**
 * Values the user set explicitly, which override the plan-derived denominator.
 *
 * The panel derives a denominator automatically and shows its provenance, so this
 * is a correction path rather than a setup step. It exists because a published
 * per-plan figure cannot detect its own disagreement with an account: data packs,
 * Education benefits, and negotiated terms are all invisible to the API. Without an
 * override such an account has no way to ever be right.
 *
 * Storage is declared in gigabytes because `enrichSnapshot` converts the reported
 * GigabyteHours consumption into GB-months before allowances are applied - so the
 * user enters the figure exactly as GitHub's billing page shows it.
 */
function configuredAllowances(snapshot: UsageSnapshot): AllowanceMap {
  const config = vscode.workspace.getConfiguration("githubUsageMonitor");
  const result: AllowanceMap = {};
  const add = (kind: UsageSnapshot["copilot"]["kind"] | "actions-minutes" | "actions-storage", key: string, unit: string): void => {
    const value = config.get<number | undefined>(key); if (value !== undefined) result[kind] = { value, unit };
  };
  add(snapshot.copilot.kind, "allowances.copilot", snapshot.copilot.unit);
  add("actions-minutes", "allowances.actionsMinutes", "minutes");
  add("actions-storage", "allowances.actionsStorage", "gigabytes");
  return result;
}

/**
 * Resolves the two lookups a percentage needs, then enriches the snapshot.
 *
 * Degrades rather than failing. If either lookup is unavailable - no credential, a
 * token without repository read access, a rate limit - the snapshot comes back with
 * `allowanceState: "unknown"` and an explanation, which is the honest outcome. A
 * failed lookup must never produce a percentage, and must never fail the refresh
 * that already succeeded.
 */
async function enrichWithAllowances(
  snapshot: UsageSnapshot,
  client: GitHubBillingClient,
  token: string | null,
  owner: BillingOwner
): Promise<UsageSnapshot> {
  const manualAllowances = configuredAllowances(snapshot);
  if (token === null) {
    return enrichSnapshot(snapshot, { visibility: {}, planName: null, manualAllowances }).snapshot;
  }
  const fetchJson: JsonFetch = (path, credential, signal) => client.getJson(path, credential, signal);
  const names = repositoryNamesIn(snapshot.actionsMinutes.breakdowns);
  const visibility = await visibilityCache
    .resolve(names, { token, owner: owner.name })
    .catch(() => ({}));
  const planName = await fetchAccountPlanName(fetchJson, token).catch(() => null);
  return enrichSnapshot(snapshot, { visibility, planName, manualAllowances }).snapshot;
}

function configuredStaleAfterMs(): number { return vscode.workspace.getConfiguration("githubUsageMonitor").get<number>("staleAfterMinutes", 30) * 60_000; }

function configuredOwner(): BillingOwner | null {
  const config = vscode.workspace.getConfiguration("githubUsageMonitor");
  const resolution = resolveBillingOwner(config.get("billingScope", "user"), config.get("billingOwner", ""));
  if (!resolution.ok) { void vscode.window.showErrorMessage(resolution.error.message); return null; }
  return resolution.owner;
}

const EMPTY_RATE = { remaining: null, resetAt: null, retryAfterMs: null } as const;

/**
 * The owner used by a refresh. For `user` scope with no configured name, the
 * signed-in account is used, so a personal account needs no setup at all. An
 * organization or enterprise name cannot be inferred and is still required, because
 * guessing which of several organizations is meant would be worse than asking.
 *
 * Resolves silently: a background refresh must never raise a sign-in dialog.
 */
async function resolveOwnerForFetch(
  getSession?: GetSessionLike
): Promise<BillingOwner | null> {
  const config = vscode.workspace.getConfiguration("githubUsageMonitor");
  const scope = config.get("billingScope", "user");
  const configured = config.get("billingOwner", "");
  let accountLabel: string | null = null;
  if (getSession !== undefined && configured.trim().length === 0 && scope === "user") {
    const session = await getSession("github", [], { createIfNone: false, silent: true }).catch(() => undefined);
    accountLabel = session?.account?.label ?? null;
  }
  const resolution = resolveEffectiveOwner(scope, configured, accountLabel);
  return resolution.ok ? resolution.owner : null;
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
