"""Admission-gate validator for the Nexus-Hub Settings catalog (v4.14.6).

`scripts/lib/settings_control/catalog.json` is the only list of what the settings
engine may write or report. These tests are the gate: a write ships as a control
only with a source and a proven row in the proof matrix, and every other cell is
Not-Settable with its reason. The rules that need nothing outside the catalog live
in `scripts/lib/settings_control/catalog.py`, which the engine loader also runs,
so they exist once. The checks below need repository files (the proof matrix,
decision records, `configs/platform-defaults.json`, the model map) that an
installed tree does not carry.
"""
from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.settings_control.catalog import CATALOG_PATH, CLAUDE_IDS_PATH as IDS_PATH, validate_structure  # noqa: E402

MODEL_MAP_PATH = REPO_ROOT / "catalog" / "skills" / "ai-development" / "model-routing" / "references" / "last-known-model-map.json"
PLATFORM_DEFAULTS_PATH = REPO_ROOT / "configs" / "platform-defaults.json"


def load_catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def validate_catalog(catalog: dict, root: Path = REPO_ROOT) -> list[str]:
    """Return one finding per rule violation; an empty list means the catalog is admitted."""
    findings = validate_structure(catalog)
    matrix = (root / catalog["proof_matrix"]).read_text(encoding="utf-8")
    proven = set(re.findall(r"^\| ((?:W|O)\d{2}) \|.*\| proven \|[^|]*\|$", matrix, flags=re.MULTILINE))
    for write in catalog["writes"]:
        wid = write["id"]
        ids = write.get("proof") or []
        if write["admission"] == "admitted" and ids and any(rid not in proven for rid in ids):
            findings.append(f"{wid}: admitted without a proven proof-matrix row ({ids})")
        source = write["source"]
        if write["kind"] == "internal" and not (root / source.get("decision", "missing")).is_file():
            findings.append(f"{wid}: internal write cites a decision record that does not exist")
    return findings + _shared_key_findings(catalog, root)


def _walk(tree: dict, path: list[str]):
    node = tree
    for part in path:
        if not isinstance(node, dict) or part not in node:
            return None, False
        node = node[part]
    return node, True


def _shared_key_findings(catalog: dict, root: Path) -> list[str]:
    findings: list[str] = []
    defaults = json.loads((root / "configs" / "platform-defaults.json").read_text(encoding="utf-8"))["platforms"]
    for write in catalog["writes"]:
        shared = write.get("shared_with_platform_defaults")
        if not shared:
            continue
        settings = defaults[shared["platform"]]["settings"]
        for path in shared["paths"]:
            value, found = _walk(settings, path)
            if not found:
                findings.append(f"{write['id']}: shared key {'.'.join(path)} is absent from platform-defaults")
                continue
            if path[0] == "modelSettings":
                ids = set(json.loads(IDS_PATH.read_text(encoding="utf-8"))["ids"])
                if set(value) != ids:
                    findings.append(f"{write['id']}: modelSettings ids disagree with claude_model_ids.json")
                continue
            values = write["values"]
            if isinstance(values, list) and values and isinstance(value, (str, bool)) and value not in values:
                findings.append(f"{write['id']}: platform-defaults value {value!r} is outside the catalog value set")
            if isinstance(values, dict) and values.get("type") == "string" and not isinstance(value, str):
                findings.append(f"{write['id']}: platform-defaults value is not a string")
    return findings


@pytest.fixture(scope="module")
def catalog() -> dict:
    return load_catalog()


def test_catalog_has_no_findings(catalog: dict) -> None:
    assert validate_catalog(catalog) == []


def test_catalog_is_not_empty_and_admits_only_proven_writes(catalog: dict) -> None:
    admitted = [w["id"] for w in catalog["writes"] if w["admission"] == "admitted"]
    assert {"claude.model", "claude.posture", "codex.model", "codex.posture", "codex.sandbox_mode", "internal.git_guardrails"} == set(admitted)


def test_every_not_settable_cell_has_a_reason(catalog: dict) -> None:
    cells = [w for w in catalog["writes"] if w["admission"] == "not-settable"]
    assert cells and all(w["not_settable_reason"].strip() for w in cells)


def test_claude_model_ids_match_the_model_map() -> None:
    model_map = json.loads(MODEL_MAP_PATH.read_text(encoding="utf-8"))
    expected = [model_map["tiers"][tier]["Anthropic"] for tier in ("frontier", "strong", "standard", "fast")]
    assert json.loads(IDS_PATH.read_text(encoding="utf-8"))["ids"] == expected


def test_omitted_keys_are_baked_from_platform_defaults(catalog: dict) -> None:
    omitted = json.loads(PLATFORM_DEFAULTS_PATH.read_text(encoding="utf-8"))["platforms"]["codex"]["omitted"]
    assert catalog["omitted_keys"]["codex"] == sorted(omitted)


def test_only_codex_model_is_an_omitted_key_exception(catalog: dict) -> None:
    assert catalog["omitted_user_choice_exceptions"] == {"codex": ["model"]}
    assert not any(name.startswith("memories") or name.startswith("features") for name in catalog["omitted_user_choice_exceptions"]["codex"])


def _mutated(catalog: dict, write_id: str, **changes: object) -> dict:
    clone = copy.deepcopy(catalog)
    for write in clone["writes"]:
        if write["id"] == write_id:
            write.update(changes)
    return clone


@pytest.mark.parametrize(
    ("write_id", "changes", "needle"),
    [
        ("claude.model", {"proof": ["W05"]}, "admitted without a proven proof-matrix row"),
        ("claude.model", {"proof": []}, "admitted without a proven proof-matrix row"),
        ("claude.effort.top_level", {"not_settable_reason": ""}, "Not-Settable without a reason"),
        ("claude.effort.top_level", {"values": ["low", "max"]}, "max must never be a default"),
        ("codex.posture", {"value_map": {"ask": "untrusted"}}, "untrusted is mapped"),
        ("codex.posture", {"applies_only_without": []}, "applies_only_without default_permissions"),
        ("claude.posture", {"weakens_safety": False, "weakening_values": []}, "weakens_safety is false"),
        ("claude.model", {"file": ".claude/settings.json"}, "not a user-level file"),
        ("codex.model", {"source": {"url": "http://example.com", "fetched": "x"}}, "https source url"),
        ("internal.git_guardrails", {"source": {"decision": "docs/decisions/none.md"}}, "decision record that does not exist"),
        ("claude.model", {"admission": "maybe"}, "admission must be"),
    ],
)
def test_each_rule_fails_closed(catalog: dict, write_id: str, changes: dict, needle: str) -> None:
    findings = validate_catalog(_mutated(catalog, write_id, **changes))
    assert any(needle in finding for finding in findings), findings


def test_a_write_to_an_omitted_key_is_refused(catalog: dict) -> None:
    clone = _mutated(catalog, "codex.model", key_path=["memories", "extract_model"])
    assert any("omitted key memories.extract_model" in f for f in validate_catalog(clone))


def test_codex_model_exception_does_not_extend_to_other_keys(catalog: dict) -> None:
    clone = _mutated(catalog, "codex.model", key_path=["features", "memories"])
    assert any("omitted key features.memories" in f for f in validate_catalog(clone))


def test_shared_key_value_set_disagreement_is_refused(catalog: dict) -> None:
    clone = _mutated(catalog, "codex.posture", values=["never"])
    assert any("outside the catalog value set" in f for f in validate_catalog(clone))


def test_two_controls_writing_one_key_path_are_refused(catalog: dict) -> None:
    clone = copy.deepcopy(catalog)
    duplicate = copy.deepcopy(next(w for w in clone["writes"] if w["id"] == "claude.model"))
    duplicate["id"] = "claude.model.copy"
    clone["writes"].append(duplicate)
    clone["controls"][1]["writes"].append("claude.model.copy")
    assert any("same key path" in f for f in validate_catalog(clone))


def _with_layer(catalog: dict, write_id: str, layer_changes: dict) -> dict:
    clone = copy.deepcopy(catalog)
    write = next(w for w in clone["writes"] if w["id"] == write_id)
    write["override_layers"][0].update(layer_changes)
    return clone


@pytest.mark.parametrize(
    ("changes", "needle"),
    [
        ({"detect": {"env": ["lower"]}}, "upper-case variable names"),
        ({"detect": {"env": ["CLAUDE_CODE_EFFORT_LEVEL"], "caveat": "both"}}, "exactly one of"),
        ({"detect": {}}, "exactly one of"),
        ({"detect": {"files": ["nowhere"], "key_paths": [["a"]]}}, "unknown file id"),
        ({"detect": {"files": ["claude-project"]}}, "need key_paths"),
        ({"detect": {"caveat": " "}}, "text is empty"),
        ({"detect": {"settings_env": ["claude-user"]}}, "exactly one of"),
    ],
)
def test_detect_specs_fail_closed(catalog: dict, changes: dict, needle: str) -> None:
    findings = validate_catalog(_with_layer(catalog, "claude.model", changes))
    assert any(needle in finding for finding in findings), findings


def test_a_layer_without_a_detect_spec_is_refused(catalog: dict) -> None:
    clone = copy.deepcopy(catalog)
    del next(w for w in clone["writes"] if w["id"] == "claude.model")["override_layers"][0]["detect"]
    assert any("has no detect spec" in f for f in validate_catalog(clone))


def test_a_tool_without_a_detect_command_is_refused(catalog: dict) -> None:
    clone = copy.deepcopy(catalog)
    del clone["tools"]["claude"]["detect"]
    assert any("tool claude lacks a detect command" in f for f in validate_catalog(clone))
