"""Every generated copy of the status command tells the agent to print the renderer output verbatim."""

import pytest

from scripts.lib.integrations import INTEGRATION_REGISTRY, get

MARKER = "print its stdout verbatim with no code fence"
# Platforms whose throwaway install emits no status command or command-skill.
NO_STATUS_SURFACE = {"aider", "copilot"}


def status_files(ctx):
    root = ctx.target_root
    found = []
    for path in root.rglob("*"):
        parts = [part.lower() for part in path.relative_to(root).parts]
        if not path.is_file() or "implement-phase" in parts:
            continue
        is_command = path.stem.lower() == "status" and path.suffix in (".md", ".toml")
        is_command_skill = path.name == "SKILL.md" and parts[-2] == "status"
        if is_command or is_command_skill:
            found.append(path)
    return found


@pytest.mark.parametrize("key", sorted(INTEGRATION_REGISTRY))
def test_installed_status_surfaces_carry_the_verbatim_rule(install_ctx, key):
    ctx = install_ctx
    ctx.selection = {"resolved": {"skills": ["implement-phase"], "commands": ["status", "implement", "update"], "agents": []}}
    get(key).install(ctx)
    files = status_files(ctx)
    if key in NO_STATUS_SURFACE:
        assert files == [], f"{key} now has a status surface: remove it from NO_STATUS_SURFACE"
        return
    assert files, f"{key}: no status command surface was generated"
    for path in files:
        text = " ".join(path.read_text(encoding="utf-8").split())
        assert MARKER in text, f"{key}: {path.relative_to(ctx.target_root)} lacks the verbatim output rule"


def test_source_command_and_references_carry_the_rule(repo_root):
    base = repo_root / "catalog"
    for relative in ("commands/status.md", "skills/workflow/implement-phase/references/progress-reporting.md",
                     "skills/workflow/implement-phase/references/status-formats.md"):
        text = " ".join((base / relative).read_text(encoding="utf-8").split())
        assert MARKER in text, relative
        assert "never hand-write a status table" in text, relative
