"""Exercise the generic-review projection CLI with valid and hostile envelopes."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "catalog/skills/code-review/security-review/scripts"
sys.path.insert(0, str(SCRIPTS))
import _audit_envelope as contract

ENVELOPES = ROOT / "tests/fixtures/security-audit/envelopes"
CASES = json.loads(
    (ROOT / "tests/fixtures/review-evidence/v4.15.3/cases.json").read_text()
)
HIDDEN = {"creationflags": 0x08000000} if sys.platform == "win32" else {}
FOREIGN = "f" * 64
SCRIPT = SCRIPTS / "project-review-findings.py"


def load(name):
    return json.loads((ENVELOPES / name).read_text())


def seal(value):
    value["run_fingerprint"] = contract.digest(
        {k: v for k, v in value.items() if k != "run_fingerprint"}
    )
    return value


def context_for(envelope):
    target = envelope["target"]
    return {
        "revision": target["revision"],
        "root_fingerprint": target["root_fingerprint"],
        "scope_fingerprint": target["scope_fingerprint"],
        "input_run_fingerprint": envelope["input_run_fingerprint"],
    }


def run_cli(envelope, tmp_path, context=None, context_name="context.json"):
    args = [sys.executable, str(SCRIPT)]
    if context is not None:
        path = tmp_path / context_name
        path.write_text(json.dumps(context))
        args += ["--expected-context", str(path)]
    raw = envelope if isinstance(envelope, bytes) else json.dumps(envelope).encode()
    return subprocess.run(args, input=raw, capture_output=True, check=False, **HIDDEN)


def assert_preserved(source, output):
    """Independent oracle: every source finding keeps identity, state, evidence."""
    by_id = {f["id"]: f for f in output["findings"]}
    assert set(by_id) == {f["id"] for f in source["findings"]}
    for finding in source["findings"]:
        projected = by_id[finding["id"]]
        assert projected["source_disposition"] == finding["disposition"]
        assert projected["source_severity"] == finding["severity"]
        assert projected["source_confidence"] == finding["confidence"]
        assert projected["release_blocking"] == finding["release_blocking"]
        assert (
            projected["security"]["evidence_receipt_ids"]
            == finding["evidence_receipt_ids"]
        )
    assert output["source"]["computed_health"] == source["computed_health"]
    assert output["source"]["reason_codes"] == source["reason_codes"]
    assert output["source"]["disposition_counts"] == source["disposition_counts"]


@pytest.mark.parametrize("case", CASES["valid"], ids=lambda c: c["envelope"])
def test_valid_envelope_projects_with_bound_context(case, tmp_path):
    source = load(case["envelope"])
    result = run_cli(source, tmp_path, context_for(source))
    assert result.returncode == 0 and not result.stderr
    output = json.loads(result.stdout)
    assert output["binding"]["state"] == "bound"
    assert output["claims"]["complete_review"] is case["complete_review"]
    assert output["claims"]["current_target_confirmation"] is True
    states = {}
    for finding in output["findings"]:
        states[finding["review_state"]] = states.get(finding["review_state"], 0) + 1
    assert states == case["states"]
    assert sum(f["release_blocking"] for f in output["findings"]) == case["blocking"]
    assert_preserved(source, output)
    assert result.stdout == run_cli(source, tmp_path, context_for(source)).stdout


def test_blocking_and_severity_mapping_never_hide_alerts(tmp_path):
    source = load("degraded.expected.json")
    source["findings"][0].update(severity="medium", release_blocking=True)
    seal(source)
    output = json.loads(run_cli(source, tmp_path, context_for(source)).stdout)
    for projected in output["findings"]:
        expected = CASES["severity_map"][projected["source_severity"]]
        if projected["release_blocking"]:
            assert projected["severity"] in {"P0", "P1"}
        else:
            assert projected["severity"] == expected
        assert projected["confidence_band"] in {25, 50, 75, 100}


def test_pending_item_is_visible_and_unverified(tmp_path):
    source = load("degraded.expected.json")
    output = json.loads(run_cli(source, tmp_path, context_for(source)).stdout)
    pending = [f for f in output["findings"] if f["review_state"] == "pending"]
    assert len(pending) == 1 and pending[0]["requires_verification"] is True
    assert "proof_class" in pending[0]["security"]["unavailable"]
    assert not any("proof_class" in f["security"] for f in output["findings"])


def test_missing_context_is_unbound_and_claims_nothing(tmp_path):
    source = load("complete-local.expected.json")
    result = run_cli(source, tmp_path)
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["binding"]["state"] == "unbound"
    assert output["claims"] == {
        "current_target_confirmation": False,
        "complete_review": False,
    }


def test_locationless_finding_keeps_identity_without_fake_location(tmp_path):
    source = load("degraded.expected.json")
    source["findings"][0]["location"] = {"locationless": True}
    seal(source)
    output = json.loads(run_cli(source, tmp_path, context_for(source)).stdout)
    target_id = source["findings"][0]["id"]
    projected = next(f for f in output["findings"] if f["id"] == target_id)
    assert projected["locationless"] is True
    assert projected["file"] is None and projected["line"] is None
    assert projected["fingerprint_key"] == "security:" + projected["id"]


def hostile(name):
    """Return (envelope, context) for one hostile control."""
    source = load("degraded.expected.json")
    context = context_for(source)
    if name == "foreign-self-consistent":
        foreign = copy.deepcopy(source)
        foreign["target"]["revision"] = "1" * 40
        foreign["target"]["root_fingerprint"] = FOREIGN
        return seal(foreign), context
    if name == "foreign-empty-complete":
        foreign = load("complete-local.expected.json")
        foreign["target"]["root_fingerprint"] = FOREIGN
        return seal(foreign), context
    if name == "stale-revision":
        return source, {**context, "revision": "2" * 40}
    if name == "wrong-scope":
        return source, {**context, "scope_fingerprint": FOREIGN}
    if name == "wrong-run-identity":
        return source, {**context, "input_run_fingerprint": FOREIGN}
    if name == "bad-fingerprint":
        broken = copy.deepcopy(source)
        broken["findings"][0]["severity"] = "low"
        return broken, context
    if name == "malformed-json":
        return b'{"schema": ', context
    if name == "unknown-context-key":
        return source, {**context, "derived_from_envelope": True}
    if name == "context-from-envelope-shape":
        return source, {"target": source["target"]}
    raise AssertionError(name)


@pytest.mark.parametrize("case", CASES["hostile"], ids=lambda c: c["name"])
def test_hostile_controls_fail_closed(case, tmp_path):
    envelope, context = hostile(case["name"])
    result = run_cli(envelope, tmp_path, context)
    assert result.returncode == case["expect_exit"] and result.stdout == b""
    assert json.loads(result.stderr) == {"error": case["expect_error"]}
    assert len(result.stderr) < 100


def test_missing_context_file_is_a_bounded_error(tmp_path):
    source = load("degraded.expected.json")
    args = [
        sys.executable,
        str(SCRIPT),
        "--expected-context",
        str(tmp_path / "absent.json"),
    ]
    result = subprocess.run(
        args,
        input=json.dumps(source).encode(),
        capture_output=True,
        check=False,
        **HIDDEN,
    )
    assert result.returncode == 2 and result.stdout == b""
    assert json.loads(result.stderr) == {"error": "review_projection_invalid"}


@pytest.mark.parametrize("drop", ["evidence_receipt_ids", "disposition", "id"])
def test_evidence_drop_mutation_is_detected(drop, tmp_path):
    source = load("degraded.expected.json")
    output = json.loads(run_cli(source, tmp_path, context_for(source)).stdout)
    assert_preserved(source, output)
    mutated = copy.deepcopy(output)
    victim = mutated["findings"][0]
    if drop == "evidence_receipt_ids":
        victim["security"]["evidence_receipt_ids"] = []
    elif drop == "disposition":
        victim["source_disposition"] = "rejected"
    else:
        victim["id"] = "sha256:" + FOREIGN
    with pytest.raises(AssertionError):
        assert_preserved(source, mutated)


def test_cli_never_opens_paths_named_in_the_envelope(tmp_path):
    source = load("degraded.expected.json")
    result = run_cli(source, tmp_path, context_for(source))
    assert result.returncode == 0
    assert not (tmp_path / "src").exists()
