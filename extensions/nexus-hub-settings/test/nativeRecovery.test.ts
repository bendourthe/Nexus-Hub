import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { patchNativeRecovery, RECOVERY_KEY, restartNativeProvider } from "../src/nativeRecovery";

const host = globalThis as typeof globalThis & { [key: symbol]: any };
beforeEach(() => { delete host[Symbol.for(RECOVERY_KEY)]; });
afterEach(() => { delete host[Symbol.for(RECOVERY_KEY)]; vi.useRealTimers(); });

it("registers renamed Codex lifecycle owners and restarts only the captured process", async () => {
  const source = 'class Renamed{internalNotificationHandlers=new Set;initialized=false;startCodexProcess(){this.internalNotificationHandlers.clear();this.initialized=true;this.starts=(this.starts||0)+1;return{success:true}}async initializeWebview(){}}';
  const patched = patchNativeRecovery("codex", source);
  expect(patchNativeRecovery("codex", patched)).toBe(patched);
  const connection = new Function(patched + ";return new Renamed")();
  connection.startCodexProcess();
  const handler = () => undefined; connection.internalNotificationHandlers.add(handler);
  const claude = vi.fn(); host[Symbol.for(RECOVERY_KEY)].claude = new Set([new WeakRef({channels: new Map(), restartSessionsWhenIdle: claude})]);
  await restartNativeProvider("codex");
  expect(connection.starts).toBe(2);
  expect(connection.internalNotificationHandlers.has(handler)).toBe(true);
  expect(claude).not.toHaveBeenCalled();
});

it("uses Claude's idle-boundary lifecycle while preserving busy sessions and other providers", async () => {
  const source = 'class Communication{channels=new Map;pendingChannels=new Map;cliRunsThroughWrapper(){return true}getCurrentState(){return{}}mayRestartNow(channel){return !channel.busy}closeChannel(id,resume){this.closed.push([id,resume])}restartSessionsWhenIdle(e){let t=this.cliRunsThroughWrapper();for(let n of this.pendingChannels.values())if(t||n.spawnedPid!==void 0)n.restartAtTurnBoundary=true;for(let[n,r]of this.channels){if(r.query===e)continue;if(this.mayRestartNow(r))this.closeChannel(n,true);else r.restartAtTurnBoundary=true}}}';
  const communication = new Function(patchNativeRecovery("claude", source) + ";return new Communication")();
  communication.closed = []; communication.getCurrentState();
  const idle = {query: {}}, busy = {query: {}, busy: true};
  communication.channels.set("idle", idle); communication.channels.set("busy", busy);
  const codex = vi.fn(); host[Symbol.for(RECOVERY_KEY)].codex = {startCodexProcess: codex};
  expect(await restartNativeProvider("claude")).toEqual({sessions: 2});
  expect(communication.closed).toEqual([["idle", true]]);
  expect(busy).toHaveProperty("restartAtTurnBoundary", true);
  expect(codex).not.toHaveBeenCalled();
});

it("deduplicates concurrent Codex restarts and waits for the native handshake", async () => {
  vi.useFakeTimers();
  const connection = {initialized: false, internalNotificationHandlers: new Set(), startCodexProcess: vi.fn(() => ({success: true}))};
  host[Symbol.for(RECOVERY_KEY)] = {codex: connection};
  const first = restartNativeProvider("codex"), second = restartNativeProvider("codex");
  expect(first).toBe(second); expect(connection.startCodexProcess).toHaveBeenCalledTimes(1);
  connection.initialized = true; await vi.advanceTimersByTimeAsync(50);
  await expect(first).resolves.toEqual({sessions: 1});
});

it("reports a failed native restart without claiming success or touching another provider", async () => {
  host[Symbol.for(RECOVERY_KEY)] = {codex: {internalNotificationHandlers: new Set(), startCodexProcess: () => ({success: false, errorMessage: "Native spawn failed"})}};
  await expect(restartNativeProvider("codex")).rejects.toThrow("Native spawn failed");
});

it("does not silently claim a Claude restart before its session owner is connected", async () => {
  await expect(restartNativeProvider("claude")).rejects.toThrow("native recovery is not connected");
});

it("retains native notification handlers even when starting Codex throws", async () => {
  const handler = () => undefined;
  const connection = {internalNotificationHandlers: new Set([handler]), startCodexProcess() { this.internalNotificationHandlers.clear(); throw new Error("spawn threw"); }};
  host[Symbol.for(RECOVERY_KEY)] = {codex: connection};
  await expect(restartNativeProvider("codex")).rejects.toThrow("spawn threw");
  expect(connection.internalNotificationHandlers.has(handler)).toBe(true);
});

it("preserves ambiguous, missing and partially patched provider code", () => {
  expect(() => patchNativeRecovery("codex", "class A{}" )).toThrow("unavailable");
  expect(() => patchNativeRecovery("codex", "class A{startCodexProcess(){}startCodexProcess(){}async initializeWebview(){}}" )).toThrow("ambiguous");
  expect(() => patchNativeRecovery("claude", `/*${RECOVERY_KEY}*/`)).toThrow("incomplete");
});
