"""Contract tests for v3.17.0 Phase 2 autonomy capability descriptors."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import ClassVar

from scripts.lib.integrations import INTEGRATION_REGISTRY
from scripts.lib.integrations.base import IntegrationBase


class _NoAutonomy(IntegrationBase):
    key = "test-no-autonomy"


class _UnverifiedAutonomy(IntegrationBase):
    key = "test-unverified-autonomy"
    config: ClassVar[dict] = {"autonomy": {"verified": False}}


class _VerifiedAutonomy(IntegrationBase):
    key = "test-verified-autonomy"
    config: ClassVar[dict] = {
        "autonomy": {"verified": True, "config_file": "settings.json"}
    }


def _contract(repo_root: Path) -> dict:
    path = repo_root / "docs" / "policy" / "platform-read-contracts.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_autonomy_accessor_gates_absent_and_unverified_descriptors() -> None:
    assert _NoAutonomy().autonomy_descriptor is None
    assert _UnverifiedAutonomy().autonomy_descriptor is None
    assert _VerifiedAutonomy().autonomy_descriptor == {
        "verified": True,
        "config_file": "settings.json",
    }


def test_every_registered_integration_has_an_autonomy_verdict(repo_root: Path) -> None:
    platforms = _contract(repo_root)["autonomy_levers"]["platforms"]
    assert set(platforms) == set(INTEGRATION_REGISTRY)
    for key, verdict in platforms.items():
        assert verdict["verdict"] in {"MATCH", "DRIFT", "UNVERIFIED"}, key
        assert verdict["verified_on"], key
        assert verdict["source_url"].startswith("https://"), key
        assert verdict["note"], key


def test_verified_descriptors_are_structurally_complete_and_match_contract(
    repo_root: Path,
) -> None:
    platforms = _contract(repo_root)["autonomy_levers"]["platforms"]
    match_keys = {key for key, value in platforms.items() if value["verdict"] == "MATCH"}
    descriptor_keys = {
        key
        for key, integration in INTEGRATION_REGISTRY.items()
        if integration.autonomy_descriptor is not None
    }
    assert descriptor_keys == match_keys

    for key in sorted(descriptor_keys):
        descriptor = INTEGRATION_REGISTRY[key].autonomy_descriptor
        assert descriptor is not None
        assert descriptor["config_file"], key
        assert descriptor["scope"] in {"project", "global"}, key
        assert descriptor["format"] in {"json", "jsonc", "toml"}, key
        assert descriptor["verified"] is True, key
        assert descriptor["key_paths"], key
        assert all(isinstance(path, str) and path for path in descriptor["key_paths"]), key
        assert isinstance(descriptor["intermediate_supported"], bool), key

        tiers = descriptor["tiers"]
        assert isinstance(tiers["full"], dict) and tiers["full"], key
        if descriptor["intermediate_supported"]:
            assert isinstance(tiers["edits_only"], dict) and tiers["edits_only"], key
        else:
            assert tiers["edits_only"] is None, key


def test_platform_contract_freshness_gate_still_passes(repo_root: Path) -> None:
    plugin = json.loads(
        (repo_root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    result = subprocess.run(
        [
            sys.executable,
            "scripts/check_platform_contract_freshness.py",
            "--version",
            plugin["version"],
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
