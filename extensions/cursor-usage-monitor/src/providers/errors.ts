import type {
  LiveUsageSource,
  ProviderError,
  ProviderErrorCode
} from "../types";

const MESSAGES: Record<ProviderErrorCode, string> = {
  "authorization-required":
    "Cursor session reuse requires explicit authorization.",
  "missing-credential":
    "No extension-owned Cursor credential is stored in SecretStorage.",
  "invalid-credential":
    "The supplied Cursor credential has an invalid format.",
  "session-expired": "The Cursor session is missing or expired.",
  "dashboard-visibility-restricted":
    "Cursor usage or spending data is unavailable for this account role.",
  "unsupported-data-path":
    "The Cursor dashboard data path is not enabled for this account.",
  "endpoint-unavailable":
    "The Cursor dashboard data path is unavailable.",
  "login-redirect": "Cursor returned a sign-in page instead of usage data.",
  "client-shell":
    "Cursor returned a client-only dashboard shell without usage data.",
  "html-schema-mismatch":
    "Cursor dashboard HTML no longer matches the approved semantic contract.",
  "json-schema-mismatch":
    "Cursor dashboard JSON no longer matches the approved fixture contract.",
  "unit-mismatch":
    "Cursor usage quantities use incompatible units and cannot be combined.",
  "invalid-value": "Cursor usage data contains an invalid value.",
  timeout: "The Cursor usage request timed out.",
  cancelled: "The Cursor usage request was cancelled.",
  "network-error": "The Cursor usage request failed.",
  "rate-limited": "Cursor usage refresh is rate limited.",
  "service-error": "Cursor usage is temporarily unavailable.",
  "credential-adapter-unavailable":
    "The authorized Cursor credential adapter is unavailable.",
  "credential-store-error":
    "Cursor credential storage is temporarily unavailable."
};

export function providerError(
  code: ProviderErrorCode,
  sourceAttempt: LiveUsageSource | null,
  options: {
    statusCode?: number;
    retryAt?: string;
    recoverable?: boolean;
  } = {}
): ProviderError {
  return {
    code,
    message: MESSAGES[code],
    sourceAttempt,
    recoverable: options.recoverable ?? defaultRecoverable(code),
    ...(options.statusCode === undefined
      ? {}
      : { statusCode: options.statusCode }),
    ...(options.retryAt === undefined ? {} : { retryAt: options.retryAt })
  };
}

export function classifyHttpError(
  statusCode: number,
  sourceAttempt: LiveUsageSource,
  retryAt?: string
): ProviderError {
  if (statusCode === 400) {
    return providerError("unsupported-data-path", sourceAttempt, {
      statusCode
    });
  }
  if (statusCode === 401) {
    return providerError("session-expired", sourceAttempt, { statusCode });
  }
  if (statusCode === 403) {
    return providerError("dashboard-visibility-restricted", sourceAttempt, {
      statusCode
    });
  }
  if (statusCode === 404) {
    return providerError("endpoint-unavailable", sourceAttempt, { statusCode });
  }
  if (statusCode === 429) {
    return providerError("rate-limited", sourceAttempt, {
      statusCode,
      ...(retryAt === undefined ? {} : { retryAt })
    });
  }
  return providerError(
    statusCode >= 500 ? "service-error" : "network-error",
    sourceAttempt,
    { statusCode }
  );
}

export function shouldTryHtmlFallback(error: ProviderError): boolean {
  return (
    error.code === "authorization-required" ||
    error.code === "missing-credential" ||
    error.code === "unsupported-data-path" ||
    error.code === "endpoint-unavailable"
  );
}

function defaultRecoverable(code: ProviderErrorCode): boolean {
  return ![
    "invalid-credential",
    "unit-mismatch",
    "invalid-value",
    "json-schema-mismatch",
    "html-schema-mismatch"
  ].includes(code);
}
