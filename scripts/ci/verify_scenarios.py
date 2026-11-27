"""Run existing CI smoke scenarios locally with disposable installation targets."""
from __future__ import annotations

import argparse
import hashlib
import uuid
from datetime import datetime, timezone
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TIMEOUT_TAIL_LINES = 200
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.ci import reporting
from scripts.ci.profiles import AUDIT_SCOPES



import runpy as _process_runpy
from pathlib import Path as _ProcessPath

_PROCESS_POLICY = _process_runpy.run_path(str(_ProcessPath(__file__).resolve().parents[1] / "nexus_process.py"))
_PROCESS_POLICY["install_no_window_default"]()


def run(argv: list[str], *, env: dict[str, str], cwd: Path, allow_failure: bool = False, timeout: float = 1200, output_limit: int | None = None) -> subprocess.CompletedProcess[str]:
    # Match the native engine's process-tree boundary, including redirected grandchildren.
    options = ({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {"start_new_session": True})
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        proc = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, **options)
        try:
            proc.wait(timeout=timeout)
        except BaseException as error:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10, check=False)
            else:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            proc.wait(timeout=10)
            if isinstance(error, subprocess.TimeoutExpired):
                # Without this the killed child's output is discarded and a slow step cannot be located.
                for label, stream in (("stdout", stdout), ("stderr", stderr)):
                    stream.seek(0)
                    tail = stream.read().decode("utf-8", errors="replace").splitlines()[-TIMEOUT_TAIL_LINES:]
                    print(f"--- {Path(argv[0]).name} {label} before the {timeout:g}s timeout (last {len(tail)} lines) ---", file=sys.stderr)
                    print("\n".join(tail), file=sys.stderr)
            raise
        stdout.seek(0)
        stderr.seek(0)
        stdout_raw = stdout.read() if output_limit is None else stdout.read(output_limit + 1)
        stderr_raw = stderr.read() if output_limit is None else stderr.read(output_limit + 1)
        if output_limit is not None and (len(stdout_raw) > output_limit or len(stderr_raw) > output_limit):
            raise RuntimeError("scanner capture exceeds output limit")
        result = subprocess.CompletedProcess(argv, proc.returncode, stdout_raw.decode("utf-8", errors="replace"), stderr_raw.decode("utf-8", errors="replace"))
    if result.returncode and not allow_failure:
        raise RuntimeError(f"command failed ({result.returncode}): {argv[0]}\n{result.stdout}\n{result.stderr}")
    return result


def isolated_environment(work: Path) -> dict[str, str]:
    env = dict(os.environ)
    home = work / "home"
    home.mkdir()
    targets = {"HOME": home, "USERPROFILE": home, "NEXUS_HUB_HOME": home / ".nexus-hub", "CLAUDE_CONFIG_DIR": home / ".claude", "GIT_CONFIG_GLOBAL": work / "gitconfig", "APPDATA": work / "appdata", "LOCALAPPDATA": work / "localappdata", "PROGRAMFILES": work / "programfiles", "PROGRAMFILES(X86)": work / "programfiles32", "XDG_CONFIG_HOME": work / "xdg-config", "XDG_DATA_HOME": work / "xdg-data"}
    for key, path in targets.items():
        env[key] = str(path)
        if key != "GIT_CONFIG_GLOBAL":
            path.mkdir(parents=True, exist_ok=True)
    # No inherited repository/config selectors may redirect writes outside this root.
    for key in tuple(env):
        if key.upper().startswith(("GIT_", "NEXUS_HUB_", "VSCODE_")) or key.upper() in ("BASH_ENV", "ENV", "PYTHONPATH", "PIP_TARGET", "PIP_PREFIX", "PIP_ROOT", "PIP_PYTHON", "PIP_BUILD_TRACKER", "PIP_LOG", "PIP_LOG_FILE", "PIP_LOCAL_LOG", "PIP_REPORT", "PIP_SRC", "PIP_SOURCE", "PIP_SOURCE_DIR", "PIP_SOURCE_DIRECTORY", "UV_CONFIG_FILE"):
            env.pop(key, None)
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=str(work / "gitconfig"), GIT_CONFIG_SYSTEM=os.devnull, GIT_TEMPLATE_DIR=str(work / "git-template"), NEXUS_HUB_HOME=str(home / ".nexus-hub"), NEXUS_HUB_NO_AUTOSEED="1", PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1", PIP_DISABLE_PIP_VERSION_CHECK="1", PIP_CONFIG_FILE=os.devnull, UV_NO_CONFIG="1")
    for key, folder in (("NPM_CONFIG_PREFIX", "npm-prefix"), ("NPM_CONFIG_CACHE", "npm-cache"), ("PIP_CACHE_DIR", "pip-cache"), ("PYTHONUSERBASE", "python-user"), ("UV_CACHE_DIR", "uv-cache"), ("UV_TOOL_DIR", "uv-tools"), ("UV_TOOL_BIN_DIR", "uv-bin"), ("UV_PYTHON_INSTALL_DIR", "uv-python"), ("GIT_TEMPLATE_DIR", "git-template")):
        destination = work / folder
        destination.mkdir()
        env[key] = str(destination)
    # Smoke scenarios do not qualify VSIX delivery or host task migration. Inert
    # launchers stop discovery from reaching host editors or Task Scheduler.
    editors = work / "editor-boundary"
    editors.mkdir()
    for name in ("code", "code-insiders", "codium", "cursor", "antigravity-ide", "antigravity", "schtasks"):
        launcher = editors / (name + ".cmd" if os.name == "nt" else name)
        launcher.write_text("@exit /b 1\n" if os.name == "nt" else "#!/bin/sh\nexit 1\n", encoding="ascii")
        launcher.chmod(0o755)
    env["PATH"] = str(editors) + os.pathsep + env.get("PATH", "")
    return env


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def registry(root: Path, work: Path, env: dict[str, str]) -> None:
    runner = str(root / "scripts/lib/integrations/runner.py")
    # OpenCode is detection-gated (v4.14.7): with no evidence of the tool the
    # installer writes nothing for it, so a bare CI host would fail the OpenCode
    # expectation below. Give the smoke real evidence, a command on PATH, which is
    # what a user's installed OpenCode provides. The stub is only resolved, never run.
    evidence = work / "tool-evidence"
    evidence.mkdir()
    stub = evidence / ("opencode.cmd" if os.name == "nt" else "opencode")
    stub.write_text("@exit /b 1\n" if os.name == "nt" else "#!/bin/sh\nexit 1\n", encoding="ascii")
    stub.chmod(0o755)
    detected = dict(env, PATH=str(evidence) + os.pathsep + env.get("PATH", ""))
    run([sys.executable, runner, "install", "--scope", "global", "--integrations", "claude,codex,gemini,antigravity2,opencode", "--overwrite", "--quiet"], env=detected, cwd=work)
    result = run([sys.executable, runner, "verify", "--target", env["HOME"]], env=detected, cwd=work, allow_failure=True)
    for expected in ("Claude -- commands:ok, skills:ok", "Codex / ChatGPT -- ~/.agents/skills:ok", "Gemini IDE -- GEMINI.md:ok", "Antigravity 2.0 IDE (global) -- skills:ok", "OpenCode -- skills:ok"):
        require(expected in result.stdout, f"read-path not populated: {expected}\n{result.stdout}")
    # The gate itself, on every host: a home with no OpenCode evidence gets no OpenCode files.
    if not shutil.which("opencode", path=env.get("PATH", "")):
        bare = work / "home-without-opencode"
        bare.mkdir()
        bare_env = dict(env, HOME=str(bare), USERPROFILE=str(bare), NEXUS_HUB_HOME=str(bare / ".nexus-hub"))
        run([sys.executable, runner, "install", "--scope", "global", "--target", str(bare), "--integrations", "opencode", "--overwrite", "--quiet"], env=bare_env, cwd=work)
        require(not (bare / ".config" / "opencode").exists(), "an absent OpenCode received global files")
    if sys.platform.startswith("linux"):
        project = work / "project"
        project.mkdir()
        run(["git", "init", "-q", str(project)], env=env, cwd=work)
        run([sys.executable, runner, "init", "--target", str(project), "--quiet"], env=env, cwd=work)
        require(any((project / ".agents/workflows").iterdir()), "project init did not seed workflows")
    print("OK: global registry read-paths (OpenCode detected through a stub command, gated off without one) and host-specific project seed")


def workspace(root: Path, work: Path, env: dict[str, str]) -> None:
    target = work / "workspace"
    target.mkdir()
    run([sys.executable, str(root / "scripts/nexus_hub_cli.py"), "org", "connect", str(root / "configs/examples/org-bundle-example"), "--force"], env=env, cwd=work)
    command = (["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(root / "scripts/installer.ps1"), "-Workspace", str(target), "-Platforms", "claude", "-Yes"] if os.name == "nt" else ["bash", str(root / "scripts/installer.sh"), "--workspace", str(target), "--platforms", "claude", "--yes"])
    run(command, env=env, cwd=work)
    run([sys.executable, str(root / "scripts/check_installer_smoke.py"), "--home", env["HOME"], "--workspace", str(target), "--source", str(root)], env=env, cwd=work)
    print("OK: real native workspace installer and shared smoke assertions")


def catalog_tarball(root: Path, target: Path, env: dict[str, str]) -> None:
    result = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=root, env=env, capture_output=True, check=True)
    with tarfile.open(target, "w:gz") as archive:
        for item in sorted(set(result.stdout.split(b"\0")) - {b""}):
            relative = Path(os.fsdecode(item))
            source = root / relative
            require(not relative.is_absolute() and ".." not in relative.parts and source.resolve().is_relative_to(root.resolve()), "catalog path escapes source root")
            if source.is_file():
                archive.add(source, arcname="Nexus-Hub-main/" + relative.as_posix(), recursive=False)


def bootstrap(root: Path, work: Path, env: dict[str, str]) -> None:
    # The full installer can install missing tools through a host package manager.
    # Redirected HOME/cache paths do not contain those OS-level installations.
    for tool in ("node", "npm"):
        require(bool(shutil.which(tool, path=env.get("PATH", ""))), f"bootstrap smoke requires preinstalled {tool}; host package installation is disabled")
    tarball = work / "catalog.tar.gz"
    catalog_tarball(root, tarball, env)
    # Optional VSIX/npm delivery is outside this smoke; never fetch missing packages.
    env.update(NEXUS_HUB_FORCE_STANDALONE="1", NEXUS_HUB_TARBALL=str(tarball), NPM_CONFIG_OFFLINE="true")
    command = (["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(root / "install.ps1")] if os.name == "nt" else ["bash", str(root / "install.sh")])
    result = run(command, env=env, cwd=work, allow_failure=True)
    home = Path(env["HOME"]) / ".nexus-hub"
    suffix = "ps1" if os.name == "nt" else "sh"
    require((home / f"src/scripts/installer.{suffix}").is_file(), f"standalone source was not extracted; bootstrap exit {result.returncode}\n{result.stdout}\n{result.stderr}")
    checked_payload = 0
    with tarfile.open(tarball, "r:gz") as archive:
        for member in archive.getmembers():
            relative = Path(member.name).relative_to("Nexus-Hub-main")
            if not member.isfile() or relative.parts[:2] not in (("catalog", "skills"), ("catalog", "commands")):
                continue
            cached = home / "src" / relative
            require(cached.is_file(), f"bootstrap catalog payload is missing: {relative}")
            with archive.extractfile(member) as payload:
                require(cached.read_bytes() == payload.read(), f"bootstrap catalog payload differs: {relative}")
            checked_payload += 1
    require(checked_payload > 0, "bootstrap archive contains no catalog payload")
    launcher = home / ("bin/nexus-hub.cmd" if os.name == "nt" else "bin/nexus-hub")
    version_command = [str(launcher), "--version"] if launcher.is_file() and (os.name == "nt" or os.access(launcher, os.X_OK)) else [sys.executable, str(home / "src/scripts/nexus_hub_cli.py"), "--version"]
    version = run(version_command, env=env, cwd=work)
    require(re.search(r"nexus-hub [0-9]+\.[0-9]+\.[0-9]+", version.stdout) is not None, "unexpected CLI version")
    if os.name != "nt":
        bash = shutil.which("bash")
        require(bool(bash), "bash unavailable")
        missing_env = dict(env, PATH="")
        missing = run([str(bash), str(root / "install.sh")], env=missing_env, cwd=work, allow_failure=True)
        require(missing.returncode != 0 and "curl" in (missing.stdout + missing.stderr).lower(), "missing-tool path did not refuse clearly")
        check_env = dict(env, NEXUS_HUB_PRECHECK_ONLY="1")
        run(["pwsh", "-NoProfile", "-File", str(root / "install.ps1")], env=check_env, cwd=work)
    print("OK: standalone bootstrap extraction, native CLI version and host-specific prechecks")


def plugin(root: Path, work: Path, env: dict[str, str]) -> None:
    run(["claude", "plugin", "marketplace", "add", str(root)], env=env, cwd=work)
    run(["claude", "plugin", "install", "nexus-hub@nexus-hub"], env=env, cwd=work)
    result = run(["claude", "plugin", "list", "--json"], env=env, cwd=work)
    installed = json.loads(result.stdout)
    matches = [item for item in installed if item.get("id") == "nexus-hub@nexus-hub"]
    require(len(matches) == 1 and matches[0].get("enabled") is True, "plugin is not installed and enabled")
    print("OK: nexus-hub@nexus-hub is installed and enabled")


def cursor_profile(root: Path, work: Path, env: dict[str, str]) -> None:
    # Resolve before the inert smoke boundary, then use both private editor stores.
    cursor = shutil.which("cursor", path=os.environ.get("PATH", ""))
    if not cursor:
        print("SKIP: Cursor CLI absent; require docs/archives/v3/v3.15/development/cursor-usage-live-smoke.md")
        return
    packages = sorted((root / "packed-vsix").glob("*.vsix"))
    require(len(packages) == 1, "expected one downloaded Cursor VSIX under packed-vsix")
    command = [cursor, "--user-data-dir", str(work / "cursor-profile"), "--extensions-dir", str(work / "cursor-extensions")]
    run([*command, "--install-extension", str(packages[0]), "--force"], env=env, cwd=work)
    listed = run([*command, "--list-extensions"], env=env, cwd=work).stdout.splitlines()
    require("nexus-hub.cursor-usage-monitor" in listed, "Cursor monitor is missing from private profile")
    require(not any(name in listed for name in ("nexus-hub.claude-usage-monitor", "nexus-hub.codex-usage-monitor", "nexus-hub.github-usage-monitor")), "VS Code-only monitor appeared in Cursor profile")
    print("OK: Cursor profile installation and host separation")


def presentify_fixtures(root: Path, work: Path, env: dict[str, str]) -> None:
    (work / "AGENTS.md").write_text("Fixture execution root.\n", encoding="utf-8")
    skill = Path("catalog/skills/specialized-domains/document-to-interactive-html")
    shutil.copytree(root / skill, work / skill)
    for minor, names in (("v3.12", ("gen_fixtures.py", "verify_phase1.py", "enrich_models.py", "verify_design_seed.py")), ("v3.13", ("verify_universal_ingestion.py", "verify_imagery.py"))):
        relative = Path(f"docs/archives/v3/{minor}/development/fixtures")
        shutil.copytree(root / relative, work / relative)
        for name in names:
            result = run([sys.executable, str(work / relative / name)], env=env, cwd=work)
            print(name + ": " + (result.stdout.strip().splitlines()[-1] if result.stdout.strip() else "passed"))
    print("OK: extraction, design, universal-ingestion and imagery fixtures in disposable root")


# Fixed CLI adapters: local reports are observations, never hosted qualification.
def _audit_destination(path: Path) -> Path:
    path = path.absolute()
    require(path.resolve() == path, "reports destination must be canonical")
    for component in (path, *path.parents):
        if component.exists() or component.is_symlink():
            require(not component.is_symlink() and not getattr(component.lstat(), "st_file_attributes", 0) & 0x400,
                    "reports destination follows a link or reparse point")
    path.mkdir(parents=True, exist_ok=True)
    security = path / "security"
    if security.exists():
        require(security.is_dir() and not security.is_symlink() and not getattr(security.lstat(), "st_file_attributes", 0) & 0x400,
                "security report destination is not an owned ordinary directory")
    security.mkdir(exist_ok=True)
    return path


def _audit_atomic(path: Path, raw: bytes, reports: Path) -> None:
    require(len(raw) <= 8_000_000, "audit output exceeds its byte limit")
    _audit_destination(reports)
    if path.exists() or path.is_symlink():
        reporting._measurement_bytes(reports, path)
    descriptor, temporary = tempfile.mkstemp(prefix=".audit-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _audit_json(path: Path, value: dict, reports: Path) -> None:
    _audit_atomic(path, (json.dumps(value, sort_keys=True, indent=2) + "\n").encode(), reports)


def _audit_analysis_source(root: Path, reports: Path, env: dict[str, str]) -> dict:
    """Version 1: sorted checkout paths + NUL + raw SHA256, excluding exact generated reports only."""
    env = {key: value for key, value in env.items() if not key.upper().startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull, GIT_TERMINAL_PROMPT="0")
    def listing(option):
        text = run(["git", "-c", "core.fsmonitor=false", "ls-files", "-z", option], cwd=root, env=env, timeout=20, output_limit=2_000_000).stdout
        require(text.count("\0") <= 20000 and (not text or text.endswith("\0")), "analyzed source inventory exceeds its limit")
        return set(text.split("\0")) - {""}
    tracked, others = listing("--cached"), listing("--others")
    require(len(tracked | others) <= 20000, "analyzed source inventory exceeds its file limit")
    try:
        prefix = reports.absolute().relative_to(root.absolute()).as_posix() + "/"
    except ValueError:
        prefix = None
    def generated(relative):
        if prefix is None or not relative.startswith(prefix) or relative in tracked:
            return False
        tail = relative[len(prefix):]
        if tail in {"summary.json", "summary.md", "metadata/environment.json", "aggregate-index.json", "hosted/codeql-python.json", "hosted/codeql-javascript-typescript.json"}:
            return True
        scopes = "(?:" + "|".join(re.escape(scope) for scope in AUDIT_SCOPES) + ")"
        return bool(re.fullmatch(r"junit/" + scopes + r"\.xml|security/" + scopes + r"\.(?:(?:current|manifest)\.json|[a-f0-9]{32}\.(?:json|txt|sarif|version\.json|packs\.txt))", tail))
    others = {path for path in others if not generated(path)}
    digest, total, count = hashlib.sha256(), 0, 0
    source_suffixes = {".py", ".pyi", ".pyw", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts", ".html", ".htm", ".vue", ".svelte"}
    for relative in sorted(tracked | others):
        path = Path(relative)
        require(not path.is_absolute() and ".." not in path.parts and ".git" not in path.parts, "analyzed source inventory contains an invalid path")
        if relative in others:
            require(path.suffix.lower() in source_suffixes and not any(part.lower() in {".codex", ".claude", "credentials", "profiles"} for part in path.parts[:-1]),
                    "untracked analyzed source identity unavailable; unknown files were not read")
        target = root / path
        size = target.lstat().st_size
        require(size <= 8_000_000 and total + size <= 536_870_912, "analyzed source exceeds its byte limit")
        raw = reporting._measurement_bytes(root, target)
        total += len(raw)
        require(total <= 536_870_912, "analyzed source exceeds its byte limit")
        digest.update(path.as_posix().encode("utf-8") + b"\0" + hashlib.sha256(raw).digest())
        count += 1
    require(count > 0, "analyzed source inventory is empty")
    dirty = run(["git", "-c", "core.fsmonitor=false", "status", "--porcelain", "--untracked-files=no"], cwd=root, env=env, timeout=20, output_limit=2_000_000).stdout.strip()
    return {"schema": "codeql-worktree/1", "sha256": digest.hexdigest(), "files": count, "clean": not dirty and not others}


def _audit_source(root: Path, scope: str, env: dict[str, str]) -> dict:
    observed = run(["git", "rev-parse", "HEAD", "HEAD^{tree}"], cwd=root, env=env, timeout=20).stdout.splitlines()
    require(len(observed) == 2 and all(re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}", item) for item in observed), "source commit/tree unavailable")
    headers = run(["git", "cat-file", "-p", "HEAD"], cwd=root, env=env, timeout=20).stdout.split("\n\n", 1)[0]
    parents = [line.split()[1] for line in headers.splitlines() if line.startswith("parent ")]
    files = ["scripts/ci/profiles.py", "scripts/ci/verify_scenarios.py", "scripts/ci/run.py", "scripts/ci/reporting.py"]
    spec = AUDIT_SCOPES[scope]
    if spec["kind"] == "sarif":
        files += [".github/workflows/codeql.yml", "scripts/ci/codeql-config.yml"]
    elif spec["kind"] in {"npm", "signatures"}:
        files += [".github/workflows/npm-audit.yml", "extensions/" + spec["package"] + "/package-lock.json"]
    else:
        files += [".github/workflows/supply-chain-watch.yml", "scripts/ci/requirements-py311.txt"]
    dirty = run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=root, env=env, timeout=20).stdout.strip()
    return {"head": observed[0], "tree": observed[1], "parents": parents, "worktree_dirty": bool(dirty),
            "files": [{"path": path, "sha256": hashlib.sha256(reporting._measurement_bytes(root, root / path)).hexdigest()} for path in files]}


def _audit_redacted(raw: bytes, *, structured: bool) -> bytes:
    require(len(raw) <= 8_000_000, "audit output exceeds its byte limit")
    if not structured:
        return reporting.redact(raw.decode("utf-8", errors="replace")).encode()
    def clean(value):
        if isinstance(value, str):
            return reporting.redact(value)
        if isinstance(value, list):
            return [clean(item) for item in value]
        if isinstance(value, dict):
            return {key: clean(item) for key, item in value.items()}
        return value
    try:
        return json.dumps(clean(reporting._measurement_json(raw)), sort_keys=True).encode()
    except (ValueError, RecursionError):
        return reporting.redact(raw.decode("utf-8", errors="replace")).encode()


def _audit_pack_identity(text: str, language: str) -> list[dict]:
    target = "codeql/python-queries" if language == "python" else "codeql/javascript-queries"
    pattern = r"^\s*(" + re.escape(target) + r")@([^:\s]+):\s*\(query\)\s+(.+?qlpack\.yml)\s*$"
    matches = [re.fullmatch(pattern, line) for line in text.splitlines()]
    matches = [item for item in matches if item]
    require(len(matches) == 1, "resolved query-pack identity unavailable; provision the exact public bundle first")
    match = matches[0]
    metadata = Path(match[3]).absolute()
    root = metadata.parent
    require(root.resolve() == root, "resolved query pack follows a link")
    paths = sorted(path for path in root.rglob("*") if path.is_file())
    require(0 < len(paths) <= 20000, "resolved query pack exceeds its file limit")
    digest = hashlib.sha256()
    total = 0
    for path in paths:
        raw = reporting._measurement_bytes(root, path)
        total += len(raw)
        require(total <= 536_870_912, "resolved query pack exceeds its byte limit")
        digest.update(path.relative_to(root).as_posix().encode() + b"\0" + hashlib.sha256(raw).digest())
    metadata_raw = reporting._measurement_bytes(root, metadata)
    return [{"name": match[1], "version": match[2], "content_sha256": digest.hexdigest(),
             "metadata_sha256": hashlib.sha256(metadata_raw).hexdigest()}]


def audit_scenario(scope: str, root: Path, work: Path, env: dict[str, str], reports_arg: Path) -> int:
    """One invocation, one fresh staging root and one terminal manifest written last."""
    spec = AUDIT_SCOPES[scope]
    invocation = uuid.uuid4().hex
    print(reporting.AUDIT_PACKET + json.dumps({"scope": scope, "invocation_id": invocation}), flush=True)
    reports = _audit_destination(reports_arg)
    current_path = reports / "security" / (scope + ".current.json")
    manifest_path = reports / "security" / (scope + ".manifest.json")
    manifest = {"schema": reporting.AUDIT_SCHEMA, "scope": scope, "invocation_id": invocation, "status": "running",
                "source": {}, "outputs": [], "output_valid": False, "scanner_exit_code": None,
                "started_at": datetime.now(timezone.utc).isoformat(), "tool": {"name": spec["tool"], "version": "Unavailable (not observed)"}}
    primary = work / "scanner-output"
    extra = []
    code = 1
    try:
        _audit_json(current_path, manifest, reports)
        _audit_json(manifest_path, manifest, reports)
        manifest["source"] = _audit_source(root, scope, env)
        if spec["kind"] == "sarif":
            manifest["source"]["analysis"] = _audit_analysis_source(root, reports, env)
            manifest["source"]["worktree_dirty"] |= not manifest["source"]["analysis"]["clean"]
        manifest["source_sha256"] = hashlib.sha256(json.dumps(manifest["source"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if spec["kind"] == "sarif":
            language = spec["language"]
            config = root / "scripts/ci/codeql-config.yml"
            manifest.update(language=language, category="/language:" + language,
                            config_sha256=hashlib.sha256(reporting._measurement_bytes(root, config)).hexdigest())
        # Persist a current non-success marker before any scanner or version dispatch.
        _audit_json(current_path, manifest, reports)
        print(reporting.AUDIT_SOURCE_PACKET + json.dumps({"scope": scope, "invocation_id": invocation, "source_sha256": manifest["source_sha256"]}), flush=True)
        if spec["tool"] == "npm":
            executable = shutil.which("npm.cmd" if os.name == "nt" else "npm", path=env.get("PATH"))
            require(bool(executable), "npm executable unavailable")
            version = run([executable, "--version"], cwd=root, env=env, allow_failure=True, timeout=20)
            manifest["tool"]["version"] = version.stdout.strip()[:256] if version.returncode == 0 else "Unavailable (version probe failed)"
            argv = [executable, "audit", "--audit-level=high", "--json"] if spec["kind"] == "npm" else [executable, "audit", "signatures"]
            process = run(argv, cwd=root / "extensions" / spec["package"], env=env, allow_failure=True, timeout=480 if spec["kind"] == "npm" else 60, output_limit=8_000_000)
            code = process.returncode
            manifest["scanner_diagnostic"] = reporting.redact(process.stderr)[:4096]
            primary.write_bytes((process.stdout if spec["kind"] == "npm" else process.stdout + process.stderr).encode())
        elif spec["kind"] == "pip":
            version = run([sys.executable, "-B", "-m", "pip_audit", "--version"], cwd=root, env=env, allow_failure=True, timeout=20)
            manifest["tool"]["version"] = version.stdout.strip()[:256] if version.returncode == 0 else "Unavailable (version probe failed)"
            process = run([sys.executable, "-B", "-m", "pip_audit", "--skip-editable", "--progress-spinner", "off", "--format", "json", "--output", str(primary)],
                          cwd=root, env=env, allow_failure=True, timeout=900, output_limit=8_000_000)
            code = process.returncode
            manifest["scanner_diagnostic"] = reporting.redact(process.stderr)[:4096]
        else:
            executable = Path(env.get("NEXUS_CI_CODEQL", ""))
            require(executable.is_absolute() and executable.is_file() and executable.suffix.lower() not in {".cmd", ".bat"} and os.access(executable, os.X_OK), "explicit provisioned CodeQL executable unavailable")
            executable_raw = reporting._measurement_bytes(executable.parent, executable)
            version = run([str(executable), "version", "--format=json"], cwd=root, env=env, timeout=30, output_limit=8_000_000)
            version_value = reporting._measurement_json(version.stdout.encode())
            require(isinstance(version_value, dict) and isinstance(version_value.get("version"), str), "CodeQL version identity unavailable")
            packs = run([str(executable), "resolve", "packs", "--format=text"], cwd=root, env=env, timeout=30, output_limit=8_000_000)
            manifest["tool"].update(version=version_value["version"], bundle={"version": version_value["version"], "executable_sha256": hashlib.sha256(executable_raw).hexdigest()},
                                    query_packs=_audit_pack_identity(packs.stdout, language))
            extra = [("version", "version.json", version.stdout.encode()), ("packs", "packs.txt", packs.stdout.encode())]
            database = work / "database"
            create = run([str(executable), "database", "create", str(database), "--language=" + language, "--build-mode=none", "--source-root=" + str(root), "--codescanning-config=" + str(config)],
                         cwd=root, env=env, allow_failure=True, timeout=1200, output_limit=8_000_000)
            code = create.returncode
            manifest["scanner_diagnostic"] = reporting.redact(create.stderr)[:4096]
            if code == 0:
                process = run([str(executable), "database", "analyze", str(database), "--format=sarif-latest", "--output=" + str(primary), "--sarif-category=/language:" + language],
                              cwd=root, env=env, allow_failure=True, timeout=1200, output_limit=8_000_000)
                code = process.returncode
                manifest["scanner_diagnostic"] = reporting.redact(process.stderr)[:4096]
        manifest["scanner_exit_code"] = code
        if spec["kind"] == "sarif":
            manifest["analysis_after"] = _audit_analysis_source(root, reports, env)
            require(manifest["analysis_after"] == manifest["source"]["analysis"], "analyzed source changed during CodeQL scan")
        raw = reporting._measurement_bytes(work, primary)
        redacted = _audit_redacted(raw, structured=spec["kind"] != "signatures")
        suffix = {"npm": "json", "pip": "json", "signatures": "txt", "sarif": "sarif"}[spec["kind"]]
        outputs = [("primary", suffix, redacted), *[(role, tail, _audit_redacted(value, structured=role == "version")) for role, tail, value in extra]]
        current = reporting._measurement_json(reporting._measurement_bytes(reports, current_path))
        require(current.get("invocation_id") == invocation, "audit invocation was superseded; no retry or publication")
        for role, suffix, raw in outputs:
            relative = f"security/{scope}.{invocation}.{suffix}"
            _audit_atomic(reports / relative, raw, reports)
            manifest["outputs"].append({"role": role, "path": relative, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
        reporting.audit_payload(redacted, scope, manifest["source"])
        manifest["output_valid"] = True
        manifest["status"] = "complete" if code == 0 else "failed"
    except Exception as error:
        manifest["status"] = "unavailable" if manifest["scanner_exit_code"] is None else "failed"
        manifest["diagnostic"] = reporting.redact(type(error).__name__ + ": " + str(error))[:1024]
        if code == 0:
            code = 1
    finally:
        manifest["completed_at"] = datetime.now(timezone.utc).isoformat()
        try:
            current = reporting._measurement_json(reporting._measurement_bytes(reports, current_path))
            if current.get("invocation_id") == invocation:
                _audit_json(manifest_path, manifest, reports)  # Terminal commit marker is LAST.
            else:
                code = code or 1
                manifest["status"] = "unavailable"
                manifest["diagnostic"] = "Invocation superseded; no current terminal marker committed"
        except (OSError, ValueError, TypeError, KeyError):
            code = code or 1
            manifest["status"] = "unavailable"
            manifest["diagnostic"] = "Current terminal marker could not be committed"
    print(f"audit {scope}: {manifest['status']}; invocation {invocation}")
    if manifest["status"] != "complete":
        print(reporting.redact(str(manifest.get("diagnostic") or manifest.get("scanner_diagnostic") or f"scanner exit {manifest['scanner_exit_code']}"))[:1024])
    return code

def main(argv: list[str] | None = None) -> int:
    tasks = {"registry": registry, "workspace": workspace, "bootstrap": bootstrap, "plugin": plugin, "cursor-profile": cursor_profile, "presentify-fixtures": presentify_fixtures}
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=[*tasks, *AUDIT_SCOPES])
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--reports-dir", type=Path)
    args = parser.parse_args(argv)
    if args.scenario in AUDIT_SCOPES:
        if args.reports_dir is None and os.environ.get("NEXUS_CI_REPORTS_DIR"):
            args.reports_dir = Path(os.environ["NEXUS_CI_REPORTS_DIR"])
        require(args.root.resolve() == ROOT.resolve(), "audit source must be the exact scenario checkout")
        require(args.reports_dir is not None, "audit scenario requires --reports-dir")
    elif args.reports_dir is not None:
        parser.error("--reports-dir belongs only to audit export scenarios")
    require((args.root / "AGENTS.md").is_file(), "repository root has no AGENTS.md")
    with tempfile.TemporaryDirectory(prefix="nexus-ci-scenario-") as scratch:
        work = Path(scratch).resolve()
        env = isolated_environment(work)
        if args.scenario in AUDIT_SCOPES:
            for key in tuple(env):
                if any(hint in key.upper() for hint in reporting._SECRET_NAME_HINTS) or key.upper() in {"CODEQL_REGISTRIES_AUTH", "PIP_INDEX_URL", "PIP_EXTRA_INDEX_URL", "UV_INDEX_URL"}:
                    env.pop(key, None)
            env.update(NPM_CONFIG_USERCONFIG=os.devnull, NPM_CONFIG_GLOBALCONFIG=os.devnull)
            return audit_scenario(args.scenario, args.root.resolve(), work, env, args.reports_dir)
        tasks[args.scenario](args.root.resolve(), work, env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
