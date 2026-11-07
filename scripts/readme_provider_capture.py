"""Render the shipped settings and usage components inside the README's VS Code frame."""
from __future__ import annotations

import json
import subprocess

from readme_guide_capture import panel_document, save_frames, shot

SKIN = ":root{color-scheme:dark;--vscode-font-family:Segoe UI,Arial,sans-serif;--vscode-font-size:13px;--vscode-foreground:#ccc;--vscode-editor-foreground:#ccc;--vscode-editor-background:#1f1f1f;--vscode-descriptionForeground:#999;--vscode-button-background:#0078a3;--vscode-button-foreground:#fff;--vscode-button-hoverBackground:#028cb8;--vscode-input-background:#313131;--vscode-input-foreground:#ddd;--vscode-input-border:#454545;--vscode-focusBorder:#007fd4;--vscode-textLink-foreground:#4daafc}"


def components(root):
    panel = panel_document(root)
    model = json.loads(panel.split("window.demoModel=", 1)[1].split(";window.acquire", 1)[0])
    process = subprocess.run(["node", str(root / "scripts/readme_usage_render.cjs")], input=json.dumps({"model": model}), capture_output=True, text=True, encoding="utf-8", check=True, timeout=30)
    usage = json.loads(process.stdout)
    for provider in ("claude", "codex", "copilot"):
        usage[provider]["dashboard"] = usage[provider]["dashboard"].replace("</head>", f"<style>{SKIN}</style></head>")
    return {"panel": panel, "usage": usage}


def component_script(value):
    return "window.README_COMPONENTS=" + json.dumps(value).replace("<", "\\u003c") + ";\n"


def capture_provider(page, root, output, kind, source):
    page.add_init_script("window.README_GENERATED=" + json.dumps(source).replace("<", "\\u003c"))
    page.goto((root / "guides/website/readme-vscode.html").as_uri() + "?tour=" + kind)
    page.wait_for_function("!!window.demoReady")
    frames, durations = [], []
    count = page.evaluate("kind=>window.vscodeDemo.scenes[kind].length", kind)
    for index in range(count):
        scene = page.evaluate("([kind,index])=>window.vscodeDemo.scenes[kind][index]",[kind,index])
        action = kind == "settings" and index in (1,4,5,6,8) or kind == "usage" and bool(scene.get("dashboard"))
        before = index - 1 if action and index != 8 else index
        page.evaluate("([kind,index])=>window.vscodeDemo.render(kind,index,{progress:0})", [kind,before])
        if kind == "settings" and index == 8:
            page.frame_locator(".settings-webview").locator("body").evaluate("()=>{window.showDemo({usageAlerts:{claude:true,codex:true,copilot:true}});window.scrollTo(0,document.querySelector('.usage-alerts-section').offsetTop);}")
        page.locator("#vs-tour-title").evaluate("(el,text)=>el.textContent=text",scene["title"])
        page.locator("#vs-tour-description").evaluate("(el,text)=>el.textContent=text",scene["text"])
        motion = page.evaluate("([kind,index])=>window.vscodeDemo.highlight(window.vscodeDemo.scenes[kind][index],{progress:0,click:false})", [kind,index])
        for progress in (.25,.5,.75,1):
            page.evaluate("([kind,index,progress,from])=>window.vscodeDemo.highlight(window.vscodeDemo.scenes[kind][index],{progress,from,click:false})", [kind,index,progress,motion["from"]])
            frames.append(shot(page.locator("#vscode-stage")))
            durations.append(100)
        page.evaluate("([kind,index])=>window.vscodeDemo.highlight(window.vscodeDemo.scenes[kind][index],{click:true})", [kind,index])
        frames.append(shot(page.locator("#vscode-stage")))
        durations.append(180)
        if kind == "usage" and scene.get("dashboard"):
            page.locator('[data-usage="'+scene["dashboard"]+'"]').click()
        elif kind == "settings":
            panel = page.frame_locator(".settings-webview")
            if index == 1: panel.get_by_role("radio",name="Low",exact=True).click()
            elif index == 5: panel.get_by_role("button",name="Apply to all",exact=True).click()
            elif index == 6: panel.get_by_role("switch",name="Fast mode",exact=True).click()
            elif index == 8: panel.get_by_role("checkbox",name="All usage alerts",exact=True).click()
        if action:
            page.evaluate("([kind,index])=>window.vscodeDemo.render(kind,index)",[kind,index])
        page.evaluate("([kind,index])=>window.vscodeDemo.highlight(window.vscodeDemo.scenes[kind][index],{click:false})", [kind,index])
        frame = shot(page.locator("#vscode-stage"))
        frames.append(frame)
        durations.append(3300 if kind == "settings" else 4200)
        frame.save(output / f"{kind}-scene-{index+1:02}.png", optimize=True)
        assert page.locator(".claude-session .vs-tab").inner_text().startswith("Claude Code")
        if kind == "settings":
            scene = page.evaluate("i=>window.vscodeDemo.scenes.settings[i]",index)
            expected = scene.get("codex") or ("Low" if scene.get("effort") == "low" else "Medium")
            assert page.locator("[data-native=codex-effort] b").inner_text() == expected
        else:
            scene = page.evaluate("i=>window.vscodeDemo.scenes.usage[i]",index)
            if scene.get("dashboard"):
                assert page.frame_locator(".usage-dashboard iframe").locator("h2").count()
            else:
                assert page.locator(".vs-hover img").count() > 0
    return save_frames(output,kind,frames,durations,"guides/website/readme-vscode.* + shipped settings and monitor renderers",count,poster=5)
