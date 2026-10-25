"""Run existing CI smoke scenarios locally with disposable installation targets."""
from __future__ import annotations

import argparse
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


import runpy as _process_runpy
from pathlib import Path as _ProcessPath

_PROCESS_POLICY = _process_runpy.run_path(str(_ProcessPath(__file__).resolve().parents[1] / "nexus_process.py"))
_PROCESS_POLICY["install_no_window_default"]()


def run(argv: list[str], *, env: dict[str, str], cwd: Path, allow_failure: bool = False, timeout: float = 1200) -> subprocess.CompletedProcess[str]:
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
        result = subprocess.CompletedProcess(argv, proc.returncode, stdout.read().decode("utf-8", errors="replace"), stderr.read().decode("utf-8", errors="replace"))
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
    run([sys.executable, runner, "install", "--scope", "global", "--integrations", "claude,codex,gemini,antigravity2,opencode", "--overwrite", "--quiet"], env=env, cwd=work)
    result = run([sys.executable, runner, "verify", "--target", env["HOME"]], env=env, cwd=work, allow_failure=True)
    for expected in ("Claude -- commands:ok, skills:ok", "Codex / ChatGPT -- ~/.agents/skills:ok", "Gemini IDE -- GEMINI.md:ok", "Antigravity 2.0 IDE (global) -- skills:ok", "OpenCode -- skills:ok"):
        require(expected in result.stdout, f"read-path not populated: {expected}\n{result.stdout}")
    if sys.platform.startswith("linux"):
        project = work / "project"
        project.mkdir()
        run(["git", "init", "-q", str(project)], env=env, cwd=work)
        run([sys.executable, runner, "init", "--target", str(project), "--quiet"], env=env, cwd=work)
        require(any((project / ".agents/workflows").iterdir()), "project init did not seed workflows")
    print("OK: global registry read-paths and host-specific project seed")


def workspace(root: Path, work: Path, env: dict[str, str]) -> None:
    target = work / "workspace"
    target.mkdir()
    run([sys.executable, str(root / "scripts/nexus_hub_cli.py"), "org", "connect", str(root / "configs/examples/org-bundle-example"), "--force"], env=env, cwd=work)
    command = (["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(root / "scripts/installer.ps1"), "-Workspace", str(target), "-Platforms", "claude", "-Yes"] if os.name == "nt" else ["bash", str(root / "scripts/installer.sh"), "--workspace", str(target), "--platforms", "claude", "--yes"])
    run(command, env=env, cwd=work)
    run([sys.executable, str(root / "scripts/check_installer_smoke.py"), "--home", env["HOME"], "--workspace", str(target)], env=env, cwd=work)
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


def main(argv: list[str] | None = None) -> int:
    tasks = {"registry": registry, "workspace": workspace, "bootstrap": bootstrap, "plugin": plugin, "cursor-profile": cursor_profile, "presentify-fixtures": presentify_fixtures}
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=tasks)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    require((args.root / "AGENTS.md").is_file(), "repository root has no AGENTS.md")
    with tempfile.TemporaryDirectory(prefix="nexus-ci-scenario-") as scratch:
        work = Path(scratch).resolve()
        env = isolated_environment(work)
        tasks[args.scenario](args.root.resolve(), work, env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
