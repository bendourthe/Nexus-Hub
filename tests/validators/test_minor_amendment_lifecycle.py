"""A captured amendment survives native implementation, publication, archive and handoff."""

import copy
import json
from pathlib import Path

from .test_completion_minor_record import SESSION, PUSH_URL, ck, cm, _git, _isolated_git_config, _no_transport_overrides
from .test_completion_minor_verdict import Walk, EVIDENCE_SECTIONS, GREEN
from .test_gap_migration_and_archive import GAPS05, LINK_CHECKER, ledger, section
from .test_minor_scope_amendment import amendment_input
from .test_controller_handoff import handoff


def _ok(result):
    assert result.returncode == 0, result.stdout + result.stderr
    return result


def test_native_amended_member_complete_lifecycle(tmp_path, monkeypatch, minor_git_seed):
    fx = Walk(tmp_path, monkeypatch, minor_git_seed)
    versions = [('v0.5.2', 'alpha'), ('v0.5.10', 'omega'), ('v0.5.11', 'added')]
    fx.write(GAPS05, ledger('v0.5', ''.join(section(v, 0, '') for v, _ in versions),
                           status='finalized', open_items=0))
    fx.commit('finalized empty minor register')
    fx.integrate()
    _ok(fx.create())
    original = fx.record()
    amendment_file, amendment = amendment_input(fx)
    grant = amendment['members'][0]['approvals']
    grant['classes'].append({'class': 'cleanup-merged'})
    grant['cleanup']['branches'] = ['feat/v0.5.11-added']
    Path(amendment_file).write_text(json.dumps(amendment), encoding='utf-8')
    fx.paste(SESSION, '--action', 'amend-minor', '--amendment', amendment_file)
    _ok(fx.run('record', 'amend-minor', '--minor', 'v0.5', '--session', SESSION,
               '--amendment', amendment_file))
    amended = fx.record()
    history = copy.deepcopy(amended['minor_amendments'])
    assert amended['members'] == original['members']

    # Both original members use the real ordered publication writer. The existing
    # Walk fixture supplies real Git releases and the isolated local hosting stub.
    for version, slug in versions[:2]:
        _ok(fx.member_start(version))
        fx.release_member(version, slug)
        assert fx.record()['minor_amendments'] == history
    assert all(m.get('start_head') for m in fx.record()['members'])

    version, slug = versions[-1]
    plan = f'docs/releases/v0/v0.5/plans/{version}-{slug}.md'
    evidence = f'docs/releases/v0/v0.5/development/{version}-last-phase-evidence.md'
    worker = tmp_path / 'added-worker'
    branch = f'feat/{version}-{slug}'
    with monkeypatch.context() as idle_git:
        idle_git.setenv('GIT_COMMITTER_DATE', '2000-01-01T00:00:00+00:00')
        _git(fx.work, 'worktree', 'add', '-q', '-b', branch, str(worker), 'origin/develop')
    base = _git(worker, 'rev-parse', 'HEAD')
    writes = sorted([plan, evidence, 'src/added.txt', 'tests/test_added.py'])
    claims = {'depends_on': ['v0.5.10'], 'read_paths': [], 'write_paths': writes}
    claim_file = tmp_path / 'added-claims.json'
    claim_file.write_text(json.dumps(claims), encoding='utf-8')
    _ok(fx.run('record', 'member-implement-start', '--minor', 'v0.5', '--member', version,
               '--session', SESSION, '--worktree', str(worker), '--head', base,
               '--claims', str(claim_file)))
    admitted = cm.effective_members(ck, fx.record())[-1]
    assert admitted['implementation']['worktree'] == str(worker.resolve())
    assert admitted['implementation']['write_paths'] == writes
    assert admitted['implementation']['base_head'] == base
    assert 'start_head' not in admitted
    assert fx.record()['minor_amendments'] == history

    body = ''.join(f'## {name}\n\nDone.\n\n' for name in EVIDENCE_SECTIONS)
    body += '## Full-suite testing and stabilization\n\n`pytest -q`: 3 passed, including tests/test_added.py.\n'
    outputs = {
        plan: (worker / plan).read_text().replace('- [ ] T001', '- [x] T001'),
        'src/added.txt': 'added\n',
        'tests/test_added.py': 'def test_part():\n    assert True\n',
        evidence: '# Evidence\n\n' + body,
    }
    for rel, text in outputs.items():
        path = worker / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
    _git(worker, 'add', '--', *writes)
    with monkeypatch.context() as idle_git:
        idle_git.setenv('GIT_COMMITTER_DATE', '2000-01-01T00:00:00+00:00')
        _git(worker, 'commit', '-qm', 'implement admitted added member')
    projected = fx.run('check-member', '--minor', 'v0.5', '--member', version,
                       '--session', SESSION, '--json')
    projection = json.loads(projected.stdout.splitlines()[-1])
    assert projection['predicates']['implementation.identity'] == 'met', projected.stdout + projected.stderr
    assert projection['predicates']['task.T001'] == 'met'

    coordinator = tmp_path / 'publication-claims.json'
    coordinator.write_text(json.dumps({'write_paths': ['CHANGELOG.md']}), encoding='utf-8')
    _ok(fx.run('record', 'member-start', '--minor', 'v0.5', '--member', version,
               '--session', SESSION, '--head', base, '--coordinator-claims', str(coordinator)))
    published = cm.effective_members(ck, fx.record())[-1]
    assert published['start_head'] == base
    assert published['coordinator_paths'] == ['CHANGELOG.md']
    _git(fx.work, 'merge', '-q', '--ff-only', branch)
    fx.release_member(version, slug)
    _git(fx.work, 'worktree', 'remove', str(worker))
    current = fx.record()
    assert current['minor_amendments'] == history
    assert cm._verified(ck, fx.rctx(), 'v0.5', current, minor_protocol=1)
    result = cm.check_minor(ck, fx.rctx(), 'v0.5', SESSION)
    added_result = next(m for m in result.members if m.version == version)
    incomplete = [(p, s) for p, s in added_result.lines if not p.startswith(('cleanup.', 'archive.')) and s not in cm._MET]
    assert not incomplete, incomplete

    # Exercise the actual archive command: move, link proof, commit, and signed
    # refreeze. No archive or completion predicate is replaced in this fixture.
    _git(fx.work, 'checkout', '-q', '-b', 'chore/close-v0.5', 'origin/develop')
    archived = fx.close('archive', '--minor', 'v0.5', '--session', SESSION, '--apply',
                        '--link-checker', str(LINK_CHECKER))
    _ok(archived)
    assert 'ARCHIVED v0.5' in archived.stdout
    closed = fx.record()
    assert closed['minor_amendments'] == history
    runtime = cm.effective_members(ck, closed)[-1]
    assert runtime['plan_path'] == plan.replace('docs/releases/', 'docs/archives/')
    assert runtime['archived']['from'] == plan
    assert runtime['implementation'] == admitted['implementation']
    assert runtime['approvals'] == amended['minor_amendment_members'][0]['approvals']
    _git(fx.work, 'branch', '-f', 'develop', 'HEAD')
    fx.publish('develop')
    archive_head = fx.head()
    fx.pr('chore/close-v0.5', 'MERGED', GREEN, archive_head)

    target = tmp_path / 'continued-controller'
    _git(fx.work, 'worktree', 'add', '-q', '-b', 'continued-controller', str(target), 'origin/develop')
    _ok(handoff(fx, fx.work, target))
    record_path = fx.record_path()
    ctx, continued = ck.resolve_minor_controller(record_path, SESSION, minor_protocol=1)
    assert ctx.root == target
    assert continued['minor_amendments'] == history
    assert continued['implementation_controller']['generation'] == 1
    assert cm._verified(ck, ctx, 'v0.5', continued, minor_protocol=1)
    _ok(handoff(fx, fx.work, target))
    continuation = fx.run('check-member', '--minor', 'v0.5', '--member', version,
                          '--session', SESSION, '--repo', str(target), '--json')
    body = json.loads(continuation.stdout.splitlines()[-1])
    assert body['predicates']['implementation.identity'] == 'met', continuation.stdout + continuation.stderr
    assert body['predicates']['task.T001'] == 'met'
    assert cm.effective_members(ck, continued)[-1]['implementation'] == admitted['implementation']


    # The cleaner independently observes the real merged feature ref and removes
    # it under the prospective amendment grant, then seals its final-pass receipt.
    worker_tip = _git(target, 'rev-parse', branch)
    fx.state['prs'] = [{'number': 1, 'headRefName': branch, 'headRefOid': worker_tip,
                        'baseRefName': 'develop', 'state': 'MERGED', 'isCrossRepository': False}]
    fx.state['activity'] = {branch: ['2000-01-01T00:00:00+00:00']}
    fx.save_state()
    import cleanup_merged
    real_exec = cleanup_merged._exec
    real_checker_run = ck._run

    def route(argv):
        # Same command-scoped transport routing as test_cleanup_merged.Repo:
        # repository identity remains HTTPS; only Git I/O reaches the bare fixture.
        if argv[0] == cleanup_git and any(arg in {'fetch', 'push', 'ls-remote'} for arg in argv[1:]):
            return [argv[0], '-c', f'url.{fx.remote.as_uri()}.insteadOf={PUSH_URL}', *argv[1:]]
        return argv

    def private_transport(argv, cwd=None):
        return real_exec(route(argv), cwd)

    def private_checker_transport(argv, *args, **kwargs):
        return real_checker_run(route(argv), *args, **kwargs)

    cleanup_git = ck.RepoContext(target, ck.Budget(60)).git
    _git(fx.work, 'remote', 'set-url', 'origin', PUSH_URL)
    try:
        with monkeypatch.context() as transport:
            transport.setattr(cleanup_merged, '_exec', private_transport)
            transport.setattr(ck, '_run', private_checker_transport)
            assert cleanup_merged.main(['--apply', '--receipt', '--minor', 'v0.5',
                                        '--session', SESSION, '--repo', str(target)]) == 0
    finally:
        _git(fx.work, 'remote', 'set-url', 'origin', str(fx.remote))
    assert branch not in _git(target, 'for-each-ref', '--format=%(refname:short)', 'refs/heads').splitlines()
    receipt_path = cleanup_merged.receipt_path(record_path)
    receipt_bytes = receipt_path.read_bytes()
    receipt = json.loads(receipt_bytes)
    assert receipt['record_nonce'] == continued['nonce']
    assert receipt['integration_tip'] == archive_head
    assert receipt['removed']
    assert any(item['name'] == branch for item in receipt['removed'])

    done = _ok(fx.run('check-minor', 'v0.5', '--session', SESSION, '--repo', str(target)))
    expected = f"MINOR COMPLETE v0.5 {archive_head} {continued['nonce']}"
    assert done.stdout.splitlines()[0] == expected, done.stdout + done.stderr
    completed_bytes = record_path.read_bytes()
    final = cm.load_minor(ck, ck.RepoContext(target, ck.Budget(60)), 'v0.5', SESSION,
                           accept_completed=True, minor_protocol=1)
    assert final.forced is None and final.record is not None
    assert final.record['completed']['head'] == archive_head
    assert final.record['minor_amendments'] == history
    assert cm.effective_members(ck, final.record)[-1]['implementation'] == admitted['implementation']
    assert cm._verified(ck, ck.RepoContext(target, ck.Budget(60)), 'v0.5', final.record, minor_protocol=1)
    again = _ok(fx.run('check-minor', 'v0.5', '--session', SESSION, '--repo', str(target)))
    assert again.stdout.splitlines()[0] == expected
    assert record_path.read_bytes() == completed_bytes
    assert receipt_path.read_bytes() == receipt_bytes
    assert cm.covering_minor(ck, ck.RepoContext(target, ck.Budget(60)), version) is None
