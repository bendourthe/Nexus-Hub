/** These adapters retain the vendor's model support, account, and billing checks. */
export const CLAUDE_FAST_API = `async applyNexusFastMode(value,revision){if(typeof value!=="boolean"||typeof revision!=="string"||revision.length>512)throw Error("Invalid Nexus fast mode");for(const comm of zre?.allComms??[]){const config=await comm.config;if(config)comm.send({type:"request",channelId:"",requestId:"",request:{type:"update_state",state:{...comm.getCurrentState()},config:{...config,nexusFast:{value,revision}}}})}return{queued:true}},async applyNexusDefaults(settings){if(settings.effort)await this.applyNexusEffort(settings.effort,settings.effortRevision);if(typeof settings.fastMode==="boolean")await this.applyNexusFastMode(settings.fastMode,settings.fastRevision)}`;

export const CLAUDE_FAST_ADOPT = `
const nexusFast=r?.nexusFast;
if(nexusFast&&typeof nexusFast.value==="boolean"&&typeof nexusFast.revision==="string"&&this.nexusFastRevision!==nexusFast.revision&&this.connection.value&&(!nexusFast.value||this.currentModelSupportsFastMode.value)){
  this.nexusFastRevision=nexusFast.revision;
  const known=typeof this.connection.value.claudeConfig.value?.fast_mode_state==="string";
  const on=this.fastModeState.value!=="off";
  if(!known||on!==nexusFast.value)queueMicrotask(()=>{void Promise.resolve(this.send(nexusFast.value?"/fast on":"/fast off",void 0,!1,{kind:"human"},{cancelParkedDialogs:!1})).catch(()=>{})});
}
`;

export const CODEX_DEFAULTS_API = `applyNexusDefaults(settings){if(settings.effort!==undefined&&!["low","medium","high","xhigh","max","ultra"].includes(settings.effort)||settings.fastMode!==undefined&&typeof settings.fastMode!=="boolean")throw Error("Invalid Nexus defaults");for(const key of ["effortRevision","fastRevision"])if(settings[key]!==undefined&&(typeof settings[key]!=="string"||settings[key].length>512))throw Error("Invalid Nexus revision");$e.broadcastToAllViews({type:"nexus-defaults-v2",...settings});return{queued:true}}`;

export const CODEX_DEFAULTS_HOOK = `
const nexusDefaultsObservers=new Set();
window.addEventListener("message",event=>{
  const data=event.data;
  if(data?.type!=="nexus-defaults-v2")return;
  event.stopImmediatePropagation();
  if(data.effort!==undefined&&!["low","medium","high","xhigh","max","ultra"].includes(data.effort))return;
  if(data.fastMode!==undefined&&typeof data.fastMode!=="boolean")return;
  if([data.effortRevision,data.fastRevision].some(value=>value!==undefined&&(typeof value!=="string"||value.length>512)))return;
  for(const observer of nexusDefaultsObservers)observer(data);
},true);
function nexusUseDefaultsBridge(settings,select,hostId,sessionId){
  const catalog=it({hostId,enabled:hostId==="local"&&!settings.isLoading}).data;
  const ref=Rt.useRef(null);
  ref.current??={applied:new Map(),pending:new Map(),queue:Promise.resolve()};
  Rt.useEffect(()=>{
    const state=ref.current;
    const observer=message=>{
      if(hostId!=="local"||settings.isLoading)return;
      const model=catalog?.models?.find(item=>item.model===settings.model);
      if(!model)return;
      const session=sessionId??"draft", prior=state.applied.get(session)??{};
      const levels=["low","medium","high","xhigh","max","ultra"];
      const available=model.supportedReasoningEfforts?.map(item=>item.reasoningEffort)??[];
      const effort=message.effort===undefined?undefined:levels.slice(0,levels.indexOf(message.effort)+1).filter(item=>available.includes(item)).at(-1)??available.find(item=>levels.includes(item));
      const changeEffort=effort!==undefined&&typeof message.effortRevision==="string"&&prior.effort!==message.effortRevision;
      const fastTier=model.serviceTiers?.find(item=>["priority","fast"].includes(item.id)||["fast","priority"].includes(item.name?.trim().toLowerCase()));
      const changeFast=typeof message.fastMode==="boolean"&&typeof message.fastRevision==="string"&&prior.fast!==message.fastRevision&&(!message.fastMode||fastTier);
      if(!changeEffort&&!changeFast)return;
      const key=JSON.stringify([message.effortRevision,message.fastRevision]);
      if(state.pending.get(session)?.key===key)return;
      const entry={key};state.pending.set(session,entry);
      state.queue=state.queue.catch(()=>{}).then(async()=>{
        if(state.pending.get(session)!==entry)return;
        if(changeFast||changeEffort&&settings.reasoningEffort!==effort){
          const result=await select(settings.model,changeEffort?effort:settings.reasoningEffort,{persistAsDefault:false,...changeFast?{serviceTier:message.fastMode?fastTier.id:"default"}:{}});
          if(result===false)throw Error("Native default update was refused");
        }
        if(state.pending.get(session)===entry){state.applied.set(session,{...prior,...changeEffort?{effort:message.effortRevision}:{},...changeFast?{fast:message.fastRevision}:{}});state.pending.delete(session)}
      }).catch(()=>{if(state.pending.get(session)===entry)state.pending.delete(session)});
    };
    nexusDefaultsObservers.add(observer);
    return()=>nexusDefaultsObservers.delete(observer);
  },[settings.model,settings.reasoningEffort,settings.isLoading,select,hostId,sessionId,catalog]);
}
`;
