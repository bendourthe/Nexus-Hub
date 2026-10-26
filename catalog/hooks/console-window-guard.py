#!/usr/bin/env python3
"""
PreToolUse hook: stop console windows from flooding the desktop when tests run on Windows.

On Windows, a console program started by a process that has no console opens a
new, focus-stealing window. A test suite that starts hundreds of git, bash,
PowerShell or Python children from such a process makes the machine unusable
until it finishes. This hook runs before a test command, scans the project for
process launches that can open windows, and blocks the command (exit 2) with the
exact fixes, so the agent repairs the code before the tests run.

Scope:
  - Acts only on Windows (or when NEXUS_CONSOLE_GUARD_PLATFORM=nt, for tests).
  - Checks test, installer, build, and agent helper commands.
  - Off when NEXUS_DISABLED_HOOKS contains console-window-guard, or when
    NEXUS_CONSOLE_GUARD=off.

A deliberate launch is accepted when its launch line carries the marker
`nexus: console-window-ok` followed by a reason.

Part of Nexus-Hub.
"""

from __future__ import annotations

import ast
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterator, NamedTuple

HOOK_NAME = "console-window-guard"
MARKER = "nexus: console-window-ok"
MAX_FILES = 20000
MAX_FILE_BYTES = 1_000_000
MAX_REPORTED = 12
SCAN_BUDGET_SECONDS = 20.0  # past this the scan stops and judges what it has read

SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "env", "__pycache__", ".tox", ".nox", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", "dist", "build", "out", "target", "bin", "obj", "coverage",
    ".next", ".nuxt", "vendor", "site-packages", ".gradle", ".idea", ".vscode-test",
}

TEST_COMMAND = re.compile(
    r"(?:^|[\s;&|(`'\"/\\])(?:"
    r"py\.test|pytest|tox|nox"
    r"|(?:npm|pnpm|yarn|bun)(?:\s+run)?\s+test"
    r"|(?:npx\s+|pnpm\s+exec\s+|yarn\s+)?(?:vitest|jest|mocha|ava)"
    r"|(?:npx\s+)?playwright\s+test"
    r"|go\s+test|cargo\s+(?:test|nextest)|dotnet\s+test|ctest"
    r"|mvn(?:w)?\s+(?:\S+\s+)*test|gradle(?:w)?\s+(?:\S+\s+)*test"
    r"|Invoke-Pester|make\s+test"
    r"|scripts/ci/run\.py"
    r")(?=$|[\s;&|)`'\".:])",
    re.IGNORECASE,
)


BUILD_COMMAND = re.compile(
    r"(?:^|[\s;&|('/\\\"])(?:"
    r"(?:npm|pnpm|yarn|bun)(?:\.cmd)?(?:\s+run)?\s+(?:install|ci|build|rebuild|prepare|pack)"
    r"|(?:pip|pip3|uv)\s+(?:pip\s+)?(?:install|sync|build|run)"
    r"|nexus-hub(?:\.cmd)?\s+(?:upgrade|install|init)|(?:npx\s+)?(?:tsc|webpack|esbuild|rollup|ninja|msbuild)|vite\s+build"
    r"|(?:cargo|dotnet)\s+(?:build|install|publish)|cmake\s+--build|make(?:\s+[^;&|]*)?"
    r"|(?:[^\s;&|]*[/\\])?(?:install(?:er)?|build|setup)[\w.-]*\.(?:py|ps1|sh|cmd|bat)"
    r"|(?:python(?:[0-9.]*)?(?:\.exe)?|py(?:\.exe)?|node(?:\.exe)?|powershell(?:\.exe)?|pwsh(?:\.exe)?|bash(?:\.exe)?|cmd(?:\.exe)?)[\"\']?\s+[^;&|]*\.(?:py|ps1|sh|js|mjs|cjs|cmd|bat)"
    r")(?=$|[\s;&|)\"'])", re.IGNORECASE,
)

PY_LAUNCH = re.compile(
    r"\bsubprocess\.(?:run|Popen|call|check_call|check_output|getoutput|getstatusoutput)\s*\("
    r"|\basyncio\.create_subprocess_(?:exec|shell)\s*\("
    r"|\bos\.(?:system|popen|spawn[lv]p?e?)\s*\("
)
PY_EXPLICIT = re.compile(r"\b(?:DETACHED_PROCESS|CREATE_NEW_CONSOLE)\b|creationflags[\"']?\s*[:=]\s*0x0*(?:8|10)\b")
PS_PSI = re.compile(r"ProcessStartInfo", re.IGNORECASE)
PS_NO_WINDOW = re.compile(r"CreateNoWindow\s*=\s*\$true", re.IGNORECASE)
PS_START_PROCESS = re.compile(r"\bStart-Process\b", re.IGNORECASE)
PS_HIDDEN = re.compile(r"-WindowStyle\s+Hidden|-NoNewWindow", re.IGNORECASE)
JS_LAUNCH = re.compile(
    r"(?<![\w.$])(?:spawn|spawnSync|exec|execSync|execFile|execFileSync|fork)\s*\("
    r"|require\([\"\'](?:node:)?child_process[\"\']\)\.(?:spawn|spawnSync|exec|execSync|execFile|execFileSync|fork)\b"
    r"|\b(?:child_process(?:_\d+)?|childProcess|cp)\.(?:spawn|spawnSync|exec|execSync|execFile|execFileSync|fork)\b"
)
PREFILTER = (b"import os", b"from os", b"import asyncio", b"from asyncio", b"subprocess", b"create_subprocess", b"os.system", b"os.popen", b"os.spawn", b"DETACHED_PROCESS",
             b"CREATE_NEW_CONSOLE", b"creationflags", b"ProcessStartInfo", b"Start-Process", b"child_process",
             b"execa", b"cross-spawn", b"exec.Command")
SUFFIXES = (".py", ".ps1", ".psm1", ".js", ".mjs", ".cjs", ".ts", ".mts", ".cts", ".go")
GO_LAUNCH = re.compile(r"\bexec\.Command(?:Context)?\s*\(")
GO_GUARD = re.compile(r"HideWindow\s*:\s*true|CREATE_NO_WINDOW|0x08000000")
JS_CHILD_PROCESS = re.compile(r"child_process|node:child_process|\bexeca\b|cross-spawn")

CONFTEST_GUARD = '''import runpy
from pathlib import Path
policy = runpy.run_path(str(Path.home() / ".nexus-hub" / "scripts" / "nexus_process.py"))
policy["install_no_window_default"]()'''


class Finding(NamedTuple):
    path: str
    line: int
    rule: str
    fix: str


def _disabled() -> bool:
    disabled = {item.strip() for item in os.environ.get("NEXUS_DISABLED_HOOKS", "").split(",")}
    return HOOK_NAME in disabled or os.environ.get("NEXUS_CONSOLE_GUARD", "").lower() in {"off", "0", "false"}


def _on_windows() -> bool:
    return os.environ.get("NEXUS_CONSOLE_GUARD_PLATFORM", os.name) == "nt"


def is_test_command(command: str) -> bool:
    normalized = re.sub(r"\b(npm|pnpm|yarn|bun)\.cmd\b", r"\1", command or "", flags=re.IGNORECASE).replace("\\", "/")
    return bool(TEST_COMMAND.search(normalized) or BUILD_COMMAND.search(normalized))


def project_root(cwd: Path) -> Path:
    for candidate in (cwd, *cwd.parents):
        if (candidate / ".git").exists():
            return candidate
    return cwd


def _marked(lines: list[str], index: int) -> bool:
    return bool(re.search(re.escape(MARKER) + r"\s+\S", lines[index]))


def _call_text(lines: list[str], index: int) -> str:
    """The call starting on this line, up to its closing parenthesis or 24 lines."""
    text, depth, started = [], 0, False
    for line in lines[index:index + 24]:
        text.append(line)
        for char in line:
            if char == "(":
                depth += 1
                started = True
            elif char == ")":
                depth -= 1
        if started and depth <= 0:
            break
    return "\n".join(text)


def _is_test_file(rel: Path) -> bool:
    name = rel.name.lower()
    parts = {part.lower() for part in rel.parts[:-1]}
    return (name.startswith("test_") or name.endswith(("_test.py", ".test.ts", ".test.js", ".spec.ts", ".spec.js", ".test.mjs"))
            or name == "conftest.py" or bool(parts & {"tests", "test", "__tests__", "e2e"}))


def _default_present(text: str, tree: ast.AST | None = None) -> bool:
    """Recognize an installed default, rather than a flag mentioned in a comment."""
    try:
        tree = tree if tree is not None else ast.parse(text)
    except (SyntaxError, RecursionError):
        return False
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    shared = any(isinstance(node.func, ast.Name) and node.func.id == "install_no_window_default" for node in calls)
    shared_fixture = any(isinstance(node.func, ast.Subscript) and isinstance(node.func.slice, ast.Constant)
                         and node.func.slice.value == "install_no_window_default" for node in calls)
    return ((shared and "nexus_process" in text) or (shared_fixture and "nexus_process.py" in text)
)


def _python_guard_present(files: list[tuple[Path, Path]]) -> set[Path]:
    guarded = set()
    for path, rel in files:
        if rel.name == "conftest.py":
            try:
                if _default_present(path.read_text(encoding="utf-8", errors="replace")):
                    guarded.add(rel.parent)
            except OSError:
                continue
    return guarded


def _javascript_findings(text: str, rel: Path, line_offset: int = 0) -> list[Finding]:
    """Apply the same JavaScript launch policy to source files and literal eval payloads."""
    lines = text.splitlines()
    shown = rel.as_posix()
    findings = []
    if not JS_CHILD_PROCESS.search(text):
        return []
    aliases = re.findall(r"import\s+(?:\*\s+as\s+)?(\w+)\s+from\s+[\"\'](?:node:)?child_process[\"\']", text)
    aliases += re.findall(r"(?:const|let|var)\s+(\w+)\s*=\s*require\([\"\'](?:node:)?child_process[\"\']\)", text)
    named_aliases = []
    for group in re.findall(r"(?:import\s*\{([^}]+)\}\s*from|(?:const|let|var)\s*\{([^}]+)\}\s*=\s*require\()[\s\"\']*(?:node:)?child_process", text):
        for item in (group[0] or group[1]).split(","):
            match = re.fullmatch(r"\s*(?:spawn|spawnSync|exec|execSync|execFile|execFileSync|fork)(?:\s+as\s+|\s*:\s*)(\w+)\s*", item)
            if match:
                named_aliases.append(match.group(1))
    named_launch = re.compile(r"(?<![\w.$])(?:" + "|".join(map(re.escape, named_aliases)) + r")\s*\(") if named_aliases else None
    alias_launch = re.compile(r"\b(?:" + "|".join(map(re.escape, aliases)) + r")\.(?:spawn|spawnSync|exec|execSync|execFile|execFileSync|fork)\s*\(") if aliases else None
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith(("//", "*", "/*")) or _marked(lines, i) or not (JS_LAUNCH.search(line) or alias_launch and alias_launch.search(line) or named_launch and named_launch.search(line)):
            continue
        if not re.search(r"\bwindowsHide\s*:\s*true\b", _call_text(lines, i)):
            findings.append(Finding(shown, line_offset + i + 1, "child_process call without windowsHide",
                                    "Pass { windowsHide: true } in the options object."))
    return findings


def _python_findings(text: str, rel: Path, guarded: bool) -> list[Finding]:
    """Check real calls, including aliases; strings containing examples are not launches."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return [Finding(rel.as_posix(), 1, "Python launch safety cannot be parsed", "Repair the syntax before launching.")]
    lines = text.splitlines()
    modules = {"subprocess"}
    functions = set()
    async_modules = {"asyncio"}
    async_functions = set()
    shutil_modules = {"shutil"}
    os_modules = {"os"}
    os_functions = set()
    assignments = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(item.asname or item.name for item in node.names if item.name == "subprocess")
            async_modules.update(item.asname or item.name for item in node.names if item.name == "asyncio")
            os_modules.update(item.asname or item.name for item in node.names if item.name == "os")
            shutil_modules.update(item.asname or item.name for item in node.names if item.name == "shutil")
        elif isinstance(node, ast.ImportFrom) and node.module == "subprocess":
            functions.update(item.asname or item.name for item in node.names if item.name in {"run", "Popen", "call", "check_call", "check_output", "getoutput", "getstatusoutput"})
            for item in node.names:
                if item.name in {"CREATE_NO_WINDOW", "DETACHED_PROCESS", "CREATE_NEW_CONSOLE"}:
                    assignments[item.asname or item.name] = [ast.Attribute(value=ast.Name(id="subprocess"), attr=item.name)]
        elif isinstance(node, ast.ImportFrom) and node.module == "asyncio":
            async_functions.update(item.asname or item.name for item in node.names if item.name in {"create_subprocess_exec", "create_subprocess_shell"})
        elif isinstance(node, ast.ImportFrom) and node.module == "os":
            os_functions.update(item.asname or item.name for item in node.names if item.name in {"system", "popen"} or item.name.startswith("spawn"))
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            for target in (node.targets if isinstance(node, ast.Assign) else [node.target]):
                if isinstance(target, ast.Name):
                    assignments.setdefault(target.id, []).append(node.value)

    def node_executable(value: ast.AST) -> bool:
        """Recognize literal Node paths and unique literal/which bindings without evaluation."""
        if isinstance(value, ast.Name):
            values = assignments.get(value.id, [])
            value = values[0] if len(values) == 1 else value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            return re.split(r"[/\\]", value.value)[-1].lower() in {"node", "node.exe"}
        return (isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute)
                and isinstance(value.func.value, ast.Name) and value.func.value.id in shutil_modules
                and value.func.attr == "which" and bool(value.args)
                and isinstance(value.args[0], ast.Constant)
                and value.args[0].value in {"node", "node.exe"})

    @lru_cache(maxsize=1024)
    def bag_values(node, seen=frozenset()):
        if len(seen) > 32:
            return None
        if isinstance(node, ast.Name) and node.id not in seen:
            values = assignments.get(node.id, [])
            return bag_values(values[0], seen | {node.id}) if len(values) == 1 else None
        if not isinstance(node, ast.Dict):
            return None
        result = set()
        for key, value in zip(node.keys, node.values):
            if key is None:
                nested = bag_values(value, seen)
                if nested is None:
                    return None
                result.update(nested)
            elif not isinstance(key, ast.Constant):
                return None
            elif key.value == "creationflags":
                result.add(value)
        return frozenset(result)

    @lru_cache(maxsize=1024)
    def safe_value(node, seen=frozenset()):
        if len(seen) > 32:
            return False
        if node is None:
            return False
        if isinstance(node, ast.Name) and node.id not in seen:
            values = assignments.get(node.id, [])
            return len(values) == 1 and safe_value(values[0], seen | {node.id})
        if isinstance(node, ast.IfExp):
            # An empty POSIX options branch is valid; the Windows branch must set the flag.
            branches = (node.body, node.orelse)
            return any(safe_value(value, seen) for value in branches) and all(
                safe_value(value, seen) or isinstance(value, ast.Dict) and not value.keys for value in branches)
        if isinstance(node, ast.Dict):
            values = bag_values(node, seen)
            return bool(values) and all(safe_value(value, seen) for value in values)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            return safe_value(node.left, seen) or safe_value(node.right, seen)
        if isinstance(node, ast.Attribute):
            return node.attr == "CREATE_NO_WINDOW"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "getattr":
            return len(node.args) >= 2 and isinstance(node.args[1], ast.Constant) and node.args[1].value == "CREATE_NO_WINDOW"
        return isinstance(node, ast.Constant) and isinstance(node.value, int) and bool(node.value & 0x08000000)

    @lru_cache(maxsize=1024)
    def unsafe_value(node, seen=frozenset()):
        if len(seen) > 32:
            return False
        if node is None:
            return False
        if isinstance(node, ast.Name) and node.id not in seen:
            values = assignments.get(node.id, [])
            return len(values) == 1 and unsafe_value(values[0], seen | {node.id})
        if isinstance(node, ast.Dict):
            values = bag_values(node, seen)
            return values is not None and any(unsafe_value(value, seen) for value in values)
        if isinstance(node, ast.Attribute):
            return node.attr in {"DETACHED_PROCESS", "CREATE_NEW_CONSOLE"}
        if isinstance(node, ast.Constant):
            return isinstance(node.value, int) and bool(node.value & 0x18)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "getattr":
            return len(node.args) >= 2 and isinstance(node.args[1], ast.Constant) and node.args[1].value in {"DETACHED_PROCESS", "CREATE_NEW_CONSOLE"}
        if isinstance(node, (ast.BinOp, ast.IfExp)):
            return any(unsafe_value(value, seen) for value in ast.iter_child_nodes(node))
        return False

    findings = []
    default = guarded or _default_present(text, tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in modules and node.attr in {"DETACHED_PROCESS", "CREATE_NEW_CONSOLE"} and not _marked(lines, node.lineno - 1):
            findings.append(Finding(rel.as_posix(), node.lineno, "explicit detached or new-console flag", "Use CREATE_NO_WINDOW without conflicting console flags."))
        if not isinstance(node, ast.Call) or _marked(lines, node.lineno - 1):
            continue
        fn = node.func
        launch = (isinstance(fn, ast.Name) and fn.id in functions or isinstance(fn, ast.Attribute)
                  and isinstance(fn.value, ast.Name) and fn.value.id in modules and fn.attr in
                  {"run", "Popen", "call", "check_call", "check_output", "getoutput", "getstatusoutput"})
        os_launch = isinstance(fn, ast.Name) and fn.id in os_functions or (isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name) and fn.value.id in os_modules and (fn.attr in {"system", "popen"} or fn.attr.startswith("spawn")))
        async_launch = (isinstance(fn, ast.Name) and fn.id in async_functions or isinstance(fn, ast.Attribute)
                        and isinstance(fn.value, ast.Name) and fn.value.id in async_modules
                        and fn.attr in {"create_subprocess_exec", "create_subprocess_shell"})
        if os_launch:
            findings.append(Finding(rel.as_posix(), node.lineno, "OS shell launch bypasses the shared subprocess default", "Use the shared hidden subprocess helper instead."))
            continue
        if not (launch or async_launch):
            continue
        # The Python default does not reach Node children launched by literal eval code.
        argv = (node.args[0].elts if node.args and isinstance(node.args[0], (ast.List, ast.Tuple))
                else node.args if async_launch else [])
        for index, value in enumerate(argv[:-1] if argv and node_executable(argv[0]) else []):
            if isinstance(value, ast.Constant) and value.value in {"-e", "--eval"}:
                script = argv[index + 1]
                if isinstance(script, ast.Name):
                    values = assignments.get(script.id, [])
                    script = values[0] if len(values) == 1 else script
                if isinstance(script, ast.Constant) and isinstance(script.value, str) and not _marked(lines, script.lineno - 1):
                    findings.extend(_javascript_findings(script.value, rel, script.lineno - 1))
        if any((key.arg == "creationflags" or key.arg is None) and unsafe_value(key.value) for key in node.keywords):
            findings.append(Finding(rel.as_posix(), node.lineno, "explicit detached or new-console launch",
                                    "Use CREATE_NO_WINDOW without DETACHED_PROCESS or CREATE_NEW_CONSOLE."))
        elif not default and not any((key.arg == "creationflags" or key.arg is None) and safe_value(key.value) for key in node.keywords):
            findings.append(Finding(rel.as_posix(), node.lineno, "process launch without CREATE_NO_WINDOW or a shared default",
                                    "Use the shared process helper, or pass creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)."))
    return findings


def _git_files(root: Path) -> list[str] | None:
    """Tracked plus untracked-but-not-ignored files, so vendored and build output is skipped."""
    if not (root / ".git").exists():
        return None
    flags = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    try:
        result = subprocess.run(["git", "-C", str(root), "ls-files", "-co", "--exclude-standard", "-z"],
                                capture_output=True, timeout=30, check=False, **flags)
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return [item for item in result.stdout.decode("utf-8", "replace").split("\0") if item]


def _candidates(root: Path) -> list[tuple[Path, Path]]:
    listed = _git_files(root)
    if listed is None:
        listed = []
        for current, dirs, names in os.walk(root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".venv")]
            listed.extend(str((Path(current) / name).relative_to(root)) for name in names)
    files = []
    for rel in listed:
        rel_path = Path(rel)
        name = rel_path.name
        if rel_path.parts[0] not in {"docs", "guides"} and name.endswith(SUFFIXES) and not name.endswith(".d.ts") and not set(rel_path.parts[:-1]) & SKIP_DIRS:
            files.append((root / rel_path, rel_path))
            if len(files) >= MAX_FILES:
                break
    return files


def _go_guard_present(files: list[tuple[Path, Path]]) -> bool:
    for path, rel in files:
        if rel.suffix == ".go":
            try:
                if GO_GUARD.search(path.read_text(encoding="utf-8", errors="replace")):
                    return True
            except OSError:
                continue
    return False


def _budget() -> float:
    try:
        return max(1.0, float(os.environ.get("NEXUS_CONSOLE_GUARD_BUDGET", SCAN_BUDGET_SECONDS)))
    except ValueError:
        return SCAN_BUDGET_SECONDS


def _read_candidates(files: list[tuple[Path, Path]]) -> Iterator[tuple[Path, Path, bytes | None, bool]]:
    """Overlap independent file reads in ordered batches with bounded memory."""
    def read(item: tuple[Path, Path]) -> tuple[Path, Path, bytes | None, bool]:
        path, rel = item
        try:
            oversized = path.stat().st_size > MAX_FILE_BYTES
            return path, rel, None if oversized else path.read_bytes(), oversized
        except OSError:
            return path, rel, None, False

    with ThreadPoolExecutor(max_workers=8) as readers:
        for offset in range(0, len(files), 16):
            yield from readers.map(read, files[offset:offset + 16])


def scan(root: Path, incomplete: list[bool] | None = None) -> list[Finding]:
    """Findings for root; when the time budget runs out, sets incomplete[0] and returns what was found."""
    deadline = time.monotonic() + _budget()
    # The guard and its tests have to spell out every pattern they detect.
    own = {Path(__file__).name, "test_console_window_guard.py"}
    files = [item for item in _candidates(root) if item[1].name not in own]
    if len(files) >= MAX_FILES and incomplete is not None:
        incomplete[:] = [True]
    guarded = _python_guard_present(files)
    go_guarded = _go_guard_present(files)
    unguarded_go: list[Finding] = []
    findings: list[Finding] = []
    unguarded_tests: list[Finding] = []
    for path, rel, raw, oversized in _read_candidates(files):
        if time.monotonic() > deadline:
            if incomplete is not None:
                incomplete[:] = [True]
            break
        if oversized:
            findings.append(Finding(rel.as_posix(), 1, "launch safety cannot be verified for oversized source", "Split the file before launching."))
            continue
        if raw is None or not any(token in raw for token in PREFILTER):
            continue
        lines = raw.decode("utf-8", errors="replace").splitlines()
        shown = rel.as_posix()
        suffix = path.suffix.lower()
        if suffix == ".py":
            covered = _is_test_file(rel) and any(parent == rel.parent or parent in rel.parents for parent in guarded)
            # The shared policy covers ordinary test launches at runtime. Only
            # explicit flag overrides or OS-shell escapes need another AST walk.
            risky = re.search(rb"child_process|execa|cross-spawn|DETACHED_PROCESS|CREATE_NEW_CONSOLE|creationflags|\bos\s*\.\s*(?:system|popen|spawn)|import\s+os\s+as|from\s+os\s+import", raw)
            if not covered or risky:
                findings.extend(_python_findings("\n".join(lines), rel, covered))
        elif suffix in {".ps1", ".psm1"}:
            text = "\n".join(lines)
            if PS_PSI.search(text) and not PS_NO_WINDOW.search(text):
                index = next(i for i, line in enumerate(lines) if PS_PSI.search(line))
                if not _marked(lines, index):
                    findings.append(Finding(shown, index + 1, "ProcessStartInfo without CreateNoWindow",
                                            "Set '$psi.UseShellExecute = $false; $psi.CreateNoWindow = $true'."))
            for i, line in enumerate(lines):
                if PS_START_PROCESS.search(line) and not line.lstrip().startswith("#") and not _marked(lines, i):
                    if not PS_HIDDEN.search(_call_text(lines, i)):
                        findings.append(Finding(shown, i + 1, "Start-Process opens a new window",
                                                "Add '-NoNewWindow' (or '-WindowStyle Hidden'), or call the program directly."))
        elif suffix == ".go":
            if go_guarded or not rel.name.endswith("_test.go"):
                continue
            for i, line in enumerate(lines):
                if GO_LAUNCH.search(line) and not line.lstrip().startswith("//") and not _marked(lines, i):
                    unguarded_go.append(Finding(shown, i + 1, "Go test starts a process without a no-window helper", ""))
        else:
            findings.extend(_javascript_findings("\n".join(lines), rel))
    if unguarded_go:
        first = unguarded_go[0]
        findings.insert(0, Finding(first.path, first.line,
                                   f"{len(unguarded_go)} exec.Command call(s) in Go tests and no Windows no-window helper",
                                   "Add a //go:build windows helper that sets cmd.SysProcAttr = &syscall.SysProcAttr"
                                   "{HideWindow: true, CreationFlags: 0x08000000} and call it for every test command."))
    if unguarded_tests:
        first = unguarded_tests[0]
        findings.insert(0, Finding(first.path, first.line,
                                   f"{len(unguarded_tests)} process launch(es) in test code and no conftest.py no-window guard",
                                   "Add this block to the top-level tests conftest.py (applies CREATE_NO_WINDOW to every "
                                   "child the suite starts):\n" + CONFTEST_GUARD))
    return findings


def report(command: str, root: Path, findings: list[Finding]) -> str:
    lines = [
        "Blocked: on Windows this command could flood the desktop with console windows.",
        f"Project: {root}",
        f"Command: {command[:160]}",
        "Fix these before running the command (each launch must be window-safe):",
    ]
    for item in findings[:MAX_REPORTED]:
        lines.append(f"- {item.path}:{item.line}: {item.rule}.")
        if item.fix:
            lines.extend("    " + part for part in item.fix.splitlines())
    if len(findings) > MAX_REPORTED:
        lines.append(f"- ...and {len(findings) - MAX_REPORTED} more of the same kinds.")
    lines.append(f"A deliberate case: put '{MARKER} <reason>' in a comment on the launch line.")
    return "\n".join(lines)


def external_python_findings(command: str, root: Path, cwd: Path) -> list[Finding]:
    """Inspect explicitly invoked Python helpers outside the project's source tree."""
    findings = []
    pattern = r'''"([^"\n]+\.py)"|'([^'\n]+\.py)'|([^\s;|&"']+\.py)'''
    for match in re.finditer(pattern, command):
        value = next(part for part in match.groups() if part)
        path = Path(value)
        if not path.is_absolute():
            path = cwd / path
        path = path.resolve()
        if root == path or root in path.parents or not path.is_file():
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                findings.append(Finding(str(path), 1, "external helper is too large to verify", "Split the helper before launching."))
                continue
            findings.extend(_python_findings(path.read_text(encoding="utf-8-sig"), path, False))
        except (OSError, UnicodeError):
            findings.append(Finding(str(path), 1, "external helper cannot be verified", "Repair access or encoding before launching."))
    return findings


def main() -> int:
    if _disabled() or not _on_windows():
        return 0
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or tool_input.get("cmd") or "")
    if not is_test_command(command):
        return 0
    root = project_root(Path(payload.get("cwd") or os.getcwd()).resolve())
    incomplete: list[bool] = [False]
    findings = scan(root, incomplete)
    findings.extend(external_python_findings(command, root, Path(payload.get("cwd") or os.getcwd()).resolve()))
    if not findings:
        if incomplete[0]:
            print(f"console-window-guard: scan stopped after {_budget():g}s with no unsafe launch found so far; "
                  "the command is blocked until the scan completes.", file=sys.stderr)
            return 2
        return 0
    print(report(command, root, findings), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
