"""Lifecycle coverage for organization knowledge materialization."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from scripts import nexus_hub_cli as cli
from scripts.lib.integrations import INTEGRATION_REGISTRY
from scripts.lib.integrations import org_knowledge as org
from scripts.lib.integrations.base import InstallContext
from scripts.lib.integrations.lifecycle import doctor, repair
from scripts.lib.integrations.manifest import InstallManifest

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_BUNDLE = REPO_ROOT / "configs" / "examples" / "org-bundle-example"


def _connect(home: Path, bundle: Path) -> None:
    connection = home / "org" / "connection.json"
    connection.parent.mkdir(parents=True, exist_ok=True)
    connection.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_type": "dir",
                "source": str(bundle),
                "branch": None,
                "connected_at": "2026-08-16T00:00:00Z",
                "last_sync": "2026-08-16T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )


def _context(target: Path, manifest: InstallManifest) -> InstallContext:
    return InstallContext(
        repo_root=REPO_ROOT,
        target_root=target,
        scope="workspace",
        overwrite=True,
        dry_run=False,
        manifest=manifest,
        template_vars={"PROJECT_NAME": "org-lifecycle"},
        instruction_only=True,
    )


def _install(key: str, context: InstallContext) -> None:
    result = INTEGRATION_REGISTRY[key].install(context)
    context.manifest.record_actions(key, result.files)


@pytest.fixture
def connected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path]:
    home = tmp_path / "nexus-home"
    bundle = tmp_path / "bundle"
    shutil.copytree(EXAMPLE_BUNDLE, bundle)
    _connect(home, bundle)
    monkeypatch.setenv("NEXUS_HUB_HOME", str(home))
    return home, bundle


def test_doctor_reports_vanished_connected_source_without_error(
    connected: tuple[Path, Path], tmp_path: Path
) -> None:
    _, bundle = connected
    target = tmp_path / "workspace"
    target.mkdir()
    manifest = InstallManifest()
    _install("aider", _context(target, manifest))
    bundle.rename(bundle.with_name("vanished-bundle"))

    report = doctor(manifest)

    assert report.has_issues()
    finding = next(
        item for item in report.findings if item.integration_key == "org-knowledge"
    )
    assert finding.diagnostic == "missing"
    assert finding.path == str(bundle)
    assert finding.detail == "connected organization source is unreachable"


def test_repair_restores_org_block_and_preserves_text_outside_markers(
    connected: tuple[Path, Path], tmp_path: Path
) -> None:
    target = tmp_path / "workspace"
    target.mkdir()
    manifest = InstallManifest()
    context = _context(target, manifest)
    _install("aider", context)
    instruction = target / "CONVENTIONS.md"
    text = instruction.read_text(encoding="utf-8")
    instruction.write_text(
        "User preface.\n\n"
        + text.replace("Preserve user data", "Delete user data")
        + "\n\nUser appendix.\n",
        encoding="utf-8",
    )

    before = doctor(manifest)
    result = repair(context)

    restored = instruction.read_text(encoding="utf-8")
    assert before.has_issues()
    assert result.files
    assert "Preserve user data" in restored
    assert "Delete user data" not in restored
    assert restored.startswith("User preface.")
    assert restored.rstrip().endswith("User appendix.")
    assert not doctor(manifest).has_issues()


def test_teardown_removes_both_owned_blocks_but_preserves_user_text(
    connected: tuple[Path, Path], tmp_path: Path
) -> None:
    target = tmp_path / "workspace"
    target.mkdir()
    manifest = InstallManifest()
    context = _context(target, manifest)
    _install("aider", context)
    instruction = target / "CONVENTIONS.md"
    instruction.write_text(
        "User-owned heading.\n\n" + instruction.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    INTEGRATION_REGISTRY["aider"].teardown(context)

    remaining = instruction.read_text(encoding="utf-8")
    assert remaining.strip() == "User-owned heading."
    assert org.NEXUS_END_MARKER not in remaining
    assert org.ORG_START_MARKER not in remaining
    assert manifest.org_shared_for("aider") == []


def test_disconnect_cleans_global_manifest_owned_artifacts_immediately(
    connected: tuple[Path, Path], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    home, _ = connected
    target = tmp_path / "global-target"
    target.mkdir()
    manifest = InstallManifest()
    context = _context(target, manifest)
    _install("aider", context)
    manifest.save(home / "install-manifest.json")
    instruction = target / "CONVENTIONS.md"

    returncode = cli.cmd_org(["disconnect", "--yes"])

    captured = capsys.readouterr()
    reloaded = InstallManifest.load(home / "install-manifest.json")
    text = instruction.read_text(encoding="utf-8")
    assert returncode == 0, captured.err
    assert "Removed 1 organization artifact" in captured.out
    assert org.ORG_START_MARKER not in text
    assert org.NEXUS_END_MARKER in text
    assert reloaded.all_org_keys() == []


def test_disconnect_then_workspace_repair_leaves_zero_org_residue(
    connected: tuple[Path, Path], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "workspace"
    target.mkdir()
    rules_root = target / ".cursor" / "rules"
    rules_root.mkdir(parents=True)
    manifest = InstallManifest()
    context = _context(target, manifest)
    _install("cursor", context)
    instruction = target / "AGENTS.md"
    org_rules = rules_root / "org"
    assert org_rules.is_dir()

    assert cli.cmd_org(["disconnect", "--yes"]) == 0
    capsys.readouterr()
    result = repair(context)

    assert any(action.action == "removed" for action in result.files)
    assert org.ORG_START_MARKER not in instruction.read_text(encoding="utf-8")
    assert not org_rules.exists()
    assert manifest.all_org_keys() == []
    assert not doctor(manifest).has_issues()


def test_preexisting_org_rules_that_are_kept_are_never_adopted_or_removed(
    connected: tuple[Path, Path], tmp_path: Path
) -> None:
    target = tmp_path / "workspace"
    target.mkdir()
    user_rule = target / ".cursor" / "rules" / "org" / "user-owned.md"
    user_rule.parent.mkdir(parents=True)
    user_rule.write_text("User-owned organization rule.\n", encoding="utf-8")
    manifest = InstallManifest()
    context = _context(target, manifest)

    _install("cursor", context)
    INTEGRATION_REGISTRY["cursor"].teardown(context)

    assert user_rule.read_text(encoding="utf-8") == "User-owned organization rule.\n"
    assert manifest.org_files_for("cursor") == []


def test_sync_source_change_is_diagnosed_and_repaired_for_two_platforms(
    connected: tuple[Path, Path], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    home, bundle = connected
    target = tmp_path / "workspace"
    target.mkdir()
    manifest = InstallManifest()
    context = _context(target, manifest)
    for key in ("aider", "cursor"):
        _install(key, context)

    core = bundle / "core.md"
    core.write_text(
        core.read_text(encoding="utf-8") + "\nAll releases require an audit note.\n",
        encoding="utf-8",
    )
    assert cli.cmd_org(["sync"]) == 0
    capsys.readouterr()

    drifted = doctor(manifest)
    repair(context)

    assert {
        finding.integration_key
        for finding in drifted.findings
        if finding.diagnostic == "drifted"
    } >= {"aider", "cursor"}
    assert "All releases require an audit note." in (
        target / "CONVENTIONS.md"
    ).read_text(encoding="utf-8")
    assert "All releases require an audit note." in (
        target / "AGENTS.md"
    ).read_text(encoding="utf-8")
    assert not doctor(manifest).has_issues()
    assert (home / "org" / "connection.json").is_file()


def test_upgrade_reuses_installers_that_reach_registry_dispatcher() -> None:
    cli_source = (REPO_ROOT / "scripts" / "nexus_hub_cli.py").read_text(
        encoding="utf-8"
    )
    bash = (REPO_ROOT / "scripts" / "installer.sh").read_text(encoding="utf-8")
    powershell = (REPO_ROOT / "scripts" / "installer.ps1").read_text(
        encoding="utf-8"
    )

    # v4.7.0: upgrade passes the target ref to the bootstrap on a pinned install,
    # so the pin is the call itself, not its argument list.
    assert "return run_bootstrap(" in cli_source
    assert "invoke_registry_platform" in bash
    assert "Invoke-RegistryPlatform" in powershell


def test_org_guide_is_linked_and_carries_the_capability_gate_contract() -> None:
    guide_path = REPO_ROOT / "guides" / "ORG_KNOWLEDGE_LAYER.md"
    guide = guide_path.read_text(encoding="utf-8")
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")

    for label in ("Activation:", "Validation:", "Rollback:", "Authority:", "Docs:"):
        assert f"**{label}**" in guide
    assert "guides/ORG_KNOWLEDGE_LAYER.md" in readme
    assert "guides/ORG_KNOWLEDGE_LAYER.md" in agents
    assert (REPO_ROOT / "configs" / "README.md").is_file()
    assert (
        REPO_ROOT
        / "catalog"
        / "skills"
        / "workflow"
        / "org-standards-authoring"
        / "references"
        / "enforcement-escalation.md"
    ).is_file()
