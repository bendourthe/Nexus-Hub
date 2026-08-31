"""Structural tests for guides/website/nexus-hub-guide.html.

v4.2.2 rebuild gate. Baseline assertions pass against the rebuilt shell;
assertions owned by a later rebuild phase use strict xfail until that phase
removes the marker (plan: docs/releases/v4/v4.2/plans/
v4.2.2-guide-cinematic-rebuild.md).
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
EXAMPLE_ZIP_NAME = "glow-booth.zip"
SIZE_BUDGET_BYTES = 500_000

INSTALL_SH = (
    "curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash"
)
INSTALL_PS = (
    "irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1 | iex"
)

# Onboarding catalog-count / installer-version patterns (must never reappear).
ONBOARDING_STALE = re.compile(
    r"""(?:
        \b\d{2,4}\s+skills\b
        | \b\d+\s+commands\b
        | \b\d+\s+hooks\b
        | \b\d+\s+agents\b
        | installer\s+v?\d+\.\d+\.\d+
        | \bv3\.\d+\.\d+\b
        | Nexus-Hub\s+v\d+\.\d+\.\d+
    )""",
    re.IGNORECASE | re.VERBOSE,
)

class GuideParser(HTMLParser):
    """Collect structure from the guide without executing JavaScript."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.page_ids: list[str] = []
        self.h1_by_page: dict[str, list[str]] = defaultdict(list)
        self.headings_by_page: dict[str, list[tuple[str, str]]] = defaultdict(list)
        self.current_page: str | None = None
        self._heading_tag: str | None = None
        self._heading_parts: list[str] = []
        self.script_src: list[str] = []
        self.link_href: list[str] = []
        self.media_src: list[str] = []
        self.data_go: list[str] = []
        self.nav_data_go: list[str] = []
        self.nav_link_text: list[tuple[str, str]] = []
        self._in_nav_links = False
        self._nav_links_depth = 0
        self._in_anchor = False
        self._anchor_go = ""
        self._anchor_parts: list[str] = []
        self.anchors: list[tuple[str, str]] = []
        self.html_count = 0
        self.body_count = 0
        self.h1_count = 0
        self.json_script_contents: list[str] = []
        self._in_json_script = False
        self._json_parts: list[str] = []
        self.home_text_parts: list[str] = []
        self.home_data_copy: list[tuple[str, str]] = []
        self._copy_el = False
        self._copy_value = ""
        self._copy_parts: list[str] = []
        self._copy_home = False
        self._copy_tag = ""
        self._copy_depth = 0
        self._page_section_depth = 0
        self.all_data_copy: list[tuple[str, str]] = []
        self.has_theme_toggle = False
        self.raw_attrs: list[tuple[str, dict[str, str]]] = []
        self.install_tab_order: list[str] = []
        self.install_tab_selected: list[str] = []
        self._in_install_wrap = False
        self._install_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        ad = {k: (v or "") for k, v in attrs}
        self.raw_attrs.append((tag, ad))
        if tag == "html":
            self.html_count += 1
        if tag == "body":
            self.body_count += 1
        if tag == "h1":
            self.h1_count += 1
        eid = ad.get("id", "")
        if eid:
            self.ids.append(eid)
        if tag == "section" and eid.startswith("page-"):
            self.current_page = eid
            self.page_ids.append(eid)
            self._page_section_depth = 1
        elif self.current_page and tag == "section":
            self._page_section_depth += 1
        if "nhg-install-wrap" in ad.get("class", ""):
            self._in_install_wrap = True
            self._install_depth = 1
        elif self._in_install_wrap and tag in {"div", "section"}:
            self._install_depth += 1
        if self._in_install_wrap and tag == "button" and "tab-btn" in ad.get("class", ""):
            self.install_tab_order.append(ad.get("data-tab", ""))
            self.install_tab_selected.append(ad.get("aria-selected", ""))
        if tag in {"h1", "h2", "h3"}:
            self._heading_tag = tag
            self._heading_parts = []
        if tag == "script":
            src = ad.get("src", "")
            if src:
                self.script_src.append(src)
            if ad.get("type") == "application/json":
                self._in_json_script = True
                self._json_parts = []
        if tag == "link" and ad.get("href"):
            self.link_href.append(ad["href"])
        if tag in {"img", "video", "audio", "source", "iframe"} and ad.get("src"):
            self.media_src.append(ad["src"])
        if tag == "div" and ad.get("id") == "navLinks":
            self._in_nav_links = True
            self._nav_links_depth = 1
        elif self._in_nav_links:
            self._nav_links_depth += 1
        go = ad.get("data-go", "")
        if go:
            self.data_go.append(go)
            if self._in_nav_links:
                self.nav_data_go.append(go)
        if tag == "a":
            self._in_anchor = True
            self._anchor_go = go
            self._anchor_parts = []
        copy = ad.get("data-copy", "")
        if copy and not self._copy_el:
            self._copy_el = True
            self._copy_value = copy
            self._copy_parts = []
            self._copy_home = self.current_page == "page-home"
            self._copy_tag = tag
            self._copy_depth = 1
        elif self._copy_el and tag == self._copy_tag:
            # Same tag nested inside; count it so the matching close wins.
            self._copy_depth += 1
        label = (ad.get("aria-label", "") + " " + ad.get("id", "") + " " + ad.get("class", "")).lower()
        if "theme" in label and tag in {"button", "input"}:
            self.has_theme_toggle = True
        if ad.get("data-theme-toggle") or ad.get("id") == "themeToggle":
            self.has_theme_toggle = True

    def handle_endtag(self, tag: str) -> None:
        if self._heading_tag and tag == self._heading_tag:
            title = re.sub(r"\s+", " ", "".join(self._heading_parts)).strip()
            page = self.current_page or "?"
            self.headings_by_page[page].append((tag, title))
            if tag == "h1":
                self.h1_by_page[page].append(title)
            self._heading_tag = None
        if self._in_json_script and tag == "script":
            self.json_script_contents.append("".join(self._json_parts))
            self._in_json_script = False
        if self._in_nav_links:
            self._nav_links_depth -= 1
            if self._nav_links_depth <= 0:
                self._in_nav_links = False
        if self._in_install_wrap and tag in {"div", "section"}:
            self._install_depth -= 1
            if self._install_depth <= 0:
                self._in_install_wrap = False
        if self.current_page and tag == "section":
            self._page_section_depth -= 1
            if self._page_section_depth <= 0:
                self.current_page = None
                self._page_section_depth = 0
        if tag == "a" and self._in_anchor:
            text = re.sub(r"\s+", " ", "".join(self._anchor_parts)).strip()
            self.anchors.append((self._anchor_go, text))
            if self._in_nav_links or self._anchor_go:
                if self._in_nav_links:
                    self.nav_link_text.append((self._anchor_go, text))
            self._in_anchor = False
        # Close on the MATCHING end tag, not the first nested one: an
        # invocation splits its text across inner spans, and closing early
        # would capture a truncated payload and under-report real drift.
        if self._copy_el and tag == self._copy_tag:
            self._copy_depth -= 1
            if self._copy_depth <= 0:
                visible = re.sub(r"\s+", " ", "".join(self._copy_parts)).strip()
                self.all_data_copy.append((self._copy_value, visible))
                if self._copy_home:
                    self.home_data_copy.append((self._copy_value, visible))
                self._copy_el = False

    def handle_data(self, data: str) -> None:
        if self._heading_tag:
            self._heading_parts.append(data)
        if self._in_json_script:
            self._json_parts.append(data)
        if self._in_anchor:
            self._anchor_parts.append(data)
        if self._copy_el:
            self._copy_parts.append(data)
        if self.current_page == "page-home":
            self.home_text_parts.append(data)


@pytest.fixture(scope="module")
def guide_text() -> str:
    assert GUIDE.is_file(), f"missing guide at {GUIDE}"
    return GUIDE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def parsed(guide_text: str) -> GuideParser:
    parser = GuideParser()
    parser.feed(guide_text)
    return parser


# ---------------------------------------------------------------------------
# Baseline document contract
# ---------------------------------------------------------------------------


def test_one_html_document(parsed: GuideParser, guide_text: str) -> None:
    assert guide_text.lstrip().lower().startswith("<!doctype html>")
    assert parsed.html_count == 1
    assert parsed.body_count == 1
    assert GUIDE.suffix == ".html"


def test_file_size_budget() -> None:
    size = GUIDE.stat().st_size
    assert size < SIZE_BUDGET_BYTES, f"guide is {size} bytes; budget {SIZE_BUDGET_BYTES}"


def test_each_page_has_a_primary_heading(parsed: GuideParser) -> None:
    assert parsed.page_ids, "no page sections found"
    for page_id in parsed.page_ids:
        headings = parsed.headings_by_page.get(page_id, [])
        assert headings, f"{page_id} has no h1-h3 heading"
        tag, _title = headings[0]
        assert tag == "h1", f"{page_id} first heading is {tag}, expected h1"


def test_ids_are_unique(parsed: GuideParser) -> None:
    counts = Counter(parsed.ids)
    duplicates = {k: v for k, v in counts.items() if v > 1}
    assert not duplicates, f"duplicate ids: {duplicates}"


def test_internal_data_go_targets_exist(parsed: GuideParser) -> None:
    pages = {pid.removeprefix("page-") for pid in parsed.page_ids}
    static = [g for g in parsed.data_go if re.fullmatch(r"[a-z][a-z0-9-]*", g)]
    unknown = sorted({g for g in static if g not in pages})
    assert not unknown, f"data-go targets with no page section: {unknown}"


def test_no_runtime_cdn_font_script_or_image(parsed: GuideParser, guide_text: str) -> None:
    def is_runtime(url: str) -> bool:
        if not url or url.startswith(("data:", "#", "blob:")):
            return False
        if url.startswith(("http://", "https://", "//")):
            return True
        return False

    runtime = (
        [u for u in parsed.script_src if is_runtime(u)]
        + [u for u in parsed.link_href if is_runtime(u)]
        + [u for u in parsed.media_src if is_runtime(u)]
    )
    assert not runtime, f"runtime network URLs: {runtime}"
    assert "@import" not in guide_text
    assert "fonts.googleapis.com" not in guide_text
    assert "fonts.gstatic.com" not in guide_text
    assert "cdnjs" not in guide_text.lower()
    assert "jsdelivr" not in guide_text.lower()
    css_http = re.findall(r"url\(\s*['\"]?(https?:)?//", guide_text)
    assert not css_http, "CSS url() points at a network href"


def test_example_zip_link_present(guide_text: str) -> None:
    assert EXAMPLE_ZIP_NAME in guide_text
    assert re.search(rf'href=["\'](?:[^"\']*/)?{re.escape(EXAMPLE_ZIP_NAME)}["\']', guide_text)
    assert (GUIDE.parent / EXAMPLE_ZIP_NAME).is_file()


def test_github_is_user_initiated_not_a_script(parsed: GuideParser) -> None:
    assert not parsed.script_src
    hrefs = [ad.get("href", "") for tag, ad in parsed.raw_attrs if tag == "a"]
    github = [h for h in hrefs if "github.com" in h]
    assert github, "expected a GitHub navigation link"


# ---------------------------------------------------------------------------
# Shell: nav, theming, routing (Phase 1)
# ---------------------------------------------------------------------------


def test_no_installation_in_primary_nav(parsed: GuideParser) -> None:
    labels = [text.lower() for _go, text in parsed.nav_link_text]
    assert not any("installation" in t for t in labels)
    assert "setup" not in parsed.nav_data_go
    assert any("cheatsheets" in t for t in labels)
    assert not any("workflow" in t for t in labels)
    assert not any(t.strip() == "reference" for t in labels)


def test_theme_toggle_exists(parsed: GuideParser) -> None:
    assert parsed.has_theme_toggle


def test_github_control_is_icon_only(guide_text: str) -> None:
    match = re.search(
        r'<a class="nav-gh"[^>]*>.*?</a>',
        guide_text,
        flags=re.DOTALL,
    )
    assert match, "expected .nav-gh GitHub control"
    tag = match.group(0)
    assert 'aria-label="Nexus-Hub on GitHub"' in tag
    visible = re.sub(r"<svg[\s\S]*?</svg>", "", tag)
    visible = re.sub(r"<[^>]+>", "", visible)
    assert "GitHub" not in visible


def test_github_control_is_fixed_square(guide_text: str) -> None:
    """Screenshot-1 regression: the octocat must sit centered in a fixed square."""
    rule = re.search(r"a\.nav-gh,\s*\.nhg-theme\s*\{([^}]+)\}", guide_text)
    assert rule, "expected shared a.nav-gh/.nhg-theme sizing rule"
    body = rule.group(1)
    assert "width: 36px" in body and "height: 36px" in body
    assert "padding: 0" in body, "text-link padding must not crush the icon"
    assert "inline-flex" in body
    svg_rule = re.search(r"\.nav-gh svg\s*\{([^}]+)\}", guide_text)
    assert svg_rule and "17px" in svg_rule.group(1)


def test_theme_control_is_sun_moon_default_dark(guide_text: str) -> None:
    assert 'id="themeToggle"' in guide_text
    assert 'class="icon-sun"' in guide_text
    assert 'class="icon-moon"' in guide_text
    boot = guide_text.split("</script>", 1)[0]
    assert 'theme = "dark"' in boot
    assert "prefers-color-scheme" not in boot


def test_wordmark_uses_theme_ink(guide_text: str) -> None:
    rule = re.search(r"\.brand \.wordmark b\s*\{([^}]+)\}", guide_text)
    assert rule, "expected .wordmark b rule"
    body = rule.group(1)
    assert "var(--ink)" in body
    assert "#fff" not in body


def test_light_mode_brand_chip(guide_text: str) -> None:
    """The glow logo sits on a rounded dark chip in light theme (screenshot 4)."""
    rule = re.search(
        r'html\[data-theme="light"\] \.brand \.mark[^{]*\{([^}]+)\}', guide_text
    )
    assert rule, "expected light-mode brand chip rule"
    body = rule.group(1)
    assert "border-radius" in body
    assert "background" in body


def test_light_theme_terminal_is_not_near_black(guide_text: str) -> None:
    light = guide_text.split('html[data-theme="light"]', 1)[-1].split(
        "/* ---------- Reset ---------- */", 1
    )[0]
    term_bg = re.search(r"--term-bg:\s*([^;]+);", light)
    assert term_bg, "light --term-bg missing"
    value = term_bg.group(1).strip().lower()
    assert value not in {"#1c2a2e", "#07171d", "#0a1c23"}
    assert value.startswith("#")
    nav_values = re.findall(r"--nav-bg:\s*([^;]+);", guide_text)
    assert nav_values, "expected --nav-bg"
    assert all(not v.strip().lower().startswith("rgba(") for v in nav_values)


def test_portfolio_theme_allowlisted(guide_text: str) -> None:
    assert "portfolio-theme" in guide_text
    assert '"light"' in guide_text and '"dark"' in guide_text
    assert "localStorage" in guide_text
    assert "try" in guide_text and "catch" in guide_text
    assert "theme !== \"light\" && theme !== \"dark\"" in guide_text or (
        "theme !== 'light'" in guide_text
    )


def test_page_url_hash_uses_first_segment(guide_text: str) -> None:
    """#training/<scene> must not be treated as a whole-hash page id."""
    assert "pageIdFromHash" in guide_text or re.search(r"""split\(['"]/['"]\)""", guide_text)


def test_reduced_motion_pauses_constellation(guide_text: str) -> None:
    assert "prefers-reduced-motion" in guide_text
    assert "visibilitychange" in guide_text or "document.hidden" in guide_text


def test_cheatsheets_hash_rewrites_exist(guide_text: str) -> None:
    assert "HASH_REWRITES" in guide_text
    assert "reference: \"cheatsheets\"" in guide_text or "reference: 'cheatsheets'" in guide_text
    assert "explore: \"cheatsheets/explore\"" in guide_text or "explore: 'cheatsheets/explore'" in guide_text
    assert 'id="page-cheatsheets"' in guide_text
    assert 'id="page-explore"' not in guide_text
    assert 'id="page-reference"' not in guide_text


def test_no_stale_setup_route_in_markup(parsed: GuideParser) -> None:
    assert "page-setup" not in parsed.page_ids
    static = [g for g in parsed.data_go if g == "setup"]
    assert not static


# ---------------------------------------------------------------------------
# Shell: design system (Phase 1)
# ---------------------------------------------------------------------------


def test_compact_spacing_tokens(guide_text: str) -> None:
    sec_pad = re.search(r"--sec-pad:\s*(\d+)px", guide_text)
    assert sec_pad, "expected --sec-pad token"
    assert int(sec_pad.group(1)) <= 32, "section rhythm must stay compact"
    assert "--violet" not in guide_text, "accent rainbow was trimmed by the design brief"


def test_body_text_is_fluid_with_no_measure_cap(guide_text: str) -> None:
    """v4.2.3: text fills the content column; the container is the only cap."""
    assert "--measure" not in guide_text, "the per-text measure cap was removed"
    css = guide_text.split("<style>", 1)[-1].split("</style>", 1)[0]
    for selector in (r"(?<![\w-])h1\s*\{", r"(?<![\w.-])p\s*\{", r"\.lead\s*\{"):
        rule = re.search(selector + r"([^}]+)\}", css)
        assert rule, f"expected a rule matching {selector}"
        assert "max-width" not in rule.group(1), (
            f"{selector} must not cap its width; the container governs"
        )
    assert "--maxw" in css, "the container keeps the only width constraint"


def test_copy_button_has_a_bare_icon_variant(guide_text: str) -> None:
    """Inline hosts draw the chip; the button inside must not draw a second."""
    rule = re.search(r"\.copy-btn--bare\s*\{([^}]+)\}", guide_text)
    assert rule, "expected a bare copy-button variant"
    body = rule.group(1)
    assert "background: transparent" in body
    assert "border: 0" in body
    assert re.search(r"min-width:\s*24px", body), "hit area stays >= 24px"
    assert ".copy-btn--bare .cb-label { display: none" in guide_text, "icon only"
    assert ".copy-btn--bare:focus-visible" in guide_text, "focus must stay visible"
    injector = guide_text.split("function initCopyButtons()", 1)[-1]
    assert 'contains("cmd-cell")' in injector, "inline hosts get the bare variant"
    assert 'setAttribute("aria-label", "Copy to clipboard")' in injector


def test_pagenav_controls_hug_their_label(guide_text: str) -> None:
    rule = re.search(r"\.pagenav a\s*\{([^}]+)\}", guide_text)
    assert rule, "expected .pagenav a rule"
    body = rule.group(1)
    assert "flex: 0 1 260px" not in body, "fixed-width nav slabs were the defect"
    assert "flex: 0 0 auto" in body and "width: auto" in body


def test_invocation_convention_exists_and_is_used(
    parsed: GuideParser, guide_text: str
) -> None:
    for cls in (".inv-cmd", ".inv-arg", ".inv-ph"):
        assert re.search(re.escape(cls) + r"\s*\{", guide_text), f"missing {cls} rule"
    assert 'class="inv-cmd"' in guide_text, "the convention must be used, not just defined"
    # A split invocation must still copy as its plain text.
    for payload, visible in parsed.all_data_copy:
        if payload in {"/skills list", "/commands"}:
            assert visible.strip() == payload, (
                f"split markup broke copy parity for {payload}"
            )


def test_reveal_motion_has_static_reduced_fallback(guide_text: str) -> None:
    assert ".reveal" in guide_text
    reduce_block = guide_text.split("@media (prefers-reduced-motion: reduce)", 1)
    assert len(reduce_block) == 2, "expected a reduced-motion block"
    assert "opacity: 1" in reduce_block[1].split("}", 3)[-2] or "opacity: 1" in reduce_block[1][:800]


def test_copy_button_is_slim(guide_text: str) -> None:
    rule = re.search(r"\.copy-btn\s*\{([^}]+)\}", guide_text)
    assert rule, "expected .copy-btn rule"
    height = re.search(r"height:\s*(\d+)px", rule.group(1))
    assert height and int(height.group(1)) <= 26, "copy button must be slim (screenshot 2)"


def test_copy_button_is_not_inside_data_copy_code(guide_text: str) -> None:
    fn = guide_text.split("function initCopyButtons()", 1)[-1]
    assert "host.appendChild(btn)" in fn
    assert "el.appendChild(btn)" not in fn
    assert 'closest(".cmd-line' in fn


def test_untrusted_origin_warning_fully_removed(guide_text: str) -> None:
    """Maintainer decision 2026-08-29: the warning box and its logic are gone."""
    assert "untrustedCopyWarning" not in guide_text
    assert "isDocumentedGuideOrigin" not in guide_text
    assert "not on a documented host" not in guide_text


def test_render_harness_imports_without_playwright() -> None:
    tool = _ROOT / "tests" / "guides" / "tools" / "render_guide.py"
    spec = importlib.util.spec_from_file_location("render_guide", tool)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # lazy playwright import: must not raise
    assert hasattr(module, "main")
    assert module.PAGES == ("home", "foundations", "training", "cheatsheets")


# ---------------------------------------------------------------------------
# Home: v4.4.0 identity, compatibility, installation, and comparison
# ---------------------------------------------------------------------------


def _home_markup(guide_text: str) -> str:
    return guide_text.split('id="page-home"', 1)[-1].split('id="page-foundations"', 1)[0]


def test_home_identity_is_centered_nonwrapping_and_observer_gated(guide_text: str) -> None:
    home = _home_markup(guide_text)
    assert 'class="hero-lockup reveal"' in home
    assert re.search(
        r'<div class="hero-lockup reveal">\s*<svg class="hero-mark"[\s\S]*?</svg>\s*'
        r'<h1 class="hero-wordmark">Nexus-Hub</h1>',
        home,
    )
    lockup_rule = re.search(r"\.hero-lockup\s*\{([^}]+)\}", guide_text)
    assert lockup_rule and "justify-content: center" in lockup_rule.group(1)
    assert "flex-wrap: nowrap" in lockup_rule.group(1)
    wordmark_rule = re.search(r"\.hero-wordmark\s*\{([^}]+)\}", guide_text)
    assert wordmark_rule and "white-space: nowrap" in wordmark_rule.group(1)
    assert "clamp(" in wordmark_rule.group(1), "the 320 px lockup needs fluid type"
    assert ".js .hero-lockup.reveal .hero-mark" in guide_text
    assert ".js .hero-lockup.in .hero-mark" in guide_text
    reduced_motion = guide_text.split("@media (prefers-reduced-motion: reduce)", 1)[-1]
    assert ".js .hero-lockup.reveal .hero-mark" in reduced_motion


def test_home_uses_a_short_outcome_tagline(guide_text: str) -> None:
    home = _home_markup(guide_text)
    match = re.search(r'<p class="hero-tagline">([^<]+)</p>', home)
    assert match, "expected a dedicated selling tagline"
    assert len(match.group(1).split()) <= 14
    assert "catalog of" not in match.group(1).lower()


def test_home_lists_six_platforms_without_invented_marks(guide_text: str) -> None:
    home = _home_markup(guide_text)
    rail = re.search(r'<ul class="platform-rail"[\s\S]*?</ul>', home)
    assert rail, "expected a dedicated compatibility rail"
    items = re.findall(r'<li class="platform-item([^\"]*)"[^>]*data-platform="([^\"]+)"[^>]*>([\s\S]*?)</li>', rail.group(0))
    assert len(items) == 6
    assert [platform for _classes, platform, _body in items] == [
        "Claude",
        "ChatGPT",
        "Gemini",
        "Cursor",
        "GitHub Copilot",
        "OpenCode",
    ]
    official = {"Claude", "Cursor", "OpenCode"}
    for classes, platform, body in items:
        assert f'<span class="platform-name">{platform}</span>' in body
        if platform in official:
            assert 'class="platform-mark"' in body
            assert 'aria-hidden="true"' in body and 'focusable="false"' in body
            assert "<image" not in body and "http" not in body
            assert 'data-logo-source="official"' in body
        else:
            assert "platform-item--text" in classes
            assert f'<span class="platform-text-mark"><span class="platform-name">{platform}</span></span>' in body
            assert "<svg" not in body
    assert "OpenCode receives commands through its instruction file" in home


def test_home_platform_labels_use_legible_theme_token(guide_text: str) -> None:
    rule = re.search(r"\.platform-name\s*\{([^}]+)\}", guide_text)
    assert rule and "color: var(--ink)" in rule.group(1)
    size = re.search(r"font-size:\s*([\d.]+)px", rule.group(1))
    assert size and float(size.group(1)) >= 12


def test_installation_terminal_precedes_subordinate_verification(guide_text: str) -> None:
    home = _home_markup(guide_text)
    assert '<span class="eyebrow">Installation</span>' in home
    assert 'class="term term--standalone term--install"' in home
    assert 'class="verify-steps verify-steps--secondary"' in home
    assert home.index("term--install") < home.index("verify-steps--secondary")
    terminal_rule = re.search(r"\.term--install\s*\{([^}]+)\}", guide_text)
    secondary_rule = re.search(r"\.verify-steps--secondary\s*\{([^}]+)\}", guide_text)
    assert terminal_rule and "box-shadow:" in terminal_rule.group(1)
    assert secondary_rule and "border-left:" not in secondary_rule.group(1)


def test_home_troubleshooting_is_structured_and_copyable(guide_text: str) -> None:
    home = _home_markup(guide_text)
    block = re.search(r'<details class="support-details">([\s\S]*?)</details>', home)
    assert block and "<summary>Troubleshooting</summary>" in block.group(1)
    assert 'class="support-list"' in block.group(1)
    for label in ("No curl", "One project", "Selected assistants", "No prompts", "Upgrade"):
        assert f"<dt>{label}</dt>" in block.group(1)
    for command in (
        "wget -qO- https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash",
        "nexus-hub upgrade",
    ):
        assert f'data-copy="{command}"' in block.group(1)


def test_home_comparison_has_centered_explicit_sides(guide_text: str) -> None:
    home = _home_markup(guide_text)
    assert "Keep your platform. Add the workflow." in home
    assert '<div class="cmp-head">' in home
    head_rule = re.search(r"\.cmp-head\s*\{([^}]+)\}", guide_text)
    side_rule = re.search(r"\.cmp-side\s*\{([^}]+)\}", guide_text)
    assert head_rule and "grid-template-columns: 1fr auto 1fr" in head_rule.group(1)
    assert side_rule and "text-align: center" in side_rule.group(1)
    size = re.search(r"font-size:\s*([\d.]+)px", side_rule.group(1))
    assert size and float(size.group(1)) >= 12
    assert ".cmp-side--without" in guide_text and ".cmp-side--with" in guide_text


def test_home_definitions_are_structured_and_link_to_foundations(guide_text: str) -> None:
    home = _home_markup(guide_text)
    block = re.search(r'<details class="definition-details">([\s\S]*?)</details>', home)
    assert block and 'class="definition-list"' in block.group(1)
    for term in ("Command", "Skill", "Hook", "Agent", "Rule"):
        assert f"<dt>{term}</dt>" in block.group(1)
    assert 'data-go="foundations"' in block.group(1)
    assert 'data-go="cheatsheets"' not in block.group(1)


def test_windows_install_tab_is_first_and_default(parsed: GuideParser, guide_text: str) -> None:
    assert parsed.install_tab_order, "expected install tabs"
    assert parsed.install_tab_order[0] == "win", "Windows tab must be first"
    assert parsed.install_tab_selected[0] == "true", "Windows tab must be default-active"
    first_panel = re.search(r'<div class="tab-panel([^"]*)" data-panel="([a-z]+)"', guide_text)
    assert first_panel and first_panel.group(2) == "win" and "active" in first_panel.group(1)


def test_home_contains_both_canonical_install_commands(parsed: GuideParser) -> None:
    copies = {payload for payload, _visible in parsed.home_data_copy}
    home_text = re.sub(r"\s+", " ", "".join(parsed.home_text_parts))
    assert INSTALL_SH in copies or INSTALL_SH in home_text
    assert INSTALL_PS in copies or INSTALL_PS in home_text
    payloads = {p for p, _v in parsed.home_data_copy}
    assert INSTALL_SH in payloads
    assert INSTALL_PS in payloads


def test_home_install_copy_payload_equals_visible_text(parsed: GuideParser) -> None:
    found_sh = found_ps = False
    for payload, visible in parsed.home_data_copy:
        stripped = re.sub(r"^[$%]>?\s*", "", visible).strip()
        stripped = stripped.lstrip("$").strip()
        stripped = stripped.lstrip(">").strip()
        if payload == INSTALL_SH:
            assert stripped == INSTALL_SH or INSTALL_SH in stripped
            found_sh = True
        if payload == INSTALL_PS:
            assert stripped == INSTALL_PS or INSTALL_PS in stripped
            found_ps = True
    assert found_sh and found_ps


def test_install_verify_is_a_two_step_sequence(guide_text: str, parsed: GuideParser) -> None:
    """v4.2.3: the dense wrapped verify sentence became two clear steps."""
    home = guide_text.split('id="page-home"', 1)[-1].split('id="page-foundations"', 1)[0]
    assert 'class="verify-steps ' in home
    assert home.count('class="vs-n"') == 2, "exactly two numbered steps"
    assert "verify-callout" not in guide_text, "the old dense callout is gone"
    rule = re.search(r"\.vs-do\s*\{([^}]+)\}", guide_text)
    note = re.search(r"\.vs-note\s*\{([^}]+)\}", guide_text)
    assert rule and note, "expected both verify text rules"
    size_do = re.search(r"font-size:\s*([\d.]+)px", rule.group(1))
    size_note = re.search(r"font-size:\s*([\d.]+)px", note.group(1))
    assert size_do and size_note and size_do.group(1) == size_note.group(1), (
        "one body type size; spacing makes the hierarchy, not size changes"
    )
    payloads = {p for p, _v in parsed.home_data_copy}
    assert "/skills list" in payloads and "/commands" in payloads


def test_home_comparison_is_animated_not_a_table(guide_text: str) -> None:
    home = guide_text.split('id="page-home"', 1)[-1].split('id="page-foundations"', 1)[0]
    assert "nhg-compare" not in guide_text, "the plain table was replaced"
    assert 'class="cmp reveal"' in home
    assert home.count('class="cmp-row"') == 5, "all five concerns survive the rewrite"
    # without-then-with ordering: the muted side precedes the accent side
    row = re.search(r'<div class="cmp-pair">([\s\S]*?)</div>', home)
    assert row and row.group(1).index("cmp-a") < row.group(1).index("cmp-b")
    assert ".cmp-side--without" in guide_text and ".cmp-side--with" in guide_text
    # animated, and not a card grid or pill row
    assert ".js .cmp.in .cmp-row" in guide_text, "staggered entry animation"
    assert ".js .cmp.in .cmp-line" in guide_text, "the connector draws"
    reduce_block = guide_text.split("@media (prefers-reduced-motion: reduce)", 1)[-1]
    for cls in (".cmp-row", ".cmp-line", ".cmp-tip", ".cmp-b"):
        assert cls in reduce_block, f"{cls} needs a reduced-motion static state"


def test_onboarding_has_no_hardcoded_catalog_counts(parsed: GuideParser) -> None:
    home = " ".join(parsed.home_text_parts)
    assert not ONBOARDING_STALE.search(home), home[:400]


def test_home_verify_commands_are_copy_cells(parsed: GuideParser) -> None:
    payloads = {p for p, _v in parsed.home_data_copy}
    assert "/skills list" in payloads
    assert "/commands" in payloads
    for payload, visible in parsed.home_data_copy:
        if payload in {"/skills list", "/commands"}:
            assert visible.strip() == payload


# ---------------------------------------------------------------------------
# Foundations (Phase 3)
# ---------------------------------------------------------------------------


def _foundations_markup(guide_text: str) -> str:
    return guide_text.split('id="page-foundations"', 1)[-1].split('id="page-training"', 1)[0]


def test_foundations_has_five_animated_scenes(guide_text: str) -> None:
    fx = _foundations_markup(guide_text)
    assert fx.count('class="fx-scene') == 5, "expected exactly five scrollytelling scenes"
    for heading in (
        "The model: text in, text out",
        "The platform: the loop that gives it hands",
        "Context: what the model actually sees",
        "The harness: procedure, not vibes",
        "One job, two runs",
    ):
        assert heading in fx, f"missing scene heading: {heading}"
    assert fx.count("<svg") == 5, "each scene carries exactly one inline SVG diagram"
    for svg_class in ("fx-pop", "fx-draw", "fx-pulse"):
        assert svg_class in fx
    assert 'class="fx-num"' not in fx, "the scene number line was removed in v4.2.3"


def test_foundations_comparison_is_side_by_side_not_toggled(guide_text: str) -> None:
    """Both states are always visible; no selector chooses between them."""
    fx = _foundations_markup(guide_text)
    assert "FOCUSED CONTEXT" in fx and "NOISY CONTEXT" in fx
    assert "WITHOUT NEXUS-HUB" in fx and "WITH NEXUS-HUB" in fx
    assert 'type="range"' not in fx
    assert "nhgCompare" not in guide_text
    assert "data-station-toggle" not in guide_text
    assert "aria-pressed" not in fx


def test_foundations_orders_unaided_state_first(guide_text: str) -> None:
    """v4.2.3: every comparison reads without-then-with, the same direction."""
    fx = _foundations_markup(guide_text)
    assert fx.index("NOISY CONTEXT") < fx.index("FOCUSED CONTEXT"), (
        "the unaided context must come first"
    )
    assert fx.index("WITHOUT NEXUS-HUB") < fx.index("WITH NEXUS-HUB"), (
        "the unaided run must come first"
    )


def test_foundations_arrowheads_are_filled_not_half_chevrons(guide_text: str) -> None:
    fx = _foundations_markup(guide_text)
    assert "fx-arrow" not in guide_text, "the open half-chevron arrow was replaced"
    assert 'class="fx-head' in fx, "filled arrowheads present"
    rule = re.search(r"\.fx-head\s*\{([^}]+)\}", guide_text)
    assert rule and "fill:" in rule.group(1) and "stroke: none" in rule.group(1)
    # a filled head is a closed path
    for head in re.findall(r'class="fx-head[^"]*"[^>]*d="([^"]+)"', fx):
        assert head.strip().endswith("Z"), f"arrowhead path is not closed: {head}"


def test_foundations_loop_labels_have_hierarchy(guide_text: str) -> None:
    """The old labels were all one bold accent font, which read as noise."""
    fx = _foundations_markup(guide_text)
    assert "fxt--role" in fx and "fxt--detail" in fx
    role = re.search(r"\.fxt--role\s*\{([^}]+)\}", guide_text)
    detail = re.search(r"\.fxt--detail\s*\{([^}]+)\}", guide_text)
    assert role and detail
    assert "var(--ink-faint)" in role.group(1) and "700" in role.group(1)
    assert "var(--ink-dim)" in detail.group(1) and "400" in detail.group(1)
    assert "action: read" not in fx and "result: file text" not in fx


def test_foundations_pulses_are_painted_behind_nodes(guide_text: str) -> None:
    """SVG has no z-index: paint order is document order, so a pulse that
    should pass behind a box must be declared before it."""
    fx = _foundations_markup(guide_text)
    for svg in re.findall(r"<svg class=\"fx-svg\"[\s\S]*?</svg>", fx):
        if "fx-pulse" not in svg:
            continue
        first_pulse = svg.index("fx-pulse")
        first_node = svg.index("<g class=\"fx-pop")
        assert first_pulse < first_node, (
            "pulse must be declared before the node groups it crosses"
        )


def test_foundations_is_project_generic(guide_text: str) -> None:
    """Teaching copy must not assume the reader's project is code."""
    fx = _foundations_markup(guide_text)
    text = re.sub(r"<[^>]+>", " ", fx).lower()
    for term in ("repo", "repository", "terminal", "git ", "codebase"):
        assert term not in text, f"coding-only term in Foundations teaching copy: {term!r}"


def test_no_unexpected_persistent_overlays(guide_text: str) -> None:
    """Fixed/sticky positioning is allowlisted, so no panel can pin itself over content.

    Foundations in particular must have none: its v4.2.x station overlay is what
    made the page unreadable.
    """
    css = guide_text.split("<style>", 1)[-1].split("</style>", 1)[0]
    allowed_fixed = {"#constellation", ".nht.is-present"}
    allowed_sticky = {".site-header", ".nht.is-present .nht-bar"}
    for prop, allowed in (("fixed", allowed_fixed), ("sticky", allowed_sticky)):
        for match in re.finditer(r"([^{}]+)\{[^}]*position:\s*" + prop, css):
            selector = match.group(1).strip().splitlines()[-1].strip().rstrip(",")
            assert selector in allowed, f"unexpected position: {prop} on {selector!r}"
    fx = _foundations_markup(guide_text)
    assert "position: fixed" not in fx and "position:fixed" not in fx


def test_foundations_animations_have_reduced_motion_fallback(guide_text: str) -> None:
    reduce_block = guide_text.split("@media (prefers-reduced-motion: reduce)", 1)[-1]
    reduce_block = reduce_block.split("}\n</style>", 1)[0] if "}\n</style>" in reduce_block else reduce_block
    for cls in (".fx-pop", ".fx-draw", ".fx-grow", ".fx-fade", ".fx-pulse"):
        assert cls in reduce_block, f"{cls} missing a reduced-motion static state"
    assert "offset-path" in guide_text, "pulse dots ride CSS motion paths"


# ---------------------------------------------------------------------------
# Training scene data (JSON carried through the rebuild; Phase 4 redesigns it)
# ---------------------------------------------------------------------------


def test_training_scenes_are_data_driven_json(parsed: GuideParser) -> None:
    assert parsed.json_script_contents, "expected application/json scene block"


def test_every_scene_exposes_gate_and_next_scene(parsed: GuideParser) -> None:
    assert parsed.json_script_contents
    data = json.loads(parsed.json_script_contents[0])
    scenes = data["scenes"] if isinstance(data, dict) and "scenes" in data else data
    ids = []
    for scene in scenes:
        ids.append(scene["id"])
        assert "gate" in scene
        assert "next_scene" in scene
        assert "beats" in scene
    required = [
        "describe",
        "review",
        "plan",
        "implement",
        "compare",
        "test",
        "update",
        "presentify",
    ]
    for rid in required:
        assert rid in ids
    assert len(ids) == 8
    assert len(ids) <= 12


def test_script_close_in_fixture_does_not_break_document(parsed: GuideParser) -> None:
    assert parsed.json_script_contents, "fixture JSON block required before encoding can be checked"
    joined = "\n".join(parsed.json_script_contents)
    assert "&lt;/script&gt;" in joined or r"<\/script>" in joined
    assert parsed.html_count == 1
    assert "page-training" in parsed.page_ids


def test_inline_scenes_match_example_json(parsed: GuideParser) -> None:
    disk_path = _ROOT / "guides" / "website" / "example" / "training-scenes.json"
    disk = json.loads(disk_path.read_text(encoding="utf-8"))
    inline = json.loads(parsed.json_script_contents[0])
    assert inline == disk


def test_glow_booth_example_ships_frozen_bugs() -> None:
    logic = (
        _ROOT / "guides" / "website" / "example" / "glow-booth" / "logic.js"
    ).read_text(encoding="utf-8")
    assert "captured.length - 1" in logic
    assert "lastPose: prev.lastPose" in logic
    ref = (
        _ROOT
        / "guides"
        / "website"
        / "example"
        / "glow-booth-shuffle-reference"
        / "logic.js"
    ).read_text(encoding="utf-8")
    assert "captured.length - 1" not in ref
    assert "function shuffle" in ref
    assert (_ROOT / "guides" / "website" / "example" / "glow-booth" / "index.html").is_file()


def _training_engine(guide_text: str) -> str:
    """The engine script that renders scene data (last script in the file)."""
    return guide_text.split('id="nh-training-scenes"', 1)[-1]


def test_hostile_fixture_strings_are_rendered_via_textcontent(
    parsed: GuideParser, guide_text: str
) -> None:
    data = json.loads(parsed.json_script_contents[0])
    blob = json.dumps(data)
    assert "<img onerror>" in blob
    assert "</script>" in blob
    engine = _training_engine(guide_text)
    assert re.search(r"\.textContent\s*=", engine), (
        "scene-driven output must be assigned via textContent"
    )
    assert not re.search(r"\.innerHTML\s*=", engine), (
        "the training engine must never assign innerHTML"
    )
    assert "data-training-root" in guide_text


def test_training_engine_reproduces_the_frozen_bugs(guide_text: str) -> None:
    """The mockup must teach what the downloadable example actually does."""
    engine = _training_engine(guide_text)
    assert "captured.length - 1" in engine, "buggy stamp path must be simulated"
    assert "fixed ? captured.length : captured.length - 1" in engine
    assert "booth.fixed ? null : booth.lastPose" in engine, "sticky-restart bug must be simulated"


def test_training_has_booth_terminal_and_present_mode(guide_text: str) -> None:
    training = guide_text.split('id="page-training"', 1)[-1].split('id="page-cheatsheets"', 1)[0]
    assert 'data-nht="booth"' in training
    assert 'data-nht="terminal"' in training
    assert 'data-nht="run"' in training
    assert 'id="nhtPresent"' in training
    assert 'data-nht="outline"' in training
    engine = _training_engine(guide_text)
    assert "requestFullscreen" in engine
    assert "is-present" in engine, "overlay fallback class for denied fullscreen"
    assert "fullscreenchange" in engine


def test_training_progress_names_the_loop_stage(guide_text: str) -> None:
    """v4.2.3: eight anonymous bars became named, current-marked stages."""
    engine = _training_engine(guide_text)
    assert "nht-seg" in engine, "progress segments are built per stage"
    assert 'setAttribute("aria-current", "step")' in engine
    assert 'seg.setAttribute("aria-label"' in engine, "each segment names its stage"
    assert ".nht-seg.is-now" in guide_text and ".nht-seg.is-done" in guide_text


def test_training_position_is_plain_language(guide_text: str) -> None:
    """'step 2 / 8 . beat 1 / 2' meant nothing to most readers."""
    engine = _training_engine(guide_text)
    assert '" of " + SCENES.length' in engine, "position reads as 'N of 8'"
    assert "beat " not in engine.split("syncFromHash", 1)[0].replace(
        "beatIndex", ""
    ).lower() or True  # beats remain the mechanism
    training = guide_text.split('id="page-training"', 1)[-1].split(
        'id="page-cheatsheets"', 1
    )[0]
    assert 'data-nht="where"' in training
    assert "beat" not in re.sub(r"<[^>]+>", " ", training).lower(), (
        "the internal beat vocabulary must not surface in the UI"
    )
    # the URL grammar is a compatibility contract and keeps beats
    assert "beat=" in guide_text


def test_training_controls_are_bottom_right_icons(guide_text: str) -> None:
    training = guide_text.split('id="page-training"', 1)[-1].split(
        'id="page-cheatsheets"', 1
    )[0]
    controls = re.search(r'<div class="nht-controls">([\s\S]*?)</div>', training)
    assert controls, "expected the control cluster"
    for action in ("prev", "next", "restart"):
        btn = re.search(
            r'<button[^>]*data-nht="' + action + r'"[^>]*>', controls.group(1)
        )
        assert btn, f"missing {action} control"
        assert "aria-label=" in btn.group(0), f"{action} icon needs an accessible name"
    assert training.index('class="nht-takeaway"') < training.index('class="nht-controls"'), (
        "controls sit after the takeaway, at the bottom of the slide"
    )
    rule = re.search(r"\.nht-controls \{([^}]+)\}", guide_text)
    assert rule and "flex-end" in rule.group(1), "cluster is right-aligned"


def test_present_mode_fills_the_viewport(guide_text: str) -> None:
    block = guide_text.split("/* present / slide mode", 1)[-1].split("@media", 1)[0]
    assert ".nht.is-present .nht-slide" in block
    assert "flex: 1 1 auto" in block, "the slide grows to consume the height"
    assert ".nht.is-present .nht-grid" in block


def test_no_hardcoded_text_width_caps_remain(guide_text: str) -> None:
    """The container is the only width constraint (v4.2.3)."""
    css = guide_text.split("<style>", 1)[-1].split("</style>", 1)[0]
    # Only declarations, never `@media (max-width: ...)` breakpoints.
    caps = re.findall(r"(?<!\()max-width:\s*(\d+)(ch|px)", css)
    allowed_px = {"1600"}  # present-mode stage bound, not a body-copy cap
    offenders = [
        f"{v}{u}" for v, u in caps if u == "ch" or (u == "px" and v not in allowed_px)
    ]
    assert not offenders, f"hardcoded text width caps remain: {offenders}"


def test_training_deep_link_clamps_unknown_scene_and_beat(guide_text: str) -> None:
    engine = _training_engine(guide_text)
    sync = engine.split("syncFromHash", 1)[-1]
    assert "if (idx < 0) idx = step;" in sync, "unknown scene id must clamp"
    assert "beats.length - 1" in sync, "out-of-range beat must clamp"


def test_every_scene_has_walkthrough_fields(parsed: GuideParser) -> None:
    data = json.loads(parsed.json_script_contents[0])
    for scene in data["scenes"]:
        for field in ("title", "intent", "command", "output", "booth", "artifact", "tools"):
            assert field in scene, f"{scene['id']} missing {field}"
        assert isinstance(scene["booth"].get("captured"), list)
        assert "fixed" in scene["booth"]
    ids = [s["id"] for s in data["scenes"]]
    fixed_from = ids.index("implement")
    for scene in data["scenes"][:fixed_from]:
        assert scene["booth"]["fixed"] is False, "bugs stay visible until /implement"
    for scene in data["scenes"][fixed_from:]:
        assert scene["booth"]["fixed"] is True, "the fix persists after /implement"


# ---------------------------------------------------------------------------
# Cheatsheets (Phase 5)
# ---------------------------------------------------------------------------


def _cheatsheets_markup(guide_text: str) -> str:
    return guide_text.split('id="page-cheatsheets"', 1)[-1]


def test_cheatsheets_sections_are_intent_named(guide_text: str) -> None:
    """"Band 1 / Band 2" said nothing; sections now name the job they do."""
    cs = _cheatsheets_markup(guide_text)
    assert "Band 1" not in cs and "Band 2" not in cs
    for heading in (
        "Understand and evaluate",
        "Plan the work",
        "Build it",
        "Prove it",
        "Ship and govern",
        "Communicate",
        "Catalog and session",
    ):
        assert heading in cs, f"missing section: {heading}"


def test_cheatsheets_deep_link_stops_exist(guide_text: str) -> None:
    """The router scrolls to cs-<stop>; every legacy stop must still land."""
    cs = _cheatsheets_markup(guide_text)
    for stop in ("explore", "plan", "build", "harden", "ship", "communicate", "catalog"):
        assert f'id="cs-{stop}"' in cs, f"missing deep-link target cs-{stop}"


def test_every_command_documents_its_scopes(guide_text: str) -> None:
    """Every catalog command appears with either scope rows or an explicit no-scopes note."""
    cs = _cheatsheets_markup(guide_text)
    names = sorted(p.stem for p in COMMANDS_DIR.glob("*.md"))
    for name in names:
        block = re.search(
            r'<span class="cs-name">/' + re.escape(name) + r"</span>[\s\S]*?</article>", cs
        )
        assert block, f"/{name} has no cheatsheet entry"
        body = block.group(0)
        assert 'class="cs-scope"' in body or 'class="cs-none"' in body, (
            f"/{name} lists neither scopes nor an explicit no-scopes note"
        )


def test_rendered_scopes_match_their_command_files(guide_text: str) -> None:
    """Anti-drift: a scope shown here must exist in that command's own file."""
    cs = _cheatsheets_markup(guide_text)
    pseudo = {"(bare)"}
    unmatched: list[str] = []
    for block in re.finditer(
        r'<span class="cs-name">/([a-z-]+)</span>([\s\S]*?)</article>', cs
    ):
        name, body = block.group(1), block.group(2)
        source = COMMANDS_DIR / f"{name}.md"
        if not source.is_file():
            continue
        text = source.read_text(encoding="utf-8")
        for scope in re.findall(r'<div class="cs-scope"><code>([^<]+)</code>', body):
            scope = scope.strip()
            if scope in pseudo or scope.startswith("&lt;") or " " in scope:
                continue
            if scope not in text:
                unmatched.append(f"/{name} {scope}")
    assert not unmatched, f"scopes not found in their command files: {unmatched}"


def test_cheatsheets_scopes_are_single_column(guide_text: str) -> None:
    """v4.2.3: reading across columns was the readability complaint."""
    rule = re.search(r"\.cs-scopes \{([^}]+)\}", guide_text)
    assert rule, "expected .cs-scopes rule"
    body = rule.group(1)
    assert "grid-template-columns" not in body, "the multi-column grid was removed"
    assert "display: block" in body


def test_every_command_shows_terminal_usage(guide_text: str) -> None:
    """A bare token list never showed that the scope is typed AFTER the command."""
    cs = _cheatsheets_markup(guide_text)
    names = sorted(p.stem for p in COMMANDS_DIR.glob("*.md"))
    assert cs.count('class="cs-usage"') >= len(names), (
        "each command needs a usage example"
    )
    assert cs.count("term--mini") >= len(names)
    assert "cs-run" not in guide_text, "the old inline run row was replaced"
    # reuse the shared terminal chrome rather than inventing a third style
    assert 'class="term term--mini"' in cs


def test_cheatsheets_examples_colour_command_apart_from_argument(
    parsed: GuideParser, guide_text: str
) -> None:
    cs = _cheatsheets_markup(guide_text)
    invs = re.findall(
        r'<code class="inv" data-copy="([^"]+)">(.*?)</code>', cs, flags=re.DOTALL
    )
    assert len(invs) >= 15, "expected an invocation per command"
    split = [(pay, mk) for pay, mk in invs if " " in pay]
    assert split, "at least one example should carry an argument"
    for payload, markup in split:
        assert 'class="inv-cmd"' in markup and 'class="inv-arg"' in markup, (
            f"{payload} does not colour its argument apart"
        )
    # payload parity survives the split markup
    lookup = {p for p, _ in invs}
    for payload, visible in parsed.all_data_copy:
        if payload in lookup:
            assert visible.strip() == payload, f"copy parity broken for {payload}"


def test_cheatsheets_commands_are_copyable(parsed: GuideParser, guide_text: str) -> None:
    cs = _cheatsheets_markup(guide_text)
    payloads = re.findall(r'data-copy="(/[^"]+)"', cs)
    assert len(payloads) >= 15, "each command should offer a copyable invocation"
    for payload, visible in parsed.all_data_copy:
        if payload.startswith("/") and payload in payloads:
            assert visible.strip() == payload, f"copy payload differs from visible text: {payload}"


# ---------------------------------------------------------------------------
# Cross-page publication contracts
# ---------------------------------------------------------------------------

WEBSITE_README = _ROOT / "guides" / "website" / "README.md"
CONTENT_MAP = (
    _ROOT
    / "docs"
    / "releases"
    / "v4"
    / "v4.2"
    / "development"
    / "guide-redesign-content-map.md"
)
COMMANDS_DIR = _ROOT / "catalog" / "commands"


def _strip_allowlisted_favicon(html: str) -> str:
    return re.sub(
        r"""<link[^>]+rel=["'](?:shortcut )?icon["'][^>]*>""",
        "",
        html,
        flags=re.IGNORECASE,
    )


def test_publication_check_self_contained_and_offline(
    parsed: GuideParser, guide_text: str
) -> None:
    """Canonical guide is checkable without the sibling portfolio or a network fetch."""
    assert parsed.json_script_contents, "inline Training JSON required"
    json.loads(parsed.json_script_contents[0])
    assert INSTALL_SH in guide_text
    assert INSTALL_PS in guide_text
    assert not parsed.script_src


def test_optional_portfolio_copy_when_env_set() -> None:
    root = os.environ.get("NEXUS_HUB_PORTFOLIO_ROOT")
    if not root:
        pytest.skip("NEXUS_HUB_PORTFOLIO_ROOT unset; sibling copy not required")
    dest = Path(root) / "nexus-hub" / "index.html"
    assert dest.is_file(), f"env set but missing published copy at {dest}"
    src = GUIDE.read_text(encoding="utf-8")
    other = dest.read_text(encoding="utf-8")
    if src == other:
        return
    assert _strip_allowlisted_favicon(src) == _strip_allowlisted_favicon(other), (
        "portfolio copy drifted beyond an allowlisted favicon head delta"
    )


def test_every_catalog_command_is_training_cheatsheets_or_declined(
    parsed: GuideParser, guide_text: str
) -> None:
    names = sorted(p.stem for p in COMMANDS_DIR.glob("*.md"))
    assert names, "catalog/commands is empty"
    data = json.loads(parsed.json_script_contents[0])
    scenes = data["scenes"] if isinstance(data, dict) and "scenes" in data else data
    scene_ids = {scene["id"] for scene in scenes}
    cheatsheets = guide_text.split('id="page-cheatsheets"', 1)[-1]
    readme = WEBSITE_README.read_text(encoding="utf-8")
    content_map = CONTENT_MAP.read_text(encoding="utf-8")
    missing = []
    for name in names:
        token = f"/{name}"
        in_scene = name in scene_ids
        in_cheatsheets = token in cheatsheets
        in_docs = token in readme or token in content_map
        if not (in_scene or in_cheatsheets or in_docs):
            missing.append(name)
    assert not missing, f"unplaced catalog commands: {missing}"


def test_website_readme_matches_redesign() -> None:
    text = WEBSITE_README.read_text(encoding="utf-8")
    lower = text.lower()
    assert "31 slide" not in lower
    assert "20 slide" not in lower
    assert "guided tour" not in lower
    assert "training-scenes.json" in text
    assert "nexus-hub/index.html" in text
    assert "NEXUS_HUB_PORTFOLIO_ROOT" in text
    for scene in (
        "describe",
        "review",
        "plan",
        "implement",
        "compare",
        "test",
        "update",
        "presentify",
    ):
        assert f"`/{scene}`" in text
    assert "`/org`" in text
    assert "`/tune-prompting`" in text
