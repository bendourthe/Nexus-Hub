#!/usr/bin/env python3
"""harness_audit.py -- deterministic read-only scoring of an agent setup.

Two capabilities share one entry point, both strictly local (zero outbound
calls):

1. `audit` (default action) -- reads the install-state manifest at
   `<target>/.nexus-hub/install-manifest.json` and the running integration
   registry, then emits a per-integration reliability score plus an aggregate
   score. Writes nothing.

2. `grade` / `snapshot` / `diff` (added v3.10.0 Phase 5) -- computes a single
   explainable 1-100 agent-setup grade from observable, locally-measurable
   signals (registry consistency, skill frontmatter conformance, security-hook
   presence and registration, agent-instruction-file presence, hook-reference
   integrity, and data-registry JSON health), can snapshot that grade to a
   local baseline, and can diff the current setup against the latest snapshot
   to surface regressions. The grade is ADVISORY: it prints and exits 0
   regardless of score; only `diff --fail-on-regression` opts into a gate.

Integration audit score axes (each 0.0 -- 1.0):

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

The setup grade combines per-dimension sub-scores via the weights in
`GRADE_WEIGHTS` (a weighted average over the dimensions that are measurable for
the given root, so a thin install is not penalized for source-tree signals it
structurally cannot have). The snapshot is a deterministic, root-independent
JSON written under `<target>/.nexus/harness-audit/latest.json` (override with
`--snapshot-dir`).

Usage:

    python scripts/harness_audit.py                       # integration audit
    python scripts/harness_audit.py --target DIR --json
    python scripts/harness_audit.py --integrations claude,gemini
    python scripts/harness_audit.py grade                 # 1-100 setup grade
    python scripts/harness_audit.py snapshot              # write the baseline
    python scripts/harness_audit.py diff                  # vs latest snapshot
    python scripts/harness_audit.py diff --fail-on-regression  # opt-in gate
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

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


# --------------------------------------------------------------------------- #
# Agent-setup grade rubric (v3.10.0 Phase 5)
# --------------------------------------------------------------------------- #
#
# Per-dimension weights for the single 1-100 agent-setup grade. They sum to 1.0
# so the grade stays in [1, 100]. This is the ONE knob that decides what "a
# healthy setup" means -- tune it here rather than in the scoring functions.
#
# The grade is ADVISORY by contract: it is printed and the process exits 0
# regardless of score, and it must never become an install or commit gate. The
# only opt-in gate is `diff --fail-on-regression`, which a CI job may choose.
GRADE_WEIGHTS = {
    "registry_consistency": 0.25,
    "skill_frontmatter": 0.20,
    "security_hooks": 0.20,
    "instruction_files": 0.15,
    "hook_registration": 0.10,
    "data_integrity": 0.10,
}

# The two repo-root agent-instruction surfaces plus the five platform templates
# that move in lockstep. The `instruction_files` dimension scores the fraction
# of these present.
EXPECTED_INSTRUCTION_FILES = (
    "AGENTS.md",
    "CLAUDE.md",
    "templates/ai-instructions/base-claude.md",
    "templates/ai-instructions/base-codex.md",
    "templates/ai-instructions/base-cursor.md",
    "templates/ai-instructions/base-gemini.md",
    "templates/ai-instructions/base-opencode.md",
)

# Security-critical hooks a healthy setup ships AND registers in settings.json.
# Present-and-registered scores full credit; present-but-unregistered scores
# half; absent scores zero.
SECURITY_HOOKS = (
    "secret-scan.sh",
    "large-file-guard.sh",
    "git-guardrails.sh",
)

# Core data registries whose JSON must parse for the `data_integrity` dimension.
CORE_REGISTRIES = (
    "skills.json",
    "marketplace.json",
    "bundles.json",
)

# Where the grade snapshot baseline lives (relative to the target root unless
# `--snapshot-dir` overrides it). `.nexus/` is already gitignored and is the
# same local-tooling convention the skill-stocktake skill uses.
SNAPSHOT_SUBDIR = Path(".nexus") / "harness-audit"
SNAPSHOT_FILENAME = "latest.json"


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
# Agent-setup grade: data model
# --------------------------------------------------------------------------- #


@dataclass
class GradeDimension:
    """One scored dimension of the agent-setup grade.

    `sub_score` is in [0.0, 1.0]; `applicable` is False when the dimension's
    inputs are structurally absent for this root (so it is excluded from the
    weighted average rather than scored as a failure).
    """

    name: str
    weight: float
    sub_score: float
    applicable: bool
    reason: str

    @property
    def points(self) -> float:
        return self.weight * self.sub_score * 100.0

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "weight": round(self.weight, 4),
            "sub_score": round(self.sub_score, 4),
            "applicable": self.applicable,
            "points": round(self.points, 2),
            "reason": self.reason,
        }


@dataclass
class SetupGrade:
    root: str
    grade: int
    dimensions: List[GradeDimension] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "schema": 1,
            "root": self.root,
            "grade": self.grade,
            "dimensions": [d.to_dict() for d in self.dimensions],
        }

    def snapshot_payload(self) -> Dict[str, object]:
        """Deterministic, root-independent payload for snapshot / diff.

        Excludes the absolute `root` (machine-specific) and any wall-clock
        field, so two runs over an unchanged setup serialize byte-identically.
        """
        return {
            "schema": 1,
            "grade": self.grade,
            "dimensions": [d.to_dict() for d in self.dimensions],
        }


@dataclass
class DimensionDelta:
    name: str
    status: str  # improved | unchanged | regressed | added | removed
    before: Optional[float]
    after: Optional[float]

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "status": self.status,
            "before": self.before,
            "after": self.after,
        }


@dataclass
class GradeDiff:
    before_grade: Optional[int]
    after_grade: int
    deltas: List[DimensionDelta] = field(default_factory=list)

    @property
    def grade_delta(self) -> Optional[int]:
        if self.before_grade is None:
            return None
        return self.after_grade - self.before_grade

    @property
    def regressed(self) -> bool:
        delta = self.grade_delta
        return delta is not None and delta < 0


# --------------------------------------------------------------------------- #
# Agent-setup grade: read-only signal helpers
# --------------------------------------------------------------------------- #


def _load_json(path: Path) -> Optional[object]:
    """Parse `path` as JSON, returning None on any read or parse failure."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _read_frontmatter(path: Path) -> Optional[str]:
    """Return the YAML frontmatter block (between the first two `---` lines),
    or None if the file has no leading frontmatter or is unreadable.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    body: List[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            return "\n".join(body)
        body.append(line)
    return None


def _count_skill_files(root: Path) -> int:
    skills_dir = root / "catalog" / "skills"
    if not skills_dir.is_dir():
        return 0
    return sum(1 for _ in skills_dir.glob("*/*/SKILL.md"))


def _count_index_rows(path: Path) -> Optional[int]:
    """Count skill rows in a `data/SKILL_INDEX.md` table (lines whose cells
    reference a `catalog/skills/.../SKILL.md` path). None if unreadable.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    count = 0
    for line in text.splitlines():
        stripped = line.strip()
        if (
            stripped.startswith("|")
            and "catalog/skills/" in stripped
            and "SKILL.md" in stripped
        ):
            count += 1
    return count


def _marketplace_category_sum(path: Path) -> Optional[int]:
    data = _load_json(path)
    if not isinstance(data, dict):
        return None
    cats = data.get("categories")
    if not isinstance(cats, list):
        return None
    total = 0
    found = False
    for cat in cats:
        if isinstance(cat, dict) and isinstance(cat.get("skill_count"), int):
            total += cat["skill_count"]
            found = True
    return total if found else None


def _referenced_hook_files(settings: Dict[str, object]) -> Set[str]:
    """Extract the set of hook script basenames referenced from a settings.json
    `hooks` block (e.g. `bash .claude/hooks/secret-scan.sh` -> `secret-scan.sh`).
    """
    names: Set[str] = set()
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return names
    marker = ".claude/hooks/"
    for event_entries in hooks.values():
        if not isinstance(event_entries, list):
            continue
        for entry in event_entries:
            if not isinstance(entry, dict):
                continue
            for hook in entry.get("hooks", []) or []:
                if not isinstance(hook, dict):
                    continue
                cmd = hook.get("command")
                if not isinstance(cmd, str):
                    continue
                idx = cmd.find(marker)
                if idx == -1:
                    continue
                tail = cmd[idx + len(marker):].split()
                if tail:
                    names.add(tail[0])
    return names


# --------------------------------------------------------------------------- #
# Agent-setup grade: per-dimension scorers
# --------------------------------------------------------------------------- #


def _grade_registry_consistency(root: Path) -> GradeDimension:
    name = "registry_consistency"
    weight = GRADE_WEIGHTS[name]
    actual = _count_skill_files(root)
    if actual == 0:
        return GradeDimension(
            name, weight, 0.0, False,
            "no catalog/skills tree found; not measurable here",
        )
    checks: List[Tuple[str, Optional[int]]] = []
    skills_json = _load_json(root / "data" / "skills.json")
    json_total: Optional[int] = None
    json_len: Optional[int] = None
    if isinstance(skills_json, dict):
        stats = skills_json.get("statistics")
        if isinstance(stats, dict) and isinstance(stats.get("total_skills"), int):
            json_total = stats["total_skills"]
        if isinstance(skills_json.get("skills"), list):
            json_len = len(skills_json["skills"])
    checks.append(("skills.json total_skills", json_total))
    checks.append(("skills.json skills[]", json_len))
    checks.append(("SKILL_INDEX.md rows", _count_index_rows(root / "data" / "SKILL_INDEX.md")))
    checks.append(("marketplace.json category sum", _marketplace_category_sum(root / "data" / "marketplace.json")))

    measurable = [(label, val) for label, val in checks if val is not None]
    if not measurable:
        return GradeDimension(
            name, weight, 0.0, False, "registries unreadable; not measurable",
        )
    agree = sum(1 for _, val in measurable if val == actual)
    sub = agree / len(measurable)
    if sub == 1.0:
        reason = f"all {len(measurable)} registries agree on {actual} skills"
    else:
        mismatches = ", ".join(label for label, val in measurable if val != actual)
        reason = (
            f"{agree}/{len(measurable)} registries match the {actual} on-disk "
            f"skills; drift in: {mismatches}"
        )
    return GradeDimension(name, weight, sub, True, reason)


def _grade_skill_frontmatter(root: Path) -> GradeDimension:
    name = "skill_frontmatter"
    weight = GRADE_WEIGHTS[name]
    skills_dir = root / "catalog" / "skills"
    files = sorted(skills_dir.glob("*/*/SKILL.md")) if skills_dir.is_dir() else []
    if not files:
        return GradeDimension(
            name, weight, 0.0, False,
            "no SKILL.md files found; not measurable here",
        )
    required = ("name:", "description:", "summary_l0:", "overview_l1:")
    conformant = 0
    for skill_file in files:
        front = _read_frontmatter(skill_file)
        if front is not None and all(key in front for key in required):
            conformant += 1
    sub = conformant / len(files)
    reason = (
        f"{conformant}/{len(files)} skills carry all four Tier-1 frontmatter "
        f"fields (name, description, summary_l0, overview_l1)"
    )
    return GradeDimension(name, weight, sub, True, reason)


def _grade_security_hooks(root: Path) -> GradeDimension:
    name = "security_hooks"
    weight = GRADE_WEIGHTS[name]
    hooks_dir = root / "catalog" / "hooks"
    if not hooks_dir.is_dir():
        return GradeDimension(
            name, weight, 0.0, False,
            "no catalog/hooks tree found; not measurable here",
        )
    try:
        settings_text = (hooks_dir / "settings.json").read_text(encoding="utf-8")
    except OSError:
        settings_text = ""
    score = 0.0
    missing: List[str] = []
    unregistered: List[str] = []
    for hook in SECURITY_HOOKS:
        on_disk = (hooks_dir / hook).is_file()
        registered = hook in settings_text
        if on_disk and registered:
            score += 1.0
        elif on_disk:
            score += 0.5
            unregistered.append(hook)
        else:
            missing.append(hook)
    sub = score / len(SECURITY_HOOKS)
    parts: List[str] = []
    if missing:
        parts.append(f"missing: {', '.join(missing)}")
    if unregistered:
        parts.append(f"present but unregistered: {', '.join(unregistered)}")
    reason = "; ".join(parts) if parts else "all security hooks present and registered"
    return GradeDimension(name, weight, sub, True, reason)


def _grade_instruction_files(root: Path) -> GradeDimension:
    name = "instruction_files"
    weight = GRADE_WEIGHTS[name]
    present = [f for f in EXPECTED_INSTRUCTION_FILES if (root / f).is_file()]
    if not present:
        return GradeDimension(
            name, weight, 0.0, False,
            "no agent-instruction files found; not measurable here",
        )
    sub = len(present) / len(EXPECTED_INSTRUCTION_FILES)
    missing = [f for f in EXPECTED_INSTRUCTION_FILES if not (root / f).is_file()]
    if missing:
        reason = (
            f"{len(present)}/{len(EXPECTED_INSTRUCTION_FILES)} instruction "
            f"files present; missing: {', '.join(missing)}"
        )
    else:
        reason = f"all {len(EXPECTED_INSTRUCTION_FILES)} instruction files present"
    return GradeDimension(name, weight, sub, True, reason)


def _grade_hook_registration(root: Path) -> GradeDimension:
    name = "hook_registration"
    weight = GRADE_WEIGHTS[name]
    hooks_dir = root / "catalog" / "hooks"
    data = _load_json(hooks_dir / "settings.json")
    if not isinstance(data, dict):
        return GradeDimension(
            name, weight, 0.0, False,
            "settings.json absent or unreadable; not measurable here",
        )
    referenced = _referenced_hook_files(data)
    if not referenced:
        return GradeDimension(
            name, weight, 1.0, True, "no hook commands referenced in settings.json",
        )
    resolved = sum(1 for h in referenced if (hooks_dir / h).is_file())
    sub = resolved / len(referenced)
    orphans = sorted(h for h in referenced if not (hooks_dir / h).is_file())
    reason = (
        f"all {len(referenced)} referenced hook scripts exist"
        if not orphans
        else f"{resolved}/{len(referenced)} referenced hooks exist; orphan references: {', '.join(orphans)}"
    )
    return GradeDimension(name, weight, sub, True, reason)


def _grade_data_integrity(root: Path) -> GradeDimension:
    name = "data_integrity"
    weight = GRADE_WEIGHTS[name]
    data_dir = root / "data"
    existing = [data_dir / f for f in CORE_REGISTRIES if (data_dir / f).is_file()]
    if not existing:
        return GradeDimension(
            name, weight, 0.0, False,
            "no data/ registries found; not measurable here",
        )
    ok = sum(1 for p in existing if _load_json(p) is not None)
    sub = ok / len(existing)
    bad = sorted(p.name for p in existing if _load_json(p) is None)
    reason = (
        f"all {len(existing)} core registries parse as valid JSON"
        if not bad
        else f"{ok}/{len(existing)} registries parse; invalid: {', '.join(bad)}"
    )
    return GradeDimension(name, weight, sub, True, reason)


# --------------------------------------------------------------------------- #
# Agent-setup grade: orchestration + snapshot/diff
# --------------------------------------------------------------------------- #


def grade(root: Path) -> SetupGrade:
    """Compute the 1-100 agent-setup grade for `root` from observable signals.

    Read-only, deterministic, zero outbound calls. The grade is a weighted
    average over the dimensions that are measurable for this root, clamped to
    [1, 100].
    """
    dimensions = [
        _grade_registry_consistency(root),
        _grade_skill_frontmatter(root),
        _grade_security_hooks(root),
        _grade_instruction_files(root),
        _grade_hook_registration(root),
        _grade_data_integrity(root),
    ]
    applicable = [d for d in dimensions if d.applicable]
    total_weight = sum(d.weight for d in applicable)
    if total_weight > 0:
        weighted = sum(d.sub_score * d.weight for d in applicable) / total_weight
    else:
        weighted = 0.0
    score = max(1, min(100, round(100.0 * weighted)))
    return SetupGrade(root=str(root), grade=score, dimensions=dimensions)


def _snapshot_path(root: Path, snapshot_dir: Optional[str]) -> Path:
    base = Path(snapshot_dir).expanduser() if snapshot_dir else root / SNAPSHOT_SUBDIR
    return base / SNAPSHOT_FILENAME


def write_snapshot(
    setup: SetupGrade, root: Path, snapshot_dir: Optional[str] = None
) -> Path:
    """Write the graded setup to a deterministic local baseline and return its
    path. The only write this module performs.
    """
    path = _snapshot_path(root, snapshot_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(setup.snapshot_payload(), indent=2, sort_keys=True)
    path.write_text(payload + "\n", encoding="utf-8")
    return path


def diff_against_snapshot(
    setup: SetupGrade, snapshot_payload: Optional[Dict[str, object]]
) -> GradeDiff:
    """Compare a freshly computed `setup` against a stored snapshot payload,
    classifying each dimension improved / unchanged / regressed (added /
    removed when the dimension set itself changed).
    """
    if not snapshot_payload:
        return GradeDiff(before_grade=None, after_grade=setup.grade, deltas=[])
    raw_before = snapshot_payload.get("grade")
    before_grade = raw_before if isinstance(raw_before, int) else None
    before_dims: Dict[str, float] = {}
    for entry in snapshot_payload.get("dimensions", []) or []:
        if isinstance(entry, dict) and isinstance(entry.get("name"), str):
            sub = entry.get("sub_score")
            if isinstance(sub, (int, float)):
                before_dims[entry["name"]] = float(sub)
    deltas: List[DimensionDelta] = []
    current_names: Set[str] = set()
    for dim in setup.dimensions:
        current_names.add(dim.name)
        after = round(dim.sub_score, 4)
        if dim.name in before_dims:
            before = round(before_dims[dim.name], 4)
            if after > before:
                status = "improved"
            elif after < before:
                status = "regressed"
            else:
                status = "unchanged"
            deltas.append(DimensionDelta(dim.name, status, before, after))
        else:
            deltas.append(DimensionDelta(dim.name, "added", None, after))
    for nm, before in before_dims.items():
        if nm not in current_names:
            deltas.append(DimensionDelta(nm, "removed", round(before, 4), None))
    return GradeDiff(before_grade=before_grade, after_grade=setup.grade, deltas=deltas)


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


def _format_grade_markdown(setup: SetupGrade) -> str:
    lines: List[str] = []
    lines.append("# Nexus-Hub Agent-Setup Grade")
    lines.append("")
    lines.append(f"- Root: `{setup.root}`")
    lines.append(f"- Setup grade: **{setup.grade} / 100** (advisory)")
    lines.append("")
    lines.append("## Rubric breakdown")
    lines.append("")
    lines.append("| Dimension | Weight | Sub-score | Points | Reason |")
    lines.append("|---|---:|---:|---:|---|")
    for d in setup.dimensions:
        sub = f"{d.sub_score:.2f}" if d.applicable else "n/a"
        pts = f"{d.points:.1f}" if d.applicable else "n/a"
        lines.append(f"| `{d.name}` | {d.weight:.2f} | {sub} | {pts} | {d.reason} |")
    lines.append("")
    lines.append("_The grade is advisory: it never blocks an install or a commit._")
    lines.append("")
    return "\n".join(lines) + "\n"


def _format_diff_markdown(diff: GradeDiff, snapshot_path: Path) -> str:
    lines: List[str] = []
    lines.append("# Nexus-Hub Agent-Setup Regression Diff")
    lines.append("")
    if diff.before_grade is None:
        lines.append(f"- No prior snapshot at `{snapshot_path}`.")
        lines.append(f"- Current grade: **{diff.after_grade} / 100**.")
        lines.append("- Run `snapshot` first to establish a baseline.")
        lines.append("")
        return "\n".join(lines) + "\n"
    delta = diff.grade_delta or 0
    if delta > 0:
        movement = f"improved by {delta}"
    elif delta < 0:
        movement = f"regressed by {-delta}"
    else:
        movement = "no change"
    lines.append(f"- Baseline: `{snapshot_path}`")
    lines.append(f"- Grade: {diff.before_grade} -> {diff.after_grade} ({movement})")
    lines.append("")
    lines.append("| Dimension | Before | After | Status |")
    lines.append("|---|---:|---:|---|")
    for d in diff.deltas:
        before = "n/a" if d.before is None else f"{d.before:.2f}"
        after = "n/a" if d.after is None else f"{d.after:.2f}"
        lines.append(f"| `{d.name}` | {before} | {after} | {d.status} |")
    lines.append("")
    lines.append("_Regressions are advisory by default; pass `--fail-on-regression` to gate._")
    lines.append("")
    return "\n".join(lines) + "\n"


def _run_grade(target_root: Path, as_json: bool) -> int:
    setup = grade(target_root)
    if as_json:
        print(json.dumps(setup.to_dict(), indent=2, sort_keys=True))
    else:
        sys.stdout.write(_format_grade_markdown(setup))
    return 0  # advisory: always succeeds


def _run_snapshot(target_root: Path, snapshot_dir: Optional[str], as_json: bool) -> int:
    setup = grade(target_root)
    path = write_snapshot(setup, target_root, snapshot_dir)
    if as_json:
        print(json.dumps({"snapshot": str(path), "grade": setup.grade}, indent=2, sort_keys=True))
    else:
        sys.stdout.write(_format_grade_markdown(setup))
        sys.stdout.write(f"\nSnapshot written: {path}\n")
    return 0  # advisory: always succeeds


def _run_diff(
    target_root: Path,
    snapshot_dir: Optional[str],
    fail_on_regression: bool,
    as_json: bool,
) -> int:
    setup = grade(target_root)
    path = _snapshot_path(target_root, snapshot_dir)
    stored = _load_json(path)
    stored = stored if isinstance(stored, dict) else None
    diff = diff_against_snapshot(setup, stored)
    if as_json:
        print(
            json.dumps(
                {
                    "before_grade": diff.before_grade,
                    "after_grade": diff.after_grade,
                    "grade_delta": diff.grade_delta,
                    "regressed": diff.regressed,
                    "deltas": [d.to_dict() for d in diff.deltas],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        sys.stdout.write(_format_diff_markdown(diff, path))
    if fail_on_regression and diff.regressed:
        return 1
    return 0  # advisory by default


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="nexus-hub-harness-audit",
        description=(
            "Read-only deterministic scoring of an agent setup. The default "
            "`audit` action scores installed integrations from the install "
            "manifest; `grade` / `snapshot` / `diff` compute an advisory 1-100 "
            "setup grade and a cross-snapshot regression diff. Zero outbound "
            "calls; the only write is the grade snapshot."
        ),
    )
    parser.add_argument(
        "action",
        nargs="?",
        default="audit",
        choices=["audit", "grade", "snapshot", "diff"],
        help=(
            "audit (default): per-integration scoring. grade: 1-100 setup "
            "grade. snapshot: write the graded setup to a local baseline. "
            "diff: compare the current setup against the latest snapshot."
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
        help="audit only: exit 1 if the aggregate score falls below this threshold (0-100).",
    )
    parser.add_argument(
        "--snapshot",
        action="store_true",
        help="Alias for the `snapshot` action (write the current grade to the local baseline).",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Alias for the `diff` action (compare the current setup against the latest snapshot).",
    )
    parser.add_argument(
        "--fail-on-regression",
        action="store_true",
        help="diff only: exit non-zero when the overall grade regressed against the snapshot (opt-in CI gate).",
    )
    parser.add_argument(
        "--snapshot-dir",
        help="Directory for the grade snapshot (default: <target>/.nexus/harness-audit).",
    )
    args = parser.parse_args(argv)
    target_root = (
        Path(args.target).expanduser().resolve() if args.target else Path.cwd().resolve()
    )

    # Flag aliases win over the positional default so `--snapshot` / `--diff`
    # behave the same as the `snapshot` / `diff` positional actions.
    action = args.action
    if args.snapshot:
        action = "snapshot"
    elif args.diff:
        action = "diff"

    if action == "grade":
        return _run_grade(target_root, args.json)
    if action == "snapshot":
        return _run_snapshot(target_root, args.snapshot_dir, args.json)
    if action == "diff":
        return _run_diff(target_root, args.snapshot_dir, args.fail_on_regression, args.json)

    # Default: integration audit (unchanged behavior).
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
