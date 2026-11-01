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

## [3.8.0] - 2026-06-20

### Added

- **A guard with a bold lead.** A long explanation that the summary must not print, because the lead says enough.
    - Activation: set the flag in the settings file.
    - Validation: run the check command.
- A plain bullet with no bold lead. Its second sentence is dropped from the summary.

### Fixed

- **Upgrade notes are readable.** The `nexus-hub upgrade` output is now short and structured.

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


# --- CHANGELOG summary ------------------------------------------------------


def _summary(installed: str | None, latest: str, changelog: str = _SAMPLE_CHANGELOG) -> str:
    return cli.summarize_changelog(changelog, installed, latest)


def test_summary_covers_every_release_after_installed_newest_first() -> None:
    out = _summary("3.6.0", "3.8.0")
    assert out.index("v3.8.0 (2026-06-20)") < out.index("v3.7.0 (2026-06-17)")
    assert "v3.6.0" not in out, "the installed release is not new"
    assert "Older stuff" not in out
    assert "nothing yet" not in out, "must not bleed into Unreleased"


def test_summary_is_structured_by_section_with_one_line_per_top_level_bullet() -> None:
    lines = _summary("3.7.0", "3.8.0").splitlines()
    assert lines[0] == "v3.8.0 (2026-06-20)"
    assert lines[1:] == [
        "  Added",
        "    - A guard with a bold lead",
        "    - A plain bullet with no bold lead",
        "  Fixed",
        "    - Upgrade notes are readable",
        "",
        "Full release notes: https://github.com/bendourthe/Nexus-Hub/releases/tag/v3.8.0",
    ]


def test_summary_skips_nested_sub_bullets_and_body_text() -> None:
    out = _summary("3.7.0", "3.8.0")
    for dropped in ("Activation", "Validation", "settings file", "long explanation", "second sentence"):
        assert dropped.lower() not in out.lower()


def test_summary_headline_strips_markdown() -> None:
    assert cli._bullet_headline("**`agent-memory` points at the [host store](docs/x.md).** More text.") == (
        "agent-memory points at the host store"
    )
    assert cli._bullet_headline("Use *emphasis* and `code` here. Then more.") == "Use emphasis and code here"


def test_summary_headline_truncates_at_a_word_boundary() -> None:
    headline = cli._bullet_headline("word " * 60)
    assert len(headline) <= cli.WHATS_NEW_ITEM_WIDTH
    assert headline.endswith("...") and not headline.endswith(" ...")
    assert "wor..." not in headline, "must not cut inside a word"


def test_summary_caps_items_per_section() -> None:
    bullets = "\n".join(f"- **Item {n}.** body" for n in range(1, 8))
    out = _summary("1.0.0", "2.0.0", f"## [2.0.0] - 2026-01-01\n\n### Added\n\n{bullets}\n")
    cap = cli.WHATS_NEW_MAX_ITEMS_PER_SECTION
    assert f"Item {cap}" in out and f"Item {cap + 1}" not in out
    assert f"+ {7 - cap} more" in out


def test_summary_caps_versions_and_counts_the_rest() -> None:
    changelog = "".join(
        f"## [1.{n}.0] - 2026-01-{n:02d}\n\n### Added\n\n- **Release {n}.**\n\n" for n in range(9, 0, -1)
    )
    out = _summary("1.0.0", "1.9.0", changelog)
    cap = cli.WHATS_NEW_MAX_VERSIONS
    assert sum(1 for line in out.splitlines() if line.startswith("v1.")) == cap
    assert f"... and {9 - cap} earlier releases" in out
    assert "v1.9.0" in out and "v1.1.0" not in out


def test_summary_without_installed_version_shows_only_the_newest_release() -> None:
    out = _summary(None, "3.8.0")
    assert "v3.8.0" in out and "v3.7.0" not in out


def test_summary_falls_back_to_released_sections_when_latest_is_ahead_of_the_changelog() -> None:
    # Latest 9.9.9 has no heading: every released section after installed still shows.
    out = _summary("3.6.0", "9.9.9")
    assert "v3.8.0" in out and "v3.7.0" in out and "nothing yet" not in out


@pytest.mark.parametrize(
    "changelog",
    ["", "no headings here", "## [Unreleased]\n- **x.**\n", "## [bad]\n- y\n"],
)
def test_summary_is_empty_when_nothing_parses(changelog: str) -> None:
    assert _summary("1.0.0", "2.0.0", changelog) == ""


def test_summary_output_is_ascii_for_any_console() -> None:
    smart = "Smart " + chr(0x201C) + "quotes" + chr(0x201D) + " " + chr(0x2014) + " and caf" + chr(0xE9)
    changelog = f"## [2.0.0] - 2026-01-01\n\n### Added\n\n- **{smart}.**\n"
    out = _summary("1.0.0", "2.0.0", changelog)
    out.encode("ascii")
    assert 'Smart "quotes" - and caf' in out


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
    raw = _write_remote_fixture(tmp_path / "remote", "3.8.0", _SAMPLE_CHANGELOG)
    # No --yes and stdin is not a TTY -> safe default is to NOT upgrade.
    proc = _run_cli(
        ["upgrade"],
        {"NEXUS_HUB_HOME": str(home), "NEXUS_HUB_RAW_BASE": raw},
        stdin="",
    )
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert "newer version is available" in out.lower()
    assert "What's new" in out
    assert "v3.8.0 (2026-06-20)" in out and "v3.7.0 (2026-06-17)" in out, "every release since the install"
    assert "  Added\n    - A guard with a bold lead" in out, "structured: section, then one line per bullet"
    assert "Activation" not in out, "nested sub-bullets are skipped"
    assert "releases/tag/v3.8.0" in out, "points at the full notes"
    assert "skipped" in out.lower()


def test_upgrade_notes_failure_never_blocks_the_upgrade(tmp_path: Path, monkeypatch, capsys) -> None:
    home = tmp_path / "home"
    home.mkdir()
    (home / "VERSION").write_text("3.6.0\n", encoding="utf-8")
    monkeypatch.setenv("NEXUS_HUB_HOME", str(home))
    monkeypatch.setenv("NEXUS_HUB_RAW_BASE", _write_remote_fixture(tmp_path / "remote", "3.8.0", _SAMPLE_CHANGELOG))

    def boom(*_args: object) -> str:
        raise ValueError("unparseable changelog")

    monkeypatch.setattr(cli, "summarize_changelog", boom)
    assert cli.cmd_upgrade(assume_yes=False) == 0
    out = capsys.readouterr().out
    assert "newer version is available" in out and "What's new" not in out


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


def test_run_bootstrap_runs_through_the_current_console_helper(monkeypatch) -> None:
    """The bootstrap must share the user's console, not get the hidden-console default."""
    seen: list[tuple[list[str], dict[str, str] | None]] = []

    def fake_helper(args, *, env=None, cwd=None):
        seen.append((args, env))
        return subprocess.CompletedProcess(args, 4)

    monkeypatch.delenv("NEXUS_HUB_UPGRADE_DRY_RUN", raising=False)
    monkeypatch.setitem(cli._PROCESS_POLICY, "run_in_current_console", fake_helper)
    assert cli.run_bootstrap("v9.9.9") == 4
    ((command, env),) = seen
    assert command == cli._bootstrap_command()
    assert env is not None and env["NEXUS_HUB_REF"] == "v9.9.9"


def test_run_bootstrap_dry_run_launches_nothing(monkeypatch, capsys) -> None:
    def must_not_run(*_args, **_kwargs):
        raise AssertionError("dry run must not launch the bootstrap")

    monkeypatch.setenv("NEXUS_HUB_UPGRADE_DRY_RUN", "1")
    monkeypatch.setitem(cli._PROCESS_POLICY, "run_in_current_console", must_not_run)
    assert cli.run_bootstrap() == 0
    assert "[dry-run]" in capsys.readouterr().out


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
