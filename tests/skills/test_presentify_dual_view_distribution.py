"""Run actual installers into scratch workspaces and use their shipped runtime."""

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "runtime_fixture", Path(__file__).with_name("test_presentify_dual_view_runtime.py")
)
runtime_fixture = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime_fixture)


@pytest.mark.slow
@pytest.mark.parametrize("shell", ["bash", "powershell"])
def test_installed_bundle_runs_offline(tmp_path, shell):
    target = tmp_path / shell
    target.mkdir()
    if shell == "powershell":
        if os.name != "nt":
            pytest.skip("PowerShell installer is qualified on Windows only")
        binary = shutil.which("powershell")
        assert binary, "Required Windows PowerShell installer is unavailable"
        command = [
            binary,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "scripts/installer.ps1"),
            "-Workspace",
            str(target),
            "-Platforms",
            "claude",
            "-Modules",
            "specialized-domains",
            "-Yes",
        ]
    else:
        git_bash = Path("C:/Program Files/Git/bin/bash.exe")
        binary = (
            str(git_bash)
            if os.name == "nt" and git_bash.exists()
            else shutil.which("bash")
        )
        assert binary, "Required Bash installer is unavailable"
        command = [
            binary,
            (ROOT / "scripts/installer.sh").as_posix(),
            "--workspace",
            target.as_posix(),
            "--platforms",
            "claude",
            "--modules",
            "specialized-domains",
            "--yes",
        ]
    result = subprocess.run(
        command,
        check=False,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=900,
    )
    assert result.returncode == 0, result.stderr[-3000:] + result.stdout[-1000:]
    bundle = target / ".claude/skills/document-to-interactive-html"
    for relative in (
        "assets/dual-view-runtime.js",
        "assets/dual-view.css",
        "assets/dual-view-figures.js",
        "scripts/dual_view.py",
        "scripts/build_presentation.py",
        "references/dual-view-handbooks.md",
    ):
        assert (bundle / relative).read_bytes() == (
            runtime_fixture.BUNDLE / relative
        ).read_bytes()
    artifact = target / "installed.html"
    for source in (ROOT / "tests/fixtures/interactive-handbooks").iterdir():
        if source.is_file():
            shutil.copy2(source, target / source.name)
    build = [
        sys.executable,
        str(bundle / "scripts/build_presentation.py"),
        str(target / "model.json"),
        "-o",
        str(artifact),
    ]
    subprocess.run(build, check=True, capture_output=True, timeout=60)
    subprocess.run([*build, "--check"], check=True, capture_output=True, timeout=60)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(artifact.as_uri())
        page.locator("[data-dv-open]").first.click()
        assert page.locator("[data-dv-count]").inner_text() == "1 / 6"
        page.locator("[data-dv-next]").click()
        assert page.locator("[data-dv-count]").inner_text() == "2 / 6"
        page.locator("[data-dv-exit]").click()
        assert not page.locator("[data-dv-deck]").is_visible()
        assert not errors
        browser.close()
