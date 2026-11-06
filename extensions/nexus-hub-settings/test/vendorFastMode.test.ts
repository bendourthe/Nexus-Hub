import { expect, it, vi } from "vitest";
import { CLAUDE_FAST_ADOPT, CODEX_DEFAULTS_HOOK } from "../src/vendorFastMode";
import { CLAUDE_UI_API } from "../src/vendorUiPatch";
import { CURSOR_FAST_ACTION, mapCursorFast, type CursorModel } from "../src/cursorEffort";

it("publishes Claude speed choices without writing effort flags or bypassing native commands", async () => {
  const comm = {config: Promise.resolve({keep: true}), getCurrentState: () => ({ready: true}), send: vi.fn()};
  const api = new Function("zre", CLAUDE_UI_API)({allComms: [comm]});
  await api.applyNexusDefaults({fastMode: true, fastRevision: "fast-1"});
  expect(comm.send).toHaveBeenCalledWith({type: "request", channelId: "", requestId: "", request: {type: "update_state", state: {ready: true}, config: {keep: true, nexusFast: {value: true, revision: "fast-1"}}}});
  await expect(api.applyNexusFastMode("true", "bad")).rejects.toThrow("Invalid");
});

it("uses Claude's native fast command only on supported models and preserves later manual choices", async () => {
  const apply = new Function("r", CLAUDE_FAST_ADOPT);
  const store = {connection: {value: {claudeConfig: {value: {ready: true}}}}, currentModelSupportsFastMode: {value: false}, fastModeState: {value: "off"}, send: vi.fn(), applySettings: vi.fn(), queueSettingsApply: vi.fn(async (work: () => Promise<void>) => work())};
  apply.call(store, {nexusFast: {value: true, revision: "on"}}); await Promise.resolve(); expect(store.send).not.toHaveBeenCalled();
  store.currentModelSupportsFastMode.value = true;
  apply.call(store, {nexusFast: {value: true, revision: "on"}}); await Promise.resolve();
  expect(store.send).toHaveBeenCalledWith("/fast on", undefined, false, {kind: "human"}, {cancelParkedDialogs: false});
  apply.call(store, {nexusFast: {value: true, revision: "on"}}); await Promise.resolve(); expect(store.send).toHaveBeenCalledTimes(1);
  store.fastModeState.value = "on";
  apply.call(store, {nexusFast: {value: false, revision: "off"}}); await Promise.resolve();
  expect(store.send).toHaveBeenLastCalledWith("/fast off", undefined, false, {kind: "human"}, {cancelParkedDialogs: false});
  store.fastModeState.value = "off";
  apply.call(store, {nexusFast: {value: false, revision: "blank-off"}}); await Promise.resolve();
  expect(store.send).toHaveBeenCalledTimes(3);
});

it("combines Codex effort and speed atomically while keeping manual changes independent", async () => {
  const listeners: ((event: {data: unknown; stopImmediatePropagation(): void}) => void)[] = [];
  const ref: {current: unknown} = {current: null};
  let cleanup = () => {}, settings = {model: "same-model", reasoningEffort: "medium", isLoading: false};
  const select = vi.fn(async (_model: string, _effort: string, _options: unknown) => true);
  const catalog = {data: {models: [{model: "same-model", supportedReasoningEfforts: ["low", "medium", "high"].map(reasoningEffort => ({reasoningEffort})), serviceTiers: [{id: "priority", name: "Fast"}]}]}};
  const hook = new Function("window", "Rt", "it", CODEX_DEFAULTS_HOOK + ";return nexusUseDefaultsBridge;")(
    {addEventListener: (_type: string, callback: typeof listeners[number]) => listeners.push(callback)},
    {useRef: () => ref, useEffect: (effect: () => () => void) => {cleanup = effect();}}, () => catalog,
  );
  const render = (id: string) => {cleanup(); hook(settings, select, "local", id);};
  const send = async (effortRevision: string, fastMode: boolean, fastRevision: string) => {
    listeners.forEach(callback => callback({data: {type: "nexus-defaults-v2", effort: "high", effortRevision, fastMode, fastRevision}, stopImmediatePropagation() {}}));
    for (let i = 0; i < 12; i++) { await Promise.resolve(); }
  };
  render("one"); await send("e1", true, "f1");
  expect(select).toHaveBeenLastCalledWith("same-model", "high", {persistAsDefault: false, serviceTier: "priority"});
  settings = {...settings, reasoningEffort: "low"}; render("one");
  await send("e1", true, "f1"); expect(select).toHaveBeenCalledTimes(1);
  await send("e1", false, "f2");
  expect(select).toHaveBeenLastCalledWith("same-model", "low", {persistAsDefault: false, serviceTier: "default"});
  render("two"); await send("e1", false, "f2");
  expect(select).toHaveBeenLastCalledWith("same-model", "high", {persistAsDefault: false, serviceTier: "default"});
  render("one"); await send("e1", false, "f2"); expect(select).toHaveBeenCalledTimes(3);
  await send("e2", true, "f3");
  expect(select).toHaveBeenLastCalledWith("same-model", "high", {persistAsDefault: false, serviceTier: "priority"});
});

const model: CursorModel = {name: "same-model", parameterDefinitions: [{id: "fast", name: "Fast", parameterType: {booleanParameter: {values: [{value: "true"}, {value: "false"}]}}}]};
const selections = [{modelId: model.name, parameters: [{id: "fast", value: "false"}, {id: "effort", value: "high"}, {id: "context", value: "256k"}]}];
it("uses only Cursor's advertised fast parameter and compatible native variants", () => {
  const mapped = mapCursorFast([model], selections, true);
  expect(mapped.supported).toBe(1);
  expect(mapped.selectedModels[0]!.parameters).toEqual([{id: "effort", value: "high"}, {id: "context", value: "256k"}, {id: "fast", value: "true"}]);
  expect(selections[0]!.parameters[0]!.value).toBe("false");
  expect(mapCursorFast([model], selections, true, () => false).selectedModels).toEqual(selections);
  expect(mapCursorFast([], selections, true).supported).toBe(0);
  expect(() => mapCursorFast([model], selections, "true" as never)).toThrow("Invalid");
});

it("updates Cursor speed once, keeps manual speed, preserves effort and reapplies on a new revision", () => {
  type Config = {modelName: string; maxMode: boolean; selectedModels: typeof selections};
  const initial: Config = {modelName: model.name, maxMode: false, selectedModels: structuredClone(selections)};
  const handle = {composerId: "one", data: {modelConfig: structuredClone(initial)}};
  const native = {
    getAvailableDefaultModels: () => [model], getModelConfig: (_surface: string) => initial,
    deriveSelectedModels: (config: Config) => config.selectedModels,
    resolveModelParametersForSubmission: (_id: string, parameters: unknown) => parameters,
    getEffectiveModelConfigForComposer: (value: typeof handle) => value.data.modelConfig,
    setModelConfigForComposer: (value: typeof handle, change: Partial<Config>, _surface?: unknown, _options?: unknown) => {value.data.modelConfig = {...value.data.modelConfig, ...change};},
  };
  let action: {run(accessor: unknown, args: unknown): unknown};
  new Function("ut", "It", "zb", "to", "g3i", CURSOR_FAST_ACTION + "true;")(
    (Action: new () => typeof action) => {action = new Action();}, class {constructor(_options: unknown) {}}, "models", "data", () => undefined,
  );
  const data = {selectedComposerIds: ["one"], getHandleIfLoaded: () => handle};
  const accessor = {get: (token: string) => token === "models" ? native : data};
  expect(action!.run(accessor, {value: true, revision: "first"})).toEqual({ready: true, updated: 1});
  const manual = structuredClone(handle.data.modelConfig.selectedModels);
  manual[0]!.parameters.find(item => item.id === "fast")!.value = "false";
  native.setModelConfigForComposer(handle, {selectedModels: manual}, undefined, {updateGlobalConfig: true});
  expect(action!.run(accessor, {value: true, revision: "first"})).toEqual({ready: true, updated: 0});
  action!.run(accessor, {value: true, revision: "apply-all"});
  expect(handle.data.modelConfig.selectedModels[0]!.parameters.find(item => item.id === "fast")!.value).toBe("true");
  expect(handle.data.modelConfig.selectedModels[0]!.parameters.find(item => item.id === "effort")!.value).toBe("high");
  expect(initial.selectedModels[0]!.parameters[0]!.value).toBe("false");
  expect(native.getModelConfig("composer").selectedModels[0]!.parameters.find(item => item.id === "fast")!.value).toBe("true");
});
