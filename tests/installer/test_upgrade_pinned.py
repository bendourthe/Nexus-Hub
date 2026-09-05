"""v4.7.0 Phase 6: `nexus-hub upgrade` on a pinned install.

A pinned install refuses to move unless told where (`--latest` re-pins to the newest
release tag, `--ref` moves to any tag or branch, which is also rollback); an unpinned
install behaves exactly as before. Exercised through the CLI with the dry-run seam so
no bootstrap runs.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PY = REPO_ROOT / "scripts" / "nexus_hub_cli.py"
_RUN_KW = {
    "capture_output": True,
    "text": True,
    "encoding": "utf-8",
    "errors": "replace",
}


def _remote(root: Path, version: str) -> str:
    (root / ".claude-plugin").mkdir(parents=True)
    (root / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"version": version}), encoding="utf-8"
    )
    (root / "CHANGELOG.md").write_text(
        f"# Changelog\n\n## [{version}] - 2026-09-05\n\n### Added\n\n- Things.\n",
        encoding="utf-8",
    )
    return root.as_uri()


def _run(
    args: list[str], env_extra: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("NEXUS_HUB_")}
    env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(CLI_PY), *args], env=env, input="", check=False, **_RUN_KW
    )  # type: ignore[arg-type]


def _home(tmp_path: Path, installed: str, pinned: str | None) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    (home / "VERSION").write_text(installed + "\n", encoding="utf-8")
    if pinned:
        (home / "PINNED_REF").write_text(pinned + "\n", encoding="utf-8")
    return home


def test_pinned_install_refuses_to_move_without_a_target(tmp_path: Path) -> None:
    home = _home(tmp_path, "4.6.0", "v4.6.0")
    raw = _remote(tmp_path / "remote", "4.7.0")
    proc = _run(
        ["upgrade", "--yes"],
        {
            "NEXUS_HUB_HOME": str(home),
            "NEXUS_HUB_RAW_BASE": raw,
            "NEXUS_HUB_UPGRADE_DRY_RUN": "1",
        },
    )
    assert proc.returncode == 3, (proc.stdout, proc.stderr)
    assert "pinned to v4.6.0" in proc.stdout + proc.stderr
    assert "--latest" in proc.stderr and "--ref" in proc.stderr
    assert "dry-run" not in proc.stdout.lower(), "nothing may run on a refusal"


def test_pinned_install_moves_to_the_newest_release_tag_with_latest(
    tmp_path: Path,
) -> None:
    home = _home(tmp_path, "4.6.0", "v4.6.0")
    raw = _remote(tmp_path / "remote", "4.7.0")
    proc = _run(
        ["upgrade", "--yes", "--latest"],
        {
            "NEXUS_HUB_HOME": str(home),
            "NEXUS_HUB_RAW_BASE": raw,
            "NEXUS_HUB_UPGRADE_DRY_RUN": "1",
        },
    )
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert "NEXUS_HUB_REF=v4.7.0" in proc.stdout


def test_ref_moves_to_the_named_tag_which_is_also_rollback(tmp_path: Path) -> None:
    home = _home(tmp_path, "4.7.0", "v4.7.0")
    proc = _run(
        ["upgrade", "--yes", "--ref", "v4.6.0"],
        {"NEXUS_HUB_HOME": str(home), "NEXUS_HUB_UPGRADE_DRY_RUN": "1"},
    )
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert "NEXUS_HUB_REF=v4.6.0" in proc.stdout


def test_unpinned_install_is_unchanged(tmp_path: Path) -> None:
    home = _home(tmp_path, "4.6.0", None)
    raw = _remote(tmp_path / "remote", "4.7.0")
    proc = _run(
        ["upgrade", "--yes"],
        {
            "NEXUS_HUB_HOME": str(home),
            "NEXUS_HUB_RAW_BASE": raw,
            "NEXUS_HUB_UPGRADE_DRY_RUN": "1",
        },
    )
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert "NEXUS_HUB_REF=main" in proc.stdout
    assert "pinned" not in proc.stdout.lower()
