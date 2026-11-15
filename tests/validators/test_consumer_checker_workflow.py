"""Consumer regressions through the real minor/approval command-line surfaces."""
from __future__ import annotations

import json

import pytest

from .test_check_plan_completion import _isolated_git_config  # noqa: F401
from .test_completion_minor_record import SESSION, Minor, _no_transport_overrides  # noqa: F401
from .test_gap_migration_and_archive import Close, WN3, ledger, section
import check_plan_completion as ck
import completion_minor as cm


def test_cli_moves_older_gap_into_current_minor_and_keeps_it_open(tmp_path, monkeypatch):
    repo = Close(tmp_path, monkeypatch)
    source = 'docs/releases/v0/v0.4/known-gaps.md'
    repo.write(source, ledger('v0.4', section('v0.4.0', 1, WN3)))
    repo.commit('older gap')
    repo.integrate()
    repo.forge(bound=('v0.4#WN-3',))
    result = repo.migrate('v0.4#WN-3', 'v0.5', '--to', 'v0.5.0')
    assert result.returncode == 0, result.stdout + result.stderr
    assert '(v0.5.0)' in result.stdout
    ledgers, unreadable = cm.load_ledgers(repo.work)
    assert not unreadable
    original = next(item for item in ledgers if item.token() == 'v0.4')
    item = original.items[0]
    rctx = repo.rctx()
    record = cm.load_minor(ck, rctx, 'v0.5', None).record
    assert cm.verify_migration(rctx, record, 'v0.5', ledgers, original, item) == ('met', 'in-scope-copy')
    target = next(item for item in ledgers if item.token() == 'v0.5')
    assert target.items[0].state == 'open'
    assert cm.gaps_minor_status(ck, repo.rctx(), 'v0.5', record)[0] == 'unmet'


@pytest.mark.parametrize('target', ['v0.5.1', 'v0.5.0', 'v0.4.0', 'v0.7.0'])
def test_cli_refuses_invalid_self_backward_and_skipped_migration(tmp_path, monkeypatch, target):
    repo = Close(tmp_path, monkeypatch)
    repo.standard()
    repo.forge()
    before = {path: path.read_bytes() for path in repo.work.glob('docs/**/known-gaps.md')}
    result = repo.migrate('v0.5#WN-3', 'v0.5', '--to', target)
    assert result.returncode in (2, 3), result.stdout + result.stderr
    assert before == {path: path.read_bytes() for path in repo.work.glob('docs/**/known-gaps.md')}


def test_cli_block_names_only_uncovered_gap_ids(tmp_path, monkeypatch):
    repo = Close(tmp_path, monkeypatch)
    repo.standard()
    repo.forge()
    args = ['record', 'block', '--minor', 'v0.5', '--session', SESSION,
            '--category', 'approval-not-covered', '--approval-class', 'gap-migration',
            '--evidence', 'new ids exceed the frozen list']
    refused = repo.run(*args, '--request', json.dumps({'ids': ['v0.5#WN-3']}))
    assert refused.returncode == ck.EXIT_MALFORMED, refused.stdout + refused.stderr
    blocked = repo.run(*args, '--request', json.dumps({'ids': ['v0.4#WN-9']}))
    assert blocked.returncode == ck.EXIT_BLOCKED, blocked.stdout + blocked.stderr
    record = cm.load_minor(ck, repo.rctx(), 'v0.5', SESSION).record
    assert record['blockers'][-1]['request'] == {'ids': ['v0.4#WN-9']}
    assert cm.migration_class(record)[0] == {'v0.5#WN-3'}
    detailed = repo.run('check-minor', 'v0.5', '--detail', '--session', SESSION)
    assert detailed.returncode == ck.EXIT_BLOCKED, detailed.stdout + detailed.stderr
    assert detailed.stdout.splitlines()[0] == 'BLOCKED: approval-not-covered'
    assert 'diagnostic gaps.minor unmet' in detailed.stderr
    status = repo.close('status', '--minor', 'v0.5', '--detail')
    assert status.returncode == ck.EXIT_BLOCKED, status.stdout + status.stderr
    assert status.stdout.splitlines()[0] == 'BLOCKED: approval-not-covered'
    assert 'diagnostic gaps.minor unmet' in status.stderr


def test_cli_answer_typo_preserves_round_for_valid_retry(tmp_path, monkeypatch):
    repo = Minor(tmp_path, monkeypatch)
    assert repo.create().returncode == 0
    blocked = repo.run('record', 'block', '--minor', 'v0.5', '--session', SESSION,
                       '--category', 'no-progress', '--evidence', 'no progress')
    assert blocked.returncode == ck.EXIT_BLOCKED
    line = repo.paste(SESSION, '--action', 'answer', '--blocker', '0')
    args = ['record', 'answer', '--minor', 'v0.5', '--session', SESSION, '--blocker', '0']
    wrong = repo.run(*args, '--text', 'reason for continuing')
    assert wrong.returncode == ck.EXIT_BLOCKED, wrong.stdout + wrong.stderr
    assert repo.record()['blockers'][0]['open']
    correct = repo.run(*args, '--pasted-line', line)
    assert correct.returncode == 0, correct.stdout + correct.stderr
    assert not repo.record()['blockers'][0]['open']
