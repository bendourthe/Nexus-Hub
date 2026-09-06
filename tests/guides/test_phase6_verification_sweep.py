"""Fail-closed rendered verification for the v4.4 guide Phase 6 sweep."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

GUIDE = Path(__file__).resolve().parents[2] / "guides" / "website" / "nexus-hub-guide.html"
GUIDE_README = GUIDE.with_name("README.md")
PAGES = ("home", "foundations", "training", "cheatsheets")
THEMES = ("dark", "light")
# v4.4.1 Phase 2 widened this set. 720 and 721 straddle the narrow-layout breakpoint so an
# off-by-one error is caught on the pixel where it happens, not averaged away between 420 and 900.
WIDTHS = (320, 420, 720, 721, 900, 1440)
TRAINING_SCENES = (
    "describe",
    "review",
    "plan",
    "implement",
    "compare",
    "test",
    "update",
    "presentify",
)


def test_browser_verification_docs_match_required_ci_contract() -> None:
    readme = GUIDE_README.read_text(encoding="utf-8")

    assert "CI does not currently require it" not in readme
    for contract in ("required `guide-render` job", "NEXUS_REQUIRE_RENDER=1", "`ci-required`"):
        assert contract in readme


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
    except Exception as error:  # noqa: BLE001 - render_gate classifies launch failures
        render_gate(  # type: ignore[operator]
            f"Playwright Chromium cannot launch: {error}"
        )


PAGE_AUDIT = r"""
() => {
  function parseColor(value) {
    const serialized = String(value);
    const channels = serialized.match(/[\d.]+/g);
    if (!channels || channels.length < 3) return null;
    const normalizedSrgb = /^color\(srgb\s/i.test(serialized);
    return {
      red: Number(channels[0]) * (normalizedSrgb ? 255 : 1),
      green: Number(channels[1]) * (normalizedSrgb ? 255 : 1),
      blue: Number(channels[2]) * (normalizedSrgb ? 255 : 1),
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

  function luminance(color) {
    const channels = [color.red, color.green, color.blue].map((channel) => {
      const normalized = channel / 255;
      return normalized <= 0.04045
        ? normalized / 12.92
        : ((normalized + 0.055) / 1.055) ** 2.4;
    });
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
  }

  function contrast(first, second) {
    const one = luminance(first);
    const two = luminance(second);
    return (Math.max(one, two) + 0.05) / (Math.min(one, two) + 0.05);
  }

  function opacityThrough(element) {
    let opacity = 1;
    for (let node = element; node; node = node.parentElement) {
      const value = Number.parseFloat(getComputedStyle(node).opacity);
      opacity *= Number.isFinite(value) ? value : 1;
    }
    return opacity;
  }

  function effectiveBackground(element) {
    const ancestors = [];
    for (let node = element; node; node = node.parentElement) ancestors.unshift(node);
    let cumulativeOpacity = 1;
    return ancestors.reduce((background, node) => {
      const style = getComputedStyle(node);
      const nodeOpacity = Number.parseFloat(style.opacity);
      cumulativeOpacity *= Number.isFinite(nodeOpacity) ? nodeOpacity : 1;
      const color = parseColor(style.backgroundColor);
      if (!color) throw new Error(`Unsupported computed background: ${style.backgroundColor}`);
      color.alpha *= cumulativeOpacity;
      return composite(color, background);
    }, {red: 255, green: 255, blue: 255, alpha: 1});
  }

  function hasVisibleTextRect(node) {
    const range = document.createRange();
    range.selectNodeContents(node);
    return Array.from(range.getClientRects()).some(
      (rect) => rect.width > 0.25 && rect.height > 0.25
    );
  }

  function elementLabel(element) {
    const id = element.id ? `#${element.id}` : "";
    const classes = Array.from(element.classList || []).slice(0, 3);
    const className = classes.length ? `.${classes.join(".")}` : "";
    const dataName = element.getAttribute && element.getAttribute("data-nht");
    return `${element.tagName.toLowerCase()}${id}${className}${dataName ? `[data-nht=${dataName}]` : ""}`;
  }

  const activePage = document.querySelector(".page.active");
  const header = document.querySelector(".site-header");
  if (!activePage || !header) throw new Error("Guide route did not expose the active page and header");
  const elements = [];
  const seen = new Set();
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walker.nextNode())) {
    if (!node.textContent || !node.textContent.trim()) continue;
    const element = node.parentElement;
    if (!element || seen.has(element)) continue;
    if (!element.closest(".site-header, .page.active")) continue;
    if (element.closest("script, style, template, noscript, [hidden], [aria-hidden=true]")) continue;
    const style = getComputedStyle(element);
    if (style.display === "none" || style.visibility !== "visible") continue;
    if (opacityThrough(element) <= 0.01 || !hasVisibleTextRect(node)) continue;
    seen.add(element);
    elements.push(element);
  }

  const samples = [];
  const unsupported = [];
  const colorKey = (color) => [color.red, color.green, color.blue, color.alpha]
    .map((value) => Number(value).toFixed(2)).join(",");

  function addTextSample(element, style, text, pseudo) {
    const isSvgText = !pseudo && element.namespaceURI === "http://www.w3.org/2000/svg";
    const sourceColor = isSvgText && style.fill !== "none" ? style.fill : style.color;
    const foreground = parseColor(sourceColor);
    if (!foreground) {
      unsupported.push({
        element: elementLabel(element) + (pseudo || ""),
        color: sourceColor,
      });
      return;
    }
    let background = effectiveBackground(element);
    const pseudoOpacity = pseudo ? Number.parseFloat(style.opacity) : 1;
    const opacity = opacityThrough(element)
      * (Number.isFinite(pseudoOpacity) ? pseudoOpacity : 1);
    if (pseudo) {
      const pseudoBackground = parseColor(style.backgroundColor);
      if (!pseudoBackground) {
        unsupported.push({
          element: elementLabel(element) + pseudo,
          color: style.backgroundColor,
        });
        return;
      }
      pseudoBackground.alpha *= opacity;
      background = composite(pseudoBackground, background);
    }
    foreground.alpha *= opacity;
    const paintedForeground = composite(foreground, background);
    const fontSize = Number.parseFloat(style.fontSize);
    const parsedWeight = Number.parseInt(style.fontWeight, 10);
    const fontWeight = Number.isFinite(parsedWeight)
      ? parsedWeight
      : (style.fontWeight === "bold" ? 700 : 400);
    const large = fontSize >= 24 || (fontSize >= 18.66 && fontWeight >= 700);
    const threshold = large ? 3 : 4.5;
    const ratio = contrast(paintedForeground, background);
    samples.push({
      element: elementLabel(element) + (pseudo || ""),
      text: text.slice(0, 90),
      pseudo: Boolean(pseudo),
      ratio,
      threshold,
      fontSize,
      fontWeight,
      foreground: colorKey(paintedForeground),
      background: colorKey(background),
      styleKey: [
        colorKey(paintedForeground),
        colorKey(background),
        style.fontFamily,
        style.fontSize,
        style.fontWeight,
        style.lineHeight,
        style.letterSpacing,
        style.textTransform,
      ].join("|"),
    });
  }

  for (const element of elements) {
    const directText = Array.from(element.childNodes)
      .filter((child) => child.nodeType === Node.TEXT_NODE)
      .map((child) => child.textContent || "")
      .join(" ")
      .replace(/\s+/g, " ")
      .trim();
    addTextSample(element, getComputedStyle(element), directText, "");
  }

  function generatedText(style) {
    const content = String(style.content || "").trim();
    if (!content || content === "none" || content === "normal"
        || content === '""' || content === "''" || /^url\(/i.test(content)) {
      return "";
    }
    if ((content.startsWith('"') && content.endsWith('"'))
        || (content.startsWith("'") && content.endsWith("'"))) {
      return content.slice(1, -1).replace(/\\([\\"'])/g, "$1").trim();
    }
    return content;
  }

  const pseudoHosts = Array.from(new Set([
    header,
    ...header.querySelectorAll("*"),
    activePage,
    ...activePage.querySelectorAll("*"),
  ]));
  for (const element of pseudoHosts) {
    if (element.closest("script, style, template, noscript, [hidden], [aria-hidden=true]")) continue;
    const hostStyle = getComputedStyle(element);
    const hostRect = element.getBoundingClientRect();
    if (hostStyle.display === "none" || hostStyle.visibility !== "visible"
        || opacityThrough(element) <= 0.01 || hostRect.width <= 0 || hostRect.height <= 0) {
      continue;
    }
    for (const pseudo of ["::before", "::after"]) {
      const style = getComputedStyle(element, pseudo);
      const text = generatedText(style);
      const pseudoOpacity = Number.parseFloat(style.opacity);
      if (!text || style.display === "none" || style.visibility !== "visible"
          || (Number.isFinite(pseudoOpacity) && pseudoOpacity <= 0.01)) continue;
      addTextSample(element, style, text, pseudo);
    }
  }

  const progressDots = Array.from(activePage.querySelectorAll("[data-progress] a"))
    .map((anchor) => {
      const rect = anchor.getBoundingClientRect();
      const dotStyle = getComputedStyle(anchor, "::before");
      const background = effectiveBackground(anchor);
      const dot = parseColor(dotStyle.backgroundColor);
      if (!dot) {
        return {
          label: anchor.getAttribute("aria-label"),
          active: anchor.matches(".on"),
          width: rect.width,
          height: rect.height,
          error: `Unsupported dot color: ${dotStyle.backgroundColor}`,
        };
      }
      const dotOpacity = Number.parseFloat(dotStyle.opacity);
      dot.alpha *= opacityThrough(anchor)
        * (Number.isFinite(dotOpacity) ? dotOpacity : 1);
      const paintedDot = composite(dot, background);
      return {
        label: anchor.getAttribute("aria-label"),
        active: anchor.matches(".on"),
        width: rect.width,
        height: rect.height,
        ratio: contrast(paintedDot, background),
        foreground: colorKey(paintedDot),
        background: colorKey(background),
      };
    });

  const documentWidth = Math.max(
    document.documentElement.scrollWidth,
    document.body ? document.body.scrollWidth : 0
  );
  return {
    route: activePage.getAttribute("data-page"),
    theme: document.documentElement.getAttribute("data-theme"),
    viewportWidth: window.innerWidth,
    documentWidth,
    sampledElements: samples.length,
    pseudoSampledElements: samples.filter((sample) => sample.pseudo).length,
    styleKeys: Array.from(new Set(samples.map((sample) => sample.styleKey))),
    progressDots,
    lowContrast: samples
      .filter((sample) => sample.ratio + 0.001 < sample.threshold)
      .map((sample) => ({
        element: sample.element,
        text: sample.text,
        ratio: Number(sample.ratio.toFixed(3)),
        threshold: sample.threshold,
        fontSize: sample.fontSize,
        fontWeight: sample.fontWeight,
        foreground: sample.foreground,
        background: sample.background,
      })),
    unsupported,
  };
}
"""


def _page_errors(page: Any) -> tuple[list[str], list[str]]:
    console_errors: list[str] = []
    runtime_errors: list[str] = []
    page.on(
        "console",
        lambda message: console_errors.append(message.text)
        if message.type == "error"
        else None,
    )
    page.on("pageerror", lambda error: runtime_errors.append(str(error)))
    return console_errors, runtime_errors


def _collect_audit_failures(
    failures: list[str],
    audit: dict[str, Any],
    case: str,
    expected_route: str,
    expected_theme: str,
) -> None:
    if audit["route"] != expected_route:
        failures.append(f"{case}: active route is {audit['route']!r}")
    if audit["theme"] != expected_theme:
        failures.append(f"{case}: applied theme is {audit['theme']!r}")
    if audit["documentWidth"] > audit["viewportWidth"] + 1:
        failures.append(
            f"{case}: horizontal document overflow "
            f"{audit['documentWidth']} > {audit['viewportWidth']}"
        )
    if audit["sampledElements"] == 0:
        failures.append(f"{case}: sampled no visible text")
    if audit["unsupported"]:
        failures.append(
            f"{case}: unsupported computed colors: {audit['unsupported'][:8]}"
        )
    if audit["lowContrast"]:
        failures.append(
            f"{case}: WCAG AA failures: {audit['lowContrast'][:12]}"
        )

    progress_dots = audit["progressDots"]
    if len(progress_dots) != len(PAGES):
        failures.append(
            f"{case}: expected {len(PAGES)} progress-dot anchors, "
            f"found {len(progress_dots)}"
        )
        return
    if sum(bool(dot["active"]) for dot in progress_dots) != 1:
        failures.append(f"{case}: progress dots must expose exactly one active state")
    for dot in progress_dots:
        label = dot.get("label") or "unlabelled progress dot"
        if "error" in dot:
            failures.append(f"{case}: {label}: {dot['error']}")
            continue
        if dot["width"] + 0.01 < 24 or dot["height"] + 0.01 < 24:
            failures.append(
                f"{case}: {label} target is {dot['width']}x{dot['height']}; "
                "expected at least 24x24"
            )
        if dot["ratio"] + 0.001 < 3:
            state = "active" if dot["active"] else "inactive"
            failures.append(
                f"{case}: {label} {state} dot contrast is "
                f"{dot['ratio']:.3f}:1; expected at least 3:1 "
                f"({dot['foreground']} on {dot['background']})"
            )


def test_all_pages_meet_contrast_and_overflow_matrix(render_gate: object) -> None:
    """Measure every rendered text element in a settled reduced-motion layout."""
    _require_browser(render_gate)
    from playwright.sync_api import sync_playwright

    guide_url = GUIDE.resolve().as_uri()
    failures: list[str] = []
    measurements: dict[str, dict[str, dict[str, object]]] = {
        theme: {
            route: {
                "elements_by_width": {},
                "pseudo_by_width": {},
                "scene_elements_by_width": {},
                "scene_pseudo_by_width": {},
                "style_keys": set(),
            }
            for route in PAGES
        }
        for theme in THEMES
    }

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for theme in THEMES:
                for width in WIDTHS:
                    context = browser.new_context(
                        viewport={"width": width, "height": 900},
                        reduced_motion="reduce",
                    )
                    context.add_init_script(
                        f'window.localStorage.setItem("portfolio-theme", "{theme}");'
                    )
                    external_requests: list[str] = []
                    context.route(re.compile(r"^https?://"), lambda route: route.abort())
                    page = context.new_page()
                    console_errors, runtime_errors = _page_errors(page)
                    page.on(
                        "request",
                        lambda request, requests=external_requests: requests.append(
                            request.url
                        )
                        if request.url.startswith(("http://", "https://"))
                        else None,
                    )
                    try:
                        for route in PAGES:
                            console_errors.clear()
                            runtime_errors.clear()
                            external_requests.clear()
                            case = f"{route}/{theme}/{width}"
                            page.goto(f"{guide_url}#{route}", wait_until="load")
                            page.wait_for_function(
                                "route => document.body.dataset.page === route",
                                arg=route,
                            )
                            if route == "training":
                                page.wait_for_function(
                                    "window.NexusTraining && window.NexusShooter"
                                )
                            audit = page.evaluate(PAGE_AUDIT)

                            record = measurements[theme][route]
                            elements_by_width = record["elements_by_width"]
                            assert isinstance(elements_by_width, dict)
                            elements_by_width[str(width)] = audit["sampledElements"]
                            pseudo_by_width = record["pseudo_by_width"]
                            assert isinstance(pseudo_by_width, dict)
                            pseudo_by_width[str(width)] = audit[
                                "pseudoSampledElements"
                            ]
                            style_keys = record["style_keys"]
                            assert isinstance(style_keys, set)
                            style_keys.update(audit["styleKeys"])
                            _collect_audit_failures(
                                failures, audit, case, route, theme
                            )

                            if route == "training":
                                scene_elements_by_width = record[
                                    "scene_elements_by_width"
                                ]
                                scene_pseudo_by_width = record[
                                    "scene_pseudo_by_width"
                                ]
                                assert isinstance(scene_elements_by_width, dict)
                                assert isinstance(scene_pseudo_by_width, dict)
                                scene_counts = {
                                    TRAINING_SCENES[0]: audit["sampledElements"]
                                }
                                scene_pseudo_counts = {
                                    TRAINING_SCENES[0]: audit[
                                        "pseudoSampledElements"
                                    ]
                                }
                                for scene in TRAINING_SCENES[1:]:
                                    page.evaluate(
                                        "scene => window.NexusTraining.go(scene)",
                                        scene,
                                    )
                                    page.wait_for_function(
                                        "scene => window.NexusTraining.snapshot().sceneId === scene",
                                        arg=scene,
                                    )
                                    scene_audit = page.evaluate(PAGE_AUDIT)
                                    scene_case = (
                                        f"training/{scene}/{theme}/{width}"
                                    )
                                    scene_counts[scene] = scene_audit[
                                        "sampledElements"
                                    ]
                                    scene_pseudo_counts[scene] = scene_audit[
                                        "pseudoSampledElements"
                                    ]
                                    style_keys.update(scene_audit["styleKeys"])
                                    _collect_audit_failures(
                                        failures,
                                        scene_audit,
                                        scene_case,
                                        route,
                                        theme,
                                    )
                                scene_elements_by_width[str(width)] = scene_counts
                                scene_pseudo_by_width[str(width)] = (
                                    scene_pseudo_counts
                                )

                            if console_errors:
                                failures.append(f"{case}: console errors: {console_errors}")
                            if runtime_errors:
                                failures.append(f"{case}: page errors: {runtime_errors}")
                            if external_requests:
                                failures.append(
                                    f"{case}: external requests: {external_requests}"
                                )
                    finally:
                        context.close()
        finally:
            browser.close()

    printable: dict[str, dict[str, dict[str, object]]] = {}
    total_style_keys: set[str] = set()
    base_route_element_samples = 0
    base_route_pseudo_samples = 0
    training_additional_scene_samples = 0
    training_additional_pseudo_samples = 0
    for theme in THEMES:
        printable[theme] = {}
        for route in PAGES:
            record = measurements[theme][route]
            style_keys = record["style_keys"]
            assert isinstance(style_keys, set)
            total_style_keys.update(f"{theme}|{key}" for key in style_keys)
            elements_by_width = record["elements_by_width"]
            pseudo_by_width = record["pseudo_by_width"]
            assert isinstance(elements_by_width, dict)
            assert isinstance(pseudo_by_width, dict)
            base_route_element_samples += sum(elements_by_width.values())
            base_route_pseudo_samples += sum(pseudo_by_width.values())
            printable[theme][route] = {
                "elements_by_width": elements_by_width,
                "pseudo_by_width": pseudo_by_width,
                "unique_styles": len(style_keys),
            }
            if route == "training":
                scene_elements_by_width = record["scene_elements_by_width"]
                scene_pseudo_by_width = record["scene_pseudo_by_width"]
                assert isinstance(scene_elements_by_width, dict)
                assert isinstance(scene_pseudo_by_width, dict)
                for scene_counts in scene_elements_by_width.values():
                    assert isinstance(scene_counts, dict)
                    training_additional_scene_samples += sum(
                        count
                        for scene, count in scene_counts.items()
                        if scene != TRAINING_SCENES[0]
                    )
                for scene_counts in scene_pseudo_by_width.values():
                    assert isinstance(scene_counts, dict)
                    training_additional_pseudo_samples += sum(
                        count
                        for scene, count in scene_counts.items()
                        if scene != TRAINING_SCENES[0]
                    )
                printable[theme][route]["scene_elements_by_width"] = (
                    scene_elements_by_width
                )
                printable[theme][route]["scene_pseudo_by_width"] = (
                    scene_pseudo_by_width
                )
    print(
        "PHASE6_TEXT_AUDIT "
        + json.dumps(
            {
                "by_theme_page": printable,
                "base_32_route_visible_element_samples": (
                    base_route_element_samples
                ),
                "base_32_route_pseudo_text_samples": base_route_pseudo_samples,
                "training_additional_scene_samples": (
                    training_additional_scene_samples
                ),
                "training_additional_pseudo_text_samples": (
                    training_additional_pseudo_samples
                ),
                "total_visible_element_samples": (
                    base_route_element_samples
                    + training_additional_scene_samples
                ),
                "total_pseudo_text_samples": (
                    base_route_pseudo_samples
                    + training_additional_pseudo_samples
                ),
                "unique_styles_both_themes": len(total_style_keys),
            },
            sort_keys=True,
        )
    )
    if len(total_style_keys) <= 242:
        failures.append(
            "contrast coverage regressed to "
            f"{len(total_style_keys)} unique computed styles; expected more than the "
            "v4.2.3 baseline of 242"
        )
    assert not failures, "Phase 6 browser matrix failed:\n- " + "\n- ".join(failures)


def _focus_by_tab_from_previous(page: Any, selector: str) -> None:
    result = page.evaluate(
        r"""
        (selector) => {
          const visible = (element) => {
            const style = getComputedStyle(element);
            const rect = element.getBoundingClientRect();
            return style.display !== "none" && style.visibility === "visible"
              && Number(style.opacity) > 0.01 && rect.width > 0 && rect.height > 0;
          };
          const candidates = Array.from(document.querySelectorAll(
            'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), '
              + 'textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
          )).filter(visible);
          const target = document.querySelector(selector);
          const index = candidates.indexOf(target);
          if (!target || index < 0) return {found: false, index};
          if (index === 0) {
            target.focus();
            return {found: true, index, first: true};
          }
          candidates[index - 1].focus();
          return {found: true, index, first: false};
        }
        """,
        selector,
    )
    assert result["found"], f"{selector} is absent from the rendered Tab order"
    if not result["first"]:
        page.keyboard.press("Tab")
    assert page.evaluate("selector => document.activeElement.matches(selector)", selector), (
        f"Tab did not reach {selector}"
    )


def test_keyboard_and_reduced_motion_are_complete(render_gate: object) -> None:
    """Prove static platform semantics and real keyboard operation of every new widget."""
    _require_browser(render_gate)
    from playwright.sync_api import sync_playwright

    guide_url = GUIDE.resolve().as_uri()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            context = browser.new_context(
                viewport={"width": 900, "height": 940},
                reduced_motion="reduce",
            )
            context.add_init_script(
                'window.localStorage.setItem("portfolio-theme", "dark");'
            )
            context.route(re.compile(r"^https?://"), lambda route: route.abort())
            page = context.new_page()
            console_errors, runtime_errors = _page_errors(page)
            try:
                failures: list[str] = []
                motion_measurements: dict[str, dict[str, object]] = {}
                for route in PAGES:
                    page.goto(f"{guide_url}#{route}", wait_until="load")
                    page.wait_for_function(
                        "route => document.body.dataset.page === route",
                        arg=route,
                    )
                    page.wait_for_timeout(120)
                    state = page.evaluate(
                        r"""
                        () => {
                          const active = document.querySelector(".page.active");
                          const canvas = document.getElementById("constellation");
                          const running = document.getAnimations({subtree: true})
                            .filter((animation) => animation.playState === "running")
                            .map((animation) => {
                              const timing = animation.effect && animation.effect.getTiming
                                ? animation.effect.getTiming()
                                : {};
                              return {
                                name: animation.animationName || "transition",
                                duration: timing.duration,
                                iterations: timing.iterations,
                                target: animation.effect && animation.effect.target
                                  ? {
                                      tag: animation.effect.target.tagName,
                                      id: animation.effect.target.id,
                                      className: animation.effect.target.getAttribute("class"),
                                      html: animation.effect.target.outerHTML.slice(0, 180),
                                    }
                                  : "unknown",
                                properties: animation.effect && animation.effect.target
                                  ? getComputedStyle(animation.effect.target).transitionProperty
                                  : "unknown",
                              };
                            });
                          const visibleText = Array.from(active.querySelectorAll("*"))
                            .filter((element) => {
                              const style = getComputedStyle(element);
                              const rect = element.getBoundingClientRect();
                              return element.textContent.trim() && style.display !== "none"
                                && style.visibility === "visible" && Number(style.opacity) > 0.01
                                && rect.width > 0 && rect.height > 0;
                            }).length;
                          return {
                            running,
                            visibleText,
                            constellation: canvas && canvas.toDataURL ? canvas.toDataURL() : null,
                          };
                        }
                        """
                    )
                    page.wait_for_timeout(160)
                    after = page.evaluate(
                        r"""
                        () => {
                          const canvas = document.getElementById("constellation");
                          return {
                            running: document.getAnimations({subtree: true})
                              .filter((animation) => animation.playState === "running").length,
                            constellation: canvas && canvas.toDataURL ? canvas.toDataURL() : null,
                          };
                        }
                        """
                    )
                    if state["running"]:
                        failures.append(
                            f"{route}: reduced motion left animations running: "
                            f"{state['running']}"
                        )
                    if after["running"] != 0:
                        failures.append(
                            f"{route}: reduced motion still had {after['running']} "
                            "animations after settlement"
                        )
                    if state["visibleText"] <= 0:
                        failures.append(
                            f"{route}: reduced-motion state has no visible text"
                        )
                    if state["constellation"] != after["constellation"]:
                        failures.append(
                            f"{route}: constellation changed under reduced motion"
                        )
                    motion_measurements[route] = {
                        "initial_running_animations": state["running"],
                        "running_animations": after["running"],
                        "visible_text_elements": state["visibleText"],
                    }

                page.goto(f"{guide_url}#home", wait_until="load")
                page.wait_for_function("document.body.dataset.page === 'home'")
                platforms = page.locator(".platform-rail > .platform-item")
                # v4.4.1 Phase 2: five approved marks; OpenCode and the text treatments retired.
                assert platforms.count() == 5
                assert page.locator(".platform-rail").get_attribute("aria-label") == (
                    "Compatible AI platforms"
                )
                assert platforms.evaluate_all(
                    "items => items.every(item => item.tagName === 'LI' && !item.hasAttribute('tabindex'))"
                ), "static platform marks must use list semantics without polluting the Tab order"
                assert platforms.all_inner_texts() == [
                    "Claude",
                    "ChatGPT",
                    "Gemini",
                    "Cursor",
                    "GitHub Copilot",
                ]

                untabbable_actions = page.evaluate(
                    r"""
                    () => Array.from(document.querySelectorAll('.site-header [data-go], .page.active [data-go]'))
                      .filter((element) => {
                        const style = getComputedStyle(element);
                        const rect = element.getBoundingClientRect();
                        if (style.display === "none" || style.visibility !== "visible"
                            || rect.width <= 0 || rect.height <= 0) return false;
                        if (element.matches('a[href], button:not([disabled])')) return false;
                        return element.tabIndex < 0;
                      })
                      .map((element) => `${element.tagName.toLowerCase()}.${element.className}`)
                    """
                )
                if untabbable_actions:
                    failures.append(
                        "pointer navigation actions are absent from the Tab order: "
                        f"{untabbable_actions}"
                    )

                active_tab = page.locator('.page.active [role="tab"][aria-selected="true"]')
                assert active_tab.count() == 1
                active_tab.focus()
                page.keyboard.press("ArrowRight")
                selected_tab = page.locator(
                    '.page.active [role="tab"][aria-selected="true"]'
                ).inner_text()
                if selected_tab != "macOS / Linux":
                    failures.append(
                        "Home install role=tab buttons do not select the next tab with "
                        f"ArrowRight; selected tab remained {selected_tab!r}"
                    )
                if page.evaluate("document.activeElement.getAttribute('role')") != "tab":
                    failures.append("Home install ArrowRight moved focus outside the tablist")
                tab_contract = page.evaluate(
                    r"""
                    () => Array.from(document.querySelectorAll('.page.active [role="tab"]')).map((tab) => {
                      const panelId = tab.getAttribute("aria-controls");
                      const panel = panelId ? document.getElementById(panelId) : null;
                      return {
                        tabId: tab.id,
                        panelId,
                        panelExists: Boolean(panel),
                        panelLabelledBy: panel && panel.getAttribute("aria-labelledby"),
                        selected: tab.getAttribute("aria-selected") === "true",
                        panelHidden: panel ? panel.hidden : null,
                        panelDisplay: panel ? getComputedStyle(panel).display : null,
                      };
                    })
                    """
                )
                for relationship in tab_contract:
                    if not relationship["tabId"] or not relationship["panelId"]:
                        failures.append(
                            "Home install tab is missing an id or aria-controls: "
                            f"{relationship}"
                        )
                        continue
                    if not relationship["panelExists"]:
                        failures.append(
                            "Home install tab aria-controls does not resolve: "
                            f"{relationship}"
                        )
                        continue
                    if relationship["panelLabelledBy"] != relationship["tabId"]:
                        failures.append(
                            "Home install panel aria-labelledby does not point back to "
                            f"its tab: {relationship}"
                        )
                    if relationship["selected"]:
                        if relationship["panelHidden"] or relationship[
                            "panelDisplay"
                        ] == "none":
                            failures.append(
                                "Home install selected panel is hidden after ArrowRight: "
                                f"{relationship}"
                            )
                    elif not relationship["panelHidden"]:
                        failures.append(
                            "Home install inactive panel lacks the hidden attribute after "
                            f"ArrowRight: {relationship}"
                        )

                progress_target = (
                    '.page.active [data-progress] a[data-go="foundations"]'
                )
                _focus_by_tab_from_previous(page, progress_target)
                assert page.evaluate("document.activeElement.tagName") == "A"
                page.keyboard.press("Enter")
                page.wait_for_function("document.body.dataset.page === 'foundations'")

                page.goto(f"{guide_url}#training/describe", wait_until="load")
                page.wait_for_function("window.NexusTraining && window.NexusShooter")
                # The idle gate means Space fires only in a STARTED, focused game, and
                # this sweep runs under reduced motion, so the tick that spawns the shot
                # is driven manually through the public step seam. Keyboard start is
                # proven with a direct focus plus Enter; the full tab-ownership walk
                # lives in test_arcade_shooter_game.py.
                page.locator("[data-arcade-start]").focus()
                assert page.evaluate(
                    "document.activeElement.hasAttribute('data-arcade-start')"
                ), "the start control must be keyboard-focusable"
                page.keyboard.press("Enter")
                page.wait_for_function(
                    "window.NexusShooter.snapshot().lifecycle !== 'idle'"
                )
                assert page.evaluate(
                    "document.activeElement.hasAttribute('data-arcade-game')"
                ), "starting must hand key ownership to the game"
                before_shots = page.evaluate(
                    "window.NexusShooter.snapshot().playerShots.length"
                )
                page.keyboard.down("Space")
                page.evaluate("window.NexusShooter.step()")
                page.keyboard.up("Space")
                assert page.evaluate(
                    "window.NexusShooter.snapshot().playerShots.length"
                ) > before_shots

                first_file = '[data-nht="file"]'
                _focus_by_tab_from_previous(page, first_file)
                file_paths = page.locator(first_file).evaluate_all(
                    "items => items.map(item => item.dataset.filePath)"
                )
                assert len(file_paths) >= 2
                assert page.evaluate(
                    "document.activeElement && document.activeElement.dataset.filePath"
                ) == file_paths[0]

                page.keyboard.press("ArrowDown")
                assert page.evaluate(
                    "document.activeElement && document.activeElement.dataset.filePath"
                ) == file_paths[1]
                page.keyboard.press("ArrowUp")
                assert page.evaluate(
                    "document.activeElement && document.activeElement.dataset.filePath"
                ) == file_paths[0]

                page.keyboard.press("End")
                assert page.evaluate(
                    "document.activeElement && document.activeElement.dataset.filePath"
                ) == file_paths[-1]
                page.keyboard.press("Space")
                assert page.locator('[data-nht="file-path"]').inner_text() == file_paths[-1]
                assert page.locator(
                    f'[data-nht="file"][data-file-path="{file_paths[-1]}"]'
                ).get_attribute("aria-selected") == "true"

                page.keyboard.press("Home")
                assert page.evaluate(
                    "document.activeElement && document.activeElement.dataset.filePath"
                ) == file_paths[0]
                page.keyboard.press("Enter")
                assert page.locator('[data-nht="file-path"]').inner_text() == file_paths[0]
                assert page.locator(
                    f'[data-nht="file"][data-file-path="{file_paths[0]}"]'
                ).get_attribute("aria-selected") == "true"

                _focus_by_tab_from_previous(
                    page, ".page.active .pagenav .next[href]"
                )
                page.keyboard.press("Enter")
                page.wait_for_function("document.body.dataset.page === 'cheatsheets'")

                page.goto(f"{guide_url}#training/describe", wait_until="load")
                page.wait_for_function("window.NexusShooter")
                # Hash navigation is same-document, so the earlier keyboard block may
                # already have consumed the start overlay; only click it if it is showing.
                if page.locator("[data-arcade-start]").is_visible():
                    page.locator("[data-arcade-start]").click()
                page.wait_for_function(
                    "window.NexusShooter.snapshot().lifecycle === 'paused'"
                )
                before = page.evaluate("window.NexusShooter.snapshot()")
                assert "reduced-motion" in before["pauseReasons"]
                page.wait_for_timeout(160)
                assert page.evaluate("window.NexusShooter.snapshot().tick") == before[
                    "tick"
                ]
                step_button = page.locator("[data-arcade-step]")
                assert step_button.is_visible() and step_button.is_enabled()
                step_button.click()
                stepped = page.evaluate("window.NexusShooter.snapshot()")
                assert stepped["tick"] == before["tick"] + 1
                page.wait_for_timeout(160)
                assert page.evaluate("window.NexusShooter.snapshot().tick") == stepped[
                    "tick"
                ]

                print(
                    "PHASE6_MOTION_AUDIT "
                    + json.dumps(motion_measurements, sort_keys=True)
                )
                assert not console_errors, f"console errors: {console_errors}"
                assert not runtime_errors, f"page errors: {runtime_errors}"
                assert not failures, "Phase 6 keyboard/motion sweep failed:\n- " + (
                    "\n- ".join(failures)
                )
            finally:
                context.close()
        finally:
            browser.close()
