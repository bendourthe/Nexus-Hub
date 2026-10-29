"""Unit and integration tests for the repository-native CI engine (v4.0.0 Phase 6).

Deterministic and offline. Real command execution is exercised with fake
commands (`sys.executable -c ...`) and tiny generated pytest cases, so the suite
proves the ENGINE without re-running the repository's validators.

One bounded integration test invokes the real entry point in `--list` mode,
which resolves every command without executing any.

Note on the redaction fixtures: their sample values are ASSEMBLED at runtime
from fragments rather than written as literals. The repository's own
`secret-scan` hook blocks a write containing a hardcoded secret-shaped
assignment, and it was right to. A scanner that exempted test files would exempt
the easiest place to hide one.
"""

from __future__ import annotations

import fnmatch
import json
import os
import subprocess
import sys
import time
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


def _profile_selects(command, relative: str, host: str) -> bool:
    relative = relative.replace("\\", "/")
    normalize = str.casefold if host == "windows" else str
    relative = normalize(relative)
    args = [normalize(arg.replace("\\", "/")) for arg in command.argv[3:]]
    targets = [arg.rstrip("/") for arg in args if not arg.startswith("-")]
    if not any(relative == target or relative.startswith(target + "/") for target in targets):
        return False
    ignores = [arg.split("=", 1)[1].rstrip("/") for arg in args if arg.startswith("--ignore=")]
    globs = [arg.split("=", 1)[1] for arg in args if arg.startswith("--ignore-glob=")]
    return not any(relative == path or relative.startswith(path + "/") for path in ignores) and not any(
        fnmatch.fnmatchcase(relative, pattern) for pattern in globs
    )


@pytest.mark.parametrize("host", ("linux", "macos", "windows"))
def test_repository_suite_is_partitioned_without_coverage_gaps(host):
    """Every host selects each repository test file once, including exclusions."""
    commands = next(group for group in groups_for("full") if group.name == "tests").commands
    repo_commands = [command for command in commands if command.name.startswith("repo-tests-") and command.runs_on(host)]
    expected_files = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in (REPO_ROOT / "tests").rglob("test_*.py")
        if "fixtures" not in path.relative_to(REPO_ROOT / "tests").parts
    ]
    assert expected_files
    assert all(sum(_profile_selects(command, relative, host) for command in repo_commands) == 1
               for relative in expected_files)
    assert all(command.timeout <= 4500 for command in repo_commands)


@pytest.mark.parametrize("host", ("linux", "macos", "windows"))
@pytest.mark.parametrize("separator", ("/", "\\"))
def test_full_guide_scheduling_preserves_scope_and_limits(host, separator):
    commands = next(group for group in groups_for("full") if group.name == "tests").commands
    commands = [command for command in commands if command.runs_on(host)
                and any(arg == "tests/guides" or arg.startswith("tests/guides/") for arg in command.argv)]
    heavy = (
        "tests/guides/test_training_game_engine.py",
        "tests/guides/test_page_openings_and_outline.py",
        "tests/guides/test_training_reward_mockup.py",
        "tests/guides/test_models_learning_lab.py",
    )
    if host == "windows":
        assert len(commands) == 2
        assert list(commands[0].argv) == [PY, "-m", "pytest", *heavy[:1], "-q", *heavy[1:]]
        assert list(commands[1].argv) == [PY, "-m", "pytest", "tests/guides", "-q",
                                             *(f"--ignore={path}" for path in heavy)]
    else:
        assert len(commands) == 1
        assert commands[0].name == "repo-tests-guides"
        assert list(commands[0].argv) == [PY, "-m", "pytest", "tests/guides", "-q"]
    for command in commands:
        assert command.timeout == 1800
        assert command.platform_timeouts == {}
        assert command.timeout_on(host) == 1800
        assert command.cwd == "." and command.env == {}
        assert not command.advisory and not command.skip_if_missing
    actual = [path.relative_to(REPO_ROOT).as_posix() for path in (REPO_ROOT / "tests/guides").rglob("test_*.py")]
    assert actual
    future = ["tests/guides/test_future.py", "tests/guides/test_9.py", "tests/guides/test__future.py",
              "tests/guides/nested/test_future.py"]
    for relative in [*actual, *future]:
        assert sum(_profile_selects(command, relative.replace("/", separator), host) for command in commands) == 1


@pytest.mark.parametrize("host", ("linux", "macos", "windows"))
def test_full_adapter_scheduling_preserves_scope_and_limits(host):
    original = (
        "tests/integrations/test_agent_model_delivery.py",
        "tests/integrations/test_base_writeresult.py",
        "tests/integrations/test_catalog_adapters.py",
        "tests/integrations/test_contract.py",
        "tests/integrations/test_cross_platform_flatten.py",
        "tests/integrations/test_global_command_surface.py",
        "tests/integrations/test_owned_root_preflight.py",
        "tests/integrations/test_skill_path_provider_order.py",
        "tests/integrations/test_windows_long_paths.py",
    )
    commands = [command for group in groups_for("full") if group.name == "tests"
                for command in group.commands if command.runs_on(host)
                and command.name.startswith("repo-tests-integrations-adapter-contracts")]
    contract = ("tests/integrations/test_contract.py",)
    remaining = tuple(path for path in original if path not in contract)
    parts = (contract, remaining) if host == "windows" else (original,)
    assert len(commands) == len(parts)
    limits = (2700, 1800) if host == "windows" else (1800,)
    for command, files, limit in zip(commands, parts, limits):
        assert list(command.argv) == [PY, "-m", "pytest", files[0], "-q", *files[1:]]
        assert command.timeout == limit and command.platform_timeouts == {}
        assert command.timeout_on(host) == limit
        assert command.cwd == "." and command.env == {}
        assert not command.advisory and not command.skip_if_missing
    actual = [arg for command in commands for arg in command.argv if arg in original]
    assert sorted(actual) == sorted(original)
    assert len(actual) == len(set(actual))


def test_existing_profile_commands_emit_coverage_and_sarif() -> None:
    groups = {group.name: group for group in groups_for("full")}
    ci_tests = next(command for command in groups["tests"].commands if command.name == "repo-tests-ci")
    scanner = next(command for command in groups["catalog"].commands if command.name == "scan_skill_security")

    assert "--cov=scripts.ci" in ci_tests.argv
    assert "--cov-report=xml:reports/coverage-ci.xml" in ci_tests.argv
    assert "--format" in scanner.argv and "sarif" in scanner.argv
    assert "--output" in scanner.argv and "reports/skill-security.sarif" in scanner.argv


def test_pre_commit_profile_installs_policy_inside_cli(tmp_path):
    """A hidden outer process does not hide Git started by a second interpreter."""
    group = next(group for group in groups_for("full") if group.name == "pre-commit")
    command = group.commands[0]
    assert list(command.argv[:2]) == [PY, "-c"]
    assert list(command.argv[3:]) == ["run", "--all-files"]
    assert command.timeout == 1800
    assert command.env == {"SKIP": "lint-templates,build-catalogs"}
    package = tmp_path / "pre_commit"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "__main__.py").write_text(
        "import inspect,json,os,subprocess,sys\n"
        "original = subprocess.Popen._execute_child\n"
        "observed = []\n"
        "def capture(self, *args, **kwargs):\n"
        "    bound = inspect.signature(original).bind(self, *args, **kwargs)\n"
        "    observed.append(bound.arguments.get('creationflags', 0))\n"
        "    return original(self, *args, **kwargs)\n"
        "subprocess.Popen._execute_child = capture\n"
        "git = subprocess.run(['git', '--version'], capture_output=True, text=True, check=True)\n"
        "print(json.dumps({'flags': observed, 'git': git.stdout.strip(), "
        "'args': sys.argv[1:], 'skip': os.environ.get('SKIP'), 'main': __name__}))\n",
        encoding="utf-8",
    )
    env = dict(command.env)
    env["PYTHONPATH"] = str(tmp_path) + os.pathsep + os.environ.get("PYTHONPATH", "")
    probe = Command(name=command.name, argv=command.argv, env=env, timeout=command.timeout)
    result = run_mod.run_command(probe, REPO_ROOT, [], quiet=True)
    assert result.status == "pass", result.output
    observed = json.loads(result.output.strip())
    assert observed["git"].startswith("git version ")
    assert observed["args"] == ["run", "--all-files"]
    assert observed["skip"] == "lint-templates,build-catalogs"
    assert observed["main"] == "__main__"
    assert len(observed["flags"]) == 1
    if os.name == "nt":
        assert observed["flags"][0] & subprocess.CREATE_NO_WINDOW


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


@pytest.fixture
def pytest_scratch_probe(tmp_path, monkeypatch):
    parent = tmp_path / "scratch"
    parent.mkdir()
    sibling = parent / "unrelated.txt"
    sibling.write_text("keep", encoding="utf-8")
    project = tmp_path / "project"
    project.mkdir()
    case = project / "test_probe.py"
    case.write_text(
        "import os,time\n"
        "def test_owned(tmp_path, tmp_path_factory):\n"
        "    (tmp_path / 'owned.txt').write_text('owned', encoding='utf-8')\n"
        "    print('base=' + str(tmp_path_factory.getbasetemp()), flush=True)\n"
        "    assert os.environ.get('PYTEST_ADDOPTS') == os.environ.get('PROBE_ADDOPTS', '')\n"
        "    mode = os.environ['PROBE_MODE']\n"
        "    if mode == 'timeout': time.sleep(30)\n"
        "    assert mode != 'fail', 'probe-failure'\n",
        encoding="utf-8",
    )
    directory_type = run_mod.tempfile.TemporaryDirectory
    roots = []
    state = {"fail_cleanup": False}

    def owned_directory(*args, **kwargs):
        directory = directory_type(*args, dir=parent, **kwargs)
        roots.append(directory)
        if state["fail_cleanup"]:
            def deny_cleanup():
                raise PermissionError("probe cleanup denied")
            monkeypatch.setattr(directory, "cleanup", deny_cleanup)
        return directory

    monkeypatch.setattr(run_mod.tempfile, "TemporaryDirectory", owned_directory)

    def command(mode="pass", *extra):
        return Command(
            name="pytest-probe", argv=[PY, "-m", "pytest", str(case), "-q", "-s", *extra],
            timeout=3 if mode == "timeout" else 30, advisory=mode == "advisory",
            env={"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": "", "PROBE_MODE": "fail" if mode == "advisory" else mode},
        )

    yield project, command, roots, sibling, state
    for directory in roots:
        directory_type.cleanup(directory)


def test_pytest_runs_use_distinct_owned_scratch_and_preserve_siblings(pytest_scratch_probe):
    project, command, roots, sibling, _ = pytest_scratch_probe
    for _ in range(2):
        result = run_mod.run_command(command(), project, [], quiet=True)
        assert result.status == "pass", result.output + result.reason
        assert result.exit_code == 0
        assert f"base={Path(roots[-1].name) / 'pytest'}" in result.output
        assert not Path(roots[-1].name).exists()
        assert "execution " in result.reason and "cleanup " in result.reason
        assert "removed" in result.reason
    assert roots[0].name != roots[1].name
    assert sibling.read_text(encoding="utf-8") == "keep"


@pytest.mark.parametrize("mode", ("pass", "fail", "advisory", "timeout", "launch"))
@pytest.mark.parametrize("fail_cleanup", (False, True))
def test_pytest_scratch_cleanup_preserves_command_facts(
    pytest_scratch_probe, monkeypatch, mode, fail_cleanup,
):
    project, command, roots, sibling, state = pytest_scratch_probe
    state["fail_cleanup"] = fail_cleanup
    if mode == "launch":
        def launch_error(*args, **kwargs):
            raise OSError("probe launch denied")
        monkeypatch.setattr(run_mod.subprocess, "Popen", launch_error)
    result = run_mod.run_command(command(mode), project, [], quiet=True)
    expected = {"pass": "pass", "fail": "fail", "advisory": "advisory-fail", "timeout": "timeout", "launch": "missing"}[mode]
    assert result.status == ("fail" if fail_cleanup and expected in ("pass", "advisory-fail") else expected)
    assert result.exit_code == {"pass": 0, "fail": 1, "advisory": 1}.get(mode)
    assert Path(roots[0].name).exists() == fail_cleanup
    assert roots[0].name in result.reason
    if fail_cleanup:
        assert result.counts_as_failure
        assert "probe cleanup denied" in result.reason
        assert f"original status={expected}" in result.reason
    if mode in ("pass", "fail", "advisory", "timeout"):
        assert f"base={Path(roots[0].name) / 'pytest'}" in result.output
    if mode in ("fail", "advisory"):
        assert "probe-failure" in result.output and "exit 1" in result.reason
    if mode == "timeout":
        assert "exceeded 3s" in result.reason
    if mode == "launch":
        assert "probe launch denied" in result.reason
    assert sibling.read_text(encoding="utf-8") == "keep"


@pytest.mark.parametrize("equals", (False, True))
def test_explicit_pytest_basetemp_remains_caller_owned(pytest_scratch_probe, equals):
    project, command, roots, sibling, _ = pytest_scratch_probe
    caller_base = project / "caller-base"
    extra = [f"--basetemp={caller_base}"] if equals else ["--basetemp", str(caller_base)]
    cmd = command("pass", *extra)
    original_argv = list(cmd.argv)
    result = run_mod.run_command(cmd, project, [], quiet=True)
    assert result.status == "pass", result.output + result.reason
    assert f"base={caller_base}" in result.output
    assert (caller_base / "test_owned0" / "owned.txt").read_text(encoding="utf-8") == "owned"
    assert not roots and list(cmd.argv) == original_argv
    assert result.reason == ""
    assert sibling.read_text(encoding="utf-8") == "keep"


def test_inherited_pytest_basetemp_remains_caller_owned(pytest_scratch_probe, monkeypatch):
    project, command, roots, _, _ = pytest_scratch_probe
    caller_base = project / "caller env base"
    addopts = f'--basetemp="{caller_base}"'
    monkeypatch.setenv("PYTEST_ADDOPTS", addopts)
    cmd = command()
    env = {key: value for key, value in cmd.env.items() if key != "PYTEST_ADDOPTS"}
    env["PROBE_ADDOPTS"] = addopts
    cmd = Command(name=cmd.name, argv=cmd.argv, env=env, timeout=cmd.timeout)
    result = run_mod.run_command(cmd, project, [], quiet=True)
    assert result.status == "pass", result.output + result.reason
    assert f"base={caller_base}" in result.output
    assert (caller_base / "test_owned0" / "owned.txt").is_file()
    assert not roots and result.reason == ""
    assert os.environ["PYTEST_ADDOPTS"] == addopts


def test_malformed_pytest_addopts_are_reported_by_pytest(pytest_scratch_probe, monkeypatch):
    project, command, roots, _, _ = pytest_scratch_probe
    monkeypatch.setenv("PYTEST_ADDOPTS", '"unterminated')
    cmd = command()
    env = {key: value for key, value in cmd.env.items() if key != "PYTEST_ADDOPTS"}
    cmd = Command(name=cmd.name, argv=cmd.argv, env=env, timeout=cmd.timeout)
    result = run_mod.run_command(cmd, project, [], quiet=True)
    assert result.status == "fail" and result.exit_code != 0
    assert "No closing quotation" in result.output
    assert not roots


def test_non_pytest_command_does_not_get_owned_scratch(pytest_scratch_probe):
    project, _, roots, _, _ = pytest_scratch_probe
    result = run_mod.run_command(_ok(), project, [], quiet=True)
    assert result.status == "pass" and result.exit_code == 0
    assert result.output.strip() == "1" and result.reason == ""
    assert not roots


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


def test_timeout_kills_process_tree_and_preserves_partial_output(tmp_path, capsys, monkeypatch):
    marker = tmp_path / "child-survived.txt"
    child_code = (
        "import pathlib,time;"
        "time.sleep(2.5);"
        f"pathlib.Path({str(marker)!r}).write_text('alive', encoding='utf-8')"
    )
    parent_code = (
        "import runpy;"
        f"policy=runpy.run_path({str(REPO_ROOT / 'scripts/nexus_process.py')!r});"
        "policy['install_no_window_default']();"
        "import subprocess,sys,time;"
        "print('partial-output', flush=True);"
        f"subprocess.Popen([sys.executable, '-c', {child_code!r}]);"
        "time.sleep(30)"
    )
    command = Command(name="tree-timeout", argv=[PY, "-c", parent_code], timeout=1)

    started = time.monotonic()
    termination = {}
    terminate_process_tree = run_mod._terminate_process_tree

    def observe_termination(proc):
        termination["requested_s"] = time.monotonic() - started
        cleanup_started = time.monotonic()
        try:
            return terminate_process_tree(proc)
        finally:
            termination["duration_s"] = time.monotonic() - cleanup_started

    monkeypatch.setattr(run_mod, "_terminate_process_tree", observe_termination)
    group = Group(name="timeout-group", commands=(command,))
    group_result = run_mod.run_group(
        group, detect_platform(), _all_scopes(), REPO_ROOT, [], quiet=True
    )
    result = group_result.commands[0]
    duration = time.monotonic() - started
    time.sleep(2)

    # The execution deadline and capture must stay prompt; Windows taskkill has
    # its own bounded OS cleanup and may consume the old one-second margin.
    assert termination["requested_s"] < 2
    assert duration - termination["duration_s"] < 2
    assert result.status == "timeout"
    assert "partial-output" in result.output
    assert "tree-timeout" in capsys.readouterr().out
    assert not marker.exists()


def test_a_missing_executable_is_a_failure_not_a_pass():
    """A missing tool and a passing tool must never look the same."""
    missing = Command(name="ghost", argv=["definitely-not-a-real-binary-xyz"], timeout=30)
    result = run_mod.run_command(missing, REPO_ROOT, [], quiet=True)
    assert result.status == "missing"
    assert result.counts_as_failure


def test_an_explicitly_optional_missing_vendor_cli_is_a_visible_skip(capsys):
    optional = Command(
        name="optional-vendor",
        argv=["definitely-not-a-real-binary-xyz"],
        timeout=30,
        skip_if_missing=True,
    )
    result = run_mod.run_command(optional, REPO_ROOT, [], quiet=True)
    run_mod._render_command_result(result, quiet=True)

    assert result.status == "skip"
    assert not result.counts_as_failure
    rendered = capsys.readouterr().out
    assert "[SKIP] optional-vendor" in rendered
    assert "executable not found on PATH" in rendered


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


def test_group_renders_missing_working_directory(capsys):
    command = Command(name="nowhere", argv=[PY, "-c", "pass"], cwd="no/such/dir", timeout=30)
    group = Group(name="g", commands=(command,))

    run_mod.run_group(group, detect_platform(), _all_scopes(), REPO_ROOT, [], quiet=True)

    output = capsys.readouterr().out
    assert "[MISSING] nowhere" in output
    assert "working directory not found" in output


def test_group_renders_missing_executable(capsys):
    command = Command(name="ghost", argv=["definitely-not-a-real-binary-xyz"], timeout=30)
    group = Group(name="g", commands=(command,))

    run_mod.run_group(group, detect_platform(), _all_scopes(), REPO_ROOT, [], quiet=True)

    output = capsys.readouterr().out
    assert "[MISSING] ghost" in output
    assert "executable not found on PATH" in output


def test_group_renders_launch_error(monkeypatch, capsys):
    def fail_to_launch(*args, **kwargs):
        raise PermissionError("launch blocked")

    monkeypatch.setattr(run_mod.subprocess, "Popen", fail_to_launch)
    group = Group(name="g", commands=(_ok("blocked"),))

    run_mod.run_group(group, detect_platform(), _all_scopes(), REPO_ROOT, [], quiet=True)

    output = capsys.readouterr().out
    assert "[MISSING] blocked" in output
    assert "PermissionError: launch blocked" in output


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


def test_full_profile_includes_optional_claude_plugin_validation():
    group = next(group for group in groups_for("full") if group.name == "claude-plugin")
    assert len(group.commands) == 1
    command = group.commands[0]
    assert list(command.argv) == ["claude", "plugin", "validate", "."]
    assert command.skip_if_missing is True


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


def test_windows_audit_tests_are_selected_only_on_windows():
    """The Windows gate must exercise the native evidence and ledger boundaries."""
    commands = [
        command
        for group in groups_for("platform")
        if group.name == "windows-hooks"
        for command in group.commands
        if "tests/skills/test_safe_artifact.py" in command.argv
    ]
    assert len(commands) == 1, "the existing Windows job omits the audit boundary tests"
    command = commands[0]
    selected = {arg for arg in command.argv if arg.startswith("tests/")}
    assert selected == {
        "tests/validators/test_validate_unicode_safety.py",
        "tests/skills/test_safe_artifact.py",
        "tests/skills/test_target_manifest.py",
        "tests/skills/test_strict_json.py",
        "tests/skills/test_security_scanner_contract.py",
        "tests/skills/test_graph_receipts.py",
        "tests/skills/test_application_audit_envelope.py",
        "tests/skills/test_security_review_sarif.py",
        "tests/skills/test_security_audit_benchmark.py",
        "tests/skills/test_security_audit_benchmark_lifecycle.py",
        "tests/skills/test_security_audit_contract_e2e.py",
    }
    assert command.runs_on("windows")
    assert not command.runs_on("linux") and not command.runs_on("macos")
    assert command.timeout == 1200


def test_platform_timeout_override_applies_only_to_its_host_class():
    cmd = Command(name="x", argv=[PY, "-c", "pass"], timeout=1800, platform_timeouts={"windows": 2400})
    assert cmd.timeout_on("windows") == 2400
    assert cmd.timeout_on("linux") == 1800
    assert cmd.timeout_on("macos") == 1800


@pytest.mark.parametrize(
    ("step", "shared", "windows"),
    [("hook-tests", 1800, 2400)],
)
def test_measured_windows_overrides_keep_shared_caps(step, shared, windows):
    """v4.13.9 WN-38: only Windows is raised, from a recorded run."""
    from scripts.ci import profiles

    found = [c for g in profiles.PROFILES["full"] for c in g.commands if c.name == step]
    assert len(found) == 1, step
    cmd = found[0]
    assert cmd.timeout == shared
    assert dict(cmd.platform_timeouts) == {"windows": windows}
    assert cmd.timeout_on("linux") == shared and cmd.timeout_on("macos") == shared


def test_run_group_runs_each_command_with_its_host_timeout(monkeypatch):
    seen = []

    def fake_run(cmd, repo_root, secrets, quiet):
        seen.append(cmd.timeout)
        return run_mod.CommandResult(name=cmd.name, group="", status="pass")

    monkeypatch.setattr(run_mod, "run_command", fake_run)
    cmd = Command(name="t", argv=[PY, "-c", "pass"], timeout=10, platform_timeouts={"windows": 20})
    group = Group(name="override-group", commands=(cmd,))
    for host, expected in (("windows", 20), ("linux", 10)):
        run_mod.run_group(group, host, _all_scopes(), REPO_ROOT, [], quiet=True)
        assert seen[-1] == expected, host


@pytest.mark.parametrize("host", ("linux", "macos", "windows"))
@pytest.mark.parametrize("separator", ("/", "\\"))
def test_full_governance_scheduling_preserves_scope_and_limits(host, separator):
    from scripts.ci import profiles

    targets = ("tests/e2e", "tests/validators", "tests/verification", "tests/workflows",
               "tests/test_git_attribution.py", "tests/test_removed_autonomy_surface.py")
    commands = [command for group in groups_for("full") for command in group.commands
                if command.name.startswith("repo-tests-governance") and command.runs_on(host)]
    if host == "windows":
        assert len(commands) == 5
        assert commands[0].name == "repo-tests-governance-rest (Windows full)"
        assert list(commands[0].argv) == [PY, "-m", "pytest", targets[0], "-q", *targets[2:]]
        assert commands[0].timeout == 2700
        masks = (profiles.VALIDATORS_SHARD_A_IGNORES, profiles.VALIDATORS_SHARD_B_IGNORES,
                 profiles.VALIDATORS_SHARD_C_IGNORES, profiles.VALIDATORS_SHARD_D_IGNORES)
        for command, name, ignores in zip(commands[1:], ("a-c", "co", "d-o", "p-z"), masks):
            assert command.name == f"repo-tests-governance-validators-{name} (Windows full)"
            assert list(command.argv) == [PY, "-m", "pytest", "tests/validators", "-q", *ignores]
            assert command.timeout == (2400 if name == "co" else 1800)
        assert sum(command.timeout_on(host) for command in commands) == 10500
    else:
        assert len(commands) == 1 and commands[0].name == "repo-tests-governance"
        assert list(commands[0].argv) == [PY, "-m", "pytest", targets[0], "-q", *targets[1:]]
        assert commands[0].timeout == 2700
    for command in commands:
        assert command.timeout_on(host) <= 3600
        assert command.platform_timeouts == {}
        assert command.cwd == "." and command.env == {}
        assert not command.advisory and not command.skip_if_missing
    actual = [path.relative_to(REPO_ROOT).as_posix() for target in targets
              for path in ([REPO_ROOT / target] if target.endswith(".py") else (REPO_ROOT / target).rglob("test_*.py"))]
    future = ["tests/validators/test_9.py", "tests/validators/test__future.py",
              "tests/validators/test_c.py", "tests/validators/test_co.py",
              "tests/validators/test_cz.py", "tests/validators/test_d.py", "tests/validators/test_o.py",
              "tests/validators/test_p.py", "tests/validators/test_z.py",
              "tests/validators/nested/test_future.py", "tests/e2e/nested/test_future.py",
              "tests/verification/test_future.py", "tests/workflows/test_future.py"]
    assert actual
    for relative in [*actual, *future]:
        assert sum(_profile_selects(command, relative.replace("/", separator), host) for command in commands) == 1, relative
