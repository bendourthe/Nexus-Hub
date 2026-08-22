"""v3.18.3 Phase 4: the structural scorer's slide-mode check family.

Seven checks, gated on `data-nav="slides"` on `<body>`, plus one that runs
UNGATED. Each is exercised twice - once on a clean slide-mode fixture that must
pass, once on a fixture carrying exactly one seeded defect that must be detected
- because a check that has only ever been shown passing is indistinguishable
from a check that cannot fail.

The ungated one earns its own emphasis. `check_slide_record_agreement` runs
whether or not the markup declares slide mode, precisely because the gate itself
can be wrong: a page whose design record says `nav: slides` while the markup
lost its `data-nav` attribute would skip every other check in the family and
score a clean pass. That is a strictly worse outcome than having no checks at
all, so the disagreement is the finding.

The scroll-mode fixtures prove the other half of the contract: a scrolling page
SKIPS these checks (one `n/a` finding) rather than failing them, and a page with
no `nav` field at all is treated as scroll mode - the backward-compatibility rule
that keeps every page authored before this axis existed out of the failure set.

The scorer is stdlib-only, so this module is dependency-free and is loaded by
path via importlib, matching `test_presentify_visual_qa.py`.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_BUNDLE = (
    _ROOT / "catalog" / "skills" / "specialized-domains" / "document-to-interactive-html"
)
_SCORER_PATH = _BUNDLE / "scripts" / "visual_qa_score.py"
_REFERENCE_PATH = _BUNDLE / "references" / "slide-navigation.md"


def _load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


scorer = _load(_SCORER_PATH, "visual_qa_score_slides")


# A clean slide-mode page: the design record agrees with the markup, two stages
# carry viewport-fitted sizing behind a scroll-locked container, fragments are
# contiguous from 1 within each slide, an ambient loop sits under a
# reduced-motion guard, and the full navigation chrome is present.
_CLEAN_SLIDES = (
    "<html><head><style>"
    "html, body{overflow: hidden;}"
    ".slide-stage{height: 100svh; width: 100svw;}"
    ".slide-ambient{animation: drift 14s linear infinite;}"
    "@media (prefers-reduced-motion: reduce){.slide-ambient{animation: none;}}"
    "</style></head>"
    "<!--\nDESIGN RECORD\nnav: slides (provenance: flag)\n-->"
    '<body data-nav="slides">'
    '<div class="slide-deck">'
    '<section class="slide-stage" id="slide-1"><div class="slide-inner">'
    '<h1>Title</h1><p data-fragment="1">a</p><p data-fragment="2">b</p>'
    "</div></section>"
    '<section class="slide-stage" id="slide-2"><div class="slide-inner">'
    '<div class="slide-ambient"></div><h2>Second</h2><p data-fragment="1">c</p>'
    "</div></section>"
    "</div>"
    '<p class="slide-counter">1 / 2</p><nav class="slide-rail"></nav>'
    '<button class="slide-hit-prev"></button><button class="slide-hit-next"></button>'
    "</body></html>"
)

# A clean scroll-mode page, for the skip-not-fail half of the contract.
_CLEAN_SCROLL = (
    "<html><head><style>.band{padding: 2rem;}</style></head>"
    "<!--\nDESIGN RECORD\nnav: scroll (provenance: defaulted)\n-->"
    "<body><section class='band'><h1>Report</h1></section></body></html>"
)


def _by_criterion(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {f["criterion"]: f for f in result["findings"]}


def _fails(result: dict[str, Any]) -> set[str]:
    return {f["criterion"] for f in result["findings"] if f["status"] == "fail"}


# --- mode detection and the skip-not-fail contract ---------------------------


def test_nav_mode_reads_the_body_attribute() -> None:
    assert scorer.nav_mode(_CLEAN_SLIDES) == "slides"
    assert scorer.nav_mode(_CLEAN_SCROLL) == "scroll"


def test_absent_data_nav_is_scroll_mode_not_an_error() -> None:
    """The backward-compatibility rule: a page from before the axis existed."""
    legacy = "<html><body><h1>Old page</h1></body></html>"
    assert scorer.nav_mode(legacy) == "scroll"
    result = scorer.score_html(legacy)
    assert not any(c.startswith("slide-") for c in _fails(result))


def test_scroll_mode_skips_the_slide_checks_rather_than_failing_them() -> None:
    result = scorer.score_html(_CLEAN_SCROLL)
    findings = _by_criterion(result)
    assert findings["slide-mode"]["status"] == "n/a"
    assert "slide-structure" not in findings
    assert not _fails(result) & {
        "slide-structure", "slide-fit", "slide-fragments",
        "slide-scroll-keyed", "slide-ambient", "slide-chrome",
    }


def test_scroll_mode_page_may_keep_its_scroll_listeners() -> None:
    """The check is gated, so a scrolling page's scroll listener is not a defect."""
    scrolly = _CLEAN_SCROLL.replace(
        "</body>", "<script>window.addEventListener('scroll', function(){});</script></body>"
    )
    assert "slide-scroll-keyed" not in _fails(scorer.score_html(scrolly))


def test_clean_slide_page_raises_no_slide_finding() -> None:
    result = scorer.score_html(_CLEAN_SLIDES)
    assert result["nav"] == "slides"
    assert not any(c.startswith("slide-") for c in _fails(result))


# --- check 7 (ungated): the design record agrees with the markup -------------


def test_record_says_slides_but_markup_lost_the_attribute_fails_closed() -> None:
    """The fail-open shape this check exists to prevent.

    Without it, the missing attribute would skip every other slide check and the
    page would score clean while being, by its own record, a broken deck.
    """
    lost = _CLEAN_SLIDES.replace('<body data-nav="slides">', "<body>")
    result = scorer.score_html(lost)
    assert "slide-record" in _fails(result)
    assert result["page_pass"] is False


def test_markup_says_slides_but_record_says_scroll_is_flagged() -> None:
    mismatch = _CLEAN_SLIDES.replace("nav: slides (provenance: flag)", "nav: scroll")
    assert "slide-record" in _fails(scorer.score_html(mismatch))


def test_slide_markup_with_no_record_nav_field_is_flagged() -> None:
    silent = _CLEAN_SLIDES.replace("nav: slides (provenance: flag)", "aspect: full")
    assert "slide-record" in _fails(scorer.score_html(silent))


def test_scroll_page_with_no_record_nav_field_is_not_flagged() -> None:
    legacy = _CLEAN_SCROLL.replace("nav: scroll (provenance: defaulted)", "aspect: standard")
    result = scorer.score_html(legacy)
    assert _by_criterion(result)["slide-record"]["status"] == "n/a"
    assert "slide-record" not in _fails(result)


# --- check 1: containers exist and classes are component-prefixed ------------


def test_slides_mode_with_no_stages_fails_with_a_named_reason() -> None:
    """A deck with no slides: a hard failure, not a crash and not a silent pass."""
    empty = _CLEAN_SLIDES.replace('class="slide-stage"', 'class="band"')
    result = scorer.score_html(empty)
    assert "slide-structure" in _fails(result)
    assert "no .slide-stage" in _by_criterion(result)["slide-structure"]["evidence"]


def test_bare_generic_class_selector_is_flagged() -> None:
    bare = _CLEAN_SLIDES.replace(".slide-stage{height", ".stage{height").replace(
        'class="slide-stage"', 'class="slide-stage stage"'
    )
    assert "slide-structure" in _fails(scorer.score_html(bare))


# --- check 2: page scroll disabled, stages viewport-fitted -------------------


def test_page_that_still_scrolls_is_flagged() -> None:
    scrolls = _CLEAN_SLIDES.replace("html, body{overflow: hidden;}", "html, body{margin: 0;}")
    assert "slide-fit" in _fails(scorer.score_html(scrolls))


def test_stage_without_viewport_fitted_height_is_flagged() -> None:
    unsized = _CLEAN_SLIDES.replace(".slide-stage{height: 100svh; width: 100svw;}",
                                    ".slide-stage{height: 800px;}")
    assert "slide-fit" in _fails(scorer.score_html(unsized))


# --- check 3: fragment indices positive, unique, contiguous from 1 -----------


def test_non_contiguous_fragment_indices_are_flagged_with_the_slide() -> None:
    gap = _CLEAN_SLIDES.replace('data-fragment="2"', 'data-fragment="3"')
    result = scorer.score_html(gap)
    assert "slide-fragments" in _fails(result)
    assert "slide 1" in _by_criterion(result)["slide-fragments"]["evidence"]


def test_non_positive_fragment_index_is_flagged() -> None:
    zero = _CLEAN_SLIDES.replace('data-fragment="1"', 'data-fragment="0"', 1)
    assert "slide-fragments" in _fails(scorer.score_html(zero))


def test_malformed_fragment_value_is_reported_not_raised() -> None:
    """Malformed input is a finding, never an unhandled exception."""
    malformed = _CLEAN_SLIDES.replace('data-fragment="2"', 'data-fragment="two"')
    result = scorer.score_html(malformed)
    assert "slide-fragments" in _fails(result)
    assert "non-numeric" in _by_criterion(result)["slide-fragments"]["evidence"]


def test_each_slide_numbers_its_own_fragments_from_1() -> None:
    """Two slides both starting at 1 is correct, not a duplicate-index defect."""
    assert "slide-fragments" not in _fails(scorer.score_html(_CLEAN_SLIDES))


# --- check 4: no scroll-keyed animation survives -----------------------------


def test_global_scroll_listener_in_a_slides_page_is_flagged() -> None:
    keyed = _CLEAN_SLIDES.replace(
        "</body>", "<script>window.addEventListener('scroll', function(){});</script></body>"
    )
    assert "slide-scroll-keyed" in _fails(scorer.score_html(keyed))


def test_element_scoped_scroll_listener_is_allowed() -> None:
    """A declared scrollable region (a long table) legitimately scrolls."""
    region = _CLEAN_SLIDES.replace(
        "</body>",
        "<script>var scrollable = document.querySelector('.slide-scrollable');"
        "scrollable.addEventListener('scroll', function(){});</script></body>",
    )
    assert "slide-scroll-keyed" not in _fails(scorer.score_html(region))


def test_intersection_observer_reveal_is_flagged() -> None:
    io_reveal = _CLEAN_SLIDES.replace(
        "</body>",
        "<script>new IntersectionObserver(function(es){"
        "es.forEach(function(e){e.target.classList.add('on');});});</script></body>",
    )
    assert "slide-scroll-keyed" in _fails(scorer.score_html(io_reveal))


def test_intersection_observer_without_a_class_toggle_is_not_flagged() -> None:
    """Lazy-loading is not a scroll-triggered reveal; the check must not cry wolf."""
    lazy = _CLEAN_SLIDES.replace(
        "</body>",
        "<script>new IntersectionObserver(function(es){"
        "es.forEach(function(e){ e.target.src = e.target.dataset.src; });});</script></body>",
    )
    assert "slide-scroll-keyed" not in _fails(scorer.score_html(lazy))


def test_scroll_driven_animation_timeline_is_flagged() -> None:
    timeline = _CLEAN_SLIDES.replace(
        ".slide-stage{height", ".slide-reveal{animation-timeline: scroll();}\n.slide-stage{height"
    )
    assert "slide-scroll-keyed" in _fails(scorer.score_html(timeline))


# --- check 5: ambient loops carry a reduced-motion guard ---------------------


def test_unguarded_infinite_animation_is_flagged() -> None:
    unguarded = _CLEAN_SLIDES.replace(
        "@media (prefers-reduced-motion: reduce){.slide-ambient{animation: none;}}", ""
    )
    assert "slide-ambient" in _fails(scorer.score_html(unguarded))


def test_reduced_motion_block_that_does_not_touch_animation_is_flagged() -> None:
    """A guard that only changes transitions leaves the loop running."""
    wrong_guard = _CLEAN_SLIDES.replace(
        "@media (prefers-reduced-motion: reduce){.slide-ambient{animation: none;}}",
        "@media (prefers-reduced-motion: reduce){.slide-stage{transition: none;}}",
    )
    assert "slide-ambient" in _fails(scorer.score_html(wrong_guard))


def test_page_with_no_ambient_animation_is_not_applicable() -> None:
    none_declared = _CLEAN_SLIDES.replace(
        ".slide-ambient{animation: drift 14s linear infinite;}", ""
    )
    result = scorer.score_html(none_declared)
    assert _by_criterion(result)["slide-ambient"]["status"] == "n/a"


# --- check 6: navigation chrome present --------------------------------------


def test_missing_navigation_chrome_is_flagged_by_name() -> None:
    no_rail = _CLEAN_SLIDES.replace('<nav class="slide-rail"></nav>', "")
    result = scorer.score_html(no_rail)
    assert "slide-chrome" in _fails(result)
    assert "progress rail" in _by_criterion(result)["slide-chrome"]["evidence"]


def test_missing_hit_zones_are_flagged() -> None:
    no_zones = _CLEAN_SLIDES.replace('<button class="slide-hit-prev"></button>', "").replace(
        '<button class="slide-hit-next"></button>', ""
    )
    result = scorer.score_html(no_zones)
    assert "slide-chrome" in _fails(result)
    assert "hit zone" in _by_criterion(result)["slide-chrome"]["evidence"]


# --- malformed input is a finding, never an exception ------------------------


@pytest.mark.parametrize(
    "label,html",
    [
        ("empty document", ""),
        ("not html at all", "just text"),
        ("unclosed stage", '<body data-nav="slides"><section class="slide-stage">'),
        (
            "nested stages",
            '<body data-nav="slides"><section class="slide-stage">'
            '<section class="slide-stage"></section></section></body>',
        ),
        ("padded / uppercased nav value", '<body data-nav="SLIDES  ">x</body>'),
        (
            "empty fragment value",
            '<body data-nav="slides"><section class="slide-stage">'
            '<p data-fragment=""></p></section></body>',
        ),
        (
            "negative fragment index",
            '<body data-nav="slides"><section class="slide-stage">'
            '<p data-fragment="-3"></p></section></body>',
        ),
        ("unterminated style block", '<style>.slide-stage{height:100svh;<body data-nav="slides">'),
        (
            "unterminated media query",
            "<style>@media (prefers-reduced-motion: reduce){.a{animation:none;</style>"
            '<body data-nav="slides"><section class="slide-stage" '
            'style="animation: x 1s infinite"></section></body>',
        ),
    ],
)
def test_malformed_input_is_scored_never_raised(label: str, html: str) -> None:
    """One aggregate over the malformed shapes: a finding, never a traceback.

    A scorer that crashes on a broken page is worse than one that misses a
    defect - the loop cannot grade anything at all, and the failure looks like
    tooling breakage rather than a page problem.
    """
    result = scorer.score_html(html)
    assert isinstance(result["findings"], list), label
    assert result["nav"] in ("slides", "scroll"), label


def test_padded_nav_value_still_resolves_to_slide_mode() -> None:
    assert scorer.nav_mode('<body data-nav="  SLIDES ">x</body>') == "slides"


# --- the reference documents what the scorer enforces ------------------------


def test_reference_documents_the_data_nav_hook_the_scorer_keys_on() -> None:
    text = _REFERENCE_PATH.read_text(encoding="utf-8")
    assert 'data-nav="slides"' in text
    assert "slide-stage" in text and "slide-rail" in text and "slide-counter" in text
