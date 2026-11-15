"""Amended membership reaches archive writers without changing approved history."""

import copy
import inspect
import json

import pytest

from .test_minor_scope_amendment import amend_fixture, amendment_input
from .test_completion_minor_record import (
    SESSION, MINOR_LEDGER, ck, cm, minor, _git, _isolated_git_config, _no_transport_overrides,
)
import minor_close as mc


def test_refreeze_updates_added_runtime_identity_and_preserves_history(minor):
    _, accepted = amend_fixture(minor)
    history = copy.deepcopy(accepted['minor_amendments'])
    record, path = mc._record(minor.rctx(), 'v0.5', SESSION)
    members = cm.effective_members(ck, record)
    originals = {m['version']: (m['plan_path'], m['plan_sha256']) for m in members}
    destination = minor.work / 'docs/archives/v0'
    destination.mkdir(parents=True)
    _git(minor.work, 'mv', 'docs/releases/v0/v0.5', 'docs/archives/v0/v0.5')
    minor.commit('archive approved plans')
    with ck.minor_transaction(record):
        mc.refreeze(minor.rctx(), record, path, 'v0.5')
    updated, _ = mc._record(minor.rctx(), 'v0.5', SESSION)
    assert updated['minor_amendments'] == history
    assert cm._verified(ck, minor.rctx(), 'v0.5', updated, minor_protocol=1)
    for member in cm.effective_members(ck, updated):
        old_path, old_hash = originals[member['version']]
        assert member['plan_path'] == old_path.replace('docs/releases/', 'docs/archives/')
        assert member['archived']['from'] == old_path
        assert member['archived']['original_sha256'] == old_hash
        assert member['archived']['close_commit'] == _git(minor.work, 'rev-parse', 'HEAD')
    assert updated['minor_amendment_members'][0]['archived']


def test_added_member_plan_cross_reference_is_protected(minor):
    _, record = amend_fixture(minor)
    by_version = {p.version: p for p in cm.scan_plans(minor.work, 0, 5)}
    rel = by_version['v0.5.11'].rel
    repair = mc.Repair(rel, rel, 'old', 'new', 1, 0)
    refusals = mc._cross_reference_refusals([repair], record, 'v0.5.2', by_version)
    assert [(r.reason, r.detail) for r in refusals] == [('member-plan-cross-reference', rel)]
    assert mc._cross_reference_refusals([repair], record, 'v0.5.11', by_version) == []


def test_other_run_added_member_plan_ownership_is_protected(minor):
    _, record = amend_fixture(minor)
    rel = cm.effective_members(ck, record)[-1]['plan_path']
    repair = mc.Repair(rel, rel, 'old', 'new', 1, 0)
    refusals = mc.bound_plan_refusals(minor.rctx(), [repair], None)
    assert [(r.reason, r.detail) for r in refusals] == [('plan-bound-by-another-run', rel)]
    assert mc.bound_plan_refusals(minor.rctx(), [repair], record) == []


@pytest.mark.parametrize('damage', ['stale-plan', 'wrong-session', 'unapproved-runtime'])
def test_archive_refuses_invalid_amended_authority_before_mutation(minor, monkeypatch, damage):
    _, record = amend_fixture(minor)
    session = SESSION
    if damage == 'stale-plan':
        plan = minor.work / cm.effective_members(ck, record)[-1]['plan_path']
        plan.write_text(plan.read_text() + '\nUnapproved scope.\n')
    elif damage == 'wrong-session':
        session = 'other-session'
    else:
        record['minor_amendment_members'][0]['version'] = 'v0.5.12'
        minor.write_record(record, resign=False)
    before = minor.record_path().read_bytes()
    files = {str(p.relative_to(minor.work)): p.read_bytes() for p in minor.work.rglob('*.md')}
    monkeypatch.setattr(mc, '_archive_member', lambda *a: pytest.fail('archive reached its write boundary'))
    assert mc.main(['archive-member', '--minor', 'v0.5', '--member', 'v0.5.2', '--session', session,
                    '--apply', '--repo', str(minor.work)]) == mc.EXIT_REFUSED
    assert minor.record_path().read_bytes() == before
    assert files == {str(p.relative_to(minor.work)): p.read_bytes() for p in minor.work.rglob('*.md')}


def test_legacy_archive_lookup_refuses_amended_record_before_write(minor, monkeypatch):
    amend_fixture(minor)
    before = minor.record_path().read_bytes()
    # Execute the pre-protocol lookup body against the current verifier. An old
    # archive must stop here, before entering either archive implementation.
    source = inspect.getsource(mc._record).replace(', minor_protocol=1', '')
    namespace = dict(vars(mc))
    exec(compile(source, mc.__file__, 'exec'), namespace)
    monkeypatch.setattr(mc, '_record', namespace['_record'])
    monkeypatch.setattr(mc, '_archive_member', lambda *a: pytest.fail('legacy archive reached mutation'))
    assert mc.main(['archive-member', '--minor', 'v0.5', '--member', 'v0.5.2', '--session', SESSION,
                    '--apply', '--repo', str(minor.work)]) == mc.EXIT_REFUSED
    assert minor.record_path().read_bytes() == before


def test_added_member_does_not_inherit_parent_archive_authority(minor, capsys):
    _, record = amend_fixture(minor)
    assert 'archive-minor' in cm._classes(record)
    assert mc.main(['archive-member', '--minor', 'v0.5', '--member', 'v0.5.11', '--session', SESSION,
                    '--apply', '--repo', str(minor.work)]) == mc.EXIT_REFUSED
    assert 'REFUSED: approval-not-covered (the member does not carry archive-member)' in capsys.readouterr().out
    assert not cm.effective_members(ck, minor.record())[-1].get('archived')


def test_archive_branch_and_plan_checks_include_added_members(minor, monkeypatch):
    _, record = amend_fixture(minor)
    _git(minor.work, 'checkout', '-q', '-b', 'chore/archive-v0.5.11', 'origin/develop')
    assert mc._archive_branch_refusals(minor.rctx(), record, 'v0.5.11') == []
    monkeypatch.setattr(cm, 'shipped', lambda *args: 'unmet')
    refusals = mc.plan_refusals(minor.rctx(), 'v0.5', record)
    assert not any(r.reason == 'queued-plan-outside-members' for r in refusals)
    assert {r.detail for r in refusals if r.reason == 'unreleased-member'} == {
        'v0.5.2', 'v0.5.10', 'v0.5.11',
    }


def test_added_gap_migration_requires_its_captured_reason(minor, capsys):
    assert minor.create().returncode == 0
    ledger = minor.work / 'docs/releases/v0/v0.5/known-gaps.md'
    ledger.write_text(MINOR_LEDGER.replace('WN-3', 'WN-4'), encoding='utf-8')
    filename, value = amendment_input(minor)
    value['gap_migration'] = {'items': [{'id': 'v0.5#WN-4', 'reason': 'user-deferred'}],
                              'named_high_risk_ids': []}
    (minor.tmp / 'amendment.json').write_text(json.dumps(value), encoding='utf-8')
    minor.paste(SESSION, '--action', 'amend-minor', '--amendment', filename)
    result = minor.run('record', 'amend-minor', '--minor', 'v0.5', '--session', SESSION,
                       '--amendment', filename)
    assert result.returncode == 0, result.stdout + result.stderr
    before = ledger.read_bytes()
    assert mc.main(['migrate', '--minor', 'v0.5', '--id', 'v0.5#WN-4', '--session', SESSION,
                    '--reason', 'vendor-feature', '--evidence', 'vendor missing',
                    '--repo', str(minor.work)]) == mc.EXIT_REFUSED
    assert 'REFUSED: migration-reason-outside-amendment' in capsys.readouterr().out
    assert ledger.read_bytes() == before
    assert not (minor.work / 'docs/releases/v0/v0.6/known-gaps.md').exists()
