"""Scan orchestration: discover files, run analyzers, aggregate and score.

A ``Scanner`` walks one or more targets (a skill directory, a single file, or
a catalog tree), reads every scannable file into a ``FileUnit``, runs every
registered analyzer over it, and aggregates the findings into a scored
``ScanResult``.
"""

from __future__ import annotations

import os
from pathlib import Path

from .analyzers import build_analyzers
from .analyzers.base import FileUnit
from .analyzers.dependencies import OSVClient
from .analyzers.subsumed import find_repo_root
from .scoring import score_findings
from .types import Finding, ScanResult

# File extensions worth reading. Mirrors validate_skills' scannable set plus a
# couple of config formats relevant to MCP declarations.
SCANNABLE_EXTENSIONS = frozenset({
    ".md", ".markdown", ".py", ".sh", ".bash", ".js", ".mjs", ".cjs", ".ts",
    ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".ps1", ".txt", ".rb",
    ".pl",
})

# Directory names never worth descending into.
EXCLUDED_DIRS = frozenset({
    ".git", "__pycache__", "node_modules", ".venv", "venv", "site-packages",
    "dist", "build", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".egg-info", ".nexus",
})

# Cap on a single file's size to keep the scan bounded (5 MB, matching the
# web-fetch body cap). Larger files are skipped with a note.
MAX_FILE_BYTES = 5 * 1024 * 1024


class Scanner:
    """Configurable static skill-security scanner.

    The optional Phase 7 modules are off by default. ``enable_signatures``
    (``--yara``) adds the local signature-rule engine; ``enable_osv``
    (``--osv``) adds the dependency-vulnerability lookup, whose live OSV.dev
    query is gated behind ``osv_online``. Tests inject ``osv_client`` to keep
    the network out of CI.
    """

    def __init__(
        self,
        repo_root: Path | None = None,
        *,
        enable_signatures: bool = False,
        enable_osv: bool = False,
        osv_online: bool = False,
        osv_client: OSVClient | None = None,
    ) -> None:
        self.repo_root = repo_root
        self._analyzers = build_analyzers(
            repo_root,
            enable_signatures=enable_signatures,
            enable_osv=enable_osv,
            osv_online=osv_online,
            osv_client=osv_client,
        )

    def _rel(self, path: Path, base: Path) -> str:
        try:
            anchor = self.repo_root or base
            return path.relative_to(anchor).as_posix()
        except ValueError:
            return path.as_posix()

    def _iter_files(self, target: Path) -> list[Path]:
        if target.is_file():
            return [target]
        files: list[Path] = []
        for dirpath, dirnames, filenames in os.walk(target):
            dirnames[:] = [
                d for d in dirnames
                if d not in EXCLUDED_DIRS and not d.endswith(".egg-info")
            ]
            for name in sorted(filenames):
                p = Path(dirpath) / name
                if p.suffix.lower() in SCANNABLE_EXTENSIONS:
                    files.append(p)
        return sorted(files)

    def scan_file(self, path: Path, base: Path) -> list[Finding]:
        """Run every analyzer over a single file."""
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                return []
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []
        unit = FileUnit.from_path(path, self._rel(path, base), text)
        findings: list[Finding] = []
        for analyzer in self._analyzers:
            findings.extend(analyzer.analyze(unit))
        return findings

    def scan(self, targets: list[Path]) -> ScanResult:
        """Scan one or more targets and return an aggregated, scored result."""
        all_findings: list[Finding] = []
        files_scanned = 0
        label = ", ".join(t.as_posix() for t in targets)
        for target in targets:
            base = target if target.is_dir() else target.parent
            for path in self._iter_files(target):
                all_findings.extend(self.scan_file(path, base))
                files_scanned += 1
        # Stable ordering: by file, then line, then descending severity.
        all_findings.sort(key=lambda f: (f.file, f.line, -f.severity.rank))
        score, band = score_findings(all_findings)
        result = ScanResult(
            target=label,
            findings=all_findings,
            files_scanned=files_scanned,
            score=score,
            band=band,
        )
        # Surface graceful-degrade notes from any optional analyzer (e.g. the
        # OSV live lookup degrading to the offline DB, or the signature engine
        # finding no rules). Deduplicated; core analyzers have no `skipped`.
        for analyzer in self._analyzers:
            for note in getattr(analyzer, "skipped", ()) or ():
                if note not in result.skipped_modules:
                    result.skipped_modules.append(note)
        return result


def scan_target(
    target: str | Path | list[str | Path],
    repo_root: str | Path | None = None,
    *,
    enable_signatures: bool = False,
    enable_osv: bool = False,
    osv_online: bool = False,
    osv_client: OSVClient | None = None,
) -> ScanResult:
    """Convenience entry: scan a target (or targets) and return the result.

    ``repo_root`` controls where the subsumed validators are loaded from and
    how file paths are reported; when omitted it is auto-detected by walking up
    from the first target. The optional-module flags mirror ``Scanner``.
    """
    raw_targets = target if isinstance(target, list) else [target]
    targets = [Path(t) for t in raw_targets]
    root = Path(repo_root) if repo_root else None
    if root is None and targets:
        root = find_repo_root(targets[0])
    scanner = Scanner(
        repo_root=root,
        enable_signatures=enable_signatures,
        enable_osv=enable_osv,
        osv_online=osv_online,
        osv_client=osv_client,
    )
    return scanner.scan(targets)
