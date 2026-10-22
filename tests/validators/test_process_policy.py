"""Shared subprocess defaults preserve APIs and hide real Windows children."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]


def policy():
    spec = importlib.util.spec_from_file_location("process_policy_under_test", ROOT / "scripts" / "nexus_process.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_handles_positional_flags_and_is_idempotent(monkeypatch):
    module = policy()
    observed = []

    class Process:
        def __init__(self, args, bufsize=-1, executable=None, stdin=None, stdout=None, stderr=None,
                     preexec_fn=None, close_fds=True, shell=False, cwd=None, env=None,
                     universal_newlines=None, startupinfo=None, creationflags=0):
            observed.append((args, creationflags))

    fake = SimpleNamespace(Popen=Process, CREATE_NO_WINDOW=0x08000000, DETACHED_PROCESS=8, CREATE_NEW_CONSOLE=16)  # nexus: console-window-ok simulated flags only
    monkeypatch.setattr(module, "subprocess", fake)
    monkeypatch.setattr(module, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr(module, "_batch_command", lambda argv, env: argv)
    assert module.install_no_window_default()
    assert not module.install_no_window_default()
    Process(["git"], -1, None, None, None, None, None, True, False, None, None, None, None, 512)
    assert observed == [(["git"], 0x08000000 | 512)]
    for forbidden in (8, 16):
        with pytest.raises(ValueError, match="CREATE_NO_WINDOW"):
            Process(["git"], creationflags=forbidden)


@pytest.mark.skipif(os.name != "nt", reason="Windows batch shim")
def test_batch_shim_runs_through_hidden_default(tmp_path):
    import subprocess
    shim = tmp_path / "a shim.cmd"
    shim.write_text("@echo off\necho shim-ok %1\n", encoding="ascii")
    result = subprocess.run([str(shim), "literal&value"], capture_output=True, text=True, check=True, timeout=20)
    assert result.stdout.strip() == 'shim-ok "literal&value"'


def test_shared_policy_is_copied_by_both_installers():
    for name in ("installer.ps1", "installer.sh"):
        assert "nexus_process.py" in (ROOT / "scripts" / name).read_text(encoding="utf8")


@pytest.mark.skipif(os.name != "nt", reason="Windows console standard handles")
def test_hidden_forwarding_preserves_stdout_and_stderr():
    import subprocess
    import sys
    script = (
        "import runpy,subprocess,sys; "
        f"runpy.run_path({str(ROOT / 'scripts/nexus_process.py')!r})['install_no_window_default'](); "
        "subprocess.run([sys.executable, '-c', \"import sys;print('child-out');print('child-err',file=sys.stderr)\"],check=True)"
    )
    result = subprocess.run([getattr(sys, "_base_executable", sys.executable), "-B", "-c", script],
                            capture_output=True, text=True, check=True, timeout=30)
    assert result.stdout.strip() == "child-out"
    assert result.stderr.strip() == "child-err"


@pytest.mark.skipif(os.name != "nt", reason="Windows batch forwarding")
def test_batch_forwarder_preserves_a_trailing_backslash(tmp_path):
    import json
    import subprocess
    import sys
    python=getattr(sys, "_base_executable", sys.executable)
    shim=tmp_path / "forward.cmd"
    shim.write_text('@echo off\n"' + python + '" -c "import json,sys;print(json.dumps(sys.argv[1:]))" %*\n', encoding="ascii")
    value="C:\\directory with spaces\\"
    result=subprocess.run([str(shim),value],capture_output=True,text=True,check=True,timeout=20)
    assert json.loads(result.stdout)==[value]



def test_an_older_generic_default_is_upgraded(monkeypatch):
    module=policy()
    observed=[]

    class Process:
        def __init__(self,*args,**kwargs):
            observed.append(kwargs.get("creationflags",0))

    Process.__init__._nexus_no_window=True
    fake=SimpleNamespace(Popen=Process,CREATE_NO_WINDOW=0x08000000,DETACHED_PROCESS=8,CREATE_NEW_CONSOLE=16)  # nexus: console-window-ok simulated flags only
    monkeypatch.setattr(module,"subprocess",fake)
    monkeypatch.setattr(module,"os",SimpleNamespace(name="nt"))
    monkeypatch.setattr(module,"_batch_command",lambda argv,env:argv)
    assert module.install_no_window_default()
    Process(["git"])
    assert observed==[0x08000000]
    assert not module.install_no_window_default()
