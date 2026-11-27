"""A started member can receive a typed execution grant through the same genuine capture (v4.15.6).

v4.15.7 was admitted without its workflow paths and then could not be granted them: the route
refused every started member. The started route accepts only the admitted worker, clean, for
literal paths that the member's own plan lists in its claims `write_paths`; the capture, seal and
HMAC are the existing ones. The pre-start route is unchanged.
"""

from __future__ import annotations

from .test_minor_execution_permission import (
    SESSION,
    TOKEN,
    ExecutionMinor,
    _declared_execution_members,
    _isolated_git_config,
    _no_transport_overrides,
    _private_native_home,
    ck,
    cm,
    execution,
)

AUTOUSE_FIXTURES = (
    _declared_execution_members,
    _isolated_git_config,
    _no_transport_overrides,
    _private_native_home,
    execution,
)
STARTED = "v4.15.7"


def _render(fx, version=STARTED):
    return fx.render(
        SESSION,
        "--action",
        "permit-member-execution-paths",
        "--member",
        version,
        "--execution",
        str(fx.request(version)),
    )


def _started(fx):
    worker = fx.worker(STARTED)
    admitted = fx.admit(STARTED, worker, sensitive=False)
    assert admitted.returncode == 0, admitted.stdout + admitted.stderr
    assert fx.member(STARTED)["implementation"] is not None
    return worker


def test_clean_started_member_receives_listed_paths_through_capture(execution):
    fx = execution
    _started(fx)
    entry = fx.grant(STARTED)
    assert entry["page"]["role"] == "implementation"
    assert entry["page"]["write_paths"] == sorted(fx.paths(STARTED))
    assert entry["accepted"]["authorization_context"]["origin"] == "host-hook-capture"
    member = fx.member(STARTED)
    assert (
        entry["page"]["worker_identity"]["worktree"]
        == member["implementation"]["worktree"]
    )
    assert cm._permitted_implementation_writes(ck, fx.record(), member) == sorted(
        fx.paths(STARTED)
    )


def test_dirty_started_worker_is_refused_without_mutation(execution):
    fx = execution
    worker = _started(fx)
    (worker / "scratch.txt").write_text("uncommitted\n", encoding="utf-8")
    before = fx.record_path().read_bytes()
    refused = _render(fx)
    assert refused.returncode != 0
    assert "minor-execution-started-worker-dirty" in refused.stdout + refused.stderr
    assert fx.record_path().read_bytes() == before


def test_path_missing_from_plan_write_paths_is_refused(tmp_path, monkeypatch):
    def drop_precommit(version, text):
        if version != STARTED:
            return text
        text = text.replace(', ".pre-commit-config.yaml"]', "]", 1)
        return (
            text
            + "\nThe pre-commit file .pre-commit-config.yaml is named here, not claimed.\n"
        )

    fx = ExecutionMinor(tmp_path, monkeypatch)
    assert fx.create().returncode == 0
    fx.original = fx.record()
    fx.add_members(transform=drop_precommit)
    _started(fx)
    before = fx.record_path().read_bytes()
    refused = _render(fx)
    assert refused.returncode != 0
    assert (
        "minor-execution-path-outside-plan-write-paths"
        in refused.stdout + refused.stderr
    )
    assert fx.record_path().read_bytes() == before


def test_unstarted_dirty_worker_keeps_the_original_refusal(execution):
    fx = execution
    worker = fx.worker(STARTED)
    (worker / "scratch.txt").write_text("uncommitted\n", encoding="utf-8")
    refused = _render(fx)
    assert refused.returncode != 0
    assert (
        "minor-execution-worker-already-started-or-dirty"
        in refused.stdout + refused.stderr
    )
    assert TOKEN == "v4.15"
