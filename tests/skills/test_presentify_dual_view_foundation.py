"""Exercise the retained neutral specimen without pretending the runtime exists."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "interactive-handbooks"
SPEC = importlib.util.spec_from_file_location(
    "handbook_fixture", FIXTURE / "build_fixture.py"
)
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def test_real_fixture_build_is_repeatable(tmp_path):
    outputs = [tmp_path / name for name in ("first.html", "second.html")]
    for output in outputs:
        subprocess.run(
            [
                sys.executable,
                str(FIXTURE / "build_fixture.py"),
                str(FIXTURE / "model.json"),
                str(output),
            ],
            check=True,
        )
    assert outputs[0].read_bytes() == outputs[1].read_bytes()
    direct = tmp_path / "direct.html"
    builder.build(FIXTURE / "model.json", direct)
    assert direct.read_bytes() == outputs[0].read_bytes()
    page = outputs[0].read_text(encoding="utf-8")
    inventory = json.loads((FIXTURE / "inventory.json").read_text(encoding="utf-8"))
    assert page.count("<h1>") == 1
    assert "runtime and production assembler pending" in page
    for key in inventory["section_ids"]:
        assert f'id="{key}"' in page


@pytest.mark.parametrize(
    "mutation, key", [("duplicate", "sections.id"), ("missing", "unknown source key")]
)
def test_bad_source_metadata_fails_before_write(tmp_path, mutation, key):
    model = json.loads((FIXTURE / "model.json").read_text(encoding="utf-8"))
    if mutation == "duplicate":
        model["sections"][1]["id"] = model["sections"][0]["id"]
    else:
        model["presentation"]["slides"][0]["source_ids"] = ["missing-unit"]
    source, output = tmp_path / "model.json", tmp_path / "output.html"
    source.write_text(json.dumps(model), encoding="utf-8")
    with pytest.raises(ValueError, match=key):
        builder.build(source, output)
    assert not output.exists()


def test_conflicting_output_preserves_existing_bytes(tmp_path):
    output = tmp_path / "owned.html"
    output.write_text("user content", encoding="utf-8")
    with pytest.raises(ValueError, match="conflicting path"):
        builder.build(FIXTURE / "model.json", output)
    assert output.read_text(encoding="utf-8") == "user content"


def test_fixture_inventory_is_independent_and_complete():
    model = json.loads((FIXTURE / "model.json").read_text(encoding="utf-8"))
    inventory = json.loads((FIXTURE / "inventory.json").read_text(encoding="utf-8"))
    assert [s["id"] for s in model["sections"]] == inventory["section_ids"]
    assert [s["id"] for s in model["presentation"]["slides"]] == inventory["slide_ids"]
    assert sorted(model["figures"]) == sorted(inventory["figure_ids"])
    assert len(inventory["negative_cases"]) >= 12
