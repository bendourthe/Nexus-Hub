"""Exercise the shipped panel against the real settings CLI in a disposable home."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

EXT = Path(__file__).resolve().parents[1]
REPO = EXT.parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from nexus_process import install_no_window_default

install_no_window_default()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    args = parser.parse_args()
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=False)
    home = work / "home"
    project = work / "project"
    bin_dir = work / "bin"
    for directory in (home / ".claude", home / ".codex", project, bin_dir):
        directory.mkdir(parents=True)
    (home / ".claude/settings.json").write_text(json.dumps({"env": {"CLAUDE_CODE_EFFORT_LEVEL": "low"}, "model": "opus"}), encoding="utf-8")
    (home / ".codex/config.toml").write_text('model_reasoning_effort = "low"\n', encoding="utf-8")
    for name, version in (("claude", "2.1.283"), ("codex", "0.136.0")):
        if os.name == "nt":
            (bin_dir / f"{name}.cmd").write_text(f"@echo off\r\necho {version}\r\n", encoding="ascii")
        else:
            tool = bin_dir / name
            tool.write_text(f"#!/bin/sh\nprintf '%s\\n' '{version}'\n", encoding="ascii")
            tool.chmod(0o700)
    env = {key: value for key, value in os.environ.items() if not key.upper().startswith(("NEXUS", "CLAUDE", "ANTHROPIC", "CODEX", "COPILOT", "VSCODE", "AI_AGENT"))}
    env.update(HOME=str(home), USERPROFILE=str(home), PATH=str(bin_dir) + os.pathsep + os.environ.get("PATH", ""))
    node = shutil.which("node")
    assert node, "Node is required"
    observations: dict[str, object] = {"actions": [], "screenshots": [], "console_errors": []}

    def cli(*arguments: str) -> dict:
        result = subprocess.run([sys.executable, str(REPO / "scripts/nexus_hub_cli.py"), "settings", *arguments, "--json", "--project", str(project)], env=env, capture_output=True, text=True, encoding="utf-8", timeout=45, check=False)
        assert result.returncode in (0, 4), result.stderr
        return json.loads(result.stdout)

    def model() -> dict:
        report = cli("show")
        explains = {control: cli("explain", control) for control in {row["control"] for row in report["records"]}}
        source = "const fs=require('fs');const {buildModel}=require(process.argv[1]);const input=JSON.parse(fs.readFileSync(0,'utf8'));input.inspect=()=>({registered:false});console.log(JSON.stringify(buildModel(input)));"
        result = subprocess.run([node, "-e", source, str(EXT / "out/viewModel.js")], input=json.dumps({"report": report, "explains": explains, "trusted": True, "profile": "Smoke"}), capture_output=True, text=True, encoding="utf-8", timeout=15, check=True)
        return json.loads(result.stdout)

    def dispatch(message: dict) -> dict:
        if message["type"] == "set":
            assert message["control"] in ("effort", "large_file_warning")
            dry = cli("set", message["control"], message["value"], "--dry-run")
            assert not dry.get("confirmation", {}).get("required"), "This smoke never approves a safety reduction"
            changed = cli("set", message["control"], message["value"])
            observations["actions"].append({"message": message, "exit_code": changed["exit_code"]})
        return model()

    initial = model()
    logo = (EXT / "media/logo.png").as_uri()
    css = (EXT / "media/panel.css").read_text(encoding="utf-8")
    script = (EXT / "media/panel.js").read_text(encoding="utf-8")
    skin = ":root{--vscode-font-family:Segoe UI,sans-serif;--vscode-font-size:13px;--vscode-foreground:#ddd;--vscode-descriptionForeground:#aaa;--vscode-sideBar-background:#181818;--vscode-editor-background:#181818;--vscode-focusBorder:#00b8cc;--vscode-input-background:#252526;--vscode-input-foreground:#eee;--vscode-button-background:#087e91;--vscode-button-foreground:#fff;--vscode-button-hoverBackground:#066b7b;--vscode-errorForeground:#f48771;--vscode-editorWarning-foreground:#e5c07b;--vscode-textLink-foreground:#47c8e5;background:#181818}"
    bridge = "window.__initial=" + json.dumps(initial).replace("<", "\\u003c") + ";window.acquireVsCodeApi=()=>({postMessage:async m=>{const model=window.smokeDispatch?await window.smokeDispatch(m):window.__initial;window.dispatchEvent(new MessageEvent('message',{data:{type:'render',model}}));}});"
    html = f'<!DOCTYPE html><html lang="en"><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nexus Settings Smoke</title><style>{skin}{css}</style><main id="app" data-logo="{logo}"></main><div id="live-status" class="visually-hidden" role="status" aria-live="polite"></div><div id="live-alert" class="visually-hidden" role="alert"></div><script>{bridge}</script><script>{script}</script></html>'
    page_file = work / "panel.html"
    page_file.write_text(html, encoding="utf-8")

    from playwright.sync_api import sync_playwright

    with sync_playwright() as runtime:
        browser = runtime.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 420, "height": 900})
        page.on("pageerror", lambda error: observations["console_errors"].append(str(error)))
        page.expose_function("smokeDispatch", dispatch)
        page.goto(page_file.as_uri())
        page.get_by_role("radiogroup", name="Default effort", exact=True).wait_for()
        assert page.locator("select").count() == 0
        assert page.get_by_role("radio").count() == 6
        assert page.get_by_role("switch").count() == 5
        assert page.locator(".effort-value").count() == 0
        card_spacing = page.evaluate("""() => {
            const heading = document.querySelector('.section-heading').getBoundingClientRect();
            const track = document.querySelector('.effort-choices').getBoundingClientRect();
            return track.top - heading.bottom;
        }""")
        assert 0 <= card_spacing <= 6, f"Excess effort card spacing: {card_spacing}"
        observations["effort_heading_gap"] = card_spacing
        page.get_by_role("radio", name="Medium", exact=True).click()
        page.wait_for_function("document.querySelector('[role=radio][data-value=medium]').getAttribute('aria-checked') === 'true'")
        assert json.loads((home / ".nexus-hub/preferences.json").read_text())["default_effort"] == "medium"
        assert json.loads((home / ".claude/settings.json").read_text())["env"]["CLAUDE_CODE_EFFORT_LEVEL"] == "medium"
        assert 'model_reasoning_effort = "medium"' in (home / ".codex/config.toml").read_text()
        for level in ("max", "ultra", "low"):
            page.locator(f"[role=radio][data-value={level}]").click()
            page.wait_for_function("level => document.querySelector('[role=radio][data-value=' + level + ']').getAttribute('aria-checked') === 'true'", arg=level)
            assert json.loads((home / ".nexus-hub/preferences.json").read_text())["default_effort"] == level
            if level in ("max", "ultra"):
                assert 'model_reasoning_effort = "xhigh"' in (home / ".codex/config.toml").read_text()
                assert json.loads((home / ".claude/settings.json").read_text())["env"]["CLAUDE_CODE_EFFORT_LEVEL"] == ("xhigh" if level == "ultra" else "max")
                assert json.loads((home / ".claude/settings.json").read_text())["ultracode"] is (level == "ultra")
        for level, fraction in (("low", 0), ("ultra", 1)):
            page.locator(f"[role=radio][data-value={level}]").click()
            page.wait_for_function("level => document.querySelector('[role=radio][data-value=' + level + ']').getAttribute('aria-checked') === 'true'", arg=level)
            geometry = page.evaluate("""() => {
                const group = document.querySelector('.effort-choices').getBoundingClientRect();
                const dot = document.querySelector('[aria-checked=true] .effort-dot').getBoundingClientRect();
                return {left: group.left, right: group.right, center: dot.x + dot.width / 2, height: dot.height};
            }""")
            assert abs(geometry["center"] - (geometry["left"] + 10 if fraction == 0 else geometry["right"] - 10)) < 1
            assert geometry["height"] == 20
        warning = page.get_by_role("switch", name="Large-file warnings", exact=True)
        warning.click()
        page.wait_for_function("document.querySelector('[data-setting=large_file_warning]').getAttribute('aria-checked') === 'false'")
        assert json.loads((home / ".nexus-hub/guardrails.json").read_text())["warn_large_files"] is False
        shell = shutil.which("powershell") if os.name == "nt" else shutil.which("bash")
        hook = REPO / "catalog/hooks" / ("large-file-guard.ps1" if os.name == "nt" else "large-file-guard.sh")
        hook_args = [shell, "-NoProfile", "-File", str(hook)] if os.name == "nt" else [shell, str(hook)]
        payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(project / "large.txt"), "content": "line\n" * 1001}})
        off = subprocess.run(hook_args, input=payload, env=env, capture_output=True, text=True, timeout=20, check=False)
        assert off.returncode == 0 and not off.stderr.strip()
        warning.click()
        page.wait_for_function("document.querySelector('[data-setting=large_file_warning]').getAttribute('aria-checked') === 'true'")
        on = subprocess.run(hook_args, input=payload, env=env, capture_output=True, text=True, timeout=20, check=False)
        assert on.returncode == 0 and "large-file-guard" in on.stderr
        observations["hook"] = {"off_exit": off.returncode, "off_output": off.stderr, "on_exit": on.returncode, "on_output": on.stderr}
        for theme in ("dark", "light"):
            if theme == "light":
                page.evaluate("document.body.classList.add('vscode-light')")
                page.add_style_tag(content=":root{--vscode-foreground:#222;--vscode-descriptionForeground:#555;--vscode-sideBar-background:#fff;--vscode-editor-background:#fff;--vscode-input-background:#fff;--vscode-input-foreground:#222;--vscode-textLink-foreground:#006b80;background:#fff}")
            for width in (320, 420, 900):
                page.set_viewport_size({"width": width, "height": 900})
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"Overflow at {width}"
                screenshot = work / f"panel-{theme}-{width}.png"
                page.screenshot(path=str(screenshot), full_page=True)
                observations["screenshots"].append(str(screenshot))
        assert not observations["console_errors"]
        browser.close()
    (work / "smoke-report.json").write_text(json.dumps(observations, indent=2), encoding="utf-8")
    print(json.dumps({"status": "pass", "actions": len(observations["actions"]), "screenshots": len(observations["screenshots"]), "report": str(work / "smoke-report.json")}))


if __name__ == "__main__":
    main()
