"""Shared helpers for the Nexus-Hub skill-activation hooks.

Imported by skill-activation-suggest.py, skill-guard.py, and skill-tracker.py.
Every function is defensive: it returns a safe empty default rather than raising,
and each hook wraps the import itself in try/except and exits 0 on failure, so the
hooks preserve their fail-open guarantee even if this module is missing.

stdlib only; no outbound calls; never logs secrets.

Part of Nexus-Hub. See catalog/style-guides/skill-activation-rules.md.
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# Discovery order for the active rules file (relative to the working directory),
# after the NEXUS_SKILL_RULES explicit override.
_RULES_FILENAMES = (
    ".claude/skill-rules.json",
    "skill-rules.json",
    ".nexus-hub/skill-rules.json",
)


def hook_disabled(hook_name: str) -> bool:
    """True when this hook is opted out via NEXUS_DISABLED_HOOKS or the minimal profile."""
    disabled = os.environ.get("NEXUS_DISABLED_HOOKS", "")
    names = {n.strip() for n in disabled.split(",") if n.strip()}
    if hook_name in names:
        return True
    return os.environ.get("NEXUS_HOOK_PROFILE", "full") == "minimal"


def read_stdin_json() -> dict[str, Any]:
    """Read the hook's JSON payload from stdin, or {} on any failure."""
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def _rules_path() -> Path | None:
    override = os.environ.get("NEXUS_SKILL_RULES", "").strip()
    if override:
        p = Path(override)
        return p if p.is_file() else None
    cwd = Path.cwd()
    for rel in _RULES_FILENAMES:
        p = cwd / rel
        if p.is_file():
            return p
    return None


def load_rules() -> list[dict[str, Any]]:
    """Load the rule list from the discovered rules file, or [] if absent/malformed."""
    path = _rules_path()
    if path is None:
        return []
    try:
        # utf-8-sig tolerates a BOM written by PowerShell on Windows.
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return []
    rules = data.get("rules") if isinstance(data, dict) else None
    if not isinstance(rules, list):
        return []
    return [r for r in rules if isinstance(r, dict)]


def rule_skipped_by_env(rule: dict[str, Any]) -> bool:
    """True when the rule's skipConditions.env variable is set to a non-empty value."""
    env_name = (rule.get("skipConditions") or {}).get("env")
    return bool(env_name) and bool(os.environ.get(str(env_name), "").strip())


def rule_skipped_by_session(rule: dict[str, Any], used: set[str]) -> bool:
    """True when skipConditions.skillAlreadyUsed is set and the skill already ran this session."""
    cond = rule.get("skipConditions") or {}
    return bool(cond.get("skillAlreadyUsed")) and str(rule.get("skill", "")) in used


def prompt_matches(rule: dict[str, Any], prompt: str) -> bool:
    """True when the prompt matches any keyword (case-insensitive substring) or intentPattern (regex)."""
    triggers = rule.get("promptTriggers") or {}
    low = prompt.lower()
    for kw in triggers.get("keywords", []) or []:
        if isinstance(kw, str) and kw and kw.lower() in low:
            return True
    for pat in triggers.get("intentPatterns", []) or []:
        if not isinstance(pat, str):
            continue
        try:
            if re.search(pat, prompt, re.IGNORECASE):
                return True
        except re.error:
            continue
    return False


def _norm(path: str) -> str:
    return path.replace("\\", "/").lower()


def path_matches(rule: dict[str, Any], file_path: str, content: str) -> bool:
    """True when the file path matches a pathPattern, is not excluded, and (if set) content matches.

    pathPatterns are fnmatch-style globs over the forward-slash-normalized,
    lowercased path (note that ``*`` spans ``/`` in fnmatch). When contentPatterns
    are present, the new content must also match at least one of them.
    """
    triggers = rule.get("fileTriggers") or {}
    patterns = triggers.get("pathPatterns") or []
    if not patterns:
        return False
    norm = _norm(file_path)
    if not any(isinstance(p, str) and fnmatch.fnmatchcase(norm, p.lower()) for p in patterns):
        return False
    for excl in triggers.get("pathExclusions", []) or []:
        if isinstance(excl, str) and fnmatch.fnmatchcase(norm, excl.lower()):
            return False
    content_patterns = triggers.get("contentPatterns") or []
    if content_patterns:
        if not content:
            return False
        for pat in content_patterns:
            if not isinstance(pat, str):
                continue
            try:
                if re.search(pat, content, re.IGNORECASE):
                    return True
            except re.error:
                continue
        return False
    return True


# --- session usage state (for skipConditions.skillAlreadyUsed) ---


def _state_file(session_id: str) -> Path:
    sid = session_id or "default"
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", sid)[:80]
    return Path(os.path.expanduser("~")) / ".nexus-hub" / "state" / f"skill-usage-{safe}.json"


def used_skills(session_id: str) -> set[str]:
    """Return the set of skill names recorded for this session, or empty on any error."""
    try:
        p = _state_file(session_id)
        if not p.is_file():
            return set()
        data = json.loads(p.read_text(encoding="utf-8"))
        return {str(s) for s in data} if isinstance(data, list) else set()
    except Exception:
        return set()


def record_skill(session_id: str, skill: str) -> None:
    """Record that a skill ran this session (best-effort; silent on any error)."""
    try:
        if not skill:
            return
        p = _state_file(session_id)
        p.parent.mkdir(parents=True, exist_ok=True)
        current = used_skills(session_id)
        current.add(skill)
        p.write_text(json.dumps(sorted(current)), encoding="utf-8")
    except Exception:
        return
