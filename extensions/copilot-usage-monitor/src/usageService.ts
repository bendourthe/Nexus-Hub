import type { OrganizationProvider, ProviderFetchError, UsageProvider } from "./providers/types";
import type { UsageData } from "./types";

/** A combined fetch: data when either half succeeded, else the personal error (and the organization one, if any). */
export type UsageFetchResult =
  | { success: true; data: UsageData; rateLimited: boolean }
  | { success: false; error: ProviderFetchError; organizationError?: ProviderFetchError; rateLimited: boolean };

/**
 * Fetches the personal figure and, when an organization is configured, the
 * organization pool, and merges them into one {@link UsageData}. One half
 * failing never hides the other: its error rides along as a partial error.
 */
export class UsageService {
  constructor(
    private readonly personal: UsageProvider,
    private readonly organization: OrganizationProvider,
  ) {}

  async fetchAll(nowMs = Date.now()): Promise<UsageFetchResult> {
    const personal = await this.personal.fetchUsage();
    const org = this.organization.isActive() ? await this.organization.fetchUsage(nowMs) : undefined;
    const rateLimited =
      (!personal.success && personal.error.code === "rate-limited") ||
      (org != null && !org.success && org.error.code === "rate-limited");

    if (personal.success || org?.success) {
      const data: UsageData = { lastUpdated: nowMs, dataSource: "api" };
      if (personal.success) {
        data.personal = { ...personal.data, fetchedAt: nowMs };
      } else {
        data.personalError = { code: personal.error.code, statusCode: personal.error.statusCode };
      }
      if (org?.success) {
        data.organization = { ...org.data, fetchedAt: nowMs };
      } else if (org) {
        data.organizationError = { code: org.error.code, statusCode: org.error.statusCode };
      }
      return { success: true, data, rateLimited };
    }
    return {
      success: false,
      error: personal.success ? { code: "usage-unavailable" } : personal.error,
      ...(org && !org.success ? { organizationError: org.error } : {}),
      rateLimited,
    };
  }
}
