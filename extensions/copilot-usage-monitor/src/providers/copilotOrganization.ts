import * as vscode from "vscode";
import { log, logOnce } from "../log";
import type { ApproximateReason, ModelCredits, OrganizationUsage } from "../types";
import { CONFIG_SECTION } from "../types";
import { nextMonthlyResetAt } from "../usageStore";
import { fetchSeatOrganizations, GITHUB_PROVIDER_ID, GitHubAuthentication, SeatOrganization } from "./copilot";
import { FetchLike, githubApiUrl, githubGet, GitHubResponse } from "./githubApi";
import type { OrganizationProvider, ProviderFetchError, ProviderFetchResult } from "./types";

/**
 * The organization pool provider. An owner connects once (v4.13.8 Phase 6):
 * first token-free, through the read-only `read:org` scope on VS Code's own
 * GitHub sign-in, recorded by a marker under {@link ORG_ROUTE_SECRET_KEY}; and
 * only when GitHub refuses that, with a read-only fine-grained token kept in VS
 * Code secret storage under {@link ORG_TOKEN_SECRET_KEY}. Either credential is
 * sent only to api.github.com. Figures: decision file v4.13.7, Copilot usage
 * monitor items (2) and (3), and its v4.13.8 amendment.
 */
export const ORG_TOKEN_SECRET_KEY = "copilotUsage.organizationToken";
/** Marks a token-free connection; holds no credential. */
export const ORG_ROUTE_SECRET_KEY = "copilotUsage.organizationRoute";
const ROUTE_SESSION = "vscode-session";

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

/** Shown in the password input box, after GitHub's pre-filled page has opened. */
export const TOKEN_PROMPT =
  "Paste the token you copied from GitHub. " +
  "It is stored in VS Code secret storage and sent only to api.github.com.";

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
    private readonly auth: GitHubAuthentication = vscode.authentication,
  ) {}

  /**
   * The stored token, else the token-free session found silently (never a
   * prompt: `read:org` was granted on Connect), else none.
   */
  private async credential(): Promise<string | undefined> {
    const route = await organizationRoute(this.secrets);
    try {
      if (route === "token") {
        return await this.secrets.get(ORG_TOKEN_SECRET_KEY);
      }
      if (route === "vscode-session") {
        const session = await this.auth.getSession(GITHUB_PROVIDER_ID, ORG_READ_SCOPES, { createIfNone: false, silent: true });
        return session?.accessToken;
      }
    } catch {
      return undefined;
    }
    return undefined;
  }

  isActive(): boolean {
    return configuredOrganization() !== "";
  }

  async fetchUsage(nowMs = Date.now()): Promise<ProviderFetchResult<OrganizationUsage>> {
    const org = configuredOrganization();
    if (!isValidOrganizationLogin(org)) {
      return { success: false, error: { code: "org-not-connected" } };
    }
    const token = await this.credential();
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

  /** An expired or revoked credential is forgotten so the next refresh does not resend it. */
  private async fail(error: ProviderFetchError): Promise<ProviderFetchResult<OrganizationUsage>> {
    if (error.code === "org-token-rejected") {
      try {
        await this.secrets.delete(ORG_TOKEN_SECRET_KEY);
        await this.secrets.delete(ORG_ROUTE_SECRET_KEY);
      } catch {
        // The next refresh reports the same rejection; nothing else to do.
      }
    }
    return { success: false, error };
  }
}

/** What happened when the user ran Connect Organization. */
export type ConnectOutcome = "connected" | "cancelled" | "rejected" | "access-denied" | "unreachable";

/** How the organization is connected, as Disconnect reports it. */
export type OrganizationRoute = "vscode-session" | "token" | "none";

/** The modal and quick-pick answers Connect offers, exported for tests. */
export const CONNECT_CHOICE = "Connect";
export const OTHER_ORGANIZATION = "Other organization";
export const OPEN_GITHUB = "Open GitHub";
export const OPEN_ORGANIZATION_SETTINGS = "Open organization settings";

/** The read-only scope the token-free route asks VS Code's GitHub sign-in for. */
export const ORG_READ_SCOPES: readonly string[] = ["read:org"];

/**
 * GitHub's pre-filled fine-grained token page (documented URL parameters):
 * the name, description, resource owner, the longest expiry GitHub allows (366
 * days), and the two read-only organization permissions. Nothing else.
 */
export function tokenCreationUrl(org: string): string {
  const params = new URLSearchParams({
    name: "Copilot Usage Monitor",
    description: "Read-only Copilot AI-credit pool for the VS Code Copilot Usage Monitor",
    target_name: org,
    expires_in: "366",
    organization_administration: "read",
    organization_copilot_seat_management: "read",
  });
  return `https://github.com/settings/personal-access-tokens/new?${params.toString()}`;
}

/** The organization's settings, where an owner approves a pending token request. */
export function organizationSettingsUrl(org: string): string {
  return `https://github.com/organizations/${encodeURIComponent(org)}/settings`;
}

/** Plain-words fixes for a token GitHub refused (403 or 404). */
export const TOKEN_FIX_MESSAGE =
  "GitHub refused the token for this organization. On the token's GitHub page, check that: " +
  "the resource owner is the organization, not your personal account; " +
  "Administration and GitHub Copilot Business are both set to read-only; " +
  "and, if the organization requires approval, an owner has approved it under the organization's Settings, Personal access tokens, Pending requests.";

/** Which route is connected: a stored token, the token-free marker, or none. */
export async function organizationRoute(secrets: vscode.SecretStorage): Promise<OrganizationRoute> {
  try {
    if (await secrets.get(ORG_TOKEN_SECRET_KEY)) {
      return "token";
    }
    return (await secrets.get(ORG_ROUTE_SECRET_KEY)) === ROUTE_SESSION ? "vscode-session" : "none";
  } catch {
    return "none";
  }
}

/** Check both pool endpoints with one credential; both status codes are kept for the log. */
async function checkBothEndpoints(
  org: string,
  authorization: string,
  fetchImpl: FetchLike,
  nowMs: number,
): Promise<{ error: ProviderFetchError | null; statuses: string }> {
  const billing = await githubGet(billingUrl(org), authorization, API_HEADERS, fetchImpl);
  const usage = await githubGet(usageUrl(org, nowMs), authorization, API_HEADERS, fetchImpl);
  const status = (r: GitHubResponse): string => (r.kind === "network-error" ? "network error" : String(r.status));
  return {
    error: failure(billing) ?? failure(usage),
    statuses: `copilot/billing ${status(billing)}, ai_credit/usage ${status(usage)}`,
  };
}

/** Typed entry, used when the seat lists no organization or the user picks another one. */
async function typeOrganization(reason: string): Promise<string | undefined> {
  const org = await vscode.window.showInputBox({
    title: "Connect Organization",
    prompt: `${reason}Type the login of the GitHub organization whose shared Copilot pool to show.`,
    value: configuredOrganization(),
    ignoreFocusOut: true,
    validateInput: (value) =>
      isValidOrganizationLogin(value.trim()) ? undefined : "Enter an organization login, for example my-org.",
  });
  return org === undefined ? undefined : org.trim();
}

/** Explains typed entry when the seat lists no organization. */
export const NO_SEAT_ORGANIZATION = "This GitHub account's Copilot seat lists no organization. ";

/**
 * Pick the organization from the seat's own list: one is preselected and
 * confirmed, several are offered as `name (login)`, none falls back to typing.
 */
export async function chooseOrganization(orgs: readonly SeatOrganization[]): Promise<string | undefined> {
  const label = (o: SeatOrganization): string => (o.name !== o.login ? `${o.name} (${o.login})` : o.login);
  if (orgs.length === 0) {
    return typeOrganization(NO_SEAT_ORGANIZATION);
  }
  if (orgs.length === 1) {
    const answer = await vscode.window.showInformationMessage(
      `Connect ${label(orgs[0])}? An organization owner can show the percentage of its shared Copilot pool.`,
      { modal: true },
      CONNECT_CHOICE,
      OTHER_ORGANIZATION,
    );
    if (answer === CONNECT_CHOICE) {
      return orgs[0].login;
    }
    return answer === OTHER_ORGANIZATION ? typeOrganization("") : undefined;
  }
  const picked = await vscode.window.showQuickPick(
    [...orgs.map((o) => ({ label: label(o), login: o.login })), { label: OTHER_ORGANIZATION, login: "" }],
    { title: "Connect Organization", placeHolder: "Which organization's Copilot pool should the status bar show?" },
  );
  if (!picked) {
    return undefined;
  }
  return picked.login || typeOrganization("");
}

/** Store the chosen route, and the login in `copilotUsage.organization`. */
async function saveConnection(secrets: vscode.SecretStorage, org: string, token: string | null): Promise<void> {
  if (token) {
    await secrets.store(ORG_TOKEN_SECRET_KEY, token);
    await secrets.delete(ORG_ROUTE_SECRET_KEY);
  } else {
    await secrets.delete(ORG_TOKEN_SECRET_KEY);
    await secrets.store(ORG_ROUTE_SECRET_KEY, ROUTE_SESSION);
  }
  await vscode.workspace
    .getConfiguration(CONFIG_SECTION)
    .update("organization", org, vscode.ConfigurationTarget.Global);
}

/**
 * The token-free route (v4.13.8 Phase 6): ask VS Code's GitHub sign-in for the
 * read-only `read:org` scope, then check both pool endpoints with it. Returns
 * "connected", "unreachable" when GitHub cannot answer (a network drop, a rate
 * limit, or a server error), or null to fall back to the guided token: when
 * GitHub refuses the session (401, 403, 404), and when the user declines the
 * consent prompt, which is how an owner who prefers a token scoped to one
 * organization over `read:org` reaches it (decision record amendment).
 */
async function connectWithSession(
  secrets: vscode.SecretStorage,
  org: string,
  auth: GitHubAuthentication,
  fetchImpl: FetchLike,
  nowMs: number,
): Promise<ConnectOutcome | null> {
  let session: vscode.AuthenticationSession | undefined;
  try {
    session = await auth.getSession(GITHUB_PROVIDER_ID, ORG_READ_SCOPES, { createIfNone: true });
  } catch {
    session = undefined;
  }
  if (!session) {
    log("Connect: the read:org consent prompt was declined; offering a read-only token instead.");
    return null;
  }
  const { error, statuses } = await checkBothEndpoints(org, `Bearer ${session.accessToken}`, fetchImpl, nowMs);
  log(`Connect: token-free route, ${statuses}.`);
  if (!error) {
    await saveConnection(secrets, org, null);
    return "connected";
  }
  if (error.code === "org-token-rejected" || error.code === "org-access-denied") {
    return null;
  }
  // A network drop, a rate limit, or a GitHub error says nothing about whether
  // the session can read the pool, so it never pushes the owner to a token.
  void vscode.window.showWarningMessage(
    error.code === "network-error"
      ? "Copilot Usage: could not reach GitHub. Check your connection and try again."
      : "Copilot Usage: GitHub could not answer right now. Run Connect Organization again in a few minutes.",
  );
  return "unreachable";
}

/** The guided read-only token: open GitHub's pre-filled page, then paste the token. */
async function connectWithToken(
  secrets: vscode.SecretStorage,
  org: string,
  fetchImpl: FetchLike,
  nowMs: number,
): Promise<ConnectOutcome> {
  const open = await vscode.window.showInformationMessage(
    "This organization needs a read-only token to share its Copilot pool.",
    {
      modal: true,
      detail:
        "Step 1: Open GitHub. The token's name, organization, read-only permissions, and longest expiry are already filled in.\n" +
        "Step 2: Click Generate token, then Copy.\n" +
        "Step 3: Paste it into the box that opens here.",
    },
    OPEN_GITHUB,
  );
  if (open !== OPEN_GITHUB) {
    return "cancelled";
  }
  await vscode.env.openExternal(vscode.Uri.parse(tokenCreationUrl(org)));
  const token = await vscode.window.showInputBox({
    title: "Connect Organization (step 3 of 3)",
    prompt: TOKEN_PROMPT,
    password: true,
    ignoreFocusOut: true,
    validateInput: (value) => (value.trim() ? undefined : "Paste the token to continue."),
  });
  if (token === undefined || !token.trim()) {
    return "cancelled";
  }

  const { error, statuses } = await checkBothEndpoints(org, `Bearer ${token.trim()}`, fetchImpl, nowMs);
  log(`Connect: token route, ${statuses}.`);
  if (!error) {
    await saveConnection(secrets, org, token.trim());
    return "connected";
  }
  if (error.code === "org-token-rejected") {
    void vscode.window.showWarningMessage(
      "Copilot Usage: GitHub rejected the token. It may have expired or been copied only in part. Run Connect Organization again to create a new one.",
    );
    return "rejected";
  }
  if (error.code === "org-access-denied") {
    void Promise.resolve(vscode.window.showWarningMessage(`Copilot Usage: ${TOKEN_FIX_MESSAGE}`, OPEN_ORGANIZATION_SETTINGS)).then(
      (choice) => {
        if (choice === OPEN_ORGANIZATION_SETTINGS) {
          void vscode.env.openExternal(vscode.Uri.parse(organizationSettingsUrl(org)));
        }
      },
    );
    return "access-denied";
  }
  void vscode.window.showWarningMessage("Copilot Usage: could not verify the token with GitHub. Check your connection and try again.");
  return "unreachable";
}

/**
 * Connect Organization (v4.13.8 Phase 6): find the organization from the seat,
 * try the token-free `read:org` route, and only when GitHub refuses it guide
 * the user through a pre-filled read-only token. A failed check stores nothing.
 * No write scope is ever requested.
 */
export async function connectOrganization(
  secrets: vscode.SecretStorage,
  fetchImpl: FetchLike = (input, init) => fetch(input, init),
  auth: GitHubAuthentication = vscode.authentication,
  nowMs = Date.now(),
): Promise<ConnectOutcome> {
  const org = await chooseOrganization(await fetchSeatOrganizations(auth, fetchImpl));
  if (!org) {
    return "cancelled";
  }
  const outcome =
    (await connectWithSession(secrets, org, auth, fetchImpl, nowMs)) ??
    (await connectWithToken(secrets, org, fetchImpl, nowMs));
  if (outcome === "connected") {
    void vscode.window.showInformationMessage("Copilot Usage: organization connected. The pool's percentage appears on the next refresh.");
  }
  return outcome;
}

/**
 * Delete the stored token and route marker, and clear the organization setting
 * from every scope VS Code lets an extension write. Returns the route that was
 * connected, so the caller can say how to remove the `read:org` grant: VS Code
 * offers an extension no way to give a granted scope back.
 */
export async function disconnectOrganization(secrets: vscode.SecretStorage): Promise<OrganizationRoute> {
  const route = await organizationRoute(secrets);
  await secrets.delete(ORG_TOKEN_SECRET_KEY);
  await secrets.delete(ORG_ROUTE_SECRET_KEY);
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
  return route;
}

/**
 * What Disconnect says. VS Code gives an extension no way to return a granted
 * scope, so a token-free connection names where the user removes `read:org`.
 */
export function disconnectMessage(route: OrganizationRoute): string {
  if (route === "vscode-session") {
    return (
      "Copilot Usage: organization disconnected. VS Code keeps the read-only read:org permission it was granted; " +
      "to remove it, sign out of GitHub in VS Code's Accounts menu, or revoke Visual Studio Code under GitHub Settings, Applications, Authorized OAuth Apps."
    );
  }
  return route === "token"
    ? "Copilot Usage: organization disconnected and its token deleted."
    : "Copilot Usage: organization disconnected.";
}
