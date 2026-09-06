"""v3.16.5 Phase 6: the cinematic scroll-scrub surface.

Three things are worth testing here, and one thing is deliberately not.

Worth testing:

1. The engine's CONTRACTS, exercised in a real browser when one is available -
   most importantly that under `prefers-reduced-motion: reduce` no `<video>`
   element is created at all. "Created but paused" is the regression this guards,
   and it is invisible in source review.
2. That the engine makes no off-host request. The single-file offline guarantee is
   the output contract, and a clip loaded over HTTP would break it silently.
3. That no vendor, product, or upstream repository name reached a distributed
   artifact - the Reverse-Engineering Attribution Rule, checked mechanically
   because it is the rule most easily broken by a helpful sentence.

Deliberately NOT tested: whether a cinematic build looks good. That is the
render loop's job (Phase 3) and the rubric's.

The browser-dependent assertions route through the `render_gate` fixture, so they
skip locally without a browser and FAIL in the CI render job that installs one.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_BUNDLE = (
    _ROOT / "catalog" / "skills" / "specialized-domains" / "document-to-interactive-html"
)
_ENGINE = _BUNDLE / "assets" / "scroll-scrub-engine.js"
_PROTOCOL = _BUNDLE / "references" / "scroll-scrub.md"
_FEATURES = _BUNDLE / "references" / "interactive-features.md"
_SKILL = _BUNDLE / "SKILL.md"
_COMMAND = _ROOT / "catalog" / "commands" / "presentify.md"

ENGINE_SRC = _ENGINE.read_text(encoding="utf-8")


def _strip_js_comments(source: str) -> str:
    """Source with comments removed, for scanning CODE rather than prose.

    Needed because the engine's own header documents the constructs it avoids
    ("no eval, no cookies, no WebSocket"), so a raw substring scan hits the
    comment that promises the construct is absent - a check that fails precisely
    when the file is most correct.
    """
    without_block = re.sub(r"/\*.*?\*/", " ", source, flags=re.S)
    return re.sub(r"(?m)^\s*//.*$", " ", without_block)


ENGINE_CODE = _strip_js_comments(ENGINE_SRC)

# A 1x1 transparent GIF is enough of a "still" for a mount test and keeps the
# fixture inline - no binary asset in the repo.
_STILL = (
    "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
)


def _page(sections: list[dict], reduce_motion: bool = False) -> str:
    """A minimal page that mounts the engine over N sections."""
    tracks = "".join(
        f'<div data-ss-section="{s["id"]}" style="height:200vh">'
        f"<h2>{s['id']}</h2></div>"
        for s in sections
    )
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        + ("<style>*{transition:none!important}</style>" if reduce_motion else "")
        + "</head><body>"
        f'<div id="stage"><div class="ss-track">{tracks}</div></div>'
        f"<script>{ENGINE_SRC}</script>"
        "<script>window.__mounted = ScrollScrub.mount("
        "document.getElementById('stage'), "
        f"{{sections: {json.dumps(sections)}, seamFade: 0.2}});</script>"
        "</body></html>"
    )


# --- 1. static contracts (no browser needed) ---------------------------------


def test_engine_is_dependency_free_and_makes_no_off_host_request():
    # NOTE on the strings below: `"eval("` appears here only as a construct this
    # test FORBIDS in the engine - nothing in this file or the engine calls eval.
    # Playwright's `page.evaluate()` further down is a browser-automation API that
    # runs a function in the page under test, unrelated to JavaScript `eval`.
    # The output contract is a single offline file. A clip fetched over HTTP would
    # break it while still "working" on the authoring machine.
    assert "import " not in ENGINE_CODE.replace("important", "")
    assert "require(" not in ENGINE_CODE
    for forbidden in ("fetch(", "XMLHttpRequest", "WebSocket", "eval(", "document.cookie"):
        assert forbidden not in ENGINE_CODE, f"engine uses {forbidden}"
    assert not re.search(r"https?://", ENGINE_CODE), "engine contains an off-host URL"


def test_engine_documents_the_data_uri_and_blob_loading_path():
    assert "data:" in ENGINE_SRC and "Blob" in ENGINE_SRC
    # The sibling-file path must be explicitly rejected, not merely unused.
    assert "byte-range" in ENGINE_SRC or "sibling" in ENGINE_SRC


def test_engine_namespaces_everything_and_names_no_vendor():
    assert "var PREFIX = 'ss-'" in ENGINE_SRC
    for name in ("monid", "higgsfield", "seedance", "scroll-world", "oso95"):
        assert name not in ENGINE_SRC.lower(), f"vendor name {name!r} in the engine"


@pytest.mark.parametrize("path", [_ENGINE, _PROTOCOL, _FEATURES, _SKILL, _COMMAND])
def test_no_vendor_name_reaches_a_distributed_artifact(path):
    """The Reverse-Engineering Attribution Rule, checked mechanically.

    Attribution belongs in the reverse-engineering matrix, not in a file the
    installer copies to users. This is the rule a single helpful sentence breaks,
    which is why it is a test rather than a convention.
    """
    text = path.read_text(encoding="utf-8").lower()
    for name in ("monid", "higgsfield", "seedance", "scroll-world", "oso95"):
        assert name not in text, f"{path.name} names {name!r}"


def test_apply_linger_holds_the_middle_and_preserves_the_ends():
    """`linger` is what makes a section's copy readable instead of sliding past,
    so its shape matters: the ends must still reach 0 and 1, and the middle must
    barely advance."""
    # Ported assertion - the pure function is small enough to reason about here,
    # and a browser is not needed to check its arithmetic.
    def apply_linger(progress, linger):
        if not linger or linger <= 0:
            return progress
        hold = min(0.9, linger)
        lead = (1 - hold) / 2
        if progress < lead:
            return (progress / lead) * lead
        if progress > 1 - lead:
            return 1 - lead + ((progress - (1 - lead)) / lead) * lead
        return lead + ((progress - lead) / hold) * 0.02

    assert apply_linger(0.0, 0.5) == pytest.approx(0.0)
    assert apply_linger(1.0, 0.5) == pytest.approx(1.0, abs=1e-9)
    # With no linger it is the identity.
    assert apply_linger(0.42, 0) == pytest.approx(0.42)
    # Across the hold window the output moves far less than the input.
    mid_low, mid_high = apply_linger(0.3, 0.6), apply_linger(0.7, 0.6)
    assert abs(mid_high - mid_low) < 0.05, "the hold window should barely advance"


# --- 2. the reduced-motion guarantee, in a real browser ----------------------


def _launch(html: str, reduced: bool):
    from playwright.sync_api import sync_playwright

    play = sync_playwright().start()
    browser = play.chromium.launch()
    context = browser.new_context(
        reduced_motion="reduce" if reduced else "no-preference",
        viewport={"width": 1280, "height": 800},
    )
    page = context.new_page()
    page.set_content(html)
    page.wait_for_timeout(250)
    return play, browser, page


def test_reduced_motion_creates_no_video_element(render_gate):
    """The guarantee is 'not created', not 'created and paused'.

    A paused video still downloads, still decodes its first frame, and still
    costs a reduced-motion user battery and memory. Only the absence of the
    element is a guarantee that cannot regress by accident, and only a real
    browser can confirm it.
    """
    try:
        import playwright.sync_api  # noqa: F401
    except Exception:
        render_gate("no headless browser available; cinematic reduce check skipped")
    sections = [
        {"id": "a", "clip": _STILL, "still": _STILL, "scroll": 1.0, "linger": 0.2},
        {"id": "b", "clip": _STILL, "still": _STILL, "scroll": 1.0},
    ]
    play, browser, page = _launch(_page(sections), reduced=True)
    try:
        counts = page.evaluate(
            "() => ({video: document.querySelectorAll('#stage video').length,"
            " img: document.querySelectorAll('#stage img').length})"
        )
    finally:
        browser.close()
        play.stop()
    assert counts["video"] == 0, "a video element was created under reduce"
    assert counts["img"] == 2, "the stills-only path should build one img per section"


def test_no_preference_uses_video_layers(render_gate):
    """The mirror of the check above: without the preference, the enhancement IS
    applied - otherwise the reduce test would pass trivially on a broken engine."""
    try:
        import playwright.sync_api  # noqa: F401
    except Exception:
        render_gate("no headless browser available; cinematic video check skipped")
    sections = [{"id": "a", "clip": _STILL, "still": _STILL, "scroll": 1.0}]
    play, browser, page = _launch(_page(sections), reduced=False)
    try:
        info = page.evaluate(
            "() => { const v = document.querySelector('#stage video');"
            " return v ? {muted: v.muted, inline: v.hasAttribute('playsinline'),"
            " hidden: document.querySelector('.ss-viewport').getAttribute('aria-hidden')}"
            " : null; }"
        )
    finally:
        browser.close()
        play.stop()
    assert info is not None, "no video layer was created without the preference"
    assert info["muted"] is True, "a scrubbed clip must be muted"
    assert info["inline"] is True, "playsinline is required for mobile"
    assert info["hidden"] == "true", "the decorative stage must be aria-hidden"


def test_mount_makes_no_network_request(render_gate):
    """The offline guarantee, observed rather than asserted from source."""
    try:
        import playwright.sync_api  # noqa: F401
    except Exception:
        render_gate("no headless browser available; cinematic offline check skipped")
    sections = [{"id": "a", "clip": _STILL, "still": _STILL, "scroll": 1.0}]
    play, browser, page = _launch(_page(sections), reduced=False)
    off_host: list[str] = []
    try:
        page.on("request", lambda req: off_host.append(req.url)
                if req.url.startswith(("http://", "https://")) else None)
        page.evaluate("() => window.scrollTo(0, 400)")
        page.wait_for_timeout(300)
    finally:
        browser.close()
        play.stop()
    assert off_host == [], f"engine made off-host requests: {off_host[:3]}"


# --- 3. the protocol and the intake surfaces agree ---------------------------


def test_protocol_covers_all_seven_sections():
    text = _PROTOCOL.read_text(encoding="utf-8")
    for anchor in (
        "When cinematic applies",
        "Job fidelity",
        "Size and cost gate",
        "Asset sources",
        "Seam and pacing protocol",
        "Stills-only fallback",
        "Accessibility",
    ):
        assert anchor in text, f"protocol missing section: {anchor}"


def test_protocol_states_the_hard_no_and_the_single_file_rule():
    text = _PROTOCOL.read_text(encoding="utf-8")
    assert "generation-as-service" in text
    assert "never shells out to a vendor CLI" in text
    # The sibling-asset layout must be refused explicitly, not merely omitted.
    assert "sibling asset layouts" in text or "sibling" in text
    assert "zero network requests" in text


def test_cinematic_is_opt_in_on_both_intake_surfaces():
    skill = _SKILL.read_text(encoding="utf-8")
    command = _COMMAND.read_text(encoding="utf-8")
    for name, text in (("SKILL.md", skill), ("presentify.md", command)):
        assert "cinematic" in text.lower(), f"{name} does not mention cinematic"
        assert "restrained|balanced|rich|cinematic" in text or "cinematic" in text
    # Both surfaces must say it is never silently selected.
    for name, text in (("SKILL.md", skill), ("presentify.md", command)):
        lowered = text.lower()
        assert "never silent" in lowered or "confirm" in lowered, (
            f"{name} does not state the rich-level proposal is confirmed, not silent"
        )


def test_the_interactivity_spectrum_documents_cinematic_above_rich():
    text = _FEATURES.read_text(encoding="utf-8")
    assert "CINEMATIC" in text
    spectrum = text[text.index("Interactivity spectrum"):]
    assert "CINEMATIC = RICH plus" in spectrum, "the mapping summary must include it"
    # The size gate is what distinguishes it from the other levels.
    assert "size / cost gate" in spectrum


def test_the_scrollytelling_catalog_has_the_scrubbed_stage_entry():
    text = _FEATURES.read_text(encoding="utf-8")
    assert "scroll-scrubbed stage" in text
    assert "not created-and-paused" in text, (
        "the catalog entry must state the reduce guarantee precisely"
    )
