"""Retained-input safety, deterministic freshness and shared figure contracts."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "catalog/skills/specialized-domains/document-to-interactive-html"
SCRIPTS = BUNDLE / "scripts"
sys.path.insert(0, str(SCRIPTS))
dual = importlib.import_module("dual_view")
FIXTURE = ROOT / "tests/fixtures/interactive-handbooks"


@pytest.fixture
def project(tmp_path):
    for path in FIXTURE.iterdir():
        if path.is_file():
            shutil.copy2(path, tmp_path / path.name)
    return tmp_path


def read_model(project):
    return json.loads((project / "model.json").read_text(encoding="utf-8"))


def save_model(project, model):
    (project / "model.json").write_text(json.dumps(model), encoding="utf-8")


def build(project, **kwargs):
    return dual.assemble(project / "model.json", project / "handbook.html", **kwargs)


def test_cli_repeatability_read_only_check_and_source_change(project):
    command = [
        sys.executable,
        str(SCRIPTS / "build_presentation.py"),
        str(project / "model.json"),
        "-o",
        str(project / "handbook.html"),
    ]
    subprocess.run(command, check=True, capture_output=True)
    first = (project / "handbook.html").read_bytes()
    build(project)
    assert (project / "handbook.html").read_bytes() == first
    before = {
        p.name: (p.read_bytes(), p.stat().st_mtime_ns)
        for p in project.iterdir()
        if p.is_file()
    }
    subprocess.run(command + ["--check"], check=True, capture_output=True)
    assert before == {
        p.name: (p.read_bytes(), p.stat().st_mtime_ns)
        for p in project.iterdir()
        if p.is_file()
    }
    model = read_model(project)
    model["figures"]["observations"]["series"][0]["values"][0] = 42
    save_model(project, model)
    with pytest.raises(ValueError, match="stale"):
        build(project, check=True)
    assert (project / "handbook.html").read_bytes() == first
    build(project)
    assert (project / "handbook.html").read_text(encoding="utf-8").count(
        "<td>42</td>"
    ) == 4


@pytest.mark.parametrize(
    "fault, message",
    [
        ("duplicate-source", "sections.id"),
        ("missing-source", "source_ids"),
        ("budget", "slide_budget"),
        ("source-count", "source_slide_count"),
        ("empty-slides", "storyboard"),
        ("theme", "theme_sequence"),
        ("coverage", "coverage"),
        ("depth", "depth"),
        ("initial", "initial_slide"),
        ("enabled", "boolean"),
        ("unknown-figure", "figure_id"),
        ("source-type", "objects"),
    ],
)
def test_bad_models_never_replace_output(project, fault, message):
    build(project)
    before = (project / "handbook.html").read_bytes()
    model = read_model(project)
    if fault == "duplicate-source":
        model["sections"][1]["id"] = "overview"
    if fault == "missing-source":
        model["presentation"]["slides"][0]["source_ids"] = ["absent"]
    if fault == "budget":
        model["presentation"]["slide_budget"] = 5
    if fault == "source-count":
        model["presentation"]["source_slide_count"] = 5
    if fault == "empty-slides":
        model["presentation"]["slides"] = []
    if fault == "theme":
        model["presentation"]["theme_sequence"] = ["light"] * 6
    if fault == "coverage":
        model["presentation"]["slides"][-1]["source_ids"] = ["overview"]
    if fault == "depth":
        model["presentation"]["depth"] = "everything"
    if fault == "initial":
        model["presentation"]["initial_slide"] = 3
    if fault == "enabled":
        model["presentation"]["enabled"] = "yes"
    if fault == "unknown-figure":
        model["sections"][2]["blocks"][1]["figure_id"] = "absent"
    if fault == "source-type":
        model["sections"][0] = "invalid"
    save_model(project, model)
    with pytest.raises((ValueError, TypeError), match=message):
        build(project)
    assert (project / "handbook.html").read_bytes() == before


@pytest.mark.parametrize(
    "path",
    [
        "../escape",
        "nested/../../escape",
        "C:/escape",
        "C:stream",
        "/escape",
        "\\\\host\\share",
        "file.html:stream",
        "",
        "a/./b",
    ],
)
def test_unsafe_paths_are_rejected(project, path):
    with pytest.raises(ValueError, match="path"):
        dual.contained(project, path)


def test_linked_ancestors_and_hardlinks_are_rejected(project, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (project / "linked").symlink_to(outside, target_is_directory=True)
    except OSError:
        if sys.platform != "win32":
            raise
        command = (
            "New-Item -ItemType Junction -Path '"
            + str(project / "linked").replace("'", "''")
            + "' -Target '"
            + str(outside).replace("'", "''")
            + "' | Out-Null"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            check=True,
            capture_output=True,
        )
    with pytest.raises(ValueError, match="linked"):
        dual.contained(project, "linked/output.html")


def test_hardlinked_output_is_rejected(project):
    source = project / "source.html"
    source.write_text("keep", encoding="utf-8")
    os.link(source, project / "handbook.html")
    with pytest.raises(ValueError, match="hard-linked"):
        build(project)
    assert source.read_text(encoding="utf-8") == "keep"


@pytest.mark.parametrize("depth", ["concise", "balanced", "deep-dive"])
def test_unit_coverage_is_independent_of_complete_reading_page(project, depth):
    model = read_model(project)
    presentation = model["presentation"]
    presentation["depth"] = depth
    presentation["slides"][2]["unit_ids"] = {"acquisition": ["acquisition-text"]}
    presentation["omissions"] = {
        "acquisition/acquisition-observations": "Chart retained in analysis and reading page"
    }
    save_model(project, model)
    if depth == "deep-dive":
        with pytest.raises(ValueError, match="deep dive missing"):
            build(project)
    else:
        build(project)
        output = (project / "handbook.html").read_text(encoding="utf-8")
        assert output.count('data-dv-unit="acquisition-observations"') == 1
        assert output.count('data-dv-unit="analysis-observations"') == 2


def test_unowned_build_record_and_input_destination_are_rejected(project):
    record = project / "handbook.html.build.json"
    record.write_text('{"private":"keep"}', encoding="utf-8")
    with pytest.raises(ValueError, match="record modified or unowned"):
        build(project)
    assert record.read_text(encoding="utf-8") == '{"private":"keep"}'
    record.unlink()
    (project / "handbook.html").write_text("retained input", encoding="utf-8")
    model = read_model(project)
    model["retained_inputs"] = ["handbook.html"]
    save_model(project, model)
    with pytest.raises(ValueError, match="overlaps"):
        build(project)


@pytest.mark.parametrize(
    "source",
    [
        '<svg><path fill="url ( https://example.invalid/x )"/></svg>',
        '<svg><path fill="u\\72l(https://example.invalid/x)"/></svg>',
        '<svg><g xmlns="http://www.w3.org/1999/xhtml"/></svg>',
    ],
)
def test_svg_resource_variants_cannot_escape(source):
    with pytest.raises(ValueError):
        dual.svg_instance(source, "instance")


def test_quoted_local_svg_reference_is_rewritten():
    source = '<svg id="root"><defs><linearGradient id="tone"/></defs><path fill="url( &quot;#tone&quot; )"/></svg>'
    assert "url(#instance-tone)" in dual.svg_instance(source, "instance")


@pytest.mark.parametrize(
    "fragment",
    [
        '<p id="same"></p><p id="same"></p>',
        '<p aria-describedby="missing">Content</p>',
        '<a href="#missing">Go</a>',
    ],
)
def test_final_document_rejects_duplicate_or_unresolved_references(fragment):
    with pytest.raises(ValueError, match="document"):
        dual.DocumentReferences(fragment)


@pytest.mark.parametrize("kind", ["pie", "doughnut", "stacked", "made-up"])
def test_unsupported_chart_semantics_require_faithful_authored_asset(project, kind):
    block = read_model(project)["figures"]["observations"]
    block["chart_type_hint"] = kind
    with pytest.raises(ValueError, match="faithful SVG"):
        dual.render_chart(block, "chart")


def test_low_confidence_chart_preserves_original_without_invented_samples(project):
    model = read_model(project)
    block = model["figures"]["observations"]
    uri = next(
        block["data_uri"]
        for section in model["sections"]
        for block in section["blocks"]
        if block["type"] == "image"
    )
    block.update(confidence="low", source_image=uri)
    output = dual.render_chart(block, "chart")
    assert uri in output and "data-dv-enlarge" in output
    assert "data-dv-mark" not in output


@pytest.mark.parametrize(
    "feature", ["annotations", "error_bars", "panels", "secondary_axis"]
)
def test_specialized_source_geometry_cannot_be_silently_dropped(project, feature):
    block = read_model(project)["figures"]["observations"]
    block[feature] = ["source geometry"]
    with pytest.raises(ValueError, match="faithful SVG"):
        dual.render_chart(block, "chart")


def test_output_edit_during_write_is_preserved_and_lock_cleaned(project, monkeypatch):
    build(project)
    original = dual.Inputs.verify
    calls = 0

    def edit(inputs):
        nonlocal calls
        calls += 1
        original(inputs)
        if calls == 2:
            (project / "handbook.html").write_text(
                "concurrent user edit", encoding="utf-8"
            )

    monkeypatch.setattr(dual.Inputs, "verify", edit)
    with pytest.raises(ValueError, match="output changed"):
        build(project)
    assert (project / "handbook.html").read_text(
        encoding="utf-8"
    ) == "concurrent user edit"
    assert not (project / "handbook.html.lock").exists()


def test_figure_zoom_resets_locally_and_photo_decodes_before_enlargement(project):
    build(project)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1366, "height": 768})
        outbound = []
        page.on(
            "request",
            lambda request: (
                outbound.append(request.url)
                if request.url.startswith(("http:", "https:"))
                else None
            ),
        )
        page.goto((project / "handbook.html").as_uri())
        figures = page.locator("[data-dv-page] [data-dv-figure]")
        zoom = figures.first.locator("[data-dv-zoom]")
        initial_width = figures.first.locator("svg").bounding_box()["width"]
        zoom.fill("2")
        assert (
            figures.first.locator("svg").bounding_box()["width"] > initial_width * 1.8
        )
        assert (
            figures.first.locator("svg").evaluate("node => node.style.width") == "200%"
        )
        assert figures.nth(1).locator("svg").evaluate("node => node.style.width") == ""
        figures.first.locator("[data-dv-figure-reset]").click()
        assert zoom.input_value() == "1"
        image = page.locator("[data-dv-page] [data-dv-enlarge] img")
        assert image.evaluate(
            "async image => { await image.decode(); return image.naturalWidth === 320 && image.naturalHeight === 160; }"
        )
        image.click()
        assert page.locator("dialog[open] img").get_attribute(
            "src"
        ) == image.get_attribute("src")
        page.get_by_role("button", name="Close image", exact=True).click()
        page.locator("dialog").wait_for(state="detached")
        assert not outbound
        browser.close()


def test_map_directory_matches_geometry_and_keyboard_selection(project):
    model = read_model(project)
    regions = json.loads((project / "map.json").read_text(encoding="utf-8"))["regions"]
    model["sections"][0]["blocks"].append(
        {"id": "map", "type": "map", "asset": "map.svg", "regions": regions}
    )
    save_model(project, model)
    build(project)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto((project / "handbook.html").as_uri())
        figure = page.locator("[data-dv-page] [data-dv-map]")
        assert figure.locator("[data-dv-region]").count() == 12
        figure.get_by_role("searchbox").fill("Region 12")
        assert figure.locator("[data-dv-region]:visible").count() == 1
        choice = figure.get_by_role("button", name="Region 12", exact=True)
        choice.focus()
        choice.press("Enter")
        assert (
            figure.locator('[data-region="Region 12"]').get_attribute("data-selected")
            == "true"
        )
        assert figure.locator("[data-dv-map-status]").inner_text() == "Region 12"
        assert page.locator('[data-dv-deck] [data-selected="true"]').count() == 0
        browser.close()
    model["sections"][0]["blocks"][-1]["regions"] = regions[:-1]
    save_model(project, model)
    with pytest.raises(ValueError, match="directory must match"):
        build(project)


@pytest.mark.parametrize("javascript_enabled", [True, False])
def test_print_keeps_semantic_figure_content_and_expands_scroll_regions(
    project, javascript_enabled
):
    model = read_model(project)
    regions = json.loads((project / "map.json").read_text(encoding="utf-8"))["regions"]
    model["sections"][0]["blocks"].append(
        {"id": "map", "type": "map", "asset": "map.svg", "regions": regions}
    )
    save_model(project, model)
    build(project)
    html = project / "handbook.html"
    html.write_text(
        html.read_text(encoding="utf-8").replace(
            "</h2>", '</h2><code style="color:#f5f3ec">Print theme contrast</code>', 1
        ),
        encoding="utf-8",
    )
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1366, "height": 768},
            java_script_enabled=javascript_enabled,
        )
        page.goto((project / "handbook.html").as_uri())
        directory = page.locator("[data-dv-page] [data-dv-map] .dv-directory")
        assert directory.evaluate("e=>e.scrollHeight>e.clientHeight")
        code = page.locator("[data-dv-page] [data-theme=dark] code").first
        palette = "e=>({ink:getComputedStyle(e).color,paper:getComputedStyle(e.closest('[data-dv-section]')).backgroundColor})"
        screen_palette = code.evaluate(palette)
        page.emulate_media(media="print")
        assert code.evaluate(palette) == screen_palette
        assert page.locator("[data-dv-page] [data-dv-region]:visible").count() == 12
        assert directory.evaluate("e=>e.scrollHeight<=e.clientHeight+1")
        assert page.locator("[data-dv-page] .dv-legend button:visible").count() > 0
        assert page.locator("[data-dv-page] .dv-image img:visible").count() > 0
        assert page.locator("[data-dv-page] details table:visible").count() > 0
        assert page.locator("[data-dv-page] .dv-figure-tools:visible").count() == 0
        assert (
            page.locator("[data-dv-deck]:visible,[data-dv-open]:visible").count() == 0
        )
        page.emulate_media(media="screen")
        assert directory.evaluate("e=>e.scrollHeight>e.clientHeight")
        assert page.locator("[data-dv-page] details[open]").count() == 0
        assert page.locator("[data-dv-page] details table:visible").count() == 0
        browser.close()


def test_svg_measurements_find_broken_labels_and_preserve_readable_rendered_text(
    project,
):
    model = read_model(project)
    model["figures"]["observations"]["axis"].update(
        {"y_max": 20, "y_label": "Observations"}
    )
    save_model(project, model)
    build(project)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1366, "height": 768})
        page.goto((project / "handbook.html").as_uri())
        page.evaluate("NexusDualView.open(2)")
        chart = page.locator("[data-dv-slide]:not([hidden]) .dv-chart svg")
        probe = """svg => [...svg.querySelectorAll('text')].map(node => {
            const b=node.getBBox(),screen=node.getScreenCTM(),v=svg.viewBox.baseVal;
            const m=svg.getScreenCTM().inverse().multiply(screen);
            const points=[[b.x,b.y],[b.x+b.width,b.y],[b.x,b.y+b.height],[b.x+b.width,b.y+b.height]].map(([x,y])=>new DOMPoint(x,y).matrixTransform(m));
            return {text:node.textContent,inside:points.every(p=>p.x>=v.x&&p.y>=v.y&&p.x<=v.x+v.width&&p.y<=v.y+v.height),font:parseFloat(getComputedStyle(node).fontSize)*Math.hypot(screen.a,screen.b)};
        })"""
        measured = chart.evaluate(probe)
        assert all(item["font"] >= 18 and item["inside"] for item in measured)
        assert chart.evaluate("""svg => {
            const title=svg.querySelector('text[transform]').getBoundingClientRect();
            return [...svg.querySelectorAll('text[text-anchor="end"]')].every(tick =>
                tick.getBoundingClientRect().left >= title.right + 2);
        }""")
        rotated = chart.locator("text[transform]")
        rotated.evaluate(
            'node => node.setAttribute("transform", "translate(24 135) rotate(-90)")'
        )
        assert any(not item["inside"] for item in chart.evaluate(probe))
        rotated.evaluate(
            'node => node.setAttribute("transform", "translate(36 135) rotate(-90)")'
        )
        chart.locator("text:not([transform])").first.evaluate(
            'node => node.setAttribute("x", "2000")'
        )
        assert any(not item["inside"] for item in chart.evaluate(probe))
        browser.close()


@pytest.mark.parametrize("font_size", [18, 28])
def test_chart_axis_title_clears_decimal_ticks(project, font_size):
    chart = read_model(project)["figures"]["observations"]
    chart["axis"].update({"y_max": 20, "y_label": "Observations"})
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.set_content(
            f"<style>svg{{width:760px}}text{{font:{font_size}px Arial}}</style>"
            + dual.render_chart(chart, "axis-spacing")
        )
        assert page.locator("svg").evaluate("""svg => {
            const title=svg.querySelector('text[transform]').getBoundingClientRect();
            return [...svg.querySelectorAll('text[text-anchor="end"]')].every(tick =>
                tick.getBoundingClientRect().left >= title.right + 2);
        }""")
        browser.close()


def test_unowned_user_edit_and_busy_writer_are_preserved(project):
    output = project / "handbook.html"
    output.write_text("user-owned content", encoding="utf-8")
    with pytest.raises(ValueError, match="unowned"):
        build(project)
    build(project, expected_output=dual.digest(output.read_bytes()))
    output.write_text("concurrent user edit", encoding="utf-8")
    with pytest.raises(ValueError, match="modified"):
        build(project)
    assert output.read_text(encoding="utf-8") == "concurrent user edit"
    output.unlink()
    lock = project / "handbook.html.lock"
    lock.write_text("other writer", encoding="utf-8")
    with pytest.raises(FileExistsError):
        build(project)
    assert lock.read_text(encoding="utf-8") == "other writer"


def test_source_change_during_render_is_detected(project, monkeypatch):
    original = dual.render

    def changing(model, inputs):
        result = original(model, inputs)
        (project / "handbook.md").write_text("changed during build", encoding="utf-8")
        return result

    monkeypatch.setattr(dual, "render", changing)
    with pytest.raises(ValueError, match="source changed"):
        build(project)
    assert not (project / "handbook.html").exists()


def test_svg_instances_rewrite_root_descendants_and_idrefs():
    source = '<svg xmlns="http://www.w3.org/2000/svg" id="root" aria-labelledby="title desc"><title id="title">Flow</title><desc id="desc">Direction</desc><defs><marker id="arrow"/><linearGradient id="tone"/></defs><path fill="url(#tone)" marker-end="url(#arrow)"/><use href="#root"/></svg>'
    first, second = (
        dual.svg_instance(source, "first"),
        dual.svg_instance(source, "second"),
    )
    assert 'aria-labelledby="first-title first-desc"' in first
    assert 'href="#first-root"' in first
    assert "url(#first-arrow)" in first
    assert "first-" not in second


@pytest.mark.parametrize(
    "source",
    [
        "<svg><script>alert(1)</script></svg>",
        '<svg><style>@import url("https://example.invalid/blocked-probe.css");</style></svg>',
        '<svg onload="alert(1)"/>',
        "<!DOCTYPE svg><svg/>",
        '<svg><use href="https://example.invalid/x"/></svg>',
        '<svg><path fill="URL(https://example.invalid/x)"/></svg>',
        '<svg><path fill="url(#missing)"/></svg>',
        '<svg><g id="a"/><g id="a"/></svg>',
    ],
)
def test_unsafe_or_broken_svg_is_rejected(source):
    with pytest.raises(ValueError):
        dual.svg_instance(source, "test")


@pytest.mark.parametrize(
    "source",
    [
        "<script>x</script>",
        '<img src="https://example.invalid/x">',
        '<button onclick="x()">x</button>',
        '<a href="javascript:alert(1)">x</a>',
    ],
)
def test_authored_active_fragments_are_rejected(source):
    with pytest.raises(ValueError):
        dual.AuthoredFragment(source, "prefix", {})


def test_authored_fragments_preserve_units_and_namespace_instances(project):
    model = read_model(project)
    model["sections"][0]["fragment"] = "intro.html"
    (project / "intro.html").write_text(
        '<div id="panel" aria-labelledby="label"><h3 id="label">Origin</h3>{{unit:overview-text}}</div>',
        encoding="utf-8",
    )
    save_model(project, model)
    build(project)
    with pytest.raises(ValueError, match="missing source units"):
        dual.AuthoredFragment(
            "<div>Omitted</div>", "prefix", {"source": "<p>Real source</p>"}
        )
    assert "<script>alert(1)</script>" not in dual.json_script(
        {"x": "</script><script>alert(1)</script>"}
    )


@pytest.mark.parametrize("values", [[-12, 18], [None, 18], [12, None], [0, 0]])
def test_chart_ranges_missing_values_and_original_precision(project, values):
    block = copy.deepcopy(read_model(project)["figures"]["observations"])
    block["series"][0]["values"] = values
    block["chart_type_hint"] = "line"
    output = dual.render_chart(block, "test")
    assert "nan" not in output.lower()
    for value in values:
        assert ("Unavailable" if value is None else str(value)) in output
    assert "Instrument" in output


def test_both_views_share_values_but_not_filter_state(project):
    build(project)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1366, "height": 768})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto((project / "handbook.html").as_uri())
        page.locator("[data-dv-page] [data-dv-series]").first.click()
        page.locator("[data-dv-open]").first.click()
        page.evaluate("NexusDualView.open(2)")
        assert (
            page.locator(
                "[data-dv-slide]:visible [data-dv-series]"
            ).first.get_attribute("aria-pressed")
            == "true"
        )
        assert page.locator("[data-dv-slide]:visible").inner_text().count("12") >= 1
        page.locator("[data-dv-exit]").click()
        assert (
            page.locator("[data-dv-page] [data-dv-series]").first.get_attribute(
                "aria-pressed"
            )
            == "false"
        )
        assert page.evaluate(
            'new Set([...document.querySelectorAll("[id]")].map(e=>e.id)).size === document.querySelectorAll("[id]").length'
        )
        assert not errors
        browser.close()


def test_page_only_omits_presentation_assets(project):
    model = read_model(project)
    model["presentation"]["enabled"] = False
    save_model(project, model)
    build(project)
    output = (project / "handbook.html").read_text(encoding="utf-8")
    assert "<div data-dv-deck" not in output
    assert "<button data-dv-open" not in output
    assert "window.NexusDualView" not in output


def test_builder_help_is_runnable():
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "build_presentation.py"), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "100%" in result.stdout and "--check" in result.stdout
