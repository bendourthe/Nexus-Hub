"""Kimi Code CLI native agent + TOML hook delivery (v3.15.8 Phase 7).

Covers the contract the Phase 1 ownership matrix requires before a Kimi row may
move from finding-only to enforceable: verbatim agent copying with validation,
user-file collision, the four-field-only hook schema, comment and table
preservation across the TOML merge, rollback on an invalid result, duplicate
suppression, host-selected commands, and teardown that removes only the managed
block.

Two negative guarantees get as much attention as the positive ones, because both
are ways this phase could quietly do damage: writing an extra field into
``[[hooks]]`` makes Kimi refuse to load the user's entire config, and writing a
project-scoped hook path would invent a surface Kimi does not document.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
import tomllib

from scripts.lib.integrations import get
from scripts.lib.integrations._kimi_native import (
    BLOCK_END,
    BLOCK_START,
    KIMI_HOOK_FIELDS,
    KIMI_HOOK_TIMEOUT_S,
    agent_is_loadable,
    build_kimi_hooks,
    hooks_block_entries,
    merge_config_hooks,
    prune_config_hooks,
    render_hooks_block,
)
from scripts.lib.integrations.base import InstallContext


@pytest.fixture
def kimi():
    return get("kimi")


@pytest.fixture
def kimi_root(install_ctx: InstallContext) -> Path:
    return (install_ctx.target_root / ".kimi-code").resolve()


def _catalog_settings(ctx: InstallContext) -> dict:
    return json.loads(
        (ctx.repo_root / "catalog" / "hooks" / "settings.json").read_text(
            encoding="utf-8"
        )
    )


def _build(ctx: InstallContext, windows: bool = False, base: str = "/k/hooks"):
    return build_kimi_hooks(
        _catalog_settings(ctx), ctx.repo_root / "catalog" / "hooks", base, windows
    )


def _config(root: Path) -> Path:
    return root / "config.toml"


# ----- agents: verbatim copy ----------------------------------------------


def test_every_catalog_agent_is_copied_byte_for_byte(kimi, install_ctx, kimi_root):
    """Kimi reads the catalog's frontmatter natively, so no transform may occur."""
    kimi._install_agents(kimi_root, install_ctx)
    src_dir = install_ctx.repo_root / "catalog" / "agents"
    sources = sorted(src_dir.glob("*.md"))
    assert sources
    for src in sources:
        dst = kimi_root / "agents" / src.name
        assert dst.exists(), f"{src.name} was not delivered"
        assert dst.read_bytes() == src.read_bytes(), f"{src.name} was modified"


def test_delivered_agents_keep_the_md_extension_and_name(kimi, install_ctx, kimi_root):
    kimi._install_agents(kimi_root, install_ctx)
    delivered = {p.name for p in (kimi_root / "agents").glob("*")}
    expected = {
        p.name for p in (install_ctx.repo_root / "catalog" / "agents").glob("*.md")
    }
    assert delivered == expected


@pytest.mark.parametrize(
    "markdown,expected_ok",
    [
        ("---\nname: good-agent\ndescription: Does a thing\n---\n\nBody here.\n", True),
        ("---\ndescription: Name falls back to the filename\n---\n\nBody.\n", True),
        ("---\nname: good-agent\n---\n\nBody but no description.\n", False),
        ("---\nname: good-agent\ndescription: d\n---\n\n", False),
        ("---\nname: NotKebab\ndescription: d\n---\n\nBody.\n", False),
        ("---\nname: also_not_kebab\ndescription: d\n---\n\nBody.\n", False),
    ],
)
def test_agent_validation_matches_kimis_documented_requirements(markdown, expected_ok):
    """description is required and the resolved name must be kebab-case."""
    assert (agent_is_loadable("good-agent", markdown) is None) is expected_ok


def test_agent_missing_required_fields_is_skipped_not_shipped(
    kimi, install_ctx, kimi_root, tmp_path
):
    src = tmp_path / "agents"
    src.mkdir()
    (src / "fine.md").write_text(
        "---\nname: fine\ndescription: ok\n---\n\nBody.\n", encoding="utf-8"
    )
    (src / "broken.md").write_text(
        "---\nname: broken\n---\n\nBody.\n", encoding="utf-8"
    )

    from scripts.lib.integrations._kimi_native import agents_to_kimi

    agents_to_kimi(install_ctx, "kimi", src, kimi_root / "agents")

    assert (kimi_root / "agents" / "fine.md").exists()
    assert not (kimi_root / "agents" / "broken.md").exists()


def test_catalog_agents_have_no_template_placeholders(install_ctx):
    """Kimi renders the body as a template, so a stray ${var} would be substituted."""
    import re

    pattern = re.compile(r"\$\{[A-Za-z_][A-Za-z0-9_]*\}")
    for md in (install_ctx.repo_root / "catalog" / "agents").glob("*.md"):
        assert not pattern.search(md.read_text(encoding="utf-8")), md.name


# ----- agents: ownership ---------------------------------------------------


def test_user_authored_agent_is_never_overwritten(kimi, install_ctx, kimi_root):
    dst = kimi_root / "agents" / "planner.md"
    dst.parent.mkdir(parents=True, exist_ok=True)
    mine = "---\nname: planner\ndescription: mine\n---\n\nMy own planner.\n"
    dst.write_text(mine, encoding="utf-8")

    kimi._install_agents(kimi_root, install_ctx)

    assert dst.read_text(encoding="utf-8") == mine


def test_owned_agent_is_refreshed_and_reinstall_is_idempotent(
    kimi, install_ctx, kimi_root
):
    kimi._install_agents(kimi_root, install_ctx)
    dst = kimi_root / "agents" / "planner.md"
    original = dst.read_bytes()
    dst.write_text("drifted", encoding="utf-8")

    kimi._install_agents(kimi_root, install_ctx)
    assert dst.read_bytes() == original

    kimi._install_agents(kimi_root, install_ctx)
    assert dst.read_bytes() == original


def test_shared_agents_directory_is_not_written(kimi, install_ctx, kimi_root):
    """Kimi reads .agents/agents but must not claim it (shared-path ownership)."""
    kimi._install_agents(kimi_root, install_ctx)
    assert not (install_ctx.target_root / ".agents" / "agents").exists()


# ----- hooks: the four-field-only schema ----------------------------------


def test_hook_entries_carry_only_the_four_permitted_fields(install_ctx):
    """An extra field makes Kimi refuse to load the user's whole config."""
    entries, _scripts, _skipped = _build(install_ctx)
    assert entries
    for entry in entries:
        assert set(entry) <= KIMI_HOOK_FIELDS, set(entry) - KIMI_HOOK_FIELDS
        assert entry["event"] and entry["command"]


def test_timeout_is_seconds_within_kimis_documented_range(install_ctx):
    entries, _scripts, _skipped = _build(install_ctx)
    for entry in entries:
        assert 1 <= entry["timeout"] <= 600
    assert KIMI_HOOK_TIMEOUT_S == 15


def test_rendered_block_parses_and_round_trips(install_ctx):
    entries, _scripts, _skipped = _build(install_ctx)
    parsed = tomllib.loads(render_hooks_block(entries))
    assert len(parsed["hooks"]) == len(entries)
    for emitted, source in zip(parsed["hooks"], entries):
        assert emitted == source


# ----- hooks: event and matcher mapping -----------------------------------


def test_catalog_events_map_without_translation(install_ctx):
    """Kimi kept the Claude-style event names, so every catalog event survives."""
    entries, _scripts, _skipped = _build(install_ctx)
    events = {entry["event"] for entry in entries}
    assert {
        "SessionStart",
        "PreToolUse",
        "PostToolUse",
        "UserPromptSubmit",
        "Stop",
    } <= events


def test_matchers_are_anchored_regexes_over_kimi_tool_names(install_ctx):
    entries, _scripts, _skipped = _build(install_ctx)
    matchers = {entry["matcher"] for entry in entries if "matcher" in entry}
    assert matchers
    for matcher in matchers:
        assert matcher.startswith("^(") and matcher.endswith(")$"), matcher
        for token in matcher[2:-2].split("|"):
            assert token in {"Bash", "Write", "Edit", "Skill"}, token


def test_multiedit_folds_into_edit_and_powershell_is_dropped(install_ctx):
    entries, _scripts, skipped = _build(install_ctx)
    matchers = " ".join(entry.get("matcher", "") for entry in entries)
    assert "MultiEdit" not in matchers
    assert "PowerShell" not in matchers
    assert any("PowerShell" in reason for reason in skipped)


def test_lifecycle_events_carry_no_matcher(install_ctx):
    entries, _scripts, _skipped = _build(install_ctx)
    for entry in entries:
        if entry["event"] in {
            "SessionStart",
            "SessionEnd",
            "UserPromptSubmit",
            "Stop",
            "PreCompact",
        }:
            assert "matcher" not in entry, entry


def test_unknown_event_is_skipped_with_a_reason(install_ctx):
    settings = {"hooks": {"NoSuchEvent": [{"matcher": "", "hooks": []}]}}
    entries, _scripts, skipped = build_kimi_hooks(
        settings, install_ctx.repo_root / "catalog" / "hooks", "/k/hooks", False
    )
    assert entries == []
    assert any("NoSuchEvent" in reason for reason in skipped)


def test_one_catalog_group_expands_to_one_entry_per_command(install_ctx):
    """Kimi allows a single command per entry where the catalog groups several."""
    settings = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Write",
                    "hooks": [
                        {"command": "bash x/secret-scan.sh"},
                        {"command": "bash x/large-file-guard.sh"},
                    ],
                }
            ]
        }
    }
    entries, _scripts, _skipped = build_kimi_hooks(
        settings, install_ctx.repo_root / "catalog" / "hooks", "/k/hooks", False
    )
    assert len(entries) == 2
    assert {e["matcher"] for e in entries} == {"^(Write)$"}


def test_identical_event_matcher_command_triples_are_suppressed(install_ctx):
    settings = {
        "hooks": {
            "PreToolUse": [
                {"matcher": "Write", "hooks": [{"command": "bash x/secret-scan.sh"}]},
                {"matcher": "Write", "hooks": [{"command": "bash x/secret-scan.sh"}]},
            ]
        }
    }
    entries, _scripts, _skipped = build_kimi_hooks(
        settings, install_ctx.repo_root / "catalog" / "hooks", "/k/hooks", False
    )
    assert len(entries) == 1


# ----- hooks: host-selected command ---------------------------------------


@pytest.mark.parametrize("windows", [False, True], ids=["posix", "windows"])
def test_command_matches_the_installing_host(install_ctx, windows):
    entries, scripts, _skipped = _build(install_ctx, windows=windows)
    for entry in entries:
        command = entry["command"]
        if ".py" in command:
            assert command.startswith("python " if windows else "python3 ")
        elif windows:
            assert command.startswith("powershell ") and ".ps1" in command
        else:
            assert command.startswith("bash ") and ".sh" in command
    shell_stems = {Path(s).stem for s in scripts if not s.endswith(".py")}
    for stem in shell_stems:
        assert f"{stem}.sh" in scripts and f"{stem}.ps1" in scripts


# ----- config.toml merge: preservation ------------------------------------


def test_merge_preserves_comments_tables_and_formatting(kimi, install_ctx, kimi_root):
    """The user's TOML is spliced, never parsed and re-emitted."""
    kimi_root.mkdir(parents=True, exist_ok=True)
    original = (
        "# My hand-written Kimi config.\n"
        "default_permission_mode = 'manual'\n"
        "\n"
        "[providers.moonshot]\n"
        "# keep this comment exactly here\n"
        'api_key = "sk-test"\n'
        "\n"
        "[[permission.rules]]\n"
        'decision = "deny"\n'
        'pattern = "Bash(rm -rf*)"\n'
    )
    _config(kimi_root).write_text(original, encoding="utf-8")

    kimi._install_hooks(kimi_root, install_ctx)

    merged = _config(kimi_root).read_text(encoding="utf-8")
    assert merged.startswith(original.rstrip("\n"))
    assert "# keep this comment exactly here" in merged
    assert "# My hand-written Kimi config." in merged
    data = tomllib.loads(merged)
    assert data["providers"]["moonshot"]["api_key"] == "sk-test"
    assert data["permission"]["rules"][0]["pattern"] == "Bash(rm -rf*)"


def test_merge_preserves_user_authored_hooks(kimi, install_ctx, kimi_root):
    kimi_root.mkdir(parents=True, exist_ok=True)
    original = '[[hooks]]\nevent = "Stop"\ncommand = "echo mine"\n'
    _config(kimi_root).write_text(original, encoding="utf-8")

    kimi._install_hooks(kimi_root, install_ctx)

    data = tomllib.loads(_config(kimi_root).read_text(encoding="utf-8"))
    commands = [h["command"] for h in data["hooks"]]
    assert "echo mine" in commands
    assert len(commands) > 1


def test_managed_block_is_delimited_by_markers(kimi, install_ctx, kimi_root):
    kimi._install_hooks(kimi_root, install_ctx)
    text = _config(kimi_root).read_text(encoding="utf-8")
    assert text.count(BLOCK_START) == 1
    assert text.count(BLOCK_END) == 1
    assert hooks_block_entries(_config(kimi_root))


def test_reinstall_is_byte_identical_and_adds_no_second_block(
    kimi, install_ctx, kimi_root
):
    kimi._install_hooks(kimi_root, install_ctx)
    first = _config(kimi_root).read_bytes()
    kimi._install_hooks(kimi_root, install_ctx)
    assert _config(kimi_root).read_bytes() == first
    assert _config(kimi_root).read_text(encoding="utf-8").count(BLOCK_START) == 1


def test_reinstall_over_a_drifted_block_replaces_only_the_block(
    kimi, install_ctx, kimi_root
):
    """Repair: hand edits inside the block are replaced, outside content is not."""
    kimi_root.mkdir(parents=True, exist_ok=True)
    _config(kimi_root).write_text("# user header\nverbose = true\n", encoding="utf-8")
    kimi._install_hooks(kimi_root, install_ctx)
    expected = _config(kimi_root).read_bytes()

    text = _config(kimi_root).read_text(encoding="utf-8")
    tampered = text.replace("timeout = 15", "timeout = 600")
    _config(kimi_root).write_text(tampered, encoding="utf-8")

    kimi._install_hooks(kimi_root, install_ctx)

    assert _config(kimi_root).read_bytes() == expected
    assert "# user header" in _config(kimi_root).read_text(encoding="utf-8")


# ----- config.toml merge: safety ------------------------------------------


def test_already_malformed_config_is_left_untouched(kimi, install_ctx, kimi_root):
    """An invalid file is the user's to fix; splicing would look like the cause."""
    kimi_root.mkdir(parents=True, exist_ok=True)
    broken = "[providers\nthis is not toml\n"
    _config(kimi_root).write_text(broken, encoding="utf-8")

    result = kimi._install_hooks(kimi_root, install_ctx)

    assert _config(kimi_root).read_text(encoding="utf-8") == broken
    assert any(
        a.action == "kept" for a in result.files if a.path.endswith("config.toml")
    )


def test_merge_rolls_back_when_the_result_would_not_parse(install_ctx, kimi_root):
    """A block that cannot parse must never reach disk."""
    kimi_root.mkdir(parents=True, exist_ok=True)
    original = "verbose = true\n"
    _config(kimi_root).write_text(original, encoding="utf-8")
    bad_block = f"{BLOCK_START}\n[[hooks]\nevent = broken\n{BLOCK_END}\n"

    action = merge_config_hooks(install_ctx, "kimi", _config(kimi_root), bad_block)

    assert action.action == "kept"
    assert _config(kimi_root).read_text(encoding="utf-8") == original


def test_existing_config_is_backed_up_before_mutation(kimi, install_ctx, kimi_root):
    kimi_root.mkdir(parents=True, exist_ok=True)
    original = "verbose = true\n"
    _config(kimi_root).write_text(original, encoding="utf-8")

    kimi._install_hooks(kimi_root, install_ctx)

    backup = kimi_root / "config.toml.nexus-hub.bak"
    assert backup.exists()
    assert backup.read_text(encoding="utf-8") == original


def test_absent_config_is_created_with_only_the_block(kimi, install_ctx, kimi_root):
    kimi._install_hooks(kimi_root, install_ctx)
    text = _config(kimi_root).read_text(encoding="utf-8")
    assert text.startswith(BLOCK_START)
    assert not (kimi_root / "config.toml.nexus-hub.bak").exists()


def test_no_temp_file_is_left_behind(kimi, install_ctx, kimi_root):
    kimi._install_hooks(kimi_root, install_ctx)
    assert not list(kimi_root.glob("*.nexus-hub.tmp"))


def test_install_summary_states_that_hooks_are_fail_open(kimi, install_ctx, kimi_root):
    result = kimi._install_hooks(kimi_root, install_ctx)
    assert any("fail-open" in note for note in result.notes)


# ----- teardown -----------------------------------------------------------


def test_teardown_removes_only_the_managed_block(kimi, install_ctx, kimi_root):
    kimi_root.mkdir(parents=True, exist_ok=True)
    original = (
        "# user header\n"
        "verbose = true\n"
        "\n"
        "[[hooks]]\n"
        'event = "Stop"\n'
        'command = "echo mine"\n'
    )
    _config(kimi_root).write_text(original, encoding="utf-8")
    kimi._install_hooks(kimi_root, install_ctx)

    kimi.teardown(install_ctx)

    surviving = _config(kimi_root).read_text(encoding="utf-8")
    assert BLOCK_START not in surviving
    assert "# user header" in surviving
    data = tomllib.loads(surviving)
    assert [h["command"] for h in data["hooks"]] == ["echo mine"]


def test_teardown_never_deletes_a_config_with_user_content(
    kimi, install_ctx, kimi_root
):
    kimi_root.mkdir(parents=True, exist_ok=True)
    _config(kimi_root).write_text("verbose = true\n", encoding="utf-8")
    kimi._install_hooks(kimi_root, install_ctx)

    kimi.teardown(install_ctx)

    assert _config(kimi_root).exists()
    assert (
        tomllib.loads(_config(kimi_root).read_text(encoding="utf-8"))["verbose"] is True
    )


def test_teardown_of_a_block_only_config_removes_the_file(kimi, install_ctx, kimi_root):
    kimi._install_hooks(kimi_root, install_ctx)
    kimi.teardown(install_ctx)
    assert not _config(kimi_root).exists()


def test_teardown_keeps_user_agents_and_removes_owned_ones(
    kimi, install_ctx, kimi_root
):
    kimi._install_agents(kimi_root, install_ctx)
    mine = kimi_root / "agents" / "my-own.md"
    mine.write_text(
        "---\nname: my-own\ndescription: d\n---\n\nBody.\n", encoding="utf-8"
    )

    kimi.teardown(install_ctx)

    assert mine.exists()
    assert not (kimi_root / "agents" / "planner.md").exists()


def test_teardown_leaves_no_empty_directories(kimi, install_ctx, kimi_root):
    kimi._install_agents(kimi_root, install_ctx)
    kimi._install_hooks(kimi_root, install_ctx)
    assert (kimi_root / "agents").is_dir() and (kimi_root / "hooks").is_dir()

    kimi.teardown(install_ctx)

    assert not (kimi_root / "agents").exists()
    assert not (kimi_root / "hooks").exists()


def test_prune_is_idempotent(kimi, install_ctx, kimi_root):
    kimi_root.mkdir(parents=True, exist_ok=True)
    _config(kimi_root).write_text("verbose = true\n", encoding="utf-8")
    kimi._install_hooks(kimi_root, install_ctx)

    prune_config_hooks(_config(kimi_root), dry_run=False)
    first = _config(kimi_root).read_bytes()
    action = prune_config_hooks(_config(kimi_root), dry_run=False)
    assert action.action == "unchanged"
    assert _config(kimi_root).read_bytes() == first


# ----- scope boundaries ---------------------------------------------------


def test_workspace_install_writes_agents_but_no_hook_config(kimi, install_ctx):
    """Kimi documents no project hook path, so none may be invented."""
    kimi.install_workspace(install_ctx)
    root = install_ctx.target_root / ".kimi-code"
    assert any((root / "agents").glob("*.md"))
    assert not (root / "config.toml").exists()
    assert not (root / "local.toml").exists()
    assert not (root / "hooks").exists()


def test_workspace_install_does_not_touch_the_user_config(kimi, install_ctx):
    kimi.install_workspace(install_ctx)
    assert not (install_ctx.target_root / "config.toml").exists()


def test_deprecated_kimi_paths_are_never_written(kimi, install_ctx):
    """The v3.15.0 migration dropped ~/.kimi and the invented .kimi/agent.yaml."""
    kimi.install_workspace(install_ctx)
    assert not (install_ctx.target_root / ".kimi").exists()


def test_existing_surfaces_survive_the_addition(kimi, install_ctx):
    kimi.install_workspace(install_ctx)
    root = install_ctx.target_root / ".kimi-code"
    assert (root / "AGENTS.md").is_file()
    assert any((root / "skills").iterdir())


def test_instruction_only_install_adds_no_agents_or_hooks(kimi, install_ctx):
    kimi.install_workspace(replace(install_ctx, instruction_only=True))
    root = install_ctx.target_root / ".kimi-code"
    assert not (root / "agents").exists()
    assert not (root / "config.toml").exists()


def test_dry_run_writes_nothing(kimi, install_ctx, kimi_root):
    dry = replace(install_ctx, dry_run=True)
    kimi._install_agents(kimi_root, dry)
    kimi._install_hooks(kimi_root, dry)
    assert not _config(kimi_root).exists()
    assert (
        not list((kimi_root / "agents").glob("*.md"))
        if (kimi_root / "agents").exists()
        else True
    )
