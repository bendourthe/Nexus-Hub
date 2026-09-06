"""Tests for the skill-activation hooks (skill-activation-suggest.py, skill-guard.py, skill-tracker.py).

Run from the repo root:
    python -m pytest catalog/hooks/tests/test_skill_activation.py -v

The hooks are advisory and fail-open by design: they always exit 0, are no-ops
when the rules file is absent, honor NEXUS_DISABLED_HOOKS / NEXUS_HOOK_PROFILE,
and the guard blocks ONLY when NEXUS_SKILL_GUARD_BLOCK=1 AND a matched rule is
enforcement=block. Tests invoke each Python hook via subprocess with a JSON
payload on stdin and a temp rules file pointed at by NEXUS_SKILL_RULES, and
assert on (stdout, stderr, exit_code). Python is the interpreter running pytest,
so no bash/jq is required and the suite never skips.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

_HOOKS_DIR = Path(__file__).parent.parent
_ACTIVATION = _HOOKS_DIR / "skill-activation-suggest.py"
_GUARD = _HOOKS_DIR / "skill-guard.py"
_TRACKER = _HOOKS_DIR / "skill-tracker.py"

_CONTROLLED_ENV = (
    "NEXUS_HOOK_PROFILE",
    "NEXUS_DISABLED_HOOKS",
    "NEXUS_SKILL_RULES",
    "NEXUS_SKILL_GUARD_BLOCK",
)


# ── Helpers ────────────────────────────────────────────────────────────────


def _run(hook: Path, payload: dict[str, Any], env_overrides: dict[str, str] | None = None) -> tuple[str, str, int]:
    env = os.environ.copy()
    for key in _CONTROLLED_ENV:
        env.pop(key, None)
    if env_overrides:
        env.update(env_overrides)
    result = subprocess.run(
        [sys.executable, str(hook)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )
    return result.stdout, result.stderr, result.returncode


def _write_rules(tmp_path: Path, rules: list[dict[str, Any]]) -> str:
    path = tmp_path / "skill-rules.json"
    path.write_text(json.dumps({"version": 1, "rules": rules}), encoding="utf-8")
    return str(path)


_SUGGEST_RULE = {
    "skill": "security-review",
    "enforcement": "suggest",
    "promptTriggers": {"keywords": ["auth", "login"], "intentPatterns": []},
    "fileTriggers": {"pathPatterns": ["*/auth/*", "*auth*"], "pathExclusions": ["*/tests/*"]},
    "message": "Editing auth code - load security-review.",
}
_BLOCK_RULE = {
    "skill": "test-driven-development",
    "enforcement": "block",
    "fileTriggers": {"pathPatterns": ["src/*"], "pathExclusions": ["*.test.*"]},
    "message": "Write the failing test first.",
}


def _prompt(text: str) -> dict[str, Any]:
    return {"prompt": text, "session_id": "test-session"}


def _write(file_path: str, content: str = "x = 1") -> dict[str, Any]:
    return {"tool_name": "Write", "tool_input": {"file_path": file_path, "content": content}, "session_id": "test-session"}


# ── Activation hook ──────────────────────────────────────────────────────────


def test_activation_suggests_on_prompt_match(tmp_path: Path) -> None:
    rules = _write_rules(tmp_path, [_SUGGEST_RULE])
    stdout, _stderr, code = _run(_ACTIVATION, _prompt("please add auth to the API"), {"NEXUS_SKILL_RULES": rules})
    assert code == 0
    assert "security-review" in stdout


def test_activation_silent_when_no_prompt_match(tmp_path: Path) -> None:
    rules = _write_rules(tmp_path, [_SUGGEST_RULE])
    stdout, _stderr, code = _run(_ACTIVATION, _prompt("please restyle the CSS"), {"NEXUS_SKILL_RULES": rules})
    assert code == 0
    assert stdout.strip() == ""


def test_activation_noop_when_rules_absent(tmp_path: Path) -> None:
    missing = str(tmp_path / "does-not-exist.json")
    stdout, _stderr, code = _run(_ACTIVATION, _prompt("add auth"), {"NEXUS_SKILL_RULES": missing})
    assert code == 0
    assert stdout.strip() == ""


def test_activation_disabled_via_env(tmp_path: Path) -> None:
    rules = _write_rules(tmp_path, [_SUGGEST_RULE])
    stdout, _stderr, code = _run(
        _ACTIVATION, _prompt("add auth"),
        {"NEXUS_SKILL_RULES": rules, "NEXUS_DISABLED_HOOKS": "skill-activation-suggest"},
    )
    assert code == 0
    assert stdout.strip() == ""


def test_activation_minimal_profile_short_circuits(tmp_path: Path) -> None:
    rules = _write_rules(tmp_path, [_SUGGEST_RULE])
    stdout, _stderr, code = _run(
        _ACTIVATION, _prompt("add auth"),
        {"NEXUS_SKILL_RULES": rules, "NEXUS_HOOK_PROFILE": "minimal"},
    )
    assert code == 0
    assert stdout.strip() == ""


# ── Guard hook ───────────────────────────────────────────────────────────────


def test_guard_suggests_by_default(tmp_path: Path) -> None:
    rules = _write_rules(tmp_path, [_SUGGEST_RULE])
    stdout, stderr, code = _run(_GUARD, _write("app/auth/login.py"), {"NEXUS_SKILL_RULES": rules})
    assert code == 0
    assert "security-review" in stderr
    assert "deny" not in stdout


def test_guard_does_not_block_a_block_rule_without_the_flag(tmp_path: Path) -> None:
    rules = _write_rules(tmp_path, [_BLOCK_RULE])
    stdout, stderr, code = _run(_GUARD, _write("src/foo.py"), {"NEXUS_SKILL_RULES": rules})
    assert code == 0
    assert "deny" not in stdout
    assert "test-driven-development" in stderr


def test_guard_blocks_when_flag_set_and_rule_is_block(tmp_path: Path) -> None:
    rules = _write_rules(tmp_path, [_BLOCK_RULE])
    stdout, _stderr, code = _run(
        _GUARD, _write("src/foo.py"),
        {"NEXUS_SKILL_RULES": rules, "NEXUS_SKILL_GUARD_BLOCK": "1"},
    )
    assert code == 0
    payload = json.loads(stdout)
    hso = payload["hookSpecificOutput"]
    assert hso["permissionDecision"] == "deny"
    assert "test-driven-development" in hso["permissionDecisionReason"]


def test_guard_suggest_rule_never_blocks_even_with_flag(tmp_path: Path) -> None:
    rules = _write_rules(tmp_path, [_SUGGEST_RULE])
    stdout, stderr, code = _run(
        _GUARD, _write("app/auth/login.py"),
        {"NEXUS_SKILL_RULES": rules, "NEXUS_SKILL_GUARD_BLOCK": "1"},
    )
    assert code == 0
    assert "deny" not in stdout
    assert "security-review" in stderr


def test_guard_respects_path_exclusions(tmp_path: Path) -> None:
    rules = _write_rules(tmp_path, [_SUGGEST_RULE])
    stdout, stderr, code = _run(_GUARD, _write("app/tests/auth_helper.py"), {"NEXUS_SKILL_RULES": rules})
    assert code == 0
    assert stderr.strip() == ""
    assert "deny" not in stdout


def test_guard_failopen_on_malformed_rules(tmp_path: Path) -> None:
    bad = tmp_path / "skill-rules.json"
    bad.write_text("{ this is not valid json", encoding="utf-8")
    stdout, stderr, code = _run(
        _GUARD, _write("src/foo.py"),
        {"NEXUS_SKILL_RULES": str(bad), "NEXUS_SKILL_GUARD_BLOCK": "1"},
    )
    assert code == 0
    assert "deny" not in stdout


def test_guard_noop_when_rules_absent(tmp_path: Path) -> None:
    missing = str(tmp_path / "nope.json")
    stdout, stderr, code = _run(_GUARD, _write("app/auth/login.py"), {"NEXUS_SKILL_RULES": missing})
    assert code == 0
    assert stderr.strip() == ""
    assert "deny" not in stdout


def test_guard_disabled_via_env(tmp_path: Path) -> None:
    rules = _write_rules(tmp_path, [_SUGGEST_RULE])
    stdout, stderr, code = _run(
        _GUARD, _write("app/auth/login.py"),
        {"NEXUS_SKILL_RULES": rules, "NEXUS_DISABLED_HOOKS": "skill-guard"},
    )
    assert code == 0
    assert stderr.strip() == ""


# ── Tracker + skipConditions round-trip ──────────────────────────────────────


def test_tracker_records_and_guard_skips_already_used_skill(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    home_env = {"HOME": str(home), "USERPROFILE": str(home)}

    # Record that security-review ran this session.
    _run(
        _TRACKER,
        {"tool_name": "Skill", "tool_input": {"skill": "security-review"}, "session_id": "sess-1"},
        home_env,
    )

    # A rule with skipConditions.skillAlreadyUsed should now be skipped.
    skip_rule = {
        **_SUGGEST_RULE,
        "skipConditions": {"skillAlreadyUsed": True},
    }
    rules = _write_rules(tmp_path, [skip_rule])
    payload = {"tool_name": "Write", "tool_input": {"file_path": "app/auth/login.py", "content": "x"}, "session_id": "sess-1"}
    _stdout, stderr, code = _run(_GUARD, payload, {**home_env, "NEXUS_SKILL_RULES": rules})
    assert code == 0
    assert "security-review" not in stderr
