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
        if copy:
            self._copy_el = True
            self._copy_value = copy
            self._copy_parts = []
            self._copy_home = self.current_page == "page-home"
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
        if self._copy_el and tag in {"div", "pre", "code", "span", "button"}:
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


def test_compact_spacing_and_measure_tokens(guide_text: str) -> None:
    sec_pad = re.search(r"--sec-pad:\s*(\d+)px", guide_text)
    assert sec_pad, "expected --sec-pad token"
    assert int(sec_pad.group(1)) <= 32, "section rhythm must stay compact"
    assert "--measure:" in guide_text, "expected shared measure token"
    assert "--violet" not in guide_text, "accent rainbow was trimmed by the design brief"


def test_hero_title_and_lead_share_measure(guide_text: str) -> None:
    h1_rule = re.search(r"(?<![\w-])h1\s*\{([^}]+)\}", guide_text)
    assert h1_rule and "var(--measure)" in h1_rule.group(1)
    lead_rule = re.search(r"\.lead\s*\{([^}]+)\}", guide_text)
    assert lead_rule and "var(--measure)" in lead_rule.group(1)


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
# Home: install section (Phase 2 completes the page; install block live now)
# ---------------------------------------------------------------------------


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


def test_onboarding_has_no_hardcoded_catalog_counts(parsed: GuideParser) -> None:
    home = " ".join(parsed.home_text_parts)
    assert not ONBOARDING_STALE.search(home), home[:400]


@pytest.mark.xfail(strict=True, reason="Phase 2 adds copyable verify-command cells")
def test_home_verify_commands_are_copy_cells(parsed: GuideParser) -> None:
    payloads = {p for p, _v in parsed.home_data_copy}
    assert "/skills list" in payloads
    assert "/commands" in payloads
    for payload, visible in parsed.home_data_copy:
        if payload in {"/skills list", "/commands"}:
            assert visible.strip() == payload


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


@pytest.mark.xfail(strict=True, reason="Phase 4 rebuilds the Training renderer with a textContent contract")
def test_hostile_fixture_strings_are_rendered_via_textcontent(
    parsed: GuideParser, guide_text: str
) -> None:
    data = json.loads(parsed.json_script_contents[0])
    blob = json.dumps(data)
    assert "<img onerror>" in blob
    assert "</script>" in blob
    assert re.search(r"\.textContent\s*=", guide_text.split("nh-training-scenes", 1)[0]), (
        "scene-driven output must be assigned via textContent"
    )
    assert "data-training-root" in guide_text


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
