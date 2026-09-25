"""Guard the wheel layout against duplicate package fixture entries."""

import tomllib
from pathlib import Path


def test_package_fixtures_are_not_force_included_twice() -> None:
    project_root = Path(__file__).resolve().parents[1]
    config = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))
    wheel = config["tool"]["hatch"]["build"]["targets"]["wheel"]

    assert wheel["packages"] == ["src/nexus_code_search"]
    assert (project_root / "src/nexus_code_search/eval/fixtures/c_app/fixtures.yaml").is_file()
    assert "src/nexus_code_search/eval/fixtures" not in wheel.get("force-include", {})


def test_benchmark_corpus_is_included_outside_the_package_source() -> None:
    project_root = Path(__file__).resolve().parents[1]
    config = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))
    wheel = config["tool"]["hatch"]["build"]["targets"]["wheel"]

    assert (project_root / "tests/fixtures/benchmark/shop_api/app.py").is_file()
    assert wheel.get("force-include", {}).get("tests/fixtures/benchmark") == (
        "nexus_code_search/contextmap/benchmark_corpus"
    )
