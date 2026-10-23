"""Contract checks for migrated profiles and report failure evidence."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.ci import reporting
from scripts.ci.profiles import PROFILES

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("suffix", ["", "\nquoted \"value\" \u6f22"] )
def test_report_metadata_names_host_and_direct_execution_and_redacts_generic_keys(monkeypatch, tmp_path, suffix):
    value = "-".join(("private", "signing", "fixture", "2940"))  # noqa: FLY002 - assembled secret fixture
    value += suffix
    monkeypatch.setenv("PRIVATE_SIGNING_KEY", value)
    run = reporting.RunResult("full", "windows", started_at=value)
    path = reporting.write_metadata(run, tmp_path)
    raw = path.read_text(encoding="utf-8")
    metadata = json.loads(raw)
    assert metadata["host"]
    assert "direct process" in metadata["shell"]
    assert value not in raw
    assert metadata["started_at"] == "[REDACTED]"
    assert reporting.redact("failed " + value) == "failed [REDACTED]"


def test_windows_core_is_required_and_selects_current_edition():
    floor = next(group for group in PROFILES["platform"] if group.name == "windows-installer")
    validators = next(group for group in PROFILES["platform"] if group.name == "windows-validators")
    core = next(group for group in PROFILES["platform"] if group.name == "windows-installer-core")
    assert len(floor.commands) == 1
    assert len(validators.commands) == 3
    floor_commands = floor.commands + validators.commands
    assert all(command.env.get("NEXUS_TEST_POWERSHELL") == "powershell" for command in floor_commands)
    assert core.commands[0].argv[0] == "pwsh"
    assert not core.commands[0].skip_if_missing
    tests = core.commands[-1]
    assert tests.env["NEXUS_TEST_POWERSHELL"] == "pwsh"
    for path in ("test_native_json_reader.py", "test_native_hook_json.py", "test_native_cli_launcher.py", "test_strict_permissions.py"):
        assert any(arg.endswith(path) for arg in tests.argv)


@pytest.mark.parametrize("monitor", ["claude", "codex", "copilot", "cursor", "gemini"])
def test_monitor_validation_is_owned_by_native_profile(monitor):
    data = yaml.safe_load((ROOT / f".github/workflows/{monitor}-usage-monitor.yml").read_text(encoding="utf-8"))
    steps = data["jobs"]["build-and-test"]["steps"]
    scripts = "\n".join(step.get("run", "") for step in steps)
    assert f"--only {monitor}-usage-monitor" in scripts
    assert "npm run compile" not in scripts and "npm run test:coverage" not in scripts
    group = next(group for group in PROFILES["full"] if group.name == f"{monitor}-usage-monitor")
    assert all(command.cwd == f"extensions/{monitor}-usage-monitor" for command in group.commands)
    commands = [list(command.argv) for command in group.commands]
    assert any("compile" in argv for argv in commands)
    assert any("test:coverage" in argv for argv in commands)
    assert (any("verify:package" in argv for argv in commands)) == (monitor in {"copilot", "cursor"})
    assert any(step.get("if") == "always()" and step.get("uses", "").startswith("actions/upload-artifact@") and step["with"]["retention-days"] == 7 for step in steps)


def test_every_migrated_native_call_resolves_groups():
    paths = [ROOT / ".github/workflows" / name for name in ("ci.yml", "doc-colocation.yml", "presentify-extractor.yml", "nexus-memory.yml", "code-search.yml", *(f"{monitor}-usage-monitor.yml" for monitor in ("claude", "codex", "copilot", "cursor", "gemini")))]
    count = 0
    for path in paths:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        for job in data["jobs"].values():
            scripts = "\n".join(step.get("run", "") for step in job.get("steps", []))
            for profile, selected in re.findall(r"scripts/ci/run.py --profile (\w+) --only ([\w,${} .-]+?)(?: --|$)", scripts, re.MULTILINE):
                if "${{" in selected:
                    for include in job["strategy"]["matrix"]["include"]:
                        assert include["group"] in {group.name for group in PROFILES[profile]}
                else:
                    assert set(selected.strip().split(",")) <= {group.name for group in PROFILES[profile]}
                count += 1
    assert count >= 20


def test_presentify_required_aggregate_keeps_unfiltered_context_and_validates_selection():
    data = yaml.safe_load((ROOT / ".github/workflows/presentify-extractor.yml").read_text(encoding="utf-8"))
    event = data.get("on", data.get(True))
    assert "schedule" not in event and "paths" not in event["pull_request"]
    gate = data["jobs"]["verify"]
    assert gate["if"] == "always()"
    assert set(gate["needs"]) == {"detect", "extractor-tests", "render"}
    assert "needs.detect.outputs.presentify" in json.dumps(gate)


@pytest.mark.parametrize("name", ["code-search", "memory"])
def test_offline_profiles_keep_digest_network_boundary_and_package_constraints(name):
    group = next(group for group in PROFILES["full"] if group.name == name + "-offline")
    build, execute = group.commands
    assert build.platforms == execute.platforms == ("linux",)
    assert list(execute.argv)[list(execute.argv).index("--network") + 1] == "none"
    assert "then exit 1" in execute.argv[-1]
    dockerfile = (ROOT / f"scripts/ci/{name}-offline.Dockerfile").read_text(encoding="utf-8")
    assert re.search(r"FROM python:3\.11-slim@sha256:[a-f0-9]{64}", dockerfile)
    assert "requirements-py311.txt" in dockerfile and "PIP_CONSTRAINT" in dockerfile


@pytest.mark.parametrize("build,profile,accepted", [("success", "success", True), ("success", "skipped", False), ("failure", "skipped", False), ("cancelled", "success", False), ("success", "unknown", False)])
def test_cursor_required_gate_rejects_every_unqualified_result(build, profile, accepted):
    bash = shutil.which("bash")
    assert bash, "Bash is required for the workflow gate control"
    data = yaml.safe_load((ROOT / ".github/workflows/cursor-usage-monitor.yml").read_text(encoding="utf-8"))
    gate = data["jobs"]["cursor-required"]
    assert gate["if"] == "always()" and set(gate["needs"]) == {"build-and-test", "e2e-cursor-profile"}
    result = subprocess.run([bash, "-c", gate["steps"][0]["run"]], env={**os.environ, "R_build": build, "R_profile": profile}, capture_output=True, timeout=10, check=False)
    assert (result.returncode == 0) is accepted


def test_bootstrap_jobs_provision_node_before_native_profile_without_cache():
    data = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    for job in ("bootstrap", "bootstrap-windows"):
        steps = data["jobs"][job]["steps"]
        setup = next(index for index, step in enumerate(steps) if step.get("uses", "").startswith("actions/setup-node@"))
        execute = next(index for index, step in enumerate(steps) if step.get("name") == "Repository-native bootstrap-smoke profile")
        assert setup < execute
        assert steps[setup]["with"] == {"node-version": "22"}


@pytest.mark.parametrize("detect,selected,extract,render,accepted", [
    ("success", "true", "success", "success", True),
    ("success", "false", "skipped", "skipped", True),
    ("success", "false", "success", "skipped", True),
    ("success", "false", "skipped", "success", True),
    ("failure", "false", "skipped", "skipped", False),
    ("cancelled", "true", "success", "success", False),
    ("skipped", "false", "skipped", "skipped", False),
    ("success", "", "success", "success", False),
    ("success", "unknown", "success", "success", False),
    *[("success", "true", bad, "success", False) for bad in ("failure", "cancelled", "skipped", "unknown")],
    *[("success", "true", "success", bad, False) for bad in ("failure", "cancelled", "skipped", "unknown")],
    *[("success", "false", bad, "skipped", False) for bad in ("failure", "cancelled", "unknown")],
    *[("success", "false", "skipped", bad, False) for bad in ("failure", "cancelled", "unknown")],
])
def test_presentify_gate_executes_selected_result_contract(detect, selected, extract, render, accepted):
    bash = shutil.which("bash")
    assert bash, "Bash is required for the aggregate gate control"
    gate = yaml.safe_load((ROOT / ".github/workflows/presentify-extractor.yml").read_text(encoding="utf-8"))["jobs"]["verify"]
    result = subprocess.run([bash, "-c", gate["steps"][0]["run"]], env={**os.environ, "R_detect": detect, "R_selected": selected, "R_extract": extract, "R_render": render}, capture_output=True, timeout=10, check=False)
    assert (result.returncode == 0) is accepted


@pytest.mark.parametrize("secret", ['"profile"', '"' * 8, "\n" * 8, "\\" * 8, "value\nwith \"quotes\" and \u6f22"])
def test_metadata_redacts_values_without_replacing_json_structure(monkeypatch, tmp_path, secret):
    monkeypatch.setenv("TEST_PRIVATE_KEY", secret)
    result = reporting.RunResult("full", "windows", started_at=secret)
    path = reporting.write_metadata(result, tmp_path, {"tool": secret})
    metadata = json.loads(path.read_text(encoding="utf-8"))
    assert metadata["started_at"] == "[REDACTED]"
    assert metadata["tools"]["tool"] == "[REDACTED]"
    assert "profile" in metadata and "platform" in metadata
