/**
 * Opening Antigravity's own Models & Usage screen as a manual cross-check.
 *
 * Kept free of the `vscode` module so the fallback order can be unit-tested.
 */

export type ExecuteCommand = (command: string, ...args: unknown[]) => PromiseLike<unknown>;

/**
 * Commands tried in order; the first that runs without throwing wins.
 *
 * 1. `antigravity.openSettings` with a target screen: current Antigravity IDE builds
 *    register it in their bundled `agy` extension and pass the argument as the
 *    settings editor's `targetScreen`, so "Models" lands on Models & Usage.
 * 2. The older `workbench.action.openAntigravitySettingsWithId` with the screen as
 *    its second argument, which earlier builds honored. Current builds still have it
 *    but only open the plain settings filtered by a setting id, which is why it is
 *    no longer first.
 * 3. The settings window itself, when neither knows the screen.
 */
export const USAGE_PAGE_ATTEMPTS: ReadonlyArray<readonly [string, ...unknown[]]> = [
  ["antigravity.openSettings", "Models"],
  ["workbench.action.openAntigravitySettingsWithId", undefined, "Models"],
  ["workbench.action.openAntigravitySettings"],
];

/** Open the Models & Usage screen; returns the command that succeeded, or undefined. */
export async function openUsagePage(execute: ExecuteCommand): Promise<string | undefined> {
  for (const [command, ...args] of USAGE_PAGE_ATTEMPTS) {
    try {
      await execute(command, ...args);
      return command;
    } catch {
      // Unknown in this build, or it failed: try the next one.
    }
  }
  return undefined;
}
