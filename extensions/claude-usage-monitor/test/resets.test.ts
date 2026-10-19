/**
 * v4.13.7 sub-task 3.6: the Claude usage response carries no reset field (live
 * captures on 2026-10-01 and 2026-10-19, v4.13.7-decisions.md "Usage-limit
 * resets"). The dashboard still shows a Limit Resets row, matching the Codex
 * monitor, but it states that the count is not reported and links to the
 * claude.ai usage page; no code path reaches anything but the existing usage
 * read and token refresh.
 */
import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DashboardPanel } from "../src/dashboardPanel";
import { ClaudeUsageProvider } from "../src/providers";
import { USAGE_API_URL, mapClaudeUsageResponse } from "../src/providers/claude";
import { RAW_RESPONSE_FILE, redactUsagePayload, saveRawUsageResponse } from "../src/rawUsageResponse";
import { __resetStubState, createdWebviewPanels } from "./vscode-stub";

const SRC = path.join(__dirname, "..", "src");
const CAPTURED = path.join(__dirname, "fixtures", "oauth-usage-captured-no-reset-field.json");
const FAKE_ACCESS = ["fake", "access", "value"].join("-");

function captured(): Record<string, unknown> {
  return JSON.parse(fs.readFileSync(CAPTURED, "utf-8"));
}

afterEach(() => {
  for (const panel of createdWebviewPanels) panel.dispose();
  __resetStubState();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("the captured response has no reset field", () => {
  it("maps the captured windows and nothing about resets", () => {
    const data = mapClaudeUsageResponse(captured() as never, "claude-opus-4-6[1m]");
    expect(data.session.percent).toBe(21);
    expect(data.weeklyAllModels.percent).toBe(4);
    expect(Object.keys(data).some((k) => /reset/i.test(k) && k !== "resetsAt")).toBe(false);
  });

  it("renders a reset row that claims no count and links only to the usage page", async () => {
    const data = mapClaudeUsageResponse(captured() as never, "claude-opus-4-6[1m]");
    let opened = 0;
    DashboardPanel.show(data, "just now", undefined, { onRefresh() {}, onOpenUsagePage() { opened++; } });
    const panel = createdWebviewPanels[0];
    const html = panel.webview.html;
    expect(html).toContain("<h3>Limit Resets</h3>");
    expect(html).toContain("Not reported by the Claude usage API");
    expect(html).toContain(">Open reset page</button>");
    expect(html).not.toContain("openResetPage");
    expect(html).not.toMatch(/reset(s)? available|No reset available/);
    expect(html.indexOf("<h3>Limit Resets</h3>")).toBeLessThan(html.indexOf("<h3>Current Model</h3>"));
    expect(html.match(/data-command="openUsagePage"/g)).toHaveLength(2);
    await panel.webview.__dispatchMessage({ command: "openUsagePage" });
    expect(opened).toBe(1);
  });
});

describe("no code path sends a request other than the usage read", () => {
  function sourceFiles(root: string): string[] {
    return fs.readdirSync(root, { withFileTypes: true }).flatMap((entry) => {
      const full = path.join(root, entry.name);
      return entry.isDirectory() ? sourceFiles(full) : entry.name.endsWith(".ts") ? [full] : [];
    });
  }

  it("statically: fetch only in the provider, and only the usage read, token refresh, and usage page URLs", () => {
    const urls = new Set<string>();
    const fetchSites: string[] = [];
    for (const file of sourceFiles(SRC)) {
      const text = fs.readFileSync(file, "utf-8");
      for (const m of text.matchAll(/https?:\/\/[^\s"'`)]+/g)) urls.add(m[0]);
      if (/\bfetch\s*\(/.test(text)) fetchSites.push(path.relative(SRC, file));
      for (const banned of ["http.request", "https.request", "XMLHttpRequest", "from \"https\"", "from \"http\""]) {
        expect(text.includes(banned), `${banned} in ${file}`).toBe(false);
      }
    }
    expect(fetchSites).toEqual([path.join("providers", "claude.ts")]);
    expect([...urls].sort()).toEqual(
      [
        "http://www.w3.org/2000/svg",
        "https://api.anthropic.com/api/oauth/usage",
        "https://claude.ai/settings/usage",
        "https://console.anthropic.com/v1/oauth/token",
      ].sort(),
    );
  });

  it("at runtime: a refresh and a raw save each send one GET to the usage endpoint", async () => {
    vi.spyOn(ClaudeUsageProvider.prototype as never, "readCredentials").mockReturnValue({
      accessToken: FAKE_ACCESS,
      refreshToken: FAKE_ACCESS,
      expiresAt: Date.now() + 3_600_000,
    } as never);
    const calls: Array<{ url: string; method: string }> = [];
    vi.stubGlobal("fetch", async (url: string, init: { method?: string }) => {
      calls.push({ url, method: init?.method ?? "GET" });
      return new Response(JSON.stringify(captured()), { status: 200 });
    });
    const provider = new ClaudeUsageProvider();
    expect((await provider.fetchUsage()).success).toBe(true);
    const raw = await provider.fetchRawUsage();
    expect(raw.success).toBe(true);
    expect(raw.success && (raw.raw as Record<string, unknown>).five_hour).toBeDefined();
    expect(calls).toEqual([
      { url: USAGE_API_URL, method: "GET" },
      { url: USAGE_API_URL, method: "GET" },
    ]);
  });
});

describe("Save Raw Usage Response", () => {
  let dir: string;
  beforeEach(() => {
    dir = fs.mkdtempSync(path.join(os.tmpdir(), "claude-raw-"));
  });
  afterEach(() => fs.rmSync(dir, { recursive: true, force: true }));

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

  it("rebuilds kept keys and values from fixed alphabets and placeholders anything outside them", () => {
    const redacted = redactUsagePayload({ "plän": 1, used_percent: 12.5, big: 1e21, reached: false, kind: "five_hour" });
    expect(redacted).toEqual({ "<key 0>": 1, used_percent: 12.5, big: 1e21, reached: false, kind: "five_hour" });
  });

  it("writes one redacted file under the given storage folder", () => {
    const body = captured();
    body.account_email = "someone@example.com";
    const file = saveRawUsageResponse(dir, USAGE_API_URL, body);
    expect(file).toBe(path.join(dir, RAW_RESPONSE_FILE));
    const saved = JSON.parse(fs.readFileSync(file, "utf-8"));
    expect(saved.response.five_hour.utilization).toBe(21);
    expect(saved.response.limits[0].kind).toBe("session");
    expect(JSON.stringify(saved)).not.toContain("someone@example.com");
    expect(saved.response.spend.disclaimer).toMatch(/^<redacted string/);
  });

  it("is contributed as a command and called from one place", () => {
    const pkg = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "package.json"), "utf-8"));
    expect(pkg.contributes.commands.map((c: { command: string }) => c.command)).toContain("claude-usage.saveRawResponse");
    const ext = fs.readFileSync(path.join(SRC, "extension.ts"), "utf-8");
    expect(ext.match(/saveRawUsageResponse\(/g)).toHaveLength(1);
  });
});
