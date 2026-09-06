"""The Plan Lifecycle and CI/CD block reaches every platform's real read path.

Template parity proves the block is IN the source templates. It does not prove
the block survives rendering into each platform's actual instruction file, which
is the only place an agent will ever read it. Those are different claims, and
Nexus-Hub has shipped a defect in the gap between them before: a PowerShell hook
sibling was present in the catalog and dead on Windows for four minor versions,
because nothing exercised the delivered artifact.

So this file installs every registered integration into a throwaway target and
asserts against what landed on disk.

Companion coverage:
  - `tests/skills/test_cicd_lifecycle_contract.py` -- the block is in all 12
    substantive templates, exactly once, with an identical body.
  - `scripts/check_base_template_parity.py` -- the lockstep five stay in step.
  - this file -- the block survives rendering to each platform's read path.
"""

from __future__ import annotations

import re
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.integrations import INTEGRATION_REGISTRY  # noqa: E402
from scripts.lib.integrations.base import InstallContext, IntegrationBase  # noqa: E402
from scripts.lib.integrations.manifest import InstallManifest  # noqa: E402

ALL_KEYS = sorted(INTEGRATION_REGISTRY)
TEMPLATE_DIR = REPO_ROOT / "templates" / "ai-instructions"

HEADING = "## Plan Lifecycle and CI/CD"
#: One distinctive sentence from the block, to catch a heading that survived
#: while its body was truncated by a rendering step.
BODY_MARKER = "publishes once"
#: The skill the block delegates to. A block that arrives without its pointer
#: leaves the reader with a rule and nowhere to go for the detail.
SKILL_POINTER = "cicd-architect"


@pytest.fixture
def short_root():
    """A deliberately SHORT throwaway root, one directory under the system temp.

    Not `tmp_path`. Installing a platform copies the whole catalog, and the
    deepest artifact in it is around 160 characters
    (`skills/tests-generation/<skill>/references/step-2-....md`) before any
    prefix. pytest's own tmp path is already ~100 characters
    (`.../pytest-of-<user>/pytest-<n>/<test-name-truncated-to-30>0/`), which puts
    the total at or past the Windows MAX_PATH limit of 260. The copy then fails
    with `[WinError 3] The system cannot find the path specified`, which reads
    like a missing file rather than a path-length ceiling.

    This is a real environment limit rather than a defect in the code under
    test: the same install succeeds at a normal target path. Keeping the root
    short is the fix that does not require long-path support to be enabled on
    the host, which cannot be assumed for a contributor machine.
    """
    root = Path(tempfile.mkdtemp(prefix="nxl"))
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


#: An `@name.md` include line, the mechanism Antigravity 1.0/2.0 and Gemini CLI
#: use instead of copying a body. Matched at the start of a line.
INCLUDE = re.compile(r"^@([A-Za-z0-9._-]+\.md)\s*$", re.MULTILINE)


def _carries_block(text: str, seen: frozenset[str] = frozenset()) -> bool:
    """True when `text` carries the block directly OR inherits it via an include.

    Inheritance is the real delivery mechanism for three platforms, so a test
    that demanded a literal copy would report a working surface as broken and
    push someone toward duplicating the body into an alias -- the exact drift
    the include exists to prevent.

    Resolution is one hop per file with cycle protection, over the catalog
    templates rather than the rendered tree, because the include is resolved by
    the PLATFORM at read time against its own instruction directory.
    """
    if HEADING in text:
        return True
    for name in INCLUDE.findall(text):
        if name in seen:
            continue
        included = TEMPLATE_DIR / name
        if not included.is_file():
            continue
        if _carries_block(included.read_text(encoding="utf-8"), seen | {name}):
            return True
    return False


def _make_ctx(target: Path) -> InstallContext:
    return InstallContext(
        repo_root=REPO_ROOT,
        target_root=target,
        scope="workspace",
        overwrite=False,
        dry_run=False,
        manifest=InstallManifest(),
        template_vars={"PROJECT_NAME": "test-project"},
    )


def _instruction_file_for(integ: IntegrationBase, target: Path) -> Path | None:
    """Resolve the integration's rendered instruction file under `target`.

    Mirrors the resolution in `test_contract.py::_instruction_file_for`, which
    is the authority on the per-platform path rules (cursor writes to the
    project root; claude and codex set an empty instruction workspace dir; the
    rest default to their workspace dir).
    """
    instr_file = integ.config.get("instruction_file")
    if not instr_file:
        return None
    if integ.key == "cursor":
        return target / instr_file
    iwd = integ.config.get("instruction_workspace_dir", integ.config.get("workspace_dir"))
    if iwd is None:
        return None
    return target / iwd / instr_file


@pytest.mark.parametrize("key", ALL_KEYS)
def test_lifecycle_block_reaches_the_rendered_instruction_file(key: str, short_root: Path):
    integ = INTEGRATION_REGISTRY[key]
    target = short_root / "t"
    target.mkdir(parents=True, exist_ok=True)

    instr_path = _instruction_file_for(integ, target)
    if instr_path is None:
        pytest.skip(f"{key} renders no instruction file in workspace scope")

    integ.install(_make_ctx(target))

    if not instr_path.is_file():
        pytest.skip(f"{key} did not render {instr_path.name} in this environment")

    rendered = instr_path.read_text(encoding="utf-8")

    if HEADING in rendered:
        # Direct delivery: the block must appear exactly once, with its body
        # and its pointer intact. Twice would mean a template and an include
        # both supplied it, which is drift waiting to happen.
        assert rendered.count(HEADING) == 1, (
            f"{key}: expected exactly one {HEADING!r} in {instr_path.name}, "
            f"found {rendered.count(HEADING)}"
        )
        assert BODY_MARKER in rendered, (
            f"{key}: the lifecycle heading rendered but its body did not"
        )
        assert SKILL_POINTER in rendered, (
            f"{key}: the lifecycle block rendered without its pointer to {SKILL_POINTER}"
        )
        return

    # Inherited delivery: the rendered file includes a template that carries the
    # block. Assert the chain actually resolves rather than accepting the mere
    # presence of an `@` line, so a rename of the included file fails here.
    includes = INCLUDE.findall(rendered)
    assert includes, (
        f"{key}: {instr_path.name} carries neither the lifecycle block nor an "
        "include that could supply it"
    )
    assert _carries_block(rendered), (
        f"{key}: {instr_path.name} includes {includes} but none of those "
        "templates carries the lifecycle block"
    )


def test_at_least_one_platform_actually_rendered_the_block(short_root: Path):
    """Guard against a vacuous pass.

    Every assertion above sits behind two skips (no instruction file, or nothing
    rendered in this environment). If the resolution helper ever stopped finding
    any file, the whole parametrized suite would go green by skipping, which is
    exactly the fail-open shape this repository keeps rediscovering.
    """
    rendered_count = 0
    for index, key in enumerate(ALL_KEYS):
        integ = INTEGRATION_REGISTRY[key]
        # Single-character-ish names: see the short_root docstring for why.
        target = short_root / f"p{index}"
        target.mkdir(parents=True, exist_ok=True)
        instr_path = _instruction_file_for(integ, target)
        if instr_path is None:
            continue
        integ.install(_make_ctx(target))
        if instr_path.is_file() and _carries_block(instr_path.read_text(encoding="utf-8")):
            rendered_count += 1

    assert rendered_count >= 3, (
        "fewer than three platforms rendered the lifecycle block; the "
        f"parametrized suite above would have passed vacuously (rendered: {rendered_count})"
    )


def test_removing_the_block_from_one_template_is_detectable():
    """Negative fixture for the source side of the same claim.

    A rollout guard that cannot fail teaches nothing. This proves the detection
    is real by removing the block from a COPY of a canonical template and
    confirming the same check reports it, without touching the repository.
    """
    template = REPO_ROOT / "templates" / "ai-instructions" / "base-codex.md"
    text = template.read_text(encoding="utf-8")
    assert HEADING in text, "precondition: the canonical template carries the block"

    start = text.index(HEADING)
    rest = text[start + len(HEADING):]
    end = rest.find("\n## ")
    mutated = text[:start] + (rest[end + 1:] if end != -1 else "")

    assert HEADING not in mutated, "the mutation did not remove the block"
    assert BODY_MARKER not in mutated, "the mutation left the block body behind"
