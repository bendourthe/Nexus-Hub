"""Explicit observer records keep native read-only validation in fresh installed CLIs."""

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest

from .test_completion_minor_record import SESSION as MINOR_SESSION, minor, ck, _isolated_git_config  # noqa: F401
from .test_plan_owner_continuation import create_owned, _hook, PLAN_REL, SESSION as PLAN_SESSION

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "catalog/skills/workflow/implement-phase"
FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _snapshot():
    spec = importlib.util.spec_from_file_location("observer_snapshot", SKILL / "scripts/status_snapshot.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("explicit", [False, True])
def test_observer_cli_record_resolution_precedence_is_inert(tmp_path, monkeypatch, capsys, explicit):
    snapshot = _snapshot()
    record = tmp_path / "private-record.json"
    record.write_text("{}", encoding="utf-8")
    calls = []
    def context(session, *, allow_resume=False):
        assert not explicit, "An explicit record must not require pre-create context"
        calls.append((session, allow_resume))
        return SimpleNamespace(), record, {}
    monkeypatch.setitem(sys.modules, "check_plan_completion", SimpleNamespace(precreate_owner_context=context))
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(sys, "argv", ["snapshot", "--scope", "v0.2.0", "--observer-session", "private-observer",
        *(["--record", str(record)] if explicit else [])])
    def build(*args):
        assert args[-2:] == (record, "private-observer")
        return {"scope": "v0.2.0"}
    monkeypatch.setattr(snapshot, "build", build)
    assert snapshot.main() == 0
    assert calls == ([] if explicit else [("private-observer", True)])
    assert json.loads(capsys.readouterr().out)["scope"] == "v0.2.0"


def _save_private_wait(fx, path, scope, observer):
    import run_plan
    record = json.loads(path.read_text())
    scope = SimpleNamespace(minor=record.get("schema") == 2, label=str(scope), repo_root=fx.work, observer_session=observer)
    facts = run_plan.native_owner_observation(scope, path, record, None, remaining_tasks=2)
    assert facts is not None
    frame = run_plan.reconcile_observation(scope, path, record, facts, 1,
        "INCOMPLETE: private observer fixture tasks remain", readonly=True)
    run_plan.save_continuation(path, frame)
    return run_plan.continuation_path(path)


def _installed_cli(fx, path, scope, observer, home, tmp_path):
    installed = home / ".nexus-hub/skills/workflow/implement-phase"
    helpers = home / ".nexus-hub/scripts"
    shutil.copytree(SKILL, installed)
    shutil.copytree(ROOT / "scripts", helpers, ignore=shutil.ignore_patterns("__pycache__"))
    declarations = tmp_path / "private_member_declarations.py"
    shutil.copyfile(ROOT / "tests/validators/member_declarations.py", declarations)
    audit = tmp_path / "actual-reader.json"
    driver = tmp_path / "private-observer-cli.py"
    driver.write_text(
        "import importlib.util,json,runpy,sys\nfrom pathlib import Path\n"
        f"sys.path.insert(0,{str(helpers)!r})\n"
        "assert 'check_plan_completion' not in sys.modules\n"
        "import completion_minor,check_plan_completion\n"
        f"spec=importlib.util.spec_from_file_location('private_declarations',{str(declarations)!r})\n"
        "declarations=importlib.util.module_from_spec(spec);spec.loader.exec_module(declarations)\n"
        "declarations.apply_to(completion_minor)\n"
        "calls=[]\n"
        "def observe(frame,event,arg):\n"
        " if event=='call' and frame.f_code.co_name in ('resolve_minor_controller','resolve_plan_controller','native_owner_observation'): calls.append([frame.f_code.co_name,frame.f_code.co_filename])\n"
        "sys.setprofile(observe)\n"
        f"spec=importlib.util.spec_from_file_location('installed_snapshot',{str(installed / 'scripts/status_snapshot.py')!r})\n"
        "snapshot=importlib.util.module_from_spec(spec);spec.loader.exec_module(snapshot)\n"
        "result=snapshot.main()\nsys.setprofile(None)\n"
        f"Path({str(audit)!r}).write_text(json.dumps(calls))\n"
        "raise SystemExit(result)\n", encoding="utf-8")
    result = subprocess.run([sys.executable, "-B", str(driver), "--repo", str(fx.work), "--scope", scope,
        "--record", str(path), "--observer-session", observer, "--runs-dir", str(fx.runs)],
        cwd=fx.work, env=fx.env, capture_output=True, text=True, creationflags=FLAGS, timeout=180)
    assert result.returncode == 0, result.stdout + result.stderr
    calls = json.loads(audit.read_text())
    reader = "resolve_minor_controller" if scope.count(".") == 1 else "resolve_plan_controller"
    assert any(name == reader for name, _ in calls)
    assert any(name == "native_owner_observation" for name, _ in calls)
    assert all(Path(file).resolve().parent == helpers for _, file in calls)
    snapshot = json.loads(result.stdout)
    snapshot_path = tmp_path / "snapshot.json"
    snapshot_path.write_text(result.stdout, encoding="utf-8")
    report = subprocess.run([sys.executable, "-B", str(installed / "scripts/status_report.py"),
        "--input", str(snapshot_path), "--json"], cwd=fx.work, env=fx.env,
        capture_output=True, text=True, creationflags=FLAGS, timeout=30)
    assert report.returncode == 0, report.stdout + report.stderr
    pending = json.loads((fx.runs / "pending" / (path.stem + ".json")).read_text())
    assert pending["paste_lines"][0] in json.loads(report.stdout)["report"]
    return snapshot


@pytest.mark.parametrize("resume", [False, True], ids=["same-owner", "pending-observer-resume"])
def test_minor_explicit_observer_cli_preserves_native_owner(minor, monkeypatch, resume):
    import approval_binding
    home = minor.tmp / "private-home"
    home.mkdir()
    for name in ("HOME", "USERPROFILE"):
        monkeypatch.setenv(name, str(home))
        minor.env[name] = str(home)
    minor.env["PYTHONDONTWRITEBYTECODE"] = "1"
    created = minor.create()
    assert created.returncode == 0, created.stdout + created.stderr
    observer = "private-minor-observer" if resume else MINOR_SESSION
    if resume:
        minor.capture(observer, "/implement v0.5")
    rendered = minor.render(observer, "--action", "resume" if resume else "add-class",
        *([] if resume else ["--class", "archive-member"]), "--page")
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    path = minor.record_path()
    record = minor.record()
    assert approval_binding.observe_issued_request(minor.runs, path.stem, ck._secret(False), record,
        rendered.stdout, observer_session=observer)
    sidecar = _save_private_wait(minor, path, "v0.5", observer)
    before = {p: p.read_bytes() for p in (path, sidecar)}
    snapshot = _installed_cli(minor, path, "v0.5", observer, home, minor.tmp)
    assert {p: p.read_bytes() for p in (path, sidecar)} == before
    assert minor.record()["session_id"] == MINOR_SESSION
    if resume:
        assert all(not work["authorized"] for work in snapshot["continuation"]["work"])


@pytest.mark.parametrize("resume", [False, True], ids=["created", "pending-observer-resume"])
def test_schema1_explicit_observer_cli_preserves_native_owner(tmp_path, monkeypatch, resume):
    import approval_binding
    home = tmp_path / "private-home"
    home.mkdir()
    for name in ("HOME", "USERPROFILE"):
        monkeypatch.setenv(name, str(home))
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "1")
    fx, ctx, path = create_owned(tmp_path, monkeypatch)
    observer = "private-plan-observer" if resume else PLAN_SESSION
    if resume:
        _hook(fx, observer, "Resume the existing approved private plan.", permission_mode="bypassPermissions")
    rendered = fx.run("record", "render", PLAN_REL, "--session", observer, "--action",
        "resume" if resume else "pause", "--question", creationflags=FLAGS)
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    record = json.loads(path.read_text())
    page = json.loads(rendered.stdout)["review_page"]
    assert approval_binding.observe_issued_request(fx.runs, path.stem, ck._secret(False), record,
        page, observer_session=observer)
    sidecar = _save_private_wait(fx, path, ctx.plan, observer)
    before = {p: p.read_bytes() for p in (path, sidecar)}
    snapshot = _installed_cli(fx, path, ctx.version, observer, home, tmp_path)
    assert {p: p.read_bytes() for p in (path, sidecar)} == before
    assert json.loads(path.read_text())["session_id"] == PLAN_SESSION
    if resume:
        assert all(not work["authorized"] for work in snapshot["continuation"]["work"])
