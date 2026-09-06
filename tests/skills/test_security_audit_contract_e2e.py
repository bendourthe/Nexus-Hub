"""Fixture-driven end-to-end contract tests for the local security-audit workflow."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from scripts.lib.integrations._catalog_adapters import flatten_skills
from scripts.lib.integrations.base import InstallContext
from scripts.lib.integrations.manifest import InstallManifest

_ROOT = Path(__file__).resolve().parents[2]
_CASES = _ROOT / "tests" / "fixtures" / "security-audit" / "cases.json"
_GATE_PATH = (
    _ROOT
    / "catalog"
    / "skills"
    / "code-review"
    / "security-review"
    / "scripts"
    / "closure-gate.py"
)
_PRESET = _ROOT / "catalog" / "skills" / "workflow" / "agent-presets" / "SKILL.md"
_REVIEWER = _ROOT / "catalog" / "agents" / "security-reviewer.md"
_WORKFLOWS = _ROOT / "data" / "workflows.json"
_RECEIPT_STATES = (
    "RAN",
    "NOT_APPLICABLE",
    "UNAVAILABLE",
    "FAILED",
    "DECLINED",
)
_REQUIRED_CASE_IDS = (
    "applicable-scanner-omitted",
    "unavailable-tool-reported",
    "command-failure-reported",
    "declined-scanner-reported",
    "forged-not-applicable",
    "before-after-target-mismatch",
    "ruleset-drift",
    "fixed-plus-unresolved-new-finding",
    "same-fixer-verifier",
    "independent-clean-verifier",
    "clean-no-remediation",
    "schema-v1-legacy",
)


def _load_gate():
    spec = importlib.util.spec_from_file_location("closure_gate_e2e", _GATE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gate = _load_gate()


def _cases() -> list[dict]:
    payload = json.loads(_CASES.read_text(encoding="utf-8"))
    return payload["cases"]


def _exit_for(record: dict) -> tuple[int, dict | None]:
    try:
        result = gate.evaluate_review_record(record)
    except gate.RecordError:
        return gate.EXIT_USAGE_ERROR, None
    if result["failure_count"]:
        return gate.EXIT_CLOSURE_FAILURE, result
    return gate.EXIT_CLEAN, result


def test_fixture_catalog_covers_required_adversarial_cases() -> None:
    ids = [case["id"] for case in _cases()]
    assert ids == list(_REQUIRED_CASE_IDS)
    assert all(case["never_execute_commands"] is True for case in _cases())


def test_fixture_commands_are_never_executed() -> None:
    commands = []
    for case in _cases():
        for receipt in case["record"].get("scanner_receipts", []):
            command = receipt.get("command")
            if command:
                commands.append(command)
    assert commands, "fixtures must include illustrative command strings"
    for command in commands:
        assert isinstance(command, str)
        assert "http://" not in command
        assert "https://" not in command


def test_every_fixture_matches_expected_closure_result() -> None:
    for case in _cases():
        exit_code, result = _exit_for(case["record"])
        assert exit_code == case["expect"]["exit_code"], case["id"]
        expected_diffs = case["expect"]["diffs"]
        if exit_code == gate.EXIT_USAGE_ERROR:
            assert result is None, case["id"]
            continue
        assert result is not None, case["id"]
        for name, expected_ids in expected_diffs.items():
            assert result["diffs"][name] == expected_ids, case["id"]
        if exit_code == gate.EXIT_CLEAN:
            assert result["status"] == "clean", case["id"]
            assert result["failure_count"] == 0, case["id"]
        else:
            for name, actual_ids in result["diffs"].items():
                if name in expected_diffs:
                    continue
                assert actual_ids == [], f"{case['id']} extra diff {name}: {actual_ids}"


def test_preset_and_reviewer_name_receipt_states_and_role_separation() -> None:
    preset = _PRESET.read_text(encoding="utf-8")
    reviewer = _REVIEWER.read_text(encoding="utf-8")
    for state in _RECEIPT_STATES:
        assert state in preset
    assert "complete" in preset and "degraded" in preset
    assert "does not apply patches" in preset
    assert "This role is read-only" in reviewer
    assert "You do not apply patches" in reviewer
    assert "independent verifier receipt" in reviewer


def test_recursive_install_delivers_security_audit_assets(tmp_path: Path) -> None:
    destination = tmp_path / "installed" / "skills"
    context = InstallContext(
        repo_root=_ROOT,
        target_root=tmp_path,
        scope="workspace",
        overwrite=False,
        dry_run=False,
        manifest=InstallManifest(),
    )
    actions = flatten_skills(
        context,
        "security-audit-e2e",
        _ROOT / "catalog" / "skills",
        destination,
    )
    assert actions
    assert (destination / "security-review" / "scripts" / "closure-gate.py").is_file()
    assert (
        destination / "security-review" / "references" / "local-scanner-recipes.md"
    ).is_file()
    assert (destination / "agent-presets" / "evals" / "trigger-cases.json").is_file()
    assert _REVIEWER.is_file()
    assert _WORKFLOWS.is_file()
    workflows = json.loads(_WORKFLOWS.read_text(encoding="utf-8"))
    matches = [
        item["id"] for item in workflows["workflows"] if item["id"] == "security-audit"
    ]
    assert matches == ["security-audit"]


def test_closure_gate_cli_does_not_spawn_scanner_commands(tmp_path: Path) -> None:
    case = next(item for item in _cases() if item["id"] == "clean-no-remediation")
    record_path = tmp_path / "record.json"
    record_path.write_text(json.dumps(case["record"]), encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, str(_GATE_PATH), str(record_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["status"] == "clean"
