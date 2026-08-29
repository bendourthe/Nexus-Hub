"""Structural tests for guides/website/nexus-hub-guide.html.

Baseline assertions pass against the current single-file guide.
Redesign assertions use strict xfail until the named phase removes the marker.
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
EXAMPLE_ZIP_NAME = "trivia-quiz.zip"

INSTALL_SH = (
    "curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash"
)
INSTALL_PS = (
    "irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1 | iex"
)

# Onboarding catalog-count / installer-version patterns (Phase 3 removes these).
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
# Baseline (must pass on the current file)
# ---------------------------------------------------------------------------


def test_one_html_document(parsed: GuideParser, guide_text: str) -> None:
    assert guide_text.lstrip().lower().startswith("<!doctype html>")
    assert parsed.html_count == 1
    assert parsed.body_count == 1
    assert GUIDE.suffix == ".html"


def test_each_page_has_a_primary_heading(parsed: GuideParser) -> None:
    """Each page section has an H1, except Training which currently titles with H2."""
    assert parsed.page_ids, "no page sections found"
    for page_id in parsed.page_ids:
        headings = parsed.headings_by_page.get(page_id, [])
        assert headings, f"{page_id} has no h1-h3 heading"
        tag, _title = headings[0]
        if page_id == "page-training":
            assert tag in {"h1", "h2"}
        else:
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


def test_github_is_user_initiated_not_a_script(parsed: GuideParser) -> None:
    assert not parsed.script_src
    hrefs = [ad.get("href", "") for tag, ad in parsed.raw_attrs if tag == "a"]
    github = [h for h in hrefs if "github.com" in h]
    assert github, "expected a GitHub navigation link"


# ---------------------------------------------------------------------------
# Redesign: Phase 2
# ---------------------------------------------------------------------------


def test_no_installation_in_primary_nav(parsed: GuideParser) -> None:
    labels = [text.lower() for _go, text in parsed.nav_link_text]
    assert not any("installation" in t for t in labels)
    assert "setup" not in parsed.nav_data_go


def test_theme_toggle_exists(parsed: GuideParser) -> None:
    assert parsed.has_theme_toggle


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


# ---------------------------------------------------------------------------
# Redesign: Phase 3
# ---------------------------------------------------------------------------


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


def test_no_stale_setup_route_in_markup(parsed: GuideParser) -> None:
    assert "page-setup" not in parsed.page_ids
    static = [g for g in parsed.data_go if g == "setup"]
    assert not static


def test_home_has_six_node_preview_including_communicate(guide_text: str) -> None:
    home_markup = guide_text.split('id="page-home"', 1)[-1].split('id="page-foundations"', 1)[0]
    assert "Map and evaluate" in home_markup
    assert 'data-go="communicate"' in home_markup
    assert "presentify" in home_markup.lower()
    assert 'data-go="setup"' not in home_markup
    for node in ("explore", "plan", "build", "harden", "ship", "communicate"):
        assert f'data-go="{node}"' in home_markup


def test_onboarding_has_no_hardcoded_catalog_counts(parsed: GuideParser) -> None:
    home = " ".join(parsed.home_text_parts)
    assert not ONBOARDING_STALE.search(home), home[:400]


# ---------------------------------------------------------------------------
# Redesign: Phase 4
# ---------------------------------------------------------------------------


def test_foundations_three_roles(guide_text: str) -> None:
    fl = guide_text.lower()
    assert "page-foundations" in fl
    assert "harness" in fl
    assert re.search(r"model\s*=\s*the brain|the brain", fl)
    assert "agent" in fl or "platform" in fl


def test_foundations_has_user_initiated_comparison(guide_text: str) -> None:
    assert re.search(r'type=["\']range["\']|role=["\']slider["\']|data-compare', guide_text)
    assert "scroll-scrub-engine" not in guide_text


def test_foundations_handoff_is_training_page_hash(guide_text: str) -> None:
    foundations = guide_text.split('id="page-foundations"', 1)[-1].split('id="page-training"', 1)[0]
    assert "Now watch the experience layer work" in foundations
    assert re.search(r'data-go=["\']training["\']|#training(?!/)', foundations)
    assert "#training/" not in foundations


def test_foundations_comparison_states_are_static_in_markup(guide_text: str) -> None:
    foundations = guide_text.split('id="page-foundations"', 1)[-1].split('id="page-training"', 1)[0]
    assert "Model alone" in foundations
    assert "Model with Nexus-Hub" in foundations
    assert 'data-nhg-keys="self"' in foundations
    assert 'id="nhgRawPane"' in foundations
    assert 'id="nhgHubPane"' in foundations


# ---------------------------------------------------------------------------
# Redesign: Phase 5
# ---------------------------------------------------------------------------


def test_training_scenes_are_data_driven_json(parsed: GuideParser) -> None:
    assert parsed.json_script_contents, "expected application/json scene block"


def test_every_scene_exposes_gate_and_next_scene(parsed: GuideParser) -> None:
    import json

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


def test_script_close_in_fixture_does_not_break_document(parsed: GuideParser) -> None:
    assert parsed.json_script_contents, "fixture JSON block required before encoding can be checked"
    joined = "\n".join(parsed.json_script_contents)
    assert "&lt;/script&gt;" in joined or r"<\/script>" in joined
    assert parsed.html_count == 1
    assert "page-training" in parsed.page_ids


def test_inline_scenes_match_example_json(parsed: GuideParser) -> None:
    import json

    disk_path = _ROOT / "guides" / "website" / "example" / "training-scenes.json"
    disk = json.loads(disk_path.read_text(encoding="utf-8"))
    inline = json.loads(parsed.json_script_contents[0])
    assert inline == disk


def test_training_workbench_is_not_a_slide_deck(guide_text: str) -> None:
    assert 'id="nhWorkbench"' in guide_text
    assert "function applyState" in guide_text
    assert "textContent" in guide_text
    assert 'class="ts-slide"' not in guide_text
    assert "scroll-scrub-engine" not in guide_text


def test_hostile_fixture_strings_are_present_for_textcontent(parsed: GuideParser) -> None:
    import json

    data = json.loads(parsed.json_script_contents[0])
    blob = json.dumps(data)
    assert "<img onerror>" in blob
    assert "</script>" in blob
    # Rendering contract: workbench JS assigns fixture strings via textContent.
    # (A live DOM is last-phase / DF-1; this is the static proof.)
    assert "els.editor.textContent" in Path(GUIDE).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Redesign: Phase 6
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


def test_every_catalog_command_is_training_reference_or_declined(
    parsed: GuideParser, guide_text: str
) -> None:
    names = sorted(p.stem for p in COMMANDS_DIR.glob("*.md"))
    assert names, "catalog/commands is empty"
    data = json.loads(parsed.json_script_contents[0])
    scenes = data["scenes"] if isinstance(data, dict) and "scenes" in data else data
    scene_ids = {scene["id"] for scene in scenes}
    reference = guide_text.split('id="page-reference"', 1)[-1]
    readme = WEBSITE_README.read_text(encoding="utf-8")
    content_map = CONTENT_MAP.read_text(encoding="utf-8")
    missing = []
    for name in names:
        token = f"/{name}"
        in_scene = name in scene_ids
        in_reference = token in reference
        in_docs = token in readme or token in content_map
        if not (in_scene or in_reference or in_docs):
            missing.append(name)
    assert not missing, f"unplaced catalog commands: {missing}"


def test_website_readme_matches_redesign() -> None:
    text = WEBSITE_README.read_text(encoding="utf-8")
    lower = text.lower()
    assert "31 slide" not in lower
    assert "20 slide" not in lower
    assert "guided tour" not in lower
    assert "fullscreen button" not in lower
    assert "training-scenes.json" in text
    assert "nexus-hub/index.html" in text
    assert "NEXUS_HUB_PORTFOLIO_ROOT" in text
    assert "sync-nexus-hub-guide.mjs" in text
    assert "Installation is not a primary page" in text
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
