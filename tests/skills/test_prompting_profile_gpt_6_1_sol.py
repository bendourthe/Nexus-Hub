"""v4.13.9 Phase 2 (T406): the GPT-6.1 Sol prompting profile.

- `gpt-6.1-sol` is a codex entry, present in the codex roster, whose roster hash still matches.
- Every claim cites `developers.openai.com`, carries a confidence, a scope, and a verified date.
- Every quoted passage appears in the evidence text saved on 2026-10-01 and is 300 characters
  or fewer, so no quote can be paraphrased from memory.
- The `none` reasoning effort is recorded as unsupported.
- The generated mirror matches the index, and no shared body names the model.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_BUNDLE = _ROOT / "catalog" / "skills" / "ai-development" / "model-prompting-research"
_INDEX = _BUNDLE / "assets" / "profiles-index.json"
_MIRROR = _BUNDLE / "references" / "models" / "gpt-6.1-sol.md"
_WRITER = _BUNDLE / "scripts" / "write_model_prompting_profile.py"
_VALIDATOR = _ROOT / "scripts" / "verify_model_prompting_profiles.py"
_EVIDENCE = _ROOT / "docs" / "releases" / "v4" / "v4.13" / "development" / "v4.13.9-sol-sources"
_SAVED_TEXT = {
    "https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra": "latest-model.txt",
    "https://developers.openai.com/api/docs/models": "models.txt",
}
_QUOTE = re.compile(r'Quote: "(.+?)"(?=;|\.\s|\s*Verified|$)')
_MODEL = "gpt-6.1-sol"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args], capture_output=True, text=True, check=False, cwd=_ROOT
    )


def _index() -> dict:
    return json.loads(_INDEX.read_text(encoding="utf-8"))


def _claims() -> list[dict]:
    return _index()["models"][_MODEL]["claims"]


def _collapse(text: str) -> str:
    return " ".join(text.split())


def test_entry_is_codex_and_rostered_with_a_valid_hash():
    index = _index()
    entry = index["models"][_MODEL]
    assert entry["platform"] == "codex"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", entry["last_verified"])
    codex = next(e for e in index["meta"]["platforms"] if e["platform"] == "codex")
    assert _MODEL in codex["roster"]
    digest = hashlib.sha256("\n".join(sorted(codex["roster"])).encode("utf-8")).hexdigest()
    assert codex["roster_hash"] == digest


def test_every_claim_is_vendor_sourced_scoped_and_dated():
    claims = _claims()
    assert len(claims) >= 8
    for claim in claims:
        assert claim["source_url"].startswith("https://developers.openai.com/"), claim["source_url"]
        assert claim["confidence"] in ("high", "medium", "low")
        assert claim["scope"] == "model-specific"
        assert re.search(r"Verified \d{4}-\d{2}-\d{2}\.", claim.get("note", "")), claim["claim"]


def test_every_quote_appears_in_the_saved_evidence_and_is_short():
    quoted = 0
    for claim in _claims():
        saved = _collapse((_EVIDENCE / _SAVED_TEXT[claim["source_url"]]).read_text(encoding="utf-8"))
        for quote in _QUOTE.findall(claim.get("note", "")):
            assert len(quote) <= 300, quote
            assert _collapse(quote) in saved, quote
            quoted += 1
    assert quoted >= 10


def test_none_effort_is_recorded_as_unsupported():
    joined = " ".join(c["claim"] for c in _claims())
    assert "none and minimal reasoning efforts are not supported" in joined
    assert "low, medium (the default), high, xhigh, and max" in joined


def test_api_level_claims_are_present():
    joined = " ".join(c["claim"] for c in _claims())
    for marker in ("Responses API", "top_logprobs", "prompt_cache_options.ttl", "configuration_update"):
        assert marker in joined, marker


def test_shipped_layer_passes_the_structural_gate():
    result = _run(str(_VALIDATOR))
    assert result.returncode == 0, result.stdout + result.stderr


def test_plan_for_codex_no_longer_lists_the_model():
    result = _run(str(_WRITER), "plan", "--platform", "codex")
    assert result.returncode == 0, result.stderr
    plan = json.loads(result.stdout)
    assert _MODEL not in plan["targets"]
    assert _MODEL in plan["roster"]


def test_mirror_matches_the_index_entry():
    text = _MIRROR.read_text(encoding="utf-8")
    assert f"# Prompting Profile: {_MODEL}" in text
    assert "**Platform**: codex" in text
    for claim in _claims():
        assert claim["claim"] in text, claim["claim"]


def test_no_shared_body_names_the_model():
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
