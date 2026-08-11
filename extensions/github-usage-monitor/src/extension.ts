import * as vscode from "vscode";
import { DashboardPanel } from "./dashboardPanel";
import { migrateSettings } from "./migration";
import { type AllowanceMap } from "./providers/allowances";
import { enrichSnapshot } from "./providers/enrich";
import { FIRST_RUN_DECLINED_KEY, runFirstRunConnection } from "./providers/firstRun";
import {
  RepositoryVisibilityCache,
  fetchCopilotSubscription,
  fetchOwnerPlanName,
  repositoryNamesIn,
  type JsonFetch
} from "./providers/repositories";
import { GitHubTokenStore, type TokenMutationResult } from "./providers/auth";
import { DEFAULT_TIMEOUT_MS, GITHUB_USER_AGENT, GitHubBillingClient, explainOrganizationNotFound, membershipPath } from "./providers/github";
import { probeWithToken, toMarkdownRow, toSanitizedRecord } from "./providers/authProbe";
import { CapabilityStore, SCOPE_CANDIDATES, capabilityKey, firstScopeCandidate } from "./providers/capability";
import { beginOwnerWrite, endOwnerWrite, ownerWriteInFlight, reconcileOwner } from "./providers/ownerReconcile";
import { diagnoseTarget, summarizeOutcome } from "./providers/diagnose";
import { billingPageUrl, isReconnectableError, resolveBillingOwner, resolveEffectiveOwner } from "./providers/scope";
import { resolveCredential } from "./providers/credentialResolver";
import {
  bindingFromSession,
  describeBinding,
  isCompleteLogOut,
  logInToMonitor,
  logOutOfMonitor,
  peekBinding,
  type GetSessionLike,
  type MonitorBinding
} from "./providers/sessionBinding";
import { buildUsageSuggestion, crossedUnnotifiedThreshold, type AlertMetric, type Thresholds } from "./recommendations";
import { isEditableSetting, readSettings, validateThresholds, type AuthDisplay } from "./settingsPanel";
import { StatusBarManager } from "./statusBarManager";
import { registerUpdateWatcher, runningIsStale } from "./updateWatcher";
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

  // Registered early and unconditionally: an install that lands underneath this
  // window leaves THIS code stale, so it is the only code able to say so.
  registerUpdateWatcher(context, "GitHub Usage Monitor");
  // A window running superseded code defers rather than competing. Global config
  // writes reach every window, so an un-reloaded window is an active participant in
  // any loop, not a passive one - see `runningIsStale`.
  setDeferToNewerWindow(runningIsStale(context));

  const tokens = new GitHubTokenStore(context.secrets);
  const store = new UsageStore(context.globalState, configuredStaleAfterMs());
  /**
   * Applies one setting written from the panel.
   *
   * Re-validates rather than trusting the message. A webview is a browser context,
   * so its client-side checks are a convenience for the user, never a guarantee for
   * the extension: `isEditableSetting` gates BOTH the key and the value type, so a
   * message cannot reach an arbitrary VS Code setting, and threshold ordering is
   * re-checked here because the panel's inline check can be bypassed.
   */
  const applySetting = (key: unknown, value: unknown): void => {
    if (!isEditableSetting(key, value)) return;
    void (async () => {
      const config = vscode.workspace.getConfiguration("githubUsageMonitor");
      if (key.startsWith("thresholds.")) {
        const current = readSettings();
        const candidate = {
          moderate: key === "thresholds.moderate" ? (value as number) : current.moderate,
          high: key === "thresholds.high" ? (value as number) : current.high,
          critical: key === "thresholds.critical" ? (value as number) : current.critical
        };
        if (validateThresholds(candidate) !== null) return;
      }
      await config.update(key, value, vscode.ConfigurationTarget.Global);
      // Re-render both surfaces so the change is visible immediately rather than at
      // the next refresh. A setting that appears to do nothing for ten minutes reads
      // as broken.
      status.show(currentState);
      showDashboard();
    })();
  };

  const dashboard = new DashboardPanel(applySetting);
  const warning = new WarningViewProvider(context.extensionUri);
  const status = new StatusBarManager("githubUsageMonitor.dashboard");
  const cached = store.get();
  let currentState: UsageState = cached === undefined ? { state: "empty" } : { state: cached.stale ? "stale" : "fresh", data: cached };

  const capabilities = new CapabilityStore(context.globalState);
  // Adapts VS Code's provider onto the narrow shape `sessionBinding` accepts. That
  // module is given no sign-out capability, so log-out cannot reach the shared
  // GitHub session that Copilot also uses.
  /**
   * Every session request is PINNED to the account the user chose.
   *
   * This is the defect the whole 2026-08-11 sequence was downstream of. A scope list
   * identifies a permission grant, not an identity: with two GitHub accounts signed
   * in to the editor, `getSession("github", ["user"], ...)` returns EITHER of them,
   * and which one is not stable between calls. The panel therefore alternated
   * between a correct reading and a 404 for the SAME configured owner - reading
   * `/users/bendourthe/settings/billing/...` succeeds with bendourthe's token and
   * 404s with the other account's, because one user cannot read another's billing.
   *
   * Every symptom in that sequence follows from it: the flickering notification (the
   * reconciler saw an alternating login), the wrong account after a reload, the
   * intermittent "insufficient-role", and the panel switching between populated and
   * empty. Four fixes downstream of a non-deterministic credential could not have
   * held, because the non-determinism was the cause rather than a trigger.
   *
   * `account` is honored from VS Code 1.94. On an older host the extra option is
   * ignored and behavior is exactly what it was, so this degrades rather than breaks.
   */
  const getSession: GetSessionLike = async (providerId, scopes, options) => {
    // NOT pinned when the user is explicitly switching. `clearSessionPreference` is
    // precisely the "let me choose an account" signal, and pinning it to the account
    // already recorded would make the Switch button unable to switch.
    const wanted = options.clearSessionPreference === true
      ? ""
      : context.globalState.get<string>(BOUND_ACCOUNT_KEY, "");
    const account =
      wanted === "" || providerId !== "github"
        ? undefined
        : (await Promise.resolve(vscode.authentication.getAccounts(providerId)).catch(() => []))
            .find((candidate) => candidate.label.trim().toLowerCase() === wanted.trim().toLowerCase());
    return (await vscode.authentication.getSession(providerId, [...scopes], {
      ...options,
      // Only when the recorded account is actually present. Passing an account the
      // provider no longer knows would fail the request outright rather than falling
      // back, which would turn a signed-out account into a broken extension.
      ...(account === undefined ? {} : { account })
    })) as Awaited<ReturnType<GetSessionLike>>;
  };
  let binding: MonitorBinding | null = null;

  const authDisplay = async (): Promise<AuthDisplay | undefined> => {
    const owner = await resolveOwnerForFetch(getSession);
    if (owner === null) {
      return undefined;
    }
    binding = await peekBinding(getSession, owner).catch(() => null);
    const stored = await tokens.hasToken().catch(() => false);
    // Falls back to the RECORDED label when a silent peek misses. The header's "User"
    // line previously existed only for as long as one lookup succeeded, so it
    // disappeared intermittently while the account had plainly not changed.
    const recorded = context.globalState.get<string>(BOUND_ACCOUNT_KEY, "");
    const display: MonitorBinding | null =
      binding !== null
        ? binding
        : recorded === ""
          ? null
          : { accountLabel: recorded, scopes: [], fingerprint: "recorded" };
    return {
      binding: display,
      target: capabilityKey(owner),
      capability: capabilities.get(owner, binding?.fingerprint ?? "none"),
      hasStoredToken: stored
    };
  };

  /**
   * The single panel. `auth` is optional so the common path stays synchronous -
   * resolving the auth display costs a silent session peek, which is worth paying
   * when the user opened Settings and not on every alert-driven reveal.
   */
  const showDashboard = (auth?: AuthDisplay): void => dashboard.show(currentState, auth);
  const showDashboardWithAuth = async (): Promise<void> => showDashboard(await authDisplay());
  const refresh = async (): Promise<void> => {
    // A signed-out monitor stays signed out. The editor's GitHub session is still
    // there and would otherwise be picked up on the very next tick.
    if (context.globalState.get<boolean>(SIGNED_OUT_KEY, false)) {
      currentState = signedOutState();
      status.show(currentState, null);
      dashboard.update(currentState, await authDisplay());
      scheduleRefresh(refresh);
      return;
    }
    status.showLoading();
    // Deliberately NOT reconciling here.
    //
    // The loop needs the edge reconcile -> write -> configuration event -> refresh ->
    // reconcile. Four attempts to make the reconcile step behave (message dedupe, a
    // scoped session request, a bound-account check, offer-instead-of-apply) each
    // removed one way IN to that cycle and the loop survived every time. Removing
    // reconciliation from the refresh path severs the cycle itself: whatever writes,
    // and however the session answers, a refresh can no longer feed a correction.
    //
    // Nothing is lost. Reconciliation catches account changes made out of band - VS
    // Code's own account preferences, Settings Sync, a hand-edited settings file -
    // which are activation and sign-in events, not per-tick ones. It runs at both.
    currentState = await fetchConfiguredUsage(tokens, store, { getSession, capabilities });
    // Resolved once and shared, so the hover and the panel name the same account
    // rather than each peeking at the session separately.
    const display = await authDisplay();
    status.show(currentState, display?.binding?.accountLabel ?? null);
    // Both surfaces, always. The status bar and the panel read the same state, so
    // updating one without the other is how a cleared warning lingered in the panel.
    dashboard.update(currentState, display);
    if (currentState.data) await maybeShowAlert(currentState.data, store, warning, showDashboard);
    await maybeOfferReconnect(currentState);
    scheduleRefresh(refresh);
  };

  /**
   * Turns a fixable authorization failure into an action instead of a quiet warning.
   *
   * Once per session, and only for failures a credential can actually resolve. A
   * reload binds whichever session VS Code considers default, which may not be the
   * account the configured owner needs - and the previous behavior was to serve
   * last-known-good data behind a small banner, which reads as "working" while the
   * figures describe a different account entirely.
   *
   * Once per session, not once per refresh: the timer fires on an interval, and an
   * offer that reappears every few minutes is the nagging Phase 3 exists to prevent.
   */
  let reconnectOffered = false;
  const maybeOfferReconnect = async (state: UsageState): Promise<void> => {
    const code = state.error?.code;
    if (reconnectOffered || code === undefined || !isReconnectableError(code)) return;
    reconnectOffered = true;
    const action = await vscode.window.showWarningMessage(
      `GitHub Usage Monitor: ${state.error?.message ?? "the configured billing owner could not be read."}`,
      "Reconnect"
    );
    if (action === "Reconnect") await vscode.commands.executeCommand("githubUsageMonitor.logIn");
  };

  // A billing-owner change IS an account change, whichever route it arrives by: the
  // sign-in picker, the settings UI, or a synced settings file. Refreshing only from
  // inside the logIn command left every other route stale, which is what "I selected
  // the organization and nothing happened" looked like from the outside.
  context.subscriptions.push(
    vscode.workspace.onDidChangeConfiguration((event) => {
      const ownerChanged =
        event.affectsConfiguration("githubUsageMonitor.billingScope") ||
        event.affectsConfiguration("githubUsageMonitor.billingOwner") ||
        event.affectsConfiguration("githubUsageMonitor.copilotMetric");
      // Skipped mid-write: the first of the pair's two writes fires this event while
      // the pair is still inconsistent, and refreshing there is what let the healer
      // reset an explicitly chosen organization back to the personal account. The
      // write's own caller refreshes once both halves have landed.
      if (ownerChanged && !ownerWriteInFlight()) void refresh();
    })
  );

  context.subscriptions.push(
    status,
    diagnostics,
    vscode.window.registerWebviewViewProvider(WARNING_VIEW_ID, warning, { webviewOptions: { retainContextWhenHidden: true } }),
    // WITH auth. Registered as the bare `showDashboard` this passed no auth at all,
    // so a panel opened from the status bar rendered with no account label no matter
    // what was recorded - the "User" line was missing on every fresh window and
    // appeared only once some other path happened to re-render with auth resolved.
    vscode.commands.registerCommand("githubUsageMonitor.dashboard", showDashboardWithAuth),
    vscode.commands.registerCommand("githubUsageMonitor.refresh", refresh),
    // Reveals the one panel with its settings section available, rather than
    // opening a second webview. The section itself is toggled by the gear.
    vscode.commands.registerCommand("githubUsageMonitor.settings", showDashboardWithAuth),
    vscode.commands.registerCommand("githubUsageMonitor.logIn", async () => {
      // Deliberately does NOT require a resolved owner. With nothing configured there
      // is no session yet, so the owner cannot be detected yet, so demanding one here
      // would deadlock the very first connection. The scope candidates come from the
      // configured LEVEL, which always has a value.
      const level = vscode.workspace.getConfiguration("githubUsageMonitor").get("billingScope", "user") as BillingOwner["scope"];
      // Use the shared helper, NOT a hand-rolled slice of the escalation list.
      // Slicing to one element here requested `user` alone and silently dropped
      // `repo`, so switching accounts undid private-repository visibility on the
      // exact path a user takes to change accounts.
      const scopes = firstScopeCandidate({ scope: level, name: "pending" });
      // clearSessionPreference makes GitHub show the account picker, so the billing
      // account can deliberately differ from the one Copilot uses.
      const next = await logInToMonitor(getSession, { scope: level, name: "pending" }, scopes);
      if (next === null) { void vscode.window.showInformationMessage("GitHub Usage Monitor: sign-in cancelled; the previous binding is unchanged."); return; }
      binding = next;
      // An explicit connection supersedes any earlier dismissal, and any sign-out.
      await context.globalState.update(FIRST_RUN_DECLINED_KEY, undefined);
      await context.globalState.update(SIGNED_OUT_KEY, undefined);
      // A fresh connection is a fresh reconciliation question; keeping the previous
      // verdict would suppress the notice for a genuinely new correction, and a
      // tripped breaker would keep a legitimate later correction from running.
      resetReconciliationBreaker();
      // Offer the organizations this account belongs to. A work account usually
      // cannot read its OWN user-scope billing - the organization or enterprise owns
      // that relationship - so binding a session without also choosing the billing
      // owner leaves the monitor querying a target that will always 403.
      //
      // This runs BEFORE the binding is announced and before any capability verdict
      // is cleared. Announcing first meant the toast was AWAITED, and a VS Code
      // notification promise settles on dismissal rather than on display - so the
      // owner picker never appeared until the notice was closed by hand (v3.16.3).
      const chosen = await chooseBillingOwnerAfterSignIn(getSession, next.scopes);
      diagnostics.appendLine(`logIn: account=${next.accountLabel ?? "(none)"} chose=${chosen === null ? "(cancelled)" : `${chosen.scope}/${chosen.name}`}`);
      // The scope a session must carry depends on the owner, which is only known
      // now. `user` and `repo` are disjoint, so choosing an organization after a
      // user-scope sign-in left the session asking for a permission the billing
      // endpoint does not accept. No-op when the scope is already granted, and
      // deliberately WITHOUT clearSessionPreference: the account was just chosen,
      // and re-showing the account picker here would be a second unasked prompt.
      if (chosen !== null) {
        const rebound = await ensureScopeForOwner(getSession, chosen, next);
        if (rebound !== null) binding = rebound;
      }
      // Forget the verdict for the target actually about to be used. Clearing the
      // PREVIOUS owner's verdict (what this did before the reorder) left a stale
      // `blocked` on the newly chosen owner, and `resolveCredential` skips a blocked
      // target - so a freshly fixed permission still read as unreachable.
      // The chosen account, recorded. This is the fact every later tick reads instead
      // of re-deriving an identity from whichever session answers first.
      await context.globalState.update(BOUND_ACCOUNT_KEY, binding?.accountLabel ?? undefined);
      const resolved = await resolveOwnerForFetch(getSession);
      if (resolved !== null) await capabilities.forget(resolved);
      void vscode.window.showInformationMessage(`GitHub Usage Monitor: ${describeBinding(binding)}`);
      // AWAIT, not fire-and-forget. The old code rendered the panel from the previous
      // account's state while the new fetch was still in flight, which is why the
      // status bar updated and the panel did not.
      await refresh();
      await showDashboardWithAuth();
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
      await showDashboardWithAuth();
    }),
    vscode.commands.registerCommand("githubUsageMonitor.logOut", async () => {
      const owner = configuredOwner();
      const result = await logOutOfMonitor({
        clearToken: () => tokens.clearToken(),
        clearCapabilities: () => owner === null ? capabilities.clear() : capabilities.forget(owner),
        clearSessionPreference: async () => { binding = null; }
      });
      // Logging out has to STICK, and clearing the binding alone did not.
      //
      // This extension deliberately cannot end VS Code's GitHub session - Copilot
      // shares it - so that session survives, the next silent peek finds it, and the
      // monitor reconnected itself within one refresh. From the user's side the
      // button did nothing: the same figures stayed on screen. A durable flag is the
      // only thing that can express "this monitor is signed out" while the editor's
      // session remains, so the state is recorded rather than inferred.
      await context.globalState.update(SIGNED_OUT_KEY, true);
      await context.globalState.update(BOUND_ACCOUNT_KEY, undefined);
      // The stale figures go too. Leaving last-known-good data behind a "signed out"
      // panel is the same lie in a different place.
      await store.clear();
      await context.globalState.update(FIRST_RUN_DECLINED_KEY, true);
      currentState = signedOutState();
      status.show(currentState, null);
      dashboard.update(currentState, await authDisplay());
      void (isCompleteLogOut(result)
        ? vscode.window.showInformationMessage("GitHub Usage Monitor: signed out. You are still signed in to the editor's GitHub session, so Copilot is unaffected.")
        : vscode.window.showWarningMessage("GitHub Usage Monitor: the binding was only partly cleared. Re-run Log out, or clear the token explicitly."));
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
  // A sign-out survives a window reload. Without this the first activation after a
  // reload found the editor's surviving GitHub session and reconnected, so the
  // decision the user made in the last window was quietly discarded in this one.
  if (context.globalState.get<boolean>(SIGNED_OUT_KEY, false)) currentState = signedOutState();
  status.show(currentState);
  if (
    !context.globalState.get<boolean>(SIGNED_OUT_KEY, false) &&
    vscode.workspace.getConfiguration("githubUsageMonitor").get<boolean>("autoFetch", true)
  ) {
    // Deliberately NOT awaited. The sign-in flow can block on a browser round-trip
    // or hang outright, and activation must not wait on it - a slow auth provider
    // would otherwise delay VS Code startup for every user of this extension.
    void (async () => {
      const owner = await resolveOwnerForFetch(getSession);
      const result = await runFirstRunConnection({
        getSession,
        hasStoredToken: () => tokens.hasToken(),
        isDeclined: () => context.globalState.get<boolean>(FIRST_RUN_DECLINED_KEY) === true,
        recordDecline: () => Promise.resolve(context.globalState.update(FIRST_RUN_DECLINED_KEY, true)),
        clearDecline: () => Promise.resolve(context.globalState.update(FIRST_RUN_DECLINED_KEY, undefined)),
        // A scope, not an owner. With nothing configured there is no session yet,
        // so the owner cannot be detected yet - but scope is all the sequence needs
        // to choose auth scopes, and passing a placeholder owner invited the reading
        // that "pending" was a real account name (v3.16.3 NI-5).
        scope: owner?.scope ?? configuredScope()
      });
      if (result.outcome.status === "connected") binding = result.outcome.binding;
      // Reconciliation runs HERE, once per activation, rather than on every refresh.
      // This is the out-of-band case it was written for: the account may have changed
      // through VS Code's account preferences, Settings Sync, or a hand-edited file
      // while this window was closed.
      await healOwnerMismatch(
        getSession,
        context.globalState.get<string>(BOUND_ACCOUNT_KEY, "") || null,
        (line) => diagnostics.appendLine(line)
      );
      await refresh();
    })();
  }
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
      return store.resolveFetch({ ok: false, error: resolved.error, rate: EMPTY_RATE }, Date.now(), owner);
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
  } else if (result.error.code === "not-found" && owner.scope === "organization" && credentialToken !== null) {
    // Only on failure, and only for the one case whose message is genuinely
    // ambiguous. A 404 from organization billing is either a role problem or an
    // enhanced-billing problem, and one extra request tells the user which.
    const lookup = await client.getJson(membershipPath(owner), credentialToken).catch(() => null);
    if (lookup !== null) result = { ...result, error: explainOrganizationNotFound(owner, lookup, result.error) };
  }
  return store.resolveFetch(result, Date.now(), owner);
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
  // The OWNER's plan, not the reader's. Asking `GET /user` here reported an
  // organization's usage against a personal plan's allowance whenever it worked at
  // all, and reported nothing at all once the organization binding dropped the
  // `user` scope that `GET /user` needs to include `plan`.
  const planName = await fetchOwnerPlanName(fetchJson, token, owner).catch(() => null);
  // Organization-only, and never fatal: an organization with no Copilot subscription,
  // or a caller who cannot read it, simply leaves the credit allowance unestablished.
  const copilot = await fetchCopilotSubscription(fetchJson, token, owner).catch(() => null);
  return enrichSnapshot(snapshot, { visibility, planName, manualAllowances, copilot }).snapshot;
}

function configuredScope(): BillingOwner["scope"] {
  return vscode.workspace.getConfiguration("githubUsageMonitor").get("billingScope", "user") as BillingOwner["scope"];
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
 * Set while the user has explicitly signed this monitor out.
 *
 * Necessary because log-out cannot end VS Code's GitHub session by design - Copilot
 * shares it - so "signed out" is not derivable from the session's absence. Without a
 * recorded fact, the next silent peek found the surviving session and reconnected.
 */
export const SIGNED_OUT_KEY = "githubUsageMonitor.signedOut";

/**
 * The account label the user actually chose at sign-in.
 *
 * Everything before this recorded nothing and re-derived the identity from whichever
 * session `getSession` happened to return. With ONE GitHub account signed in to VS
 * Code that inference is right by luck; with two it is a coin toss, and every
 * symptom reported on 2026-08-11 falls out of it:
 *
 *   - the reconciler rewrote the billing owner toward whichever account answered,
 *     each rewrite fired a configuration event, and the pair oscillated - a
 *     notification appearing and vanishing several times a second;
 *   - a window reload bound the other account and reported its figures;
 *   - the header's "User" line vanished whenever a silent peek happened to miss,
 *     because the label existed only for as long as one lookup succeeded.
 *
 * A choice the user made is a fact to store, not a value to re-guess on every tick.
 */
export const BOUND_ACCOUNT_KEY = "githubUsageMonitor.boundAccount";

/**
 * Whether an observed session is the one the user bound.
 *
 * Returns true when nothing is recorded yet, so a first run and an upgrade from a
 * version that stored no label both behave exactly as before rather than refusing to
 * reconcile at all.
 */
export function isBoundAccount(observedLogin: string | null, boundLabel: string | null): boolean {
  if (boundLabel === null || boundLabel.trim() === "") return true;
  if (observedLogin === null) return false;
  return observedLogin.trim().toLowerCase() === boundLabel.trim().toLowerCase();
}

/**
 * The state a signed-out monitor shows: the connect prompt, not an error.
 *
 * `not-connected` is the code `isNotConnected` keys the panel's Connect screen off,
 * so this renders the "log in" box rather than a failure notice.
 */
export function signedOutState(): UsageState {
  return {
    state: "empty",
    error: {
      code: "not-connected",
      message: 'Signed out of GitHub Usage Monitor. Choose "Log in" to connect an account again.'
    }
  };
}

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

/**
 * After a sign-in, let the user pick WHICH billing owner to monitor.
 *
 * Binding a session and choosing a billing owner are separate facts, and treating
 * them as one is why switching to a work account produced a permanent
 * `insufficient-role`: the session moved, the owner did not, and an
 * enterprise-managed user generally cannot read its own user-scope billing because
 * the organization owns that relationship.
 *
 * `GET /user/orgs` lists only organizations the caller can see, so the choices are
 * exactly the ones worth offering. A single personal account skips the prompt
 * entirely - a picker with one option is noise.
 */
async function chooseBillingOwnerAfterSignIn(
  getSession: GetSessionLike,
  boundScopes: readonly string[]
): Promise<BillingOwner | null> {
  // The SAME scope set the sign-in just bound, not `[]`. VS Code keys a session by
  // its scope set, so requesting a different set here returned a DIFFERENT session,
  // which could belong to a different account - meaning the organizations offered
  // were not necessarily the organizations of the account the user had just picked.
  // That is the extra "select your user again" step reported 2026-08-11.
  const session = await getSession("github", boundScopes, { createIfNone: false, silent: true }).catch(() => undefined);
  if (session === undefined) return null;
  const login = session.account?.label ?? null;

  const json = async (path: string): Promise<unknown> => {
    const response = await fetch(`https://api.github.com${path}`, {
      headers: {
        Authorization: `Bearer ${session.accessToken}`,
        Accept: "application/vnd.github+json",
        "User-Agent": GITHUB_USER_AGENT
      }
    }).catch(() => undefined);
    return response !== undefined && response.ok ? await response.json().catch(() => undefined) : undefined;
  };

  const orgs = await json("/user/orgs");
  const orgLogins = Array.isArray(orgs)
    ? orgs.map((entry) => (entry as { login?: unknown }).login).filter((value): value is string => typeof value === "string")
    : [];
  if (orgLogins.length === 0) {
    // Personal account with no organizations: the owner IS the account, so record it
    // rather than leaving billingOwner blank and re-detecting it on every fetch.
    if (login === null) return null;
    await writeOwner("user", login);
    return { scope: "user", name: login };
  }

  const picked = await vscode.window.showQuickPick(
    [
      ...(login === null ? [] : [{ label: login, description: "Personal account", scope: "user" as const, name: login }]),
      ...orgLogins.map((name) => ({ label: name, description: "Organization", scope: "organization" as const, name }))
    ],
    {
      title: "GitHub Usage Monitor: which billing owner should this monitor report?",
      placeHolder: "A work account's billing usually belongs to its organization, not to you"
    }
  );
  if (picked === undefined) return null;
  await writeOwner(picked.scope, picked.name);
  return { scope: picked.scope, name: picked.name };
}

/**
 * Re-binds the session at the scope the CHOSEN owner requires, or does nothing.
 *
 * The owner is only known after the picker, and the required scope follows from the
 * owner rather than from the level that happened to be configured beforehand. Since
 * `user` and `repo` share no members, picking an organization after a personal
 * sign-in previously left the session holding `user` while the organization billing
 * endpoint accepts only `admin:org` or `repo`.
 *
 * Returns null when nothing changed, so the caller keeps the binding it already has
 * rather than replacing a good one with a failed re-bind.
 */
async function ensureScopeForOwner(
  getSession: GetSessionLike,
  owner: BillingOwner,
  current: MonitorBinding
): Promise<MonitorBinding | null> {
  const needed = firstScopeCandidate(owner);
  const held = new Set(current.scopes);
  if (needed.every((scope) => held.has(scope))) return null;
  const session = await getSession("github", needed, { createIfNone: true }).catch(() => undefined);
  return session === undefined ? null : bindingFromSession(session);
}

/**
 * Set when this window is running superseded code, which makes it defer.
 *
 * Global configuration writes reach every window, so a window running old code can
 * drive a loop in windows running new code. A superseded window keeps displaying and
 * stops writing - deferring to whichever window is current.
 */
let deferToNewerWindow = false;

export function setDeferToNewerWindow(value: boolean): void {
  deferToNewerWindow = value;
}

async function writeOwner(scope: "user" | "organization", name: string): Promise<void> {
  // A superseded window must not write. This is the containment for the cross-window
  // loop: whatever its old code decides, it cannot broadcast that decision.
  if (deferToNewerWindow) return;
  // Guarded across BOTH writes. There is no transaction in the settings store, and a
  // reconciliation that observes the half-written pair undoes the user's choice - see
  // the guard's own comment for the failure this prevents.
  beginOwnerWrite();
  try {
    const config = vscode.workspace.getConfiguration("githubUsageMonitor");
    await config.update("billingScope", scope, vscode.ConfigurationTarget.Global);
    await config.update("billingOwner", name, vscode.ConfigurationTarget.Global);
  } finally {
    endOwnerWrite();
  }
}

/**
 * Corrects a stale scope/owner pair before it is used.
 *
 * Runs on every refresh rather than only after an explicit sign-in, because the
 * account can change by routes the extension never sees: VS Code's own
 * "Manage Extension Account Preferences", Settings Sync, or a hand-edited settings
 * file. Reconciling only inside the logIn command left every other route to fail
 * with a permanent `insufficient-role`.
 */
/**
 * Automatic owner writes made this session, and the ceiling on them.
 *
 * A circuit breaker, not a guess. Every previous fix argued that a particular cycle
 * could no longer happen, and each argument was wrong in a way only the user's
 * machine revealed. This bounds the blast radius of being wrong again: after a small
 * number of automatic corrections the reconciler goes inert for the session and says
 * so, so the worst remaining outcome is a stale setting rather than an unusable
 * editor.
 */
const MAX_AUTOMATIC_OWNER_WRITES = 2;
let automaticOwnerWrites = 0;
let reconciliationDisabled = false;

/** Reset when the user explicitly signs in, which is a fresh reconciliation question. */
export function resetReconciliationBreaker(): void {
  automaticOwnerWrites = 0;
  reconciliationDisabled = false;
  lastReconcileReason = null;
  offeredReconciliation = false;
}

async function healOwnerMismatch(
  getSession: GetSessionLike,
  boundLabel: string | null = null,
  trace: (line: string) => void = () => undefined
): Promise<void> {
  if (reconciliationDisabled) return;
  // A superseded window defers entirely: it neither corrects nor announces.
  if (deferToNewerWindow) {
    trace("reconcile: skipped, this window runs superseded code and defers to a reloaded one");
    return;
  }
  // Never judge a pair that is still being written. This healer is the only thing
  // that can silently overrule an explicit user choice, so it yields rather than
  // races.
  if (ownerWriteInFlight()) return;
  const config = vscode.workspace.getConfiguration("githubUsageMonitor");
  const scope = config.get<BillingOwner["scope"]>("billingScope", "user");
  const owner = config.get<string>("billingOwner", "");

  // Ask for the session that MATTERS for this owner, not for scopes `[]`.
  //
  // VS Code keys a session by its scope set, so once two sessions exist - a personal
  // one holding `user` and a work one holding `repo, read:org` - a `[]` request can
  // return either, and which one it returns is not stable. The reconciler then
  // "corrected" the owner toward whichever account came back, the write fired a
  // configuration event, the refresh reconciled again against the OTHER session, and
  // the pair oscillated. Observed 2026-08-11 as a notification appearing and
  // disappearing several times a second.
  const session = await getSession(
    "github",
    firstScopeCandidate({ scope, name: owner === "" ? "pending" : owner }),
    { createIfNone: false, silent: true }
  ).catch(() => undefined);
  const login = session?.account?.label ?? null;
  // No session for THIS owner's scope set is not evidence of a mismatch. Reconciling
  // against an unrelated session is what caused the oscillation above.
  if (login === null) return;

  // And neither is a session belonging to a DIFFERENT account than the one the user
  // bound. Scoping the request was not enough: both of this user's accounts hold a
  // `user`-scoped session, so the scope set alone does not identify the account, and
  // the oscillation survived. The recorded choice does identify it.
  if (!isBoundAccount(login, boundLabel)) return;

  const result = reconcileOwner({ scope, owner, login });
  // The trace that ends the guessing. Every input and every verdict, in the
  // extension's own output channel, so a reproduction produces evidence instead of
  // another round of inference.
  trace(`reconcile: scope=${scope} owner=${owner || "(empty)"} login=${login} bound=${boundLabel ?? "(none)"} -> kind=${result.kind} changed=${result.changed} safeToApply=${result.safeToApply}`);
  if (!result.changed) return;

  if (result.safeToApply) {
    if (automaticOwnerWrites >= MAX_AUTOMATIC_OWNER_WRITES) {
      reconciliationDisabled = true;
      trace(`reconcile: breaker tripped after ${automaticOwnerWrites} automatic writes; reconciliation is off for this session`);
      void vscode.window.showWarningMessage(
        "GitHub Usage Monitor: the billing owner kept being corrected, so automatic correction is off for this window. Set the account explicitly with Switch, or reload."
      );
      return;
    }
    automaticOwnerWrites += 1;
    // Self-terminating corrections only. Through the same guarded writer the picker
    // uses: writing the pair unguarded here reopened the window `writeOwner` closes.
    await writeOwner(result.scope as "user" | "organization", result.owner);
    if (lastReconcileReason === result.reason) return;
    lastReconcileReason = result.reason;
    void vscode.window.showInformationMessage(`GitHub Usage Monitor: ${result.reason}`);
    return;
  }

  // OFFERED, never applied - and offered at most once per session.
  //
  // This is the branch that would not stop flickering. Applying it wrote
  // configuration, the write fired a change event, the event refreshed, the refresh
  // reconciled against whichever of two signed-in accounts answered next, and round
  // it went. Nothing is written here, so there is no event, so there is no cycle -
  // the loop is broken structurally rather than by another guard on the input.
  if (offeredReconciliation) return;
  offeredReconciliation = true;
  const APPLY = "Update owner";
  const action = await vscode.window.showInformationMessage(`GitHub Usage Monitor: ${result.reason}`, APPLY, "Keep current");
  if (action === APPLY) await writeOwner(result.scope as "user" | "organization", result.owner);
}

/** The last correction announced, so an unchanged verdict is not re-announced. */
let lastReconcileReason: string | null = null;

/**
 * Whether the offer-only correction has been put to the user this session.
 *
 * One offer, ever. A prompt that reappears on a timer is the same defect as the
 * notification loop wearing a button.
 */
let offeredReconciliation = false;
