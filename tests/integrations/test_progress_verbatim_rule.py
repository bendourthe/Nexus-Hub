"""Every generated copy of the progress command prints the renderer output verbatim; the /status shim is gone (v4.15.5)."""

import pytest

from scripts.lib.integrations import INTEGRATION_REGISTRY, get

MARKER = "print its stdout verbatim with no code fence"
# Platforms whose throwaway install emits no status command or command-skill.
NO_STATUS_SURFACE = {"aider", "copilot"}


def command_files(ctx, name):
    root = ctx.target_root
    found = []
    for path in root.rglob("*"):
        parts = [part.lower() for part in path.relative_to(root).parts]
        if not path.is_file() or "implement-phase" in parts:
            continue
        is_command = path.stem.lower() == name and path.suffix in (".md", ".toml")
        is_command_skill = path.name == "SKILL.md" and parts[-2] == name
        if is_command or is_command_skill:
            found.append(path)
    return found


@pytest.mark.parametrize("key", sorted(INTEGRATION_REGISTRY))
def test_installed_progress_surfaces_carry_the_verbatim_rule_and_no_status_shim(install_ctx, key):
    ctx = install_ctx
    ctx.selection = {"resolved": {"skills": ["implement-phase"], "commands": ["progress", "implement", "update"], "agents": []}}
    get(key).install(ctx)
    progress, status = command_files(ctx, "progress"), command_files(ctx, "status")
    if key in NO_STATUS_SURFACE:
        assert progress == [] and status == [], f"{key} now has a progress surface: remove it from NO_STATUS_SURFACE"
        return
    assert progress, f"{key}: the progress command surface must be generated"
    assert status == [], f"{key}: the removed /status shim is still generated"
    for path in progress:
        text = " ".join(path.read_text(encoding="utf-8").split())
        assert MARKER in text, f"{key}: {path.relative_to(ctx.target_root)} lacks the verbatim output rule"


def test_source_command_and_references_carry_the_rule(repo_root):
    base = repo_root / "catalog"
    for relative in ("commands/progress.md", "skills/workflow/implement-phase/references/progress-reporting.md",
                     "skills/workflow/implement-phase/references/status-formats.md"):
        text = " ".join((base / relative).read_text(encoding="utf-8").split())
        assert MARKER in text, relative
        assert "never hand-write a status table" in text, relative
