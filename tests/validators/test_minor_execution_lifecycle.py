"""Full private minor lifecycle using the original isolation fixtures."""
from __future__ import annotations

from .test_minor_execution_permission import (
    ExecutionMinor, LINK_CHECKER, SCRIPTS, SESSION, TOKEN, WORKFLOW_PATHS,
    _git, _isolated_git_config, _no_transport_overrides, _private_native_home,
    ck, cm, copy, json, ledger, section, subprocess, sys,
)


def test_four_native_rows_survive_real_private_prefix_archive_and_handoff(tmp_path, monkeypatch):
    """Minimal private plans qualify interfaces, never the real 149-task prefix."""
    fx = ExecutionMinor(tmp_path, monkeypatch)
    created = fx.create()
    assert created.returncode == 0, created.stdout + created.stderr

    def frozen_dependencies(version, text):
        if version == "v4.15.8":
            return text.replace('"depends_on": []', '"depends_on": ["v4.15.6", "v4.15.7"]', 1)
        return text

    fx.add_members(transform=frozen_dependencies)
    versions = [f"v4.15.{patch}" for patch in range(9)]
    gaps = fx.work / "docs/releases/v4/v4.15/known-gaps.md"
    gaps.parent.mkdir(parents=True, exist_ok=True)
    gaps.write_text(ledger(TOKEN, "".join(section(version, 0, "") for version in versions),
                           status="finalized", open_items=0), encoding="utf-8")
    fx.commit("private finalized empty gap register")
    fx.integrate()
    for version in versions[:5]:
        started = fx.publication(version)
        assert started.returncode == 0, started.stdout + started.stderr
        fx.released_fixture_member(version)
    for version in versions[5:8]:
        root = fx.worker(version)
        fx.grant(version)
        admitted = fx.admit(version, root)
        assert admitted.returncode == 0, admitted.stdout + admitted.stderr
        started = fx.publication(version, ["CHANGELOG.md"])
        assert started.returncode == 0, started.stdout + started.stderr
        fx.released_fixture_member(version, root)
        _, projected = fx.project(version)
        assert projected["predicates"]["implementation.identity"] == "met"

    version = "v4.15.8"
    root = fx.worker(version)
    admitted = fx.admit(version, root, sensitive=False, depends=("v4.15.6", "v4.15.7"))
    assert admitted.returncode == 0, admitted.stdout + admitted.stderr
    original_implementation = copy.deepcopy(fx.member(version)["implementation"])
    entry = fx.grant(version)
    assert entry["page"]["role"] == "coordinator"
    assert cm.execution_permission_paths(ck, fx.record(), fx.member(version), "coordinator") == []
    started = fx.publication(version, ["CHANGELOG.md", WORKFLOW_PATHS[0]])
    assert started.returncode == 0, started.stdout + started.stderr
    assert fx.member(version)["implementation"] == original_implementation
    assert cm.execution_permission_paths(ck, fx.record(), fx.member(version), "coordinator") == WORKFLOW_PATHS[:1]
    authorized = fx.run("record", "authorize", "--minor", TOKEN, "--session", SESSION,
                        "--member", version, "--approval-class", "ci-security-change", "--request",
                        json.dumps({"paths": WORKFLOW_PATHS[:1]}))
    assert authorized.returncode == 0, authorized.stdout + authorized.stderr
    assert "AUTHORIZED" in authorized.stdout
    (root / WORKFLOW_PATHS[0]).write_text("name: private activated coordinator\n", encoding="utf-8")
    _, projected = fx.project(version)
    assert projected["predicates"]["implementation.identity"] == "met"
    fx.released_fixture_member(version, root)
    history = copy.deepcopy(fx.record()["minor_execution_permissions"])
    assert len(history) == 4
    _git(fx.work, "checkout", "-q", "-b", "chore/close-v4.15", "origin/develop")
    archived = subprocess.run([sys.executable, str(SCRIPTS / "minor_close.py"), "archive", "--minor", TOKEN,
                              "--session", SESSION, "--apply", "--repo", str(fx.work),
                              "--link-checker", str(LINK_CHECKER)], cwd=fx.work, env=fx.env,
                              capture_output=True, text=True, check=False, timeout=210,
                              creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    assert archived.returncode == 0, archived.stdout + archived.stderr
    assert "ARCHIVED v4.15" in archived.stdout
    fx.integrate()
    assert fx.record()["minor_execution_permissions"] == history
    target = tmp_path / "continued-controller"
    _git(fx.work, "worktree", "add", "-q", "-b", "continued-controller", str(target), "origin/develop")
    current = fx.record()
    generation = (current.get("implementation_controller") or {}).get("generation", 0)
    transferred = fx.run("record", "controller-handoff", "--minor", TOKEN, "--session", SESSION,
                         "--repo", str(fx.work), "--to", str(target), "--head", _git(fx.work, "rev-parse", "HEAD"),
                         "--expected-generation", str(generation), "--apply")
    assert transferred.returncode == 0, transferred.stdout + transferred.stderr
    ctx, continued = ck.resolve_minor_controller(fx.record_path(), SESSION, minor_protocol=1, execution_protocol=1)
    assert ctx.root == target
    assert continued["minor_execution_permissions"] == history
    assert cm._verified(ck, ctx, TOKEN, continued, minor_protocol=1, execution_protocol=1)
