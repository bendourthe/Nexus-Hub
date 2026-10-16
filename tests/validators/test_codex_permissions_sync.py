"""Tests for the Codex mode of the shared permission helper (merge_permissions.py --codex).

Two shipped defects shaped this mode, and each has a guard here:

* **Windows refusal.** The profile restricts reads to chosen roots. Codex's native
  Windows ``unelevated`` sandbox (also its fallback when ``elevated`` setup is
  unavailable) cannot enforce split read restrictions and refuses to start a thread.
  A Windows host must therefore end up with NO Nexus-managed profile, while a profile
  the user authored is left alone.
* **Stale profiles.** The installers treated "the block exists" as "the block is
  current", so a fixed template (":project_roots" -> ":minimal" + ":workspace_roots")
  never reached an existing machine. Every run must now converge to the template.

Results are parsed with stdlib ``tomllib`` so the check never relies on the library
that wrote the file.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

pytest.importorskip("tomlkit")

REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER = REPO_ROOT / "scripts" / "merge_permissions.py"
TEMPLATE = REPO_ROOT / "configs" / "permissions" / "codex-permissions.toml"


def _load():
    spec = importlib.util.spec_from_file_location("merge_permissions", HELPER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mp = _load()

PREAMBLE = mp._codex_preamble(TEMPLATE.read_text(encoding="utf-8"))

# The shape of a real ~/.codex/config.toml created from an older template and then
# edited by Codex itself: stale ":project_roots", Codex-owned tables around the profile.
LEGACY = PREAMBLE + """
approval_policy = "on-request"
default_permissions = "default"
model = "some-model"
sandbox_mode = "workspace-write"

[windows]
sandbox = "unelevated"

[permissions.default.filesystem]
# Grant read access to project directories; write remains blocked by default.
":project_roots" = "read"
"/home/me/extra" = "write"

[permissions.default.network]
enabled = true
mode = "limited"
allowed_domains = [
  "github.com",
  "my.internal.example",
]

[projects.'/home/me/repo']
trust_level = "trusted"
"""

# What the pre-v4.14 installers produced when they appended to an existing config.
APPENDED = """model = "some-model"

[projects.'/home/me/repo']
trust_level = "trusted"


# --- Nexus-Hub auto-approve permissions ---
default_permissions = "default"

[permissions.default.filesystem]
":project_roots" = "read"

[permissions.default.network]
enabled = true
allowed_domains = ["github.com"]
"""


def _sync(path: Path, windows: bool) -> tuple[list[str], list[str]]:
    return mp.codex_sync(TEMPLATE, path, windows, backup=False)


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "config.toml"
    path.write_bytes(text.encode("utf-8"))
    return path


def test_windows_removes_the_managed_profile_and_keeps_everything_else(tmp_path: Path) -> None:
    path = _write(tmp_path, LEGACY)

    changed, removed = _sync(path, windows=True)

    doc = tomllib.loads(path.read_text(encoding="utf-8"))
    assert removed == ["[permissions.default]", "default_permissions"]
    assert changed == []
    assert "permissions" not in doc and "default_permissions" not in doc
    assert doc["sandbox_mode"] == "workspace-write"
    assert doc["windows"] == {"sandbox": "unelevated"}
    assert doc["projects"]["/home/me/repo"] == {"trust_level": "trusted"}
    assert not path.read_text(encoding="utf-8").startswith(PREAMBLE)


def test_windows_cleans_an_appended_block_including_its_misplaced_selector(tmp_path: Path) -> None:
    # The old installers appended `default_permissions` after the last table, so TOML
    # bound it to `[projects.'/home/me/repo']` instead of the root.
    assert "default_permissions" in tomllib.loads(APPENDED)["projects"]["/home/me/repo"]
    path = _write(tmp_path, APPENDED)

    _, removed = _sync(path, windows=True)

    text = path.read_text(encoding="utf-8")
    assert mp._CODEX_MARKER not in text
    assert "default_permissions (misplaced under a table)" in removed
    assert tomllib.loads(text) == {
        "model": "some-model", "approval_policy": "on-request",
        "projects": {"/home/me/repo": {"trust_level": "trusted"}},
    }


def test_posix_moves_a_misplaced_selector_to_the_root(tmp_path: Path) -> None:
    path = _write(tmp_path, APPENDED)

    _sync(path, windows=False)

    doc = tomllib.loads(path.read_text(encoding="utf-8"))
    assert doc["default_permissions"] == "default"
    assert doc["projects"]["/home/me/repo"] == {"trust_level": "trusted"}
    assert _sync(path, windows=False) == ([], [])


def test_windows_second_run_writes_nothing(tmp_path: Path) -> None:
    path = _write(tmp_path, LEGACY)
    _sync(path, windows=True)
    before = path.read_bytes()

    assert mp.codex_sync(TEMPLATE, path, True, backup=True) == ([], [])
    assert path.read_bytes() == before
    assert not list(tmp_path.glob("config.toml.bak.*"))


def test_windows_keeps_a_user_authored_profile(tmp_path: Path) -> None:
    own = 'default_permissions = "default"\n\n[permissions.default.filesystem]\n":root" = "read"\n'
    path = _write(tmp_path, own)

    assert _sync(path, windows=True) == (["approval_policy"], [])
    assert tomllib.loads(path.read_text(encoding="utf-8"))["permissions"]["default"]


def test_windows_fresh_install_writes_no_profile(tmp_path: Path) -> None:
    path = tmp_path / ".codex" / "config.toml"

    _sync(path, windows=True)

    assert tomllib.loads(path.read_text(encoding="utf-8")) == {"approval_policy": "on-request"}


def test_line_endings_are_preserved(tmp_path: Path) -> None:
    path = _write(tmp_path, LEGACY)

    _sync(path, windows=True)

    assert b"\r\n" not in path.read_bytes()


def test_posix_refreshes_a_stale_profile_and_keeps_user_additions(tmp_path: Path) -> None:
    path = _write(tmp_path, LEGACY)

    changed, removed = _sync(path, windows=False)

    profile = tomllib.loads(path.read_text(encoding="utf-8"))["permissions"]["default"]
    assert removed == ["permissions.default.filesystem.:project_roots"]
    assert profile["filesystem"] == {
        "/home/me/extra": "write", ":minimal": "read", ":workspace_roots": "read",
    }
    assert "my.internal.example" in profile["network"]["allowed_domains"]
    assert "pypi.org" in profile["network"]["allowed_domains"]
    assert "permissions.default.filesystem.:minimal" in changed
    assert _sync(path, windows=False) == ([], [])


def test_posix_adds_the_profile_with_a_root_level_selector(tmp_path: Path) -> None:
    path = _write(tmp_path, 'model = "m"\n\n[projects.\'/r\']\ntrust_level = "trusted"\n')

    _sync(path, windows=False)

    doc = tomllib.loads(path.read_text(encoding="utf-8"))
    assert doc["default_permissions"] == "default"
    assert doc["permissions"]["default"]["filesystem"][":workspace_roots"] == "read"
    assert doc["projects"]["/r"] == {"trust_level": "trusted"}


def test_posix_inserts_a_missing_selector_for_a_managed_profile(tmp_path: Path) -> None:
    path = _write(tmp_path, APPENDED.replace('default_permissions = "default"\n', ""))

    changed, _ = _sync(path, windows=False)

    assert "default_permissions" in changed
    assert tomllib.loads(path.read_text(encoding="utf-8"))["default_permissions"] == "default"


def test_posix_fresh_install_copies_the_template(tmp_path: Path) -> None:
    path = tmp_path / ".codex" / "config.toml"

    _sync(path, windows=False)

    assert path.read_text(encoding="utf-8") == TEMPLATE.read_text(encoding="utf-8")


def test_missing_tomlkit_degrades_with_an_install_hint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _write(tmp_path, LEGACY)
    monkeypatch.setitem(sys.modules, "tomlkit", None)

    with pytest.raises(ValueError, match="pip install tomlkit"):
        _sync(path, windows=True)
    assert path.read_text(encoding="utf-8") == LEGACY


def test_cli_reports_removals_on_stdout(tmp_path: Path) -> None:
    path = _write(tmp_path, LEGACY)

    result = subprocess.run(
        [sys.executable, str(HELPER), "--codex", "--codex-os", "windows", "--no-backup",
         "--template", str(TEMPLATE), "--settings", str(path)],
        capture_output=True, text=True, check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["removed: [permissions.default]", "removed: default_permissions"]


@pytest.mark.parametrize("writer", [
    "scripts/installer.sh", "scripts/installer.ps1", "scripts/Install-Nexus-Hub-Permissions.ps1",
])
def test_every_codex_writer_delegates_to_the_helper(writer: str) -> None:
    text = (REPO_ROOT / writer).read_text(encoding="utf-8")

    assert "--codex" in text or "-Codex" in text
    # The string-append path, whose presence check never refreshed a stale profile.
    assert "permissions.default.network" not in text
    assert "Nexus-Hub auto-approve permissions ---" not in text
