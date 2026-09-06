from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL = REPO_ROOT / "tests" / "guides" / "tools" / "render_guide.py"

HOME_RUNTIME_METRICS = r"""
() => {
  function rectFor(element) {
    const rect = element.getBoundingClientRect();
    return {
      width: rect.width,
      height: rect.height,
      left: rect.left,
      right: rect.right,
    };
  }

  function parseColor(value) {
    const channels = value.match(/[\d.]+/g);
    if (!channels || channels.length < 3) {
      throw new Error(`Unsupported computed color: ${value}`);
    }
    return {
      red: Number(channels[0]),
      green: Number(channels[1]),
      blue: Number(channels[2]),
      alpha: channels.length > 3 ? Number(channels[3]) : 1,
    };
  }

  function composite(top, bottom) {
    const alpha = top.alpha + bottom.alpha * (1 - top.alpha);
    if (alpha === 0) return {red: 0, green: 0, blue: 0, alpha: 0};
    return {
      red: (top.red * top.alpha + bottom.red * bottom.alpha * (1 - top.alpha)) / alpha,
      green: (top.green * top.alpha + bottom.green * bottom.alpha * (1 - top.alpha)) / alpha,
      blue: (top.blue * top.alpha + bottom.blue * bottom.alpha * (1 - top.alpha)) / alpha,
      alpha,
    };
  }

  function effectiveBackground(element) {
    const ancestors = [];
    for (let node = element; node; node = node.parentElement) ancestors.unshift(node);
    return ancestors.reduce(
      (background, node) => composite(
        parseColor(getComputedStyle(node).backgroundColor),
        background,
      ),
      {red: 255, green: 255, blue: 255, alpha: 1},
    );
  }

  function luminance(color) {
    const channels = [color.red, color.green, color.blue].map((channel) => {
      const normalized = channel / 255;
      return normalized <= 0.04045
        ? normalized / 12.92
        : ((normalized + 0.055) / 1.055) ** 2.4;
    });
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
  }

  function contrastFor(element) {
    const background = effectiveBackground(element);
    const foreground = composite(parseColor(getComputedStyle(element).color), background);
    const foregroundLuminance = luminance(foreground);
    const backgroundLuminance = luminance(background);
    return {
      name: element.textContent.trim(),
      foreground,
      background,
      ratio: (Math.max(foregroundLuminance, backgroundLuminance) + 0.05)
        / (Math.min(foregroundLuminance, backgroundLuminance) + 0.05),
    };
  }

  const lockup = document.querySelector(".hero-lockup.in");
  const wordmark = document.querySelector(".hero-wordmark");
  if (!lockup || !wordmark) throw new Error("Home hero lockup did not enter its revealed state");
  const wordmarkRange = document.createRange();
  wordmarkRange.selectNodeContents(wordmark);

  return {
    theme: document.documentElement.getAttribute("data-theme"),
    activeHome: Boolean(document.querySelector('.page.active[data-page="home"]')),
    viewportWidth: window.innerWidth,
    lockup: rectFor(lockup),
    wordmark: {
      ...rectFor(wordmark),
      lineCount: new Set(
        Array.from(wordmarkRange.getClientRects())
          .filter((rect) => rect.width > 0 && rect.height > 0)
          .map((rect) => Math.round(rect.top))
      ).size,
    },
    platforms: Array.from(document.querySelectorAll(".platform-item")).map((item) => ({
      name: item.getAttribute("data-platform"),
      ...rectFor(item),
    })),
    officialMarks: Array.from(
      // v4.4.1 Phase 2: `platform-mark` moved to the wrapper so each approved SVG stays
      // byte-verbatim and hash-checkable. All five marks are official geometry now, so the
      // old data-logo-source split no longer distinguishes anything.
      document.querySelectorAll('.platform-mark > svg'),
    ).map((mark) => {
      const geometry = mark.getBBox();
      return {
        platform: mark.closest(".platform-item")?.getAttribute("data-platform"),
        ...rectFor(mark),
        geometryWidth: geometry.width,
        geometryHeight: geometry.height,
      };
    }),
    contrasts: Array.from(document.querySelectorAll(".platform-name"))
      .filter((name) => {
        const style = getComputedStyle(name);
        const rect = name.getBoundingClientRect();
        return style.display !== "none"
          && style.visibility !== "hidden"
          && Number(style.opacity) > 0
          && rect.width > 0
          && rect.height > 0;
      })
      .map(contrastFor),
    verifyNumerals: Array.from(
      document.querySelectorAll(".verify-steps--secondary .vs-n"),
    ).map(contrastFor),
    comparisonLabels: Array.from(document.querySelectorAll(".cmp-side"))
      .map(contrastFor),
  };
}
"""


def _load_renderer() -> ModuleType:
    spec = importlib.util.spec_from_file_location("render_guide_tool", TOOL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _require_browser(render_gate: object) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        render_gate("Playwright is not installed")  # type: ignore[operator]
        return

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            browser.close()
    except Exception as error:  # noqa: BLE001 - environment probe classifies launch failures
        render_gate(f"Playwright Chromium cannot launch: {error}")  # type: ignore[operator]


def test_parser_preserves_legacy_output_root_by_default() -> None:
    renderer = _load_renderer()

    args = renderer._parse_args(["--label", "phase-1"])

    assert args.output_dir == renderer.OUT_BASE
    assert args.label == "phase-1"


def test_parser_accepts_explicit_output_root(tmp_path: Path) -> None:
    renderer = _load_renderer()

    args = renderer._parse_args(
        ["--label", "phase-1", "--output-dir", str(tmp_path)]
    )

    assert args.output_dir == tmp_path
    assert args.output_dir / args.label == tmp_path / "phase-1"


def test_display_path_accepts_locations_outside_repository(tmp_path: Path) -> None:
    renderer = _load_renderer()

    assert renderer._display_path(tmp_path) == str(tmp_path.resolve())


def test_explicit_output_root_writes_local_browser_evidence(
    tmp_path: Path,
    render_gate: object,
) -> None:
    _require_browser(render_gate)
    renderer = _load_renderer()

    result = renderer.main(
        [
            "--label",
            "smoke",
            "--output-dir",
            str(tmp_path),
            "--pages",
            "home",
            "--themes",
            "dark",
            "--widths",
            "320",
            "--reduced-motion",
        ]
    )

    screenshot = tmp_path / "smoke" / "home-dark-320-rm.png"
    assert result == 0
    assert screenshot.is_file()
    assert screenshot.stat().st_size > 0


def test_home_runtime_contract_across_themes_and_widths(
    render_gate: object,
) -> None:
    _require_browser(render_gate)
    from playwright.sync_api import sync_playwright

    renderer = _load_renderer()
    guide_url = renderer.GUIDE.resolve().as_uri()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for theme in ("dark", "light"):
                for width in (320, 1440):
                    case = f"{theme}/{width}px"
                    context = browser.new_context(viewport={"width": width, "height": 940})
                    context.add_init_script(
                        f'window.localStorage.setItem("portfolio-theme", "{theme}");'
                    )
                    external_requests: list[str] = []
                    context.route(re.compile(r"^https?://"), lambda route: route.abort())
                    page = context.new_page()
                    console_errors: list[str] = []
                    page_errors: list[str] = []
                    page.on(
                        "console",
                        lambda message, errors=console_errors: errors.append(message.text)
                        if message.type == "error"
                        else None,
                    )
                    page.on(
                        "pageerror",
                        lambda error, errors=page_errors: errors.append(str(error)),
                    )
                    page.on(
                        "request",
                        lambda request, requests=external_requests: requests.append(request.url)
                        if request.url.startswith(("http://", "https://"))
                        else None,
                    )

                    try:
                        page.goto(f"{guide_url}#home", wait_until="load")
                        page.wait_for_selector(
                            ".hero-lockup.in",
                            state="attached",
                            timeout=3000,
                        )
                        metrics = page.evaluate(HOME_RUNTIME_METRICS)

                        assert not console_errors, f"{case}: console errors: {console_errors}"
                        assert not page_errors, f"{case}: page errors: {page_errors}"
                        assert not external_requests, (
                            f"{case}: Home attempted external requests: {external_requests}"
                        )
                        assert metrics["theme"] == theme, (
                            f"{case}: requested theme was not applied"
                        )
                        assert metrics["activeHome"], f"{case}: Home page is not active"

                        for subject in ("lockup", "wordmark"):
                            box = metrics[subject]
                            assert box["width"] > 0 and box["height"] > 0, (
                                f"{case}: {subject} has an empty box: {box}"
                            )
                            assert box["left"] >= -0.5, (
                                f"{case}: {subject} escapes the left viewport edge: {box}"
                            )
                            assert box["right"] <= metrics["viewportWidth"] + 0.5, (
                                f"{case}: {subject} escapes the right viewport edge: {box}"
                            )
                        assert metrics["wordmark"]["lineCount"] == 1, (
                            f"{case}: Nexus Hub wordmark wrapped to multiple lines"
                        )

                        platforms = metrics["platforms"]
                        assert len(platforms) == 5, (
                            f"{case}: expected five platform items, got {len(platforms)}"
                        )
                        empty_platforms = [
                            platform["name"]
                            for platform in platforms
                            if platform["width"] <= 0 or platform["height"] <= 0
                        ]
                        assert not empty_platforms, (
                            f"{case}: platform items have empty boxes: {empty_platforms}"
                        )

                        official_marks = metrics["officialMarks"]
                        assert len(official_marks) == 5, (
                            f"{case}: expected five inline platform marks, got {len(official_marks)}"
                        )
                        empty_marks = [
                            mark["platform"]
                            for mark in official_marks
                            if mark["width"] <= 0
                            or mark["height"] <= 0
                            or mark["geometryWidth"] <= 0
                            or mark["geometryHeight"] <= 0
                        ]
                        assert not empty_marks, (
                            f"{case}: official SVG marks have empty geometry: {empty_marks}"
                        )

                        contrasts = metrics["contrasts"]
                        assert len(contrasts) == 5, (
                            f"{case}: expected five visible platform names, got {len(contrasts)}"
                        )
                        low_contrast = [
                            f'{result["name"]}={result["ratio"]:.2f}:1'
                            for result in contrasts
                            if result["ratio"] < 4.5
                        ]
                        assert not low_contrast, (
                            f"{case}: platform-name contrast is below 4.5:1: {low_contrast}"
                        )

                        verify_numerals = metrics["verifyNumerals"]
                        assert len(verify_numerals) == 2, (
                            f"{case}: expected two visible verification numerals, "
                            f"got {len(verify_numerals)}"
                        )
                        low_numeral_contrast = [
                            f'{result["name"]}={result["ratio"]:.2f}:1'
                            for result in verify_numerals
                            if result["ratio"] < 4.5
                        ]
                        assert not low_numeral_contrast, (
                            f"{case}: verification numeral contrast is below 4.5:1: "
                            f"{low_numeral_contrast}"
                        )

                        comparison_labels = metrics["comparisonLabels"]
                        assert len(comparison_labels) == 2, (
                            f"{case}: expected two visible comparison labels, "
                            f"got {len(comparison_labels)}"
                        )
                        low_comparison_contrast = [
                            f'{result["name"]}={result["ratio"]:.2f}:1'
                            for result in comparison_labels
                            if result["ratio"] < 4.5
                        ]
                        assert not low_comparison_contrast, (
                            f"{case}: comparison-label contrast is below 4.5:1: "
                            f"{low_comparison_contrast}"
                        )
                    finally:
                        context.close()
        finally:
            browser.close()


@pytest.mark.parametrize("width", (320, 420, 720, 721, 900, 1440))
def test_foundations_phase2_diagrams_are_legible_at_release_and_breakpoint_widths(
    render_gate: object,
    width: int,
) -> None:
    _require_browser(render_gate)
    from playwright.sync_api import sync_playwright

    renderer = _load_renderer()
    guide_url = renderer.GUIDE.resolve().as_uri()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for theme in ("dark", "light"):
                context = browser.new_context(viewport={"width": width, "height": 940})
                context.add_init_script(
                    f'window.localStorage.setItem("portfolio-theme", "{theme}");'
                )
                context.route(re.compile(r"^https?://"), lambda route: route.abort())
                page = context.new_page()
                console_errors: list[str] = []
                page_errors: list[str] = []
                page.on(
                    "console",
                    lambda message, errors=console_errors: errors.append(message.text)
                    if message.type == "error"
                    else None,
                )
                page.on(
                    "pageerror",
                    lambda error, errors=page_errors: errors.append(str(error)),
                )

                try:
                    page.goto(f"{guide_url}#foundations", wait_until="load")
                    page.wait_for_selector(
                        '.page.active[data-page="foundations"]',
                        state="visible",
                        timeout=3000,
                    )
                    metrics = page.evaluate(
                        r"""
                        () => {
                          const visible = (element) => {
                            const style = getComputedStyle(element);
                            const rect = element.getBoundingClientRect();
                            return style.display !== "none"
                              && style.visibility !== "hidden"
                              && rect.width > 0
                              && rect.height > 0;
                          };
                          return {
                            theme: document.documentElement.getAttribute("data-theme"),
                            bodyOverflow: document.documentElement.scrollWidth - window.innerWidth,
                            diagrams: Array.from(
                              document.querySelectorAll("svg[data-phase2-diagram]"),
                            ).filter(visible).map((diagram) => {
                                  const frame = diagram.getBoundingClientRect();
                                  const nodes = Array.from(diagram.querySelectorAll(
                                    "[data-stage], [data-token-piece], "
                                      + "[data-image-stage], [data-phase2-node]",
                                  )).map((node) => {
                                    const shape = Array.from(node.children).find(
                                      (child) => child.tagName.toLowerCase() === "rect",
                                    );
                                    const shapeRect = shape ? shape.getBoundingClientRect() : null;
                                    return {
                                      name: node.getAttribute("data-stage")
                                        || node.getAttribute("data-token-piece")
                                        || node.getAttribute("data-image-stage")
                                        || node.getAttribute("data-phase2-node"),
                                      hasShape: Boolean(shapeRect),
                                      texts: Array.from(node.children)
                                        .filter((child) => child.tagName.toLowerCase() === "text")
                                        .map((label) => {
                                          const rect = label.getBoundingClientRect();
                                          return shapeRect ? {
                                            text: label.textContent.trim(),
                                            left: rect.left - shapeRect.left,
                                            right: shapeRect.right - rect.right,
                                            top: rect.top - shapeRect.top,
                                            bottom: shapeRect.bottom - rect.bottom,
                                          } : {text: label.textContent.trim()};
                                        }),
                                    };
                                  });
                                  return {
                                    name: diagram.getAttribute("data-phase2-diagram"),
                                    width: frame.width,
                                    height: frame.height,
                                    nodes,
                                    texts: Array.from(diagram.querySelectorAll("text"))
                                      .filter(visible)
                                      .map((label) => {
                                        const rect = label.getBoundingClientRect();
                                        return {
                                          text: label.textContent.trim(),
                                          left: rect.left - frame.left,
                                          right: frame.right - rect.right,
                                          top: rect.top - frame.top,
                                          bottom: frame.bottom - rect.bottom,
                                          height: rect.height,
                                        };
                                      }),
                                  };
                                }),
                              };
                            }
                        """
                    )

                    assert not console_errors, f"{theme}: {console_errors}"
                    assert not page_errors, f"{theme}: {page_errors}"
                    assert metrics["theme"] == theme
                    assert metrics["bodyOverflow"] <= 1, (
                        f"{theme}: Foundations scrolls horizontally by "
                        f'{metrics["bodyOverflow"]}px'
                    )
                    diagrams = metrics["diagrams"]
                    assert {diagram["name"] for diagram in diagrams} == {
                        "tokens",
                    }
                    for diagram in diagrams:
                        if width == 720:
                            assert diagram["height"] <= 720, (
                                f'{diagram["name"]}: mobile diagram is excessively tall: '
                                f'{diagram["height"]}px'
                            )
                        assert diagram["texts"], (
                            f'{diagram["name"]}: no visible labels'
                        )
                        for label in diagram["texts"]:
                            assert label["height"] >= 11.5, (
                                f'{theme}/{diagram["name"]}: label too small: {label}'
                            )
                            for edge in ("left", "right", "top", "bottom"):
                                assert label[edge] >= -1, (
                                    f'{theme}/{diagram["name"]}: label escapes {edge}: '
                                    f"{label}"
                                )
                        assert diagram["nodes"], (
                            f'{diagram["name"]}: no shape-containment nodes'
                        )
                        for node in diagram["nodes"]:
                            assert node["hasShape"], (
                                f'{theme}/{diagram["name"]}/{node["name"]}: '
                                "missing containing rect"
                            )
                            assert node["texts"], (
                                f'{theme}/{diagram["name"]}/{node["name"]}: '
                                "missing direct text labels"
                            )
                            for label in node["texts"]:
                                for edge in ("left", "right", "top", "bottom"):
                                    assert label[edge] >= -1, (
                                        f'{theme}/{diagram["name"]}/{node["name"]}: '
                                        f'label escapes {edge}: {label}'
                                    )
                finally:
                    context.close()
        finally:
            browser.close()


def test_training_cold_deep_link_accepts_and_discards_legacy_beat(
    render_gate: object,
) -> None:
    _require_browser(render_gate)
    from playwright.sync_api import sync_playwright

    renderer = _load_renderer()
    guide_url = renderer.GUIDE.resolve().as_uri()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            context = browser.new_context(viewport={"width": 900, "height": 940})
            context.route(re.compile(r"^https?://"), lambda route: route.abort())
            page = context.new_page()
            try:
                page.goto(
                    f"{guide_url}#training/review?beat=1",
                    wait_until="load",
                )
                page.wait_for_selector(
                    '.page.active[data-page="training"]',
                    state="visible",
                    timeout=3000,
                )
                page.wait_for_function(
                    """
                    () => document.querySelector('[data-nht="title"]')?.textContent
                      === "Turn the symptom into a finding"
                    """,
                    timeout=3000,
                )
                assert page.evaluate("location.hash") == "#training/review"
                assert page.locator('[data-nht="title"]').inner_text() == (
                    "Turn the symptom into a finding"
                )
                assert "tell a real damage defect from hard difficulty" in (
                    page.locator('[data-nht="takeaway"]').inner_text()
                )
            finally:
                context.close()
        finally:
            browser.close()


@pytest.mark.parametrize("theme", ("dark", "light"))
def test_training_page_navigation_does_not_overflow_at_320px(
    render_gate: object,
    theme: str,
) -> None:
    _require_browser(render_gate)
    from playwright.sync_api import sync_playwright

    renderer = _load_renderer()
    guide_url = renderer.GUIDE.resolve().as_uri()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            context = browser.new_context(viewport={"width": 320, "height": 940})
            context.route(re.compile(r"^https?://"), lambda route: route.abort())
            context.add_init_script(
                f'window.localStorage.setItem("portfolio-theme", "{theme}");'
            )
            page = context.new_page()
            try:
                page.goto(f"{guide_url}#training", wait_until="load")
                page.wait_for_selector(
                    '.page.active[data-page="training"]',
                    state="visible",
                    timeout=3000,
                )
                page.add_style_tag(
                    content=".pagenav, .pagenav * { font-family: Arial, sans-serif !important; }"
                )
                metrics = page.locator(
                    '.page.active[data-page="training"] .pagenav'
                ).evaluate(
                    """
                    nav => ({
                      documentWidth: document.documentElement.scrollWidth,
                      viewportWidth: window.innerWidth,
                      navigationWidth: nav.clientWidth,
                      navigationScrollWidth: nav.scrollWidth,
                    })
                    """
                )
                assert metrics["documentWidth"] <= metrics["viewportWidth"] + 1, (
                    f"{theme}: training document overflow: {metrics}"
                )
                assert (
                    metrics["navigationScrollWidth"]
                    <= metrics["navigationWidth"] + 1
                ), f"{theme}: training page navigation overflow: {metrics}"
            finally:
                context.close()
        finally:
            browser.close()


def test_foundations_story_diagram_retirement_is_honest() -> None:
    """v4.4.1 Phase 4 rebuilt the Foundations story diagrams as HTML node trees, so the
    SVG variant-visibility, node-containment, and traveling-pulse machinery the old
    route-motion test measured no longer has a subject. Its living replacements are the
    visual-defect detector's containment and overflow rules (six viewports, both themes)
    and test_v441_phase4_foundations.py for the shared grammar and media behavior. This
    guard keeps the retirement honest: an SVG story diagram cannot ride back in without
    restoring those assertions.
    """
    guide_text = _load_renderer().GUIDE.read_text(encoding="utf-8")
    assert "data-phase3-diagram" not in guide_text, (
        "an SVG story diagram returned; restore variant, containment, and pulse coverage"
    )
