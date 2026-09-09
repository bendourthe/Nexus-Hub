"""Retained handbook assembly for build_presentation.py; no extraction or network."""

from __future__ import annotations

import base64
import hashlib
import html
import json
import math
import os
import re
import tempfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path, PureWindowsPath
from typing import Any

BUNDLE = Path(__file__).resolve().parent.parent
ID = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]*\Z")


def raster_uri(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(
        r"data:image/(?:png|jpeg|webp|gif);base64,[A-Za-z0-9+/=\s]+", value
    ):
        raise ValueError("image.data_uri: embedded raster required")
    base64.b64decode(re.sub(r"\s", "", value.split(",", 1)[1]), validate=True)
    return value


def image_html(uri: str, caption: str) -> str:
    return (
        '<figure><button class="dv-image" data-dv-enlarge aria-label="Enlarge image"><img src="'
        + escaped(raster_uri(uri))
        + '" alt="'
        + escaped(caption)
        + '"></button><figcaption>'
        + escaped(caption)
        + "</figcaption></figure>"
    )


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def escaped(value: Any) -> str:
    return html.escape(str(value), quote=True)


def json_script(value: Any) -> str:
    return (
        json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False)
        .replace("<", "\\u003c")
        .replace("&", "\\u0026")
    )


def contained(root: Path, relative: str) -> Path:
    """Reject traversal, alternate streams, and linked ancestors before opening."""
    if not isinstance(relative, str) or not relative or "\x00" in relative:
        raise ValueError("path: expected nonempty relative text")
    portable = relative.replace("\\", "/")
    if PureWindowsPath(relative).drive or portable.startswith("/") or ":" in portable:
        raise ValueError(f"path: absolute or alternate-stream path {relative}")
    parts = portable.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ValueError(f"path: unsafe component in {relative}")
    target = root.joinpath(*parts)
    for part in (root, *target.parents, target):
        if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
            raise ValueError(f"path: linked ancestor or leaf {relative}")
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"path: escapes authoring root {relative}")
    if target.is_file() and target.stat().st_nlink > 1:
        raise ValueError(f"path: hard-linked file {relative}")
    return target


class Inputs:
    """Remember the exact bytes read so changes invalidate a pending write."""

    def __init__(self, root: Path):
        self.root = root.absolute()
        self.hashes: dict[str, str] = {}

    def read(self, relative: str) -> bytes:
        data = contained(self.root, relative).read_bytes()
        fingerprint = digest(data)
        if relative in self.hashes and self.hashes[relative] != fingerprint:
            raise ValueError(f"source changed during build: {relative}")
        self.hashes[relative] = fingerprint
        return data

    def verify(self) -> None:
        for relative, expected in self.hashes.items():
            if digest(contained(self.root, relative).read_bytes()) != expected:
                raise ValueError(f"source changed during build: {relative}")


class DocumentReferences(HTMLParser):
    """Check final instance IDs and local navigation/accessibility references."""

    def __init__(self, text: str):
        super().__init__()
        self.ids: set[str] = set()
        self.refs: set[str] = set()
        self.feed(text)
        if self.refs - self.ids:
            raise ValueError(
                f"document: unresolved references {sorted(self.refs - self.ids)}"
            )

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if not value:
                continue
            if key == "id":
                if value in self.ids:
                    raise ValueError(f"document: duplicate ID {value}")
                self.ids.add(value)
            elif (
                key in {"href", "xlink:href"}
                and value.startswith("#")
                and len(value) > 1
            ):
                self.refs.add(value[1:])
            elif key in {
                "aria-labelledby",
                "aria-describedby",
                "aria-controls",
                "for",
                "headers",
            }:
                self.refs.update(value.split())

    handle_startendtag = handle_starttag


class FragmentValidator(HTMLParser):
    """Retained HTML is passive markup; behavior comes from reviewed local assets."""

    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in {
            "div",
            "span",
            "article",
            "section",
            "aside",
            "header",
            "footer",
            "p",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "strong",
            "em",
            "b",
            "i",
            "small",
            "br",
            "hr",
            "ul",
            "ol",
            "li",
            "dl",
            "dt",
            "dd",
            "a",
            "figure",
            "figcaption",
            "img",
            "table",
            "thead",
            "tbody",
            "tfoot",
            "tr",
            "td",
            "th",
            "caption",
            "colgroup",
            "col",
            "pre",
            "code",
            "blockquote",
            "details",
            "summary",
            "time",
            "sup",
            "sub",
            "abbr",
        }:
            raise ValueError(f"fragment: active element {tag}")
        for key, raw in attrs:
            value = raw or ""
            if key == "id":
                if value in self.ids or not ID.fullmatch(value):
                    raise ValueError("fragment: invalid or duplicate ID")
                self.ids.add(value)
            if "{{" in value:
                raise ValueError("fragment: source-unit slots must be text nodes")
            if key.startswith("on") or key in {"srcdoc", "action", "formaction"}:
                raise ValueError(f"fragment: executable attribute {key}")
            if key in {"srcset", "background", "ping", "autofocus", "is"}:
                raise ValueError(f"fragment: active resource attribute {key}")
            if key == "src":
                raster_uri(value)
            if key in {"href", "xlink:href", "poster"} and not value.startswith("#"):
                raise ValueError(f"fragment: non-embedded resource {key}")
            if key == "style":
                safe_css(value)

    handle_startendtag = handle_starttag


class AuthoredFragment(HTMLParser):
    """Keep authored composition while inserting escaped retained source units."""

    def __init__(self, text: str, prefix: str, units: dict[str, str]):
        super().__init__()
        validator = FragmentValidator()
        validator.feed(text)
        self.ids = {key: f"{prefix}-{key}" for key in validator.ids}
        self.units = units
        self.seen: set[str] = set()
        self.parts: list[str] = []
        self.feed(text)
        if self.seen != set(units):
            raise ValueError(
                f"fragment: missing source units {sorted(set(units) - self.seen)}"
            )

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        result = []
        for key, value in attrs:
            if value is None:
                result.append(key)
                continue
            if key == "id":
                value = self.ids[value]
            elif key in {"href", "xlink:href"} and value.startswith("#"):
                value = "#" + self.ids.get(value[1:], value[1:])
            elif key in {"aria-labelledby", "aria-describedby", "for", "headers"}:
                value = " ".join(self.ids.get(item, item) for item in value.split())
            value = re.sub(
                r"url\(#([^\s)]+)\)",
                lambda m: f"url(#{self.ids.get(m[1], m[1])})",
                value,
            )
            result.append(f'{key}="{escaped(value)}"')
        self.parts.append(f"<{tag} {' '.join(result)}>")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.parts[-1] = self.parts[-1][:-1] + "/>"

    def handle_endtag(self, tag: str) -> None:
        self.parts.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        parts = re.split(r"\{\{unit:([^}]+)\}\}", data)
        for i, part in enumerate(parts):
            if i % 2:
                if part not in self.units or part in self.seen:
                    raise ValueError(
                        f"fragment: unknown or duplicate source unit {part}"
                    )
                self.seen.add(part)
                self.parts.append(self.units[part])
            else:
                self.parts.append(html.escape(part, quote=False))


def safe_css(text: str) -> str:
    inspected = re.sub(
        r"url\(['\"]?data:font/[a-z0-9.+-]+;base64,[a-zA-Z0-9+/=]+['\"]?\)", "", text
    )
    if re.search(
        r"</|@import|url\s*\(|image-set\s*\(|expression\s*\(|\\",
        inspected,
        re.IGNORECASE,
    ):
        raise ValueError("style: external or executable CSS is not accepted")
    return text


def svg_instance(text: str, prefix: str) -> str:
    """Copy SVG IDs and all local references without the original DOM's defs."""
    if "<!" in text:
        raise ValueError("SVG: declarations and entities are not accepted")
    root = ET.fromstring(text)
    if root.tag.rsplit("}", 1)[-1] != "svg":
        raise ValueError("SVG: root must be svg")
    forbidden = {
        "script",
        "foreignObject",
        "animate",
        "set",
        "animateTransform",
        "animateMotion",
    }
    ids = [node.attrib["id"] for node in root.iter() if "id" in node.attrib]
    if len(set(ids)) != len(ids) or any(not ID.fullmatch(key) for key in ids):
        raise ValueError("SVG: duplicate source ID")
    mapping = {key: f"{prefix}-{key}" for key in ids}
    for node in root.iter():
        if node.tag.startswith("{") and not node.tag.startswith(
            "{http://www.w3.org/2000/svg}"
        ):
            raise ValueError("SVG: foreign namespace")
        if node.tag.rsplit("}", 1)[-1] in forbidden:
            raise ValueError("SVG: active content")
        for name, value in list(node.attrib.items()):
            if "\\" in value:
                raise ValueError("SVG: escaped resource syntax is not accepted")
            key = name.rsplit("}", 1)[-1]
            if key.lower().startswith("on") or key in {"style", "src", "base"}:
                raise ValueError(f"SVG: active attribute {key}")
            if key == "id":
                node.set(name, mapping[value])
            elif key in {
                "href",
                "aria-labelledby",
                "aria-describedby",
                "aria-controls",
            }:
                references = (
                    [value[1:]]
                    if key == "href" and value.startswith("#")
                    else value.split()
                )
                if not references or any(ref not in mapping for ref in references):
                    raise ValueError(f"SVG: unresolved local reference {value}")
                node.set(
                    name,
                    ("#" if key == "href" else "")
                    + " ".join(mapping[ref] for ref in references),
                )
            elif re.search(r"url\s*\(", value, re.IGNORECASE):

                def rewrite(match: re.Match[str]) -> str:
                    reference = match.group(1).strip().strip("\"'")
                    if not reference.startswith("#"):
                        raise ValueError("SVG: external reference")
                    key = reference[1:]
                    if key not in mapping:
                        raise ValueError(f"SVG: missing definition {key}")
                    return f"url(#{mapping[key]})"

                replaced = re.sub(
                    r"url\s*\(([^)]*)\)", rewrite, value, flags=re.IGNORECASE
                )
                if re.search(r"url\s*\((?!#)", replaced, re.IGNORECASE):
                    raise ValueError("SVG: external reference")
                node.set(name, replaced)
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    return ET.tostring(root, encoding="unicode")


def validate(model: dict[str, Any]) -> None:
    """Fail incomplete coverage and frozen-budget violations before rendering."""
    if (
        not isinstance(model, dict)
        or not isinstance(model.get("sections"), list)
        or not model["sections"]
    ):
        raise ValueError("sections: nonempty retained source required")
    sections = model["sections"]
    for key in ("design", "figures"):
        if not isinstance(model.get(key, {}), dict):
            raise TypeError(f"{key}: object required")
    if not isinstance(model.get("sources", []), list) or any(
        not isinstance(source, dict) or not isinstance(source.get("path"), str)
        for source in model.get("sources", [])
    ):
        raise ValueError("sources: path objects required")
    if any(not isinstance(section, dict) for section in sections):
        raise ValueError("sections: objects required")
    keys = [section.get("id") for section in sections]
    if any(not isinstance(key, str) or not ID.fullmatch(key) for key in keys) or len(
        set(keys)
    ) != len(keys):
        raise ValueError("sections.id: unique stable identifiers required")
    for section in sections:
        if not isinstance(section.get("blocks"), list) or not isinstance(
            section.get("heading"), str
        ):
            raise TypeError(f"section {section['id']}: heading and blocks required")
        if any(not isinstance(block, dict) for block in section["blocks"]):
            raise ValueError(f"section {section['id']}: block objects required")
        unit_ids = [block.get("id") for block in section["blocks"]]
        if any(
            not isinstance(key, str) or not ID.fullmatch(key) for key in unit_ids
        ) or len(set(unit_ids)) != len(unit_ids):
            raise ValueError("blocks.id: unique stable source-unit IDs required")
        if section["id"] in {"page-title", "handbook-record"} or section[
            "id"
        ].startswith(("slide-", "dv-")):
            raise ValueError("sections.id: reserved runtime namespace")
    presentation = model.get("presentation")
    if (
        not isinstance(presentation, dict)
        or type(presentation.get("enabled")) is not bool
    ):
        raise ValueError("presentation.enabled: explicit boolean required")
    if not presentation["enabled"]:
        return
    slides = presentation.get("slides")
    if not isinstance(slides, list) or not slides:
        raise ValueError("presentation.slides: nonempty storyboard required")
    if any(not isinstance(slide, dict) for slide in slides):
        raise ValueError("presentation.slides: objects required")
    slide_ids = [slide.get("id") for slide in slides]
    if any(
        not isinstance(key, str) or not ID.fullmatch(key) for key in slide_ids
    ) or len(set(slide_ids)) != len(slide_ids):
        raise ValueError("presentation.slides.id: unique stable identifiers required")
    budget = presentation.get("slide_budget")
    if type(budget) is not int or budget < 1 or len(slides) > budget:
        raise ValueError("presentation.slide_budget: missing or exceeded")
    source_count = presentation.get("source_slide_count", budget)
    if type(source_count) is not int or source_count < len(slides):
        raise ValueError("presentation.source_slide_count: source ceiling exceeded")
    if presentation.get("theme") not in {"light", "dark", "mixed"}:
        raise ValueError("presentation.theme: invalid policy")
    themes = presentation.get("theme_sequence")
    if (
        not isinstance(themes, list)
        or len(themes) != len(slides)
        or any(t not in {"light", "dark"} for t in themes)
    ):
        raise ValueError(
            "presentation.theme_sequence: resolve and save themes before building"
        )
    if presentation["theme"] != "mixed" and any(
        t != presentation["theme"] for t in themes
    ):
        raise ValueError("presentation.theme_sequence: contradicts policy")
    if presentation["theme"] == "mixed" and len(slides) > 1 and len(set(themes)) != 2:
        raise ValueError("presentation.theme_sequence: mixed policy needs both themes")
    depth = presentation.get("depth")
    if depth not in {"concise", "balanced", "deep-dive"}:
        raise ValueError("presentation.depth: invalid policy")
    represented = set()
    units = {
        section["id"]: {block["id"] for block in section["blocks"]}
        for section in sections
    }
    covered = {key: set() for key in keys}
    for slide in slides:
        refs = slide.get("source_ids")
        if (
            not isinstance(refs, list)
            or not refs
            or any(ref not in keys for ref in refs)
        ):
            raise ValueError(f"slide {slide['id']}: unknown or empty source_ids")
        represented.update(refs)
        selections = slide.get("unit_ids", {})
        if not isinstance(selections, dict) or any(
            key not in refs for key in selections
        ):
            raise ValueError("slide.unit_ids: use source_ids as keys")
        for key in refs:
            selected = selections.get(key, list(units[key]))
            if (
                not isinstance(selected, list)
                or any(
                    not isinstance(item, str) or item not in units[key]
                    for item in selected
                )
                or len(set(selected)) != len(selected)
            ):
                raise ValueError("slide.unit_ids: unknown or duplicate source unit")
            covered[key].update(selected)
    omitted = set(keys) - represented
    if depth in {"balanced", "deep-dive"} and omitted:
        raise ValueError(
            f"presentation.coverage: missing source units {sorted(omitted)}"
        )
    omissions = presentation.get("omissions", {})
    missing_units = {
        f"{key}/{unit}" for key in keys for unit in units[key] - covered[key]
    }
    if depth == "deep-dive" and missing_units:
        raise ValueError(
            f"presentation.coverage: deep dive missing {sorted(missing_units)}"
        )
    if depth == "balanced" and any(units[key] and not covered[key] for key in keys):
        raise ValueError("presentation.coverage: balanced requires every major section")
    if missing_units and (
        not isinstance(omissions, dict)
        or any(
            not omissions.get(key) and not omissions.get(key.split("/", 1)[0])
            for key in missing_units
        )
    ):
        raise ValueError("presentation.omissions: every omitted unit needs a reason")
    if omitted and (
        not isinstance(omissions, dict)
        or any(not omissions.get(key) for key in omitted)
    ):
        raise ValueError("presentation.omissions: every omitted source needs a reason")
    if presentation.get("initial_slide", 1) != 1:
        raise ValueError("presentation.initial_slide: global entry must start at 1")


def render_chart(block: dict[str, Any], prefix: str) -> str:
    """Render retained Cartesian series with truthful missing-data gaps and axes."""
    categories, series = block.get("categories", []), block.get("series", [])
    if any(
        block.get(key)
        for key in ("annotations", "error_bars", "panels", "secondary_axis")
    ):
        raise ValueError("chart: retain a faithful SVG for specialized geometry")
    if (
        block.get("chart_type_hint", "bar") not in {"bar", "line"}
        or block.get("axis", {}).get("scale", "linear") != "linear"
    ):
        raise ValueError(
            "chart: retain a faithful SVG or original for non-Cartesian/nonlinear figures"
        )
    if not categories or not series:
        return '<p class="dv-unavailable">Chart data unavailable.</p>'
    if block.get("confidence") == "low":
        return (
            '<p class="dv-unavailable">Chart reconstruction is unverified; data has not been inferred.</p>'
            + (
                image_html(
                    block["source_image"], block.get("caption", "Retained original")
                )
                if block.get("source_image")
                else "<p>Original image unavailable.</p>"
            )
        )
    values = []
    for item in series:
        if not item.get("name") or len(item.get("values", [])) != len(categories):
            raise ValueError("chart: named series must align with categories")
        for value in item["values"]:
            if value is not None:
                if type(value) not in {int, float} or not math.isfinite(value):
                    raise ValueError("chart: finite numbers or null required")
                values.append(value)
    if not values:
        return '<p class="dv-unavailable">Chart samples unavailable.</p>'
    axis = block.get("axis", {})
    lower, upper = (
        axis.get("y_min", min(0, min(values))),
        axis.get("y_max", max(0, max(values))),
    )
    if (
        not isinstance(lower, (int, float))
        or not isinstance(upper, (int, float))
        or not math.isfinite(lower + upper)
    ):
        raise ValueError("chart.axis: finite bounds required")
    if upper == lower:
        upper = lower + 1
    if lower > min(values) or upper < max(values) or upper <= lower:
        raise ValueError("chart.axis: bounds conceal source samples")
    left, top, width, height = 100, 30, 560, 210
    y = lambda value: top + height * (upper - value) / (upper - lower)
    baseline = y(min(upper, max(lower, 0)))
    parts = [
        f'<figure data-dv-figure="{prefix}" class="dv-chart"><figcaption>{escaped(block.get("caption", ""))}</figcaption>',
        '<div data-dv-native data-dv-zoom-view tabindex="0" aria-label="Chart plot; scroll to inspect"><svg viewBox="0 0 760 340" role="img" aria-label="'
        + escaped(block.get("caption", "Chart"))
        + '">',
    ]
    for value in sorted(
        {lower, upper, (lower + upper) / 2, *([0] if lower <= 0 <= upper else [])}
    ):
        yy = y(value)
        parts.append(
            f'<path d="M{left} {yy:.3f}H{left + width}" fill="none" stroke="currentColor" opacity=".3"/><text x="90" y="{yy + 6:.3f}" text-anchor="end">{escaped(value)}</text>'
        )
    step = width / len(categories)
    for ci, category in enumerate(categories):
        parts.append(
            f'<text x="{left + (ci + 0.5) * step:.3f}" y="272" text-anchor="middle">{escaped(category)}</text>'
        )
    palette = ["#b65b14", "#176b87", "#6d56a6", "#187564"]
    for si, item in enumerate(series):
        parts.append(
            f'<g data-dv-series-marks="{si}" fill="{palette[si % len(palette)]}" stroke="{palette[si % len(palette)]}">'
        )
        previous = None
        for ci, value in enumerate(item["values"]):
            if value is None:
                previous = None
                continue
            xx = left + (ci + 0.5) * step
            yy = y(value)
            title = escaped(
                f"{item['name']}, {categories[ci]}: {value} {axis.get('unit', '')}"
            )
            if block.get("chart_type_hint") == "line":
                if previous:
                    parts.append(
                        f'<path data-dv-animate="comparison" data-dv-mark d="M{previous[0]:.3f} {previous[1]:.3f}L{xx:.3f} {yy:.3f}" fill="none" stroke-width="3"/>'
                    )
                parts.append(
                    f'<circle cx="{xx:.3f}" cy="{yy:.3f}" r="4"><title>{title}</title></circle>'
                )
                previous = (xx, yy)
            else:
                bar_width = step * 0.7 / len(series)
                xx = left + ci * step + step * 0.15 + si * bar_width
                parts.append(
                    f'<rect data-dv-animate="comparison" data-dv-mark x="{xx:.3f}" y="{min(yy, baseline):.3f}" width="{max(1, bar_width - 2):.3f}" height="{abs(yy - baseline):.3f}"><title>{title}</title></rect>'
                )
        parts.append("</g>")
    parts.append(
        f'<text x="380" y="310" text-anchor="middle">{escaped(axis.get("x_label", ""))}</text><text transform="translate(24 135) rotate(-90)" text-anchor="middle">{escaped(axis.get("y_label", axis.get("unit", "")))}</text></svg></div><div class="dv-legend">'
    )
    for si, item in enumerate(series):
        parts.append(
            f'<button data-dv-series="{si}" aria-pressed="true">{escaped(item["name"])}</button>'
        )
    parts.append(
        "</div>"
        + figure_controls()
        + "<details><summary>Exact chart values</summary><table><thead><tr><th>Category</th>"
        + "".join("<th>" + escaped(item["name"]) + "</th>" for item in series)
        + "</tr></thead><tbody>"
    )
    for ci, category in enumerate(categories):
        parts.append(
            "<tr><th>"
            + escaped(category)
            + "</th>"
            + "".join(
                "<td>"
                + escaped(
                    "Unavailable" if item["values"][ci] is None else item["values"][ci]
                )
                + "</td>"
                for item in series
            )
            + "</tr>"
        )
    original = (
        image_html(block["source_image"], block.get("caption", "Retained original"))
        if block.get("source_image")
        else ""
    )
    provenance = ""
    if block.get("provenance") == "reconstructed-from-image":
        provenance = (
            "<p>Reconstructed from source figure. Precision: "
            + escaped(block.get("precision", "unverified"))
            + ".</p>"
        )
        if not block.get("precision") or not original:
            raise ValueError("reconstructed chart: precision and original required")
    return (
        "".join(parts)
        + "</tbody></table></details>"
        + provenance
        + original
        + "</figure>"
    )


def figure_controls() -> str:
    return '<div class="dv-figure-tools"><label>Zoom <input data-dv-zoom type="range" min="1" max="3" step=".25" value="1"></label><button data-dv-figure-reset>Reset figure</button></div>'


def render(model: dict[str, Any], inputs: Inputs) -> tuple[str, dict[str, str]]:
    """Assemble authored compositions while keeping all source text escaped."""
    import build_presentation as legacy

    validate(model)
    enabled = model["presentation"]["enabled"]
    dependencies = {}
    for name in (
        "scripts/dual_view.py",
        "scripts/build_presentation.py",
        "assets/theme.json",
        "assets/dual-view-figures.js",
    ) + (("assets/dual-view-runtime.js", "assets/dual-view.css") if enabled else ()):
        dependencies[name] = digest((BUNDLE / name).read_bytes())
    theme = legacy.load_theme(None)
    section_map = {section["id"]: section for section in model["sections"]}
    design = model.get("design", {})
    reading_themes = design.get("reading_themes", ["light"] * len(section_map))
    if len(reading_themes) != len(section_map) or any(
        value not in {"light", "dark"} for value in reading_themes
    ):
        raise ValueError(
            "design.reading_themes: save one valid theme per rendered section"
        )
    for name in model.get("retained_inputs", []):
        inputs.read(name)
    for source in model.get("sources", []):
        inputs.read(source["path"])
    figures = model.get("figures", {})
    counter = 0

    def block_html(block: dict[str, Any], view: str) -> str:
        nonlocal counter
        counter += 1
        prefix = f"dv-{view}-figure-{counter}"
        kind = block.get("type")
        if kind == "figure":
            key = block.get("figure_id")
            if key not in figures:
                raise ValueError(f"figure_id: missing definition {key}")
            block = figures[key]
            kind = block.get("type")
        if kind == "chart":
            return render_chart(block, prefix)
        if kind == "svg":
            return (
                "<figure>"
                + svg_instance(inputs.read(block["asset"]).decode("utf-8"), prefix)
                + "<figcaption>"
                + escaped(block.get("alt", ""))
                + "</figcaption></figure>"
            )
        if kind == "map":
            regions = block.get("regions", [])
            if not regions or any(not item.get("label") for item in regions):
                raise ValueError("map.regions: labeled retained regions required")
            geometry = svg_instance(inputs.read(block["asset"]).decode("utf-8"), prefix)
            labels = [item["label"] for item in regions]
            represented = {
                node.get("data-region")
                for node in ET.fromstring(geometry).iter()
                if node.get("data-region")
            }
            if len(set(labels)) != len(labels) or represented != set(labels):
                raise ValueError(
                    "map.regions: directory must match retained SVG regions"
                )
            return (
                '<figure data-dv-map><div data-dv-native data-dv-zoom-view tabindex="0" aria-label="Map; scroll to inspect">'
                + geometry
                + "</div>"
                + figure_controls()
                + '<label>Find region <input data-dv-map-search type="search"></label><div data-dv-native tabindex="0" class="dv-directory">'
                + "".join(
                    '<button data-dv-region="'
                    + escaped(item["label"])
                    + '">'
                    + escaped(item["label"])
                    + "</button>"
                    for item in regions
                )
                + '</div><p data-dv-map-status role="status"></p></figure>'
            )
        if kind == "image":
            return image_html(
                block.get("data_uri", ""), block.get("caption", block.get("alt", ""))
            )
        if kind not in {"paragraph", "bullets", "table", "code", "quote", "notes"}:
            raise ValueError(f"block.type: unsupported retained content {kind}")
        output = legacy.render_block(block, theme)
        if kind in {"table", "code"}:
            output = (
                '<div data-dv-native tabindex="0" class="dv-directory">'
                + output
                + "</div>"
            )
        return output

    def content(
        section: dict[str, Any],
        view: str,
        selected: list[str] | None = None,
        fragment_path: str | None = None,
    ) -> str:
        nonlocal counter
        counter += 1
        prefix = f"dv-{view}-fragment-{counter}"
        units = {
            str(block.get("id", f"{section['id']}-{i}")): '<div data-dv-unit="'
            + escaped(block.get("id", f"{section['id']}-{i}"))
            + '">'
            + block_html(block, view)
            + "</div>"
            for i, block in enumerate(section["blocks"])
            if selected is None or block["id"] in selected
        }
        if selected is None and len(units) != len(section["blocks"]):
            raise ValueError(f"section {section['id']}: duplicate source unit")
        fragment_path = fragment_path or (
            section.get("fragment") if selected is None else None
        )
        if fragment_path:
            fragment = inputs.read(fragment_path).decode("utf-8")
            return "".join(AuthoredFragment(fragment, prefix, units).parts)
        return "".join(units.values())

    title = escaped(model.get("title", "Handbook"))
    css = (
        (BUNDLE / "assets/dual-view.css").read_text(encoding="utf-8") if enabled else ""
    )
    if design.get("stylesheet"):
        css += safe_css(inputs.read(design["stylesheet"]).decode("utf-8"))
    brand = (
        svg_instance(
            inputs.read(design["brand_asset"]).decode("utf-8"), "dv-page-brand"
        )
        if design.get("brand_asset")
        else ""
    )
    parts = [
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        f"<title>{title}</title><style>{BASE_CSS}{css}</style><main data-dv-page>",
        f"<header>{brand}<h1>{title}</h1>",
    ]
    if enabled:
        parts.append("<button data-dv-open>Presentation Mode</button>")
    parts.append("</header>")
    if enabled:
        parts.append(
            '<nav class="dv-top-menu"><a href="#page-title">Top</a><button data-dv-open>Presentation Mode</button></nav>'
        )
    aliases = design.get("aliases", {})
    if any(
        not ID.fullmatch(key) or target not in section_map or key in section_map
        for key, target in aliases.items()
    ):
        raise ValueError("design.aliases: unique anchors and known targets required")
    parts.append('<span id="page-title"></span>')
    for i, section in enumerate(model["sections"]):
        key = section["id"]
        parts.append(
            f'<section id="{key}" data-dv-section="{key}" data-theme="{reading_themes[i]}">'
        )
        parts.extend(
            f'<span id="{escaped(alias)}"></span>'
            for alias, target in aliases.items()
            if target == key
        )
        parts.append(
            f"<h2>{escaped(section['heading'])}</h2>"
            + content(section, "page")
            + "</section>"
        )
    parts.append('</main><p data-dv-status role="status"></p>')
    if enabled:
        parts.append('<div data-dv-deck hidden><div class="dv-stage">')
        for i, slide in enumerate(model["presentation"]["slides"]):
            key = slide["id"]
            heading = slide.get(
                "heading", section_map[slide["source_ids"][0]]["heading"]
            )
            parts.append(
                f'<section id="slide-{i + 1}" data-dv-slide="{key}" data-theme="{model["presentation"]["theme_sequence"][i]}" class="dv-composition-{escaped(slide.get("composition", "content"))}" hidden><h2>{escaped(heading)}</h2>'
            )
            if design.get("brand_asset"):
                parts.append(
                    '<div class="dv-brand">'
                    + svg_instance(
                        inputs.read(design["brand_asset"]).decode("utf-8"),
                        f"dv-brand-{i}",
                    )
                    + "</div>"
                )
            parts.extend(
                content(
                    section_map[source],
                    "deck",
                    slide.get("unit_ids", {}).get(source),
                    slide.get("fragments", {}).get(source),
                )
                for source in slide["source_ids"]
            )
            parts.append("</section>")
        parts.append("</div>" + controls() + "</div>")
    record = {
        "schema_version": 1,
        "presentation": model["presentation"],
        "design": design,
        "sources": inputs.hashes,
        "build": dependencies,
        "sections": list(section_map),
        "figures": list(figures),
        "status": "requires-rendered-factual-and-design-qualification",
    }
    parts.append(
        '<script type="application/json" id="handbook-record">'
        + json_script(record)
        + "</script>"
    )
    parts.append(
        "<script>"
        + (BUNDLE / "assets/dual-view-figures.js").read_text(encoding="utf-8")
        + "</script>"
    )
    if enabled:
        parts.append(
            "<script>"
            + (BUNDLE / "assets/dual-view-runtime.js").read_text(encoding="utf-8")
            + "</script>"
        )
    parts.append("</html>")
    output = "\n".join(parts)
    DocumentReferences(output)
    return output, dependencies


def controls() -> str:
    paths = {
        "prev": "M16 4L8 12L16 20",
        "next": "M8 4L16 12L8 20",
        "replay": "M5 8A8 8 0 1 1 4 16M5 2V8H11",
        "fullscreen": "M3 9V3H9M15 3H21V9M21 15V21H15M9 21H3V15",
        "exit": "M5 5L19 19M19 5L5 19",
    }
    buttons = {
        key: f'<button data-dv-{key}><svg aria-hidden="true" viewBox="0 0 24 24"><path d="{path}"/></svg>{name}</button>'
        for (key, path), name in zip(
            paths.items(), ["Back", "Next", "Replay", "Fullscreen", "Exit"]
        )
    }
    return (
        '<nav data-dv-controls aria-label="Presentation controls">'
        + buttons["prev"]
        + buttons["replay"]
        + '<span data-dv-count aria-live="polite"></span><select data-dv-picker aria-label="Go to slide"></select>'
        + buttons["next"]
        + buttons["fullscreen"]
        + buttons["exit"]
        + "</nav>"
    )


BASE_CSS = """
[data-dv-zoom-view]{max-height:320px;overflow:auto}[data-dv-zoom-view]>svg{max-width:none;width:100%;display:block}.dv-figure-tools{display:flex;gap:1rem;align-items:center;flex-wrap:wrap}.dv-figure-tools label{display:flex;gap:.5rem;align-items:center}[data-region][data-selected=true]{stroke:currentColor;stroke-width:4}html{font:18px/1.55 system-ui,sans-serif;scrollbar-color:#52677b transparent}body{margin:0;background:#f5f3ec;color:#15283c}*{box-sizing:border-box}button,input,select{font:inherit}button{cursor:pointer;min-height:44px}header,[data-dv-section]{padding:clamp(1.25rem,4vw,4rem)}header h1{font-size:clamp(2rem,5vw,4rem);line-height:1.1}header>svg{width:240px;max-height:60px}[data-theme=dark]{background:#142235;color:#f5f3ec}[data-theme=light]{background:#f5f3ec;color:#15283c}h2{overflow-wrap:anywhere}[data-dv-section] h2{font-size:clamp(1.5rem,3vw,2.7rem);line-height:1.15}.dv-top-menu{position:sticky;top:0;display:flex;justify-content:space-between;background:#f5f3ec;color:#15283c;padding:.5rem;z-index:2}figure{margin:0;min-width:0}figure>svg{width:100%;max-height:220px}figcaption{font-size:1rem}.dv-chart svg{width:100%;min-width:650px;max-height:290px}.dv-chart svg text{font-size:24px;fill:currentColor;stroke:none}.dv-chart [data-dv-native]{overflow:auto}.dv-legend{display:flex;gap:.5rem;justify-content:center;flex-wrap:wrap}.dv-legend button{background:transparent;color:inherit;border:1px solid currentColor;border-radius:.5rem}.dv-directory{max-height:200px;overflow:auto;scrollbar-color:currentColor transparent}table{border-collapse:collapse;font-size:1rem}td,th{padding:.3rem .7rem;border-bottom:1px solid currentColor;text-align:left}pre{font-size:1rem}.dv-image{border:0;background:transparent;padding:0}.dv-image img{object-fit:contain;max-width:100%;max-height:240px}.dv-brand{position:absolute;right:1rem;top:1rem;max-width:120px}.dv-brand svg{width:100%}[data-dv-slide]>.dv-brand~*{min-width:0}[data-dv-slide]:has(.dv-brand)>h2{padding-right:140px}[data-dv-slide]>[data-dv-unit]{min-width:0}[data-dv-slide] details[open]{overflow:auto;max-height:180px}[data-dv-map] input{width:100%}[data-dv-region][hidden]{display:none!important}[data-dv-region]{display:block;width:100%;text-align:left}.dv-enlargement{max-width:94vw;max-height:90vh}.dv-enlargement img{max-width:85vw;max-height:75vh;object-fit:contain}dialog::backdrop{background:#101820cc}@media(max-width:760px){[data-dv-slide]:has(.dv-brand)>h2{padding-right:0;padding-top:3rem}}@media print{.dv-top-menu,button,input,select,dialog,[data-dv-deck]{display:none!important}[data-dv-page]{display:block!important}[data-dv-section]{break-inside:avoid;background:white;color:black}}
"""


def assemble(
    model_path: Path,
    output_path: Path,
    *,
    root: Path | None = None,
    check: bool = False,
    expected_output: str | None = None,
) -> dict[str, Any]:
    root = (root or model_path.parent).absolute()
    model_path, output_path = model_path.absolute(), output_path.absolute()
    model_name, output_name = (
        model_path.relative_to(root).as_posix(),
        output_path.relative_to(root).as_posix(),
    )
    output_path = contained(root, output_name)
    if output_path.suffix.lower() != ".html" or output_path == model_path:
        raise ValueError("output: distinct .html destination required")
    inputs = Inputs(root)
    model = json.loads(inputs.read(model_name))
    output, dependencies = render(model, inputs)
    if any(
        name in inputs.hashes
        for name in (output_name, output_name + ".build.json", output_name + ".lock")
    ):
        raise ValueError("output: destination overlaps retained input")
    payload = output.encode("utf-8")
    record_path = contained(root, output_name + ".build.json")
    record = {
        "schema_version": 1,
        "output": output_name,
        "output_sha256": digest(payload),
        "sources": inputs.hashes,
        "build": dependencies,
    }
    current = output_path.read_bytes() if output_path.exists() else None
    old_record = record_path.read_bytes() if record_path.exists() else None
    if old_record:
        previous_record = json.loads(old_record)
        if (
            not isinstance(previous_record, dict)
            or previous_record.get("schema_version") != 1
            or previous_record.get("output") != output_name
            or not re.fullmatch(
                r"[a-f0-9]{64}", str(previous_record.get("output_sha256", ""))
            )
        ):
            raise ValueError("build record modified or unowned")
    inputs.verify()
    if any(
        digest((BUNDLE / name).read_bytes()) != expected
        for name, expected in dependencies.items()
    ):
        raise ValueError("builder changed during build")
    if check:
        if current != payload or not old_record or json.loads(old_record) != record:
            raise ValueError(f"stale or missing output/build record: {output_name}")
        return record
    if current is not None and current != payload:
        previous = json.loads(old_record).get("output_sha256") if old_record else None
        if digest(current) != (expected_output or previous):
            raise ValueError(f"output modified or unowned: {output_name}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lock = contained(root, output_name + ".lock")
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    temps = []
    try:
        inputs.verify()
        if (output_path.read_bytes() if output_path.exists() else None) != current or (
            record_path.read_bytes() if record_path.exists() else None
        ) != old_record:
            raise ValueError("output changed during build")
        if any(
            digest((BUNDLE / name).read_bytes()) != expected
            for name, expected in dependencies.items()
        ):
            raise ValueError("builder changed during build")
        for target, data in [
            (output_path, payload),
            (
                record_path,
                (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8"),
            ),
        ]:
            descriptor, name = tempfile.mkstemp(
                prefix="." + target.name + ".", dir=target.parent
            )
            temp = Path(name)
            temps.append(temp)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
        inputs.verify()
        contained(root, output_name)
        contained(root, output_name + ".build.json")
        if (output_path.read_bytes() if output_path.exists() else None) != current or (
            record_path.read_bytes() if record_path.exists() else None
        ) != old_record:
            raise ValueError("output changed before replacement")
        for temp, target in zip(temps, [output_path, record_path]):
            os.replace(temp, target)
        return record
    finally:
        for temp in temps:
            temp.unlink(missing_ok=True)
        lock.unlink(missing_ok=True)
