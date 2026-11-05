"""Catalog loader and structural validator for the Nexus-Hub Settings engine.

`catalog.json` is the only list of what the engine may write or report. This
module loads it and applies every rule that needs nothing outside the file, so
the same rules guard the repository gate (`tests/validators/`) and an installed
tree, which carries no proof matrix, `configs/`, or decision records. Checks that
need those repository files stay in the validator test. A catalog that is missing
or breaks a rule is refused with the findings; the engine never falls back to
built-in guesses.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PACKAGE_DIR = Path(__file__).resolve().parent
CATALOG_PATH = PACKAGE_DIR / "catalog.json"
CLAUDE_IDS_PATH = PACKAGE_DIR / "claude_model_ids.json"

TOOLS = {"claude", "codex", "copilot-cli", "vscode-copilot", "internal"}
SURFACES = {"cli", "vscode-host", "desktop"}
LAYER_KINDS = {"env", "project-file", "managed-file", "policy", "remembered-ui"}

#: Catalog `file` value -> reader file id. `vscode-config` has no file: the
#: editor owns it and the CLI never parses it.
USER_FILE_IDS: dict[str, str | None] = {
    "~/.claude/settings.json": "claude-user",
    "~/.codex/config.toml": "codex-user",
    "~/.copilot/settings.json": "copilot-user",
    "~/.nexus-hub/guardrails.json": "nexus-guardrails",
    "~/.nexus-hub/preferences.json": "nexus-preferences",
    "vscode-config": None,
}
#: Every file id a layer may name. The reader owns the path of each.
FILE_IDS = frozenset(
    {
        "claude-user", "claude-project", "claude-project-local", "claude-managed",
        "codex-user", "codex-project",
        "copilot-user", "copilot-repo", "copilot-repo-local",
        "nexus-guardrails", "nexus-preferences",
    }
)
DIR_IDS = frozenset({"claude-dir", "codex-dir", "copilot-dir"})

REQUIRED_WRITE_KEYS = {
    "id", "kind", "tool", "surface", "file", "key_path", "values", "value_map",
    "override_layers", "takes_effect", "proven_versions", "weakens_safety",
    "weakening_values", "source", "admission",
}
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
    ("internal", "block_dangerous_git", False),
    ("internal", "scan_secrets", False),
    ("internal", "protect_user_edits", False),
}
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
MODEL_ID_SEGMENT = "<model-id>"
NOT_DOCUMENTED = "<none documented>"


class CatalogError(Exception):
    """The catalog is missing, unreadable, or breaks a rule."""

    def __init__(self, findings: list[str]) -> None:
        super().__init__("; ".join(findings))
        self.findings = findings


@dataclass(frozen=True)
class Group:
    """The writes one control makes on one tool surface, in catalog order."""

    control: dict[str, Any]
    tool: str
    surface: str
    writes: tuple[dict[str, Any], ...]


def _native_values(write: dict[str, Any]) -> list[Any]:
    values = write["values"]
    return values if isinstance(values, list) else []


def joined_key(write: dict[str, Any]) -> str:
    return ".".join(str(part) for part in write["key_path"])


def _detect_findings(wid: str, layer: dict[str, Any]) -> list[str]:
    detect = layer.get("detect")
    if not isinstance(detect, dict):
        return [f"{wid}: override layer {layer.get('locator')} has no detect spec"]
    forms = [name for name in ("caveat", "skip") if name in detect]
    forms += ["probe"] if ("env" in detect or "files" in detect) else []
    if len(forms) != 1:
        return [f"{wid}: detect spec of layer {layer.get('locator')} must be exactly one of env/files, caveat, or skip"]
    if "caveat" in detect or "skip" in detect:
        text = detect.get("caveat", detect.get("skip"))
        return [] if isinstance(text, str) and text.strip() else [f"{wid}: caveat or skip text is empty"]
    findings: list[str] = []
    names = detect.get("env", [])
    if not isinstance(names, list) or any(not isinstance(n, str) or not ENV_NAME.match(n) for n in names):
        findings.append(f"{wid}: detect env names must be upper-case variable names")
    for field in ("settings_env", "files"):
        ids = detect.get(field, [])
        if not isinstance(ids, list) or any(i not in FILE_IDS for i in ids):
            findings.append(f"{wid}: detect {field} names an unknown file id")
    if detect.get("settings_env") and not names:
        findings.append(f"{wid}: settings_env needs env names")
    if "files" in detect:
        paths = detect.get("key_paths")
        if not detect["files"] or not paths or any(not isinstance(p, list) or not p for p in paths):
            findings.append(f"{wid}: detect files need key_paths")
    for field in ("when_value_in", "ignored_values"):
        if field in detect and not isinstance(detect[field], list):
            findings.append(f"{wid}: detect {field} must be a list")
    return findings


def validate_structure(catalog: dict[str, Any]) -> list[str]:
    """Return one finding per rule violation that needs nothing outside the catalog."""
    findings: list[str] = []
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
        if write["file"] not in USER_FILE_IDS:
            findings.append(f"{wid}: writes {write['file']}, which is not a user-level file")
        if re.search(r"\.claude/settings|\.codex/config|\.github/copilot|managed", write["file"]) and not write["file"].startswith("~/"):
            findings.append(f"{wid}: targets a project-level or managed file")
        for layer in write["override_layers"]:
            if layer.get("kind") not in LAYER_KINDS or not layer.get("fix") or not layer.get("locator"):
                findings.append(f"{wid}: malformed override layer {layer.get('locator')}")
            else:
                findings += _detect_findings(wid, layer)
        source = write["source"]
        if write["kind"] == "vendor":
            if not str(source.get("url", "")).startswith("https://") or not ISO_DATE.match(str(source.get("fetched", ""))):
                findings.append(f"{wid}: vendor write needs an https source url and an ISO fetched date")
        elif not str(source.get("decision", "")).strip():
            findings.append(f"{wid}: internal write must cite its decision record")
        if write["admission"] == "admitted":
            if not write.get("proof"):
                findings.append(f"{wid}: admitted without a proven proof-matrix row ({write.get('proof') or []})")
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
        if "default" in write and (write["kind"] != "internal" or not any(type(write["default"]) is type(v) and write["default"] == v for v in values)):
            findings.append(f"{wid}: default must be an allowed internal native value")
        if "only_when_present" in write and not isinstance(write["only_when_present"], bool):
            findings.append(f"{wid}: only_when_present must be boolean")
        if write["tool"] == "codex" and write["key_path"] == ["approval_policy"] and "untrusted" in values:
            findings.append(f"{wid}: untrusted is retired and must never be mapped")
        mapped = list(write["value_map"].values())
        if write["tool"] in ("claude", "copilot-cli") and write["key_path"][-1] == "effortLevel" and ("max" in values or "max" in mapped):
            findings.append(f"{wid}: max must never be a default effort")
        if write["tool"] == "codex" and write["key_path"] == ["approval_policy"] and "untrusted" in mapped:
            findings.append(f"{wid}: untrusted is mapped")
        key = (write["tool"], write["file"], tuple(write["key_path"]))
        if key in seen_paths and key[2] != (NOT_DOCUMENTED,):
            findings.append(f"{wid}: same key path as {seen_paths[key]}")
        seen_paths[key] = wid
        omitted = catalog["omitted_keys"].get(write["tool"], [])
        allowed_exception = exceptions.get(write["tool"], [])
        joined = joined_key(write)
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
    findings += _control_findings(catalog)
    findings += _removable_findings(catalog)
    return findings


def _removable_findings(catalog: dict[str, Any]) -> list[str]:
    """Rules for `removable_overrides`: the only keys `remove-override` may delete."""
    findings: list[str] = []
    controls = {c["id"] for c in catalog["controls"]}
    seen: set[str] = set()
    for row in catalog.get("removable_overrides", []):
        rid = row.get("id", "<no id>")
        if rid in seen:
            findings.append(f"removable override {rid} is listed twice")
        seen.add(rid)
        if row.get("control") not in controls:
            findings.append(f"removable override {rid} names unknown control {row.get('control')}")
        if row.get("tool") not in catalog["tools"]:
            findings.append(f"removable override {rid} names unknown tool {row.get('tool')}")
        if USER_FILE_IDS.get(row.get("file")) is None:
            findings.append(f"removable override {rid} must name a user-level file")
        path = row.get("key_path")
        if not isinstance(path, list) or not path or not all(isinstance(p, str) and p for p in path) or MODEL_ID_SEGMENT in path:
            findings.append(f"removable override {rid} needs a literal key path")
        if not isinstance(row.get("weakens_safety"), bool):
            findings.append(f"removable override {rid} needs a boolean weakens_safety")
        if not str(row.get("reason", "")).strip():
            findings.append(f"removable override {rid} needs a reason")
        source = row.get("source", {})
        if not str(source.get("url", "")).startswith("https://") or not ISO_DATE.match(str(source.get("fetched", ""))):
            findings.append(f"removable override {rid} needs an https source url and an ISO fetched date")
    return findings


def _control_findings(catalog: dict[str, Any]) -> list[str]:
    ids = {w["id"] for w in catalog["writes"] if "id" in w}
    claimed = [wid for control in catalog["controls"] for wid in control["writes"]]
    findings = [f"control references unknown write {wid}" for wid in claimed if wid not in ids]
    findings += [f"write {wid} belongs to no control" for wid in sorted(ids - set(claimed))]
    for tool, info in catalog["tools"].items():
        if "cannot_remove" not in info or "agent_session_markers" not in info:
            findings.append(f"tool {tool} lacks cannot_remove or agent_session_markers")
        detect = info.get("detect")
        if not isinstance(detect, dict) or not str(detect.get("command", "")).strip():
            findings.append(f"tool {tool} lacks a detect command")
        elif "config_dir" in detect and detect["config_dir"] not in DIR_IDS:
            findings.append(f"tool {tool} names an unknown config_dir")
    return findings


def load_catalog(path: Path | None = None) -> dict[str, Any]:
    """Load and validate the catalog; raise `CatalogError` with every finding."""
    target = path or CATALOG_PATH
    try:
        catalog = json.loads(target.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CatalogError([f"catalog {target.name} cannot be read ({exc.strerror or exc})"]) from exc
    except ValueError as exc:
        raise CatalogError([f"catalog {target.name} is not valid JSON ({exc})"]) from exc
    try:
        findings = validate_structure(catalog)
    except (KeyError, TypeError, AttributeError) as exc:
        raise CatalogError([f"catalog {target.name} has the wrong shape ({type(exc).__name__}: {exc})"]) from exc
    if findings:
        raise CatalogError(findings)
    return catalog


def load_claude_model_ids(path: Path | None = None) -> list[str]:
    """The bundled list of current Claude model ids (Anthropic column of the model map)."""
    target = path or CLAUDE_IDS_PATH
    try:
        ids = json.loads(target.read_text(encoding="utf-8"))["ids"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise CatalogError([f"{target.name} cannot be read as a list of ids ({exc})"]) from exc
    if not isinstance(ids, list) or not all(isinstance(i, str) and i for i in ids):
        raise CatalogError([f"{target.name} must hold a list of non-empty strings"])
    return ids


def write_groups(catalog: dict[str, Any]) -> list[Group]:
    """Group each control's writes by (tool, surface), keeping catalog order."""
    by_id = {w["id"]: w for w in catalog["writes"]}
    groups: list[Group] = []
    for control in catalog["controls"]:
        buckets: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for wid in control["writes"]:
            write = by_id[wid]
            buckets.setdefault((write["tool"], write["surface"]), []).append(write)
        groups += [Group(control, tool, surface, tuple(writes)) for (tool, surface), writes in buckets.items()]
    return groups
