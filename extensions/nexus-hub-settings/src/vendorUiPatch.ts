import { createHash } from "node:crypto";
import { CLAUDE_FAST_ADOPT, CLAUDE_FAST_API, CODEX_DEFAULTS_API, CODEX_DEFAULTS_HOOK } from "./vendorFastMode";
import { CURSOR_WORKBENCH_HASH, CURSOR_WORKBENCH_PATH, CURSOR_WORKBENCH_VERSION, patchCursorWorkbench } from "./cursorEffort";

export type UiVendor = "claude" | "codex" | "cursor";
export const uiHash = (value: string): string => createHash("sha256").update(value).digest("hex");
const levels = '["low","medium","high","xhigh","max","ultra"]';
const validate = `if(!${levels}.includes(e))throw Error("Invalid Nexus effort");`;

const CLAUDE_EFFORT_API = `return{nexusEffortBridgeVersion:2,async applyNexusEffort(e,revision=e){${validate}const level=e==="ultra"?"xhigh":e;let updated=0;this.nexusRevisions??=new WeakMap();for(const comm of zre?.allComms??[]){const applied=comm.cachedClaudeSettings?.applied;if(this.nexusRevisions.get(comm)!==revision&&(applied?.effort!==level||Boolean(applied?.ultracode)!==(e==="ultra"))){for(const[id]of comm.channels){await comm.writeUserSettingsAndPush(id,{effortLevel:level,ultracode:e==="ultra"},true);updated++}}const actual=comm.cachedClaudeSettings?.applied;if(this.nexusRevisions.get(comm)!==revision&&comm.channels.size&&(actual?.effort!==level||Boolean(actual?.ultracode)!==(e==="ultra")))throw Error("Claude did not apply the requested effort");this.nexusRevisions.set(comm,revision);const config=await comm.config;if(config)comm.send({type:"request",channelId:"",requestId:"",request:{type:"update_state",state:{...comm.getCurrentState(),nexusEffort:{effort:e,revision}},config:{...config,nexusEffort:{effort:e,revision}}}})}return{updated}}}`;
// Claude deliberately seeds effort once. Adopt later verified host changes through its own signal owner.
export const CLAUDE_UI_ADOPT = `const nexus=r?.nexusEffort;if(nexus&&${levels}.includes(nexus.effort)&&this.nexusEffortRevision!==nexus.revision){this.nexusEffortRevision=nexus.revision;this.adoptAppliedEffort({effort:nexus.effort==="ultra"?"xhigh":nexus.effort,ultracodeRequested:nexus.effort==="ultra"},{available:true})}`;
const CODEX_EFFORT_API = `return{nexusEffortBridgeVersion:2,applyNexusEffort(e,revision=e){${validate}$e.broadcastToAllViews({type:"nexus-effort-v1",effort:e,revision});return{queued:true}}}`;
const CODEX_ORIGINAL_PANEL = 'async createNewPanel(){let e=F1("/extension/panel/new"),r=Be.window.activeTextEditor?.viewColumn??Be.ViewColumn.Active;await Be.commands.executeCommand("vscode.openWith",e,t.customEditorViewType,{viewColumn:r,preserveFocus:!1,preview:!1})}';
export const CODEX_NEW_PANEL = CODEX_ORIGINAL_PANEL.replace('F1("/extension/panel/new")', 'F1("/extension/panel/new?nexus="+(0,w8e.randomUUID)())');

export const CLAUDE_UI_API = CLAUDE_EFFORT_API.replace("nexusEffortBridgeVersion:2", "nexusEffortBridgeVersion:3").replace("async applyNexusEffort(", CLAUDE_FAST_API + ",async applyNexusEffort(");
export const CODEX_UI_API = CODEX_EFFORT_API.replace("nexusEffortBridgeVersion:2", "nexusEffortBridgeVersion:3").replace("applyNexusEffort(", CODEX_DEFAULTS_API + ",applyNexusEffort(");

// This hook calls the same setter as the native effort picker. It does not synthesize server notifications.
export const CODEX_UI_HOOK = `
const nexusEffortObservers=new Set();
window.addEventListener("message",event=>{
  const message=event.data;
  if(message?.type!=="nexus-effort-v1")return;
  event.stopImmediatePropagation();
  if(!${levels}.includes(message.effort))return;
  for(const observer of nexusEffortObservers)observer(message.effort,message.revision??message.effort);
},true);
function nexusUseEffortBridge(settings,select,hostId,sessionId){
  const catalog=it({hostId,enabled:hostId==="local"&&!settings.isLoading}).data;
  const pending=Rt.useRef(null);
  Rt.useEffect(()=>{
    const observer=(wanted,revision)=>{
      const key=revision;
      if(pending.current?.key===key&&pending.current.done)return;
      if(hostId!=="local"||settings.isLoading)return;
      const supported=catalog?.models?.find(model=>model.model===settings.model)?.supportedReasoningEfforts?.map(level=>level.reasoningEffort);
      if(!supported)return;
      const levels=${levels};
      const mapped=levels.slice(0,levels.indexOf(wanted)+1).filter(level=>supported.includes(level)).at(-1)??levels.find(level=>supported.includes(level));
      if(!mapped||pending.current?.key===key)return;
      if(settings.reasoningEffort===mapped){pending.current={key,done:true};return;}
      pending.current={key,done:false};
      Promise.resolve().then(()=>select(settings.model,mapped,{persistAsDefault:false})).then(()=>{pending.current={key,done:true}}).catch(()=>{pending.current=null});
    };
    nexusEffortObservers.add(observer);
    return()=>nexusEffortObservers.delete(observer);
  },[settings.model,settings.reasoningEffort,settings.isLoading,select,hostId,catalog,sessionId]);
}
`;

interface UiRecipe { version: string; files: Record<string, string> }
export const UI_RECIPES: Readonly<Record<UiVendor, UiRecipe>> = {
  cursor: { version: CURSOR_WORKBENCH_VERSION, files: { [CURSOR_WORKBENCH_PATH]: CURSOR_WORKBENCH_HASH } },
  claude: { version: "2.1.318", files: { "extension.js": "62ba16d87adcd747d2112cb31e37eec753844d17455d6b410eb849e909128fa0", "webview/index.js": "82b65ed1b5537cee1d08016717e5cbd00cf8696dffa164e2cfadff77524dbfde" } },
  codex: { version: "26.1021.22027", files: { "out/extension.js": "a9cc6736cd2c2d22f6cf43fc5763d5f8a873e4f741f522b44a600b1926f4e627", "webview/assets/use-model-settings-aafcff4b111c.js": "23d2322fe24ae6d151e2fef55108942be50ca8b38aacd52e5102143bb2d1b47e" } },
};

function replaceOnce(source: string, before: string, after: string): string {
  const index = source.indexOf(before);
  if (index < 0 || source.indexOf(before, index + before.length) >= 0) { throw new Error("The native UI adapter does not match this vendor build."); }
  return source.slice(0, index) + after + source.slice(index + before.length);
}

export function patchedUiSource(vendor: UiVendor, relative: string, original: string): string {
  if (uiHash(original) !== UI_RECIPES[vendor].files[relative]) { throw new Error("The native extension was changed; its current file was preserved."); }
  if (vendor === "cursor") { return patchCursorWorkbench(original); }
  if (vendor === "claude" && relative === "extension.js") {
    return replaceOnce(original, 'if(n)nre(e,t,n)}function Xbr(e,t)', `if(n)nre(e,t,n);${CLAUDE_UI_API}}function Xbr(e,t)`);
  }
  if (vendor === "claude") {
    return replaceOnce(original, "let r=this.connection.value?.config.value,s=r?.claudeSettings?.applied,a=", "let r=this.connection.value?.config.value;" + CLAUDE_UI_ADOPT + CLAUDE_FAST_ADOPT + "let s=r?.claudeSettings?.applied,a=");
  }
  if (relative === "out/extension.js") {
    const tail = 'ie().warning("Desktop bridge init failed",{safe:{},sensitive:{error:Se}})}})()}';
    const host = replaceOnce(original, tail, tail.slice(0, -1) + ";" + CODEX_UI_API + "}");
    return replaceOnce(host, CODEX_ORIGINAL_PANEL, CODEX_NEW_PANEL);
  }
  const hook = replaceOnce(original, "let w;return n[19]!==y||n[20]!==S||n[21]!==h||n[22]!==C?", "nexusUseEffortBridge(y,S,h.hostId,r);nexusUseDefaultsBridge(y,S,h.hostId,r);let w;return n[19]!==y||n[20]!==S||n[21]!==h||n[22]!==C?");
  return hook.replace("//# sourceMappingURL=", CODEX_UI_HOOK + CODEX_DEFAULTS_HOOK + "\n//# sourceMappingURL=");
}

export function codexTabManifest(original: string): string {
  const manifest = JSON.parse(original);
  const commands = manifest.contributes?.commands;
  const menu = manifest.contributes?.menus?.["editor/title"];
  if (!Array.isArray(commands) || !Array.isArray(menu)) { throw new Error("The Codex editor menu is unavailable."); }
  const sidebar = commands.find((entry: { command?: string }) => entry.command === "chatgpt.openSidebar");
  const panel = commands.find((entry: { command?: string }) => entry.command === "chatgpt.newCodexPanel");
  if (!sidebar?.icon || !panel || !menu.some((entry: { command?: string }) => entry.command === "chatgpt.openSidebar")) { throw new Error("The Codex editor menu changed and was preserved."); }
  panel.icon = sidebar.icon;
  panel.title = "Open Codex in New Tab";
  commands.push({command: "nexusHubSettings.openCodex", title: "Open Codex", icon: sidebar.icon});
  for (const entry of [...menu]) {
    if (entry.command !== "chatgpt.openSidebar") { continue; }
    const originalWhen = typeof entry.when === "string" && entry.when ? " && (" + entry.when + ")" : "";
    menu.push({...entry, command: "nexusHubSettings.openCodex", when: "nexusHubSettings.enabled" + originalWhen});
    entry.when = "!nexusHubSettings.enabled" + originalWhen;
  }
  manifest.contributes.menus.commandPalette ??= [];
  manifest.contributes.menus.commandPalette.push({command: "nexusHubSettings.openCodex", when: "nexusHubSettings.enabled"});
  return JSON.stringify(manifest, null, 2) + "\n";
}
