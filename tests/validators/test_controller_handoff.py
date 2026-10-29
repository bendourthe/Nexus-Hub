"""Controller handoff regressions using private temporary run authority."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

from .test_completion_minor_record import Minor, SESSION, _git, ck, cm
from .test_completion_minor_record import _no_transport_overrides  # noqa: F401 - autouse fixture
from .test_check_plan_completion import _isolated_git_config  # noqa: F401 - autouse fixture
import minor_close
import run_plan


@pytest.fixture
def controller(tmp_path, monkeypatch, minor_git_seed):
    fixture = Minor(tmp_path, monkeypatch, minor_git_seed)
    permanent = fixture.work
    source = tmp_path / 'controller'
    _git(permanent, 'worktree', 'add', '-q', '-b', 'controller', str(source), 'develop')
    fixture.work = source
    created = fixture.create()
    assert created.returncode == 0, created.stdout + created.stderr
    path = fixture.record_path()
    return fixture, source, permanent, path


def handoff(fixture, source, target, *, apply=True, generation=0):
    head = _git(target, 'rev-parse', 'HEAD')
    args = ['record', 'controller-handoff', '--minor', 'v0.5', '--session', SESSION,
            '--repo', str(source), '--to', str(target), '--head', head,
            '--expected-generation', str(generation)]
    if apply:
        args.append('--apply')
    return subprocess.run([sys.executable, str(Path(ck.__file__).resolve()), *args],
        cwd=target, env=fixture.env, capture_output=True, text=True, timeout=90,
        check=False, **ck.NO_WINDOW)


def test_real_cli_dry_run_transfer_retry_and_source_removal(controller):
    fixture, source, target, path = controller
    before = path.read_bytes()
    record = json.loads(before)
    directory_before = {p.name: p.read_bytes() for p in path.parent.glob('*') if p.is_file()}
    preview = handoff(fixture, source, target, apply=False)
    assert preview.returncode == 0, preview.stdout + preview.stderr
    assert path.read_bytes() == before
    assert directory_before == {p.name: p.read_bytes() for p in path.parent.glob('*') if p.is_file()}
    applied = handoff(fixture, source, target)
    assert applied.returncode == 0, applied.stdout + applied.stderr
    after = path.read_bytes()
    moved = json.loads(after)
    assert moved['implementation_controller']['generation'] == 1
    assert moved['implementation_controller']['origin_record_key'] == path.stem
    assert {k: v for k, v in moved.items() if k not in ('implementation_controller', 'approvals_hmac')} == {
        k: v for k, v in record.items() if k not in ('implementation_controller', 'approvals_hmac')}
    assert cm.record_file(ck, ck.RepoContext(target, ck.Budget(60)), 'v0.5') == path
    retry = handoff(fixture, source, target)
    assert retry.returncode == 0, retry.stdout + retry.stderr
    assert path.read_bytes() == after
    refused = fixture.run('record', 'block', '--minor', 'v0.5', '--session', SESSION,
                          '--category', 'no-progress', '--evidence', 'old controller')
    assert refused.returncode != 0
    assert path.read_bytes() == after
    _git(target, 'worktree', 'remove', str(source))
    retry = handoff(fixture, source, target)
    assert retry.returncode == 0, retry.stdout + retry.stderr
    assert path.read_bytes() == after
    ctx, verified = ck.resolve_minor_controller(path, SESSION)
    assert isinstance(verified, ck.MinorSnapshot)
    assert verified.record_path == path.resolve()
    assert ctx.root == target
    assert verified['nonce'] == record['nonce']


# Each actual command wrapper must reject a stale snapshot before entering its body.
# W05 is separately tested at the actual common completion-stamp write boundary.
WRAPPED_WRITERS = [
    ('W02-answer', cm.cmd_record_answer),
    ('W03-pause', lambda module, args: cm.cmd_record_action(module, args, 'pause')),
    ('W04-resume', lambda module, args: cm.cmd_record_action(module, args, 'resume')),
    ('W06-member-start', cm.cmd_record_member_start),
    ('W07-implement-start', cm.cmd_record_member_implement_start),
    ('W08-block', cm.cmd_record_block),
    ('W09-archive', lambda _module, args: minor_close.cmd_archive(args)),
    ('W10-adopt', lambda _module, args: ck.cmd_record_adopt_policy(args)),
    ('W11-authorize', lambda _module, args: ck.cmd_record_authorize(args)),
    ('W12-resolve', lambda _module, args: ck.cmd_record_resolve(args)),
]


@pytest.mark.parametrize(('label', 'command'), WRAPPED_WRITERS, ids=[item[0] for item in WRAPPED_WRITERS])
def test_all_command_writers_refuse_snapshot_changed_before_lease(controller, monkeypatch, label, command):
    fixture, source, target, path = controller
    real_lease = ck.minor_lease
    applied_bytes = []
    prompts_before = {p.name: p.read_bytes() for p in (fixture.runs / 'prompts').glob('*')}
    used_before = {str(p.relative_to(fixture.runs)): p.read_bytes()
                   for p in fixture.runs.rglob('*') if p.is_file() and p.parent.name == 'consumed-prompts'}

    @contextmanager
    def race(path_arg, expected, ctx):
        if not applied_bytes:
            result = handoff(fixture, source, target)
            assert result.returncode == 0, result.stdout + result.stderr
            applied_bytes.append(path.read_bytes())
        with real_lease(path_arg, expected, ctx) as lease:
            yield lease

    monkeypatch.setattr(ck, 'minor_lease', race)
    args = argparse.Namespace(minor='v0.5', repo=str(source), session=SESSION, plan=None,
                              apply=True, member='v0.5.2')
    with pytest.raises(ck.MinorConflict, match='minor-record-changed'):
        command(ck, args)
    assert path.read_bytes() == applied_bytes[0]
    assert prompts_before == {p.name: p.read_bytes() for p in (fixture.runs / 'prompts').glob('*')}
    assert used_before == {str(p.relative_to(fixture.runs)): p.read_bytes()
                          for p in fixture.runs.rglob('*') if p.is_file() and p.parent.name == 'consumed-prompts'}
    assert not (source / 'docs/archives').exists(), label


def test_apply_revalidation_runs_on_its_own_budget(controller, monkeypatch):
    # --apply validates the target twice (before the lease and inside it). A large
    # minor's first pass can consume most of BUDGET_SECONDS; the second pass must not
    # inherit that spent budget and report member-history-cannot-verify.
    import time
    fixture, source, target, path = controller
    real = cm._handoff_target
    budgets = []

    def spending(module, source_ctx, record, target_root, head):
        budgets.append(source_ctx.budget)
        result = real(module, source_ctx, record, target_root, head)
        if len(budgets) == 1:
            source_ctx.budget.deadline = time.monotonic()  # pre-lease pass spent everything
        return result

    monkeypatch.setattr(cm, '_handoff_target', spending)
    args = argparse.Namespace(minor='v0.5', session=SESSION, repo=str(source), to=str(target),
                              head=_git(target, 'rev-parse', 'HEAD'), expected_generation=0, apply=True)
    assert cm.cmd_record_controller_handoff(ck, args) == 0
    assert len(budgets) == 2 and budgets[0] is not budgets[1]
    assert json.loads(path.read_bytes())['implementation_controller']['generation'] == 1


def test_stale_completion_stamp_cannot_replace_transfer(controller):
    fixture, source, target, path = controller
    stale = ck.read_record(fixture.rctx(), path)
    applied = handoff(fixture, source, target)
    assert applied.returncode == 0, applied.stdout + applied.stderr
    expected = path.read_bytes()
    stale['completed'] = {'at': ck._now(), 'head': _git(target, 'rev-parse', 'HEAD')}
    stale['approvals_hmac'] = ck._sign(stale, ck._secret(create=False))
    with pytest.raises(ck.MinorConflict, match='minor-record-changed'):
        ck._write_record(path, stale)
    assert path.read_bytes() == expected


def test_runner_start_interlock_preserves_original_adjacent_lock(controller, monkeypatch):
    fixture, source, target, path = controller
    monkeypatch.chdir(source)
    scope = run_plan.Scope('v0.5')
    record = ck.read_record(fixture.rctx(), path)
    with run_plan.controller_runner_lock(scope, path, record):
        refused = handoff(fixture, source, target)
        assert refused.returncode != 0
        assert 'runner-live' in refused.stdout
        assert path.with_name(path.stem + '.runner.lock').is_file()
    assert not path.with_name(path.stem + '.runner.lock').exists()
    applied = handoff(fixture, source, target)
    assert applied.returncode == 0, applied.stdout + applied.stderr


@pytest.mark.parametrize('failure', ['untracked', 'tracked', 'hidden-index', 'cleanup-bound'])
def test_target_refusal_is_no_change(controller, failure):
    fixture, source, target, path = controller
    if failure == 'untracked':
        (target / 'untracked.txt').write_text('user content', encoding='utf-8')
    elif failure == 'tracked':
        plan = target / 'docs/releases/v0/v0.5/plans/v0.5.2-alpha.md'
        plan.write_text(plan.read_text(encoding='utf-8') + '\nuser content\n', encoding='utf-8')
    elif failure == 'hidden-index':
        _git(target, 'update-index', '--assume-unchanged', 'docs/releases/v0/v0.5/plans/v0.5.2-alpha.md')
    else:
        record = fixture.record()
        record['members'][0]['approvals']['cleanup']['worktrees'] = [str(target)]
        fixture.write_record(record, resign=True)
    before = path.read_bytes()
    result = handoff(fixture, source, target)
    assert result.returncode != 0
    assert path.read_bytes() == before


def test_guard_process_exit_releases_os_lock_without_deleting_sidecar(controller):
    fixture, source, target, path = controller
    ready = fixture.tmp / 'guard-ready'
    script = fixture.tmp / 'hold_guard.py'
    script.write_text(
        'import sys,time\nfrom pathlib import Path\n'
        + 'sys.path.insert(0, ' + repr(str(Path(ck.__file__).parent)) + ')\n'
        + 'import check_plan_completion as ck\n'
        + 'ctx=ck.RepoContext(Path(' + repr(str(source)) + '),ck.Budget(30))\n'
        + 'record=ck.read_record(ctx,Path(' + repr(str(path)) + '))\n'
        + 'with ck.minor_transaction(record):\n'
        + ' Path(' + repr(str(ready)) + ').write_text("ready")\n'
        + ' time.sleep(20)\n', encoding='utf-8')
    process = subprocess.Popen([sys.executable, str(script)], cwd=target, env=fixture.env, **ck.NO_WINDOW)
    import time
    try:
        deadline = time.monotonic() + 10
        while not ready.is_file() and time.monotonic() < deadline:
            time.sleep(0.025)
        assert ready.is_file()
        refused = handoff(fixture, source, target)
        assert refused.returncode != 0
        assert 'minor-record-busy' in refused.stdout
    finally:
        process.kill()
        process.wait(timeout=5)
    assert path.with_name(path.stem + '.mutation.lock').is_file()
    result = handoff(fixture, source, target)
    assert result.returncode == 0, result.stdout + result.stderr



@pytest.fixture
def creation_rounds(tmp_path, monkeypatch, minor_git_seed):
    """Two real linked roots with genuine fixture create input prepared before any owner."""
    import approval_binding
    fixture = Minor(tmp_path, monkeypatch, minor_git_seed)
    permanent = fixture.work
    roots, rounds = [], []
    approvals = str(fixture.approvals())
    for index in (1, 2):
        root = tmp_path / f'creator-{index}'
        _git(permanent, 'worktree', 'add', '-q', '-b', f'creator-{index}', str(root), 'develop')
        fixture.work = root
        session = f'creator-session-{index}'
        fixture.paste(session, '--approvals', approvals)
        event = approval_binding.capture_events(fixture.runs, session)[-1]
        roots.append(root)
        rounds.append((session, event))
    return fixture, permanent, roots, rounds, approvals


def create_at(fixture, root, session, approvals):
    return subprocess.run([sys.executable, str(Path(ck.__file__).resolve()),
        'record', 'create', '--minor', 'v0.5', '--session', session,
        '--repo', str(root), '--approvals', approvals], cwd=root, env=fixture.env,
        capture_output=True, text=True, timeout=90, check=False, **ck.NO_WINDOW)


def test_competing_linked_root_initial_creations_leave_one_authority_and_one_unused_input(creation_rounds):
    import approval_binding
    import time
    fixture, _permanent, roots, rounds, approvals = creation_rounds
    script = fixture.tmp / 'race_creation.py'
    script.write_text(
        'import sys,time\nfrom pathlib import Path\nfrom contextlib import contextmanager\n'
        + 'sys.path.insert(0,' + repr(str(Path(ck.__file__).parent)) + ')\n'
        + 'import check_plan_completion as ck\n'
        + 'real=ck.minor_creation_lease\n'
        + '@contextmanager\ndef ready(ctx,token):\n'
        + ' Path(sys.argv[1]).write_text("ready")\n'
        + ' deadline=time.monotonic()+15\n'
        + ' while not Path(sys.argv[2]).exists():\n'
        + '  if time.monotonic()>deadline: raise RuntimeError("creation barrier timeout")\n'
        + '  time.sleep(0.025)\n'
        + ' with real(ctx,token): yield\n'
        + 'ck.minor_creation_lease=ready\n'
        + 'raise SystemExit(ck.main(sys.argv[3:]))\n', encoding='utf-8')
    go = fixture.tmp / 'create-go'
    processes, ready_files = [], []
    try:
        for index, (root, (session, _event)) in enumerate(zip(roots, rounds)):
            ready = fixture.tmp / f'create-ready-{index}'
            ready_files.append(ready)
            processes.append(subprocess.Popen([sys.executable, str(script), str(ready), str(go),
                'record', 'create', '--minor', 'v0.5', '--session', session,
                '--repo', str(root), '--approvals', approvals], cwd=root, env=fixture.env,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **ck.NO_WINDOW))
        deadline = time.monotonic() + 15
        while not all(path.exists() for path in ready_files) and time.monotonic() < deadline:
            time.sleep(0.025)
        assert all(path.exists() for path in ready_files)
        go.write_text('go', encoding='utf-8')
        outputs = [process.communicate(timeout=90) for process in processes]
        assert sum(process.returncode == 0 for process in processes) == 1, outputs
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
    records = []
    for path in fixture.runs.glob('*.json'):
        value = json.loads(path.read_text(encoding='utf-8'))
        if value.get('schema') == 2 and value.get('minor') == 'v0.5':
            records.append((path, value))
    assert len(records) == 1
    _, record = records[0]
    for session, event in rounds:
        assert approval_binding.event_available(fixture.runs, session, event) is (session != record['session_id'])
    locks = list((fixture.runs / 'creation-locks').glob('*.lock'))
    assert len(locks) == 1  # Same canonical common directory/scope, not per linked root.


def test_signed_absent_binding_legacy_owner_is_visible_from_sibling_before_create(creation_rounds):
    import approval_binding
    fixture, _permanent, roots, rounds, approvals = creation_rounds
    first = create_at(fixture, roots[0], rounds[0][0], approvals)
    assert first.returncode == 0, first.stdout + first.stderr
    first_ctx = ck.RepoContext(roots[0], ck.Budget(60))
    owner = cm.record_file(ck, first_ctx, 'v0.5')
    original = owner.read_bytes()
    assert 'implementation_controller' not in json.loads(original)
    sibling = ck.RepoContext(roots[1], ck.Budget(60))
    assert cm.minor_candidates(ck, sibling, 'v0.5', include_linked=True) == [owner]
    assert cm.other_minor_owns(ck, sibling, 'v0.5.2', None)
    second = create_at(fixture, roots[1], rounds[1][0], approvals)
    assert second.returncode != 0
    assert 'minor-authority-already-exists' in second.stdout
    assert owner.read_bytes() == original
    assert approval_binding.event_available(fixture.runs, rounds[1][0], rounds[1][1])
    assert not sibling.scoped_record_path('minor:v0.5').exists()


@pytest.mark.parametrize('error_type', [ck.MinorConflict, OSError])
def test_runner_acquisition_lease_exit_failure_releases_only_own_created_lock(tmp_path, monkeypatch, error_type):
    record_path = tmp_path / 'fixture.json'
    lock_path = record_path.with_name(record_path.stem + '.runner.lock')
    marker = error_type('injected lease exit failure')
    @contextmanager
    def failed(_record):
        yield
        raise marker
    monkeypatch.setattr(ck, 'minor_transaction', failed)
    with pytest.raises(run_plan.RunnerError, match='injected lease exit failure') as raised:
        with run_plan.controller_runner_lock(argparse.Namespace(minor=True), record_path, {}):
            pytest.fail('runner loop must not begin after lease failure')
    assert raised.value.__cause__ is marker
    assert not lock_path.exists()
    with run_plan.Lock(record_path):
        assert lock_path.is_file()
    assert not lock_path.exists()


def test_runner_failed_acquisition_preserves_replaced_same_pid_and_live_prior_lock(tmp_path, monkeypatch):
    import os
    record_path = tmp_path / 'fixture.json'
    lock_path = record_path.with_name(record_path.stem + '.runner.lock')
    saved = tmp_path / 'moved-original-lock'
    @contextmanager
    def replaced(_record):
        yield
        lock_path.rename(saved)
        lock_path.write_text(str(os.getpid()), encoding='ascii')
        raise ck.MinorConflict('injected replacement')
    monkeypatch.setattr(ck, 'minor_transaction', replaced)
    with pytest.raises(run_plan.RunnerError, match='injected replacement'):
        with run_plan.controller_runner_lock(argparse.Namespace(minor=True), record_path, {}):
            pytest.fail('runner loop must not begin')
    assert saved.is_file()
    assert lock_path.read_text(encoding='ascii') == str(os.getpid())
    prior = lock_path.read_bytes()
    @contextmanager
    def normal(_record):
        yield
    monkeypatch.setattr(ck, 'minor_transaction', normal)
    with pytest.raises(run_plan.RunnerError, match='another runner'):
        with run_plan.controller_runner_lock(argparse.Namespace(minor=True), record_path, {}):
            pytest.fail('live prior runner must be preserved')
    assert lock_path.read_bytes() == prior


def test_runner_lock_write_io_failure_cleans_its_exclusively_created_entry(tmp_path, monkeypatch):
    record_path = tmp_path / 'fixture.json'
    lock_path = record_path.with_name(record_path.stem + '.runner.lock')
    @contextmanager
    def normal(_record):
        yield
    def fail_write(_fd, _payload):
        raise OSError('injected runner lock write')
    monkeypatch.setattr(ck, 'minor_transaction', normal)
    with monkeypatch.context() as scoped:
        scoped.setattr(run_plan.os, 'write', fail_write)
        with pytest.raises(run_plan.RunnerError, match='injected runner lock write'):
            with run_plan.controller_runner_lock(argparse.Namespace(minor=True), record_path, {}):
                pytest.fail('runner loop must not begin')
    assert not lock_path.exists()



def test_staged_gate_and_runner_keep_original_record_after_controller_removal(controller):
    import shutil
    fixture, source, target, path = controller
    home = fixture.tmp / 'isolated-runtime-home'
    scripts = home / '.nexus-hub/scripts'
    scripts.mkdir(parents=True)
    for script in Path(ck.__file__).parent.glob('*.py'):
        shutil.copyfile(script, scripts / script.name)
    original = json.loads(path.read_bytes())
    result = handoff(fixture, source, target)
    assert result.returncode == 0, result.stdout + result.stderr
    transferred = path.read_bytes()
    _git(target, 'worktree', 'remove', str(source))
    python_name = Path(sys.executable).stem if os.name == 'nt' else Path(sys.executable).name
    env = {**fixture.env, 'HOME': str(home), 'USERPROFILE': str(home),
           'PATH': str(Path(sys.executable).parent) + os.pathsep + fixture.env.get('PATH', ''),
           'NEXUS_HUB_RUNS_DIR': str(fixture.runs), 'NEXUS_GATE_FORMAT': 'top-level-block',
           'NEXUS_GATE_BUDGET_SECONDS': '30'}
    for name in ('NEXUS_RUNNER_CHECKER', 'NEXUS_RUNNER_LAUNCH', 'NEXUS_GATE_HOOK_DIR'):
        env.pop(name, None)
    payload = {'session_id': SESSION, 'hook_event_name': 'Stop', 'stop_hook_active': False,
               'permission_mode': 'bypassPermissions'}
    stopped = subprocess.run([sys.executable, str(scripts / 'completion_gate.py'), 'stop'],
        cwd=target, env=env, input=json.dumps(payload), text=True,
        capture_output=True, timeout=90, check=False, **ck.NO_WINDOW)
    assert stopped.returncode == 0, stopped.stdout + stopped.stderr
    assert 'Minor controller verification failed' not in stopped.stdout
    assert json.loads(stopped.stdout)['decision'] == 'block'
    assert path.with_name(path.stem + '.gate.json').is_file()
    marker = fixture.tmp / 'platform-observed.json'
    platform = fixture.tmp / 'local_platform.py'
    platform.write_text('import json\nfrom pathlib import Path\n'
        + 'Path(' + repr(str(marker)) + ').write_text(json.dumps({"cwd":str(Path.cwd())}))\n', encoding='utf-8')
    harness = fixture.tmp / 'run_staged.py'
    harness.write_text('import sys\n'
        + 'sys.path.insert(0,' + repr(str(scripts)) + ')\n'
        + 'import run_plan\n'
        + 'def fixture(prompt): return [' + repr(python_name) + ',' + repr(str(platform)) + ']\n'
        + 'run_plan.TEMPLATES["fixture"]=(fixture,fixture,False)\n'
        + 'raise SystemExit(run_plan.run("v0.5","fixture",1))\n', encoding='utf-8')
    ran = subprocess.run([sys.executable, str(harness)], cwd=target, env=env,
        text=True, capture_output=True, timeout=180, check=False, **ck.NO_WINDOW)
    assert ran.returncode == 1, ran.stdout + ran.stderr
    assert marker.is_file(), ran.stdout + ran.stderr
    assert json.loads(marker.read_text(encoding='utf-8'))['cwd'] == str(target)
    assert not path.with_name(path.stem + '.runner.lock').exists()
    current = json.loads(path.read_bytes())
    assert current['nonce'] == original['nonce']
    assert current['session_id'] == original['session_id']
    assert path.read_bytes() == transferred  # Gate observations/counters stay in adjacent sidecars.


def test_missing_legacy_origin_refuses_competing_creation_without_consuming_input(creation_rounds):
    import approval_binding
    fixture, _permanent, roots, rounds, approvals = creation_rounds
    first = create_at(fixture, roots[0], rounds[0][0], approvals)
    assert first.returncode == 0, first.stdout + first.stderr
    owner = cm.record_file(ck, ck.RepoContext(roots[0], ck.Budget(60)), 'v0.5')
    before = owner.read_bytes()
    _git(_permanent, 'worktree', 'remove', str(roots[0]))
    second = create_at(fixture, roots[1], rounds[1][0], approvals)
    assert second.returncode != 0
    assert 'controller-ownership-unavailable' in second.stdout
    assert owner.read_bytes() == before
    assert approval_binding.event_available(fixture.runs, rounds[1][0], rounds[1][1])


@pytest.fixture
def ownership_prefilter_legacy(controller, monkeypatch):
    """A separately created v0.4 fixture authority whose completed origin is removed."""
    fixture, source, target, own_path = controller
    base = fixture.tmp / 'legacy-fixture'
    base.mkdir()
    legacy = Minor(base, monkeypatch)
    legacy.plan('v0.4.1', 'legacy', folder='docs/releases/v0/v0.4/plans')
    legacy.commit('add unrelated legacy minor fixture')
    permanent = legacy.work
    origin = base / 'legacy-controller'
    _git(permanent, 'worktree', 'add', '-q', '-b', 'legacy-controller', str(origin), 'main')
    legacy.work = origin
    legacy.runs = fixture.runs
    legacy.env['NEXUS_HUB_RUNS_DIR'] = str(fixture.runs)
    monkeypatch.setenv('NEXUS_HUB_RUNS_DIR', str(fixture.runs))
    approvals = legacy.approvals()
    spec = json.loads(approvals.read_text(encoding='utf-8'))
    spec['classes'] = [row for row in spec['classes'] if row['class'] != 'gap-migration']
    approvals.write_text(json.dumps(spec), encoding='utf-8')
    session = 'unrelated-legacy-fixture-session'
    legacy.capture(session, '/implement v0.4', at=0.0)
    rendered = legacy.run('record', 'render', '--minor', 'v0.4', '--session', session,
                          '--approvals', str(approvals))
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    legacy.capture(session, rendered.stdout.splitlines()[0])
    created = legacy.run('record', 'create', '--minor', 'v0.4', '--session', session,
                         '--approvals', str(approvals))
    assert created.returncode == 0, created.stdout + created.stderr
    legacy_path = cm.record_file(ck, ck.RepoContext(origin, ck.Budget(60)), 'v0.4')
    record = json.loads(legacy_path.read_bytes())
    assert 'implementation_controller' not in record
    assert [member['version'] for member in record['members']] == ['v0.4.1']
    record['completed'] = {'at': ck._now(), 'head': record['start_head']}
    _write_ownership_fixture_record(legacy_path, record)
    cm.controller_identity(ck, fixture.rctx(), record, legacy_path, same_common=False)
    _git(permanent, 'worktree', 'remove', str(origin))
    assert not origin.exists()
    return fixture, own_path, legacy_path, origin, permanent


def _write_ownership_fixture_record(path, record):
    """Sign only the private Minor fixture's completion or adversarial test state."""
    record['approvals_hmac'] = ck._sign(record, ck._secret(create=False))
    path.write_text(json.dumps(record), encoding='utf-8')


@pytest.mark.parametrize('null_binding', [False, True], ids=['absent-binding', 'explicit-null-common'])
def test_ownership_prefilter_load_ignores_authenticated_unrelated_deleted_origin(ownership_prefilter_legacy, monkeypatch, null_binding):
    fixture, own_path, legacy_path, origin, permanent = ownership_prefilter_legacy
    if null_binding:
        record = json.loads(legacy_path.read_bytes())
        record['implementation_controller'] = {'repo_root': str(origin.resolve()), 'git_common_dir': None}
        _write_ownership_fixture_record(legacy_path, record)
        # Explicit None keeps the existing full-resolution fallback while the origin exists.
        _git(permanent, 'worktree', 'add', '-q', str(origin), 'legacy-controller')
        identity = cm.controller_identity(ck, fixture.rctx(), record, legacy_path, same_common=False)
        assert identity['git_common_dir'] == str((permanent / '.git').resolve())
        _git(permanent, 'worktree', 'remove', str(origin))
    before = {p.name: p.read_bytes() for p in fixture.runs.glob('*.json')}
    common_probes = []
    original_common = cm._common_dir
    def observed_common(ctx, root):
        common_probes.append(root)
        return original_common(ctx, root)
    monkeypatch.setattr(cm, '_common_dir', observed_common)
    state = cm.load_minor(ck, fixture.rctx(), 'v0.5', SESSION)
    assert state.record is not None and state.record.record_path == own_path.resolve()
    assert state.forced is None
    assert not origin.exists() and origin not in common_probes
    assert before == {p.name: p.read_bytes() for p in fixture.runs.glob('*.json')}
    # A direct authority lookup still requires full Git resolution for that legacy owner.
    with pytest.raises(ck.MinorConflict, match='controller-ownership-unavailable'):
        cm.record_file(ck, fixture.rctx(), 'v0.4')
    assert before == {p.name: p.read_bytes() for p in fixture.runs.glob('*.json')}


@pytest.mark.parametrize(('damage', 'reason'), [
    ('signature', 'record-tampered'),
    ('wrong-key', 'controller-origin-or-common-dir-mismatch'),
    ('scope', 'record-tampered'),
    ('binding-fields', 'invalid-controller-binding-fields'),
    ('common-metadata', 'controller-ownership-unavailable'),
])
def test_ownership_prefilter_authenticates_excluded_metadata(ownership_prefilter_legacy, damage, reason):
    fixture, _own_path, legacy_path, origin, _permanent = ownership_prefilter_legacy
    record = json.loads(legacy_path.read_bytes())
    if damage == 'signature':
        record['nonce'] += '-tampered'
        legacy_path.write_text(json.dumps(record), encoding='utf-8')
    elif damage == 'wrong-key':
        wrong = legacy_path.with_name('0' * 64 + '.json')
        assert wrong != legacy_path and not wrong.exists()
        legacy_path.rename(wrong)
    else:
        if damage == 'scope':
            record['scope'] = 'plan'
        elif damage == 'binding-fields':
            record['implementation_controller'] = {'repo_root': str(origin.resolve()),
                'git_common_dir': None, 'unknown': True}
        else:
            record['implementation_controller'] = {'repo_root': str(origin.resolve()),
                'git_common_dir': 'relative-common-directory'}
        _write_ownership_fixture_record(legacy_path, record)
    before = {p.name: p.read_bytes() for p in fixture.runs.glob('*.json')}
    with pytest.raises(ck.MinorConflict, match=reason):
        cm.load_minor(ck, fixture.rctx(), 'v0.5', SESSION)
    assert before == {p.name: p.read_bytes() for p in fixture.runs.glob('*.json')}


@pytest.mark.parametrize('completed', [True, False], ids=['completed-matching', 'live-matching'])
def test_ownership_prefilter_matching_deleted_origin_still_refuses(ownership_prefilter_legacy, completed):
    fixture, own_path, legacy_path, _origin, _permanent = ownership_prefilter_legacy
    if not completed:
        record = json.loads(legacy_path.read_bytes())
        record['completed'] = None
        _write_ownership_fixture_record(legacy_path, record)
    before = {p.name: p.read_bytes() for p in fixture.runs.glob('*.json')}
    with pytest.raises(ck.MinorConflict, match='controller-ownership-unavailable'):
        cm.other_minor_owns(ck, fixture.rctx(), 'v0.4.1', own_path)
    assert before == {p.name: p.read_bytes() for p in fixture.runs.glob('*.json')}


def test_ownership_prefilter_unreadable_unknown_record_still_refuses(controller):
    fixture, _source, _target, _own_path = controller
    unknown = fixture.runs / ('f' * 64 + '.json')
    assert not unknown.exists()
    unknown.write_text('{unreadable unknown possible owner', encoding='utf-8')
    before = {p.name: p.read_bytes() for p in fixture.runs.glob('*.json')}
    with pytest.raises(ck.MinorConflict, match='controller-ownership-unavailable'):
        cm.load_minor(ck, fixture.rctx(), 'v0.5', SESSION)
    assert before == {p.name: p.read_bytes() for p in fixture.runs.glob('*.json')}



def test_live_branches_prefilter_completed_deleted_origin(ownership_prefilter_legacy, monkeypatch):
    fixture, own_path, legacy_path, origin, _permanent = ownership_prefilter_legacy
    before = {p.name: p.read_bytes() for p in fixture.runs.glob('*.json')}
    probes = []
    original_common = cm._common_dir
    def observed_common(ctx, root):
        probes.append(root)
        return original_common(ctx, root)
    monkeypatch.setattr(cm, '_common_dir', observed_common)
    ctx = fixture.rctx()
    original_run = ctx.run
    def observed_run(argv, *args, **kwargs):
        if argv[:3] == [ctx.gh, 'pr', 'list']:
            return 0, json.dumps([{'headRefName': 'fixture-open-pr'}])
        return original_run(argv, *args, **kwargs)
    monkeypatch.setattr(ctx, 'run', observed_run)
    names = cm.live_branches(ck, ctx, json.loads(own_path.read_bytes()), 'acme/demo')
    assert names is not None and 'fixture-open-pr' in names
    assert not origin.exists() and origin not in probes
    assert 'legacy-controller' not in names
    assert legacy_path.exists()
    assert before == {p.name: p.read_bytes() for p in fixture.runs.glob('*.json')}


@pytest.mark.parametrize(('damage', 'reason'), [
    ('live', 'controller-ownership-unavailable'),
    ('signature', 'record-tampered'),
    ('wrong-key', 'controller-origin-or-common-dir-mismatch'),
])
def test_live_branches_prefilter_keeps_owner_validation(ownership_prefilter_legacy, damage, reason):
    fixture, own_path, legacy_path, _origin, _permanent = ownership_prefilter_legacy
    record = json.loads(legacy_path.read_bytes())
    if damage == 'live':
        record['completed'] = None
        _write_ownership_fixture_record(legacy_path, record)
    elif damage == 'signature':
        record['nonce'] += '-tampered'
        legacy_path.write_text(json.dumps(record), encoding='utf-8')
    else:
        legacy_path.rename(legacy_path.with_name('0' * 64 + '.json'))
    before = {p.name: p.read_bytes() for p in fixture.runs.glob('*.json')}
    with pytest.raises(ck.MinorConflict, match=reason):
        cm.live_branches(ck, fixture.rctx(), json.loads(own_path.read_bytes()), 'acme/demo')
    assert before == {p.name: p.read_bytes() for p in fixture.runs.glob('*.json')}


def _ledger_exclusion_inputs(controller, monkeypatch):
    fixture, _source, _target, own_path = controller
    ctx = fixture.rctx()
    state = cm.load_minor(ck, ctx, 'v0.5', SESSION)
    assert state.forced is None and isinstance(state.record, ck.MinorSnapshot)
    assert state.record.record_path == own_path.resolve()
    ledger = cm.Ledger(fixture.work / 'docs/releases/v0/v0.4/known-gaps.md',
        'docs/releases/v0/v0.4/known-gaps.md', (0, 4), 'active', '', [])
    monkeypatch.setattr(cm, '_integration_ref', lambda *_: 'origin/develop')
    monkeypatch.setattr(cm, 'unmerged_changes', lambda *_: {})
    monkeypatch.setattr(cm, 'live_branches', lambda *_: set())
    monkeypatch.setattr(cm, 'scan_plans', lambda *args, **kwargs: [argparse.Namespace(status='queued')])
    owners = []
    def owned(_ck, _ctx, _plan, _live, own):
        owners.append(own)
        return False
    monkeypatch.setattr(cm, '_owned_by_live_run', owned)
    return fixture, ctx, state.record, ledger, owners


@pytest.mark.parametrize('plain_dict', [False, True], ids=['snapshot', 'plain-dict'])
def test_excluded_ledgers_reuses_snapshot_path_and_keeps_dict_fallback(controller, monkeypatch, plain_dict):
    fixture, ctx, snapshot, ledger, owners = _ledger_exclusion_inputs(controller, monkeypatch)
    discoveries = []
    def rediscover(*args):
        discoveries.append(args)
        assert plain_dict, 'authenticated snapshot must not rediscover its controller through Git'
        return snapshot.record_path
    monkeypatch.setattr(cm, 'record_file', rediscover)
    before = {p.name: p.read_bytes() for p in fixture.runs.glob('*.json')}
    record = dict(snapshot) if plain_dict else snapshot
    assert cm.excluded_ledgers(ck, ctx, 'v0.5', record, [ledger]) == {}
    assert owners == [snapshot.record_path]
    assert len(discoveries) == int(plain_dict)
    assert before == {p.name: p.read_bytes() for p in fixture.runs.glob('*.json')}


def test_excluded_ledgers_spent_budget_does_not_report_empty_exclusions(controller, monkeypatch):
    fixture, ctx, snapshot, _ledger, _owners = _ledger_exclusion_inputs(controller, monkeypatch)
    monkeypatch.setattr(ctx.budget, 'remaining', lambda: 0.0)
    before = {p.name: p.read_bytes() for p in fixture.runs.glob('*.json')}
    assert cm.excluded_ledgers(ck, ctx, 'v0.5', snapshot, []) is None
    assert before == {p.name: p.read_bytes() for p in fixture.runs.glob('*.json')}


def test_excluded_ledgers_mid_scan_exhaustion_is_unknown(controller, monkeypatch):
    fixture, ctx, snapshot, ledger, owners = _ledger_exclusion_inputs(controller, monkeypatch)
    left = [60.0]
    monkeypatch.setattr(ctx.budget, 'remaining', lambda: left[0])
    def changes(*args):
        left[0] = 0.0
        return {}
    monkeypatch.setattr(cm, 'unmerged_changes', changes)
    monkeypatch.setattr(cm, 'record_file', lambda *args: snapshot.record_path)
    before = {p.name: p.read_bytes() for p in fixture.runs.glob('*.json')}
    assert cm.excluded_ledgers(ck, ctx, 'v0.5', snapshot, [ledger]) is None
    assert owners == [snapshot.record_path]
    assert before == {p.name: p.read_bytes() for p in fixture.runs.glob('*.json')}
