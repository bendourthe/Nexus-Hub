"""Browser qualification of every control in the retained v4.11 report pilot."""

import importlib
import os
from collections import Counter
from pathlib import Path

import pytest

if os.environ.get("NEXUS_REQUIRE_RENDER") == "1":
    playwright_sync = importlib.import_module("playwright.sync_api")
else:
    playwright_sync = pytest.importorskip(
        "playwright.sync_api", reason="playwright is not installed"
    )

expect = playwright_sync.expect
sync_playwright = playwright_sync.sync_playwright


ROOT = Path(__file__).resolve().parents[2]
PILOT = (
    ROOT
    / "docs/releases/v4/v4.11/development/interactive-handbooks"
    / "phase-6-native-attempts/report-final/pilot.html"
)


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as playwright:
        instance = playwright.chromium.launch()
        yield instance
        instance.close()


@pytest.fixture
def page(browser):
    current = browser.new_page(viewport={"width": 1366, "height": 768})
    errors = []
    outbound = []
    current.on("pageerror", lambda error: errors.append(str(error)))

    def block(route):
        outbound.append(route.request.url)
        route.abort()

    current.route("http**/*", block)
    current.goto(PILOT.resolve().as_uri())
    yield current
    assert not errors, errors
    assert not outbound, outbound
    current.close()


def _open(page, index):
    page.evaluate("index => window.NexusDualView.open(index)", index)


def _figure(page, view):
    if view == "reading":
        return page.locator('[data-dv-section="counts"] [data-dv-figure]')
    _open(page, 2)
    return page.locator('[data-dv-slide="counts"] [data-dv-figure]')


def _assert_series_hides_marks(figure, series):
    marks = figure.locator(f'[data-dv-series-marks="{series}"]')
    assert marks.evaluate("el => getComputedStyle(el).display") != "none"
    figure.locator(f'[data-dv-series="{series}"]').click()
    assert marks.evaluate("el => getComputedStyle(el).display") == "none", (
        "plotted marks stayed visible"
    )


def test_control_census_has_no_unmapped_elements(page):
    actual = Counter(
        page.evaluate(
            """() => [...document.querySelectorAll('button,input,select,summary,a[href]')]
              .map(el => {
                const owner = el.closest('[data-dv-slide],[data-dv-section]');
                const scope = owner ? (owner.dataset.dvSlide || owner.dataset.dvSection)
                  : el.closest('[data-dv-deck]') ? 'deck-shell' : 'page-shell';
                const marker = el.getAttributeNames().find(name =>
                  ['data-dv-open','data-dv-series','data-dv-zoom','data-dv-figure-reset',
                   'data-dv-enlarge','data-dv-prev','data-dv-replay','data-dv-picker',
                   'data-dv-next','data-dv-fullscreen','data-dv-exit'].includes(name));
                const identity = el.tagName === 'A' ? `href=${el.getAttribute('href')}`
                  : el.tagName === 'SUMMARY' ? `summary=${el.textContent.trim()}`
                  : marker ? `${marker}=${el.getAttribute(marker)}`
                  : el.matches('input[type=number][aria-label="Observation count axis ceiling"]')
                    ? 'axis-ceiling' : 'unmapped';
                return `${scope}|${el.tagName.toLowerCase()}|${identity}`;
              })"""
        )
    )
    expected = Counter(
        {
            "page-shell|button|data-dv-open=": 2,
            **{f"page-shell|a|href=#{target}": 1 for target in ("overview", "counts", "review-path", "scope")},
            **{f"agenda|a|href=#{target}": 2 for target in ("counts", "review-path", "scope")},
            **{f"counts|{tag}|{marker}": 2 for tag, marker in (
                ("button", "data-dv-series=0"), ("button", "data-dv-series=1"),
                ("input", "data-dv-zoom="), ("button", "data-dv-figure-reset="),
                ("input", "axis-ceiling"),
                ("summary", "summary=Exact chart values"),
            )},
            "review-path|summary|summary=Inspect supplied diagram": 1,
            "review-path|button|data-dv-enlarge=": 1,
            **{f"review|{tag}|{marker}": 1 for tag, marker in (
                ("summary", "summary=Inspect supplied diagram"),
                ("button", "data-dv-enlarge="),
            )},
            **{f"deck-shell|button|data-dv-{name}=": 1 for name in (
                "prev", "replay", "next", "fullscreen", "exit"
            )},
            "deck-shell|select|data-dv-picker=": 1,
        }
    )
    assert sum(actual.values()) == 34, actual
    assert actual == expected


@pytest.mark.parametrize("button_index", [0, 1])
def test_both_reading_open_buttons_activate_cover(page, button_index):
    page.locator("[data-dv-page] [data-dv-open]").nth(button_index).click()
    expect(page.locator("[data-dv-deck]")).to_be_visible()
    expect(page.locator('[data-dv-slide="cover"]')).to_be_visible()
    expect(page.locator("[data-dv-count]")).to_have_text("1 / 5")


@pytest.mark.parametrize("view", ["reading", "presentation"])
@pytest.mark.parametrize("series", ["0", "1"])
def test_series_controls_change_plotted_marks(page, view, series):
    figure = _figure(page, view)
    _assert_series_hides_marks(figure, series)


def test_inert_stage_control_is_detected_by_plotted_marks(page):
    figure = _figure(page, "presentation")
    page.evaluate(
        """() => document.addEventListener('click', event => {
          if (event.target.closest('[data-dv-slide="counts"] [data-dv-series="0"]'))
            event.stopImmediatePropagation();
        }, true)"""
    )
    with pytest.raises(AssertionError, match="plotted marks stayed visible"):
        _assert_series_hides_marks(figure, "0")


@pytest.mark.parametrize("view", ["reading", "presentation"])
def test_zoom_and_reset_change_chart_not_only_control_state(page, view):
    figure = _figure(page, view)
    zoom = figure.locator("[data-dv-zoom]")
    svg = figure.locator("[data-dv-zoom-view] > svg")
    zoom.focus()
    zoom.press("ArrowRight")
    assert svg.evaluate("el => el.style.width") == "125%"
    figure.locator('[data-dv-series="0"]').click()
    expect(figure.locator('[data-dv-series-marks="0"]')).to_have_css("display", "none")
    figure.locator("[data-dv-figure-reset]").click()
    assert svg.evaluate("el => el.style.width") == "100%"
    assert figure.locator('[data-dv-series-marks="0"]').evaluate(
        "el => getComputedStyle(el).display"
    ) != "none"


@pytest.mark.parametrize("view", ["reading", "presentation"])
def test_axis_ceiling_changes_plotted_axis(page, view):
    figure = _figure(page, view)
    axis = figure.get_by_label("Observation count axis ceiling")
    labels = figure.locator("svg > text")
    before = labels.all_text_contents()
    axis.fill("40")
    axis.press("Tab")
    page.wait_for_function(
        "figure => [...figure.querySelectorAll('svg > text')].some(t => t.textContent === '40')",
        arg=figure.element_handle(),
    )
    assert labels.all_text_contents() != before
    expect(figure.locator(".tide-chart-status")).to_contain_text("Axis: 0 to 40")


@pytest.mark.parametrize("view", ["reading", "presentation"])
@pytest.mark.parametrize("kind", ["counts", "review"])
def test_details_summaries_reveal_content(page, view, kind):
    if view == "reading":
        owner = page.locator(f'[data-dv-section="{"counts" if kind == "counts" else "review-path"}"]')
    else:
        _open(page, 2 if kind == "counts" else 3)
        owner = page.locator(f'[data-dv-slide="{kind}"]')
    details = owner.locator("details")
    assert details.count() == 1
    assert not details.evaluate("el => el.open")
    details.locator("summary").click()
    expect(details).to_have_attribute("open", "")
    assert details.locator("table,img").count() >= 1


@pytest.mark.parametrize("view", ["reading", "presentation"])
def test_enlarge_and_close_image(page, view):
    if view == "reading":
        owner = page.locator('[data-dv-section="review-path"]')
    else:
        _open(page, 3)
        owner = page.locator('[data-dv-slide="review"]')
    owner.locator("summary").click()
    enlarge = owner.locator("[data-dv-enlarge]")
    enlarge.click()
    dialog = page.locator("dialog.dv-enlargement[open]")
    expect(dialog.locator("img")).to_be_visible()
    dialog.get_by_role("button", name="Close image").click()
    expect(dialog).to_have_count(0)
    expect(enlarge).to_be_focused()


@pytest.mark.parametrize("scope,target", [
    ("page-shell", "overview"), ("page-shell", "counts"),
    ("page-shell", "review-path"), ("page-shell", "scope"),
    ("reading-agenda", "counts"), ("reading-agenda", "review-path"),
    ("reading-agenda", "scope"), ("slide-agenda", "counts"),
    ("slide-agenda", "review-path"), ("slide-agenda", "scope"),
])
def test_every_internal_link_reaches_its_target(page, scope, target):
    if scope == "page-shell":
        link = page.locator(f'.dv-top-menu a[href="#{target}"]')
    elif scope == "reading-agenda":
        link = page.locator(f'[data-dv-section="agenda"] a[href="#{target}"]')
    else:
        _open(page, 1)
        link = page.locator(f'[data-dv-slide="agenda"] a[href="#{target}"]')
    link.click()
    if scope == "slide-agenda":
        slide = {"counts": "counts", "review-path": "review", "scope": "appendix"}[target]
        expect(page.locator(f'[data-dv-slide="{slide}"]')).to_be_visible()
        expect(page.locator("[data-dv-deck]")).to_be_visible()
        return
    expect(page.locator("[data-dv-page]")).to_be_visible()
    page.wait_for_function("hash => location.hash === hash", arg=f"#{target}")
    expect(page.locator(f"#{target}")).to_be_visible()


def test_deck_next_previous_and_picker(page):
    _open(page, 0)
    page.locator("[data-dv-next]").click()
    expect(page.locator("[data-dv-count]")).to_have_text("2 / 5")
    page.locator("[data-dv-prev]").click()
    expect(page.locator("[data-dv-count]")).to_have_text("1 / 5")
    page.locator("[data-dv-picker]").select_option("3")
    expect(page.locator('[data-dv-slide="review"]')).to_be_visible()
    expect(page.locator("[data-dv-count]")).to_have_text("4 / 5")


def test_deck_replay_starts_new_visible_animation(page):
    _open(page, 3)
    page.evaluate(
        "window.__pilotOldAnimation = document.querySelector("
        "'[data-dv-slide=review] [data-dv-animate]').getAnimations()[0]"
    )
    assert page.evaluate("Boolean(window.__pilotOldAnimation)")
    page.locator("[data-dv-replay]").click()
    assert page.evaluate(
        "window.__pilotOldAnimation !== document.querySelector("
        "'[data-dv-slide=review] [data-dv-animate]').getAnimations()[0]"
    )


def test_deck_fullscreen_and_exit_restore_reading(page):
    opener = page.locator("[data-dv-page] [data-dv-open]").first
    opener.click()
    fullscreen = page.locator("[data-dv-fullscreen]")
    page.wait_for_function(
        "document.fullscreenElement === document.querySelector('[data-dv-deck]')",
        timeout=5000,
    )
    before = page.evaluate(
        "document.fullscreenElement === document.querySelector('[data-dv-deck]')"
    )
    fullscreen.click()
    page.wait_for_function(
        "expected => (document.fullscreenElement === document.querySelector('[data-dv-deck]')) === expected",
        arg=not before,
        timeout=5000,
    )
    fullscreen.click()
    page.wait_for_function(
        "expected => (document.fullscreenElement === document.querySelector('[data-dv-deck]')) === expected",
        arg=before,
        timeout=5000,
    )
    page.locator("[data-dv-exit]").click()
    expect(page.locator("[data-dv-page]")).to_be_visible()
    expect(page.locator("[data-dv-deck]")).to_be_hidden()
    expect(opener).to_be_focused()
