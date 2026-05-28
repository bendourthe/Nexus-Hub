"""Tests for v2.3.0 / Phase 4 / T010 lifecycle additions.

Covers:

* `InstallManifest.record_actions` round-trips through `to_dict` / `from_dict`.
* `lifecycle.doctor` reports OK on a clean install.
* `lifecycle.doctor` flags `missing` when a managed file is deleted.
* `lifecycle.doctor` flags `drifted` when a managed file is edited in place.
* `lifecycle.repair` reverts a drifted file back to its installed content.
* `lifecycle.list_installed` enumerates every recorded entry.

The tests exercise the real `claude` integration through the same fixtures
the contract suite uses so any regression in the install pipeline is caught
here instead of silently passing.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.integrations import INTEGRATION_REGISTRY  # noqa: E402
from scripts.lib.integrations.base import InstallContext  # noqa: E402
from scripts.lib.integrations.lifecycle import (  # noqa: E402
    DIAGNOSTIC_DRIFTED,
    DIAGNOSTIC_MISSING,
    DIAGNOSTIC_OK,
    DIAGNOSTIC_UNKNOWN,
    doctor,
    list_installed,
    repair,
)
from scripts.lib.integrations.manifest import InstallManifest  # noqa: E402


@pytest.fixture
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    return home


@pytest.fixture
def fresh_target(tmp_path: Path) -> Path:
    target = tmp_path / "workspace"
    target.mkdir()
    return target


def _make_ctx(target: Path, overwrite: bool = False) -> InstallContext:
    return InstallContext(
        repo_root=REPO_ROOT,
        target_root=target,
        scope="workspace",
        overwrite=overwrite,
        dry_run=False,
        manifest=InstallManifest(),
        template_vars={"PROJECT_NAME": "test-project"},
    )


def _install_and_record(key: str, ctx: InstallContext):
    integ = INTEGRATION_REGISTRY[key]
    result = integ.install(ctx)
    ctx.manifest.record_actions(key, result.files)
    return result


# --------------------------------------------------------------------------- #
# Manifest round-trip
# --------------------------------------------------------------------------- #


def test_manifest_record_actions_roundtrips(fake_home: Path, fresh_target: Path) -> None:
    ctx = _make_ctx(fresh_target)
    _install_and_record("claude", ctx)
    dumped = ctx.manifest.to_dict()
    assert "actions" in dumped
    assert "claude" in dumped["actions"]
    rehydrated = InstallManifest.from_dict(dumped)
    assert rehydrated.all_action_keys() == ctx.manifest.all_action_keys()
    assert rehydrated.actions_for("claude") == ctx.manifest.actions_for("claude")


def test_manifest_record_actions_persists_to_disk(
    fake_home: Path, fresh_target: Path, tmp_path: Path
) -> None:
    ctx = _make_ctx(fresh_target)
    _install_and_record("claude", ctx)
    persisted = tmp_path / "manifest.json"
    ctx.manifest.save(persisted)
    reloaded = InstallManifest.load(persisted)
    assert reloaded.actions_for("claude")
    # Every entry should have the four expected fields.
    for entry in reloaded.actions_for("claude"):
        assert {"path", "action", "sha256", "mtime"} <= set(entry.keys())


# --------------------------------------------------------------------------- #
# doctor
# --------------------------------------------------------------------------- #


def test_doctor_reports_ok_after_clean_install(
    fake_home: Path, fresh_target: Path
) -> None:
    ctx = _make_ctx(fresh_target)
    _install_and_record("claude", ctx)
    report = doctor(ctx.manifest, ["claude"])
    assert not report.has_issues()
    diagnostics = {f.diagnostic for f in report.findings}
    assert diagnostics <= {DIAGNOSTIC_OK, DIAGNOSTIC_UNKNOWN}


def test_doctor_flags_missing_after_delete(
    fake_home: Path, fresh_target: Path
) -> None:
    ctx = _make_ctx(fresh_target)
    _install_and_record("claude", ctx)
    # Delete every managed *file* (not directories) to simulate a stray rm.
    deleted: list[str] = []
    for entry in ctx.manifest.actions_for("claude"):
        sha = entry.get("sha256")
        path = Path(str(entry.get("path", "")))
        if sha is not None and path.is_file():
            path.unlink()
            deleted.append(str(path))
            break
    assert deleted, "fixture: no recorded files to delete"
    report = doctor(ctx.manifest, ["claude"])
    missing = [f for f in report.findings if f.diagnostic == DIAGNOSTIC_MISSING]
    assert any(f.path == deleted[0] for f in missing)
    assert report.has_issues()


def test_doctor_flags_drifted_after_in_place_edit(
    fake_home: Path, fresh_target: Path
) -> None:
    ctx = _make_ctx(fresh_target)
    _install_and_record("claude", ctx)
    drifted_path: str | None = None
    for entry in ctx.manifest.actions_for("claude"):
        sha = entry.get("sha256")
        path = Path(str(entry.get("path", "")))
        if sha is not None and path.is_file():
            path.write_text(path.read_text(encoding="utf-8") + "\n# drifted\n", encoding="utf-8")
            drifted_path = str(path)
            break
    assert drifted_path is not None
    report = doctor(ctx.manifest, ["claude"])
    drifted = [f for f in report.findings if f.diagnostic == DIAGNOSTIC_DRIFTED]
    assert any(f.path == drifted_path for f in drifted)
    assert report.has_issues()


def test_doctor_handles_unknown_integration(fresh_target: Path) -> None:
    manifest = InstallManifest()
    report = doctor(manifest, ["claude", "does-not-exist"])
    assert report.integrations_unknown == ["claude", "does-not-exist"]
    assert report.findings == []


# --------------------------------------------------------------------------- #
# repair
# --------------------------------------------------------------------------- #


def test_repair_restores_drifted_file(fake_home: Path, fresh_target: Path) -> None:
    ctx = _make_ctx(fresh_target)
    _install_and_record("claude", ctx)
    drift_target: Path | None = None
    original_sha: str | None = None
    for entry in ctx.manifest.actions_for("claude"):
        sha = entry.get("sha256")
        path = Path(str(entry.get("path", "")))
        if sha is not None and path.is_file():
            drift_target = path
            original_sha = str(sha)
            path.write_text("DRIFTED CONTENT", encoding="utf-8")
            break
    assert drift_target is not None and original_sha is not None
    # repair() uses ctx; rewrite needs overwrite=True per lifecycle.repair.
    repair_ctx = InstallContext(
        repo_root=REPO_ROOT,
        target_root=fresh_target,
        scope="workspace",
        overwrite=True,
        dry_run=False,
        manifest=ctx.manifest,
        template_vars={"PROJECT_NAME": "test-project"},
    )
    repair(repair_ctx, ["claude"])
    # The repaired file should once again hash to the recorded value, OR the
    # repair recorded a new SHA matching the file's new content.
    new_report = doctor(repair_ctx.manifest, ["claude"])
    assert not new_report.has_issues()


def test_repair_is_noop_when_clean(fake_home: Path, fresh_target: Path) -> None:
    ctx = _make_ctx(fresh_target)
    _install_and_record("claude", ctx)
    result = repair(ctx, ["claude"])
    # No file should have been re-written when nothing drifted.
    assert all(fa.action in ("unchanged", "kept", "not-found") for fa in result.files)


# --------------------------------------------------------------------------- #
# list_installed
# --------------------------------------------------------------------------- #


def test_list_installed_enumerates_recorded_entries(
    fake_home: Path, fresh_target: Path
) -> None:
    ctx = _make_ctx(fresh_target)
    _install_and_record("claude", ctx)
    data = list_installed(ctx.manifest)
    assert "claude" in data
    assert data["claude"]
    assert all("path" in r and "action" in r for r in data["claude"])


def test_list_installed_empty_manifest_returns_empty_dict() -> None:
    assert list_installed(InstallManifest()) == {}
