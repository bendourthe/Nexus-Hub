"""Tests for the security-review deterministic closure gate."""

from __future__ import annotations

import ast
import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from scripts.lib.integrations._catalog_adapters import flatten_skills
from scripts.lib.integrations.base import InstallContext
from scripts.lib.integrations.manifest import InstallManifest

_ROOT = Path(__file__).resolve().parents[2]
_BUNDLE = _ROOT / "catalog" / "skills" / "code-review" / "security-review"
_GATE_PATH = _BUNDLE / "scripts" / "closure-gate.py"
_REFERENCE_PATH = _BUNDLE / "references" / "closure-gate-review-record.md"
_SKILL_PATH = _BUNDLE / "SKILL.md"
_EVAL_SKILL_PATH = (
    _ROOT / "catalog" / "skills" / "workflow" / "skill-eval-loop" / "SKILL.md"
)
_GAPS_SKILL_PATH = (
    _ROOT / "catalog" / "skills" / "workflow" / "known-gaps-tracker" / "SKILL.md"
)


def _load_gate():
    spec = importlib.util.spec_from_file_location("closure_gate", _GATE_PATH)
    assert spec and spec.loader, f"cannot load {_GATE_PATH}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gate = _load_gate()


def _clean_record() -> dict:
    return {
        "schema_version": 1,
        "components": [
            {
                "id": "api",
                "status": "COVERED",
                "review_action_ids": ["RA-1"],
            },
            {
                "id": "generated-client",
                "status": "OMITTED",
                "review_action_ids": [],
                "caveat": "Generated code is outside the declared scope.",
            },
        ],
        "review_actions": [
            {
                "id": "RA-1",
                "component_id": "api",
                "action": "Traced request inputs to authorization checks.",
                "result": "One surviving finding.",
                "evidence": "trace:api-auth",
            }
        ],
        "findings": [
            {
                "id": "F-confirmed",
                "disposition": "confirmed",
                "evidence_fact_ids": ["FACT-1"],
            },
            {
                "id": "F-pending",
                "disposition": "needs-live-validation",
                "pending_validation": {
                    "safe_test": "Send one unauthorized read request.",
                    "expected_vulnerable": "The response returns the target record.",
                    "expected_safe": "The response is 403 or 404.",
                    "potential_severity": "P1 HIGH",
                },
            },
            {"id": "F-corrected", "disposition": "corrected"},
            {
                "id": "F-rejected",
                "disposition": "rejected",
                "rejection_record": {
                    "counter_hypothesis": "All actual routes enforce ownership.",
                    "actual_input_sources": ["path", "body"],
                    "routes": [
                        {
                            "source": "path",
                            "result": "observed-safe",
                            "evidence": "test:path-owner-guard",
                        },
                        {
                            "source": "body",
                            "result": "observed-blocked",
                            "evidence": "trace:body-id-ignored",
                        },
                    ],
                    "reachability_claim": False,
                },
            },
        ],
        "facts": [{"id": "FACT-1", "evidence": "artifact:F-confirmed.txt"}],
        "report_claims": [{"id": "CLAIM-1", "fact_ids": ["FACT-1"]}],
    }


def _evaluate_with(change) -> dict:
    record = copy.deepcopy(_clean_record())
    change(record)
    return gate.evaluate_review_record(record)


def test_clean_record_passes_with_empty_diffs() -> None:
    result = gate.evaluate_review_record(_clean_record())

    assert result["status"] == "clean"
    assert result["failure_count"] == 0
    assert all(not item_ids for item_ids in result["diffs"].values())


def test_component_without_action_or_caveat_fails() -> None:
    result = _evaluate_with(
        lambda record: record["components"][0].update(review_action_ids=[])
    )

    assert result["diffs"]["components_without_review_action_or_caveat"] == ["api"]


def test_uncovered_component_with_explicit_caveat_is_resolved() -> None:
    def change(record: dict) -> None:
        record["components"][1]["status"] = "UNCOVERED"
        record["components"][1]["caveat"] = "No pass assigned; review is incomplete."

    result = _evaluate_with(change)

    assert result["status"] == "clean"


def test_finding_without_terminal_or_pending_disposition_fails() -> None:
    result = _evaluate_with(
        lambda record: record["findings"].append({"id": "F-dropped"})
    )

    assert result["diffs"]["findings_without_terminal_or_pending_disposition"] == [
        "F-dropped"
    ]


def test_incomplete_live_validation_receipt_is_not_explicitly_pending() -> None:
    def change(record: dict) -> None:
        del record["findings"][1]["pending_validation"]["expected_safe"]

    result = _evaluate_with(change)

    assert result["diffs"]["findings_without_terminal_or_pending_disposition"] == [
        "F-pending"
    ]


def test_confirmed_finding_without_supported_fact_fails() -> None:
    result = _evaluate_with(lambda record: record.update(facts=[]))

    assert result["diffs"]["confirmed_findings_without_supporting_evidence"] == [
        "F-confirmed"
    ]


def test_rejected_finding_without_route_complete_record_fails() -> None:
    def change(record: dict) -> None:
        record["findings"][3]["rejection_record"]["routes"].pop()

    result = _evaluate_with(change)

    assert result["diffs"]["rejected_findings_without_complete_rejection_record"] == [
        "F-rejected"
    ]


def test_reachability_rejection_requires_observed_evidence() -> None:
    def change(record: dict) -> None:
        rejection = record["findings"][3]["rejection_record"]
        rejection["reachability_claim"] = True

    result = _evaluate_with(change)

    assert result["diffs"]["rejected_findings_without_complete_rejection_record"] == [
        "F-rejected"
    ]


def test_report_claim_without_matching_fact_fails() -> None:
    result = _evaluate_with(
        lambda record: record["report_claims"][0].update(fact_ids=["FACT-missing"])
    )

    assert result["diffs"]["report_claims_without_matching_facts"] == ["CLAIM-1"]


def test_cli_exit_codes_distinguish_clean_failure_and_malformed_data(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    record_path = tmp_path / "review-record.json"
    record_path.write_text(json.dumps(_clean_record()), encoding="utf-8")
    assert gate.main([str(record_path)]) == gate.EXIT_CLEAN
    assert json.loads(capsys.readouterr().out)["status"] == "clean"

    failing = _clean_record()
    failing["report_claims"][0]["fact_ids"] = []
    record_path.write_text(json.dumps(failing), encoding="utf-8")
    assert gate.main([str(record_path)]) == gate.EXIT_CLOSURE_FAILURE
    assert json.loads(capsys.readouterr().out)["failure_count"] == 1

    record_path.write_text("{not-json", encoding="utf-8")
    assert gate.main([str(record_path)]) == gate.EXIT_USAGE_ERROR
    assert json.loads(capsys.readouterr().err)["status"] == "usage-error"


def test_duplicate_ids_are_rejected_as_ambiguous_data() -> None:
    record = _clean_record()
    record["facts"].append(copy.deepcopy(record["facts"][0]))

    with pytest.raises(gate.RecordError, match="duplicate id"):
        gate.evaluate_review_record(record)


def test_malformed_collection_values_fail_closed_without_type_errors() -> None:
    def change(record: dict) -> None:
        record["components"][0]["status"] = []
        record["findings"][0]["disposition"] = []
        record["findings"][3]["rejection_record"]["routes"][0]["result"] = []

    result = _evaluate_with(change)

    assert result["failure_count"] == 3
    assert result["diffs"]["components_without_review_action_or_caveat"] == ["api"]
    assert result["diffs"]["findings_without_terminal_or_pending_disposition"] == [
        "F-confirmed"
    ]
    assert result["diffs"]["rejected_findings_without_complete_rejection_record"] == [
        "F-rejected"
    ]


def test_gate_imports_only_the_standard_library() -> None:
    tree = ast.parse(_GATE_PATH.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])

    assert imports <= (set(sys.stdlib_module_names) | {"__future__"})


def test_bundle_documentation_references_gate_schema_and_tests() -> None:
    body = _SKILL_PATH.read_text(encoding="utf-8")

    assert "closure-gate.py" in body
    assert "closure-gate-review-record.md" in body
    assert "test_closure_gate.py" in body
    assert _REFERENCE_PATH.is_file()


def test_adversarial_eval_doctrine_names_every_required_safeguard() -> None:
    body = _EVAL_SKILL_PATH.read_text(encoding="utf-8")

    for required_text in (
        "Score axes separately",
        "Give every axis an objective trap",
        "Split the battery into two tiers",
        "Keep ground truth judge-only",
        "Randomize each fixture seed",
        "Judge artifacts, not self-reports",
        "One seed is a smoke test, not a benchmark",
    ):
        assert required_text in body


def test_monotonic_scrutiny_only_raises_attention_and_defers_store() -> None:
    body = _GAPS_SKILL_PATH.read_text(encoding="utf-8")

    assert "may only RAISE attention" in body
    assert "never excludes an item from re-examination" in body
    assert "PRIORITY and RECHECK signal, never a coverage claim" in body
    assert "durable cross-run scrutiny store is explicitly deferred" in body


def test_closure_gate_bundle_distributes_through_flattened_skill_copy(
    tmp_path: Path,
) -> None:
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
        "phase6-test",
        _ROOT / "catalog" / "skills",
        destination,
    )

    installed_bundle = destination / "security-review"
    installed_gate = installed_bundle / "scripts" / _GATE_PATH.name
    installed_reference = installed_bundle / "references" / _REFERENCE_PATH.name
    assert actions
    assert installed_gate.read_bytes() == _GATE_PATH.read_bytes()
    assert installed_reference.read_bytes() == _REFERENCE_PATH.read_bytes()
