"""All supported adapters carry one reporting contract and complete resources."""

import importlib.util
import subprocess
import sys

import pytest

from scripts.lib.integrations import INTEGRATION_REGISTRY, get
from scripts.lib.integrations.base import MarkdownIntegration
from scripts.lib.integrations.reporting import RESOURCES, audit_reporting
from scripts.lib.integrations.result import FileAction, WriteResult


@pytest.mark.parametrize("key", sorted(INTEGRATION_REGISTRY))
def test_every_platform_has_reporting_instructions_or_native_skill(repo_root, key):
    integration = get(key)
    template = integration.config.get("instruction_template")
    if template:
        rendered = MarkdownIntegration._resolve_includes(repo_root / template)
        assert "- Progress:" in rendered, key
        assert "implement-phase/scripts/status_report.py" in rendered, key
        assert "progress-reporting.md" in rendered and "status-formats.md" in rendered, key
    else:
        assert key == "hermes" and integration.config["skills_subdir"] == "skills"


@pytest.mark.parametrize("key", [key for key in INTEGRATION_REGISTRY if key not in ("aider", "copilot")])
def test_installed_renderer_runs_with_identical_output_and_repairs_missing_resources(install_ctx, key):
    ctx = install_ctx
    ctx.selection = {"resolved": {"skills": ["implement-phase"], "commands": ["status", "implement", "update"], "agents": []}}
    get(key).install(ctx)
    scripts = list(ctx.target_root.rglob("implement-phase/scripts/status_report.py"))
    assert scripts, f"{key}: reporting renderer not delivered"
    source = ctx.repo_root / "catalog/skills/workflow/implement-phase"
    for script in scripts:
        folder = script.parent.parent
        for relative in RESOURCES:
            assert (folder / relative).read_bytes() == (source / relative).read_bytes(), (key, relative)
        command = [sys.executable, str(script), "--input", str(folder / "references/status-snapshot.json"), "--event", "request"]
        installed = subprocess.run(command, capture_output=True, text=True, check=False)
        canonical = subprocess.run([sys.executable, str(source / "scripts/status_report.py"), "--input", str(source / "references/status-snapshot.json")], capture_output=True, text=True, check=False)
        assert installed.returncode == canonical.returncode == 0, installed.stderr
        assert installed.stdout == canonical.stdout
    # Exercise the real adapter again after a bundled file disappears.
    victim = scripts[0].parent.parent / "references/status-formats.md"
    victim.unlink()
    get(key).install(ctx)
    assert victim.read_bytes() == (source / "references/status-formats.md").read_bytes()


def test_install_reports_legacy_codex_shadow_without_overwriting_it(install_ctx):
    legacy = install_ctx.target_root / ".codex/skills/implement-phase"
    legacy.mkdir(parents=True)
    skill = legacy / "SKILL.md"
    skill.write_text("old user-preserved copy", encoding="utf-8")
    install_ctx.selection = {"resolved": {"skills": ["implement-phase"], "commands": ["status"], "agents": []}}
    result = get("codex").install(install_ctx)
    assert any("reporting parity NOT verified" in note and ".codex" in note for note in result.notes)
    assert skill.read_text(encoding="utf-8") == "old user-preserved copy"


def test_incomplete_bundle_is_detected_and_dry_run_reads_nothing(install_ctx):
    folder = install_ctx.target_root / "skills/implement-phase"
    folder.mkdir(parents=True)
    result = WriteResult(files=[FileAction(str(folder), "created")])
    assert len(audit_reporting("claude", install_ctx, result)) == len(RESOURCES)
    install_ctx.dry_run = True
    assert audit_reporting("claude", install_ctx, result) == []


def test_diagnostic_resource_inventory_matches_runtime_auditor(repo_root):
    path = repo_root / "catalog/skills/workflow/implement-phase/scripts/status_report.py"
    spec = importlib.util.spec_from_file_location("runtime_report", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert RESOURCES == module.RESOURCES
