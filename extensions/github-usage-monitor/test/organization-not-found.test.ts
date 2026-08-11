import { describe, expect, it } from "vitest";
import { explainOrganizationNotFound, membershipPath } from "../src/providers/github";
import type { ProviderError } from "../src/types";

/**
 * Regression cover for the organization billing 404 observed 2026-08-10.
 *
 * `GET /organizations/SupiraMedical/settings/billing/ai_credit/usage` returned 404
 * while `X-Accepted-OAuth-Scopes: admin:org, repo` and `X-OAuth-Scopes: repo` - so
 * the credential already carried an accepted scope and the scope headers could not
 * explain the failure. The message nonetheless said "Verify the scope", pointing the
 * user at the one thing that was already correct.
 *
 * These tests pin the discriminator: the membership role, which separates a
 * permission failure from an enhanced-billing-platform failure.
 */

const owner = { scope: "organization" as const, name: "SupiraMedical" };

const fallback: ProviderError = {
  code: "not-found",
  statusCode: 404,
  message: "GitHub could not find the configured billing owner or endpoint. Verify the scope and authorization."
};

describe("explainOrganizationNotFound", () => {
  it("targets the membership endpoint for the configured organization", () => {
    expect(membershipPath(owner)).toBe("/user/memberships/orgs/SupiraMedical");
    expect(membershipPath({ scope: "organization", name: "a b/c" })).toBe("/user/memberships/orgs/a%20b%2Fc");
  });

  it("names the role gap when the account is a plain member", () => {
    const error = explainOrganizationNotFound(owner, { ok: true, value: { state: "active", role: "member" } }, fallback);

    expect(error.code).toBe("missing-organization-administration-read");
    expect(error.message).toContain("not an organization owner or billing manager");
    expect(error.message).toContain("SupiraMedical");
    // The misleading instruction from the original message must be gone.
    expect(error.message).not.toContain("Verify the scope");
  });

  it("rules permission out when the account already holds a billing-capable role", () => {
    for (const role of ["admin", "billing_manager"]) {
      const error = explainOrganizationNotFound(owner, { ok: true, value: { state: "active", role } }, fallback);

      expect(error.code).toBe("enhanced-billing-unavailable");
      expect(error.message).toContain("not a permission problem");
      expect(error.message).toContain("enhanced billing");
    }
  });

  it("reports a pending invitation rather than a permission gap", () => {
    const error = explainOrganizationNotFound(owner, { ok: true, value: { state: "pending", role: "member" } }, fallback);

    expect(error.message).toContain("pending invitation");
  });

  it("reads a 403 on the membership lookup as an app-approval or SSO refusal", () => {
    const error = explainOrganizationNotFound(owner, { ok: false, status: 403 }, fallback);

    expect(error.message).toContain("restricts OAuth apps");
    expect(error.message).toContain("single sign-on");
  });

  it("keeps the original error when the lookup answers nothing useful", () => {
    expect(explainOrganizationNotFound(owner, { ok: false, status: 404 }, fallback)).toEqual(fallback);
    expect(explainOrganizationNotFound(owner, { ok: false, status: 500 }, fallback)).toEqual(fallback);
    expect(explainOrganizationNotFound(owner, { ok: true, value: null }, fallback)).toEqual(fallback);
    expect(explainOrganizationNotFound(owner, { ok: true, value: { role: 7 } }, fallback)).toEqual(fallback);
  });
});
