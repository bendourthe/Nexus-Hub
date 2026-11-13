/* Documentation-only windows; embedded controls and monitor views come from source. */
(function () {
  "use strict";
  const sources=window.README_GENERATED||window.README_COMPONENTS, screens=document.querySelector('#screens');
  const kind=new URLSearchParams(location.search).get('tour')==='platforms'?'platforms':'usage';
  const names={claude:'Claude Code',codex:'Codex',copilot:'GitHub Copilot'};
  const assets='../../extensions/nexus-hub-settings/media/';
  function icon(p){if(p==='cursor'||p==='antigravity')return '../../assets/readme/'+p+'-app.png';return p==='copilot'?'../../extensions/copilot-usage-monitor/icons/copilot-light.svg':assets+p+'-icon.svg';}
  function taskbar(p){return `<div class="desktop-taskbar"><div class="start"><i></i><i></i><i></i><i></i></div><span>Search</span><img src="${icon(p)}" alt=""><img src="${assets}logo.png" alt="Nexus Hub"></div>`;}
  function desktop(p){return `<article class="desktop" data-provider="${p}"><h2 class="desktop-label">${names[p]}</h2><div class="window"><div class="titlebar"><span style="color:#1689db">&#10095;&#10094;</span>File &nbsp; Edit &nbsp; View<span class="window-buttons">&#8722; &#9633; &#215;</span></div><div class="tabs"><div class="tab"><img src="${icon(p)}" alt="">${names[p]}<span>&#215;</span></div></div><div class="content"><div class="chat-heading"><img src="${icon(p)}" alt="">${names[p]}</div><div class="sample-message">Add the zero-health regression test.</div><div class="sample-response">The project context and Nexus Hub instructions are available.<p>I will add the boundary test, run it, and check the result.</p><code>tests/damage.test.js</code></div><div class="composer">${p==='claude'?'Reply or type / for commands':p==='codex'?'Ask Codex anything, @ to mention files':'Ask Copilot or type / for commands'}<div class="composer-tools"><span>+ &nbsp; ${p==='codex'?'Full access':'Agent'}</span><b>${p==='claude'?'Opus 5.5 Medium':p==='codex'?'GPT-6.1 Sol Medium':'Auto'}</b><span>&#8593;</span></div></div></div><div class="dashboard" hidden><iframe title="${names[p]} usage dashboard"></iframe></div><div class="hover" hidden></div><div class="status"><button type="button" aria-label="Open ${names[p]} usage dashboard"><img src="${icon(p)}" alt="">${sources.usage[p].text.replace(/\$\([^)]+\)/g,'').trim()}</button></div></div>${taskbar(p)}</article>`;}
  function editor(p){const anti=p==='antigravity';return `<article class="desktop ${p}" data-editor="${p}"><h2 class="desktop-label">${anti?'Antigravity IDE':'Cursor'}</h2><div class="window"><div class="titlebar"><img src="${icon(p)}" alt="">File &nbsp; Edit &nbsp; Selection &nbsp; View<span class="window-buttons">&#8722; &#9633; &#215;</span></div><div class="ide-layout"><aside class="hub-sidebar"><div class="pane-label">NEXUS HUB: SETTINGS</div><iframe title="Nexus Hub settings in ${anti?'Antigravity':'Cursor'}"></iframe></aside><section class="agent"><div class="agent-toolbar"><span>${anti?'Agent':'Damage regression'}</span><span>&#8853; &nbsp; &#9719; &nbsp; &#183;&#183;&#183;</span></div><div class="sample-message">/test unit</div><div class="sample-response">I will check the damage boundary using the project tests and Nexus Hub workflow.<div class="tool">Read tests/damage.test.js<br>Run npm test<br><span>2 passed, 0 failed</span></div></div><p class="agent-note">${anti?'Native Agent with Gemini models.':'Agent chat in an editor tab.'}</p><div class="composer">${anti?'Ask anything, @ to mention, / for actions':'Plan, @ for context, / for commands'}<div class="composer-tools"><span>${anti?'No Project':'Agent'}</span><b data-effort>${anti?'Gemini 4 Argon':'Claude Opus 5.5'} Medium</b><span>&#8593;</span></div></div></section></div><div class="status"><span style="font-size:10px;padding:3px">Nexus Hub &nbsp; <b data-default>Medium</b> &nbsp; | &nbsp; ${anti?'Gemini':'Cursor'} usage</span></div></div>${taskbar(p)}</article>`;}
  const scenes=kind==='usage'?[
    {title:'Three monitors in VS Code',text:'Claude Code, Codex, and GitHub Copilot each have a usage indicator in the status bar.',state:0},
    {title:'Hover for usage and reset times',text:'All three hovers show their actual monitor bars and available reset countdowns.',state:1},
    {title:'Click to open the dashboards',text:'Each status item opens its corresponding dashboard in an editor tab.',state:2,click:true},
    {title:'Review the account details',text:'The dashboard shows the limits, reset information, and controls available for that provider.',state:3}
  ]:[
    {title:'Nexus Hub in Cursor and Antigravity',text:'The shared harness works inside each IDE. Controls adapt to its supported features.',state:0},
    {title:'Global effort in Cursor',text:'Changing Nexus effort updates Cursor Agent. Manual session choices remain possible.',state:1},
    {title:'Supported Fast mode',text:'Cursor supports Fast mode. Antigravity keeps the toggle disabled.',state:2},
    {title:'One alert switch per IDE',text:'Cursor and Antigravity each show their own usage-alert master switch, with no unrelated provider controls.',state:3}
  ];
  let index=0,playing=false,tours=[];
  function setTitle(){document.querySelector('#scene-title').textContent=scenes[index].title;document.querySelector('#scene-text').textContent=scenes[index].text;document.querySelector('#position').textContent=`${index+1} / ${scenes.length}`;}
  async function render(at,options={}){
    index=(at+scenes.length)%scenes.length;const scene=scenes[index];setTitle();
    if(kind==='usage'){
      await Promise.all([...screens.querySelectorAll('.desktop')].map(async(card,i)=>{
        const p=card.dataset.provider,hover=card.querySelector('.hover'),dash=card.querySelector('.dashboard'),status=card.querySelector('.status button');
        hover.hidden=scene.state!==1||options.showHover===false;dash.hidden=scene.state<2;
        if(scene.state>=2){card.querySelector('.tab').innerHTML=`<img src="${icon(p)}" alt="">${names[p]} Usage <span>&#215;</span>`;const iframe=dash.querySelector('iframe');if(!iframe.dataset.loaded){iframe.srcdoc=sources.usage[p].dashboard;await new Promise(r=>iframe.onload=r);iframe.dataset.loaded='true';}if(scene.state===3)iframe.contentWindow.scrollTo(0,190);else iframe.contentWindow.scrollTo(0,0);}
        else card.querySelector('.tab').innerHTML=`<img src="${icon(p)}" alt="">${names[p]} <span>&#215;</span>`;
        const base=card.querySelector('.window').getBoundingClientRect(),r=status.getBoundingClientRect();
        tours[i].layer.querySelector('.tour-cursor').style.visibility=scene.state===0?'hidden':'visible';
        tours[i].focus(scene.state===1&&!hover.hidden?hover:scene.state>=2?dash:status,{point:{x:r.x-base.x+r.width/2,y:r.y-base.y+10},progress:options.progress,from:options.from?.[i],click:options.click??scene.click});
      }));
    }else{
      for(const card of screens.querySelectorAll('[data-editor]')){
        const anti=card.dataset.editor==='antigravity',win=card.querySelector('iframe').contentWindow,low=scene.state>0&&!anti;
        win.showDemo({preferences:{effort:low?'low':'medium'},sessionDefaults:{effort:low?'low':'medium',fastMode:false,codexTabs:true}});
        card.querySelector('[data-default]').textContent=low?'Low':'Medium';card.querySelector('[data-effort]').textContent=(anti?'Gemini 4 Argon':'Claude Opus 5.5')+(low?' Low':' Medium');
        win.scrollTo(0,scene.state===3?win.document.querySelector('.usage-alerts-section').offsetTop:0);
      }
    }
    return tours.map(t=>{const r=t.layer.querySelector('.tour-cursor').style.transform.match(/[\d.]+/g);return r?{x:+r[0],y:+r[1]}:null});
  }
  async function start(){
    screens.className=kind==='platforms'?'editors':'';screens.innerHTML=kind==='usage'?['claude','codex','copilot'].map(desktop).join(''):['cursor','antigravity'].map(editor).join('');
    if(kind==='usage'){
      for(const card of screens.querySelectorAll('.desktop')){
        const p=card.dataset.provider;card.querySelector('.hover').innerHTML=sources.usage[p].tooltip;
        const tour=ReadmeTour.mount(card.querySelector('.window'));tours.push(tour);
        card.querySelector('.status button').onclick=()=>{playing=false;render(2)};
        card.querySelector('.status button').onmouseenter=()=>{if(index<2)render(1)};
      }
    }else{
      await Promise.all([...screens.querySelectorAll('[data-editor]')].map(async card=>{
        const iframe=card.querySelector('iframe');iframe.srcdoc=sources.panel;await new Promise(r=>iframe.onload=r);
        const anti=card.dataset.editor==='antigravity';iframe.contentWindow.showDemo({editorCapabilities:{extensionSettings:false,fastMode:!anti},usageAlertProviders:[anti?'gemini':'cursor'],usageAlerts:{cursor:true,gemini:true}});
      }));
    }
    await render(0);await Promise.all([...document.images].map(i=>i.complete?Promise.resolve():new Promise(r=>i.onload=r)));window.demoReady=true;
  }
  window.addEventListener('message',event=>{if(kind!=='platforms'||event.data?.type!=='readme-setting')return;const card=[...screens.querySelectorAll('[data-editor]')].find(c=>c.querySelector('iframe').contentWindow===event.source);if(!card)return;const message=event.data.message,win=event.source;if(message.type==='set'&&message.control==='effort'){const value=message.value,label={low:'Low',medium:'Medium',high:'High',xhigh:'Extra high',max:'Max',ultra:'Ultra'}[value];win.showDemo({preferences:{effort:value}});card.querySelector('[data-default]').textContent=label;card.querySelector('[data-effort]').textContent=(card.dataset.editor==='cursor'?'Claude Opus 5.5 ':'Gemini 4 Argon ')+label;}if(message.type==='setFastMode')win.showDemo({sessionDefaults:{...win.demoModel.sessionDefaults,fastMode:message.value}});if(message.type==='setUsageAlert')win.showDemo({usageAlerts:{cursor:message.enabled,gemini:message.enabled}});});
  document.querySelector('#previous').onclick=()=>{playing=false;render(index-1)};document.querySelector('#next').onclick=()=>{playing=false;render(index+1)};document.querySelector('#play').onclick=()=>{playing=!playing;document.querySelector('#play').textContent=playing?'Pause':'Play';document.querySelector('#play').setAttribute('aria-pressed',String(playing));};
  setInterval(()=>{if(playing&&!document.hidden)render(index+1)},6500);
  window.showcaseDemo={render,scenes,kind};start();
})();
