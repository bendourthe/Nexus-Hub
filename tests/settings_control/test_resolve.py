"""Resolver tests for the settings read side (v4.14.6 Phase 2, T013).

Layer cases are parametrized from the catalog, so a new override layer is
exercised the moment it is added: one fixture home in which that layer wins, one
in which nothing is set (`tool-default`), and one with an installed version
outside the proven range.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from scripts.lib.settings_control import catalog as catalog_mod
from scripts.lib.settings_control import readers, resolve

CATALOG = catalog_mod.load_catalog()
CLAUDE_IDS = ["claude-fable-5-1", "claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5"]  # same list as conftest.Machine


def nest(path: list[str], value: Any) -> dict[str, Any]:
    for part in reversed(path):
        value = {part: value}
    return value


def _layer_cases() -> list:
    cases = []
    for write in CATALOG["writes"]:
        if write["surface"] != "cli":
            continue
        for index, layer in enumerate(write["override_layers"]):
            detect = layer["detect"]
            tag = f"{write['id']}-{index}"
            if "env" in detect:
                cases.append(pytest.param(write["id"], index, "shell", id=f"{tag}-shell"))
                cases += [pytest.param(write["id"], index, f"block:{f}", id=f"{tag}-block-{f}") for f in detect.get("settings_env", [])]
            cases += [pytest.param(write["id"], index, f"file:{f}", id=f"{tag}-file-{f}") for f in detect.get("files", [])]
    return cases


def _stage(machine: Any, write: dict[str, Any], layer: dict[str, Any], how: str) -> None:
    detect = layer["detect"]
    if "when_value_in" in detect:  # the layer only matters for this user value
        machine.put(catalog_mod.USER_FILE_IDS[write["file"]], nest(write["key_path"], detect["when_value_in"][0]))
    if how == "shell":
        machine.env[detect["env"][0]] = "layer-value"
    elif how.startswith("block:"):
        machine.put(how.split(":", 1)[1], {"env": {detect["env"][0]: "layer-value"}})
    else:
        file_id = how.split(":", 1)[1]
        if file_id == "codex-project":
            machine.trust_project()
        machine.put(file_id, nest(detect["key_paths"][0], "zz-layer-value"))


def _writes_by_id() -> dict[str, dict[str, Any]]:
    return {w["id"]: w for w in CATALOG["writes"]}


@pytest.mark.parametrize(("write_id", "index", "how"), _layer_cases())
def test_each_override_layer_wins_in_a_fixture_home(machine: Any, admitted: dict[str, Any], write_id: str, index: int, how: str) -> None:
    write = _writes_by_id()[write_id]
    layer = write["override_layers"][index]
    _stage(machine, write, layer, how)

    record = machine.records(admitted)[next(c["id"] for c in CATALOG["controls"] if write_id in c["writes"]), write["tool"], write["surface"]]

    assert record["state"] == "overridden-by", record
    assert record["fix"] == layer["fix"]
    assert record["layer"]
    assert "overridden" not in record["layer"]
    if how == "shell":
        assert record["layer"] == f"env {layer['detect']['env'][0]} (shell)"
    elif how.startswith("block:"):
        assert record["layer"].startswith(f"env {layer['detect']['env'][0]} (") and record["layer"].endswith("env block)")
    else:
        assert record["layer"].startswith("file ")


@pytest.mark.parametrize(
    ("write_id", "index"),
    [(w["id"], i) for w in CATALOG["writes"] if w["surface"] == "cli" for i, l in enumerate(w["override_layers"]) if "caveat" in l["detect"]],
)
def test_undetectable_layers_become_caveats_never_a_second_state(machine: Any, admitted: dict[str, Any], write_id: str, index: int) -> None:
    write = _writes_by_id()[write_id]
    record = machine.records(admitted)[next(c["id"] for c in CATALOG["controls"] if write_id in c["writes"]), write["tool"], write["surface"]]

    assert write["override_layers"][index]["detect"]["caveat"] in record["caveats"]
    assert record["state"] in resolve.STATES and record["state"] != "overridden-by"


def test_every_record_has_exactly_one_known_state(machine: Any, catalog: dict[str, Any], admitted: dict[str, Any]) -> None:
    for source in (catalog, admitted):
        found = resolve.resolve(source, machine.snapshot(source), CLAUDE_IDS)
        assert found and all(r["state"] in resolve.STATES for r in found)
        assert len({(r["control"], r["tool"], r["surface"]) for r in found}) == len(found)


def test_nothing_set_reports_tool_default_for_every_admitted_cell(machine: Any, catalog: dict[str, Any]) -> None:
    records = machine.records(catalog)

    assert records["model", "claude", "cli"]["state"] == "tool-default"
    assert records["posture", "claude", "cli"]["state"] == "tool-default"
    assert records["model", "codex", "cli"]["state"] == "tool-default"
    assert records["posture", "codex", "cli"]["state"] == "tool-default"
    assert records["git_guardrails", "internal", "cli"]["state"] == "tool-default"
    assert all(r["value"] is None for r in records.values() if r["state"] == "tool-default")


def test_user_values_are_in_effect_and_mapped_to_control_values(machine: Any, catalog: dict[str, Any]) -> None:
    machine.put("claude-user", {"model": "opus", "permissions": {"defaultMode": "bypassPermissions"}})
    machine.put("codex-user", {"approval_policy": "never", "sandbox_mode": "workspace-write", "model": "gpt-x"})
    machine.put("nexus-guardrails", {"block_git_bypass_flags": True})

    records = machine.records(catalog)

    assert (records["model", "claude", "cli"]["state"], records["model", "claude", "cli"]["value"]) == ("in-effect", "opus")
    assert (records["posture", "claude", "cli"]["state"], records["posture", "claude", "cli"]["value"]) == ("in-effect", "full-auto")
    assert (records["posture", "codex", "cli"]["state"], records["posture", "codex", "cli"]["value"]) == ("in-effect", "full-auto")
    assert (records["git_guardrails", "internal", "cli"]["state"], records["git_guardrails", "internal", "cli"]["value"]) == ("in-effect", "on")
    assert records["model", "codex", "cli"]["value"] == "gpt-x"


def test_ambiguous_native_value_lists_every_control_value(machine: Any, catalog: dict[str, Any]) -> None:
    machine.put("codex-user", {"approval_policy": "on-request", "sandbox_mode": "workspace-write"})

    assert machine.records(catalog)["posture", "codex", "cli"]["value"] == "ask/accept-edits"


def test_a_value_nexus_hub_does_not_write_is_shown_with_a_caveat(machine: Any, catalog: dict[str, Any]) -> None:
    machine.put("claude-user", {"permissions": {"defaultMode": "plan"}})

    record = machine.records(catalog)["posture", "claude", "cli"]

    assert (record["state"], record["value"]) == ("in-effect", "plan")
    assert any("not a value Nexus-Hub writes" in c for c in record["caveats"])


def test_shell_model_override_changes_only_the_claude_model_row(machine: Any, catalog: dict[str, Any]) -> None:
    machine.put("claude-user", {"model": "opus"})
    machine.put("codex-user", {"model": "gpt-x"})
    before = machine.records(catalog)
    machine.env["ANTHROPIC_MODEL"] = "claude-haiku-5-5"

    after = machine.records(catalog)

    assert after["model", "claude", "cli"]["state"] == "overridden-by"
    assert after["model", "claude", "cli"]["layer"] == "env ANTHROPIC_MODEL (shell)"
    assert after["model", "claude", "cli"]["layer_value"] == "claude-haiku-5-5"
    changed = {k for k in after if after[k] != before[k]}
    assert changed == {("model", "claude", "cli")}


def test_legacy_effort_env_block_is_named_with_its_fix_once_effort_is_admitted(machine: Any, admitted: dict[str, Any]) -> None:
    machine.put("claude-user", {"env": {"CLAUDE_CODE_EFFORT_LEVEL": "high"}, "modelSettings": {m: {"effortLevel": "high"} for m in CLAUDE_IDS}})

    record = machine.records(admitted)["effort", "claude", "cli"]

    assert record["state"] == "overridden-by"
    assert record["layer"] == "env CLAUDE_CODE_EFFORT_LEVEL (settings.json env block)"
    assert record["fix"].startswith("Unset CLAUDE_CODE_EFFORT_LEVEL")


def test_the_legacy_effort_override_is_surfaced_while_effort_is_not_settable(machine: Any, catalog: dict[str, Any]) -> None:
    machine.put("claude-user", {"env": {"CLAUDE_CODE_EFFORT_LEVEL": "high"}})

    record = machine.records(catalog)["effort", "claude", "cli"]

    assert record["state"] == "not-settable"
    assert any("env CLAUDE_CODE_EFFORT_LEVEL (settings.json env block) = high" in c for c in record["caveats"])


def test_a_layer_that_agrees_with_the_user_value_overrides_nothing(machine: Any, catalog: dict[str, Any]) -> None:
    machine.put("claude-user", {"model": "opus"})
    machine.put("claude-project", {"model": "opus"})

    assert machine.records(catalog)["model", "claude", "cli"]["state"] == "in-effect"


def test_highest_ranked_layer_wins_and_the_rest_are_listed(machine: Any, catalog: dict[str, Any]) -> None:
    machine.put("claude-user", {"model": "opus"})
    machine.put("claude-project", {"model": "sonnet"})
    machine.env["ANTHROPIC_MODEL"] = "haiku"
    machine.put("claude-managed", {"model": "fixed"})

    record = machine.records(catalog)["model", "claude", "cli"]

    assert record["layer"].startswith("file ") and record["layer"].endswith("(managed)")
    assert any(c.startswith("Also set: env ANTHROPIC_MODEL (shell)") for c in record["caveats"])
    assert any(c.startswith("Also set: file .claude/settings.json (project)") for c in record["caveats"])


def test_disable_bypass_blocks_only_a_bypass_default(machine: Any, catalog: dict[str, Any]) -> None:
    machine.put("claude-user", {"permissions": {"defaultMode": "acceptEdits", "disableBypassPermissionsMode": "disable"}})
    assert machine.records(catalog)["posture", "claude", "cli"]["state"] == "in-effect"

    machine.put("claude-user", {"permissions": {"defaultMode": "bypassPermissions"}})
    record = machine.records(catalog)["posture", "claude", "cli"]

    assert record["state"] == "overridden-by" and "disableBypassPermissionsMode" not in record["layer"]
    assert record["layer"] == "file ~/.claude/settings.json (user)"


def test_project_bypass_default_is_ignored_by_the_vendor_and_so_by_the_resolver(machine: Any, catalog: dict[str, Any]) -> None:
    machine.put("claude-user", {"permissions": {"defaultMode": "acceptEdits"}})
    machine.put("claude-project", {"permissions": {"defaultMode": "bypassPermissions"}})

    assert machine.records(catalog)["posture", "claude", "cli"]["state"] == "in-effect"


def test_codex_project_file_is_read_only_for_a_trusted_project(machine: Any, catalog: dict[str, Any]) -> None:
    machine.put("codex-user", {"model": "user-model"})
    machine.put("codex-project", {"model": "project-model"})

    untrusted = machine.records(catalog)["model", "codex", "cli"]
    assert untrusted["state"] == "in-effect"
    assert any(".codex/config.toml was not read (the project is not trusted by Codex)" in c for c in untrusted["caveats"])

    machine.trust_project()
    trusted = machine.records(catalog)["model", "codex", "cli"]
    assert (trusted["state"], trusted["layer"], trusted["layer_value"]) == ("overridden-by", "file .codex/config.toml (project)", "project-model")


def test_codex_default_permissions_and_mismatched_sandbox_are_caveats(machine: Any, catalog: dict[str, Any]) -> None:
    machine.put("codex-user", {"approval_policy": "never", "sandbox_mode": "read-only", "default_permissions": ":workspace"})

    record = machine.records(catalog)["posture", "codex", "cli"]

    assert record["state"] == "in-effect"
    assert any(c.startswith("sandbox_mode is read-only; Nexus-Hub writes workspace-write for full-auto") for c in record["caveats"])
    assert any("default_permissions is set" in c for c in record["caveats"])


def test_echoed_values_cannot_drive_the_terminal(machine: Any, catalog: dict[str, Any]) -> None:
    machine.put("claude-project", {"model": "evil\x1b[2Jname\u00e9"})

    record = machine.records(catalog)["model", "claude", "cli"]

    assert record["layer_value"] == r"evil\x1b[2Jname\xe9"
    assert record["layer_value"].isascii() and "\x1b" not in record["layer_value"]


def test_echoed_project_values_are_truncated(machine: Any, catalog: dict[str, Any]) -> None:
    machine.put("claude-project", {"model": "x" * 500})

    record = machine.records(catalog)["model", "claude", "cli"]

    assert len(record["layer_value"]) <= resolve.ECHO_LIMIT and record["layer_value"].endswith("...")


@pytest.mark.parametrize(("seen", "outside"), [("2.1.290", True), ("2.1.282", True), ("2.1.283", False), ("2.1.283.0", False)])
def test_version_outside_the_proven_range_is_unverified(machine: Any, catalog: dict[str, Any], seen: str, outside: bool) -> None:
    machine.commands["claude"] = seen
    machine.put("claude-user", {"model": "opus"})
    machine.env["ANTHROPIC_MODEL"] = "haiku"

    record = machine.records(catalog)["model", "claude", "cli"]

    if outside:
        assert (record["state"], record["detail"]) == ("unverified-for-version", seen)
        assert any(c.startswith("Present: env ANTHROPIC_MODEL (shell)") for c in record["caveats"])
    else:
        assert record["state"] == "overridden-by"
    assert machine.records(catalog)["model", "codex", "cli"]["state"] == "tool-default"


def test_a_failing_version_call_is_cannot_detect_for_version_ranged_writes_only(machine: Any, catalog: dict[str, Any]) -> None:
    machine.version_errors["claude"] = "timed out after 5 s"

    records = machine.records(catalog)

    assert (records["model", "claude", "cli"]["state"], records["model", "claude", "cli"]["detail"]) == ("cannot-detect", "version: timed out after 5 s")
    assert records["git_guardrails", "internal", "cli"]["state"] == "tool-default"


def test_a_tool_that_is_not_installed_is_reported_so(machine: Any, catalog: dict[str, Any]) -> None:
    del machine.commands["claude"]
    del machine.commands["copilot"]

    records = machine.records(catalog)

    assert records["model", "claude", "cli"]["state"] == "tool-not-installed"
    assert records["model", "codex", "cli"]["state"] == "tool-default"
    assert records["model", "copilot-cli", "cli"]["state"] == "not-settable"
    assert any("not installed" in c for c in records["model", "copilot-cli", "cli"]["caveats"])


def test_config_directory_without_the_command_still_counts_as_installed(machine: Any, catalog: dict[str, Any]) -> None:
    del machine.commands["claude"]
    machine.put("claude-user", {"model": "opus"})

    record = machine.records(catalog)["model", "claude", "cli"]

    assert (record["state"], record["detail"]) == ("cannot-detect", "version: the command is not on PATH")


def test_editor_rows_are_cannot_detect_from_the_cli(machine: Any, admitted: dict[str, Any]) -> None:
    record = machine.records(admitted)["posture", "vscode-copilot", "vscode-host"]

    assert record["state"] == "cannot-detect" and record["detail"].startswith("read from the editor")


def test_claude_effort_covers_each_current_model_or_reports_the_gap(machine: Any, admitted: dict[str, Any]) -> None:
    assert machine.records(admitted)["effort", "claude", "cli"]["state"] == "tool-default"

    machine.put("claude-user", {"modelSettings": {"claude-opus-5-5": {"effortLevel": "high"}}})
    partial = machine.records(admitted)["effort", "claude", "cli"]
    assert (partial["state"], partial["detail"]) == ("not-covered", "claude-fable-5-1, claude-sonnet-5-5, claude-haiku-5-5")

    machine.put("claude-user", {"modelSettings": {m: {"effortLevel": "high"} for m in CLAUDE_IDS}})
    full = machine.records(admitted)["effort", "claude", "cli"]
    assert (full["state"], full["value"]) == ("in-effect", "high")

    machine.put("claude-user", {"modelSettings": {"claude-opus-5-5": {"effortLevel": "low"}}})
    assert machine.records(admitted)["effort", "claude", "cli"]["value"].startswith("mixed (")


def test_top_level_effort_alone_does_not_cover_current_models(machine: Any, admitted: dict[str, Any]) -> None:
    machine.put("claude-user", {"effortLevel": "xhigh"})

    record = machine.records(admitted)["effort", "claude", "cli"]

    assert record["state"] == "not-covered" and record["detail"] == ", ".join(CLAUDE_IDS)


def test_a_dotted_model_id_is_one_key_never_split(machine: Any, admitted: dict[str, Any]) -> None:
    ids = ["claude-x-1.2"]
    machine.put("claude-user", {"modelSettings": {"claude-x-1.2": {"effortLevel": "medium"}}})

    record = machine.records(admitted, ids)["effort", "claude", "cli"]

    assert (record["state"], record["value"]) == ("in-effect", "medium")


def test_models_already_present_are_kept_beside_the_bundled_ids(machine: Any, admitted: dict[str, Any]) -> None:
    machine.put("claude-user", {"modelSettings": {**{m: {"effortLevel": "high"} for m in CLAUDE_IDS}, "claude-extra": {"effortLevel": "high"}}})

    record = machine.records(admitted)["effort", "claude", "cli"]

    assert record["state"] == "in-effect" and set(record["native"]) == {*CLAUDE_IDS, "claude-extra"}


@pytest.mark.parametrize(
    ("file_id", "text", "needle"),
    [
        ("claude-user", "{not json", "is not valid JSON (line 1)"),
        ("claude-user", "[1, 2]", "is not a JSON object"),
        ("codex-user", "model = ", "is not valid TOML"),
    ],
)
def test_an_unparseable_user_file_is_cannot_detect_never_a_guess(machine: Any, catalog: dict[str, Any], file_id: str, text: str, needle: str) -> None:
    machine.put(file_id, text)

    records = machine.records(catalog)
    tool = "claude" if file_id == "claude-user" else "codex"

    assert records["model", tool, "cli"]["state"] == "cannot-detect"
    assert needle in records["model", tool, "cli"]["detail"]


def test_an_unparseable_layer_file_blocks_the_verdict_for_rows_it_could_override(machine: Any, catalog: dict[str, Any]) -> None:
    machine.put("claude-user", {"model": "opus"})
    machine.put("claude-project", "{broken")

    record = machine.records(catalog)["model", "claude", "cli"]

    assert record["state"] == "cannot-detect" and ".claude/settings.json is not valid JSON" in record["detail"]
    assert machine.records(catalog)["model", "codex", "cli"]["state"] == "tool-default"


def test_a_project_file_over_one_megabyte_is_not_read(machine: Any, catalog: dict[str, Any]) -> None:
    machine.put("claude-user", {"model": "opus"})
    machine.put("claude-project", json.dumps({"model": "big", "pad": "x" * readers.MAX_PROJECT_BYTES}))

    record = machine.records(catalog)["model", "claude", "cli"]

    assert record["state"] == "in-effect"
    assert any(".claude/settings.json was not read (the file is over 1 MB)" in c for c in record["caveats"])


def test_a_project_file_outside_the_project_root_is_not_followed(machine: Any, tmp_path: Any) -> None:
    outside = tmp_path / "elsewhere" / "settings.json"
    outside.parent.mkdir()
    outside.write_text('{"model": "evil"}', encoding="utf-8")

    result = readers.read_file("claude-project", outside, "settings.json", machine.project)

    assert result.status == "skipped" and "outside the project" in result.detail


def test_a_symlinked_project_file_leading_outside_is_not_followed(
    machine: Any, catalog: dict[str, Any], tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "outside.json"
    target.write_text('{"model": "evil"}', encoding="utf-8")
    link = machine.path("claude-project")
    link.parent.mkdir(parents=True)
    try:
        link.symlink_to(target)
    except OSError:  # no symlink privilege on this host: a stand-in file whose resolution leads outside
        link.write_text('{"model": "evil"}', encoding="utf-8")
        original = Path.resolve
        monkeypatch.setattr(Path, "resolve", lambda self, *a, **k: original(target) if self == link else original(self, *a, **k))
    machine.put("claude-user", {"model": "opus"})

    record = machine.records(catalog)["model", "claude", "cli"]

    assert record["state"] == "in-effect" and any("outside the project" in c for c in record["caveats"])


def test_a_snapshot_is_immutable_and_survives_a_mid_run_edit(machine: Any, catalog: dict[str, Any]) -> None:
    machine.put("claude-user", {"model": "opus"})
    snapshot = machine.snapshot(catalog)
    before = resolve.resolve(catalog, snapshot, CLAUDE_IDS)

    machine.put("claude-user", {"model": "sonnet"}, merge_into=False)

    assert resolve.resolve(catalog, snapshot, CLAUDE_IDS) == before
    with pytest.raises(TypeError):
        snapshot.files["claude-user"] = None  # type: ignore[index]
    with pytest.raises(TypeError):
        snapshot.env["X"] = "1"  # type: ignore[index]
    with pytest.raises(AttributeError):
        snapshot.home = "elsewhere"  # type: ignore[misc]
    assert machine.records(catalog)["model", "claude", "cli"]["value"] == "sonnet"


def test_resolving_does_not_modify_the_catalog(machine: Any, catalog: dict[str, Any]) -> None:
    before = copy.deepcopy(catalog)
    machine.records(catalog)

    assert catalog == before


def test_config_directory_variables_are_honored(machine: Any, catalog: dict[str, Any], tmp_path: Any) -> None:
    alt = tmp_path / "alt-claude"
    alt.mkdir()
    (alt / "settings.json").write_text('{"model": "from-alt"}', encoding="utf-8")
    machine.env["CLAUDE_CONFIG_DIR"] = str(alt)

    assert machine.records(catalog)["model", "claude", "cli"]["value"] == "from-alt"


def test_dropping_a_cell_to_not_settable_changes_the_result_with_no_code_change(machine: Any, catalog: dict[str, Any], mutate: Any) -> None:
    flipped = mutate(catalog, "codex.model", admission="not-settable", not_settable_reason="proof withdrawn", proof=[])

    record = machine.records(flipped)["model", "codex", "cli"]

    assert (record["state"], record["detail"]) == ("not-settable", "proof withdrawn")


def test_parse_version_and_windowless_version_runner() -> None:
    assert readers.parse_version("codex-cli 0.136.0") == "0.136.0"
    assert readers.parse_version("2.1.283 (Claude Code)") == "2.1.283"
    assert readers.parse_version("nothing") is None
    import sys

    version, error = readers.run_version([sys.executable, "--version"])
    assert error is None and version and version.count(".") >= 1


def test_a_slow_version_call_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    import sys

    monkeypatch.setattr(readers, "VERSION_TIMEOUT_SECONDS", 1)

    version, error = readers.run_version([sys.executable, "-c", "import time; time.sleep(30)"])

    assert version is None and error == "timed out after 1 s"


def test_a_missing_executable_is_an_error_not_a_crash() -> None:
    version, error = readers.run_version(["definitely-not-a-real-binary-xyz"])

    assert version is None and error and error.startswith("could not run")


def test_toml_is_read_with_the_standard_library_when_tomlkit_is_missing(machine: Any, catalog: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    import sys

    monkeypatch.setitem(sys.modules, "tomlkit", None)  # forces ImportError on `import tomlkit`
    machine.put("codex-user", {"model": "gpt-x"})
    assert machine.records(catalog)["model", "codex", "cli"]["value"] == "gpt-x"

    machine.put("codex-user", "model = ")
    record = machine.records(catalog)["model", "codex", "cli"]

    assert record["state"] == "cannot-detect" and "is not valid TOML (line 1)" in record["detail"]


def test_toml_errors_name_the_line_with_tomlkit(machine: Any, catalog: dict[str, Any]) -> None:
    machine.put("codex-user", 'model = "ok"\nbroken = \n')

    record = machine.records(catalog)["model", "codex", "cli"]

    assert record["state"] == "cannot-detect" and "is not valid TOML (line 2)" in record["detail"]
