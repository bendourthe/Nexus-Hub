"""Cross-platform materialization tests for organization knowledge bundles."""

from __future__ import annotations

import json
import shutil
import stat
from pathlib import Path

import pytest

from scripts.lib.integrations import INTEGRATION_REGISTRY
from scripts.lib.integrations import org_knowledge as org
from scripts.lib.integrations.base import InstallContext
from scripts.lib.integrations.manifest import InstallManifest

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_BUNDLE = REPO_ROOT / "configs" / "examples" / "org-bundle-example"
REPRESENTATIVE_PLATFORMS = ("claude", "codex", "cursor", "gemini", "opencode", "aider")


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


def _ctx(target: Path, manifest: InstallManifest, **overrides: object) -> InstallContext:
    values = {
        "repo_root": REPO_ROOT,
        "target_root": target,
        "scope": "workspace",
        "overwrite": False,
        "dry_run": False,
        "manifest": manifest,
        "template_vars": {"PROJECT_NAME": "org-test"},
    }
    values.update(overrides)
    return InstallContext(**values)


def _instruction_path(key: str, target: Path) -> Path:
    integration = INTEGRATION_REGISTRY[key]
    if key == "cursor":
        return target / integration.config["instruction_file"]
    directory = integration.config.get(
        "instruction_workspace_dir", integration.config.get("workspace_dir")
    )
    return target / str(directory or "") / integration.config["instruction_file"]


def _remove_tree(path: Path) -> None:
    """Remove a copied tree after clearing Windows read-only attributes."""

    for descendant in sorted(path.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        mode = stat.S_IRWXU if descendant.is_dir() else stat.S_IWRITE | stat.S_IREAD
        descendant.chmod(mode)
    path.chmod(stat.S_IRWXU)
    shutil.rmtree(path)


@pytest.fixture
def connected_bundle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    home = tmp_path / "nexus-home"
    bundle = tmp_path / "bundle"
    shutil.copytree(EXAMPLE_BUNDLE, bundle)
    _connect(home, bundle)
    monkeypatch.setenv("NEXUS_HUB_HOME", str(home))
    return home, bundle


@pytest.mark.parametrize("key", REPRESENTATIVE_PLATFORMS)
def test_workspace_install_materializes_org_block_after_nexus_and_is_idempotent(
    key: str,
    connected_bundle: tuple[Path, Path],
    tmp_path: Path,
) -> None:
    _, bundle = connected_bundle
    target = tmp_path / key
    target.mkdir()
    manifest = InstallManifest()
    integration = INTEGRATION_REGISTRY[key]

    integration.install(_ctx(target, manifest, instruction_only=True))
    instruction = _instruction_path(key, target)
    text = instruction.read_text(encoding="utf-8")

    assert text.count(org.ORG_START_MARKER) == 1
    assert text.count(org.ORG_END_MARKER) == 1
    assert text.index(org.ORG_START_MARKER) > text.index(org.NEXUS_END_MARKER)
    assert "## Organization Standards (Example Organization)" in text
    assert "These organization standards take precedence" in text
    assert f"On-demand organization references: `{bundle / 'references'}`." in text
    assert str(instruction) in manifest.shared_for(key)

    second = integration.install(_ctx(target, manifest, instruction_only=True))
    org_actions = [
        action
        for action in second.files
        if Path(action.path) == instruction or "org" in Path(action.path).parts
    ]
    assert org_actions
    assert all(action.action in {"unchanged", "kept"} for action in org_actions)
    assert instruction.read_text(encoding="utf-8").count(org.ORG_START_MARKER) == 1


@pytest.mark.parametrize("key", ("claude", "cursor", "gemini", "opencode"))
def test_rules_are_projected_under_native_org_subtree_and_tracked(
    key: str,
    connected_bundle: tuple[Path, Path],
    tmp_path: Path,
) -> None:
    target = tmp_path / key
    target.mkdir()
    manifest = InstallManifest()
    rules_root = target / INTEGRATION_REGISTRY[key].config["workspace_dir"] / "rules"
    rules_root.mkdir(parents=True)

    INTEGRATION_REGISTRY[key].install(_ctx(target, manifest, instruction_only=True))

    rule = rules_root / "org" / "python" / "code-style.md"
    assert rule.is_file()
    assert str(rule) in manifest.files_for(key)


def test_default_precedence_and_rendered_budget_warning_are_not_truncated(
    connected_bundle: tuple[Path, Path],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, bundle = connected_bundle
    manifest_data = json.loads((bundle / "org.json").read_text(encoding="utf-8"))
    manifest_data.pop("precedence_statement")
    (bundle / "org.json").write_text(json.dumps(manifest_data), encoding="utf-8")
    long_core = "\n".join(f"Rule {number}" for number in range(198)) + "\n"
    (bundle / "core.md").write_text(long_core, encoding="utf-8")
    target = tmp_path / "workspace"
    target.mkdir()

    INTEGRATION_REGISTRY["aider"].install(_ctx(target, InstallManifest()))

    text = (target / "CONVENTIONS.md").read_text(encoding="utf-8")
    assert org.DEFAULT_PRECEDENCE_STATEMENT in text
    assert "Rule 197" in text
    warning = capsys.readouterr().err
    assert warning.count("rendered organization block exceeds") == 1
    assert "content was not truncated" in warning


def test_no_connection_is_silent_unless_verbose(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("NEXUS_HUB_HOME", str(tmp_path / "empty-home"))
    target = tmp_path / "workspace"
    target.mkdir()
    manifest = InstallManifest()
    context = _ctx(target, manifest)

    assert org.seed_org_knowledge("aider", context) == []
    assert capsys.readouterr().err == ""
    context.verbose = True
    assert org.seed_org_knowledge("aider", context) == []
    assert "no connection; skipped" in capsys.readouterr().err


def test_invalid_bundle_warns_once_and_install_continues(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    home = tmp_path / "home"
    bundle = tmp_path / "invalid"
    bundle.mkdir()
    (bundle / "org.json").write_text("{}", encoding="utf-8")
    _connect(home, bundle)
    monkeypatch.setenv("NEXUS_HUB_HOME", str(home))
    target = tmp_path / "workspace"
    target.mkdir()

    result = INTEGRATION_REGISTRY["aider"].install(_ctx(target, InstallManifest()))

    assert (target / "CONVENTIONS.md").is_file()
    assert result.files
    warning_lines = capsys.readouterr().err.splitlines()
    assert len(warning_lines) == 1
    assert "invalid bundle" in warning_lines[0]
    assert org.ORG_START_MARKER not in (target / "CONVENTIONS.md").read_text(encoding="utf-8")


def test_manifest_tracking_failure_does_not_break_materialization(
    connected_bundle: tuple[Path, Path], tmp_path: Path
) -> None:
    instruction = tmp_path / "CONVENTIONS.md"
    instruction.write_text(
        f"{org.NEXUS_END_MARKER}\n",
        encoding="utf-8",
    )

    class FailingManifest:
        def shared_for(self, integration_key: str) -> list[str]:
            return [str(instruction)]

        def files_for(self, integration_key: str) -> list[str]:
            return []

        def track_shared(self, integration_key: str, path: str) -> None:
            raise RuntimeError("manifest unavailable")

    context = _ctx(tmp_path, InstallManifest())
    context.manifest = FailingManifest()

    actions = org.seed_org_knowledge("aider", context)

    assert actions[0].action == "updated"
    assert org.ORG_START_MARKER in instruction.read_text(encoding="utf-8")


def test_dedicated_instruction_rewrite_reappends_org_block(
    connected_bundle: tuple[Path, Path], tmp_path: Path
) -> None:
    target = tmp_path / "workspace"
    target.mkdir()
    manifest = InstallManifest()
    integration = INTEGRATION_REGISTRY["nexus-ai"]

    integration.install(_ctx(target, manifest, overwrite=True))
    instruction = target / ".nexus-ai" / "catalog" / "NEXUS_AI.md"
    first = instruction.read_text(encoding="utf-8")
    assert first.count(org.ORG_START_MARKER) == 1

    integration.install(_ctx(target, manifest, overwrite=True))
    second = instruction.read_text(encoding="utf-8")
    assert second.count(org.ORG_START_MARKER) == 1
    assert second.index(org.ORG_START_MARKER) > second.index("# org-test")


def test_refresh_pruning_then_instruction_only_reseed_restores_claude_org_rules(
    connected_bundle: tuple[Path, Path], tmp_path: Path
) -> None:
    target = tmp_path / "workspace"
    target.mkdir()
    manifest = InstallManifest()
    integration = INTEGRATION_REGISTRY["claude"]
    org_rule = target / ".claude" / "rules" / "org" / "python" / "code-style.md"
    rules_root = target / ".claude" / "rules"
    shutil.copytree(REPO_ROOT / "catalog" / "rules", rules_root)
    integration.install(_ctx(target, manifest, instruction_only=True))
    assert org_rule.is_file()

    _remove_tree(rules_root)
    shutil.copytree(REPO_ROOT / "catalog" / "rules", rules_root)
    assert not org_rule.exists()

    integration.install(_ctx(target, manifest, instruction_only=True))
    assert org_rule.is_file()


def test_installer_registry_calls_follow_claude_rules_refresh_in_both_shells() -> None:
    bash = (REPO_ROOT / "scripts" / "installer.sh").read_text(encoding="utf-8")
    powershell = (REPO_ROOT / "scripts" / "installer.ps1").read_text(encoding="utf-8")

    for body, rules_token, registry_token in (
        (bash, 'safe_folder_copy "$repo_root/catalog/rules"', 'invoke_registry_platform "$repo_root"'),
        (powershell, 'Safe-Folder-Copy -Source "$RepoRoot\\catalog\\rules"', "Invoke-RegistryPlatform -RepoRoot $RepoRoot"),
    ):
        positions = []
        offset = 0
        while True:
            rules = body.find(rules_token, offset)
            if rules < 0:
                break
            registry = body.find(registry_token, rules)
            positions.append((rules, registry))
            offset = rules + len(rules_token)
        assert len(positions) >= 2
        assert all(registry > rules for rules, registry in positions[:2])


def test_runner_threads_quiet_state_into_org_diagnostics() -> None:
    runner = (REPO_ROOT / "scripts" / "lib" / "integrations" / "runner.py").read_text(
        encoding="utf-8"
    )

    assert runner.count("verbose=not args.quiet") == 2


def test_posture_roster_matches_registry_and_unknown_keys_degrade() -> None:
    assert set(org.PLATFORM_POSTURES) == set(INTEGRATION_REGISTRY)
    assert org.platform_posture("future-platform").classification == "advisory (unclassified)"
    rows = org.platform_posture_rows(["future-platform"])
    assert rows == [
        (
            "future-platform",
            "advisory (unclassified)",
            "No verified platform precedence mechanism is recorded; treat the projection as guidance only.",
        )
    ]
