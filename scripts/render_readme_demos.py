"""Render the local README mockups as reproducible GIFs and static posters.

Requires locally installed Playwright Chromium and Pillow. No network calls.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from nexus_process import install_no_window_default

install_no_window_default()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New output directory; existing files are never overwritten")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    source = ROOT / "guides/website/readme-demos.html"
    report: dict[str, object] = {"source": str(source.relative_to(ROOT)), "mockup": True, "artifacts": []}
    artifacts: list[dict[str, object]] = []
    with sync_playwright() as runtime:
        browser = runtime.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1200, "height": 1100}, device_scale_factor=1, reduced_motion="reduce")
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(source.as_uri())
        page.wait_for_function("!!window.readmeDemos")
        page.evaluate("document.fonts.ready")
        for kind in ("settings", "workflow"):
            count = page.evaluate("kind => window.readmeDemos.scenes[kind].length", kind)
            frames: list[Image.Image] = []
            durations: list[int] = []
            posters: list[Image.Image] = []
            stage = page.locator(f"#{kind}-stage")
            for index in range(count):
                page.evaluate("([kind,index]) => window.readmeDemos.render(kind,index)", [kind, index])
                page.wait_for_function("Array.from(document.images).every(i => i.complete)")
                assert page.evaluate("Array.from(document.images).every(i => i.naturalWidth > 0)"), "A local image did not load"
                frame = Image.open(io.BytesIO(stage.screenshot())).convert("RGB")
                posters.append(frame)
                frames.append(frame)
                durations.append(3900 if kind == "settings" else 5200)
                # Capture an eased pointer transition before the next state appears.
                if index + 1 < count:
                    for progress in (0.2, 0.4, 0.6, 0.8, 1):
                        page.evaluate("([kind,index,next,progress]) => window.readmeDemos.render(kind,index,{next,progress})", [kind, index, index + 1, progress])
                        # The GIF intentionally demonstrates motion; the HTML preview remains opt-in.
                        page.locator(f"#{kind}-stage .mock-pointer").evaluate("el => el.style.display = 'block'")
                        frames.append(Image.open(io.BytesIO(stage.screenshot())).convert("RGB"))
                        durations.append(80)
            assert len({frame.size for frame in frames}) == 1, "Scene geometry changed between frames"
            # One palette across all scenes prevents color flicker between frames.
            sample = Image.new("RGB", (320 * count, 220))
            for index, frame in enumerate(posters):
                sample.paste(frame.resize((320, 220)), (320 * index, 0))
            palette = sample.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
            indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
            gif = output / f"nexus-hub-{kind}.gif"
            indexed[0].save(gif, save_all=True, append_images=indexed[1:], duration=durations, loop=0, optimize=True, disposal=1)
            posters[0].save(output / f"nexus-hub-{kind}.png", optimize=True)
            for index, frame in enumerate(posters):
                frame.save(output / f"{kind}-scene-{index + 1:02}.png", optimize=True)
            with Image.open(gif) as result:
                duration = 0
                for index in range(result.n_frames):
                    result.seek(index)
                    duration += result.info["duration"]
                assert result.n_frames > count
                assert gif.stat().st_size < 4 * 1024 * 1024, "README animation exceeds the 4 MiB budget"
                artifacts.append({"kind": kind, "width": result.width, "height": result.height, "frames": result.n_frames, "duration_ms": duration, "bytes": gif.stat().st_size, "scenes": count})
        assert not errors, errors
        browser.close()
    report["artifacts"] = artifacts
    report["browser_errors"] = errors
    (output / "render-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
