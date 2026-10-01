"""Tests for `nexus-hub init` through the CLI core and both launchers (AR-01).

The installer tells users to run `nexus-hub init` and the on-open autoseed hook
calls it, but until v4.13.6 the CLI core had no `init` subcommand, so every call
exited with "invalid choice: 'init'" and the hook swallowed the failure. The
CLI now forwards `init` to the integration runner of a source tree that holds
both the runner and `catalog/`.

Each test builds an installed-layout home (`<home>/scripts/nexus_hub_cli.py`)
with no catalog, so the checkout this file runs from can never satisfy the
lookup by accident, and a stand-in source tree whose runner records the argv
and the `NEXUS_HUB_INIT` marker it received.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"

_RUN_KW = dict(capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)

_RECORDING_RUNNER = """\
import json, os, sys
from pathlib import Path
Path(os.environ["INIT_RECORD"]).write_text(json.dumps({
    "argv": sys.argv[1:],
    "init_marker": os.environ.get("NEXUS_HUB_INIT"),
}), encoding="utf-8")
sys.exit(int(os.environ.get("INIT_EXIT", "0")))
"""


def _installed_home(tmp_path: Path) -> Path:
    home = tmp_path / "home" / ".nexus-hub"
    (home / "scripts").mkdir(parents=True)
    shutil.copy2(SCRIPTS / "nexus_hub_cli.py", home / "scripts" / "nexus_hub_cli.py")
    (home / "bin").mkdir()
    shutil.copy2(SCRIPTS / "nexus-hub", home / "bin" / "nexus-hub")
    shutil.copy2(SCRIPTS / "nexus-hub.cmd", home / "bin" / "nexus-hub.cmd")
    return home


def _stand_in_source(root: Path) -> Path:
    runner = root / "scripts" / "lib" / "integrations" / "runner.py"
    runner.parent.mkdir(parents=True)
    runner.write_text(_RECORDING_RUNNER, encoding="utf-8")
    (root / "catalog").mkdir()
    return root


def _env(home: Path, record: Path, **extra: str) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in {"NEXUS_HUB_SRC", "NEXUS_HUB_INIT"}}
    env.update(NEXUS_HUB_HOME=str(home), INIT_RECORD=str(record), **extra)
    return env


def _run_cli(home: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(home / "scripts" / "nexus_hub_cli.py"), "init", *args],
        env=env,
        **_RUN_KW,
    )


def test_init_forwards_every_token_and_the_intent_marker(tmp_path: Path) -> None:
    home = _installed_home(tmp_path)
    _stand_in_source(home / "src")
    record = tmp_path / "record.json"

    proc = _run_cli(home, _env(home, record), "--target", "proj dir", "--dry-run", "--quiet")

    assert proc.returncode == 0, proc.stderr
    seen = json.loads(record.read_text(encoding="utf-8"))
    assert seen == {
        "argv": ["init", "--target", "proj dir", "--dry-run", "--quiet"],
        "init_marker": "1",
    }


def test_init_returns_the_runner_exit_code(tmp_path: Path) -> None:
    home = _installed_home(tmp_path)
    _stand_in_source(home / "src")

    proc = _run_cli(home, _env(home, tmp_path / "r.json", INIT_EXIT="3"))

    assert proc.returncode == 3


def test_nexus_hub_src_takes_precedence_over_the_bootstrap_tree(tmp_path: Path) -> None:
    home = _installed_home(tmp_path)
    (home / "src").mkdir()  # a bootstrap tree without a runner never qualifies
    source = _stand_in_source(tmp_path / "checkout")
    record = tmp_path / "record.json"

    proc = _run_cli(home, _env(home, record, NEXUS_HUB_SRC=str(source)), "--dry-run")

    assert proc.returncode == 0, proc.stderr
    assert json.loads(record.read_text(encoding="utf-8"))["argv"] == ["init", "--dry-run"]


def test_a_runner_without_a_catalog_is_not_a_source_tree(tmp_path: Path) -> None:
    home = _installed_home(tmp_path)
    source = _stand_in_source(home / "src")
    shutil.rmtree(source / "catalog")
    record = tmp_path / "record.json"

    proc = _run_cli(home, _env(home, record))

    assert proc.returncode == 2
    assert "needs the Nexus-Hub source tree" in proc.stderr
    assert not record.exists()


def test_init_is_no_longer_an_invalid_choice_from_the_checkout() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "nexus_hub_cli.py"), "init", "--help"],
        env={k: v for k, v in os.environ.items() if k != "NEXUS_HUB_SRC"},
        **_RUN_KW,
    )

    assert proc.returncode == 0, proc.stderr
    assert "invalid choice" not in proc.stderr
    assert "--target" in proc.stdout


def test_init_is_listed_in_the_top_level_help() -> None:
    proc = subprocess.run([sys.executable, str(SCRIPTS / "nexus_hub_cli.py"), "--help"], **_RUN_KW)

    assert proc.returncode == 0
    assert "init" in proc.stdout


def test_the_real_runner_seeds_a_monorepo_subdirectory_through_the_cli(tmp_path: Path) -> None:
    home = _installed_home(tmp_path)
    target = tmp_path / "monorepo" / "packages" / "app"  # spec-kit S8: a subdirectory target
    target.mkdir(parents=True)

    proc = _run_cli(home, _env(home, tmp_path / "unused.json", NEXUS_HUB_SRC=str(REPO_ROOT)), "--target", str(target))

    assert proc.returncode == 0, proc.stderr
    assert (target / ".cursor" / "rules" / "nexus-hub.mdc").is_file()


@pytest.mark.skipif(shutil.which("bash") is None, reason="no bash on PATH")
def test_the_posix_launcher_reaches_init(tmp_path: Path) -> None:
    home = _installed_home(tmp_path)
    _stand_in_source(home / "src")
    record = tmp_path / "record.json"

    proc = subprocess.run(
        [shutil.which("bash"), str(home / "bin" / "nexus-hub"), "init", "--target", "x"],
        env=_env(home, record),
        **_RUN_KW,
    )

    assert proc.returncode == 0, proc.stderr
    assert json.loads(record.read_text(encoding="utf-8"))["argv"] == ["init", "--target", "x"]


@pytest.mark.skipif(os.name != "nt", reason="the .cmd launcher runs only on Windows")
def test_the_windows_launcher_reaches_init(tmp_path: Path) -> None:
    home = _installed_home(tmp_path)
    _stand_in_source(home / "src")
    record = tmp_path / "record.json"

    proc = subprocess.run(
        ["cmd", "/c", str(home / "bin" / "nexus-hub.cmd"), "init", "--target", "x"],
        env=_env(home, record),
        **_RUN_KW,
    )

    assert proc.returncode == 0, proc.stderr
    assert json.loads(record.read_text(encoding="utf-8"))["argv"] == ["init", "--target", "x"]


def test_an_invalid_nexus_hub_src_is_refused_not_ignored(tmp_path: Path) -> None:
    """A set override that does not qualify must never fall back to another tree."""
    home = _installed_home(tmp_path)
    _stand_in_source(home / "src")  # a valid fallback exists and must not be used
    record = tmp_path / "record.json"

    proc = _run_cli(home, _env(home, record, NEXUS_HUB_SRC=str(tmp_path / "missing")))

    assert proc.returncode == 2
    assert "is not a Nexus-Hub source tree" in proc.stderr
    assert not record.exists()
