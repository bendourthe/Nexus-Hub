"""Physical installed reporting copies use the canonical native runtime."""

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from tests.integrations.test_native_owner_continuation import owner, _recovery_with_real_wait

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "catalog/skills/workflow/implement-phase"
FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def load_snapshot(path):
    spec = importlib.util.spec_from_file_location("delivery_snapshot", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("layout", ["source", "junction"])
def test_source_and_windows_junction_resolve_source_native_helpers(tmp_path, monkeypatch, layout):
    def forbidden_home():
        pytest.fail("A resolved source snapshot must not select installed helpers")
    monkeypatch.setattr(Path, "home", forbidden_home)
    if layout == "source":
        assert load_snapshot(SKILL / "scripts/status_snapshot.py").native_scripts_dir() == ROOT / "scripts"
        return
    if os.name != "nt":
        pytest.skip("Windows directory junction control requires Windows")
    link = tmp_path / "private-source-junction"
    script = tmp_path / "create-junction.ps1"
    script.write_text(
        "param([string]$LinkPath,[string]$SourcePath)\n"
        "$ErrorActionPreference='Stop'\n"
        "New-Item -ItemType Junction -Path $LinkPath -Value $SourcePath | Out-Null\n",
        encoding="utf-8-sig")
    try:
        result = subprocess.run(["powershell.exe", "-NoProfile", "-File", str(script), str(link), str(SKILL)],
            capture_output=True, text=True, creationflags=FLAGS, timeout=30)
        assert result.returncode == 0, result.stdout + result.stderr
        assert link.is_junction()
        assert load_snapshot(link / "scripts/status_snapshot.py").native_scripts_dir() == ROOT / "scripts"
    finally:
        if link.is_junction():
            os.rmdir(link)


@pytest.mark.parametrize("relative", [
    ".agents/skills/implement-phase", ".claude/skills/implement-phase",
    ".cursor/skills/implement-phase", ".gemini/skills/implement-phase",
    ".nexus-hub/skills/workflow/implement-phase",
])
def test_physical_installed_copy_uses_home_native_helpers(tmp_path, monkeypatch, relative):
    home = tmp_path / "home"
    copy = home / relative
    shutil.copytree(SKILL, copy)
    monkeypatch.setattr(Path, "home", lambda: home)
    module = load_snapshot(copy / "scripts/status_snapshot.py")
    assert module.native_scripts_dir() == home / ".nexus-hub/scripts"
    assert load_snapshot(SKILL / "scripts/status_snapshot.py").native_scripts_dir() == ROOT / "scripts"


def test_snapshot_cli_without_native_record_executes(tmp_path):
    copy = tmp_path / ".agents/skills/implement-phase"
    shutil.copytree(SKILL, copy)
    overlay = tmp_path / "overlay.json"
    overlay.write_text(json.dumps({"work": [{"id": "package", "title": "Verify the approved runtime packaging",
        "authorized": True, "feasible": True, "evidence": "Private runtime delivery fixture"}]}), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-B", str(copy / "scripts/status_snapshot.py"),
         "--repo", str(ROOT), "--scope", "v4.15", "--overlay", str(overlay)],
        capture_output=True, text=True, creationflags=FLAGS, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert '"scope": "v4.15"' in result.stdout


@pytest.mark.parametrize("relative", [".agents/skills/implement-phase", ".nexus-hub/skills/workflow/implement-phase"])
def test_installed_snapshot_projects_private_native_request_and_renders(owner, monkeypatch, relative):
    """Path/presentation control; owner intentionally stubs the operational reader."""
    home = owner.runs.parent / "home"
    installed = home / relative
    shutil.copytree(SKILL, installed)
    shutil.copytree(ROOT / "scripts", home / ".nexus-hub/scripts", ignore=shutil.ignore_patterns("__pycache__"))
    monkeypatch.setattr(Path, "home", lambda: home)
    scope, frame = _recovery_with_real_wait(owner, "action")
    before = {p: p.read_bytes() for p in owner.runs.rglob("*") if p.is_file()}
    snapshot = load_snapshot(installed / "scripts/status_snapshot.py")
    facts = snapshot.native_owner_projection(owner.path, scope.repo_root, scope.label,
        frame["observation"], frame["disposition"], 7)
    state = snapshot._STATE.reconcile(facts, frame["disposition"])
    spec = importlib.util.spec_from_file_location("delivery_report", installed / "scripts/status_report.py")
    report = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(report)
    assert state["state"] == "waiting_owner_action"
    required = "\n".join(report.required_parts(state))
    assert "Provide the required installed-version proof" in required
    assert owner.pending["paste_lines"][0] not in required
    assert {p: p.read_bytes() for p in owner.runs.rglob("*") if p.is_file()} == before


def test_fresh_installed_snapshot_cli_uses_actual_private_native_reader(tmp_path, monkeypatch):
    from tests.validators.test_completion_minor_record import Minor, SESSION, TRANSPORT_OVERRIDE_ENV, ck
    import approval_binding
    import completion_gate
    import run_plan

    home = tmp_path / "private-home"
    home.mkdir()
    empty_config = tmp_path / "empty.gitconfig"
    empty_config.write_text("", encoding="utf-8")
    for name, value in {"HOME": str(home), "USERPROFILE": str(home),
                        "GIT_CONFIG_GLOBAL": str(empty_config), "GIT_CONFIG_NOSYSTEM": "1",
                        "PYTHONDONTWRITEBYTECODE": "1"}.items():
        monkeypatch.setenv(name, value)
    for name in (*TRANSPORT_OVERRIDE_ENV, "GH_HOST", "NEXUS_RUNNER_LAUNCH"):
        monkeypatch.delenv(name, raising=False)
    minor = Minor(tmp_path, monkeypatch)
    created = minor.create()
    assert created.returncode == 0, created.stdout + created.stderr
    rendered = minor.render(SESSION, "--action", "add-class", "--class", "archive-member", "--page")
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    path = minor.record_path()
    context, record = ck.resolve_minor_controller(path, SESSION, minor_protocol=1, execution_protocol=1)
    assert approval_binding.observe_issued_request(minor.runs, path.stem, ck._secret(False), record, rendered.stdout)
    completion_gate._reconcile_stop({"session_id": SESSION, "hook_event_name": "Stop",
        "last_assistant_message": rendered.stdout}, path, record, context.root,
        1, "INCOMPLETE: private fixture tasks remain", [])
    sidecar = run_plan.continuation_path(path)
    before = {p: p.read_bytes() for p in (path, sidecar)}
    installed = home / ".nexus-hub/skills/workflow/implement-phase"
    helpers = home / ".nexus-hub/scripts"
    shutil.copytree(SKILL, installed)
    shutil.copytree(ROOT / "scripts", helpers, ignore=shutil.ignore_patterns("__pycache__"))
    declarations = tmp_path / "fixture_declarations.py"
    shutil.copyfile(ROOT / "tests/validators/member_declarations.py", declarations)
    audit = tmp_path / "loaded-native-helpers.json"
    driver = tmp_path / "installed-snapshot-cli.py"
    driver.write_text(
        "import importlib.util,json,sys\nfrom pathlib import Path\n"
        f"sys.path.insert(0,{str(helpers)!r})\n"
        "assert 'check_plan_completion' not in sys.modules\n"
        "import completion_minor,check_plan_completion\n"
        f"spec=importlib.util.spec_from_file_location('fixture_declarations',{str(declarations)!r})\n"
        "declarations=importlib.util.module_from_spec(spec);spec.loader.exec_module(declarations)\n"
        "declarations.apply_to(completion_minor)\n"
        "calls=[]\ncontrollers=[]\n"
        "def observe(frame,event,arg):\n"
        " if event=='call' and frame.f_code.co_name=='resolve_minor_controller': calls.append(frame.f_code.co_filename)\n"
        " if event=='call' and frame.f_code.co_name=='native_owner_observation': controllers.append(frame.f_code.co_filename)\n"
        "sys.setprofile(observe)\n"
        f"spec=importlib.util.spec_from_file_location('installed_snapshot',{str(installed / 'scripts/status_snapshot.py')!r})\n"
        "snapshot=importlib.util.module_from_spec(spec);spec.loader.exec_module(snapshot)\n"
        "result=snapshot.main()\nsys.setprofile(None)\n"
        "loaded={name:str(Path(sys.modules[name].__file__).resolve()) for name in "
        "('check_plan_completion','completion_minor')}\n"
        f"Path({str(audit)!r}).write_text(json.dumps(dict(loaded=loaded,reader_calls=calls,controller_calls=controllers)))\n"
        "raise SystemExit(result)\n", encoding="utf-8")
    result = subprocess.run([sys.executable, "-B", str(driver), "--repo", str(minor.work),
        "--scope", "v0.5", "--record", str(path), "--runs-dir", str(minor.runs)],
        cwd=minor.work, env=minor.env, capture_output=True, text=True, creationflags=FLAGS, timeout=180)
    assert result.returncode == 0, result.stdout + result.stderr
    loaded = json.loads(audit.read_text())
    assert loaded["reader_calls"] and all(Path(p).resolve() == helpers / "check_plan_completion.py" for p in loaded["reader_calls"])
    assert loaded["controller_calls"] and all(Path(p).resolve() == helpers / "run_plan.py" for p in loaded["controller_calls"])
    assert all(Path(p).parent == helpers for p in loaded["loaded"].values())
    snapshot_path = tmp_path / "snapshot.json"
    snapshot_path.write_text(result.stdout, encoding="utf-8")
    report = subprocess.run([sys.executable, "-B", str(installed / "scripts/status_report.py"),
        "--input", str(snapshot_path), "--json"], cwd=minor.work, env=minor.env,
        capture_output=True, text=True, creationflags=FLAGS, timeout=30)
    assert report.returncode == 0, report.stdout + report.stderr
    pending = json.loads((minor.runs / "pending" / (path.stem + ".json")).read_text())
    assert pending["paste_lines"][0] in json.loads(report.stdout)["report"]
    assert {p: p.read_bytes() for p in (path, sidecar)} == before


@pytest.mark.parametrize("shell", ["bash", "powershell"])
def test_installer_delivers_complete_common_reporting_tree(tmp_path, shell):
    home = tmp_path / "home"
    home.mkdir()
    source = ROOT / "scripts" / ("installer.sh" if shell == "bash" else "installer.ps1")
    text = source.read_text(encoding="utf-8-sig")
    name = "install_reporting_runtime" if shell == "bash" else "Install-ReportingRuntime"
    assert name in text
    # Extract functions only; never run the installer or inspect the actual home.
    if shell == "bash":
        definitions = []
        for function in ("safe_folder_copy", name):
            start = text.index(function + "() {")
            end = text.index("\n}", start) + 2
            definitions.append(text[start:end])
        script = "\n".join(definitions) + '\nwrite_item() { :; }\nOVERWRITE_ALL=false\n' + name + ' "$1"\n'
        command = [shutil.which("bash"), "-c", script, "fixture", ROOT.as_posix()]
    else:
        script = tmp_path / "delivery.ps1"
        script.write_text(
            "$tokens=$null; $errors=$null\n"
            "$tree=[Management.Automation.Language.Parser]::ParseFile($args[0],[ref]$tokens,[ref]$errors)\n"
            "if ($errors.Count) { throw $errors[0] }\n"
            "foreach ($name in @('Safe-Folder-Copy','Install-ReportingRuntime')) {\n"
            " $node=$tree.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name},$true)\n"
            " if (-not $node) { throw $name }; Invoke-Expression $node.Extent.Text\n}\n"
            "function Write-Item {}\nfunction Restore-Title {}\n"
            "$script:OverwriteMode='MERGE'\nInstall-ReportingRuntime -RepoRoot $args[1]\n",
            encoding="utf-8-sig",
        )
        command = [shutil.which("powershell"), "-NoProfile", "-File", str(script), str(source), str(ROOT)]
    if not command[0]:
        pytest.skip(f"{shell} unavailable")
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    result = subprocess.run(command, env=env, capture_output=True, text=True,
                            creationflags=FLAGS, timeout=60)
    assert result.returncode == 0, result.stderr
    delivered = home / ".nexus-hub/skills/workflow/implement-phase"
    expected = {p.relative_to(SKILL): p.read_bytes() for p in SKILL.rglob("*") if p.is_file()}
    actual = {p.relative_to(delivered): p.read_bytes() for p in delivered.rglob("*") if p.is_file()}
    assert actual == expected
    dispatch = 'install_workspace "$REPO_ROOT"' if shell == "bash" else 'Install-Workspace -RepoRoot $repoRoot'
    call = 'install_reporting_runtime "$REPO_ROOT"' if shell == "bash" else 'Install-ReportingRuntime -RepoRoot $repoRoot'
    assert text.index(call) < text.index(dispatch)
