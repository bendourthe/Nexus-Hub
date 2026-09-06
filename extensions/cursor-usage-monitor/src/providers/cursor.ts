import type {
  LiveUsageSource,
  ProviderResult,
  UsageSnapshot
} from "../types";
import type { CursorCredentialStore } from "./auth";
import {
  providerError,
  shouldTryHtmlFallback
} from "./errors";
import {
  normalizeHtmlUsage,
  normalizeSnapshotPayload
} from "./normalizer";

export type CursorDashboardPage = "spending" | "usage";

export interface CredentialJsonTransport {
  fetchUsage(
    credential: string,
    signal?: AbortSignal
  ): Promise<ProviderResult<unknown>>;
}

export interface HtmlDashboardTransport {
  fetchPage(
    page: CursorDashboardPage,
    signal?: AbortSignal
  ): Promise<ProviderResult<string>>;
}

export interface CursorUsageProviderDependencies {
  credentials?: Pick<CursorCredentialStore, "withCredential">;
  jsonTransport?: CredentialJsonTransport;
  htmlTransport?: HtmlDashboardTransport;
  now?: () => Date;
}

export class CursorUsageProvider {
  private readonly now: () => Date;

  public constructor(
    private readonly dependencies: CursorUsageProviderDependencies
  ) {
    this.now = dependencies.now ?? (() => new Date());
  }

  public async fetch(signal?: AbortSignal): Promise<ProviderResult<UsageSnapshot>> {
    const jsonAttempt = await this.tryJson(signal);
    if (jsonAttempt.ok) {
      return jsonAttempt;
    }
    if (!shouldTryHtmlFallback(jsonAttempt.error)) {
      return jsonAttempt;
    }
    return this.tryHtml(signal);
  }

  private async tryJson(
    signal?: AbortSignal
  ): Promise<ProviderResult<UsageSnapshot>> {
    const { credentials, jsonTransport } = this.dependencies;
    if (credentials === undefined || jsonTransport === undefined) {
      return {
        ok: false,
        error: providerError("authorization-required", "credential-api")
      };
    }

    const payload = await credentials.withCredential(async (credential) =>
      stampSource(
        await jsonTransport.fetchUsage(credential, signal),
        "credential-api"
      )
    );
    if (!payload.ok) {
      return payload;
    }
    return normalizeSnapshotPayload(payload.value, {
      source: "credential-api",
      fetchedAt: this.now().toISOString()
    });
  }

  private async tryHtml(
    signal?: AbortSignal
  ): Promise<ProviderResult<UsageSnapshot>> {
    const { htmlTransport } = this.dependencies;
    if (htmlTransport === undefined) {
      return {
        ok: false,
        error: providerError("endpoint-unavailable", "html-scrape")
      };
    }

    const spending = await safeHtmlFetch(htmlTransport, "spending", signal);
    if (!spending.ok) {
      return spending;
    }
    const usage = await safeHtmlFetch(htmlTransport, "usage", signal);
    if (!usage.ok) {
      return usage;
    }
    return normalizeHtmlUsage(
      spending.value,
      usage.value,
      this.now().toISOString()
    );
  }
}

async function safeHtmlFetch(
  transport: HtmlDashboardTransport,
  page: CursorDashboardPage,
  signal?: AbortSignal
): Promise<ProviderResult<string>> {
  try {
    return stampSource(
      await transport.fetchPage(page, signal),
      "html-scrape"
    );
  } catch {
    return {
      ok: false,
      error: providerError("network-error", "html-scrape")
    };
  }
}

function stampSource<T>(
  result: ProviderResult<T>,
  sourceAttempt: LiveUsageSource
): ProviderResult<T> {
  return result.ok
    ? result
    : {
        ok: false,
        error: { ...result.error, sourceAttempt }
      };
}
