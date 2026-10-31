"""The install manifest's diagnostic `logs` trail stays bounded across installs."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.lib.integrations.manifest import MAX_LOGS, InstallManifest


def test_save_keeps_only_the_most_recent_log_lines(tmp_path: Path) -> None:
    manifest = InstallManifest()
    for i in range(MAX_LOGS + 250):
        manifest.log("claude", f"line {i}")

    path = tmp_path / "install-manifest.json"
    manifest.save(path)

    logs = json.loads(path.read_text(encoding="utf-8"))["logs"]
    assert len(logs) == MAX_LOGS
    assert logs[0] == "[claude] line 250"
    assert logs[-1] == f"[claude] line {MAX_LOGS + 249}"


def test_load_trims_an_oversized_legacy_trail(tmp_path: Path) -> None:
    path = tmp_path / "install-manifest.json"
    legacy = {"tracked": {"claude": ["a.md"]}, "shared": {}, "actions": {}}
    legacy["logs"] = [f"[claude] old {i}" for i in range(3 * MAX_LOGS)]
    path.write_text(json.dumps(legacy), encoding="utf-8")

    manifest = InstallManifest.load(path)
    manifest.log("claude", "new")
    manifest.save(path)

    data = json.loads(path.read_text(encoding="utf-8"))
    assert len(data["logs"]) == MAX_LOGS
    assert data["logs"][-1] == "[claude] new"
    assert data["tracked"] == {"claude": ["a.md"]}


def test_repeated_installs_do_not_grow_the_trail(tmp_path: Path) -> None:
    path = tmp_path / "install-manifest.json"
    for run in range(5):
        manifest = InstallManifest.load(path)
        for i in range(MAX_LOGS):
            manifest.log("codex", f"run {run} line {i}")
        manifest.save(path)

    logs = json.loads(path.read_text(encoding="utf-8"))["logs"]
    assert len(logs) == MAX_LOGS
    assert logs[0] == "[codex] run 4 line 0"
