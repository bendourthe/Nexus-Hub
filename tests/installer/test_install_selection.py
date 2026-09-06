"""Resolver and manifest tests for the install-selection contract (v3.16.1 Phase 5.5).

The point of this module is to freeze the architecture BEFORE Phase 6 mutates two
3000-line installers. Every behavior asserted here is something a Bash or
PowerShell implementation will have to reproduce, and the shared fixture matrix in
`tests/fixtures/install-selection/cases.json` is the artifact all three
implementations are checked against. Phase 6.5 extends this module to run the
same cases through the other two paths; the case ids are the join key.

Two assertions carry more weight than the rest:

`test_resolution_never_writes` is the fail-before-write rule made mechanical. The
contract promises that an invalid selector cannot leave a half-installed tree,
and the way that promise is kept is that resolution is a pure function. This test
runs every failing case with the working directory inside an otherwise-empty
temp dir and asserts nothing appeared.

`test_hash_equality_pairs` is the cross-implementation join. The hash covers the
resolved outcome rather than the request, so two different ways of asking for the
same install must agree. If that ever stops holding, Phase 6's parity check
degrades into comparing each implementation against itself.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_FIXTURES = _ROOT / "tests" / "fixtures" / "install-selection"

import sys

if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.lib.installer.selection import (  # noqa: E402
    ALWAYS_PRESENT,
    EXIT_CATALOG_ERROR,
    EXIT_USER_ERROR,
    Available,
    CatalogSelectionError,
    SelectionError,
    SelectionRequest,
    UserSelectionError,
    available_from_catalog,
    load_catalog,
    resolve,
)
from scripts.lib.integrations.manifest import InstallManifest  # noqa: E402


def _cases() -> list:
    data = json.loads((_FIXTURES / "cases.json").read_text(encoding="utf-8"))
    return data["cases"]


ALL_CASES = _cases()
RESOLVER_CASES = [c for c in ALL_CASES if c["scope"] == "resolver"]
INSTALL_CASES = [c for c in ALL_CASES if c["scope"] == "install"]


def _request(case: dict) -> SelectionRequest:
    """Build a request from a fixture case's `input` block.

    `modules_raw` and `profiles` exist so a case can exercise the parser's own
    failure modes (stray comma, two profiles) rather than only post-parse errors.
    """
    inp = case["input"]
    profiles = inp.get("profiles")
    if profiles is None:
        profiles = [inp["profile"]] if inp.get("profile") else []
    modules = inp.get("modules")
    if "modules_raw" in inp:
        modules = [inp["modules_raw"]]
    return SelectionRequest.from_args(
        profiles=profiles, modules=modules or [], bundles=inp.get("bundles") or []
    )


def _run(case: dict):
    catalog = load_catalog(_FIXTURES / case["catalog"])
    available = available_from_catalog(catalog)
    return resolve(catalog, _request(case), available)


def _plans_by_id() -> dict:
    """Resolve every succeeding resolver case once, keyed by id, for hash pairing."""
    out = {}
    for case in RESOLVER_CASES:
        if case["expect"]["exit_code"] != 0:
            continue
        out[case["id"]] = _run(case)
    return out


# --------------------------------------------------------------------------- #
# The fixture matrix
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("case", RESOLVER_CASES, ids=lambda c: c["id"])
def test_case_exit_code(case: dict) -> None:
    expected = case["expect"]["exit_code"]
    if expected == 0:
        _run(case)  # must not raise
        return
    with pytest.raises(SelectionError) as excinfo:
        _run(case)
    assert excinfo.value.exit_code == expected, (
        f"{case['id']}: expected exit {expected}, got {excinfo.value.exit_code}. "
        f"Why this case exists: {case['why']}"
    )


@pytest.mark.parametrize(
    "case",
    [c for c in RESOLVER_CASES if c["expect"]["exit_code"] != 0],
    ids=lambda c: c["id"],
)
def test_failure_messages_name_the_problem(case: dict) -> None:
    with pytest.raises(SelectionError) as excinfo:
        _run(case)
    message = str(excinfo.value).lower()
    for token in case["expect"].get("error_contains", []):
        assert token.lower() in message, (
            f"{case['id']}: the error message must name {token!r} so the user can "
            f"act on it. Got: {excinfo.value}"
        )


@pytest.mark.parametrize(
    "case",
    [c for c in RESOLVER_CASES if c["expect"].get("skills") is not None],
    ids=lambda c: c["id"],
)
def test_case_resolves_expected_skills(case: dict) -> None:
    if case["expect"]["exit_code"] != 0:
        pytest.skip("failure case")
    plan = _run(case)
    assert plan.skills == case["expect"]["skills"], (
        f"{case['id']}: resolved skill set differs. Why this case exists: {case['why']}"
    )


@pytest.mark.parametrize(
    "case",
    [c for c in RESOLVER_CASES if c["expect"].get("commands") is not None],
    ids=lambda c: c["id"],
)
def test_case_resolves_expected_surfaces(case: dict) -> None:
    plan = _run(case)
    assert plan.commands == case["expect"]["commands"], f"{case['id']}: commands differ"
    if case["expect"].get("agents") is not None:
        assert plan.agents == case["expect"]["agents"], f"{case['id']}: agents differ"


@pytest.mark.parametrize(
    "case",
    [c for c in RESOLVER_CASES if c["expect"].get("reasons")],
    ids=lambda c: c["id"],
)
def test_case_records_dependency_reasons(case: dict) -> None:
    plan = _run(case)
    for skill, reason in case["expect"]["reasons"].items():
        assert plan.reasons.get(skill) == reason, (
            f"{case['id']}: {skill!r} should carry reason {reason!r}, got "
            f"{plan.reasons.get(skill)!r}. Reasons are how a user answers 'why is "
            "this skill installed'."
        )


@pytest.mark.parametrize(
    "case",
    [
        c
        for c in RESOLVER_CASES
        if c["expect"].get("excluded_commands") or c["expect"].get("excluded_agents")
    ],
    ids=lambda c: c["id"],
)
def test_case_records_exclusion_reasons(case: dict) -> None:
    plan = _run(case)
    for name, reason in case["expect"].get("excluded_commands", {}).items():
        assert plan.excluded_commands.get(name) == reason, (
            f"{case['id']}: command {name!r} should be excluded with {reason!r}, "
            f"got {plan.excluded_commands.get(name)!r}"
        )
    for name, reason in case["expect"].get("excluded_agents", {}).items():
        assert plan.excluded_agents.get(name) == reason, (
            f"{case['id']}: agent {name!r} should be excluded with {reason!r}, "
            f"got {plan.excluded_agents.get(name)!r}"
        )


@pytest.mark.parametrize(
    "case",
    [c for c in RESOLVER_CASES if c["expect"].get("warnings") is not None],
    ids=lambda c: c["id"],
)
def test_case_warnings(case: dict) -> None:
    plan = _run(case)
    assert plan.warnings == case["expect"]["warnings"], (
        f"{case['id']}: warnings differ. Why this case exists: {case['why']}"
    )


def test_hash_equality_pairs() -> None:
    """Cases declaring `same_hash_as` must hash identically.

    This is the cross-implementation join key. If it degrades, Phase 6's parity
    check compares each implementation only against itself.
    """
    plans = _plans_by_id()
    checked = 0
    for case in RESOLVER_CASES:
        peer = case["expect"].get("same_hash_as")
        if not peer or case["expect"]["exit_code"] != 0:
            continue
        checked += 1
        assert plans[case["id"]].hash() == plans[peer].hash(), (
            f"{case['id']} and {peer} resolve to the same install but hash "
            f"differently.\n  {case['id']}: {plans[case['id']].canonical()}\n"
            f"  {peer}: {plans[peer].canonical()}"
        )
    assert checked >= 4, f"Expected several hash-equality pairs, found {checked}"


def test_install_scope_cases_are_declared_for_phase6() -> None:
    """Phase 6 owns these; Phase 5 asserts only that they exist and are shaped.

    Declaring them now is what stops Phase 6 from inventing its own expectations
    after the implementation is already written.
    """
    assert INSTALL_CASES, "The fixture matrix must declare install-scope cases."
    for case in INSTALL_CASES:
        assert case.get("why"), f"{case['id']} must state why it exists"
        assert "expect" in case and "exit_code" in case["expect"]


# --------------------------------------------------------------------------- #
# Contract properties beyond the case table
# --------------------------------------------------------------------------- #


def test_resolution_never_writes(tmp_path: Path) -> None:
    """Fail-before-write, made mechanical.

    Resolution is pure, so a failing selector physically cannot have written
    anything. Running from an empty cwd and asserting it stays empty is the
    strongest cheap check available.
    """
    before = os.getcwd()
    os.chdir(tmp_path)
    try:
        for case in RESOLVER_CASES:
            try:
                _run(case)
            except SelectionError:
                pass
        assert list(tmp_path.iterdir()) == [], (
            f"Resolution created files: {[p.name for p in tmp_path.iterdir()]}. "
            "The resolver must be pure so an invalid selector cannot leave a "
            "half-installed tree."
        )
    finally:
        os.chdir(before)


def test_selector_forms_are_equivalent() -> None:
    """`--modules a,b` and `--modules a --modules b` must be indistinguishable."""
    catalog = load_catalog(_FIXTURES / "catalog-valid.json")
    available = available_from_catalog(catalog)
    csv = resolve(
        catalog, SelectionRequest.from_args(modules=["mod-ai,mod-web"]), available
    )
    repeated = resolve(
        catalog, SelectionRequest.from_args(modules=["mod-ai", "mod-web"]), available
    )
    assert csv.hash() == repeated.hash()
    assert csv.skills == repeated.skills


def test_whitespace_around_elements_is_stripped() -> None:
    catalog = load_catalog(_FIXTURES / "catalog-valid.json")
    available = available_from_catalog(catalog)
    padded = resolve(
        catalog, SelectionRequest.from_args(modules=[" mod-ai , mod-web "]), available
    )
    clean = resolve(
        catalog, SelectionRequest.from_args(modules=["mod-ai,mod-web"]), available
    )
    assert padded.hash() == clean.hash()


def test_every_plan_is_sorted() -> None:
    """Sorting is what makes the plan hashable and diffable across languages."""
    for case in RESOLVER_CASES:
        if case["expect"]["exit_code"] != 0:
            continue
        plan = _run(case)
        for label, seq in (
            ("skills", plan.skills),
            ("commands", plan.commands),
            ("agents", plan.agents),
            ("always_present", plan.always_present),
        ):
            assert seq == sorted(seq), f"{case['id']}: {label} is not sorted: {seq}"


def test_always_present_surfaces_appear_in_every_plan() -> None:
    """A narrower capability set must never mean weaker guardrails."""
    for case in RESOLVER_CASES:
        if case["expect"]["exit_code"] != 0:
            continue
        plan = _run(case)
        assert set(ALWAYS_PRESENT) <= set(plan.always_present), (
            f"{case['id']} dropped a policy surface. Filtering hooks or rules out "
            "of a focused install would make it less safe than the default."
        )
        for required in ("hooks", "rules", "settings", "templates"):
            assert required in plan.always_present


def test_every_resolved_skill_has_a_reason() -> None:
    for case in RESOLVER_CASES:
        if case["expect"]["exit_code"] != 0:
            continue
        plan = _run(case)
        missing = [s for s in plan.skills if s not in plan.reasons]
        assert not missing, f"{case['id']}: skills with no recorded reason: {missing}"


def test_undeclared_surfaces_always_install() -> None:
    """The deliberate default: no declaration means always installed.

    Excluding undeclared surfaces would silently shrink every install the moment
    selection shipped, before a single declaration existed.
    """
    catalog = load_catalog(_FIXTURES / "catalog-valid.json")
    available = available_from_catalog(catalog)
    plan = resolve(catalog, SelectionRequest.from_args(profiles=["minimal"]), available)
    assert "cmd-free" in plan.commands, "An undeclared command must install."
    assert "agent-free" in plan.agents, "An undeclared agent must install."


def test_related_skills_links_are_not_dependencies() -> None:
    """Only `skill_dependencies` edges expand a selection.

    If wiki-links were traversed, almost any selection would expand to the whole
    catalog and selective installation would be pointless.
    """
    catalog = load_catalog(_FIXTURES / "catalog-valid.json")
    available = available_from_catalog(catalog)
    plan = resolve(
        catalog, SelectionRequest.from_args(bundles=["role-alpha"]), available
    )
    assert plan.skills == ["a1", "c1"], (
        "role-alpha declares exactly a1 and c1 and no dependency edges, so "
        f"nothing else may enter the plan. Got {plan.skills}."
    )


def test_unreachable_catalog_defect_does_not_block_an_unrelated_install() -> None:
    """Traversal-scoped validation, asserted directly.

    catalog-cycle.json contains a real cycle. Selecting a module that does not
    reach it must still succeed, or one bad row in data/bundles.json becomes
    everyone's problem.
    """
    catalog = load_catalog(_FIXTURES / "catalog-cycle.json")
    available = available_from_catalog(catalog)
    plan = resolve(catalog, SelectionRequest.from_args(modules=["mod-safe"]), available)
    assert plan.skills == ["safe"]

    with pytest.raises(CatalogSelectionError):
        resolve(catalog, SelectionRequest.from_args(modules=["mod-cycle"]), available)


def test_error_types_map_to_exit_codes() -> None:
    assert UserSelectionError("x").exit_code == EXIT_USER_ERROR == 2
    assert CatalogSelectionError("x").exit_code == EXIT_CATALOG_ERROR == 3


def test_resolver_works_against_the_real_catalog() -> None:
    """The fixtures are synthetic; this proves the resolver runs on real data.

    A resolver that only ever sees its own fixtures can encode an assumption the
    real catalog violates. This is a smoke test, not a behavioral assertion, so
    it stays valid as the catalog grows.
    """
    catalog = load_catalog(_ROOT / "data" / "bundles.json")
    available = available_from_catalog(catalog, repo_root=_ROOT)
    assert len(available.skills) > 200, "Expected the real catalog to be present."

    full = resolve(catalog, SelectionRequest.from_args(), available)
    assert len(full.skills) == len(available.skills)
    assert full.warnings == []

    focused = resolve(
        catalog, SelectionRequest.from_args(modules=["ai-engineering"]), available
    )
    assert "eval-pipeline-audit" in focused.skills, (
        "Phase 2 added eval-pipeline-audit to the ai-engineering module, so a "
        "focused AI install must resolve it."
    )
    assert len(focused.skills) < len(full.skills), "A module must narrow the install."


def test_every_real_bundle_resolves() -> None:
    """Every profile, module, and bundle in the real catalog must resolve.

    This is the resolver-side equivalent of the Phase 2 repair (NI-1): the four
    broken references found then would each fail here with exit 3.
    """
    catalog = load_catalog(_ROOT / "data" / "bundles.json")
    available = available_from_catalog(catalog, repo_root=_ROOT)
    failures = []
    for kind, key in (
        ("profile", "profiles"),
        ("module", "modules"),
        ("bundle", "bundles"),
    ):
        for entry in catalog.get(key, []):
            if entry["id"] == "full":
                continue
            kwargs = {f"{kind}s": [entry["id"]]}
            try:
                resolve(catalog, SelectionRequest.from_args(**kwargs), available)
            except SelectionError as exc:
                failures.append(f"{kind} {entry['id']}: {exc}")
    assert not failures, "Selections that do not resolve:\n" + "\n".join(failures)


# --------------------------------------------------------------------------- #
# Manifest compatibility
# --------------------------------------------------------------------------- #


def test_manifest_without_selection_loads_as_full() -> None:
    """A pre-v3.16.1 manifest must load cleanly and mean 'full'."""
    legacy = {"tracked": {"claude": ["a.md"]}, "shared": {}, "logs": [], "actions": {}}
    m = InstallManifest.from_dict(legacy)
    assert m.selection() is None, (
        "An absent selection key must read as None, which callers interpret as a "
        "full install - which is what that manifest recorded."
    )
    assert m.selection_hash() is None
    assert m.files_for("claude") == ["a.md"]


def test_full_install_manifest_is_byte_identical_to_pre_v3161() -> None:
    """A full install must not start writing a new manifest key.

    The contract's byte-equivalence requirement covers the installed tree; making
    the manifest identical too means an existing diff-based check does not begin
    reporting a change on every full install.
    """
    m = InstallManifest()
    m.track("claude", "a.md")
    assert "selection" not in m.to_dict()


def test_manifest_round_trips_a_selection(tmp_path: Path) -> None:
    catalog = load_catalog(_FIXTURES / "catalog-valid.json")
    available = available_from_catalog(catalog)
    plan = resolve(catalog, SelectionRequest.from_args(modules=["mod-ai"]), available)

    m = InstallManifest()
    m.track("claude", "a.md")
    m.set_selection(plan.to_dict())

    path = tmp_path / "install-manifest.json"
    m.save(path)
    reloaded = InstallManifest.load(path)

    assert reloaded.selection_hash() == plan.hash()
    assert reloaded.selection()["resolved"]["skills"] == ["a1", "a2", "a3"]
    assert reloaded.files_for("claude") == ["a.md"]


def test_manifest_selection_is_a_copy_not_a_reference() -> None:
    """Mutating the caller's dict must not silently rewrite recorded history."""
    m = InstallManifest()
    payload = {"hash": "sha256:abc", "resolved": {"skills": ["a1"]}}
    m.set_selection(payload)
    payload["hash"] = "sha256:tampered"
    assert m.selection_hash() == "sha256:abc"


def test_install_context_defaults_to_no_selection() -> None:
    """Additive field: every existing caller keeps full-install behavior."""
    from scripts.lib.integrations.base import InstallContext

    ctx = InstallContext(repo_root=_ROOT, target_root=_ROOT)
    assert ctx.selection is None, (
        "InstallContext.selection must default to None (no filtering), so a "
        "pre-v3.16.1 caller that constructs a context without it keeps its exact "
        "current behavior."
    )


_SECURITY_AUDIT_OWNERS = (
    "security-review",
    "dependency-security-audit",
    "cve-reachability-analyzer",
    "cloud-security-posture-detection",
    "security-patch-advisor",
    "testing-review",
    "adversarial-verifier",
    "agent-presets",
)


def test_security_specialist_closes_security_audit_owners() -> None:
    """A focused security install must include every security-audit capability owner."""
    catalog = load_catalog(_ROOT / "data" / "bundles.json")
    available = available_from_catalog(catalog, repo_root=_ROOT)
    plan = resolve(
        catalog,
        SelectionRequest.from_args(bundles=["security-specialist"]),
        available,
    )
    missing = [name for name in _SECURITY_AUDIT_OWNERS if name not in plan.skills]
    assert not missing, f"security-specialist is missing audit owners: {missing}"


def test_security_audit_workflow_manifest_is_catalog_data() -> None:
    """workflows.json stays with the other always-parsed catalog indexes.

    Recursive skill copy does not carry data/ files. The installer already copies
    catalog indexes as a shared surface; this test freezes that the security-audit
    object remains in the source catalog rather than adding a new copy line.
    """
    workflows = json.loads(
        (_ROOT / "data" / "workflows.json").read_text(encoding="utf-8")
    )
    matches = [
        item for item in workflows["workflows"] if item["id"] == "security-audit"
    ]
    assert len(matches) == 1
    assert "indexes" in ALWAYS_PRESENT
