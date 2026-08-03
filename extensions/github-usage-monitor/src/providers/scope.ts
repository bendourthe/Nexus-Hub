import type { BillingOwner, BillingScope, ProviderError } from "../types";

const OWNER_PATTERN = /^[A-Za-z0-9](?:[A-Za-z0-9-]{0,98}[A-Za-z0-9])?$/u;

export type ScopeResolution =
  | { ok: true; owner: BillingOwner }
  | { ok: false; error: ProviderError };

export type CopilotEndpoint = "ai-credits" | "premium-requests";

export function resolveBillingOwner(scope: string, name: string): ScopeResolution {
  if (!isBillingScope(scope)) {
    return {
      ok: false,
      error: {
        code: "invalid-scope",
        message: "Choose exactly one billing scope: user, organization, or enterprise."
      }
    };
  }

  const normalized = name.trim();
  if (!OWNER_PATTERN.test(normalized) || normalized.includes("--")) {
    return {
      ok: false,
      error: {
        code: "invalid-scope",
        message: `Enter a valid GitHub ${scope} name using letters, digits, or single hyphens.`
      }
    };
  }

  return { ok: true, owner: { scope, name: normalized } };
}

export function billingEndpoint(owner: BillingOwner, suffix: string): string {
  const encoded = encodeURIComponent(owner.name);
  switch (owner.scope) {
    case "user":
      return `/users/${encoded}/settings/billing/${suffix}`;
    case "organization":
      return `/organizations/${encoded}/settings/billing/${suffix}`;
    case "enterprise":
      return `/enterprises/${encoded}/settings/billing/${suffix}`;
  }
}

export function copilotEndpointSuffix(endpoint: CopilotEndpoint): string {
  return endpoint === "ai-credits" ? "ai_credit/usage" : "premium_request/usage";
}

export function requiredPermission(owner: BillingOwner): string {
  switch (owner.scope) {
    case "user":
      return "Plan: read";
    case "organization":
      return "Administration: read and organization administrator role";
    case "enterprise":
      return "enterprise owner or billing manager";
  }
}

export function permissionError(owner: BillingOwner): ProviderError {
  switch (owner.scope) {
    case "user":
      return {
        code: "missing-plan-read",
        message: "The token needs user Plan: read permission for personal billing usage.",
        requiredPermission: requiredPermission(owner)
      };
    case "organization":
      return {
        code: "missing-organization-administration-read",
        message: "The token needs organization Administration: read and the caller must be an organization administrator.",
        requiredPermission: requiredPermission(owner)
      };
    case "enterprise":
      return {
        code: "missing-enterprise-billing-permission",
        message: "Enterprise billing usage requires an enterprise owner or billing manager credential.",
        requiredPermission: requiredPermission(owner)
      };
  }
}

export function managedCopilotScopeError(): ProviderError {
  return {
    code: "managed-copilot-personal-scope",
    message: "Managed Copilot usage is billed to an organization or enterprise and is not available from personal scope."
  };
}

function isBillingScope(value: string): value is BillingScope {
  return value === "user" || value === "organization" || value === "enterprise";
}
