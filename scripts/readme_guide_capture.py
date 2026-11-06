"""Capture the existing guide DOM and shipped webview, without running installers or agents."""
from __future__ import annotations

import base64
import io
import json

from PIL import Image

STEPS = ("describe", "review", "plan", "implement", "test", "update")


def shot(locator):
    return Image.open(io.BytesIO(locator.screenshot(animations="disabled"))).convert("RGB")


def save_frames(output, kind, frames, durations, source, scenes, poster=0):
    """Use a shared palette and write a first-frame poster plus inspectable keyframes."""
    width, height = max(f.width for f in frames), max(f.height for f in frames)
    padded = []
    for frame in frames:
        canvas = Image.new("RGB", (width, height), "#111820")
        canvas.paste(frame, ((width-frame.width)//2, 0))
        padded.append(canvas)
    frames = padded
    sample = Image.new("RGB", (320 * min(len(frames), 24), 240))
    stride = max(1, len(frames) // 24)
    for i, frame in enumerate(frames[::stride][:24]):
        sample.paste(frame.resize((320, 240)), (320 * i, 0))
    palette = sample.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    target = output / f"nexus-hub-{kind}.gif"
    indexed[0].save(target, save_all=True, append_images=indexed[1:], duration=durations, loop=0, optimize=True, disposal=1)
    frames[poster].save(output / f"nexus-hub-{kind}.png", optimize=True)
    for i in sorted({0, len(frames) // 2, len(frames) - 1}):
        frames[i].save(output / f"{kind}-keyframe-{i:03}.png", optimize=True)
    assert target.stat().st_size < 4 * 1024 * 1024, f"{kind} exceeds 4 MiB"
    with Image.open(target) as result:
        total = 0
        for i in range(result.n_frames):
            result.seek(i)
            total += result.info["duration"]
        return {"kind": kind, "width": result.width, "height": result.height, "frames": result.n_frames, "duration_ms": total, "bytes": target.stat().st_size, "scenes": scenes, "source": source}


def capture_installation(page, root, output):
    page.goto((root / "guides/website/nexus-hub-guide.html").as_uri())
    page.add_style_tag(content=".site-header{visibility:hidden!important}")
    frames, durations = [], []
    # The real guide reserves the output height while lines stream into view.
    for os_name in ("win", "mac", "linux"):
        page.locator(f"#install-tab-{os_name}").click()
        terminal = page.locator(f'[data-tm="{os_name}"]')
        count = terminal.locator(".tm-l").count()
        for state, visible in [("prompt", 0), ("menu" if os_name == "win" else "click", 0), ("paste", 0), ("enter", 0)] + [("run", i) for i in range(1, count + 1, 2)] + [("done", count)]:
            terminal.evaluate("""(el, state) => { el.classList.add('tm--anim'); el.classList.remove('is-live'); el.dataset.tmStep=state[0]; el.querySelectorAll('.tm-l').forEach((line,i)=>line.classList.toggle('is-on',i<state[1])); }""", [state, visible])
            frames.append(shot(terminal))
            durations.append(3400 if state == "done" else 800 if state != "run" else 180)
    # OS terminal bodies differ slightly in height; letterbox instead of distorting.
    width, height = max(f.width for f in frames), max(f.height for f in frames)
    padded = []
    for frame in frames:
        canvas = Image.new("RGB", (width, height), "#111820")
        canvas.paste(frame, ((width - frame.width) // 2, 0))
        padded.append(canvas)
    return save_frames(output, "installation", padded, durations, "guides/website/nexus-hub-guide.html: .tm", 3, poster=durations.index(3400))


def training(page, root):
    page.goto((root / "guides/website/training.html").as_uri())
    page.wait_for_function("!!window.NexusTrainingPage?.story()")
    page.evaluate("document.fonts.ready")
    page.add_style_tag(content=".site-header{visibility:hidden!important}")


def capture_workflow(page, root, output):
    training(page, root)
    frames, durations = [], []
    poster = 0
    for step in STEPS:
        page.evaluate("id => window.NexusTrainingPage.go(id)", step)
        duration = page.evaluate("id=>window.NexusTrainingPage.story().state(id).duration", step)
        # Reparent the original nodes together. No new IDE markup or story text.
        page.evaluate("""id => { const section=document.getElementById(id), box=document.createElement('div'); box.id='readme-source-'+id; box.style.cssText='background:var(--bg);padding:16px 0 0'; const flow=section.querySelector('.tr-flow'); const ide=section.querySelector('.ide'); flow.style.margin='0 0 16px'; box.append(flow,ide); section.querySelector('.container').append(box); }""", step)
        times = sorted({0, 800, 1600, 2400, 3500, *range(5000, int(duration), 1800), int(duration)})
        for i, time in enumerate(times):
            page.evaluate("([id,t])=>window.NexusTrainingPage.story().seek(id,t)", [step, time])
            frames.append(shot(page.locator(f"#readme-source-{step}")))
            durations.append(2800 if i == len(times) - 1 else max(240, int((times[i + 1] - time) / 2)))
        frames[-1].save(output / f"workflow-{step}.png", optimize=True)
        if step == "describe":
            poster = len(frames) - 1
    return save_frames(output, "workflow", frames, durations, "guides/website/training.html + src/training-story.js + src/training-story.json", 6, poster=poster)


def capture_commands(page, root, output):
    page.goto((root / "guides/website/nexus-hub-guide.html").as_uri() + "#cheatsheets")
    page.add_style_tag(content=".site-header{visibility:hidden!important}")
    page.wait_for_timeout(150)
    section = page.locator("#page-cheatsheets")
    # Use the guide's real command cards and their original typography.
    page.evaluate("""() => {const section=document.getElementById('page-cheatsheets'); section.hidden=false; section.style.display='block';} """)
    groups = section.locator(".cs-cmd")
    assert groups.count(), "Guide command cards were not found"
    frames = []
    for name in ("/describe", "/review", "/plan", "/implement", "/test", "/update", "/handoff", "/skills"):
        card = groups.filter(has=page.locator(".cs-name", has_text=name)).first
        assert card.count(), name
        assert (root / "catalog/commands" / (name.removeprefix("/")+".md")).is_file(), name
        frames.append(shot(card))
    width = max(f.width for f in frames)
    height = max(f.height for f in frames)
    padded = []
    for frame in frames:
        canvas = Image.new("RGB", (width, height), "#071a20")
        canvas.paste(frame, ((width-frame.width)//2, 0))
        padded.append(canvas)
    return save_frames(output, "commands", padded, [6000]*len(padded), "guides/website/nexus-hub-guide.html: #page-cheatsheets", len(padded))


def panel_document(root):
    media = root / "extensions/nexus-hub-settings/media"
    skin = ":root{--vscode-font-family:Segoe UI,sans-serif;--vscode-font-size:13px;--vscode-foreground:#ddd;--vscode-descriptionForeground:#aaa;--vscode-sideBar-background:#181818;--vscode-editor-background:#181818;--vscode-focusBorder:#00b8cc;--vscode-input-background:#252526;--vscode-input-foreground:#eee;--vscode-button-background:#087e91;--vscode-button-foreground:#fff;--vscode-button-hoverBackground:#066b7b;--vscode-textLink-foreground:#47c8e5;background:#181818}"
    css = (media / "panel.css").read_text(encoding="utf-8")
    for name in ("claude-icon.svg", "codex-icon.svg"):
        data = base64.b64encode((media / name).read_bytes()).decode("ascii")
        css = css.replace("./" + name, "data:image/svg+xml;base64," + data)
    controls = [{"id": "effort", "choices": ["low","medium","high","xhigh","max","ultra"], "rows": [], "canApply": True}]
    for name in ("git_safety", "secret_scan", "edit_preservation", "large_file_warning", "git_guardrails"):
        controls.append({"id": name, "canApply": True, "rows": [{"tool": "internal", "value": "off" if name=="git_guardrails" else "on", "state": "in-effect", "canSet": True}]})
    model = {"controls": controls, "preferences": {"effort": "medium"}, "readOnly": False, "busy": False, "hubVersion": "4.14.8", "claudeAvailable": True, "codexAvailable": True, "showExtensionControls": True, "fastModeAvailable": True, "sessionDefaults": {"effort": "medium", "fastMode": False, "codexTabs": True}, "usageAlerts": {"claude": True,"codex": True,"copilot": True}, "usageAlertProviders": ["claude","codex","copilot"]}
    bridge = "window.demoModel="+json.dumps(model)+";window.acquireVsCodeApi=()=>({postMessage:m=>{if(m.type==='ready') window.dispatchEvent(new MessageEvent('message',{data:{type:'render',model:window.demoModel}}));}});window.showDemo=m=>{Object.assign(window.demoModel,m);window.dispatchEvent(new MessageEvent('message',{data:{type:'render',model:window.demoModel}}));};"
    return f'<!doctype html><html><meta charset="utf-8"><base href="{media.as_uri()}/"><style>{skin}{css}</style><main id="app" data-logo="{(media / "logo.png").as_uri()}" data-claude-icon="{(media / "claude-icon.svg").as_uri()}" data-codex-icon="{(media / "codex-icon.svg").as_uri()}"></main><script>{bridge}</script><script>{(media / "panel.js").read_text(encoding="utf-8")}</script></html>'


def capture_settings(page, root, output):
    training(page, root)
    page.evaluate("window.NexusTrainingPage.story().seek('describe',7000)")
    page.locator("#describe .ide-editor").evaluate("el=>el.remove()")
    page.locator("#describe .ide-chat").evaluate("""el=>{const clone=el.cloneNode(true);clone.dataset.provider='codex';el.dataset.provider='claude';el.after(clone); for(const [node,label,model] of [[el,'Claude Code','Claude Sonnet 5.5'],[clone,'Codex','GPT-6.1 Sol']]) {node.querySelector('.ide-chat-t').textContent=label;node.querySelector('.ide-usage-name').textContent='Usage';node.querySelector('.ide-log').innerHTML='<div class="ide-msg ide-msg--user"><p class="ide-who">You</p><p class="ide-said">Help me fix the ship&#39;s damage calculation.</p></div>';node.querySelector('.ide-input').textContent='Ask about this project';node.querySelector('.ide-pick--model .ide-pick-name').textContent=model;node.querySelector('.ide-lock').remove();}}""")
    # Reuse the guide's menus, activity bar and chat components. Replace Explorer
    # with the shipped panel and show two side-by-side illustrative sessions.
    page.locator("#describe .ide-explorer").evaluate("""(el,content)=>{el.style.cssText='padding:0;width:360px;overflow:hidden';const frame=document.createElement('iframe'); frame.title='Nexus Hub settings';frame.style.cssText='border:0;width:100%;height:100%';frame.srcdoc=content;el.replaceChildren(frame);} """, panel_document(root))
    page.add_style_tag(content="#describe .ide-main{grid-template-columns:44px 360px minmax(0,1fr) minmax(0,1fr)} #describe .ide{height:820px} #describe .ide-pick--mode{display:none} #describe .ide-pick--model{max-width:170px} #describe .ide-pick--effort{max-width:none} #describe .ide-chat-t{white-space:nowrap;min-width:80px} .readme-caption{padding:14px 18px;background:#151b21;color:#e2e6ea;font:14px Segoe UI,sans-serif}")
    page.locator("#describe .ide").evaluate("""el=>{const box=document.createElement('div');box.id='settings-capture';el.before(box);box.append(el);const caption=document.createElement('p');caption.className='readme-caption';box.append(caption);} """)
    frame = page.frame_locator("#describe .ide-explorer iframe")
    frame.locator("#effort-title").wait_for()
    frames, durations = [], []
    scenes = (("medium",False,None,"Medium"),("low",False,None,"Low"),("low",False,None,"Medium"),("low",False,None,"Low"),("low",True,None,"Low"),("low",True,".guardrails-section","Low"),("low",True,".usage-alerts-section","Low"),("low",True,".editor-section","Low"))
    labels = ("Global default: Medium", "Global change: Low in both sessions", "Manual Codex choice: Medium", "Apply to all: Low restored", "Fast mode on", "Guardrails", "Usage alerts", "Extension controls")
    for index, (effort, fast, scroll, codex_effort) in enumerate(scenes):
        frame.locator("body").evaluate("""(el,state)=>{ window.showDemo({preferences:{effort:state[0]},sessionDefaults:{effort:state[0],fastMode:state[1],codexTabs:true}});window.scrollTo(0,state[2]?document.querySelector(state[2]).offsetTop:0); }""", [effort,fast,scroll])
        page.locator("#describe .ide-chat").evaluate_all("""(nodes,s)=>nodes.forEach(n=>{n.querySelector('.ide-pick--effort .ide-pick-name').textContent=n.dataset.provider==='codex'?s[1]:s[0];n.querySelector('.ide-pick--model').setAttribute('aria-label',s[2]?'Model / Fast mode on':'Model / Fast mode off');n.querySelector('.ide-chat-t').textContent=(n.dataset.provider==='codex'?'Codex':'Claude Code')+(s[2]?' / Fast':'');})""", [effort.capitalize(),codex_effort,fast])
        page.locator("#settings-capture .readme-caption").evaluate("(el,text)=>el.textContent=text+' / Illustrative sessions; shipped settings panel'",labels[index])
        frames.append(shot(page.locator("#settings-capture")))
        durations.append(4500)
        frames[-1].save(output / f"settings-scene-{index+1:02}.png", optimize=True)
    return save_frames(output,"settings",frames,durations,"guides/website/training.html shell + extensions/nexus-hub-settings/media/panel.{js,css}",len(frames))
