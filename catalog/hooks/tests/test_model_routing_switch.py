"""Tests for the model-routing switch helper (Phase 2 of v3.4.0 model-routing).

Exercises catalog/skills/ai-development/model-routing/scripts/switch-model.sh
across the three-tier switch spectrum and its model-validation contract:

  - manual / one-action platforms print an instruction and exit 0;
  - scriptable platforms validate the requested model against the enumerated
    set before emitting a switch command (exit 0 when present, 3 when absent);
  - an unresolvable enumerated set refuses cleanly (exit 4);
  - unknown / unrecognized platforms refuse cleanly (exit 2).

Validation is made deterministic without installing any platform CLI by
passing the enumerated set through the documented NEXUS_ROUTING_MODELS env
seam. A parity check asserts the .ps1 sibling ships alongside the .sh.

Run from the repo root:
    python -m pytest catalog/hooks/tests/test_model_routing_switch.py -v
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

_SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / "catalog"
    / "skills"
    / "ai-development"
    / "model-routing"
    / "scripts"
)
_SWITCH_SH = _SCRIPTS / "switch-model.sh"


def _run(
    bash_bin: str, *args: str, models: str | None = None
) -> subprocess.CompletedProcess:
    """Run switch-model.sh with the given positional args.

    `models`, when given, is exported as NEXUS_ROUTING_MODELS (the enumerated-set
    seam). When None, the var is explicitly removed so the helper falls back to
    live enumeration.
    """
    env = {**os.environ}
    env.pop("NEXUS_ROUTING_MODELS", None)
    if models is not None:
        env["NEXUS_ROUTING_MODELS"] = models
    return subprocess.run(
        [bash_bin, str(_SWITCH_SH), *args],
        text=True,
        capture_output=True,
        env=env,
    )


# ── Manual / one-action tiers (no enumeration needed) ───────────────────────


def test_claude_code_prints_model_and_effort_keystrokes(bash_bin: str):
    r = _run(bash_bin, "claude-code", "claude-opus-4-8", "high")
    assert r.returncode == 0
    assert "/model claude-opus-4-8" in r.stdout
    assert "/effort high" in r.stdout


def test_claude_code_without_effort_omits_effort_line(bash_bin: str):
    r = _run(bash_bin, "claude-code", "claude-opus-4-8")
    assert r.returncode == 0
    assert "/model claude-opus-4-8" in r.stdout
    assert "/effort" not in r.stdout


def test_manual_platform_prints_picker_instruction(bash_bin: str):
    r = _run(bash_bin, "cursor", "claude-sonnet-4-6")
    assert r.returncode == 0
    assert "model picker" in r.stdout


# ── Scriptable tier: model validation against the enumerated set ────────────


def test_scriptable_emits_switch_when_model_in_set(bash_bin: str):
    r = _run(
        bash_bin,
        "codex",
        "gpt-5-codex",
        "high",
        models="gpt-5,o3,gpt-5-codex",
    )
    assert r.returncode == 0
    assert "codex -c model=gpt-5-codex" in r.stdout
    assert "model_reasoning_effort=high" in r.stdout


def test_scriptable_refuses_when_model_not_in_set(bash_bin: str):
    r = _run(bash_bin, "codex", "nonexistent-model", models="gpt-5,o3")
    assert r.returncode == 3
    assert "not in the enumerated set" in r.stderr


def test_scriptable_effort_ignored_where_no_effort_knob(bash_bin: str):
    r = _run(
        bash_bin,
        "antigravity",
        "some-model",
        "high",
        models="some-model,other",
    )
    assert r.returncode == 0
    assert "agy -m some-model" in r.stdout
    assert "no documented effort knob" in r.stderr


def test_scriptable_refuses_when_set_unresolvable(bash_bin: str):
    # gemini-cli's enumerate helper always returns an empty-model sentinel
    # (its models live in alias config), so with no NEXUS_ROUTING_MODELS the
    # set cannot be resolved and the helper must refuse with exit 4 rather
    # than guess. This holds regardless of whether ~/.gemini exists.
    r = _run(bash_bin, "gemini-cli", "gemini-2.5-pro")
    assert r.returncode == 4
    assert "enumeration is unavailable" in r.stderr


# ── Unknown / unrecognized platforms refuse cleanly ─────────────────────────


def test_unknown_platform_refused(bash_bin: str):
    r = _run(bash_bin, "unknown", "some-model")
    assert r.returncode == 2
    assert "unknown" in r.stderr.lower()


def test_unrecognized_platform_refused(bash_bin: str):
    r = _run(bash_bin, "frobnicator", "some-model")
    assert r.returncode == 2
    assert "unrecognized platform" in r.stderr


# ── Cross-platform parity invariant ─────────────────────────────────────────


def test_ps1_sibling_ships_for_every_sh_helper():
    """Every .sh helper under the skill's scripts/ has a .ps1 sibling (the
    AGENTS.md cross-platform parity rule)."""
    sh_helpers = sorted(_SCRIPTS.glob("*.sh"))
    assert sh_helpers, "expected at least one .sh helper under scripts/"
    missing = [
        p.name for p in sh_helpers if not p.with_suffix(".ps1").is_file()
    ]
    assert not missing, f".sh helpers without a .ps1 sibling: {missing}"
