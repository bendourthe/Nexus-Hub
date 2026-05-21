"""Tests for the Antigravity 2.0 + CLI commands schema.

Added in v2.2.0 Phase 2 (T012). Locks in the conclusion from
docs/v2.2.0/antigravity-cli-commands-schema.md: Antigravity 2.0 + CLI mirrors
catalog/commands/*.md verbatim into ~/.agent/workflows/<name>.md (not the
TOML form used by Gemini CLI). The existing SkillsIntegration._mirror_catalog
helper handles this correctly; no _write_antigravity_commands variant is
required.
"""

from __future__ import annotations

from scripts.lib.integrations import get
from scripts.lib.integrations.base import InstallContext


def test_antigravity_20_workflows_are_md_not_toml(install_ctx: InstallContext):
    """Antigravity 2.0 + CLI must receive verbatim .md command files, not the
    .toml form Gemini CLI uses. This is the contract documented in
    docs/v2.2.0/antigravity-cli-commands-schema.md.
    """
    integ = get("antigravity2")
    integ.install(install_ctx)
    workflows_dir = install_ctx.target_root / ".agent" / "workflows"
    assert workflows_dir.exists(), "workflows directory must exist after install"

    md_files = list(workflows_dir.rglob("*.md"))
    toml_files = list(workflows_dir.rglob("*.toml"))

    assert len(md_files) >= 2, (
        f"Antigravity 2.0 + CLI should mirror catalog/commands/*.md as .md files; "
        f"got {len(md_files)} .md files under {workflows_dir}"
    )
    assert len(toml_files) == 0, (
        f"Antigravity 2.0 + CLI must NOT produce .toml command files (that is the "
        f"Gemini CLI schema); got {len(toml_files)} .toml files under {workflows_dir}"
    )


def test_antigravity_20_workflow_content_is_verbatim(install_ctx: InstallContext, repo_root):
    """The mirrored workflow file must equal the catalog source byte-for-byte
    (no TOML wrapping, no escaping of backslashes or triple-quotes).
    """
    integ = get("antigravity2")
    integ.install(install_ctx)

    src_dir = repo_root / "catalog" / "commands"
    md_sources = sorted(src_dir.glob("*.md"))[:2]
    assert len(md_sources) >= 2, "need at least 2 catalog/commands/*.md files for this test"

    for src in md_sources:
        mirrored = install_ctx.target_root / ".agent" / "workflows" / src.name
        assert mirrored.exists(), f"mirrored workflow {mirrored} missing"
        assert mirrored.read_bytes() == src.read_bytes(), (
            f"{src.name}: mirrored workflow body must be byte-identical to the "
            f"catalog source (no TOML wrapping)"
        )


def test_gemini_cli_workflows_are_toml(install_ctx: InstallContext):
    """Companion check: Gemini CLI still uses the .toml schema (this is what
    Antigravity CLI explicitly does NOT inherit).
    """
    integ = get("gemini-cli")
    integ.install(install_ctx)
    commands_dir = install_ctx.target_root / ".gemini" / "commands"
    assert commands_dir.exists()
    toml_files = list(commands_dir.glob("*.toml"))
    assert len(toml_files) >= 1, "Gemini CLI must produce .toml command files"
