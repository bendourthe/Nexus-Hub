"""Read an existing web-page handbook as a first-class extractor source."""

import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "catalog/skills/specialized-domains/document-to-interactive-html"
sys.path.insert(0, str(BUNDLE / "scripts"))
extractor = importlib.import_module("extract_content")
FIXTURE = ROOT / "tests/fixtures/interactive-handbooks-qualification/repo/inputs"


def read(tmp_path, markup, name="page.html"):
    target = tmp_path / name
    target.write_text(markup, encoding="utf-8")
    cov = {"skip_reasons": []}
    title, sections = extractor._extract_html(str(target), 1_000_000, cov, name)
    return title, sections, cov


def blocks(sections):
    return [b for s in sections for b in s["blocks"]]


class TestRecognition:
    @pytest.mark.parametrize("suffix", [".html", ".htm", ".xhtml"])
    def test_web_page_suffixes_map_to_the_html_reader(self, suffix):
        assert extractor.EXTENSION_FORMATS[suffix] == "html"

    def test_the_frozen_legacy_handbook_is_now_read(self, tmp_path):
        """This page was the ninth source the repository case could not ingest."""
        out = tmp_path / "model.json"
        result = subprocess.run(
            [sys.executable, str(BUNDLE / "scripts/extract_content.py"),
             str(FIXTURE), "-o", str(out)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr[-600:]
        model = json.loads(out.read_text(encoding="utf-8"))
        paths = [s["path"] for s in model["sources"]]
        assert "docs/handbooks/html/operations.html" in paths
        assert len(paths) == 9, paths


class TestStructure:
    def test_headings_become_sections_and_the_first_is_the_title(self, tmp_path):
        title, sections, _ = read(
            tmp_path,
            "<h1>Queue operations</h1><p>Retry limit: 2.</p>"
            "<h2>Archive</h2><p>Reliability unavailable.</p>",
        )
        assert title == "Queue operations"
        assert [s["heading"] for s in sections] == ["Queue operations", "Archive"]
        assert sections[0]["blocks"][0]["text"] == "Retry limit: 2."

    def test_document_title_element_wins_over_the_first_heading(self, tmp_path):
        title, _, _ = read(
            tmp_path, "<title>Operations handbook</title><h1>Queue</h1><p>Body.</p>"
        )
        assert title == "Operations handbook"

    def test_lists_become_bullets(self, tmp_path):
        _, sections, _ = read(
            tmp_path, "<h1>H</h1><ul><li>first</li><li>second</li></ul>"
        )
        bullet = next(b for b in blocks(sections) if b["type"] == "bullets")
        assert bullet["items"] == ["first", "second"]

    def test_tables_keep_their_header_and_rows(self, tmp_path):
        _, sections, _ = read(
            tmp_path,
            "<h1>H</h1><table><tr><th>Setting</th><th>Value</th></tr>"
            "<tr><td>Retry limit</td><td>2</td></tr></table>",
        )
        table = next(b for b in blocks(sections) if b["type"] == "table")
        assert table["header"] == ["Setting", "Value"]
        assert table["rows"] == [["Retry limit", "2"]]

    def test_preformatted_text_becomes_a_code_block(self, tmp_path):
        _, sections, _ = read(tmp_path, "<h1>H</h1><pre>python build.py</pre>")
        code = next(b for b in blocks(sections) if b["type"] == "code")
        assert "python build.py" in code["text"]

    def test_image_alt_text_is_retained_as_content(self, tmp_path):
        _, sections, _ = read(
            tmp_path, '<h1>H</h1><img src="d.png" alt="Queue throughput chart">'
        )
        assert any(
            "Queue throughput chart" in b.get("text", "") for b in blocks(sections)
        )

    def test_whitespace_in_markup_does_not_leak_into_text(self, tmp_path):
        _, sections, _ = read(
            tmp_path, "<h1>H</h1><p>Retry\n   limit:\t2.</p>"
        )
        assert blocks(sections)[0]["text"] == "Retry limit: 2."


class TestNonContentIsExcluded:
    """A real page carries chrome and code that are not the handbook."""

    @pytest.mark.parametrize("tag", ["nav", "header", "footer", "aside"])
    def test_page_chrome_contributes_no_text(self, tmp_path, tag):
        _, sections, _ = read(
            tmp_path,
            f"<{tag}><p>Skip to content</p></{tag}><h1>Real</h1><p>Body text.</p>",
        )
        assert not any("Skip to content" in str(b) for b in blocks(sections))
        assert any("Body text." in str(b) for b in blocks(sections))

    @pytest.mark.parametrize("tag", ["script", "style", "noscript"])
    def test_code_and_styling_contribute_no_text(self, tmp_path, tag):
        _, sections, _ = read(
            tmp_path,
            f"<h1>Real</h1><{tag}>var secret = 1;</{tag}><p>Body text.</p>",
        )
        assert not any("secret" in str(b) for b in blocks(sections))
        assert any("Body text." in str(b) for b in blocks(sections))


class TestDegradation:
    def test_unclosed_tags_still_yield_content(self, tmp_path):
        _, sections, cov = read(
            tmp_path, "<h1>Heading<p>Body without closing tags"
        )
        assert any("Body without closing tags" in str(b) for b in blocks(sections))

    def test_a_page_with_no_readable_content_says_so(self, tmp_path):
        _, sections, cov = read(tmp_path, "<html><head></head><body></body></html>")
        assert sections == []
        assert any("no readable content" in r for r in cov["skip_reasons"])

    def test_chrome_only_page_is_not_reported_as_content(self, tmp_path):
        _, sections, cov = read(tmp_path, "<nav><p>Home</p><p>About</p></nav>")
        assert sections == []
        assert any("no readable content" in r for r in cov["skip_reasons"])
