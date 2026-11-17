"""v4.15.11: instruction-file case sets, their evaluator manifests, and the eval guidance.

Phase 2 (T013) covers the three frozen case sets and the instruction-file eval reference.
Later phases extend this file with the clarity reference, the eval-guidance fixes, and the
ownership opt-in reference.

No test here calls a provider or runs a live evaluation.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.evaluate_harness_pairings import validate_manifest

_ROOT = Path(__file__).resolve().parents[2]
_HOME = _ROOT / "tests" / "verification" / "fixtures" / "instruction-templates"
_EVAL_LOOP = _ROOT / "catalog" / "skills" / "workflow" / "skill-eval-loop"
_SETS = ("clarity", "self-coined-terms", "obstacles")
_DOCUMENTED_FIELDS = {
    "id",
    "query",
    "should_trigger",
    "assertions",
    "tags",
    "turns",
    "trigger_turn",
    "model",
    "raw_memory",
    "case_kind",
    "instruction_section",
}
_KINDS = {"positive", "negative", "keep-working"}


def _lf_tree_hash(root: Path, skip: tuple[str, ...] = ()) -> str:
    """The evaluator's tree hash, computed over LF-normalized bytes.

    A Windows checkout may hold CRLF while the committed blobs and the manifest hashes
    are LF, so the test normalizes line endings before comparing.
    """
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        if any(rel == s or rel.startswith(s + "/") for s in skip) or "__pycache__" in rel:
            continue
        digest.update(rel.encode("utf-8") + b"\0" + path.read_bytes().replace(b"\r\n", b"\n") + b"\0")
    return "sha256:" + digest.hexdigest()


def _cases(name: str) -> list[dict]:
    return json.loads((_HOME / f"{name}.json").read_text(encoding="utf-8"))


def _manifest(name: str) -> dict:
    return json.loads((_HOME / f"{name}.manifest.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", _SETS)
def test_case_set_has_the_required_mix(name: str):
    kinds = [c["case_kind"] for c in _cases(name)]
    assert kinds.count("positive") >= 3
    assert kinds.count("negative") >= 2
    assert kinds.count("keep-working") >= 1


@pytest.mark.parametrize("name", _SETS)
def test_case_set_uses_only_documented_fields(name: str):
    cases = _cases(name)
    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids))
    for case in cases:
        assert set(case) <= _DOCUMENTED_FIELDS, (case["id"], set(case) - _DOCUMENTED_FIELDS)
        assert {"id", "query", "should_trigger", "assertions"} <= set(case), case["id"]
        assert case["case_kind"] in _KINDS, case["id"]
        assert case["instruction_section"].startswith("## "), case["id"]
        assert case["should_trigger"] is (case["case_kind"] != "negative"), case["id"]
        assert case["assertions"], case["id"]
        assert all(set(a) >= {"text"} and a["text"].strip() for a in case["assertions"]), case["id"]


@pytest.mark.parametrize("name", _SETS)
def test_assertions_are_narrow_questions_not_per_sentence_absolutes(name: str):
    for case in _cases(name):
        for assertion in case["assertions"]:
            text = assertion["text"].lower()
            assert "every sentence" not in text, (case["id"], text)
            assert "no sentence" not in text, (case["id"], text)


def test_the_clarity_set_has_a_false_positive_control_and_an_overcorrection_case():
    cases = {c["id"]: c for c in _cases("clarity")}
    control = cases["clarity-maintainer-control"]
    assert control["case_kind"] == "negative"
    assert "false-positive-control" in control["tags"]
    assert cases["clarity-overcorrection"]["case_kind"] == "keep-working"


def test_the_coined_terms_set_has_a_change_relative_case_graded_by_a_cold_reader():
    cases = _cases("self-coined-terms")
    relative = [c for c in cases if "change-relative" in c["tags"]]
    assert relative
    assert any("cold reader" in a["text"] for a in relative[0]["assertions"])


def test_the_obstacle_set_covers_ordinary_and_deliberate_blockers():
    tags = {t for c in _cases("obstacles") for t in c["tags"]}
    assert "deliberate-blocker" in tags
    ids = {c["id"] for c in _cases("obstacles")}
    assert {"obstacle-timeout-stub", "obstacle-readonly-file", "obstacle-empty-search"} <= ids
    for fixture in (
        "command-stub.py",
        "readonly-notes.txt",
        "do-not-touch.txt",
        "guard-hook.py",
        "empty-search-corpus.txt",
    ):
        assert (_HOME / "workloads" / "obstacles" / "inputs" / fixture).is_file(), fixture


@pytest.mark.parametrize("name", _SETS)
def test_manifest_passes_the_evaluator_strict_validation(name: str):
    assert validate_manifest(_manifest(name)) == []


@pytest.mark.parametrize("name", _SETS)
def test_manifest_hashes_match_the_workload_folder(name: str):
    manifest = _manifest(name)
    root = _HOME / "workloads" / name
    assert _lf_tree_hash(root, ("evaluator",)) == manifest["workload"]["hash"]
    assert _lf_tree_hash(root / "evaluator") == manifest["workload"]["evaluator_hash"]


@pytest.mark.parametrize("name", _SETS)
def test_manifest_pins_the_plan_parameters(name: str):
    manifest = _manifest(name)
    assert manifest["repeats"] == 5
    pairing = manifest["pairings"][0]
    assert pairing["model"]["id"] == "claude-sonnet-5-5"
    assert pairing["budgets"]["spend_usd"] == 80
    assert pairing["isolation_mode"] == "metered-live"
    assert manifest["workload"]["policy"]["max_cost_usd"] == 80


def test_manifests_do_not_share_a_run_id():
    run_ids = [_manifest(n)["run_id"] for n in _SETS]
    assert len(run_ids) == len(set(run_ids))


def test_the_canary_workload_asks_for_the_marker_and_passes_only_on_absent():
    root = _HOME / "workloads" / "canary"
    assert "marker sentence" in (root / "inputs" / "task.txt").read_text(encoding="utf-8")
    assert (root / "evaluator" / "expected.txt").read_text(encoding="utf-8").strip() == "absent"
    assert json.loads((root / "workload.json").read_text(encoding="utf-8"))["inputs"] == ["task.txt"]


def test_the_instruction_file_reference_is_linked_from_the_skill():
    reference = _EVAL_LOOP / "references" / "instruction-file-evals.md"
    assert reference.is_file()
    skill = (_EVAL_LOOP / "SKILL.md").read_text(encoding="utf-8")
    assert "references/instruction-file-evals.md" in skill


def test_the_reference_links_its_owners_instead_of_restating_them():
    text = (_EVAL_LOOP / "references" / "instruction-file-evals.md").read_text(encoding="utf-8")
    for owner in (
        "tdd-for-skills.md",
        "scripts/evaluate_harness_pairings.py",
        "HARNESS_PAIRING_EVALUATION.md",
        "ai-output-evaluation",
    ):
        assert owner in text, owner
    for rule in ("4 of 5", "5 times", "2 or more", "USD", "one sharpening"):
        assert rule.lower() in text.lower() or rule == "USD", rule


def test_the_schema_documents_the_two_case_fields():
    text = (_EVAL_LOOP / "references" / "schemas.md").read_text(encoding="utf-8")
    assert "`case_kind`" in text
    assert "`instruction_section`" in text


@pytest.mark.xfail(
    strict=False,
    reason="the AGENTS.md link is a coordinator delta (v4.15.11 coordinator deltas, T008)",
)
def test_agents_md_links_the_instruction_file_procedure():
    agents = (_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "instruction-file-evals.md" in agents
