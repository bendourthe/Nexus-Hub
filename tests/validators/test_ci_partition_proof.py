"""Prove by collection that CI shards neither drop nor duplicate a test.

Each case below is a root that CI runs as several shard commands. The proof asks
pytest itself: the node IDs collected by every shard must be pairwise disjoint,
and their union must equal what one unsharded run of the same roots collects. No
snapshot is frozen, so the proof holds as tests are added.

The test runs on the host that executes it, so the Linux family is proven by the
Linux governance shard and the Windows family by a Windows validator shard.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from collections.abc import Sequence
from functools import cache
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.ci.profiles import PROFILES, Command  # noqa: E402

HOST = "windows" if os.name == "nt" else "linux"
HOOKS = ("catalog/hooks/tests",)
VALIDATORS = ("tests/validators",)
#: The pre-split `repo-tests-governance` roots, which Linux runs as several shards.
GOVERNANCE = (
    "tests/e2e",
    "tests/validators",
    "tests/verification",
    "tests/workflows",
    "tests/test_git_attribution.py",
    "tests/test_removed_autonomy_surface.py",
)
NODE_ID = re.compile(r"^\S+\.py(::\S.*)?$")


def _commands(profile: str, group_prefix: str, command_prefix: str) -> list[Command]:
    """Pytest commands of the groups (or family) with this prefix that run on this host."""
    found = [
        command
        for group in PROFILES[profile]
        if group.name.startswith(group_prefix) or group.family == group_prefix
        for command in group.commands
        if command.runs_on(HOST) and "pytest" in command.argv and command.name.startswith(command_prefix)
    ]
    assert found, f"no pytest command for {group_prefix}/{command_prefix} on {HOST}"
    return found


def _collect(argv: Sequence[str], env: dict[str, str], cwd: str = ".") -> set[str]:
    """Node IDs a pytest argv collects, with run-only options dropped."""
    kept: list[str] = []
    skip_next = False
    for arg in argv[argv.index("pytest") + 1 :]:
        if skip_next:
            skip_next = False
        elif arg in ("-q", "-o"):
            skip_next = arg == "-o"
        elif not arg.startswith(("--cov", "--junitxml")):
            kept.append(arg)
    # PYTEST_ADDOPTS from CI (xdist workers) would change what `--collect-only` prints.
    full_env = {**os.environ, **env, "PYTEST_ADDOPTS": ""}
    proc = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", *kept, "--collect-only", "-q", "-p", "no:cacheprovider"],
        cwd=REPO_ROOT / cwd,
        env=full_env,
        capture_output=True,
        text=True,
        timeout=1200,
        check=False,
    )
    assert proc.returncode == 0, f"collection failed for {kept}: {proc.stdout[-800:]} {proc.stderr[-800:]}"
    return {line.strip() for line in proc.stdout.splitlines() if NODE_ID.match(line.strip())}


@cache
def _unsharded(roots: tuple[str, ...]) -> frozenset[str]:
    return frozenset(_collect(["pytest", *roots], {}))


def assert_partition(shards: dict[str, set[str]], whole: frozenset[str]) -> None:
    """Shards are pairwise disjoint and their union is exactly `whole`."""
    assert whole, "the unsharded collection is empty, so the proof would be vacuous"
    names = list(shards)
    for i, first in enumerate(names):
        assert shards[first], f"shard {first} collected nothing (pytest exit 5 fails CI)"
        for second in names[i + 1 :]:
            overlap = shards[first] & shards[second]
            assert not overlap, f"{first} and {second} both run {sorted(overlap)[:3]}"
    union = set().union(*shards.values())
    assert not whole - union, f"no shard runs {sorted(whole - union)[:3]} ({len(whole - union)} total)"
    assert not union - whole, f"shards collect {sorted(union - whole)[:3]} that the roots do not"


def _prove(profile: str, group_prefix: str, command_prefix: str, roots: tuple[str, ...]) -> None:
    commands = _commands(profile, group_prefix, command_prefix)
    shards = {c.name: _collect(c.argv, dict(c.env), c.cwd) for c in commands}
    assert_partition(shards, _unsharded(roots))


def test_linux_hook_shards_partition_the_hook_suite() -> None:
    if HOST != "linux":
        pytest.skip("the Linux hook shards run on Linux; the Windows family is proven separately")
    _prove("full", "hook-tests", "hook-tests", HOOKS)


def test_governance_shards_partition_the_governance_roots() -> None:
    """Linux and macOS run two shards; the Windows `full` profile runs its own five."""
    _prove("full", "tests", "repo-tests-governance", GOVERNANCE)


def test_windows_hook_shards_partition_the_hook_suite() -> None:
    if HOST != "windows":
        pytest.skip("the Windows hook shards run on Windows")
    _prove("platform", "windows-hooks", "hook-tests", HOOKS)


def test_windows_validator_shards_partition_the_validator_suite() -> None:
    if HOST != "windows":
        pytest.skip("the Windows validator shards run on Windows")
    _prove("platform", "windows-validators", "validators", VALIDATORS)


# ---------------------------------------------------------------------------
# The workflow must run every shard, and the sharded jobs must stay least-privilege.
# ---------------------------------------------------------------------------

CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"
SHARDED_JOBS = ("tests", "tests-hooks", "tests-windows-hooks-rest", "tests-windows-validators-4")
SHA_PINNED = re.compile(r"@[0-9a-f]{40}(\s|$)")


def _workflow() -> dict:
    yaml = pytest.importorskip("yaml")
    return yaml.safe_load(CI.read_text(encoding="utf-8"))


@pytest.mark.parametrize(("job", "family", "extra"), [("tests", "tests", {"extension-tests"}), ("tests-hooks", "hook-tests", set())])
def test_matrix_legs_select_every_member_of_their_shard_family(job: str, family: str, extra: set[str]) -> None:
    """A shard missing from the matrix would never run, whatever the proof says."""
    legs = _workflow()["jobs"][job]["strategy"]["matrix"]["include"]
    selected = {name for leg in legs for name in leg["only"].split(",")}
    members = {g.name for g in PROFILES["full"] if g.family == family}
    assert members and selected == members | extra
    assert len({leg["shard"] for leg in legs}) == len(legs), "two legs would upload one artifact name"


@pytest.mark.parametrize("job", SHARDED_JOBS)
def test_sharded_jobs_pin_every_action_and_declare_no_permissions(job: str) -> None:
    workflow = _workflow()
    assert workflow["permissions"] == {"contents": "read"}
    body = workflow["jobs"][job]
    assert "permissions" not in body, f"{job} would widen the workflow's read-only token"
    uses = [step["uses"] for step in body["steps"] if "uses" in step]
    assert uses
    for line in uses:
        assert SHA_PINNED.search(line), f"{job} uses {line!r}, which is not pinned to a 40-hex commit"


def test_partition_proof_rejects_a_dropped_and_a_duplicated_test() -> None:
    """The proof fails open if it cannot see a misplacement, so show that it can."""
    whole = frozenset({"a.py::t1", "a.py::t2", "b.py::t1"})
    assert_partition({"x": {"a.py::t1", "a.py::t2"}, "y": {"b.py::t1"}}, whole)
    with pytest.raises(AssertionError, match="no shard runs"):
        assert_partition({"x": {"a.py::t1"}, "y": {"b.py::t1"}}, whole)
    with pytest.raises(AssertionError, match="both run"):
        assert_partition({"x": {"a.py::t1", "a.py::t2"}, "y": {"b.py::t1", "a.py::t2"}}, whole)
