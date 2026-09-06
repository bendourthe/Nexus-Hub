"""Tests for the `nexus-hub` CLI + the upgrade checker (v3.7.0 Phase 3).

The installer drops a small `nexus-hub` launcher on PATH (a POSIX shim
`~/.nexus-hub/bin/nexus-hub` and a Windows `nexus-hub.cmd`) over the stdlib-only
CLI core `scripts/nexus_hub_cli.py`. The CLI implements:

  * `nexus-hub --version`  - print the installer-written `~/.nexus-hub/VERSION`;
  * `nexus-hub upgrade`    - compare installed vs the latest on the project's own
                             GitHub, show a what's-new summary, and on confirmation
                             re-run the install bootstrap to upgrade in place.

These tests cover:
  * the CLI/launcher artifacts exist and both installers wire them up (VERSION
    marker, `bin/` launcher, CLI copy, PATH hint);
  * version reading (VERSION file, BOM tolerance, plugin.json fallback, unknown);
  * semver comparison and CHANGELOG what's-new extraction;
  * the fetch helper against a local `file://` source and its offline failure;
  * the upgrade subcommand end-to-end (up-to-date, behind + skip, behind +
    confirmed dry-run, offline) driven by env seams against a `file://` fixture;
  * the only-the-project's-own-GitHub outbound invariant.

Everything runs on the Python interpreter directly (no bash), so the Windows
bash-resolution problem that used to be tracked as WN-v36-1 never applied to this
suite. (That item's framing, "bash cannot be fully run on the Windows dev host",
was DISPROVEN in v3.15.6 Phase 4: the cause was PATH shadowing by the WSL launcher
stub, not host incapability.)
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"
CLI_PY = SCRIPTS / "nexus_hub_cli.py"
LAUNCHER_POSIX = SCRIPTS / "nexus-hub"
LAUNCHER_CMD = SCRIPTS / "nexus-hub.cmd"
INSTALL_SH = SCRIPTS / "installer.sh"
INSTALL_PS1 = SCRIPTS / "installer.ps1"

_RUN_KW = dict(capture_output=True, text=True, encoding="utf-8", errors="replace")


def _load_cli():
    """Import the CLI core module fresh (it reads env at call time, not import)."""
    spec = importlib.util.spec_from_file_location("nexus_hub_cli", CLI_PY)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cli = _load_cli()


def _write_remote_fixture(directory: Path, version: str, changelog: str) -> str:
    """Lay out a fake remote tree (plugin.json + CHANGELOG.md) and return its URI."""
    (directory / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (directory / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "nexus-hub", "version": version}), encoding="utf-8"
    )
    (directory / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
    return directory.as_uri()


_SAMPLE_CHANGELOG = """# Changelog

## [Unreleased]

### Added

- nothing yet

## [3.7.0] - 2026-06-17

### Added

- The `nexus-hub upgrade` checker landed here.

## [3.6.0] - 2026-06-17

### Added

- Older stuff.
"""


def _run_cli(args: list[str], env_extra: dict[str, str], stdin: str | None = None):
    """Run the CLI as a subprocess with the given extra env (and a clean base)."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("NEXUS_HUB_")}
    env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(CLI_PY), *args],
        env=env,
        input=stdin,
        **_RUN_KW,
    )


# --- Artifacts exist --------------------------------------------------------


def test_cli_and_launchers_exist() -> None:
    assert CLI_PY.is_file(), "the nexus-hub CLI core must exist"
    assert LAUNCHER_POSIX.is_file(), "the POSIX nexus-hub launcher must exist"
    assert LAUNCHER_CMD.is_file(), "the Windows nexus-hub.cmd launcher must exist"


def test_posix_launcher_is_thin_shim() -> None:
    body = LAUNCHER_POSIX.read_text(encoding="utf-8")
    assert "nexus_hub_cli.py" in body, "launcher must hand off to the CLI core"
    assert "NEXUS_HUB_HOME" in body, "launcher must honor the home override"
    assert "exec" in body, "launcher should exec the interpreter"


def test_cmd_launcher_is_thin_shim() -> None:
    body = LAUNCHER_CMD.read_text(encoding="utf-8")
    assert "nexus_hub_cli.py" in body, "launcher must hand off to the CLI core"
    assert "NEXUS_HUB_HOME" in body, "launcher must honor the home override"


# --- Version reading --------------------------------------------------------


def test_read_version_from_version_file(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "VERSION").write_text("3.6.0\n", encoding="utf-8")
    monkeypatch.setenv("NEXUS_HUB_HOME", str(tmp_path))
    assert cli.read_installed_version() == "3.6.0"


def test_read_version_tolerates_bom(tmp_path: Path, monkeypatch) -> None:
    # A PowerShell-written file can carry a UTF-8 BOM; it must be stripped.
    (tmp_path / "VERSION").write_text("3.6.0", encoding="utf-8-sig")
    monkeypatch.setenv("NEXUS_HUB_HOME", str(tmp_path))
    assert cli.read_installed_version() == "3.6.0"


def test_read_version_falls_back_to_plugin_json(tmp_path: Path, monkeypatch) -> None:
    plugin = tmp_path / "src" / ".claude-plugin"
    plugin.mkdir(parents=True)
    (plugin / "plugin.json").write_text(
        json.dumps({"version": "3.5.0"}), encoding="utf-8"
    )
    monkeypatch.setenv("NEXUS_HUB_HOME", str(tmp_path))
    assert cli.read_installed_version() == "3.5.0"


def test_read_version_unknown(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("NEXUS_HUB_HOME", str(tmp_path))
    assert cli.read_installed_version() is None


# --- Semver -----------------------------------------------------------------


@pytest.mark.parametrize(
    "installed,latest,expected",
    [
        ("3.6.0", "3.7.0", -1),
        ("3.7.0", "3.7.0", 0),
        ("3.8.0", "3.7.0", 1),
        ("3.7.0", "3.10.0", -1),  # numeric, not lexical, comparison
        ("garbage", "3.7.0", -1),  # unparseable installed sorts as oldest
    ],
)
def test_compare_semver(installed: str, latest: str, expected: int) -> None:
    assert cli.compare_semver(installed, latest) == expected


# --- CHANGELOG extraction ---------------------------------------------------


def test_changelog_section_exact_heading() -> None:
    section = cli.extract_changelog_section(_SAMPLE_CHANGELOG, "3.7.0")
    assert "nexus-hub upgrade" in section
    assert "Older stuff" not in section, "must stop at the next version heading"
    assert "nothing yet" not in section, "must not bleed into Unreleased"


def test_changelog_section_falls_back_and_skips_unreleased() -> None:
    section = cli.extract_changelog_section(_SAMPLE_CHANGELOG, "9.9.9")
    # 9.9.9 has no heading -> first versioned section (3.7.0), skipping Unreleased.
    assert "nexus-hub upgrade" in section
    assert "nothing yet" not in section


# --- fetch_text -------------------------------------------------------------


def test_fetch_text_reads_file_uri(tmp_path: Path) -> None:
    target = tmp_path / "hello.txt"
    target.write_text("payload", encoding="utf-8")
    assert cli.fetch_text(target.as_uri()) == "payload"


def test_fetch_text_offline_raises(tmp_path: Path) -> None:
    missing = (tmp_path / "nope.txt").as_uri()
    with pytest.raises(cli.FetchError):
        cli.fetch_text(missing)


# --- upgrade subcommand (end-to-end via env seams) --------------------------


def test_version_subcommand(tmp_path: Path) -> None:
    (tmp_path / "VERSION").write_text("3.6.0\n", encoding="utf-8")
    proc = _run_cli(["--version"], {"NEXUS_HUB_HOME": str(tmp_path)})
    assert proc.returncode == 0, proc.stderr
    assert "3.6.0" in proc.stdout


def test_upgrade_up_to_date(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    (home / "VERSION").write_text("3.7.0\n", encoding="utf-8")
    raw = _write_remote_fixture(tmp_path / "remote", "3.7.0", _SAMPLE_CHANGELOG)
    proc = _run_cli(
        ["upgrade"],
        {"NEXUS_HUB_HOME": str(home), "NEXUS_HUB_RAW_BASE": raw},
    )
    assert proc.returncode == 0, proc.stderr
    assert "already on the latest" in proc.stdout.lower()


def test_upgrade_behind_shows_whats_new_and_skips(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    (home / "VERSION").write_text("3.6.0\n", encoding="utf-8")
    raw = _write_remote_fixture(tmp_path / "remote", "3.7.0", _SAMPLE_CHANGELOG)
    # No --yes and stdin is not a TTY -> safe default is to NOT upgrade.
    proc = _run_cli(
        ["upgrade"],
        {"NEXUS_HUB_HOME": str(home), "NEXUS_HUB_RAW_BASE": raw},
        stdin="",
    )
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert "newer version is available" in out.lower()
    assert "3.7.0" in out
    assert "nexus-hub upgrade" in out, "must print the what's-new CHANGELOG block"
    assert "skipped" in out.lower()


def test_upgrade_behind_confirmed_dry_run(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    (home / "VERSION").write_text("3.6.0\n", encoding="utf-8")
    raw = _write_remote_fixture(tmp_path / "remote", "3.7.0", _SAMPLE_CHANGELOG)
    proc = _run_cli(
        ["upgrade", "--yes"],
        {
            "NEXUS_HUB_HOME": str(home),
            "NEXUS_HUB_RAW_BASE": raw,
            "NEXUS_HUB_INSTALL_BASE": "https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main",
            "NEXUS_HUB_UPGRADE_DRY_RUN": "1",
        },
    )
    assert proc.returncode == 0, proc.stderr
    assert "dry-run" in proc.stdout.lower()
    # The re-run targets the project's own GitHub bootstrap.
    assert "install.sh" in proc.stdout or "install.ps1" in proc.stdout


def test_upgrade_offline_fails_clearly(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    (home / "VERSION").write_text("3.6.0\n", encoding="utf-8")
    # Point the raw base at a directory with no plugin.json -> fetch fails.
    empty = tmp_path / "empty"
    empty.mkdir()
    proc = _run_cli(
        ["upgrade"],
        {"NEXUS_HUB_HOME": str(home), "NEXUS_HUB_RAW_BASE": empty.as_uri()},
    )
    assert proc.returncode == 2, (proc.stdout, proc.stderr)
    assert "could not reach" in proc.stderr.lower()


# --- Outbound-host invariant ------------------------------------------------


def test_cli_no_outbound_beyond_github() -> None:
    """The CLI may only ever name the project's own GitHub as an outbound host."""
    for line in CLI_PY.read_text(encoding="utf-8").splitlines():
        if "https://" not in line:
            continue
        lowered = line.lower()
        if "github.com" in lowered or "githubusercontent.com" in lowered:
            continue
        pytest.fail(f"unexpected outbound URL in nexus_hub_cli.py: {line.strip()}")


# --- Installer wiring (static surface) --------------------------------------


def test_installer_sh_wires_cli_launcher() -> None:
    body = INSTALL_SH.read_text(encoding="utf-8")
    assert "install_cli_launcher" in body, "installer.sh must define + call the launcher install"
    assert 'nexus_hub_cli.py' in body, "installer.sh must copy the CLI core"
    assert 'scripts/nexus-hub' in body, "installer.sh must copy the POSIX launcher"
    assert 'bin' in body and "VERSION" in body, "installer.sh must create bin/ and write VERSION"


def test_installer_ps1_wires_cli_launcher() -> None:
    body = INSTALL_PS1.read_text(encoding="utf-8")
    assert "Install-CliLauncher" in body, "installer.ps1 must define + call the launcher install"
    assert "nexus_hub_cli.py" in body, "installer.ps1 must copy the CLI core"
    assert "nexus-hub.cmd" in body, "installer.ps1 must copy the Windows launcher"
    assert "VERSION" in body, "installer.ps1 must write the VERSION marker"
