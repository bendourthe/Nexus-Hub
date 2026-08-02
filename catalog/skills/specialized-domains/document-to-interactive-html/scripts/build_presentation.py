#!/usr/bin/env python3
"""
build_presentation.py - deterministic baseline builder for the
document-to-interactive-html skill (Phase 2).

It consumes the normalized content-model JSON emitted by extract_content.py
(see references/content-model.md) and produces ONE self-contained, offline
HTML presentation by populating the scaffold in assets/presentation-template.html.
Every block is rendered server-side here: paragraphs, nested bullets, tables,
base64 images, quotes, code, and hidden speaker notes, plus `chart` blocks
rendered as INLINE SVG (bar / line / pie / doughnut) with no charting library
and no CDN. The theme (assets/theme.json, or a theme-tokens / brand-styling
override) is merged over the template defaults and emitted as CSS custom
properties.

LOCAL-FIRST and ZERO-NETWORK by construction: this script imports no socket /
urllib / http / requests module and opens no connection, and it never writes an
external reference into the output. A post-write self-check fails the build if
the output contains a fetching construct that points off-host (an external
src/href, an @import, a url(...) to http(s), or a <script src>/<link
stylesheet>), so the offline guarantee is enforced, not assumed. Note that a
URL appearing only as escaped body text in a source document is NOT a fetch and
does not trip the check.

Usage:
    python build_presentation.py model.json -o deck.html
    python build_presentation.py model.json -o deck.html --theme my-brand.json
    python build_presentation.py model.json -o deck.html --title "Q3 Review"
    python build_presentation.py model.json -o deck.html --layout full

All diagnostics go to stderr; the only stdout is none (the artifact is the file).
Output is deterministic: section order, block order, and chart geometry are a
pure function of the input model and theme.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE = SKILL_ROOT / "assets" / "presentation-template.html"
DEFAULT_THEME = SKILL_ROOT / "assets" / "theme.json"

SUPPORTED_KINDS = {
    "title",
    "content",
    "section-break",
    "data",
    "quote",
    "image",
    "appendix",
}

THEME_BLOCK_RE = re.compile(
    r"/\* NEXUS_THEME_START.*?\*/.*?/\* NEXUS_THEME_END \*/", re.DOTALL
)
ASPECT_BLOCK_RE = re.compile(
    r"/\* NEXUS_ASPECT_START.*?\*/.*?/\* NEXUS_ASPECT_END \*/", re.DOTALL
)
SLIDES_RE = re.compile(
    r"(<!-- NEXUS_SLIDES_START -->).*?(<!-- NEXUS_SLIDES_END -->)", re.DOTALL
)
# DEVIATION (Phase 1.3): the title content must not contain "<", so this match
# cannot span from the header comment's literal "<title>" mention across the
# head to the real </title> (which the prior DOTALL `.*?` did, deleting the
# comment close, <html>, <head>, and the <meta> tags). [^<]* keeps the match to
# a single well-formed title element.
TITLE_RE = re.compile(r"<title>[^<]*</title>")
HTML_TAG_RE = re.compile(r"<html\b[^>]*>", re.IGNORECASE)

# Output-aspect canvas presets. Each maps a --layout value to the
# (--page-max, --gutter) pair the builder injects into the template's
# NEXUS_ASPECT block; the builder also stamps data-aspect on <html>. "standard"
# reproduces the historical centered column; "full" is a true edge-to-edge
# canvas (page-max 100% with small gutters, so the widest content band clears
# ~95% of a 1920px viewport); "portrait" is a narrow reading column. --measure
# stays scoped to prose only and is never set here or on the slide wrapper.
ASPECTS: dict[str, tuple[str, str]] = {
    "full": ("100%", "clamp(1rem, 2vw, 2rem)"),
    "standard": ("1180px", "clamp(24px, 7vw, 140px)"),
    "portrait": ("46rem", "clamp(20px, 6vw, 72px)"),
}
DEFAULT_LAYOUT = "standard"

# A fetch is a construct that loads a resource off-host. Plain URL text in a
# slide body is escaped and lives in element content, so it is not a fetch.
_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_FETCH_PATTERNS = [
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


# --- text + number helpers -------------------------------------------------


def _esc(text: object) -> str:
    """Escape text for element content (ampersands and angle brackets)."""
    return html.escape(str(text), quote=False)


def _esc_attr(text: object) -> str:
    """Escape text for a double-quoted attribute value."""
    return html.escape(str(text), quote=True)


_HEX_COLOR_RE = re.compile(r"#[0-9A-Fa-f]{3,8}\Z")


def _safe_color(value: object) -> str | None:
    """Return `value` only when it is a strict #hex color (3-8 hex digits),
    else None. Annotation colors flow into a `style="..."` attribute, so a value
    that is not a plain hex color is dropped rather than interpolated, closing
    the attribute-context injection path (the model is a general input contract,
    not only the trusted extractor output)."""
    text = str(value or "")
    return text if _HEX_COLOR_RE.fullmatch(text) else None


def _fmt_num(value: float) -> str:
    """Format a number without a trailing .0 (3.0 -> '3', 1.25 -> '1.25')."""
    number = float(value)
    if number == int(number):
        return str(int(number))
    return f"{number:.2f}".rstrip("0").rstrip(".")


# --- theme merge + CSS emission --------------------------------------------


def _deep_merge(base: dict, override: dict) -> dict:
    """Merge override into a copy of base (nested dicts merged, scalars set)."""
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_theme(theme_path: Path | None) -> dict:
    """Load the default theme and merge an optional override over it."""
    with DEFAULT_THEME.open(encoding="utf-8") as handle:
        theme = json.load(handle)
    if theme_path is not None:
        with theme_path.open(encoding="utf-8") as handle:
            theme = _deep_merge(theme, json.load(handle))
    return theme


def _space_values(spacing: dict) -> list[int]:
    """Compute eight spacing steps (px) from base + scale multipliers."""
    base = float(spacing.get("base", 8) or 8)
    scale = list(spacing.get("scale") or [0.5, 1, 1.5, 2, 3, 4, 6, 8])
    steps: list[int] = []
    for i in range(8):
        if i < len(scale):
            multiplier = float(scale[i])
        else:
            multiplier = float(scale[-1]) * (i - len(scale) + 2)
        steps.append(max(1, round(base * multiplier)))
    return steps


def theme_to_css(theme: dict) -> str:
    """Render the theme as the CSS custom-property block the template reads."""
    palette = theme.get("palette", {})
    fonts = theme.get("fonts", {})
    spaces = _space_values(theme.get("spacing", {}))
    lines = ["/* NEXUS_THEME_START */"]
    # The template CSS references --color-bg / --color-fg (and primary /
    # secondary / accent / muted), so emit those exact names, mapping the
    # theme's `background` / `foreground` palette keys to `bg` / `fg`. Emitting
    # --color-background / --color-foreground left those two vars undefined in
    # the built output, so the body lost its theme background / foreground
    # colors (BG-1, resolved in v3.15.4 Phase 7).
    color_vars = {
        "primary": "primary",
        "secondary": "secondary",
        "accent": "accent",
        "background": "bg",
        "foreground": "fg",
        "muted": "muted",
    }
    for slot, var in color_vars.items():
        lines.append(f"  --color-{var}: {palette.get(slot, '#1c1c1c')};")
    lines.append(f"  --font-heading: {fonts.get('heading', 'Georgia, serif')};")
    lines.append(f"  --font-body: {fonts.get('body', 'system-ui, sans-serif')};")
    lines.append(f"  --font-mono: {fonts.get('mono', 'monospace')};")
    for index, value in enumerate(spaces, start=1):
        lines.append(f"  --space-{index}: {value}px;")
    lines.append(f"  --radius: {theme.get('radius', 6)}px;")
    lines.append(f"  --shadow: {theme.get('shadow', 'none')};")
    lines.append("  /* NEXUS_THEME_END */")
    return "\n  ".join(lines)


def aspect_to_css(layout: str) -> str:
    """Render the NEXUS_ASPECT custom-property block for the chosen layout."""
    page_max, gutter = ASPECTS.get(layout, ASPECTS[DEFAULT_LAYOUT])
    lines = [
        "/* NEXUS_ASPECT_START */",
        f"  --page-max: {page_max};",
        f"  --gutter: {gutter};",
        "  /* NEXUS_ASPECT_END */",
    ]
    return "\n  ".join(lines)


def set_aspect_attr(html_text: str, layout: str) -> str:
    """Stamp data-aspect=<layout> on the root <html> element (first tag only)."""

    def _replace(match: re.Match) -> str:
        tag = match.group(0)
        if "data-aspect=" in tag:
            return re.sub(
                r'data-aspect="[^"]*"', f'data-aspect="{layout}"', tag, count=1
            )
        return tag[:-1] + f' data-aspect="{layout}">'

    return HTML_TAG_RE.sub(_replace, html_text, count=1)


def _chart_colors(theme: dict, count: int) -> list[str]:
    """Return `count` series colors, cycling the theme's chart palette."""
    palette = theme.get("chart_palette")
    if not palette:
        base = theme.get("palette", {})
        palette = [
            base.get("accent", "#c2410c"),
            base.get("primary", "#1f2a44"),
            base.get("secondary", "#3a4a6b"),
            base.get("muted", "#6b6b6b"),
        ]
    return [palette[i % len(palette)] for i in range(max(1, count))]


# --- inline SVG charts (no library, no namespace attribute) ----------------


def _svg_bar(categories: list, series: list, colors: list, muted: str) -> str:
    width, height = 720, 340
    m_left, m_right, m_top, m_bottom = 56, 20, 24, 60
    plot_w = width - m_left - m_right
    plot_h = height - m_top - m_bottom
    baseline = m_top + plot_h
    values = [v for s in series for v in s.get("values", [])]
    v_max = max(values + [0]) or 1
    n_cat = max(1, len(categories))
    group_w = plot_w / n_cat
    bar_w = (group_w * 0.78) / max(1, len(series))
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Bar chart">']
    for frac in (0.0, 0.5, 1.0):
        y = baseline - plot_h * frac
        parts.append(
            f'<line x1="{m_left}" y1="{y:.1f}" x2="{width - m_right}" '
            f'y2="{y:.1f}" stroke="{muted}" stroke-width="1" opacity="0.25"/>'
        )
        parts.append(
            f'<text x="{m_left - 8}" y="{y + 4:.1f}" text-anchor="end" '
            f'font-size="12" fill="{muted}">{_esc(_fmt_num(v_max * frac))}</text>'
        )
    for ci, category in enumerate(categories):
        group_x = m_left + ci * group_w + group_w * 0.11
        for si, one in enumerate(series):
            seq = one.get("values", [])
            value = seq[ci] if ci < len(seq) else 0
            bar_h = plot_h * (float(value) / v_max)
            x = group_x + si * bar_w
            y = baseline - bar_h
            parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(1.0, bar_w - 2):.1f}" '
                f'height="{bar_h:.1f}" fill="{colors[si]}" rx="2">'
                f"<title>{_esc(category)} {_esc(one.get('name', ''))}: "
                f"{_esc(_fmt_num(value))}</title></rect>"
            )
        parts.append(
            f'<text x="{m_left + ci * group_w + group_w / 2:.1f}" '
            f'y="{baseline + 20}" text-anchor="middle" font-size="12" '
            f'fill="{muted}">{_esc(category)}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


def _svg_line(categories: list, series: list, colors: list, muted: str) -> str:
    width, height = 720, 340
    m_left, m_right, m_top, m_bottom = 56, 20, 24, 60
    plot_w = width - m_left - m_right
    plot_h = height - m_top - m_bottom
    baseline = m_top + plot_h
    values = [v for s in series for v in s.get("values", [])]
    v_max = max(values + [0]) or 1
    n = max(1, len(categories))
    step = plot_w / max(1, n - 1) if n > 1 else 0
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Line chart">']
    for frac in (0.0, 0.5, 1.0):
        y = baseline - plot_h * frac
        parts.append(
            f'<line x1="{m_left}" y1="{y:.1f}" x2="{width - m_right}" '
            f'y2="{y:.1f}" stroke="{muted}" stroke-width="1" opacity="0.25"/>'
        )
        parts.append(
            f'<text x="{m_left - 8}" y="{y + 4:.1f}" text-anchor="end" '
            f'font-size="12" fill="{muted}">{_esc(_fmt_num(v_max * frac))}</text>'
        )
    for si, one in enumerate(series):
        seq = one.get("values", [])
        points = []
        for ci in range(len(categories)):
            value = float(seq[ci]) if ci < len(seq) else 0.0
            x = m_left + (ci * step if n > 1 else plot_w / 2)
            y = baseline - plot_h * (value / v_max)
            points.append(f"{x:.1f},{y:.1f}")
        parts.append(
            f'<polyline fill="none" stroke="{colors[si]}" stroke-width="2.5" '
            f'points="{" ".join(points)}"/>'
        )
        for point in points:
            px, py = point.split(",")
            parts.append(f'<circle cx="{px}" cy="{py}" r="3" fill="{colors[si]}"/>')
    for ci, category in enumerate(categories):
        x = m_left + (ci * step if n > 1 else plot_w / 2)
        parts.append(
            f'<text x="{x:.1f}" y="{baseline + 20}" text-anchor="middle" '
            f'font-size="12" fill="{muted}">{_esc(category)}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


def _svg_pie(categories: list, values: list, colors: list, doughnut: bool) -> str:
    size = 320
    cx = cy = size / 2
    radius = 132
    total = sum(float(v) for v in values) or 1.0
    parts = [
        (
            f'<svg viewBox="0 0 {size} {size}" role="img" '
            f'aria-label="{"Doughnut" if doughnut else "Pie"} chart">'
        )
    ]
    if doughnut:
        circumference = 2 * math.pi * radius
        offset = 0.0
        stroke_w = 56
        for i, value in enumerate(values):
            frac = float(value) / total
            dash = frac * circumference
            parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" '
                f'stroke="{colors[i % len(colors)]}" stroke-width="{stroke_w}" '
                f'stroke-dasharray="{dash:.2f} {circumference - dash:.2f}" '
                f'stroke-dashoffset="{-offset:.2f}" '
                f'transform="rotate(-90 {cx} {cy})">'
                f"<title>{_esc(categories[i] if i < len(categories) else '')}: "
                f"{_esc(_fmt_num(value))}</title></circle>"
            )
            offset += dash
    else:
        start = -math.pi / 2
        for i, value in enumerate(values):
            frac = float(value) / total
            end = start + frac * 2 * math.pi
            x1 = cx + radius * math.cos(start)
            y1 = cy + radius * math.sin(start)
            x2 = cx + radius * math.cos(end)
            y2 = cy + radius * math.sin(end)
            large = 1 if frac > 0.5 else 0
            parts.append(
                f'<path d="M {cx:.1f} {cy:.1f} L {x1:.1f} {y1:.1f} '
                f'A {radius} {radius} 0 {large} 1 {x2:.1f} {y2:.1f} Z" '
                f'fill="{colors[i % len(colors)]}">'
                f"<title>{_esc(categories[i] if i < len(categories) else '')}: "
                f"{_esc(_fmt_num(value))}</title></path>"
            )
            start = end
    parts.append("</svg>")
    return "".join(parts)


def render_chart(block: dict, theme: dict) -> str:
    """Render a chart block as an inline-SVG figure with a legend."""
    categories = [str(c) for c in block.get("categories", [])]
    series = [s for s in block.get("series", []) if isinstance(s, dict)]
    if not categories or not series:
        return ""
    hint = str(block.get("chart_type_hint", "bar")).lower()
    if hint in ("pie", "doughnut"):
        colors = _chart_colors(theme, len(categories))
        svg = _svg_pie(
            categories, series[0].get("values", []), colors, hint == "doughnut"
        )
        legend_labels = list(zip(categories, colors))
    else:
        colors = _chart_colors(theme, len(series))
        renderer = _svg_line if hint == "line" else _svg_bar
        muted = theme.get("palette", {}).get("muted", "#6b6b6b")
        svg = renderer(categories, series, colors, muted)
        legend_labels = [
            (s.get("name", f"Series {i + 1}"), colors[i]) for i, s in enumerate(series)
        ]
    legend = "".join(
        f'<span><span class="swatch" style="background:{color}"></span>'
        f"{_esc(label)}</span>"
        for label, color in legend_labels
    )
    return (
        f'<figure class="chart-figure">{svg}'
        f'<div class="chart-legend">{legend}</div></figure>'
    )


# --- block + section rendering ---------------------------------------------


def _render_bullets(items: list) -> str:
    """Render a flat depth-tagged item list as nested <ul> markup."""
    if not items:
        return ""
    out = ['<ul class="block-bullets">']
    prev = 0
    first = True
    for item in items:
        text = _esc(str(item.get("text", "")).strip())
        depth = max(0, int(item.get("depth", 0) or 0))
        depth = min(depth, prev + 1)
        if first:
            out.append("<li>" + text)
            first = False
        elif depth > prev:
            out.append("<ul>" * (depth - prev) + "<li>" + text)
        elif depth < prev:
            out.append("</li>" + "</ul></li>" * (prev - depth) + "<li>" + text)
        else:
            out.append("</li><li>" + text)
        prev = depth
    out.append("</li>" + "</ul></li>" * prev + "</ul>")
    return "".join(out)


def _render_table(block: dict) -> str:
    header = block.get("header") or []
    rows = block.get("rows") or []
    parts = ["<table>"]
    if header:
        cells = "".join(f"<th>{_esc(c)}</th>" for c in header)
        parts.append(f"<thead><tr>{cells}</tr></thead>")
    parts.append("<tbody>")
    for row in rows:
        cells = "".join(f"<td>{_esc(c)}</td>" for c in row)
        parts.append(f"<tr>{cells}</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)


def _render_annotated_figure(uri: str, alt: str, annotations: list, caption: str) -> str:
    """Recreate an annotated figure: the base image plus a registered overlay
    layer (regions positioned by image-relative percentage coords), a legend,
    and a CSS-only view-original toggle. Offline, no JS (see the overlay-
    recreation pattern in references/figure-reconstruction.md part 5)."""
    toggle_id = "figorig-" + hashlib.md5(
        json.dumps(annotations, sort_keys=True).encode("utf-8")
    ).hexdigest()[:10]
    regions: list[str] = []
    legend: list[tuple[str, str | None]] = []
    for annotation in annotations:
        bbox = list(annotation.get("bbox") or []) + [0.0, 0.0, 0.0, 0.0]
        x, y, w, h = (float(value) for value in bbox[:4])
        label = str(annotation.get("text", "") or "")
        group = str(annotation.get("group", "") or "")
        fill = _safe_color(annotation.get("fill"))  # dropped unless a strict #hex
        style = (
            f"left:{x * 100:.2f}%;top:{y * 100:.2f}%;"
            f"width:{w * 100:.2f}%;height:{h * 100:.2f}%"
        )
        if fill:
            style += f";--region-color:{fill}"
        label_html = (
            f'<span class="fig-region__label">{_esc(label)}</span>' if label else ""
        )
        group_attr = f' data-group="{_esc_attr(group)}"' if group else ""
        regions.append(
            f'<div class="fig-region" style="{style}" tabindex="0"{group_attr} '
            f'role="img" aria-label="{_esc_attr(label or "annotated region")}">'
            f"{label_html}</div>"
        )
        key = label or group
        if key and key not in [item[0] for item in legend]:
            legend.append((key, fill))
    legend_html = ""
    if legend:
        items = "".join(
            f'<li><span class="fig-legend__swatch" '
            f'style="{("background:" + color) if color else ""}"></span>'
            f"{_esc(key)}</li>"
            for key, color in legend
        )
        legend_html = f'<ul class="fig-legend">{items}</ul>'
    return (
        '<figure class="fig-annotated">'
        f'<input type="checkbox" id="{toggle_id}" class="fig-toggle" hidden>'
        '<div class="fig-figure">'
        f'<img src="{_esc_attr(uri)}" alt="{_esc_attr(alt)}">'
        f'<div class="fig-overlay">{"".join(regions)}</div>'
        '<span class="fig-provenance">recreated from source figure</span>'
        "</div>"
        f"{legend_html}"
        f'<label class="fig-view-original" for="{toggle_id}">View original</label>'
        f"{caption}"
        "</figure>"
    )


def _render_image(block: dict) -> str:
    uri = str(block.get("data_uri", ""))
    if not uri.startswith("data:"):
        return ""
    alt = block.get("alt", "Image")
    caption = ""
    if alt and alt != "Image":
        caption = f"<figcaption>{_esc(alt)}</figcaption>"
    annotations = block.get("annotations") or []
    if annotations:
        return _render_annotated_figure(uri, alt, annotations, caption)
    return (
        f'<figure><img src="{_esc_attr(uri)}" alt="{_esc_attr(alt)}">{caption}</figure>'
    )


def render_block(block: dict, theme: dict) -> str:
    """Render one content-model block; unknown types are ignored."""
    kind = block.get("type")
    if kind == "paragraph":
        return f"<p>{_esc(block.get('text', ''))}</p>"
    if kind == "bullets":
        return _render_bullets(block.get("items", []))
    if kind == "table":
        return _render_table(block)
    if kind == "image":
        return _render_image(block)
    if kind == "chart":
        return render_chart(block, theme)
    if kind == "code":
        return f"<pre><code>{_esc(block.get('text', ''))}</code></pre>"
    if kind == "quote":
        attribution = block.get("attribution", "")
        attr_html = (
            f'<span class="quote-attribution">{_esc(attribution)}</span>'
            if attribution
            else ""
        )
        return f"<blockquote>{_esc(block.get('text', ''))}{attr_html}</blockquote>"
    if kind == "notes":
        return f'<aside class="notes">{_esc(block.get("text", ""))}</aside>'
    return ""  # forward-compatible: ignore unknown block types


def render_section(section: dict, index: int, theme: dict) -> str:
    """Render one content-model section as a template slide."""
    kind = section.get("kind", "content")
    if kind not in SUPPORTED_KINDS:
        kind = "content"
    heading = section.get("heading", "") or ""
    subheading = section.get("subheading")
    parts = [
        (
            f'<section class="slide slide--{kind}" data-kind="{kind}" '
            f'aria-roledescription="slide">'
        ),
        '<div class="slide__body">',
    ]
    if heading:
        if kind == "section-break":
            parts.append(
                f'<h2 class="slide__heading"><span class="slide__index">'
                f"{index + 1:02d}</span><span>{_esc(heading)}</span></h2>"
            )
        else:
            tag = "h1" if kind == "title" else "h2"
            parts.append(f'<{tag} class="slide__heading">{_esc(heading)}</{tag}>')
    if subheading:
        parts.append(f'<p class="slide__subheading">{_esc(subheading)}</p>')
    for block in section.get("blocks", []) or []:
        rendered = render_block(block, theme)
        if rendered:
            parts.append(rendered)
    parts.append("</div></section>")
    return "\n".join(parts)


# --- assembly + self-check -------------------------------------------------


def render_slides(model: dict, theme: dict) -> str:
    sections = model.get("sections", []) or []
    if not sections:
        sections = [
            {
                "heading": model.get("title", "Presentation"),
                "kind": "title",
                "blocks": [],
            }
        ]
    return "\n".join(render_section(s, i, theme) for i, s in enumerate(sections))


def assert_no_external(html_text: str) -> None:
    """Fail the build if the output contains an off-host fetching construct."""
    stripped = _COMMENT_RE.sub("", html_text)
    offenders: list[str] = []
    for pattern in _FETCH_PATTERNS:
        match = pattern.search(stripped)
        if match:
            start = max(0, match.start() - 30)
            offenders.append(stripped[start : match.end() + 30].replace("\n", " "))
    if offenders:
        print(
            "Error: output contains external reference(s); the offline guarantee "
            "would be broken:",
            file=sys.stderr,
        )
        for snippet in offenders:
            print(f"  ...{snippet}...", file=sys.stderr)
        raise SystemExit(3)


def build_html(
    model: dict,
    theme: dict,
    template_text: str,
    title: str,
    layout: str = DEFAULT_LAYOUT,
) -> str:
    """Populate the template's title, theme block, aspect block, and slides."""
    css = theme_to_css(theme)
    slides = render_slides(model, theme)
    safe_title = _esc(title)
    result = TITLE_RE.sub(
        lambda _m: f"<title>{safe_title}</title>", template_text, count=1
    )
    result = THEME_BLOCK_RE.sub(lambda _m: css, result, count=1)
    result = ASPECT_BLOCK_RE.sub(lambda _m: aspect_to_css(layout), result, count=1)
    result = set_aspect_attr(result, layout)
    result = SLIDES_RE.sub(
        lambda m: f"{m.group(1)}\n{slides}\n{m.group(2)}", result, count=1
    )
    return result


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build one self-contained, offline interactive HTML presentation "
            "from a content-model JSON (see references/content-model.md). "
            "Local-only; renders inline SVG charts; no network calls."
        )
    )
    parser.add_argument(
        "model", help="Content-model JSON path (from extract_content.py)."
    )
    parser.add_argument("-o", "--out", required=True, help="Output .html path.")
    parser.add_argument(
        "--theme",
        default=None,
        help="Optional theme override JSON (theme-tokens curated theme or a "
        "brand-styling brand JSON); merged over assets/theme.json.",
    )
    parser.add_argument(
        "--template",
        default=str(DEFAULT_TEMPLATE),
        help="Presentation template path (default: bundled assets template).",
    )
    parser.add_argument(
        "--title", default=None, help="Override the presentation title."
    )
    parser.add_argument(
        "--layout",
        choices=sorted(ASPECTS),
        default=DEFAULT_LAYOUT,
        help="Output aspect / canvas: 'full' (edge-to-edge, page-max 100%), "
        "'standard' (centered column, the default), or 'portrait' (narrow "
        "reading column). Sets data-aspect and the injected --page-max/--gutter.",
    )
    args = parser.parse_args(argv)

    model_path = Path(args.model)
    if not model_path.is_file():
        print(f"Error: content model not found: {model_path}", file=sys.stderr)
        return 2
    with model_path.open(encoding="utf-8") as handle:
        model: dict[str, Any] = json.load(handle)
    if int(model.get("schema_version", 1)) not in (1, 2):
        print(
            f"Error: unsupported content-model schema_version "
            f"{model.get('schema_version')}; this builder understands versions "
            "1 and 2 (v2 fields are additive and ignored where unknown).",
            file=sys.stderr,
        )
        return 2

    template_path = Path(args.template)
    if not template_path.is_file():
        print(f"Error: template not found: {template_path}", file=sys.stderr)
        return 2
    template_text = template_path.read_text(encoding="utf-8")

    theme = load_theme(Path(args.theme) if args.theme else None)
    title = args.title or model.get("title", "Presentation")

    output = build_html(model, theme, template_text, title, args.layout)
    assert_no_external(output)

    out_path = Path(args.out)
    if out_path.parent and not out_path.parent.exists():
        out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(output, encoding="utf-8")
    print(
        f"Wrote {out_path} ({len(model.get('sections', []))} slide(s)).",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
