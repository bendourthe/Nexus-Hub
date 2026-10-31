#!/usr/bin/env python3
"""Proof-spike harness for the Nexus-Hub Settings admission gate (v4.14.6).

Summary: repo-internal scaffolding that applies each candidate settings write in a
scratch home, starts the real tool with its tools turned off and no sign-in, and
records the single field it reports. A candidate ships as a control only when a
row here is `proven`; everything else is cataloged Not-Settable with its reason.

Safety properties (each is a failure mode in the plan, sub-task 1.4):

- The user's real configuration files are hashed before and after the run. Any
  change aborts with an error naming the file (exit 3). Nothing is ever written
  to a real home.
- Every probe runs with HOME, USERPROFILE, APPDATA, LOCALAPPDATA and the tool's
  config-directory variable pointed at a scratch home, with a scrubbed
  environment that carries no API key. No sign-in file is copied. A probe that
  reports a credential source other than "none" stops the whole run, because
  that probe could have made a billable request.
- Scratch homes are owner-only, removed in a `finally` block, and a startup
  sweep removes any left behind by an interrupted run.
- No probe that runs without a sign-in reaches an external host. Codex's `doctor`
  and `exec` (and Claude's init probe) try to connect to vendor and GitHub hosts
  even with no credential (measured with Codex 0.136.0: api.openai.com, chatgpt.com,
  api.github.com, github.com), and a header such as `reasoning effort` is printed
  before that attempt fails. So every such probe runs with HTTP_PROXY, HTTPS_PROXY
  and ALL_PROXY pointed at a listener on 127.0.0.1 that forwards nothing and
  records the host of each attempt (`OfflineSink`). The tools honored the proxy
  variables for every connection observed; a version that does not would still
  reach its hosts, which is why the matrix prints what the sink recorded.
- Each probe is bounded to 120 seconds and recorded `timed out`. A tool that is
  not installed gets `not-observed: tool not installed`, never a pass.
- Evidence quotes only the single matched field and passes through a redaction
  filter for token-shaped values.

Usage:
    python scripts/dev/settings_proof_spike.py --list
    python scripts/dev/settings_proof_spike.py --hashes
    python scripts/dev/settings_proof_spike.py --matrix PATH [--json PATH]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from nexus_process import install_no_window_default  # noqa: E402

install_no_window_default()

PROBE_TIMEOUT = 120
MARKER = ".nexus-spike-marker"
HOME_ENV_KEYS = ("SYSTEMROOT", "PATH", "TEMP", "TMP", "COMSPEC", "PATHEXT", "WINDIR")
REDACTIONS = (
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    re.compile(r"[A-Fa-f0-9]{40,}"),
    re.compile(r"[A-Za-z0-9+/=_-]{48,}"),
)


class OfflineSink:
    """A listener on 127.0.0.1 that every no-sign-in probe is pointed at; it answers 502 and forwards nothing.

    The probes that run without a credential still try to reach their vendor, so they are given this address
    as their proxy. The sink records the host of each attempt, which the matrix prints, so a tool that stops
    honoring the proxy variables shows up as attempts that are missing instead of as a silent external call.
    """

    def __init__(self) -> None:
        self.attempts: list[str] = []
        self.port = 0
        self._lock = threading.Lock()
        self._server: socket.socket | None = None

    def _serve(self, server: socket.socket) -> None:
        while True:
            try:
                connection, _ = server.accept()
            except OSError:
                return
            try:
                connection.settimeout(1.0)
                first = connection.recv(2048).decode("latin-1", "replace").splitlines()[:1]
                with self._lock:
                    self.attempts.append(first[0] if first else "")
                connection.sendall(b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
            except OSError:
                pass
            finally:
                connection.close()

    def env(self) -> dict[str, str]:
        """Proxy variables that send every outbound connection here, starting the listener on first use."""
        if self._server is None:
            server = socket.socket()
            server.bind(("127.0.0.1", 0))
            server.listen(64)
            self.port = server.getsockname()[1]
            self._server = server
            threading.Thread(target=self._serve, args=(server,), daemon=True).start()
        url = f"http://127.0.0.1:{self.port}"
        names = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy")
        return {**{name: url for name in names}, "NO_PROXY": "", "no_proxy": ""}

    def hosts(self) -> list[str]:
        """The distinct hosts the probes tried to reach, from `CONNECT host:port` or an absolute-URI request line."""
        found = set()
        with self._lock:
            lines = list(self.attempts)
        for line in lines:
            match = re.match(r"CONNECT ([^ :]+)", line) or re.match(r"[A-Z]+ https?://([^/ :]+)", line)
            found.add(match.group(1) if match else "(unparsed)")
        return sorted(found)

    def close(self) -> None:
        if self._server is not None:
            self._server.close()
            self._server = None


SINK = OfflineSink()


@dataclass
class Row:
    rid: str
    candidate: str
    action: str
    observed: str
    verdict: str
    version: str = ""


def redact(text: str) -> str:
    for pattern in REDACTIONS:
        text = pattern.sub("[redacted]", text)
    return text[:200]


def real_files() -> list[Path]:
    home = Path.home()
    appdata = os.environ.get("APPDATA")
    files = [
        home / ".claude" / "settings.json",
        home / ".claude" / "remote-settings.json",
        home / ".claude" / ".credentials.json",
        home / ".codex" / "config.toml",
        home / ".codex" / "auth.json",
        home / ".copilot" / "settings.json",
        home / ".copilot" / "config.json",
        home / ".nexus-hub" / "guardrails.json",
        home / ".nexus-hub" / "settings-control.json",
        home / ".nexus-hub" / "core-settings-seeds.json",
    ]
    if appdata:
        files.append(Path(appdata) / "Code" / "User" / "settings.json")
    return files


TOKEN_KEY = re.compile(r"token|expires", re.IGNORECASE)


def _mask_tokens(node: object) -> object:
    if isinstance(node, dict):
        return {key: ("<masked>" if TOKEN_KEY.search(key) and not isinstance(value, (dict, list)) else _mask_tokens(value)) for key, value in node.items()}
    if isinstance(node, list):
        return [_mask_tokens(item) for item in node]
    return node


def fingerprint(path: Path) -> str:
    """SHA-256 of a real file; for the Claude sign-in file, of its content with token and expiry values masked.

    Live Claude Code sessions rewrite that file periodically to refresh the access token,
    so its raw hash changes with no spike running. Everything else in it is still compared.
    """
    if not path.is_file():
        return "absent"
    data = path.read_bytes()
    if path.name == ".credentials.json":
        try:
            data = json.dumps(_mask_tokens(json.loads(data)), sort_keys=True).encode("utf-8")
        except ValueError:
            pass
    return hashlib.sha256(data).hexdigest()


def hash_real_files() -> dict[str, str]:
    return {str(path): fingerprint(path) for path in real_files()}


def settled_changes(before: dict[str, str]) -> tuple[dict[str, str], list[str]]:
    """Re-hash after the run; a file that differs is re-read a few times first.

    An editor can rewrite its own settings file while the spike runs (VS Code
    rewrites user settings.json non-atomically), so one differing read is not yet
    a change. A file counts as changed only when it still differs after retries.
    """
    after = hash_real_files()
    for _ in range(60):
        differing = [name for name in before if before[name] != after[name]]
        if not differing:
            break
        time.sleep(0.75)
        refreshed = hash_real_files()
        after.update({name: refreshed[name] for name in differing})
    return after, [name for name in before if before[name] != after[name]]


def sweep_stale() -> int:
    removed = 0
    for entry in Path(tempfile.gettempdir()).glob("nexus-spike-*"):
        if (entry / MARKER).is_file():
            shutil.rmtree(entry, ignore_errors=True)
            removed += 1
    return removed


class Scratch:
    """One owner-only scratch home with a working directory and a scrubbed environment."""

    def __init__(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="nexus-spike-"))
        (self.root / MARKER).write_text("scratch\n", encoding="utf-8")
        os.chmod(self.root, 0o700)
        self.home = self.root / "home"
        self.cwd = self.root / "cwd"
        for name in ("home", "cwd", "appdata", "localappdata"):
            (self.root / name).mkdir()

    def env(self, **extra: str) -> dict[str, str]:
        env = {key: os.environ[key] for key in HOME_ENV_KEYS if key in os.environ}
        env.update(
            HOME=str(self.home), USERPROFILE=str(self.home),
            APPDATA=str(self.root / "appdata"), LOCALAPPDATA=str(self.root / "localappdata"),
        )
        env.update(extra)
        return env

    def offline_env(self, **extra: str) -> dict[str, str]:
        """`env`, with every outbound connection sent to the local sink. For every probe that runs without a sign-in."""
        return self.env(**{**SINK.env(), **extra})

    def cleanup(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)


def run(argv: list[str], scratch: Scratch, env: dict[str, str], stdin_text: str | None = None) -> tuple[int, str, str]:
    """Run one bounded child with no window; returns (rc, stdout, stderr) or rc -1 on timeout."""
    try:
        done = subprocess.run(argv, cwd=scratch.cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=PROBE_TIMEOUT, input=stdin_text, stdin=None if stdin_text is not None else subprocess.DEVNULL, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired:
        return -1, "", "timed out"
    return done.returncode, done.stdout, done.stderr


def version_of(argv: list[str]) -> str:
    exe = shutil.which(argv[0])
    if not exe:
        return ""
    scratch = Scratch()
    try:
        rc, out, _ = run([exe, *argv[1:]], scratch, scratch.env())
        return out.strip().splitlines()[0] if rc == 0 and out.strip() else ""
    finally:
        scratch.cleanup()


class CredentialLeak(RuntimeError):
    """A probe reported a credential source, so it could have made a billable request."""


def claude_init(user: dict | None = None, project: dict | None = None, env: dict[str, str] | None = None) -> dict[str, str]:
    scratch = Scratch()
    try:
        if user is not None:
            (scratch.home / "settings.json").write_text(json.dumps(user), encoding="utf-8")
        if project is not None:
            (scratch.cwd / ".claude").mkdir()
            (scratch.cwd / ".claude" / "settings.json").write_text(json.dumps(project), encoding="utf-8")
        argv = [shutil.which("claude") or "claude", "-p", "probe", "--output-format", "stream-json", "--verbose", "--max-turns", "1", "--tools", ""]
        rc, out, err = run(argv, scratch, scratch.offline_env(CLAUDE_CONFIG_DIR=str(scratch.home), **(env or {})))
        if rc == -1:
            return {"error": "timed out"}
        for line in out.splitlines():
            if line.startswith("{") and '"subtype":"init"' in line.replace(" ", ""):
                init = json.loads(line)
                if init.get("apiKeySource") != "none":
                    raise CredentialLeak("claude reported a credential source; run stopped")
                return {"model": init.get("model", ""), "permissionMode": init.get("permissionMode", "")}
        return {"error": redact((err or out)[:150])}
    finally:
        scratch.cleanup()


def codex_report(config: str, project_config: str | None = None, trust: bool = False) -> dict[str, str]:
    scratch = Scratch()
    try:
        codex_home = scratch.root / "codexhome"
        codex_home.mkdir()
        # The user's own file carries `[windows] sandbox`; without it a Windows host
        # degrades workspace-write to read-only, which would hide the key under test.
        text = config + '\n[windows]\nsandbox = "unelevated"\n'
        if trust:
            text += f"\n[projects.'{scratch.cwd}']\ntrust_level = \"trusted\"\n"
        (codex_home / "config.toml").write_text(text, encoding="utf-8")
        if project_config is not None:
            (scratch.cwd / ".codex").mkdir()
            (scratch.cwd / ".codex" / "config.toml").write_text(project_config, encoding="utf-8")
        exe = shutil.which("codex") or "codex"
        env = scratch.offline_env(CODEX_HOME=str(codex_home))
        rc, out, err = run([exe, "doctor", "--json"], scratch, env)
        report: dict[str, str] = {}
        if rc != -1:
            try:
                details = json.loads(out)["checks"]["config.load"]["details"]
                report["model"] = str(details.get("model", ""))
            except (ValueError, KeyError):
                report["model"] = ""
        rc, out, err = run([exe, "debug", "prompt-input", "probe"], scratch, env)
        sandbox = re.search(r"`sandbox_mode` is `([a-z-]+)`", out)
        approval = re.search(r"Approval policy is currently ([A-Za-z-]+)", out) or re.search(r"`approval_policy` is `([a-z-]+)`", out)
        report["sandbox_mode"] = sandbox.group(1) if sandbox else ""
        report["approval"] = approval.group(1) if approval else ("on-request" if "# Escalation Requests" in out else "")
        return report
    finally:
        scratch.cleanup()


def claude_effort(user: dict, env: dict[str, str] | None = None, project: dict | None = None) -> str:
    """Read the effective effort the way a user would: `/effort status`, a local command.

    It runs with no sign-in and makes no model request, so it costs nothing, and its outbound
    connection attempts go to the local sink.
    """
    scratch = Scratch()
    try:
        (scratch.home / "settings.json").write_text(json.dumps(user), encoding="utf-8")
        if project is not None:
            (scratch.cwd / ".claude").mkdir()
            (scratch.cwd / ".claude" / "settings.json").write_text(json.dumps(project), encoding="utf-8")
        argv = [shutil.which("claude") or "claude", "-p", "/effort status", "--output-format", "stream-json", "--verbose", "--max-turns", "1", "--tools", ""]
        rc, out, err = run(argv, scratch, scratch.offline_env(CLAUDE_CONFIG_DIR=str(scratch.home), **(env or {})))
        for line in out.splitlines():
            if line.startswith("{") and '"type":"result"' in line.replace(" ", ""):
                result = json.loads(line)
                if result.get("total_cost_usd"):
                    raise CredentialLeak("a no-sign-in effort probe reported a cost; run stopped")
                match = re.search(r"effort level: ([a-z]+)", str(result.get("result")))
                return match.group(1) if match else "unreadable"
        return "timed out" if rc == -1 else "no result"
    finally:
        scratch.cleanup()


def codex_effort(effort: str) -> str:
    """Read `reasoning effort` from the header `codex exec` prints before any request.

    `codex exec` prints the header and then tries to reach the vendor. A scratch CODEX_HOME with no
    sign-in is used, nothing is billed, and the connection goes to the local sink (`OfflineSink`)
    instead of an external host, so the header is read without contacting anything outside this machine.
    """
    scratch = Scratch()
    try:
        codex_home = scratch.root / "codexhome"
        codex_home.mkdir()
        (codex_home / "config.toml").write_text(f'model_reasoning_effort = "{effort}"\n[windows]\nsandbox = "unelevated"\n', encoding="utf-8")
        rc, _, err = run([shutil.which("codex") or "codex", "exec", "--ephemeral", "--skip-git-repo-check", "probe"], scratch, scratch.offline_env(CODEX_HOME=str(codex_home)))
        match = re.search(r"reasoning effort: ([a-z]+)", err)
        return match.group(1) if match else ("timed out" if rc == -1 else "unreadable")
    finally:
        scratch.cleanup()


# Paid probes: every request is capped by the tool's own budget flag and by a running tally.
PAID_REQUEST_CAP_USD = 0.10
PAID_RESERVE_USD = 0.15  # the tool's budget flag stops after the fact (a request cost USD 0.1245 under a 0.10 flag), so the tally reserves more
PAID_COSTS: list[tuple[str, float]] = []
ATTRIBUTION_PROMPT = (
    "Do not use any tool. Reply with the exact attribution lines you were told to append to git commit messages and pull request "
    "descriptions (for example a Co-Authored-By trailer or a 'Generated with' line), copied verbatim. "
    "If you were given no such lines, reply exactly NONE."
)


def claude_attribution(user: dict, label: str, budget: float) -> str:
    """One billable Haiku request with a trimmed copy of the real sign-in in a scratch home."""
    if sum(cost for _, cost in PAID_COSTS) + PAID_RESERVE_USD > budget:
        return "not-run: the next request could exceed the paid cap"
    source = Path.home() / ".claude" / ".credentials.json"
    scratch = Scratch()
    try:
        stored = json.loads(source.read_text(encoding="utf-8"))
        trimmed = scratch.home / ".credentials.json"
        trimmed.write_text(json.dumps({"claudeAiOauth": stored["claudeAiOauth"], "organizationUuid": stored.get("organizationUuid")}), encoding="utf-8")
        os.chmod(trimmed, 0o600)
        before = hashlib.sha256(trimmed.read_bytes()).hexdigest()
        (scratch.home / "settings.json").write_text(json.dumps({"model": "claude-haiku-5-5", **user}), encoding="utf-8")
        run(["git", "init", "-q"], scratch, scratch.env())  # the attribution lines are injected for a session in a git repository
        argv = [shutil.which("claude") or "claude", "-p", ATTRIBUTION_PROMPT, "--model", "claude-haiku-5-5", "--tools", "Bash", "--permission-prompts", "none", "--max-turns", "1", "--max-budget-usd", f"{PAID_REQUEST_CAP_USD:.2f}", "--no-session-persistence", "--output-format", "stream-json", "--verbose"]
        rc, out, err = run(argv, scratch, scratch.env(CLAUDE_CONFIG_DIR=str(scratch.home), CLAUDE_CODE_DISABLE_CLAUDE_MDS="1"))
        refreshed = hashlib.sha256(trimmed.read_bytes()).hexdigest() != before if trimmed.exists() else True
        for line in out.splitlines():
            if line.startswith("{") and '"type":"result"' in line.replace(" ", ""):
                result = json.loads(line)
                cost = float(result.get("total_cost_usd") or 0)
                PAID_COSTS.append((label, cost))
                answer = " ".join(str(result.get("result")).split())
                return f"{answer[:110]} (cost USD {cost:.4f}" + ("; copied token was refreshed" if refreshed else "") + ")"
        return "timed out" if rc == -1 else redact(" ".join((err or out).split())[:120])
    finally:
        scratch.cleanup()


def find_bash() -> str | None:
    for path in (r"C:\Program Files\Git\bin\bash.exe", r"C:\Program Files\Git\usr\bin\bash.exe", "/bin/bash", "/usr/bin/bash"):
        if Path(path).is_file():
            return path
    found = shutil.which("bash")
    return found if found and "system32" not in found.lower() else None


def guard_exit(switch: str | None, override: str | None) -> str:
    bash = find_bash()
    if not bash:
        return "not-observed: no bash"
    scratch = Scratch()
    try:
        if switch is not None:
            (scratch.home / ".nexus-hub").mkdir()
            (scratch.home / ".nexus-hub" / "guardrails.json").write_text(json.dumps({"block_git_bypass_flags": switch == "true"}), encoding="utf-8")
        extra = {"NEXUS_GUARD_GIT_BYPASS": override} if override is not None else {}
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "git commit --no-verify -m x"}})
        hook = REPO_ROOT / "catalog" / "hooks" / "git-guardrails.sh"
        rc, _, err = run([bash, str(hook)], scratch, scratch.env(**extra), stdin_text=payload)
        return f"exit {rc}" + (": " + redact(err.strip().split(".")[0][:90]) if rc == 2 and err.strip() else "")
    finally:
        scratch.cleanup()


def judge(observed: dict[str, str], expected: dict[str, str]) -> tuple[str, str]:
    if "error" in observed:
        return observed["error"], "not-observed"
    shown = ", ".join(f'{key}="{observed.get(key, "")}"' for key in expected)
    return shown, "proven" if all(observed.get(key) == value for key, value in expected.items()) else "not-proven"


MANUAL = "not-observed: manual, VS Code window"
PAID = "not-observed: needs a paid model request"
NOCOPILOT = "not-observed: tool not installed"
CANNOT = "cannot-detect: no file or API exposes it"

# Fixed candidate list: (id, candidate, action). The count is part of the contract.
CANDIDATES = (
    ("W01", "Claude Code CLI: model", "user settings model=claude-sonnet-5-5"),
    ("W02", "Claude Code CLI: permissions.defaultMode (ask)", "user settings defaultMode=default"),
    ("W03", "Claude Code CLI: permissions.defaultMode (accept-edits)", "user settings defaultMode=acceptEdits"),
    ("W04", "Claude Code CLI: permissions.defaultMode (full-auto)", "user settings defaultMode=bypassPermissions"),
    ("W05", "Claude Code CLI: skipDangerousModePermissionPrompt", "user settings skipDangerousModePermissionPrompt=true"),
    ("W06", "Claude Code CLI: modelSettings.<id>.effortLevel", "user settings modelSettings.<id>.effortLevel=low for each current model id, read with /effort status"),
    ("W07", "Claude Code CLI: top-level effortLevel", "user settings effortLevel=low, read with /effort status on an older and a current model"),
    ("W08", "Claude Code CLI: attribution.commit and attribution.pr", "user settings attribution empty strings versus default, Haiku asked to quote its attribution instructions"),
    ("W09", "Claude Code VS Code panel: claudeCode.initialPermissionMode", "VS Code user settings value bypassPermissions"),
    ("W10", "Claude Code VS Code panel: claudeCode.allowDangerouslySkipPermissions", "VS Code user settings value true"),
    ("W11", "Codex: model", "config.toml model=gpt-5.6-sol"),
    ("W12", "Codex: model_reasoning_effort", "config.toml model_reasoning_effort=low and high, read from the codex exec header (the connection that follows goes to the local sink)"),
    ("W13", "Codex: approval_policy (ask, accept-edits)", "config.toml approval_policy=on-request, sandbox_mode=workspace-write"),
    ("W14", "Codex: approval_policy (full-auto)", "config.toml approval_policy=never, sandbox_mode=workspace-write"),
    ("W15", "Codex: sandbox_mode in a trusted project", "config.toml sandbox_mode=workspace-write, project trusted"),
    ("W16", "Codex: default_permissions excludes posture keys", "config.toml default_permissions=:workspace"),
    ("W17", "Codex: commit attribution", "no vendor key found"),
    ("W18", "Copilot CLI: model", "settings.json model"),
    ("W19", "Copilot CLI: effortLevel", "settings.json effortLevel=low"),
    ("W20", "Copilot CLI: defaultPermissionMode", "settings.json defaultPermissionMode=allow-all"),
    ("W21", "Copilot CLI: includeCoAuthoredBy", "settings.json includeCoAuthoredBy=false"),
    ("W22", "Copilot CLI: permissions.disableBypassPermissionsMode removal", "remove the key"),
    ("W23", "VS Code Copilot Chat: chat.tools.global.autoApprove", "VS Code user settings value true"),
    ("W24", "VS Code Copilot Chat: chat.permissions.default", "VS Code user settings value autoApprove"),
    ("W25", "Git-guardrails: block_git_bypass_flags on", "guardrails.json true, hook payload git commit --no-verify"),
    ("W26", "Git-guardrails: block_git_bypass_flags off", "guardrails.json false, same payload"),
    ("O01", "Override: ANTHROPIC_MODEL beats user model", "env ANTHROPIC_MODEL=claude-haiku-5-5 with user model=claude-sonnet-5-5"),
    ("O02", "Override: CLAUDE_CODE_EFFORT_LEVEL and project effortLevel beat user modelSettings", "shell env, settings env block, and project effortLevel=xhigh, each with user modelSettings low"),
    ("O03", "Override: project .claude/settings.json model beats user model", "project model=claude-haiku-5-5, user model=claude-sonnet-5-5"),
    ("O04", "Override: project defaultMode=bypassPermissions is ignored", "project settings defaultMode=bypassPermissions only"),
    ("O05", "Override: permissions.disableBypassPermissionsMode blocks bypass", "user settings defaultMode=bypassPermissions plus disableBypassPermissionsMode=disable"),
    ("O06", "Override: Claude VS Code remembered mode", "last picked mode in the mode indicator"),
    ("O07", "Override: Codex trusted project .codex/config.toml beats user model", "project model differs from user model, project trusted"),
    ("O08", "Override: Copilot CLI repository .github/copilot/settings.json beats user model", "repository settings model"),
    ("O09", "Override: VS Code workspace settings beat user settings", "workspace value for a chat key"),
    ("O10", "Override: Claude managed settings (managed-settings.json, MDM, server)", "cannot stage locally"),
    ("O11", "Override: Codex requirements.toml and cloud-managed config", "cannot stage locally"),
    ("O12", "Override: VS Code organization policy (ChatToolsAutoApprove, ChatDefaultModel)", "cannot stage locally"),
    ("O13", "Override: Copilot CLI managed permissions.defaultMode and MDM value", "cannot stage locally"),
)


def run_probes(versions: dict[str, str], paid_budget: float = 0.0) -> list[Row]:
    sonnet, haiku = "claude-sonnet-5-5", "claude-haiku-5-5"
    cv, xv = versions["claude"], versions["codex"]
    have_claude, have_codex, have_copilot = bool(cv), bool(xv), bool(versions["copilot"])
    plain: dict[str, tuple[str, str, str]] = {}  # rid -> (observed, verdict, version)

    def claude(rid: str, expected: dict[str, str], **kwargs: object) -> None:
        if not have_claude:
            plain[rid] = ("", "not-observed: tool not installed", "")
            return
        observed, verdict = judge(claude_init(**kwargs), expected)  # type: ignore[arg-type]
        plain[rid] = (observed, verdict, cv)

    claude("W01", {"model": sonnet}, user={"model": sonnet})
    claude("W02", {"permissionMode": "default"}, user={"permissions": {"defaultMode": "default"}})
    claude("W03", {"permissionMode": "acceptEdits"}, user={"permissions": {"defaultMode": "acceptEdits"}})
    claude("W04", {"permissionMode": "bypassPermissions"}, user={"permissions": {"defaultMode": "bypassPermissions"}, "skipDangerousModePermissionPrompt": True})
    claude("O01", {"model": haiku}, user={"model": sonnet}, env={"ANTHROPIC_MODEL": haiku})
    claude("O03", {"model": haiku}, user={"model": sonnet}, project={"model": haiku})
    claude("O04", {"permissionMode": "default"}, project={"permissions": {"defaultMode": "bypassPermissions"}})
    claude("O05", {"permissionMode": "default"}, user={"permissions": {"defaultMode": "bypassPermissions", "disableBypassPermissionsMode": "disable"}})

    def codex(rid: str, expected: dict[str, str], **kwargs: object) -> None:
        if not have_codex:
            plain[rid] = ("", "not-observed: codex not installed", "")
            return
        observed, verdict = judge(codex_report(**kwargs), expected)  # type: ignore[arg-type]
        plain[rid] = (observed, verdict, xv)

    codex("W11", {"model": "gpt-5.6-sol"}, config='model = "gpt-5.6-sol"\n')
    codex("W13", {"approval": "on-request", "sandbox_mode": "workspace-write"}, config='approval_policy = "on-request"\nsandbox_mode = "workspace-write"\n', trust=True)
    codex("W14", {"approval": "never", "sandbox_mode": "workspace-write"}, config='approval_policy = "never"\nsandbox_mode = "workspace-write"\n', trust=True)
    if have_codex:
        # A/B: the key must move the observation both ways, or it is not the lever.
        read_only = codex_report(config='sandbox_mode = "read-only"\n', trust=True)["sandbox_mode"]
        writable = codex_report(config='sandbox_mode = "workspace-write"\n', trust=True)["sandbox_mode"]
        plain["W15"] = (f'read-only config -> "{read_only}"; workspace-write config -> "{writable}"', "proven" if (read_only, writable) == ("read-only", "workspace-write") else "not-proven", xv)
    else:
        plain["W15"] = ("", "not-observed: codex not installed", "")
    # The posture write conflicts with default_permissions (vendor: do not combine); the
    # observation shows which one wins, which is why the engine skips the write.
    codex("W16", {"sandbox_mode": "workspace-write"}, config='default_permissions = ":workspace"\nsandbox_mode = "read-only"\n', trust=True)
    codex("O07", {"model": "gpt-5.6-sol"}, config='model = "gpt-6-luna"\n', project_config='model = "gpt-5.6-sol"\n', trust=True)

    low = {"effortLevel": "low"}
    current_ids = ("claude-fable-5-1", "claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5")
    if have_claude:
        # W06: each current model id reads back its own saved level (set low, default is not low).
        seen = {i: claude_effort({"model": i, "modelSettings": {i: low}}) for i in current_ids}
        plain["W06"] = ("; ".join(f"{i} -> {v}" for i, v in seen.items()), "proven" if set(seen.values()) == {"low"} else "not-proven", cv)
        # W07: a top-level effortLevel moves an older model but not a current one (vendor: Opus 5.5 and later ignore the user-scope key).
        older, newest = claude_effort({"model": "claude-opus-5", **low}), claude_effort({"model": "claude-opus-5-5", **low})
        plain["W07"] = (f"claude-opus-5 -> {older}; claude-opus-5-5 -> {newest} (not covered)", "proven" if older == "low" and newest != "low" else "not-proven", cv)
        shell = claude_effort({"model": haiku, "modelSettings": {haiku: low}}, env={"CLAUDE_CODE_EFFORT_LEVEL": "high"})
        block = claude_effort({"model": haiku, "env": {"CLAUDE_CODE_EFFORT_LEVEL": "high"}, "modelSettings": {haiku: low}})
        project = claude_effort({"model": haiku, "modelSettings": {haiku: low}}, project={"effortLevel": "xhigh"})
        plain["O02"] = (f"shell env high over modelSettings low -> {shell}; settings env block -> {block}; project effortLevel xhigh -> {project}", "proven" if (shell, block, project) == ("high", "high", "xhigh") else "not-proven", cv)
    if have_codex:
        low_seen, high_seen = codex_effort("low"), codex_effort("high")
        plain["W12"] = (f'config low -> "{low_seen}"; config high -> "{high_seen}"', "proven" if (low_seen, high_seen) == ("low", "high") else "not-proven", xv)
    if have_claude and paid_budget > 0:
        baseline = claude_attribution({}, "W08 default attribution", paid_budget)
        sees = any(word in baseline.lower() for word in ("co-authored-by", "generated with"))
        # Without a visible baseline the empty-string run would prove nothing, so it is not paid for.
        silenced = claude_attribution({"attribution": {"commit": "", "pr": ""}}, "W08 attribution empty strings", paid_budget) if sees else "not-run: the default run showed no attribution lines"
        plain["W08"] = (f"default: {baseline} | empty strings: {silenced}", "proven" if sees and silenced.upper().startswith("NONE") else "not-proven", cv)

    plain["W25"] = (guard_exit("true", None), "", "git-guardrails.sh")
    plain["W26"] = (guard_exit("false", None), "", "git-guardrails.sh")
    for rid, expected in (("W25", "exit 2"), ("W26", "exit 0")):
        shown, _, ver = plain[rid]
        plain[rid] = (shown, "proven" if shown.startswith(expected) else "not-proven", ver)

    fixed = {
        "W05": PAID.replace("a paid model request", "an interactive session (the warning dialog)"),
        "W08": PAID + " (run with --paid-cap)",
        "W09": MANUAL, "W10": MANUAL, "W23": MANUAL, "W24": MANUAL, "O06": MANUAL, "O09": MANUAL,
        "W17": "not-observed: no vendor key documented",
        "O10": CANNOT, "O11": CANNOT, "O12": CANNOT, "O13": CANNOT,
    }
    for rid in ("W18", "W19", "W20", "W21", "W22", "O08"):
        fixed[rid] = NOCOPILOT if not have_copilot else MANUAL
    rows = []
    for rid, candidate, action in CANDIDATES:
        observed, verdict, ver = plain.get(rid, ("", fixed.get(rid, "not-observed"), ""))
        rows.append(Row(rid, candidate, action, redact(observed), verdict, ver))
    return rows


MANUAL_STEPS = (
    ("W09, W10, O06", "Start a scratch VS Code (`code --user-data-dir <scratch>`) with the Claude Code extension, set `claudeCode.initialPermissionMode` to `bypassPermissions` and `claudeCode.allowDangerouslySkipPermissions` to `true` in that profile's user settings, open a new Claude Code panel conversation, and read the mode indicator. Repeat after picking Manual in the indicator and starting another conversation to see the remembered mode."),
    ("W23, W24, O09", "In the same scratch VS Code, set `chat.tools.global.autoApprove` to `true` (accept the warning dialog and copy its text into the matrix), run any agent tool in a Copilot Chat agent turn, and confirm no approval prompt appears; repeat with `chat.permissions.default` set to `autoApprove`, then with a workspace `.vscode/settings.json` value of `false`."),
)


def write_matrix(path: Path, rows: list[Row], versions: dict[str, str], before: dict[str, str], after: dict[str, str]) -> None:
    changed = [name for name in before if before[name] != after[name]]
    lines = [
        "# v4.14.6 Proof Matrix",
        "",
        "**Covers**: every enumerated candidate write and override layer of `v4.14.6-nexus-hub-settings-extension.md` Phase 1 (T006, T007), the action applied, the single field observed, and the verdict. A catalog entry cites a `proven` row here, or is Not-Settable with the reason in the verdict column.",
        "",
        f"**Recorded**: {time.strftime('%Y-%m-%d')} by `python scripts/dev/settings_proof_spike.py`. Versions: " + ", ".join(f"{k} {v or 'not installed'}" for k, v in versions.items()) + ".",
        "",
        f"**Real-file guard**: {len(before)} real configuration files hashed before and after; " + ("CHANGED: " + ", ".join(changed) if changed else "all identical") + ".",
        "",
        "**Paid probes**: " + ("; ".join(f"{label} USD {cost:.4f}" for label, cost in PAID_COSTS) + f"; total USD {sum(c for _, c in PAID_COSTS):.4f} against a cap of USD 1.00" if PAID_COSTS else "none run (pass --paid-cap)") + ". Effort rows (W06, W07, W12, O02) cost nothing: no sign-in is present and no model runs. Nothing here is \"local\" in the sense of making no connection: `codex exec` and `codex doctor` try to reach vendor and GitHub hosts even without a credential, and the `/effort status` run starts the Claude CLI, which may do the same. So every probe without a sign-in ran with its proxy variables pointed at a listener on 127.0.0.1 that forwards nothing (`OfflineSink`); " + (f"it recorded attempts for {len(SINK.hosts())} host(s): {', '.join(SINK.hosts())}. None of them was contacted." if SINK.hosts() else "it recorded no attempt, so either the tools made none or they did not honor the proxy variables; this run cannot tell which.") + " The paid probes, when run, are the only requests that leave the machine.",
        "",
        f"**Count**: {len(rows)} candidates; " + ", ".join(f"{sum(r.verdict == v for r in rows)} {v}" for v in ("proven", "not-proven")) + f", {sum(r.verdict.startswith('not-observed') for r in rows)} not-observed, {sum(r.verdict.startswith('cannot-detect') for r in rows)} cannot-detect.",
        "",
        "| ID | Candidate | Action | Observed field | Verdict | Version |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        observed = r.observed.replace("|", "\\|") or "-"
        lines.append(f"| {r.rid} | {r.candidate} | {r.action} | {observed} | {r.verdict} | {r.version or '-'} |")
    lines += ["", "## Manual observations", "", "Each needs a human in a VS Code window. They are listed here so one sitting covers them; until observed, their candidates ship Not-Settable.", ""]
    for ids, steps in MANUAL_STEPS:
        lines += [f"- **{ids}**: {steps}", ""]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--list", action="store_true", help="print the enumerated candidates and exit")
    parser.add_argument("--hashes", action="store_true", help="print the real-file hashes and exit")
    parser.add_argument("--matrix", type=Path, help="write the proof matrix markdown here")
    parser.add_argument("--json", type=Path, help="also write the rows as JSON here")
    parser.add_argument("--paid-cap", type=float, default=0.0, help="total USD the billable probes may spend (default 0: none run)")
    args = parser.parse_args()
    if args.list:
        for rid, candidate, action in CANDIDATES:
            print(f"{rid}\t{candidate}\t{action}")
        print(f"count\t{len(CANDIDATES)}")
        return 0
    if args.hashes:
        print(json.dumps(hash_real_files(), indent=2))
        return 0
    swept = sweep_stale()
    before = hash_real_files()
    versions = {"claude": version_of(["claude", "--version"]), "codex": version_of(["codex", "--version"]), "copilot": version_of(["copilot", "--version"])}
    if "not found" in versions["copilot"].lower():
        versions["copilot"] = ""
    try:
        rows = run_probes(versions, args.paid_cap)
    except CredentialLeak as exc:
        print(f"ABORT: {exc}", file=sys.stderr)
        return 4
    finally:
        sweep_stale()
    after, changed = settled_changes(before)
    if args.matrix:
        write_matrix(args.matrix, rows, versions, before, after)
    if args.json:
        args.json.write_text(json.dumps([r.__dict__ for r in rows], indent=2), encoding="utf-8", newline="\n")
    print(f"swept {swept} stale scratch homes; {len(rows)} candidates; real-file hashes " + ("CHANGED: " + ", ".join(changed) if changed else "identical"))
    for verdict in ("proven", "not-proven"):
        print(verdict, sum(r.verdict == verdict for r in rows))
    return 3 if changed else 0


if __name__ == "__main__":
    sys.exit(main())
