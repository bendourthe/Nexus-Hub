import { createHash } from "node:crypto";

export interface CursorParameter { id: string; value: string }
export interface CursorSelection { modelId: string; parameters?: CursorParameter[] }
export interface CursorModel {
  name: string;
  idAliases?: string[];
  parameterDefinitions?: {
    id: string;
    name?: string;
    parameterType?: { enumParameter?: { values: { value: string; displayName?: string }[] } };
  }[];
}

/** Self-contained because the exact-build workbench adapter embeds this function. */
export function mapCursorEffort(
  models: CursorModel[],
  selected: CursorSelection[],
  effort: string,
  compatible: (model: CursorModel, parameters: CursorParameter[]) => boolean = () => true,
): { selectedModels: CursorSelection[]; supported: number } {
  const ranks: Record<string, number> = { low: 0, minimal: 0, medium: 1, high: 2, xhigh: 3, extrahigh: 3, max: 4, maximum: 4, ultra: 5, ultracode: 5 };
  const normalize = (value: string): string => value.toLowerCase().replace(/[^a-z0-9]/g, "");
  const wanted = ranks[effort];
  if (wanted === undefined || !["low", "medium", "high", "xhigh", "max", "ultra"].includes(effort)) { throw new Error("Invalid Nexus effort"); }
  let supported = 0;
  const selectedModels = selected.map((entry) => {
    const model = models.find((item) => item.name === entry.modelId || item.idAliases?.includes(entry.modelId));
    if (!model) { return entry; }
    const definitions = (model.parameterDefinitions ?? []).filter((item) => {
      const names = [normalize(item.id), normalize(item.name ?? "")];
      return names.some((name) => name.includes("effort") || /^(reasoning|thinking)level$/.test(name)) && item.parameterType?.enumParameter;
    });
    if (definitions.length !== 1) { return entry; }
    const definition = definitions[0]!;
    const choices = (definition.parameterType!.enumParameter!.values ?? []).flatMap((item) => {
      const rank = ranks[normalize(item.value)] ?? ranks[normalize(item.displayName ?? "")];
      return rank === undefined ? [] : [{ value: item.value, rank }];
    }).sort((a, b) => {
      const lowerA = a.rank <= wanted, lowerB = b.rank <= wanted;
      return lowerA !== lowerB ? lowerA ? -1 : 1 : lowerA ? b.rank - a.rank : a.rank - b.rank;
    });
    for (const choice of choices) {
      const parameters = (entry.parameters ?? []).map((item) => ({ ...item }));
      const index = parameters.findIndex((item) => item.id === definition.id);
      const value = { id: definition.id, value: choice.value };
      if (index < 0) { parameters.push(value); } else { parameters[index] = value; }
      if (!compatible(model, parameters)) { continue; }
      supported++;
      return { ...entry, parameters };
    }
    return entry;
  });
  return { selectedModels, supported };
}

export const CURSOR_EFFORT_COMMAND = "nexusHubSettings.cursor.applyEffort";
export const CURSOR_WORKBENCH_PATH = "out/vs/workbench/workbench.desktop.main.js";
export const CURSOR_WORKBENCH_HASH = "5aec61924cced4345b0a5c67c741bf56aa6358f6b791cb71129be0de08e2800f";
export const CURSOR_WORKBENCH_VERSION = "3.29.9";
export const CURSOR_ACTION_ANCHOR = 'ut(class extends It{constructor(){super({id:"cursorai.action.switchToModelSlug"';

// Only the pinned build's service tokens and variant resolver are referenced here.
export const CURSOR_EFFORT_ACTION = `ut(class extends It {
  constructor() { super({id:"${CURSOR_EFFORT_COMMAND}",title:{value:"Nexus Hub Effort",original:"Nexus Hub Effort"},f1:false}); }
  run(accessor,args) {
    if(!args || !["low","medium","high","xhigh","max","ultra"].includes(args.effort) || typeof args.revision!=="string" || args.revision.length>512) throw Error("Invalid Nexus effort request");
    const modelService=accessor.get(zb), dataService=accessor.get(to);
    const mapper=${mapCursorEffort.toString()};
    const catalog=modelService.getAvailableDefaultModels();
    if(!catalog.some(model=>mapper([model],[{modelId:model.name}],args.effort).supported)) return {ready:false,updated:0,unsupported:0};
    const state=this.nexusState??={applied:new WeakMap(),manual:new Set(),reading:false};
    if(state.revision!==args.revision) { state.revision=args.revision; state.manual.clear(); }
    state.effort=args.effort;
    const map=(selected,maxMode)=>mapper(modelService.getAvailableDefaultModels(),selected.map(item=>({...item,parameters:modelService.resolveModelParametersForSubmission(item.modelId,item.parameters,maxMode)})),state.effort,(model,parameters)=>{
      if(!model.variants?.length) return true;
      const variant=g3i(model,parameters,maxMode);
      const actual=variant?.parameterValues;
      return actual?.length===parameters.length && parameters.every(item=>actual.some(value=>value.id===item.id&&value.value===item.value));
    });
    if(!state.original) {
      state.original=modelService.getModelConfig;
      state.setOriginal=modelService.setModelConfigForComposer;
      modelService.setModelConfigForComposer=function(handle,change,surface,options) {
        if(options?.updateGlobalConfig===true && change.selectedModels) state.manual.add(handle.composerId??handle.data.composerId);
        return state.setOriginal.call(this,handle,change,surface,options);
      };
      modelService.getModelConfig=function(surface) {
        const config=state.original.call(this,surface);
        if(state.reading || !["composer","background-composer","plan-execution"].includes(surface)) return config;
        state.reading=true;
        try { const mapped=map(this.deriveSelectedModels(config),config.maxMode===true); return mapped.supported ? {...config,selectedModels:mapped.selectedModels} : config; }
        finally { state.reading=false; }
      };
    }
    let updated=0,unsupported=0;
    for(const id of dataService.selectedComposerIds) {
      if(state.manual.has(id)) continue;
      const handle=dataService.getHandleIfLoaded(id);
      if(!handle) continue;
      if(state.applied.get(handle)===args.revision) continue;
      const config=modelService.getEffectiveModelConfigForComposer(handle);
      const mapped=map(modelService.deriveSelectedModels(config),config.maxMode===true);
      if(mapped.supported) { modelService.setModelConfigForComposer(handle,{selectedModels:mapped.selectedModels},undefined,{updateGlobalConfig:false}); updated++; }
      else unsupported++;
      state.applied.set(handle,args.revision);
    }
    return {ready:true,updated,unsupported};
  }
}),`;

export function patchCursorWorkbench(original: string): string {
  if (createHash("sha256").update(original).digest("hex") !== CURSOR_WORKBENCH_HASH) { throw new Error("This Cursor build has not been qualified; its workbench was preserved."); }
  const index = original.indexOf(CURSOR_ACTION_ANCHOR);
  if (index < 0 || original.indexOf(CURSOR_ACTION_ANCHOR, index + CURSOR_ACTION_ANCHOR.length) >= 0) { throw new Error("Cursor's model action registration changed and was preserved."); }
  return original.slice(0, index) + CURSOR_EFFORT_ACTION + original.slice(index);
}

/** Retain every integrity entry; update only the digest for our exact workbench output. */
export function cursorProductManifest(original: string, writtenHash: string): string {
  const checksum = Buffer.from(CURSOR_WORKBENCH_HASH, "hex").toString("base64").replace(/=+$/, "");
  const manifest = JSON.parse(original);
  const key = CURSOR_WORKBENCH_PATH.slice(4);
  if (manifest.applicationName !== "cursor" || manifest.checksums?.[key] !== checksum || !/^[a-f0-9]{64}$/.test(writtenHash)) { throw new Error("Cursor's integrity manifest changed and was preserved."); }
  const token = JSON.stringify(checksum), index = original.indexOf(token);
  if (index < 0 || original.indexOf(token, index + token.length) >= 0) { throw new Error("Cursor's integrity entry is ambiguous and was preserved."); }
  return original.slice(0, index) + JSON.stringify(Buffer.from(writtenHash, "hex").toString("base64").replace(/=+$/, "")) + original.slice(index + token.length);
}
