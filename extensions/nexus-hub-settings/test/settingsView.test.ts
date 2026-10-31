import { beforeEach, describe, expect, it, vi } from "vitest";
import type { SettingsController } from "../src/controller";
import { SettingsViewProvider, buildHtml, contentSecurityPolicy, newNonce } from "../src/settingsView";
import { buildModel, emptyModel } from "../src/viewModel";
import { explains, layers, showReport } from "./fixtures";
import { Uri, stub } from "./vscode-stub";

const PARTS = { cspSource: "vscode-webview://abc", nonce: "N0nce_-x", scriptUri: "vscode-webview://abc/panel.js", styleUri: "vscode-webview://abc/panel.css", logoUri: "vscode-webview://abc/logo.png" };

describe("the webview page", () => {
  it("allows one nonce-guarded script, the extension's own style and logo, and no network", () => {
    const policy = contentSecurityPolicy(PARTS.cspSource, PARTS.nonce);
    expect(policy).toContain("default-src 'none'");
    expect(policy).toContain(`script-src 'nonce-${PARTS.nonce}'`);
    expect(policy).toContain(`style-src ${PARTS.cspSource}`);
    expect(policy).toContain(`img-src ${PARTS.cspSource}`);
    expect(policy).toContain("connect-src 'none'");
    expect(policy).toContain("base-uri 'none'");
    expect(policy).not.toMatch(/unsafe-inline|unsafe-eval|\*|https?:/);
  });

  it("has exactly one script element, carrying the nonce and a src, and no inline handlers or styles", () => {
    const html = buildHtml(PARTS);
    const scripts = html.match(/<script\b[^>]*>/g) ?? [];
    expect(scripts).toHaveLength(1);
    expect(scripts[0]).toContain(`nonce="${PARTS.nonce}"`);
    expect(scripts[0]).toContain(`src="${PARTS.scriptUri}"`);
    expect(html).not.toMatch(/<script[^>]*>[^<]+<\/script>/);
    expect(html).not.toMatch(/\son[a-z]+=/i);
    expect(html).not.toMatch(/\sstyle=/i);
    expect(html).toContain(`data-logo="${PARTS.logoUri}"`);
    expect(html).toContain('<html lang="en">');
  });

  it("has a polite status region and an assertive alert region before the script runs, so a notice is spoken", () => {
    const html = buildHtml(PARTS);
    expect(html).toMatch(/<div id="live-status"[^>]*role="status"[^>]*aria-live="polite"[^>]*><\/div>/);
    expect(html).toMatch(/<div id="live-alert"[^>]*role="alert"[^>]*aria-live="assertive"[^>]*><\/div>/);
    expect(html.indexOf('id="live-status"')).toBeLessThan(html.indexOf("<script"));
  });

  it("escapes anything it was given before it reaches an attribute", () => {
    const html = buildHtml({ ...PARTS, logoUri: 'x"><script>alert(1)</script>' });
    expect(html).not.toContain("<script>alert(1)");
    expect(html).toContain("&quot;&gt;&lt;script&gt;");
  });

  it("makes a fresh unguessable nonce per load", () => {
    const nonces = new Set(Array.from({ length: 20 }, () => newNonce()));
    expect(nonces.size).toBe(20);
    expect([...nonces].every((n) => /^[A-Za-z0-9_-]{22}$/.test(n))).toBe(true);
  });
});

function fakeView() {
  const handlers: { message?: (raw: unknown) => Promise<void>; visibility?: () => void; dispose?: () => void } = {};
  const disposed: string[] = [];
  const webview = {
    options: {} as Record<string, unknown>,
    html: "",
    cspSource: PARTS.cspSource,
    asWebviewUri: (uri: Uri) => uri,
    postMessage: vi.fn(async () => true),
    onDidReceiveMessage: (cb: (raw: unknown) => Promise<void>) => {
      handlers.message = cb;
      return { dispose: () => void disposed.push("message") };
    },
  };
  const view = {
    webview,
    visible: true,
    onDidChangeVisibility: (cb: () => void) => {
      handlers.visibility = cb;
      return { dispose: () => void disposed.push("visibility") };
    },
    onDidDispose: (cb: () => void) => {
      handlers.dispose = cb;
    },
  };
  return { view, webview, handlers, disposed };
}

function fakeController() {
  const model = buildModel({ report: showReport(), explains: explains(), inspect: (k) => layers(k), trusted: true, profile: "Default" });
  let listener: ((m: typeof model) => void) | undefined;
  const subscription = { dispose: vi.fn() };
  const controller = {
    current: () => model,
    handle: vi.fn(async () => model),
    refresh: vi.fn(async () => model),
    onChange: vi.fn((l: typeof listener) => {
      listener = l;
      return subscription;
    }),
  };
  return { controller, model, push: (m: typeof model) => listener?.(m), subscription };
}

describe("the view provider", () => {
  beforeEach(() => stub.reset());

  it("limits resources to the media folder, enables only its own script, and posts renders to the page", () => {
    const { view, webview } = fakeView();
    const { controller, model, push } = fakeController();
    const provider = new SettingsViewProvider(Uri.file("C:\\ext"), controller as unknown as SettingsController);

    provider.resolveWebviewView(view as never);

    const options = webview.options as { enableScripts: boolean; localResourceRoots: Uri[] };
    expect(options.enableScripts).toBe(true);
    expect(options.localResourceRoots.map((u) => u.fsPath)).toEqual(["C:\\ext\\media"]);
    expect(webview.html).toContain("panel.js");
    expect(webview.html).toContain("script-src 'nonce-");
    push(model);
    expect(webview.postMessage).toHaveBeenCalledWith({ type: "render", model });
  });

  it("validates every message and forwards only valid ones to the controller", async () => {
    const { view, webview, handlers } = fakeView();
    const { controller } = fakeController();
    new SettingsViewProvider(Uri.file("C:\\ext"), controller as unknown as SettingsController).resolveWebviewView(view as never);

    await handlers.message!({ type: "set", control: "effort", value: "high", tool: null });
    expect(controller.handle).toHaveBeenCalledWith({ type: "set", control: "effort", value: "high", tool: null });

    await handlers.message!({ type: "set", control: "effort", value: "max" });
    await handlers.message!({ type: "exec", cmd: "calc" });
    expect(controller.handle).toHaveBeenCalledTimes(1);
    const rejected = webview.postMessage.mock.calls.at(-1)?.[0] as unknown as { model: { notice: { text: string } } };
    expect(rejected.model.notice.text).toContain("ignored");
  });

  it("refreshes when it becomes visible again and releases everything when disposed", () => {
    const { view, handlers, disposed } = fakeView();
    const { controller, subscription } = fakeController();
    new SettingsViewProvider(Uri.file("C:\\ext"), controller as unknown as SettingsController).resolveWebviewView(view as never);

    handlers.visibility!();
    expect(controller.refresh).toHaveBeenCalledTimes(1);
    view.visible = false;
    handlers.visibility!();
    expect(controller.refresh).toHaveBeenCalledTimes(1);

    handlers.dispose!();
    expect(subscription.dispose).toHaveBeenCalled();
    expect(disposed.sort()).toEqual(["message", "visibility"]);
    expect(emptyModel("Default", "windows").controls).toEqual([]);
  });
});
