"""Consumer regressions: real Git history, immutable evidence and approval scope."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import approval_binding as binding  # noqa: E402
import approval_page  # noqa: E402
import check_plan_completion as ck  # noqa: E402
import completion_minor as cm  # noqa: E402
import minor_close  # noqa: E402


@pytest.mark.parametrize('heading,expected', [
    ('# [2.14.2](https://example.test/compare) (2026-10-18)', 'met'),
    ('## [2.14.2]', 'met'), ('# [2.14.20]', 'unmet'),
    ('### [2.14.2]', 'unmet'), ('prose # [2.14.2]', 'unmet'),
])
def test_semantic_release_heading(tmp_path, heading, expected):
    (tmp_path / 'CHANGELOG.md').write_text(heading + '\n', encoding='utf-8')
    assert ck._changelog_status(SimpleNamespace(root=tmp_path, version='v2.14.2')) == expected


def test_merged_then_deleted_task_paths(tmp_path, monkeypatch):
    monkeypatch.setenv('GIT_CONFIG_GLOBAL', str(tmp_path / 'empty-config'))
    monkeypatch.setenv('GIT_CONFIG_NOSYSTEM', '1')
    def git(*args):
        return subprocess.run(['git', '-C', str(tmp_path), *args], check=True,
                              capture_output=True, text=True).stdout.strip()
    git('init', '-q', '-b', 'develop')
    git('config', 'user.email', 'test@example.invalid')
    git('config', 'user.name', 'Test')
    (tmp_path / 'README.md').write_text('baseline\n')
    git('add', '.')
    git('commit', '-qm', 'baseline')
    start = git('rev-parse', 'HEAD')
    git('checkout', '-qb', 'feature')
    for name in ('converter.py', '2026-10-19-decision.md'):
        (tmp_path / name).write_text('temporary\n')
    git('add', '.')
    git('commit', '-qm', 'implement')
    git('rm', '-q', 'converter.py', '2026-10-19-decision.md')
    git('commit', '-qm', 'planned removal')
    git('checkout', '-q', 'develop')
    git('merge', '--no-ff', '-qm', 'merge feature', 'feature')
    ctx = SimpleNamespace(root=tmp_path, git=shutil.which('git'), budget=ck.Budget(20))
    assert ck._task_status(ctx, True, 'converter.py', start) == 'met'
    assert ck._task_status(ctx, True, 'YYYY-MM-DD-decision.md', start) == 'met'
    assert ck._task_status(ctx, True, 'never-existed.py', start) == 'unmet'
    assert ck._task_status(ctx, False, 'converter.py', start) == 'unmet'


def test_relative_ledger_root(tmp_path, monkeypatch):
    path = tmp_path / 'docs/archives/v1/v1.0/known-gaps.md'
    path.parent.mkdir(parents=True)
    path.write_text('# Gaps\n\n## Warnings\n\n### WN-1: outstanding\n')
    monkeypatch.chdir(tmp_path)
    ledgers, unreadable = cm.load_ledgers(Path('.'))
    assert not unreadable
    assert ledgers[0].rel == 'docs/archives/v1/v1.0/known-gaps.md'
    assert ledgers[0].items[0].state == 'open'


@pytest.mark.parametrize('suffix', ['txt', 'md', 'json'])
def test_unicode_fix_preserves_evidence(tmp_path, suffix):
    rel = f'docs/releases/v2/v2.15/development/evidence/capture.{suffix}'
    target = tmp_path / rel
    target.parent.mkdir(parents=True)
    raw = b'\xef\xbb\xbfraw capture\r\n'
    target.write_bytes(raw)
    ordinary = tmp_path / 'docs/note.md'
    ordinary.write_bytes(b'\xef\xbb\xbfauthored note\n')
    proc = subprocess.run([sys.executable, str(ROOT / 'scripts/validate_unicode_safety.py'),
                           '--root', str(tmp_path), '--path', 'docs', '--strict', '--fix'],
                          capture_output=True, text=True)
    assert target.read_bytes() == raw, proc.stdout + proc.stderr
    assert ordinary.read_bytes() == b'authored note\n'
    assert proc.returncode == 1, 'unfixed evidence must still report its finding'
    assert 'preserved evidence' in proc.stdout


def test_unicode_fix_preserves_explicit_evidence_outside_root(tmp_path):
    root = tmp_path / 'root'
    root.mkdir()
    target = tmp_path / 'outside/evidence/capture.txt'
    target.parent.mkdir(parents=True)
    raw = b'\xef\xbb\xbfexternal capture\r\n'
    target.write_bytes(raw)
    proc = subprocess.run([sys.executable, str(ROOT / 'scripts/validate_unicode_safety.py'),
                           '--root', str(root), '--path', str(target), '--strict', '--fix'],
                          capture_output=True, text=True)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert 'Traceback' not in proc.stderr
    assert 'preserved evidence' in proc.stdout
    assert target.read_bytes() == raw


def test_uncovered_gap_ids_do_not_inherit_class_authority():
    record = {'approvals': {'classes': [
        {'class': 'gap-migration', 'bound': ['v2.12#WN-1'], 'named': []}]}}
    assert ck.uncovered_gap_request(record, {'ids': ['v2.12#WN-2']})
    assert ck.uncovered_gap_request(record, {'ids': ['v2.12#WN-1', 'v2.12#WN-2']})
    assert not ck.uncovered_gap_request(record, {'ids': ['v2.12#WN-1']})
    assert not ck.uncovered_gap_request(record, {'ids': ['v2.12.0#WN-1']})
    for request in ({}, {'ids': []}, {'ids': 'v2.12#WN-2'}, {'ids': [None]}):
        assert not ck.uncovered_gap_request(record, request)


def test_wrong_pasted_line_does_not_spend_round(tmp_path, monkeypatch):
    monkeypatch.delenv('NEXUS_RUNNER_LAUNCH', raising=False)
    runs, secret, session, key = tmp_path / 'runs', b'x' * 32, 'session', 'record'
    page = binding.action_page('answer', rel='docs/plan.md', version='v2.15.0',
                               record_nonce='n' * 32, blocker=1, category='no-progress')
    pending = binding.render(runs, key, secret, action='answer', scope='v2.15.0',
                             page=page, session=session, blocker=1)
    line = pending['paste_lines'][0]
    prompt_dir = runs / 'prompts'
    prompt_dir.mkdir()
    capture = prompt_dir / (hashlib.sha256(session.encode()).hexdigest() + '.jsonl')
    capture.write_text('\n'.join(json.dumps({'session': session, 'prompt': binding.digest(text),
                                             'at': pending['rendered_at'] + delta})
                                 for text, delta in [('implement request', -1), (line, 1)]) + '\n')
    kwargs = dict(action='answer', live_page=page, session=session)
    with pytest.raises(binding.Refusal, match='approval-not-captured'):
        binding.consume(runs, key, secret, **kwargs, pasted_line='reason for continuing')
    assert binding.pending_path(runs, key).exists()
    assert not list((runs / 'consumed-prompts').glob('*.json'))
    binding.consume(runs, key, secret, **kwargs, pasted_line=line)
    assert not binding.pending_path(runs, key).exists()
    with pytest.raises(binding.Refusal, match='code-used'):
        binding.consume(runs, key, secret, **kwargs, pasted_line=line)


def test_archive_reports_unrepaired_data_and_code(tmp_path):
    old, new = 'docs/releases/v2/v2.15', 'docs/archives/v2/v2.15'
    contents = {
        'docs/handbooks/handbooks.json': json.dumps({'evidence': old + '/receipt.json'}),
        '.gitattributes': old + '/log.txt -text\n',
        'docs/index.md': f'[plan]({old}/plans/a.md) and `{old}/plans/a.md`\n',
        'src/catalog.json': json.dumps({'path': old + '/data.json'}),
        'src/comment.py': '# see ' + old + '/data.json\n',
        'docs/archives/v1/v1.0/log.txt': 'historical ' + old + '/data.json\n',
    }
    for rel, text in contents.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    files = [(rel, rel, rel) for rel in contents]
    repairs = minor_close.plan_repairs(tmp_path, files, old, new)
    residual = minor_close.residual_references(tmp_path, files, repairs, old)
    assert set(residual) == set(contents)
    assert all(count > 0 for count in residual.values())
    assert old not in repairs[0].repaired.split('`')[0]
    for rel, text in contents.items():
        assert (tmp_path / rel).read_text() == text


def test_approval_summary_counts_scope_without_promising_repairs():
    display = {'gap_counts': {'v1.0': 217}, 'phases': [
        {'version': 'v2.15.0', 'tier': 'standard', 'effort': 'high', 'phase': 1, 'tasks': 0}]}
    rows = '\n'.join(approval_page._summary({'scope': {'minor': 'v2.15', 'kind': 'minor'},
                                          'cleanup': {'rule': 'run-owned'}},
                                         display, [], True, 'v2.16.0'))
    assert '| Open gaps in scope | 217' in rows
    assert '| Fixed |' not in rows
    assert '| Time |' not in rows


@pytest.mark.parametrize('verified', [True, False])
def test_blocked_detail_is_diagnostic_only(monkeypatch, capsys, verified):
    ctx = SimpleNamespace(notices=[], _git_out=lambda *args: 'head')
    record = {'approvals': {}} if verified else None
    verdict = cm.MinorVerdict('BLOCKED: no-progress', ck.EXIT_BLOCKED, record=record)
    monkeypatch.setattr(cm, 'minor_context', lambda *args: ctx)
    monkeypatch.setattr(cm, 'check_minor', lambda *args: verdict)
    monkeypatch.setattr(cm, '_integration_ref', lambda *args: 'develop')
    monkeypatch.setattr(cm, 'load_ledgers_at', lambda *args: ([], []))
    monkeypatch.setattr(cm, 'gaps_minor_status', lambda *args: ('cannot-verify', ['unparsed historical ledger']))
    args = ck.build_parser().parse_args(['check-minor', 'v2.15', '--detail'])
    assert cm.cmd_check_minor(ck, args) == ck.EXIT_BLOCKED
    out = capsys.readouterr()
    assert out.out.strip() == 'BLOCKED: no-progress'
    assert ('diagnostic gaps.minor cannot-verify' in out.err) == verified
    assert ('unparsed historical ledger' in out.err) == verified
    assert 'completed' not in (record or {})


@pytest.mark.parametrize('prompt', [
    'Approve /implement v2.15 (approval VEV2CW3E)',
    'Continue /implement v2.14 past blocker 1 (approval VEV2CW3E)',
])
def test_exact_approval_pastes_reach_capture(tmp_path, monkeypatch, prompt):
    monkeypatch.setenv('NEXUS_HUB_RUNS_DIR', str(tmp_path))
    monkeypatch.delenv('NEXUS_RUNNER_LAUNCH', raising=False)
    payload = {'session_id': 'paste-session', 'prompt': prompt}
    proc = subprocess.run([sys.executable, str(ROOT / 'scripts/completion_gate.py'), 'capture'],
                          input=json.dumps(payload), capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    files = list((tmp_path / 'prompts').glob('*.jsonl'))
    assert len(files) == 1
    entry = json.loads(files[0].read_text())
    assert entry['prompt'] == binding.digest(prompt)
    assert prompt not in files[0].read_text(), 'only the digest is persisted'


def test_close_status_detail_keeps_blocked_exit(monkeypatch, capsys):
    record = {'approvals': {}}
    state = cm.MinorState(record=record, forced=('BLOCKED: no-progress', ck.EXIT_BLOCKED))
    monkeypatch.setattr(minor_close, '_context', lambda *args: object())
    monkeypatch.setattr(cm, 'load_minor', lambda *args: state)
    monkeypatch.setattr(cm, 'gaps_minor_status', lambda *args: ('unmet', ['open historical item']))
    args = minor_close.build_parser().parse_args(['status', '--minor', 'v2.15', '--detail'])
    assert minor_close.cmd_status(args) == minor_close.EXIT_REFUSED
    out = capsys.readouterr()
    assert out.out.strip() == 'BLOCKED: no-progress'
    assert 'diagnostic gaps.minor unmet' in out.err
    assert 'open historical item' in out.err


def test_handbook_hash_is_crlf_independent_and_preserves_binary(tmp_path):
    import runpy
    checker = runpy.run_path(str(ROOT / 'catalog/skills/documentation/technical-documentation/scripts/check_handbooks.py'))
    digest = checker['digest']
    text = tmp_path / 'capture.txt'
    text.write_bytes(b'first\nsecond\n')
    expected = digest(text)
    text.write_bytes(b'first\r\nsecond\r\n')
    assert digest(text) == expected
    text.write_bytes(b'first\r\nchanged\r\n')
    assert digest(text) != expected
    raw = b'\0binary\r\n'
    text.write_bytes(raw)
    assert digest(text) == hashlib.sha256(raw).hexdigest()
