"""Shared pytest fixtures for integration-registry tests."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from scripts.lib.integrations import legacy  # noqa: E402
from scripts.lib.integrations.base import InstallContext  # noqa: E402
from scripts.lib.integrations.manifest import InstallManifest  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_nexus_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep workspace lock and backup writes out of the invoking home."""
    monkeypatch.setenv("NEXUS_HUB_HOME", str(tmp_path / "nexus-home"))


@pytest.fixture(scope="module", autouse=True)
def isolated_legacy_host_cleanup(request: pytest.FixtureRequest):
    """Generic installs must not query or mutate editor extensions or OS tasks."""
    if Path(request.module.__file__).name == "test_legacy_cleanups.py":
        yield
        return
    host_callbacks = {
        legacy._cleanup_claude_legacy_vscode_extension,
        legacy._cleanup_windows_auth_monitor_task,
    }
    with pytest.MonkeyPatch.context() as patch:
        patch.setitem(legacy.LEGACY_CLEANUPS, "claude", [
            callback for callback in legacy.LEGACY_CLEANUPS["claude"]
            if callback not in host_callbacks
        ])
        yield


@pytest.fixture(autouse=True)
def isolated_legacy_filesystem_home(request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> None:
    """Give unconfigured tests a private home outside their install target."""
    if Path(request.module.__file__).name == "test_legacy_cleanups.py":
        return
    home = tmp_path_factory.mktemp("integration-home")
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def install_ctx(tmp_path: Path) -> InstallContext:
    return InstallContext(
        repo_root=REPO_ROOT,
        target_root=tmp_path,
        scope="workspace",
        overwrite=False,
        dry_run=False,
        manifest=InstallManifest(),
        template_vars={"PROJECT_NAME": "test-project"},
    )
