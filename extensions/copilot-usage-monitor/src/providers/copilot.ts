import * as vscode from "vscode";
import type { PersonalUsage, QuotaRow } from "../types";
import { FetchLike, githubApiUrl, githubGet } from "./githubApi";
import type { CredentialResult, ProviderFetchError, ProviderFetchResult, UsageProvider } from "./types";

/**
 * The personal Copilot provider. It reads the GitHub session VS Code holds for
 * the account the user pinned for this extension, and the quota GitHub serves
 * at the undocumented `copilot_internal/user` endpoint (the one the Copilot
 * extension's own usage popup reads). Settled in decision file v4.13.7,
 * Copilot usage monitor items (1) and (1b).
 *
 * Account choice is VS Code's: `getSession` is never passed an `account`, so
 * the extension's stored account preference decides. Nothing here reads git
 * configuration, a repository remote, or another tool's login.
 */
export const GITHUB_PROVIDER_ID = "github";
const USER_PATH = "/copilot_internal/user";

/**
 * Background refresh: an empty scope list matches a session of any scopes, so
 * the session the Copilot extension created is found without a prompt.
 */
export const BACKGROUND_SCOPES: readonly string[] = [];
/** Interactive sign-in: the narrowest named scope, used only on the user's click. */
export const SIGN_IN_SCOPES: readonly string[] = ["read:user"];

/** The slice of `vscode.authentication` the provider uses, so tests can stub it. */
export interface GitHubAuthentication {
  getSession(
    providerId: string,
    scopes: readonly string[],
    options: vscode.AuthenticationGetSessionOptions,
  ): Thenable<vscode.AuthenticationSession | undefined>;
  getAccounts?(providerId: string): Thenable<readonly vscode.AuthenticationSessionAccountInformation[]>;
}

const QUOTA_ORDER = ["premium_interactions", "chat", "completions"];
const QUOTA_LABELS: Record<string, string> = {
  premium_interactions: "Premium requests",
  chat: "Chat",
  completions: "Code completions",
};
/** Two served percentages further apart than this are treated as disagreeing. */
const CROSS_CHECK_TOLERANCE = 1;

function asRecord(value: unknown): Record<string, unknown> | null {
  return value != null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function finite(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function clampPercent(value: number): number {
  return Math.min(100, Math.max(0, value));
}

function quotaLabel(id: string): string {
  return QUOTA_LABELS[id] ?? id.replace(/_+/g, " ").replace(/^\w/, (c) => c.toUpperCase());
}

/**
 * Map one `quota_snapshots` entry to a row, or null when GitHub serves no limit
 * for it. A quota gives a percentage only when `unlimited` is false, `has_quota`
 * is true, and `entitlement` is above 0: an unlimited seat's
 * `percent_remaining: 100` is a constant, not a reading.
 */
export function mapQuota(id: string, raw: unknown): QuotaRow | null {
  const q = asRecord(raw);
  if (!q || q.unlimited !== false || q.has_quota !== true) {
    return null;
  }
  const entitlement = finite(q.entitlement);
  if (entitlement == null || entitlement <= 0) {
    return null;
  }
  const remaining = finite(q.remaining) ?? finite(q.quota_remaining);
  const percentRemaining = finite(q.percent_remaining);
  const served = percentRemaining != null ? clampPercent(100 - percentRemaining) : undefined;
  const computed =
    remaining != null ? clampPercent(((entitlement - remaining) / entitlement) * 100) : undefined;
  let percent: number;
  if (served != null && computed != null) {
    // Both come from GitHub. When they disagree, show the higher used figure so
    // a usage warning errs toward early rather than late.
    percent = Math.abs(served - computed) > CROSS_CHECK_TOLERANCE ? Math.max(served, computed) : served;
  } else if (served != null) {
    percent = served;
  } else if (computed != null) {
    percent = computed;
  } else {
    return null;
  }
  return {
    id,
    label: quotaLabel(id),
    percent,
    entitlement,
    remaining: remaining ?? entitlement * (1 - percent / 100),
  };
}

function planLabel(payload: Record<string, unknown>): string {
  const sku = typeof payload.access_type_sku === "string" ? payload.access_type_sku : "";
  const plan = typeof payload.copilot_plan === "string" ? payload.copilot_plan : "";
  if (sku === "free_limited_copilot") {
    return "Copilot Free";
  }
  if (plan === "business") {
    return "Copilot Business";
  }
  if (plan === "enterprise") {
    return "Copilot Enterprise";
  }
  if (plan === "individual") {
    return "Copilot individual plan";
  }
  return "GitHub Copilot";
}

function resetOf(payload: Record<string, unknown>): number | null {
  if (typeof payload.quota_reset_date_utc === "string") {
    const parsed = Date.parse(payload.quota_reset_date_utc);
    if (!Number.isNaN(parsed)) {
      return parsed;
    }
  }
  if (typeof payload.quota_reset_date === "string" && /^\d{4}-\d{2}-\d{2}$/.test(payload.quota_reset_date)) {
    const parsed = Date.parse(`${payload.quota_reset_date}T00:00:00Z`);
    if (!Number.isNaN(parsed)) {
      return parsed;
    }
  }
  return null;
}

/**
 * Map a `copilot_internal/user` payload to the personal figure. Returns null
 * only when `quota_snapshots` is missing, which the fetcher reports as
 * `usage-unavailable`. Unknown fields are ignored; the login, ids, and
 * organization list are never read.
 */
export function mapCopilotUser(raw: unknown): PersonalUsage | null {
  const payload = asRecord(raw);
  const snapshots = payload ? asRecord(payload.quota_snapshots) : null;
  if (!payload || !snapshots) {
    return null;
  }
  const ids = Object.keys(snapshots).sort((a, b) => {
    const ia = QUOTA_ORDER.indexOf(a);
    const ib = QUOTA_ORDER.indexOf(b);
    return (ia === -1 ? QUOTA_ORDER.length : ia) - (ib === -1 ? QUOTA_ORDER.length : ib) || a.localeCompare(b);
  });
  const quotas: QuotaRow[] = [];
  let creditsUsed = 0;
  for (const id of ids) {
    creditsUsed += finite(asRecord(snapshots[id])?.credits_used) ?? 0;
    const row = mapQuota(id, snapshots[id]);
    if (row) {
      quotas.push(row);
    }
  }
  const primary =
    QUOTA_ORDER.map((id) => quotas.find((q) => q.id === id)).find((q) => q != null) ?? null;
  return { planLabel: planLabel(payload), quotas, primary, creditsUsed, resetsAt: resetOf(payload) };
}

function errorFor(status: number, statusText: string, rateLimited: boolean): ProviderFetchError {
  if (rateLimited) {
    return { code: "rate-limited", statusCode: status, statusText };
  }
  if (status === 401) {
    return { code: "token-invalid", statusCode: status, statusText };
  }
  if (status >= 500) {
    return { code: "api-error", statusCode: status, statusText };
  }
  return { code: "usage-unavailable", statusCode: status, statusText };
}

export class CopilotUsageProvider implements UsageProvider {
  readonly id = "copilot" as const;
  readonly displayName = "GitHub Copilot";

  constructor(
    private readonly auth: GitHubAuthentication = vscode.authentication,
    private readonly fetchImpl: FetchLike = (input, init) => fetch(input, init),
  ) {}

  /** The pinned account's session, found silently. Never prompts. */
  private async silentSession(): Promise<vscode.AuthenticationSession | undefined> {
    try {
      return await this.auth.getSession(GITHUB_PROVIDER_ID, BACKGROUND_SCOPES, {
        createIfNone: false,
        silent: true,
      });
    } catch {
      return undefined;
    }
  }

  /** With several accounts signed in and no preference, a silent request picks none. */
  private async severalAccounts(): Promise<boolean> {
    try {
      const accounts = (await this.auth.getAccounts?.(GITHUB_PROVIDER_ID)) ?? [];
      return accounts.length > 1;
    } catch {
      return false;
    }
  }

  async readCredential(): Promise<CredentialResult> {
    const session = await this.silentSession();
    if (session) {
      return { ok: true };
    }
    return { ok: false, reason: (await this.severalAccounts()) ? "choose-account" : "missing" };
  }

  async fetchUsage(): Promise<ProviderFetchResult<PersonalUsage>> {
    const session = await this.silentSession();
    if (!session) {
      const code = (await this.severalAccounts()) ? "choose-account" : "no-credentials";
      return { success: false, error: { code } };
    }
    const response = await githubGet(
      githubApiUrl(USER_PATH),
      `token ${session.accessToken}`,
      { Accept: "application/json" },
      this.fetchImpl,
    );
    if (response.kind === "network-error") {
      return { success: false, error: { code: "network-error" } };
    }
    if (response.status < 200 || response.status >= 300) {
      return { success: false, error: errorFor(response.status, response.statusText, response.rateLimited) };
    }
    const usage = response.parsed ? mapCopilotUser(response.body) : null;
    if (!usage) {
      return { success: false, error: { code: "usage-unavailable" } };
    }
    return { success: true, data: usage };
  }
}

/** User-initiated sign-in or account choice. VS Code stores the chosen account as this extension's preference. */
export async function signIn(auth: GitHubAuthentication = vscode.authentication): Promise<boolean> {
  try {
    const session = await auth.getSession(GITHUB_PROVIDER_ID, SIGN_IN_SCOPES, { createIfNone: true });
    return session != null;
  } catch {
    return false;
  }
}

/** User-initiated account switch: clear the stored preference so VS Code asks again. */
export async function switchAccount(auth: GitHubAuthentication = vscode.authentication): Promise<boolean> {
  try {
    const session = await auth.getSession(GITHUB_PROVIDER_ID, SIGN_IN_SCOPES, {
      clearSessionPreference: true,
      createIfNone: true,
    });
    return session != null;
  } catch {
    return false;
  }
}
