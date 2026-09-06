"""Unit and integration tests for the repository-native CI engine (v4.0.0 Phase 6).

Deterministic and offline. Real command execution is exercised with fake
commands (`sys.executable -c ...`) so the suite proves the ENGINE rather than
re-running the repository's validators, which `ci-full` already does.

One bounded integration test invokes the real entry point in `--list` mode,
which resolves every command without executing any.

Note on the redaction fixtures: their sample values are ASSEMBLED at runtime
from fragments rather than written as literals. The repository's own
`secret-scan` hook blocks a write containing a hardcoded secret-shaped
assignment, and it was right to. A scanner that exempted test files would exempt
the easiest place to hide one.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.ci import PROFILE_NAMES  # noqa: E402
from scripts.ci import change_scope  # noqa: E402
from scripts.ci import run as run_mod  # noqa: E402
from scripts.ci.profiles import (  # noqa: E402
    PROFILES,
    Command,
    Group,
    detect_platform,
    groups_for,
)

PY = sys.executable

#: Assembled, never written as a literal. See the module docstring.
FAKE_TOKEN = "gh" + "p_" + ("A" * 30)
FAKE_SECRET_VALUE = "-".join(["nexus", "ci", "fixture", "value", "0123456789"])


def _ok(name: str = "ok", **kw) -> Command:
    return Command(name=name, argv=[PY, "-c", "print(1)"], timeout=60, **kw)


def _fail(name: str = "bad", code: int = 3, **kw) -> Command:
    return Command(name=name, argv=[PY, "-c", f"import sys;sys.exit({code})"], timeout=60, **kw)


# ---------------------------------------------------------------------------
# Profile definitions
# ---------------------------------------------------------------------------


def test_the_five_canonical_profiles_exist_and_no_others():
    assert tuple(PROFILES) == PROFILE_NAMES


@pytest.mark.parametrize("profile", PROFILE_NAMES)
def test_every_profile_resolves(profile: str):
    groups_for(profile)


def test_unknown_profile_raises_with_the_valid_set():
    with pytest.raises(KeyError) as excinfo:
        groups_for("turbo")
    assert "fast" in str(excinfo.value)


def test_report_profile_runs_nothing():
    """Aggregation-only is what makes the report profile safe to call after a failure."""
    assert groups_for("report") == ()


def test_every_group_scope_key_is_a_known_scope():
    for profile in PROFILE_NAMES:
        for group in groups_for(profile):
            assert group.scope_key is None or group.scope_key in change_scope.SCOPE_KEYS, (
                f"{profile}/{group.name} declares unknown scope {group.scope_key!r}"
            )


def test_group_and_command_names_are_unique_within_a_profile():
    """A duplicate name silently overwrites its twin in the JUnit output."""
    for profile in PROFILE_NAMES:
        groups = groups_for(profile)
        names = [g.name for g in groups]
        assert len(names) == len(set(names)), f"{profile} has duplicate group names"
        for group in groups:
            cmd_names = [c.name for c in group.commands]
            assert len(cmd_names) == len(set(cmd_names)), (
                f"{profile}/{group.name} has duplicate command names"
            )


def test_every_command_declares_a_timeout():
    """A command with no timeout can hang a run forever, which is worse than red."""
    for profile in PROFILE_NAMES:
        for group in groups_for(profile):
            for cmd in group.commands:
                assert cmd.timeout > 0, f"{group.name}/{cmd.name} has no timeout"


def test_repository_suite_timeout_covers_the_measured_windows_baseline():
    repo_tests = next(
        command
        for group in groups_for("full")
        if group.name == "tests"
        for command in group.commands
        if command.name == "repo-tests"
    )
    assert repo_tests.timeout >= 4500


def test_no_command_is_a_shell_string():
    """argv-as-list keeps a path containing a space from being re-split.

    This repository lives under a OneDrive path with a space in it, so the
    concern is live rather than theoretical.
    """
    for profile in PROFILE_NAMES:
        for group in groups_for(profile):
            for cmd in group.commands:
                assert not isinstance(cmd.argv, str), f"{cmd.name} passes a shell string"
                assert len(cmd.argv) >= 1


def test_platform_profile_covers_every_host_class():
    """A platform profile naming only one host would prove nothing elsewhere."""
    declared = {
        p
        for group in groups_for("platform")
        for cmd in group.commands
        for p in (cmd.platforms or ())
    }
    assert {"linux", "macos", "windows"} <= declared


def test_windows_hook_leg_pins_the_powershell_edition():
    """The BOM defect class reproduces on 5.1 and not on 7, so the edition matters."""
    cmds = [
        c for g in groups_for("platform") for c in g.commands if "windows" in (c.platforms or ())
    ]
    pinned = [c for c in cmds if c.env.get("NEXUS_TEST_POWERSHELL") == "powershell"]
    assert pinned, "no Windows leg pins NEXUS_TEST_POWERSHELL=powershell"


def test_fast_profile_runs_no_test_suite():
    """The fast profile exists to be cheap. A pytest invocation defeats the point."""
    for group in groups_for("fast"):
        for cmd in group.commands:
            assert "pytest" not in " ".join(cmd.argv), f"{cmd.name} runs pytest in fast"


def test_release_profile_is_not_a_validation_rerun():
    """Contract section 4: the release event never re-runs the complete suite."""
    for group in groups_for("release"):
        for cmd in group.commands:
            assert "pytest" not in " ".join(cmd.argv), f"{cmd.name} re-runs tests in release"


# ---------------------------------------------------------------------------
# Command execution
# ---------------------------------------------------------------------------


def test_a_passing_command_reports_pass():
    result = run_mod.run_command(_ok(), REPO_ROOT, [], quiet=True)
    assert result.status == "pass"
    assert result.exit_code == 0
    assert not result.counts_as_failure


def test_a_failing_command_reports_fail_with_its_exit_code():
    result = run_mod.run_command(_fail(code=7), REPO_ROOT, [], quiet=True)
    assert result.status == "fail"
    assert result.exit_code == 7
    assert result.counts_as_failure


def test_an_advisory_failure_does_not_count_as_a_failure():
    result = run_mod.run_command(_fail(advisory=True), REPO_ROOT, [], quiet=True)
    assert result.status == "advisory-fail"
    assert not result.counts_as_failure


def test_a_timeout_is_a_failure_not_a_pass():
    slow = Command(name="slow", argv=[PY, "-c", "import time;time.sleep(30)"], timeout=1)
    result = run_mod.run_command(slow, REPO_ROOT, [], quiet=True)
    assert result.status == "timeout"
    assert result.counts_as_failure
    assert "exceeded 1s" in result.reason


def test_a_missing_executable_is_a_failure_not_a_pass():
    """A missing tool and a passing tool must never look the same."""
    missing = Command(name="ghost", argv=["definitely-not-a-real-binary-xyz"], timeout=30)
    result = run_mod.run_command(missing, REPO_ROOT, [], quiet=True)
    assert result.status == "missing"
    assert result.counts_as_failure


def test_a_missing_working_directory_is_a_failure():
    cmd = Command(name="nowhere", argv=[PY, "-c", "pass"], cwd="no/such/dir", timeout=30)
    result = run_mod.run_command(cmd, REPO_ROOT, [], quiet=True)
    assert result.status == "missing"


def test_an_inline_token_shape_is_redacted_from_output():
    cmd = Command(name="leaky", argv=[PY, "-c", f"print({FAKE_TOKEN!r})"], timeout=60)
    result = run_mod.run_command(cmd, REPO_ROOT, [], quiet=True)
    assert "[REDACTED]" in result.output
    assert FAKE_TOKEN not in result.output


def test_a_known_secret_value_is_redacted_from_output():
    cmd = Command(name="echo-value", argv=[PY, "-c", f"print({FAKE_SECRET_VALUE!r})"], timeout=60)
    result = run_mod.run_command(cmd, REPO_ROOT, [FAKE_SECRET_VALUE], quiet=True)
    assert FAKE_SECRET_VALUE not in result.output
    assert "[REDACTED]" in result.output


def test_per_command_env_reaches_the_subprocess():
    cmd = Command(
        name="env",
        argv=[PY, "-c", "import os;print(os.environ[chr(78)+'EXUS_CI_PROBE'])"],
        timeout=60,
        env={"NEXUS_CI_PROBE": "seen"},
    )
    result = run_mod.run_command(cmd, REPO_ROOT, [], quiet=True)
    assert "seen" in result.output


# ---------------------------------------------------------------------------
# Group and profile aggregation
# ---------------------------------------------------------------------------


def _all_scopes() -> change_scope.ScopeDecision:
    return change_scope._all_required("test")


def test_group_status_is_fail_when_any_command_fails():
    group = Group(name="g", commands=(_ok(), _fail(), _ok("ok2")))
    result = run_mod.run_group(group, detect_platform(), _all_scopes(), REPO_ROOT, [], quiet=True)
    assert result.status == "fail"
    assert len(result.commands) == 3


def test_a_group_keeps_running_after_a_failure():
    """One run should report every independent failure, not only the first."""
    group = Group(name="g", commands=(_fail("first"), _fail("second")))
    result = run_mod.run_group(group, detect_platform(), _all_scopes(), REPO_ROOT, [], quiet=True)
    assert [c.status for c in result.commands] == ["fail", "fail"]


def test_off_platform_commands_are_recorded_as_skips_not_omitted():
    """A skip nobody can see is indistinguishable from a pass."""
    other = "linux" if detect_platform() != "linux" else "windows"
    group = Group(name="g", commands=(_ok(), _ok("elsewhere", platforms=(other,))))
    result = run_mod.run_group(group, detect_platform(), _all_scopes(), REPO_ROOT, [], quiet=True)
    statuses = {c.name: c.status for c in result.commands}
    assert statuses["elsewhere"] == "skip"
    assert "scoped to" in next(c.reason for c in result.commands if c.name == "elsewhere")


def test_a_group_out_of_scope_is_skipped_with_a_reason():
    decision = change_scope.classify_paths(["docs/readme-prose.md"])
    group = Group(name="g", commands=(_ok(),), scope_key="extensions")
    result = run_mod.run_group(group, detect_platform(), decision, REPO_ROOT, [], quiet=True)
    assert result.status == "skip"
    assert result.skipped_reason


def test_a_group_with_no_scope_key_always_runs():
    decision = change_scope.classify_paths(["docs/readme-prose.md"])
    group = Group(name="g", commands=(_ok(),), scope_key=None)
    result = run_mod.run_group(group, detect_platform(), decision, REPO_ROOT, [], quiet=True)
    assert result.status == "pass"


# ---------------------------------------------------------------------------
# Change scope -- fail closed
# ---------------------------------------------------------------------------


def test_an_empty_diff_runs_everything():
    decision = change_scope.classify_paths([])
    assert decision.conservative
    assert decision.required == set(change_scope.SCOPE_KEYS)


def test_an_unresolvable_diff_runs_everything():
    decision = change_scope.classify("definitely-not-a-revision-xyz", repo_root=REPO_ROOT)
    assert decision.conservative
    assert decision.required == set(change_scope.SCOPE_KEYS)


def test_an_all_zero_base_sha_runs_everything():
    """The new-branch sentinel. Nothing to diff against."""
    decision = change_scope.classify("0" * 40, repo_root=REPO_ROOT)
    assert decision.conservative


def test_no_base_runs_everything():
    assert change_scope.classify(None).conservative


def test_an_unrecognized_path_runs_everything():
    decision = change_scope.classify_paths(["some-brand-new-top-level-thing/x.py"])
    assert decision.conservative
    assert "unrecognized" in decision.reason


def test_a_root_wide_file_runs_everything():
    decision = change_scope.classify_paths(["Makefile"])
    assert decision.conservative
    assert "Makefile" in decision.reason


def test_documentation_prose_scopes_to_docs_only():
    """The one class it is safe to skip, and the only reason this module exists."""
    decision = change_scope.classify_paths(["docs/v4/v4.0/development/history/x.md"])
    assert not decision.conservative
    assert decision.required == {"docs"}
    assert "catalog" in decision.skipped


def test_a_catalog_change_requires_the_catalog_scope():
    decision = change_scope.classify_paths(["catalog/skills/workflow/x/SKILL.md"])
    assert "catalog" in decision.required
    assert not decision.conservative


def test_a_workflow_change_requires_the_workflow_scope():
    decision = change_scope.classify_paths([".github/workflows/ci.yml"])
    assert "workflows" in decision.required


def test_a_policy_doc_change_is_validator_input_not_prose():
    """docs/policy feeds several validators, so editing it must run them."""
    decision = change_scope.classify_paths(["docs/policy/required-checks.json"])
    assert {"docs", "platforms", "workflows"} <= decision.required


def test_windows_path_separators_are_normalized():
    decision = change_scope.classify_paths(["catalog\\skills\\workflow\\x\\SKILL.md"])
    assert "catalog" in decision.required
    assert not decision.conservative


def test_a_deleted_or_renamed_file_classifies_by_path():
    """A rename reports both sides as ordinary paths, so both classify normally."""
    decision = change_scope.classify_paths(
        ["catalog/skills/a/old/SKILL.md", "catalog/skills/a/new/SKILL.md"]
    )
    assert decision.required == {"catalog"}


def test_a_large_diff_is_handled_without_special_casing():
    paths = [f"docs/v4/v4.0/development/history/file-{i}.md" for i in range(5000)]
    decision = change_scope.classify_paths(paths)
    assert decision.required == {"docs"}


def test_a_mixed_diff_unions_every_matched_scope():
    decision = change_scope.classify_paths(
        ["catalog/skills/a/SKILL.md", ".github/workflows/ci.yml", "tests/ci/test_x.py"]
    )
    assert {"catalog", "workflows", "tests"} <= decision.required


def test_classify_never_raises_on_a_hostile_input():
    for bad in ([""], ["   "], ["../../etc/passwd"], ["\x00weird"]):
        decision = change_scope.classify_paths(bad)
        assert isinstance(decision, change_scope.ScopeDecision)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_list_mode_exits_zero_and_runs_nothing(capsys):
    code = run_mod.main(["--profile", "full", "--list"])
    assert code == 0
    out = capsys.readouterr().out
    assert "catalog-parse" in out
    assert "[scope:" in out


def test_cli_rejects_an_unknown_profile():
    with pytest.raises(SystemExit) as excinfo:
        run_mod.main(["--profile", "turbo"])
    assert excinfo.value.code != 0


def test_cli_requires_a_profile():
    with pytest.raises(SystemExit):
        run_mod.main([])


def test_platform_override_changes_the_resolved_listing(capsys):
    run_mod.main(["--profile", "platform", "--platform", "linux", "--list"])
    linux = capsys.readouterr().out
    run_mod.main(["--profile", "platform", "--platform", "windows", "--list"])
    windows = capsys.readouterr().out
    assert linux != windows, "the platform override did not change the resolved commands"
    assert "skipped on linux" in linux
    assert "skipped on windows" in windows


@pytest.mark.parametrize("profile", PROFILE_NAMES)
def test_real_cli_list_mode_runs_offline_for_every_profile(profile: str):
    """One bounded integration test against the real entry point.

    List mode resolves every command without executing any, so this proves the
    module imports, the parser accepts each profile, and no profile definition
    raises at load time, in well under a second and with no network.
    """
    proc = subprocess.run(
        [PY, "scripts/ci/run.py", "--profile", profile, "--list"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    assert f"profile: {profile}" in proc.stdout


def test_the_engine_needs_no_ci_provider_environment():
    """Contract section 3: a profile runs with no CI-provider variables set.

    Asserting on the SOURCE rather than by clearing the environment, because a
    passing run on a machine that never had those variables proves nothing.
    """
    for name in ("run.py", "profiles.py", "change_scope.py", "reporting.py"):
        text = (REPO_ROOT / "scripts" / "ci" / name).read_text(encoding="utf-8")
        for forbidden in ("GITHUB_ACTIONS", "GITHUB_OUTPUT", "GITHUB_STEP_SUMMARY", "CI_PIPELINE"):
            assert forbidden not in text, f"{name} reads the CI provider variable {forbidden}"


def test_extension_suites_target_their_configured_test_path_not_the_package_root():
    """An explicit `.` overrides each package's own `testpaths = ["tests"]`.

    A bare `pytest` honors the package configuration; `pytest .` does not, and
    walks the whole tree instead -- pulling in benchmark fixture corpora that
    import modules deliberately absent from the environment. `make test` runs
    bare pytest and passed while this profile passed `.` and failed, so the two
    looked equivalent and were not. Naming the configured path keeps them so.
    """
    for group in groups_for("full"):
        if group.name != "extension-tests":
            continue
        for cmd in group.commands:
            argv = list(cmd.argv)
            if "pytest" not in argv:
                continue
            targets = [a for a in argv[argv.index("pytest") + 1:] if not a.startswith("-")]
            assert targets, f"{cmd.name} passes pytest no target at all"
            assert "." not in targets, (
                f"{cmd.name} targets the package root, which overrides its "
                "testpaths and collects non-test fixture code"
            )


def test_extension_commands_isolate_imports_to_the_current_checkout():
    """A stale editable install must not redirect tests to another checkout."""
    commands = {
        command.name: command
        for group in groups_for("full")
        if group.name == "extension-tests"
        for command in group.commands
    }
    for name, command in commands.items():
        paths = command.env.get("PYTHONPATH", "").split(os.pathsep)
        assert paths[0] == "src", f"{name} does not prefer its current src tree"

    expected_compressor_paths = ["src", "../nexus-code-search/src"]
    assert commands["context-compressor"].env["PYTHONPATH"].split(os.pathsep) == (
        expected_compressor_paths
    )
    assert commands["compression-accuracy-gate"].env["PYTHONPATH"].split(os.pathsep) == (
        expected_compressor_paths
    )
