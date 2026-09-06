"""Tests for the edit-routing classifier and guard-gated apply engine (v3.15.5 Phase 3).

This is the phase that can autonomously write to the shipping catalog, so the
tests are weighted toward what must NOT happen: a model-specific finding reaching
a shared body, an edit surviving a failed guard, a write landing on a protected
branch, or one edit's revert destroying another's surviving change.

It also pins a correction. The plan asserted that
`scripts/check_base_template_parity.py` makes the hard rail physical ("a
model-named line in a shared base-*.md fails the build"). That is false, and
`test_parity_guard_does_not_catch_a_model_named_line_in_lockstep` documents the
reality: the guard compares the five templates to EACH OTHER, so the same
model-named line applied to all five passes it. The rail is therefore enforced by
the engine, which the paired test proves.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_BUNDLE = _ROOT / "catalog" / "skills" / "ai-development" / "model-prompting-research"
_ENGINE_PATH = _BUNDLE / "scripts" / "apply_prompting_edits.py"
_PARITY = _ROOT / "scripts" / "check_base_template_parity.py"
_TEMPLATES = _ROOT / "templates" / "ai-instructions"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


engine = _load("mpr_engine", _ENGINE_PATH)
# The authoritative list of the five lockstep templates. Imported rather than
# hardcoded so this test follows the guard if the set ever changes; note that
# templates/ai-instructions also holds NON-lockstep base-*.md files (for example
# base-google-shared.md), which the guard ignores.
parity = _load("mpr_parity", _PARITY)


def _proposal(**over) -> dict:
    base = {
        "id": "p1",
        "model": "model-a",
        "scope": "model-agnostic-candidate",
        "target": "catalog/commands/demo.md",
        "target_kind": "command-body",
        "old": "Run the thing.",
        "new": "Run the thing, then state what changed.",
        "source_url": "https://vendor.example/docs",
    }
    base.update(over)
    return base


# ---------------------------------------------------------------------------
# 3.1 Classifier: the routing table
# ---------------------------------------------------------------------------


def test_model_agnostic_with_an_allowed_target_is_eligible() -> None:
    assert engine.classify(_proposal())["route"] == engine.ELIGIBLE


@pytest.mark.parametrize(
    "scope",
    [
        pytest.param("model-specific", id="declared_model_specific"),
        pytest.param(None, id="missing"),
        pytest.param("", id="empty"),
        pytest.param("maybe-general", id="unrecognized"),
        pytest.param("MODEL-AGNOSTIC-CANDIDATE", id="wrong_case"),
    ],
)
def test_anything_but_the_exact_agnostic_tag_routes_to_the_profile_layer(scope) -> None:
    """Ambiguity must resolve to model-specific, never the other way."""
    decision = engine.classify(_proposal(scope=scope))

    assert decision["route"] == engine.PROFILE_ONLY


@pytest.mark.parametrize(
    "kind",
    ["readme", "installer", "data-registry", "hook", "", None],
)
def test_a_target_outside_the_allowed_surfaces_is_rejected(kind) -> None:
    decision = engine.classify(_proposal(target_kind=kind))

    assert decision["route"] == engine.REJECTED
    assert "allowed shared-body surfaces" in decision["reason"]


@pytest.mark.parametrize("kind", sorted(engine.ALLOWED_TARGET_KINDS))
def test_every_allowed_target_kind_is_eligible(kind: str) -> None:
    assert engine.classify(_proposal(target_kind=kind))["route"] == engine.ELIGIBLE


@pytest.mark.parametrize(
    ("field", "value", "fragment"),
    [
        pytest.param("target", "", "no target file path", id="no_target"),
        pytest.param("old", "", "no 'old' anchor", id="no_anchor"),
    ],
)
def test_structurally_incomplete_proposals_are_rejected(field, value, fragment) -> None:
    decision = engine.classify(_proposal(**{field: value}))

    assert decision["route"] == engine.REJECTED
    assert fragment in decision["reason"]


def test_a_no_op_edit_is_rejected() -> None:
    decision = engine.classify(_proposal(new="Run the thing."))

    assert decision["route"] == engine.REJECTED
    assert "no-op" in decision["reason"]


# ---------------------------------------------------------------------------
# 3.1 The hard rail: an edit may not INTRODUCE a model identifier
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "On claude-opus-5, prefer terse prompts.",
        "GPT-5.5 wants explicit numbering.",
        "Use Sonnet 5 for this tier.",
        "gemini-3 handles long context.",
        "Opus prefers step numbering.",
        "Route to haiku for cheap work.",
        "o3 needs a different framing.",
        "deepseek-v3 differs here.",
    ],
)
def test_an_edit_introducing_a_model_identifier_is_blocked(text: str) -> None:
    """The rail fires regardless of the declared scope."""
    decision = engine.classify(_proposal(new=text))

    assert decision["route"] == engine.PROFILE_ONLY
    assert "HARD RAIL" in decision["reason"]
    assert decision["introduced_models"]


def test_rewording_a_line_that_already_names_a_model_is_allowed() -> None:
    """The rail forbids INTRODUCING a name, not touching a line that has one."""
    decision = engine.classify(
        _proposal(
            old="Route hard tasks to claude-opus-5 always.",
            new="Route hard tasks to claude-opus-5 by default.",
        )
    )

    assert decision["route"] == engine.ELIGIBLE


def test_removing_a_model_name_is_allowed() -> None:
    decision = engine.classify(
        _proposal(old="Route hard tasks to claude-opus-5.", new="Route hard tasks to the strongest tier.")
    )

    assert decision["route"] == engine.ELIGIBLE


def test_introduced_mentions_are_computed_against_the_old_text() -> None:
    introduced = engine.introduced_model_mentions(
        "claude-opus-5 is fine", "claude-opus-5 and gpt-5.5 are fine"
    )

    assert any("gpt-5.5" in m for m in introduced)
    assert not any("claude-opus-5" == m for m in introduced)


def test_prose_without_a_model_name_is_not_flagged() -> None:
    assert engine.model_mentions("Be explicit about the desired output shape.") == []


# ---------------------------------------------------------------------------
# The corrected hard-rail proof
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _TEMPLATES.is_dir(), reason="lockstep templates absent")
def test_parity_guard_does_not_catch_a_model_named_line_in_lockstep(tmp_path: Path) -> None:
    """DOCUMENTS REALITY, and is why the rail lives in the engine.

    The plan claimed the parity guard makes a model-named line in a shared
    base-*.md fail the build. It does not: the guard compares the five templates
    to each other, so the SAME model-named line applied to all five is perfect
    lockstep and passes. If this test ever starts failing, the parity guard has
    gained content-level checks and this comment (and the engine rail's
    justification) should be revisited.
    """
    dst = tmp_path / "templates" / "ai-instructions"
    dst.mkdir(parents=True)
    for name in parity.LOCKSTEP_FILES:
        src = _TEMPLATES / name
        if not src.is_file():
            pytest.skip(f"lockstep template {name} absent")
        text = src.read_text(encoding="utf-8")
        assert "## Branching\n" in text, f"fixture precondition: no Branching heading in {name}"
        dst.joinpath(name).write_text(
            text.replace("## Branching\n", "## Branching\n\n- On claude-opus-5, be terse.\n", 1),
            encoding="utf-8",
        )

    result = subprocess.run(
        [sys.executable, str(_PARITY), "--root", str(tmp_path)],
        capture_output=True, text=True, check=False,
    )

    assert result.returncode == 0, "parity guard unexpectedly caught it; revisit the engine rail"


def test_the_engine_blocks_the_edit_the_parity_guard_misses() -> None:
    """The paired half: what the parity guard lets through, the engine stops."""
    decision = engine.classify(
        _proposal(
            target="templates/ai-instructions/base-claude.md",
            target_kind="base-template-line",
            old="## Branching\n",
            new="## Branching\n\n- On claude-opus-5, be terse.\n",
        )
    )

    assert decision["route"] == engine.PROFILE_ONLY
    assert "claude-opus-5" in " ".join(decision["introduced_models"])


# ---------------------------------------------------------------------------
# 3.2 The apply loop, on a real temporary git repo
# ---------------------------------------------------------------------------


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True, check=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A throwaway git repo with a `develop` branch and one editable file."""
    if shutil.which("git") is None:  # pragma: no cover
        pytest.skip("git not available")
    root = tmp_path / "repo"
    (root / "catalog" / "commands").mkdir(parents=True)
    _git(root.parent, "init", "-q", str(root))
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "Test")
    # The trailing duplicate pair gives the ambiguous-anchor test a genuinely
    # repeated string while keeping the other anchors unique.
    (root / "catalog" / "commands" / "demo.md").write_text(
        "Run the thing.\n\nSecond line.\n\nRepeated token here.\nRepeated token here.\n",
        encoding="utf-8",
    )
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "seed")
    _git(root, "branch", "-M", "develop")
    return root


PASS_GUARD = ("ok", (sys.executable, "-c", "raise SystemExit(0)"))
FAIL_GUARD = ("always-fails", (sys.executable, "-c", "import sys; print('nope'); raise SystemExit(1)"))


def test_a_guard_passing_edit_is_applied(repo: Path) -> None:
    decisions = engine.classify_all([_proposal()])

    result = engine.apply_loop(repo, [_proposal()], decisions, (PASS_GUARD,))

    assert len(result["applied"]) == 1
    assert result["quarantined"] == []
    assert "state what changed" in (repo / "catalog/commands/demo.md").read_text(encoding="utf-8")


def test_a_guard_failing_edit_is_auto_reverted_and_quarantined(repo: Path) -> None:
    before = (repo / "catalog/commands/demo.md").read_text(encoding="utf-8")
    decisions = engine.classify_all([_proposal()])

    result = engine.apply_loop(repo, [_proposal()], decisions, (FAIL_GUARD,))

    assert result["applied"] == []
    assert len(result["quarantined"]) == 1
    assert result["quarantined"][0]["failing_guard"] == "always-fails"
    assert (repo / "catalog/commands/demo.md").read_text(encoding="utf-8") == before


def test_one_edit_failing_does_not_abort_the_run(repo: Path) -> None:
    """A quarantine is per-edit; later proposals must still be attempted."""
    good = _proposal(id="good", old="Second line.", new="Second line, clarified.")
    bad = _proposal(id="bad", target_kind="readme")  # rejected, not applied
    proposals = [bad, good]
    decisions = engine.classify_all(proposals)

    result = engine.apply_loop(repo, proposals, decisions, (PASS_GUARD,))

    assert [d["id"] for d in result["applied"]] == ["good"]


def test_a_failing_second_edit_does_not_destroy_a_surviving_first_edit(repo: Path) -> None:
    """The snapshot-restore correction: `git checkout --` would revert BOTH."""
    target = "catalog/commands/demo.md"
    first = _proposal(id="first", target=target, old="Run the thing.", new="Run the thing carefully.")
    second = _proposal(id="second", target=target, old="Second line.", new="Second line changed.")
    proposals = [first, second]
    decisions = engine.classify_all(proposals)

    # A guard that fails only once the SECOND edit has landed.
    sentinel = (
        "guard-on-second",
        (sys.executable, "-c",
         "import sys,io; t=io.open(r'{}',encoding='utf-8').read();"
         " raise SystemExit(1 if 'Second line changed.' in t else 0)".format(
             (repo / target).as_posix())),
    )

    result = engine.apply_loop(repo, proposals, decisions, (sentinel,))

    text = (repo / target).read_text(encoding="utf-8")
    assert [d["id"] for d in result["applied"]] == ["first"]
    assert [d["id"] for d in result["quarantined"]] == ["second"]
    assert "Run the thing carefully." in text, "the surviving first edit must be preserved"
    assert "Second line changed." not in text, "the failing second edit must be reverted"


@pytest.mark.parametrize(
    ("old", "fragment"),
    [
        pytest.param("Not present anywhere.", "not found", id="missing_anchor"),
        pytest.param("Repeated token here.", "ambiguous", id="ambiguous_anchor"),
    ],
)
def test_an_unusable_anchor_is_quarantined_not_applied(repo: Path, old: str, fragment: str) -> None:
    proposal = _proposal(old=old, new="replacement")
    decisions = engine.classify_all([proposal])

    result = engine.apply_loop(repo, [proposal], decisions, (PASS_GUARD,))

    assert result["applied"] == []
    assert result["quarantined"][0]["failing_guard"] == "apply"
    assert fragment in result["quarantined"][0]["detail"]


# ---------------------------------------------------------------------------
# 3.2 Branch isolation
# ---------------------------------------------------------------------------


def test_the_engine_creates_and_lands_on_the_isolated_branch(repo: Path) -> None:
    branch = engine.ensure_working_branch(repo, "20260727-1200", "develop")

    assert branch == "feat/tune-prompting-20260727-1200"
    assert engine.current_branch(repo) == branch
    assert engine.current_branch(repo) not in engine.PROTECTED_BRANCHES


def test_checkout_is_idempotent_when_the_branch_already_exists(repo: Path) -> None:
    engine.ensure_working_branch(repo, "s1", "develop")
    _git(repo, "checkout", "-q", "develop")

    assert engine.ensure_working_branch(repo, "s1", "develop") == "feat/tune-prompting-s1"


def test_a_missing_stamp_is_refused(repo: Path) -> None:
    with pytest.raises(engine.ApplyError, match="stamp is required"):
        engine.ensure_working_branch(repo, "  ", "develop")


@pytest.mark.parametrize("protected", sorted(engine.PROTECTED_BRANCHES))
def test_protected_branch_names_are_known(protected: str) -> None:
    assert protected in engine.PROTECTED_BRANCHES


def test_end_to_end_apply_never_leaves_head_on_develop(repo: Path) -> None:
    payload = {"stamp": "e2e-1", "proposals": [_proposal()], "unverified_models": []}
    payload_path = repo / "proposals.json"
    payload_path.write_text(json.dumps(payload), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_ENGINE_PATH), "apply", "--input", str(payload_path),
         "--repo", str(repo), "--stamp", "e2e-1", "--base-branch", "develop",
         "--guard", "ok:{} -c pass".format(sys.executable)],
        capture_output=True, text=True, check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert engine.current_branch(repo) == "feat/tune-prompting-e2e-1"
    assert "STOP" in result.stdout, "the run must say the branch is for human merge"


def test_without_commit_the_edits_stay_uncommitted(repo: Path) -> None:
    payload_path = repo / "proposals.json"
    payload_path.write_text(json.dumps({"proposals": [_proposal()]}), encoding="utf-8")

    subprocess.run(
        [sys.executable, str(_ENGINE_PATH), "apply", "--input", str(payload_path),
         "--repo", str(repo), "--stamp", "nc-1",
         "--guard", "ok:{} -c pass".format(sys.executable)],
        capture_output=True, text=True, check=False,
    )

    status = subprocess.run(["git", "status", "--porcelain"], cwd=str(repo),
                            capture_output=True, text=True, check=True).stdout
    assert "catalog/commands/demo.md" in status, "edits should be present but uncommitted"


def test_with_commit_the_surviving_edits_are_committed(repo: Path) -> None:
    payload_path = repo / "proposals.json"
    payload_path.write_text(json.dumps({"proposals": [_proposal()]}), encoding="utf-8")

    subprocess.run(
        [sys.executable, str(_ENGINE_PATH), "apply", "--input", str(payload_path),
         "--repo", str(repo), "--stamp", "c-1", "--commit",
         "--guard", "ok:{} -c pass".format(sys.executable)],
        capture_output=True, text=True, check=False,
    )

    log = subprocess.run(["git", "log", "--oneline", "-1"], cwd=str(repo),
                         capture_output=True, text=True, check=True).stdout
    assert "tune-prompting" in log
    assert engine.current_branch(repo) == "feat/tune-prompting-c-1"
    develop_log = subprocess.run(["git", "log", "--oneline", "develop"], cwd=str(repo),
                                 capture_output=True, text=True, check=True).stdout
    assert "tune-prompting" not in develop_log, "develop must be untouched"


# ---------------------------------------------------------------------------
# The default guard suite
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "command"), [(n, c) for n, c in engine.DEFAULT_GUARDS]
)
def test_every_default_guard_points_at_a_script_that_exists(name: str, command) -> None:
    """A renamed or moved gate would quarantine every edit on a real run.

    The loop's control flow is tested with injected guards (fast, deterministic),
    so nothing else would catch a typo in the default command list until a live
    run mysteriously quarantined everything.
    """
    script = next((a for a in command if str(a).endswith(".py")), None)

    assert script is not None, f"guard {name!r} runs no .py script: {command}"
    assert (_ROOT / script).is_file(), f"guard {name!r} points at a missing script: {script}"


def test_the_default_suite_covers_the_gates_the_plan_requires() -> None:
    names = {n for n, _ in engine.DEFAULT_GUARDS}

    assert {"base-template-parity", "profile-schema", "version-sync"} <= names


# ---------------------------------------------------------------------------
# 3.3 Gap report
# ---------------------------------------------------------------------------


def _report(**over) -> str:
    args = {
        "stamp": "20260727-1200",
        "branch": "feat/tune-prompting-20260727-1200",
        "decisions": engine.classify_all([_proposal(), _proposal(id="p2", scope="model-specific")]),
        "result": {"applied": [{"id": "p1", "target": "catalog/commands/demo.md"}],
                   "quarantined": []},
        "proposals": [_proposal(), _proposal(id="p2", scope="model-specific")],
        "unverified_models": [],
        "diff_stat": " demo.md | 1 +\n",
    }
    args.update(over)
    return engine.build_report(**args)


def test_report_is_deterministic() -> None:
    assert _report() == _report()


@pytest.mark.parametrize(
    "heading",
    [
        "## Applied to shared bodies",
        "## Quarantined (auto-reverted, not applied)",
        "## Routed to the profile layer only",
        "## Rejected proposals",
        "## Branch diff summary",
        "## Known-gaps entries to record",
    ],
)
def test_report_carries_every_section(heading: str) -> None:
    assert heading in _report()


def test_report_emits_a_known_gap_per_quarantined_edit() -> None:
    text = _report(result={
        "applied": [],
        "quarantined": [{"id": "p1", "target": "catalog/commands/demo.md",
                         "failing_guard": "trigger-routing", "detail": "collision"}],
    })

    assert "QG-p1" in text
    assert "trigger-routing" in text


def test_report_emits_a_known_gap_per_unverified_model() -> None:
    text = _report(unverified_models=["model-b", "model-c"])

    assert "NI-model-b" in text and "NI-model-c" in text


def test_report_says_none_when_there_is_nothing_to_record() -> None:
    assert "every rostered model was verified" in _report()


def test_report_escapes_pipes_so_tables_survive() -> None:
    text = _report(
        proposals=[_proposal(source_url="https://x.example/a|b")],
        result={"applied": [{"id": "p1", "target": "t"}], "quarantined": []},
    )

    assert "a\\|b" in text


def test_report_puts_a_blank_line_before_every_table() -> None:
    """The markdown style guide's most common rendering bug."""
    lines = _report().splitlines()
    for i, line in enumerate(lines):
        if line.startswith("| ") and i and not lines[i - 1].startswith("|"):
            assert lines[i - 1].strip() == "", f"line {i}: table not preceded by a blank line"
