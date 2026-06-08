"""Producer-catalog allowlist for trusted security-category skill bodies.

A producer catalog like Nexus-Hub ships a ``security`` skill category whose
``SKILL.md`` bodies legitimately carry authorized red-team methodology: example
credentials / tokens, attack directives, and payloads shown inside fenced code
blocks to *teach* defenders what a system must withstand. Those teaching
payloads would otherwise trip the deterministic HIGH/CRITICAL gate -- the
clearest case is a fenced example ``Authorization: Bearer <token>``, which the
secret analyzer flags HIGH **even inside a fence** (a genuinely leaked key must
never be suppressed; see ``scripts/validate_skills.py`` ``scan_text_for_secrets``).

This module caps such findings BELOW HIGH, but only under tightly scoped
conditions, and never for the danger classes that must always trip the gate. It
is a *policy layer*, not a detection change: every analyzer keeps reporting the
real detection class and severity, and this layer lowers the severity to MEDIUM
only when all of the scoping rules below hold. The construct still surfaces (at
MEDIUM) for the ``skill-security-scan`` semantic-adjudication skill -- it is
capped, not suppressed -- so the producer-catalog prose-capping discipline is
reused rather than a blanket suppression added.

Scoping rules (ALL must hold for a finding to be capped):

1. **Trusted producer catalog.** The scan is rooted at a real Nexus-Hub
   checkout (``repo_root`` resolved) AND the host file resolves to a path under
   ``<repo_root>/catalog/skills/security/``. A third-party skill scanned via
   ``/skills import`` is not under the trusted repo's security tree (its
   ``repo_root`` does not resolve to a Nexus-Hub checkout, or its path is
   elsewhere), so it is never allowlisted -- its findings score at their real
   class.
2. **Prose / fenced context only.** The host file is a Markdown skill body
   (``.md`` / ``.markdown``). Bundled executable scripts (``.py``, ``.sh``,
   ``.ps1``, ...) are real code, not teaching prose, and are never capped -- a
   payload that actually runs is detected at full severity even inside a
   ``security`` skill.
3. **Not a never-relax class.** The finding's detection class is not one of the
   danger classes the adoption plan forbids relaxing -- data exfiltration (2),
   excessive agency (5), behavioral dynamic code execution (12),
   taint-to-sink code injection (13), and signature / live-malware (14). These
   keep their real severity even inside a trusted security skill body.

When all three hold and the finding's severity exceeds MEDIUM, it is lowered to
MEDIUM (the same ceiling the prose text-pattern analyzer already enforces).
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from .types import Finding, Severity

# Repo-relative location of the trusted producer-catalog security category.
SECURITY_CATEGORY_PARTS: tuple[str, ...] = ("catalog", "skills", "security")

# Markdown skill-body suffixes -- the prose / fenced teaching context.
MARKDOWN_SUFFIXES = frozenset({".md", ".markdown"})

# Detection classes whose severity must NEVER be relaxed by the allowlist, even
# inside a trusted security-skill body:
#   2  data exfiltration (exfiltration-to-external-host)
#   5  excessive agency
#   12 behavioral AST: dynamic code execution (exec/eval/compile)
#   13 taint tracking: tainted input -> dangerous sink (code injection)
#   14 signature rules: live malware / web shell / cryptominer / exploit
NEVER_RELAX_CLASSES = frozenset({2, 5, 12, 13, 14})

# The ceiling a capped finding is lowered to (mirrors the prose MEDIUM cap).
_CAP = Severity.MEDIUM


def is_trusted_security_skill_body(path: Path, repo_root: Path | None) -> bool:
    """Return True iff ``path`` is a Markdown skill body inside the trusted
    Nexus-Hub ``catalog/skills/security/`` tree of ``repo_root``.

    Returns False when ``repo_root`` is None (a third-party / installed scan
    with no Nexus-Hub checkout), when the file is outside the ``security``
    category, or when the file is not a Markdown body. Path comparison is done
    on resolved absolute paths so a relative target (e.g. ``catalog/skills``)
    is handled the same as an absolute one.
    """
    if repo_root is None:
        return False
    if path.suffix.lower() not in MARKDOWN_SUFFIXES:
        return False
    try:
        rel = path.resolve().relative_to(repo_root.resolve())
    except (ValueError, OSError):
        return False
    n = len(SECURITY_CATEGORY_PARTS)
    return rel.parts[:n] == SECURITY_CATEGORY_PARTS


def apply_allowlist(
    findings: list[Finding], path: Path, repo_root: Path | None
) -> list[Finding]:
    """Cap producer-catalog security-skill prose findings at MEDIUM.

    Returns a new list with every eligible finding (above MEDIUM, not a
    never-relax class) lowered to MEDIUM when ``path`` is a trusted security
    skill body; all other findings (and all findings for non-trusted files) are
    returned unchanged. Never raises a severity.
    """
    if not is_trusted_security_skill_body(path, repo_root):
        return findings
    capped: list[Finding] = []
    for finding in findings:
        if (
            finding.detection_class not in NEVER_RELAX_CLASSES
            and finding.severity.rank > _CAP.rank
        ):
            capped.append(replace(finding, severity=_CAP))
        else:
            capped.append(finding)
    return capped
