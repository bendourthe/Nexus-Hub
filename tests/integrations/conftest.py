"""Shared pytest fixtures for integration-registry tests."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from scripts.lib.integrations.base import InstallContext  # noqa: E402
from scripts.lib.integrations.manifest import InstallManifest  # noqa: E402


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
