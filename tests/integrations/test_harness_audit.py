"""Tests for v2.3.0 / Phase 4 / T012 harness_audit scoring."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import harness_audit  # noqa: E402
from scripts.lib.integrations import INTEGRATION_REGISTRY  # noqa: E402
from scripts.lib.integrations.base import InstallContext  # noqa: E402
from scripts.lib.integrations.manifest import InstallManifest  # noqa: E402


@pytest.fixture
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    return home


@pytest.fixture
def fresh_target_with_install(
    tmp_path: Path, fake_home: Path
) -> tuple[Path, Path]:
    """Install `claude` against a fresh workspace and persist the manifest."""
    target = tmp_path / "workspace"
    target.mkdir()
    manifest = InstallManifest()
    ctx = InstallContext(
        repo_root=REPO_ROOT,
        target_root=target,
        scope="workspace",
        overwrite=False,
        dry_run=False,
        manifest=manifest,
        template_vars={"PROJECT_NAME": "test-project"},
    )
    integ = INTEGRATION_REGISTRY["claude"]
    result = integ.install(ctx)
    manifest.record_actions("claude", result.files)
    manifest_path = target / ".nexus-hub" / "install-manifest.json"
    manifest.save(manifest_path)
    return target, manifest_path


def test_audit_returns_empty_report_when_no_manifest(tmp_path: Path) -> None:
    report = harness_audit.audit(tmp_path / "empty")
    assert report.integrations == []
    assert report.aggregate() == 0.0


def test_audit_scores_clean_install_at_high_score(
    fresh_target_with_install: tuple[Path, Path]
) -> None:
    target, _ = fresh_target_with_install
    report = harness_audit.audit(target)
    assert report.integrations, "claude install should produce an audit entry"
    claude = report.integrations[0]
    # A clean install should score very high on every axis.
    assert claude.score >= 80.0, f"expected score >= 80, got {claude.score}"
    assert claude.axes["presence"] == pytest.approx(1.0)
    assert claude.axes["integrity"] == pytest.approx(1.0)
    assert claude.missing == 0
    assert claude.drifted == 0


def test_audit_penalizes_drifted_files(
    fresh_target_with_install: tuple[Path, Path]
) -> None:
    target, manifest_path = fresh_target_with_install
    manifest = InstallManifest.load(manifest_path)
    # Drift exactly one file.
    for entry in manifest.actions_for("claude"):
        sha = entry.get("sha256")
        path = Path(str(entry.get("path", "")))
        if sha is not None and path.is_file():
            path.write_text("DRIFTED", encoding="utf-8")
            break
    report = harness_audit.audit(target)
    claude = report.integrations[0]
    assert claude.drifted >= 1
    assert claude.axes["integrity"] < 1.0


def test_audit_penalizes_missing_files(
    fresh_target_with_install: tuple[Path, Path]
) -> None:
    target, manifest_path = fresh_target_with_install
    manifest = InstallManifest.load(manifest_path)
    for entry in manifest.actions_for("claude"):
        sha = entry.get("sha256")
        path = Path(str(entry.get("path", "")))
        if sha is not None and path.is_file():
            path.unlink()
            break
    report = harness_audit.audit(target)
    claude = report.integrations[0]
    assert claude.missing >= 1
    # Both presence and integrity drop when a file disappears.
    assert claude.axes["presence"] < 1.0
    assert claude.axes["integrity"] < 1.0


def test_audit_score_is_deterministic(
    fresh_target_with_install: tuple[Path, Path]
) -> None:
    target, _ = fresh_target_with_install
    first = harness_audit.audit(target).aggregate()
    second = harness_audit.audit(target).aggregate()
    assert first == second


def test_main_json_output_is_parseable(
    fresh_target_with_install: tuple[Path, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    import json

    target, _ = fresh_target_with_install
    code = harness_audit.main(["--target", str(target), "--json"])
    captured = capsys.readouterr().out
    assert code == 0
    parsed = json.loads(captured)
    assert "aggregate_score" in parsed
    assert parsed["integrations"]


def test_main_min_score_threshold(
    fresh_target_with_install: tuple[Path, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    target, _ = fresh_target_with_install
    # 200 is unreachable (max is 100) so this should always exit 1.
    code = harness_audit.main(
        ["--target", str(target), "--min-score", "200", "--json"]
    )
    assert code == 1


def test_audit_handles_unknown_integration_gracefully(tmp_path: Path) -> None:
    # Hand-build a manifest with a key that is NOT in the registry.
    target = tmp_path / "workspace"
    target.mkdir()
    manifest = InstallManifest()
    manifest._actions["does-not-exist"] = [
        {"path": "fake.txt", "action": "created", "sha256": None, "mtime": None}
    ]
    manifest_path = target / ".nexus-hub" / "install-manifest.json"
    manifest.save(manifest_path)
    report = harness_audit.audit(target, requested=["does-not-exist"])
    # _audit_one returns None for unknown keys; the audit just skips them.
    assert report.integrations == []
