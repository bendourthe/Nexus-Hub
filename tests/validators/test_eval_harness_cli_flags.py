"""Every flag the skill-eval harness emits must exist in the installed CLI.

`scripts/optimize_skill_description.py::build_cli_command` once built
`claude -p ... --skill <path>` and `codex exec ... --prompt <path>`; neither
flag exists, so no live run could start (v4.13 AR-04). The old parity test only
checked that no branch invoked another CLI, which is why it never noticed.

The help text is captured, not fetched, so CI needs no CLI: Claude Code 2.1.283
(`claude --help`) and codex-cli 0.136.0 (`codex exec --help`), both captured on
2026-10-10 and transliterated to ASCII. Re-capture the fixtures when a CLI
release renames a flag; this test then names the flag that no longer exists.
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_OPTIMIZER = _REPO_ROOT / "scripts" / "optimize_skill_description.py"
_HELP_DIR = _REPO_ROOT / "tests" / "fixtures" / "cli-help"
_HELP = {
    "claude": _HELP_DIR / "claude-code-2.1.283-help.txt",
    "codex": _HELP_DIR / "codex-cli-0.136.0-exec-help.txt",
}
# An option definition starts within the first few columns; deeper-indented
# dashes are description prose that merely mentions another flag.
_OPTION_LINE = re.compile(r"^\s{1,8}(-{1,2}[A-Za-z][\w-]*(?:,\s+-{1,2}[A-Za-z][\w-]*)*)")


def _load_optimizer():
    spec = importlib.util.spec_from_file_location("optimize_skill_description_flags", _OPTIMIZER)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules[spec.name] = module  # type: ignore[union-attr]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


@pytest.fixture(scope="module")
def optimizer():
    return _load_optimizer()


def documented_flags(cli: str) -> set[str]:
    flags: set[str] = set()
    for line in _HELP[cli].read_text(encoding="ascii").splitlines():
        match = _OPTION_LINE.match(line)
        if match:
            flags.update(part.strip() for part in match.group(1).split(","))
    return flags


def emitted_flags(cmd: list[str]) -> list[str]:
    # Values never start with "-" here: the prompt and model are fixed below.
    return [token for token in cmd[1:] if token.startswith("-")]


def test_help_fixtures_parse_to_known_flags() -> None:
    claude = documented_flags("claude")
    codex = documented_flags("codex")
    assert {"-p", "--print", "--model", "--output-format", "--setting-sources"} <= claude
    assert {"--model", "-m", "--cd", "--ignore-user-config", "--ephemeral"} <= codex
    # The defect's flags are absent, so a regression to them fails below.
    assert "--skill" not in claude
    assert "--prompt" not in codex


@pytest.mark.parametrize("cli", ["claude", "codex"])
@pytest.mark.parametrize("with_skill", [False, True], ids=["baseline", "skill"])
def test_every_emitted_flag_exists_in_cli_help(
    optimizer, tmp_path: Path, cli: str, with_skill: bool
) -> None:
    skill = tmp_path / "SKILL.md"
    skill.write_text("---\nname: fixture-skill\ndescription: x\n---\n", encoding="utf-8")
    kwargs = {"model": "fixture-model"}
    # Judge the flags alone, not the call shape, so this test names the bad
    # flag even against a builder that predates `project_dir`.
    if with_skill and "project_dir" in inspect.signature(optimizer.build_cli_command).parameters:
        kwargs["project_dir"] = tmp_path / "project"
    cmd = optimizer.build_cli_command(
        cli, "summarize the fixture", skill if with_skill else None, **kwargs
    )

    assert cmd[0] == cli
    if cli == "codex":
        assert cmd[1] == "exec"
    unknown = [flag for flag in emitted_flags(cmd) if flag not in documented_flags(cli)]
    assert unknown == [], f"{cli} does not accept {unknown}: {cmd}"


def test_claude_skill_arm_uses_the_pilot_isolation(optimizer, tmp_path: Path) -> None:
    project = tmp_path / "project"
    cmd = optimizer.build_cli_command(
        "claude", "q", tmp_path / "SKILL.md", model="m", project_dir=project
    )

    assert cmd[cmd.index("--setting-sources") + 1] == "project"
    assert cmd[cmd.index("--output-format") + 1] == "stream-json"
    assert "--strict-mcp-config" in cmd
    assert cmd[cmd.index("--add-dir") + 1] == str(project)


def test_invoke_cli_stages_the_skill_where_the_cli_reads_it(
    optimizer, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    skill = tmp_path / "src" / "SKILL.md"
    skill.parent.mkdir()
    skill.write_text("---\nname: staged-skill\ndescription: x\n---\nbody\n", encoding="utf-8")
    seen: list[dict] = []

    def fake_run(cmd, **kwargs):
        cwd = Path(kwargs["cwd"])
        seen.append({
            "cmd": cmd,
            "claude": (cwd / ".claude" / "skills" / "staged-skill" / "SKILL.md").is_file(),
            "codex": (cwd / ".agents" / "skills" / "staged-skill" / "SKILL.md").is_file(),
        })
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(optimizer.subprocess, "run", fake_run)
    optimizer.invoke_cli("claude", "q", skill, "m")
    optimizer.invoke_cli("codex", "q", skill, "m")

    assert seen[0]["claude"] and not seen[0]["codex"]
    assert seen[1]["codex"] and not seen[1]["claude"]
    assert "--skill" not in seen[0]["cmd"]
    assert "--prompt" not in seen[1]["cmd"]


def _stream(*tool_inputs: dict) -> str:
    events = [{"type": "system", "subtype": "init", "skills": ["fixture-skill"]}]
    for tool_input in tool_inputs:
        events.append({
            "type": "assistant",
            "message": {"content": [{"type": "tool_use", "name": "Skill", "input": tool_input}]},
        })
    events.append({"type": "result", "subtype": "success"})
    return "\n".join(json.dumps(event) for event in events)


def test_stream_detection_reads_the_skill_tool_call(optimizer) -> None:
    hit = _stream({"skill": "fixture-skill"})
    other = _stream({"command": "/another-skill"})
    none = _stream()

    assert optimizer._detect_trigger(hit, "unrelated words here", "fixture-skill") is True
    assert optimizer._detect_trigger(other, "unrelated words here", "fixture-skill") is False
    # A stream that never calls Skill is a measured non-selection, even when the
    # transcript happens to echo a description phrase.
    assert optimizer._detect_trigger(none + "\nstructured task", "structured task", "fixture-skill") is False
    # Plain text keeps the phrase heuristic.
    assert optimizer._detect_trigger("a structured task ran", "structured task", "fixture-skill") is True
