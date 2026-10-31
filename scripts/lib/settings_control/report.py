"""Report assembly and plain-text rendering for `nexus-hub settings show` and `explain`.

Output is ASCII only so a Windows console never garbles it. Every sentence comes
from catalog text or a fixed template here.
"""
from __future__ import annotations

from typing import Any

from .readers import Snapshot

SCHEMA_VERSION = 1
_COLUMNS = ("control", "tool", "state", "value", "layer")


def build_report(catalog: dict[str, Any], snapshot: Snapshot, records: list[dict[str, Any]]) -> dict[str, Any]:
    """The JSON document `show --json` prints (validated by schema/show.schema.json)."""
    tools = {}
    for tool, info in catalog["tools"].items():
        state = snapshot.tools[tool]
        tools[tool] = {
            "label": info["label"], "installed": state.installed, "version": state.version,
            "cannot_remove": list(info["cannot_remove"]),
        }
    return {"schema_version": SCHEMA_VERSION, "project": snapshot.project, "platform": snapshot.platform, "tools": tools, "records": records}


def _state_text(record: dict[str, Any]) -> str:
    if record["state"] in ("not-covered", "unverified-for-version") and record["detail"]:
        return f"{record['state']} {record['detail']}"
    if record["state"] == "cannot-detect" and record["detail"]:
        return "cannot-detect"
    return record["state"]


def _row(record: dict[str, Any]) -> tuple[str, ...]:
    tool = record["tool"] if record["surface"] == "cli" else f"{record['tool']} ({record['surface']})"
    layer = f"{record['layer']} = {record['layer_value']}" if record["layer"] else "-"
    return (record["control"], tool, _state_text(record), record["value"] or "-", layer)


def render_table(report: dict[str, Any]) -> str:
    rows = [_COLUMNS] + [_row(r) for r in report["records"]]
    widths = [max(len(row[i]) for row in rows) for i in range(len(_COLUMNS))]
    lines = ["  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)).rstrip() for row in rows]
    lines.insert(1, "  ".join("-" * w for w in widths))
    notes: list[str] = []
    for record in report["records"]:
        name = f"{record['control']} / {record['tool']}" + ("" if record["surface"] == "cli" else f" ({record['surface']})")
        lines_for = []
        if record["state"] in ("not-settable", "cannot-detect") and record["detail"]:
            lines_for.append(f"{record['state']}: {record['detail']}")
        if record["fix"]:
            lines_for.append(f"fix: {record['fix']}")
        lines_for += [f"note: {c}" for c in record["caveats"]]
        if lines_for:
            notes.append(f"  {name}")
            notes += [f"    {text}" for text in lines_for]
    if notes:
        lines += ["", "Notes (every control is a default for NEW sessions only):"] + notes
    return "\n".join(lines)


def _write_data(write: dict[str, Any]) -> dict[str, Any]:
    data = {
        key: write[key]
        for key in (
            "id", "kind", "tool", "surface", "file", "key_path", "values", "value_map", "takes_effect",
            "proven_versions", "weakens_safety", "weakening_values", "source", "admission",
        )
    }
    for optional in ("proof", "not_settable_reason", "applies_only_without", "notes"):
        if optional in write:
            data[optional] = write[optional]
    data["override_layers"] = [{k: layer[k] for k in ("kind", "locator", "fix")} for layer in write["override_layers"]]
    return data


def explain_data(catalog: dict[str, Any], control_id: str) -> dict[str, Any]:
    """Everything the catalog says about one control. KeyError names the known ids."""
    controls = {c["id"]: c for c in catalog["controls"]}
    if control_id not in controls:
        raise KeyError(", ".join(controls))
    control = controls[control_id]
    by_id = {w["id"]: w for w in catalog["writes"]}
    writes = [_write_data(by_id[wid]) for wid in control["writes"]]
    used = sorted({w["tool"] for w in writes} & set(catalog["tools"]))
    tools = {t: {"label": catalog["tools"][t]["label"], "cannot_remove": list(catalog["tools"][t]["cannot_remove"])} for t in used}
    return {
        "control": {"id": control["id"], "label": control["label"], "values": control["values"]},
        "writes": writes, "tools": tools,
    }


def render_explain(data: dict[str, Any]) -> str:
    control = data["control"]
    lines = [f"{control['label']} ({control['id']}): values {control['values']}", ""]
    for write in data["writes"]:
        status = "settable" if write["admission"] == "admitted" else "not-settable"
        key = ".".join(str(p) for p in write["key_path"])
        lines.append(f"{write['id']}  [{status}]  {write['tool']} / {write['surface']}")
        lines.append(f"    file: {write['file']}  key: {key}")
        if write["value_map"]:
            lines.append("    value map: " + ", ".join(f"{k} -> {v}" for k, v in write["value_map"].items()))
        lines.append(f"    takes effect: {write['takes_effect']}")
        source = write["source"]
        lines.append("    source: " + (f"{source['url']} (fetched {source['fetched']})" if "url" in source else source["decision"]))
        if write["admission"] == "admitted":
            lines.append(f"    proof: {', '.join(write['proof'])}  proven versions: {write['proven_versions']}")
        else:
            lines.append(f"    why not settable: {write['not_settable_reason']}")
        if write["weakens_safety"]:
            lines.append(f"    weakens safety for: {', '.join(write['weakening_values'])}")
        for layer in write["override_layers"]:
            lines.append(f"    override [{layer['kind']}] {layer['locator']}")
            lines.append(f"        fix: {layer['fix']}")
        lines.append("")
    for tool in data["tools"].values():
        lines.append(f"Cannot remove ({tool['label']}):")
        lines += [f"    - {item}" for item in tool["cannot_remove"]]
    return "\n".join(lines).rstrip()
