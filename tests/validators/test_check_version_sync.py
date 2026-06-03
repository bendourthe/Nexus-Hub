"""Tests for scripts/check_version_sync.py.

The guard reads the canonical version from `.claude-plugin/plugin.json` and
asserts every other version-carrying surface agrees with it. These tests build
small fixture trees under a temporary `--root` and exercise the in-sync path,
each drift class, the partial-tree tolerance, and the JSON output.
"""

from __future__ import annotations

import json
from pathlib import Path


SCRIPT = "check_version_sync.py"


def write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _plugin_json(version: str) -> str:
    return json.dumps({"name": "nexus-hub", "version": version}, indent=2)


def _marketplace_json(version: str) -> str:
    return json.dumps({"plugin": {"name": "nexus-hub", "version": version}}, indent=2)


def _installer_sh(version: str) -> str:
    return f'#!/usr/bin/env bash\nset -euo pipefail\nNEXUS_HUB_VERSION="{version}"\n'


def _installer_ps1(version: str) -> str:
    return f'$script:NexusHubVersion = "{version}"\n'


def _changelog(version: str) -> str:
    return f"# Changelog\n\n---\n\n## [{version}] - 2026-06-02\n\nNotes.\n"


def _readme(version: str) -> str:
    return f"# Nexus-Hub\n\n<!-- nexus-hub-version: {version} -->\n\nBody.\n"


def _agents(version: str) -> str:
    return f"# AGENTS.md\n\n<!-- nexus-hub-version: {version} -->\n\nBody.\n"


def build_full_tree(root: Path, version: str = "2.4.0") -> Path:
    """Write every surface at the same version (a perfectly in-sync tree)."""
    write(root / ".claude-plugin" / "plugin.json", _plugin_json(version))
    write(root / "data" / "marketplace.json", _marketplace_json(version))
    write(root / "scripts" / "installer.sh", _installer_sh(version))
    write(root / "scripts" / "installer.ps1", _installer_ps1(version))
    write(root / "CHANGELOG.md", _changelog(version))
    write(root / "README.md", _readme(version))
    write(root / "AGENTS.md", _agents(version))
    return root


def test_in_sync_tree_passes(tmp_path: Path, runner) -> None:
    build_full_tree(tmp_path, "2.4.0")
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 0, result.stderr


def test_injected_installer_sh_drift_fails(tmp_path: Path, runner) -> None:
    build_full_tree(tmp_path, "2.4.0")
    write(tmp_path / "scripts" / "installer.sh", _installer_sh("2.3.0"))
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "installer.sh" in result.stderr
    assert "2.3.0" in result.stderr
    assert "2.4.0" in result.stderr


def test_installer_ps1_drift_fails(tmp_path: Path, runner) -> None:
    build_full_tree(tmp_path, "2.4.0")
    write(tmp_path / "scripts" / "installer.ps1", _installer_ps1("2.2.0"))
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "installer.ps1" in result.stderr


def test_marketplace_drift_fails(tmp_path: Path, runner) -> None:
    build_full_tree(tmp_path, "2.4.0")
    write(tmp_path / "data" / "marketplace.json", _marketplace_json("1.9.0"))
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "marketplace.json" in result.stderr


def test_changelog_heading_drift_fails(tmp_path: Path, runner) -> None:
    build_full_tree(tmp_path, "2.4.0")
    write(tmp_path / "CHANGELOG.md", _changelog("2.3.0"))
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "CHANGELOG.md" in result.stderr


def test_readme_marker_drift_fails(tmp_path: Path, runner) -> None:
    # Proves marker surfaces ARE checked when the marker is present.
    build_full_tree(tmp_path, "2.4.0")
    write(tmp_path / "README.md", _readme("0.9.0"))
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "README.md" in result.stderr


def test_missing_surfaces_are_tolerated(tmp_path: Path, runner) -> None:
    # Only the canonical + one matching surface present: absent files are
    # skipped, not failures, so a partial tree stays green.
    write(tmp_path / ".claude-plugin" / "plugin.json", _plugin_json("2.4.0"))
    write(tmp_path / "scripts" / "installer.sh", _installer_sh("2.4.0"))
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 0, result.stderr


def test_missing_marker_is_skipped_not_failed(tmp_path: Path, runner) -> None:
    # A README present but lacking the version marker is tolerated (the marker
    # is an optional anchor), while structured surfaces still match.
    build_full_tree(tmp_path, "2.4.0")
    write(tmp_path / "README.md", "# Nexus-Hub\n\nNo marker here.\n")
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 0, result.stderr


def test_unparseable_structured_surface_fails(tmp_path: Path, runner) -> None:
    # installer.sh present but with no NEXUS_HUB_VERSION constant -> a finding.
    build_full_tree(tmp_path, "2.4.0")
    write(tmp_path / "scripts" / "installer.sh", "#!/usr/bin/env bash\necho hi\n")
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "installer.sh" in result.stderr


def test_missing_canonical_is_usage_error(tmp_path: Path, runner) -> None:
    # No plugin.json at all -> usage/IO error, exit 2.
    write(tmp_path / "scripts" / "installer.sh", _installer_sh("2.4.0"))
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 2
    assert "canonical" in result.stderr.lower()


def test_multiple_drift_surfaces_all_listed(tmp_path: Path, runner) -> None:
    build_full_tree(tmp_path, "2.4.0")
    write(tmp_path / "scripts" / "installer.sh", _installer_sh("2.3.0"))
    write(tmp_path / "scripts" / "installer.ps1", _installer_ps1("2.3.0"))
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "installer.sh" in result.stderr
    assert "installer.ps1" in result.stderr


def test_json_output_in_sync(tmp_path: Path, runner) -> None:
    build_full_tree(tmp_path, "2.4.0")
    result = runner(SCRIPT, tmp_path, ["--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["canonical"] == "2.4.0"
    assert payload["in_sync"] is True
    assert len(payload["surfaces"]) == 6


def test_json_output_reports_drift(tmp_path: Path, runner) -> None:
    build_full_tree(tmp_path, "2.4.0")
    write(tmp_path / "data" / "marketplace.json", _marketplace_json("2.3.0"))
    result = runner(SCRIPT, tmp_path, ["--json"])
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["in_sync"] is False
    drifted = [s for s in payload["surfaces"] if s["status"] == "drift"]
    assert any("marketplace.json" in s["path"] for s in drifted)
