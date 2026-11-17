"""v4.15.11 Phase 1 (T003): the Claude Fable 5.2 prompting profile.

- The index carries a `claude-fable-5-2` entry whose every claim cites the vendor's own
  Fable 5.2 prompting guide, is model-specific, and records the quoted source wording.
- The claims cover each measured finding the plan names, with its number and its cost.
- The Markdown mirror matches the index entry claim for claim.
- The primary roster lists the model and kept every profiled model.
- No shared body (templates, commands, any SKILL.md) gained the string `claude-fable-5-2`,
  except the opt-in ownership reference, which is a reference file and not a shared body.
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
_MIRROR = _BUNDLE / "references" / "models" / "claude-fable-5-2.md"
_WRITER = _BUNDLE / "scripts" / "write_model_prompting_profile.py"
_VALIDATOR = _ROOT / "scripts" / "verify_model_prompting_profiles.py"
_MODEL = "claude-fable-5-2"
_GUIDE = (
    "https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/"
    "prompting-claude-fable-5-2"
)

# One marker per finding the plan requires the entry to record.
_COVERAGE_MARKERS = [
    "defaults to high",  # effort default
    "medium and xhigh",  # sweep advice
    "answer directly without deliberating",  # think-less lines no longer work
    "about half as many sessions ended with unfinished work",  # finishing work
    "about 30 percent",  # finishing-work token cost
    "name the exact actions",  # approval rules
    "about 75 percent",  # ownership: consolidation with the sentence
    "under 10 percent",  # ownership: consolidation without it
    "70 to 80 percent",  # ownership token cost
    "unrequested changes",
    "A scope rule does not cancel the ownership sentence",
    "left out small changes",  # summaries omit small changes
    "progress-update thinking blocks",
    "about 20 percent",  # progress-update text cost
    "roughly halved the number of subagents",
    "treats never as absolute",  # scoped never rules
    "token budget shown in the prompt",  # older-harness removal
    "low-context reader",
    "reasoning_extraction",
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
    assert len(entry["claims"]) >= 12


def test_every_claim_is_vendor_sourced_scoped_and_verified():
    for claim in _claims():
        assert claim["source_url"].startswith(_GUIDE), claim["source_url"]
        assert claim["scope"] == "model-specific", claim["claim"]
        assert claim["confidence"] in {"high", "medium"}, claim["claim"]
        assert "Quote: " in claim.get("note", ""), claim["claim"]


@pytest.mark.parametrize("marker", _COVERAGE_MARKERS)
def test_required_finding_is_recorded(marker: str):
    joined = " ".join(c["claim"] for c in _claims())
    assert marker in joined, marker


def test_mirror_matches_the_index_claim_for_claim():
    text = _MIRROR.read_text(encoding="utf-8")
    assert f"# Prompting Profile: {_MODEL}" in text
    claims = _claims()
    for claim in claims:
        assert claim["claim"][:60] in text, claim["claim"][:60]
    assert text.count("platform.claude.com") == len(claims)


def test_ownership_claim_points_to_the_opt_in_reference():
    ownership = [c for c in _claims() if "70 to 80 percent" in c["claim"]]
    assert len(ownership) == 1
    assert "codebase-ownership-mode.md" in ownership[0]["claim"]


def test_primary_roster_lists_the_model_and_kept_every_profiled_model():
    meta = _index()["meta"]
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
