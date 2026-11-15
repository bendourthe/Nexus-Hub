import { expect, it, vi } from "vitest";
import { CLAUDE_RECOVERY_API, CODEX_RECOVERY_API, CODEX_SESSION_TRACKER, patchCodexRecovery } from "../src/vendorRecovery";

it("restarts only Codex, preserves internal handlers and waits for initialization before refreshing all tabs", async () => {
  const handler = () => undefined;
  const provider = {fatalError: new Error("old"), nexusRefreshPanels: vi.fn().mockResolvedValue({refreshed: 2})};
  const connection = {initialized: false, internalNotificationHandlers: new Set([handler]), startCodexProcess: vi.fn(() => {
    connection.internalNotificationHandlers.clear(); connection.initialized = true; return {success: true};
  })};
  const api = new Function("$e", "v", `return{${CODEX_RECOVERY_API}}`)(provider, connection);
  expect(await api.nexusRestartProvider()).toEqual({refreshed: 2});
  expect(connection.startCodexProcess).toHaveBeenCalledTimes(1);
  expect(connection.internalNotificationHandlers.has(handler)).toBe(true);
  expect(provider.fatalError).toBeNull(); expect(provider.nexusRefreshPanels).toHaveBeenCalledWith(true);
  await api.nexusRefreshTab(); expect(provider.nexusRefreshPanels).toHaveBeenLastCalledWith(false);
});

it("keeps failed restarts visible and does not refresh against a failed process", async () => {
  const provider = {nexusRefreshPanels: vi.fn()};
  const connection = {internalNotificationHandlers: new Set(), startCodexProcess: () => ({success: false, errorMessage: "Unavailable"})};
  const api = new Function("$e", "v", `return{${CODEX_RECOVERY_API}}`)(provider, connection);
  await expect(api.nexusRestartProvider()).rejects.toThrow("Unavailable"); expect(provider.nexusRefreshPanels).not.toHaveBeenCalled();
});

it("uses Claude's idle-boundary session restart without touching other providers", async () => {
  const comm = {channels: new Map([["session", {}]]), restartSessionsWhenIdle: vi.fn()};
  const api = new Function("zre", `return{${CLAUDE_RECOVERY_API}}`)({allComms: [comm]});
  expect(await api.nexusRestartProvider()).toEqual({sessions: 1}); expect(comm.restartSessionsWhenIdle).toHaveBeenCalledTimes(1);
});

it("tracks only valid local conversation routes through the existing native message bus", () => {
  const bus = {postMessage: vi.fn()}, init = vi.fn();
  const effect = new Function("Rt", "hostId", "sessionId", "nexusInitVscode", "nexusVscode", CODEX_SESSION_TRACKER);
  const react = {useEffect: (fn: () => void) => fn()};
  for (const [host, id] of [["remote", "12345678-1234-1234-1234-123456789abc"], ["local", "../invalid"]]) { effect(react, host, id, init, bus); }
  expect(bus.postMessage).not.toHaveBeenCalled();
  effect(react, "local", "12345678-1234-1234-1234-123456789abc", init, bus);
  expect(bus.postMessage).toHaveBeenCalledWith({type: "nexus-panel-session", id: "12345678-1234-1234-1234-123456789abc"});
});

it("defers hidden renderer timers, replaces listeners on refresh and retains the current conversation", async () => {
  const source = 'async initializeWebview(e,r,n,o){let i=0;let s=new K2;this.registerClientCoordinationForWebview(e,n,s);this.workerBusMessageHandler.registerWebview(e);let a=e.onDidReceiveMessage(u=>{if(s.markMessageReceived(),u.type==="ready")o?.()});this.subscriptions.push(a,n(()=>{s.dispose(),this.chunkedMessageSender.dispose(e)})),e.html=await this.getWebviewContent(e),s.start()}';
  const timers: {start: ReturnType<typeof vi.fn>; dispose: ReturnType<typeof vi.fn>}[] = [];
  class Timer {start = vi.fn(); dispose = vi.fn(); markMessageReceived = vi.fn(); constructor() {timers.push(this);} }
  const patched = patchCodexRecovery(source);
  const methods = new Function("K2", `return new class{${patched}}`)(Timer);
  let listener: (event: unknown) => void = () => undefined, visible = () => undefined;
  const removed = vi.fn(), panel = {active: true, visible: false, webview: {html: "", onDidReceiveMessage: (cb: typeof listener) => {listener = cb; return {dispose: removed};}}, onDidDispose: () => ({dispose: vi.fn()}), onDidChangeViewState: (cb: () => void) => {visible = cb; return {dispose: vi.fn()};}};
  const state = {ready: true, pendingMessages: [], initialRoute: "/local/old"};
  const provider = Object.assign(methods, {subscriptions: [], editorPanels: new Map([[panel, state]]), isPanelAlive: () => true, findPanelByWebview: () => panel, registerClientCoordinationForWebview: vi.fn(), clearPendingRequestsForWebview: vi.fn(), disposeClientCoordinationForWebview: vi.fn(), workerBusMessageHandler: {registerWebview: vi.fn(), unregisterWebview: vi.fn()}, chunkedMessageSender: {dispose: vi.fn()}, getWebviewContent: async () => state.initialRoute, onPanelReady: vi.fn()});
  await provider.initializeWebview(panel.webview, "panel", panel.onDidDispose);
  expect(timers[0].start).not.toHaveBeenCalled(); panel.visible = true; visible(); expect(timers[0].start).toHaveBeenCalledTimes(1);
  listener({type: "nexus-panel-session", id: "12345678-1234-1234-1234-123456789abc"});
  await provider.nexusRefreshPanels(false);
  expect(removed).toHaveBeenCalledTimes(1); expect(timers[0].dispose).toHaveBeenCalledTimes(1);
  expect(panel.webview.html).toBe("/local/12345678-1234-1234-1234-123456789abc"); expect(timers[1].start).toHaveBeenCalledTimes(1);
  for (const subscription of provider.subscriptions) { subscription.dispose(); }
  expect(removed).toHaveBeenCalledTimes(2);
});
