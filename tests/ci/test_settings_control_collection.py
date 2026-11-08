"""The settings engine's test root is collected on every operating system (v4.14.6 Phase 2, T015).

`scripts/ci/profiles.py` lists explicit test roots and has no catch-all, so a new
root that no step names runs on no host. This pins the one step that names it.
"""
from __future__ import annotations

import pytest

from scripts.ci import profiles

ROOT = "tests/settings_control"


def _commands(host: str) -> list[profiles.Command]:
    return [c for group in profiles.PROFILES["full"] for c in group.commands if c.runs_on(host)]


@pytest.mark.parametrize("host", ("linux", "macos", "windows"))
def test_the_full_profile_collects_the_settings_root_exactly_once(host: str) -> None:
    named = [c for c in _commands(host) if ROOT in c.argv]

    assert [c.name for c in named] == ["repo-tests-settings-control"]
    assert list(named[0].argv)[1:] == ["-m", "pytest", ROOT, "-q"]
    assert not named[0].advisory and not named[0].skip_if_missing and named[0].cwd == "."
    assert named[0].timeout_on(host) <= 3600


@pytest.mark.parametrize("host", ("linux", "macos", "windows"))
def test_no_ignore_glob_partition_can_drop_or_double_count_the_settings_root(host: str) -> None:
    """A partition selects only the roots it names, so none that uses --ignore-glob may name this root."""
    partitions = [c for c in _commands(host) if any(str(a).startswith("--ignore-glob") for a in c.argv)]

    assert partitions
    assert not [c.name for c in partitions if any(str(a).startswith(ROOT) for a in c.argv)]


def test_the_step_is_in_no_other_profile_with_a_different_shape() -> None:
    steps = [c for groups in profiles.PROFILES.values() for g in groups for c in g.commands if ROOT in c.argv]

    assert {c.name for c in steps} == {"repo-tests-settings-control"}
