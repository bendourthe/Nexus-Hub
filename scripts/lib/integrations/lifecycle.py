"""Install-state lifecycle helpers: doctor / repair / list_installed.

These three operations form the user-facing surface that v2.3.0 (Phase 4 / T010)
adds on top of the existing integration registry. They are deliberately
ADDITIVE: they read the manifest's recorded `FileAction` records (see
`manifest.record_actions`) and never replace the existing
`merge_marker_section` idempotency or the user-edit-preservation guarantees in
`MarkdownIntegration`.

- ``list_installed(manifest)`` -- enumerate what every integration wrote.
- ``doctor(ctx)``              -- diagnose drift / missing managed files.
- ``repair(ctx)``              -- re-write managed files reported as drifted
                                  or missing by ``doctor`` (delegates the
                                  re-write to each integration's ``install``
                                  so marker semantics are honored).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from . import INTEGRATION_REGISTRY, get
from .base import InstallContext
from .manifest import InstallManifest, _hash_path
from .result import WriteResult


# Action vocabulary stored in the manifest is the same six values as
# `result.VALID_ACTIONS`. `doctor` adds three diagnostic statuses describing
# the current on-disk state vs. the manifest record.
DIAGNOSTIC_OK = "ok"            # file present and content matches the recorded SHA-256
DIAGNOSTIC_MISSING = "missing"  # file was recorded but is no longer on disk
DIAGNOSTIC_DRIFTED = "drifted"  # file present but content differs from the recorded SHA-256
DIAGNOSTIC_UNKNOWN = "unknown"  # file recorded with no SHA-256 (e.g. directory tree summary)

# Manifest entries with these action values do not represent a file the runner
# wrote, so they are skipped by both `doctor` and `repair`.
SKIP_ACTIONS = frozenset({"not-found", "kept", "removed"})


@dataclass(frozen=True)
class DoctorFinding:
    """One per-file health check result returned by `doctor`."""

    integration_key: str
    path: str
    recorded_action: str
    diagnostic: str  # one of DIAGNOSTIC_* constants
    recorded_sha256: Optional[str]
    current_sha256: Optional[str]
    detail: Optional[str] = None


@dataclass
class DoctorReport:
    """Aggregated `doctor` output for one or more integrations."""

    findings: List[DoctorFinding] = field(default_factory=list)
    integrations_checked: List[str] = field(default_factory=list)
    integrations_unknown: List[str] = field(default_factory=list)

    def has_issues(self) -> bool:
        return any(
            f.diagnostic in (DIAGNOSTIC_MISSING, DIAGNOSTIC_DRIFTED)
            for f in self.findings
        )

    def counts(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for f in self.findings:
            out[f.diagnostic] = out.get(f.diagnostic, 0) + 1
        return out

    def findings_for(self, integration_key: str) -> List[DoctorFinding]:
        return [f for f in self.findings if f.integration_key == integration_key]


def _resolve_keys(manifest: InstallManifest, requested: Optional[List[str]]) -> List[str]:
    """Return the integration keys to operate on.

    If `requested` is None or empty, return every key the manifest has
    recorded actions for. Otherwise intersect the request with the manifest
    so we never fabricate diagnostics for an integration that was never
    installed.
    """
    available = manifest.all_action_keys()
    if not requested:
        return available
    return [k for k in requested if k in available]


def list_installed(manifest: InstallManifest) -> Dict[str, List[Dict[str, object]]]:
    """Return `{integration_key: [action_record, ...]}` for every integration
    in the manifest. Pure data; callers format it for stdout.
    """
    return {key: manifest.actions_for(key) for key in manifest.all_action_keys()}


def doctor(
    manifest: InstallManifest,
    requested: Optional[List[str]] = None,
) -> DoctorReport:
    """Diagnose drift / missing managed files against the recorded manifest.

    For each file recorded by `record_actions()`:

    * If the recorded action is in `SKIP_ACTIONS` (`not-found`, `kept`,
      `removed`), skip it -- the runner did not own that file.
    * If the recorded `sha256` is `None` (directory tree summary entry), emit
      `DIAGNOSTIC_UNKNOWN`. Tree-mirror integrations record one entry per
      tree, not per file, so the unknown-state response is intentional.
    * Else compare the recorded SHA-256 to the current on-disk content; emit
      `DIAGNOSTIC_OK` / `MISSING` / `DRIFTED` accordingly.
    """
    report = DoctorReport()
    requested_keys = requested or []
    if requested_keys:
        for key in requested_keys:
            if key not in manifest.all_action_keys():
                report.integrations_unknown.append(key)
    keys = _resolve_keys(manifest, requested_keys)
    for key in keys:
        report.integrations_checked.append(key)
        for record in manifest.actions_for(key):
            action = str(record.get("action", ""))
            path_str = str(record.get("path", ""))
            recorded_sha = record.get("sha256")
            if action in SKIP_ACTIONS:
                continue
            if recorded_sha is None:
                # No content hash recorded -- this is a tree summary or a
                # tracked directory. We surface it as `unknown` so the user
                # at least sees it in the report.
                current_sha = None
                current = Path(path_str)
                diagnostic = (
                    DIAGNOSTIC_UNKNOWN if current.exists() else DIAGNOSTIC_MISSING
                )
            else:
                current_sha = _hash_path(Path(path_str))
                if current_sha is None:
                    diagnostic = DIAGNOSTIC_MISSING
                elif current_sha == recorded_sha:
                    diagnostic = DIAGNOSTIC_OK
                else:
                    diagnostic = DIAGNOSTIC_DRIFTED
            report.findings.append(
                DoctorFinding(
                    integration_key=key,
                    path=path_str,
                    recorded_action=action,
                    diagnostic=diagnostic,
                    recorded_sha256=(
                        str(recorded_sha) if recorded_sha is not None else None
                    ),
                    current_sha256=current_sha,
                )
            )
    from .org_knowledge import diagnose_org_knowledge

    for finding in diagnose_org_knowledge(manifest, requested_keys or None):
        if finding.integration_key not in report.integrations_checked:
            report.integrations_checked.append(finding.integration_key)
        report.findings.append(
            DoctorFinding(
                integration_key=finding.integration_key,
                path=finding.path,
                recorded_action="org-knowledge",
                diagnostic=finding.diagnostic,
                recorded_sha256=None,
                current_sha256=None,
                detail=finding.detail,
            )
        )
    return report


def repair(
    ctx: InstallContext,
    requested: Optional[List[str]] = None,
) -> WriteResult:
    """Re-run `install` for every integration whose `doctor` report shows
    drift or missing managed files.

    The re-run goes through the regular `install()` path so that:

    * Marker-managed instruction files use `merge_marker_section` (user edits
      between the markers are still replaced; user edits OUTSIDE the markers
      are preserved -- the existing behavior).
    * Tree-mirror copies are idempotent (`unchanged` for already-good files).
    * Newly-missing files are recreated.

    `repair` does NOT attempt to roll back unrelated user edits in shared
    files; that is by design and matches the additive guarantee in the plan.
    """
    report = doctor(ctx.manifest, requested)
    affected: List[str] = []
    for key in report.integrations_checked:
        findings = report.findings_for(key)
        if any(
            f.diagnostic in (DIAGNOSTIC_MISSING, DIAGNOSTIC_DRIFTED)
            for f in findings
        ):
            affected.append(key)
    result = WriteResult()
    for key in affected:
        try:
            integ = get(key)
        except KeyError:
            result.note(f"[skip:{key}] not in registry; cannot repair")
            continue
        sub = integ.install(ctx)
        # Capture the new actions so the next `doctor` reflects the repair.
        ctx.manifest.record_actions(key, sub.files)
        result.extend(sub)
    if not affected:
        result.note("no integrations needed repair")
    return result


def render_stale(stale) -> List[str]:
    """One stale platform's plan as report lines: removed, trimmed, kept, and why.

    v4.14.7 Phase 5. `stale` is a `_stale.StalePlatform`; kept and trimmed items
    are listed (up to 20) because they are the ones a user must review.
    """
    from ._stale import KEEP, REMOVE, STRIP

    counts = stale.counts()
    lines = [
        f"  - {stale.display_name}: not detected ({stale.evidence})",
        f"    {counts.get(REMOVE, 0)} to remove, {counts.get(STRIP, 0)} to trim, "
        f"{counts.get(KEEP, 0)} kept for your review, under {stale.root}",
    ]
    shown = 0
    for entry in stale.entries:
        if entry.verdict in (KEEP, STRIP) and shown < 20:
            lines.append(f"      {entry.verdict}: {entry.path} ({entry.reason})")
            shown += 1
    return lines


def stale_report_lines(ctx: InstallContext, integrations) -> List[str]:
    """Doctor's stale-surface section (v4.14.7 Phase 5). Read-only.

    Lists every detection-gated platform that is not installed yet still has
    Nexus-Hub files recorded in the manifest, and points at the opt-in removal.
    """
    from ._stale import find_stale

    stale = find_stale(ctx, integrations)
    if not stale:
        return []
    lines = ["[doctor] stale Nexus-Hub surfaces for tools that are not installed:"]
    for platform in stale:
        lines.extend(render_stale(platform))
    lines.append("  Preview or remove them with `nexus-hub prune-undetected` (add --yes to remove).")
    return lines


def legacy_report_lines(home: Path, verdicts=None) -> List[str]:
    """Obsolete ~/.agent and home-root ~/.opencode trees (v4.14.7 Phase 6). Read-only.

    A tree whose every file is recognized Nexus-Hub output is reported as
    removable with `nexus-hub prune-undetected --yes`; any other tree is kept,
    with up to ten of its unrecognized entries named.
    """
    from .legacy import classify_legacy_layout, load_layout_fingerprints

    if verdicts is None:
        doc = load_layout_fingerprints()
        if doc is None:
            return []
        verdicts = [classify_legacy_layout(home, layout, doc) for layout in sorted(doc["layouts"])]
    lines: List[str] = []
    for verdict in verdicts:
        if verdict.status == "absent":
            continue
        label = "removable" if verdict.status == "removable" else "legacy layout, not removed"
        lines.append(f"  - {verdict.root}: {label} ({verdict.reason})")
        for item in verdict.unrecognized[:10]:
            lines.append(f"      unrecognized: {item}")
    if lines:
        lines.insert(0, "[doctor] obsolete Nexus-Hub layouts:")
    return lines


__all__ = [
    "DIAGNOSTIC_OK",
    "DIAGNOSTIC_MISSING",
    "DIAGNOSTIC_DRIFTED",
    "DIAGNOSTIC_UNKNOWN",
    "SKIP_ACTIONS",
    "DoctorFinding",
    "DoctorReport",
    "doctor",
    "legacy_report_lines",
    "list_installed",
    "render_stale",
    "repair",
    "stale_report_lines",
]
