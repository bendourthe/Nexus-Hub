"""v3.15.4 Phase 5: iterative multi-agent visual-QA self-critique loop.

Two testable surfaces:

1. The deterministic STRUCTURAL scorer (`scripts/visual_qa_score.py`) flags a
   seeded defective fixture on each structural criterion (narrow full-width
   column, missing image caps, a dropped annotation overlay, a consented mix run
   with zero imagery, a non-offline page) and passes a clean fixture. It also
   degrades cleanly (structural mode, no browser needed) and drives the CLI exit
   codes.

1b. (v3.16.5) The four `references/responsive-typography.md` checks: fluid macro
   spacing, the rendered font-size floors (checked at BOTH the clamp minimum and
   1920px), emphasis-token distinctness, and WCAG contrast. Each is exercised on a
   clean fluid fixture plus one fixture per seeded defect class, including the
   near-miss cases that make the checks trustworthy rather than noisy: micro
   spacing is not flagged, SVG user-unit text is exempt from the px floors, a
   region-scoped `footer code` rule does not stand in for the page-wide one, and
   semantic status colors stay out of the contrast set.

2. The Dynamic-Workflow template (`assets/visual-qa-workflow.js`) and the rubric
   reference carry the required content: the three mandatory workflow rules
   (graceful degradation, scope-first token caution, skill-native) and the five
   rubric criteria. The template is an adapt-me artifact (not executed here), so
   these are structural assertions on the files.

The scorer is stdlib-only, so these tests are dependency-free (they run in both
the deps-light ci.yml tests job and the presentify-extractor workflow). The
scorer is loaded by path via importlib, matching test_media_key_setup.py.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_BUNDLE = (
    _ROOT / "catalog" / "skills" / "specialized-domains" / "document-to-interactive-html"
)
_SCORER_PATH = _BUNDLE / "scripts" / "visual_qa_score.py"
_WORKFLOW_PATH = _BUNDLE / "assets" / "visual-qa-workflow.js"
_RUBRIC_PATH = _BUNDLE / "references" / "visual-qa-rubric.md"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


scorer = _load(_SCORER_PATH, "visual_qa_score")

# A clean full-width page: canvas vars filling the viewport, the image caps, an
# annotated overlay with a region + view-original toggle, and an embedded image.
_CLEAN = (
    '<html data-aspect="full">'
    "<style>:root{--page-max: 100%; --gutter: clamp(1rem, 2vw, 2rem);}"
    " figure img{max-height: 80vh; object-fit: contain;}</style>"
    '<figure class="fig-annotated"><div class="fig-figure">'
    '<img src="data:image/png;base64,AAAA">'
    '<div class="fig-overlay"><div class="fig-region">North</div></div></div>'
    '<label class="fig-view-original">View original</label></figure>'
    "</html>"
)


def _fails(result: dict) -> set[str]:
    return {f["criterion"] for f in result["findings"] if f["status"] == "fail"}


# --- 1. structural scorer: clean passes, each seeded defect is flagged --------


def test_scorer_clean_page_passes():
    result = scorer.score_html(_CLEAN, expect_images=1)
    assert result["page_pass"] is True
    assert result["high_severity"] == 0
    assert result["mode"] == "structural"


def test_scorer_flags_narrow_full_width():
    narrow = _CLEAN.replace("--page-max: 100%", "--page-max: 600px")
    result = scorer.score_html(narrow)
    assert result["page_pass"] is False
    assert "full-width" in _fails(result)


def test_scorer_flags_missing_image_caps():
    nocaps = (
        '<html data-aspect="standard"><figure>'
        '<img src="data:image/png;base64,AAAA"></figure></html>'
    )
    result = scorer.score_html(nocaps)
    assert result["page_pass"] is False
    assert "image-sizing" in _fails(result)


def test_scorer_flags_dropped_overlay():
    dropped = (
        '<html data-aspect="standard"><style>figure img{max-height: 80vh;'
        " object-fit: contain;}</style>"
        '<figure class="fig-annotated"></figure></html>'
    )
    result = scorer.score_html(dropped)
    assert result["page_pass"] is False
    assert "annotation-fidelity" in _fails(result)


def test_scorer_flags_zero_imagery_on_consented_expectation():
    text_only = '<html data-aspect="standard"><p>text only</p></html>'
    result = scorer.score_html(text_only, expect_images=1)
    assert result["page_pass"] is False
    assert "imagery-integration" in _fails(result)


def test_scorer_flags_external_reference():
    not_offline = (
        '<html data-aspect="standard"><style>figure img{max-height: 80vh;'
        ' object-fit: contain;}</style>'
        '<link rel="stylesheet" href="https://cdn.example.com/x.css">'
        '<img src="data:image/png;base64,AAAA"></html>'
    )
    result = scorer.score_html(not_offline)
    assert result["page_pass"] is False
    assert "readability-layout" in _fails(result)


def test_scorer_na_criteria_do_not_block():
    # Standard aspect, no figures, no imagery expectation: the applicable
    # criteria are n/a and the page passes structurally.
    minimal = "<html data-aspect=\"standard\"><p>Just prose.</p></html>"
    result = scorer.score_html(minimal)
    assert result["page_pass"] is True
    statuses = {f["criterion"]: f["status"] for f in result["findings"]}
    assert statuses["full-width"] == "n/a"
    assert statuses["image-sizing"] == "n/a"
    assert statuses["imagery-integration"] == "n/a"


def test_scorer_cli_exit_codes(tmp_path):
    clean = tmp_path / "clean.html"
    clean.write_text(_CLEAN, encoding="utf-8")
    assert scorer.main([str(clean), "--expect-images", "1"]) == 0

    defect = tmp_path / "defect.html"
    defect.write_text(_CLEAN.replace("--page-max: 100%", "--page-max: 600px"), encoding="utf-8")
    assert scorer.main([str(defect)]) == 1

    assert scorer.main([str(tmp_path / "missing.html")]) == 2


# --- 1b. v3.16.5: the responsive-typography contract checks ------------------
#
# A clean fluid/readable page: a tokenized type scale whose clamp MINIMUMS sit at
# the role floors, fluid macro spacing, an AA-clearing palette, and an
# unqualified `code` rule distinct on both the color and the family axis.
_FLUID = (
    '<html data-aspect="standard"><style>'
    ":root{"
    "--base:#12141a; --surface:#1d212b; --ink:#f2f4f8; --ink-dim:#c3c9d6;"
    "--accent:#8fb6e8;"
    "--step--2: clamp(0.8125rem, 0.78rem + 0.16vw, 0.9375rem);"
    "--step-0: clamp(1rem, 0.94rem + 0.30vw, 1.1875rem);"
    "--gutter: clamp(1.25rem, 4vw, 2.5rem);"
    "}"
    "body{font-size:var(--step-0); color:var(--ink); background:var(--base)}"
    ".band{padding-inline:var(--gutter); padding-block:clamp(3.5rem,7vh,7rem)}"
    ".editorial{display:grid; gap:clamp(1.25rem,3vw,3.5rem)}"
    "footer b{font-size:var(--step--2)}"
    "code{font-family:Consolas,monospace; color:var(--accent)}"
    "</style><p>Prose with a <code>/review</code> token.</p></html>"
)


def test_scorer_clean_fluid_page_passes_all_typography_checks():
    result = scorer.score_html(_FLUID)
    statuses = {f["criterion"]: f["status"] for f in result["findings"]}
    assert statuses["fluid-spacing"] == "pass"
    assert statuses["font-floor"] == "pass"
    assert statuses["emphasis-token"] == "pass"
    assert statuses["contrast"] == "pass"
    assert result["page_pass"] is True


def test_scorer_flags_fixed_macro_spacing_on_a_band():
    fixed = _FLUID.replace(
        ".editorial{display:grid; gap:clamp(1.25rem,3vw,3.5rem)}",
        ".editorial{display:grid; gap:2rem}",
    )
    result = scorer.score_html(fixed)
    finding = next(f for f in result["findings"] if f["criterion"] == "fluid-spacing")
    assert finding["status"] == "fail"
    # One occurrence is a slip (MEDIUM), not a page-blocking layout failure.
    assert finding["severity"] == "medium"


def test_scorer_escalates_three_fixed_macro_dimensions_to_high():
    fixed = (
        _FLUID.replace(
            ".editorial{display:grid; gap:clamp(1.25rem,3vw,3.5rem)}",
            ".editorial{display:grid; gap:2rem}",
        )
        .replace("padding-inline:var(--gutter)", "padding-inline:40px")
        .replace("padding-block:clamp(3.5rem,7vh,7rem)", "padding-block:3rem")
    )
    result = scorer.score_html(fixed)
    finding = next(f for f in result["findings"] if f["criterion"] == "fluid-spacing")
    assert finding["severity"] == "high"
    assert result["page_pass"] is False


def test_scorer_ignores_component_internal_micro_spacing():
    # A chip's own padding is component-internal and may stay rem-based.
    micro = _FLUID.replace(
        "footer b{font-size:var(--step--2)}",
        "footer b{font-size:var(--step--2)} .chip{padding:.35rem .6rem}",
    )
    finding = next(
        f for f in scorer.score_html(micro)["findings"]
        if f["criterion"] == "fluid-spacing"
    )
    assert finding["status"] == "pass"


def test_scorer_flags_secondary_text_below_the_13px_floor():
    # The v3.16.5 root-cause defect: the fluid clamp sits on body while a child
    # is sized in rem, so it resolves against the 16px ROOT and never scales.
    small = _FLUID.replace("footer b{font-size:var(--step--2)}", "footer b{font-size:.7rem}")
    result = scorer.score_html(small)
    finding = next(f for f in result["findings"] if f["criterion"] == "font-floor")
    assert finding["status"] == "fail"
    assert finding["severity"] == "high"
    assert "11.2px" in finding["evidence"]
    assert result["page_pass"] is False


def test_scorer_checks_the_clamp_minimum_not_only_the_1920px_value():
    # Resolves to 16px at 1920px but bottoms out at 11px on a laptop width, which
    # is the size most readers get. Checking only the wide viewport misses it.
    sneaky = _FLUID.replace(
        "footer b{font-size:var(--step--2)}",
        "footer b{font-size:clamp(0.6875rem, 0.5rem + 0.6vw, 1rem)}",
    )
    finding = next(
        f for f in scorer.score_html(sneaky)["findings"]
        if f["criterion"] == "font-floor"
    )
    assert finding["status"] == "fail"
    assert "11.0px" in finding["evidence"]


def test_scorer_exempts_svg_user_unit_text_from_the_font_floors():
    # SVG text declares its size in viewBox user units, so a px floor is
    # meaningless; the `fill:` declaration is the discriminator.
    svg_text = _FLUID.replace(
        "code{font-family:Consolas,monospace; color:var(--accent)}",
        "code{font-family:Consolas,monospace; color:var(--accent)}"
        " .nlabel{fill:var(--ink-dim); font-size:9px}",
    )
    finding = next(
        f for f in scorer.score_html(svg_text)["findings"]
        if f["criterion"] == "font-floor"
    )
    assert finding["status"] == "pass"


def test_scorer_resolves_step_tokens_instead_of_treating_var_as_opaque():
    # Regression guard against an inverted incentive: if `var(...)` read as
    # opaque, a page that correctly moved its type onto a tokenized scale would
    # be checked LESS than one hardcoding sizes, and a malformed step token would
    # ship silently.
    broken_token = _FLUID.replace(
        "--step--2: clamp(0.8125rem, 0.78rem + 0.16vw, 0.9375rem);",
        "--step--2: 0.6rem;",
    )
    result = scorer.score_html(broken_token)
    finding = next(f for f in result["findings"] if f["criterion"] == "font-floor")
    assert finding["status"] == "fail"
    # The message names the DECLARED token, not just the resolved pixels, so the
    # reader knows which scale step to fix.
    assert "var(--step--2)" in finding["evidence"]
    assert "9.6px" in finding["evidence"]


def test_resolve_var_follows_indirection_and_honors_a_fallback():
    props = {"--a": "var(--b)", "--b": "0.9rem"}
    assert scorer.resolve_var("var(--a)", props) == "0.9rem"
    assert scorer.resolve_var("var(--missing, 1.25rem)", props) == "1.25rem"
    # Undeclared with no fallback stays unresolved rather than silently becoming 0.
    assert scorer.resolve_var("var(--nope)", props) == "var(--nope)"


def test_scorer_flags_indistinguishable_emphasis_tokens():
    muted = _FLUID.replace(
        "code{font-family:Consolas,monospace; color:var(--accent)}",
        "code{font-family:Consolas,monospace}",
    )
    result = scorer.score_html(muted)
    finding = next(f for f in result["findings"] if f["criterion"] == "emphasis-token")
    assert finding["status"] == "fail"
    assert "no color" in finding["evidence"]
    assert result["page_pass"] is False


def test_scorer_does_not_accept_a_region_scoped_token_rule_as_page_wide_proof():
    # `footer code` styles ONE region. Accepting it would pass a page whose
    # page-wide tokens are still invisible - the observed shipping defect.
    scoped = _FLUID.replace(
        "code{font-family:Consolas,monospace; color:var(--accent)}",
        "code{font-family:Consolas,monospace} footer code{color:var(--accent)}",
    )
    finding = next(
        f for f in scorer.score_html(scoped)["findings"]
        if f["criterion"] == "emphasis-token"
    )
    assert finding["status"] == "fail"
    assert "base" in finding["evidence"]


def test_scorer_emphasis_token_is_na_without_token_markup():
    no_tokens = _FLUID.replace("<code>/review</code>", "/review")
    finding = next(
        f for f in scorer.score_html(no_tokens)["findings"]
        if f["criterion"] == "emphasis-token"
    )
    assert finding["status"] == "n/a"


def test_contrast_ratio_matches_the_wcag_reference_values():
    assert scorer.contrast_ratio("#ffffff", "#000000") == 21.0
    assert round(scorer.contrast_ratio("#777777", "#ffffff"), 2) == 4.48
    assert scorer.contrast_ratio("not-a-color", "#000000") is None


def test_scorer_flags_a_foreground_unusable_on_every_background_as_high():
    unusable = _FLUID.replace("--accent:#8fb6e8;", "--accent:#3d4d66;")
    result = scorer.score_html(unusable)
    finding = next(f for f in result["findings"] if f["criterion"] == "contrast")
    assert finding["status"] == "fail"
    assert finding["severity"] == "high"
    assert result["page_pass"] is False


def test_scorer_grades_a_single_failing_surface_as_medium():
    # --ink-dim clears AA on --base but not on the lighter --surface: the color is
    # usable, just not on that one surface.
    partial = _FLUID.replace("--surface:#1d212b;", "--surface:#8d93a3;")
    result = scorer.score_html(partial)
    finding = next(f for f in result["findings"] if f["criterion"] == "contrast")
    assert finding["status"] == "fail"
    assert finding["severity"] == "medium"
    assert result["page_pass"] is True  # MEDIUM alone does not block


def test_scorer_excludes_semantic_status_colors_from_the_contrast_set():
    # A badge color whose applicable floor is 3:1 (large / bordered text) must not
    # be graded against the 4.5:1 body floor, since its rendered size is unknown.
    status = _FLUID.replace("--accent:#8fb6e8;", "--accent:#8fb6e8; --stop:#c25050;")
    finding = next(
        f for f in scorer.score_html(status)["findings"]
        if f["criterion"] == "contrast"
    )
    assert finding["status"] == "pass"


def test_len_px_resolves_additive_clamp_preferred_terms():
    # `0.94rem + 0.30vw` at 1920px = 15.04 + 5.76 = 20.8, clamped to the 19px max.
    assert round(scorer._len_px("clamp(1rem, 0.94rem + 0.30vw, 1.1875rem)", 1920), 2) == 19.0
    assert round(scorer._clamp_min_px("clamp(1rem, 0.94rem + 0.30vw, 1.1875rem)"), 2) == 16.0


def test_css_rules_extracts_media_nested_rules_and_skips_the_prelude():
    rules = scorer.css_rules(
        "<style>@media (max-width:600px){.band{gap:1rem}}</style>"
    )
    assert rules == [(".band", {"gap": "1rem"})]


def test_responsive_typography_reference_states_the_floors_and_rules():
    text = (_BUNDLE / "references" / "responsive-typography.md").read_text(
        encoding="utf-8"
    )
    for anchor in (
        "Fluid space, never fixed space",
        "Wrapping serves the viewport",
        "Fluid type scale defined once",
        "Minimum rendered sizes",
        "Emphasis tokens must be visually distinct",
        "Contrast floors",
    ):
        assert anchor in text, f"contract missing rule: {anchor}"
    # The floors are stated as numbers, not as "small but readable".
    assert "16px" in text and "13px" in text and "12px" in text


# --- 1c. v3.16.5 Phase 2: the svg-diagram-quality contract -------------------
#
# A clean diagram: one marker definition, attached with marker-end, a connector
# terminating on the box edges, and a height-constrained sticky container.
_MARKER = (
    '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"'
    ' markerWidth="6" markerHeight="6" orient="auto" markerUnits="strokeWidth">'
    '<path d="M0 0 L10 5 L0 10 z" fill="currentColor"/></marker></defs>'
)
_SVG_OK = (
    '<html data-aspect="standard"><style>'
    ".rail-sticky{position:sticky;top:5.5rem}"
    ".rail-sticky svg{width:100%;height:auto;max-height:calc(100vh - 7rem)}"
    "</style>"
    '<div class="rail-sticky"><svg viewBox="0 0 300 200">' + _MARKER +
    '<rect x="30" y="14" width="240" height="52"/>'
    '<path class="flow" d="M150 66 L150 96" marker-end="url(#arrow)"/>'
    '<rect x="30" y="96" width="240" height="52"/>'
    "</svg></div></html>"
)


def _svg_finding(html: str, criterion: str) -> dict:
    return next(
        f for f in scorer.score_html(html)["findings"] if f["criterion"] == criterion
    )


def test_scorer_clean_diagram_passes_all_svg_checks():
    result = scorer.score_html(_SVG_OK)
    statuses = {f["criterion"]: f["status"] for f in result["findings"]}
    assert statuses["svg-arrowhead"] == "pass"
    assert statuses["svg-viewport-fit"] == "pass"
    assert statuses["svg-marker-integrity"] == "pass"
    assert result["page_pass"] is True


def test_scorer_flags_a_hand_placed_triangle_arrowhead():
    # The 2026-08-10 defect: a filled triangle sitting near a line end, which
    # detaches from it the moment the geometry moves.
    detached = _SVG_OK.replace(
        '<path class="flow" d="M150 66 L150 96" marker-end="url(#arrow)"/>',
        '<path class="flow" d="M150 66 L150 96"/>'
        '<path d="M150 96 l -4 -8 l 8 0 z" fill="#5a3434"/>',
    )
    finding = _svg_finding(detached, "svg-arrowhead")
    assert finding["status"] == "fail"
    assert finding["severity"] == "high"
    assert "detaches" in finding["evidence"]


def test_scorer_does_not_flag_the_triangle_inside_a_marker_definition():
    # A marker's own arrowhead IS a small filled triangle by design. Flagging it
    # would make the correct construction unusable.
    assert _svg_finding(_SVG_OK, "svg-arrowhead")["status"] == "pass"
    assert "M0 0 L10 5 L0 10 z" in _SVG_OK  # the marker triangle is really there


def test_scorer_flags_inconsistently_applied_arrowheads():
    # A pipeline whose first connector has a head and whose rest do not reads as
    # an unfinished drawing. Medium: the arrows exist, they are just uneven.
    uneven = _SVG_OK.replace(
        '<rect x="30" y="96" width="240" height="52"/>',
        '<rect x="30" y="96" width="240" height="52"/>'
        '<path class="flow" d="M150 148 L150 178"/>',
    )
    finding = _svg_finding(uneven, "svg-arrowhead")
    assert finding["status"] == "fail"
    assert finding["severity"] == "medium"
    assert "inconsistently" in finding["evidence"]


def test_scorer_accepts_a_marker_attached_from_css():
    # A marker does NOT inherit from the element referencing it, so a connector
    # whose stroke changes with state needs a second marker swapped in by CSS.
    # Reading attributes only would report this correct page as headless.
    css_attached = _SVG_OK.replace(
        ".rail-sticky{position:sticky;top:5.5rem}",
        ".rail-sticky{position:sticky;top:5.5rem} .flow{marker-end:url(#arrow)}",
    ).replace(' marker-end="url(#arrow)"', "")
    assert _svg_finding(css_attached, "svg-arrowhead")["status"] == "pass"
    assert _svg_finding(css_attached, "svg-marker-integrity")["status"] == "pass"


def test_scorer_flags_an_unconstrained_svg_in_a_sticky_container():
    unpinned = _SVG_OK.replace(
        ".rail-sticky svg{width:100%;height:auto;max-height:calc(100vh - 7rem)}",
        ".rail-sticky svg{width:100%;height:auto}",
    )
    result = scorer.score_html(unpinned)
    finding = next(
        f for f in result["findings"] if f["criterion"] == "svg-viewport-fit"
    )
    assert finding["status"] == "fail"
    assert finding["severity"] == "high"
    assert "unreachable" in finding["evidence"]
    assert result["page_pass"] is False


def test_scorer_ignores_a_sticky_container_that_holds_no_svg():
    # A sticky page nav or table header is not a pinned graphic.
    nav = (
        '<html data-aspect="standard"><style>#nav{position:sticky;top:0}</style>'
        '<nav id="nav"><a href="#a">A</a></nav>'
        '<svg viewBox="0 0 10 10"><rect x="1" y="1" width="2" height="2"/></svg>'
        "</html>"
    )
    assert _svg_finding(nav, "svg-viewport-fit")["status"] == "pass"


def test_scorer_flags_a_dangling_marker_reference_as_high():
    # A reference to a marker that does not exist renders NO arrowhead, silently.
    dangling = _SVG_OK.replace('marker-end="url(#arrow)"', 'marker-end="url(#nope)"')
    finding = _svg_finding(dangling, "svg-marker-integrity")
    assert finding["status"] == "fail"
    assert finding["severity"] == "high"
    assert "#nope" in finding["evidence"]


def test_scorer_flags_an_unreferenced_marker_as_medium():
    unused = _SVG_OK.replace(' marker-end="url(#arrow)"', "")
    result = scorer.score_html(unused)
    finding = next(
        f for f in result["findings"] if f["criterion"] == "svg-marker-integrity"
    )
    assert finding["status"] == "fail"
    assert finding["severity"] == "medium"
    assert result["page_pass"] is True  # dead definition, not a broken render


def test_parse_svg_refuses_entity_declarations():
    # Hardening without a dependency: the entity-expansion DoS class needs an
    # inline <!ENTITY, so a block carrying one is refused unparsed. stdlib
    # ElementTree does not resolve external entities, so XXE does not apply.
    bomb = (
        '<svg viewBox="0 0 10 10"><!DOCTYPE svg [<!ENTITY a "aaaa">]>'
        "<rect/></svg>"
    )
    assert scorer._parse_svg(bomb) is None
    assert scorer._parse_svg('<svg viewBox="0 0 10 10"><rect/></svg>') is not None


def test_is_small_triangle_discriminates_arrowheads_from_real_shapes():
    assert scorer._is_small_triangle("M96 40 l -5 -8 l 10 0 z") is True
    assert scorer._is_small_triangle("M0 0 L10 5 L0 10 z") is True
    # A large closed triangle is a real shape, not an arrowhead.
    assert scorer._is_small_triangle("M0 0 L200 100 L0 200 z") is False
    # A connector is not closed.
    assert scorer._is_small_triangle("M150 66 L150 96") is False
    # A curve is not a triangle even when small and closed.
    assert scorer._is_small_triangle("M0 0 C 5 5, 8 8, 0 10 z") is False


def test_path_points_tracks_relative_and_absolute_commands():
    commands, points = scorer._path_points("M10 10 l 5 0 L 30 10 v 5 z")
    assert commands == ["M", "L", "L", "V", "Z"]
    assert points == [(10.0, 10.0), (15.0, 10.0), (30.0, 10.0), (30.0, 15.0)]


def test_svg_diagram_quality_reference_states_all_five_rules():
    text = (_BUNDLE / "references" / "svg-diagram-quality.md").read_text(
        encoding="utf-8"
    )
    for anchor in (
        "Arrowheads are `<marker>` elements",
        "Dash patterns must not collide",
        "Connectors terminate on node edges",
        "Viewport fit for pinned and sticky graphics",
        "Geometry self-check before shipping",
    ):
        assert anchor in text, f"contract missing rule: {anchor}"
    # The marker attributes that make a head behave are named, not implied.
    assert 'orient="auto"' in text and 'markerUnits="strokeWidth"' in text


# --- 2. workflow template + rubric carry the required content ----------------


def test_workflow_template_carries_mandatory_rules():
    text = _WORKFLOW_PATH.read_text(encoding="utf-8")
    # A valid Workflow script starts with the meta literal.
    assert "export const meta" in text
    # Rule 1: graceful degradation ladder (workflow + render).
    assert "isolated subagents" in text
    assert "single sequential agent" in text
    assert "visual_qa_score.py" in text  # structural fallback for the render
    # Rule 2: scope-first token caution.
    assert "5-15x" in text
    assert "CALIBRATE" in text or "Calibrate" in text or "calibrate" in text
    # Rule 3: skill-native (no outbound, local render).
    assert "No outbound call" in text or "no outbound" in text.lower()
    assert "LOCAL" in text
    # Cross-links to the orchestration + budget skills.
    assert "[[agent-orchestration-primitives]]" in text
    assert "[[ai-billing-safeguards]]" in text
    # The grade -> verify -> synthesize shape.
    assert "adversarially verify" in text.lower() or "REFUTE" in text


def test_rubric_reference_lists_all_criteria_and_pass_bar():
    text = _RUBRIC_PATH.read_text(encoding="utf-8")
    for criterion in (
        "Full-width compliance",
        "Image sizing",
        "Annotation fidelity",
        "Imagery integration",
        "Readability and layout integrity",
    ):
        assert criterion in text, f"rubric missing criterion: {criterion}"
    assert "page-level pass bar" in text.lower()
    assert "structural" in text.lower() and "agent-vision" in text.lower()
