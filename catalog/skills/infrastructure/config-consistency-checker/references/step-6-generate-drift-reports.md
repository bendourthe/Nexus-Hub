### Step 6: Generate Drift Reports

**Drift Report Generator** (`scripts/generate_drift_report.py`):

```python
"""Generate a human-readable drift report from comparison findings."""
import json
import sys
from datetime import datetime, timezone


def generate_markdown_report(
    findings: list[dict],
    schema_violations: dict[str, list[dict]] | None = None,
) -> str:
    """Generate a Markdown drift report."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = []
    lines.append("# Configuration Drift Report")
    lines.append("")
    lines.append(f"**Generated**: {now}")
    lines.append("")

    # Summary
    critical = [f for f in findings if f["severity"] == "critical"]
    warnings = [f for f in findings if f["severity"] == "warning"]
    info = [f for f in findings if f["severity"] == "info"]

    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Severity | Count |")
    lines.append(f"|----------|-------|")
    lines.append(f"| Critical | {len(critical)} |")
    lines.append(f"| Warning  | {len(warnings)} |")
    lines.append(f"| Info     | {len(info)} |")
    lines.append(f"| **Total** | **{len(findings)}** |")
    lines.append("")

    if not findings:
        lines.append("No configuration drift detected. All environments are consistent.")
        return "\n".join(lines)

    # Critical findings
    if critical:
        lines.append("## Critical Findings")
        lines.append("")
        lines.append("These issues will likely cause failures in the affected environments.")
        lines.append("")
        for f in critical:
            lines.append(f"### {f['key']}")
            lines.append("")
            lines.append(f"**Type**: {f['finding_type']}")
            lines.append(f"**Issue**: {f['message']}")
            lines.append("")
            if f.get("environments"):
                lines.append("| Environment | Value |")
                lines.append("|-------------|-------|")
                for env, val in f["environments"].items():
                    display_val = str(val)
                    if len(display_val) > 60:
                        display_val = display_val[:57] + "..."
                    lines.append(f"| {env} | `{display_val}` |")
                lines.append("")
            lines.append(f"**Remediation**: {f['remediation']}")
            lines.append("")

    # Warning findings
    if warnings:
        lines.append("## Warnings")
        lines.append("")
        lines.append("These issues may cause unexpected behavior or indicate configuration debt.")
        lines.append("")
        for f in warnings:
            lines.append(f"- **{f['key']}** ({f['finding_type']}): {f['message']}")
            if f.get("remediation"):
                lines.append(f"  - Remediation: {f['remediation']}")
        lines.append("")

    # Info findings
    if info:
        lines.append("## Informational")
        lines.append("")
        lines.append("These findings are non-critical but worth reviewing.")
        lines.append("")
        for f in info:
            lines.append(f"- **{f['key']}**: {f['message']}")
        lines.append("")

    # Schema violations
    if schema_violations:
        lines.append("## Schema Violations")
        lines.append("")
        for env, violations in schema_violations.items():
            if not violations:
                continue
            lines.append(f"### {env}")
            lines.append("")
            for v in violations:
                lines.append(f"- **{v['key']}**: {v['message']} (current value: `{v['value']}`)")
            lines.append("")

    return "\n".join(lines)


def generate_json_report(findings: list[dict]) -> str:
    """Generate a machine-readable JSON report."""
    now = datetime.now(timezone.utc).isoformat()
    report = {
        "generated_at": now,
        "total_findings": len(findings),
        "by_severity": {
            "critical": [f for f in findings if f["severity"] == "critical"],
            "warning": [f for f in findings if f["severity"] == "warning"],
            "info": [f for f in findings if f["severity"] == "info"],
        },
        "by_type": {},
    }

    for f in findings:
        ftype = f["finding_type"]
        report["by_type"].setdefault(ftype, []).append(f)

    return json.dumps(report, indent=2, default=str)


if __name__ == "__main__":
    findings_path = sys.argv[1] if len(sys.argv) > 1 else "config_findings.json"
    output_format = sys.argv[2] if len(sys.argv) > 2 else "markdown"
    output_path = sys.argv[3] if len(sys.argv) > 3 else "drift_report.md"

    with open(findings_path) as f:
        findings = json.load(f)

    if output_format == "json":
        report = generate_json_report(findings)
        output_path = output_path.replace(".md", ".json")
    else:
        report = generate_markdown_report(findings)

    with open(output_path, "w") as f:
        f.write(report)

    print(f"Drift report written to {output_path}")
```
