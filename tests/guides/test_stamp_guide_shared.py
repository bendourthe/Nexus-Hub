"""v4.13.10: scripts/stamp_guide_shared.py inlines shared fragments from one source.

Each test builds a throwaway site under tmp_path, so the real guide is never written.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "stamp_guide_shared.py"


def _site(tmp_path: Path, fragment: str = "<p>{{who}}</p>\n", pages: dict[str, str] | None = None) -> Path:
    web = tmp_path / "guides" / "website"
    (web / "shared").mkdir(parents=True)
    (web / "shared" / "foot.html").write_text(fragment, encoding="utf-8")
    (web / "shared" / "fragments.json").write_text(json.dumps({
        "fragments": {"foot": {"syntax": "html", "file": "foot.html"}},
        "pages": {"a.html": {"vars": {"who": "A"}}, "b.html": {"vars": {"who": "B"}}},
    }), encoding="utf-8")
    default = "<body>\n<!-- shared:foot -->\nold\n<!-- /shared:foot -->\n</body>\n"
    for name in ("a.html", "b.html"):
        (web / name).write_text((pages or {}).get(name, default), encoding="utf-8", newline="\n")
    return web


def _run(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), "--root", str(tmp_path), *args], capture_output=True, text=True)


def test_stamp_fills_each_page_with_its_own_values(tmp_path: Path) -> None:
    web = _site(tmp_path)
    assert _run(tmp_path).returncode == 0
    assert (web / "a.html").read_text(encoding="utf-8") == "<body>\n<!-- shared:foot -->\n<p>A</p>\n<!-- /shared:foot -->\n</body>\n"
    assert "<p>B</p>" in (web / "b.html").read_text(encoding="utf-8")
    assert _run(tmp_path, "--check").returncode == 0


def test_check_reports_drift_and_writes_nothing(tmp_path: Path) -> None:
    web = _site(tmp_path)
    before = (web / "a.html").read_bytes()
    result = _run(tmp_path, "--check")
    assert result.returncode == 1
    assert "a.html: foot" in result.stderr
    assert (web / "a.html").read_bytes() == before


def test_crlf_pages_keep_their_line_endings(tmp_path: Path) -> None:
    web = _site(tmp_path)
    (web / "a.html").write_bytes(b"<body>\r\n<!-- shared:foot -->\r\nold\r\n<!-- /shared:foot -->\r\n</body>\r\n")
    assert _run(tmp_path).returncode == 0
    assert (web / "a.html").read_bytes() == b"<body>\r\n<!-- shared:foot -->\r\n<p>A</p>\r\n<!-- /shared:foot -->\r\n</body>\r\n"


@pytest.mark.parametrize(
    ("page", "message"),
    [
        ("<body>\n</body>\n", "marker pair for foot is missing"),
        ("<!-- shared:foot -->\nx\n<!-- /shared:foot -->\n<!-- shared:foot -->\ny\n<!-- /shared:foot -->\n", "more than once"),
        ("<!-- /shared:foot -->\n<!-- shared:foot -->\n", "comes before"),
    ],
)
def test_bad_markers_fail_without_writing(tmp_path: Path, page: str, message: str) -> None:
    web = _site(tmp_path, pages={"b.html": page})
    before = {name: (web / name).read_bytes() for name in ("a.html", "b.html")}
    result = _run(tmp_path)
    assert result.returncode == 2
    assert message in result.stderr
    assert {name: (web / name).read_bytes() for name in before} == before, "a failed run writes no page"


def test_missing_fragment_source_names_the_file(tmp_path: Path) -> None:
    web = _site(tmp_path)
    (web / "shared" / "foot.html").unlink()
    result = _run(tmp_path)
    assert result.returncode == 2
    assert "foot.html is missing" in result.stderr


def test_missing_placeholder_value_is_an_error(tmp_path: Path) -> None:
    _site(tmp_path, fragment="<p>{{nobody}}</p>\n")
    result = _run(tmp_path)
    assert result.returncode == 2
    assert "needs a value for {{nobody}}" in result.stderr


def test_the_real_guide_pages_are_current() -> None:
    result = subprocess.run([sys.executable, str(SCRIPT), "--check"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
