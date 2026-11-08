"""Fixtures for the settings engine read side (v4.14.6 Phase 2).

`Machine` builds a scratch home and project, a fake PATH, and fake tool versions,
so a test never reads the real machine: the managed-settings path is always
redirected, and no tool is started.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any, Callable

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.settings_control import catalog as catalog_mod  # noqa: E402
from scripts.lib.settings_control import apply, readers, resolve  # noqa: E402

CLAUDE_IDS = ["claude-fable-5-1", "claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5"]
DEFAULT_VERSIONS = {"claude": "2.1.283", "codex": "0.136.0", "copilot": "1.0.0", "code": "1.144.0"}


def _quote(text: str) -> str:
    return json.dumps(text)  # a JSON string is a valid TOML basic string for these inputs


def to_toml(data: dict[str, Any], prefix: tuple[str, ...] = ()) -> str:
    """A tiny TOML writer for fixtures: nested tables of str, bool, int."""
    lines = [f"{_quote(k)} = {json.dumps(v)}" for k, v in data.items() if not isinstance(v, dict)]
    out = "\n".join(lines) + ("\n" if lines else "")
    for key, value in data.items():
        if isinstance(value, dict):
            name = ".".join(_quote(p) for p in (*prefix, key))
            out += f"\n[{name}]\n" + to_toml(value, (*prefix, key))
    return out


def merge(base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merge(base[key], value)
        else:
            base[key] = value
    return base


def nest(path: list[str], value: Any) -> dict[str, Any]:
    for part in reversed(path):
        value = {part: value}
    return value


def admit_all(catalog: dict[str, Any]) -> dict[str, Any]:
    """A copy of the catalog with every write admitted, to exercise every layer."""
    clone = copy.deepcopy(catalog)
    for write in clone["writes"]:
        write["admission"] = "admitted"
        write["proof"] = ["W00"]
        if "min" in write["proven_versions"] or not write["proven_versions"]:
            write["proven_versions"] = {"min": "0", "max": "99999"}
    return clone


class Machine:
    def __init__(self, root: Path) -> None:
        self.home = root / "home"
        self.project = root / "project"
        self.managed = root / "managed" / "managed-settings.json"
        self.home.mkdir()
        self.project.mkdir()
        self.env: dict[str, str] = {"PATH": ""}
        self.commands: dict[str, str] = dict(DEFAULT_VERSIONS)
        self.version_errors: dict[str, str] = {}
        self.said: list[str] = []

    def path(self, file_id: str) -> Path:
        found = self.managed if file_id == "claude-managed" else readers.file_path(file_id, self.home, self.env, self.project, "linux")
        assert found is not None
        return found

    def put(self, file_id: str, data: dict[str, Any] | str, *, merge_into: bool = True) -> Path:
        path = self.path(file_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        toml = path.suffix == ".toml"
        if isinstance(data, str):
            path.write_text(data, encoding="utf-8")
            return path
        if merge_into and path.exists() and not toml:
            data = merge(json.loads(path.read_text(encoding="utf-8")), data)
        if merge_into and path.exists() and toml:
            import tomllib

            data = merge(tomllib.loads(path.read_text(encoding="utf-8")), data)
        path.write_text(to_toml(data) if toml else json.dumps(data), encoding="utf-8")
        return path

    def trust_project(self) -> None:
        self.put("codex-user", {"projects": {str(self.project.resolve()): {"trust_level": "trusted"}}})

    def snapshot(self, catalog: dict[str, Any]) -> readers.Snapshot:
        def which(command: str) -> str | None:
            return f"/stub/{command}" if command in self.commands else None

        def runner(argv: list[str]) -> tuple[str | None, str | None]:
            name = Path(argv[0]).name
            if name in self.version_errors:
                return None, self.version_errors[name]
            return self.commands[name], None

        return readers.take_snapshot(
            catalog, home=self.home, env=self.env, project=self.project, platform="linux",
            which=which, version_runner=runner, file_overrides={"claude-managed": self.managed},
        )

    def context(self, catalog: dict[str, Any], **seams: Any) -> apply.Context:
        """A write-side context on this machine: no TTY, a fixed clock, and the fake PATH and versions."""

        def which(command: str) -> str | None:
            return f"/stub/{command}" if command in self.commands else None

        def runner(argv: list[str]) -> tuple[str | None, str | None]:
            return self.commands[Path(argv[0]).name], None

        ctx = apply.Context(
            catalog, home=self.home, env=self.env, project=self.project, platform="linux", claude_ids=list(CLAUDE_IDS),
            which=which, version_runner=runner, is_tty=lambda: False, ask=lambda prompt: "", clock=lambda: 1000.0, say=self.said.append,
        )
        for name, value in seams.items():
            setattr(ctx, name, value)
        return ctx

    def records(self, catalog: dict[str, Any], ids: list[str] | None = None) -> dict[tuple[str, str, str], dict[str, Any]]:
        found = resolve.resolve(catalog, self.snapshot(catalog), CLAUDE_IDS if ids is None else ids)
        return {(r["control"], r["tool"], r["surface"]): r for r in found}


@pytest.fixture(scope="session")
def catalog() -> dict[str, Any]:
    return catalog_mod.load_catalog()


@pytest.fixture()
def machine(tmp_path: Path) -> Machine:
    return Machine(tmp_path)


@pytest.fixture(scope="session")
def admitted(catalog: dict[str, Any]) -> dict[str, Any]:
    return admit_all(catalog)


@pytest.fixture()
def mutate() -> Callable[..., dict[str, Any]]:
    def apply(catalog: dict[str, Any], write_id: str, **changes: Any) -> dict[str, Any]:
        clone = copy.deepcopy(catalog)
        next(w for w in clone["writes"] if w["id"] == write_id).update(changes)
        return clone

    return apply
