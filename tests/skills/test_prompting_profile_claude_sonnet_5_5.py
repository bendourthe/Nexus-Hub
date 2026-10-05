"""v4.13.8 Phase 2 (T307): the Claude Sonnet 5.5 prompting profile.

- The index carries a `claude-sonnet-5-5` entry whose every claim cites the vendor's own
  documentation under platform.claude.com, is model-specific, and survived verification.
- The claims cover the areas the plan names, including all five breaking API changes.
- The Markdown mirror matches the index entry claim for claim.
- The primary roster was refreshed from a live API enumeration without dropping a profiled model.
- No shared body (templates, commands, any SKILL.md) gained the string `claude-sonnet-5-5`.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_BUNDLE = _ROOT / "catalog" / "skills" / "ai-development" / "model-prompting-research"
_INDEX = _BUNDLE / "assets" / "profiles-index.json"
_MIRROR = _BUNDLE / "references" / "models" / "claude-sonnet-5-5.md"
_WRITER = _BUNDLE / "scripts" / "write_model_prompting_profile.py"
_VALIDATOR = _ROOT / "scripts" / "verify_model_prompting_profiles.py"
_MODEL = "claude-sonnet-5-5"
_VENDOR_PREFIX = "https://platform.claude.com/docs/en/"

# One marker per area the plan requires the entry to cover.
_COVERAGE_MARKERS = [
    "recalibrated",  # effort levels and the Claude API default
    "at medium for well-specified tasks",  # agentic-coding starting effort
    "128,000",  # max_tokens headroom for thinking
    "at xhigh or max effort a request with between_tools returns a 400 error",
    "per-message output_config.effort",  # no per-message effort change with between_tools
    "display, budget_tokens, or block_binding",  # between_tools takes no other field
    "Think the problem through before you answer.",  # the JSON reasoning-task line
    "checks in before the work is done",  # check-ins at low and medium effort
    "reviewer subagents",  # self-started review rounds at xhigh and max
    "progress-update thinking blocks",
    "turn-scoped system message",  # the progress reminder
    "possible prompt injection",  # mid-turn user messages
    "real check that exercises the change",  # the verification paragraph
    "letter case",  # tolerant tool-call handling
    "reasoning_extraction",  # safeguard refusal categories
]

# One marker per breaking API change the migration guide lists for moves from Claude Sonnet 5.
_BREAKING_MARKERS = [
    "tool_choice of type any or tool is rejected",
    "Opus 5.5, or any Fable or Mythos model",
    "computer_toolset_20260801",
    "advisor tool",
    "between tool calls returns in progress-update thinking blocks",
]


def _index() -> dict:
    return json.loads(_INDEX.read_text(encoding="utf-8"))


def _claims() -> list[dict]:
    return _index()["models"][_MODEL]["claims"]


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args], capture_output=True, text=True, check=False, cwd=_ROOT
    )


def test_entry_exists_on_the_primary_platform():
    entry = _index()["models"][_MODEL]
    assert entry["platform"] == "claude-code"
    assert len(entry["claims"]) >= 30


def test_every_claim_is_vendor_sourced_scoped_and_verified():
    for claim in _claims():
        assert claim["source_url"].startswith(_VENDOR_PREFIX), claim["source_url"]
        assert claim["scope"] == "model-specific", claim["claim"]
        assert claim["confidence"] in {"high", "medium"}, claim["claim"]
        assert "Quote: " in claim.get("note", ""), claim["claim"]


@pytest.mark.parametrize("marker", _COVERAGE_MARKERS)
def test_required_area_is_covered(marker: str):
    joined = " ".join(c["claim"] for c in _claims())
    assert marker in joined, marker


@pytest.mark.parametrize("marker", _BREAKING_MARKERS)
def test_each_breaking_api_change_is_recorded(marker: str):
    breaking = [c["claim"] for c in _claims() if c["claim"].startswith("Breaking change from Claude Sonnet 5")]
    assert any(marker in text for text in breaking), marker


def test_mirror_matches_the_index_claim_for_claim():
    text = _MIRROR.read_text(encoding="utf-8")
    assert f"# Prompting Profile: {_MODEL}" in text
    assert "**Roster provenance**: `api`" in text
    claims = _claims()
    for claim in claims:
        assert claim["claim"][:60] in text, claim["claim"][:60]
    assert text.count("platform.claude.com") == len(claims)


def test_primary_roster_is_live_and_kept_every_profiled_model():
    meta = _index()["meta"]
    assert meta["roster_source"] == "api"
    assert _MODEL in meta["roster"]
    expected = hashlib.sha256("\n".join(sorted(meta["roster"])).encode("utf-8")).hexdigest()
    assert meta["roster_hash"] == expected
    primary_models = [m for m, e in _index()["models"].items() if e["platform"] == "claude-code"]
    missing = [m for m in primary_models if m not in meta["roster"]]
    assert missing == [], missing


def test_planner_no_longer_lists_the_model():
    result = _run(str(_WRITER), "plan")
    assert result.returncode == 0, result.stderr
    assert _MODEL not in json.loads(result.stdout)["targets"]


def test_shipped_layer_passes_the_structural_gate():
    result = _run(str(_VALIDATOR))
    assert result.returncode == 0, result.stdout + result.stderr


def test_no_shared_body_gained_the_model_id():
    surfaces = [
        *(_ROOT / "templates" / "ai-instructions").glob("*.md"),
        *(_ROOT / "catalog" / "commands").glob("*.md"),
        *(_ROOT / "catalog" / "skills").rglob("SKILL.md"),
    ]
    leaked = [
        str(p.relative_to(_ROOT))
        for p in surfaces
        if _MODEL in p.read_text(encoding="utf-8", errors="replace")
    ]
    assert leaked == [], leaked
