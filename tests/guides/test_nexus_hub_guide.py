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
        | Nexus[- ]Hub\s+v\d+\.\d+\.\d+
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


def test_legacy_example_assets_are_not_in_the_reader_path(guide_text: str) -> None:
    lower = guide_text.lower()
    assert "glow booth" not in lower
    assert "glow-booth" not in lower
    assert not re.search(r'<a[^>]+download(?:\s|=|>)', guide_text, re.IGNORECASE)
    assert (GUIDE.parent / "glow-booth.zip").is_file(), (
        "the legacy regression fixture remains until a separately approved deletion"
    )


def test_github_is_user_initiated_not_a_script(parsed: GuideParser) -> None:
    assert not parsed.script_src
    hrefs = [ad.get("href", "") for tag, ad in parsed.raw_attrs if tag == "a"]
    github = [h for h in hrefs if "github.com" in h]
    assert github, "expected a GitHub navigation link"


def test_global_runtime_does_not_round_trip_dom_content_through_html(
    guide_text: str,
) -> None:
    assert 'setAttribute("data-html"' not in guide_text
    assert not re.search(r"typed\.innerHTML\s*=", guide_text)


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
    assert 'aria-label="Nexus Hub on GitHub"' in tag
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
    assert "flex: 0 0 auto" not in body, "nav labels must shrink on narrow screens"
    assert "flex: 0 1 auto" in body and "width: auto" in body


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
    reduce_blocks = re.findall(
        r"@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{((?:[^{}]|\{[^{}]*\})*)\}",
        guide_text,
    )
    assert reduce_blocks, "expected a reduced-motion block"
    assert any(
        re.search(r"\.js \.reveal\s*\{[^}]*opacity:\s*1", block)
        for block in reduce_blocks
    ), "reduced motion must expose reveal content regardless of stylesheet ordering"


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
    # v4.4.1 Phase 2: the mark and wordmark share an inner float wrapper, and the title is
    # two nav-matched spans rather than the hyphenated single string.
    assert re.search(
        r'<div class="hero-lockup reveal">\s*<div class="hero-lockup-float">\s*'
        r'<svg class="hero-mark"[\s\S]*?</svg>\s*'
        r'<h1 class="hero-wordmark"><b>Nexus</b> <span>Hub</span></h1>',
        home,
    )
    assert "Nexus-Hub" not in home.split("</h1>", 1)[0]
    lockup_rule = re.search(r"\.hero-lockup\s*\{([^}]+)\}", guide_text)
    assert lockup_rule and "justify-content: center" in lockup_rule.group(1)
    float_rule = re.search(r"\.hero-lockup-float\s*\{([^}]+)\}", guide_text)
    assert float_rule and "flex-wrap: nowrap" in float_rule.group(1)
    wordmark_rule = re.search(r"\.hero-wordmark\s*\{([^}]+)\}", guide_text)
    assert wordmark_rule and "white-space: nowrap" in wordmark_rule.group(1)
    assert "clamp(" in wordmark_rule.group(1), "the 320 px lockup needs fluid type"
    assert ".js .hero-lockup.reveal .hero-mark" in guide_text
    assert ".js .hero-lockup.in .hero-mark" in guide_text
    reduced_motion = guide_text.split("@media (prefers-reduced-motion: reduce)", 1)[-1]
    assert ".js .hero-lockup.reveal .hero-mark" in reduced_motion


def test_home_hero_restores_the_v412_subtitle_and_lead(guide_text: str) -> None:
    home = _home_markup(guide_text)
    assert "hero-tagline" not in home, "the v4.4.1 tagline is replaced by the v4.1.2 statement"
    sub = re.search(r'<h2 class="hero-subtitle">([\s\S]*?)</h2>', home)
    assert sub and re.sub(r"<[^>]+>", "", sub.group(1)) == (
        "Upgrade any agentic AI platform with an autonomous team of world experts"
    )
    assert '<span class="gtext">autonomous team of world experts</span>' in sub.group(1)
    lead = re.search(r'<p class="hero-lead">([^<]+)</p>', home)
    assert lead and lead.group(1).startswith("Nexus Hub is an advanced harness for agentic AI platforms.")


def test_home_lists_the_five_approved_platforms_from_ledger_bytes(guide_text: str) -> None:
    """v4.4.1 Phase 2 replaces the six-item rail, and every mark must be an APPROVED byte sequence.

    The hash comparison runs against the raw embedded substring before any normalization, so a
    re-fetched, re-minified, or hand-edited mark fails here instead of shipping an unreviewed
    third-party asset into a published page.
    """
    import hashlib

    home = _home_markup(guide_text)
    rail = re.search(r'<ul class="platform-rail"[\s\S]*?</ul>', home)
    assert rail, "expected a dedicated compatibility rail"
    items = re.findall(
        r'<li class="platform-item"[^>]*data-platform="([^"]+)"[^>]*>([\s\S]*?)</li>', rail.group(0)
    )
    assert [platform for platform, _body in items] == [
        "Claude",
        "ChatGPT",
        "Gemini",
        "Cursor",
        "GitHub Copilot",
    ]

    staged_dir = (
        _ROOT
        / "docs"
        / "releases"
        / "v4"
        / "v4.4"
        / "development"
        / "guide-visual-and-arcade-rebuild"
        / "assets"
    )
    stems = {
        "Claude": "claude",
        "ChatGPT": "chatgpt",
        "Gemini": "gemini",
        "Cursor": "cursor",
        "GitHub Copilot": "github-copilot",
    }
    for platform, body in items:
        stem = stems[platform]
        assert f'<span class="platform-name">{platform}</span>' in body
        assert f'data-mark="{stem}"' in body, f"{platform} mark is not tagged with its ledger stem"
        assert 'aria-hidden="true"' in body, f"{platform} decorative mark must be hidden from AT"
        embedded = re.search(r"(<svg[\s\S]*?</svg>)", body)
        assert embedded, f"{platform} has no inline geometry"
        blob = embedded.group(1)
        assert "<image" not in blob and "base64," not in blob, f"{platform} embeds a raster"
        assert "http" not in blob.replace('xmlns="http://www.w3.org/2000/svg"', ""), (
            f"{platform} references an external URL"
        )
        staged = (staged_dir / f"{stem}.svg").read_text(encoding="utf-8").strip()
        assert hashlib.sha256(blob.encode("utf-8")).hexdigest() == hashlib.sha256(
            staged.encode("utf-8")
        ).hexdigest(), (
            f"{platform} embedded bytes do not match the approved staged asset {stem}.svg; "
            "re-approval is required rather than a ledger update"
        )

    # The opaque shell and the text-treatment fallback both retired with the six-item rail.
    assert "platform-mark-shell" not in home
    assert "platform-item--text" not in home
    assert "OpenCode" not in home, "OpenCode and its instruction-file note were removed in v4.4.1"


def test_platform_mark_attribution_lives_in_the_site_footer(guide_text: str) -> None:
    """The GitHub Copilot codicon is CC BY 4.0, so attribution is a licence term, not a nicety.

    v4.4.2 (decision 2026-09-02-platform-mark-attribution-in-footer): the Home disclosure is
    gone and the attribution sits in the shared site footer, outside the Home reading flow but
    visible on every page that shows the marks.
    """
    home = _home_markup(guide_text)
    assert "platform-credits" not in home, "the Home credits disclosure was removed in v4.4.2"
    footer = re.search(r'<footer class="site-footer"[\s\S]*?</footer>', guide_text)
    assert footer, "a shared site footer must carry the attribution"
    body = footer.group(0)
    assert "CC BY 4.0" in body
    assert "Microsoft Corporation" in body
    assert "Codicons" in body
    assert "no affiliation or endorsement" in body, "nominative-use statement is missing"
    assert 'href="https://creativecommons.org/licenses/by/4.0/"' in body


def test_home_hero_is_the_unhyphenated_nexus_hub_lockup(guide_text: str) -> None:
    """v4.4.1 Phase 2: the hero title matches the nav wordmark and is no longer hyphenated."""
    home = _home_markup(guide_text)
    heading = re.search(r'<h1 class="hero-wordmark">([\s\S]*?)</h1>', home)
    assert heading, "expected the hero wordmark heading"
    inner = heading.group(1)
    assert inner == "<b>Nexus</b> <span>Hub</span>", (
        f"hero wordmark must mirror the nav structure exactly; got {inner!r}"
    )
    text = re.sub(r"<[^>]+>", "", inner).strip()
    assert text == "Nexus Hub", f"hero title must read 'Nexus Hub'; got {text!r}"
    assert "Nexus-Hub" not in heading.group(0)
    # The float lives on an inner wrapper so it never competes with the .reveal entry transform.
    assert '<div class="hero-lockup-float">' in home


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
    assert "Raw prompting vs Nexus Hub" in home, "v4.4.2 merges the two comparisons under one title"
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
    """v4.4.2: a count may appear only through a stamped data-count marker, so every count-bearing
    phrase in Home text must equal the CURRENT catalog value; a stale literal fails here."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("stamp_guide_counts", _ROOT / "scripts" / "stamp_guide_counts.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    counts = mod.compute_counts(_ROOT)
    home = re.sub(r"\s+", " ", " ".join(parsed.home_text_parts))
    for match in ONBOARDING_STALE.finditer(home):
        phrase = match.group(0)
        num = re.search(r"\d+", phrase)
        noun = re.search(r"skills|hooks|commands", phrase, re.IGNORECASE)
        assert num and noun, f"non-count stale marker in Home: {phrase!r}"
        assert int(num.group(0)) == counts[noun.group(0).lower()], f"stale count in Home: {phrase!r}"


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


def _foundation_scene(guide_text: str, scene_id: str) -> str:
    fx = _foundations_markup(guide_text)
    scene = re.search(
        rf'<section[^>]+id="{re.escape(scene_id)}"[\s\S]*?</section>', fx
    )
    assert scene, f"missing Foundations scene: {scene_id}"
    return scene.group(0)


def test_foundations_phase3_has_eight_title_subtitle_scenes(guide_text: str) -> None:
    fx = _foundations_markup(guide_text)
    # v4.4.3 merged the two harness scenes into one, on the review's instruction that a reader
    # needs one picture of where the two loops sit rather than two to superimpose.
    # v4.4.4 merged the chatbot comparison into the Agentic Platforms scene, on the review's
    # instruction that one segment should carry the idea.
    assert fx.count('class="fx-scene') == 6, "expected six Foundations scenes"
    assert fx.count('class="fx-title"') == 6
    assert fx.count('class="fx-subtitle"') == 6
    expected = [
        "Tokens Definition",
        "Prompt Engineering",
        "Context Engineering",
        "Models",
        "Agentic Platforms",
        "Harnesses",
    ]
    found = re.findall(r'<h2 id="[^"]+"[^>]*>([^<]*)</h2>', fx)
    assert found == expected, (
        f"Foundations scene order is wrong; got {found} expected {expected}"
    )
    assert not re.search(r"What (?:Is|Are)", fx), (
        "the old 'What Is / What Are' heading construction must not survive"
    )
    assert fx.count("<svg") >= 7, "each scene carries inline visual teaching"
    # v4.4.1 Phase 4 retired fx-pulse with the last SVG story diagram; pop and draw remain
    # live on the tokens connector, and the chip/cycle primitives carry the rest.
    for svg_class in ("fx-pop", "fx-draw"):
        assert svg_class in fx
    assert 'class="fx-num"' not in fx, "the scene number line was removed in v4.2.3"


def test_foundations_chatbot_and_agent_share_a_request_but_not_the_handoff(
    guide_text: str,
) -> None:
    # v4.4.4: the comparison lives inside the Agentic Platforms scene now.
    scene = _foundation_scene(guide_text, "fx-agent-platform")
    assert "Agentic Platforms" in scene
    assert "Where a chatbot answers, an agentic platform can act" in scene
    # v4.4.1 Phase 4: the comparison is an HTML two-lane group, chatbot lane first.
    assert scene.count('data-phase3-node="shared-request"') == 1
    assert scene.index('data-phase3-node="chatbot-handoff"') < scene.index(
        'data-phase3-node="agent-handoff"'
    )
    # v4.4.5 added the mockup's six-part anatomy to this scene, which names `Boundary` a third
    # time in a different block. The claim was always about the two LANES carrying matching
    # labels, so it is measured over the lane lists rather than over the whole scene.
    lanes = "".join(
        scene[m.start() : scene.index("</dl>", m.start())]
        for m in re.finditer(r'<dl class="fx-parts">', scene)
    )
    assert lanes.count('<dl class="fx-parts">') == 2, "expected exactly two lanes"
    for part in ("Boundary", "Action", "Outcome", "Leaves behind"):
        assert lanes.count("<dt>" + part + "</dt>") == 2, (
            "both lanes must carry an explicit " + part + " label"
        )
    text = re.sub(r"<[^>]+>", " ", scene).lower()
    assert "same request" in text
    assert "answer handoff" in text and "every step is applied and checked" in text
    assert "work handoff" in text and "saved change" in text and "checked result" in text
    assert re.search(r"chatbots?.{0,100}(?:can|may|increasingly).{0,60}tools", text)
    assert "where the work happens" in text
    assert re.search(r"what .{0,30} leaves behind", text)
    # Honest capability language, never a promise.
    assert "when permitted" in text and "supported" in text
    assert "promises success" in text or "promise" in text


def test_foundations_context_makes_budget_competition_and_full_behavior_visible(
    guide_text: str,
) -> None:
    """v4.4.1 Phase 3: context is separable from the request, finite, and selectable."""
    scene = _foundation_scene(guide_text, "fx-context")
    assert 'class="fx-ctx-query"' in scene and 'class="cx-mat' in scene
    for kind in ("Attached image", "Attached PDF", "Selected folder"):
        assert '<span class="cx-kind">' + kind + "</span>" in scene, (
            "missing selected context: " + kind
        )
    assert scene.index("fx-spend-tag--bad") < scene.index("fx-spend-tag--good"), (
        "the unfocused selection must read before the task-matched one"
    )
    text = re.sub(r"<[^>]+>", " ", scene).lower()
    for concept in ("token", "finite", "optional", "stale", "duplicated", "too large"):
        assert concept in text, "missing context concept: " + concept
    assert "conversation" in text and "tool results" in text
    assert 'type="range"' not in scene and "aria-pressed" not in scene
    assert not re.search(r"\b\d+(?:\.\d+)?\s+tokens?\s+per\s+word\b", scene, re.IGNORECASE)


def test_foundations_harness_layers_are_honest_and_repository_anchored(
    guide_text: str,
) -> None:
    """v4.4.3 merged the two harness scenes: one scene now defines a harness AND shows what the
    Nexus Hub layer adds, so all three layers and the five repository-anchored claims live here.
    The rules are unchanged; only the scene they live in is."""
    harness = _foundation_scene(guide_text, "fx-harness")
    for layer in ("model", "platform", "nexus-hub"):
        assert f'data-phase3-harness-layer="{layer}"' in harness
    htext = re.sub(r"<[^>]+>", " ", harness).lower()
    assert re.search(r"(?:every|agentic) platform.{0,80}(?:already|ships).{0,40}harness", htext)
    for part in ("context", "tools", "permissions", "execution", "observations"):
        assert part in htext, f"the built-in loop must name {part}"
    for part in ("skills", "hooks", "gates", "artifacts"):
        assert part in htext, f"the outer loop must name {part}"

    practice = harness
    claims = re.findall(
        r'data-phase3-claim="([^"]+)" data-artifact="([^"]+)"', practice
    )
    assert {claim for claim, _artifact in claims} == {
        "one-source-catalog",
        "matched-procedures",
        "event-hooks",
        "written-gates",
        "durable-artifacts",
    }
    assert all(artifact.strip() for _claim, artifact in claims)
    ptext = re.sub(r"<[^>]+>", " ", practice).lower()
    for claim in ("one source", "hooks", "prompt-independent", "definition of done"):
        assert claim in ptext
    assert "chain" in ptext, "the trail must show artifacts chaining between commands"
    assert "does not replace the model" in ptext, "the honest scope qualifier is required"
    assert re.search(r"only where the host exposes the registered event", ptext)
    for vendor in ("claude", "codex", "cursor", "copilot", "antigravity"):
        assert not re.search(rf"{vendor}.{{0,30}}(?:lacks?|cannot|does not)", ptext)


def test_foundations_phase3_diagrams_animate_with_observer_and_static_fallback(
    guide_text: str,
) -> None:
    """v4.4.1 Phase 4: the story diagrams are HTML node trees.

    v4.4.3 removed the spinning work-cycle ring from both scenes: it depicted nothing a reader
    could name, and its own caption had to say so. The shared grammar it provided is still
    required, now as the one-pass block, and the remaining continuous motion is the hero lockup,
    which keeps the liveness gate the ring used to carry.
    """
    fx = _foundations_markup(guide_text)
    assert 'class="fx-cycle"' not in fx, "the work-cycle ring must not come back into a scene"
    assert ".js .hero-lockup.live .hero-lockup-float" in guide_text, (
        "continuous motion must be gated on liveness, not free-running"
    )
    scene_selector = re.search(r'var scenes = document.querySelectorAll\("([^"\n]+)"\)', guide_text)
    assert scene_selector
    assert {".fx-scene", ".hero-lockup", ".guard-fig", ".ph"} <= {
        selector.strip() for selector in scene_selector.group(1).split(",")
    }
    assert "IntersectionObserver" in guide_text
    reduce_block = guide_text.split("@media (prefers-reduced-motion: reduce)", 1)[-1]
    assert ".fx-tokchip" in reduce_block, "token chips need a static reduced-motion state"
    assert "nhg-lockup-float" in guide_text and ".hero-lockup-float" in reduce_block, (
        "the lockup float needs a static reduced-motion state"
    )
    for retired in ("fx-pulse", "fx-grow", "fx-fade"):
        assert retired not in guide_text, (
            retired + " was retired; a reintroduced consumer must restore its states"
        )




def test_foundations_tokens_use_a_reproducible_nonuniversal_example(
    guide_text: str,
) -> None:
    """v4.4.1 Phase 3: a real prompt, a verified split, and equivalent chips.

    The split asserted below is the actual cl100k_base encoding of the displayed prompt,
    so the example is reproducible rather than illustrative. "Summarise" costing three
    tokens is the whole teaching point: a token is not a word.
    """
    scene = _foundation_scene(guide_text, "fx-tokens")
    assert 'data-tokenizer="cl100k_base"' in scene
    assert "Summarise this contract and list every deadline." in scene
    space = "\u2423"
    expected = [
        "Sum", "mar", "ise", space + "this", space + "contract", space + "and",
        space + "list", space + "every", space + "deadline", ".",
    ]
    chips = re.findall(r'<span class="fx-tokchip-txt">([^<]*)</span>', scene)
    assert chips == expected, "token chips do not match the verified split: " + repr(chips)
    assert "fxchip--good" not in scene, (
        "a second chip style implies a category the tokenizer does not have"
    )
    lowered = scene.lower()
    assert "becomes 10 tokens" in lowered
    assert "a token is not a word" in lowered
    assert "other models cut the same sentence differently" in lowered
    assert scene.count('clip-path="url(#nxp-tokcell-') == 9, "expected nine cropped image cells"
    assert scene.count('href="#nxp-tokimg"') >= 10, (
        "the source plus every cell must draw the same artwork, so no cell can be empty"
    )
    assert 'data-phase2-connector="image-tokenization"' in scene
    assert "holds real pixels" in lowered
    assert "not a literal token count" in lowered
    assert not re.search(r"\b\d+(?:\.\d+)?\s+tokens?\s+per\s+word\b", scene, re.IGNORECASE)


def test_foundations_prompt_engineering_uses_one_non_coding_job(
    guide_text: str,
) -> None:
    """v4.4.1 Phase 3: one non-coding request, shown vague and then precise."""
    scene = _foundation_scene(guide_text, "fx-prompts")
    # v4.4.4 rebuilt this scene: the vague prompt sits beside the reasons it fails and the
    # engineered prompt spans the diagram below. The `fx-state` lane classes went with the old
    # three-column grid, so the weaker-state-first rule is asserted on the new carriers.
    assert scene.index("Vague") < scene.index("Engineered"), "the weaker state must read first"
    assert scene.index('class="pe-box"') < scene.index('class="pe-precise"')
    # v4.4.5 renamed the parts Query, Context, Goal, Format on instruction. One word changed
    # MEANING rather than spelling: "Goal" now names the finish line the figure used to call
    # "Done". The old four are asserted absent, because a scene carrying both vocabularies
    # teaches neither.
    for part in ("Request", "Context", "Goal", "Format"):
        assert "<dt>" + part + "</dt>" in scene, "missing prompt part: " + part
    for retired in ("Material", "Done"):
        assert "<dt>" + retired + "</dt>" not in scene, "the old vocabulary survives: " + retired
    assert "Summarise this contract and list every deadline." in scene
    assert "Look at this contract." in scene
    # the flaws are named rather than summarised in one sentence
    for flaw in ("No request", "No context", "No goal", "No format"):
        assert flaw in scene, "missing named flaw: " + flaw
    assert "terminal" not in scene.lower() and "source code" not in scene.lower()


def test_foundations_mobile_phase2_diagrams_are_centered_and_bounded(
    guide_text: str,
) -> None:
    """v4.4.1 Phase 4 retired the dual desktop/mobile SVG variant system: the HTML scenes
    stack through one media query instead of shipping two drawings. This guard keeps the
    retirement honest; reintroducing a variant system must restore its bounding rules."""
    assert "fx-svg--mobile" not in guide_text
    assert "fx-svg--desktop" not in guide_text


def test_foundations_comparisons_show_both_states_without_a_toggle(
    guide_text: str,
) -> None:
    """Each teaching comparison keeps both states available in the same scene."""
    fx = _foundations_markup(guide_text)
    assert "fx-spend-tag--bad" in fx and "fx-spend-tag--good" in fx
    assert 'data-phase3-node="chatbot-handoff"' in fx
    assert 'data-phase3-node="agent-handoff"' in fx
    # v4.4.3: the merged harness scene carries the without-then-with trail.
    practice = _foundation_scene(guide_text, "fx-harness")
    assert ">PLATFORM LOOP<" in practice
    assert ">PLATFORM LOOP + NEXUS HUB<" in practice
    assert 'type="range"' not in fx
    assert "nhgCompare" not in guide_text
    assert "data-station-toggle" not in guide_text
    # Models has capability and effort selectors; the other comparisons remain fully visible.
    pressed = re.findall(r"<[^>]*aria-pressed[^>]*>", fx.replace(_foundation_scene(guide_text, "fx-model-lifecycle"), ""))
    assert all("data-media-toggle" in tag for tag in pressed), (
        "aria-pressed outside the media toggle suggests a comparison hidden behind a control"
    )


def test_foundations_orders_unaided_state_first(guide_text: str) -> None:
    """v4.2.3: every comparison reads without-then-with, the same direction."""
    fx = _foundations_markup(guide_text)
    assert fx.index("fx-spend-tag--bad") < fx.index("fx-spend-tag--good"), (
        "the unaided context must come first"
    )
    assert fx.index("fx-state--weak") < fx.index("fx-state--strong"), (
        "the weaker lane must come before the stronger one"
    )
    assert fx.index('data-phase3-node="chatbot-handoff"') < fx.index(
        'data-phase3-node="agent-handoff"'
    ), "the answer-handoff lane must come first"
    # v4.4.3: the merged harness scene carries the without-then-with trail.
    practice = _foundation_scene(guide_text, "fx-harness")
    assert practice.index(">PLATFORM LOOP<") < practice.index(
        ">PLATFORM LOOP + NEXUS HUB<"
    ), "the host-native run must come before the augmented run"


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
    # The surviving SVG labels keep the role class; the HTML scenes express the same
    # hierarchy through tag/body class pairs with distinct computed weight and colour.
    assert "fxt--role" in fx
    role = re.search(r"\.fxt--role\s*\{([^}]+)\}", guide_text)
    assert role and "var(--ink-faint)" in role.group(1) and "700" in role.group(1)
    for tag_cls in (".fx-out-tag", ".fx-mini-tag", ".fx-layer-tag"):
        rule = re.search(re.escape(tag_cls) + r"[^{]*\{([^}]+)\}", guide_text)
        assert rule, f"missing hierarchy tag rule {tag_cls}"
        assert "700" in rule.group(1) and "uppercase" in rule.group(1), (
            f"{tag_cls} must read as a small-caps role label"
        )
    assert "action: read" not in fx and "result: file text" not in fx


def test_models_network_signal_has_a_static_fallback_and_node_layer(guide_text: str) -> None:
    """The requested Models traversal restores motion with a readable node layer."""
    assert "fx-pulse" not in guide_text
    assert 'class="ml-graph" data-graph="language"' in guide_text
    assert '<use href="#ml-network"/>' in guide_text
    assert '.ml-node{stroke:var(--bg-0);' in guide_text
    assert 'animation-play-state:paused;' in guide_text
    assert '.ml-playing .ml-spark{animation-play-state:running;}' in guide_text
    assert "#fx-model-lifecycle *,#fx-model-lifecycle *::before{animation:none!important" in guide_text


def test_foundations_is_project_generic(guide_text: str) -> None:
    """Teaching copy must not assume the reader's project is code.

    v4.4.1 Phase 3 narrows this guard: "codebase" is now PERMITTED, because Context
    Engineering lists it as one of several kinds of material a request can carry. The
    positive requirement below is what stops that concession from quietly making the
    scene code-only, so the broad non-coding kinds must still appear alongside it.
    """
    fx = _foundations_markup(guide_text)
    text = re.sub(r"<[^>]+>", " ", fx).lower()
    for term in ("repo", "repository", "terminal", "git"):
        assert not re.search(r"\b" + re.escape(term) + r"\b", text), (
            "coding-only term in Foundations teaching copy: " + repr(term)
        )
    for broad in ("image", "file or document", "project folder or workspace"):
        assert broad in text, (
            "Foundations must keep broad non-coding context examples; missing " + repr(broad)
        )


def test_no_unexpected_persistent_overlays(guide_text: str) -> None:
    """Fixed/sticky positioning is allowlisted, so no panel can pin itself over content.

    Foundations in particular must have none: its v4.2.x station overlay is what
    made the page unreadable.
    """
    css = guide_text.split("<style>", 1)[-1].split("</style>", 1)[0]
    allowed_fixed = {"#constellation", ".nht.is-present"}
    allowed_sticky = {".site-header", ".nht.is-present .nht-bar", ".cx-preview-bar"}
    for prop, allowed in (("fixed", allowed_fixed), ("sticky", allowed_sticky)):
        for match in re.finditer(r"([^{}]+)\{[^}]*position:\s*" + prop, css):
            selector = match.group(1).strip().splitlines()[-1].strip().rstrip(",")
            assert selector in allowed, f"unexpected position: {prop} on {selector!r}"
    fx = _foundations_markup(guide_text)
    assert "position: fixed" not in fx and "position:fixed" not in fx


def test_foundations_animations_have_reduced_motion_fallback(guide_text: str) -> None:
    reduce_block = guide_text.split("@media (prefers-reduced-motion: reduce)", 1)[-1]
    reduce_block = reduce_block.split("}\n</style>", 1)[0] if "}\n</style>" in reduce_block else reduce_block
    # The live motion primitives after the Phase 4 rebuild: reveal pops, drawn connectors,
    # token-chip reveals, and the shared work-cycle spin.
    for cls in (".fx-pop", ".fx-draw", ".fx-tokchip", ".hero-lockup-float"):
        assert cls in reduce_block, f"{cls} missing a reduced-motion static state"


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
    safe_closes = ("&lt;/script&gt;", r"<\/script>", r"\u003c/script\u003e")
    assert any(token in joined for token in safe_closes)
    assert "</script>" in json.dumps(json.loads(joined))
    assert parsed.html_count == 1
    assert "page-training" in parsed.page_ids


def test_inline_scenes_match_example_json(parsed: GuideParser) -> None:
    disk_path = _ROOT / "guides" / "website" / "example" / "training-scenes.json"
    disk = json.loads(disk_path.read_text(encoding="utf-8"))
    inline = json.loads(parsed.json_script_contents[0])
    assert inline == disk


def test_training_scene_schema_is_strict_and_cumulative(parsed: GuideParser) -> None:
    data = json.loads(parsed.json_script_contents[0])
    assert set(data) == {"initial", "scenes"}
    assert set(data["initial"]) == {"game", "files"}
    assert data["initial"]["game"] == {
        "damageMode": "buggy",
        "verticalMovementEnabled": False,
        "fixture": "enemy-hit",
    }
    initial_files = data["initial"]["files"]
    assert initial_files, "the explorer needs the files that exist before /describe"
    assert {item["path"] for item in initial_files} >= {
        "src/damage.js",
        "src/game.js",
    }
    assert len({item["path"] for item in initial_files}) == len(initial_files)
    for item in initial_files:
        assert set(item) >= {"path", "language", "content"}
        assert item["path"] and item["language"] and item["content"].strip()

    current = {item["path"]: item["content"] for item in initial_files}
    seen_actions: set[str] = set()
    for scene in data["scenes"]:
        assert set(scene) == {
            "id",
            "stage",
            "title",
            "intent",
            "command",
            "tools",
            "output",
            "game",
            "files",
            "focus_file",
            "artifact",
            "gate",
            "takeaway",
        }
        assert re.search(r"\byou\b", scene["intent"], re.IGNORECASE)
        assert scene["command"].startswith(f"/{scene['id']}")
        assert scene["tools"] and all(
            set(tool) == {"name", "purpose"} and all(tool.values())
            for tool in scene["tools"]
        )
        assert scene["output"] and all(
            isinstance(line, str) and line.strip() for line in scene["output"]
        )
        assert set(scene["game"]) == {
            "damageMode",
            "verticalMovementEnabled",
            "fixture",
        }
        assert scene["game"]["damageMode"] in {"buggy", "fixed"}
        assert isinstance(scene["game"]["verticalMovementEnabled"], bool)
        assert scene["game"]["fixture"] in {"enemy-hit", "asteroid-hit", "play"}
        assert scene["files"]
        for file_change in scene["files"]:
            assert set(file_change) >= {"path", "action", "language", "content"}
            action = file_change["action"]
            path = file_change["path"]
            seen_actions.add(action)
            assert action in {"create", "modify"}
            assert file_change["content"].strip(), f"{path} needs real file content"
            if action == "create":
                assert path not in current, f"{path} cannot be created twice"
            else:
                assert path in current, f"{path} must exist before it is modified"
                assert current[path] != file_change["content"], (
                    f"{path} modify action must change its content"
                )
            current[path] = file_change["content"]
        assert scene["focus_file"] in current
        assert set(scene["artifact"]) == {"path", "summary"}
        assert set(scene["gate"]) == {"name", "status", "prompt"}
        assert scene["gate"]["status"] == "pass"
        assert scene["takeaway"].strip()
    assert seen_actions == {"create", "modify"}


def test_training_game_state_changes_at_implement_and_compare(parsed: GuideParser) -> None:
    scenes = json.loads(parsed.json_script_contents[0])["scenes"]
    states = {scene["id"]: scene["game"] for scene in scenes}
    for scene_id in ("describe", "review", "plan"):
        assert states[scene_id]["damageMode"] == "buggy"
        assert states[scene_id]["verticalMovementEnabled"] is False
    assert states["implement"] == {
        "damageMode": "fixed",
        "verticalMovementEnabled": False,
        "fixture": "enemy-hit",
    }
    for scene_id in ("compare", "test", "update", "presentify"):
        assert states[scene_id]["damageMode"] == "fixed"
        assert states[scene_id]["verticalMovementEnabled"] is True
    compare = next(scene for scene in scenes if scene["id"] == "compare")
    assert any("Follow-on /plan and /implement" in line for line in compare["output"])


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


def test_training_explorer_is_accessible_and_uses_text_only_rendering(
    guide_text: str,
) -> None:
    training = guide_text.split('id="page-training"', 1)[-1].split(
        'id="page-cheatsheets"', 1
    )[0]
    for marker in (
        'data-nht="file-tree"',
        'data-nht="file-path"',
        'data-nht="file-state"',
        'data-nht="file-body"',
    ):
        assert marker in training
    assert re.search(r'data-nht="file-tree"[^>]+role="tree"', training)
    engine = _training_engine(guide_text)
    assert "Not created yet" in engine
    assert "diff-add" in engine and "diff-remove" in engine
    assert 'setAttribute("role", "treeitem")' in engine
    assert 'setAttribute("aria-selected"' in engine
    assert re.search(r"fileBody\.textContent\s*=", engine)
    assert not re.search(r"(?:fileBody|fileTree)\.innerHTML\s*=", engine)


def test_training_runtime_exposes_deterministic_state_contract(guide_text: str) -> None:
    engine = _training_engine(guide_text)
    assert "window.NexusTraining" in engine
    for member in ("go:", "run:", "selectFile:", "snapshot:"):
        assert member in engine
    assert "Object.freeze" in engine
    assert "parsed.initial" in engine
    assert "projectStateThrough" in engine
    assert "appliedThrough" in engine
    assert "scene.booth" not in engine
    assert "scene.editor" not in engine
    assert "config.preset" not in engine


def test_training_engine_uses_shooter_damage_contract(guide_text: str) -> None:
    """v4.4.1 Phase 5 replaces the wrap-collision Asteroids with the seeded damage bug."""
    engine = _training_engine(guide_text)
    assert "function collides" in engine
    assert "function damageOutcome" in engine
    assert "setDamageMode" in engine and "setVerticalMovementEnabled" in engine
    assert 'mode === "buggy"' in engine, "the seeded bug lives in the pure damage seam"
    for retired in ("missedWrapHits", "WRAP HIT MISSED", "setSplittingEnabled", "NexusAsteroids"):
        assert retired not in engine, retired + " belongs to the retired Asteroids engine"


def test_training_has_game_terminal_and_present_mode(guide_text: str) -> None:
    training = guide_text.split('id="page-training"', 1)[-1].split('id="page-cheatsheets"', 1)[0]
    assert "data-arcade-game" in training
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
    where_assignment = re.search(
        r"els\.where\.textContent\s*=\s*([\s\S]*?);",
        engine,
    )
    assert where_assignment, "expected the Training position-label assignment"
    assert "beat" not in where_assignment.group(1).lower()
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
    block = guide_text.split("/* Full-screen slide mode (v4.4.1 Phase 6)", 1)[-1].split("@media", 1)[0]
    assert ".nht.is-present .nht-slide" in block
    assert "flex: 1 1 auto" in block, "the slide grows to consume the height"
    assert ".nht.is-present .nht-grid" in block
    assert "overflow-y: auto" in block, "the terminal keeps the one bounded secondary scroll"


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


def test_training_deep_link_clamps_unknown_scene_and_ignores_legacy_beat(
    guide_text: str,
) -> None:
    engine = _training_engine(guide_text)
    sync = engine.split("syncFromHash", 1)[-1]
    assert "if (idx < 0) idx = step;" in sync, "unknown scene id must clamp"
    assert re.search(r"syncFromHash:\s*function\s*\(sceneId\)", engine)
    assert "beatIndex" not in sync, "legacy beat values no longer control scene state"
    assert r"(?:\?beat=([^&]+))?" in engine, "old deep links remain parse-compatible"


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
