"""Admission-gate validator for the Nexus-Hub Settings catalog (v4.14.6 Phase 1).

`scripts/lib/settings_control/catalog.json` is the only list of what the settings
engine may write or report. These tests are the gate: a write ships as a control
only with a source and a proven row in the proof matrix, and every other cell is
Not-Settable with its reason. The module also exposes `validate_catalog`, which
the engine loader imports in Phase 2 so the rules exist once.
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = REPO_ROOT / "scripts" / "lib" / "settings_control" / "catalog.json"
IDS_PATH = REPO_ROOT / "scripts" / "lib" / "settings_control" / "claude_model_ids.json"
MODEL_MAP_PATH = REPO_ROOT / "catalog" / "skills" / "ai-development" / "model-routing" / "references" / "last-known-model-map.json"
PLATFORM_DEFAULTS_PATH = REPO_ROOT / "configs" / "platform-defaults.json"

TOOLS = {"claude", "codex", "copilot-cli", "vscode-copilot", "internal"}
SURFACES = {"cli", "vscode-host", "desktop"}
LAYER_KINDS = {"env", "project-file", "managed-file", "policy", "remembered-ui"}
USER_FILES = ("~/.claude/settings.json", "~/.codex/config.toml", "~/.copilot/settings.json", "~/.nexus-hub/guardrails.json", "vscode-config")
REQUIRED_WRITE_KEYS = {"id", "kind", "tool", "surface", "file", "key_path", "values", "value_map", "override_layers", "takes_effect", "proven_versions", "weakens_safety", "weakening_values", "source", "admission"}
# (tool, joined key path, native value) pairs that lower a safety barrier.
WEAKENING_NATIVE = {
    ("claude", "permissions.defaultMode", "bypassPermissions"),
    ("claude", "skipDangerousModePermissionPrompt", True),
    ("claude", "claudeCode.initialPermissionMode", "bypassPermissions"),
    ("claude", "claudeCode.allowDangerouslySkipPermissions", True),
    ("codex", "approval_policy", "never"),
    ("copilot-cli", "defaultPermissionMode", "allow-all"),
    ("vscode-copilot", "chat.tools.global.autoApprove", True),
    ("vscode-copilot", "chat.permissions.default", "autoApprove"),
    ("internal", "block_git_bypass_flags", False),
}
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load_catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def _native_values(write: dict) -> list:
    values = write["values"]
    return values if isinstance(values, list) else []


def _joined(write: dict) -> str:
    return ".".join(str(part) for part in write["key_path"])


def validate_catalog(catalog: dict, root: Path = REPO_ROOT) -> list[str]:
    """Return one finding per rule violation; an empty list means the catalog is admitted."""
    findings: list[str] = []
    matrix = (root / catalog["proof_matrix"]).read_text(encoding="utf-8")
    proven = set(re.findall(r"^\| ((?:W|O)\d{2}) \|.*\| proven \|[^|]*\|$", matrix, flags=re.MULTILINE))
    seen_paths: dict[tuple, str] = {}
    exceptions = catalog.get("omitted_user_choice_exceptions", {})
    for write in catalog["writes"]:
        wid = write.get("id", "<no id>")
        missing = REQUIRED_WRITE_KEYS - set(write)
        if missing:
            findings.append(f"{wid}: missing fields {sorted(missing)}")
            continue
        if write["tool"] not in TOOLS:
            findings.append(f"{wid}: unknown tool {write['tool']}")
        if write["surface"] not in SURFACES:
            findings.append(f"{wid}: unknown surface {write['surface']}")
        if write["file"] not in USER_FILES:
            findings.append(f"{wid}: writes {write['file']}, which is not a user-level file")
        if re.search(r"\.claude/settings|\.codex/config|\.github/copilot|managed", write["file"]) and not write["file"].startswith("~/"):
            findings.append(f"{wid}: targets a project-level or managed file")
        for layer in write["override_layers"]:
            if layer.get("kind") not in LAYER_KINDS or not layer.get("fix") or not layer.get("locator"):
                findings.append(f"{wid}: malformed override layer {layer.get('locator')}")
        source = write["source"]
        if write["kind"] == "vendor":
            if not str(source.get("url", "")).startswith("https://") or not ISO_DATE.match(str(source.get("fetched", ""))):
                findings.append(f"{wid}: vendor write needs an https source url and an ISO fetched date")
        elif not (root / source.get("decision", "missing")).is_file():
            findings.append(f"{wid}: internal write cites a decision record that does not exist")
        if write["admission"] == "admitted":
            ids = write.get("proof") or []
            if not ids or any(rid not in proven for rid in ids):
                findings.append(f"{wid}: admitted without a proven proof-matrix row ({ids})")
            if not write["proven_versions"]:
                findings.append(f"{wid}: admitted without a proven tool-version range")
        elif write["admission"] == "not-settable":
            if not write.get("not_settable_reason"):
                findings.append(f"{wid}: Not-Settable without a reason")
            if write.get("proof"):
                findings.append(f"{wid}: Not-Settable write must not carry a Proof Record")
        else:
            findings.append(f"{wid}: admission must be admitted or not-settable")
        values = _native_values(write)
        if write["tool"] == "codex" and write["key_path"] == ["approval_policy"] and "untrusted" in values:
            findings.append(f"{wid}: untrusted is retired and must never be mapped")
        mapped = list(write["value_map"].values())
        if write["tool"] in ("claude", "copilot-cli") and write["key_path"][-1] == "effortLevel" and ("max" in values or "max" in mapped):
            findings.append(f"{wid}: max must never be a default effort")
        if write["tool"] == "codex" and write["key_path"] == ["approval_policy"] and "untrusted" in mapped:
            findings.append(f"{wid}: untrusted is mapped")
        key = (write["tool"], write["file"], tuple(write["key_path"]))
        if key in seen_paths and key[2] != ("<none documented>",):
            findings.append(f"{wid}: same key path as {seen_paths[key]}")
        seen_paths[key] = wid
        omitted = catalog["omitted_keys"].get(write["tool"], [])
        allowed_exception = exceptions.get(write["tool"], [])
        joined = _joined(write)
        for name in omitted:
            if (joined == name or joined.startswith(name + ".")) and joined not in allowed_exception:
                findings.append(f"{wid}: targets omitted key {name}")
        for native in values + [v for v in mapped if isinstance(v, (str, bool))]:
            if isinstance(native, (str, bool)) and (write["tool"], joined, native) in WEAKENING_NATIVE and not write["weakens_safety"]:
                findings.append(f"{wid}: {native!r} lowers a safety barrier but weakens_safety is false")
        if write["weakens_safety"] and not write["weakening_values"]:
            findings.append(f"{wid}: weakens_safety without weakening_values")
        if write["tool"] == "codex" and write["key_path"] in (["approval_policy"], ["sandbox_mode"]) and write.get("applies_only_without") != ["default_permissions"]:
            findings.append(f"{wid}: Codex posture write must declare applies_only_without default_permissions")
    findings += _shared_key_findings(catalog, root)
    findings += _control_findings(catalog)
    return findings


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


def _control_findings(catalog: dict) -> list[str]:
    ids = {w["id"] for w in catalog["writes"]}
    claimed = [wid for control in catalog["controls"] for wid in control["writes"]]
    findings = [f"control references unknown write {wid}" for wid in claimed if wid not in ids]
    findings += [f"write {wid} belongs to no control" for wid in sorted(ids - set(claimed))]
    for tool, info in catalog["tools"].items():
        if "cannot_remove" not in info or "agent_session_markers" not in info:
            findings.append(f"tool {tool} lacks cannot_remove or agent_session_markers")
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
