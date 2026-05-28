#!/usr/bin/env python3
"""harness_audit.py -- deterministic read-only scoring of installed integrations.

Reads the install-state manifest at `<target>/.nexus-hub/install-manifest.json`
and the running integration registry, then emits a per-integration reliability
score plus an aggregate score. Zero outbound calls, zero writes.

Score axes (each 0.0 -- 1.0):

    presence         -- recorded files that still exist on disk
    integrity        -- recorded SHA-256 hashes that still match current bytes
    coverage         -- expected surface (skills / commands / hooks / rules)
                        the integration declared in `config` vs. what the
                        manifest actually recorded
    marker_integrity -- shared instruction files whose marker block is intact

The four axes are combined into a single 0-100 score per integration via the
weights in `DEFAULT_WEIGHTS`. The aggregate score is the mean of the per-
integration scores. Output is Markdown by default; pass `--json` for a
machine-readable variant.

Usage:

    python scripts/harness_audit.py
    python scripts/harness_audit.py --target /path/to/project --json
    python scripts/harness_audit.py --integrations claude,gemini
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.integrations import INTEGRATION_REGISTRY  # noqa: E402
from scripts.lib.integrations.lifecycle import (  # noqa: E402
    DIAGNOSTIC_DRIFTED,
    DIAGNOSTIC_MISSING,
    DIAGNOSTIC_OK,
    doctor as lifecycle_doctor,
)
from scripts.lib.integrations.manifest import InstallManifest  # noqa: E402


# Weights for the four scoring axes. Sum to 1.0 so the per-integration score
# stays in [0, 100]. Tunable below in the user-contribution slot.
DEFAULT_WEIGHTS = {
    "presence": 0.30,
    "integrity": 0.30,
    "coverage": 0.20,
    "marker_integrity": 0.20,
}


# Config keys that signal an integration declared a surface area we can audit.
# An integration with three of these declared and none recorded would score
# low on `coverage` even if everything it DID write is intact.
SURFACE_KEYS = (
    "instruction_file",
    "skills_subdir",
    "commands_subdir",
    "agents_subdir",
    "rules_subdir",
    "hooks_subdir",
)


@dataclass
class IntegrationAudit:
    key: str
    display_name: str
    recorded_files: int
    present: int
    drifted: int
    missing: int
    declared_surfaces: int
    recorded_surfaces: int
    shared_files: List[str] = field(default_factory=list)
    shared_files_with_marker: int = 0
    score: float = 0.0
    axes: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        return {
            "key": self.key,
            "display_name": self.display_name,
            "recorded_files": self.recorded_files,
            "present": self.present,
            "drifted": self.drifted,
            "missing": self.missing,
            "declared_surfaces": self.declared_surfaces,
            "recorded_surfaces": self.recorded_surfaces,
            "shared_files": self.shared_files,
            "shared_files_with_marker": self.shared_files_with_marker,
            "score": round(self.score, 2),
            "axes": {k: round(v, 4) for k, v in self.axes.items()},
        }


@dataclass
class AuditReport:
    target: str
    manifest_path: str
    integrations: List[IntegrationAudit] = field(default_factory=list)
    weights: Dict[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))

    def aggregate(self) -> float:
        if not self.integrations:
            return 0.0
        return sum(i.score for i in self.integrations) / len(self.integrations)

    def to_dict(self) -> Dict[str, object]:
        return {
            "target": self.target,
            "manifest_path": self.manifest_path,
            "weights": self.weights,
            "aggregate_score": round(self.aggregate(), 2),
            "integrations": [i.to_dict() for i in self.integrations],
        }


# --------------------------------------------------------------------------- #
# Per-axis scoring
# --------------------------------------------------------------------------- #


def _has_marker(path: Path) -> bool:
    """Return True if `path` exists and contains the canonical Nexus-Hub
    marker pair. False if either marker is missing or the file is unreadable.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    return (
        "<!-- nexus-hub:start -->" in text
        and "<!-- nexus-hub:end -->" in text
    )


def _audit_one(
    key: str,
    manifest: InstallManifest,
    weights: Dict[str, float],
) -> Optional[IntegrationAudit]:
    if key not in INTEGRATION_REGISTRY:
        return None
    integ = INTEGRATION_REGISTRY[key]
    records = manifest.actions_for(key)
    report = lifecycle_doctor(manifest, [key])
    findings = report.findings_for(key)
    present = sum(1 for f in findings if f.diagnostic == DIAGNOSTIC_OK)
    drifted = sum(1 for f in findings if f.diagnostic == DIAGNOSTIC_DRIFTED)
    missing = sum(1 for f in findings if f.diagnostic == DIAGNOSTIC_MISSING)
    auditable = present + drifted + missing

    declared = sum(1 for k in SURFACE_KEYS if integ.config.get(k))
    # Heuristic: every recorded file path that contains the declared surface
    # name (subdir suffix) counts as covering that surface.
    surface_hits: set = set()
    for k in SURFACE_KEYS:
        sub = integ.config.get(k)
        if not sub:
            continue
        needle = str(sub).lower()
        for rec in records:
            if needle and needle in str(rec.get("path", "")).lower():
                surface_hits.add(k)
                break
    # Also count the instruction_file by its own name.
    instr = integ.config.get("instruction_file")
    if instr:
        for rec in records:
            if str(instr).lower() in str(rec.get("path", "")).lower():
                surface_hits.add("instruction_file")
                break
    recorded_surfaces = len(surface_hits)

    shared = manifest.shared_for(key)
    shared_intact = sum(1 for p in shared if _has_marker(Path(p)))

    # Axis scores (0.0 -- 1.0, gracefully degrading when the denominator is 0).
    axis_presence = (present + drifted) / auditable if auditable else 1.0
    axis_integrity = present / auditable if auditable else 1.0
    axis_coverage = recorded_surfaces / declared if declared else 1.0
    axis_marker = shared_intact / len(shared) if shared else 1.0
    axes = {
        "presence": axis_presence,
        "integrity": axis_integrity,
        "coverage": axis_coverage,
        "marker_integrity": axis_marker,
    }

    # ----- BEGIN user-contribution slot: how do we combine the axes? --------
    # The default combines them as a weighted average using `weights`. You
    # may prefer a multiplicative model (any zero axis tanks the score), a
    # quadratic penalty on drift, or a configurable floor for marker
    # integrity. Keep the output in [0, 100].
    score = 100.0 * sum(axes[k] * weights.get(k, 0.0) for k in axes)
    # ----- END user-contribution slot ---------------------------------------

    return IntegrationAudit(
        key=key,
        display_name=integ.display_name or key,
        recorded_files=len(records),
        present=present,
        drifted=drifted,
        missing=missing,
        declared_surfaces=declared,
        recorded_surfaces=recorded_surfaces,
        shared_files=list(shared),
        shared_files_with_marker=shared_intact,
        score=score,
        axes=axes,
    )


def audit(
    target_root: Path,
    requested: Optional[List[str]] = None,
    weights: Optional[Dict[str, float]] = None,
) -> AuditReport:
    """Build an `AuditReport` for `target_root`'s install manifest."""
    manifest_path = target_root / ".nexus-hub" / "install-manifest.json"
    report = AuditReport(
        target=str(target_root),
        manifest_path=str(manifest_path),
        weights=dict(weights or DEFAULT_WEIGHTS),
    )
    if not manifest_path.exists():
        return report
    manifest = InstallManifest.load(manifest_path)
    keys = requested or manifest.all_action_keys()
    for key in keys:
        audit_entry = _audit_one(key, manifest, report.weights)
        if audit_entry is not None:
            report.integrations.append(audit_entry)
    return report


# --------------------------------------------------------------------------- #
# Formatters
# --------------------------------------------------------------------------- #


def _format_markdown(report: AuditReport) -> str:
    lines: List[str] = []
    lines.append(f"# Nexus-Hub Harness Audit")
    lines.append("")
    lines.append(f"- Target: `{report.target}`")
    lines.append(f"- Manifest: `{report.manifest_path}`")
    lines.append(f"- Aggregate score: **{report.aggregate():.1f} / 100**")
    lines.append("")
    if not report.integrations:
        lines.append("_(no integrations recorded -- run installer first)_")
        return "\n".join(lines) + "\n"
    lines.append("## Per-integration scores")
    lines.append("")
    lines.append("| Integration | Score | Files | Present | Drifted | Missing | Surfaces | Markers OK |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---|")
    for i in report.integrations:
        surfaces = f"{i.recorded_surfaces}/{i.declared_surfaces}"
        markers = f"{i.shared_files_with_marker}/{len(i.shared_files)}" if i.shared_files else "n/a"
        lines.append(
            f"| `{i.key}` | {i.score:.1f} | {i.recorded_files} | "
            f"{i.present} | {i.drifted} | {i.missing} | {surfaces} | {markers} |"
        )
    lines.append("")
    lines.append("## Axis weights")
    lines.append("")
    for axis, w in report.weights.items():
        lines.append(f"- `{axis}`: {w:.2f}")
    lines.append("")
    return "\n".join(lines) + "\n"


def _format_json(report: AuditReport) -> str:
    return json.dumps(report.to_dict(), indent=2, default=str)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="nexus-hub-harness-audit",
        description=(
            "Read-only deterministic scoring of installed integrations. "
            "Reads the install-state manifest and the running registry; "
            "writes nothing."
        ),
    )
    parser.add_argument(
        "--target",
        help="Workspace root (defaults to CWD).",
    )
    parser.add_argument(
        "--integrations",
        help="Comma-separated keys (default: every integration in the manifest).",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown.")
    parser.add_argument(
        "--min-score",
        type=float,
        default=None,
        help="Exit 1 if the aggregate score falls below this threshold (0-100).",
    )
    args = parser.parse_args(argv)
    target_root = (
        Path(args.target).expanduser().resolve() if args.target else Path.cwd().resolve()
    )
    requested = (
        [k.strip() for k in args.integrations.split(",") if k.strip()]
        if args.integrations
        else None
    )
    report = audit(target_root, requested)
    if args.json:
        print(_format_json(report))
    else:
        sys.stdout.write(_format_markdown(report))
    if args.min_score is not None and report.aggregate() < args.min_score:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
