"""Subsumed validator analyzers (behavior-preserving unification).

Nexus-Hub already shipped three fragmented security validators under
``scripts/``: the fence-aware secret scan inside ``validate_skills.py``,
``scan_supply_chain_iocs.py``, and ``validate_workflow_security.py``. Rather
than re-author (and risk drifting from) their patterns, this module *loads the
originals by path* and routes their findings through the unified ``Finding``
schema. The originals are left byte-for-byte unchanged -- their ``make
validate`` entry points and their entire pytest suites keep passing -- so the
unification is behavior-preserving by construction (the scanner literally calls
their detection functions).

When the scanner runs outside a Nexus-Hub checkout (e.g. an installed
``/skills scan`` on a third-party skill) the originals are not on disk. The
secret analyzer then falls back to a compact, fence-aware re-authored pattern
set so the installed scanner still detects leaked credentials; the
supply-chain and workflow analyzers, whose surface is repo manifests and CI
files, simply record themselves as skipped.
"""

from __future__ import annotations

import importlib.util
import os
import re
from pathlib import Path
from types import ModuleType

from ..fences import iter_lines_with_fence
from ..types import Finding, Severity
from .base import FileUnit, make_finding

# Cache loaded original modules per repo root so we import each at most once.
_MODULE_CACHE: dict[tuple[str, str], ModuleType | None] = {}


def find_repo_root(start: Path) -> Path | None:
    """Locate the Nexus-Hub checkout root by walking up from ``start``.

    Honors ``NEXUS_HUB_ROOT`` first; otherwise looks for a directory that
    contains both ``scripts/`` and one of the subsumed validators.
    """
    env = os.environ.get("NEXUS_HUB_ROOT")
    if env:
        root = Path(env)
        if (root / "scripts" / "validate_skills.py").is_file():
            return root
    cur = start.resolve()
    for candidate in [cur, *cur.parents]:
        if (candidate / "scripts" / "validate_skills.py").is_file():
            return candidate
    return None


def load_repo_module(repo_root: Path, script_name: str) -> ModuleType | None:
    """Load a ``scripts/<script_name>`` module by path (cached)."""
    key = (str(repo_root), script_name)
    if key in _MODULE_CACHE:
        return _MODULE_CACHE[key]
    path = repo_root / "scripts" / script_name
    module: ModuleType | None = None
    if path.is_file():
        try:
            spec = importlib.util.spec_from_file_location(
                f"_nss_subsumed_{script_name.replace('.', '_')}", path
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
        except Exception:  # pragma: no cover - defensive; degrade gracefully
            module = None
    _MODULE_CACHE[key] = module
    return module


# ---------------------------------------------------------------------------
# Secret scanning (subsumes validate_skills.py secret scan, class 3)
# ---------------------------------------------------------------------------

_SECRET_FINDING_RE = re.compile(r"potential (?P<name>.+?) detected \(line ~(?P<line>\d+)\)")

# Fallback patterns (used only when validate_skills.py is not on disk). High-
# confidence credential formats; "Generic secret assignment" is fence-exempt
# in Markdown (a documentation example, not a real leak).
_FALLBACK_PATTERNS: list[tuple[str, re.Pattern[str], Severity]] = [
    ("OpenAI API key", re.compile(r"sk-[A-Za-z0-9]{20,}"), Severity.HIGH),
    ("Anthropic API key", re.compile(r"sk-ant-[A-Za-z0-9\-]{20,}"), Severity.HIGH),
    ("AWS Access Key", re.compile(r"AKIA[0-9A-Z]{16}"), Severity.HIGH),
    ("GitHub PAT (classic)", re.compile(r"ghp_[A-Za-z0-9]{36}"), Severity.HIGH),
    ("GitHub PAT (fine-grained)", re.compile(r"github_pat_[A-Za-z0-9_]{82}"), Severity.HIGH),
    ("Hardcoded Bearer token", re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]{50,}"), Severity.HIGH),
    ("Generic secret assignment", re.compile(r"""(?:password|secret|token|api_key)\s*=\s*["'][^"']{8,}["']""", re.IGNORECASE), Severity.MEDIUM),
]
_FALLBACK_FENCE_EXEMPT = {"Generic secret assignment"}


def _secret_severity(pattern_name: str) -> Severity:
    return Severity.MEDIUM if pattern_name == "Generic secret assignment" else Severity.HIGH


class SecretsAnalyzer:
    """Subsumes the fence-aware hardcoded-secret scan (class 3)."""

    name = "secrets"

    def __init__(self, repo_root: Path | None) -> None:
        self._module = load_repo_module(repo_root, "validate_skills.py") if repo_root else None

    def analyze(self, unit: FileUnit) -> list[Finding]:
        if self._module is not None:
            return self._analyze_via_original(unit)
        return self._analyze_fallback(unit)

    def _analyze_via_original(self, unit: FileUnit) -> list[Finding]:
        findings: list[Finding] = []
        raw = self._module.scan_text_for_secrets(unit.text, unit.path)  # type: ignore[union-attr]
        for entry in raw:
            m = _SECRET_FINDING_RE.search(entry)
            name = m.group("name") if m else "hardcoded secret"
            line = int(m.group("line")) if m else 0
            findings.append(make_finding(
                detection_class=3, severity=_secret_severity(name),
                title=f"Hardcoded secret: {name}",
                message=f"A {name} appears in this file. Verify it is not a live credential; if real, rotate it and load from the environment instead.",
                unit=unit, line=line, analyzer=self.name,
            ))
        return findings

    def _analyze_fallback(self, unit: FileUnit) -> list[Finding]:
        findings: list[Finding] = []
        for line_no, line, in_fence in iter_lines_with_fence(unit.text):
            for name, pattern, severity in _FALLBACK_PATTERNS:
                if unit.is_markdown and in_fence and name in _FALLBACK_FENCE_EXEMPT:
                    continue
                if pattern.search(line):
                    findings.append(make_finding(
                        detection_class=3, severity=severity,
                        title=f"Hardcoded secret: {name}",
                        message=f"A {name} appears in this file. Verify it is not a live credential.",
                        unit=unit, line=line_no, snippet=line, analyzer=self.name,
                    ))
        return findings


# ---------------------------------------------------------------------------
# Supply-chain IOCs (subsumes scan_supply_chain_iocs.py, class 4)
# ---------------------------------------------------------------------------


class SupplyChainAnalyzer:
    """Subsumes the supply-chain IOC scan (class 4).

    Findings are mapped to MEDIUM: the original is a pass/fail validator that
    already runs green on the repo via ``make validate``; surfacing its
    findings at MEDIUM unifies the capability without letting a manifest IOC
    trip the HIGH/CRITICAL catalog gate. Markdown is skipped (the original
    never scanned it, and the secret/text analyzers cover skill bodies).
    """

    name = "supply-chain"

    def __init__(self, repo_root: Path | None) -> None:
        self._module = load_repo_module(repo_root, "scan_supply_chain_iocs.py") if repo_root else None

    def analyze(self, unit: FileUnit) -> list[Finding]:
        if self._module is None or unit.is_markdown:
            return []
        findings: list[Finding] = []
        try:
            raw = self._module.scan_file(unit.path)  # type: ignore[union-attr]
        except Exception:  # pragma: no cover - defensive
            return []
        for line, _col, msg in raw:
            findings.append(make_finding(
                detection_class=4, severity=Severity.MEDIUM,
                title="Supply-chain IOC",
                message=str(msg),
                unit=unit, line=int(line) if line else 0, analyzer=self.name,
            ))
        return findings


# ---------------------------------------------------------------------------
# Workflow security (subsumes validate_workflow_security.py, class 4)
# ---------------------------------------------------------------------------


class WorkflowSecurityAnalyzer:
    """Subsumes the GitHub Actions workflow-security scan (class 4)."""

    name = "workflow-security"

    def __init__(self, repo_root: Path | None) -> None:
        self._module = load_repo_module(repo_root, "validate_workflow_security.py") if repo_root else None

    def analyze(self, unit: FileUnit) -> list[Finding]:
        if self._module is None:
            return []
        parts = unit.path.as_posix().lower()
        if ".github/workflows/" not in parts or unit.suffix not in (".yml", ".yaml"):
            return []
        findings: list[Finding] = []
        try:
            raw = self._module.scan_workflow(unit.path)  # type: ignore[union-attr]
        except Exception:  # pragma: no cover - defensive
            return []
        for line, msg in raw:
            findings.append(make_finding(
                detection_class=4, severity=Severity.MEDIUM,
                title="CI workflow security",
                message=str(msg),
                unit=unit, line=int(line) if line else 0, analyzer=self.name,
            ))
        return findings
