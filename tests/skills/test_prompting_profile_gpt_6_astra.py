"""v4.7.0 amendment Phase 3 (T050): the first OpenAI prompting profile behind the schema-1.1.0 decision.

- The shipped index is schema 1.1.0, carries a codex entry in `meta.platforms`, and passes the
  structural gate; a per-platform `roster_hash` mismatch fails that gate naming the entry.
- `plan --platform codex` no longer lists `gpt-6-astra`.
- Every `gpt-6-astra` claim carries a vendor-domain `source_url` and a `scope`; at least seven
  are the API-level claims the plan named.
- No shared body (templates, commands, any SKILL.md) gained the string `gpt-6-astra`.
- The two closing-summary markers are detected as advisories on their own lines.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_BUNDLE = _ROOT / "catalog" / "skills" / "ai-development" / "model-prompting-research"
_INDEX = _BUNDLE / "assets" / "profiles-index.json"
_MIRROR = _BUNDLE / "references" / "models" / "gpt-6-astra.md"
_WRITER = _BUNDLE / "scripts" / "write_model_prompting_profile.py"
_VALIDATOR = _ROOT / "scripts" / "verify_model_prompting_profiles.py"
_FRESHNESS = _ROOT / "scripts" / "check_model_prompting_freshness.py"
_DETECTOR = (
    _ROOT
    / "catalog"
    / "skills"
    / "developer-experience"
    / "anti-slop-editing"
    / "scripts"
    / "detect_prose_cliches.py"
)
_API_CLAIM_MARKERS = [
    "none reasoning effort",
    "configuration_update",
    "Responses API",
    "async: true",
    "top_logprobs",
    "EU data residency",
    "prompt_cache_options.ttl",
]


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args], capture_output=True, text=True, check=False, cwd=_ROOT
    )


def _index() -> dict:
    return json.loads(_INDEX.read_text(encoding="utf-8"))


def _hash(roster: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(roster)).encode("utf-8")).hexdigest()


def test_shipped_index_is_schema_1_1_0_with_a_codex_platform_entry():
    index = _index()
    assert index["schema_version"] == "1.1.0"
    entries = {e["platform"]: e for e in index["meta"]["platforms"]}
    assert "codex" in entries
    assert entries["codex"]["roster_hash"] == _hash(entries["codex"]["roster"])
    assert "gpt-6-astra" in entries["codex"]["roster"]
    assert index["meta"]["platform"] == "claude-code", (
        "the legacy primary platform is untouched"
    )


def test_shipped_layer_passes_the_structural_gate():
    result = _run(str(_VALIDATOR))
    assert result.returncode == 0, result.stdout + result.stderr


def test_per_platform_roster_hash_mismatch_fails_the_gate(tmp_path: Path):
    index = _index()
    bundle = tmp_path / "bundle"
    (bundle / "assets").mkdir(parents=True)
    (bundle / "references" / "models").mkdir(parents=True)
    for entry in index["meta"]["platforms"]:
        if entry["platform"] == "codex":
            entry["roster_hash"] = "0" * 64
    (bundle / "assets" / "profiles-index.json").write_text(
        json.dumps(index), encoding="utf-8"
    )
    for model_id in index["models"]:
        (bundle / "references" / "models" / f"{model_id}.md").write_text(
            f"# Prompting Profile: {model_id}\n", encoding="utf-8"
        )
    result = _run(str(_VALIDATOR), "--bundle", str(bundle))
    assert result.returncode == 1
    assert (
        "meta.platforms[0].roster_hash does not match" in result.stdout + result.stderr
    )


def test_plan_for_codex_no_longer_lists_gpt_6_astra():
    result = _run(str(_WRITER), "plan", "--platform", "codex")
    assert result.returncode == 0, result.stderr
    plan = json.loads(result.stdout)
    assert "gpt-6-astra" not in plan["targets"]
    assert "gpt-6-astra" in plan["roster"]


def test_every_astra_claim_is_vendor_sourced_and_scoped():
    claims = _index()["models"]["gpt-6-astra"]["claims"]
    assert len(claims) >= 7
    for claim in claims:
        assert claim["source_url"].startswith("https://developers.openai.com/"), claim[
            "source_url"
        ]
        assert claim["scope"] == "model-specific"
        assert claim["confidence"] != "unverified"
    joined = " ".join(c["claim"] for c in claims)
    for marker in _API_CLAIM_MARKERS:
        assert marker in joined, marker


def test_mirror_reflects_the_index_entry():
    text = _MIRROR.read_text(encoding="utf-8")
    assert "# Prompting Profile: gpt-6-astra" in text
    assert "**Platform**: codex" in text
    assert text.count("developers.openai.com") >= 7


def test_no_shared_body_gained_the_model_id():
    surfaces = [
        *(_ROOT / "templates" / "ai-instructions").glob("*.md"),
        *(_ROOT / "catalog" / "commands").glob("*.md"),
        *(_ROOT / "catalog" / "skills").rglob("SKILL.md"),
    ]
    leaked = [
        str(p.relative_to(_ROOT))
        for p in surfaces
        if "gpt-6-astra" in p.read_text(encoding="utf-8", errors="replace")
    ]
    assert leaked == [], leaked


def test_freshness_reads_the_codex_entry_with_platform_flag(tmp_path: Path):
    index = _index()
    codex = next(e for e in index["meta"]["platforms"] if e["platform"] == "codex")
    bundle = tmp_path / "bundle"
    (bundle / "assets").mkdir(parents=True)
    (bundle / "references" / "models").mkdir(parents=True)
    (bundle / "assets" / "profiles-index.json").write_text(
        json.dumps(index), encoding="utf-8"
    )
    result = _run(
        str(_FRESHNESS),
        "--advisory",
        "--bundle",
        str(bundle),
        "--platform",
        "codex",
        *codex["roster"],
    )
    assert result.returncode == 0
    assert "IN SYNC" in result.stdout


def test_closing_summary_markers_are_flagged_once_per_line(tmp_path: Path):
    fixture = tmp_path / "markers.md"
    fixture.write_text("Bottom Line: ship it\n\nIn short: done\n", encoding="utf-8")
    result = _run(str(_DETECTOR), "--json", str(fixture))
    report = json.loads(result.stdout)
    findings = report["findings"] if isinstance(report, dict) else report
    marker_hits = [f for f in findings if f["id"] == "closing-summary-marker"]
    assert len(marker_hits) == 2
    assert all(f["class"] == "advisory" for f in marker_hits)
