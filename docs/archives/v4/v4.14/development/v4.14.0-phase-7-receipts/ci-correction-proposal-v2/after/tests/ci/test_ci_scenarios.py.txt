"""Behavioral controls for disposable CI smoke scenarios."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

from scripts.ci import verify_scenarios as scenarios


def result(argv, text="", code=0):
    return subprocess.CompletedProcess(argv, code, text, "")


@pytest.mark.parametrize("entries,accepted", [([], False), ([{"id": "nexus-hub@nexus-hub", "enabled": False}], False), ([{"id": "nexus-hub@nexus-hub", "enabled": True}] * 2, False), ([{"id": "other", "enabled": True}], False), ([{"id": "nexus-hub@nexus-hub", "enabled": True}], True)])
def test_plugin_acceptance(monkeypatch, tmp_path, entries, accepted):
    monkeypatch.setattr(scenarios, "run", lambda argv, **kwargs: result(argv, json.dumps(entries)))
    if accepted:
        scenarios.plugin(tmp_path, tmp_path, {})
    else:
        with pytest.raises(RuntimeError, match="not installed and enabled"):
            scenarios.plugin(tmp_path, tmp_path, {})


MESSAGES = ("Claude -- commands:ok, skills:ok", "Codex / ChatGPT -- ~/.agents/skills:ok", "Gemini IDE -- GEMINI.md:ok", "Antigravity 2.0 IDE (global) -- skills:ok", "OpenCode -- skills:ok")


@pytest.mark.parametrize("omitted", [None, *range(5)])
def test_registry_acceptance(monkeypatch, tmp_path, omitted):
    monkeypatch.setattr(scenarios.sys, "platform", "win32")
    text = "\n".join(value for index, value in enumerate(MESSAGES) if index != omitted)
    monkeypatch.setattr(scenarios, "run", lambda argv, **kwargs: result(argv, text, 1))
    if omitted is None:
        scenarios.registry(tmp_path, tmp_path, {"HOME": str(tmp_path)})
    else:
        with pytest.raises(RuntimeError, match="read-path not populated"):
            scenarios.registry(tmp_path, tmp_path, {"HOME": str(tmp_path)})


@pytest.mark.parametrize("artifact,version,accepted", [(False, "nexus-hub 4.13.13", False), (True, "wrong output", False), (True, "nexus-hub 4.13.13", True)])
def test_bootstrap_acceptance(monkeypatch, tmp_path, artifact, version, accepted):
    monkeypatch.setattr(scenarios, "catalog_tarball", lambda *args: None)
    original_which = shutil.which
    monkeypatch.setattr(scenarios.shutil, "which", lambda tool, **kwargs: tool if tool in ("node", "npm") else original_which(tool, **kwargs))
    env = {"HOME": str(tmp_path / "home"), "PATH": os.environ["PATH"]}
    def invoke(argv, **kwargs):
        if kwargs["env"].get("PATH") == "":
            return result(argv, "curl required", 1)
        if "--version" in argv:
            return result(argv, version)
        if artifact:
            path = Path(env["HOME"]) / (".nexus-hub/src/scripts/installer.ps1" if os.name == "nt" else ".nexus-hub/src/scripts/installer.sh")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        return result(argv)
    monkeypatch.setattr(scenarios, "run", invoke)
    if accepted:
        scenarios.bootstrap(tmp_path, tmp_path, env)
    else:
        with pytest.raises(RuntimeError):
            scenarios.bootstrap(tmp_path, tmp_path, env)


def test_isolation_keeps_shared_tools_and_shadows_all_editors(monkeypatch, tmp_path):
    shared = tmp_path / "shared-tools"
    shared.mkdir()
    for name in ("code", "cursor", "antigravity", "git"):
        (shared / (name + ".cmd" if os.name == "nt" else name)).write_text("", encoding="ascii")
    monkeypatch.setenv("PATH", str(shared) + os.pathsep + os.environ["PATH"])
    env = scenarios.isolated_environment(tmp_path)
    assert str(shared) in env["PATH"].split(os.pathsep)
    for name in ("code", "code-insiders", "codium", "cursor", "antigravity-ide", "antigravity"):
        command = shutil.which(name, path=env["PATH"])
        assert command and Path(command).parent == tmp_path / "editor-boundary"
    assert Path(env["NPM_CONFIG_PREFIX"]).is_relative_to(tmp_path)
    assert Path(env["UV_TOOL_BIN_DIR"]).is_relative_to(tmp_path)


def test_stale_git_routing_cannot_mutate_external_repository(monkeypatch, tmp_path):
    victim = tmp_path / "external.git"
    subprocess.run(["git", "init", "--bare", "-q", str(victim)], check=True)
    before = (victim / "config").read_bytes()
    for key in ("GIT_COMMON_DIR", "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS"):
        monkeypatch.setenv(key, str(victim))
    private = tmp_path / "private"
    private.mkdir()
    env = scenarios.isolated_environment(private)
    subprocess.run(["git", "init", "-q", str(private / "project")], env=env, check=True)
    assert (victim / "config").read_bytes() == before
    assert not any(key in env for key in ("GIT_COMMON_DIR", "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS"))


@pytest.mark.parametrize("entry", ["../escape.txt", "/outside.txt"])
def test_archive_rejects_escaping_paths(monkeypatch, tmp_path, entry):
    monkeypatch.setattr(scenarios.subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, os.fsencode(entry) + b"\0", b""))
    with pytest.raises(RuntimeError, match="escapes source root"):
        scenarios.catalog_tarball(tmp_path, tmp_path / "catalog.tar.gz", {})


def test_run_failure_and_success_are_distinct(tmp_path):
    env = os.environ.copy()
    assert scenarios.run([sys.executable, "-c", "print('ok')"], env=env, cwd=tmp_path).stdout.strip() == "ok"
    with pytest.raises(RuntimeError, match="command failed"):
        scenarios.run([sys.executable, "-c", "raise SystemExit(7)"], env=env, cwd=tmp_path)
    assert scenarios.run([sys.executable, "-c", "raise SystemExit(7)"], env=env, cwd=tmp_path, allow_failure=True).returncode == 7


@pytest.mark.parametrize("tree_cleanup", [True, False], ids=["process-tree", "parent-only-control"])
def test_timeout_reaps_redirected_grandchild(monkeypatch, tmp_path, tree_cleanup):
    # Release only after cleanup returns: a pre-cleanup write cannot fail this
    # oracle. The parent-only control must prove the surviving child can write.
    marker, ready, release = (tmp_path / name for name in ("escaped-child", "ready", "release"))
    child = (
        "import os,time;from pathlib import Path;"
        f"Path({str(ready)!r}).write_text(str(os.getpid()));"
        f"gate=Path({str(release)!r});"
        "exec('while not gate.exists(): time.sleep(0.01)');"
        f"Path({str(marker)!r}).write_text('escaped')"
    )
    parent = (
        "import subprocess,sys,time;"
        f"subprocess.Popen([sys.executable,'-c',{child!r}],"
        "stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(60)"
    )
    # Bypass the Windows virtualenv launcher shim so parent-only means one PID.
    command = [getattr(sys, "_base_executable", sys.executable), "-c", parent]
    real_popen, real_run = subprocess.Popen, subprocess.run
    parents, child_handles = [], []
    child_pid = None

    def wait_until(predicate):
        deadline = time.monotonic() + 10
        while not predicate():
            if time.monotonic() >= deadline:
                pytest.fail("process boundary did not reach its handshake within 10 seconds")
            time.sleep(0.01)

    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
    else:
        import signal
        real_killpg = os.killpg

    def capture_parent(argv, **kwargs):
        nonlocal child_pid
        proc = real_popen(argv, **kwargs)
        if argv == command:
            parents.append(proc)
            wait_until(lambda: ready.is_file() and bool(ready.read_text(encoding="ascii")))
            child_pid = int(ready.read_text(encoding="ascii"))
            if os.name == "nt":
                handle = kernel.OpenProcess(0x100000, False, child_pid)
                if not handle:
                    raise ctypes.WinError(ctypes.get_last_error())
                child_handles.append(handle)
        return proc

    def child_alive():
        if os.name == "nt":
            state = kernel.WaitForSingleObject(child_handles[0], 0)
            assert state in (0, 258), state
            return state == 258
        state = real_run(["ps", "-o", "stat=", "-p", str(child_pid)], capture_output=True, text=True, check=False)
        return state.returncode == 0 and bool(state.stdout.strip()) and not state.stdout.lstrip().startswith("Z")

    monkeypatch.setattr(scenarios.subprocess, "Popen", capture_parent)
    if not tree_cleanup:
        if os.name == "nt":
            def parent_only(argv, **kwargs):
                return real_run([part for part in argv if part != "/T"], **kwargs)
            monkeypatch.setattr(scenarios.subprocess, "run", parent_only)
        else:
            monkeypatch.setattr(scenarios.os, "killpg", lambda pid, sig: os.kill(pid, sig))
    try:
        with pytest.raises(subprocess.TimeoutExpired):
            scenarios.run(command, env=os.environ.copy(), cwd=tmp_path, timeout=0.2)
        assert child_alive() is (not tree_cleanup)
        release.touch()
        if tree_cleanup:
            assert not marker.exists()
        else:
            wait_until(marker.is_file)
            assert marker.read_text(encoding="ascii") == "escaped"
    finally:
        # Reap this test's intentional survivor; a retained Windows handle keeps
        # the PID tied to that process until the final cleanup has completed.
        if os.name == "nt":
            for proc in parents:
                if proc.poll() is None:
                    real_run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, timeout=10, check=False)
            if child_handles and child_alive():
                real_run(["taskkill", "/PID", str(child_pid), "/T", "/F"], capture_output=True, timeout=10, check=False)
            for handle in child_handles:
                kernel.CloseHandle(handle)
        else:
            for proc in parents:
                try:
                    real_killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        for proc in parents:
            proc.wait(timeout=10)


@pytest.mark.parametrize("missing", ["node", "npm"])
def test_bootstrap_missing_prerequisite_has_no_installer_or_archive_side_effect(monkeypatch, tmp_path, missing):
    monkeypatch.setattr(scenarios.shutil, "which", lambda tool, **kwargs: None if tool == missing else tool)
    def forbidden(*args, **kwargs):
        pytest.fail("bootstrap reached a side effect before prerequisite validation")
    monkeypatch.setattr(scenarios, "catalog_tarball", forbidden)
    monkeypatch.setattr(scenarios, "run", forbidden)
    with pytest.raises(RuntimeError, match="requires preinstalled " + missing):
        scenarios.bootstrap(tmp_path, tmp_path, {"PATH": "fixture-tool-path"})
    assert not (tmp_path / "catalog.tar.gz").exists()
