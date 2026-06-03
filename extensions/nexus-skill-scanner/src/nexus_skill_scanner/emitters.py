"""Output emitters: terminal, JSON, Markdown, and SARIF.

Each emitter renders a ``ScanResult`` to a string. SARIF (v2.1.0) is the
machine format for CI / IDE integration (GitHub code scanning); JSON is the
generic structured format; Markdown is for human-readable reports; terminal is
the default interactive output.
"""

from __future__ import annotations

import json

from .frameworks import DETECTION_CLASSES
from .types import Finding, ScanResult, Severity

_SEVERITY_ORDER = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]


def _sorted_for_display(findings: list[Finding]) -> list[Finding]:
    return sorted(
        findings,
        key=lambda f: (-f.severity.rank, f.detection_class, f.file, f.line),
    )


def emit_terminal(result: ScanResult, *, use_color: bool = False) -> str:
    counts = result.counts_by_severity()
    lines: list[str] = []
    lines.append(f"Skill-security scan: {result.target}")
    lines.append(
        f"  files scanned: {result.files_scanned}   "
        f"findings: {len(result.findings)}   "
        f"score: {result.score}/100 ({result.band.label.upper()})"
    )
    summary = "  ".join(f"{s.label}={counts[s.label]}" for s in _SEVERITY_ORDER)
    lines.append(f"  severity: {summary}")
    if result.skipped_modules:
        lines.append(f"  skipped modules: {', '.join(result.skipped_modules)}")
    lines.append("")
    if not result.findings:
        lines.append("  No findings.")
        return "\n".join(lines)
    for f in _sorted_for_display(result.findings):
        lines.append(
            f"  [{f.severity.label.upper():8}] class {f.detection_class:2} "
            f"{f.class_name} - {f.title}"
        )
        lines.append(f"             {f.location()}")
        if f.snippet:
            lines.append(f"             > {f.snippet}")
        lines.append(f"             {f.message}")
        if f.framework_ids:
            lines.append(f"             frameworks: {', '.join(f.framework_ids)}")
        lines.append("")
    return "\n".join(lines)


def _finding_to_dict(f: Finding) -> dict:
    return {
        "detection_class": f.detection_class,
        "class_name": f.class_name,
        "severity": f.severity.label,
        "title": f.title,
        "message": f.message,
        "file": f.file,
        "line": f.line,
        "snippet": f.snippet,
        "framework_ids": list(f.framework_ids),
        "executable": f.executable,
        "analyzer": f.analyzer,
    }


def emit_json(result: ScanResult) -> str:
    payload = {
        "target": result.target,
        "files_scanned": result.files_scanned,
        "score": result.score,
        "band": result.band.label,
        "severity_counts": result.counts_by_severity(),
        "skipped_modules": result.skipped_modules,
        "findings": [_finding_to_dict(f) for f in _sorted_for_display(result.findings)],
    }
    return json.dumps(payload, indent=2)


def emit_markdown(result: ScanResult) -> str:
    counts = result.counts_by_severity()
    out: list[str] = []
    out.append(f"# Skill-Security Scan Report")
    out.append("")
    out.append(f"**Target**: {result.target}")
    out.append("")
    out.append(f"**Risk score**: {result.score}/100 ({result.band.label.upper()})")
    out.append("")
    out.append(f"**Files scanned**: {result.files_scanned}")
    out.append("")
    out.append("## Summary")
    out.append("")
    out.append("| Severity | Count |")
    out.append("|---|---|")
    for s in _SEVERITY_ORDER:
        out.append(f"| {s.label.upper()} | {counts[s.label]} |")
    out.append("")
    if not result.findings:
        out.append("No findings.")
        out.append("")
        return "\n".join(out)
    out.append("## Findings")
    out.append("")
    out.append("| Severity | Class | Title | Location | Frameworks |")
    out.append("|---|---|---|---|---|")
    for f in _sorted_for_display(result.findings):
        frameworks = ", ".join(f.framework_ids) or "-"
        title = f.title.replace("|", "\\|")
        out.append(
            f"| {f.severity.label.upper()} | {f.detection_class} {f.class_name} "
            f"| {title} | `{f.location()}` | {frameworks} |"
        )
    out.append("")
    out.append("## Detail")
    out.append("")
    for f in _sorted_for_display(result.findings):
        out.append(f"### [{f.severity.label.upper()}] {f.class_name}: {f.title}")
        out.append("")
        out.append(f"- **Location**: `{f.location()}`")
        out.append(f"- **Frameworks**: {', '.join(f.framework_ids) or '-'}")
        if f.snippet:
            out.append(f"- **Match**: `{f.snippet}`")
        out.append(f"- **Why**: {f.message}")
        out.append("")
    return "\n".join(out)


_SARIF_LEVEL = {
    "critical": "error",
    "high": "error",
    "medium": "warning",
    "low": "note",
}


def emit_sarif(result: ScanResult) -> str:
    """SARIF v2.1.0 for GitHub code scanning / IDE integration."""
    rules: dict[str, dict] = {}
    for num, dc in DETECTION_CLASSES.items():
        rule_id = f"NSS-{num:02d}"
        rules[rule_id] = {
            "id": rule_id,
            "name": dc.name.replace(" ", ""),
            "shortDescription": {"text": dc.name},
            "properties": {"frameworks": list(dc.framework_ids)},
        }
    results = []
    for f in _sorted_for_display(result.findings):
        rule_id = f"NSS-{f.detection_class:02d}"
        results.append({
            "ruleId": rule_id,
            "level": _SARIF_LEVEL.get(f.severity.label, "warning"),
            "message": {"text": f"{f.title}: {f.message}"},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": f.file},
                    "region": {"startLine": max(1, f.line)},
                }
            }],
            "properties": {
                "severity": f.severity.label,
                "detectionClass": f.detection_class,
                "frameworks": list(f.framework_ids),
                "analyzer": f.analyzer,
            },
        })
    sarif = {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [{
            "tool": {
                "driver": {
                    "name": "nexus-skill-scanner",
                    "informationUri": "https://github.com/bendourthe/Nexus-Hub",
                    "version": "3.0.0",
                    "rules": list(rules.values()),
                }
            },
            "results": results,
        }],
    }
    return json.dumps(sarif, indent=2)


EMITTERS = {
    "terminal": emit_terminal,
    "json": emit_json,
    "markdown": emit_markdown,
    "sarif": emit_sarif,
}


def render(result: ScanResult, fmt: str) -> str:
    fmt = fmt.lower()
    if fmt not in EMITTERS:
        raise ValueError(f"unknown format: {fmt!r} (choose from {sorted(EMITTERS)})")
    return EMITTERS[fmt](result)
