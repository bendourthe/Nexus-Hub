"""Regression contract for the retired v3.17.0 autonomy feature."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

RETIRED_PATHS = (
    ".github/workflows/autonomy-security.yml",
    "catalog/hooks/autonomy-expiry.ps1",
    "catalog/hooks/autonomy-expiry.sh",
    "catalog/hooks/autonomy-guard.ps1",
    "catalog/hooks/autonomy-guard.sh",
    "catalog/hooks/tests/test_autonomy_expiry.py",
    "catalog/hooks/tests/test_autonomy_guard.py",
    "extensions/claude-usage-monitor/src/autonomyStatus.ts",
    "extensions/claude-usage-monitor/src/autonomyStatusBar.ts",
    "extensions/claude-usage-monitor/test/autonomyStatus.test.ts",
    "extensions/codex-usage-monitor/src/autonomyStatus.ts",
    "extensions/codex-usage-monitor/src/autonomyStatusBar.ts",
    "extensions/codex-usage-monitor/test/autonomyStatus.test.ts",
    "scripts/lib/autonomy.py",
    "scripts/lib/autonomy_cli.py",
    "tests/integrations/test_autonomy_descriptors.py",
    "tests/test_autonomy.py",
    "tests/test_autonomy_cli.py",
)


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_retired_autonomy_runtime_files_are_absent() -> None:
    remaining = [path for path in RETIRED_PATHS if (REPO_ROOT / path).exists()]
    assert remaining == []


def test_public_cli_and_usage_monitors_do_not_expose_autonomy() -> None:
    for relative_path in (
        "scripts/nexus_hub_cli.py",
        "extensions/claude-usage-monitor/package.json",
        "extensions/claude-usage-monitor/src/extension.ts",
        "extensions/claude-usage-monitor/vitest.config.mts",
        "extensions/codex-usage-monitor/package.json",
        "extensions/codex-usage-monitor/src/extension.ts",
        "extensions/codex-usage-monitor/vitest.config.mts",
    ):
        assert "autonom" not in _read(relative_path).lower(), relative_path


def test_integrations_do_not_publish_autonomy_descriptors() -> None:
    integration_root = REPO_ROOT / "scripts" / "lib" / "integrations"
    offenders = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in integration_root.glob("*.py")
        if "autonom" in path.read_text(encoding="utf-8").lower()
    ]
    assert offenders == []


def test_installed_hook_contract_has_no_autonomy_handlers() -> None:
    settings = json.loads(_read("catalog/hooks/settings.json"))
    assert "autonom" not in json.dumps(settings).lower()
    assert "autonom" not in _read("MANIFEST.sha256").lower()


def test_active_policy_docs_do_not_advertise_retired_autonomy() -> None:
    contracts = json.loads(_read("docs/policy/platform-read-contracts.json"))
    assert "autonomy_levers" not in contracts
    assert "## Time-Bounded Agent Autonomy" not in _read("AGENTS.md")
    assert "## Time-Bounded Autonomy Roster" not in _read("docs/permissions-research.md")
    assert "## Autonomy lever verification" not in _read(
        "docs/policy/platform-read-contracts.md"
    )
