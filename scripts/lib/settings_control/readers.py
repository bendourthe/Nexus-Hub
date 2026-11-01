"""Read-only readers: every file, variable, and tool fact the resolver needs.

`take_snapshot` reads each file once into an immutable `Snapshot`, so a file
edited mid-run cannot produce a mixed verdict. Nothing here writes. VS Code
`settings.json` is never parsed in Python (it is JSON with comments, stored per
profile); the panel supplies those values. Project files are untrusted data:
over 1 MB they are not read, a symlink leading outside the project is not
followed, and a Codex project file is read only for a trusted project.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Mapping

from .catalog import FILE_IDS, USER_FILE_IDS

MAX_PROJECT_BYTES = 1_000_000
VERSION_TIMEOUT_SECONDS = 5
_VERSION = re.compile(r"\d+(?:\.\d+)+")
#: file id -> (scope shown to the user, format). Scope orders override layers.
FILE_INFO: dict[str, tuple[str, str]] = {
    "claude-user": ("user", "json"),
    "claude-project": ("project", "json"),
    "claude-project-local": ("project", "json"),
    "claude-managed": ("managed", "json"),
    "codex-user": ("user", "toml"),
    "codex-project": ("project", "toml"),
    "copilot-user": ("user", "json"),
    "copilot-repo": ("project", "json"),
    "copilot-repo-local": ("project", "json"),
    "nexus-guardrails": ("user", "json"),
}
assert set(FILE_INFO) == FILE_IDS  # one vocabulary, no drift between catalog and readers


@dataclass(frozen=True)
class FileRead:
    """One file as read once: `ok` carries data, the others carry a reason."""

    file_id: str
    display: str
    status: str  # "ok" | "absent" | "invalid" | "skipped"
    data: Any = None
    detail: str = ""


@dataclass(frozen=True)
class ToolState:
    installed: bool
    version: str | None = None
    version_error: str | None = None


@dataclass(frozen=True)
class Snapshot:
    """Everything read for one invocation. Immutable by construction."""

    home: str
    project: str | None
    platform: str
    env: Mapping[str, str]
    files: Mapping[str, FileRead]
    tools: Mapping[str, ToolState]
    codex_project_trusted: bool = False


def platform_name() -> str:
    return {"win32": "windows", "darwin": "macos"}.get(sys.platform, "linux")


def _env_dir(env: Mapping[str, str], name: str, home: Path, default: str) -> Path:
    value = env.get(name, "").strip()
    return Path(value) if value else home / default


def dir_path(dir_id: str, home: Path, env: Mapping[str, str]) -> Path:
    """Configuration directory of a tool, honoring the vendor's documented override variable."""
    if dir_id == "claude-dir":
        return _env_dir(env, "CLAUDE_CONFIG_DIR", home, ".claude")
    if dir_id == "codex-dir":
        return _env_dir(env, "CODEX_HOME", home, ".codex")
    if dir_id == "copilot-dir":
        return _env_dir(env, "COPILOT_HOME", home, ".copilot")
    raise KeyError(dir_id)


def managed_claude_path(platform: str) -> Path:
    """Vendor-documented managed-settings location (code.claude.com settings page)."""
    if platform == "windows":
        return Path("C:/Program Files/ClaudeCode/managed-settings.json")
    if platform == "macos":
        return Path("/Library/Application Support/ClaudeCode/managed-settings.json")
    return Path("/etc/claude-code/managed-settings.json")


def file_path(file_id: str, home: Path, env: Mapping[str, str], project: Path | None, platform: str) -> Path | None:
    """Absolute path of a file id, or None when it needs a project and none is given."""
    if file_id == "claude-user":
        return dir_path("claude-dir", home, env) / "settings.json"
    if file_id == "claude-managed":
        return managed_claude_path(platform)
    if file_id == "codex-user":
        return dir_path("codex-dir", home, env) / "config.toml"
    if file_id == "copilot-user":
        return dir_path("copilot-dir", home, env) / "settings.json"
    if file_id == "nexus-guardrails":
        return home / ".nexus-hub" / "guardrails.json"
    if project is None:
        return None
    relative = {
        "claude-project": (".claude", "settings.json"),
        "claude-project-local": (".claude", "settings.local.json"),
        "codex-project": (".codex", "config.toml"),
        "copilot-repo": (".github", "copilot", "settings.json"),
        "copilot-repo-local": (".github", "copilot", "settings.local.json"),
    }[file_id]
    return project.joinpath(*relative)


def printable(text: str) -> str:
    """Printable ASCII only: a value or path from a project file must not drive the terminal."""
    return "".join(c if " " <= c <= "~" else (f"\\x{ord(c):02x}" if ord(c) <= 0xFF else f"\\u{ord(c):04x}") for c in text)


def display_path(path: Path, home: Path, project: Path | None) -> str:
    """Short, stable, printable path for messages: `~/...` under home, project-relative under the project."""
    for base, prefix in ((project, ""), (home, "~/")):
        if base is None:
            continue
        try:
            return printable(prefix + path.relative_to(base).as_posix())
        except ValueError:
            continue
    return printable(str(path))


def _iso(value: Any) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def plain_data(data: Any) -> Any:
    """A copy of parsed data that is plain JSON: TOML dates and times become ISO text. May raise `RecursionError`."""
    return json.loads(json.dumps(data, default=_iso))


def _parse_toml(text: str) -> Any:
    try:
        import tomlkit  # optional; stdlib tomllib reads the same documents
    except ImportError:
        tomlkit = None
    if tomlkit is not None:
        try:
            parsed = tomlkit.parse(text)
            return parsed.unwrap() if hasattr(parsed, "unwrap") else dict(parsed)
        except tomlkit.exceptions.ParseError as exc:
            raise ValueError(f"line {exc.line}") from exc
    try:
        import tomllib
    except ImportError as exc:
        raise OSError("no TOML reader is available: run pip install tomlkit") from exc
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        match = re.search(r"line (\d+)", str(exc))
        # "at end of document" carries no line: report the last line of the text.
        line = getattr(exc, "lineno", None) or (match.group(1) if match else len(text.rstrip("\n").splitlines()) or 1)
        raise ValueError(f"line {line}") from exc


def read_file(file_id: str, path: Path, display: str, project: Path | None = None) -> FileRead:
    """Read one config file once; never raises, never guesses."""
    scope, fmt = FILE_INFO[file_id]
    is_project = scope == "project"
    try:
        if not path.exists():
            return FileRead(file_id, display, "absent")
        if is_project and project is not None:
            real = path.resolve()
            try:
                real.relative_to(project.resolve())
            except ValueError:
                return FileRead(file_id, display, "skipped", detail="a symlink points outside the project")
            if real.stat().st_size > MAX_PROJECT_BYTES:
                return FileRead(file_id, display, "skipped", detail="the file is over 1 MB")
        if not path.is_file():
            return FileRead(file_id, display, "invalid", detail=f"{display} is not a regular file")
        text = path.read_bytes().decode("utf-8-sig")
    except UnicodeDecodeError:
        return FileRead(file_id, display, "invalid", detail=f"{display} is not valid UTF-8")
    except OSError as exc:
        return FileRead(file_id, display, "invalid", detail=f"{display} cannot be read ({exc.strerror or exc})")
    label = "JSON" if fmt == "json" else "TOML"
    try:
        data = json.loads(text) if fmt == "json" else plain_data(_parse_toml(text))
    except RecursionError:
        return FileRead(file_id, display, "invalid", detail=f"{display} is nested too deeply to read")
    except json.JSONDecodeError as exc:
        return FileRead(file_id, display, "invalid", detail=f"{display} is not valid JSON (line {exc.lineno})")
    except ValueError as exc:
        return FileRead(file_id, display, "invalid", detail=f"{display} is not valid {label} ({exc})")
    except OSError as exc:
        return FileRead(file_id, display, "invalid", detail=f"{display} cannot be read ({exc})")
    if not isinstance(data, dict):
        return FileRead(file_id, display, "invalid", detail=f"{display} is not a {label} object")
    return FileRead(file_id, display, "ok", data=data)


def _normalized(path: str | Path) -> str:
    text = str(path)
    if text.startswith("\\\\?\\"):
        text = text[4:]
    return os.path.normcase(os.path.normpath(text))


def codex_project_trusted(codex_user: FileRead, project: Path | None) -> bool:
    """True when `projects."<path>".trust_level` trusts the project or an ancestor."""
    if project is None or codex_user.status != "ok":
        return False
    table = codex_user.data.get("projects")
    if not isinstance(table, dict):
        return False
    trusted = {
        _normalized(key) for key, value in table.items() if isinstance(value, dict) and value.get("trust_level") == "trusted"
    }
    here = project.resolve()
    return any(_normalized(candidate) in trusted for candidate in (here, *here.parents))


def parse_version(text: str) -> str | None:
    match = _VERSION.search(text or "")
    return match.group(0) if match else None


def run_version(argv: list[str]) -> tuple[str | None, str | None]:
    """Run `<tool> --version` once; return (version, error). Windowless on Windows."""
    try:
        done = subprocess.run(
            argv, capture_output=True, text=True, timeout=VERSION_TIMEOUT_SECONDS, stdin=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), check=False,
        )
    except subprocess.TimeoutExpired:
        return None, f"timed out after {VERSION_TIMEOUT_SECONDS} s"
    except OSError as exc:
        return None, f"could not run ({exc.strerror or exc})"
    version = parse_version(done.stdout) or parse_version(done.stderr)
    return (version, None) if version else (None, "no version in the output")


def needs_version(catalog: dict[str, Any], tool: str) -> bool:
    """Only a tool with an admitted write carrying a proven min/max range is asked its version."""
    return any(
        w["tool"] == tool and w["admission"] == "admitted" and ("min" in w["proven_versions"] or "max" in w["proven_versions"])
        for w in catalog["writes"]
    )


def _tool_states(
    catalog: dict[str, Any], home: Path, env: Mapping[str, str],
    which: Callable[[str], str | None], version_runner: Callable[[list[str]], tuple[str | None, str | None]],
) -> dict[str, ToolState]:
    states: dict[str, ToolState] = {}
    for tool, info in catalog["tools"].items():
        detect = info["detect"]
        command = which(detect["command"])
        dir_id = detect.get("config_dir")
        has_dir = dir_id is not None and dir_path(dir_id, home, env).is_dir()
        installed = bool(command) or has_dir
        version = error = None
        if installed and needs_version(catalog, tool):
            if command:
                version, error = version_runner([command, "--version"])
            else:
                error = "the command is not on PATH"
        states[tool] = ToolState(installed, version, error)
    return states


def take_snapshot(
    catalog: dict[str, Any],
    *,
    home: Path | None = None,
    env: Mapping[str, str] | None = None,
    project: Path | None = None,
    platform: str | None = None,
    which: Callable[[str], str | None] | None = None,
    version_runner: Callable[[list[str]], tuple[str | None, str | None]] = run_version,
    file_overrides: Mapping[str, Path] | None = None,
) -> Snapshot:
    """Read every file and tool fact once.

    The keyword arguments are test seams (a scratch home, a fake PATH or version,
    a redirected managed-settings path); the CLI passes only `project`.
    """
    home = home or Path.home()
    env = MappingProxyType(dict(os.environ if env is None else env))
    platform = platform or platform_name()
    project = project.resolve() if project is not None else None
    find = which or (lambda command: shutil.which(command, path=env.get("PATH")))
    paths = dict(file_overrides or {})
    files: dict[str, FileRead] = {}

    def read(file_id: str) -> FileRead:
        path = paths.get(file_id) or file_path(file_id, home, env, project, platform)
        if path is None:
            return FileRead(file_id, file_id, "absent")
        return read_file(file_id, path, display_path(path, home, project), project)

    for file_id in sorted(FILE_IDS - {"codex-project"}):
        files[file_id] = read(file_id)
    trusted = codex_project_trusted(files["codex-user"], project)
    if trusted:
        files["codex-project"] = read("codex-project")
    else:
        path = paths.get("codex-project") or file_path("codex-project", home, env, project, platform)
        display = display_path(path, home, project) if path else "codex-project"
        present = path is not None and path.exists()
        files["codex-project"] = (
            FileRead("codex-project", display, "skipped", detail="the project is not trusted by Codex") if present
            else FileRead("codex-project", display, "absent")
        )
    return Snapshot(
        home=str(home), project=str(project) if project else None, platform=platform, env=env,
        files=MappingProxyType(files), tools=MappingProxyType(_tool_states(catalog, home, env, find, version_runner)),
        codex_project_trusted=trusted,
    )


def user_file_id(write: dict[str, Any]) -> str | None:
    """Reader file id of a write's own user-level file (None for `vscode-config`)."""
    return USER_FILE_IDS[write["file"]]
