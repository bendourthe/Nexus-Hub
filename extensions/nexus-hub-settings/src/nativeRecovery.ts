/** Provider-owned lifecycle recovery, registered without minified variable names or version allowlists. */
export type RecoveryProvider = "claude" | "codex";
export const RECOVERY_KEY = "nexusHub.nativeRecovery.v1";
interface Connection {
  startCodexProcess(): { success: boolean; errorMessage?: string };
  initialized: boolean;
  internalNotificationHandlers: Set<unknown>;
  fatalError?: Error | null;
}
interface ClaudeSession {
  channels: Map<unknown, unknown>;
  shutDown?: boolean;
  restartSessionsWhenIdle(): void;
}
interface Registry {
  codex?: Connection;
  codexView?: { fatalError: Error | null; mostRecentErrorLog?: string | null };
  claude?: Set<WeakRef<ClaudeSession>>;
  pending?: Partial<Record<RecoveryProvider, Promise<{ sessions: number }>>>;
}
function registry(): Registry {
  const host = globalThis as typeof globalThis & { [key: symbol]: Registry | undefined };
  return host[Symbol.for(RECOVERY_KEY)] ??= {};
}
const store = `(globalThis[Symbol.for("${RECOVERY_KEY}")]??={})`;
const captures = {
  codex: `{/*${RECOVERY_KEY}:codex*/${store}.codex=this;}`,
  codexView: `{/*${RECOVERY_KEY}:view*/${store}.codexView=this;}`,
  claude: `{/*${RECOVERY_KEY}:claude*/const state=${store};state.claude??=new Set;if(!this[Symbol.for("${RECOVERY_KEY}.registered")]){Object.defineProperty(this,Symbol.for("${RECOVERY_KEY}.registered"),{value:true});state.claude.add(new WeakRef(this))}}`,
};

/** Unique native method signatures are the compatibility contract; changed shapes are preserved untouched. */
export function patchNativeRecovery(provider: RecoveryProvider, source: string): string {
  const hooks = provider === "codex"
    ? [{ pattern: /\bstartCodexProcess\(\)\{/g, code: captures.codex }, { pattern: /\basync initializeWebview\([^)]*\)\{/g, code: captures.codexView }]
    : [{ pattern: /\bgetCurrentState\(\)\{/g, code: captures.claude }];
  if (source.includes(RECOVERY_KEY)) {
    if (hooks.every(hook => source.includes(hook.code))) { return source; }
    throw new Error("The provider recovery registration is incomplete; the current file was preserved.");
  }
  if (provider === "claude" && !source.includes("restartSessionsWhenIdle(")) { throw new Error("Claude's session lifecycle is unavailable; its current file was preserved."); }
  let result = source;
  for (const hook of hooks) {
    const matches = [...result.matchAll(hook.pattern)];
    if (matches.length !== 1) { throw new Error("The provider lifecycle is ambiguous or unavailable; its current file was preserved."); }
    const match = matches[0]!;
    const at = match.index! + match[0].length;
    result = result.slice(0, at) + hook.code + result.slice(at);
  }
  return result;
}

export function restartNativeProvider(provider: RecoveryProvider): Promise<{ sessions: number }> {
  const state = registry();
  state.pending ??= {};
  const pending = state.pending[provider];
  if (pending) { return pending; }
  const work = (async () => {
    if (provider === "claude") {
      if (!state.claude) { throw new Error("Claude's native recovery is not connected. No other extension was restarted."); }
      let sessions = 0;
      for (const reference of state.claude ?? []) {
        const session = reference.deref();
        if (!session || session.shutDown) { state.claude!.delete(reference); continue; }
        if (typeof session.restartSessionsWhenIdle !== "function" || !(session.channels instanceof Map)) { throw new Error("Claude's native session lifecycle changed. No other extension was restarted."); }
        sessions += session.channels.size;
        session.restartSessionsWhenIdle();
      }
      return { sessions };
    }
    const connection = state.codex;
    if (!connection || typeof connection.startCodexProcess !== "function" || !(connection.internalNotificationHandlers instanceof Set)) {
      throw new Error("Codex's native recovery is not connected. No other extension was restarted.");
    }
    // Keep the provider's initialization broadcasts and notification subscribers across its own teardown.
    const handlers = [...connection.internalNotificationHandlers];
    if (state.codexView) { state.codexView.fatalError = null; state.codexView.mostRecentErrorLog = null; }
    let result: { success: boolean; errorMessage?: string };
    try { result = connection.startCodexProcess(); }
    finally { for (const handler of handlers) { connection.internalNotificationHandlers.add(handler); } }
    if (!result.success) { throw new Error(result.errorMessage || "Codex could not restart."); }
    const deadline = Date.now() + 15_000;
    while (!connection.initialized) {
      if (connection.fatalError) { throw connection.fatalError; }
      if (Date.now() >= deadline) { throw new Error("Codex did not finish restarting within 15 seconds."); }
      await new Promise(resolve => setTimeout(resolve, 50));
    }
    return { sessions: 1 };
  })();
  state.pending[provider] = work;
  void work.then(() => { delete state.pending![provider]; }, () => { delete state.pending![provider]; });
  return work;
}
