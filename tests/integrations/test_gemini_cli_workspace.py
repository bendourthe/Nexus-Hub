"""Gemini CLI workspace instruction file and rules surface (WN-5-v4133, v4.13.11).

https://geminicli.com/docs/cli/gemini-md/ (re-fetched 2026-10-10) loads the global
~/.gemini/GEMINI.md and GEMINI.md files found in the configured workspace
directories and their parents; it documents no `<project>/.gemini/GEMINI.md` and
no rules/ directory. The adapter therefore writes the workspace instruction at the
project root and writes no rules/ mirror at either scope.
"""

from __future__ import annotations

from dataclasses import replace

from scripts.lib.integrations import get
from scripts.lib.integrations.base import InstallContext


def test_workspace_instruction_lands_at_the_project_root(install_ctx: InstallContext):
    get("gemini-cli").install(install_ctx)
    root_file = install_ctx.target_root / "GEMINI.md"
    assert root_file.is_file(), "Gemini CLI reads the workspace GEMINI.md at the root"
    assert not (install_ctx.target_root / ".gemini" / "GEMINI.md").exists()
    # The other workspace surfaces stay under .gemini/.
    assert (install_ctx.target_root / ".gemini" / "skills").is_dir()
    assert (install_ctx.target_root / ".gemini" / "settings.json").is_file()


def test_no_unread_rules_dir_at_either_scope(install_ctx: InstallContext):
    get("gemini-cli").install(install_ctx)
    assert not (install_ctx.target_root / ".gemini" / "rules").exists()
    ctx = replace(install_ctx, scope="global", explicit_target=True)
    get("gemini-cli").install(ctx)
    assert (install_ctx.target_root / ".gemini" / "GEMINI.md").is_file()
    assert not (install_ctx.target_root / ".gemini" / "rules").exists()
