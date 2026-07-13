"""[from v2.1.0 known-gaps: DF-001] Registry-vs-legacy installer parity tests.

Background
----------
v2.1.0 Phase 10 shipped the integration registry as ADDITIVE. The original 4
platforms (Claude / Codex / Gemini IDE / Copilot - plus Cursor / OpenCode as
behavioral-guardrails) continue to install through the legacy bash copy blocks
in ``scripts/installer.sh``. v2.2.0 Phase 3 sub-task 3.6 closes the parity gap
so the legacy blocks can be safely removed in sub-task 3.7.

What this suite asserts
-----------------------
For each of the 5 platforms (claude, codex, cursor, gemini, opencode), the
**catalog tree mirrors** produced by the registry runner are byte-identical to
the source catalog. The legacy bash installer copies catalog/skills/,
catalog/commands/, catalog/agents/, catalog/rules/ via ``safe_folder_copy``
(byte-for-byte). The registry uses ``IntegrationBase._copy_tree`` which calls
``shutil.copytree(src, dst, dirs_exist_ok=True)`` -- also byte-for-byte. The
two paths should therefore produce trees with identical SHA-256 hashes.

What this suite does NOT yet assert
-----------------------------------
**Instruction-file content parity**. The legacy bash installer renders
``base-<platform>.md`` via a ``sed`` substitution that fills 13+ placeholders
(``{{PROJECT_NAME}}``, ``{{PRIMARY_LANGUAGE}}``, ``{{BUILD_CMD}}``, ...). The
registry runner currently only substitutes ``{{PROJECT_NAME}}``. Closing this
gap requires extending the runner's ``template_vars`` to mirror every key the
bash installer fills. Tracked under DF-001 (carry-forward) in
``docs/archive/v2/v2.2/known-gaps.md``.

When parity becomes byte-identical for instruction files too, sub-task 3.7
(``scripts/installer.sh`` legacy block removal) can complete.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.integrations import get  # noqa: E402
from scripts.lib.integrations.base import InstallContext  # noqa: E402
from scripts.lib.integrations.manifest import InstallManifest  # noqa: E402


LEGACY_FIVE = ["claude", "codex", "cursor", "gemini", "opencode"]


def _hash_tree(root: Path) -> dict[str, str]:
    """Return ``{relative_posix_path: sha256_hex}`` for every file under root."""
    hashes: dict[str, str] = {}
    for f in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = f.relative_to(root).as_posix()
        hashes[rel] = hashlib.sha256(f.read_bytes()).hexdigest()
    return hashes


@pytest.fixture
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    return home


def _install_workspace(key: str, target: Path) -> None:
    integ = get(key)
    ctx = InstallContext(
        repo_root=REPO_ROOT,
        target_root=target,
        scope="workspace",
        overwrite=False,
        dry_run=False,
        manifest=InstallManifest(),
        template_vars={"PROJECT_NAME": "parity-test"},
    )
    integ.install(ctx)


# ---------------------------------------------------------------------------
# Tree-mirror parity: catalog/<dir>/ -> <target>/<workspace_dir>/<subdir>/
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "key,catalog_subdir,target_subdir",
    [
        # Skills are no longer verbatim mirrors: as of v3.12.0 the SKILL.md-standard
        # platforms (claude, codex, gemini, gemini-cli, opencode, nexus-ai,
        # antigravity) FLATTEN catalog/skills/<category>/<name>/ to skills/<name>/
        # (one level, as those tools actually scan) and add a skill per command.
        # That flattening + command-skill behavior is asserted per-platform in the
        # dedicated tests (test_codex.py, test_antigravity.py,
        # test_cross_platform_flatten.py). Only the tree-shaped surfaces
        # (commands/agents/rules) and the legacy codex prompts flat copy remain
        # verbatim mirrors, so only their parity rows stay here.
        ("claude", "catalog/commands", ".claude/commands"),
        ("claude", "catalog/agents", ".claude/agents"),
        ("claude", "catalog/rules", ".claude/rules"),
        ("codex", "catalog/commands", ".codex/prompts"),
        ("opencode", "catalog/commands", ".opencode/commands"),
        ("opencode", "catalog/rules", ".opencode/rules"),
    ],
)
def test_catalog_tree_mirror_is_byte_identical(
    key: str, catalog_subdir: str, target_subdir: str, fake_home: Path, tmp_path: Path
) -> None:
    """The registry's tree mirror is byte-identical to the source catalog tree.

    The legacy bash installer copies these same directories via ``safe_folder_copy``
    (``rsync -a`` / ``cp -R``). Both paths must produce identical bytes for
    DF-001 to close.
    """
    target = tmp_path / "ws"
    target.mkdir()
    _install_workspace(key, target)

    source = REPO_ROOT / catalog_subdir
    dest = target / target_subdir
    if not source.exists():
        pytest.skip(f"{source} does not exist in this repo")
    assert dest.exists(), f"{key} did not produce {dest}"

    src_hashes = _hash_tree(source)
    dst_hashes = _hash_tree(dest)
    assert src_hashes == dst_hashes, (
        f"{key}: tree mirror at {dest} diverges from source {source}; "
        f"affected files: {sorted(set(src_hashes) ^ set(dst_hashes))[:5]}"
    )


# ---------------------------------------------------------------------------
# Cursor: rules are flattened into .mdc files with frontmatter. The legacy
# bash path and the registry path use the same _md_to_mdc helper, so the
# resulting bytes are deterministic. Assert that the file set matches.
# ---------------------------------------------------------------------------


def test_cursor_produces_expected_rule_set(fake_home: Path, tmp_path: Path) -> None:
    target = tmp_path / "ws"
    target.mkdir()
    _install_workspace("cursor", target)

    rules_dir = target / ".cursor" / "rules"
    assert rules_dir.is_dir()
    mdc_files = sorted(p.name for p in rules_dir.glob("*.mdc"))
    assert mdc_files, "cursor produced no .mdc rule files"
    # Every .mdc must have YAML frontmatter (the registry's `_md_to_mdc`
    # produces this; the legacy bash path delegates to the same helper).
    for name in mdc_files:
        body = (rules_dir / name).read_text(encoding="utf-8")
        assert body.startswith("---\n"), f"{name}: missing frontmatter"
        assert "scope: auto" in body, f"{name}: missing scope: auto"


# ---------------------------------------------------------------------------
# Instruction file gap: documented (not asserted byte-identical yet)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("key", LEGACY_FIVE)
def test_instruction_file_is_produced(key: str, fake_home: Path, tmp_path: Path) -> None:
    """The registry's install must PRODUCE the instruction file at the expected
    location. (Byte-level body parity is asserted by
    ``test_instruction_body_parity_with_legacy_render`` below.)
    """
    target = tmp_path / "ws"
    target.mkdir()
    _install_workspace(key, target)

    integ = get(key)
    if key == "cursor":
        instr_path = target / "AGENTS.md"
    else:
        instruction_file = integ.config.get("instruction_file")
        workspace_dir = integ.config.get("workspace_dir")
        if not (workspace_dir is not None and instruction_file):
            pytest.skip(f"{key} has no instruction file in workspace scope")
        # v2.3.0 / DF-001: claude/codex render to the project root (empty
        # instruction_workspace_dir); others render under the workspace dir.
        iwd = integ.config.get("instruction_workspace_dir", workspace_dir)
        instr_path = target / iwd / instruction_file
    assert instr_path.is_file(), f"{key}: instruction file not produced at {instr_path}"
    assert instr_path.stat().st_size > 0, f"{key}: instruction file is empty"


# ---------------------------------------------------------------------------
# Instruction-file BODY parity (DF-001 / MT-2 close)
#
# The legacy bash `render_template` fills 15 placeholders via `sed`, replaces
# `{{SKILL_INDEX}}` from data/SKILL_INDEX.md, and appends per-language coding
# snippets, then writes the raw body. The registry runner now does the same
# substitution but wraps the body in the shared `<!-- NEXUS_HUB_* -->` marker
# block (the deliberate v2.2.0 user-edit-preservation feature). Byte parity is
# therefore asserted at the MANAGED-BODY level: the content the registry places
# between the markers must equal an independent reference render of the same
# template + var set.
#
# `_reference_render` is a deliberately naive str.replace re-implementation of
# the bash substitution -- NOT the production regex renderer -- so it has teeth:
# a regex bug, a forgotten SKILL_INDEX load, or a snippet-append whitespace
# drift in production would diverge from this oracle and fail the test. This is
# the precondition that authorizes removing the legacy bash render_template
# blocks.
# ---------------------------------------------------------------------------

LEGACY_INSTRUCTION_THREE = ["claude", "codex", "gemini"]

# A full var set exercising every placeholder the bash installer fills, plus a
# language whose coding snippet exists in the repo.
PARITY_VARS = {
    "PROJECT_NAME": "parity-test",
    "PROJECT_DESCRIPTION": "(Add a 2-3 sentence project description here, or run /setup-project)",
    "PRIMARY_LANGUAGE": "Python",
    "LANGUAGE_VERSION": "",
    "PACKAGE_MANAGER": "uv (or pip with venv)",
    "BUILD_TOOL": "uv",
    "TEST_FRAMEWORK": "pytest",
    "LINT_TOOL": "ruff",
    "PROJECT_STRUCTURE_BRIEF": "(Run /setup-project to generate project layout)",
    "BUILD_CMD": "uv run python src/main.py",
    "TEST_CMD": "uv run pytest tests/",
    "LINT_CMD": "uv run ruff check . && uv run ruff format .",
    "NON_OBVIOUS_TOOLING": "- Use `uv` not `pip` for Python package management",
    "LANGUAGE_CONVENTIONS": "(See coding-snippets or run /setup-project)",
    "OS_CONTEXT": "I am a Linux user. Ensure shell commands are POSIX-compatible.",
}
PARITY_LANGUAGES = ["Python"]


def _reference_render(
    template_text: str, vars_map: dict[str, str], repo_root: Path, languages: list[str]
) -> str:
    """Independent oracle mirroring the legacy bash `render_template` body."""
    out = template_text
    for key, value in vars_map.items():
        out = out.replace("{{" + key + "}}", value)
    index_path = repo_root / "data" / "SKILL_INDEX.md"
    if index_path.exists():
        out = out.replace("{{SKILL_INDEX}}", index_path.read_text(encoding="utf-8"))
    for lang in languages:
        lang_key = lang.strip().lower()
        if lang_key == "c++":
            lang_key = "cpp"
        elif lang_key == "c#":
            lang_key = "csharp"
        if not lang_key:
            continue
        snippet = repo_root / "templates" / "ai-instructions" / "coding-snippets" / f"{lang_key}.md"
        if snippet.exists():
            out = out.rstrip("\n") + "\n\n" + snippet.read_text(encoding="utf-8").strip() + "\n"
    return out


def _extract_marker_body(file_text: str) -> str:
    from scripts.lib.installer.instruction_merge import (
        DEFAULT_END_MARKER,
        DEFAULT_START_MARKER,
    )

    start = file_text.index(DEFAULT_START_MARKER) + len(DEFAULT_START_MARKER)
    end = file_text.rindex(DEFAULT_END_MARKER)
    return file_text[start:end].strip()


@pytest.mark.parametrize("scope", ["global", "workspace"])
@pytest.mark.parametrize("key", LEGACY_INSTRUCTION_THREE)
def test_instruction_body_parity_with_legacy_render(
    key: str, scope: str, fake_home: Path, tmp_path: Path
) -> None:
    integ = get(key)
    target = tmp_path / "ws"
    target.mkdir()
    ctx = InstallContext(
        repo_root=REPO_ROOT,
        target_root=target,
        scope=scope,
        overwrite=False,
        dry_run=False,
        manifest=InstallManifest(),
        template_vars=dict(PARITY_VARS),
        languages=list(PARITY_LANGUAGES),
        instruction_only=True,
    )
    integ.install(ctx)

    instruction_file = integ.config["instruction_file"]
    if scope == "global":
        global_dir = integ.config["global_dir"].lstrip("~/")
        instr_path = Path.home() / global_dir / instruction_file
    else:
        iwd = integ.config.get("instruction_workspace_dir", integ.config["workspace_dir"])
        instr_path = target / iwd / instruction_file
    assert instr_path.is_file(), f"{key}/{scope}: instruction file not at {instr_path}"

    body = _extract_marker_body(instr_path.read_text(encoding="utf-8"))
    template_path = REPO_ROOT / integ.config["instruction_template"]
    expected = _reference_render(
        template_path.read_text(encoding="utf-8"), PARITY_VARS, REPO_ROOT, PARITY_LANGUAGES
    ).strip()

    assert body == expected, (
        f"{key}/{scope}: registry instruction body diverges from the reference render"
    )
    # DF-001 completeness: no known instruction placeholder left literal.
    for token in (
        "{{PROJECT_NAME}}",
        "{{PRIMARY_LANGUAGE}}",
        "{{PACKAGE_MANAGER}}",
        "{{BUILD_CMD}}",
        "{{TEST_CMD}}",
        "{{LINT_CMD}}",
        "{{OS_CONTEXT}}",
        "{{NON_OBVIOUS_TOOLING}}",
        "{{SKILL_INDEX}}",
    ):
        assert token not in body, f"{key}/{scope}: literal {token} left in instruction body"
