#!/usr/bin/env python3
"""visual_qa_score.py - deterministic STRUCTURAL scorer for the presentify
visual-QA gate (Phase 5).

Scores a generated presentify `.html` against the STRUCTURAL subset of
`references/visual-qa-rubric.md` - the checks that need no human eye: full-width
band width, the image-sizing caps, annotated-overlay well-formedness, imagery
integration count, layout / offline integrity, and (v3.16.5) the four
deterministic halves of the `references/responsive-typography.md` contract -
fluid macro spacing, rendered font-size floors, emphasis-token distinctness, and
WCAG contrast - plus the three deterministic rules of the
`references/svg-diagram-quality.md` contract: no hand-placed triangle
arrowheads, height-constrained pinned graphics, and marker integrity - and the
three render-surfaced defect classes the v3.16.5 errata added (stacked sticky
layers, anchor targets that land under a sticky nav, clipping command blocks).

All rem- and ch-derived values resolve against the page's ACTUAL root font size,
parsed from its `html` rule. A page that scales its root (the v3.16.5 errata E1
pattern) renders every rem dimension larger than a 16px assumption predicts, so
assuming 16px both under-reports font sizes and under-reports the gutter - which
once turned a real 0.947 band fraction into a passing 0.954.
It is the headless-optional structural-review path the Step 9 loop
degrades to when no browser (or no agent vision) is available, and the target the
Phase 5 tests seed defects against.

The AGENT-VISION criteria (crop of meaningful content, dead space, annotation
placement vs the source, imagery relevance, contrast / legibility) are NOT
scored here; they are the agent's screenshot judgment. A pass from this scorer
is a "structural-only" pass, recorded as such.

LOCAL and OFFLINE by construction: it reads a local file and computes from the
markup / computed CSS, importing no network module and making no request.

Usage:
    python visual_qa_score.py out.html
    python visual_qa_score.py out.html --expect-images 2
    python visual_qa_score.py out.html --aspect full --json

Exit codes:
    0  page passes the structural bar (no HIGH-severity finding).
    1  a HIGH-severity structural finding is open.
    2  usage error (file not found / bad arguments).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

FULL_WIDTH_MIN = 0.95
HERO_CAP = "max-height: 80vh"
OBJECT_FIT = "object-fit: contain"

# --- references/responsive-typography.md thresholds ---------------------------
# At or above this size a padding / gap is MACRO spacing and must be fluid;
# below it the dimension is component-internal and may stay rem-based (rule 1).
MACRO_SPACING_PX = 24.0
# Hard rendered-size floors per text role (rule 4).
_FONT_FLOORS = {"body": 16.0, "secondary": 13.0, "interactive": 12.0}
AA_RATIO = 4.5  # WCAG AA for body and secondary text (rule 6).

_STYLE_RE = re.compile(r"<style[^>]*>(.*?)</style>", re.DOTALL | re.IGNORECASE)
_CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
# Leaf declaration blocks only: `[^{}]` cannot span a nested brace, so an at-rule
# prelude is skipped while the rules nested inside it still match.
_RULE_RE = re.compile(r"([^{}]+)\{([^{}]*)\}")
_MACRO_SPACING_PROPS = frozenset(
    {"gap", "column-gap", "row-gap", "padding", "padding-block", "padding-inline"}
)
_FLUID_RE = re.compile(r"clamp\(|min\(|max\(|\bv[wh]\b|\d+%|var\(", re.IGNORECASE)
_BAND_SELECTOR_RE = re.compile(
    r"band|bleed|\bcols?\b|grid|editorial|rail|shell|container|layout|wrap|"
    r"^section|\bmain\b|gutter",
    re.IGNORECASE,
)
# An interactive ELEMENT being styled directly (the compound starts with a name).
_INTERACTIVE_ELEMENT_RE = re.compile(
    r"^(?:a|button|input|select|textarea|summary|label)\b", re.IGNORECASE
)
# A class/id naming an interactive COMPONENT. Deliberately excludes bare `label`
# and `nav`: `.label` is usually a static caption, and `#nav .brand` is a label
# inside a nav rather than a control.
_INTERACTIVE_CLASS_RE = re.compile(
    r"btn|chip|\btab\b|ctl|toggle|control|nav-link|menu-item", re.IGNORECASE
)
_VAR_RE = re.compile(r"var\(\s*(--[a-z0-9_-]+)\s*(?:,([^()]*))?\)", re.IGNORECASE)
_TOKEN_MARKUP_RE = re.compile(r"<(?:code|kbd|samp)\b", re.IGNORECASE)
_TOKEN_SELECTOR_RE = re.compile(r"\b(?:code|kbd|samp)\b|\.token", re.IGNORECASE)
# A token color that merely restates the body ink is not a distinguishing step.
_BODY_INK_RE = re.compile(r"--ink\)|--text\)|--fg\)|\bcurrentcolor\b", re.IGNORECASE)
_FG_NAME_RE = re.compile(r"ink|text|fg|accent|foreground", re.IGNORECASE)
_BG_NAME_RE = re.compile(r"base|^bg|background|surface|paper|canvas", re.IGNORECASE)
_NON_TEXT_NAME_RE = re.compile(
    r"rule|border|line|shadow|divider|outline|ring", re.IGNORECASE
)
_STATUS_NAME_RE = re.compile(
    r"\b(?:ok|warn|stop|err|error|success|info|danger|caution)\b", re.IGNORECASE
)

# --- references/svg-diagram-quality.md ----------------------------------------
_SVG_BLOCK_RE = re.compile(r"<svg\b.*?</svg>", re.DOTALL | re.IGNORECASE)
# Entity / DOCTYPE declarations are refused before parsing; see _parse_svg.
_XML_DECL_GUARD_RE = re.compile(r"<!(?:DOCTYPE|ENTITY)\b", re.IGNORECASE)
_PATH_CMD_RE = re.compile(r"([MmLlHhVvCcSsQqTtAaZz])([^MmLlHhVvCcSsQqTtAaZz]*)")
_NUMBER_RE = re.compile(r"-?\d*\.?\d+(?:[eE][-+]?\d+)?")
_URL_REF_RE = re.compile(r"url\(\s*#([^)\s]+)\s*\)", re.IGNORECASE)
_SELECTOR_TOKEN_RE = re.compile(r"[.#]([A-Za-z][\w-]*)")
# --- Phase 6 cinematic stage --------------------------------------------------
# An <img> carrying a data: URI that is NOT a cinematic stage layer, i.e. a real
# figure the Phase 2 caps apply to. A stage layer is decorative and uses
# object-fit: cover by design, so the figure caps do not apply to it.
_NON_STAGE_IMG_RE = re.compile(
    r'''<img(?![^>]*\bss-layer\b)[^>]*src\s*=\s*["']data:image''', re.IGNORECASE
)
# --- Phase 5 imagery placement -----------------------------------------------
_PLACEMENT_RE = re.compile(r"^\s*placement:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
_PLACEMENT_ROLES = frozenset({"hero", "header", "hero/header", "background",
                             "contextual", "contextual illustration", "gallery"})
_IN_PAGE_ANCHOR_RE = re.compile(r'''<a\b[^>]*href\s*=\s*["']#[^"']+["']''', re.IGNORECASE)
_INLINE_STYLE_RE = re.compile(r'''\bstyle\s*=\s*["']([^"']*)["']''', re.IGNORECASE)

_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_PAGE_MAX_RE = re.compile(r"--page-max:\s*([^;]+);")
_GUTTER_RE = re.compile(r"--gutter:\s*([^;]+);")
_ASPECT_RE = re.compile(r'data-aspect="([^"]*)"')
_ZOOM_RE = re.compile(r"\bzoom:\s*[0-9]")
# Off-host fetch constructs (mirror build_presentation.assert_no_external).
_FETCH_RE = [
    re.compile(
        r"""\b(?:src|href|poster|cite|action|formaction|xlink:href)\s*"""
        r"""=\s*["']?\s*(?:https?:)?//""",
        re.IGNORECASE,
    ),
    re.compile(r"@import\b", re.IGNORECASE),
    re.compile(r"""url\(\s*["']?\s*(?:https?:)?//""", re.IGNORECASE),
    re.compile(r"""<link\b[^>]*\brel\s*=\s*["']?stylesheet""", re.IGNORECASE),
    re.compile(r"<script\b[^>]*\bsrc\s*=", re.IGNORECASE),
]


def _len_px(token: str, viewport: int, root_font: float = 16.0) -> float:
    """Resolve a simple CSS length (px / rem / em / vw / vh / %), an additive sum
    (`0.94rem + 0.3vw`, as used inside a clamp preferred term), or a clamp() to
    pixels. `em` is resolved against `root_font` (callers that care about the true
    inherited size must reject `em` before calling)."""
    token = token.strip()
    if token.startswith("clamp(") and token.endswith(")"):
        low, pref, high = (
            _len_px(part, viewport, root_font)
            for part in _split_top_level(token[len("clamp(") : -1], ",")
        )
        return max(low, min(pref, high))
    # min() / max() over comma-separated lengths. `max(.92em, 0.8125rem)` is the
    # idiomatic way to floor a relative size, so a checker that cannot read it
    # would fail the very construction the contract asks authors to use.
    for name, reducer in (("min(", min), ("max(", max)):
        if token.startswith(name) and token.endswith(")"):
            return reducer(
                _len_px(part, viewport, root_font)
                for part in _split_top_level(token[len(name) : -1], ",")
            )
    # An additive preferred term such as `0.94rem + 0.3vw`; CSS allows the bare
    # sum inside clamp()/min()/max() without a calc() wrapper.
    parts = _split_top_level(token, "+")
    if len(parts) > 1:
        return sum(_len_px(part, viewport, root_font) for part in parts)
    for suffix, factor in (
        ("px", 1.0),
        ("rem", root_font),
        ("em", root_font),
        ("vw", viewport / 100.0),
        ("vh", viewport / 100.0),
        ("%", viewport / 100.0),
    ):
        if token.endswith(suffix):
            try:
                return float(token[: -len(suffix)]) * factor
            except ValueError:
                return 0.0
    try:
        return float(token)
    except ValueError:
        return 0.0


def _split_top_level(text: str, sep: str) -> list[str]:
    """Split on `sep` at paren depth 0, so nested clamp()/min()/var() survive."""
    parts: list[str] = []
    depth = 0
    current = ""
    for char in text:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        if char == sep and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += char
    parts.append(current)
    return [part.strip() for part in parts if part.strip()]


def _clamp_min_px(token: str, root_font: float = 16.0) -> float:
    """The LOWER bound of a clamp(), or the plain resolved length. On a common
    laptop width the clamp is usually still pinned at its minimum, so the minimum
    is the size most readers actually get - which is why the font floors are
    checked here as well as at 1920px."""
    token = token.strip()
    if token.startswith("clamp(") and token.endswith(")"):
        parts = _split_top_level(token[len("clamp(") : -1], ",")
        if parts:
            return _len_px(parts[0], 1920, root_font)
    return _len_px(token, 1920, root_font)


def band_fraction(html: str, viewport: int = 1920) -> float | None:
    """Heuristic widest-content-band fraction from the injected `--page-max` /
    `--gutter` canvas vars, or None when they are absent.

    The gutter is resolved against the SCALED root (E3). With E1 root scaling the
    real gutter at 1920px is ~51px rather than 44px, so assuming 16px inflated
    the content band and reported a marginal failure as a pass.
    """
    page_max_match = _PAGE_MAX_RE.search(html)
    gutter_match = _GUTTER_RE.search(html)
    if not page_max_match or not gutter_match:
        return None
    root_at_viewport, _, _ = root_font_px(css_rules(html), viewport)
    gutter = _len_px(gutter_match.group(1), viewport, root_at_viewport)
    available = viewport - 2 * gutter
    page_max = page_max_match.group(1).strip()
    if page_max == "100%":
        band = available
    else:
        band = min(_len_px(page_max, viewport), available)
    return band / viewport


def _finding(
    criterion: str,
    status: str,
    kind: str,
    evidence: str,
    severity: str | None = None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "segment": "page (structural)",
        "criterion": criterion,
        "status": status,
        "kind": kind,
        "evidence": evidence,
    }
    if severity:
        entry["severity"] = severity
    return entry


def inline_style_rules(html: str) -> list[tuple[str, dict[str, str]]]:
    """Declarations from `style="..."` attributes, as pseudo-rules.

    A CSS-rule parser cannot see an inline style, so a size declared there is
    graded by nothing. That is not hypothetical: an inline
    `style="font-size:.72rem"` rendered at 11.52px on every viewport of this
    repo's own calibration fixture while the font-floor check reported all 40
    declared sizes clean, and only a real render caught it. The selector is
    synthesized as `[style] #N` so findings still name a locatable element.
    """
    rules: list[tuple[str, dict[str, str]]] = []
    for index, body in enumerate(_INLINE_STYLE_RE.findall(html)):
        decls: dict[str, str] = {}
        for decl in body.split(";"):
            if ":" not in decl:
                continue
            prop, _, value = decl.partition(":")
            decls[prop.strip().lower()] = value.strip()
        if decls:
            rules.append((f"[style] #{index + 1}", decls))
    return rules


def css_rules(html: str) -> list[tuple[str, dict[str, str]]]:
    """Extract `(selector, {property: value})` for every LEAF CSS rule in the
    document's `<style>` blocks.

    The regex matches only declaration blocks that contain no nested brace, so an
    at-rule prelude (`@media (...)`) is skipped while the rules inside it are
    still returned. Consequence, and a deliberate limitation: a media-scoped rule
    is graded as if unconditional. That errs toward reporting - a small font
    declared only under a narrow breakpoint is still a small font - and is noted
    rather than corrected, because resolving cascade + breakpoints statically is
    the job of the real render (Step 9), not of this heuristic.
    """
    rules: list[tuple[str, dict[str, str]]] = []
    for style in _STYLE_RE.findall(html):
        css = _CSS_COMMENT_RE.sub("", style)
        for selector, body in _RULE_RE.findall(css):
            selector = " ".join(selector.split())
            if not selector or selector.startswith("@"):
                continue
            decls: dict[str, str] = {}
            for decl in body.split(";"):
                if ":" not in decl:
                    continue
                prop, _, value = decl.partition(":")
                decls[prop.strip().lower()] = value.strip()
            if decls:
                rules.append((selector, decls))
    return rules


def _hex_to_rgb(value: str) -> tuple[int, int, int] | None:
    digits = value.lstrip("#")
    if len(digits) == 3:
        digits = "".join(char * 2 for char in digits)
    if len(digits) == 8:  # #rrggbbaa - alpha ignored (the pair is graded opaque)
        digits = digits[:6]
    if len(digits) != 6:
        return None
    try:
        return tuple(int(digits[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]
    except ValueError:
        return None


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    """WCAG 2.x relative luminance."""
    channels = []
    for raw in rgb:
        srgb = raw / 255.0
        channels.append(
            srgb / 12.92 if srgb <= 0.04045 else ((srgb + 0.055) / 1.055) ** 2.4
        )
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ratio(fg: str, bg: str) -> float | None:
    """WCAG contrast ratio between two hex colors, or None if either is unparsable."""
    fg_rgb, bg_rgb = _hex_to_rgb(fg), _hex_to_rgb(bg)
    if fg_rgb is None or bg_rgb is None:
        return None
    lighter, darker = sorted(
        (_relative_luminance(fg_rgb), _relative_luminance(bg_rgb)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def check_fluid_spacing(rules: list[tuple[str, dict[str, str]]]) -> dict[str, Any]:
    """Rule 1: macro spacing on a band / grid container must be viewport-fluid.

    When the ROOT font-size is itself fluid (E1), a rem-based macro dimension
    scales with the window and therefore SATISFIES this rule - `2.5rem` of band
    padding is 40px at a 16px root and 64px at a 25.6px one. Flagging it would
    penalise the very technique E1 prescribes, so rem counts as fluid exactly
    when the root is.
    """
    _, _, root_is_fluid = root_font_px(rules)
    offenders: list[str] = []
    for selector, decls in rules:
        if not _BAND_SELECTOR_RE.search(selector):
            continue
        for prop, value in decls.items():
            if prop not in _MACRO_SPACING_PROPS:
                continue
            if _FLUID_RE.search(value):
                continue
            if root_is_fluid and "rem" in value:
                continue
            sizes = [_len_px(token, 1920) for token in value.split()]
            if sizes and max(sizes) >= MACRO_SPACING_PX:
                offenders.append(f"{selector} {{{prop}: {value}}}")
    if not offenders:
        return _finding(
            "fluid-spacing", "pass", "structural",
            "no fixed macro spacing on a band / grid container",
        )
    severity = "high" if len(offenders) > 2 else "medium"
    return _finding(
        "fluid-spacing", "fail", "structural",
        f"{len(offenders)} fixed macro spacing declaration(s) "
        f"(>= {MACRO_SPACING_PX:.0f}px, no clamp/vw/vh): " + "; ".join(offenders[:5]),
        severity,
    )


def root_font_px(
    rules: list[tuple[str, dict[str, str]]], viewport: int = 1920
) -> tuple[float, float, bool]:
    """The root font-size as `(at_viewport, at_its_clamp_minimum, is_fluid)`.

    E1 puts the viewport-proportional scaling on the ROOT
    (`html{font-size:clamp(1rem, 0.5vw + 0.55rem, 1.6rem)}`), so every rem- and
    ch-derived dimension on the page scales with the window. A checker that
    assumes 16px therefore misreads the whole page: it under-reports rendered
    font sizes and under-reports the gutter, which is how a 0.947 band fraction
    presented as a passing 0.954.

    The clamp MINIMUM is returned alongside because root scaling does nothing
    below it - at 1366px this fixture's root is pinned at 16px, so that is where
    the readability floors actually bite.
    """
    declared: str | None = None
    for selector, decls in rules:
        parts = [part.strip().lower() for part in selector.split(",")]
        if any(part in ("html", ":root") for part in parts) and "font-size" in decls:
            declared = decls["font-size"]
    if declared is None:
        return 16.0, 16.0, False
    at_viewport = _len_px(declared, viewport, 16)
    at_minimum = _clamp_min_px(declared, 16)
    is_fluid = bool(_FLUID_RE.search(declared))
    return (at_viewport or 16.0), (at_minimum or 16.0), is_fluid


def custom_properties(rules: list[tuple[str, dict[str, str]]]) -> dict[str, str]:
    """Every declared `--name: value` custom property, first declaration winning."""
    props: dict[str, str] = {}
    for _selector, decls in rules:
        for prop, value in decls.items():
            if prop.startswith("--"):
                props.setdefault(prop, value)
    return props


def resolve_var(value: str, props: dict[str, str], depth: int = 4) -> str:
    """Substitute `var(--name[, fallback])` from the declared custom properties.

    Without this, a page that correctly moves its type onto a tokenized scale
    would be checked LESS than one hardcoding sizes, because every `var(...)`
    would read as opaque - so a malformed `--step--2: 0.6rem` would pass silently.
    """
    for _ in range(depth):
        match = _VAR_RE.search(value)
        if match is None:
            return value
        name = match.group(1).strip()
        fallback = (match.group(2) or "").strip()
        replacement = props.get(name, fallback)
        if not replacement:
            return value  # undeclared and no fallback: leave it unresolvable
        value = value[: match.start()] + replacement + value[match.end() :]
    return value


def _font_role(selector: str) -> str:
    """Classify a font-size rule's text role: body prose, interactive, or secondary.

    The interactive test reads only the LAST compound of each selector - the thing
    actually being styled - and distinguishes an ELEMENT name from a CLASS name.
    Matching any token anywhere was wrong in both directions: `#nav .brand` styles
    a non-interactive brand label but contains `nav`, and `.cmd-bar .label` styles
    a static caption whose class is literally `label`. Both were graded against the
    12px interactive floor instead of the 13px secondary floor, and both shipped
    below 13px until a real render measured them.
    """
    if selector.startswith("[style]"):
        return "secondary"
    parts = [part.strip().lower() for part in selector.split(",")]
    if any(part in ("body", "html", "p") for part in parts):
        return "body"
    for part in parts:
        compound = re.split(r"[\s>+~]+", part)[-1]
        compound = re.sub(r"::?[a-z-]+(\([^)]*\))?", "", compound)
        if compound.startswith((".", "#")):
            if _INTERACTIVE_CLASS_RE.search(compound):
                return "interactive"
        elif _INTERACTIVE_ELEMENT_RE.match(compound):
            return "interactive"
    return "secondary"


def check_font_floor(
    rules: list[tuple[str, dict[str, str]]],
    viewport: int = 1920,
    inline: list[tuple[str, dict[str, str]]] | None = None,
) -> dict[str, Any]:
    """Rule 4: every font-size clears its role floor at BOTH the clamp minimum and
    the resolved value at `viewport`, including sizes declared in inline
    `style="..."` attributes (which no CSS-rule parser can see)."""
    inline = inline or []
    props = custom_properties(rules)
    root_at_viewport, root_at_minimum, _ = root_font_px(rules, viewport)
    offenders: list[str] = []
    checked = 0
    for selector, decls in rules + inline:
        declared = decls.get("font-size")
        if declared is None:
            continue
        value = resolve_var(declared, props)
        if _VAR_RE.search(value) or "%" in value:
            continue  # still unresolvable, or a percentage of the inherited size
        # SVG text inside a scaled viewBox declares its size in USER UNITS, so a
        # px floor is meaningless. Such rules paint with `fill`, HTML text with
        # `color` - that is the discriminator, and it needs no naming convention.
        if "fill" in decls:
            continue
        # `em` is relative to the inherited size, which is not resolvable here.
        if re.search(r"[\d.]em\b", value):
            continue
        role = _font_role(selector)
        floor = _FONT_FLOORS[role]
        checked += 1
        # Evaluated at BOTH ends of the root's own scaling range: at the root
        # clamp minimum (a 1366px laptop, where root scaling has bottomed out and
        # the floors actually bite) and at `viewport` with the scaled root.
        at_min = _clamp_min_px(value, root_at_minimum)
        at_viewport = _len_px(value, viewport, root_at_viewport)
        worst = min(at_min, at_viewport)
        if worst + 0.01 < floor:
            offenders.append(
                f"{selector} {{font-size: {declared}}} -> {worst:.1f}px "
                f"({role} floor {floor:.0f}px)"
            )
    if not checked:
        return _finding(
            "font-floor", "n/a", "structural", "no resolvable font-size declarations"
        )
    if offenders:
        return _finding(
            "font-floor", "fail", "structural",
            f"{len(offenders)}/{checked} font-size(s) below the rendered floor: "
            + "; ".join(offenders[:6]),
            "high",
        )
    return _finding(
        "font-floor", "pass", "structural",
        f"{checked} font-size(s) clear the 16 / 13 / 12px floors at the clamp "
        f"minimum and at {viewport}px",
    )


def check_emphasis_token(
    html: str, rules: list[tuple[str, dict[str, str]]]
) -> dict[str, Any]:
    """Rule 5: inline meaning-carrying tokens differ from prose on BOTH a color
    axis and a family / weight axis."""
    if not _TOKEN_MARKUP_RE.search(html):
        return _finding(
            "emphasis-token", "n/a", "structural", "no inline token markup on the page"
        )
    # Grade the UNQUALIFIED base rule (`code`, `kbd`, `samp`) when one exists,
    # falling back to the aggregate of scoped rules otherwise. A scoped rule such
    # as `footer code` styles tokens in ONE region, so accepting it as proof would
    # pass a page whose page-wide tokens are still invisible - which is precisely
    # how a command name shipped indistinguishable inside a margin note.
    base: list[dict[str, str]] = []
    scoped: list[dict[str, str]] = []
    for selector, decls in rules:
        if not _TOKEN_SELECTOR_RE.search(selector):
            continue
        parts = [part.strip().lower() for part in selector.split(",")]
        if parts and all(part in ("code", "kbd", "samp") for part in parts):
            base.append(decls)
        else:
            scoped.append(decls)
    graded = base or scoped
    scope = "base" if base else "scoped-only"
    has_color = any(
        "color" in decls and not _BODY_INK_RE.search(decls["color"]) for decls in graded
    )
    has_face = any(
        "font-family" in decls or "font-weight" in decls for decls in graded
    )
    if has_color and has_face:
        return _finding(
            "emphasis-token", "pass", "structural",
            f"inline tokens ({scope} rule) declare both a distinct color and a "
            "family / weight change",
        )
    missing = []
    if not has_color:
        missing.append("no color distinct from the body ink")
    if not has_face:
        missing.append("no font-family / font-weight change")
    return _finding(
        "emphasis-token", "fail", "structural",
        f"inline tokens ({scope} rule) are not distinct on both axes: "
        + "; ".join(missing),
        "high",
    )


def check_contrast(rules: list[tuple[str, dict[str, str]]]) -> dict[str, Any]:
    """Rule 6: declared foreground / background custom-property pairs clear AA.

    Severity is graded by how badly a color fails, so the HIGH bar stays
    meaningful: the primary body pair, or a foreground unusable on ANY declared
    background, is HIGH; a single failing combination while others pass is MEDIUM.
    Semantic status colors are excluded - they render as large or bordered badge
    text whose applicable floor is 3:1 and whose size is not knowable here.
    """
    declared = custom_properties(rules)
    props = {
        name[2:]: resolved
        for name, value in declared.items()
        if (resolved := resolve_var(value, declared)).startswith("#")
    }
    foregrounds = [
        name for name in props
        if _FG_NAME_RE.search(name)
        and not _NON_TEXT_NAME_RE.search(name)
        and not _STATUS_NAME_RE.search(name)
    ]
    backgrounds = [name for name in props if _BG_NAME_RE.search(name)]
    if not foregrounds or not backgrounds:
        return _finding(
            "contrast", "n/a", "structural",
            "no declared ink / background custom-property pair to grade",
        )
    primary_fg = next(
        (name for name in foregrounds if re.search(r"ink|text|fg", name)), None
    )
    primary_bg = next(
        (name for name in backgrounds if re.search(r"base|canvas|paper|^bg", name)),
        backgrounds[0],
    )
    failures: list[str] = []
    severity = None
    for fg in foregrounds:
        ratios = {bg: contrast_ratio(props[fg], props[bg]) for bg in backgrounds}
        usable = [bg for bg, ratio in ratios.items() if ratio and ratio >= AA_RATIO]
        for bg, ratio in ratios.items():
            if ratio is None or ratio >= AA_RATIO:
                continue
            failures.append(f"--{fg} on --{bg} = {ratio:.2f}:1")
            if not usable or (fg == primary_fg and bg == primary_bg):
                severity = "high"
            elif severity is None:
                severity = "medium"
    if not failures:
        return _finding(
            "contrast", "pass", "structural",
            f"{len(foregrounds)} foreground(s) clear AA {AA_RATIO}:1 on "
            f"{len(backgrounds)} background(s)",
        )
    return _finding(
        "contrast", "fail", "structural",
        f"{len(failures)} pair(s) below AA {AA_RATIO}:1: " + "; ".join(failures[:6]),
        severity or "medium",
    )


def _svg_blocks(html: str) -> list[str]:
    """Every inline `<svg>...</svg>` source block, outermost only."""
    return _SVG_BLOCK_RE.findall(html)


def _parse_svg(block: str) -> Any | None:
    """Parse one SVG block with stdlib XML, or None when it is not well-formed.

    An SVG embedded in HTML can carry markup this parser rejects, so an
    unparsable block is SKIPPED rather than reported as a defect: the scorer's
    job here is to find broken diagrams, not to be an XML validator.

    XML-hardening without a dependency: `xml.etree.ElementTree` does not resolve
    external entities or retrieve DTDs, so the XXE class does not apply. The
    entity-expansion DoS class (billion laughs, quadratic blowup) DOES, and it
    requires an inline `<!ENTITY` declaration, so any block carrying a DOCTYPE or
    ENTITY declaration is refused unparsed. `defusedxml` would be the standard
    answer, but this script is stdlib-only by contract - it ships to users through
    the skill bundle and must not add an install requirement - and refusing the
    declaration removes the attack surface the library would have guarded.
    """
    from xml.etree import ElementTree

    if _XML_DECL_GUARD_RE.search(block):
        return None
    try:
        return ElementTree.fromstring(block)
    except ElementTree.ParseError:
        return None


def _path_points(d: str) -> tuple[list[str], list[tuple[float, float]]]:
    """Command letters (uppercased) and the absolute points a path `d` visits.

    Only M/L/H/V/Z are tracked exactly; a curve's control points are treated as
    waypoints, which is enough for the extent test that identifies a triangle.
    """
    commands: list[str] = []
    points: list[tuple[float, float]] = []
    x = y = 0.0
    for letter, raw in _PATH_CMD_RE.findall(d):
        commands.append(letter.upper())
        relative = letter.islower()
        nums = [float(n) for n in _NUMBER_RE.findall(raw)]
        if letter.upper() == "Z":
            continue
        if letter.upper() == "H":
            for n in nums:
                x = x + n if relative else n
                points.append((x, y))
            continue
        if letter.upper() == "V":
            for n in nums:
                y = y + n if relative else n
                points.append((x, y))
            continue
        for index in range(0, len(nums) - 1, 2):
            dx, dy = nums[index], nums[index + 1]
            x, y = (x + dx, y + dy) if relative else (dx, dy)
            points.append((x, y))
    return commands, points


def _is_small_triangle(d: str, max_extent: float = 24.0) -> bool:
    """A closed 3-vertex path whose bounding box is small: a hand-placed arrowhead."""
    commands, points = _path_points(d)
    if not commands or commands[0] != "M" or commands[-1] != "Z":
        return False
    if [command for command in commands if command in ("L", "H", "V")] != ["L", "L"]:
        return False
    if any(command in ("C", "S", "Q", "T", "A") for command in commands):
        return False
    if len(points) != 3:
        return False
    width = max(p[0] for p in points) - min(p[0] for p in points)
    height = max(p[1] for p in points) - min(p[1] for p in points)
    return width <= max_extent and height <= max_extent


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _css_marker_attachments(
    rules: list[tuple[str, dict[str, str]]],
) -> tuple[set[str], set[str]]:
    """Class tokens CSS attaches a marker to, and the marker ids CSS references.

    Attaching a marker from CSS is legitimate and sometimes necessary: a marker
    does NOT inherit from the element that references it, so a connector whose
    stroke changes with state needs a second marker swapped in by a CSS rule.
    Both SVG checks must therefore read CSS as well as attributes, or they would
    report a correctly-authored page as missing its arrowheads.
    """
    classes: set[str] = set()
    ids: set[str] = set()
    for selector, decls in rules:
        marker_values = [
            value for prop, value in decls.items() if prop.startswith("marker-")
        ]
        if not marker_values:
            continue
        classes.update(_SELECTOR_TOKEN_RE.findall(selector))
        for value in marker_values:
            match = _URL_REF_RE.search(value)
            if match:
                ids.add(match.group(1))
    return classes, ids


def placement_decisions(html: str) -> list[dict[str, str]]:
    """Parse the design record's `IMAGERY PLACEMENTS` block.

    One `placement:` line per section, `|`-separated:
        placement: <section> | <role> | embedded | <why>
        placement: <section> | none: <reason>

    Read from the RAW html because the block lives inside an HTML comment - the
    design record is deliberately not user-visible.
    """
    decisions: list[dict[str, str]] = []
    for line in _PLACEMENT_RE.findall(html):
        fields = [part.strip() for part in line.split("|")]
        section = fields[0] if fields else ""
        rest = fields[1:]
        status = "unknown"
        role = ""
        reason = ""
        for field in rest:
            lowered = field.lower()
            if lowered.startswith("none"):
                status = "none"
                reason = field.partition(":")[2].strip()
            elif lowered == "embedded":
                status = "embedded"
            elif lowered in _PLACEMENT_ROLES:
                role = lowered
        if section.lower().startswith("none"):
            # `placement: none: <reason>` with no section field.
            status = "none"
            reason = section.partition(":")[2].strip()
            section = ""
        decisions.append(
            {"section": section, "role": role, "status": status, "reason": reason}
        )
    return decisions


def check_svg_arrowheads(
    html: str, rules: list[tuple[str, dict[str, str]]] | None = None
) -> dict[str, Any]:
    """Rule 1: arrowheads are markers, applied consistently - never hand-placed
    triangles that detach from their line when geometry moves."""
    css_classes, _ = _css_marker_attachments(rules or [])
    blocks = _svg_blocks(html)
    if not blocks:
        return _finding("svg-arrowhead", "n/a", "structural", "no inline SVG")
    triangles: list[str] = []
    inconsistent: list[str] = []
    for index, block in enumerate(blocks):
        root = _parse_svg(block)
        if root is None:
            continue
        # A marker's OWN arrowhead path is a small triangle by design, so skip
        # anything inside a <marker> before looking for stray ones.
        in_marker: set[int] = set()
        for marker in root.iter():
            if _local(marker.tag) == "marker":
                for child in marker.iter():
                    in_marker.add(id(child))
        connectors: dict[str, list[bool]] = {}
        for element in root.iter():
            if _local(element.tag) != "path" or id(element) in in_marker:
                continue
            d = element.get("d", "")
            fill = (element.get("fill") or "").strip().lower()
            if _is_small_triangle(d) and fill not in ("", "none"):
                triangles.append(f"svg[{index}] path d=\"{d[:40]}\" fill={fill}")
                continue
            key = element.get("class") or "(unclassed)"
            has_marker = any(
                element.get(f"marker-{position}")
                for position in ("end", "start", "mid")
            ) or bool(set(key.split()) & css_classes)
            connectors.setdefault(key, []).append(has_marker)
        for key, flags in connectors.items():
            if any(flags) and not all(flags):
                missing = len([flag for flag in flags if not flag])
                inconsistent.append(
                    f"svg[{index}] class={key}: {missing}/{len(flags)} connector(s) "
                    "carry no marker while siblings do"
                )
    if triangles:
        return _finding(
            "svg-arrowhead", "fail", "structural",
            f"{len(triangles)} hand-placed triangle arrowhead(s) outside a <marker> "
            "(detaches when geometry moves): " + "; ".join(triangles[:4]),
            "high",
        )
    if inconsistent:
        return _finding(
            "svg-arrowhead", "fail", "structural",
            "arrowheads applied inconsistently: " + "; ".join(inconsistent[:4]),
            "medium",
        )
    return _finding(
        "svg-arrowhead", "pass", "structural",
        f"{len(blocks)} inline SVG(s): no stray triangle arrowheads, markers "
        "applied consistently",
    )


def _element_inner_html(html: str, attr_index: int) -> str:
    """The inner HTML of the element whose opening tag contains `attr_index`.

    Real containment, by walking the tag depth to the matching close. A bounded
    lookahead window was tried first and is wrong: it reports any `<svg>` that
    merely FOLLOWS the container, so a sticky page nav with a diagram later on
    the page reads as a pinned graphic. A check that cries wolf on an ordinary
    sticky nav is a check people switch off.
    """
    open_lt = html.rfind("<", 0, attr_index)
    if open_lt < 0:
        return ""
    name = re.match(r"<([A-Za-z][\w-]*)", html[open_lt:])
    open_end = html.find(">", open_lt)
    if name is None or open_end < 0 or html[open_end - 1] == "/":
        return ""
    tag = name.group(1)
    boundary = re.compile(rf"</?{re.escape(tag)}\b", re.IGNORECASE)
    depth, position = 1, open_end + 1
    while depth and position < len(html):
        match = boundary.search(html, position)
        if match is None:
            break
        depth += -1 if match.group(0).startswith("</") else 1
        position = match.end()
    return html[open_end + 1 : position]


def _is_height_constrained(decls: dict[str, str]) -> bool:
    """Whether a rule pins an element's height to something bounded.

    `max-height` is the obvious form, but a viewport-relative `height` (a `vh`
    value, or a `calc()` over one) constrains just as firmly - and paired with
    `width: auto; max-width: 100%` it is the better construction, because the
    graphic derives its width from the capped height instead of letterboxing.
    The canonical fixture uses exactly that, so demanding the `max-height`
    spelling would fail a page that satisfies the rule more completely.
    """
    if "max-height" in decls:
        return True
    height = decls.get("height", "").strip().lower()
    return bool(height) and height != "auto" and ("vh" in height or "vmin" in height)


def check_svg_viewport_fit(
    html: str, rules: list[tuple[str, dict[str, str]]]
) -> dict[str, Any]:
    """Rule 4: an SVG pinned in a sticky container must be height-constrained, or
    its overflow is unreachable by any scroll."""
    pinned: list[str] = []
    for selector, decls in rules:
        if decls.get("position", "").strip().lower() not in ("sticky", "fixed"):
            continue
        token = _SELECTOR_TOKEN_RE.findall(selector)
        if token:
            pinned.append(token[-1])
    if not pinned:
        return _finding(
            "svg-viewport-fit", "n/a", "structural", "no sticky / fixed container"
        )
    offenders: list[str] = []
    for token in dict.fromkeys(pinned):
        # Containment without a DOM: locate the element carrying the token and
        # inspect its actual inner HTML, not a lookahead window.
        holds_svg = any(
            "<svg" in _element_inner_html(html, match.start())
            for match in re.finditer(
                rf"""(?:class|id)\s*=\s*["'][^"']*\b{re.escape(token)}\b""", html
            )
        )
        if not holds_svg:
            continue
        constrained = any(
            "svg" in selector
            and token in selector
            and _is_height_constrained(decls)
            for selector, decls in rules
        )
        if not constrained:
            offenders.append(token)
    if offenders:
        return _finding(
            "svg-viewport-fit", "fail", "structural",
            "SVG pinned in a sticky container with no max-height (overflow is "
            "unreachable): " + ", ".join(f".{token}" for token in offenders),
            "high",
        )
    return _finding(
        "svg-viewport-fit", "pass", "structural",
        "every SVG in a sticky / fixed container is height-constrained",
    )


def check_svg_marker_integrity(
    html: str, rules: list[tuple[str, dict[str, str]]] | None = None
) -> dict[str, Any]:
    """Rule 5: every marker reference resolves and every defined marker is used."""
    blocks = _svg_blocks(html)
    if not blocks:
        return _finding("svg-marker-integrity", "n/a", "structural", "no inline SVG")
    defined: set[str] = set()
    _, referenced = _css_marker_attachments(rules or [])
    referenced = set(referenced)
    for block in blocks:
        root = _parse_svg(block)
        if root is None:
            continue
        for element in root.iter():
            if _local(element.tag) == "marker" and element.get("id"):
                defined.add(element.get("id", ""))
            for position in ("end", "start", "mid"):
                value = element.get(f"marker-{position}")
                if value:
                    match = _URL_REF_RE.search(value)
                    if match:
                        referenced.add(match.group(1))
    dangling = sorted(referenced - defined)
    unused = sorted(defined - referenced)
    if dangling:
        return _finding(
            "svg-marker-integrity", "fail", "structural",
            "marker reference(s) resolve to nothing, so NO arrowhead renders: "
            + ", ".join(f"#{name}" for name in dangling),
            "high",
        )
    if unused:
        return _finding(
            "svg-marker-integrity", "fail", "structural",
            "marker(s) defined but never referenced: "
            + ", ".join(f"#{name}" for name in unused),
            "medium",
        )
    if not defined:
        return _finding(
            "svg-marker-integrity", "n/a", "structural",
            "no markers defined or referenced",
        )
    return _finding(
        "svg-marker-integrity", "pass", "structural",
        f"{len(defined)} marker(s) defined, all referenced, no dangling reference",
    )


def check_render_only_defects(
    html: str, rules: list[tuple[str, dict[str, str]]]
) -> dict[str, Any]:
    """The three `references/responsive-typography.md` rule 7 defects.

    All three are invisible in markup read as prose and obvious in a rendered
    screenshot, which is why they shipped: a sticky table header pinning under a
    sticky nav, anchor jumps landing section titles beneath that nav, and long
    command lines clipped at a container edge. Each is nevertheless decidable from
    the CSS, so they are checked here rather than left to the eye.
    """
    findings: list[str] = []

    # (a) At most one sticky layer per scroll context. Two layers that pin to the
    #     same offset stack, and the lower one covers what it labels.
    pinned: dict[str, list[str]] = {}
    for selector, decls in rules:
        if decls.get("position", "").strip().lower() != "sticky":
            continue
        top = decls.get("top", "auto").strip().lower()
        pinned.setdefault(top, []).append(selector)
    for top, selectors in pinned.items():
        if top in ("auto", "") or len(selectors) < 2:
            continue
        findings.append(
            f"{len(selectors)} sticky layers pin to the same offset (top: {top}): "
            + ", ".join(selectors[:4])
            + " - the lower layer covers the content it labels"
        )

    # (b) An in-page anchor under a sticky nav needs scroll-margin-top on the
    #     target, or the heading lands underneath the nav.
    has_anchors = bool(_IN_PAGE_ANCHOR_RE.search(html))
    has_sticky = bool(pinned)
    declares_scroll_margin = any(
        "scroll-margin-top" in decls or "scroll-margin" in decls
        for _selector, decls in rules
    )
    if has_anchors and has_sticky and not declares_scroll_margin:
        findings.append(
            "in-page anchors under a sticky layer with no scroll-margin-top on any "
            "target - every jump lands the heading beneath the sticky element"
        )

    # (c) A command block must wrap or scroll; clipping loses the tail of a line
    #     silently, which is worse than an obviously broken command.
    if "<pre" in html.lower():
        pre_rules = [
            decls for selector, decls in rules
            if re.search(r"(^|[\s,>+~])pre\b", selector, re.IGNORECASE)
        ]
        wraps = any(
            "pre-wrap" in decls.get("white-space", "")
            or "pre-line" in decls.get("white-space", "")
            or decls.get("overflow-wrap", "").strip().lower() in ("anywhere", "break-word")
            for decls in pre_rules
        )
        scrolls = any(
            decls.get("overflow-x", decls.get("overflow", "")).strip().lower()
            in ("auto", "scroll")
            for decls in pre_rules
        )
        if not wraps and not scrolls:
            findings.append(
                "a <pre> block neither wraps (white-space: pre-wrap) nor scrolls "
                "(overflow-x: auto), so a long command line is clipped and its tail "
                "is lost silently"
            )

    if not findings:
        return _finding(
            "render-only-defects", "pass", "structural",
            "one sticky layer per offset, anchor targets clear the sticky nav, "
            "command blocks wrap or scroll",
        )
    return _finding(
        "render-only-defects", "fail", "structural",
        f"{len(findings)} render-surfaced defect(s): " + "; ".join(findings),
        "high",
    )


# --- Slide-mode structural checks (nav=slides, v3.18.3 Phase 4) ---------------
#
# Every check below is gated on `data-nav="slides"` on <body>: an absent
# attribute means scroll mode and the whole family is SKIPPED, never failed.
# The one exception is `check_slide_record_agreement`, which runs UNGATED
# precisely because the gate itself can be wrong - a page whose design record
# says slides but whose markup lost the attribute would otherwise skip every
# slide check and score a clean pass, which is the fail-open shape this family
# exists to prevent.

_BODY_NAV_RE = re.compile(
    r"""<body\b[^>]*?\bdata-nav\s*=\s*["']([^"']*)["']""", re.IGNORECASE
)
_RECORD_NAV_RE = re.compile(r"^\s*nav:\s*([A-Za-z]+)", re.IGNORECASE | re.MULTILINE)
_SLIDE_STAGE_RE = re.compile(
    r"""<[A-Za-z][\w-]*\b[^>]*\bclass\s*=\s*["'][^"']*\bslide-stage\b""", re.IGNORECASE
)
_DATA_FRAGMENT_RE = re.compile(
    r"""\bdata-fragment\s*=\s*["']([^"']*)["']""", re.IGNORECASE
)
_REDUCED_MOTION_RE = re.compile(
    r"@media[^{]*prefers-reduced-motion\s*:\s*reduce[^{]*\{", re.IGNORECASE
)
_GLOBAL_SCROLL_LISTENER_RE = re.compile(
    r"""(?:(\w+)\s*\.\s*)?addEventListener\(\s*["']scroll["']""", re.IGNORECASE
)
_SCROLL_TIMELINE_RE = re.compile(r"animation-timeline\s*:\s*scroll\(", re.IGNORECASE)
_SCRIPT_RE = re.compile(r"<script[^>]*>(.*?)</script>", re.DOTALL | re.IGNORECASE)
_INFINITE_ANIM_RE = re.compile(r"\binfinite\b", re.IGNORECASE)

# Structural wrappers this mode introduces. A bare generic class here collides
# with another component the moment two features coexist - the collision that
# once blanked a hero with zero console errors - so the contract requires the
# `slide-` prefix on every one of them.
_GENERIC_SLIDE_CLASSES = ("stage", "deck", "rail", "counter", "inner", "slide")

# Global scroll receivers. An element-scoped listener on a declared scrollable
# region is legitimate in slide mode (a long table scrolls); a listener on the
# window or document is page-scroll-keyed animation, which slide mode removed.
_GLOBAL_RECEIVERS = frozenset({"", "window", "document", "globalthis", "self"})

# Navigation chrome the contract requires, by its documented class name.
_CHROME_CLASSES = {
    "progress rail": "slide-rail",
    "slide counter": "slide-counter",
    "previous hit zone": "slide-hit-prev",
    "next hit zone": "slide-hit-next",
}


def nav_mode(html: str) -> str:
    """The navigation mode the MARKUP declares: `slides` or `scroll`.

    Absence of `data-nav` means `scroll`, per the backward-compatibility rule -
    a page authored before the axis existed is a scrolling page, not an error.
    """
    match = _BODY_NAV_RE.search(html)
    return "slides" if match and match.group(1).strip().lower() == "slides" else "scroll"


def record_nav_mode(html: str) -> str | None:
    """The navigation mode the DESIGN RECORD claims, or None when it says nothing.

    Read from the raw HTML (comments included), because the design record IS an
    HTML comment - the stripped text the other checks read has it removed.
    """
    for comment in _COMMENT_RE.findall(html):
        match = _RECORD_NAV_RE.search(comment)
        if match:
            return match.group(1).strip().lower()
    return None


def slide_sections(html: str) -> list[str]:
    """The inner HTML of every `.slide-stage` element, in document order."""
    sections: list[str] = []
    for match in _SLIDE_STAGE_RE.finditer(html):
        sections.append(_element_inner_html(html, match.end() - 1))
    return sections


def check_slide_record_agreement(html: str) -> dict[str, Any]:
    """The design record's `nav` field agrees with the markup (UNGATED).

    Deliberately outside the `data-nav` gate. If the record says slides and the
    attribute is missing, every other slide check silently skips and the page
    scores clean - a fail-open outcome strictly worse than no check at all.
    """
    declared = nav_mode(html)
    recorded = record_nav_mode(html)
    if recorded is None:
        if declared == "slides":
            return _finding(
                "slide-record", "fail", "structural",
                "markup declares data-nav=\"slides\" but the design record names no "
                "nav mode - the resolved mode and its provenance are unrecorded",
                "high",
            )
        return _finding(
            "slide-record", "n/a", "structural",
            "no nav field in the design record; treated as scroll (backward compatible)",
        )
    if recorded not in ("slides", "scroll"):
        return _finding(
            "slide-record", "fail", "structural",
            f"design record nav value {recorded!r} is neither slides nor scroll",
            "high",
        )
    if recorded != declared:
        return _finding(
            "slide-record", "fail", "structural",
            f"design record says nav={recorded} but the markup declares {declared} "
            "- the mode gate and the record disagree, so the wrong contract is graded",
            "high",
        )
    return _finding(
        "slide-record", "pass", "structural",
        f"design record and markup agree on nav={declared}",
    )


def check_slide_structure(
    html: str, rules: list[tuple[str, dict[str, str]]]
) -> dict[str, Any]:
    """Slide containers exist and their classes carry the `slide-` prefix."""
    sections = slide_sections(html)
    if not sections:
        return _finding(
            "slide-structure", "fail", "structural",
            "data-nav=\"slides\" but the page contains no .slide-stage section - "
            "a deck with no slides",
            "high",
        )
    bare: list[str] = []
    for selector, _decls in rules:
        for token in _SELECTOR_TOKEN_RE.findall(selector):
            if token.lower() in _GENERIC_SLIDE_CLASSES:
                bare.append(f".{token} (in {selector})")
    if bare:
        return _finding(
            "slide-structure", "fail", "structural",
            f"{len(sections)} slide(s), but {len(bare)} bare generic class "
            "selector(s) can collide with another component: " + ", ".join(bare[:4]),
            "high",
        )
    return _finding(
        "slide-structure", "pass", "structural",
        f"{len(sections)} slide stage(s), all mode classes component-prefixed",
    )


def check_slide_fit(rules: list[tuple[str, dict[str, str]]]) -> dict[str, Any]:
    """Page scroll is disabled and each stage declares viewport-fitted sizing."""
    issues: list[str] = []
    no_scroll = any(
        decls.get("overflow", decls.get("overflow-y", "")).strip().lower() == "hidden"
        for selector, decls in rules
        if re.search(r"\b(html|body)\b|slide-deck", selector, re.IGNORECASE)
    )
    if not no_scroll:
        issues.append(
            "no scroll container declares overflow: hidden (html, body, or "
            ".slide-deck) - the page still scrolls behind the deck"
        )
    stage_rules = [
        decls for selector, decls in rules
        if re.search(r"\bslide-stage\b", selector, re.IGNORECASE)
    ]
    sized = any(
        re.search(r"\d\s*(svh|dvh|lvh|vh)\b", decls.get("height", ""), re.IGNORECASE)
        or re.search(r"\d\s*(svh|dvh|lvh|vh)\b", decls.get("min-height", ""), re.IGNORECASE)
        or decls.get("inset", "").strip() == "0"
        for decls in stage_rules
    )
    if stage_rules and not sized:
        issues.append(
            "no .slide-stage rule declares viewport-fitted height (svh / dvh / vh, "
            "or inset: 0 on a viewport-sized deck) - stages are not stage-sized"
        )
    if issues:
        return _finding(
            "slide-fit", "fail", "structural",
            f"{len(issues)} stage-sizing defect(s): " + "; ".join(issues),
            "high",
        )
    return _finding(
        "slide-fit", "pass", "structural",
        "page scroll disabled and stages declare viewport-fitted sizing",
    )


def check_slide_fragments(html: str) -> dict[str, Any]:
    """`data-fragment` values are positive, unique, and contiguous from 1.

    Per slide, not per page: fragment order is a within-slide build sequence, so
    two slides both numbering 1..3 is correct, while one slide numbering 1, 3 has
    a gap the runtime's ordered reveal cannot express.
    """
    problems: list[str] = []
    for index, inner in enumerate(slide_sections(html), start=1):
        raw = _DATA_FRAGMENT_RE.findall(inner)
        if not raw:
            continue
        values: list[int] = []
        for token in raw:
            text = token.strip()
            if not text.lstrip("+-").isdigit():
                problems.append(f"slide {index}: non-numeric data-fragment {token!r}")
                continue
            values.append(int(text))
        if not values:
            continue
        if any(value < 1 for value in values):
            problems.append(
                f"slide {index}: non-positive fragment index "
                f"{sorted(value for value in values if value < 1)}"
            )
        duplicates = sorted({value for value in values if values.count(value) > 1})
        expected = list(range(1, len(set(values)) + 1))
        if sorted(set(values)) != expected:
            problems.append(
                f"slide {index}: fragments {sorted(set(values))} are not contiguous "
                f"from 1 (expected {expected})"
            )
        elif duplicates:
            # Duplicates reveal together by design; report only as context when
            # the sequence is otherwise well-formed.
            continue
    if problems:
        return _finding(
            "slide-fragments", "fail", "structural",
            f"{len(problems)} fragment-indexing defect(s): " + "; ".join(problems[:4]),
            "high",
        )
    return _finding(
        "slide-fragments", "pass", "structural",
        "every slide's data-fragment values are positive and contiguous from 1",
    )


def check_slide_scroll_keyed(html: str) -> dict[str, Any]:
    """No scroll-keyed animation survives in a slide-mode page.

    Slide mode has no page scroll, so a scroll-keyed effect is not merely
    redundant - it never fires, leaving content that was supposed to reveal
    permanently hidden. An element-scoped scroll listener is allowed: a declared
    scrollable region (a long table) legitimately scrolls inside its stage.
    """
    issues: list[str] = []
    for script in _SCRIPT_RE.findall(html):
        for receiver in _GLOBAL_SCROLL_LISTENER_RE.findall(script):
            if (receiver or "").strip().lower() in _GLOBAL_RECEIVERS:
                issues.append(
                    f"a global scroll listener ({receiver or 'bare'}.addEventListener"
                    "('scroll', ...)) drives behavior from a page scroll that slide "
                    "mode removed"
                )
                break
        if "IntersectionObserver" in script and re.search(
            r"classList\s*\.\s*(add|toggle)", script
        ):
            issues.append(
                "an IntersectionObserver toggles classes (a scroll-triggered reveal); "
                "in slide mode reveals are entry-triggered or fragment-stepped"
            )
    if _SCROLL_TIMELINE_RE.search(html):
        issues.append("animation-timeline: scroll() is keyed to a scroll that never happens")
    if issues:
        return _finding(
            "slide-scroll-keyed", "fail", "structural",
            f"{len(issues)} scroll-keyed construct(s) in a slides page: "
            + "; ".join(dict.fromkeys(issues)),
            "high",
        )
    return _finding(
        "slide-scroll-keyed", "pass", "structural",
        "no scroll listener, scroll-driven reveal, or scroll timeline remains",
    )


def check_slide_ambient(html: str) -> dict[str, Any]:
    """Every ambient (infinite) animation is guarded by a reduced-motion rule.

    The grammar disables ambient loops entirely under reduced motion rather than
    slowing them, so an infinite animation with no guard is a vestibular hazard
    that ships to exactly the readers who asked not to receive it.
    """
    infinite: list[str] = []
    for selector, decls in css_rules(html):
        for prop in ("animation", "animation-iteration-count"):
            if prop in decls and _INFINITE_ANIM_RE.search(decls[prop]):
                infinite.append(selector)
                break
    if not infinite:
        return _finding(
            "slide-ambient", "n/a", "structural",
            "no infinite (ambient) animation declared",
        )
    guarded = False
    for style in _STYLE_RE.findall(html):
        css = _CSS_COMMENT_RE.sub("", style)
        for match in _REDUCED_MOTION_RE.finditer(css):
            depth, position = 1, match.end()
            while depth and position < len(css):
                if css[position] == "{":
                    depth += 1
                elif css[position] == "}":
                    depth -= 1
                position += 1
            if re.search(r"\banimation", css[match.end() : position], re.IGNORECASE):
                guarded = True
                break
        if guarded:
            break
    if not guarded:
        return _finding(
            "slide-ambient", "fail", "structural",
            f"{len(infinite)} infinite animation(s) ({', '.join(dict.fromkeys(infinite))[:120]}) "
            "with no prefers-reduced-motion rule touching animation - an ambient loop "
            "must be disabled entirely under reduced motion, not slowed",
            "high",
        )
    return _finding(
        "slide-ambient", "pass", "structural",
        f"{len(infinite)} ambient animation(s), all under a reduced-motion guard",
    )


def check_slide_chrome(html: str) -> dict[str, Any]:
    """The documented navigation chrome is present: rail, counter, hit zones."""
    missing = [
        label for label, klass in _CHROME_CLASSES.items()
        if not re.search(rf"""class\s*=\s*["'][^"']*\b{klass}\b""", html, re.IGNORECASE)
    ]
    if missing:
        return _finding(
            "slide-chrome", "fail", "structural",
            "navigation chrome missing: " + ", ".join(missing)
            + " - a keyboard-only deck gives the reader no position or pointer path",
            "high",
        )
    return _finding(
        "slide-chrome", "pass", "structural",
        "progress rail, slide counter, and both hit zones present",
    )


def score_html(
    html: str,
    *,
    aspect: str | None = None,
    expect_images: int | None = None,
    viewport: int = 1920,
) -> dict[str, Any]:
    """Score the HTML text against the structural rubric subset. Returns a dict
    with the per-criterion findings, the high-severity count, and the binary
    page-level pass bar (no open high-severity finding)."""
    stripped = _COMMENT_RE.sub("", html)
    findings: list[dict[str, Any]] = []

    # 1. Full-width compliance (Phase 1).
    aspect_match = _ASPECT_RE.search(html)
    resolved_aspect = aspect or (aspect_match.group(1) if aspect_match else None)
    if resolved_aspect == "full":
        frac = band_fraction(html, viewport)
        if frac is None:
            findings.append(
                _finding("full-width", "fail", "structural",
                         "no --page-max/--gutter canvas vars found", "high")
            )
        elif frac < FULL_WIDTH_MIN:
            findings.append(
                _finding("full-width", "fail", "structural",
                         f"widest band {frac:.3f} of viewport (< {FULL_WIDTH_MIN})",
                         "high")
            )
        else:
            findings.append(
                _finding("full-width", "pass", "structural",
                         f"widest band {frac:.3f} of viewport")
            )
        if "transform: scale(" in stripped or _ZOOM_RE.search(stripped):
            findings.append(
                _finding("full-width", "fail", "structural",
                         "global zoom / transform:scale simulates width", "high")
            )
    else:
        findings.append(
            _finding("full-width", "n/a", "structural",
                     f"aspect={resolved_aspect or 'unknown'} (not full-width)")
        )

    # 2. Image sizing caps (Phase 2), meaningful only when a FIGURE is present.
    #
    # A cinematic stage layer (`references/scroll-scrub.md`) is not a figure: it is
    # a decorative, aria-hidden full-bleed backdrop, and `object-fit: cover` is the
    # correct treatment for it - `contain` would letterbox the stage and defeat the
    # effect the level exists for. So a page whose only `data:` images are stage
    # layers is n/a here rather than failing for missing figure caps.
    # The caps apply to a rendered FIGURE BOX, so require one: a <figure>, or an
    # <img> carrying a data: URI that is not a cinematic stage layer. A bare
    # `data:image` substring is not enough - on a cinematic page the stills live
    # inside an inline <script> config and the layers are created at runtime, so
    # the static file has no <img> at all and there is no box to cap. Matching the
    # substring made every cinematic build fail for a missing cap on a figure it
    # does not have.
    has_figures = "<figure" in html or bool(_NON_STAGE_IMG_RE.search(html))
    if not has_figures and "data:image" in html:
        findings.append(
            _finding("image-sizing", "n/a", "structural",
                     "embedded image data but no figure box to cap (a cinematic "
                     "stage builds its decorative layers at runtime, and "
                     "object-fit: cover is correct for them)")
        )
    elif has_figures:
        missing = [cap for cap in (HERO_CAP, OBJECT_FIT) if cap not in html]
        if missing:
            findings.append(
                _finding("image-sizing", "fail", "structural",
                         f"missing image caps: {', '.join(missing)}", "high")
            )
        else:
            findings.append(
                _finding("image-sizing", "pass", "structural",
                         "hero max-height + object-fit: contain present")
            )
    else:
        findings.append(
            _finding("image-sizing", "n/a", "structural", "no images / figures")
        )

    # 3. Annotation fidelity (Phase 3), only when an annotated figure is present.
    annotated = html.count('class="fig-annotated"')
    if annotated:
        regions = html.count('class="fig-region"')
        has_toggle = 'class="fig-view-original"' in html
        if regions == 0:
            findings.append(
                _finding("annotation-fidelity", "fail", "structural",
                         f"{annotated} annotated figure(s) but 0 overlay regions "
                         "(dropped overlay)", "high")
            )
        elif not has_toggle:
            findings.append(
                _finding("annotation-fidelity", "fail", "structural",
                         "overlay present but no view-original toggle", "medium")
            )
        else:
            findings.append(
                _finding("annotation-fidelity", "pass", "structural",
                         f"{annotated} annotated figure(s), {regions} region(s), "
                         "view-original toggle present")
            )
    else:
        findings.append(
            _finding("annotation-fidelity", "n/a", "structural",
                     "no annotated figures")
        )

    # 4. Imagery integration (Phase 4) + the placement record (Phase 5), only
    #    when an expectation is supplied - i.e. on a consented stock / ai / both run.
    if expect_images is not None:
        count = len(re.findall(r"data:image/", html))
        decisions = placement_decisions(html)
        embedded = [d for d in decisions if d["status"] == "embedded"]
        declined_without_reason = [
            d for d in decisions if d["status"] == "none" and not d["reason"]
        ]
        if count < expect_images:
            findings.append(
                _finding("imagery-integration", "fail", "structural",
                         f"{count} embedded image(s), expected >= {expect_images}",
                         "high")
            )
        elif not decisions:
            # The page has assets but no placement record, so the placement pass
            # either never ran or was not written down. Both mean nobody can tell
            # whether a section was skipped deliberately or forgotten - which is
            # the whole defect the record exists to close.
            findings.append(
                _finding("imagery-integration", "fail", "structural",
                         f"{count} embedded image(s) but NO `IMAGERY PLACEMENTS` "
                         "block in the design record: the placement pass left no "
                         "decision trail", "high")
            )
        elif len(embedded) > count:
            # Comparing against the total is deliberate: a page's `data:` images
            # include source figures, so an embedded-placement count ABOVE the
            # total is provably wrong while one below it is normal.
            findings.append(
                _finding("imagery-integration", "fail", "structural",
                         f"the placement record claims {len(embedded)} embedded "
                         f"asset(s) but the page contains only {count} `data:` "
                         "image(s) in total - the record does not match the page",
                         "high")
            )
        elif declined_without_reason:
            findings.append(
                _finding("imagery-integration", "fail", "structural",
                         f"{len(declined_without_reason)} placement(s) declined with "
                         "no reason: "
                         + ", ".join(
                             d["section"] or "(unnamed)"
                             for d in declined_without_reason[:4]
                         )
                         + " - a decline is valid, an unexplained one is not",
                         "medium")
            )
        else:
            findings.append(
                _finding("imagery-integration", "pass", "structural",
                         f"{count} embedded image(s) (>= {expect_images}); "
                         f"{len(decisions)} placement decision(s) recorded "
                         f"({len(embedded)} embedded, "
                         f"{len(decisions) - len(embedded)} declined with a reason)")
            )
    else:
        findings.append(
            _finding("imagery-integration", "n/a", "structural",
                     "no integration expectation (procedural / non-consented run)")
        )

    # 5. Readability / layout integrity (structural subset: offline + well-formed).
    external = next((p.pattern for p in _FETCH_RE if p.search(stripped)), None)
    if external:
        findings.append(
            _finding("readability-layout", "fail", "structural",
                     "off-host fetch construct found (not offline)", "high")
        )
    elif "</html>" not in html.lower():
        findings.append(
            _finding("readability-layout", "fail", "structural",
                     "document is not well-formed (no </html>)", "high")
        )
    else:
        findings.append(
            _finding("readability-layout", "pass", "structural",
                     "offline and well-formed")
        )

    # 6-9. Fluid layout and readability (references/responsive-typography.md).
    rules = css_rules(html)
    findings.append(check_fluid_spacing(rules))
    findings.append(check_font_floor(rules, viewport, inline_style_rules(stripped)))
    findings.append(check_emphasis_token(stripped, rules))
    findings.append(check_contrast(rules))

    # 10-12. Authored-SVG integrity (references/svg-diagram-quality.md).
    findings.append(check_svg_arrowheads(stripped, rules))
    findings.append(check_svg_viewport_fit(stripped, rules))
    findings.append(check_svg_marker_integrity(stripped, rules))

    # 13. The three defect classes only a render surfaces (rule 7).
    findings.append(check_render_only_defects(stripped, rules))

    # 14. Slide-mode integrity (references/slide-navigation.md; rubric criterion 12).
    #     The record check runs UNGATED - it is what catches a page whose record
    #     says slides while the markup lost data-nav, which would otherwise skip
    #     every check below and score clean.
    findings.append(check_slide_record_agreement(html))
    if nav_mode(html) == "slides":
        findings.append(check_slide_structure(stripped, rules))
        findings.append(check_slide_fit(rules))
        findings.append(check_slide_fragments(stripped))
        findings.append(check_slide_scroll_keyed(stripped))
        findings.append(check_slide_ambient(html))
        findings.append(check_slide_chrome(stripped))
    else:
        findings.append(
            _finding("slide-mode", "n/a", "structural",
                     "scroll mode (data-nav absent or scroll): slide-mode checks skipped")
        )

    root_at_viewport, root_at_minimum, root_is_fluid = root_font_px(rules, viewport)
    high = sum(1 for finding in findings if finding.get("severity") == "high")
    return {
        "mode": "structural",
        "nav": nav_mode(html),
        "root_font_px": round(root_at_viewport, 2),
        "root_font_px_at_clamp_min": round(root_at_minimum, 2),
        "root_font_is_fluid": root_is_fluid,
        "findings": findings,
        "high_severity": high,
        "page_pass": high == 0,
        "note": (
            "structural-only: agent-vision criteria (crop, dead space, "
            "annotation placement vs source, imagery relevance, contrast) "
            "were not graded"
        ),
    }


def score_file(path: str | Path, **kwargs: Any) -> dict[str, Any]:
    return score_html(Path(path).read_text(encoding="utf-8"), **kwargs)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic STRUCTURAL scorer for the presentify "
        "visual-QA gate (Phase 5)."
    )
    parser.add_argument("html", help="generated .html to score")
    parser.add_argument(
        "--aspect", default=None,
        help="override the resolved aspect (else read from data-aspect)"
    )
    parser.add_argument(
        "--expect-images", type=int, default=None,
        help="minimum embedded images expected (a consented stock/mix run)"
    )
    parser.add_argument("--viewport", type=int, default=1920)
    parser.add_argument("--json", action="store_true", help="emit the result as JSON")
    args = parser.parse_args(argv)

    path = Path(args.html)
    if not path.is_file():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 2
    result = score_file(
        path, aspect=args.aspect, expect_images=args.expect_images,
        viewport=args.viewport,
    )
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for finding in result["findings"]:
            sev = f" [{finding['severity']}]" if finding.get("severity") else ""
            print(
                f"{finding['status'].upper():4} {finding['criterion']}{sev}: "
                f"{finding['evidence']}",
                file=sys.stderr,
            )
        verdict = "PASS" if result["page_pass"] else "FAIL"
        print(
            f"{verdict} (structural-only; {result['high_severity']} high-severity)",
            file=sys.stderr,
        )
    return 0 if result["page_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
