#!/usr/bin/env python3
"""Render local HTML and report deterministic visual-defect findings.

The detector uses Playwright only at execution time. It keeps stdout reserved
for one JSON document and writes the human-readable verdict to stderr, so the
same invocation works as both a gate and a diagnostic command.

Exit codes:
    0  No gate findings.
    1  One or more rendered findings, including load/evaluation failures.
    2  Invalid input or arguments.
    3  Playwright or a launchable Chromium browser is unavailable.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from urllib.request import url2pathname

DEFAULT_VIEWPORTS = (420, 900, 1440)
DEFAULT_VIEWPORT_HEIGHT = 900
DEFAULT_TOLERANCE_PX = 1.0
DEFAULT_MINIMUM_TEXT_WIDTH_PX = 16.0
DEFAULT_MINIMUM_TEXT_HEIGHT_PX = 12.0
DEFAULT_FONT_FLOOR_PX = 12.0
DEFAULT_TIMEOUT_MS = 10_000
DEFAULT_SETTLE_MS = 100
MAX_LOCAL_STYLESHEET_BYTES = 5 * 1024 * 1024
THEME_STORAGE_KEY = "portfolio-theme"
SUPPORTED_THEMES = ("dark", "light")

PLAYWRIGHT_INSTALL_HINT = (
    "Install the renderer with: python -m pip install playwright && "
    "python -m playwright install chromium"
)

GATE_RULES = frozenset(
    {
        "parent-padding-escape",
        "svg-viewbox-overflow",
        "text-overlap",
        "horizontal-overflow",
        "fixed-text-max-width",
        "undersized-text-box",
        "font-size-floor",
    }
)


_DETECTOR_JS = r"""
({
  tolerance,
  minimumTextWidth,
  minimumTextHeight,
  fontFloor,
  viewportWidth,
  viewportHeight,
  allowlist,
  linkedStylesheets
}) => {
  const severityRank = { low: 1, medium: 2, high: 3, error: 4 };
  const findingsByElement = new Map();
  const invalidSelectorKeys = new Set();
  let suppressed = 0;

  const round = (value) => Number.isFinite(Number(value))
    ? Math.round(Number(value) * 100) / 100
    : value;

  const classText = (element) => {
    if (!element) return "";
    const value = element.className;
    if (typeof value === "string") return value;
    return value && typeof value.baseVal === "string" ? value.baseVal : "";
  };

  const revealSignature = (element) => {
    const signature = [
      classText(element),
      element.getAttribute && element.getAttribute("data-reveal"),
      element.getAttribute && element.getAttribute("data-scroll-reveal"),
      element.getAttribute && element.getAttribute("data-animate"),
      element.getAttribute && element.getAttribute("data-visibility")
    ].filter(Boolean).join(" ");
    return /(?:^|[\s_-])(?:reveal|scroll-reveal|fade-in|enter|in-view|intersection|pending)(?:$|[\s_-])/i.test(signature);
  };

  const hiddenByDesign = (element) => {
    let current = element;
    while (current && current.nodeType === Node.ELEMENT_NODE) {
      if (current.tagName === "DETAILS" && !current.open && current !== element) {
        const summary = Array.from(current.children).find((child) => child.tagName === "SUMMARY");
        if (!summary || (element !== summary && !summary.contains(element))) return true;
      }
      const style = getComputedStyle(current);
      if (
        current.hidden ||
        style.display === "none" ||
        style.visibility === "hidden" ||
        style.visibility === "collapse" ||
        style.contentVisibility === "hidden"
      ) return true;
      if (Number.parseFloat(style.opacity || "1") === 0 && revealSignature(current)) {
        return true;
      }
      current = current.parentElement;
    }
    return false;
  };

  const rendered = (element) => {
    if (!element || hiddenByDesign(element)) return false;
    const rect = element.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  };

  const ownText = (element) => Array.from(element.childNodes).some(
    (node) => node.nodeType === Node.TEXT_NODE && Boolean(node.textContent.trim())
  );
  const mediaTags = new Set(["img", "video", "canvas", "svg", "picture", "iframe", "object", "embed", "figure"]);
  const textTags = new Set(["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "figcaption", "dd", "dt", "label", "legend", "caption", "summary", "time", "address", "code"]);
  const containerNames = new Set(["container", "wrapper", "shell", "layout", "page", "frame", "viewport", "inner", "outer"]);
  const mediaNames = new Set(["media", "image", "video", "visual", "artwork", "illustration"]);
  const textNames = new Set(["copy", "text", "prose", "paragraph", "title", "subtitle", "heading", "headline", "description", "intro", "lead", "caption", "label", "message", "note", "summary"]);

  const nameTokens = (element) => {
    const names = [element.id || "", ...Array.from(element.classList || [])];
    return names.flatMap((name) => name.toLowerCase().split(/[-_]/).filter(Boolean));
  };

  const fixedWidthTextEvidence = (element) => {
    const tag = element.tagName.toLowerCase();
    if (mediaTags.has(tag)) return null;
    if (textTags.has(tag)) return "semantic-text-tag";
    if (ownText(element)) return "direct-text";
    const tokens = nameTokens(element);
    if (tokens.some((token) => textNames.has(token))) return "text-name";
    if (tokens.some((token) => containerNames.has(token) || mediaNames.has(token))) return null;
    return null;
  };

  const stableSelector = (element) => {
    if (element.id) return `#${CSS.escape(element.id)}`;
    const parts = [];
    let current = element;
    while (current && current.nodeType === Node.ELEMENT_NODE && current !== document.documentElement) {
      let part = current.tagName.toLowerCase();
      const parent = current.parentElement;
      if (parent) {
        const peers = Array.from(parent.children).filter(
          (peer) => peer.tagName === current.tagName
        );
        if (peers.length > 1) part += `:nth-of-type(${peers.indexOf(current) + 1})`;
      }
      parts.unshift(part);
      if (current === document.body) break;
      current = parent;
    }
    return parts.join(" > ");
  };

  const validatedAllowlist = [];
  for (const entry of allowlist) {
    try {
      document.querySelectorAll(entry.selector);
      validatedAllowlist.push(entry);
    } catch (error) {
      const key = `allowlist:${entry.selector}`;
      if (!invalidSelectorKeys.has(key)) {
        invalidSelectorKeys.add(key);
        findingsByElement.set(key, {
          rule: "selector-evaluation",
          severity: "error",
          selector: entry.selector,
          viewport: { width: viewportWidth, height: viewportHeight },
          measurements: { error: String(error && error.message ? error.message : error) },
          message: `Could not evaluate allowlist selector ${entry.selector}`
        });
      }
    }
  }

  const isAllowed = (element, rule) => validatedAllowlist.some((entry) => {
    if (entry.rule !== "*" && entry.rule !== rule) return false;
    if (entry.viewports && !entry.viewports.includes(viewportWidth)) return false;
    try {
      return element.matches(entry.selector);
    } catch (_) {
      return false;
    }
  });

  const addFinding = (rule, severity, element, measurements, message, selectorOverride = null) => {
    if (element && isAllowed(element, rule)) {
      suppressed += 1;
      return;
    }
    const selector = selectorOverride || stableSelector(element);
    const key = selectorOverride ? `selector:${selectorOverride}` : selector;
    const candidate = {
      rule,
      severity,
      selector,
      viewport: { width: viewportWidth, height: viewportHeight },
      measurements,
      message
    };
    const existing = findingsByElement.get(key);
    if (!existing || severityRank[severity] > severityRank[existing.severity]) {
      findingsByElement.set(key, candidate);
    }
  };

  const excludedTags = new Set([
    "SCRIPT", "STYLE", "LINK", "META", "TITLE", "NOSCRIPT", "TEMPLATE",
    "SOURCE", "TRACK", "DEFS", "CLIPPATH", "MASK", "PATTERN", "SYMBOL", "MARKER"
  ]);
  const allElements = Array.from(document.body ? document.body.querySelectorAll("*") : [])
    .filter((element) => !excludedTags.has(element.tagName) && rendered(element));
  const htmlElements = allElements.filter((element) => !element.closest("svg"));

  // Rule 1: a rendered child must stay inside the immediate parent's padding box.
  for (const element of htmlElements) {
    const parent = element.parentElement;
    if (!parent || parent === document.body || parent === document.documentElement || !rendered(parent)) continue;
    const parentStyle = getComputedStyle(parent);
    if (parentStyle.display === "contents") continue;
    const childRect = element.getBoundingClientRect();
    const parentRect = parent.getBoundingClientRect();
    const paddingBox = {
      left: parentRect.left + (Number.parseFloat(parentStyle.borderLeftWidth) || 0),
      top: parentRect.top + (Number.parseFloat(parentStyle.borderTopWidth) || 0),
      right: parentRect.right - (Number.parseFloat(parentStyle.borderRightWidth) || 0),
      bottom: parentRect.bottom - (Number.parseFloat(parentStyle.borderBottomWidth) || 0)
    };
    const parentHasHorizontalOverflow = parent.scrollWidth > parent.clientWidth + tolerance;
    const horizontalScroller = ["auto", "scroll"].includes(parentStyle.overflowX);
    const escapesLeft = !parentHasHorizontalOverflow && !horizontalScroller && childRect.left < paddingBox.left - tolerance;
    const escapesRight = !parentHasHorizontalOverflow && !horizontalScroller && childRect.right > paddingBox.right + tolerance;
    const escapesTop = childRect.top < paddingBox.top - tolerance;
    const escapesBottom = childRect.bottom > paddingBox.bottom + tolerance;
    if (escapesLeft || escapesRight || escapesTop || escapesBottom) {
      addFinding(
        "parent-padding-escape",
        "high",
        element,
        {
          child: {
            left: round(childRect.left), top: round(childRect.top),
            right: round(childRect.right), bottom: round(childRect.bottom)
          },
          parent_padding_box: {
            left: round(paddingBox.left), top: round(paddingBox.top),
            right: round(paddingBox.right), bottom: round(paddingBox.bottom)
          },
          excess_px: {
            left: round(Math.max(0, paddingBox.left - childRect.left)),
            right: round(Math.max(0, childRect.right - paddingBox.right)),
            top: round(Math.max(0, paddingBox.top - childRect.top)),
            bottom: round(Math.max(0, childRect.bottom - paddingBox.bottom))
          },
          tolerance_px: tolerance
        },
        "Element escapes its parent's padding box"
      );
    }
  }

  // Rule 2: SVG graphics must remain within the declared viewBox.
  const graphicSelector = "path,rect,circle,ellipse,line,polyline,polygon,text,image,use,foreignObject";
  for (const svg of Array.from(document.querySelectorAll("svg")).filter(rendered)) {
    const viewBox = svg.viewBox && svg.viewBox.baseVal;
    if (!viewBox || viewBox.width <= 0 || viewBox.height <= 0) continue;
    const bounds = {
      left: viewBox.x,
      top: viewBox.y,
      right: viewBox.x + viewBox.width,
      bottom: viewBox.y + viewBox.height
    };
    for (const graphic of Array.from(svg.querySelectorAll(graphicSelector)).filter(rendered)) {
      if (graphic.closest("defs,clipPath,mask,pattern,symbol,marker")) continue;
      let box;
      try {
        box = graphic.getBBox();
      } catch (_) {
        continue;
      }
      const graphicBounds = {
        left: box.x,
        top: box.y,
        right: box.x + box.width,
        bottom: box.y + box.height
      };
      const graphicRect = graphic.getBoundingClientRect();
      const svgRect = svg.getBoundingClientRect();
      const renderedOutside = (
        graphicRect.left < svgRect.left - tolerance ||
        graphicRect.top < svgRect.top - tolerance ||
        graphicRect.right > svgRect.right + tolerance ||
        graphicRect.bottom > svgRect.bottom + tolerance
      );
      if (
        graphicBounds.left < bounds.left - tolerance ||
        graphicBounds.top < bounds.top - tolerance ||
        graphicBounds.right > bounds.right + tolerance ||
        graphicBounds.bottom > bounds.bottom + tolerance ||
        renderedOutside
      ) {
        addFinding(
          "svg-viewbox-overflow",
          "high",
          graphic,
          {
            graphic_bbox: {
              left: round(graphicBounds.left), top: round(graphicBounds.top),
              right: round(graphicBounds.right), bottom: round(graphicBounds.bottom)
            },
            view_box: {
              left: round(bounds.left), top: round(bounds.top),
              right: round(bounds.right), bottom: round(bounds.bottom)
            },
            rendered_bbox_px: {
              left: round(graphicRect.left), top: round(graphicRect.top),
              right: round(graphicRect.right), bottom: round(graphicRect.bottom)
            },
            rendered_svg_box_px: {
              left: round(svgRect.left), top: round(svgRect.top),
              right: round(svgRect.right), bottom: round(svgRect.bottom)
            },
            tolerance_units: tolerance
          },
          "SVG content extends past its viewBox"
        );
      }
    }
  }

  // Rule 3: painted direct-text fragments must not occupy the same rendered area.
  const clippingOverflow = new Set(["auto", "clip", "hidden", "scroll"]);
  const clipToPaintedAncestors = (rect, element) => {
    const clipped = {
      left: rect.left,
      top: rect.top,
      right: rect.right,
      bottom: rect.bottom
    };
    let current = element;
    while (current && current !== document.documentElement) {
      const style = getComputedStyle(current);
      const overflowApplies = !["contents", "inline"].includes(style.display);
      const clipX = overflowApplies && clippingOverflow.has(style.overflowX);
      const clipY = overflowApplies && clippingOverflow.has(style.overflowY);
      if (clipX || clipY) {
        const currentRect = current.getBoundingClientRect();
        const clientBox = {
          left: currentRect.left + current.clientLeft,
          top: currentRect.top + current.clientTop,
          right: currentRect.left + current.clientLeft + current.clientWidth,
          bottom: currentRect.top + current.clientTop + current.clientHeight
        };
        if (clipX) {
          clipped.left = Math.max(clipped.left, clientBox.left);
          clipped.right = Math.min(clipped.right, clientBox.right);
        }
        if (clipY) {
          clipped.top = Math.max(clipped.top, clientBox.top);
          clipped.bottom = Math.min(clipped.bottom, clientBox.bottom);
        }
        if (clipped.right <= clipped.left || clipped.bottom <= clipped.top) return null;
      }
      current = current.parentElement;
    }
    return clipped;
  };
  const directTextFragments = (element) => Array.from(element.childNodes)
    .filter((node) => node.nodeType === Node.TEXT_NODE && Boolean(node.textContent.trim()))
    .flatMap((node) => {
      const range = document.createRange();
      range.selectNodeContents(node);
      return Array.from(range.getClientRects())
        .filter((rect) => rect.width > 0 && rect.height > 0)
        .map((rect) => clipToPaintedAncestors(rect, element))
        .filter(Boolean);
    });
  const textNodes = htmlElements
    .filter(ownText)
    .flatMap((element) => directTextFragments(element).map((rect) => ({ element, rect })))
    .sort((left, right) => left.rect.top - right.rect.top || left.rect.left - right.rect.left);
  for (let leftIndex = 0; leftIndex < textNodes.length; leftIndex += 1) {
    const left = textNodes[leftIndex];
    for (let rightIndex = leftIndex + 1; rightIndex < textNodes.length; rightIndex += 1) {
      const right = textNodes[rightIndex];
      if (right.rect.top >= left.rect.bottom - tolerance) break;
      if (left.element.contains(right.element) || right.element.contains(left.element)) continue;
      const overlapWidth = Math.min(left.rect.right, right.rect.right) - Math.max(left.rect.left, right.rect.left);
      const overlapHeight = Math.min(left.rect.bottom, right.rect.bottom) - Math.max(left.rect.top, right.rect.top);
      if (overlapWidth > tolerance && overlapHeight > tolerance) {
        addFinding(
          "text-overlap",
          "high",
          right.element,
          {
            other_selector: stableSelector(left.element),
            overlap_width_px: round(overlapWidth),
            overlap_height_px: round(overlapHeight),
            tolerance_px: tolerance
          },
          `Text box overlaps ${stableSelector(left.element)}`
        );
      }
    }
  }

  // Rule 4: overflow must provide a real horizontal scroller.
  for (const element of htmlElements) {
    if (element.clientWidth <= 0 || element.scrollWidth <= element.clientWidth + tolerance) continue;
    const style = getComputedStyle(element);
    if (["auto", "scroll"].includes(style.overflowX)) continue;
    const elementRect = element.getBoundingClientRect();
    const visibleOverflowingDescendant = Array.from(element.querySelectorAll("*")).some((descendant) => {
      if (!rendered(descendant)) return false;
      let intermediate = descendant.parentElement;
      while (intermediate && intermediate !== element) {
        if (["auto", "scroll"].includes(getComputedStyle(intermediate).overflowX)) return false;
        intermediate = intermediate.parentElement;
      }
      const descendantRect = descendant.getBoundingClientRect();
      return (
        descendantRect.left < elementRect.left - tolerance ||
        descendantRect.right > elementRect.right + tolerance
      );
    });
    if (!ownText(element) && !visibleOverflowingDescendant) continue;
    addFinding(
      "horizontal-overflow",
      "high",
      element,
      {
        client_width_px: round(element.clientWidth),
        scroll_width_px: round(element.scrollWidth),
        excess_px: round(element.scrollWidth - element.clientWidth),
        overflow_x: style.overflowX,
        tolerance_px: tolerance
      },
      "Content overflows horizontally without an overflow-x scroller"
    );
  }

  // Collect active fixed-unit max-width declarations once, then match them.
  const fixedWidthPattern = /(?:^|[^a-z0-9_-])(?:\d+(?:\.\d+)?|\.\d+)\s*(?:px|ch)\b/i;
  const variableWidthPattern = /\bvar\(/i;
  const variableReferencePattern = /var\(\s*(--[a-z0-9_-]+)/gi;
  const resolveFixedWidth = (element, value, seen = new Set()) => {
    const source = String(value || "").trim();
    if (!source) return null;
    if (fixedWidthPattern.test(source)) return source;
    for (const match of source.matchAll(variableReferencePattern)) {
      const name = match[1];
      if (seen.has(name)) continue;
      const nextSeen = new Set(seen);
      nextSeen.add(name);
      const resolved = getComputedStyle(element).getPropertyValue(name).trim();
      const fixed = resolveFixedWidth(element, resolved, nextSeen);
      if (fixed) return `${source} -> ${name}: ${fixed}`;
    }
    return null;
  };
  const fixedRules = [];
  const visitRules = (rules) => {
    for (const rule of Array.from(rules || [])) {
      if (rule.type === CSSRule.STYLE_RULE) {
        const value = rule.style && rule.style.getPropertyValue("max-width");
        if (value && (fixedWidthPattern.test(value) || variableWidthPattern.test(value))) {
          fixedRules.push({ selector: rule.selectorText, value: value.trim() });
        }
        continue;
      }
      if (!rule.cssRules) continue;
      if (rule.type === CSSRule.MEDIA_RULE && !window.matchMedia(rule.conditionText).matches) continue;
      if (rule.type === CSSRule.SUPPORTS_RULE && !CSS.supports(rule.conditionText)) continue;
      visitRules(rule.cssRules);
    }
  };
  for (const sheet of Array.from(document.styleSheets)) {
    try {
      visitRules(sheet.cssRules);
    } catch (_) {
      // Cross-origin sheets cannot be inspected. The offline route blocks them,
      // and their absence is reflected by the page's computed layout.
    }
  }
  for (const linked of linkedStylesheets || []) {
    if (linked.error) {
      addFinding(
        "stylesheet-evaluation",
        "error",
        null,
        { href: linked.href, error: linked.error },
        `Could not inspect local stylesheet ${linked.href}`,
        linked.href
      );
      continue;
    }
    try {
      const sheet = new CSSStyleSheet();
      sheet.replaceSync(linked.source);
      visitRules(sheet.cssRules);
    } catch (error) {
      addFinding(
        "stylesheet-evaluation",
        "error",
        null,
        { href: linked.href, error: String(error && error.message ? error.message : error) },
        `Could not parse local stylesheet ${linked.href}`,
        linked.href
      );
    }
  }

  // Rule 5: text must not be capped by a fixed px/ch max-width declaration.
  for (const element of htmlElements) {
    const textEvidence = fixedWidthTextEvidence(element);
    if (!textEvidence) continue;
    const declarations = [];
    const inlineValue = element.style && element.style.getPropertyValue("max-width");
    const resolvedInlineValue = resolveFixedWidth(element, inlineValue);
    if (resolvedInlineValue) {
      declarations.push({ selector: "[style]", value: inlineValue.trim(), resolved_value: resolvedInlineValue });
    }
    for (const rule of fixedRules) {
      try {
        if (element.matches(rule.selector)) {
          const resolvedRuleValue = resolveFixedWidth(element, rule.value);
          if (resolvedRuleValue) declarations.push({ ...rule, resolved_value: resolvedRuleValue });
        }
      } catch (error) {
        const key = `stylesheet:${rule.selector}`;
        if (!invalidSelectorKeys.has(key)) {
          invalidSelectorKeys.add(key);
          addFinding(
            "selector-evaluation",
            "error",
            null,
            { error: String(error && error.message ? error.message : error) },
            `Could not evaluate stylesheet selector ${rule.selector}`,
            rule.selector
          );
        }
      }
    }
    if (!declarations.length || getComputedStyle(element).maxWidth === "none") continue;
    addFinding(
      "fixed-text-max-width",
      "high",
      element,
      {
        declarations,
        text_evidence: textEvidence,
        computed_max_width: getComputedStyle(element).maxWidth,
        rendered_width_px: round(element.getBoundingClientRect().width)
      },
      `Text-bearing element uses fixed max-width ${declarations[0].value}`
    );
  }

  // aria-hidden content still participates in pixel geometry checks above, but
  // decorative text intentionally removed from the accessibility tree does not
  // establish a semantic legibility floor.
  const semanticTextElements = htmlElements.filter(
    (element) => ownText(element) && !element.closest('[aria-hidden="true"]')
  );

  // Rule 6: a non-inline rendered box holding text must meet the minimum size.
  for (const element of semanticTextElements) {
    const style = getComputedStyle(element);
    if (style.display === "inline") continue;
    const rect = element.getBoundingClientRect();
    if (rect.width < minimumTextWidth - tolerance || rect.height < minimumTextHeight - tolerance) {
      addFinding(
        "undersized-text-box",
        "high",
        element,
        {
          width_px: round(rect.width),
          height_px: round(rect.height),
          minimum_width_px: minimumTextWidth,
          minimum_height_px: minimumTextHeight,
          tolerance_px: tolerance
        },
        "Rendered text box is smaller than the configured minimum"
      );
    }
  }

  // Rule 7: directly rendered text must remain above the legibility floor.
  for (const element of semanticTextElements) {
    const size = Number.parseFloat(getComputedStyle(element).fontSize);
    if (Number.isFinite(size) && size < fontFloor - tolerance) {
      addFinding(
        "font-size-floor",
        "high",
        element,
        {
          computed_font_size_px: round(size),
          floor_px: fontFloor,
          tolerance_px: tolerance
        },
        "Computed font-size is below the legibility floor"
      );
    }
  }

  return {
    findings: Array.from(findingsByElement.values()),
    suppressed
  };
}
"""


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def _non_negative_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed < 0:
        raise argparse.ArgumentTypeError("must be a finite number zero or greater")
    return parsed


def _positive_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed <= 0:
        raise argparse.ArgumentTypeError("must be a finite number greater than zero")
    return parsed


def _fragment(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]*", value):
        raise argparse.ArgumentTypeError(
            "fragment must be a non-empty local element id without '#', '/', or '?'"
        )
    return value


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render local HTML and detect deterministic visual defects."
    )
    parser.add_argument("html", help="local HTML file to inspect")
    parser.add_argument(
        "--viewports",
        nargs="+",
        type=_positive_int,
        default=list(DEFAULT_VIEWPORTS),
        metavar="WIDTH",
        help="viewport widths in pixels (default: 420 900 1440)",
    )
    parser.add_argument(
        "--height",
        type=_positive_int,
        default=DEFAULT_VIEWPORT_HEIGHT,
        help=f"viewport height in pixels (default: {DEFAULT_VIEWPORT_HEIGHT})",
    )
    parser.add_argument(
        "--tolerance",
        type=_non_negative_float,
        default=DEFAULT_TOLERANCE_PX,
        help=f"geometry tolerance in pixels (default: {DEFAULT_TOLERANCE_PX:g})",
    )
    parser.add_argument("--allowlist", type=Path, help="JSON file of recorded exceptions")
    parser.add_argument(
        "--minimum-text-width",
        type=_positive_float,
        default=DEFAULT_MINIMUM_TEXT_WIDTH_PX,
        help="minimum rendered width for a non-inline text box",
    )
    parser.add_argument(
        "--minimum-text-height",
        type=_positive_float,
        default=DEFAULT_MINIMUM_TEXT_HEIGHT_PX,
        help="minimum rendered height for a non-inline text box",
    )
    parser.add_argument(
        "--font-floor",
        type=_positive_float,
        default=DEFAULT_FONT_FLOOR_PX,
        help="minimum computed font-size in pixels",
    )
    parser.add_argument(
        "--timeout-ms",
        type=_positive_int,
        default=DEFAULT_TIMEOUT_MS,
        help="local page-load timeout",
    )
    parser.add_argument(
        "--settle-ms",
        type=_non_negative_float,
        default=DEFAULT_SETTLE_MS,
        help="delay after load before measurement",
    )
    parser.add_argument(
        "--theme",
        choices=SUPPORTED_THEMES,
        help="seed the Nexus-Hub guide theme before page scripts run",
    )
    parser.add_argument(
        "--fragment",
        type=_fragment,
        help="activate a hash-routed local page by element id, e.g. foundations",
    )
    return parser.parse_args(argv)


def _base_report(path: Path, args: argparse.Namespace) -> dict[str, Any]:
    return {
        "status": "pass",
        "file": str(path.resolve()),
        "viewports": [
            {"width": width, "height": args.height} for width in args.viewports
        ],
        "tolerance_px": args.tolerance,
        "minimum_text_box_px": {
            "width": args.minimum_text_width,
            "height": args.minimum_text_height,
        },
        "font_floor_px": args.font_floor,
        "theme": args.theme,
        "fragment": args.fragment,
        "allowlist": str(args.allowlist.resolve()) if args.allowlist else None,
        "findings": [],
        "gate_findings": 0,
        "suppressed_findings": 0,
        "page_pass": True,
    }


def _finding(
    rule: str,
    message: str,
    *,
    selector: str,
    viewport: dict[str, int] | None,
    measurements: dict[str, Any],
    severity: str = "error",
) -> dict[str, Any]:
    return {
        "rule": rule,
        "severity": severity,
        "selector": selector,
        "viewport": viewport,
        "measurements": measurements,
        "message": message,
    }


def _error_text(error: BaseException) -> str:
    text = " ".join(str(error).split())
    return text[:500] if text else error.__class__.__name__


def _load_allowlist(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ValueError(f"cannot read allowlist {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"allowlist is not valid JSON: {error}") from error

    if isinstance(payload, dict):
        entries = payload.get("allow")
    else:
        entries = payload
    if not isinstance(entries, list):
        raise TypeError("allowlist must be an array or an object with an 'allow' array")

    normalized: list[dict[str, Any]] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise TypeError(f"allowlist entry {index} must be an object")
        rule = entry.get("rule")
        selector = entry.get("selector")
        reason = entry.get("reason")
        if rule not in GATE_RULES and rule != "*":
            raise ValueError(f"allowlist entry {index} has unknown rule {rule!r}")
        if not isinstance(selector, str) or not selector.strip():
            raise ValueError(f"allowlist entry {index} needs a non-empty selector")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"allowlist entry {index} needs a non-empty reason")

        viewport_value = entry.get("viewport")
        if viewport_value is None or viewport_value == "*":
            viewports = None
        elif isinstance(viewport_value, int) and viewport_value > 0:
            viewports = [viewport_value]
        elif (
            isinstance(viewport_value, list)
            and viewport_value
            and all(isinstance(value, int) and value > 0 for value in viewport_value)
        ):
            viewports = viewport_value
        else:
            raise ValueError(
                f"allowlist entry {index} viewport must be '*', a positive integer, "
                "or a non-empty array of positive integers"
            )
        normalized.append(
            {
                "rule": rule,
                "selector": selector.strip(),
                "reason": reason.strip(),
                "viewports": viewports,
            }
        )
    return normalized


def _scan_viewport(
    page: Any,
    file_uri: str,
    *,
    width: int,
    height: int,
    tolerance: float,
    minimum_text_width: float,
    minimum_text_height: float,
    font_floor: float,
    allowlist: list[dict[str, Any]],
    timeout_ms: int,
    settle_ms: float,
    theme: str | None = None,
) -> dict[str, Any]:
    """Load and measure one viewport, returning findings instead of raising."""
    viewport = {"width": width, "height": height}
    if theme is not None:
        try:
            page.add_init_script(
                "try {"
                f"localStorage.setItem({json.dumps(THEME_STORAGE_KEY)}, {json.dumps(theme)});"
                "window.__nexusVisualDetectorThemeSeeded = true;"
                "} catch (error) {"
                "window.__nexusVisualDetectorThemeSeeded = String("
                "error && error.message ? error.message : error);"
                "}"
            )
        except Exception as error:  # noqa: BLE001 - requested theme is a gate contract
            return {
                "findings": [
                    _finding(
                        "theme-setup",
                        "Could not seed the requested guide theme",
                        selector="<document>",
                        viewport=viewport,
                        measurements={
                            "requested_theme": theme,
                            "error": _error_text(error),
                        },
                    )
                ],
                "suppressed": 0,
            }
    try:
        page.goto(file_uri, wait_until="load", timeout=timeout_ms)
    except Exception as error:  # noqa: BLE001 - a failed load is a gate finding
        return {
            "findings": [
                _finding(
                    "page-load",
                    "Page failed to load",
                    selector="<document>",
                    viewport=viewport,
                    measurements={"error": _error_text(error)},
                )
            ],
            "suppressed": 0,
        }

    if theme is not None:
        try:
            theme_state = page.evaluate(
                "() => [window.__nexusVisualDetectorThemeSeeded || false, "
                "document.documentElement.getAttribute('data-theme')]"
            )
        except Exception as error:  # noqa: BLE001 - requested theme is a gate contract
            theme_state = [_error_text(error), None]
        if theme_state != [True, theme]:
            return {
                "findings": [
                    _finding(
                        "theme-setup",
                        "Loaded document did not honor the requested guide theme",
                        selector="<document>",
                        viewport=viewport,
                        measurements={
                            "requested_theme": theme,
                            "actual_theme": theme_state[1]
                            if isinstance(theme_state, list) and len(theme_state) > 1
                            else None,
                            "storage_state": theme_state[0]
                            if isinstance(theme_state, list) and theme_state
                            else "theme state was not an array",
                        },
                    )
                ],
                "suppressed": 0,
            }

    if settle_ms:
        page.wait_for_timeout(settle_ms)
    fragment = urlsplit(file_uri).fragment
    if fragment:
        try:
            fragment_state = page.evaluate(
                """
                (fragment) => {
                  const candidates = [
                    document.getElementById(fragment),
                    document.getElementById(`page-${fragment}`),
                    ...Array.from(document.querySelectorAll('[data-page]')).filter(
                      (element) => element.getAttribute('data-page') === fragment,
                    ),
                  ].filter((element, index, values) =>
                    element && values.indexOf(element) === index
                  );
                  const visible = candidates.find((element) => {
                    const style = getComputedStyle(element);
                    const rect = element.getBoundingClientRect();
                    return style.display !== 'none'
                      && style.visibility !== 'hidden'
                      && rect.width > 0
                      && rect.height > 0;
                  });
                  return {
                    exists: candidates.length > 0,
                    visible: Boolean(visible),
                    matched: candidates.map((element) => ({
                      id: element.id || null,
                      page: element.getAttribute('data-page'),
                    })),
                  };
                }
                """,
                fragment,
            )
        except Exception as error:  # noqa: BLE001 - fragment proof is a gate contract
            fragment_state = {"exists": False, "visible": False, "error": _error_text(error)}
        if not fragment_state.get("exists") or not fragment_state.get("visible"):
            return {
                "findings": [
                    _finding(
                        "fragment-target",
                        "Requested hash-routed target did not exist or become visible",
                        selector=f"#{fragment}",
                        viewport=viewport,
                        measurements={"fragment": fragment, **fragment_state},
                    )
                ],
                "suppressed": 0,
            }
    linked_stylesheets = _read_linked_local_stylesheets(page)
    try:
        return page.evaluate(
            _DETECTOR_JS,
            {
                "tolerance": tolerance,
                "minimumTextWidth": minimum_text_width,
                "minimumTextHeight": minimum_text_height,
                "fontFloor": font_floor,
                "viewportWidth": width,
                "viewportHeight": height,
                "allowlist": allowlist,
                "linkedStylesheets": linked_stylesheets,
            },
        )
    except Exception as error:  # noqa: BLE001 - evaluation failure must be visible
        return {
            "findings": [
                _finding(
                    "detector-evaluation",
                    "Could not evaluate visual-defect selectors",
                    selector="<document>",
                    viewport=viewport,
                    measurements={"error": _error_text(error)},
                )
            ],
            "suppressed": 0,
        }


def _read_linked_local_stylesheets(page: Any) -> list[dict[str, str]]:
    """Return bounded local linked CSS without relaxing browser file isolation."""
    try:
        hrefs = page.eval_on_selector_all(
            'link[rel~="stylesheet"][href]',
            "(links) => links.map((link) => link.href)",
        )
    except Exception as error:  # noqa: BLE001 - inspection failure must be visible
        return [{"href": "<document>", "error": _error_text(error)}]

    linked_stylesheets: list[dict[str, str]] = []
    seen: set[Path] = set()
    for href in hrefs:
        if not isinstance(href, str):
            continue
        parsed = urlsplit(href)
        if parsed.scheme.lower() != "file":
            continue
        try:
            path_text = url2pathname(parsed.path)
            if parsed.netloc:
                path_text = f"//{parsed.netloc}{path_text}"
            path = Path(path_text).resolve(strict=True)
            if path in seen:
                continue
            seen.add(path)
            size = path.stat().st_size
            if size > MAX_LOCAL_STYLESHEET_BYTES:
                raise ValueError(
                    f"stylesheet is {size} bytes; limit is {MAX_LOCAL_STYLESHEET_BYTES}"
                )
            source = path.read_bytes().decode("utf-8-sig", errors="replace")
        except (OSError, ValueError) as error:
            linked_stylesheets.append({"href": href, "error": _error_text(error)})
            continue
        linked_stylesheets.append({"href": href, "source": source})
    return linked_stylesheets


def _route_local_only(route: Any) -> None:
    scheme = urlsplit(route.request.url).scheme.lower()
    if scheme in {"file", "data", "blob", "about"}:
        route.continue_()
    else:
        route.abort("blockedbyclient")


def _run_detector(
    path: Path,
    args: argparse.Namespace,
    allowlist: list[dict[str, Any]],
) -> tuple[dict[str, Any], int]:
    report = _base_report(path, args)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        report.update(
            {
                "status": "cannot-run",
                "findings": [
                    _finding(
                        "renderer-unavailable",
                        PLAYWRIGHT_INSTALL_HINT,
                        selector="<renderer>",
                        viewport=None,
                        measurements={"playwright_importable": False},
                    )
                ],
                "gate_findings": 1,
                "page_pass": False,
            }
        )
        return report, 3

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                file_uri = path.resolve().as_uri()
                if args.fragment:
                    file_uri = f"{file_uri}#{args.fragment}"
                for width in args.viewports:
                    context = browser.new_context(
                        viewport={"width": width, "height": args.height},
                        reduced_motion="reduce",
                    )
                    try:
                        context.route("**/*", _route_local_only)
                        page = context.new_page()
                        result = _scan_viewport(
                            page,
                            file_uri,
                            width=width,
                            height=args.height,
                            tolerance=args.tolerance,
                            minimum_text_width=args.minimum_text_width,
                            minimum_text_height=args.minimum_text_height,
                            font_floor=args.font_floor,
                            allowlist=allowlist,
                            timeout_ms=args.timeout_ms,
                            settle_ms=args.settle_ms,
                            theme=args.theme,
                        )
                        report["findings"].extend(result["findings"])
                        report["suppressed_findings"] += int(result["suppressed"])
                    finally:
                        context.close()
            finally:
                browser.close()
    except Exception as error:  # noqa: BLE001 - launch failure is a cannot-run state
        report.update(
            {
                "status": "cannot-run",
                "findings": [
                    _finding(
                        "renderer-unavailable",
                        f"Chromium could not launch. {PLAYWRIGHT_INSTALL_HINT}",
                        selector="<renderer>",
                        viewport=None,
                        measurements={
                            "playwright_importable": True,
                            "error": _error_text(error),
                        },
                    )
                ],
                "gate_findings": 1,
                "page_pass": False,
            }
        )
        return report, 3

    report["gate_findings"] = len(report["findings"])
    report["page_pass"] = report["gate_findings"] == 0
    report["status"] = "pass" if report["page_pass"] else "fail"
    return report, 0 if report["page_pass"] else 1


def _emit(report: dict[str, Any]) -> None:
    print(json.dumps(report, indent=2, sort_keys=True))
    for finding in report["findings"]:
        viewport = finding.get("viewport")
        viewport_label = (
            f"{viewport['width']}x{viewport['height']}" if viewport else "no viewport"
        )
        print(
            f"[{finding['severity'].upper()}] {finding['rule']} at "
            f"{finding['selector']} ({viewport_label}): {finding['message']}",
            file=sys.stderr,
        )
    verdict = "PASS" if report["page_pass"] else report["status"].upper()
    print(
        f"{verdict} visual-defect detector: {report['gate_findings']} finding(s), "
        f"{report['suppressed_findings']} allowlisted",
        file=sys.stderr,
    )


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    path = Path(args.html)
    if not path.is_file():
        report = _base_report(path, args)
        report.update(
            {
                "status": "input-error",
                "findings": [
                    _finding(
                        "input-error",
                        f"HTML file not found: {path}",
                        selector="<input>",
                        viewport=None,
                        measurements={"path": str(path)},
                    )
                ],
                "gate_findings": 1,
                "page_pass": False,
            }
        )
        _emit(report)
        return 2

    try:
        allowlist = _load_allowlist(args.allowlist)
    except (TypeError, ValueError) as error:
        report = _base_report(path, args)
        report.update(
            {
                "status": "input-error",
                "findings": [
                    _finding(
                        "input-error",
                        str(error),
                        selector="<allowlist>",
                        viewport=None,
                        measurements={},
                    )
                ],
                "gate_findings": 1,
                "page_pass": False,
            }
        )
        _emit(report)
        return 2

    report, exit_code = _run_detector(path, args, allowlist)
    _emit(report)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
