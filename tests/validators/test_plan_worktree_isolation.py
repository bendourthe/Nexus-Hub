"""Worktree isolation for plans (v4.12.1).

A plan runs in its own worktree rather than only its own branch. A branch alone
serializes work: a second plan cannot start without switching the single
checkout, and switching underneath a running session changes the files that
session is editing.

Three rules are guarded here, each owned by a different file:

* ``implement-phase`` creates worktrees and dispatches eligible minor workers.
* ``/update release`` verifies integration and reconciles executor cleanup,
  preserving active controllers and workers until final minor cleanup.
* The mechanics stay with ``using-git-worktrees`` and the ranking with
  ``plan-queue-assessment``; this module asserts the HANDOFF exists rather than
  re-checking those skills' own rules.

The teardown assertions matter most. Without them the cost of parallel plans is
permanent: ten shipped plans leave ten stale checkouts, each pinning objects and
each indistinguishable from the real repository at a glance.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import nexus_worktrees as nw

_ROOT = Path(__file__).resolve().parents[2]
_RUNBOOK = (
    _ROOT
    / "catalog"
    / "skills"
    / "workflow"
    / "implement-phase"
    / "references"
    / "implement-phase-runbook.md"
)
_SKILL = _ROOT / "catalog" / "skills" / "workflow" / "implement-phase" / "SKILL.md"
_IMPLEMENT_CMD = _ROOT / "catalog" / "commands" / "implement.md"
_UPDATE_CMD = _ROOT / "catalog" / "commands" / "update.md"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8").replace("\r\n", "\n")


# --- creation ---------------------------------------------------------------


def test_runbook_creates_a_worktree_not_only_a_branch() -> None:
    t = _read(_RUNBOOK)
    assert "Isolate the plan in its own worktree" in t
    assert "not merely a branch" in t


def test_runbook_delegates_worktree_mechanics() -> None:
    """Mechanics belong to using-git-worktrees; do not re-derive them."""
    t = _read(_RUNBOOK)
    assert "[[using-git-worktrees]]" in t
    assert "Do not re-derive that procedure here." in t


def test_runbook_names_the_worktree_predictably() -> None:
    """The release step finds the worktree by name, so naming is load-bearing."""
    t = _read(_RUNBOOK)
    assert (
        "A predictable directory is what lets the release step find and remove it later."
        in t
    )


def test_runbook_has_a_branch_fallback() -> None:
    t = _read(_RUNBOOK)
    assert "Worktrees unavailable" in t
    assert "fall back to a branch" in t


# --- parallel reporting -----------------------------------------------------


def _parallel_assessment() -> str:
    text = _read(_RUNBOOK)
    return text.split("### Phase 0c: Assess and dispatch parallel plans", 1)[1].split(
        "\n## Phase 1:", 1
    )[0]


def test_runbook_assesses_and_dispatches_parallel_plans() -> None:
    section = _parallel_assessment()
    assert "[[plan-queue-assessment]]" in section
    assert "single-plan invocation reports compatible queued plans" in section
    assert "without starting plans outside its approval" in section
    assert (
        "minor invocation automatically dispatches eligible approved members" in section
    )


def test_parallel_dispatch_records_actual_worker_identity() -> None:
    """A suggested launch is not evidence that an isolated worker exists."""
    section = _parallel_assessment()
    assert "launch suggestion alone is not dispatch evidence" in section
    assert "actual returned agent handle" in section
    assert "branch, linked worktree, base, signed claims and status" in section
    assert "NEW terminal window" not in section
    assert "/implement v4.17.0-<slug> in-full" not in section


def test_parallel_report_states_its_basis_and_never_omits_itself() -> None:
    section = _parallel_assessment()
    assert "overlap basis as named paths and prerequisites" in section
    assert "no eligible parallel plans" in section
    assert "named conflicts, missing prerequisites or unknowns" in section
    assert "never omit the assessment" in section


def test_missing_ranking_owner_is_declared_not_reconstructed() -> None:
    section = _parallel_assessment()
    assert "assessment owner is unavailable" in section
    assert "mark compatibility not covered and execute serially" in section
    assert "never reconstruct its ranking rules from memory" in section


# --- teardown ---------------------------------------------------------------

_TEARDOWN_CHECKS = [
    "fully merged",  # branch is integrated
    "no uncommitted or untracked work",  # tree is clean
    "git worktree prune",  # records are pruned
]


@pytest.mark.parametrize("needle", _TEARDOWN_CHECKS)
def test_runbook_teardown_covers_each_precondition(needle: str) -> None:
    t = _read(_RUNBOOK)
    section = t[t.index("Retire the worktree") :]
    assert needle in section, f"teardown omits: {needle}"


def test_teardown_is_gated_on_a_green_merge() -> None:
    """Removing a worktree before the merge lands deletes unfinished work."""
    t = _read(_RUNBOOK)
    assert "Never remove a worktree before the merge is green and merged" in t
    assert "never with `--force` to get past a dirty tree" in t


def test_teardown_is_quoted_as_evidence() -> None:
    t = _read(_RUNBOOK)
    assert "## Worktree teardown" in t


def test_release_command_owns_the_integration_and_teardown_gate() -> None:
    t = _read(_UPDATE_CMD)
    assert "Plan worktree integration and teardown" in t
    assert "fully merged" in t
    assert "stops the release rather than being force-removed" in t
    assert "silent no-op" in t


def test_release_gate_states_why_it_exists() -> None:
    """A gate whose cost is unstated is the first one dropped."""
    t = _read(_UPDATE_CMD)
    assert "ten shipped plans leave ten stale checkouts" in t


# --- surfaced in the always-read bodies -------------------------------------


def test_skill_body_states_all_three_guarantees() -> None:
    t = _read(_SKILL)
    assert "Worktree isolation and parallel plans" in t
    assert "not just its own branch" in t
    assert "reconciles worktree retirement after green merged integration" in t
    assert "active-controller and active-worker exception" in t
    assert "final minor completion still requires its cleanup evidence" in t
    assert "Never override KEEP or force-remove a dirty worktree" in t


def test_command_states_the_guarantee() -> None:
    t = _read(_IMPLEMENT_CMD)
    assert "Worktree isolation and parallel plans (guarantee)" in t
    assert "[[using-git-worktrees]]" in t
    assert "[[plan-queue-assessment]]" in t


def test_skill_verification_covers_the_three_rules() -> None:
    t = _read(_SKILL)
    assert "created through `[[using-git-worktrees]]`" in t
    assert (
        "actual worker handles, exclusive signed claims, worktree/base identity and status"
        in t
    )
    assert "eligible plans dispatched when capacity opened" in t
    assert (
        "retirement followed the completion contract after green merged integration"
        in t
    )
    assert "exact executor KEEP and permitted minor-controller/worker deferral" in t
    assert "final minor cleanup remains required" in t


@pytest.mark.parametrize(
    ("path", "needle"),
    [
        (_RUNBOOK, "Never remove a worktree before the merge is green and merged"),
        (_UPDATE_CMD, "ten shipped plans leave ten stale checkouts"),
        (_SKILL, "Worktree isolation and parallel plans"),
    ],
)
def test_claims_have_teeth(path: Path, needle: str) -> None:
    """Each predicate must fail when its target content is removed."""
    assert needle not in _read(path).replace(needle, "")


# --- worktree placement (v4.12.1) -------------------------------------------
#
# A real instance motivated this rule: a worktree at `.claude/worktrees/...`
# held 1,267 lines of uncommitted work. It was git-ignored, so the ignore gate
# passed and the tracked-path rule did not apply. When the repository moved,
# every worktree pointer broke and that work was unreachable through git until
# the pointers were repaired.

_WORKTREE_SKILL = (
    _ROOT / "catalog" / "skills" / "workflow" / "using-git-worktrees" / "SKILL.md"
)

_VENDOR_DIRS = [".claude/", ".cursor/", ".vscode/", ".idea/", ".codex/", ".gemini/"]


def test_worktree_skill_bars_vendor_directories() -> None:
    t = _read(_WORKTREE_SKILL)
    assert "Never place a worktree inside a vendor or tool directory" in t
    assert "even when that directory is git-ignored" in t


@pytest.mark.parametrize("vendor", _VENDOR_DIRS)
def test_each_vendor_directory_is_named(vendor: str) -> None:
    """A rule that names no directory is one nobody applies."""
    assert vendor in _read(_WORKTREE_SKILL), f"vendor dir not named: {vendor}"


def test_rule_explains_why_the_ignore_gate_is_insufficient() -> None:
    """Without this, a reader assumes check-ignore already covers it."""
    assert "the ignore gate alone does not catch this" in _read(_WORKTREE_SKILL)


def test_rule_carries_its_motivating_instance() -> None:
    assert "1,267 lines of uncommitted work" in _read(_WORKTREE_SKILL)


def test_verification_covers_placement() -> None:
    assert "NOT inside a vendor or tool directory" in _read(_WORKTREE_SKILL)


def test_placement_rule_has_teeth() -> None:
    needle = "Never place a worktree inside a vendor or tool directory"
    assert needle not in _read(_WORKTREE_SKILL).replace(needle, "")


# --- release publication sequence (v4.12.1) ---------------------------------
#
# v4.12.1 merged to main only. develop sat five commits behind until a branch
# cut from it turned up missing a test module that had just shipped. The order
# below is what prevents that, and the cleanup step is what stops worktrees
# accumulating one per release.

_UPDATE = _ROOT / "catalog" / "commands" / "update.md"


def test_release_lands_on_the_integration_branch_first() -> None:
    t = _read(_UPDATE)
    assert "Land the release on the integration branch FIRST" in t
    assert "before `main` sees it" in t


def test_the_straight_to_main_failure_is_named() -> None:
    """A rule whose failure mode is unstated is the first one skipped."""
    t = _read(_UPDATE)
    assert (
        "Merging the release straight to `main` is the failure this ordering prevents"
        in t
    )
    assert "v4.12.1 merged to `main` only" in t


def test_cleanup_happens_before_tagging() -> None:
    t = _read(_UPDATE)
    assert "Clear what the release consumed, BEFORE tagging" in t


@pytest.mark.parametrize(
    "needle",
    [
        "git branch --merged",  # merged-branch proof
        # v4.13.6: the release cleanup runs cleanup_merged.py, whose per-item
        # `dirty` and `untracked` checks are the clean-tree proof
        # (tests/validators/test_cleanup_merged.py WORKTREE_CASES); the step
        # itself must still refuse to override a KEEP or to force.
        "A `KEEP` line is never overridden by hand",  # a failed check is final
        "git worktree prune",  # records pruned
        "`-D`, `--force`, and `worktree remove --force` are never used",  # no forcing
    ],
)
def test_cleanup_step_is_fail_closed(needle: str) -> None:
    t = _read(_UPDATE)
    assert needle in t, f"cleanup step omits: {needle}"


def test_main_receives_the_cleaned_result_last() -> None:
    t = _read(_UPDATE)
    assert "Then merge to `main`, tag, push, publish" in t


def test_sequence_self_gates_for_simple_repositories() -> None:
    """A single-branch repo must not be blocked by a two-branch rule."""
    t = _read(_UPDATE)
    assert "Self-gates" in t
    assert "silent no-ops, not warnings" in t


def test_flow_summary_shows_the_order() -> None:
    """The one-line summary is what most readers see; it must not contradict."""
    t = _read(_UPDATE)
    assert (
        "merge to integration branch, retire merged branches + worktrees, merge to release branch"
        in t
    )


def test_publication_sequence_has_teeth() -> None:
    needle = "Land the release on the integration branch FIRST"
    assert needle not in _read(_UPDATE).replace(needle, "")


# --- centralized placement and creation parity (v4.15.6) ----------------------

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "scripts"


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout


@pytest.fixture
def world(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    home = tmp_path / "home"
    home.mkdir()
    cfg = tmp_path / "gitconfig"
    cfg.write_text(
        "[user]\n\tname = F\n\temail = f@example.invalid\n[init]\n\tdefaultBranch = main\n",
        encoding="utf-8",
    )
    env = {
        "HOME": str(home),
        "USERPROFILE": str(home),
        "NEXUS_HUB_HOME": str(home / ".nexus-hub"),
        "NEXUS_WORKTREE_STATE": str(tmp_path / "state"),
        "NEXUS_WORKTREE_ROOT": str(tmp_path / "central"),
        "GIT_CONFIG_GLOBAL": str(cfg),
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    repo = tmp_path / "ws" / "app"
    repo.mkdir(parents=True)
    git("init", "-q", cwd=repo)
    (repo / "a.txt").write_text("1\n", encoding="utf-8")
    git("add", ".", cwd=repo)
    git("commit", "-q", "-m", "init", cwd=repo)
    return {
        "repo": repo,
        "central": tmp_path / "central",
        "tmp": tmp_path,
        "home": home,
    }


def run(argv: list[str], **kw: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", timeout=180, **kw)  # type: ignore[arg-type]


def payload(proc: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(proc.stdout)


def entry_points(world: dict[str, Path]) -> dict[str, list[str]]:
    installed = world["home"] / ".nexus-hub" / "scripts"
    installed.mkdir(parents=True, exist_ok=True)
    for name in ("nexus_hub_cli.py", "nexus_worktrees.py", "nexus_process.py"):
        shutil.copy2(SCRIPTS / name, installed / name)
    return {
        "helper": [sys.executable, str(SCRIPTS / "nexus_worktrees.py")],
        "cli": [sys.executable, str(SCRIPTS / "nexus_hub_cli.py"), "worktree"],
        "installed": [sys.executable, str(installed / "nexus_hub_cli.py"), "worktree"],
    }


def test_create_places_the_worktree_at_the_canonical_destination(
    world: dict[str, Path]
) -> None:
    proc = run(
        [
            *entry_points(world)["cli"],
            "create",
            "--repo",
            str(world["repo"]),
            "--branch",
            "feat/x",
            "--base",
            "HEAD",
            "--name",
            "feat/x",
            "--json",
        ]
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    out = payload(proc)
    dest = Path(out["path"])
    assert (
        out["status"] == "created"
        and dest.parent.parent == world["central"]
        and (dest / "a.txt").is_file()
    )
    assert nw.key_of(dest) in {
        nw.key_of(w.path)
        for w in nw.list_registered(nw.GitInspector(), cwd=str(world["repo"]))
    }
    assert git("rev-parse", "--abbrev-ref", "HEAD", cwd=dest).strip() == "feat/x"
    listing = payload(
        run(
            [
                *entry_points(world)["cli"],
                "list",
                "--repo",
                str(world["repo"]),
                "--json",
            ]
        )
    )
    row = next(w for w in listing["worktrees"] if not w["main"])
    assert row["in_policy"] is True and row["canonical_destination"] == str(dest)
    identities = json.loads(
        (Path(os.environ["NEXUS_WORKTREE_STATE"]) / "identities.json").read_text(
            encoding="utf-8"
        )
    )
    assert list(identities["repos"]) == [out["identity"]]


def test_every_entry_point_gives_the_same_ownership_location_and_refusals(
    world: dict[str, Path]
) -> None:
    seen: dict[str, tuple] = {}
    for label, argv in entry_points(world).items():
        name = f"parity-{label}"
        made = run(
            [
                *argv,
                "create",
                "--repo",
                str(world["repo"]),
                "--branch",
                name,
                "--base",
                "HEAD",
                "--name",
                name,
                "--json",
            ]
        )
        again = run(
            [
                *argv,
                "create",
                "--repo",
                str(world["repo"]),
                "--branch",
                name,
                "--base",
                "HEAD",
                "--name",
                name,
                "--json",
            ]
        )
        other = run(
            [
                *argv,
                "create",
                "--repo",
                str(world["repo"]),
                "--branch",
                "other-" + label,
                "--base",
                "HEAD",
                "--name",
                name,
                "--json",
            ]
        )
        bad_base = run(
            [
                *argv,
                "create",
                "--repo",
                str(world["repo"]),
                "--branch",
                "b-" + label,
                "--base",
                "no-such-ref",
                "--name",
                "x-" + label,
                "--json",
            ]
        )
        dashed = run(
            [
                *argv,
                "create",
                "--repo",
                str(world["repo"]),
                "--branch=-evil",
                "--base",
                "HEAD",
                "--name",
                "y",
                "--json",
            ]
        )
        made_out = payload(made)
        seen[label] = (
            made.returncode,
            made_out["status"],
            made_out["identity"],
            Path(made_out["path"]).parent.parent.name == "central",
            again.returncode,
            payload(again)["status"],
            other.returncode,
            payload(other)["code"],
            bad_base.returncode,
            payload(bad_base)["code"],
            dashed.returncode,
            payload(dashed)["code"],
        )
    assert len(set(seen.values())) == 1, seen
    assert next(iter(seen.values())) == (
        0,
        "created",
        next(iter(seen.values()))[2],
        True,
        0,
        "exists",
        2,
        "destination-registered-other-branch",
        2,
        "base-unresolved",
        2,
        "invalid-branch",
    )


def test_existing_branch_and_invalid_root_refuse_before_any_git_write(
    world: dict[str, Path]
) -> None:
    cli = entry_points(world)["cli"]
    git("branch", "taken", cwd=world["repo"])
    before = git("worktree", "list", "--porcelain", cwd=world["repo"])
    exists = run(
        [
            *cli,
            "create",
            "--repo",
            str(world["repo"]),
            "--branch",
            "taken",
            "--base",
            "HEAD",
            "--name",
            "t",
            "--json",
        ]
    )
    assert exists.returncode == 2 and payload(exists)["code"] == "branch-exists"
    env = {**os.environ, "NEXUS_WORKTREE_ROOT": "relative/root"}
    bad = run(
        [
            *cli,
            "create",
            "--repo",
            str(world["repo"]),
            "--branch",
            "n",
            "--base",
            "HEAD",
            "--name",
            "n",
            "--json",
        ],
        env=env,
    )
    inside = {**os.environ, "NEXUS_WORKTREE_ROOT": str(world["repo"] / "wt")}
    nested = run(
        [
            *cli,
            "create",
            "--repo",
            str(world["repo"]),
            "--branch",
            "n",
            "--base",
            "HEAD",
            "--name",
            "n",
            "--json",
        ],
        env=inside,
    )
    assert bad.returncode == nested.returncode == 2
    assert (
        payload(bad)["code"] == "root-not-absolute"
        and payload(nested)["code"] == "root-inside-repository"
    )
    assert (
        git("worktree", "list", "--porcelain", cwd=world["repo"]) == before
        and not world["central"].exists()
    )


def test_unregistered_occupant_and_name_collisions_refuse(
    world: dict[str, Path]
) -> None:
    cli = entry_points(world)["cli"]
    first = payload(
        run(
            [
                *cli,
                "create",
                "--repo",
                str(world["repo"]),
                "--branch",
                "one",
                "--base",
                "HEAD",
                "--name",
                "same",
                "--json",
            ]
        )
    )
    squat = Path(first["path"]).parent / "squatter"
    squat.mkdir()
    refused = run(
        [
            *cli,
            "create",
            "--repo",
            str(world["repo"]),
            "--branch",
            "two",
            "--base",
            "HEAD",
            "--name",
            "squatter",
            "--json",
        ]
    )
    assert refused.returncode == 2 and payload(refused)["code"] == "destination-exists"
    lossy_a = payload(
        run([*cli, "path", "--repo", str(world["repo"]), "--name", "feat/x", "--json"])
    )
    lossy_b = payload(
        run([*cli, "path", "--repo", str(world["repo"]), "--name", "feat-x", "--json"])
    )
    assert lossy_a["path"] != lossy_b["path"]


def test_concurrent_creates_serialize_per_repository(world: dict[str, Path]) -> None:
    cli = entry_points(world)["cli"]
    same = [
        subprocess.Popen(
            [
                *cli,
                "create",
                "--repo",
                str(world["repo"]),
                "--branch",
                "race",
                "--base",
                "HEAD",
                "--name",
                "race",
                "--json",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for _ in range(3)
    ]
    outs = [(p.communicate(timeout=180)[0], p.returncode) for p in same]
    statuses = sorted(json.loads(o)["status"] for o, rc in outs if rc == 0)
    assert statuses == ["created", "exists", "exists"], outs
    diff = [
        subprocess.Popen(
            [
                *cli,
                "create",
                "--repo",
                str(world["repo"]),
                "--branch",
                f"b{i}",
                "--base",
                "HEAD",
                "--name",
                "dup",
                "--json",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for i in range(3)
    ]
    results = [(p.communicate(timeout=180)[0], p.returncode) for p in diff]
    assert sorted(rc for _, rc in results) == [0, 2, 2], results
    registered = nw.list_registered(nw.GitInspector(), cwd=str(world["repo"]))
    assert len(registered) == 3  # main, race, one dup
    assert not list((Path(os.environ["NEXUS_WORKTREE_STATE"]) / "locks").glob("*.lock"))


def test_held_lock_refuses_with_an_actionable_message(
    world: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    inspector = nw.GitInspector()
    identity, _ = nw.repo_context(
        inspector, str(world["repo"]), nw.resolve_root().path, write=False
    )
    with nw.RepoLock(identity.id):
        with pytest.raises(nw.PolicyError) as caught:
            with nw.RepoLock(identity.id, wait=0.3):
                pass
    assert caught.value.code == "repository-locked"


def test_missing_helper_blocks_the_capability_explicitly(
    world: dict[str, Path]
) -> None:
    installed = world["home"] / "broken" / "scripts"
    installed.mkdir(parents=True)
    shutil.copy2(SCRIPTS / "nexus_hub_cli.py", installed / "nexus_hub_cli.py")
    shutil.copy2(SCRIPTS / "nexus_process.py", installed / "nexus_process.py")
    proc = run(
        [
            sys.executable,
            str(installed / "nexus_hub_cli.py"),
            "worktree",
            "path",
            "--repo",
            str(world["repo"]),
            "--name",
            "x",
        ]
    )
    assert proc.returncode == 2 and "nexus_worktrees.py missing" in proc.stderr


def test_shell_quoting_survives_powershell_and_git_bash(
    world: dict[str, Path],
) -> None:
    powershell_bin = shutil.which("powershell") or shutil.which("pwsh")
    bash_bin = shutil.which("bash")
    if not powershell_bin or not bash_bin:
        pytest.skip("needs both PowerShell and bash")
    helper = str(SCRIPTS / "nexus_worktrees.py")
    name = "it's a quoted name"
    results = {}
    ps = run(
        [
            powershell_bin,
            "-NoProfile",
            "-Command",
            f"& '{sys.executable}' '{helper}' path --repo '{world['repo']}' --name \"it's a quoted name\" --json",
        ]
    )
    sh = run(
        [
            bash_bin,
            "-c",
            'python "$0" path --repo "$1" --name "$2" --json',
            helper,
            str(world["repo"]),
            name,
        ]
    )
    direct = run(
        [
            sys.executable,
            helper,
            "path",
            "--repo",
            str(world["repo"]),
            "--name",
            name,
            "--json",
        ]
    )
    for label, proc in (("ps", ps), ("sh", sh), ("direct", direct)):
        assert proc.returncode == 0, (label, proc.stdout, proc.stderr)
        results[label] = payload(proc)["path"]
    assert results["ps"] == results["sh"] == results["direct"]


def test_guard_and_creator_agree_on_what_is_inside_the_root(
    world: dict[str, Path]
) -> None:
    created = payload(
        run(
            [
                *entry_points(world)["cli"],
                "create",
                "--repo",
                str(world["repo"]),
                "--branch",
                "agree",
                "--base",
                "HEAD",
                "--name",
                "agree",
                "--json",
            ]
        )
    )
    hook = REPO / "catalog" / "hooks" / "_worktree_policy.py"
    env = {**os.environ}

    def decision(dest: str) -> int:
        body = json.dumps(
            {
                "cwd": str(world["repo"]),
                "tool_input": {"command": f'git worktree add "{dest}" -b z'},
            }
        )
        return run([sys.executable, str(hook)], input=body, env=env).returncode

    assert (
        decision(created["path"] + "-sibling") == 0
    )  # same <root>/<identity>/<name> shape
    assert decision(str(world["repo"].parent / "sibling-wt")) == 42


def test_skill_names_every_native_surface_and_its_destination_capability() -> None:
    text = (REPO / "catalog/skills/workflow/using-git-worktrees/SKILL.md").read_text(
        encoding="utf-8"
    )
    for needle in (
        "EnterWorktree",
        "`name`",
        "`path`",
        "Raw `git worktree add`",
        "Uncovered",
        "worktree-policy",
        "nexus-hub worktree create",
        "Cursor and Codex agent worktrees",
    ):
        assert needle in text, needle
    assert "native tool before raw" not in (
        REPO
        / "catalog/skills/workflow/implement-phase/references/implement-phase-runbook.md"
    ).read_text(encoding="utf-8")


def test_cursor_receives_the_guard_only_through_the_imported_claude_settings() -> None:
    """Exactly one route: the catalog registration, no curated or native Cursor entry."""
    from scripts.lib.integrations import cursor as cursor_integration

    klass = next(v for v in vars(cursor_integration).values() if isinstance(v, type) and hasattr(v, "_CURATED_HOOK_SCRIPTS"))
    assert not any("worktree" in name for name in klass._CURATED_HOOK_SCRIPTS)
    registration = json.dumps(klass._hook_registration(klass, lambda script: script))
    assert "worktree-policy" not in registration
    settings = json.loads((REPO / "catalog/hooks/settings.json").read_text(encoding="utf-8"))
    commands = [h["command"] for g in settings["hooks"]["PreToolUse"] for h in g["hooks"] if "worktree-policy" in h["command"]]
    assert commands == ["bash .claude/hooks/worktree-policy.sh"]
    group = next(g for g in settings["hooks"]["PreToolUse"] if g["hooks"][0]["command"].endswith("worktree-policy.sh"))
    assert group["matcher"] == "Bash|PowerShell" and settings["hooks"]["PreToolUse"][-1] is group
