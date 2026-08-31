"""Per-platform seeding tests for the install-time behavioral defaults.

Covers v3.16.0 Phase 3. `configs/platform-defaults.json` declares what each
platform's default should be; `scripts/lib/integrations/platform_defaults.py`
seeds it into that platform's own config at global-install time.

The assertions that matter most are the ones about NOT writing:

- a value the user already set is never overwritten (seed-if-absent),
- a user's comments and formatting survive (tomlkit for TOML, append-only for
  YAML, because a PyYAML round-trip silently strips every comment),
- an UNVERIFIED or not-writable platform receives nothing at all.

A defaults mechanism that clobbers a user's config is worse than no defaults
mechanism, so those paths get more coverage than the happy path.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.integrations import list_keys  # noqa: E402
from scripts.lib.integrations import platform_defaults as pd  # noqa: E402
from scripts.lib.integrations.result import VALID_ACTIONS  # noqa: E402

SOURCE = json.loads(
    (REPO_ROOT / "configs" / "platform-defaults.json").read_text(encoding="utf-8")
)
PLATFORMS = SOURCE["platforms"]
WRITE_TARGETS = {
    k: v for k, v in PLATFORMS.items() if v["install_target"]["mode"] == "write"
}

tomlkit = pytest.importorskip("tomlkit", reason="TOML seeding needs tomlkit")
yaml = pytest.importorskip("yaml", reason="YAML seeding needs PyYAML")


class Ctx:
    """Minimal InstallContext stand-in; the seeder only reads three attributes."""

    def __init__(self, scope: str = "global", dry_run: bool = False) -> None:
        self.scope = scope
        self.dry_run = dry_run
        self.manifest = None


def _source_with(key: str, path: Path, fmt: str, settings: dict) -> dict:
    return {
        "platforms": {
            key: {
                "settings": settings,
                "install_target": {
                    "mode": "write",
                    "path": str(path),
                    "format": fmt,
                    "scope": "global",
                    "merge": "seed-if-absent",
                },
            }
        }
    }


# --------------------------------------------------------------------------
# Declaration shape
# --------------------------------------------------------------------------


def test_every_write_target_uses_a_supported_format():
    """A declared format with no writer would be a silent no-op on install."""
    for name, entry in WRITE_TARGETS.items():
        fmt = entry["install_target"]["format"]
        assert fmt in pd.SUPPORTED_FORMATS, f"{name}: no writer for format {fmt!r}"
        assert fmt in pd._WRITERS, f"{name}: format {fmt!r} has no registered writer"


def test_every_declared_platform_is_a_registered_integration():
    unknown = sorted(set(PLATFORMS) - set(list_keys()))
    assert not unknown, f"defaults declare non-registered platforms: {unknown}"


def test_gemini_never_declares_a_write_target():
    """Gemini's VS Code lever is verified, but gemini-cli owns ~/.gemini settings."""
    gemini = PLATFORMS["gemini"]
    assert gemini["settings"] == {}
    assert gemini["install_target"]["mode"] == "not-writable"
    assert PLATFORMS["gemini-cli"]["install_target"]["path"] == "~/.gemini/settings.json"
    owners = [
        name
        for name, entry in WRITE_TARGETS.items()
        if entry["install_target"]["path"] == "~/.gemini/settings.json"
    ]
    assert owners == ["gemini-cli"], f"~/.gemini/settings.json must have one owner, got {owners}"


def test_no_two_platforms_write_the_same_file():
    seen: dict[str, str] = {}
    for name, entry in WRITE_TARGETS.items():
        path = entry["install_target"]["path"]
        assert path not in seen, f"{name} and {seen[path]} both write {path}"
        seen[path] = name


# --------------------------------------------------------------------------
# JSON seeding
# --------------------------------------------------------------------------


def test_json_target_is_created_when_absent(tmp_path: Path):
    target = tmp_path / "settings.json"
    src = _source_with("qwen", target, "json", {"model": {"reasoningEffort": "medium"}})

    actions = pd.seed_platform_defaults("qwen", Ctx(), src)

    assert [a.action for a in actions] == ["created"]
    assert json.loads(target.read_text(encoding="utf-8")) == {
        "model": {"reasoningEffort": "medium"}
    }


def test_json_target_merges_without_clobbering_user_keys(tmp_path: Path):
    target = tmp_path / "settings.json"
    target.write_text(json.dumps({"userKey": "mine", "model": {"name": "custom"}}), encoding="utf-8")
    src = _source_with("qwen", target, "json", {"model": {"reasoningEffort": "medium"}})

    actions = pd.seed_platform_defaults("qwen", Ctx(), src)

    data = json.loads(target.read_text(encoding="utf-8"))
    assert [a.action for a in actions] == ["updated"]
    assert data["userKey"] == "mine", "an unrelated user key must survive"
    assert data["model"]["name"] == "custom", "a sibling key must survive"
    assert data["model"]["reasoningEffort"] == "medium"


def test_json_never_overwrites_a_value_the_user_already_set(tmp_path: Path):
    """The single most important guarantee: reinstall must not reset a choice."""
    target = tmp_path / "settings.json"
    target.write_text(json.dumps({"model": {"reasoningEffort": "xhigh"}}), encoding="utf-8")
    src = _source_with("qwen", target, "json", {"model": {"reasoningEffort": "medium"}})

    actions = pd.seed_platform_defaults("qwen", Ctx(), src)

    assert json.loads(target.read_text(encoding="utf-8"))["model"]["reasoningEffort"] == "xhigh"
    assert [a.action for a in actions] == ["kept"]


def test_json_seeding_is_idempotent(tmp_path: Path):
    target = tmp_path / "settings.json"
    src = _source_with("qwen", target, "json", {"model": {"reasoningEffort": "medium"}})

    pd.seed_platform_defaults("qwen", Ctx(), src)
    snapshot = target.read_bytes()
    second = pd.seed_platform_defaults("qwen", Ctx(), src)

    assert target.read_bytes() == snapshot
    assert [a.action for a in second] == ["kept"]


def test_antigravity_seeds_documented_default_agent_mode(tmp_path: Path, monkeypatch):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))

    actions = pd.seed_platform_defaults("antigravity2", Ctx())

    target = fake_home / ".gemini" / "antigravity-cli" / "settings.json"
    assert json.loads(target.read_text(encoding="utf-8")) == {"agentMode": "default"}
    assert [a.action for a in actions] == ["created"]


def test_antigravity_never_overwrites_user_agent_mode(tmp_path: Path, monkeypatch):
    fake_home = tmp_path / "home"
    target = fake_home / ".gemini" / "antigravity-cli" / "settings.json"
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps({"agentMode": "accept-edits"}), encoding="utf-8")
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))

    actions = pd.seed_platform_defaults("antigravity2", Ctx())

    assert json.loads(target.read_text(encoding="utf-8")) == {
        "agentMode": "accept-edits"
    }
    assert [a.action for a in actions] == ["kept"]


def test_json_leaves_a_scalar_where_a_table_was_expected(tmp_path: Path):
    """A user who set a scalar where we expect a table made a choice; respect it."""
    target = tmp_path / "settings.json"
    target.write_text(json.dumps({"model": "a-string"}), encoding="utf-8")
    src = _source_with("qwen", target, "json", {"model": {"reasoningEffort": "medium"}})

    pd.seed_platform_defaults("qwen", Ctx(), src)

    assert json.loads(target.read_text(encoding="utf-8"))["model"] == "a-string"


def test_malformed_json_target_is_left_untouched(tmp_path: Path):
    target = tmp_path / "settings.json"
    target.write_text("{ not json", encoding="utf-8")
    src = _source_with("qwen", target, "json", {"model": {"reasoningEffort": "medium"}})

    actions = pd.seed_platform_defaults("qwen", Ctx(), src)

    assert target.read_text(encoding="utf-8") == "{ not json"
    assert [a.action for a in actions] == ["kept"]


# --------------------------------------------------------------------------
# TOML seeding (comments and layout must survive)
# --------------------------------------------------------------------------


def test_toml_target_is_created_when_absent(tmp_path: Path):
    target = tmp_path / "config.toml"
    src = _source_with("codex", target, "toml", {"model_reasoning_effort": "medium"})

    actions = pd.seed_platform_defaults("codex", Ctx(), src)

    assert [a.action for a in actions] == ["created"]
    assert tomlkit.parse(target.read_text(encoding="utf-8"))["model_reasoning_effort"] == "medium"


def test_toml_preserves_user_comments_and_unrelated_keys(tmp_path: Path):
    """The reason tomlkit is a dependency rather than a plain TOML writer."""
    original = '# my important note\nmodel = "gpt-5.5"\n\n[profiles.deep]\nverbose = true\n'
    target = tmp_path / "config.toml"
    target.write_text(original, encoding="utf-8")
    src = _source_with("codex", target, "toml", {"model_reasoning_effort": "medium"})

    pd.seed_platform_defaults("codex", Ctx(), src)

    body = target.read_text(encoding="utf-8")
    assert "# my important note" in body, "user comments must survive a seed"
    assert 'model = "gpt-5.5"' in body, "user values must survive a seed"
    assert "[profiles.deep]" in body, "user tables must survive a seed"
    assert tomlkit.parse(body)["model_reasoning_effort"] == "medium"


def test_toml_never_overwrites_an_existing_value(tmp_path: Path):
    target = tmp_path / "config.toml"
    target.write_text('model_reasoning_effort = "xhigh"\n', encoding="utf-8")
    src = _source_with("codex", target, "toml", {"model_reasoning_effort": "medium"})

    actions = pd.seed_platform_defaults("codex", Ctx(), src)

    assert tomlkit.parse(target.read_text(encoding="utf-8"))["model_reasoning_effort"] == "xhigh"
    assert [a.action for a in actions] == ["kept"]


def test_toml_seeds_a_nested_table(tmp_path: Path):
    target = tmp_path / "config.toml"
    src = _source_with("kimi", target, "toml", {"thinking": {"effort": "medium"}})

    pd.seed_platform_defaults("kimi", Ctx(), src)

    assert tomlkit.parse(target.read_text(encoding="utf-8"))["thinking"]["effort"] == "medium"


def test_malformed_toml_target_is_left_untouched(tmp_path: Path):
    target = tmp_path / "config.toml"
    target.write_text("this is [not valid toml\n", encoding="utf-8")
    src = _source_with("codex", target, "toml", {"model_reasoning_effort": "medium"})

    actions = pd.seed_platform_defaults("codex", Ctx(), src)

    assert target.read_text(encoding="utf-8") == "this is [not valid toml\n"
    assert [a.action for a in actions] == ["kept"]


# --------------------------------------------------------------------------
# YAML seeding (append-only on an existing file)
# --------------------------------------------------------------------------


def test_yaml_target_is_created_when_absent(tmp_path: Path):
    target = tmp_path / ".aider.conf.yml"
    src = _source_with("aider", target, "yaml", {"reasoning-effort": "medium"})

    actions = pd.seed_platform_defaults("aider", Ctx(), src)

    assert [a.action for a in actions] == ["created"]
    assert yaml.safe_load(target.read_text(encoding="utf-8"))["reasoning-effort"] == "medium"


def test_hermes_reasoning_effort_uses_current_agent_namespace(tmp_path: Path):
    target = tmp_path / "config.yaml"
    src = _source_with(
        "hermes", target, "yaml", {"agent": {"reasoning_effort": "medium"}}
    )

    actions = pd.seed_platform_defaults("hermes", Ctx(), src)

    loaded = yaml.safe_load(target.read_text(encoding="utf-8"))
    assert loaded["agent"]["reasoning_effort"] == "medium"
    assert "reasoning_effort" not in loaded
    assert [a.action for a in actions] == ["created"]


def test_yaml_append_preserves_comments_and_existing_content(tmp_path: Path):
    """PyYAML cannot round-trip comments, so an existing file is appended to."""
    original = "# keep me\nmodel: my-model\n"
    target = tmp_path / ".aider.conf.yml"
    target.write_text(original, encoding="utf-8")
    src = _source_with("aider", target, "yaml", {"reasoning-effort": "medium"})

    actions = pd.seed_platform_defaults("aider", Ctx(), src)

    body = target.read_text(encoding="utf-8")
    assert body.startswith(original), "the original file must be preserved verbatim"
    assert "# keep me" in body
    loaded = yaml.safe_load(body)
    assert loaded["model"] == "my-model"
    assert loaded["reasoning-effort"] == "medium"
    assert [a.action for a in actions] == ["updated"]


def test_yaml_skips_a_key_whose_top_level_parent_already_exists(tmp_path: Path):
    """Appending a second mapping for an existing key would duplicate it."""
    target = tmp_path / "config.yaml"
    target.write_text("skills:\n  guard_agent_created: true\n", encoding="utf-8")
    src = _source_with("hermes", target, "yaml", {"skills": {"write_approval": True}})

    actions = pd.seed_platform_defaults("hermes", Ctx(), src)

    loaded = yaml.safe_load(target.read_text(encoding="utf-8"))
    assert loaded == {"skills": {"guard_agent_created": True}}, "must not duplicate the key"
    assert [a.action for a in actions] == ["kept"]


def test_yaml_never_overwrites_an_existing_value(tmp_path: Path):
    target = tmp_path / ".aider.conf.yml"
    target.write_text("reasoning-effort: xhigh\n", encoding="utf-8")
    src = _source_with("aider", target, "yaml", {"reasoning-effort": "medium"})

    actions = pd.seed_platform_defaults("aider", Ctx(), src)

    assert yaml.safe_load(target.read_text(encoding="utf-8"))["reasoning-effort"] == "xhigh"
    assert [a.action for a in actions] == ["kept"]


def test_malformed_yaml_target_is_left_untouched(tmp_path: Path):
    target = tmp_path / "config.yaml"
    target.write_text("a:\n  - b\n c: broken\n", encoding="utf-8")
    src = _source_with("hermes", target, "yaml", {"reasoning_effort": "medium"})

    actions = pd.seed_platform_defaults("hermes", Ctx(), src)

    assert [a.action for a in actions] == ["kept"]


# --------------------------------------------------------------------------
# Platforms that must receive nothing
# --------------------------------------------------------------------------


NOT_WRITABLE = sorted(
    k for k, v in PLATFORMS.items() if v["install_target"]["mode"] == "not-writable"
)


@pytest.mark.parametrize("key", NOT_WRITABLE)
def test_not_writable_platforms_receive_nothing(key: str, tmp_path: Path):
    """Derived from the declaration, not hardcoded, so a reclassification is covered."""
    assert pd.seed_platform_defaults(key, Ctx()) == []


def test_aider_is_not_writable_because_it_has_no_nexus_hub_surface():
    """Regression: aider's install_global is a documented no-op.

    The integration's own docstring states that ~/.aider.conf.yml is a surface
    Nexus-Hub does not touch, and it performs no Aider detection. Phase 3
    initially declared it writable; the integration suite caught the
    contradiction. The lever is still VERIFIED in the contract - what is absent
    is a surface to write it through, not evidence.
    """
    assert PLATFORMS["aider"]["install_target"]["mode"] == "not-writable"
    assert pd.seed_platform_defaults("aider", Ctx()) == []


def test_claude_is_not_double_written(tmp_path: Path):
    """Claude's settings.json is delivered by the installer copy, not seeded."""
    assert PLATFORMS["claude"]["install_target"]["mode"] == "already-delivered"
    assert pd.seed_platform_defaults("claude", Ctx()) == []


@pytest.mark.parametrize("key", sorted(set(list_keys()) - set(PLATFORMS)))
def test_undeclared_platforms_receive_nothing(key: str):
    """No UNVERIFIED platform may be seeded: the do-not-invent rule at runtime."""
    assert pd.seed_platform_defaults(key, Ctx()) == []


def test_workspace_scope_seeds_nothing(tmp_path: Path):
    target = tmp_path / "settings.json"
    src = _source_with("qwen", target, "json", {"model": {"reasoningEffort": "medium"}})

    assert pd.seed_platform_defaults("qwen", Ctx(scope="workspace"), src) == []
    assert not target.exists()


def test_dry_run_writes_nothing(tmp_path: Path):
    target = tmp_path / "settings.json"
    src = _source_with("qwen", target, "json", {"model": {"reasoningEffort": "medium"}})

    actions = pd.seed_platform_defaults("qwen", Ctx(dry_run=True), src)

    assert not target.exists(), "a dry run must not touch the disk"
    assert [a.action for a in actions] == ["created"]


# --------------------------------------------------------------------------
# Degradation and plumbing
# --------------------------------------------------------------------------


def test_missing_source_degrades_to_no_seeding(tmp_path: Path):
    assert pd.load_source((tmp_path / "absent.json",)) == {}


def test_malformed_source_degrades_with_one_note(tmp_path: Path, capsys):
    path = tmp_path / "platform-defaults.json"
    path.write_text("{ not json", encoding="utf-8")

    assert pd.load_source((path,)) == {}
    err = capsys.readouterr().err
    assert "unreadable" in err and err.count("\n") == 1


def test_unsupported_format_is_a_note_not_a_crash(tmp_path: Path, capsys):
    src = _source_with("qwen", tmp_path / "x.ini", "ini", {"a": 1})

    assert pd.seed_platform_defaults("qwen", Ctx(), src) == []
    assert "unsupported target format" in capsys.readouterr().err


def test_every_action_is_in_the_valid_vocabulary(tmp_path: Path):
    target = tmp_path / "settings.json"
    src = _source_with("qwen", target, "json", {"model": {"reasoningEffort": "medium"}})
    for _ in range(2):
        for action in pd.seed_platform_defaults("qwen", Ctx(), src):
            assert action.action in VALID_ACTIONS


def test_merge_missing_reports_the_paths_it_added():
    target: dict = {"keep": 1}
    added = pd.merge_missing(target, {"a": {"b": "x"}, "c": "y"})
    assert sorted(added) == ["a.b", "c"]
    assert target == {"keep": 1, "a": {"b": "x"}, "c": "y"}


def test_home_is_resolved_through_path_home_not_expanduser(tmp_path: Path, monkeypatch):
    """Regression: the seeder must honour a patched Path.home().

    The first implementation used os.path.expanduser, which reads USERPROFILE /
    HOME from the process environment and therefore escaped the fake home the
    integration test suite installs into. The result was config files written
    into the developer's REAL home directory during a test run. Resolving `~`
    through Path.home() is what confines a seed to the home under test.
    """
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))

    resolved = pd._expand("~/.qwen/settings.json")

    assert resolved == fake_home / ".qwen" / "settings.json"
    assert str(tmp_path) in str(resolved), "must not escape the patched home"


def test_seeding_writes_under_a_patched_home(tmp_path: Path, monkeypatch):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))
    src = {
        "platforms": {
            "qwen": {
                "settings": {"model": {"reasoningEffort": "medium"}},
                "install_target": {
                    "mode": "write",
                    "path": "~/.qwen/settings.json",
                    "format": "json",
                    "scope": "global",
                    "merge": "seed-if-absent",
                },
            }
        }
    }

    pd.seed_platform_defaults("qwen", Ctx(), src)

    assert (fake_home / ".qwen" / "settings.json").is_file()


def test_undetected_platforms_are_not_seeded():
    """Regression: seeding must not create config for uninstalled software.

    The dispatcher hook originally ran unconditionally, so a detection-gated
    integration that had marked itself not-detected still received a seeded
    config file. That would create, for example, ~/.hermes/config.yaml on a
    machine with no Hermes installed.
    """
    body = (REPO_ROOT / "scripts" / "lib" / "integrations" / "base.py").read_text(encoding="utf-8")
    assert "result.detected is not False" in body, (
        "seeding must be gated on the detection outcome, and on `is not False` "
        "rather than truthiness, because detected=None means 'not detection-gated'"
    )


def test_seeding_is_wired_into_the_install_dispatcher():
    """A hook nobody calls is not a feature; assert the wiring survives edits."""
    body = (REPO_ROOT / "scripts" / "lib" / "integrations" / "base.py").read_text(encoding="utf-8")
    assert "seed_platform_defaults" in body, (
        "IntegrationBase.install must invoke seed_platform_defaults for global scope"
    )
