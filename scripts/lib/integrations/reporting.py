"""Read-only reporting diagnostics after platform materialization.

Never overwrite a legacy skill to hide drift. Report incomplete copies and
Codex's historical duplicate root so the installer cannot imply status parity.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import InstallContext
    from .result import WriteResult

RESOURCES = ("SKILL.md", "references/progress-reporting.md", "references/status-formats.md",
             "references/status-snapshot.json", "scripts/status_report.py", "scripts/status_snapshot.py",
             "scripts/continuation_state.py")


def audit_reporting(key: str, ctx: InstallContext, result: WriteResult) -> list[str]:
    """Compare reporting bundles actually delivered, including shadowing copies."""
    if ctx.dry_run or ctx.instruction_only:
        return []
    source = ctx.repo_root / "catalog/skills/workflow/implement-phase"
    # Thin test/catalog fixtures without this skill have no reporting contract.
    if not source.is_dir():
        return []
    candidates: set[Path] = set()
    for action in result.files:
        path = Path(action.path)
        for parent in (path, *path.parents):
            if parent.name == "implement-phase" and parent.is_dir():
                candidates.add(parent)
                break
    if key == "codex":
        root = ctx.global_root if ctx.scope == "global" else ctx.target_root
        for rel in (".codex/skills/implement-phase", ".agents/skills/implement-phase"):
            path = root / rel
            if path.is_dir():
                candidates.add(path)
    for root in {ctx.target_root, ctx.global_root}:
        for relative in (".nexus-hub/skills/workflow/implement-phase", ".nexus-hub/skills/implement-phase"):
            common = root / relative
            if common.is_dir():
                candidates.add(common)
    issues = []
    if key in ("aider", "copilot") and not candidates:
        issues.append("reporting parity NOT verified: common implement-phase reporting bundle not installed; use the complete installer")
    for candidate in sorted(candidates):
        for relative in RESOURCES:
            expected, actual = source / relative, candidate / relative
            try:
                if not expected.is_file() or not actual.is_file():
                    issues.append(f"reporting parity NOT verified: missing {candidate / relative}")
                elif expected.read_bytes() != actual.read_bytes():
                    issues.append(f"reporting parity NOT verified: stale {actual}")
            except OSError:
                issues.append(f"reporting parity NOT verified: unreadable {actual}")
    return issues
