"""Verification and audit must not penalize an intentional exclusion (v3.16.1 Phase 7.4).

Selective installation creates a new way for a health check to be wrong: a
focused install is *supposed* to be missing most of the catalog, so any check
that measures completeness against the full catalog will report every focused
install as broken. Train users to see that, and they stop reading the output.

Investigating this phase found that both checks are already safe **by
construction**, for a reason worth pinning down rather than rediscovering:

* `runner.py verify` asserts each documented read path is POPULATED, not that it
  holds the whole catalog.
* `harness_audit.py` scores its coverage axis as `recorded_surfaces / declared`,
  counting SURFACES (skills / commands / hooks / rules), not skills.

So this module does not test a change - it pins the property, because the
tempting future "fix" in both places is to compare against the catalog, and that
edit would look like an improvement while breaking every focused install.

The second half is the other side of the same coin: neither check may become so
permissive that it stops noticing genuinely missing policy infrastructure.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_RUNNER = _ROOT / "scripts" / "lib" / "integrations" / "runner.py"
_AUDIT = _ROOT / "scripts" / "harness_audit.py"

from scripts.lib.installer.selection import (  # noqa: E402
    SelectionRequest,
    available_from_catalog,
    load_catalog,
    resolve,
)
from scripts.lib.integrations.manifest import InstallManifest  # noqa: E402


@pytest.fixture(scope="module")
def runner_src() -> str:
    return _RUNNER.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def audit_src() -> str:
    return _AUDIT.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# verify: population, not completeness
# --------------------------------------------------------------------------- #

def test_verify_reports_the_recorded_selection(runner_src: str) -> None:
    """A PASS on a focused install must be interpretable as such."""
    assert "focused install (" in runner_src, (
        "cmd_verify must report the recorded scope before its checks, or a PASS "
        "on a focused install reads as a PASS on a full one."
    )


def test_verify_does_not_compare_against_the_full_catalog(runner_src: str) -> None:
    """The check that would break every focused install must stay absent.

    `_verify_checks` asserts each read path is populated. If it ever started
    counting catalog skills, a focused install would report NEEDS-ACTION for
    doing exactly what the user asked.
    """
    start = runner_src.index("def _verify_checks")
    body = runner_src[start:start + 3000]
    for forbidden in ("catalog/skills", "skill_count", "len(available.skills)"):
        assert forbidden not in body, (
            f"_verify_checks references {forbidden!r}, which turns an advisory "
            "population check into a completeness check and reports every "
            "focused install as broken."
        )


def test_verify_stays_advisory(runner_src: str) -> None:
    start = runner_src.index("def cmd_verify")
    body = runner_src[start:start + 4000]
    assert "always exit 0" in body or "return 0" in body, (
        "verify is advisory and must never fail an install."
    )


# --------------------------------------------------------------------------- #
# harness_audit: surfaces, not skill counts
# --------------------------------------------------------------------------- #

def test_audit_coverage_counts_surfaces_not_skills(audit_src: str) -> None:
    assert "axis_coverage = recorded_surfaces / declared" in audit_src, (
        "The coverage axis must remain surfaces-present over surfaces-declared. "
        "Scoring it against catalog skill counts would drop every focused "
        "install's grade for an intentional exclusion."
    )


def test_audit_does_not_score_against_catalog_skill_count(audit_src: str) -> None:
    start = audit_src.index("def _audit_one")
    body = audit_src[start:audit_src.index("def ", start + 10)]
    assert "catalog/skills" not in body, (
        "_audit_one must not read the catalog; it scores what the manifest "
        "recorded, which is what makes it selection-agnostic."
    )


# --------------------------------------------------------------------------- #
# Still strict where it matters
# --------------------------------------------------------------------------- #

def test_policy_surfaces_are_present_under_every_selection() -> None:
    """An exclusion is intentional only for skills, commands, and agents.

    Rules, hooks, templates and settings are never filtered, so a check that
    tolerates a missing one would be tolerating a real defect.
    """
    catalog = load_catalog(_ROOT / "data" / "bundles.json")
    available = available_from_catalog(catalog, repo_root=_ROOT)
    for kwargs in ({"profiles": ["minimal"]}, {"modules": ["ai-engineering"]}, {}):
        plan = resolve(catalog, SelectionRequest.from_args(**kwargs), available)
        for required in ("hooks", "rules", "settings", "templates"):
            assert required in plan.always_present, (
                f"{required} missing from always_present for {kwargs}; a focused "
                "install must not be less safe than the default one."
            )


def test_a_manifest_without_selection_still_reads_as_full() -> None:
    """Verification of a pre-v3.16.1 install must not change behavior."""
    m = InstallManifest.from_dict({"tracked": {"claude": ["a.md"]}})
    assert m.selection() is None


def test_selection_manifest_round_trips_for_verification(tmp_path: Path) -> None:
    """verify and doctor read the plan back out of the manifest, so it must persist."""
    catalog = load_catalog(_ROOT / "data" / "bundles.json")
    available = available_from_catalog(catalog, repo_root=_ROOT)
    plan = resolve(catalog, SelectionRequest.from_args(modules=["ai-engineering"]), available)

    m = InstallManifest()
    m.set_selection(plan.to_dict())
    path = tmp_path / "install-manifest.json"
    m.save(path)

    reloaded = InstallManifest.load(path).selection()
    assert reloaded["hash"] == plan.hash()
    assert reloaded["requested"]["modules"] == ["ai-engineering"]
    assert len(reloaded["resolved"]["skills"]) == len(plan.skills)


# --------------------------------------------------------------------------- #
# The read contract itself
# --------------------------------------------------------------------------- #

def test_read_contract_json_is_intact() -> None:
    """Phase 7 must not have disturbed the machine-readable read contract."""
    data = json.loads((_ROOT / "docs" / "policy" / "platform-read-contracts.json").read_text(encoding="utf-8"))
    assert "contract_checks" in data and "install_verify" in data
    assert len(data["contract_checks"]) >= 10, (
        "the contract must still cover every verified platform"
    )


def test_selective_install_guide_documents_the_exit_codes() -> None:
    """The user-facing guide must match the contract's exit-code split."""
    guide = (_ROOT / "guides" / "reference" / "SELECTIVE_INSTALLATION.md").read_text(encoding="utf-8")
    assert "**2** means your selector was wrong" in guide or re.search(r"exit 2", guide), (
        "the guide must explain exit 2 (user fault)"
    )
    assert re.search(r"exit 3|\*\*3\*\*", guide), "the guide must explain exit 3 (catalog fault)"
    for surface in ("hooks", "rules", "templates"):
        assert surface in guide, f"the guide must state that {surface} always install"
