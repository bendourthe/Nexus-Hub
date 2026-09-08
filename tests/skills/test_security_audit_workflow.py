"""Preset, workflow-manifest, and role-separation tests for security-audit."""

from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_PRESET = _ROOT / "catalog" / "skills" / "workflow" / "agent-presets" / "SKILL.md"
_TRIGGERS = (
    _ROOT
    / "catalog"
    / "skills"
    / "workflow"
    / "agent-presets"
    / "evals"
    / "trigger-cases.json"
)
_WORKFLOWS = _ROOT / "data" / "workflows.json"
_REVIEWER = _ROOT / "catalog" / "agents" / "security-reviewer.md"

_REQUIRED_OWNERS = (
    "security-review",
    "dependency-security-audit",
    "cve-reachability-analyzer",
    "cloud-security-posture-detection",
    "security-patch-advisor",
    "testing-review",
    "adversarial-verifier",
)
_DETECTION = (
    "security-review",
    "dependency-security-audit",
    "cloud-security-posture-detection",
)


def _preset_text() -> str:
    return _PRESET.read_text(encoding="utf-8")


def _security_audit_workflow() -> dict:
    payload = json.loads(_WORKFLOWS.read_text(encoding="utf-8"))
    matches = [item for item in payload["workflows"] if item["id"] == "security-audit"]
    assert len(matches) == 1
    return matches[0]


def test_one_security_audit_identity_in_preset_and_manifest() -> None:
    body = _preset_text()
    workflow = _security_audit_workflow()

    assert body.count("### Preset: security-audit") == 1
    assert workflow["id"] == "security-audit"
    assert "security-audit" in body
    ids = [
        item["id"]
        for item in json.loads(_WORKFLOWS.read_text(encoding="utf-8"))["workflows"]
        if item["id"] == "security-audit"
    ]
    assert ids == ["security-audit"]


def test_required_owners_are_members() -> None:
    body = _preset_text()
    skills = _security_audit_workflow()["skills"]

    for owner in _REQUIRED_OWNERS:
        assert owner in skills
        assert owner in body


def test_detection_precedes_remediation() -> None:
    skills = _security_audit_workflow()["skills"]
    patch_at = skills.index("security-patch-advisor")
    for owner in _DETECTION:
        assert skills.index(owner) < patch_at

    body = _preset_text()
    detect_at = body.index("**Detect**")
    remediate_at = body.index("**Remediate**")
    assert detect_at < remediate_at


def test_testing_and_rescan_precede_closure() -> None:
    skills = _security_audit_workflow()["skills"]
    assert skills.index("testing-review") < skills.index("adversarial-verifier")
    assert skills.index("security-patch-advisor") < skills.index("testing-review")

    body = _preset_text()
    test_at = body.index("**Test**")
    rescan_at = body.index("**Re-scan**")
    close_at = body.index("**Close**")
    assert test_at < rescan_at < close_at


def test_independent_verifier_is_read_only() -> None:
    reviewer = _REVIEWER.read_text(encoding="utf-8")
    body = _preset_text()

    assert "This role is read-only" in reviewer
    assert (
        "do not apply patches" in reviewer.lower()
        or "You do not apply patches" in reviewer
    )
    assert "Write" not in reviewer.split("tools:", 1)[1].split("\n", 1)[0]
    assert "Edit" not in reviewer.split("tools:", 1)[1].split("\n", 1)[0]
    assert "independent verifier" in body.lower() or "Independent verify" in body
    assert "does not apply patches" in body


def test_trigger_cases_cover_positives_and_negatives() -> None:
    payload = json.loads(_TRIGGERS.read_text(encoding="utf-8"))
    assert payload["skill"] == "agent-presets"
    cases = {item["id"]: item for item in payload["cases"]}

    for case_id in (
        "pos-full-security-audit",
        "pos-scan-fix-rescan",
        "pos-dependency-plus-iac",
        "pos-prerelease-verification",
    ):
        assert cases[case_id]["should_trigger"] is True

    for case_id in (
        "neg-one-cve-reachability",
        "neg-one-cloud-posture",
        "neg-patch-only",
        "neg-ordinary-code-review",
    ):
        assert cases[case_id]["should_trigger"] is False


def test_workflow_projection_comes_only_from_routing_authority() -> None:
    path = _ROOT / "catalog/skills/workflow/agent-presets/references/security-audit-routing.json"
    authority = json.loads(path.read_text(encoding="utf-8"))
    expected = {s["owner"] for s in authority["surfaces"]}
    expected.update(h["owner"] for s in authority["surfaces"] for h in s["handoffs"])
    expected.update(authority["fixed_stages"])
    workflow = _security_audit_workflow()
    assert set(workflow["skills"]) == expected
    assert len(workflow["skills"]) == len(expected)
    assert (_ROOT / workflow["routing_manifest"]).resolve() == path.resolve()
    assert "licensing-compliance" not in expected
    assert "authentication-patterns" in expected


def test_absent_bundle_owners_are_explicit_unavailable_handoffs() -> None:
    data = json.loads((_ROOT / "data/bundles.json").read_text(encoding="utf-8"))
    bundle = next(item for item in data["bundles"] if item["id"] == "security-specialist")
    missing = set(_security_audit_workflow()["skills"]) - set(bundle["skills"])
    assert missing == {"advanced-attack-patterns", "business-logic-abuse", "ai-attack-patterns", "prompt-injection-defense"}
    text = _preset_text()
    assert "missing owners remain explicit `UNAVAILABLE` receipts" in text
    assert "No automatic installation" in (_PRESET.parent / "references/security-audit-routing.md").read_text(encoding="utf-8")


def test_host_receipt_fixture_records_offline_declines_without_health_claims() -> None:
    payload = json.loads((_ROOT / "tests/fixtures/security-audit/routing-host-offline.json").read_text(encoding="utf-8"))
    assert payload["offline_only"] is True
    assert {r["owner"] for r in payload["receipts"]} == set(payload["planned_owners"])
    assert len(payload["receipts"]) == len(payload["planned_owners"])
    for receipt in payload["receipts"]:
        assert receipt["provenance"] == "self_attested"
        assert receipt["run_fingerprint"] == payload["run_fingerprint"]
        assert receipt["state"] in {"RAN", "UNAVAILABLE", "FAILED", "DECLINED"}
        assert "execution_context" in receipt
        if receipt["kind"] in {"network", "cloud", "model"}:
            assert receipt["state"] == "DECLINED" and receipt["reason_code"] == "OFFLINE_ONLY"
        if receipt["execution_context"] is None:
            assert "BOUNDARY_CONTEXT_MISSING" in receipt["limitation_codes"]
    assert "computed_health" not in json.dumps(payload)
    assert "process_observed" not in json.dumps(payload)
