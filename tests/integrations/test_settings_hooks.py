"""Gemini CLI and Qwen native hook delivery (v3.15.8 Phase 6).

Covers the contract the Phase 1 ownership matrix requires before either row may
move from finding-only to enforceable: event mapping (including Gemini CLI's
renames), regex matcher translation, host-selected commands standing in for the
``commandWindows`` slot neither platform has, a structured merge that preserves
the user's unrelated configuration, malformed-input safety, duplicate
suppression, and teardown that removes only owned entries.

Most tests drive ``_install_settings_hooks`` (and the pure adapters underneath)
rather than a full ``install()``, so they exercise the installer's own code
without paying for a 270-skill catalog copy per test. Both platforms are
parametrized wherever the assertion is a shared invariant, so the two cannot
drift apart in ownership or teardown behavior.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from scripts.lib.integrations import get
from scripts.lib.integrations._settings_hooks import (
    GEMINI_CLI_SPEC,
    OWNED_NAME_PREFIX,
    QWEN_SPEC,
    build_settings_hooks,
    command_base,
    command_for,
    merge_settings_hooks,
    prune_settings_hooks,
    script_for_host,
)
from scripts.lib.integrations.base import InstallContext

PLATFORMS = (("gemini-cli", ".gemini", GEMINI_CLI_SPEC), ("qwen", ".qwen", QWEN_SPEC))
PLATFORM_IDS = [key for key, _dir, _spec in PLATFORMS]


@pytest.fixture(params=PLATFORMS, ids=PLATFORM_IDS)
def platform(request, install_ctx: InstallContext):
    """Yield an (integration, root, spec) triple for each hook-bearing platform."""
    key, config_dir, spec = request.param
    return get(key), (install_ctx.target_root / config_dir).resolve(), spec


def _install(integration, ctx: InstallContext, root: Path, scope: str = "workspace"):
    return integration._install_settings_hooks(root, ctx, scope=scope)


def _settings(root: Path) -> dict:
    return json.loads((root / "settings.json").read_text(encoding="utf-8"))


def _handlers(data: dict, event: str) -> list[dict]:
    return [h for group in data["hooks"].get(event, []) for h in group["hooks"]]


def _all_handlers(data: dict) -> list[dict]:
    return [h for groups in data["hooks"].values() for g in groups for h in g["hooks"]]


def _catalog_settings(ctx: InstallContext) -> dict:
    path = ctx.repo_root / "catalog" / "hooks" / "settings.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _build(spec, ctx: InstallContext, windows: bool, base: str = "/hooks"):
    return build_settings_hooks(
        spec, _catalog_settings(ctx), ctx.repo_root / "catalog" / "hooks", base, windows
    )


# ----- event mapping -------------------------------------------------------


def test_gemini_renames_every_lifecycle_event(install_ctx):
    """Gemini CLI's events differ from the catalog's, so the map must translate."""
    events, _scripts, _skipped = _build(GEMINI_CLI_SPEC, install_ctx, windows=False)
    assert "BeforeTool" in events and "AfterTool" in events
    assert "BeforeAgent" in events and "AfterAgent" in events
    # The Claude-style names must NOT leak through as Gemini events.
    for claude_name in ("PreToolUse", "PostToolUse", "UserPromptSubmit", "Stop"):
        assert claude_name not in events


def test_qwen_keeps_the_catalog_event_names(install_ctx):
    events, _scripts, _skipped = _build(QWEN_SPEC, install_ctx, windows=False)
    assert {"PreToolUse", "PostToolUse", "UserPromptSubmit", "Stop"} <= set(events)
    assert "BeforeTool" not in events


@pytest.mark.parametrize("spec", [GEMINI_CLI_SPEC, QWEN_SPEC], ids=PLATFORM_IDS)
def test_unmappable_event_is_skipped_with_a_reason(spec, install_ctx):
    """An event with no counterpart is dropped and explained, never guessed at."""
    settings = {"hooks": {"NoSuchEvent": [{"matcher": "", "hooks": []}]}}
    events, _scripts, skipped = build_settings_hooks(
        spec, settings, install_ctx.repo_root / "catalog" / "hooks", "/hooks", False
    )
    assert events == {}
    assert any("NoSuchEvent" in reason for reason in skipped)


@pytest.mark.parametrize("spec", [GEMINI_CLI_SPEC, QWEN_SPEC], ids=PLATFORM_IDS)
def test_every_emitted_event_is_declared_in_the_spec_map(spec, install_ctx):
    events, _scripts, _skipped = _build(spec, install_ctx, windows=False)
    assert set(events) <= set(spec.event_map.values())


# ----- matcher translation -------------------------------------------------


@pytest.mark.parametrize("spec", [GEMINI_CLI_SPEC, QWEN_SPEC], ids=PLATFORM_IDS)
def test_tool_matchers_are_anchored_regexes_over_platform_tool_ids(spec, install_ctx):
    """Matchers must name the platform's tools, not Claude's, as a regex."""
    events, _scripts, _skipped = _build(spec, install_ctx, windows=False)
    tool_event = "BeforeTool" if spec is GEMINI_CLI_SPEC else "PreToolUse"
    matchers = {group["matcher"] for group in events[tool_event] if "matcher" in group}
    assert matchers, "tool event emitted no matcher at all"
    for matcher in matchers:
        assert matcher.startswith("^(") and matcher.endswith(")$"), matcher
        for token in matcher[2:-2].split("|"):
            assert token in {"run_shell_command", "write_file", "replace"}, token
    # Claude tool names must not survive into a matcher.
    assert not any(name in m for m in matchers for name in ("Bash", "Write", "Edit"))


@pytest.mark.parametrize("spec", [GEMINI_CLI_SPEC, QWEN_SPEC], ids=PLATFORM_IDS)
def test_skill_matcher_has_no_equivalent_and_is_dropped(spec, install_ctx):
    settings = {
        "hooks": {
            "PostToolUse": [
                {"matcher": "Skill", "hooks": [{"command": "bash x/skill-tracker.py"}]}
            ]
        }
    }
    events, _scripts, skipped = build_settings_hooks(
        spec, settings, install_ctx.repo_root / "catalog" / "hooks", "/hooks", False
    )
    assert events == {}
    assert any("Skill" in reason for reason in skipped)


@pytest.mark.parametrize("spec", [GEMINI_CLI_SPEC, QWEN_SPEC], ids=PLATFORM_IDS)
def test_lifecycle_events_carry_no_tool_matcher(spec, install_ctx):
    """A tool matcher on a lifecycle event would never match anything."""
    events, _scripts, _skipped = _build(spec, install_ctx, windows=False)
    lifecycle = {
        "SessionStart",
        "SessionEnd",
        "BeforeAgent",
        "AfterAgent",
        "UserPromptSubmit",
        "Stop",
        "PreCompress",
        "PreCompact",
    }
    for event, groups in events.items():
        if event in lifecycle:
            assert all("matcher" not in group for group in groups), event


# ----- host-selected commands (the missing commandWindows) -----------------


@pytest.mark.parametrize("spec", [GEMINI_CLI_SPEC, QWEN_SPEC], ids=PLATFORM_IDS)
@pytest.mark.parametrize("windows", [False, True], ids=["posix", "windows"])
def test_registered_command_matches_the_installing_host(spec, install_ctx, windows):
    """Exactly one sibling is registered, and it is the one the host can run."""
    events, _scripts, _skipped = _build(spec, install_ctx, windows)
    commands = [
        handler["command"]
        for groups in events.values()
        for group in groups
        for handler in group["hooks"]
    ]
    assert commands
    for command in commands:
        if ".py" in command:
            assert command.startswith("python " if windows else "python3 ")
        elif windows:
            assert command.startswith("powershell ") and ".ps1" in command
            assert ".sh" not in command
        else:
            assert command.startswith("bash ") and ".sh" in command
            assert ".ps1" not in command


@pytest.mark.parametrize("spec", [GEMINI_CLI_SPEC, QWEN_SPEC], ids=PLATFORM_IDS)
@pytest.mark.parametrize("windows", [False, True], ids=["posix", "windows"])
def test_both_siblings_are_copied_regardless_of_host(spec, install_ctx, windows):
    """Re-running on the other OS only re-points the registration."""
    _events, scripts, _skipped = _build(spec, install_ctx, windows)
    shell_stems = {Path(s).stem for s in scripts if not s.endswith(".py")}
    assert shell_stems
    for stem in shell_stems:
        assert f"{stem}.sh" in scripts and f"{stem}.ps1" in scripts


@pytest.mark.parametrize("spec", [GEMINI_CLI_SPEC, QWEN_SPEC], ids=PLATFORM_IDS)
def test_only_the_hosts_shell_flavored_guardrails_are_registered(spec, install_ctx):
    """Bash and PowerShell collapse onto one tool, so registering both double-fires."""
    posix, _s1, _k1 = _build(spec, install_ctx, windows=False)
    win, _s2, _k2 = _build(spec, install_ctx, windows=True)
    tool_event = "BeforeTool" if spec is GEMINI_CLI_SPEC else "PreToolUse"
    posix_names = {h["name"] for g in posix[tool_event] for h in g["hooks"]}
    win_names = {h["name"] for g in win[tool_event] for h in g["hooks"]}
    assert f"{OWNED_NAME_PREFIX}require-description" in posix_names
    assert f"{OWNED_NAME_PREFIX}require-description" not in win_names
    assert f"{OWNED_NAME_PREFIX}require-powershell-description" in win_names
    assert f"{OWNED_NAME_PREFIX}require-powershell-description" not in posix_names


@pytest.mark.parametrize("windows", [False, True], ids=["posix", "windows"])
def test_script_for_host_relies_on_the_sibling_invariant(windows):
    assert script_for_host("secret-scan.sh", windows).endswith(
        ".ps1" if windows else ".sh"
    )
    # Python hooks are cross-platform and are never swapped.
    assert script_for_host("skill-guard.py", windows) == "skill-guard.py"


def test_windows_command_quotes_the_path():
    """A hooks path under a user profile can contain spaces."""
    command = command_for("secret-scan.ps1", "C:/Users/Some One/.qwen/hooks", True)
    assert '"C:/Users/Some One/.qwen/hooks/secret-scan.ps1"' in command


# ----- handler fields ------------------------------------------------------


def test_qwen_declares_the_shell_field_and_status_message(install_ctx):
    events, _scripts, _skipped = _build(QWEN_SPEC, install_ctx, windows=False)
    shell_handlers = [
        h
        for groups in events.values()
        for g in groups
        for h in g["hooks"]
        if not h["command"].startswith("python")
    ]
    assert shell_handlers
    assert all(h["shell"] == "bash" for h in shell_handlers)
    assert all(h["statusMessage"].startswith("Nexus-Hub") for h in shell_handlers)


def test_gemini_omits_fields_it_does_not_document(install_ctx):
    events, _scripts, _skipped = _build(GEMINI_CLI_SPEC, install_ctx, windows=False)
    for groups in events.values():
        for group in groups:
            for handler in group["hooks"]:
                assert "shell" not in handler
                assert "statusMessage" not in handler


@pytest.mark.parametrize("spec", [GEMINI_CLI_SPEC, QWEN_SPEC], ids=PLATFORM_IDS)
def test_every_handler_carries_the_shared_required_fields(spec, install_ctx):
    events, _scripts, _skipped = _build(spec, install_ctx, windows=False)
    for groups in events.values():
        for group in groups:
            for handler in group["hooks"]:
                assert handler["type"] == "command"
                assert handler["name"].startswith(OWNED_NAME_PREFIX)
                assert handler["command"]
                assert isinstance(handler["timeout"], int) and handler["timeout"] > 0


# ----- workspace command paths --------------------------------------------


@pytest.mark.parametrize(
    "spec,var",
    [(GEMINI_CLI_SPEC, "GEMINI_PROJECT_DIR"), (QWEN_SPEC, "QWEN_PROJECT_DIR")],
    ids=PLATFORM_IDS,
)
def test_workspace_paths_use_the_platform_project_variable(spec, var, tmp_path):
    """A committed project settings.json must not carry an absolute local path."""
    root = tmp_path / (".gemini" if spec is GEMINI_CLI_SPEC else ".qwen")
    posix = command_base(spec, root, "workspace", "hooks", windows=False)
    assert posix == f"${var}/{root.name}/hooks"
    assert str(tmp_path) not in posix
    windows = command_base(spec, root, "workspace", "hooks", windows=True)
    assert windows == f"$env:{var}/{root.name}/hooks"


@pytest.mark.parametrize("spec", [GEMINI_CLI_SPEC, QWEN_SPEC], ids=PLATFORM_IDS)
def test_global_paths_are_absolute(spec, tmp_path):
    base = command_base(spec, tmp_path / ".gemini", "global", "hooks", windows=False)
    assert base.startswith(tmp_path.as_posix())


# ----- structured merge ----------------------------------------------------


def test_merge_preserves_unrelated_user_configuration(platform, install_ctx):
    """settings.json holds the whole CLI config, so nothing else may move."""
    integration, root, _spec = platform
    root.mkdir(parents=True, exist_ok=True)
    original = {
        "model": {"name": "some-model"},
        "ui": {"theme": "dark"},
        "mcpServers": {"mine": {"command": "node", "args": ["s.js"]}},
        "someFutureKey": {"nested": [1, 2, 3]},
    }
    (root / "settings.json").write_text(
        json.dumps(original, indent=2), encoding="utf-8"
    )

    _install(integration, install_ctx, root)

    merged = _settings(root)
    for key, value in original.items():
        assert merged[key] == value, f"{key} was not preserved"
    assert merged["hooks"], "no hooks were registered"


def test_merge_preserves_a_user_hook_in_the_same_event(platform, install_ctx):
    integration, root, spec = platform
    root.mkdir(parents=True, exist_ok=True)
    event = "BeforeTool" if spec is GEMINI_CLI_SPEC else "PreToolUse"
    user_handler = {"type": "command", "command": "echo mine", "name": "my-own-hook"}
    (root / "settings.json").write_text(
        json.dumps({"hooks": {event: [{"matcher": ".*", "hooks": [user_handler]}]}}),
        encoding="utf-8",
    )

    _install(integration, install_ctx, root)

    assert user_handler in _handlers(_settings(root), event)


def test_reinstall_does_not_duplicate_handlers(platform, install_ctx):
    integration, root, _spec = platform
    _install(integration, install_ctx, root)
    first = (root / "settings.json").read_bytes()
    _install(integration, install_ctx, root)
    assert (root / "settings.json").read_bytes() == first

    # A guardrail legitimately appears more than once within an event when the
    # catalog registers it against different matchers -- secret-scan is bound to
    # both Write and Edit, which are distinct tool ids here. What must never
    # happen is the same handler registered twice against the SAME matcher,
    # which is what would double-fire it on one tool call.
    data = _settings(root)
    seen: list[tuple[str, str, str]] = []
    for event, groups in data["hooks"].items():
        for group in groups:
            for handler in group["hooks"]:
                seen.append((event, group.get("matcher", ""), handler["name"]))
    assert len(seen) == len(set(seen))
    assert any(name.startswith(OWNED_NAME_PREFIX) for _e, _m, name in seen)


def test_second_install_after_a_user_edit_replaces_only_owned_handlers(
    platform, install_ctx
):
    """Repair: a drifted owned handler is re-merged, a user handler is not."""
    integration, root, spec = platform
    _install(integration, install_ctx, root)
    event = "BeforeTool" if spec is GEMINI_CLI_SPEC else "PreToolUse"

    data = _settings(root)
    data["hooks"][event].append(
        {
            "matcher": "^(custom_tool)$",
            "hooks": [{"type": "command", "command": "echo u"}],
        }
    )
    for group in data["hooks"][event]:
        for handler in group["hooks"]:
            if handler.get("name", "").startswith(OWNED_NAME_PREFIX):
                handler["command"] = "bash /wrong/path.sh"
    (root / "settings.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

    _install(integration, install_ctx, root)

    handlers = _handlers(_settings(root), event)
    assert {"type": "command", "command": "echo u"} in handlers
    assert not any(h.get("command") == "bash /wrong/path.sh" for h in handlers)


def test_malformed_settings_is_never_rewritten(platform, install_ctx):
    """Losing a user's whole config to a syntax error is worse than no hooks."""
    integration, root, _spec = platform
    root.mkdir(parents=True, exist_ok=True)
    broken = '{"model": "x",,,}'
    (root / "settings.json").write_text(broken, encoding="utf-8")

    result = _install(integration, install_ctx, root)

    assert (root / "settings.json").read_text(encoding="utf-8") == broken
    assert any(
        a.action == "kept" for a in result.files if a.path.endswith("settings.json")
    )


def test_non_object_settings_is_never_rewritten(platform, install_ctx):
    integration, root, _spec = platform
    root.mkdir(parents=True, exist_ok=True)
    (root / "settings.json").write_text("[1, 2, 3]", encoding="utf-8")
    _install(integration, install_ctx, root)
    assert (root / "settings.json").read_text(encoding="utf-8") == "[1, 2, 3]"


def test_existing_settings_is_backed_up_before_mutation(platform, install_ctx):
    integration, root, _spec = platform
    root.mkdir(parents=True, exist_ok=True)
    original = '{\n  "ui": {\n    "theme": "dark"\n  }\n}'
    (root / "settings.json").write_text(original, encoding="utf-8")

    _install(integration, install_ctx, root)

    backup = root / "settings.json.nexus-hub.bak"
    assert backup.exists()
    assert backup.read_text(encoding="utf-8") == original


def test_absent_settings_is_created_with_only_hooks(platform, install_ctx):
    integration, root, _spec = platform
    _install(integration, install_ctx, root)
    assert list(_settings(root)) == ["hooks"]
    assert not (root / "settings.json.nexus-hub.bak").exists()


def test_no_temp_file_is_left_behind(platform, install_ctx):
    integration, root, _spec = platform
    _install(integration, install_ctx, root)
    assert not list(root.glob("*.nexus-hub.tmp"))


# ----- kill switch ---------------------------------------------------------


def test_disable_all_hooks_is_reported_rather_than_overridden(platform, install_ctx):
    """A user kill switch is a decision, not a defect to silently reverse."""
    integration, root, _spec = platform
    root.mkdir(parents=True, exist_ok=True)
    (root / "settings.json").write_text(
        json.dumps({"disableAllHooks": True}), encoding="utf-8"
    )

    result = _install(integration, install_ctx, root)

    assert _settings(root)["disableAllHooks"] is True
    assert any("disableAllHooks" in note for note in result.notes)


def test_install_summary_does_not_claim_an_armed_guardrail(platform, install_ctx):
    integration, root, _spec = platform
    result = _install(integration, install_ctx, root)
    assert result.notes, "install reported nothing about hook activation"


# ----- teardown ------------------------------------------------------------


def test_teardown_removes_only_owned_handlers(platform, install_ctx):
    integration, root, spec = platform
    root.mkdir(parents=True, exist_ok=True)
    event = "BeforeTool" if spec is GEMINI_CLI_SPEC else "PreToolUse"
    user_handler = {"type": "command", "command": "echo mine", "name": "my-own-hook"}
    (root / "settings.json").write_text(
        json.dumps(
            {"ui": {"theme": "dark"}, "hooks": {event: [{"hooks": [user_handler]}]}}
        ),
        encoding="utf-8",
    )
    _install(integration, install_ctx, root)

    integration.teardown(install_ctx)

    surviving = _settings(root)
    assert surviving["ui"] == {"theme": "dark"}
    assert _handlers(surviving, event) == [user_handler]
    assert not any(
        h["name"].startswith(OWNED_NAME_PREFIX) for h in _all_handlers(surviving)
    )


def test_teardown_never_deletes_the_user_settings_file(platform, install_ctx):
    integration, root, _spec = platform
    root.mkdir(parents=True, exist_ok=True)
    (root / "settings.json").write_text(
        json.dumps({"ui": {"theme": "dark"}}), encoding="utf-8"
    )
    _install(integration, install_ctx, root)

    integration.teardown(install_ctx)

    assert (root / "settings.json").exists()
    assert _settings(root)["ui"] == {"theme": "dark"}


def test_teardown_of_a_hooks_only_file_removes_it(platform, install_ctx):
    integration, root, _spec = platform
    _install(integration, install_ctx, root)
    integration.teardown(install_ctx)
    assert not (root / "settings.json").exists()


def test_teardown_leaves_no_empty_hooks_directory(platform, install_ctx):
    integration, root, _spec = platform
    _install(integration, install_ctx, root)
    assert (root / "hooks").is_dir()
    integration.teardown(install_ctx)
    assert not (root / "hooks").exists()


def test_prune_is_idempotent(platform, install_ctx):
    integration, root, _spec = platform
    root.mkdir(parents=True, exist_ok=True)
    (root / "settings.json").write_text(json.dumps({"ui": {}}), encoding="utf-8")
    _install(integration, install_ctx, root)
    base = command_base(
        integration.hook_spec, root, "workspace", "hooks", windows=False
    )
    prune_settings_hooks(root / "settings.json", base, dry_run=False)
    first = (root / "settings.json").read_bytes()
    action = prune_settings_hooks(root / "settings.json", base, dry_run=False)
    assert action.action == "unchanged"
    assert (root / "settings.json").read_bytes() == first


# ----- ownership by name ---------------------------------------------------


def test_a_renamed_owned_handler_is_still_recognized(install_ctx):
    """The installed hooks dir is the second ownership signal after the name."""
    dst = install_ctx.target_root / "settings.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(
        json.dumps(
            {
                "hooks": {
                    "PreToolUse": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "name": "renamed-by-hand",
                                    "command": "bash /owned/hooks/secret-scan.sh",
                                }
                            ]
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    merge_settings_hooks(install_ctx, "qwen", dst, {}, "/owned/hooks")

    assert "hooks" not in json.loads(dst.read_text(encoding="utf-8"))


def test_a_user_handler_pointing_elsewhere_is_not_claimed(install_ctx):
    dst = install_ctx.target_root / "settings.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    mine = {"type": "command", "name": "theirs", "command": "bash /elsewhere/x.sh"}
    dst.write_text(
        json.dumps({"hooks": {"PreToolUse": [{"hooks": [mine]}]}}), encoding="utf-8"
    )

    merge_settings_hooks(install_ctx, "qwen", dst, {}, "/owned/hooks")

    assert _handlers(json.loads(dst.read_text(encoding="utf-8")), "PreToolUse") == [
        mine
    ]


# ----- dry run and non-regression -----------------------------------------


def test_dry_run_writes_nothing(platform, install_ctx):
    integration, root, _spec = platform
    _install(integration, replace(install_ctx, dry_run=True), root)
    assert not (root / "settings.json").exists()


def test_hooks_install_does_not_disturb_the_existing_surfaces(install_ctx):
    """Qwen's skills, agents, commands, and QWEN.md must survive the addition."""
    qwen = get("qwen")
    qwen.install_workspace(install_ctx)
    root = install_ctx.target_root
    assert (root / "QWEN.md").is_file()
    for subdir in ("skills", "agents", "commands"):
        assert any((root / ".qwen" / subdir).iterdir()), subdir
    assert (root / ".qwen" / "settings.json").is_file()
    assert any((root / ".qwen" / "hooks").iterdir())


def test_instruction_only_install_registers_no_hooks(install_ctx):
    qwen = get("qwen")
    qwen.install_workspace(replace(install_ctx, instruction_only=True))
    assert not (install_ctx.target_root / ".qwen" / "settings.json").exists()
