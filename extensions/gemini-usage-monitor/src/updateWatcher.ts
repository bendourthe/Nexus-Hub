import * as vscode from "vscode";

/**
 * Offers a restart when this extension is replaced underneath a running window.
 *
 * VS Code loads extension code into the extension host at activation and never
 * hot-swaps it. `code --install-extension` is a filesystem operation: it changes
 * what would load NEXT time. So "successfully installed" and "running" are two
 * different states, and the gap between them is silent.
 *
 * Nexus-Hub's installers only print "Restart <editor> to activate" to a terminal the
 * user may not be looking at (installer.ps1, installer.sh), and VS Code's own
 * "Restart Extensions" affordance is unreliable for a CLI-side install - especially
 * because the installers uninstall before reinstalling, so the window sees a removal
 * followed by an addition rather than a version bump. Observed 2026-08-10: a 0.3.1
 * install reported success while the window kept running 0.3.0, and a bug fix was
 * tested against the build that still had the bug.
 *
 * The outgoing version is the only code in a position to notice, because it is the
 * code that is now stale. Hence a watcher here rather than a message in the installer.
 */

/** What the watcher observed and whether it has already spoken. */
export interface UpdateWatcherState {
  /** This extension was absent at some point, so an uninstall/reinstall is underway. */
  seenMissing: boolean;
  /** A restart has already been offered. One prompt per session, never a nag. */
  prompted: boolean;
}

export function initialWatcherState(): UpdateWatcherState {
  return { seenMissing: false, prompted: false };
}

export interface UpdateEvaluation {
  state: UpdateWatcherState;
  /** True exactly once, on the transition that proves the running code is stale. */
  prompt: boolean;
}

/**
 * Decides whether the running code has been superseded.
 *
 * Two distinct shapes have to be caught, which is why a version comparison alone is
 * not enough:
 *
 *   1. A version bump (0.3.0 -> 0.3.1). The installed version simply differs.
 *   2. A same-version reinstall. Both installers pass `--force` precisely so a
 *      rebuild at an unchanged version still lands, and the Nexus-Hub installer
 *      uninstalls first. The versions then match while the loaded code is stale, so
 *      the absence itself is the evidence.
 *
 * Pure, so both shapes are testable without an extension host.
 */
export function evaluateInstallChange(
  state: UpdateWatcherState,
  runningVersion: string,
  installedVersion: string | undefined
): UpdateEvaluation {
  if (state.prompted) return { state, prompt: false };

  // Mid-uninstall. Not an update yet - the reinstall is what completes it, and
  // prompting now would ask the user to restart into nothing.
  if (installedVersion === undefined) {
    return { state: { ...state, seenMissing: true }, prompt: false };
  }

  const replaced = installedVersion !== runningVersion || state.seenMissing;
  if (!replaced) return { state, prompt: false };

  return { state: { seenMissing: false, prompted: true }, prompt: true };
}

/** The message shown, kept here so the wording is asserted by test rather than by eye. */
export function restartMessage(displayName: string, runningVersion: string, installedVersion: string): string {
  return installedVersion === runningVersion
    ? `${displayName} was reinstalled. This window is still running the previous build - restart extensions to load it.`
    : `${displayName} was updated to ${installedVersion}. This window is still running ${runningVersion} - restart extensions to load it.`;
}

export const RESTART_ACTION = "Restart Extensions";

/**
 * Wires the watcher to the real extension host.
 *
 * `restartExtensionHost` rather than `reloadWindow`: reloading the window discards
 * the user's editor state to solve a problem confined to the extension host.
 */
export function registerUpdateWatcher(
  context: vscode.ExtensionContext,
  displayName: string
): void {
  const id = context.extension.id;
  const runningVersion = String((context.extension.packageJSON as { version?: unknown }).version ?? "");
  if (runningVersion === "") return;

  let state = initialWatcherState();
  context.subscriptions.push(
    vscode.extensions.onDidChange(() => {
      const installed = vscode.extensions.getExtension(id);
      const installedVersion = installed === undefined
        ? undefined
        : String((installed.packageJSON as { version?: unknown }).version ?? "");
      const evaluation = evaluateInstallChange(state, runningVersion, installedVersion);
      state = evaluation.state;
      if (!evaluation.prompt || installedVersion === undefined) return;

      void vscode.window
        .showInformationMessage(restartMessage(displayName, runningVersion, installedVersion), RESTART_ACTION)
        .then((action) => {
          if (action === RESTART_ACTION) void vscode.commands.executeCommand("workbench.action.restartExtensionHost");
        });
    })
  );
}
