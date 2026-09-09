"""Conditional intake routing and real retained output agreement across profiles."""

import importlib
import io
import itertools
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "catalog/skills/specialized-domains/document-to-interactive-html"
sys.path.insert(0, str(BUNDLE / "scripts"))
intake = importlib.import_module("resolve_presentation")
dual = importlib.import_module("dual_view")
scorer = importlib.import_module("visual_qa_score")


def axes(result):
    return [question["axis"] for question in result["questions"]]


def test_conditional_interview_preserves_answers_and_cancels_after_no():
    initial = intake.resolve({})
    assert initial["status"] == "pending" and axes(initial) == ["presentation"]
    yes = intake.resolve(
        {}, session={"presentation": "yes", "style": "editorial", "images": "none"}
    )
    assert axes(yes) == ["presentation_theme", "presentation_depth"]
    themed = intake.resolve({"presentation_theme": "light"}, session=yes["values"])
    assert axes(themed) == ["presentation_depth"]
    depth = intake.resolve({"presentation_depth": "deep-dive"}, session=yes["values"])
    assert axes(depth) == ["presentation_theme"]
    no = intake.resolve({"presentation": "no"}, session=themed["values"])
    assert not axes(no) and no["presentation"] == {"enabled": False}
    assert no["values"]["style"] == "editorial"


@pytest.mark.parametrize(
    "explicit,enabled",
    [
        ({"nav": "slides"}, True),
        ({"nav": "scroll"}, True),
        (
            {
                "presentation": "no",
                "nav": "slides",
                "presentation_theme": "dark",
                "presentation_depth": "deep-dive",
            },
            False,
        ),
        ({"presentation_theme": "light"}, True),
        ({"presentation_depth": "concise"}, True),
    ],
)
def test_legacy_aliases_and_no_precedence(explicit, enabled):
    result = intake.resolve(explicit, interactive=False)
    assert result["status"] == "resolved"
    assert result["presentation"]["enabled"] is enabled


def test_new_defaults_saved_policy_and_explicit_precedence():
    assert intake.resolve({}, interactive=False)["presentation"] == {
        "enabled": True,
        "theme": "mixed",
        "depth": "balanced",
    }
    project = {
        "presentation": "no",
        "presentation_theme": "light",
        "presentation_depth": "concise",
        "brand": "tide",
        "layout": "portrait",
        "motion": "restrained",
        "slide_budget": 6,
    }
    result = intake.resolve(
        {"presentation": "yes"},
        session={"presentation_depth": "deep-dive"},
        project=project,
        interactive=False,
    )
    assert result["presentation"] == {
        "enabled": True,
        "theme": "light",
        "depth": "deep-dive",
    }
    assert result["provenance"]["presentation"] == "explicit"
    assert result["provenance"]["presentation_depth"] == "session"
    assert result["provenance"]["brand"] == "project"
    assert result["values"]["slide_budget"] == 6
    assert (
        intake.resolve({}, project=project, interactive=False)["presentation"][
            "enabled"
        ]
        is False
    )


def test_complete_source_and_independent_verbosity():
    result = intake.resolve({"complete_source": True}, interactive=False)
    assert result["values"]["verbosity"] == "comprehensive"
    assert result["presentation"]["depth"] == "deep-dive"
    result = intake.resolve(
        {"verbosity": "distilled", "presentation_depth": "deep-dive"}, interactive=False
    )
    assert (
        result["values"]["verbosity"] == "distilled"
        and result["presentation"]["depth"] == "deep-dive"
    )
    assert (
        intake.resolve(
            {"complete_source": True, "presentation_depth": "concise"},
            interactive=False,
        )["status"]
        == "conflict"
    )


def test_invalid_options_leave_pending_axes_or_documented_defaults():
    result = intake.resolve({"presentation": "maybe", "nav": "deck"})
    assert axes(result) == ["presentation"] and len(result["notes"]) == 2
    result = intake.resolve({"presentation_theme": "rainbow"}, interactive=False)
    assert result["presentation"]["theme"] == "mixed" and result["notes"]


def test_saved_theme_assignment_does_not_reroll_existing_ids():
    before = intake.save_themes(["one", "two", "three"], "mixed", "frozen")
    assert set(before.values()) == {"light", "dark"}
    after = intake.save_themes(
        ["one", "new", "two", "three"], "mixed", "different", before
    )
    assert all(after[key] == value for key, value in before.items())
    with pytest.raises(ValueError, match="Saved mixed"):
        intake.save_themes(
            ["one", "two"], "mixed", "frozen", {"one": "light", "two": "light"}
        )


@pytest.fixture
def project(tmp_path):
    for source in (ROOT / "tests/fixtures/interactive-handbooks").iterdir():
        if source.is_file():
            shutil.copy2(source, tmp_path / source.name)
    return tmp_path


@pytest.mark.parametrize(
    "theme,depth",
    list(
        itertools.product(
            ("light", "dark", "mixed"), ("concise", "balanced", "deep-dive")
        )
    ),
)
def test_nine_profiles_agree_at_intake_model_dom_and_scorer(project, theme, depth):
    model = json.loads((project / "model.json").read_text(encoding="utf-8"))
    settings = intake.resolve(
        {
            "presentation_theme": theme,
            "presentation_depth": depth,
            "verbosity": "comprehensive",
        },
        interactive=False,
    )
    model["presentation"].update(settings["presentation"])
    if depth == "concise":
        model["presentation"]["slides"].pop()
        model["presentation"]["omissions"] = {
            "appendix": "Directory retained in reading view"
        }
    elif depth == "balanced":
        model["presentation"]["slides"][2]["unit_ids"] = {
            "acquisition": ["acquisition-text"]
        }
        model["presentation"]["omissions"] = {
            "acquisition/acquisition-observations": "Same figure explained in analysis"
        }
    ids = [slide["id"] for slide in model["presentation"]["slides"]]
    themes = intake.save_themes(ids, theme, "fixed")
    model["presentation"]["theme_sequence"] = [themes[key] for key in ids]
    (project / "model.json").write_text(json.dumps(model), encoding="utf-8")
    dual.assemble(project / "model.json", project / "handbook.html")
    source = (project / "handbook.html").read_text(encoding="utf-8")
    assert scorer.check_dual_view_contract(source)["status"] == "pass"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto((project / "handbook.html").as_uri())
        assert page.locator(
            '[data-dv-page] [data-theme="dark"] figure > svg text'
        ).evaluate_all(
            'nodes => nodes.length > 0 && nodes.every(node => getComputedStyle(node).fill !== "rgb(0, 0, 0)")'
        )
        assert page.locator("[data-dv-page] [data-dv-section]").count() == 6
        assert (
            page.get_by_role("button", name="Presentation Mode", exact=True).count()
            == 2
        )
        page.get_by_role("button", name="Presentation Mode", exact=True).first.click()
        for index, expected in enumerate(model["presentation"]["theme_sequence"]):
            page.evaluate("(index)=>NexusDualView.open(index)", index)
            page.locator("[data-dv-replay]").click()
            assert (
                page.locator("[data-dv-slide]:not([hidden])").get_attribute(
                    "data-theme"
                )
                == expected
            )
        page.locator("[data-dv-exit]").click()
        page.get_by_role("button", name="Presentation Mode", exact=True).last.click()
        assert page.locator("[data-dv-count]").inner_text().startswith("1 /")
        browser.close()
    dual.assemble(project / "model.json", project / "handbook.html", check=True)
    assert (project / "handbook.html").read_text(encoding="utf-8") == source
    assert (
        scorer.check_dual_view_contract(
            source.replace("data-dv-slide=", "data-broken-slide=", 1)
        )["severity"]
        == "high"
    )


def test_page_only_result_has_passing_absence_guard(project):
    model = json.loads((project / "model.json").read_text(encoding="utf-8"))
    model["presentation"] = intake.resolve(
        {"presentation": "no", "nav": "slides"}, interactive=False
    )["presentation"]
    (project / "model.json").write_text(json.dumps(model), encoding="utf-8")
    dual.assemble(project / "model.json", project / "handbook.html")
    source = (project / "handbook.html").read_text(encoding="utf-8")
    finding = scorer.check_dual_view_contract(source)
    assert finding["status"] == "pass" and "N/A" in str(finding)
    assert (
        scorer.check_dual_view_contract(
            source + "<button data-dv-open>Presentation Mode</button>"
        )["severity"]
        == "high"
    )


def test_resolver_cli_returns_pending_questions_without_source_access(project):
    request = project / "intake.json"
    request.write_text(
        json.dumps({"explicit": {"presentation": "yes", "presentation_theme": "dark"}}),
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            str(BUNDLE / "scripts/resolve_presentation.py"),
            "--input",
            str(request),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert axes(json.loads(result.stdout)) == ["presentation_depth"]


def test_command_and_direct_skill_delegate_to_same_intake_owner():
    command = (ROOT / "catalog/commands/presentify.md").read_text(encoding="utf-8")
    skill = (BUNDLE / "SKILL.md").read_text(encoding="utf-8")
    for source in (command, skill):
        assert "references/presentation-intake.md" in source
        assert "scripts/resolve_presentation.py" in source
        assert "NO runtime scroll / slides toggle" not in source
        assert "**Slide deck**" not in source


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {"explicit": []},
        {"explicit": {"complete_source": "yes"}},
        {"explicit": {"complete_source": True, "verbosity": "distilled"}},
    ],
)
def test_cli_rejects_malformed_or_conflicting_intake(project, payload, capsys):
    path = project / "bad-intake.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert intake.main(["--input", str(path), "--non-interactive"]) == 2
    captured = capsys.readouterr()
    assert "Error" in captured.err or "conflict" in captured.out


def test_cli_defaults_and_lower_priority_complete_source(project, capsys):
    path = project / "intake.json"
    path.write_text("{}", encoding="utf-8")
    assert intake.main(["--input", str(path), "--non-interactive"]) == 0
    assert json.loads(capsys.readouterr().out)["presentation"]["enabled"] is True
    result = intake.resolve(
        {"presentation_depth": "concise"},
        project={"complete_source": True},
        interactive=False,
    )
    assert result["presentation"]["depth"] == "concise"
    assert result["provenance"]["presentation_depth"] == "explicit"


def test_scorer_fails_closed_on_malformed_records_and_fake_mixed_policy(project):
    assert (
        scorer.check_dual_view_contract("<main data-dv-page></main>")["severity"]
        == "high"
    )
    model = json.loads((project / "model.json").read_text(encoding="utf-8"))
    dual.assemble(project / "model.json", project / "handbook.html")
    source = (project / "handbook.html").read_text(encoding="utf-8")
    assert (
        scorer.check_dual_view_contract(source.replace('"dark"', '"light"'))["severity"]
        == "high"
    )
    report = scorer.score_html(source.replace("data-dv-slide=", "data-lost-slide=", 1))
    assert any(
        finding["criterion"] == "dual-view" and finding.get("severity") == "high"
        for finding in report["findings"]
    )
    model["presentation"] = {"enabled": False}
    model["sections"][0]["blocks"][0]["text"] = (
        "Example API identifier: window.NexusDualView"
    )
    (project / "model.json").write_text(json.dumps(model), encoding="utf-8")
    dual.assemble(project / "model.json", project / "handbook.html")
    assert (
        scorer.check_dual_view_contract(
            (project / "handbook.html").read_text(encoding="utf-8")
        )["status"]
        == "pass"
    )


def test_cross_format_design_and_optional_native_export_handoffs():
    for relative in (
        "specialized-domains/pptx-generation",
        "specialized-domains/docx-generation",
        "specialized-domains/pdf-document-generation",
        "specialized-domains/generative-art",
        "developer-experience/html-output-conventions",
    ):
        source = (ROOT / "catalog/skills" / relative / "SKILL.md").read_text(
            encoding="utf-8"
        )
        assert "hallmark-design" in source and "anti-slop-editing" in source
    pptx = (
        ROOT
        / "catalog/skills/specialized-domains/pptx-generation/references/retained-handbook-export.md"
    ).read_text(encoding="utf-8")
    for contract in (
        "headerless",
        "0.2 seconds",
        "timed playback",
        "package relationships",
        "source/output map",
        "Do not delete",
    ):
        assert contract in pptx


@pytest.mark.parametrize(
    "layout,expected_width", [("full", 1366), ("standard", 1180), ("portrait", 828)]
)
def test_retained_reading_canvas_does_not_change_presentation_canvas(
    project, layout, expected_width
):
    model = json.loads((project / "model.json").read_text(encoding="utf-8"))
    model["design"]["layout"] = layout
    (project / "model.json").write_text(json.dumps(model), encoding="utf-8")
    dual.assemble(project / "model.json", project / "handbook.html")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1366, "height": 768})
        page.goto((project / "handbook.html").as_uri())
        assert page.locator("[data-dv-page]").bounding_box()["width"] == pytest.approx(
            expected_width
        )
        page.evaluate("NexusDualView.open(2)")
        assert page.locator("[data-dv-deck]").bounding_box()["width"] == 1366
        figure = page.locator("[data-dv-slide]:not([hidden]) [data-dv-figure]")
        before = figure.locator("svg").bounding_box()["width"]
        figure.locator("[data-dv-zoom]").fill("2")
        assert figure.locator("svg").bounding_box()["width"] > before * 1.8
        browser.close()


def test_retained_cli_rejects_unretained_layout_override(project):
    result = subprocess.run(
        [
            sys.executable,
            str(BUNDLE / "scripts/build_presentation.py"),
            str(project / "model.json"),
            "-o",
            str(project / "handbook.html"),
            "--layout",
            "portrait",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2 and "design.layout" in result.stderr
    assert not (project / "handbook.html").exists()


def test_both_directed_connectors_paint_and_theme_variant_stays_legible(project):
    dual.assemble(project / "model.json", project / "handbook.html")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1366, "height": 768})
        page.goto((project / "handbook.html").as_uri())
        assert (
            page.locator("header > svg text").evaluate(
                "node => getComputedStyle(node).fill"
            )
            == "rgb(21, 40, 60)"
        )
        page.locator("#review").scroll_into_view_if_needed()
        svg = page.locator("#review figure > svg")
        assert svg.locator("path[marker-end]").count() == 2
        points = svg.evaluate(
            "svg => [180,400].map(x => {const point=new DOMPoint(x,90).matrixTransform(svg.getScreenCTM());return {x:Math.round(point.x),y:Math.round(point.y)};})"
        )
        screenshot = Image.open(io.BytesIO(page.screenshot())).convert("RGB")
        background = (20, 34, 53)
        assert all(
            screenshot.getpixel((point["x"], point["y"])) != background
            for point in points
        )
        svg.locator("path[marker-end]").evaluate_all(
            'nodes => nodes.forEach(node => node.style.stroke="none")'
        )
        broken = Image.open(io.BytesIO(page.screenshot())).convert("RGB")
        assert all(
            broken.getpixel((point["x"], point["y"])) == background for point in points
        )
        browser.close()
