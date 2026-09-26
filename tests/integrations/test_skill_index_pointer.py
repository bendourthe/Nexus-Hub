"""Tests for the opt-in Skill-Index Pointer (v4.13.3 Phase 5).

`NEXUS_HUB_SKILL_INDEX=pointer` replaces the full skill table with a short
pointer, but only where Native Skill Enumeration holds: a VERIFIED skill read
path for the platform and scope (from `platform-read-contracts.json`) that holds
an installed skills tree. Everything else, including an unset or invalid value,
renders the full index exactly as before.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.check_memory_integration_budget import estimate_tokens
from scripts.lib.integrations import get, list_keys, runner
from scripts.lib.integrations import skill_read_paths as srp
from scripts.lib.integrations.base import InstallContext
from scripts.lib.integrations.manifest import InstallManifest

FACTS = srp.load_facts(REPO_ROOT)
INDEX = (REPO_ROOT / "data" / "SKILL_INDEX.md").read_text(encoding="utf-8")


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "home"
    root.mkdir()
    monkeypatch.setenv("HOME", str(root))
    monkeypatch.setenv("USERPROFILE", str(root))
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: root))
    monkeypatch.delenv("NEXUS_HUB_SKILL_INDEX", raising=False)
    return root


def _ctx(home: Path, mode: str = "full", scope: str = "global", repo_root: Path = REPO_ROOT) -> InstallContext:
    target = home if scope == "global" else home / "project"
    target.mkdir(exist_ok=True)
    return InstallContext(repo_root=repo_root, target_root=target, scope=scope, explicit_target=True,
                          manifest=InstallManifest(), instruction_only=True, skill_index_mode=mode)


CATALOG_SKILL = sorted(srp.catalog_skill_names(REPO_ROOT))[0]


def _seed(path: Path, name: str = CATALOG_SKILL) -> None:
    (path / name).mkdir(parents=True, exist_ok=True)
    (path / name / "SKILL.md").write_text(f"---\nname: {name}\ndescription: d\n---\n", encoding="utf-8")


def _resolved(entry_path: str, ctx: InstallContext) -> Path:
    return ctx.global_root / entry_path[2:] if entry_path.startswith("~/") else ctx.target_root / entry_path


def _verified(key: str, scope: str) -> list[str]:
    return [e["path"] for e in FACTS.get(key, {}).get(scope, []) if e.get("status") == "VERIFIED"]


# --- mode parsing -----------------------------------------------------------


@pytest.mark.parametrize(("raw", "mode"), [(None, "full"), ("", "full"), ("full", "full"), ("pointer", "pointer"),
                                           (" Pointer ", "pointer"), ("pointers", "full"), ("1", "full"),
                                           ("yes", "full")])
def test_only_pointer_selects_pointer_mode(raw: str | None, mode: str) -> None:
    assert srp.index_mode(raw) == mode


def test_runner_reads_the_variable_once(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NEXUS_HUB_SKILL_INDEX", "pointer")
    assert runner._skill_index_mode() == "pointer"
    monkeypatch.setenv("NEXUS_HUB_SKILL_INDEX", "bogus")
    assert runner._skill_index_mode() == "full"


# --- rendering --------------------------------------------------------------


def _claude_file(home: Path, mode: str) -> str:
    ctx = _ctx(home, mode)
    get("claude").install(ctx)
    return (home / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")


def test_full_mode_is_byte_identical_to_the_default(home: Path, tmp_path: Path) -> None:
    _seed(home / ".claude" / "skills")
    full = _claude_file(home, "full")
    (home / ".claude" / "CLAUDE.md").unlink()
    ctx = InstallContext(repo_root=REPO_ROOT, target_root=home, scope="global", explicit_target=True,
                         manifest=InstallManifest(), instruction_only=True)
    get("claude").install(ctx)
    assert (home / ".claude" / "CLAUDE.md").read_text(encoding="utf-8") == full
    assert full.count("**Total:") == 1


def test_pointer_replaces_the_index_on_an_eligible_platform(home: Path) -> None:
    _seed(home / ".claude" / "skills")
    text = _claude_file(home, "pointer")
    assert "**Total:" not in text
    assert "Nexus-Hub Skill Index" in text  # the install verify needle still holds
    pointer = srp.render_pointer(home / ".claude" / "skills", None)
    assert pointer in text
    assert estimate_tokens(pointer) <= 0.1 * estimate_tokens(INDEX)


def test_pointer_without_an_installed_tree_keeps_the_full_index(home: Path) -> None:
    assert _claude_file(home, "pointer").count("**Total:") == 1


def _advertised(text: str) -> list[str]:
    """Backticked paths inside the pointer block only (up to the next heading)."""
    section = text[text.index("# Nexus-Hub Skill Index"):]
    following = re.search(r"\n#", section[1:])
    section = section[: following.start() + 1] if following else section
    return [p for p in re.findall(r"`([^`]+)`", section) if "/" in p]


def test_every_advertised_path_exists(home: Path) -> None:
    _seed(home / ".claude" / "skills")
    without = _claude_file(home, "pointer")
    assert "complete table" not in without
    assert len(_advertised(without)) == 1
    (home / ".nexus-hub" / "data").mkdir(parents=True)
    (home / ".nexus-hub" / "data" / "SKILL_INDEX.md").write_text(INDEX, encoding="utf-8")
    advertised = _advertised(_claude_file(home, "pointer"))
    assert len(advertised) == 2
    assert all(Path(p).exists() for p in advertised)


@pytest.mark.parametrize("scope", ["global", "workspace"])
def test_workspace_and_global_pointers_name_existing_dirs(home: Path, scope: str) -> None:
    ctx = _ctx(home, "pointer", scope)
    for path in _verified("claude", scope):
        _seed(_resolved(path, ctx))
    pointer = get("claude")._skill_index_pointer(ctx)
    assert pointer is not None
    [skills_dir] = re.findall(r"`([^`]+)`", pointer)[:1]
    assert Path(skills_dir).is_dir()


# --- eligibility from facts and installed destinations -----------------------


@pytest.mark.parametrize("scope", ["global", "workspace"])
def test_eligibility_matches_the_facts_for_every_integration(home: Path, scope: str) -> None:
    ctx = _ctx(home, "pointer", scope)
    for key in list_keys():
        assert get(key).native_skill_enumeration(ctx) is False, f"{key} eligible with nothing installed"
    for key in list_keys():
        for path in _verified(key, scope):
            _seed(_resolved(path, ctx))
    for key in list_keys():
        expected = bool(_verified(key, scope))
        assert get(key).native_skill_enumeration(ctx) is expected, (key, scope)


def test_unverified_paths_never_count(home: Path) -> None:
    ctx = _ctx(home, "pointer")
    for scopes in FACTS.values():
        for entry in scopes.get("global", []) if isinstance(scopes, dict) else []:
            if entry.get("status") == "UNVERIFIED":
                _seed(_resolved(entry["path"], ctx))
    assert get("copilot").native_skill_enumeration(ctx) is False  # ~/.claude/skills is UNVERIFIED for Copilot
    assert get("gemini").native_skill_enumeration(ctx) is False


def test_a_tree_of_only_foreign_skills_is_not_enumeration(home: Path) -> None:
    """Another tool's skills in a shared path must not hide the Nexus-Hub index."""
    ctx = _ctx(home, "pointer")
    _seed(home / ".agents" / "skills", "some-vendor-skill")
    for key in ("copilot", "opencode", "cursor", "windsurf", "gemini-cli", "codex"):
        assert srp.enumerated_skill_dir(key, ctx) is None, key
    _seed(home / ".agents" / "skills")
    assert srp.enumerated_skill_dir("codex", ctx) == home / ".agents" / "skills"


def test_missing_contract_fails_closed(home: Path, tmp_path: Path) -> None:
    _seed(home / ".claude" / "skills")
    ctx = _ctx(home, "pointer", repo_root=tmp_path / "no-repo")
    assert srp.enumerated_skill_dir("claude", ctx) is None


def _runner_install(home: Path, keys: str, monkeypatch: pytest.MonkeyPatch) -> int:
    monkeypatch.setenv("NEXUS_HUB_SKILL_INDEX", "pointer")
    return runner.main(["install", "--scope", "global", "--target", str(home), "--integrations", keys, "--quiet"])


def test_shared_path_consumer_first_is_resolved_after_its_provider(home: Path,
                                                                     monkeypatch: pytest.MonkeyPatch) -> None:
    (home / ".copilot").mkdir()
    assert _runner_install(home, "copilot,codex", monkeypatch) == 0
    personal = (home / ".copilot" / "copilot-instructions.md").read_text(encoding="utf-8")
    assert "**Total:" not in personal  # ~/.agents/skills from codex, evaluated after codex installed


def test_failed_shared_path_provider_keeps_the_consumer_on_the_full_index(home: Path,
                                                                            monkeypatch: pytest.MonkeyPatch) -> None:
    (home / ".copilot").mkdir()
    codex = get("codex")

    def boom(ctx):
        raise RuntimeError("provider failed")

    monkeypatch.setattr(type(codex), "install", boom)
    assert _runner_install(home, "codex,copilot", monkeypatch) == 2
    personal = (home / ".copilot" / "copilot-instructions.md").read_text(encoding="utf-8")
    assert personal.count("**Total:") == 1


# --- contract validation and installers ---------------------------------------


def test_contract_facts_validate_against_the_doc() -> None:
    doc = (REPO_ROOT / "docs" / "policy" / "platform-read-contracts.md").read_text(encoding="utf-8")
    assert srp.validate(FACTS, doc) == []


@pytest.mark.parametrize(("entry", "fragment"), [
    ({"path": "~/.x/skills", "status": "MAYBE"}, "status must be"),
    ({"path": "~/.claude/skills", "status": "VERIFIED", "source": "http://x", "verified": "2026-09-25"}, "https"),
    ({"path": "~/.claude/skills", "status": "VERIFIED", "source": "https://x"}, "ISO verified date"),
    ({"path": "~/.nowhere/skills", "status": "VERIFIED", "source": "https://x", "verified": "2026-09-25"}, "not documented"),
    ({"path": ".claude/skills", "status": "VERIFIED", "source": "https://x", "verified": "2026-09-25"}, "start with ~/"),
])
def test_validate_rejects_bad_entries(entry: dict, fragment: str) -> None:
    problems = srp.validate({"demo": {"global": [entry]}}, "~/.claude/skills .claude/skills")
    assert any(fragment in p for p in problems), problems


def test_contract_verifier_runs_the_new_check() -> None:
    from scripts import verify_platform_contracts as vpc

    assert vpc.skill_read_path_problems((REPO_ROOT / "docs" / "policy" / "platform-read-contracts.md")
                                        .read_text(encoding="utf-8")) == []


@pytest.mark.parametrize("installer", ["installer.sh", "installer.ps1"])
def test_installers_pass_the_environment_through_to_the_runner(installer: str) -> None:
    text = (REPO_ROOT / "scripts" / installer).read_text(encoding="utf-8-sig")
    # The runner reads NEXUS_HUB_SKILL_INDEX from its inherited environment; an
    # installer that cleared or overrode it would silently disable the option.
    assert not re.search(r"(?m)(^|[\s;|&(])env -i\s", text)
    assert "NEXUS_HUB_SKILL_INDEX" not in text
    assert ('"$py" "${args[@]}"' in text) if installer.endswith(".sh") else ("& $py @argsList" in text)


@pytest.mark.parametrize(("installer", "codex", "copilot"), [
    ("installer.sh", '"global" "" "codex"', '"global" "" "copilot"'),
    ("installer.sh", '"workspace" "$target_path" "codex"', '"workspace" "$target_path" "copilot"'),
    ("installer.ps1", '-Scope "global" -IntegrationKey "codex"', '-Scope "global" -IntegrationKey "copilot"'),
    ("installer.ps1", '-TargetPath $targetPath -IntegrationKey "codex"', '-TargetPath $targetPath -IntegrationKey "copilot"'),
])
def test_installers_run_the_shared_path_provider_before_copilot(installer: str, codex: str, copilot: str) -> None:
    """Copilot is pointer-eligible only through ~/.agents/skills, which Codex writes.

    The installers call the runner once per platform, so a Copilot call that ran
    first would render the full index until the next install. Pin the order.
    """
    text = (REPO_ROOT / "scripts" / installer).read_text(encoding="utf-8-sig")
    assert text.count(codex) == 1 and text.count(copilot) == 1
    assert text.index(codex) < text.index(copilot)
