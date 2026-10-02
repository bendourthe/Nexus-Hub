import * as vscode from "vscode";
import { logOnce } from "../log";
import type { ApproximateReason, ModelCredits, OrganizationUsage } from "../types";
import { CONFIG_SECTION } from "../types";
import { nextMonthlyResetAt } from "../usageStore";
import { FetchLike, githubApiUrl, githubGet, GitHubResponse } from "./githubApi";
import { ORG_ACCESS_MESSAGE } from "./errors";
import type { OrganizationProvider, ProviderFetchError, ProviderFetchResult } from "./types";

/**
 * The organization pool provider. An owner or billing manager connects once by
 * pasting a read-only fine-grained token, which is kept only in VS Code secret
 * storage (`context.secrets`) under {@link ORG_TOKEN_SECRET_KEY} and sent only
 * to api.github.com. Figures: decision file v4.13.7, Copilot usage monitor
 * items (2) and (3).
 */
export const ORG_TOKEN_SECRET_KEY = "copilotUsage.organizationToken";

/** GitHub's documented headers for the billing endpoints. */
const API_HEADERS = {
  Accept: "application/vnd.github+json",
  "X-GitHub-Api-Version": "2026-03-10",
};

/** The only SKU counted toward the pool (decision file item 2). */
export const POOL_SKU = "Copilot AI Credits";

/** Included AI credits per seat per month, as GitHub publishes them. */
export const CREDITS_PER_SEAT = { business: 1_900, enterprise: 3_900 } as const;

/** A GitHub organization login: alphanumerics and single hyphens, at most 39 characters. */
const ORG_LOGIN = /^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$/;

export function isValidOrganizationLogin(value: string): boolean {
  return ORG_LOGIN.test(value);
}

/** Exactly which token to create, shown in the password input box. */
export const TOKEN_PROMPT =
  "Paste a fine-grained personal access token. Resource owner: the organization. " +
  "Organization permissions: Administration (read-only) and GitHub Copilot Business (read-only). " +
  "Repository access: public repositories (read-only). Pick a short expiry. " +
  "The token is stored in VS Code secret storage and sent only to api.github.com.";

function asRecord(value: unknown): Record<string, unknown> | null {
  return value != null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function count(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) && value > 0 ? value : 0;
}

/**
 * Map `GET /orgs/{org}/copilot/billing` and
 * `GET /organizations/{org}/settings/billing/ai_credit/usage` to the pool.
 *
 * Used is the unrounded sum of `discountQuantity` over line items whose
 * `product` is `Copilot`, `sku` is `Copilot AI Credits`, and `unitType` is
 * `ai-credits`, with a finite, non-negative quantity; any other line item is
 * left out and logged once. Total is `seat_breakdown.total` times the published
 * rate for `plan_type`. The total is approximate when a seat was added this
 * cycle (proration is unpublished) or a seat is pending cancellation. Returns
 * null when the usage payload has no `usageItems` array, or when its
 * `timePeriod` is missing or names another year or month than `nowMs` (the
 * month that was requested), so a stale or misrouted report is never shown.
 */
export function mapOrganizationUsage(
  billingRaw: unknown,
  usageRaw: unknown,
  nowMs = Date.now(),
): OrganizationUsage | null {
  const usage = asRecord(usageRaw);
  if (!usage || !Array.isArray(usage.usageItems)) {
    return null;
  }
  const period = asRecord(usage.timePeriod);
  const requested = new Date(nowMs);
  if (
    !period ||
    period.year !== requested.getUTCFullYear() ||
    period.month !== requested.getUTCMonth() + 1
  ) {
    logOnce("org-period-mismatch", "Ignored an AI credit report for a different month than the one requested.");
    return null;
  }
  let used = 0;
  let excluded = 0;
  const byModel = new Map<string, number>();
  for (const item of usage.usageItems) {
    const rec = asRecord(item);
    const quantity = rec?.discountQuantity;
    if (
      !rec ||
      rec.product !== "Copilot" ||
      rec.sku !== POOL_SKU ||
      rec.unitType !== "ai-credits" ||
      typeof quantity !== "number" ||
      !Number.isFinite(quantity) ||
      quantity < 0
    ) {
      excluded += 1;
      continue;
    }
    used += quantity;
    const model = typeof rec.model === "string" && rec.model ? rec.model : "Other";
    byModel.set(model, (byModel.get(model) ?? 0) + quantity);
  }
  if (excluded > 0) {
    logOnce("org-excluded-items", `Left ${excluded} usage line item(s) out of the pool: not Copilot AI credits, or not a valid quantity.`);
  }

  const billing = asRecord(billingRaw);
  const seatsRec = asRecord(billing?.seat_breakdown);
  const seats = count(seatsRec?.total);
  const rawPlan = billing?.plan_type;
  const planType = rawPlan === "business" || rawPlan === "enterprise" ? rawPlan : "unknown";
  const creditsPerSeat = planType === "unknown" ? 0 : CREDITS_PER_SEAT[planType];
  const total = seats * creditsPerSeat;

  const approximateReasons: ApproximateReason[] = [];
  if (count(seatsRec?.added_this_cycle) > 0) {
    approximateReasons.push("seat-added");
  }
  if (count(seatsRec?.pending_cancellation) > 0) {
    approximateReasons.push("pending-cancellation");
  }

  const models: ModelCredits[] = [...byModel.entries()]
    .map(([model, value]) => ({ model, used: value }))
    .sort((a, b) => b.used - a.used);

  return {
    used,
    total,
    percent: total > 0 ? Math.min(100, (used / total) * 100) : null,
    seats,
    planType,
    creditsPerSeat,
    approximate: approximateReasons.length > 0,
    approximateReasons,
    resetsAt: nextMonthlyResetAt(nowMs),
    models,
  };
}

/** The configured organization login, trimmed, or "" when none is set. */
export function configuredOrganization(): string {
  return (vscode.workspace.getConfiguration(CONFIG_SECTION).get<string>("organization", "") ?? "").trim();
}

function billingUrl(org: string): URL {
  return githubApiUrl(`/orgs/${encodeURIComponent(org)}/copilot/billing`);
}

function usageUrl(org: string, nowMs: number): URL {
  const now = new Date(nowMs);
  return githubApiUrl(`/organizations/${encodeURIComponent(org)}/settings/billing/ai_credit/usage`, {
    year: String(now.getUTCFullYear()),
    month: String(now.getUTCMonth() + 1),
  });
}

function failure(response: GitHubResponse): ProviderFetchError | null {
  if (response.kind === "network-error") {
    return { code: "network-error" };
  }
  const { status, statusText } = response;
  if (response.rateLimited) {
    return { code: "rate-limited", statusCode: status, statusText };
  }
  if (status === 401) {
    return { code: "org-token-rejected", statusCode: status, statusText };
  }
  if (status === 403 || status === 404) {
    return { code: "org-access-denied", statusCode: status, statusText };
  }
  if (status < 200 || status >= 300) {
    return { code: status >= 500 ? "api-error" : "usage-unavailable", statusCode: status, statusText };
  }
  if (!response.parsed) {
    return { code: "usage-unavailable" };
  }
  return null;
}

export class CopilotOrganizationProvider implements OrganizationProvider {
  constructor(
    private readonly secrets: vscode.SecretStorage,
    private readonly fetchImpl: FetchLike = (input, init) => fetch(input, init),
  ) {}

  isActive(): boolean {
    return configuredOrganization() !== "";
  }

  async fetchUsage(nowMs = Date.now()): Promise<ProviderFetchResult<OrganizationUsage>> {
    const org = configuredOrganization();
    if (!isValidOrganizationLogin(org)) {
      return { success: false, error: { code: "org-not-connected" } };
    }
    let token: string | undefined;
    try {
      token = await this.secrets.get(ORG_TOKEN_SECRET_KEY);
    } catch {
      token = undefined;
    }
    if (!token) {
      return { success: false, error: { code: "org-not-connected" } };
    }
    const authorization = `Bearer ${token}`;

    const billing = await githubGet(billingUrl(org), authorization, API_HEADERS, this.fetchImpl);
    const billingError = failure(billing);
    if (billingError) {
      return this.fail(billingError);
    }
    const usage = await githubGet(usageUrl(org, nowMs), authorization, API_HEADERS, this.fetchImpl);
    const usageError = failure(usage);
    if (usageError) {
      return this.fail(usageError);
    }
    const mapped = mapOrganizationUsage(
      billing.kind === "response" ? billing.body : undefined,
      usage.kind === "response" ? usage.body : undefined,
      nowMs,
    );
    if (!mapped) {
      return { success: false, error: { code: "usage-unavailable" } };
    }
    return { success: true, data: mapped };
  }

  /** An expired or revoked token is removed so the next refresh does not resend it. */
  private async fail(error: ProviderFetchError): Promise<ProviderFetchResult<OrganizationUsage>> {
    if (error.code === "org-token-rejected") {
      try {
        await this.secrets.delete(ORG_TOKEN_SECRET_KEY);
      } catch {
        // The next refresh reports the same rejection; nothing else to do.
      }
    }
    return { success: false, error };
  }
}

/** What happened when the user ran Connect Organization. */
export type ConnectOutcome = "connected" | "cancelled" | "rejected" | "access-denied" | "unreachable";

/**
 * Ask for the organization login and a token, verify the token with one call to
 * `GET /orgs/{org}/copilot/billing`, and only then store it in secret storage
 * and the login in `copilotUsage.organization`. A failed check stores nothing.
 */
export async function connectOrganization(
  secrets: vscode.SecretStorage,
  fetchImpl: FetchLike = (input, init) => fetch(input, init),
): Promise<ConnectOutcome> {
  const org = await vscode.window.showInputBox({
    title: "Connect Organization (1 of 2)",
    prompt: "The login of the GitHub organization whose shared Copilot pool to show.",
    value: configuredOrganization(),
    ignoreFocusOut: true,
    validateInput: (value) =>
      isValidOrganizationLogin(value.trim()) ? undefined : "Enter an organization login, for example my-org.",
  });
  if (org === undefined) {
    return "cancelled";
  }
  const login = org.trim();
  const token = await vscode.window.showInputBox({
    title: "Connect Organization (2 of 2)",
    prompt: TOKEN_PROMPT,
    password: true,
    ignoreFocusOut: true,
    validateInput: (value) => (value.trim() ? undefined : "Paste the token to continue."),
  });
  if (token === undefined || !token.trim()) {
    return "cancelled";
  }

  const check = await githubGet(billingUrl(login), `Bearer ${token.trim()}`, API_HEADERS, fetchImpl);
  const error = failure(check);
  if (error) {
    const outcome: ConnectOutcome =
      error.code === "org-token-rejected"
        ? "rejected"
        : error.code === "org-access-denied"
          ? "access-denied"
          : "unreachable";
    const message =
      outcome === "rejected"
        ? "GitHub rejected the token. Check that it has not expired and was created for this organization, then try again."
        : outcome === "access-denied"
          ? ORG_ACCESS_MESSAGE
          : "Could not verify the token with GitHub. Check your connection and try again.";
    void vscode.window.showWarningMessage(`Copilot Usage: ${message}`);
    return outcome;
  }

  await secrets.store(ORG_TOKEN_SECRET_KEY, token.trim());
  await vscode.workspace
    .getConfiguration(CONFIG_SECTION)
    .update("organization", login, vscode.ConfigurationTarget.Global);
  void vscode.window.showInformationMessage("Copilot Usage: organization connected. The pool appears on the next refresh.");
  return "connected";
}

/**
 * Delete the stored token and clear the organization setting from every scope
 * VS Code lets an extension write. The setting is application-scoped, but a
 * value written to a workspace file before that is cleared too.
 */
export async function disconnectOrganization(secrets: vscode.SecretStorage): Promise<void> {
  await secrets.delete(ORG_TOKEN_SECRET_KEY);
  const config = vscode.workspace.getConfiguration(CONFIG_SECTION);
  for (const target of [
    vscode.ConfigurationTarget.Global,
    vscode.ConfigurationTarget.Workspace,
    vscode.ConfigurationTarget.WorkspaceFolder,
  ]) {
    try {
      await config.update("organization", undefined, target);
    } catch {
      // No workspace or folder is open for this scope; nothing to clear there.
    }
  }
}
