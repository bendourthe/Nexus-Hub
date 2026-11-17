import { afterEach, expect, it, vi } from "vitest";
import { applyNativeEffort, patchNativeEffortView, CODEX_NATIVE_HOOK, EFFORT_MARKER } from "../src/nativeEffort";
import { RECOVERY_KEY } from "../src/nativeRecovery";

const host = globalThis as unknown as {[key: symbol]: unknown};
afterEach(() => { delete host[Symbol.for(RECOVERY_KEY)]; });
const tick = async () => { for (let i = 0; i < 12; i++) { await Promise.resolve(); } };

it("updates each existing Claude channel, initializes later channels, and preserves subsequent manual choices", async () => {
  const setter = vi.fn(async (_id, settings) => ({effort: settings.effortLevel, ultracode: settings.ultracode}));
  const owner = {channels: new Map([["one", {}], ["two", {}]]), writeUserSettingsAndPush: setter, config: Promise.resolve({keep: true}), getCurrentState: () => ({keep: true}), send: vi.fn()};
  host[Symbol.for(RECOVERY_KEY)] = {claude: new Set([new WeakRef(owner)])};
  expect(await applyNativeEffort("claude", "high", "one")).toEqual({updated: 2});
  expect(setter).toHaveBeenCalledWith("one", {effortLevel: "high", ultracode: false}, true);
  expect(await applyNativeEffort("claude", "high", "one")).toEqual({updated: 0});
  owner.channels.set("three", {});
  expect(await applyNativeEffort("claude", "high", "one")).toEqual({updated: 1});
  expect(await applyNativeEffort("claude", "ultra", "two")).toEqual({updated: 3});
  expect(setter).toHaveBeenLastCalledWith("three", {effortLevel: "xhigh", ultracode: true}, true);
  expect(owner.send).toHaveBeenLastCalledWith(expect.objectContaining({request: expect.objectContaining({config: {keep: true, nexusEffort: {effort: "ultra", revision: "two"}}})}));
});

it("does not claim Claude applied an effort rejected by native readback", async () => {
  const owner = {channels: new Map([["one", {}]]), writeUserSettingsAndPush: vi.fn(async () => ({effort: "low"})), config: Promise.resolve({}), getCurrentState: () => ({}), send: vi.fn()};
  host[Symbol.for(RECOVERY_KEY)] = {claude: new Set([new WeakRef(owner)])};
  await expect(applyNativeEffort("claude", "high", "one")).rejects.toThrow("did not confirm");
  expect(owner.send).not.toHaveBeenCalled();
});

function browser() {
  let message: (event: unknown) => void = () => undefined;
  const effects: (() => void)[] = [];
  const refs: {current: unknown}[] = []; let at = 0;
  const react = {useRef: () => refs[at++] ?? (refs[at - 1] = {current: undefined}), useEffect: (effect: () => void) => {effects.push(effect);} };
  const use = new Function("window", CODEX_NATIVE_HOOK + ";return nexusUseNativeEffort")({addEventListener: (_name: string, listener: typeof message) => {message = listener;}});
  const select = vi.fn(async () => true), next = vi.fn(async () => true);
  const owner = {hostId: "local", modelSettings: {model: "same-model", reasoningEffort: "medium", isLoading: false}, setModelAndReasoningEffort: select, setModelAndReasoningEffortForNextTurn: next};
  const query = () => ({data: {models: [{model: "same-model", supportedReasoningEfforts: ["low", "medium", "high", "xhigh"].map(reasoningEffort => ({reasoningEffort}))}]}});
  return {owner, select, next, render: (session: string | null) => {at = 0; use(react, query, owner, session); effects.splice(0).forEach(effect => effect());}, send: (effort: string, revision: string) => message({data: {type: EFFORT_MARKER, effort, revision}, stopImmediatePropagation() {}})};
}

it("changes an already-open Codex conversation through its next-turn setter, maps supported effort, and preserves its model", async () => {
  const page = browser(); page.render("existing-thread");
  page.send("ultra", "first"); await tick();
  expect(page.next).toHaveBeenCalledWith("same-model", "xhigh", {threadSettings: {}});
  expect(page.select).not.toHaveBeenCalled();
  page.owner.modelSettings.reasoningEffort = "low";
  page.send("ultra", "first"); await tick(); expect(page.next).toHaveBeenCalledTimes(1);
  page.send("high", "second"); await tick(); expect(page.next).toHaveBeenLastCalledWith("same-model", "high", {threadSettings: {}});
});

it("changes Codex drafts without persisting a separate provider default", async () => {
  const page = browser(); page.render(null); page.send("high", "one"); await tick();
  expect(page.select).toHaveBeenCalledWith("same-model", "high", {persistAsDefault: false}); expect(page.next).not.toHaveBeenCalled();
});

it("serializes Codex updates and applies the latest revision after an older update finishes", async () => {
  const page = browser(); let finish: (value: boolean) => void = () => undefined;
  page.next.mockImplementationOnce(() => new Promise<boolean>(resolve => {finish = resolve;}));
  page.render("thread"); page.send("high", "first"); await tick(); page.send("low", "second");
  expect(page.next).toHaveBeenCalledTimes(1); finish(true); await tick();
  expect(page.next).toHaveBeenCalledTimes(2); expect(page.next).toHaveBeenLastCalledWith("same-model", "low", {threadSettings: {}});
});

it("does not loop a refused Codex setter until a new revision is requested", async () => {
  const page = browser(); page.next.mockResolvedValue(false); page.render("thread");
  page.send("high", "first"); await tick(); page.send("high", "first"); await tick(); expect(page.next).toHaveBeenCalledTimes(1);
  page.send("high", "second"); await tick(); expect(page.next).toHaveBeenCalledTimes(2);
});

it("leaves remote Codex sessions unchanged", async () => {
  const page = browser(); page.owner.hostId = "remote"; page.render("thread"); page.send("high", "first"); await tick(); expect(page.next).not.toHaveBeenCalled();
});

it("discovers Codex aliases from semantic native properties and preserves ambiguous sources", () => {
  const source = 'function Other({listModelsData:unused}){}function Catalog(){let{data:x,isLoading:y}=query(z);return {listModelsData:x}}function Select(e,t){let session=e===void 0?null:e;let context=(0,React.use)(Context);let result;return result={...base,modelSettings:settings,setModelAndReasoningEffortForNextTurn:next,setModelAndReasoningEffort:draft},result}';
  const patched = patchNativeEffortView("codex", source);
  expect(patched).toContain('nexusUseNativeEffort(React,query,result,session)');
  expect(patchNativeEffortView("codex", patched)).toBe(patched);
  expect(() => patchNativeEffortView("codex", source + source)).toThrow("ambiguous");
  expect(() => patchNativeEffortView("codex", "changed source")).toThrow("unavailable");
  expect(() => patchNativeEffortView("codex", "/*" + EFFORT_MARKER + "*/ changed source")).toThrow("incomplete");
});

it("updates Claude through its revision-aware native signal instead of overwriting every render", () => {
  const source = 'adoptAppliedEffort();let r=this.connection.value?.config.value,s=r?.claudeSettings?.applied,a=s.effort;';
  const patched = patchNativeEffortView("claude", source);
  expect(patched).toContain('this.nexusEffortRevision!==nexus.revision'); expect(patchNativeEffortView("claude", patched)).toBe(patched);
  expect(() => patchNativeEffortView("claude", source + source)).toThrow("ambiguous");
  const renamed = source.replaceAll("let r=", "let config=").replaceAll("r?.", "config?.");
  const patchedRenamed = patchNativeEffortView("claude", renamed);
  expect(patchedRenamed).toContain("config?.nexusEffort"); expect(patchNativeEffortView("claude", patchedRenamed)).toBe(patchedRenamed);
});
