"""Completion-gate plugins for OpenCode, OpenClaw, Pi, and Hermes (v4.13.2 Phase 5).

Two kinds of evidence:

  * placement: each integration installs its plugin user-global, only when the
    platform is detected, never with NEXUS_HUB_COMPLETION_PLUGINS=0, and as
    manifest-owned files that teardown removes;
  * behavior: each plugin is EXECUTED against a stub gate core in a throwaway
    home (TypeScript plugins under Node when it is available, Hermes under
    Python) and must continue exactly when the core says so, through that
    platform's documented continuation call.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.lib.integrations import get
from scripts.lib.integrations._completion_plugins import (
    SPECS,
    install_completion_plugin,
)
from scripts.lib.integrations.base import InstallContext
from scripts.lib.integrations.manifest import InstallManifest
from scripts.lib.integrations.openclaw import OpenClawIntegration
from scripts.lib.integrations.result import WriteResult

REPO = Path(__file__).resolve().parents[2]
PLUGINS = REPO / "catalog" / "plugins" / "completion-gate"
TS_PLUGINS = [PLUGINS / "opencode" / "nexus-completion-gate.ts", PLUGINS / "pi" / "nexus-completion-gate.ts",
              PLUGINS / "openclaw" / "index.ts"]
NODE = shutil.which("node")

STUB_CORE = r'''
import json, sys
payload = json.loads(sys.stdin.read() or "{}")
if sys.argv[1:] == ["stop"] and payload.get("session_id") == "s-incomplete":
    print(json.dumps({"decision": "continue", "reason": "incomplete: task.T002"}))
'''


def _ctx(root: Path) -> InstallContext:
    return InstallContext(repo_root=REPO, target_root=root, scope="global", manifest=InstallManifest(),
                          explicit_target=True)


@pytest.fixture
def home(tmp_path: Path) -> Path:
    scripts = tmp_path / "home" / ".nexus-hub" / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "completion_gate.py").write_text(STUB_CORE, encoding="utf-8")
    return tmp_path / "home"


def _env(home: Path, **extra: str) -> dict[str, str]:
    env = dict(os.environ)
    env.update(HOME=str(home), USERPROFILE=str(home), **extra)
    return env


# ----- placement -----------------------------------------------------------


@pytest.mark.parametrize(
    ("key", "detect", "dest"),
    [
        ("pi", ".pi", ".pi/agent/extensions/nexus-completion-gate.ts"),
        ("hermes", ".hermes", ".hermes/plugins/nexus-completion-gate/__init__.py"),
        ("opencode", ".config/opencode", ".config/opencode/plugins/nexus-completion-gate.ts"),
    ],
)
def test_detected_platform_gets_the_plugin_and_teardown_removes_it(tmp_path: Path, monkeypatch, key, detect, dest) -> None:
    monkeypatch.delenv("NEXUS_HUB_COMPLETION_PLUGINS", raising=False)
    (tmp_path / detect).mkdir(parents=True)
    ctx = _ctx(tmp_path)
    get(key).install(ctx)
    assert (tmp_path / dest).is_file()
    get(key).teardown(ctx)
    assert not (tmp_path / dest).exists()


@pytest.mark.parametrize(("key", "dest"), [("pi", ".pi"), ("hermes", ".hermes"), ("opencode", ".config/opencode")])
def test_absent_platform_gets_no_executable_code(tmp_path: Path, key: str, dest: str) -> None:
    get(key).install(_ctx(tmp_path))
    assert not list(tmp_path.rglob("nexus-completion-gate*"))


def test_opt_out_writes_nothing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("NEXUS_HUB_COMPLETION_PLUGINS", "0")
    (tmp_path / ".pi").mkdir()
    get("pi").install(_ctx(tmp_path))
    assert not list(tmp_path.rglob("nexus-completion-gate*"))


def test_openclaw_plugin_layout_and_setup_note(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("NEXUS_HUB_COMPLETION_PLUGINS", raising=False)
    result = WriteResult()
    dest = tmp_path / ".openclaw" / "extensions" / "nexus-completion-gate"
    install_completion_plugin(OpenClawIntegration(), _ctx(tmp_path), "openclaw", dest, result)
    assert {p.name for p in dest.iterdir()} == {"package.json", "openclaw.plugin.json", "index.ts"}
    manifest = json.loads((dest / "openclaw.plugin.json").read_text(encoding="utf-8"))
    assert manifest["id"] == "nexus-completion-gate" and "configSchema" in manifest
    assert json.loads((dest / "package.json").read_text(encoding="utf-8"))["openclaw"]["extensions"] == ["./index.ts"]
    assert any("openclaw plugins enable nexus-completion-gate" in n for n in result.notes)


def test_openclaw_install_global_wires_the_plugin() -> None:
    source = (REPO / "scripts" / "lib" / "integrations" / "openclaw.py").read_text(encoding="utf-8")
    assert "state_dir.is_dir()" in source
    assert 'install_completion_plugin(self, ctx, "openclaw", state_dir / "extensions" / PLUGIN_ID, result)' in source


def test_every_spec_source_exists() -> None:
    for platform, (sources, _, _) in SPECS.items():
        for source in sources:
            assert (PLUGINS / platform / source).is_file(), f"{platform}/{source}"


# ----- static contract -----------------------------------------------------


def _run_gate_block(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    start = text.index("const CORE =")
    end = text.index("\n}\n", text.index("function runGate")) + 3
    return text[start:end]


def test_typescript_plugins_share_one_gate_call() -> None:
    blocks = {_run_gate_block(p) for p in TS_PLUGINS}
    assert len(blocks) == 1


@pytest.mark.parametrize("path", TS_PLUGINS, ids=lambda p: p.parent.name)
def test_typescript_plugins_spawn_without_a_shell_and_import_nothing_third_party(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert "shell: false" in text
    assert "completion_gate.py" in text and '"stop"' in text
    imports = re.findall(r'^import .* from "([^"]+)";', text, re.MULTILINE)
    allowed = {"node:child_process", "node:os", "node:path", "openclaw/plugin-sdk/plugin-entry"}
    assert set(imports) <= allowed, imports
    assert "$`" not in text and "exec(" not in text


# ----- behavior ------------------------------------------------------------

OPENCODE_HARNESS = r'''
const mod = await import(process.argv[2]);
const calls = [];
const client = { session: { prompt: async (args) => calls.push(args) } };
const hooks = await mod.NexusCompletionGate({ client });
for (const id of ["s-incomplete", "s-other"]) {
  await hooks.event({ event: { type: "session.idle", properties: { sessionID: id } } });
}
await hooks.event({ event: { type: "session.status", properties: { sessionID: "s-incomplete" } } });
console.log(JSON.stringify(calls));
'''

PI_HARNESS = r'''
const mod = await import(process.argv[2]);
let handler;
mod.default({ on: (name, fn) => { if (name === "agent_before_settle") handler = fn; } });
const out = [];
for (const id of ["s-incomplete", "s-other"]) {
  out.push(await handler({}, { sessionManager: { getSessionId: () => id } }) ?? null);
}
console.log(JSON.stringify(out));
'''

OPENCLAW_HARNESS = r'''
const mod = await import(process.argv[2]);
let handler;
mod.default.register({ on: (name, fn) => { if (name === "before_agent_finalize") handler = fn; } });
const out = [];
for (const id of ["s-incomplete", "s-other"]) out.push(await handler({}, { sessionId: id }) ?? null);
console.log(JSON.stringify(out));
'''


def _node(tmp: Path, plugin: Path, harness: str, home: Path,
          *, cwd: Path | None = None, env: dict[str, str] | None = None) -> object:
    work = tmp / "plugin"
    work.mkdir()
    target = work / plugin.name
    shutil.copy(plugin, target)
    (work / "harness.mjs").write_text(harness, encoding="utf-8")
    if plugin.parent.name == "openclaw":
        sdk = work / "node_modules" / "openclaw"
        (sdk / "plugin-sdk").mkdir(parents=True)
        (sdk / "package.json").write_text(json.dumps(
            {"name": "openclaw", "type": "module", "exports": {"./plugin-sdk/plugin-entry": "./plugin-sdk/plugin-entry.js"}}),
            encoding="utf-8")
        (sdk / "plugin-sdk" / "plugin-entry.js").write_text("export const definePluginEntry = (entry) => entry;\n",
                                                            encoding="utf-8")
    url = target.resolve().as_uri()
    proc = subprocess.run([NODE, str(work / "harness.mjs"), url], capture_output=True, text=True, timeout=120,
                          cwd=cwd, env=env if env is not None else _env(home), check=False)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout.strip().splitlines()[-1])


pytestmark_node = pytest.mark.skipif(NODE is None, reason="node is not installed")


@pytestmark_node
def test_opencode_prompts_only_for_an_incomplete_session(tmp_path: Path, home: Path) -> None:
    calls = _node(tmp_path, TS_PLUGINS[0], OPENCODE_HARNESS, home)
    assert calls == [{"path": {"id": "s-incomplete"},
                      "body": {"parts": [{"type": "text", "text": "incomplete: task.T002"}]}}]


@pytestmark_node
def test_pi_requests_one_continuation_only_when_incomplete(tmp_path: Path, home: Path) -> None:
    out = _node(tmp_path, TS_PLUGINS[1], PI_HARNESS, home)
    assert out[0]["continue"] is True
    assert out[0]["entries"][0]["content"] == "incomplete: task.T002"
    assert out[1] is None


@pytestmark_node
def test_openclaw_revises_only_when_incomplete(tmp_path: Path, home: Path) -> None:
    out = _node(tmp_path, TS_PLUGINS[2], OPENCLAW_HARNESS, home)
    assert out[0]["action"] == "revise" and out[0]["reason"] == "incomplete: task.T002"
    assert out[0]["retry"]["idempotencyKey"] == "nexus-completion-gate"
    assert out[1] is None


@pytestmark_node
@pytest.mark.skipif(sys.platform != "win32", reason="Windows searches the working directory for bare executables")
@pytest.mark.parametrize(
    ("plugin", "harness"),
    [(TS_PLUGINS[0], OPENCODE_HARNESS), (TS_PLUGINS[1], PI_HARNESS), (TS_PLUGINS[2], OPENCLAW_HARNESS)],
    ids=["opencode", "pi", "openclaw"],
)
def test_typescript_plugins_ignore_a_python_exe_planted_in_the_working_directory(
    tmp_path: Path, home: Path, plugin: Path, harness: str,
) -> None:
    poison = tmp_path / "poison"
    poison.mkdir()
    shutil.copyfile(NODE, poison / "python.exe")
    path = str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", "")
    env = _env(home, PATH=path)
    for key in list(env):
        if key.lower() == "nodefaultcurrentdirectoryinexepath":
            env.pop(key)
    probe = subprocess.run(
        [NODE, "-e", "const {spawnSync}=require('node:child_process'); const r=spawnSync('python',['--version']); process.stdout.write((r.stdout||'').toString()+(r.stderr||'').toString());"],
        cwd=poison, env=env, capture_output=True, text=True, timeout=30, check=False,
    )
    assert probe.stdout.startswith("v"), (probe.returncode, probe.stdout, probe.stderr)
    out = _node(tmp_path, plugin, harness, home, cwd=poison, env=env)
    if plugin.parent.name == "opencode":
        assert len(out) == 1 and out[0]["path"]["id"] == "s-incomplete"
    else:
        assert out[0] is not None


@pytestmark_node
@pytest.mark.skipif(sys.platform != "win32", reason="Windows Python launchers use .exe")
@pytest.mark.parametrize(
    ("plugin", "harness"),
    [(TS_PLUGINS[0], OPENCODE_HARNESS), (TS_PLUGINS[1], PI_HARNESS), (TS_PLUGINS[2], OPENCLAW_HARNESS)],
    ids=["opencode", "pi", "openclaw"],
)
def test_typescript_plugins_try_every_python_before_the_py_fallback(
    tmp_path: Path, home: Path, plugin: Path, harness: str,
) -> None:
    early = tmp_path / "early-path"
    early.mkdir()
    shutil.copyfile(NODE, early / "py.exe")
    path = os.pathsep.join((str(early), str(Path(sys.executable).parent), os.environ.get("PATH", "")))
    out = _node(tmp_path, plugin, harness, home, env=_env(home, PATH=path))
    if plugin.parent.name == "opencode":
        assert len(out) == 1 and out[0]["path"]["id"] == "s-incomplete"
    else:
        assert out[0] is not None


def test_hermes_continues_only_when_incomplete(tmp_path: Path, home: Path) -> None:
    code = (
        "import importlib.util, json, sys\n"
        f"spec = importlib.util.spec_from_file_location('gate', {str(PLUGINS / 'hermes' / '__init__.py')!r})\n"
        "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
        "hooks = {}\n"
        "m.register(type('C', (), {'register_hook': lambda self, n, f: hooks.__setitem__(n, f)})())\n"
        "print(json.dumps([hooks['pre_verify'](session_id=s, coding=True) for s in ('s-incomplete', 's-other')]))\n"
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60,
                          env=_env(home), check=False)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == [{"action": "continue", "message": "incomplete: task.T002"}, None]


def test_hermes_plugin_continues_through_the_real_core(tmp_path: Path) -> None:
    """The plugin-to-core contract end to end: real core, stub checker, bound record."""
    home = tmp_path / "home"
    scripts = home / ".nexus-hub" / "scripts"
    runs = home / ".nexus-hub" / "runs"
    scripts.mkdir(parents=True)
    runs.mkdir(parents=True)
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copy(REPO / "scripts" / "completion_gate.py", scripts / "completion_gate.py")
    (scripts / "check_plan_completion.py").write_text(
        "import sys\n"
        "if sys.argv[1] == 'check':\n    print('INCOMPLETE: task.T002'); sys.exit(1)\n"
        "if sys.argv[1] == 'score':\n    print('1 abc -'); sys.exit(0)\n",
        encoding="utf-8",
    )
    record = {"schema": 1, "session_id": "s-real", "repo_root": str(repo), "plan": "docs/plans/x.md"}
    (runs / "abc.json").write_text(json.dumps(record), encoding="utf-8")
    code = (
        "import importlib.util, json\n"
        f"spec = importlib.util.spec_from_file_location('gate', {str(PLUGINS / 'hermes' / '__init__.py')!r})\n"
        "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
        "print(json.dumps(m._pre_verify(session_id='s-real', coding=True)))\n"
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=120,
                          env=_env(home), check=False)
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert out["action"] == "continue"
    assert "task.T002" in out["message"]
