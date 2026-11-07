"use strict";

const HANDOFF_TEXT = `# Handoff | 2026-11-07T16:20:00Z | claude-desktop | usage-limit

Previous handoffs: None.

## Goal
Fix ship damage handling and add regression tests.

## Done and verified
- Reviewed the supplied src/damage.js.
- The supplied test report shows the nonfatal-hit test passes: 100 health - 6 damage = 94.

## In progress
- The zero-health regression test is still missing.

## Next steps
1. Check the supplied source and test report.
2. Add a test: 6 health - 6 damage = 0, destroyed is true.
3. Run npm test in a tool with project access and report the result.

## Files touched
None in this desktop chat. Supplied context: src/damage.js, tests/damage.test.js, test-summary.txt.

## Constraints and decisions the user stated
- Preserve unrelated edits and the public API.

## Open questions and blockers
None.

## Repository state
Not a git repository in this desktop chat; branch, HEAD, and uncommitted changes omitted.`;
const platformDemoScenes = [
 {title:"Open the project",text:"Open nexus-defenders with its project files and Nexus Hub guidance.",phase:0,step:0,target:"open-project"},
 {title:"Work in Claude",text:"The supplied report passes the nonfatal test. The zero-health regression is unfinished.",phase:1,step:0,target:"claude-chat"},
 {title:"Choose how to proceed",text:"Nexus pauses new work and offers Wait for reset, Hand off, or Continue on credits.",phase:2,step:1,target:"usage-question"},
 {title:"Select Hand off",text:"Choose Hand off to generate a resume prompt and continue in another tool.",phase:3,step:2,target:"handoff-choice",click:true},
 {title:"Generate the handoff",text:"The prompt records the goal, verified work, unfinished steps, files, constraints, and repository state.",phase:4,step:2,target:"handoff-output",generate:true},
 {title:"Review the prompt",text:"The full Nexus handoff is ready to copy. It describes task work, without carrying the old usage limit into the next session.",phase:5,step:2,target:"handoff-output"},
 {title:"Click Copy",text:"Copy the complete handoff from Claude's response.",phase:6,step:3,target:"copy-handoff",click:true},
 {title:"Handoff copied",text:"The clipboard now contains the full resume prompt.",phase:7,step:3,target:"copy-handoff"},
 {title:"Switch to ChatGPT",text:"Focus ChatGPT's composer in the project that contains the relevant files.",phase:8,step:3,target:"chatgpt-input",click:true},
 {title:"Paste the handoff",text:"Paste the same full prompt into ChatGPT's input. Review it before sending.",phase:9,step:3,target:"chatgpt-input"},
 {title:"Send the prompt",text:"Send the handoff as a user message.",phase:10,step:3,target:"chatgpt-send",click:true},
 {title:"Resume from the handoff",text:"The sent message contains the full handoff. ChatGPT recovers the unfinished zero-health test.",phase:11,step:4,target:"sent-handoff"},
 {title:"Continue the task",text:"ChatGPT drafts the missing test. Run and verify it in a tool with project access.",phase:12,step:4,target:"chatgpt-chat"}
];
function escapeDemo(value){return String(value).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
function desktopTaskbar() {
  return `<div class="computer-taskbar"><div class="taskbar-center"><span class="start-mark" aria-hidden="true"><i></i><i></i><i></i><i></i></span><span class="desktop-search">&#9906; Search</span><span class="taskbar-app active">${mark('claude')}</span><span class="taskbar-app active">${mark('codex')}</span><span class="taskbar-app terminal-symbol">&gt;_</span></div><span class="desktop-clock">&#8963; &nbsp; &#9682; &nbsp; &#9834; &nbsp; 10:42 AM<br>11/7/2026</span></div>`;
}
function processStrip(labels,active,kind) {
  return `<ol class="process-strip" aria-label="${kind} process">${labels.map((label,i)=>`<li class="${i===active?'active':i<active?'done':''}" ${i===active?'aria-current="step"':''}><span>${i<active?'&#10003;':i+1}</span><b>${label}</b></li>`).join('')}</ol>`;
}
function nativeWindow(provider,body,project,composer) {
  const claude=provider==='Claude',id=claude?'claude':'chatgpt';
  const sidebar=`<aside class="project-sidebar"><div class="app-wordmark">${claude?'Claude':'ChatGPT'} <span>&#9776;</span></div><span class="project-new">&#9998; &nbsp; New chat</span><span class="project-new">&#9906; &nbsp; Search chats</span>${claude?'<span class="project-new">&#9633; &nbsp; Projects</span><span class="project-new">&#9671; &nbsp; Artifacts</span>':'<span class="project-new">&#9638; &nbsp; Library</span>'}<b>Projects</b><div class="project-item ${project?'active':''}">&#9633; nexus-defenders</div><div class="project-item">&#9633; Design review</div><b>${claude?'Recents':'Your chats'}</b><div class="project-item">Damage regression</div><div class="project-item">Project review</div><div class="app-account"><span>BD</span> Ben Dourthe</div></aside>`;
  return `<article class="native-window ${claude?'claude-app':'chatgpt-app'}" aria-label="${provider} desktop window"><div class="native-title">${mark(claude?'claude':'codex')}<span>${provider}</span><span class="native-window-buttons" aria-hidden="true">&#8722; &nbsp; &#9633; &nbsp; &#215;</span></div><div class="native-app-layout">${sidebar}<div class="native-conversation"><div class="native-provider"><span>${claude?'Chat &nbsp; Cowork &nbsp; Code':'ChatGPT &#8964;'}</span><span>&#8599; &nbsp; &#183;&#183;&#183;</span></div><div class="project-heading">${project?'nexus-defenders':'Projects'} <span>&#8964;</span></div><div class="native-chat">${body}</div><div class="native-composer ${composer?'pasted':''}" data-target="${id}-input">${composer?`<textarea readonly aria-label="ChatGPT prompt">${escapeDemo(composer)}</textarea>`:`<div>${claude?'Reply...':'Ask anything'}</div>`}<div class="composer-tools"><span>+</span><span>${claude?'Sonnet &#8964;':'&#9834;'}</span><span class="send-symbol" data-target="${id}-send" aria-label="Send">&#8593;</span></div></div><div class="app-footnote">${claude?'Claude is AI and can make mistakes.':'ChatGPT can make mistakes. Check important info.'}</div></div></div></article>`;
}
function platformMarkup(s, options={}) {
 const p=s.phase, progress=options.generateProgress??1;
 let left='';
 if(p===0)left='<div class="native-welcome"><h3>Projects</h3><p>Your work, with its own context.</p><div class="project-card" data-target="open-project"><b>nexus-defenders</b><p>Ship damage and regression tests</p><small>Files and Nexus Hub guidance added</small></div></div>';
 else if(p<4)left=`<div class="native-user">Fix the ship's damage calculation and add regression tests.</div><div class="native-message" data-target="claude-chat"><p>The supplied nonfatal test passes. Next: the zero-health regression.</p><div class="changed-file">damage.js <span>Project context</span></div></div>${p>=2?`<div class="native-question" data-target="usage-question"><p class="usage-question-title">Usage limit reached</p><p>New work is paused. How would you like to continue?</p>${[['wait','Wait for reset','Stop here and wait for the allowance to reset.'],['handoff','Hand off','Generate a resume prompt for another tool.'],['credits','Continue on credits','Use pay-per-use credits after confirming spending.']].map(([value,label,note])=>`<div class="native-option ${p===3&&value==='handoff'?'selected':''}" ${value==='handoff'?'data-target="handoff-choice"':''}><i></i><span><b>${label}</b>${value==='wait'?'<small class="recommended">Recommended</small>':''}<small>${note}</small></span></div>`).join('')}</div>`:''}`;
 else {const generated=p===4?HANDOFF_TEXT.slice(0,Math.max(28,Math.floor(HANDOFF_TEXT.length*progress))):HANDOFF_TEXT;left=`<div class="native-user compact">Hand off</div><div class="native-message"><p>${p===4&&progress<1?'Generating the handoff...':'Paste this prompt into the agent that will continue.'}</p></div><div class="handoff-code" data-target="handoff-output"><div class="code-toolbar"><span>Nexus handoff</span><span class="copy-button ${p>=7?'copied':''}" data-target="copy-handoff">${p>=7?'&#10003; Copied':'&#10697; Copy'}</span></div><pre class="handoff-output">${escapeDemo(generated)}${p===4&&progress<1?'<span class="typing-caret">&#9612;</span>':''}</pre></div>`;}
 let right='<div class="native-welcome"><h3>What can I help with?</h3><p>nexus-defenders</p></div>';
 if(p>=11)right=`<div class="native-user sent-handoff" data-target="sent-handoff"><pre>${escapeDemo(HANDOFF_TEXT)}</pre></div><div class="native-message" data-target="chatgpt-chat"><p>I have the task context. The missing step is the zero-health regression.</p>${p===12?'<pre class="native-test">test("zero health destroys the ship", () =&gt; {\n  const result = applyHit({ health: 6 }, 6);\n  expect(result.health).toBe(0);\n  expect(result.destroyed).toBe(true);\n});</pre><p>Add this test, then run npm test in the project.</p>':''}</div>`;
 const pasted=p===9||p===10?HANDOFF_TEXT:'';
 return `<div class="split-desktop"><div class="desktop-label"><span>nexus-defenders</span><span>Claude desktop &#8594; ChatGPT desktop</span></div><div class="split-windows">${nativeWindow('Claude',left,p>0,'')}${nativeWindow('ChatGPT',right,true,pasted)}</div>${desktopTaskbar()}</div>${processStrip(['Project','Usage choice','Handoff','Copy and paste','Resume'],s.step,'Handoff')}`;
}
