"""Tests for the Nexus-AI version manifest (`nexus-hub-version.json`).

The Nexus-AI desktop app reads this manifest to display the installed catalog
version, detect when a newer release is published upstream, and resolve each
surface subdirectory. These tests pin the contract: correct location, canonical
version, deterministic/idempotent bytes, and teardown removal.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.lib.integrations import get
from scripts.lib.integrations.base import InstallContext

VERSION_FILE = "nexus-hub-version.json"


def _canonical_version(repo_root: Path) -> str:
    data = json.loads((repo_root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    return data["version"]


def test_version_manifest_written_with_canonical_version(
    install_ctx: InstallContext, repo_root: Path
) -> None:
    integ = get("nexus-ai")
    integ.install(install_ctx)

    manifest_path = install_ctx.target_root / ".nexus-ai" / "catalog" / VERSION_FILE
    assert manifest_path.exists(), f"expected version manifest at {manifest_path}"

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["product"] == "Nexus-Hub"
    assert payload["version"] == _canonical_version(repo_root)
    assert payload["source_repo"] == "bendourthe/Nexus-Hub"
    assert payload["latest_release_api"].startswith("https://api.github.com/repos/")
    # The layout map lets the app resolve every surface without hardcoding names.
    assert payload["layout"]["skills"] == "skills"
    assert payload["layout"]["instructions"] == "NEXUS_AI.md"
    for key in ("commands", "agents", "rules", "hooks", "mcp_configs", "templates"):
        assert key in payload["layout"], f"layout missing {key}"


def test_version_manifest_is_idempotent(install_ctx: InstallContext) -> None:
    integ = get("nexus-ai")
    integ.install(install_ctx)
    result = integ.install(install_ctx)

    actions = [fa for fa in result.files if fa.path.endswith(VERSION_FILE)]
    assert actions, "expected a version-manifest action on reinstall"
    assert actions[0].action == "unchanged"


def test_version_manifest_removed_on_teardown(install_ctx: InstallContext) -> None:
    integ = get("nexus-ai")
    integ.install(install_ctx)
    manifest_path = install_ctx.target_root / ".nexus-ai" / "catalog" / VERSION_FILE
    assert manifest_path.exists()

    integ.teardown(install_ctx)
    assert not manifest_path.exists(), "teardown should remove the version manifest"
