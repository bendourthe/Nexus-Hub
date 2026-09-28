"""Keep pip cache inputs aligned with the packages each CI job installs."""

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parents[2]
CI = ROOT / ".github" / "workflows" / "ci.yml"
LOCK = "scripts/ci/requirements-py311.txt"


@pytest.mark.parametrize(
    ("job_name", "manifest", "step_name"),
    (
        ("guide-render", "scripts/ci/requirements-guide-render.in", "Install guide render test dependencies"),
        ("tests-windows", "scripts/ci/requirements-windows.in", "Install test dependencies"),
    ),
)
def test_scoped_pip_cache_uses_the_installed_manifest(
    job_name: str, manifest: str, step_name: str
) -> None:
    workflow = yaml.safe_load(CI.read_text(encoding="utf-8"))
    steps = workflow["jobs"][job_name]["steps"]
    setup = next(step for step in steps if step.get("uses", "").startswith("actions/setup-python@"))
    inputs = setup["with"]["cache-dependency-path"].splitlines()
    assert inputs == [manifest, LOCK]
    assert (ROOT / manifest).is_file()
    install = next(step for step in steps if step.get("name") == step_name)
    assert install["run"] == f"python -m pip install -c {LOCK} -r {manifest}"
