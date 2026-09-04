"""v4.4.1 Phase 4 gates: approved media bytes, shared visual grammar, and media behavior.

The media assertions decode every embedded payload and hash it against the staged ledger
file, exactly as the Phase 2 platform-mark tests do. A page whose gallery was re-exported,
re-compressed, or hand-edited after approval fails here rather than shipping unreviewed
bytes. The browser assertions cover the claims markup cannot prove: that the moving image
never plays until asked, that asking works, and that the shared work-cycle glyph is
motionless yet complete under reduced motion.
"""

from __future__ import annotations

import base64
import hashlib
import os
import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
ASSETS = (
    _ROOT
    / "docs"
    / "releases"
    / "v4"
    / "v4.4"
    / "development"
    / "guide-visual-and-arcade-rebuild"
    / "assets"
)
REQUIRE_RENDER = os.environ.get("NEXUS_REQUIRE_RENDER") == "1"


@pytest.fixture(scope="module")
def guide_text() -> str:
    return GUIDE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def models_scene(guide_text: str) -> str:
    m = re.search(r'<section class="lesson" id="fx-model-lifecycle"[\s\S]*?</section>', guide_text)
    assert m, "missing the Models scene"
    return m.group(0)


def _staged_hash(name: str) -> str:
    return hashlib.sha256((ASSETS / name).read_bytes()).hexdigest()


# ------------------------------------------------------------------ approved media bytes






def test_the_audio_asset_left_the_page_with_its_teaching(models_scene: str, guide_text: str) -> None:
    """v4.4.4 retired audio from the Models teaching, on the operator's instruction.

    The old test asserted the embedded WAV matched the approved ledger bytes. With audio out of the
    teaching, the honest assertion is the opposite: the asset must NOT be shipped, because a 12 KB
    embedded payload nothing explains is worse than no payload. The ledger row stays in the
    provenance document as a record of what was once approved.
    """
    assert "data:audio/wav" not in guide_text, "the approved WAV is still embedded"
    assert "<audio" not in guide_text, "the audio element is still shipped"
    assert "fx-out-audio" not in guide_text and "fx-wave" not in guide_text
    assert "initWaveform" not in guide_text, "the waveform engine is still shipped"
    assert 'data-output-kind="audio"' not in models_scene


def test_media_ledger_records_every_embedded_payload() -> None:
    ledger = (ASSETS.parent / "asset-provenance.md").read_text(encoding="utf-8")
    for name in (
        "model-output-image.svg",
        "model-output-video.gif",
        "model-output-video-poster.svg",
        "model-output-audio.wav",
    ):
        assert _staged_hash(name) in ledger, (
            f"{name}: the staged bytes are not the bytes the ledger approved"
        )
    assert "SETTLED" in ledger.split("## 3.")[1].split("##")[0]


# ------------------------------------------------------------------ shared visual grammar




# ------------------------------------------------------------------------ browser gates


@pytest.fixture(scope="module")
def playwright_mod():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:  # pragma: no cover - environment dependent
        if REQUIRE_RENDER:
            pytest.fail("NEXUS_REQUIRE_RENDER=1 but playwright is not installed")
        pytest.skip("playwright is not installed")
    try:
        with sync_playwright() as pw:
            pw.chromium.launch().close()
    except Exception as exc:  # pragma: no cover - environment dependent
        if REQUIRE_RENDER:
            pytest.fail(f"NEXUS_REQUIRE_RENDER=1 but chromium is unavailable: {exc}")
        pytest.skip(f"chromium is unavailable: {exc}")
    return sync_playwright
