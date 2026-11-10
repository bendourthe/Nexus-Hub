"""History and consumer checks using the original private fixtures."""
from __future__ import annotations

from .test_minor_execution_permission import (
    EXECUTION_CONSUMER_PROBE, OLD_EXECUTION_CONSUMER_PROBE,
    Path, REGISTRY, SCRIPTS, SESSION, SETTINGS, TOKEN, WORKFLOW_PATHS,
    _git, _isolated_git_config, _no_transport_overrides, _private_native_home,
    _unchanged_snapshot, add_registration, ck, cm, copy, execution,
    execution_baseline_scripts, execution_discovery, hashlib, hmac, json,
    os, pytest, shutil, subprocess, sys,
)


def test_original_signing_payload_remains_byte_compatible(execution, execution_baseline_scripts):
    record = execution.original
    assert "minor_execution_format" not in record
    assert "minor_execution_permissions" not in record
    payload = {key: record.get(key) for key in ck._SIGNED_FIELDS + ck._SIGNED_MINOR_FIELDS}
    expected = hmac.new(ck._secret(create=False), ck._canonical(payload), hashlib.sha256).hexdigest()
    assert record["approvals_hmac"] == expected
    assert ck._sign(record, ck._secret(create=False)) == expected
    probe = execution_baseline_scripts / "unextended_signer_probe.py"
    probe.write_text("import json,sys\nimport check_plan_completion as ck\n"
                     "print(ck._sign(json.loads(sys.stdin.read()),ck._secret(create=False),minor_protocol=1))\n",
                     encoding="utf-8")
    env = {**execution.env, "PYTHONDONTWRITEBYTECODE": "1"}
    env.pop("PYTHONPATH", None)
    original = subprocess.run([sys.executable, str(probe)], input=json.dumps(record), cwd=execution.work,
                              env=env, capture_output=True, text=True, check=False, timeout=90,
                              creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    assert original.returncode == 0, original.stderr
    assert original.stdout.strip() == record["approvals_hmac"]


def test_new_permission_protocol_is_explicit_and_legacy_cannot_resign(execution):
    version = "v4.15.7"
    execution.worker(version)
    execution.grant(version)
    record = execution.record()
    assert record["minor_execution_format"] == 1
    with pytest.raises(ck.MinorConflict):
        ck._sign(record, ck._secret(create=False), minor_protocol=1)
    assert not cm._verified(ck, execution.rctx(), TOKEN, record, minor_protocol=1)
    assert cm._verified(ck, execution.rctx(), TOKEN, record, minor_protocol=1, execution_protocol=1)


@pytest.mark.parametrize("version", ["v4.15.5", "v4.15.7"])
def test_captured_execution_page_refuses_changed_bound_context(execution, version):
    root = execution.worker(version)
    request = execution.request(version)
    rendered = execution.render(SESSION, "--action", "permit-member-execution-paths", "--member", version,
                                "--execution", str(request))
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    execution.capture(SESSION, rendered.stdout.splitlines()[0])
    original = execution.record_path().read_bytes()
    private_capture = {path: path.read_bytes() for path in execution.runs.rglob("*") if path.is_file()}
    worker_head = _git(root, "rev-parse", "HEAD")
    worker_branch = _git(root, "branch", "--show-current")
    controller_head = _git(execution.work, "rev-parse", "HEAD")
    integration_head = _git(execution.work, "rev-parse", "origin/develop")
    plan = execution.work / execution.member(version)["plan_path"]
    plan_bytes, request_bytes = plan.read_bytes(), request.read_bytes()
    changes = ["worker-head", "worker-branch", "integration-head", "plan", "resumed-session"]
    if version == "v4.15.7":
        changes.append("request-paths")
    for change in changes:
        session = SESSION
        try:
            if change == "worker-head":
                _git(root, "commit", "-q", "--allow-empty", "-m", "private changed worker identity")
            elif change == "worker-branch":
                _git(root, "checkout", "-q", "-b", "private-changed-execution-branch")
            elif change == "integration-head":
                _git(execution.work, "commit", "-q", "--allow-empty", "-m", "private changed integration identity")
                execution.integrate()
            elif change == "plan":
                plan.write_bytes(plan_bytes + b"\nBound plan change after rendering.\n")
            elif change == "request-paths":
                request.write_text(json.dumps({"write_paths": WORKFLOW_PATHS[:1]}), encoding="utf-8")
            else:
                session = "execution-bound-context-resume"
                execution.paste(session, "--action", "resume")
                resumed = execution.run("record", "resume", "--minor", TOKEN, "--session", session)
                assert resumed.returncode == 0, resumed.stdout + resumed.stderr
            expected = execution.record_path().read_bytes()
            denied = execution.run("record", "permit-member-execution-paths", "--minor", TOKEN,
                                   "--session", session, "--member", version, "--execution", str(request))
            assert denied.returncode != 0, change
            assert "Traceback" not in denied.stdout + denied.stderr
            assert execution.record_path().read_bytes() == expected, change
        finally:
            # These are exact disposable fixture snapshots, never live records.
            _git(root, "checkout", "-q", worker_branch)
            _git(root, "reset", "--hard", "-q", worker_head)
            plan.write_bytes(plan_bytes)
            request.write_bytes(request_bytes)
            _git(execution.work, "reset", "--hard", "-q", controller_head)
            _git(execution.work, "branch", "-f", "develop", integration_head)
            _git(execution.remote, "update-ref", "refs/heads/develop", integration_head)
            _git(execution.work, "update-ref", "refs/remotes/origin/develop", integration_head)
            for path, raw in private_capture.items():
                path.write_bytes(raw)
    assert execution.record_path().read_bytes() == original
    accepted = execution.run("record", "permit-member-execution-paths", "--minor", TOKEN, "--session", SESSION,
                             "--member", version, "--execution", str(request))
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    assert len(execution.record()["minor_execution_permissions"]) == 1


def test_native_ownership_checks_refuse_changed_private_snapshot(execution, monkeypatch, capsys):
    other_minor, other_session = "v4.16", "private-distinct-minor-owner"
    other_plan = execution.work / "docs/releases/v4/v4.16/plans/v4.16.0-other-native-authority.md"
    other_plan.parent.mkdir(parents=True, exist_ok=True)
    other_plan.write_text("# Plan - Other Native Authority\n\n**Version**: v4.16.0\n**Slug**: other-native-authority\n"
                          "**Status**: queued\n\n## Phase 1: Build\n\n- [ ] T001 Build src/other-native-authority.txt\n",
                          encoding="utf-8")
    execution.commit("integrate private nonoverlapping authority plan")
    execution.integrate()
    approvals = execution.approvals()
    execution.capture(other_session, "/implement v4.16", at=0.0)
    page = execution.run("record", "render", "--minor", other_minor, "--session", other_session,
                         "--approvals", str(approvals))
    assert page.returncode == 0, page.stdout + page.stderr
    execution.capture(other_session, page.stdout.splitlines()[0])
    created = execution.run("record", "create", "--minor", other_minor, "--session", other_session,
                            "--approvals", str(approvals))
    assert created.returncode == 0, created.stdout + created.stderr
    other = cm.load_minor(ck, execution.rctx(), other_minor, other_session, minor_protocol=1, execution_protocol=1)
    assert other.forced is None and other.record is not None and not other.record.get("completed")
    other_path = execution.rctx().scoped_record_path("minor:" + other_minor)
    other_original = other_path.read_bytes()
    execution.worker("v4.15.7")
    execution.grant("v4.15.7")
    path = execution.record_path()
    original = path.read_bytes()
    alternate = execution.runs / "alternate-authentic-owner.json"
    renamed = execution.runs / "renamed-distinct-native-owner.json"
    real = cm.ownership
    baseline_calls = []

    def observing(*args, **kwargs):
        reason = real(*args, **kwargs)
        baseline_calls.append(reason)
        return reason

    with monkeypatch.context() as patch:
        patch.chdir(execution.work)
        patch.setattr(cm, "ownership", observing)
        capsys.readouterr()
        ck.main(["check-minor", TOKEN, "--session", SESSION, "--json"])
        baseline_output = capsys.readouterr()
    assert baseline_calls and baseline_calls[0] is None
    assert "owned-by-another-run" not in baseline_output.out
    assert "record.provenance" not in baseline_output.out
    assert path.read_bytes() == original and other_path.read_bytes() == other_original
    # Record byte changes repeat on every ownership call, so each bounded retry sees fresh drift and
    # the refusal must survive them all; "own-bytes-once" drifts a single time and the retry absorbs
    # it. An identical second owner, a rename, or a removal is planted once and refused directly.
    for change in ("own-bytes", "alternate-owner", "existing-owner-bytes", "own-bytes-once", "owner-rename", "owner-remove"):
        calls = []
        contexts = []
        git_before = _unchanged_snapshot(execution)[1:]

        def changing(*args, **kwargs):
            reason = real(*args, **kwargs)
            calls.append(reason)
            contexts.append(args[1])
            drift = b"\n" * len(calls)
            if change == "own-bytes":
                path.write_bytes(original + drift)
            elif change == "alternate-owner":
                if len(calls) == 1:
                    alternate.write_bytes(original)
            elif change == "existing-owner-bytes":
                other_path.write_bytes(other_original + drift)
            elif len(calls) == 1:
                if change == "own-bytes-once":
                    path.write_bytes(original + b"\n")
                elif change == "owner-rename":
                    other_path.rename(renamed)
                else:
                    other_path.unlink()
            return reason

        try:
            with monkeypatch.context() as patch:
                patch.chdir(execution.work)
                patch.setattr(cm, "ownership", changing)
                capsys.readouterr()
                result = ck.main(["check-minor", TOKEN, "--session", SESSION, "--json"])
                observed = capsys.readouterr()
            assert calls and calls[0] is None, change
            assert contexts[0].budget.remaining() > 0, change
            if change in {"owner-rename", "owner-remove"}:
                # A vanished candidate is wrapped by minor_candidates before the
                # outer observation boundary; the public CLI blocks explicitly.
                assert result == ck.EXIT_BLOCKED, (change, observed.out, observed.err)
                assert observed.out.strip() == "BLOCKED: controller-ownership-unavailable", change
            elif change == "own-bytes-once":
                assert len(calls) >= 2, change
                assert result == ck.EXIT_INCOMPLETE, (change, observed.out, observed.err)
                assert "record.provenance" not in observed.out, (change, observed.out, observed.err)
            elif change == "alternate-owner":
                # The planted duplicate is drift on the first decision; the retry then sees it as a
                # stable second owner and the candidate scan refuses it before ownership runs again.
                assert result == ck.EXIT_BLOCKED, (change, observed.out, observed.err)
                assert observed.out.strip() == "BLOCKED: controller-origin-or-common-dir-mismatch", change
            else:
                assert len(calls) >= len(cm._OWNERSHIP_RETRY_DELAYS) + 1, (change, len(calls))
                assert result == ck.EXIT_INCOMPLETE, (change, observed.out, observed.err)
                assert "record.provenance" in observed.out, (change, observed.out, observed.err)
            assert "Traceback" not in observed.out + observed.err
            own_drift = {"own-bytes": b"\n" * len(calls), "own-bytes-once": b"\n"}.get(change, b"")
            assert path.read_bytes() == original + own_drift
            assert _unchanged_snapshot(execution)[1:] == git_before
            if change == "existing-owner-bytes":
                assert other_path.read_bytes() == other_original + b"\n" * len(calls)
            elif change == "owner-rename":
                assert not other_path.exists() and renamed.read_bytes() == other_original
            elif change == "owner-remove":
                assert not other_path.exists()
            else:
                assert other_path.read_bytes() == other_original
        finally:
            path.write_bytes(original)
            other_path.write_bytes(other_original)
            alternate.unlink(missing_ok=True)
            renamed.unlink(missing_ok=True)


def test_native_writer_rejects_permission_history_mutation(execution):
    version = "v4.15.7"
    execution.worker(version)
    execution.grant(version)
    before = execution.record_path().read_bytes()
    changes = ("remove-format", "remove-history", "remove-entry", "mutate-path", "change-member", "change-role", "bool-format", "unknown-kind")
    for change in changes:
        value = cm.load_minor(ck, execution.rctx(), TOKEN, SESSION, minor_protocol=1, execution_protocol=1).record
        if change == "remove-format":
            value.pop("minor_execution_format")
        elif change == "remove-history":
            value.pop("minor_execution_permissions")
        elif change == "remove-entry":
            value["minor_execution_permissions"].clear()
        elif change == "mutate-path":
            value["minor_execution_permissions"][0]["page"]["write_paths"].append(WORKFLOW_PATHS[2])
        elif change == "change-member":
            value["minor_execution_permissions"][0]["page"]["member"] = "v4.15.8"
        elif change == "change-role":
            value["minor_execution_permissions"][0]["page"]["role"] = "coordinator"
        elif change == "bool-format":
            value["minor_execution_format"] = True
        else:
            value["minor_execution_permissions"][0]["page"]["capability_kind"] = "unknown"
        with pytest.raises(ck.MinorConflict):
            value["approvals_hmac"] = ck._sign(value, ck._secret(create=False), minor_protocol=1, execution_protocol=1)
            ck._write_record(execution.record_path(), value)
        assert execution.record_path().read_bytes() == before, change
    stale = cm.load_minor(ck, execution.rctx(), TOKEN, SESSION, minor_protocol=1, execution_protocol=1).record
    changed = before + b"\n"
    execution.record_path().write_bytes(changed)
    try:
        with pytest.raises(ck.MinorConflict, match="minor-record-changed"):
            ck._write_record(execution.record_path(), stale)
        assert execution.record_path().read_bytes() == changed
    finally:
        execution.record_path().write_bytes(before)


def test_refreshed_integration_settings_are_not_misattributed_to_worker(execution):
    version = "v4.15.5"
    root = execution.worker(version)
    entry = execution.grant(version)
    assert execution.admit(version, root).returncode == 0
    inherited = copy.deepcopy(SETTINGS)
    inherited["model"] = "legitimate-integration-model"
    inherited["hooks"]["PreToolUse"].append({"matcher": "Write", "hooks": [
        {"type": "command", "command": "bash .claude/hooks/inherited-write-guard.sh"}]})
    (execution.work / REGISTRY).write_text(json.dumps(inherited), encoding="utf-8")
    execution.commit("private independent integration update")
    execution.integrate()
    _git(root, "merge", "-q", "--no-ff", "-m", "refresh private integration", "origin/develop")
    add_registration(root, version)
    _git(root, "add", "--", REGISTRY)
    _git(root, "commit", "-q", "-m", "private allowed registration after refresh")
    _, body = execution.project(version)
    assert body["predicates"]["implementation.identity"] == "met"
    assert execution.record()["minor_execution_permissions"] == [entry]


@pytest.mark.parametrize("change", ["bytes", "completed-to-live", "create", "remove", "rename"])
def test_execution_discovery_refuses_between_member_record_or_owner_changes(execution_discovery, change):
    ctx, paths = execution_discovery
    with pytest.raises(cm.ObservationUnavailable, match="record.provenance"):
        with cm._execution_ownership_reader(ck, ctx) as (observed, read, common):
            assert observed == paths and common
            assert read(paths[0])["value"] == 0
            # Mutate after the first real record read, as a later member is inspected.
            if change == "bytes":
                paths[1].write_text('{"schema":1,"value":"changed"}', encoding="utf-8")
                read(paths[1])
            elif change == "completed-to-live":
                paths[0].write_text('{"schema":1,"state":"active","value":0}', encoding="utf-8")
            elif change == "create":
                (paths[0].parent / "alternate-owner.json").write_text('{"schema":1}', encoding="utf-8")
            elif change == "remove":
                paths[1].unlink()
            else:
                paths[1].rename(paths[1].with_name("renamed-owner.json"))


def test_execution_discovery_closes_reader_and_refreshes_next_operation(execution_discovery):
    ctx, paths = execution_discovery
    with cm._execution_ownership_reader(ck, ctx) as (_, first, _):
        assert first(paths[0])["value"] == 0
    with pytest.raises(cm.ObservationUnavailable, match="record.provenance"):
        first(paths[0])
    paths[0].write_text('{"schema":1,"state":"active","value":"fresh"}', encoding="utf-8")
    with cm._execution_ownership_reader(ck, ctx) as (_, second, _):
        assert second(paths[0])["value"] == "fresh"
        with pytest.raises(cm.ObservationUnavailable, match="record.provenance"):
            first(paths[0])


def test_execution_discovery_preserves_git_provenance_change_refusal(execution_discovery):
    ctx, paths = execution_discovery
    # Keep the store inside Git so a newly tracked record changes provenance.
    nested = ctx.root / "records"
    shutil.move(str(paths[0].parent), nested)
    paths = [nested / path.name for path in paths]
    os.environ["NEXUS_HUB_RUNS_DIR"] = str(nested)
    with pytest.raises(cm.ObservationUnavailable, match="record.provenance"):
        with cm._execution_ownership_reader(ck, ctx) as (_, read, _):
            assert read(paths[0])["value"] == 0
            _git(ctx.root, "add", "--", str(paths[0].relative_to(ctx.root)))


def test_execution_discovery_ignores_non_authority_gate_heartbeat(execution_discovery):
    ctx, paths = execution_discovery
    heartbeat = paths[0].parent / "private.gate.json"
    with cm._execution_ownership_reader(ck, ctx) as (observed, read, _):
        assert observed == paths
        assert read(paths[0])["value"] == 0
        heartbeat.write_text('{"heartbeat":"new"}', encoding="utf-8")
    with cm._execution_ownership_reader(ck, ctx) as (observed, read, _):
        assert observed == paths
        assert read(paths[1])["value"] == 1
        heartbeat.write_text('{"heartbeat":"changed"}', encoding="utf-8")


def test_execution_discovery_nested_reader_has_separate_lifetime(execution_discovery):
    ctx, paths = execution_discovery
    with cm._execution_ownership_reader(ck, ctx) as (_, outer, _):
        assert outer(paths[0])["value"] == 0
        other = ck.RepoContext(ctx.root, ck.Budget(20))
        with cm._execution_ownership_reader(ck, other) as (_, inner, _):
            assert inner(paths[1])["value"] == 1
        with pytest.raises(cm.ObservationUnavailable, match="record.provenance"):
            inner(paths[0])
        assert outer(paths[0])["value"] == 0


def test_execution_discovery_refuses_changed_linked_controller_common_dir(execution_discovery, tmp_path):
    ctx, paths = execution_discovery
    _git(ctx.root, "config", "user.name", "Test")
    _git(ctx.root, "config", "user.email", "t@example.invalid")
    (ctx.root / "seed.txt").write_text("private seed\n", encoding="utf-8")
    _git(ctx.root, "add", "seed.txt")
    _git(ctx.root, "commit", "-q", "-m", "private discovery seed")
    linked = tmp_path / "linked-controller"
    alternate = tmp_path / "alternate-controller"
    _git(ctx.root, "worktree", "add", "-q", "-b", "private-linked", str(linked))
    alternate.mkdir()
    _git(alternate, "init", "-q")
    pointer = linked / ".git"
    original = pointer.read_bytes()
    attributes = None
    if os.name == "nt":
        import ctypes
        attributes = ctypes.windll.kernel32.GetFileAttributesW(str(pointer))
        assert attributes != 0xFFFFFFFF
        assert ctypes.windll.kernel32.SetFileAttributesW(str(pointer), attributes & ~3)
    try:
        with pytest.raises(cm.ObservationUnavailable, match="record.provenance"):
            with cm._execution_ownership_reader(ck, ck.RepoContext(linked, ck.Budget(20))) as (_, read, _):
                assert read(paths[0])["value"] == 0
                pointer.write_text("gitdir: " + str(alternate / ".git") + "\n", encoding="utf-8")
    finally:
        pointer.write_bytes(original)
        if attributes is not None:
            assert ctypes.windll.kernel32.SetFileAttributesW(str(pointer), attributes)


@pytest.mark.parametrize("version", ["v4.15.5", "v4.15.7"])
def test_complete_current_consumers_and_captured_resume_preserve_typed_history(execution, version):
    execution.worker(version)
    entry = execution.grant(version)
    installed = Path(execution.env["NEXUS_HUB_HOME"]) / "scripts"
    shutil.copytree(SCRIPTS, installed, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    probe = installed / "execution_consumer_probe.py"
    probe.write_text(EXECUTION_CONSUMER_PROBE, encoding="utf-8")
    env = {**execution.env, "PYTHONDONTWRITEBYTECODE": "1"}
    env.pop("PYTHONPATH", None)

    def observed_readers(session):
        before = _unchanged_snapshot(execution)
        result = subprocess.run([sys.executable, str(probe), str(execution.record_path()), session],
                                cwd=execution.work, env=env, capture_output=True, text=True,
                                check=False, timeout=90, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        assert result.returncode == 0, result.stdout + result.stderr
        observed = json.loads(result.stdout)
        assert observed["readers"] == ["runner", "gate", "cleanup", "archive"]
        assert observed["history"] == [entry]
        assert _unchanged_snapshot(execution) == before

    observed_readers(SESSION)
    other = "execution-resume-session"
    before = execution.record_path().read_bytes()
    refused = execution.run("record", "resume", "--minor", TOKEN, "--session", other)
    assert refused.returncode != 0
    assert execution.record_path().read_bytes() == before
    execution.paste(other, "--action", "resume")
    resumed = execution.run("record", "resume", "--minor", TOKEN, "--session", other)
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    assert execution.record()["minor_execution_permissions"] == [entry]
    observed_readers(other)


@pytest.mark.parametrize("version", ["v4.15.5", "v4.15.7"])
def test_old_and_mixed_bundles_refuse_before_record_or_git_mutation(execution, execution_baseline_scripts, tmp_path, version):
    execution.worker(version)
    execution.grant(version)
    env = {**execution.env, "PYTHONDONTWRITEBYTECODE": "1"}
    env.pop("PYTHONPATH", None)
    for mix in ("old", "new-checker-only", "new-minor-only", "old-archive"):
        bundle = tmp_path / ("mixed-" + mix)
        shutil.copytree(execution_baseline_scripts, bundle)
        names = (["check_plan_completion.py"] if mix == "new-checker-only" else
                 ["completion_minor.py"] if mix == "new-minor-only" else
                 ["check_plan_completion.py", "completion_minor.py", "approval_page.py"] if mix == "old-archive" else [])
        for name in names:
            shutil.copyfile(SCRIPTS / name, bundle / name)
        before = _unchanged_snapshot(execution)
        command = ([sys.executable, str(bundle / "minor_close.py"), "archive", "--minor", TOKEN,
                    "--session", SESSION, "--apply", "--repo", str(execution.work)] if mix == "old-archive" else
                   [sys.executable, str(bundle / "check_plan_completion.py"), "record", "pause",
                    "--minor", TOKEN, "--session", SESSION])
        result = subprocess.run(command, cwd=execution.work, env=env, capture_output=True, text=True,
                                check=False, timeout=90, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        assert result.returncode != 0, result.stdout + result.stderr
        assert "ModuleNotFoundError" not in result.stderr and "SyntaxError" not in result.stderr
        assert "Traceback" not in result.stderr
        assert any(word in (result.stdout + result.stderr).lower() for word in ("execution", "protocol", "tampered"))
        assert _unchanged_snapshot(execution) == before
    for reader in ("run_plan.py", "completion_gate.py", "cleanup_merged.py", "minor_close.py"):
        home = tmp_path / ("old-reader-" + reader.replace(".py", ""))
        bundle = home / ".nexus-hub" / "scripts"
        shutil.copytree(SCRIPTS, bundle, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copyfile(execution_baseline_scripts / reader, bundle / reader)
        probe = bundle / "old_execution_consumer_probe.py"
        probe.write_text(OLD_EXECUTION_CONSUMER_PROBE, encoding="utf-8")
        old_env = {**env, "HOME": str(home), "USERPROFILE": str(home), "NEXUS_HUB_HOME": str(home / ".nexus-hub")}
        before = _unchanged_snapshot(execution)
        refused = subprocess.run([sys.executable, str(probe), str(execution.record_path()), SESSION, reader],
                                 cwd=execution.work, env=old_env, capture_output=True, text=True,
                                 check=False, timeout=90, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        assert refused.returncode == 3, refused.stdout + refused.stderr
        assert "CONTROLLED REFUSAL" in refused.stdout
        if reader in {"cleanup_merged.py", "minor_close.py"}:
            assert "minor-execution-protocol-required" in refused.stdout + refused.stderr
        assert "Traceback" not in refused.stderr
        assert _unchanged_snapshot(execution) == before
