"""v3.15.4 Phase 5: iterative multi-agent visual-QA self-critique loop.

Two testable surfaces:

1. The deterministic STRUCTURAL scorer (`scripts/visual_qa_score.py`) flags a
   seeded defective fixture on each structural criterion (narrow full-width
   column, missing image caps, a dropped annotation overlay, a consented mix run
   with zero imagery, a non-offline page) and passes a clean fixture. It also
   degrades cleanly (structural mode, no browser needed) and drives the CLI exit
   codes.

2. The Dynamic-Workflow template (`assets/visual-qa-workflow.js`) and the rubric
   reference carry the required content: the three mandatory workflow rules
   (graceful degradation, scope-first token caution, skill-native) and the five
   rubric criteria. The template is an adapt-me artifact (not executed here), so
   these are structural assertions on the files.

The scorer is stdlib-only, so these tests are dependency-free (they run in both
the deps-light ci.yml tests job and the presentify-extractor workflow). The
scorer is loaded by path via importlib, matching test_media_key_setup.py.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_BUNDLE = (
    _ROOT / "catalog" / "skills" / "specialized-domains" / "document-to-interactive-html"
)
_SCORER_PATH = _BUNDLE / "scripts" / "visual_qa_score.py"
_WORKFLOW_PATH = _BUNDLE / "assets" / "visual-qa-workflow.js"
_RUBRIC_PATH = _BUNDLE / "references" / "visual-qa-rubric.md"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


scorer = _load(_SCORER_PATH, "visual_qa_score")

# A clean full-width page: canvas vars filling the viewport, the image caps, an
# annotated overlay with a region + view-original toggle, and an embedded image.
_CLEAN = (
    '<html data-aspect="full">'
    "<style>:root{--page-max: 100%; --gutter: clamp(1rem, 2vw, 2rem);}"
    " figure img{max-height: 80vh; object-fit: contain;}</style>"
    '<figure class="fig-annotated"><div class="fig-figure">'
    '<img src="data:image/png;base64,AAAA">'
    '<div class="fig-overlay"><div class="fig-region">North</div></div></div>'
    '<label class="fig-view-original">View original</label></figure>'
    "</html>"
)


def _fails(result: dict) -> set[str]:
    return {f["criterion"] for f in result["findings"] if f["status"] == "fail"}


# --- 1. structural scorer: clean passes, each seeded defect is flagged --------


def test_scorer_clean_page_passes():
    result = scorer.score_html(_CLEAN, expect_images=1)
    assert result["page_pass"] is True
    assert result["high_severity"] == 0
    assert result["mode"] == "structural"


def test_scorer_flags_narrow_full_width():
    narrow = _CLEAN.replace("--page-max: 100%", "--page-max: 600px")
    result = scorer.score_html(narrow)
    assert result["page_pass"] is False
    assert "full-width" in _fails(result)


def test_scorer_flags_missing_image_caps():
    nocaps = (
        '<html data-aspect="standard"><figure>'
        '<img src="data:image/png;base64,AAAA"></figure></html>'
    )
    result = scorer.score_html(nocaps)
    assert result["page_pass"] is False
    assert "image-sizing" in _fails(result)


def test_scorer_flags_dropped_overlay():
    dropped = (
        '<html data-aspect="standard"><style>figure img{max-height: 80vh;'
        " object-fit: contain;}</style>"
        '<figure class="fig-annotated"></figure></html>'
    )
    result = scorer.score_html(dropped)
    assert result["page_pass"] is False
    assert "annotation-fidelity" in _fails(result)


def test_scorer_flags_zero_imagery_on_consented_expectation():
    text_only = '<html data-aspect="standard"><p>text only</p></html>'
    result = scorer.score_html(text_only, expect_images=1)
    assert result["page_pass"] is False
    assert "imagery-integration" in _fails(result)


def test_scorer_flags_external_reference():
    not_offline = (
        '<html data-aspect="standard"><style>figure img{max-height: 80vh;'
        ' object-fit: contain;}</style>'
        '<link rel="stylesheet" href="https://cdn.example.com/x.css">'
        '<img src="data:image/png;base64,AAAA"></html>'
    )
    result = scorer.score_html(not_offline)
    assert result["page_pass"] is False
    assert "readability-layout" in _fails(result)


def test_scorer_na_criteria_do_not_block():
    # Standard aspect, no figures, no imagery expectation: the applicable
    # criteria are n/a and the page passes structurally.
    minimal = "<html data-aspect=\"standard\"><p>Just prose.</p></html>"
    result = scorer.score_html(minimal)
    assert result["page_pass"] is True
    statuses = {f["criterion"]: f["status"] for f in result["findings"]}
    assert statuses["full-width"] == "n/a"
    assert statuses["image-sizing"] == "n/a"
    assert statuses["imagery-integration"] == "n/a"


def test_scorer_cli_exit_codes(tmp_path):
    clean = tmp_path / "clean.html"
    clean.write_text(_CLEAN, encoding="utf-8")
    assert scorer.main([str(clean), "--expect-images", "1"]) == 0

    defect = tmp_path / "defect.html"
    defect.write_text(_CLEAN.replace("--page-max: 100%", "--page-max: 600px"), encoding="utf-8")
    assert scorer.main([str(defect)]) == 1

    assert scorer.main([str(tmp_path / "missing.html")]) == 2


# --- 2. workflow template + rubric carry the required content ----------------


def test_workflow_template_carries_mandatory_rules():
    text = _WORKFLOW_PATH.read_text(encoding="utf-8")
    # A valid Workflow script starts with the meta literal.
    assert "export const meta" in text
    # Rule 1: graceful degradation ladder (workflow + render).
    assert "isolated subagents" in text
    assert "single sequential agent" in text
    assert "visual_qa_score.py" in text  # structural fallback for the render
    # Rule 2: scope-first token caution.
    assert "5-15x" in text
    assert "CALIBRATE" in text or "Calibrate" in text or "calibrate" in text
    # Rule 3: skill-native (no outbound, local render).
    assert "No outbound call" in text or "no outbound" in text.lower()
    assert "LOCAL" in text
    # Cross-links to the orchestration + budget skills.
    assert "[[agent-orchestration-primitives]]" in text
    assert "[[ai-billing-safeguards]]" in text
    # The grade -> verify -> synthesize shape.
    assert "adversarially verify" in text.lower() or "REFUTE" in text


def test_rubric_reference_lists_all_criteria_and_pass_bar():
    text = _RUBRIC_PATH.read_text(encoding="utf-8")
    for criterion in (
        "Full-width compliance",
        "Image sizing",
        "Annotation fidelity",
        "Imagery integration",
        "Readability and layout integrity",
    ):
        assert criterion in text, f"rubric missing criterion: {criterion}"
    assert "page-level pass bar" in text.lower()
    assert "structural" in text.lower() and "agent-vision" in text.lower()
