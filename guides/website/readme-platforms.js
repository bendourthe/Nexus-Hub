"use strict";

// Representative examples. /skills list reads the current command catalog.
const readmeCommandGroups = [
  {title:"Understand",items:[["/describe","Map the project"],["/review","Review code and risks"],["/compare","Compare an external source"],["/research","Investigate a topic"]]},
  {title:"Build",items:[["/spec","Clarify requirements"],["/plan","Define phases and checks"],["/implement","Build and verify"],["/test","Test behavior and boundaries"],["/update release","Prepare the release"]]},
  {title:"Continue",items:[["/handoff","Generate a resume prompt"],["/usage","Inspect supported usage sources"],["/route","Choose a model"],["/skills list","Show the current cheatsheet"]]}
];
const commandDemoScenes = [
  {title:"Command discovery",text:"Run /skills list inside an installed agent to see the current commands and arguments.",command:"/skills list",target:"command-input"},
  {title:"Focused review",text:"Add a scope when needed: /review security reviews security rather than the whole project.",command:"/review security",target:"command-input"},
  {title:"Task handoff",text:"Use /handoff when switching tools. The generated prompt carries the task and its next step.",command:"/handoff focus on the damage regression",target:"command-input"}
];
const platformDemoScenes = [
  {title:"Open the project",text:"Open nexus-defenders in Claude. The same project context is ready in ChatGPT.",phase:0,step:0,target:"open-project"},
  {title:"Work in Claude",text:"Claude reviews the supplied files. The zero-health regression is still unfinished.",phase:1,step:0,target:"claude-chat"},
  {title:"Usage warning",text:"A usage warning pauses new work. Claude offers to generate a handoff.",phase:2,step:1,target:"handoff-choice"},
  {title:"Generate a handoff",text:"Choose Generate handoff to continue the task in another tool.",phase:3,step:2,target:"handoff-choice"},
  {title:"Generate the prompt",text:"Claude records completed work, supplied test evidence, constraints, and the next step.",phase:4,step:2,target:"copy-handoff"},
  {title:"Copy the handoff",text:"Copy the generated prompt from Claude's chat.",phase:5,step:3,target:"copy-handoff"},
  {title:"Paste into ChatGPT",text:"Paste the handoff into the ChatGPT project with the relevant files, then send it.",phase:6,step:3,target:"chatgpt-input"},
  {title:"Recover the next step",text:"ChatGPT identifies the same unfinished zero-health regression from the supplied context.",phase:7,step:4,target:"chatgpt-chat"},
  {title:"Continue the task",text:"ChatGPT drafts the missing test. Run and verify that change in a tool with project access.",phase:8,step:4,target:"chatgpt-chat"}
];
const INSTALL_WINDOWS="irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1 | iex";
const INSTALL_POSIX="curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash";
const installationDemoScenes = [
  {title:"Open PowerShell",text:"On Windows, open PowerShell and copy the install command from the guide.",os:"windows",phase:0,step:0,target:"terminal-input"},
  {title:"Paste the command",text:"Right-click to paste the command into PowerShell.",os:"windows",phase:1,step:0,target:"terminal-paste"},
  {title:"Run the installer",text:"Press Enter to download the catalog and start the installer.",os:"windows",phase:2,step:1,target:"terminal-input"},
  {title:"Configure detected tools",text:"The installer copies harness files into the supported tools it finds on your machine.",os:"windows",phase:3,step:1,target:"terminal-output"},
  {title:"Verify the install",text:"Review the verification result, then reopen your IDE or start a new agent session.",os:"windows",phase:4,step:2,target:"terminal-output"},
  {title:"macOS Terminal",text:"On macOS, paste the shell command into Terminal and press Enter.",os:"mac",phase:2,step:1,target:"terminal-input"},
  {title:"macOS verification",text:"The same catalog is installed into the supported tools detected on macOS.",os:"mac",phase:4,step:2,target:"terminal-output"},
  {title:"Linux Terminal",text:"On Linux, run the same shell command in your terminal.",os:"linux",phase:2,step:1,target:"terminal-input"},
  {title:"Linux verification",text:"Review the detected platforms and verification result before starting a new session.",os:"linux",phase:4,step:2,target:"terminal-output"}
];
function desktopTaskbar(message="") {
  return `<div class="computer-taskbar"><span class="start-mark" aria-hidden="true">&#8862;</span><span class="taskbar-app">${mark('claude')}</span><span class="taskbar-app">${mark('codex')}</span><span class="taskbar-app terminal-symbol">&gt;_</span><span class="clipboard-status">${message}</span><span class="desktop-clock">10:42</span></div>`;
}
function processStrip(labels,active,kind) {
  return `<ol class="process-strip" aria-label="${kind} process">${labels.map((label,i)=>`<li class="${i===active?'active':i<active?'done':''}" ${i===active?'aria-current="step"':''}><span>${i<active?'&#10003;':i+1}</span><b>${label}</b></li>`).join('')}</ol>`;
}
function nativeWindow(provider,body,project,composer) {
  const claude=provider==='Claude',id=claude?'claude':'chatgpt';
  const sidebar=`<aside class="project-sidebar"><span class="project-new">New chat</span><b>Projects</b><div class="project-item ${project?'active':''}">nexus-defenders</div><div class="project-item">Design review</div>${project?'<b>Project files</b><span class="project-file">damage.js</span><span class="project-file">damage.test.js</span><span class="project-file">test-summary.txt</span><span class="project-file">Nexus Hub guidance</span>':''}</aside>`;
  return `<article class="native-window ${claude?'claude-app':'chatgpt-app'}" aria-label="${provider} desktop window"><div class="native-title">${mark(claude?'claude':'codex')}<b>${provider}</b><span class="native-window-buttons" aria-hidden="true">- &nbsp; &#9633; &nbsp; &#215;</span></div><div class="native-app-layout">${sidebar}<div class="native-conversation"><div class="native-provider"><b>${project?'nexus-defenders':'Projects'}</b><span>Project chat</span></div><div class="native-chat">${body}</div><div class="native-composer ${composer?'pasted':''}" data-target="${id}-input">${composer||'Message '+provider+'...'}<span class="send-symbol" aria-label="Send">&#8593;</span></div></div></div></article>`;
}
function platformMarkup(s) {
  const p=s.phase;
  let left='';
  if(p===0)left='<div class="native-welcome"><h3>Claude</h3><p>Choose a project to begin.</p><span class="native-button" data-target="open-project">Open project...</span><div class="recent-project">Recent: nexus-defenders</div></div>';
  else if(p<4)left=`<div class="native-user">Fix the ship\'s damage calculation and add regression tests.</div><div class="native-message" data-target="claude-chat"><b>Claude</b><p>The supplied test report passes the nonfatal hit. Next: the zero-health regression.</p><div class="changed-file">damage.js <span>supplied file</span></div></div>${p>=2?`<div class="native-limit">Usage limit warning. New work is paused.</div><div class="native-question"><b>Generate a handoff to continue elsewhere?</b><div class="native-option ${p===3?'selected':''}" data-target="handoff-choice"><i></i><span>Generate handoff</span></div><div class="native-option"><i></i><span>Not now</span></div></div>`:''}`;
  else left=`<div class="native-user compact">Generate handoff</div><div class="native-message"><b>Claude</b><p>Paste this prompt into the agent that will continue.</p></div><div class="handoff-code"><div class="code-toolbar"><span>Handoff prompt (excerpt)</span><span class="copy-button ${p>=5?'copied':''}" data-target="copy-handoff">${p>=5?'&#10003; Copied':'Copy'}</span></div><pre>Goal: fix damage handling.\n\nReviewed: supplied damage.js.\nVerified: nonfatal test passes\n(from supplied test report).\nOpen: zero-health regression.\n\nNext:\n1. Check the supplied context.\n2. Add the zero-health test.\n3. Run npm test.\n\nPreserve unrelated edits.</pre></div>`;
  let right='<div class="native-welcome"><h3>ChatGPT</h3><p>nexus-defenders</p><p class="subtle">Ready for your next task.</p></div>';
  if(p>=7)right=`<div class="native-user compact">Continue from this handoff. Check the current state first.</div><div class="native-message" data-target="chatgpt-chat"><b>ChatGPT</b><p>From the supplied context:<br>The damage fix is present.<br>Remaining: zero-health regression.</p>${p===8?'<div class="changed-file">Suggested test <span>draft</span></div><pre class="native-test">test("zero health destroys the ship", () =&gt; {\n  const result = applyHit({ health: 6 }, 6);\n  expect(result.health).toBe(0);\n  expect(result.destroyed).toBe(true);\n});</pre><p>Add this test in the project, then run npm test.</p>':'<p>I will use the supplied files to draft that test and preserve the existing design.</p>'}</div>`;
  const pasted=p===6?'Continue from this handoff.\n\nReviewed: damage.js; supplied nonfatal test passes.\nNext: add the zero-health regression, then run npm test.\nBranch: feat/damage-fix':'';
  return `<div class="split-desktop"><div class="desktop-label"><span>nexus-defenders</span><span>Claude desktop &#8594; ChatGPT desktop</span></div><div class="split-windows">${nativeWindow('Claude',left,p>0,'')}${nativeWindow('ChatGPT',right,true,pasted)}</div>${desktopTaskbar(p===5?'Handoff copied':p===6?'Handoff pasted into ChatGPT':'Project context supplied to both apps')}</div>${processStrip(['Project','Usage warning','Handoff','Copy and paste','Resume'],s.step,'Handoff')}`;
}
function installationMarkup(s) {
  const win=s.os==='windows',mac=s.os==='mac',command=win?INSTALL_WINDOWS:INSTALL_POSIX;
  const title=win?'Windows PowerShell':mac?'Terminal - dev@MacBook':'Terminal - dev@ubuntu';
  const prompt=win?'PS C:\\Users\\dev&gt;':mac?'dev@MacBook ~ %':'dev@ubuntu:~$';
  const home=win?'C:\\Users\\dev':mac?'/Users/dev':'/home/dev';
  let output='';
  if(s.phase>=3)output=`<div class="terminal-lines" data-target="terminal-output"><div>Downloading Nexus-Hub catalog (bendourthe/Nexus-Hub@main)...</div><div class="terminal-warning">warning: unverified 'main' tarball (no published checksum).</div><div>Extracting catalog to ${home}${win?'\\.nexus-hub\\src':'/.nexus-hub/src'}...</div><div>Running installer...</div><br><div>SKILLS &amp; COMMANDS</div><div>Checking User Profile (${home})...</div><div>[OK] Claude Code: skills, commands, rules</div><div>[OK] Other detected platforms configured</div></div>`;
  if(s.phase>=4)output+=`<div class="terminal-verified"><br>INSTALL VERIFICATION<br>[verify] PASS Claude -- commands:ok, skills:ok, CLAUDE.md SKILL_INDEX:ok<br>[verify] all detected platforms surface the catalog.<br><br>Nexus-Hub installed (Global scope).${win?'<br>Press Enter to continue...':''}</div>`;
  return `<div class="install-desktop ${s.os}"><div class="terminal-window"><div class="terminal-title"><span class="terminal-symbol">&gt;_</span>${title}<span class="native-window-buttons" aria-hidden="true">- &nbsp; &#9633; &nbsp; &#215;</span></div><div class="terminal-content"><div class="terminal-input" data-target="terminal-input"><span>${prompt} </span><code>${s.phase>=2?escapeHtml(command):'<span class="terminal-caret"></span>'}</code></div>${s.phase===1?'<div class="terminal-menu"><span>Copy</span><b data-target="terminal-paste">Paste</b><span>Select all</span></div>':''}${output}</div></div><div class="install-desktop-label">${win?'Windows':mac?'macOS':'Linux'} / Selected example output</div></div>${processStrip(['Paste command','Install','Verify'],s.step,'Installation')}`;
}
function commandMarkup(s) {
  const items=readmeCommandGroups.flatMap(group=>group.items);
  return `${chrome()}<div class="commands-editor"><aside class="commands-explorer"><h3>NEXUS-DEFENDERS</h3><div>src/</div><div>tests/</div><div>docs/</div><div>README.md</div></aside><article class="commands-chat"><div class="provider-mini">${mark('claude')}<b>Claude Code</b><span class="subtle">Agent</span></div><div class="command-user" data-target="command-input">${s.command}</div><div class="command-reply"><b>Command cheatsheet</b><p class="subtle">Representative examples. /skills list reads the current catalog.</p><table><thead><tr><th>Command</th><th>Purpose</th></tr></thead><tbody>${items.map(([command,purpose])=>`<tr><td><code>${command}</code></td><td>${purpose}</td></tr>`).join('')}</tbody></table></div></article></div>`;
}
