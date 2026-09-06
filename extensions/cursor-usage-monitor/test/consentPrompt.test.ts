import { afterEach, describe, expect, it, vi } from "vitest";
import {
  ALLOW_LABEL,
  DENY_LABEL,
  WindowConsentPrompt
} from "../src/extension";
import { consentPromptRequest } from "../src/providers/consent";
import {

  CURSOR_WIRE_CONTRACT,
  CursorLiveUsageTransport
} from "../src/providers/liveTransport";
import {
  informationMessages,
  informationResponses,
  resetVscodeStub
} from "./vscode-stub";

afterEach(() => {
  resetVscodeStub();
  vi.unstubAllGlobals();
});

describe("WindowConsentPrompt", () => {
  it("maps the allow label to a grant", async () => {
    informationResponses.push(ALLOW_LABEL);
    expect(await new WindowConsentPrompt().ask(consentPromptRequest())).toBe(
      "granted"
    );
  });

  it("maps the refusal label to a decline, never to a grant", async () => {
    informationResponses.push(DENY_LABEL);
    expect(await new WindowConsentPrompt().ask(consentPromptRequest())).toBe(
      "declined"
    );
  });

  it("maps a closed dialog to dismissed so nothing is persisted", async () => {
    informationResponses.push(undefined);
    expect(await new WindowConsentPrompt().ask(consentPromptRequest())).toBe(
      "dismissed"
    );
  });

  it("shows the disclosure title to the user", async () => {
    informationResponses.push(ALLOW_LABEL);
    const request = consentPromptRequest();
    await new WindowConsentPrompt().ask(request);
    expect(informationMessages.at(-1)).toBe(request.title);
  });

  it("uses labels a user can tell apart without reading the detail", () => {
    expect(ALLOW_LABEL).not.toBe(DENY_LABEL);
    expect(ALLOW_LABEL.toLowerCase()).toContain("allow");
    expect(DENY_LABEL.toLowerCase()).toContain("manual");
  });
});

describe("default fetch client", () => {
  it("requests the allowlisted route with the session in a header", async () => {
    const calls: Array<{ url: string; init: RequestInit }> = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init: RequestInit) => {
        calls.push({ url, init });
        return {
          ok: true,
          status: 200,
          headers: { get: () => null },
          json: async () => ({ shape: "rejected downstream" })
        };
      })
    );

    const session = "fixture-session-token-abcdef0123456789";
    const result = await new CursorLiveUsageTransport().fetchUsage(session);

    expect(calls).toHaveLength(1);
    expect(calls[0]?.url).toBe(
      `${CURSOR_WIRE_CONTRACT.origin}${CURSOR_WIRE_CONTRACT.route}`
    );
    const headers = calls[0]?.init.headers as Record<string, string>;
    expect(headers.Authorization).toBe(`Bearer ${session}`);
    expect(calls[0]?.url).not.toContain(session);

    // A 200 with an unrecognized body is still rejected, not accepted.
    expect(!result.ok && result.error.code).toBe("json-schema-mismatch");
  });

  it("passes retry metadata through and skips parsing a failed body", async () => {
    const json = vi.fn();
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: false,
        status: 429,
        headers: { get: (name: string) => (name === "retry-after" ? "120" : null) },
        json
      }))
    );

    const result = await new CursorLiveUsageTransport().fetchUsage("token-0123456789abcdef");
    expect(!result.ok && result.error.code).toBe("rate-limited");
    expect(!result.ok && result.error.retryAt).toBe("120");
    expect(json).not.toHaveBeenCalled();
  });

  it("reports a thrown request as a network error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new Error("dns failure");
      })
    );
    const result = await new CursorLiveUsageTransport().fetchUsage(
      "token-0123456789abcdef"
    );
    expect(!result.ok && result.error.code).toBe("network-error");
  });
});
