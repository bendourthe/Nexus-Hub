"""Cross-platform behavior tests for old-version-docs-guard.{sh,ps1}."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest


HOOKS = Path(__file__).resolve().parent.parent
HOOK_SH = HOOKS / "old-version-docs-guard.sh"
HOOK_PS1 = HOOKS / "old-version-docs-guard.ps1"


@pytest.fixture(params=["sh", "ps1"])
def run(request):
    """Run either sibling so every assertion also proves exit-code parity."""
    implementation = request.param
    if implementation == "sh":
        if shutil.which("jq") is None:
            pytest.skip("jq is required by the Bash hook")
        prefix = [request.getfixturevalue("bash_bin"), str(HOOK_SH)]
    else:
        prefix = [request.getfixturevalue("powershell_bin"), "-NoProfile", "-File", str(HOOK_PS1)]

    def _run(
        path: str,
        cwd: Path,
        *,
        path_key: str = "file_path",
        env_extra: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        payload = {"tool_name": "Write", "tool_input": {path_key: path, "content": "irrelevant"}}
        env = {**os.environ}
        for key in ("NEXUS_HOOK_PROFILE", "NEXUS_DISABLED_HOOKS", "NEXUS_OLD_DOCS_GUARD"):
            env.pop(key, None)
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            prefix,
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            cwd=cwd,
            env=env,
            timeout=120,
        )

    return _run


def _version_dir(root: Path, layout: str, version: str) -> Path:
    major = version.split(".", 1)[0]
    if layout == "releases":
        return root / f"docs/releases/v{major}/v{version}"
    if layout == "v-bucket":
        return root / f"docs/v{major}/v{version}"
    if layout == "flat":
        return root / f"docs/v{version}"
    if layout == "versions":
        return root / f"docs/versions/v{major}/v{version}"
    raise AssertionError(f"unknown layout: {layout}")


def _path(layout: str, version: str) -> str:
    return _version_dir(Path(), layout, version).as_posix() + "/plans/plan.md"


@pytest.mark.parametrize(
    "layout, old_version, active_version",
    [
        ("releases", "0.8", "1.0"),
        ("v-bucket", "0.8", "1.0"),
        ("flat", "0.8.1", "1.0.0"),
        ("versions", "0.8.1", "1.0.0"),
    ],
)
def test_warns_for_historical_path_in_every_layout(run, tmp_path: Path, layout: str, old_version: str, active_version: str) -> None:
    _version_dir(tmp_path, layout, old_version).mkdir(parents=True)
    _version_dir(tmp_path, layout, active_version).mkdir(parents=True)

    result = run(_path(layout, old_version), tmp_path)

    assert result.returncode == 0
    assert "old-version-docs-guard" in result.stderr
    assert f"v{old_version}" in result.stderr
    assert f"active is v{active_version}" in result.stderr
    assert "/update refactor" in result.stderr


@pytest.mark.parametrize(
    "layout, active_version",
    [("releases", "1.0"), ("v-bucket", "1.0"), ("flat", "1.0.0"), ("versions", "1.0.0")],
)
def test_stays_silent_for_active_version_in_every_layout(run, tmp_path: Path, layout: str, active_version: str) -> None:
    _version_dir(tmp_path, layout, active_version).mkdir(parents=True)

    result = run(_path(layout, active_version), tmp_path)

    assert result.returncode == 0
    assert result.stderr == ""


@pytest.mark.parametrize(
    "path",
    [
        "docs/archives/v0/v0.8/history.md",
        "docs/archive/v0/v0.8/history.md",  # Legacy detection fixture.
        "docs/archive/v0.8.1/history.md",  # Legacy detection fixture.
        "docs/archive/versions/v0/v0.8.1/history.md",  # Legacy detection fixture.
    ],
)
def test_archive_equivalents_are_guarded(run, tmp_path: Path, path: str) -> None:
    _version_dir(tmp_path, "releases", "1.0").mkdir(parents=True)

    result = run(path, tmp_path)

    assert result.returncode == 0
    assert "old-version-docs-guard" in result.stderr


def test_block_mode_returns_one(run, tmp_path: Path) -> None:
    _version_dir(tmp_path, "releases", "0.8").mkdir(parents=True)
    _version_dir(tmp_path, "releases", "1.0").mkdir(parents=True)

    result = run(_path("releases", "0.8"), tmp_path, env_extra={"NEXUS_OLD_DOCS_GUARD": "block"})

    assert result.returncode == 1
    assert "Blocked by NEXUS_OLD_DOCS_GUARD=block" in result.stderr


@pytest.mark.parametrize("path", ["src/main.py", "docs/DEVLOG.md"])
def test_non_versioned_paths_are_silent(run, tmp_path: Path, path: str) -> None:
    _version_dir(tmp_path, "releases", "1.0").mkdir(parents=True)

    result = run(path, tmp_path)

    assert result.returncode == 0
    assert result.stderr == ""


def test_no_active_version_is_silent(run, tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()

    result = run(_path("releases", "0.8"), tmp_path)

    assert result.returncode == 0
    assert result.stderr == ""


def test_disabled_hook_is_silent(run, tmp_path: Path) -> None:
    _version_dir(tmp_path, "releases", "0.8").mkdir(parents=True)
    _version_dir(tmp_path, "releases", "1.0").mkdir(parents=True)

    result = run(
        _path("releases", "0.8"),
        tmp_path,
        env_extra={"NEXUS_DISABLED_HOOKS": "old-version-docs-guard"},
    )

    assert result.returncode == 0
    assert result.stderr == ""


def test_minimal_profile_is_silent(run, tmp_path: Path) -> None:
    _version_dir(tmp_path, "releases", "0.8").mkdir(parents=True)
    _version_dir(tmp_path, "releases", "1.0").mkdir(parents=True)

    result = run(_path("releases", "0.8"), tmp_path, env_extra={"NEXUS_HOOK_PROFILE": "minimal"})

    assert result.returncode == 0
    assert result.stderr == ""


def test_path_alias_is_honored(run, tmp_path: Path) -> None:
    _version_dir(tmp_path, "releases", "0.8").mkdir(parents=True)
    _version_dir(tmp_path, "releases", "1.0").mkdir(parents=True)

    result = run(_path("releases", "0.8"), tmp_path, path_key="path")

    assert result.returncode == 0
    assert "old-version-docs-guard" in result.stderr


def test_windows_separators_are_normalized(run, tmp_path: Path) -> None:
    _version_dir(tmp_path, "releases", "0.8").mkdir(parents=True)
    _version_dir(tmp_path, "releases", "1.0").mkdir(parents=True)

    result = run(_path("releases", "0.8").replace("/", "\\"), tmp_path)

    assert result.returncode == 0
    assert "old-version-docs-guard" in result.stderr
