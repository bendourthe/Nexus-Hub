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
arrowheads, height-constrained pinned graphics, and marker integrity.
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
_INTERACTIVE_SELECTOR_RE = re.compile(
    r"\b(?:a|button|input|select|textarea|summary|label)\b|:hover|:focus|"
    r"btn|chip|tab|ctl|nav|link|toggle|control",
    re.IGNORECASE,
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


def _len_px(token: str, viewport: int, root_font: int = 16) -> float:
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
    # An additive preferred term such as `0.94rem + 0.3vw`; CSS allows the bare
    # sum inside clamp()/min()/max() without a calc() wrapper.
    parts = _split_top_level(token, "+")
    if len(parts) > 1:
        return sum(_len_px(part, viewport, root_font) for part in parts)
    for suffix, factor in (
        ("px", 1.0),
        ("rem", float(root_font)),
        ("em", float(root_font)),
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


def _clamp_min_px(token: str, root_font: int = 16) -> float:
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
    `--gutter` canvas vars, or None when they are absent."""
    page_max_match = _PAGE_MAX_RE.search(html)
    gutter_match = _GUTTER_RE.search(html)
    if not page_max_match or not gutter_match:
        return None
    gutter = _len_px(gutter_match.group(1), viewport)
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
    """Rule 1: macro spacing on a band / grid container must be viewport-fluid."""
    offenders: list[str] = []
    for selector, decls in rules:
        if not _BAND_SELECTOR_RE.search(selector):
            continue
        for prop, value in decls.items():
            if prop not in _MACRO_SPACING_PROPS:
                continue
            if _FLUID_RE.search(value):
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
    """Classify a font-size rule's text role: body prose, interactive, or secondary."""
    parts = [part.strip().lower() for part in selector.split(",")]
    if any(part in ("body", "html", "p") for part in parts):
        return "body"
    if any(_INTERACTIVE_SELECTOR_RE.search(part) for part in parts):
        return "interactive"
    return "secondary"


def check_font_floor(
    rules: list[tuple[str, dict[str, str]]], viewport: int = 1920
) -> dict[str, Any]:
    """Rule 4: every font-size clears its role floor at BOTH the clamp minimum and
    the resolved value at `viewport`."""
    props = custom_properties(rules)
    offenders: list[str] = []
    checked = 0
    for selector, decls in rules:
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
        at_min = _clamp_min_px(value)
        at_viewport = _len_px(value, viewport)
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
            and "max-height" in decls
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

    # 2. Image sizing caps (Phase 2), meaningful only when images are present.
    has_figures = "<figure" in html or "data:image" in html
    if has_figures:
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

    # 4. Imagery integration (Phase 4), only when an expectation is supplied.
    if expect_images is not None:
        count = len(re.findall(r"data:image/", html))
        if count < expect_images:
            findings.append(
                _finding("imagery-integration", "fail", "structural",
                         f"{count} embedded image(s), expected >= {expect_images}",
                         "high")
            )
        else:
            findings.append(
                _finding("imagery-integration", "pass", "structural",
                         f"{count} embedded image(s) (>= {expect_images})")
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
    findings.append(check_font_floor(rules, viewport))
    findings.append(check_emphasis_token(stripped, rules))
    findings.append(check_contrast(rules))

    # 10-12. Authored-SVG integrity (references/svg-diagram-quality.md).
    findings.append(check_svg_arrowheads(stripped, rules))
    findings.append(check_svg_viewport_fit(stripped, rules))
    findings.append(check_svg_marker_integrity(stripped, rules))

    high = sum(1 for finding in findings if finding.get("severity") == "high")
    return {
        "mode": "structural",
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
