import { RECOVERY_KEY, type RecoveryProvider } from "./nativeRecovery";
import { CLAUDE_UI_ADOPT } from "./vendorUiPatch";

const LEVELS = ["low", "medium", "high", "xhigh", "max", "ultra"];
export const EFFORT_MARKER = "nexusHub.nativeEffort.v1";
interface ClaudeOwner {
  channels: Map<string, unknown>;
  shutDown?: boolean;
  writeUserSettingsAndPush(id: string, settings: {effortLevel: string; ultracode: boolean}, flagsOnly: boolean): Promise<{effort?: string; ultracode?: boolean} | undefined>;
  cachedClaudeSettings?: {applied?: {effort?: string; ultracode?: boolean}};
  config: Promise<Record<string, unknown>>;
  getCurrentState(): Record<string, unknown>;
  send(message: unknown): void;
}
interface EffortRegistry { codexView?: {broadcastToAllViews(message: unknown): void}; claude?: Set<WeakRef<ClaudeOwner>> }
const revisions = new WeakMap<ClaudeOwner, Map<string, string>>();

/** Use the actual native owners captured by provider-only recovery, without version allowlists. */
export async function applyNativeEffort(provider: RecoveryProvider, effort: string, revision: string): Promise<{updated: number}> {
  if (!LEVELS.includes(effort) || typeof revision !== "string" || revision.length > 512) { throw new Error("Invalid Nexus effort"); }
  const state = (globalThis as unknown as {[key: symbol]: EffortRegistry})[Symbol.for(RECOVERY_KEY)];
  if (provider === "codex") {
    if (!state?.codexView) { return {updated: 0}; }
    if (typeof state?.codexView?.broadcastToAllViews !== "function") { throw new Error("Codex's native effort owner is not connected."); }
    state.codexView.broadcastToAllViews({type: EFFORT_MARKER, effort, revision});
    return {updated: 0}; // Delivery is queued; native setters, not this broadcast, confirm application.
  }
  let updated = 0;
  for (const reference of state?.claude ?? []) {
    const owner = reference.deref();
    if (!owner || owner.shutDown) { continue; }
    if (!(owner.channels instanceof Map) || typeof owner.writeUserSettingsAndPush !== "function") { throw new Error("Claude's native effort setter is unavailable."); }
    let applied = revisions.get(owner);
    if (!applied) { applied = new Map(); revisions.set(owner, applied); }
    for (const [id] of owner.channels) {
      if (applied.get(id) === revision) { continue; }
      const actual = await owner.writeUserSettingsAndPush(id, {effortLevel: effort === "ultra" ? "xhigh" : effort, ultracode: effort === "ultra"}, true);
      const read = actual ?? owner.cachedClaudeSettings?.applied;
      if (read?.effort !== (effort === "ultra" ? "xhigh" : effort) || Boolean(read.ultracode) !== (effort === "ultra")) { throw new Error("Claude did not confirm the requested effort."); }
      applied.set(id, revision); updated++;
    }
    for (const id of applied.keys()) { if (!owner.channels.has(id)) { applied.delete(id); } }
    const config = await owner.config;
    if (config) { owner.send({type: "request", channelId: "", requestId: "", request: {type: "update_state", state: {...owner.getCurrentState(), nexusEffort: {effort, revision}}, config: {...config, nexusEffort: {effort, revision}}}}); }
  }
  return {updated};
}

export const CODEX_NATIVE_HOOK = `
/*${EFFORT_MARKER}*/
const nexusNativeObservers=new Set(),nexusNativeApplied=new Map(),nexusNativePending=new Map(),nexusNativeFailed=new Map();
let nexusNativeLatest;
window.addEventListener("message",event=>{
  const message=event.data;
  if(message?.type!=="${EFFORT_MARKER}"||!${JSON.stringify(LEVELS)}.includes(message.effort)||typeof message.revision!=="string"||message.revision.length>512)return;
  event.stopImmediatePropagation();nexusNativeLatest=message;
  for(const observer of nexusNativeObservers)observer(message);
},true);
function nexusUseNativeEffort(react,query,owner,session){
  const catalog=query({hostId:owner.hostId,enabled:owner.hostId==="local"&&!owner.modelSettings.isLoading}).data;
  const ref=react.useRef();ref.current={owner,session,catalog};
  react.useEffect(()=>{
    const observer=message=>{
      const {owner,session,catalog}=ref.current,settings=owner.modelSettings;
      if(owner.hostId!=="local"||settings.isLoading)return;
      const key=session??"draft",revision=message.revision;
      if(nexusNativeApplied.get(key)===revision||nexusNativeFailed.get(key)===revision||nexusNativePending.has(key))return;
      const supported=catalog?.models?.find(model=>model.model===settings.model)?.supportedReasoningEfforts?.map(item=>item.reasoningEffort);
      if(!supported)return;
      const levels=${JSON.stringify(LEVELS)},wanted=levels.indexOf(message.effort);
      const mapped=levels.slice(0,wanted+1).filter(level=>supported.includes(level)).at(-1)??levels.find(level=>supported.includes(level));
      if(!mapped)return;
      if(settings.reasoningEffort===mapped){nexusNativeApplied.set(key,revision);return;}
      const select=session==null?owner.setModelAndReasoningEffort:owner.setModelAndReasoningEffortForNextTurn;
      const work=Promise.resolve().then(()=>select(settings.model,mapped,session==null?{persistAsDefault:false}:{threadSettings:{}}));
      nexusNativePending.set(key,work);
      void work.then(result=>{if(result===false)throw Error("The native effort update was refused");nexusNativeApplied.set(key,revision)}).catch(()=>{nexusNativeFailed.set(key,revision)}).finally(()=>{nexusNativePending.delete(key);if(nexusNativeLatest?.revision!==revision&&nexusNativeLatest)observer(nexusNativeLatest)});
    };
    nexusNativeObservers.add(observer);if(nexusNativeLatest)observer(nexusNativeLatest);
    return()=>nexusNativeObservers.delete(observer);
  },[]);
}
`;

/** Discover aliases from unique semantic properties; preserve missing or ambiguous contracts. */
export function patchNativeEffortView(provider: RecoveryProvider, source: string): string {
  if (source.includes(EFFORT_MARKER)) {
    if (provider === "codex" ? source.includes(CODEX_NATIVE_HOOK) && source.split("nexusUseNativeEffort(").length === 3 : source.includes("this.nexusEffortRevision!==nexus.revision") && source.includes("this.adoptAppliedEffort({effort:nexus.effort")) { return source; }
    throw new Error("The native effort integration is incomplete; provider files were preserved.");
  }
  if (provider === "claude") {
    const anchors = [...source.matchAll(/let ([$\w]+)=this\.connection\.value\?\.config\.value,([$\w]+)=\1\?\.claudeSettings\?\.applied,([$\w]+)=/g)];
    if (anchors.length !== 1 || !source.includes("adoptAppliedEffort(")) { throw new Error("Claude's native effort signal is unavailable or ambiguous."); }
    const anchor = anchors[0]!, config = anchor[1]!, applied = anchor[2]!, next = anchor[3]!;
    const adopt = CLAUDE_UI_ADOPT.replace("r?.nexusEffort", config + "?.nexusEffort");
    return source.replace(anchor[0], `let ${config}=this.connection.value?.config.value;/*${EFFORT_MARKER}*/${adopt}let ${applied}=${config}?.claudeSettings?.applied,${next}=`);
  }
  const targets = [...source.matchAll(/([$\w]+)=\{\.\.\.([$\w]+),modelSettings:([$\w]+),setModelAndReasoningEffortForNextTurn:([$\w]+),setModelAndReasoningEffort:([$\w]+)\}/g)];
  if (targets.length !== 1) { throw new Error("Codex's native model settings owner is unavailable or ambiguous."); }
  const target = targets[0]!, result = target[1]!;
  const functionStart = source.lastIndexOf("function ", target.index);
  const body = source.slice(functionStart, target.index);
  const react = /\(0,([$\w]+)\.use\)\(/.exec(body)?.[1];
  const session = /([$\w]+)=[$\w]+===void 0\?null:[$\w]+/.exec(body)?.[1];
  const queries = new Set([...source.matchAll(/listModelsData:/g)].flatMap(match => {
    const body = source.slice(source.lastIndexOf("function ", match.index), match.index);
    return [...body.matchAll(/let\{data:[$\w]+,isLoading:[$\w]+\}=([$\w]+)\([$\w]+\)/g)].map(query => query[1]!);
  }));
  const query = queries.size === 1 ? [...queries][0] : undefined;
  const tail = "," + result + "}";
  const end = source.indexOf(tail, target.index);
  if (!react || !session || !query || end < 0 || end - target.index! > 600) { throw new Error("Codex's native effort hook contract changed."); }
  return source.slice(0, end) + `,nexusUseNativeEffort(${react},${query},${result},${session})` + source.slice(end) + "\n" + CODEX_NATIVE_HOOK;
}
