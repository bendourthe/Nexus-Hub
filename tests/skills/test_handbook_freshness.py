"""Exercise read-only freshness, source-map failures and release blocking."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "catalog/skills/documentation/technical-documentation/scripts/check_handbooks.py"
)
spec = importlib.util.spec_from_file_location("check_handbooks", SCRIPT)
assert spec and spec.loader
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2) if isinstance(value, dict) else value,
        encoding="utf-8",
    )


def receipt(root, entry):
    """Seed explicit synthetic evidence to test invalidation, not authoring quality."""
    evidence = "docs/handbooks/test-review.txt"
    write(root / evidence, "synthetic verifier receipt fixture")
    snapshot = checker.snapshot(root, entry)
    checks = {
        kind: {
            "status": "pass",
            "evidence": evidence,
            "evidence_sha256": checker.digest(root / evidence),
        }
        for kind in ("build", "content", "rendered")
    }
    checks["rendered"].update(
        browser="synthetic-test-browser", output_sha256=snapshot["output_sha256"]
    )
    write(root / entry["evidence"], {"snapshot": snapshot, "checks": checks})


@pytest.fixture
def project(tmp_path):
    entries = []
    for name, folder in (("overview", "html"), ("topic", "topics/runtime")):
        source = f"docs/handbooks/markdown/{name}.md"
        output = f"docs/handbooks/{folder}/{name}.html"
        write(tmp_path / source, f"# {name}\nThe retry limit is 2.")
        write(
            tmp_path / output,
            f"<main data-dv-page id='{name}'>The retry limit is 2.<button data-dv-open></button><button data-dv-open></button></main><div data-dv-deck><section data-dv-slide>Retry 2</section></div>",
        )
        entry = {
            "id": name,
            "output": output,
            "inputs": [source, "config.json", "native.py"],
            "code_inputs": ["config.json"],
            "builder": {"identity": "native.py", "inputs": ["native.py"]},
            "presentation": True,
            "evidence": f"docs/handbooks/{name}.evidence.json",
        }
        entries.append(entry)
    write(tmp_path / "config.json", {"retries": 2})
    write(tmp_path / "native.py", "print('native generator')")
    write(
        tmp_path / "docs/handbooks/handbooks.json",
        {"schema_version": 1, "handbooks": entries},
    )
    for entry in entries:
        receipt(tmp_path, entry)
    return tmp_path, entries


def test_unchanged_checks_are_read_only_and_cover_both_layouts(project):
    root, _entries = project
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    first = checker.check(root)
    second = checker.check(root)
    assert first == second and first["status"] == "pass"
    assert {row["id"] for row in first["documents"]} == {"overview", "topic"}
    assert before == {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}


@pytest.mark.parametrize(
    "path,action",
    [
        ("config.json", "edit"),
        ("native.py", "edit"),
        ("docs/handbooks/markdown/overview.md", "edit"),
        ("docs/handbooks/html/overview.html", "edit"),
        ("docs/handbooks/html/overview.html", "remove"),
        ("docs/handbooks/markdown/overview.md", "remove"),
        ("docs/handbooks/overview.evidence.json", "remove"),
        ("docs/handbooks/test-review.txt", "edit"),
    ],
)
def test_changed_or_missing_dependency_blocks_without_replacing_original(
    project, path, action
):
    root, _ = project
    target = root / path
    if action == "remove":
        target.unlink()
    else:
        target.write_text("changed", encoding="utf-8")
    existing = {p: p.read_bytes() for p in root.rglob("*.html")}
    assert checker.check(root)["status"] == "incomplete"
    assert existing == {p: p.read_bytes() for p in root.rglob("*.html")}


def test_inventory_cannot_claim_verification(project):
    root, entries = project
    (root / entries[0]["evidence"]).unlink()
    result = checker.check(root, inventory=True)
    assert result["status"] == "inventory-only"
    assert all(
        row["status"] == "inventoried-not-verified" for row in result["documents"]
    )


def test_narrow_scope_is_visible_and_does_not_qualify_all_outputs(project):
    root, entries = project
    (root / entries[1]["output"]).unlink()
    narrow = checker.check(root, scope={"overview"})
    assert narrow["status"] == "pass" and narrow["scope"] == ["overview"]
    assert checker.check(root)["status"] == "incomplete"
    assert checker.check(root, scope={"unknown"})["status"] == "incomplete"


def test_unmapped_legacy_html_is_not_a_no_op(project):
    root, _ = project
    write(root / "docs/handbooks/legacy.html", "<p>Original authored content</p>")
    result = checker.check(root)
    assert "unmapped HTML" in str(result["errors"])
    assert (
        root / "docs/handbooks/legacy.html"
    ).read_text() == "<p>Original authored content</p>"


@pytest.mark.parametrize(
    "name", ["../escape", "/absolute", "C:/escape", "a\\b", "a//b", "./a"]
)
def test_source_paths_are_unambiguous(tmp_path, name):
    with pytest.raises(ValueError):
        checker.local(tmp_path, name)


def test_missing_tree_and_empty_map_require_bootstrap(tmp_path):
    assert checker.check(tmp_path)["status"] == "incomplete"
    write(
        tmp_path / "docs/handbooks/handbooks.json",
        {"schema_version": 1, "handbooks": []},
    )
    assert checker.check(tmp_path)["status"] == "incomplete"


def test_missing_rendered_proof_cannot_be_waived_by_known_gap(project):
    root, entries = project
    p = root / entries[0]["evidence"]
    evidence = json.loads(p.read_text())
    evidence["checks"]["rendered"] = {"status": "unavailable", "known_gap": "accepted"}
    write(p, evidence)
    assert checker.check(root)["status"] == "incomplete"


def test_native_generator_failure_leaves_stale_output_blocked(project):
    root, _ = project
    write(root / "native.py", "raise SystemExit(9)")
    before = (root / "docs/handbooks/html/overview.html").read_bytes()
    assert (
        subprocess.run(
            [sys.executable, str(root / "native.py")], check=False
        ).returncode
        == 9
    )
    assert checker.check(root)["status"] == "incomplete"
    assert (root / "docs/handbooks/html/overview.html").read_bytes() == before


def test_release_pre_version_gate_blocks_before_mutation(project):
    root, _ = project
    destination = root / SCRIPT.relative_to(ROOT)
    write(destination, SCRIPT.read_text())
    write(root / "VERSION", "4.9.0")
    write(root / "config.json", {"retries": 3})
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/check_release_preconditions.py"),
            "--root",
            str(root),
            "--pre-version",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1 and "stale" in result.stdout
    assert (root / "VERSION").read_text() == "4.9.0"


def test_opt_out_requires_both_declared_reason_and_absent_deck(project):
    root, entries = project
    entry = entries[0]
    entry.update(presentation=False, opt_out_reason="Explicit project instruction")
    write(
        root / "docs/handbooks/handbooks.json",
        {"schema_version": 1, "handbooks": entries},
    )
    receipt(root, entry)
    assert checker.check(root)["status"] == "incomplete"
    write(root / entry["output"], "<main data-dv-page>Complete reading page</main>")
    receipt(root, entry)
    assert checker.check(root)["documents"][0]["status"] == "verified-opt-out"
    del entry["opt_out_reason"]
    write(
        root / "docs/handbooks/handbooks.json",
        {"schema_version": 1, "handbooks": entries},
    )
    assert checker.check(root)["status"] == "incomplete"


def test_manifest_cannot_hide_duplicate_or_excluded_output(project):
    root, entries = project
    write(
        root / "docs/handbooks/handbooks.json",
        {"schema_version": 1, "handbooks": entries + [entries[0]]},
    )
    assert checker.check(root)["status"] == "incomplete"
    write(
        root / "docs/handbooks/handbooks.json",
        {
            "schema_version": 1,
            "handbooks": entries,
            "excluded": {entries[0]["output"]: "hide"},
        },
    )
    assert checker.check(root)["status"] == "incomplete"


def test_changed_version_dependency_only_invalidates_its_document(project):
    root, entries = project
    write(root / "VERSION", "4.9.0")
    entries[0]["inputs"].append("VERSION")
    write(
        root / "docs/handbooks/handbooks.json",
        {"schema_version": 1, "handbooks": entries},
    )
    receipt(root, entries[0])
    before = (root / entries[1]["output"]).read_bytes()
    assert checker.check(root)["status"] == "pass"
    write(root / "VERSION", "4.9.1")
    result = checker.check(root)
    assert [row["status"] for row in result["documents"]] == ["incomplete", "verified"]
    assert (root / entries[1]["output"]).read_bytes() == before


def test_changed_integrated_candidate_is_rechecked_without_unrelated_output_churn(
    project,
):
    root, _entries = project

    def git(*args):
        return subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
        )

    git("init", "-q")
    git("config", "user.name", "Fixture")
    git("config", "user.email", "fixture@example.invalid")
    git("add", ".")
    git("commit", "-qm", "initial fixture")
    first = checker.check(root)
    write(root / "unrelated.txt", "unrelated merge content")
    git("add", ".")
    git("commit", "-qm", "unrelated candidate")
    second = checker.check(root)
    assert first["candidate"]["revision"] != second["candidate"]["revision"]
    assert second["status"] == "pass"
    write(root / "config.json", {"retries": 4})
    assert checker.check(root)["status"] == "incomplete"
    assert checker.check(root)["candidate"]["working_tree"] == "uncommitted"


def test_native_refresh_updates_both_views_and_retains_snapshot_inputs(project):
    import shutil

    from playwright.sync_api import sync_playwright

    root, entries = project
    entry = entries[0]
    native = """import json
from pathlib import Path
root = Path(__file__).parent
count = json.loads((root / "config.json").read_text())["retries"]
text = f"The retry limit is {count}."
(root / "docs/handbooks/markdown/overview.md").write_text("# Retry policy\\n\\n" + text)
html = f"<main data-dv-page><h1 id='policy'>Retry policy</h1><p>{text}</p><button data-dv-open>Presentation Mode</button><button data-dv-open>Presentation Mode</button></main><div data-dv-deck hidden><section data-dv-slide data-theme='dark'><h2>Retry policy</h2><p>{text}</p><button id='exit'>Exit</button></section></div>"
html += "<script>const deck=document.querySelector('[data-dv-deck]');document.querySelectorAll('[data-dv-open]').forEach(b=>b.onclick=()=>deck.hidden=false);document.querySelector('#exit').onclick=()=>deck.hidden=true;</script>"
(root / "docs/handbooks/html/overview.html").write_text(html)
"""
    write(root / "native.py", native)

    def build():
        subprocess.run([sys.executable, str(root / "native.py")], check=True)

    build()
    for item in entries:
        receipt(root, item)
    assert checker.check(root)["status"] == "pass"
    write(root / "config.json", {"retries": 7})
    assert checker.check(root)["status"] == "incomplete"
    build()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.goto((root / entry["output"]).as_uri())
        assert page.locator("[data-dv-page] p").inner_text() == "The retry limit is 7."
        page.locator("[data-dv-open]").first.click()
        assert page.locator("[data-dv-deck]").is_visible()
        assert page.locator("[data-dv-slide] p").inner_text() == "The retry limit is 7."
        assert page.locator("[data-dv-slide]").get_attribute("data-theme") == "dark"
        page.locator("#exit").click()
        assert page.locator("#policy").is_visible()
        browser.close()
    receipt(root, entry)
    assert checker.check(root, scope={"overview"})["status"] == "pass"
    before = (root / entry["output"]).read_bytes()
    build()
    assert (root / entry["output"]).read_bytes() == before
    snapshot_root = root / "docs/archives/v4/v4.9/handbooks"
    rebuild = snapshot_root / "rebuild-root"
    shutil.copytree(root / "docs/handbooks", rebuild / "docs/handbooks")
    for item in entries:
        for name in item["inputs"]:
            destination = rebuild / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root / name, destination)
    assert (rebuild / "docs/handbooks/handbooks.json").is_file()
    assert (rebuild / "docs/handbooks/markdown/overview.md").is_file()
    assert (rebuild / "docs/handbooks/html/overview.html").read_bytes() == before
    assert (root / entry["output"]).is_file()
    assert (rebuild / "native.py").read_bytes() == (root / "native.py").read_bytes()
    assert checker.check(rebuild, scope={"overview"})["status"] == "pass"
