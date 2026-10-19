"""Workspace-scope install output matches the global layout (AR-20).

v3.14.5 rewrote the GLOBAL install output: Claude renders one checklist instead
of a line per copy step, and platforms that deliver nothing on this machine are
collected into one "NOT DETECTED (skipped)" section rather than each printing an
inline note under its own provider header. The workspace path kept the old
output until v4.13.11. These tests run a real workspace install in both shells
for Claude, Kimi, and Gemini CLI without the enterprise flag. Every registry
platform delivers surfaces at workspace scope in a clean home (probed
2026-10-10), so the skipped Gemini CLI is the deterministic absent platform;
Kimi shows that a delivering platform still prints its provider header, now
lazily, exactly as in the global install.

Every run is fully isolated: HOME, USERPROFILE, APPDATA, LOCALAPPDATA,
NEXUS_HUB_HOME, the Git global config, and the temporary directory all point
into fresh temporary directories, and the install target is a throwaway
workspace, so nothing reaches the real user's home or AI-tool configuration.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from scripts.ci.verify_scenarios import isolated_environment

_ROOT = Path(__file__).resolve().parents[2]
_SH = _ROOT / "scripts" / "installer.sh"
_PS1 = _ROOT / "scripts" / "installer.ps1"
_CAPTURE = {"capture_output": True, "text": True, "encoding": "utf-8", "errors": "replace"}
_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def _windows_powershell() -> str | None:
    if sys.platform != "win32":
        return None
    return shutil.which("powershell")


@pytest.fixture
def short_root():
    """Short-path scratch root; a full skill tree under pytest's deep tmp_path
    can pass the Windows 260-character limit for reasons unrelated to output."""
    path = Path(tempfile.mkdtemp(prefix="nxw"))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _isolated(root: Path) -> tuple[dict[str, str], Path]:
    boundary = root / "fixture-env"
    boundary.mkdir()
    isolated = isolated_environment(boundary)
    dirs = {name: root / name for name in ("h", "a", "l", "t", "ws")}
    for d in dirs.values():
        d.mkdir()
    env = {
        **isolated,
        "HOME": str(dirs["h"]),
        "USERPROFILE": str(dirs["h"]),
        "CLAUDE_CONFIG_DIR": str(dirs["h"] / ".claude"),
        "APPDATA": str(dirs["a"]),
        "LOCALAPPDATA": str(dirs["l"]),
        "NEXUS_HUB_HOME": str(dirs["h"] / ".nexus-hub"),
        "GIT_CONFIG_GLOBAL": str(dirs["h"] / ".gitconfig"),
        "TEMP": str(dirs["t"]),
        "TMP": str(dirs["t"]),
        "TMPDIR": dirs["t"].as_posix(),
    }
    return env, dirs["ws"]


def _header(provider: str) -> re.Pattern[str]:
    return re.compile(rf"^[ \t]*\S {provider}[ \t]*\r?$", re.MULTILINE)


def _section(output: str) -> str:
    """The SKILLS & COMMANDS section only, where the platform blocks render."""
    start = output.find("SKILLS & COMMANDS")
    end = output.find("AUTO-APPROVE PERMISSIONS", start)
    assert start != -1 and end != -1, f"install sections missing:\n{output[-3000:]}"
    return output[start:end]


def _assert_global_layout(section: str, enterprise_flag: str) -> None:
    assert "> NOT DETECTED (skipped)" in section, f"no grouped NOT DETECTED section:\n{section}"
    assert f"- Gemini CLI (enterprise-only; re-run with {enterprise_flag})" in section, section
    # The skipped platform no longer prints an inline note under an eager header:
    # with only Gemini CLI selected from Google, no GOOGLE header renders at all.
    assert "Gemini CLI: skipped" not in section, f"inline skip note remains:\n{section}"
    # Provider headers are "> NAME" in Bash and an arrow glyph in PowerShell (which
    # may decode as a replacement character), so match any one marker character.
    assert not _header("GOOGLE").search(section), f"an eager GOOGLE header remains:\n{section}"
    # A delivering platform keeps exactly one provider header followed by its block.
    assert len(_header("KIMI").findall(section)) == 1, section
    assert re.search(r"KIMI[ \t]*\r?\n\s*Kimi Code CLI \(\.kimi-code/\)", section), section
    # Claude renders the checklist, not the bespoke per-step lines.
    assert "Skills catalog installed" not in section, f"bespoke Claude lines remain:\n{section}"
    assert re.search(r"\] Skills: +\S*\.claude[\\/]skills", section), f"no Claude checklist row:\n{section}"
    assert re.search(r"\] Core Files: +\S*CLAUDE\.md", section), section


@pytest.mark.slow
@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_bash_workspace_install_groups_undetected_platforms(short_root: Path) -> None:
    env, workspace = _isolated(short_root)
    proc = subprocess.run(
        [shutil.which("bash"), str(_SH), "--workspace", workspace.as_posix(),
         "--platforms", "claude,kimi,gemini-cli", "--modules", "ai-engineering", "--yes"],
        cwd=str(_ROOT), env=env, timeout=900, **_CAPTURE,
    )
    assert proc.returncode == 0, f"rc={proc.returncode}\n{(proc.stderr or '')[-3000:]}"
    _assert_global_layout(_section(_ANSI.sub("", proc.stdout or "")), "--enterprise")


@pytest.mark.slow
@pytest.mark.skipif(_windows_powershell() is None, reason="Windows PowerShell 5.1 not available")
def test_powershell_workspace_install_groups_undetected_platforms(short_root: Path) -> None:
    env, workspace = _isolated(short_root)
    proc = subprocess.run(
        [_windows_powershell(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(_PS1),
         "-Workspace", str(workspace), "-Platforms", "claude,kimi,gemini-cli",
         "-Modules", "ai-engineering", "-Yes"],
        cwd=str(_ROOT), env=env, timeout=900, **_CAPTURE,
    )
    assert proc.returncode == 0, f"rc={proc.returncode}\n{(proc.stderr or '')[-3000:]}"
    _assert_global_layout(_section(proc.stdout or ""), "-Enterprise")
