"""Argon profile, source boundaries and existing Google placement regressions."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

_ROOT = Path(__file__).resolve().parents[2]
_BUNDLE = _ROOT / "catalog" / "skills" / "ai-development" / "model-prompting-research"
_INDEX = _BUNDLE / "assets" / "profiles-index.json"
_WRITER = _BUNDLE / "scripts" / "write_model_prompting_profile.py"
_VALIDATOR = _ROOT / "scripts" / "verify_model_prompting_profiles.py"
_MAP = (
    _ROOT / "catalog" / "skills" / "ai-development" / "model-routing"
    / "references" / "last-known-model-map.json"
)
_ALLOWED = {
    "ai.google.dev", "docs.cloud.google.com", "cloud.google.com",
    "aistudio.google.com", "blog.google",
}
_MODEL = "gemini-4-argon"


def _index() -> dict:
    return json.loads(_INDEX.read_text(encoding="utf-8"))


def _claims() -> list[dict]:
    return _index()["models"][_MODEL]["claims"]


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args], cwd=_ROOT, capture_output=True, text=True, check=False
    )


def test_shipped_layer_passes_structural_gate():
    result = _run(str(_VALIDATOR))
    assert result.returncode == 0, result.stdout + result.stderr


def test_gemini_roster_contains_argon_with_valid_hash():
    entry = next(
        e for e in _index()["meta"]["platforms"] if e["platform"] == "gemini"
    )
    assert _MODEL in entry["roster"]
    assert "gemini-4-argon-cyber-permissive" not in entry["roster"]
    expected = hashlib.sha256(
        "\n".join(sorted(entry["roster"])).encode("utf-8")
    ).hexdigest()
    assert entry["roster_hash"] == expected
    assert entry["roster_source"] == "api"


def test_platform_plan_no_longer_lists_argon_for_research():
    result = _run(str(_WRITER), "plan", "--platform", "gemini")
    assert result.returncode == 0, result.stderr
    planned = json.loads(result.stdout)
    assert _MODEL in planned["roster"]
    assert _MODEL not in planned["targets"]


def test_every_claim_has_an_allowlisted_source_and_recorded_scope():
    claims = _claims()
    model_claims = [c for c in claims if c["scope"] == "model-specific"]
    candidates = [c for c in claims if c["scope"] == "model-agnostic-candidate"]
    assert len(model_claims) == 14
    assert len(candidates) == 1
    assert len(claims) == len(model_claims) + len(candidates)
    for claim in claims:
        parsed = urlsplit(claim["source_url"])
        assert parsed.scheme == "https"
        assert parsed.hostname in _ALLOWED, claim["source_url"]
        assert claim["confidence"] != "unverified"
    for claim in model_claims:
        assert claim["scope"] == "model-specific"
        assert claim["evidence_scope"] == "model"


def test_preflight_is_a_cited_page_candidate_with_correct_source_numbering():
    candidates = [c for c in _claims() if c["scope"] == "model-agnostic-candidate"]
    assert len(candidates) == 1
    claim = candidates[0]
    assert claim["claim"] == (
        "Before a long autonomous run, confirm access to the required tools "
        "and documentation and agreement on the intended result."
    )
    assert claim["source_url"] == (
        "https://aistudio.google.com/learn/gemini-4-argon-developer-guide"
    )
    assert claim["confidence"] == "medium"
    assert claim["evidence_scope"] == "cited-page"
    assert "page 8, tip 1, third bullet" in claim["note"]
    assert "not evidence of a model-specific advantage" in claim["note"]
    assert "cross-model effectiveness" in claim["note"]
    assert "actual tip 2 on page 9 concerns verification" in claim["note"]


def test_claim_text_is_plain_paraphrase_without_agent_directives():
    for claim in _claims():
        text = claim["claim"]
        assert not any(token in text for token in ("|", "<", "](")), text
        assert not re.search(
            r"\bignore\b|you must|system:", text, re.IGNORECASE
        ), text


def test_thinking_budget_claims_remain_scoped_to_their_surfaces():
    claims = [c for c in _claims() if "thinking_budget" in c["claim"]]
    legacy = [c for c in claims if "/generate-content/thinking" in c["source_url"]]
    cloud = [
        c for c in claims
        if urlsplit(c["source_url"]).hostname == "docs.cloud.google.com"
    ]
    assert len(legacy) == len(cloud) == 1
    assert "alone" in legacy[0]["claim"] and "warning" in legacy[0]["claim"]
    assert "combining both" in legacy[0]["claim"] and "400" in legacy[0]["claim"]
    assert "Cloud" in cloud[0]["claim"] and "400" in cloud[0]["claim"]


def test_cloud_prose_avoidance_is_guidance_not_a_behavior_guarantee():
    calls = [c for c in _claims() if "FunctionResponse" in c["claim"]]
    assert len(calls) == 1
    assert urlsplit(calls[0]["source_url"]).hostname == "docs.cloud.google.com"
    text = calls[0]["claim"]
    assert "id, name and order" in text
    assert "guidance discourages unstructured prose" in text


def test_timeout_claims_do_not_transfer_legacy_guidance_to_other_surfaces():
    claims = [c for c in _claims() if "timeout" in c["claim"]]
    legacy = [
        c for c in claims if "/generate-content/latest-model" in c["source_url"]
    ]
    interactions = [
        c for c in claims
        if c["source_url"] == "https://ai.google.dev/gemini-api/docs/latest-model"
    ]
    assert len(legacy) == len(interactions) == 1
    assert "Legacy" in legacy[0]["claim"] and "20 minutes" in legacy[0]["claim"]
    current = interactions[0]["claim"]
    assert "Interactions" in current and "15 minutes" in current
    assert "exceeding 65,536 tokens requires background execution" in current
    assert not any(
        urlsplit(c["source_url"]).hostname == "docs.cloud.google.com"
        for c in claims
    )


def test_generated_mirror_matches_each_claim_and_is_linked():
    mirror = (_BUNDLE / "references" / "models" / f"{_MODEL}.md").read_text(
        encoding="utf-8"
    )
    links = (_BUNDLE / "references" / "model-profiles.md").read_text(
        encoding="utf-8"
    )
    assert f"# Prompting Profile: {_MODEL}" in mirror
    for claim in _claims():
        assert claim["claim"] in mirror
        assert claim["source_url"] in mirror
    assert f"(models/{_MODEL}.md)" in links


def test_model_id_does_not_leak_into_shared_bodies():
    roots = [
        _ROOT / "templates" / "ai-instructions",
        _ROOT / "catalog" / "commands",
        _ROOT / "catalog" / "skills",
    ]
    assert all(p.is_dir() for p in roots), "the complete source surfaces are required"
    groups = [
        list(roots[0].glob("*.md")),
        list(roots[1].glob("*.md")),
        list(roots[2].rglob("SKILL.md")),
    ]
    assert all(group for group in groups), "every shared surface must be scanned"
    leaked = [
        str(p.relative_to(_ROOT))
        for group in groups
        for p in group
        if _MODEL in p.read_text(encoding="utf-8", errors="replace")
    ]
    assert leaked == [], leaked


def test_existing_google_frontier_and_strong_placements_are_preserved():
    snapshot = json.loads(_MAP.read_text(encoding="utf-8"))
    assert snapshot["tiers"]["frontier"]["Google"] == _MODEL
    assert snapshot["tiers"]["strong"]["Google"] == "gemini-3.8-flash"
