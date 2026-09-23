"""Keep the local test prerequisite aligned with extension projects."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EDITABLE_EXTRA = re.compile(r'-e "extensions/([^/\"]+)/\[dev\]"')


def test_make_dev_installs_every_extension_development_extra() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    recipe = makefile.split("\ndev: ", 1)[1].split("\ntest: ", 1)[0]
    extension_names = {path.parent.name for path in (ROOT / "extensions").glob("*/pyproject.toml")}

    assert "python -m pip install" in recipe
    assert set(EDITABLE_EXTRA.findall(recipe)) == extension_names
    assert set(EDITABLE_EXTRA.findall(readme)) == extension_names
    assert "after make dev" in makefile
