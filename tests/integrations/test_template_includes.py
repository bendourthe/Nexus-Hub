"""Include-only shims render self-contained (v4.13.1 Phase 2).

`base-gemini-cli.md` and the `base-antigravity-*.md` shims start with
`@base-google-shared.md`. Installed verbatim, that import resolved relative to the
installed `GEMINI.md`, where no such file exists, so every shared rule (Autonomous
Operation, Writing Discipline, the user-edit rule, the attribution ban) silently never
reached those platforms. Rendering now inlines the import.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.check_base_template_parity import template_roster  # noqa: E402
from scripts.lib.integrations.base import MarkdownIntegration  # noqa: E402

TEMPLATES = REPO_ROOT / "templates" / "ai-instructions"
SHARED_MARKER = "You are operating autonomously"
_, SHIMS = template_roster(REPO_ROOT)


@pytest.mark.parametrize("shim", SHIMS, ids=lambda p: p.name)
def test_every_shim_renders_with_the_shared_rules_inlined(shim: Path) -> None:
    text = MarkdownIntegration._resolve_includes(shim)
    assert not any(line.strip().startswith("@base-") for line in text.splitlines()), shim.name
    assert text.count(SHARED_MARKER) == 1, shim.name
    # The shim's own surface content is kept after the inlined shared block.
    own = [line for line in shim.read_text(encoding="utf-8").splitlines() if line.startswith("## Surface")]
    assert all(line in text for line in own)


def test_a_substantive_template_renders_unchanged() -> None:
    path = TEMPLATES / "base-claude.md"
    assert MarkdownIntegration._resolve_includes(path) == path.read_text(encoding="utf-8")


def test_cycles_and_unknown_names_are_left_as_written(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("@b.md\nA body\n", encoding="utf-8")
    (tmp_path / "b.md").write_text("@a.md\nB body\n@missing.md\n@../escape.md\n", encoding="utf-8")
    text = MarkdownIntegration._resolve_includes(tmp_path / "a.md")
    assert text == "@a.md\nB body\n@missing.md\n@../escape.md\nA body\n"


def test_an_installed_antigravity_file_carries_the_shared_rules(tmp_path: Path, monkeypatch) -> None:
    from scripts.lib.integrations import get
    from scripts.lib.integrations.base import InstallContext
    from scripts.lib.integrations.manifest import InstallManifest

    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    (tmp_path / ".gemini").mkdir()
    ctx = InstallContext(repo_root=REPO_ROOT, target_root=tmp_path, scope="global", explicit_target=True,
                         manifest=InstallManifest(), instruction_only=True)
    get("antigravity2").install(ctx)
    text = (tmp_path / ".gemini" / "GEMINI.md").read_text(encoding="utf-8")
    assert SHARED_MARKER in text
    assert "@base-google-shared.md" not in text
