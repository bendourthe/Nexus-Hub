"""Tests for scripts/check_platform_contract_freshness.py (v3.14.5 Phase 6).

The freshness gate is the release-vs-contract layer: it fails whenever the platform
read-contract was not re-verified for the release being cut (JSON
meta.verified_for_version != the canonical project version). These tests prove it
is GREEN in the steady state (stamp == release version) and RED the moment the
release version advances past the stamp.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.check_platform_contract_freshness import (  # noqa: E402
    CONTRACT_JSON,
    PLUGIN_JSON,
    main,
)


def _stamped_version() -> str:
    meta = json.loads(CONTRACT_JSON.read_text(encoding="utf-8"))["meta"]
    return str(meta["verified_for_version"]).strip()


def test_passes_when_release_version_matches_stamp():
    stamped = _stamped_version()
    assert main(["--version", stamped, "--quiet"]) == 0


def test_passes_on_real_repo_default():
    # During development the plugin.json version equals the stamped value, so the
    # gate must be green with no --version override. This is the invariant that
    # keeps `make validate` / CI passing until a release bump.
    assert main(["--quiet"]) == 0
    # ... and that invariant is exactly "the two are in sync right now".
    plugin_version = str(json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))["version"]).strip()
    assert plugin_version == _stamped_version()


def test_fails_when_release_version_advances(capsys):
    # Simulate the release bump: the plugin version moves ahead of the last
    # verified-for version, so the contract is stale for this release.
    stale_target = _stamped_version() + "-bumped-for-test"
    assert main(["--version", stale_target]) == 1
    out = capsys.readouterr().out
    assert "STALE" in out
    assert "governance step 4" in out


def test_fails_on_empty_version_override(capsys):
    # An explicit empty --version cannot resolve a canonical version -> fail closed.
    assert main(["--version", "   "]) == 1
    assert "could not resolve" in capsys.readouterr().out
