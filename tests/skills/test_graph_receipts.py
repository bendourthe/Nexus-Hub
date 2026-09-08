"""Graph receipts preserve qualified metadata without disclosing raw results."""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "catalog/skills/code-review/security-review/scripts"
sys.path.insert(0, str(BUNDLE))
import _graph_receipt as graph

spec = importlib.util.spec_from_file_location("graph_closure", BUNDLE / "closure-gate.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


@pytest.fixture
def record():
    return json.loads((ROOT / "tests/fixtures/security-audit/application-audit-complete.json").read_text())


def node(name="module.handler", path="src/app.py"):
    return {"qualified_name": name, "file_path": path, "start_line": 2, "end_line": 4, "signature": "private-source-canary", "docstring": "private-source-canary"}


def project(raw, identity, **kwargs):
    return graph.project(raw, operation="code_node", qualified_symbol="module.handler", parameters={"symbol": "module.handler"}, identity=identity, receipt_id="G-1", duration_ms=1, **kwargs)


def test_recursive_projection_removes_sensitive_values(record):
    raw = {"matches": [node()], "source": "private-source-canary", "root": "C:/private/canary", "results": [{"node": node(), "config": {"token": "private-source-canary"}, "prompts": ["private-source-canary"], "command": "private-source-canary", "environment": {"value": "private-source-canary"}}]}
    receipt = project(raw, record["application_audit"])
    encoded = json.dumps(receipt)
    assert "private-source-canary" not in encoded and "C:/" not in encoded and "module.handler" not in encoded
    assert len(receipt["locations"]) == 1
    assert receipt["locations"][0]["symbol"] == graph.symbol_id("module.handler")
    assert receipt["quality"] == "unknown"


@pytest.mark.parametrize("count,quality", [(0,"unknown"), (1,"unknown"), (2,"ambiguous")])
def test_absence_and_ambiguity_never_prove_freshness(record,count,quality):
    receipt = project({"matches": count, "results": []},record["application_audit"])
    assert receipt["quality"] == quality


def test_bounded_projection_marks_partial(record):
    receipt = project({"matches": [node("m.a"),node("m.b"),node("m.c")]},record["application_audit"],limit=1)
    assert receipt["truncated"] and receipt["quality"] == "partial" and len(receipt["locations"]) == 1


@pytest.mark.parametrize("change", [
    {"operation":"find_path"}, {"query_provenance":"invented"}, {"result_digest":None}, {"parameters_digest":"invalid"}, {"duration_ms":True}, {"result_count":-1}, {"truncated":1}, {"symbol":"raw-secret-canary"}, {"availability":[]}, {"quality":[]}, {"ambiguity":"invented"}, {"reason_code":"private-canary"}, {"fallback":"invented"}, {"extra":{"secret":"private-canary"}}, {"run_fingerprint":"7"*64}, {"target_revision":"not-a-revision"}, {"qualified":False}, {"index_digest":"bad"}, {"locations":{}},
])
def test_invalid_graph_metadata_fails_profile(record,change):
    record["application_audit"]["graph_receipts"][0].update(change)
    result=gate.evaluate_review_record(record)
    assert result["computed_health"] == "failed"
    assert "private-canary" not in json.dumps(result)


@pytest.mark.parametrize("state,reason,health", [("NOT_APPLICABLE","GRAPH_NOT_APPLICABLE","degraded"),("UNAVAILABLE","GRAPH_UNAVAILABLE","degraded"),("UNAVAILABLE","GRAPH_TIMEOUT","degraded"),("DECLINED","GRAPH_DECLINED","degraded"),("FAILED","GRAPH_FAILED","failed")])
def test_terminal_receipt_outcomes(record,state,reason,health):
    r=record["application_audit"]["graph_receipts"][0]
    r.update(availability=state,reason_code=reason,quality="unknown",result_digest=None,result_count=0,locations=[])
    assert gate.evaluate_review_record(record)["computed_health"] == health


def test_raw_error_is_hashed_not_emitted(record):
    result=project({"error":"private-source-canary"},record["application_audit"])
    assert result["availability"] == "FAILED" and "private-source-canary" not in json.dumps(result)


@pytest.mark.parametrize("path", ["../outside.py", "C:/private.py", "src/secret=value.py", "src\\app.py"])
def test_unsafe_locations_rejected(record,path):
    with pytest.raises(ValueError):
        project({"matches":[node(path=path)]},record["application_audit"])


@pytest.mark.parametrize("raw", [{"matches":True},{"matches":-1},{"matches":"many"},{"matches":[{"qualified_name":3,"file_path":"src/app.py"}]},{"matches":[dict(node(),start_line=0)]}])
def test_malformed_results_rejected(record,raw):
    with pytest.raises(ValueError):
        project(raw,record["application_audit"])


def test_duplicate_and_unbounded_locations_rejected(record):
    identity=record["application_audit"]
    r=project({"matches":[node()]},identity)
    r["locations"]*=2
    with pytest.raises(ValueError): graph.validate(r,identity)
    r["locations"]*=60
    with pytest.raises(ValueError): graph.validate(r,identity)


def test_complete_claim_cannot_hide_partial_result(record):
    r=record["application_audit"]["graph_receipts"][0]
    r["truncated"]=True
    assert gate.evaluate_review_record(record)["computed_health"] == "failed"


def test_result_limits_and_depth_are_visible(record):
    value={"matches":1,"results":[]}
    for _ in range(35): value={"matches":1,"results":[value]}
    assert project(value,record["application_audit"])["truncated"]
    assert project({"matches":0,"results":[{}]*10002},record["application_audit"])["truncated"]


def test_no_result_does_not_remove_supported_finding(record):
    before=copy.deepcopy(record["findings"])
    record["application_audit"]["graph_receipts"]=[project({"matches":0},record["application_audit"])]
    result=gate.evaluate_review_record(record)
    assert result["computed_health"] == "degraded" and record["findings"] == before


def test_conflicting_results_for_same_query_fail(record):
    receipt=copy.deepcopy(record["application_audit"]["graph_receipts"][0])
    receipt.update(id="G-2",result_digest="8"*64)
    record["application_audit"]["graph_receipts"].append(receipt)
    assert gate.evaluate_review_record(record)["computed_health"] == "failed"


@pytest.mark.parametrize("change", [{"reason_code":"GRAPH_FAILED"},{"result_count":2},{"reason_code":"GRAPH_NO_RESULT"},{"reason_code":"GRAPH_PARTIAL"},{"reason_code":"GRAPH_AMBIGUOUS"},{"reason_code":"GRAPH_UNKNOWN"}])
def test_contradictory_run_metadata_fails(record,change):
    record["application_audit"]["graph_receipts"][0].update(change)
    assert gate.evaluate_review_record(record)["computed_health"] == "failed"


def test_symbol_substitution_cannot_evade_query_conflict(record):
    receipt=copy.deepcopy(record["application_audit"]["graph_receipts"][0])
    receipt.update(id="G-2",result_digest="8"*64,symbol=graph.symbol_id("other.symbol"))
    record["application_audit"]["graph_receipts"].append(receipt)
    assert gate.evaluate_review_record(record)["computed_health"] == "failed"
