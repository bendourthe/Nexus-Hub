import * as crypto from "node:crypto";
import * as vscode from "vscode";
import { SettingsController } from "./controller";
import { validateMessage } from "./messages";
import { ViewModel } from "./viewModel";

/**
 * The webview host. The page is a fixed shell; every value comes from the engine's
 * JSON and is drawn by `media/panel.js` with `textContent`, never `innerHTML`. The
 * content security policy allows exactly one script (the panel's, by per-load nonce)
 * and the extension's own stylesheet and logo, and no network at all.
 */

export interface HtmlParts {
  cspSource: string;
  nonce: string;
  scriptUri: string;
  styleUri: string;
  logoUri: string;
}

export function newNonce(): string {
  return crypto.randomBytes(16).toString("base64url");
}

function attr(text: string): string {
  return text.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

export function contentSecurityPolicy(cspSource: string, nonce: string): string {
  return [
    "default-src 'none'",
    `img-src ${cspSource}`,
    `style-src ${cspSource}`,
    `script-src 'nonce-${nonce}'`,
    "font-src 'none'",
    "connect-src 'none'",
    "frame-src 'none'",
    "form-action 'none'",
    "base-uri 'none'",
  ].join("; ");
}

export function buildHtml(parts: HtmlParts): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Security-Policy" content="${attr(contentSecurityPolicy(parts.cspSource, parts.nonce))}">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Nexus Hub Settings</title>
<link rel="stylesheet" href="${attr(parts.styleUri)}">
</head>
<body>
<main id="app" data-logo="${attr(parts.logoUri)}"><p>Loading the current settings...</p></main>
<div id="live-status" class="visually-hidden" role="status" aria-live="polite" aria-atomic="true"></div>
<div id="live-alert" class="visually-hidden" role="alert" aria-live="assertive" aria-atomic="true"></div>
<script nonce="${attr(parts.nonce)}" src="${attr(parts.scriptUri)}"></script>
</body>
</html>`;
}

export class SettingsViewProvider implements vscode.WebviewViewProvider {
  static readonly viewType = "nexusHubSettings.view";

  constructor(
    private readonly extensionUri: vscode.Uri,
    private readonly controller: SettingsController,
  ) {}

  resolveWebviewView(view: vscode.WebviewView): void {
    const media = vscode.Uri.joinPath(this.extensionUri, "media");
    const webview = view.webview;
    webview.options = { enableScripts: true, localResourceRoots: [media] };
    const uri = (name: string): string => webview.asWebviewUri(vscode.Uri.joinPath(media, name)).toString();
    webview.html = buildHtml({ cspSource: webview.cspSource, nonce: newNonce(), scriptUri: uri("panel.js"), styleUri: uri("panel.css"), logoUri: uri("logo.png") });

    const post = (model: ViewModel): void => {
      void webview.postMessage({ type: "render", model });
    };
    const subscription = this.controller.onChange(post);
    const received = webview.onDidReceiveMessage(async (raw: unknown) => {
      const checked = validateMessage(raw, this.controller.current());
      if (!checked.ok) {
        post({ ...this.controller.current(), notice: { level: "warn", text: `The panel sent a request that was ignored (${checked.reason}).` } });
        return;
      }
      await this.controller.handle(checked.message);
    });
    const visible = view.onDidChangeVisibility(() => {
      if (view.visible) {
        void this.controller.refresh();
      }
    });
    view.onDidDispose(() => {
      subscription.dispose();
      received.dispose();
      visible.dispose();
    });
  }
}
