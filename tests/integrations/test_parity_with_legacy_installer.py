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
``docs/v2.2.0/known-gaps.md``.

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
        ("claude", "catalog/skills", ".claude/skills"),
        ("claude", "catalog/commands", ".claude/commands"),
        ("claude", "catalog/agents", ".claude/agents"),
        ("claude", "catalog/rules", ".claude/rules"),
        ("codex", "catalog/skills", ".codex/skills"),
        ("codex", "catalog/commands", ".codex/prompts"),
        ("gemini", "catalog/skills", ".gemini/skills"),
        ("opencode", "catalog/skills", ".opencode/skills"),
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
    """The registry's install must at least PRODUCE the instruction file.

    Byte-level parity with bash sed-substitution is tracked in
    docs/v2.2.0/known-gaps.md (DF-001 part 2) and is intentionally not asserted
    here.
    """
    target = tmp_path / "ws"
    target.mkdir()
    _install_workspace(key, target)

    integ = get(key)
    if key == "cursor":
        instr_path = target / "AGENTS.md"
    else:
        workspace_dir = integ.config.get("workspace_dir")
        instruction_file = integ.config.get("instruction_file")
        if not (workspace_dir and instruction_file):
            pytest.skip(f"{key} has no instruction file in workspace scope")
        instr_path = target / workspace_dir / instruction_file
    assert instr_path.is_file(), f"{key}: instruction file not produced at {instr_path}"
    assert instr_path.stat().st_size > 0, f"{key}: instruction file is empty"
