#!/usr/bin/env python3
"""verify_universal_ingestion.py - v3.13.0 Phase 5 CI verifier.

Standalone (no pytest): builds a temp repository tree in memory, runs the
document-to-interactive-html extractor over it, and asserts the universal-
ingestion + prominence behavior. Exits non-zero on the first failed check.

Builds its own tree with tempfile so the walk's ignore behavior (node_modules,
.gitignore, binary sniff, caps) is reproducible in CI without depending on
committed fixtures (a committed `node_modules/` would itself be gitignored).
"""

from __future__ import annotations

import base64
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

def _repo_root(start: Path) -> Path:
    """Walk up to the repository root instead of hand-counting parent depth.

    A fixed ``parents[N]`` silently breaks whenever the file moves a level, and
    the v4.0.0 docs migration moved this tree one level deeper. Anchoring on a
    marker that only the root carries makes the location irrelevant.
    """
    for candidate in [start, *start.parents]:
        if (candidate / "AGENTS.md").is_file() and (candidate / "catalog").is_dir():
            return candidate
    raise RuntimeError(f"repository root not found above {start}")

REPO_ROOT = _repo_root(Path(__file__).resolve().parent)
EXTRACTOR = (
    REPO_ROOT
    / "catalog/skills/specialized-domains/document-to-interactive-html"
    / "scripts/extract_content.py"
)
PNG_1x1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYPhfDwAChwGA"
    "60e6kgAAAABJRU5ErkJggg=="
)

_checks = 0
_fails = 0


def check(cond: bool, label: str) -> None:
    global _checks, _fails
    _checks += 1
    if not cond:
        _fails += 1
        print(f"FAIL: {label}", file=sys.stderr)
    else:
        print(f"  ok: {label}")


def load_extractor():
    spec = importlib.util.spec_from_file_location("ec_universal", EXTRACTOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_tree(root: Path) -> None:
    (root / "src" / "lib").mkdir(parents=True)
    (root / "data").mkdir()
    (root / "assets").mkdir()
    (root / "node_modules" / "pkg").mkdir(parents=True)
    (root / "README.md").write_text(
        "# Demo\n\nIntro paragraph.\n\n## Features\n\n- one\n- two\n\n"
        "## Data\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n```python\nprint(1)\n```\n",
        encoding="utf-8",
    )
    (root / "src" / "app.py").write_text(
        '"""App."""\n\n\ndef run():\n    return "ok"\n', encoding="utf-8"
    )
    (root / "src" / "util.js").write_text("export const x = 1;\n", encoding="utf-8")
    (root / "src" / "lib" / "helper.go").write_text(
        "package lib\n\nfunc H() string { return \"hi\" }\n", encoding="utf-8"
    )
    (root / "data" / "metrics.csv").write_text(
        "Quarter,Revenue,Cost\nQ1,120,80\nQ2,145,90\n", encoding="utf-8"
    )
    (root / "data" / "notes.txt").write_text(
        "First para.\n\nSecond para.\n", encoding="utf-8"
    )
    # A .csv that is actually binary (NUL bytes) -> binary sniff must skip it.
    (root / "data" / "blob.csv").write_bytes(b"a,b\n\x00\x00\x00binary\x00\n")
    (root / "assets" / "logo.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"></svg>\n', encoding="utf-8"
    )
    (root / "assets" / "pixel.png").write_bytes(PNG_1x1)
    (root / ".gitignore").write_text("secret.txt\n", encoding="utf-8")
    (root / "secret.txt").write_text("do not ingest\n", encoding="utf-8")
    (root / "node_modules" / "pkg" / "index.js").write_text(
        "module.exports = 1;\n", encoding="utf-8"
    )


def main() -> int:
    ec = load_extractor()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "demo-repo"
        root.mkdir()
        build_tree(root)

        model = ec.build_model([str(root)])
        srcs = {s["path"]: s["format"] for s in model["sources"]}

        # Walk exclusions.
        check("secret.txt" not in srcs, "gitignored file excluded (secret.txt)")
        check(
            not any("node_modules" in p for p in srcs),
            "ignored dir excluded (node_modules)",
        )
        check(
            "data/blob.csv" not in srcs,
            "binary file with text extension excluded (blob.csv)",
        )

        # New-format extractors.
        check(srcs.get("README.md") == "markdown", "README.md -> markdown")
        check(srcs.get("src/app.py") == "code", "app.py -> code")
        check(srcs.get("src/lib/helper.go") == "code", "helper.go -> code")
        check(srcs.get("data/metrics.csv") == "csv", "metrics.csv -> csv")
        check(srcs.get("data/notes.txt") == "text", "notes.txt -> text")
        check(srcs.get("assets/logo.svg") == "image", "logo.svg -> image")
        check(srcs.get("assets/pixel.png") == "image", "pixel.png -> image")

        # Code language + path.
        code_blocks = [
            b
            for s in model["sections"]
            for b in s["blocks"]
            if b["type"] == "code" and b.get("path")
        ]
        langs = {b["path"]: b["language"] for b in code_blocks}
        check(langs.get("src/app.py") == "python", "app.py language python")
        check(langs.get("src/lib/helper.go") == "go", "helper.go language go")
        check(langs.get("src/util.js") == "javascript", "util.js language javascript")

        # CSV -> chart with real series.
        charts = [
            b
            for s in model["sections"]
            for b in s["blocks"]
            if b["type"] == "chart"
        ]
        check(
            any(
                c.get("provenance") == "source-data"
                and [ser["name"] for ser in c["series"]] == ["Revenue", "Cost"]
                for c in charts
            ),
            "metrics.csv -> chart with Revenue+Cost series",
        )

        # Repository assembly.
        check(model["sections"][0]["kind"] == "overview", "first section is overview")
        check("tree" in model, "tree present")
        top = {c["name"] for c in model["tree"]["children"]}
        check(
            {"src", "data", "assets", "README.md"} <= top,
            "tree top-level has src/data/assets/README.md",
        )
        check(
            any(
                s["kind"] == "section-break" and s["heading"] == "src"
                for s in model["sections"]
            ),
            "code grouped under a 'src' section-break",
        )

        # Coverage walk manifest.
        walk = model["coverage"].get("walk", {})
        check(walk.get("gitignored", 0) >= 1, "walk manifest counts gitignored")
        check(walk.get("dirs_ignored", 0) >= 1, "walk manifest counts dirs_ignored")
        check(walk.get("binary_skipped", 0) >= 1, "walk manifest counts binary_skipped")

        # Standalone image prominence signals (raster gets native dims).
        png_img = next(
            (
                b
                for s in model["sections"]
                for b in s["blocks"]
                if b["type"] == "image" and b.get("origin") == "standalone-image"
                and b.get("width")
            ),
            None,
        )
        check(
            png_img is not None and png_img["width"] == 1 and png_img["height"] == 1,
            "standalone raster carries native width/height (1x1)",
        )

        # Determinism.
        m2 = ec.build_model([str(root)])
        check(
            json.dumps(model, sort_keys=True) == json.dumps(m2, sort_keys=True),
            "deterministic: two runs identical",
        )

        # Caps.
        capped = ec.build_model([str(root)], max_files=2)
        check(
            capped["coverage"]["walk"]["file_count_capped"] > 0,
            "--max-files cap drops extra files",
        )
        truncated = ec.build_model([str(root)], max_text_bytes=20)
        has_trunc = any(
            b.get("truncated")
            for s in truncated["sections"]
            for b in s["blocks"]
            if b["type"] == "code"
        )
        check(has_trunc, "--max-text-bytes truncates a code block")

        # Prominence sink: rounding, clamp, absence.
        cov = ec._new_coverage("x.png")
        b1 = ec._image_block(
            PNG_1x1, "image/png", "t", 2_000_000, cov,
            origin="embedded-raster", page=1, page_fraction=0.62349,
        )
        check(b1["page_fraction"] == 0.623, "page_fraction rounds to 3dp")
        b2 = ec._image_block(
            PNG_1x1, "image/png", "t", 2_000_000, cov,
            origin="embedded-raster", page_fraction=1.5,
        )
        check(b2["page_fraction"] == 1.0, "page_fraction clamps to 1.0")
        b3 = ec._image_block(
            PNG_1x1, "image/png", "t", 2_000_000, cov, origin="embedded-raster"
        )
        check("page_fraction" not in b3, "page_fraction absent when not provided")

    print(f"\nverify_universal_ingestion: {_checks} checks, {_fails} failure(s).")
    return 1 if _fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
