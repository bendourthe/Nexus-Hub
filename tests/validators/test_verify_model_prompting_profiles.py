"""Tests for scripts/verify_model_prompting_profiles.py (v3.15.5 Phase 1).

The validator is the HARD structural gate on the per-model prompting profile
layer. These tests prove three things: the real shipped seed passes, every
documented structural rule fails loudly when broken, and the two rules that are
deliberately NOT enforced (roster coverage, freshness) stay unenforced.

Each case runs the script as a subprocess via the shared `runner` fixture against
a synthesized bundle in a temporary directory, so the tests exercise the actual
CLI surface end users will run.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Iterable
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

SCRIPT = "verify_model_prompting_profiles.py"
CATALOG_BUNDLE_REL = Path("catalog/skills/ai-development/model-prompting-research")
FLAT_BUNDLE_REL = Path("skills/model-prompting-research")


def _roster_hash(roster: list[str]) -> str:
    """Recompute the canonical roster hash independently of the script.

    Deliberately duplicated rather than imported: if someone changes the joining
    rule in the script, this test should fail rather than silently agree with it.
    """
    return hashlib.sha256("\n".join(sorted(roster)).encode("utf-8")).hexdigest()


def _valid_index(roster: list[str] | None = None) -> dict:
    """A minimal, valid index carrying one profiled model."""
    roster = sorted(roster if roster is not None else ["model-a", "model-b"])
    return {
        "schema_version": "1.0.0",
        "meta": {
            "last_verified": "2026-07-27",
            "platform": "claude-code",
            "roster_source": "picker",
            "roster": roster,
            "roster_hash": _roster_hash(roster),
        },
        "models": {
            "model-a": {
                "platform": "claude-code",
                "last_verified": "2026-07-27",
                "claims": [
                    {
                        "claim": "Be explicit about the desired output shape.",
                        "source_url": "https://example.invalid/docs/prompting",
                        "confidence": "high",
                        "scope": "model-specific",
                    }
                ],
            }
        },
    }


def _write_bundle(
    root: Path,
    index: dict | str,
    mirrors: Iterable[str] = ("model-a",),
    *,
    flattened: bool = False,
) -> Path:
    """Materialize a profile-layer bundle under `root`. Returns the bundle path."""
    bundle = root / (FLAT_BUNDLE_REL if flattened else CATALOG_BUNDLE_REL)
    (bundle / "assets").mkdir(parents=True, exist_ok=True)
    (bundle / "references" / "models").mkdir(parents=True, exist_ok=True)
    payload = index if isinstance(index, str) else json.dumps(index, indent=2)
    (bundle / "assets" / "profiles-index.json").write_text(payload, encoding="utf-8")
    for model_id in mirrors:
        (bundle / "references" / "models" / f"{model_id}.md").write_text(
            f"# Prompting Profile: {model_id}\n", encoding="utf-8"
        )
    return bundle


# ---------------------------------------------------------------------------
# The shipped seed (the must-pass baseline `make validate` runs)
# ---------------------------------------------------------------------------


def test_shipped_seed_layer_is_structurally_valid(runner) -> None:
    result = runner(SCRIPT, REPO_ROOT)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "[profile-schema] OK" in result.stdout


def test_shipped_seed_reports_unprofiled_rostered_models_as_a_note(runner) -> None:
    """Rostered-but-unprofiled models are surfaced, but never as a failure."""
    result = runner(SCRIPT, REPO_ROOT)

    assert result.returncode == 0
    assert "not yet profiled" in result.stdout
    assert "not a gate failure" in result.stdout


# ---------------------------------------------------------------------------
# Bundle discovery
# ---------------------------------------------------------------------------


def test_valid_fixture_bundle_passes(tmp_path: Path, runner) -> None:
    _write_bundle(tmp_path, _valid_index())

    result = runner(SCRIPT, tmp_path)

    assert result.returncode == 0, result.stdout
    assert "[profile-schema] OK: 1 profiled model(s) of 2 rostered" in result.stdout


def test_flattened_installed_layout_is_discovered(tmp_path: Path, runner) -> None:
    """The installed copy sees `skills/<name>/`, not the in-repo catalog path."""
    _write_bundle(tmp_path, _valid_index(), flattened=True)

    result = runner(SCRIPT, tmp_path)

    assert result.returncode == 0, result.stdout


def test_missing_bundle_fails_with_the_searched_paths(tmp_path: Path, runner) -> None:
    result = runner(SCRIPT, tmp_path)

    assert result.returncode == 1
    assert "MISSING bundle" in result.stdout
    assert "model-prompting-research" in result.stdout


def test_missing_index_fails(tmp_path: Path, runner) -> None:
    bundle = tmp_path / CATALOG_BUNDLE_REL
    (bundle / "references" / "models").mkdir(parents=True)

    result = runner(SCRIPT, tmp_path)

    assert result.returncode == 1
    assert "missing profile index" in result.stdout


def test_unparseable_index_fails(tmp_path: Path, runner) -> None:
    _write_bundle(tmp_path, "{not json,")

    result = runner(SCRIPT, tmp_path)

    assert result.returncode == 1
    assert "not valid JSON" in result.stdout


# ---------------------------------------------------------------------------
# Structural rules: one parametrized mutation per documented rule
# ---------------------------------------------------------------------------


def _drop_top_key(key: str) -> Callable[[dict], None]:
    def mutate(index: dict) -> None:
        del index[key]

    return mutate


MUTATIONS: list[tuple[str, Callable[[dict], None], str]] = [
    (
        "unknown_top_level_key",
        lambda index: index.update({"profiles": {}}),
        "unknown top-level key(s): profiles",
    ),
    ("missing_meta", _drop_top_key("meta"), "missing required top-level key 'meta'"),
    ("missing_models", _drop_top_key("models"), "missing required top-level key 'models'"),
    (
        "missing_schema_version",
        _drop_top_key("schema_version"),
        "missing required top-level key 'schema_version'",
    ),
    (
        "unknown_meta_key",
        lambda index: index["meta"].update({"rooster": []}),
        "meta has unknown key(s): rooster",
    ),
    (
        "missing_meta_key",
        lambda index: index["meta"].pop("platform"),
        "meta is missing required key 'platform'",
    ),
    (
        "bad_last_verified_format",
        lambda index: index["meta"].update({"last_verified": "July 2026"}),
        "meta.last_verified must be a YYYY-MM-DD string",
    ),
    (
        "bad_roster_source",
        lambda index: index["meta"].update({"roster_source": "guess"}),
        "meta.roster_source must be one of",
    ),
    (
        "unsorted_roster",
        lambda index: index["meta"].update(
            {"roster": ["model-b", "model-a"], "roster_hash": _roster_hash(["model-a", "model-b"])}
        ),
        "meta.roster must be sorted ascending",
    ),
    (
        "duplicate_roster_entry",
        lambda index: index["meta"].update(
            {
                "roster": ["model-a", "model-a", "model-b"],
                "roster_hash": _roster_hash(["model-a", "model-a", "model-b"]),
            }
        ),
        "must not contain duplicate model ids",
    ),
    (
        "empty_roster",
        lambda index: index["meta"].update({"roster": []}),
        "meta.roster must be a non-empty array",
    ),
    (
        "roster_hash_not_restamped",
        lambda index: index["meta"]["roster"].append("model-c"),
        "meta.roster_hash does not match meta.roster",
    ),
    (
        "roster_hash_wrong_shape",
        lambda index: index["meta"].update({"roster_hash": "deadbeef"}),
        "must be 64 lowercase hex characters",
    ),
    (
        "empty_models_map",
        lambda index: index.update({"models": {}}),
        "models must carry at least one model entry",
    ),
    (
        "unknown_model_key",
        lambda index: index["models"]["model-a"].update({"notes": "x"}),
        "has unknown key(s): notes",
    ),
    (
        "missing_model_key",
        lambda index: index["models"]["model-a"].pop("platform"),
        "is missing required key 'platform'",
    ),
    (
        "empty_claims",
        lambda index: index["models"]["model-a"].update({"claims": []}),
        "claims must be a non-empty array",
    ),
    (
        "claim_typo_key",
        lambda index: index["models"]["model-a"]["claims"][0].update({"sources_url": "x"}),
        "has unknown key(s): sources_url",
    ),
    (
        "claim_missing_required_key",
        lambda index: index["models"]["model-a"]["claims"][0].pop("scope"),
        "is missing required key 'scope'",
    ),
    (
        "claim_empty_text",
        lambda index: index["models"]["model-a"]["claims"][0].update({"claim": "  "}),
        ".claim must be a non-empty string",
    ),
    (
        "claim_non_http_source",
        lambda index: index["models"]["model-a"]["claims"][0].update(
            {"source_url": "docs/prompting.md"}
        ),
        ".source_url must be an http(s) URL",
    ),
    (
        "claim_bad_confidence",
        lambda index: index["models"]["model-a"]["claims"][0].update({"confidence": "pretty sure"}),
        ".confidence must be one of",
    ),
    (
        "claim_bad_scope",
        lambda index: index["models"]["model-a"]["claims"][0].update({"scope": "shared-body"}),
        ".scope must be one of",
    ),
    (
        "claim_non_string_note",
        lambda index: index["models"]["model-a"]["claims"][0].update({"note": 7}),
        ".note must be a string when present",
    ),
]


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [pytest.param(fn, expected, id=name) for name, fn, expected in MUTATIONS],
)
def test_structural_violation_fails(
    tmp_path: Path, runner, mutation: Callable[[dict], None], expected: str
) -> None:
    index = _valid_index()
    mutation(index)
    _write_bundle(tmp_path, index)

    result = runner(SCRIPT, tmp_path)

    assert result.returncode == 1, f"expected failure, got:\n{result.stdout}"
    assert expected in result.stdout, result.stdout


# ---------------------------------------------------------------------------
# Bidirectional mirror match
# ---------------------------------------------------------------------------


def test_indexed_model_without_a_markdown_mirror_fails(tmp_path: Path, runner) -> None:
    _write_bundle(tmp_path, _valid_index(), mirrors=())

    result = runner(SCRIPT, tmp_path)

    assert result.returncode == 1
    assert "has no Markdown mirror" in result.stdout


def test_markdown_mirror_without_an_index_entry_fails(tmp_path: Path, runner) -> None:
    _write_bundle(tmp_path, _valid_index(), mirrors=("model-a", "model-z"))

    result = runner(SCRIPT, tmp_path)

    assert result.returncode == 1
    assert "has no matching entry in the index's models map" in result.stdout


# ---------------------------------------------------------------------------
# Deliberate non-checks: coverage and freshness are NOT this gate's business
# ---------------------------------------------------------------------------


def test_rostered_but_unprofiled_model_is_not_an_error(tmp_path: Path, runner) -> None:
    """An UNVERIFIED model is a known-gaps item, never a build failure."""
    _write_bundle(tmp_path, _valid_index(roster=["model-a", "model-b", "model-c"]))

    result = runner(SCRIPT, tmp_path)

    assert result.returncode == 0, result.stdout
    assert "model-b" in result.stdout and "model-c" in result.stdout


def test_a_very_old_last_verified_date_is_not_an_error(tmp_path: Path, runner) -> None:
    """Freshness belongs to check_model_prompting_freshness.py, advisory-only."""
    index = _valid_index()
    index["meta"]["last_verified"] = "2020-01-01"
    index["models"]["model-a"]["last_verified"] = "2020-01-01"
    _write_bundle(tmp_path, index)

    result = runner(SCRIPT, tmp_path)

    assert result.returncode == 0, result.stdout


def test_quiet_suppresses_success_output(tmp_path: Path, runner) -> None:
    _write_bundle(tmp_path, _valid_index())

    result = runner(SCRIPT, tmp_path, ["--quiet"])

    assert result.returncode == 0
    assert result.stdout.strip() == ""


# ---------------------------------------------------------------------------
# Wrong-JSON-shape guards: what a hand-edit of the index can actually produce
# ---------------------------------------------------------------------------


def test_explicit_bundle_override_pointing_nowhere_fails(tmp_path: Path, runner) -> None:
    _write_bundle(tmp_path, _valid_index())

    result = runner(SCRIPT, tmp_path, ["--bundle", str(tmp_path / "no-such-dir")])

    assert result.returncode == 1
    assert "MISSING bundle" in result.stdout


def test_top_level_is_not_an_object_fails(tmp_path: Path, runner) -> None:
    _write_bundle(tmp_path, "[1, 2, 3]")

    result = runner(SCRIPT, tmp_path)

    assert result.returncode == 1
    assert "must contain a JSON object at the top level" in result.stdout


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        pytest.param(
            lambda index: index.update({"meta": "2026-07-27"}),
            "meta must be an object",
            id="meta_is_a_string",
        ),
        pytest.param(
            lambda index: index.update({"models": ["model-a"]}),
            "models must be an object",
            id="models_is_a_list",
        ),
        pytest.param(
            lambda index: index.update({"models": {"model-a": "claims go here"}}),
            "models['model-a'] must be an object",
            id="model_entry_is_a_string",
        ),
        pytest.param(
            lambda index: index["models"]["model-a"].update({"claims": "one claim"}),
            "claims must be a non-empty array",
            id="claims_is_a_string",
        ),
        pytest.param(
            lambda index: index["models"]["model-a"].update({"claims": ["just a string"]}),
            "claims[0] must be an object",
            id="claim_is_a_string",
        ),
    ],
)
def test_wrong_json_shape_fails(
    tmp_path: Path, runner, mutation: Callable[[dict], None], expected: str
) -> None:
    index = _valid_index()
    mutation(index)
    _write_bundle(tmp_path, index)

    result = runner(SCRIPT, tmp_path)

    assert result.returncode == 1, f"expected failure, got:\n{result.stdout}"
    assert expected in result.stdout, result.stdout


def test_absent_profiles_directory_fails_when_a_model_is_indexed(
    tmp_path: Path, runner
) -> None:
    """No references/models/ at all, but the index claims a profiled model."""
    bundle = tmp_path / CATALOG_BUNDLE_REL
    (bundle / "assets").mkdir(parents=True)
    (bundle / "assets" / "profiles-index.json").write_text(
        json.dumps(_valid_index(), indent=2), encoding="utf-8"
    )

    result = runner(SCRIPT, tmp_path)

    assert result.returncode == 1
    assert "missing profiles directory" in result.stdout
