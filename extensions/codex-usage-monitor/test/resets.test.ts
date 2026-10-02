/**
 * v4.13.7 sub-task 3.6: reset availability. Fixtures are sanitized from one
 * live wham/usage response (v4.13.7-decisions.md, "Usage-limit resets"); the
 * response reports `rate_limit_reset_credits` as two counts with no kind and no
 * expiry, so the row shows a count only.
 */
import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DashboardPanel } from "../src/dashboardPanel";
import { EARLY_REFRESH_DELAY_MS, EarlyRefresh } from "../src/earlyRefresh";
import { CodexUsageProvider } from "../src/providers";
import { CODEX_USAGE_URL, mapCodexUsageResponse, readResets } from "../src/providers/codex";
import { RAW_RESPONSE_FILE, redactUsagePayload, saveRawUsageResponse } from "../src/rawUsageResponse";
import type { UsageData } from "../src/types";
import { __resetStubState, __setStubConfig, createdWebviewPanels } from "./vscode-stub";

const FIXTURES = path.join(__dirname, "fixtures");
const SRC = path.join(__dirname, "..", "src");
// Fake credential-shaped strings, assembled so no literal looks like a secret.
const FAKE_JWT = ["ey", "JhbGciOiJIUzI1NiJ9", ".payload.sig"].join("");
const FAKE_ACCESS = ["fake", "access", "value"].join("-");

function fixture(name: string): Record<string, unknown> {
  return JSON.parse(fs.readFileSync(path.join(FIXTURES, name), "utf-8"));
}

function mapped(name: string): UsageData {
  const data = mapCodexUsageResponse(fixture(name));
  expect(data).not.toBeNull();
  return data!;
}

function callbacks() {
  return { onRefresh: vi.fn(), onOpenUsagePage: vi.fn(), onOpenResetPage: vi.fn() };
}

function show(data: UsageData, cb = callbacks()): string {
  DashboardPanel.show(data, "just now", undefined, cb);
  return createdWebviewPanels[0].webview.html;
}

function resetButton(html: string): string {
  const match = html.match(/<button data-command="openResetPage"[^>]*>/);
  expect(match, "reset button").not.toBeNull();
  return match![0];
}

afterEach(() => {
  for (const panel of createdWebviewPanels) panel.dispose();
  __resetStubState();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("mapping rate_limit_reset_credits", () => {
  it("reads the served count from the reset-available fixture", () => {
    expect(mapped("wham-usage-reset-available.json").resets).toEqual({ available: 1 });
  });

  it("reads a zero count as no reset available", () => {
    expect(mapped("wham-usage-no-reset.json").resets).toEqual({ available: 0 });
  });

  it("reports nothing when the field is absent", () => {
    expect(mapped("wham-usage-no-reset-field.json").resets).toBeUndefined();
  });

  it("prefers the applicable count, the stricter of the two", () => {
    expect(readResets({ rate_limit_reset_credits: { available_count: 2, applicable_available_count: 0 } })).toEqual({ available: 0 });
    expect(readResets({ rate_limit_reset_credits: { available_count: 2 } })).toEqual({ available: 2 });
  });

  it("never falls back to the looser count when the applicable count is present but malformed", () => {
    vi.spyOn(console, "warn").mockImplementation(() => {});
    for (const applicable of [null, -1, "0", 1.5, Number.NaN, []]) {
      const value = { applicable_available_count: applicable, available_count: 4 };
      expect(readResets({ rate_limit_reset_credits: value }), JSON.stringify(value)).toBeUndefined();
    }
  });

  it("treats a malformed field as not reported, logs at most once, and never guesses", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    for (const value of ["1", 1, [], { available_count: -1 }, { available_count: 1.5 }, { applicable_available_count: "1" }, {}]) {
      expect(readResets({ rate_limit_reset_credits: value }), JSON.stringify(value)).toBeUndefined();
    }
    expect(readResets({ rate_limit_reset_credits: null })).toBeUndefined();
    expect(warn.mock.calls.length).toBeLessThanOrEqual(1);
  });

  it("keeps the usage percentages when the reset field changes shape", () => {
    const body = fixture("wham-usage-reset-available.json");
    body.rate_limit_reset_credits = { count: "one" };
    vi.spyOn(console, "warn").mockImplementation(() => {});
    const data = mapCodexUsageResponse(body)!;
    expect(data.weeklyAllModels.percent).toBe(100);
    expect(data.resets).toBeUndefined();
  });
});

describe("the Limit Resets row and the Open reset page button", () => {
  it("renders the row and an enabled button with the reset fixture", () => {
    const html = show(mapped("wham-usage-reset-available.json"));
    expect(html).toContain("<h3>Limit Resets</h3>");
    expect(html).toContain("1 reset available");
    expect(resetButton(html)).not.toContain("disabled");
    expect(html).toContain('data-command="openUsagePage"');
  });

  it("renders a disabled button with the No reset available tooltip with the no-reset fixture", () => {
    const html = show(mapped("wham-usage-no-reset.json"));
    expect(html).toContain("No reset available");
    expect(resetButton(html)).toContain("disabled");
    expect(html).toContain('<span title="No reset available"><button data-command="openResetPage"');
  });

  it("reads No reset available after the used-reset fixture replaces the reset fixture on refresh", () => {
    show(mapped("wham-usage-reset-available.json"));
    const used = mapped("wham-usage-reset-used.json");
    DashboardPanel.updateIfOpen(used, "just now", undefined);
    const html = DashboardPanel.currentHtml()!;
    expect(html).toContain("No reset available");
    expect(html).not.toContain("1 reset available");
    expect(resetButton(html)).toContain("disabled");
    expect(used.weeklyAllModels.percent).toBe(0);
  });

  it("renders no reset row or button when the response lacks the field", () => {
    const html = show(mapped("wham-usage-no-reset-field.json"));
    expect(html).not.toContain("Limit Resets");
    expect(html).not.toContain('data-command="openResetPage"');
    expect(html).not.toContain("reset available");
  });

  it("calls only the open-page callback, and only while a reset is available", async () => {
    const cb = callbacks();
    show(mapped("wham-usage-reset-available.json"), cb);
    await createdWebviewPanels[0].webview.__dispatchMessage({ command: "openResetPage" });
    expect(cb.onOpenResetPage).toHaveBeenCalledTimes(1);
    expect(cb.onRefresh).not.toHaveBeenCalled();

    DashboardPanel.updateIfOpen(mapped("wham-usage-no-reset.json"), "now", undefined);
    await createdWebviewPanels[0].webview.__dispatchMessage({ command: "openResetPage" });
    expect(cb.onOpenResetPage).toHaveBeenCalledTimes(1);
  });

  it("lists openResetPage among the commands the webview script may post", () => {
    const html = show(mapped("wham-usage-reset-available.json"));
    expect(html).toContain("const WEBVIEW_COMMANDS = ['refresh', 'openUsagePage', 'openResetPage'];");
  });
});

describe("the early refresh after Open reset page", () => {
  it("refreshes once, a minute after the button is pressed", () => {
    vi.useFakeTimers();
    const refresh = vi.fn();
    const early = new EarlyRefresh(refresh);
    early.schedule();
    vi.advanceTimersByTime(EARLY_REFRESH_DELAY_MS - 1);
    expect(refresh).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1);
    expect(refresh).toHaveBeenCalledTimes(1);
    vi.advanceTimersByTime(10 * EARLY_REFRESH_DELAY_MS);
    expect(refresh).toHaveBeenCalledTimes(1);
  });

  it("restarts the wait on a second press instead of stacking refreshes, and cancels on dispose", () => {
    vi.useFakeTimers();
    const refresh = vi.fn();
    const early = new EarlyRefresh(refresh);
    early.schedule();
    vi.advanceTimersByTime(30_000);
    early.schedule();
    vi.advanceTimersByTime(EARLY_REFRESH_DELAY_MS);
    expect(refresh).toHaveBeenCalledTimes(1);
    early.schedule();
    early.dispose();
    vi.advanceTimersByTime(EARLY_REFRESH_DELAY_MS);
    expect(refresh).toHaveBeenCalledTimes(1);
  });
});

describe("no code path sends a request other than the usage read", () => {
  let dir: string;
  beforeEach(() => {
    dir = fs.mkdtempSync(path.join(os.tmpdir(), "codex-resets-"));
  });
  afterEach(() => fs.rmSync(dir, { recursive: true, force: true }));

  function sourceFiles(root: string): string[] {
    return fs.readdirSync(root, { withFileTypes: true }).flatMap((entry) => {
      const full = path.join(root, entry.name);
      return entry.isDirectory() ? sourceFiles(full) : entry.name.endsWith(".ts") ? [full] : [];
    });
  }

  it("statically: one fetch call site, and the only URLs are the usage read and the usage page", () => {
    const urls = new Set<string>();
    const fetchSites: string[] = [];
    for (const file of sourceFiles(SRC)) {
      const text = fs.readFileSync(file, "utf-8");
      for (const m of text.matchAll(/https?:\/\/[^\s"'`)]+/g)) urls.add(m[0]);
      if (/\bfetch\s*\(/.test(text)) fetchSites.push(path.relative(SRC, file));
      for (const banned of ["http.request", "https.request", "XMLHttpRequest", "child_process", "from \"https\"", "from \"http\""]) {
        expect(text.includes(banned), `${banned} in ${file}`).toBe(false);
      }
    }
    expect(fetchSites).toEqual([path.join("providers", "codex.ts")]);
    expect([...urls].sort()).toEqual(
      ["http://www.w3.org/2000/svg", "https://chatgpt.com/backend-api/wham/usage", "https://chatgpt.com/settings/usage?tab=overview"].sort(),
    );
  });

  it("at runtime: a refresh and a raw save each send exactly one GET to the usage endpoint", async () => {
    const auth = path.join(dir, "auth.json");
    fs.writeFileSync(auth, JSON.stringify({ tokens: { access_token: FAKE_ACCESS, account_id: "acct-fake" } }));
    __setStubConfig("codexUsage", "authPath", auth);
    const calls: Array<{ url: string; method: string }> = [];
    vi.stubGlobal("fetch", async (url: string, init: { method?: string }) => {
      calls.push({ url, method: init?.method ?? "GET" });
      return new Response(JSON.stringify(fixture("wham-usage-reset-available.json")), { status: 200 });
    });
    const provider = new CodexUsageProvider();
    const result = await provider.fetchUsage();
    expect(result.success).toBe(true);
    const raw = await provider.fetchRawUsage();
    expect(raw.success).toBe(true);
    expect(calls).toEqual([
      { url: CODEX_USAGE_URL, method: "GET" },
      { url: CODEX_USAGE_URL, method: "GET" },
    ]);
  });
});

describe("Save Raw Usage Response", () => {
  let dir: string;
  beforeEach(() => {
    dir = fs.mkdtempSync(path.join(os.tmpdir(), "codex-raw-"));
  });
  afterEach(() => fs.rmSync(dir, { recursive: true, force: true }));

  it("keeps keys, numbers, booleans, dates, and enum words, and replaces identifying strings", () => {
    const body: Record<string, unknown> = {
      email: "someone@example.com",
      account_id: "9b2f0c1e-0000-4000-8000-123456789abc",
      user_id: 123456,
      plan_type: "plus",
      link: "https://chatgpt.com/x",
      when: "2026-10-29T00:00:00Z",
      rate_limit_reset_credits: { available_count: 1, applicable_available_count: 1 },
      nested: [{ display_name: "Someone", limit_reached: true }],
      "9b2f0c1e-0000-4000-8000-123456789abc": { used: 1 },
    };
    body["access_" + "token"] = FAKE_JWT;
    const redacted = redactUsagePayload(body) as Record<string, unknown>;
    const text = JSON.stringify(redacted);
    for (const secret of ["someone@example.com", "9b2f0c1e", "123456", FAKE_JWT, "https://chatgpt.com/x", "Someone"]) {
      expect(text.includes(secret), secret).toBe(false);
    }
    expect(redacted.plan_type).toBe("plus");
    expect(redacted.when).toBe("2026-10-29T00:00:00Z");
    expect(redacted.rate_limit_reset_credits).toEqual({ available_count: 1, applicable_available_count: 1 });
    expect((redacted.nested as Array<Record<string, unknown>>)[0].limit_reached).toBe(true);
  });

  it("redacts camelCase, run-together, and secret-word keys as well as snake_case ones", () => {
    const body: Record<string, unknown> = {
      userId: 123456789,
      accountId: 987654,
      orgUuid: "acme",
      displayName: "benjamin",
      userEmail: "benjamin",
      username: "bdourthe",
      password: "hunter",
      sessiontoken: "abcdefghijklmnopqrstuvwxyz",
      phone: 15551234567,
      ownerHandle: "octo",
      planType: "plus",
      usedPercent: 42,
    };
    const redacted = redactUsagePayload(body) as Record<string, unknown>;
    const text = JSON.stringify(redacted);
    for (const secret of ["123456789", "987654", "acme", "benjamin", "bdourthe", "hunter", "abcdefghijklmnopqrstuvwxyz", "15551234567", "octo"]) {
      expect(text.includes(secret), secret).toBe(false);
    }
    expect(redacted.planType).toBe("plus");
    expect(redacted.usedPercent).toBe(42);
  });

  it("writes one file under the given storage folder and replaces it on the next save", () => {
    const file = saveRawUsageResponse(dir, CODEX_USAGE_URL, fixture("wham-usage-reset-available.json"));
    expect(file).toBe(path.join(dir, RAW_RESPONSE_FILE));
    saveRawUsageResponse(dir, CODEX_USAGE_URL, fixture("wham-usage-no-reset.json"));
    expect(fs.readdirSync(dir)).toEqual([RAW_RESPONSE_FILE]);
    const saved = JSON.parse(fs.readFileSync(file, "utf-8"));
    expect(saved.endpoint).toBe(CODEX_USAGE_URL);
    expect(saved.response.rate_limit_reset_credits).toEqual({ applicable_available_count: 0, available_count: 0 });
    expect(JSON.stringify(saved)).not.toContain("user@example.invalid");
  });

  it("is contributed as a command and never runs on its own", () => {
    const pkg = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "package.json"), "utf-8"));
    const commands = pkg.contributes.commands.map((c: { command: string }) => c.command);
    expect(commands).toContain("codex-usage.saveRawResponse");
    expect(pkg.activationEvents).toEqual(["onStartupFinished"]);
    const ext = fs.readFileSync(path.join(SRC, "extension.ts"), "utf-8");
    expect(ext.match(/saveRawUsageResponse\(/g)).toHaveLength(1);
    expect(ext).toMatch(/registerCommand\(SAVE_RAW_COMMAND/);
  });
});
