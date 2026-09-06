import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import {
  CursorCredentialStore,
  type SecretStorageLike
} from "../src/providers/auth";
import {
  CursorUsageProvider,
  type CursorDashboardPage
} from "../src/providers/cursor";
import {
  classifyHttpError,
  providerError,
  shouldTryHtmlFallback
} from "../src/providers/errors";
import type { ProviderResult } from "../src/types";

class FakeSecrets implements SecretStorageLike {
  private readonly values = new Map<string, string>();

  public async get(key: string): Promise<string | undefined> {
    return this.values.get(key);
  }

  public async store(key: string, value: string): Promise<void> {
    this.values.set(key, value);
  }

  public async delete(key: string): Promise<void> {
    this.values.delete(key);
  }
}

const credential = "fixture-credential-value-1234567890";
const now = () => new Date("2026-08-04T16:00:00Z");

function fixture<T = unknown>(name: string): T {
  const path = resolve(__dirname, "../../../tests/fixtures/cursor-usage", name);
  const text = readFileSync(path, "utf8");
  return (name.endsWith(".html") ? text : JSON.parse(text)) as T;
}

async function credentialStore(
  withCredential = true
): Promise<CursorCredentialStore> {
  const store = new CursorCredentialStore(new FakeSecrets());
  if (withCredential) {
    await store.setCredential(credential);
  }
  return store;
}

function success<T>(value: T): ProviderResult<T> {
  return { ok: true, value };
}

describe("CursorUsageProvider", () => {
  it("uses credential JSON first and does not request HTML on success", async () => {
    let jsonCalls = 0;
    let htmlCalls = 0;
    const provider = new CursorUsageProvider({
      credentials: await credentialStore(),
      jsonTransport: {
        async fetchUsage(observed) {
          jsonCalls += 1;
          expect(observed).toBe(credential);
          return success(fixture("included-usage-healthy.json"));
        }
      },
      htmlTransport: {
        async fetchPage() {
          htmlCalls += 1;
          return success("");
        }
      },
      now
    });

    const result = await provider.fetch();
    expect(result.ok && result.value.source).toBe("credential-api");
    expect(jsonCalls).toBe(1);
    expect(htmlCalls).toBe(0);
  });

  it("falls back to exactly two HTML pages when no credential exists", async () => {
    const pages: CursorDashboardPage[] = [];
    const provider = new CursorUsageProvider({
      credentials: await credentialStore(false),
      jsonTransport: {
        async fetchUsage() {
          throw new Error("must not be called without a credential");
        }
      },
      htmlTransport: {
        async fetchPage(page) {
          pages.push(page);
          return success(
            fixture(
              page === "spending"
                ? "scrape-spending-page.html"
                : "scrape-usage-page.html"
            )
          );
        }
      },
      now
    });

    const result = await provider.fetch();
    expect(result.ok && result.value.source).toBe("html-scrape");
    expect(pages).toEqual(["spending", "usage"]);
  });

  it.each([400, 404])(
    "uses bounded HTML fallback after HTTP %i",
    async (statusCode) => {
      const pages: CursorDashboardPage[] = [];
      const provider = new CursorUsageProvider({
        credentials: await credentialStore(),
        jsonTransport: {
          async fetchUsage() {
            const error = classifyHttpError(statusCode, "credential-api");
            return {
              ok: false,
              error: { ...error, sourceAttempt: null }
            };
          }
        },
        htmlTransport: {
          async fetchPage(page) {
            pages.push(page);
            return success(
              fixture(
                page === "spending"
                  ? "scrape-spending-page.html"
                  : "scrape-usage-page.html"
              )
            );
          }
        },
        now
      });

      expect((await provider.fetch()).ok).toBe(true);
      expect(pages).toEqual(["spending", "usage"]);
    }
  );

  it.each([
    [401, "session-expired"],
    [403, "dashboard-visibility-restricted"],
    [429, "rate-limited"]
  ] as const)(
    "stops without HTML fallback after HTTP %i",
    async (statusCode, code) => {
      let htmlCalls = 0;
      const provider = new CursorUsageProvider({
        credentials: await credentialStore(),
        jsonTransport: {
          async fetchUsage() {
            const error = classifyHttpError(statusCode, "credential-api");
            return {
              ok: false,
              error: { ...error, sourceAttempt: null }
            };
          }
        },
        htmlTransport: {
          async fetchPage() {
            htmlCalls += 1;
            return success("");
          }
        },
        now
      });

      const result = await provider.fetch();
      expect(!result.ok && result.error.code).toBe(code);
      expect(!result.ok && result.error.sourceAttempt).toBe("credential-api");
      expect(htmlCalls).toBe(0);
    }
  );

  it("does not hide JSON schema drift behind HTML fallback", async () => {
    let htmlCalls = 0;
    const provider = new CursorUsageProvider({
      credentials: await credentialStore(),
      jsonTransport: {
        async fetchUsage() {
          return success({});
        }
      },
      htmlTransport: {
        async fetchPage() {
          htmlCalls += 1;
          return success("");
        }
      },
      now
    });
    const result = await provider.fetch();
    expect(!result.ok && result.error.code).toBe("json-schema-mismatch");
    expect(htmlCalls).toBe(0);
  });

  it("stops the HTML pair on the first typed failure", async () => {
    const pages: CursorDashboardPage[] = [];
    const provider = new CursorUsageProvider({
      htmlTransport: {
        async fetchPage(page) {
          pages.push(page);
          return {
            ok: false,
            error: providerError("session-expired", null)
          };
        }
      },
      now
    });
    const result = await provider.fetch();
    expect(!result.ok && result.error.code).toBe("session-expired");
    expect(!result.ok && result.error.sourceAttempt).toBe("html-scrape");
    expect(pages).toEqual(["spending"]);
  });

  it("redacts unexpected HTML transport exceptions", async () => {
    const provider = new CursorUsageProvider({
      htmlTransport: {
        async fetchPage() {
          throw new Error(`must not expose ${credential}`);
        }
      },
      now
    });
    const result = await provider.fetch();
    expect(!result.ok && result.error.code).toBe("network-error");
    expect(!result.ok && result.error.message).not.toContain(credential);
  });

  it("returns a typed failure when no transport is configured", async () => {
    const result = await new CursorUsageProvider({ now }).fetch();
    expect(!result.ok && result.error.code).toBe("endpoint-unavailable");
  });
});

describe("provider error policy", () => {
  it("classifies service and unknown HTTP failures safely", () => {
    expect(classifyHttpError(503, "html-scrape").code).toBe("service-error");
    expect(classifyHttpError(418, "html-scrape").code).toBe("network-error");
    expect(
      classifyHttpError(
        429,
        "credential-api",
        "2026-08-04T16:05:00Z"
      )
    ).toMatchObject({
      code: "rate-limited",
      retryAt: "2026-08-04T16:05:00Z"
    });
  });

  it("allows fallback only for explicitly bounded cases", () => {
    expect(
      shouldTryHtmlFallback(
        providerError("missing-credential", "credential-api")
      )
    ).toBe(true);
    expect(
      shouldTryHtmlFallback(providerError("session-expired", "credential-api"))
    ).toBe(false);
  });
});
