import { describe, expect, it } from "vitest";
import { CURSOR_EFFORT_ACTION, CURSOR_WORKBENCH_HASH, cursorProductManifest, mapCursorEffort, type CursorModel } from "../src/cursorEffort";

const model: CursorModel = { name: "same-model", parameterDefinitions: [{ id: "effort", name: "Reasoning effort", parameterType: { enumParameter: { values: ["low", "medium", "high", "xhigh"].map(value => ({ value })) } } }] };
const selection = [{ modelId: "same-model", parameters: [{ id: "effort", value: "high" }, { id: "speed", value: "standard" }] }];

describe("Cursor native effort mapping", () => {
  it("updates only the exact workbench integrity entry and preserves all other checks", () => {
    const checksum = Buffer.from(CURSOR_WORKBENCH_HASH, "hex").toString("base64").replace(/=+$/, "");
    const original = JSON.stringify({applicationName: "cursor", checksums: {"vs/workbench/workbench.desktop.main.js": checksum, "other-file": "unchanged"}, extra: true}, null, 2);
    const after = JSON.parse(cursorProductManifest(original, "a".repeat(64)));
    expect(after.checksums["vs/workbench/workbench.desktop.main.js"]).toBe(Buffer.from("a".repeat(64), "hex").toString("base64").replace(/=+$/, ""));
    expect(after.checksums["other-file"]).toBe("unchanged");
    expect(after.extra).toBe(true);
    expect(() => cursorProductManifest(original.replace(checksum, "unknown"), "a".repeat(64))).toThrow("preserved");
    expect(() => cursorProductManifest(original, "bad")).toThrow("preserved");
  });
  it("maps only advertised levels and preserves the model and unrelated parameters", () => {
    const mapped = mapCursorEffort([model], selection, "ultra");
    expect(mapped.supported).toBe(1);
    expect(mapped.selectedModels).toEqual([{ modelId: "same-model", parameters: [{ id: "effort", value: "xhigh" }, { id: "speed", value: "standard" }] }]);
    expect(selection[0]!.parameters[0]!.value).toBe("high");
  });
  it("uses native display names without inventing native values", () => {
    const native = { ...model, parameterDefinitions: [{ id: "thinking_level", parameterType: { enumParameter: { values: [{ value: "native-1", displayName: "Medium" }, { value: "native-2", displayName: "Extra high" }] } } }] };
    expect(mapCursorEffort([native], [{ modelId: model.name }], "low").selectedModels[0]!.parameters).toEqual([{ id: "thinking_level", value: "native-1" }]);
  });
  it("falls back when the native variant would require unrelated changes", () => {
    const mapped = mapCursorEffort([model], selection, "ultra", (_model, parameters) => parameters.find(item => item.id === "effort")?.value !== "xhigh");
    expect(mapped.selectedModels[0]!.parameters!.find(item => item.id === "effort")?.value).toBe("high");
  });
  it("leaves Auto, boolean thinking switches and unknown levels alone", () => {
    expect(mapCursorEffort([], selection, "low")).toEqual({ supported: 0, selectedModels: selection });
    const unknown = { ...model, parameterDefinitions: [{ id: "effort", parameterType: { enumParameter: { values: [{ value: "unknown" }] } } }] };
    expect(mapCursorEffort([unknown], selection, "low").supported).toBe(0);
    expect(() => mapCursorEffort([model], selection, "invalid")).toThrow("Invalid Nexus effort");
  });
});

it("updates each open session once, preserves manual choices, reapplies and seeds new sessions", () => {
  let Action: { new(): { run(accessor: { get(token: string): unknown }, args: unknown): unknown } } | undefined;
  const handles = new Map(["one", "two"].map(id => [id, { composerId: id, data: { modelConfig: { modelName: "same-model", maxMode: false, selectedModels: structuredClone(selection) } } }]));
  const storedDefault = { modelName: "same-model", maxMode: false, selectedModels: structuredClone(selection) };
  const modelService = {
    getAvailableDefaultModels: () => [model],
    getModelConfig: (_surface: string) => storedDefault,
    deriveSelectedModels: (config: typeof storedDefault) => config.selectedModels,
    resolveModelParametersForSubmission: (_id: string, parameters: unknown) => parameters,
    getEffectiveModelConfigForComposer: (handle: { data: { modelConfig: typeof storedDefault } }) => handle.data.modelConfig,
    setModelConfigForComposer: (handle: { data: { modelConfig: typeof storedDefault } }, change: { selectedModels: typeof selection }, _surface: unknown, options: unknown) => {
      expect(options).toHaveProperty("updateGlobalConfig");
      handle.data.modelConfig = { ...handle.data.modelConfig, ...change };
    },
  };
  const dataService = { selectedComposerIds: ["one", "two"], getHandleIfLoaded: (id: string) => handles.get(id) };
  new Function("ut", "It", "zb", "to", "g3i", CURSOR_EFFORT_ACTION + "true;")((action: typeof Action) => { Action = action; }, class { constructor(_args: unknown) {} }, "models", "data", () => undefined);
  const action = new Action!();
  const accessor = { get: (token: string) => token === "models" ? modelService : dataService };
  expect(action.run(accessor, { effort: "low", revision: "first" })).toEqual({ ready: true, updated: 2, unsupported: 0 });
  const manual = structuredClone(handles.get("one")!.data.modelConfig.selectedModels);
  manual[0]!.parameters[0]!.value = "medium";
  modelService.setModelConfigForComposer(handles.get("one")!, {selectedModels: manual}, undefined, {updateGlobalConfig: true});
  storedDefault.selectedModels[0]!.parameters[0]!.value = "medium";
  expect(action.run(accessor, { effort: "low", revision: "first" })).toEqual({ ready: true, updated: 0, unsupported: 0 });
  expect(handles.get("one")!.data.modelConfig.selectedModels[0]!.parameters[0]!.value).toBe("medium");
  expect(modelService.getModelConfig("composer").selectedModels[0]!.parameters[0]!.value).toBe("low");
  expect(storedDefault.selectedModels[0]!.parameters[0]!.value).toBe("medium");
  handles.set("one", structuredClone(handles.get("one")!));
  expect(action.run(accessor, { effort: "low", revision: "first" })).toEqual({ ready: true, updated: 0, unsupported: 0 });
  const fresh = { composerId: "new", data: { modelConfig: modelService.getModelConfig("composer") } };
  handles.set("new", fresh); dataService.selectedComposerIds.push("new");
  action.run(accessor, { effort: "low", revision: "first" });
  expect(fresh.data.modelConfig.selectedModels[0]!.parameters[0]!.value).toBe("low");
  action.run(accessor, { effort: "low", revision: "apply-all" });
  expect(handles.get("one")!.data.modelConfig.selectedModels[0]!.parameters[0]!.value).toBe("low");
  handles.set("one", {composerId: "one", data: {modelConfig: {...storedDefault, selectedModels: manual}}});
  action.run(accessor, { effort: "low", revision: "apply-all" });
  expect(handles.get("one")!.data.modelConfig.selectedModels[0]!.parameters[0]!.value).toBe("low");
  action.run(accessor, { effort: "ultra", revision: "next" });
  expect(handles.get("two")!.data.modelConfig.selectedModels[0]!.parameters[0]!.value).toBe("xhigh");
  expect(handles.get("two")!.data.modelConfig.maxMode).toBe(false);
});

it("does not change defaults or session state without a usable native catalog", () => {
  let Action: { new(): { run(accessor: unknown, args: unknown): unknown } } | undefined;
  new Function("ut", "It", "zb", "to", "g3i", CURSOR_EFFORT_ACTION + "true;")((action: typeof Action) => { Action = action; }, class { constructor(_args: unknown) {} }, "models", "data", () => undefined);
  const action = new Action!();
  const getModelConfig = () => ({ modelName: "default" });
  const native = { getAvailableDefaultModels: () => [{ name: "default", parameterDefinitions: [] }], getModelConfig };
  const accessor = { get: (token: string) => token === "models" ? native : {} };
  expect(action.run(accessor, { effort: "low", revision: "one" })).toEqual({ ready: false, updated: 0, unsupported: 0 });
  expect(native.getModelConfig).toBe(getModelConfig);
  expect(() => action.run(accessor, { effort: "bad", revision: "one" })).toThrow("Invalid Nexus effort request");
  expect(() => action.run(accessor, { effort: "low", revision: "x".repeat(513) })).toThrow("Invalid Nexus effort request");
});
