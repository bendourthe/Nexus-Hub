"""Tests for the ``nexus-hub org`` connection lifecycle."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from scripts import nexus_hub_cli as cli

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"
CLI_PY = SCRIPTS / "nexus_hub_cli.py"
LAUNCHER_CMD = SCRIPTS / "nexus-hub.cmd"
EXAMPLE_BUNDLE = REPO_ROOT / "configs" / "examples" / "org-bundle-example"

_RUN_KW = {
    "capture_output": True,
    "text": True,
    "encoding": "utf-8",
    "errors": "replace",
}


def _run_org(args: list[str], home: Path, monkeypatch, capsys):
    monkeypatch.setenv("NEXUS_HUB_HOME", str(home))
    return cli.cmd_org(args), capsys.readouterr()


def _copy_bundle(destination: Path) -> Path:
    shutil.copytree(EXAMPLE_BUNDLE, destination)
    return destination


def _git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        **_RUN_KW,
    )


@pytest.fixture
def bare_bundle_repo(tmp_path: Path) -> tuple[Path, str]:
    work = _copy_bundle(tmp_path / "bundle-work")
    _git("init", "--initial-branch", "main", cwd=work)
    _git("config", "user.name", "Nexus-Hub Tests", cwd=work)
    _git("config", "user.email", "tests@nexus-hub.invalid", cwd=work)
    _git("add", ".", cwd=work)
    _git("commit", "-m", "test: add organization bundle", cwd=work)

    bare = tmp_path / "bundle.git"
    _git("init", "--bare", str(bare))
    _git("remote", "add", "origin", str(bare), cwd=work)
    _git("push", "origin", "main", cwd=work)
    return bare, bare.as_uri()


@pytest.mark.parametrize(
    "value,expected",
    [
        ("https://example.invalid/org.git", True),
        ("ssh://git@example.invalid/org.git", True),
        ("file:///tmp/org.git", True),
        ("git@example.invalid:org/repo.git", True),
        ("./organization-bundle", False),
        (r"C:\\standards\\org", False),
    ],
)
def test_git_url_detection(value: str, expected: bool) -> None:
    assert cli._looks_like_git_url(value) is expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("main", "main"),
        ("feature/org-layer", "feature-org-layer"),
        ("../escape", "-escape"),
        (".hidden", "hidden"),
        ("", "branch"),
    ],
)
def test_branch_name_sanitization_matches_installer(raw: str, expected: str) -> None:
    assert cli.sanitize_branch_name(raw) == expected


def test_connect_directory_records_valid_connection(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    home = tmp_path / "home"
    bundle = _copy_bundle(tmp_path / "bundle")

    returncode, captured = _run_org(["connect", str(bundle)], home, monkeypatch, capsys)

    assert returncode == 0, captured.err
    assert "Connected organization bundle" in captured.out
    state = json.loads((home / "org" / "connection.json").read_text(encoding="utf-8"))
    assert state["schema_version"] == 1
    assert state["source_type"] == "dir"
    assert state["source"] == str(bundle.resolve())
    assert state["branch"] is None
    assert state["connected_at"]
    assert state["last_sync"] == state["connected_at"]


def test_connect_rejects_invalid_bundle_without_partial_state(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    home = tmp_path / "home"
    invalid = tmp_path / "invalid"
    invalid.mkdir()
    (invalid / "org.json").write_text("{}", encoding="utf-8")

    returncode, captured = _run_org(
        ["connect", str(invalid)], home, monkeypatch, capsys
    )

    assert returncode == 2
    assert "missing required key" in captured.err
    assert not (home / "org" / "connection.json").exists()


def test_connect_rejects_missing_and_null_byte_paths(
    tmp_path: Path, monkeypatch
) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("NEXUS_HUB_HOME", str(home))
    assert cli.cmd_org(["connect", str(tmp_path / "missing")]) == 2
    with pytest.raises(ValueError, match="Null byte"):
        cli._resolve_org_path("bad\x00path")
    assert not (home / "org" / "connection.json").exists()


def test_existing_connection_requires_force_noninteractively(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    home = tmp_path / "home"
    first = _copy_bundle(tmp_path / "first")
    second = _copy_bundle(tmp_path / "second")
    assert _run_org(["connect", str(first)], home, monkeypatch, capsys)[0] == 0

    returncode, captured = _run_org(["connect", str(second)], home, monkeypatch, capsys)

    assert returncode == 2
    assert "--force" in captured.err
    state = json.loads((home / "org" / "connection.json").read_text(encoding="utf-8"))
    assert state["source"] == str(first.resolve())


def test_force_replaces_existing_connection(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    home = tmp_path / "home"
    first = _copy_bundle(tmp_path / "first")
    second = _copy_bundle(tmp_path / "second")
    assert _run_org(["connect", str(first)], home, monkeypatch, capsys)[0] == 0

    returncode, captured = _run_org(
        ["connect", str(second), "--force"], home, monkeypatch, capsys
    )

    assert returncode == 0, captured.err
    state = json.loads((home / "org" / "connection.json").read_text(encoding="utf-8"))
    assert state["source"] == str(second.resolve())


def test_connection_write_is_atomic_and_concurrent_writes_remain_valid(
    tmp_path: Path, monkeypatch
) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("NEXUS_HUB_HOME", str(home))
    replacements: list[tuple[Path, Path]] = []
    real_replace = os.replace

    def recording_replace(source, destination):
        replacements.append((Path(source), Path(destination)))
        real_replace(source, destination)

    monkeypatch.setattr(cli.os, "replace", recording_replace)
    states = [
        {
            "schema_version": 1,
            "source_type": "dir",
            "source": str(tmp_path / name),
            "branch": None,
            "connected_at": name,
            "last_sync": name,
        }
        for name in ("one", "two")
    ]
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(cli._write_org_connection, states))

    stored = json.loads((home / "org" / "connection.json").read_text(encoding="utf-8"))
    assert stored in states
    assert replacements
    assert all(
        source.parent == destination.parent for source, destination in replacements
    )
    assert all(destination.name == "connection.json" for _, destination in replacements)


def test_status_reports_connection_and_validation_summary(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    home = tmp_path / "home"
    bundle = _copy_bundle(tmp_path / "bundle")
    assert _run_org(["connect", str(bundle)], home, monkeypatch, capsys)[0] == 0

    returncode, captured = _run_org(["status"], home, monkeypatch, capsys)

    assert returncode == 0, captured.err
    assert "Organization knowledge connection" in captured.out
    assert "Source type: dir" in captured.out
    assert str(bundle.resolve()) in captured.out
    assert "valid:" in captured.out
    assert "Platform posture (all registered platforms" in captured.out
    assert "copilot" in captured.out
    assert "personal-over-org documented inversion" in captured.out
    assert "instructions, not enforcement" in captured.out


def test_status_without_connection_is_actionable(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    returncode, captured = _run_org(["status"], tmp_path / "home", monkeypatch, capsys)
    assert returncode == 1
    assert "not connected" in captured.out.lower()
    assert "org connect" in captured.out
    assert "Platform posture (all registered platforms" in captured.out


def test_sync_directory_revalidates_and_updates_timestamp(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    home = tmp_path / "home"
    bundle = _copy_bundle(tmp_path / "bundle")
    assert _run_org(["connect", str(bundle)], home, monkeypatch, capsys)[0] == 0
    state_path = home / "org" / "connection.json"
    before = json.loads(state_path.read_text(encoding="utf-8"))
    before["last_sync"] = "2000-01-01T00:00:00Z"
    state_path.write_text(json.dumps(before), encoding="utf-8")

    returncode, captured = _run_org(["sync"], home, monkeypatch, capsys)

    assert returncode == 0, captured.err
    after = json.loads(state_path.read_text(encoding="utf-8"))
    assert after["last_sync"] != "2000-01-01T00:00:00Z"
    assert "Organization bundle synchronized" in captured.out


def test_connect_and_sync_git_source_with_local_bare_repo(
    tmp_path: Path, bare_bundle_repo: tuple[Path, str], monkeypatch, capsys
) -> None:
    _, uri = bare_bundle_repo
    home = tmp_path / "home"

    connected, captured = _run_org(
        ["connect", uri, "--branch", "main"], home, monkeypatch, capsys
    )

    assert connected == 0, captured.err
    state = json.loads((home / "org" / "connection.json").read_text(encoding="utf-8"))
    assert state["source_type"] == "git"
    assert state["source"] == uri
    assert state["branch"] == "main"
    assert (home / "org" / "repo" / ".git").is_dir()
    synced, captured = _run_org(["sync"], home, monkeypatch, capsys)
    assert synced == 0, captured.err
    assert "Organization bundle synchronized" in captured.out


def test_failed_git_clone_leaves_no_connection_or_cache(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    home = tmp_path / "home"
    missing = (tmp_path / "missing.git").as_uri()

    returncode, captured = _run_org(["connect", missing], home, monkeypatch, capsys)

    assert returncode == 2
    assert "git clone failed" in captured.err.lower()
    assert not (home / "org" / "connection.json").exists()
    assert not (home / "org" / "repo").exists()


def test_disconnect_requires_confirmation_and_yes_removes_state_and_cache(
    tmp_path: Path, bare_bundle_repo: tuple[Path, str], monkeypatch, capsys
) -> None:
    _, uri = bare_bundle_repo
    home = tmp_path / "home"
    assert (
        _run_org(["connect", uri, "--branch", "main"], home, monkeypatch, capsys)[0]
        == 0
    )

    refused, captured = _run_org(["disconnect"], home, monkeypatch, capsys)
    assert refused == 2
    assert "--yes" in captured.err
    assert (home / "org" / "connection.json").is_file()

    removed, captured = _run_org(["disconnect", "--yes"], home, monkeypatch, capsys)
    assert removed == 0, captured.err
    assert not (home / "org" / "connection.json").exists()
    assert not (home / "org" / "repo").exists()
    assert "next install or repair" in captured.out


def test_help_lists_org_command() -> None:
    proc = subprocess.run(
        [sys.executable, str(CLI_PY), "--help"], check=False, **_RUN_KW
    )
    assert proc.returncode == 0
    assert "org" in proc.stdout
    assert "connect" in proc.stdout


def test_org_git_commands_never_enable_a_shell() -> None:
    source = CLI_PY.read_text(encoding="utf-8")
    assert "shell=True" not in source


@pytest.mark.skipif(os.name != "nt", reason="Windows launcher proof")
def test_windows_launcher_reaches_org_subcommand(tmp_path: Path) -> None:
    home = tmp_path / "installed"
    scripts = home / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy2(CLI_PY, scripts / CLI_PY.name)
    shutil.copytree(SCRIPTS / "lib", scripts / "lib")
    env = dict(os.environ)
    env["NEXUS_HUB_HOME"] = str(home)
    proc = subprocess.run(
        ["cmd.exe", "/d", "/c", "call", str(LAUNCHER_CMD), "org", "status"],
        env=env,
        check=False,
        **_RUN_KW,
    )

    assert proc.returncode == 1, (proc.stdout, proc.stderr)
    assert "not connected" in proc.stdout.lower()
