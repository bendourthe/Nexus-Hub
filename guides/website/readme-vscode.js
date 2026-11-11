(function () {
  "use strict";
  const settingsScenes = [
    { title:"One global effort level", text:"Medium is saved in Nexus Hub. Both open editor tabs use Medium.", effort:"medium", overview:true, target:"panel:effort" },
    { title:"Change to Low", text:"Changing the Nexus default updates Claude Code and Codex, including open sessions.", effort:"low", overview:true, target:"panel:radio:low", click:true },
    { title:"Claude Code updates", text:"The Claude Code session now uses Low.", effort:"low", target:"[data-native=claude-effort]" },
    { title:"Codex updates", text:"The Codex session also uses Low. New sessions inherit this default.", effort:"low", target:"[data-native=codex-effort]" },
    { title:"A manual session choice", text:"Change Codex to Medium for this session. Claude Code and the global default stay Low.", effort:"low", codex:"Medium", target:"[data-native=codex-effort]", click:true },
    { title:"Apply to all", text:"Apply to all restores the saved Low default in both sessions.", effort:"low", target:"panel:applyAll", click:true },
    { title:"Fast mode", text:"Fast mode updates supported Claude Code and Codex sessions. It may increase usage or cost.", effort:"low", fast:true, target:"panel:fast", click:true },
    { title:"Guardrails", text:"Enabled guardrails check the next supported tool call, including full-access sessions.", effort:"low", fast:true, target:"panel:guards" },
    { title:"Usage alerts", text:"Turn all alerts off or choose individual monitors. Taskbar colors remain active.", effort:"low", fast:true, alerts:false, target:"panel:alerts", click:true },
    { title:"Compact status hover", text:"Hover Nexus Hub for the saved effort level and enabled guardrails.", effort:"low", fast:true, alerts:false, hover:"nexus", target:".vs-hover" },
  ];
  const usageScenes = [
    {title:"Claude usage hover",text:"Hover the Claude taskbar item for current, weekly, model-specific usage and reset countdowns.",hover:"claude",target:".vs-hover"},
    {title:"Claude usage dashboard",text:"Click the same taskbar item to open the full dashboard in an editor tab.",dashboard:"claude",target:".usage-dashboard",click:true},
    {title:"Codex usage hover",text:"Hover Codex for current and weekly usage, available resets and account details.",hover:"codex",target:".vs-hover"},
    {title:"Codex usage dashboard",text:"Click Codex to open its dashboard, including the account's reset controls.",dashboard:"codex",target:".usage-dashboard",click:true},
    {title:"Copilot usage hover",text:"Hover Copilot for the monthly quota and reset details available from the account.",hover:"copilot",target:".vs-hover"},
    {title:"Copilot usage dashboard",text:"Click Copilot to open its monthly usage dashboard.",dashboard:"copilot",target:".usage-dashboard",click:true},
  ];
  let sources = window.README_GENERATED || window.README_COMPONENTS, index = 0, kind = new URLSearchParams(location.search).get("tour") === "usage" ? "usage" : "settings", playing = false;
  const panel = document.querySelector(".settings-webview"), root = document.querySelector(".vscode-workbench"), tour = ReadmeTour.mount(root);
  const icons = {nexus:"logo.png",claude:"claude-icon.svg",codex:"codex-icon.svg",copilot:"copilot-icon.svg"};
  function icon(provider) { return `<img src="${provider==='copilot'?'../../extensions/copilot-usage-monitor/icons/copilot-light.svg':'../../extensions/nexus-hub-settings/media/'+icons[provider]}" alt="">`; }
  function markdownIcons(value) { return value.replace(/\$\(([^)]+)\)/g, (_, name) => ({check:"&#10003;","circle-slash":"&#8856;",warning:"&#9888;",question:"?"}[name] || "")); }
  function updatePanel(scene) {
    const win = panel.contentWindow;
    if (!win?.showDemo) return;
    const model = win.demoModel;
    model.controls[0].rows = [{tool:"internal",state:"in-effect",value:scene.effort || "medium",canSet:true}];
    win.showDemo({preferences:{effort:scene.effort || "medium"},sessionDefaults:{effort:scene.effort || "medium",fastMode:!!scene.fast,codexTabs:true},usageAlerts:{claude:scene.alerts!==false,codex:scene.alerts!==false,copilot:scene.alerts!==false}});
    const selectors = {guards:".guardrails-section",alerts:".usage-alerts-section"};
    win.scrollTo(0, selectors[scene.target?.slice(6)] ? win.document.querySelector(selectors[scene.target.slice(6)]).offsetTop : 0);
  }
  function panelTarget(key) {
    const selectors={effort:".effort-section","radio:low":"[role=radio][data-value=low]",applyAll:"[data-setting=applyAll]",fast:"[data-setting=fast]",guards:".guardrails-section",alerts:".alerts-master"};
    const node=panel.contentDocument?.querySelector(selectors[key]);if(!node)return null;
    const r=node.getBoundingClientRect(), base=panel.getBoundingClientRect();
    return {x:base.x+r.x,y:base.y+r.y,width:r.width,height:Math.min(r.height,panel.clientHeight-r.y)};
  }
  function highlight(scene, options={}) {
    tour.layer.querySelector(".tour-shade").style.opacity=scene.overview?".12":"1";
    const provider=scene.hover||scene.dashboard, item=provider?document.querySelector(`[data-usage=${provider}]`):null, r=item?.getBoundingClientRect(), base=root.getBoundingClientRect();
    return tour.focus(scene.target?.startsWith("panel:") ? panelTarget(scene.target.slice(6)) : scene.target, {progress:options.progress,from:options.from,point:r?{x:r.x-base.x+r.width/2,y:r.y-base.y+r.height/2}:undefined,click:options.click??scene.click});
  }
  async function render(tourKind, at, options={}) {
    if(kind!==tourKind){kind=tourKind;fillPicker();}const scenes=kind==="usage"?usageScenes:settingsScenes;index=(at+scenes.length)%scenes.length;const scene=scenes[index];
    updatePanel(scene);
    for (const provider of ["claude","codex"]) {
      const button=document.querySelector(`[data-native=${provider}-effort]`), level=provider==="codex"&&scene.codex?scene.codex:(scene.effort==="low"?"Low":"Medium");
      button.innerHTML=(scene.fast?"&#9889; ":"")+(provider==="claude"?"Opus 5.5":"GPT-6.1 Sol")+` <b>${level}</b> &#8964;`;
    }
    for(const provider of ["nexus","claude","codex","copilot"]){const item=document.querySelector(`[data-usage=${provider}]`),state=provider==="nexus"?sources.usage.nexus[scene.effort||"medium"]:sources.usage[provider];item.innerHTML=icon(provider)+state.text.replace(/\$\([^)]+\)/g,"").trim();}
    document.querySelector(".codex-session").hidden=!!scene.dashboard;document.querySelector(".usage-dashboard").hidden=!scene.dashboard;
    if(scene.dashboard){document.querySelector(".dashboard-name").textContent={claude:"Claude Usage",codex:"Codex Usage",copilot:"Copilot Usage"}[scene.dashboard];const iframe=document.querySelector(".usage-dashboard iframe");iframe.srcdoc=sources.usage[scene.dashboard].dashboard;await new Promise(resolve=>iframe.onload=resolve);}
    const hover=document.querySelector(".vs-hover");hover.hidden=!scene.hover;
    if(scene.hover){const item=document.querySelector(`[data-usage=${scene.hover}]`).getBoundingClientRect(),base=root.getBoundingClientRect();hover.style.right="auto";hover.style.left=Math.max(8,Math.min(base.width-326,item.x-base.x+item.width/2-159))+"px";hover.innerHTML=markdownIcons(scene.hover==="nexus"?sources.usage.nexus[scene.effort||"medium"].tooltip:sources.usage[scene.hover].tooltip);await Promise.all([...hover.querySelectorAll('img')].map(i=>i.complete?Promise.resolve():new Promise(r=>i.onload=r)));}
    document.querySelector("#vs-tour-title").textContent=scene.title;document.querySelector("#vs-tour-description").textContent=scene.text;
    document.querySelector("#position").textContent=`${index+1} / ${scenes.length}`;
    document.querySelectorAll(".vs-scene-picker button").forEach((b,i)=>b.setAttribute("aria-current",i===index?"step":"false"));
    const motion=highlight(scene,options);return motion;
  }
  function fillPicker(){
    const scenes=kind==="usage"?usageScenes:settingsScenes, picker=document.querySelector(".vs-scene-picker");picker.replaceChildren();
    scenes.forEach((scene,i)=>{const b=document.createElement("button");b.type="button";b.textContent=scene.title;b.onclick=()=>{stop();render(kind,i)};picker.append(b)});
  }
  async function start(input) {
    sources=input;panel.srcdoc=sources.panel;await new Promise(resolve=>panel.onload=resolve);
    fillPicker();
    await render(kind,0);window.demoReady=true;
  }
  function stop(){playing=false;document.querySelector("#play").textContent="Play";document.querySelector("#play").setAttribute("aria-pressed","false");}
  document.querySelector("#previous").onclick=()=>{stop();render(kind,index-1)};document.querySelector("#next").onclick=()=>{stop();render(kind,index+1)};
  document.querySelector("#play").onclick=()=>{playing=!playing;document.querySelector("#play").textContent=playing?"Pause":"Play";document.querySelector("#play").setAttribute("aria-pressed",String(playing));};
  setInterval(()=>{if(playing&&!document.hidden)render(kind,index+1)},4500);
  window.addEventListener("message",event=>{if(event.source!==panel.contentWindow||event.data?.type!=="readme-setting")return;const message=event.data.message,current=(kind==="usage"?usageScenes:settingsScenes)[index];if(message.type==="set"&&message.control==="effort"){current.effort=message.value;delete current.codex;}if(message.type==="applyAll")delete current.codex;if(message.type==="setFastMode")current.fast=message.value;if(message.type==="setUsageAlert"&&message.provider==="all")current.alerts=message.enabled;render(kind,index);});
  for(const provider of ["claude","codex","copilot"]){const item=document.querySelector(`[data-usage=${provider}]`);item.addEventListener("click",()=>{stop();const at=usageScenes.findIndex(s=>s.dashboard===provider);render("usage",at)});item.addEventListener("mouseenter",()=>{const hover=document.querySelector(".vs-hover"),r=item.getBoundingClientRect(),base=root.getBoundingClientRect();hover.innerHTML=markdownIcons(sources.usage[provider].tooltip);hover.style.right="auto";hover.style.left=Math.max(8,Math.min(base.width-326,r.x-base.x+r.width/2-159))+"px";hover.hidden=false;});item.addEventListener("mouseleave",()=>{const scene=(kind==="usage"?usageScenes:settingsScenes)[index];if(!scene.hover)document.querySelector(".vs-hover").hidden=true;});}
  window.vscodeDemo={start,render,highlight,scenes:{settings:settingsScenes,usage:usageScenes}};
  if(sources)start(sources);
})();
