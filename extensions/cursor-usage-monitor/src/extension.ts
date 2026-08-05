import { homedir } from "node:os";
import * as vscode from "vscode";
import {
  CursorUsageRuntime,
  type RuntimeDependencies
} from "./cursorUsageRuntime";
import {
  CursorCredentialStore,
  resolveCursorStatePath
} from "./providers/auth";
import {
  ConsentGate,
  type ConsentAnswer,
  type ConsentPrompt,
  type ConsentPromptRequest
} from "./providers/consent";
import { CursorUsageProvider } from "./providers/cursor";
import {
  createCredentialSource,
  resolveLiveCapability
} from "./providers/liveAccess";
import { CursorLiveUsageTransport } from "./providers/liveTransport";
import { CursorSessionAdapter } from "./providers/session";

export {
  COMMAND_IDS,
  CursorUsageRuntime,
  type RuntimeDependencies
} from "./cursorUsageRuntime";

const CONFIGURATION_SECTION = "cursorUsage";

let activeRuntime: CursorUsageRuntime | undefined;

/**
 * Composition root. Live transport is wired here but stays inert until the session
 * adapter reports a usable state database AND consent is granted, so the shipped
 * default reads nothing without an explicit answer from the user.
 */
export function activate(context: vscode.ExtensionContext): void {
  activeRuntime?.dispose();

  const secrets = new CursorCredentialStore(context.secrets);
  const consent = new ConsentGate(
    context.globalState,
    new WindowConsentPrompt()
  );
  const adapter = new CursorSessionAdapter({ statePath: resolveStatePath() });
  const liveAccess = { secrets, consent, adapter };

  // Resolved asynchronously after activation; the runtime reads it through a thunk
  // so activation stays synchronous and start-up is never blocked on a prompt.
  let liveCapable = false;

  const dependencies: RuntimeDependencies = {
    provider: new CursorUsageProvider({
      credentials: createCredentialSource(liveAccess),
      jsonTransport: new CursorLiveUsageTransport()
    }),
    liveTransportCapable: () => liveCapable,
    revokeLiveConsent: async () => {
      liveCapable = false;
      await consent.revoke();
    }
  };

  const runtime = new CursorUsageRuntime(context, dependencies);
  activeRuntime = runtime;
  context.subscriptions.push(runtime);
  runtime.start();

  void resolveLiveCapability(liveAccess).then((capable) => {
    if (activeRuntime !== runtime) {
      return;
    }
    liveCapable = capable;
    runtime.capabilityChanged();
  });
}

export function deactivate(): void {
  activeRuntime?.dispose();
  activeRuntime = undefined;
}

function resolveStatePath(): string {
  const configured = vscode.workspace
    .getConfiguration(CONFIGURATION_SECTION)
    .get<string>("stateDbPath", "")
    .trim();
  if (configured.length > 0) {
    return configured;
  }
  return (
    resolveCursorStatePath(process.platform, {
      home: homedir(),
      ...(process.env.APPDATA === undefined
        ? {}
        : { appData: process.env.APPDATA }),
      ...(process.env.XDG_CONFIG_HOME === undefined
        ? {}
        : { xdgConfigHome: process.env.XDG_CONFIG_HOME })
    }) ?? ""
  );
}

export const ALLOW_LABEL = "Allow live usage";
export const DENY_LABEL = "Keep manual only";

/**
 * A modal prompt that states the read boundary in full. The disclosure text comes
 * from `consent.ts` so what the user is shown and what the adapter does cannot
 * drift apart. Exported so the choice-to-answer mapping can be asserted directly:
 * treating a refusal as a grant would be a privacy defect, not a UI nit.
 */
export class WindowConsentPrompt implements ConsentPrompt {
  public async ask(request: ConsentPromptRequest): Promise<ConsentAnswer> {
    const detail = [
      "This will:",
      ...request.willRead.map((line) => `- ${line}`),
      "",
      "This will never:",
      ...request.willNotRead.map((line) => `- ${line}`)
    ].join("\n");

    const choice = await vscode.window.showInformationMessage(
      request.title,
      { modal: true, detail },
      ALLOW_LABEL,
      DENY_LABEL
    );
    if (choice === ALLOW_LABEL) {
      return "granted";
    }
    return choice === DENY_LABEL ? "declined" : "dismissed";
  }
}
