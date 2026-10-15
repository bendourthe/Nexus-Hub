#!/usr/bin/env python3
"""
generate_local_image.py - Opt-in, LOCAL-ONLY AI image generation for the
document-to-interactive-html skill (Tier 3 imagery).

This script ships as a Tier-3 bundled resource: the authoring stage invokes it
via the shell ONLY when the user has chosen the `ai` imagery tier. It generates
an original image from a content-and-style-derived prompt using a LOCAL model
runtime and locally-present weights, base64-embeds the result, and records the
model, its license, and the copyright caveat - so the final HTML still opens
offline with zero external requests.

HARD CONSTRAINT - LOCAL ONLY, ZERO NETWORK: this script makes NO network call
and imports NO network / hosted-API client of any kind. A third-party image
generation API (DALL-E, Midjourney, hosted Stable Diffusion, FLUX Pro, ...) is
OUT OF SCOPE by policy (generation-as-service is a hard-no). Generation runs on
the local machine or it does not run at all. Model WEIGHTS must be obtained by
the user out-of-band; the script never downloads them (it forces the runtime
into offline mode before importing it), so a missing runtime or missing weights
DEGRADES to a setup hint rather than reaching out to a server.

COMMERCIAL-USE SAFETY: the default models are commercially-clean and locally
runnable - FLUX.1 schnell (Apache-2.0) and SDXL base (CreativeML Open RAIL++-M).
A model whose license is not free-for-commercial-use is rejected. AI-generated
output is recorded with the caveat that pure-AI output may not be copyrightable.

RUNTIMES (either, both optional and lazy):
    1. diffusers + torch (pip install diffusers torch transformers accelerate),
       loaded with local_files_only=True and HF_HUB_OFFLINE=1 so no weight
       download is ever attempted.
    2. A user-configured LOCAL CLI via the NEXUS_LOCAL_IMAGE_CMD environment
       variable (e.g. a ComfyUI / stable-diffusion.cpp headless command). It is
       run locally via subprocess (never a shell), with {prompt} / {out} /
       {width} / {height} / {steps} placeholders substituted. Declare its
       model license via NEXUS_LOCAL_IMAGE_LICENSE.

GRACEFUL DEGRADE: when no local runtime / weights are present, or generation
fails, the script prints a setup hint, writes an empty degraded manifest, and
exits with the degrade code (3); the authoring stage falls back to Tier 1. It
never raises and never falls back to a hosted API.

Usage:
    python generate_local_image.py --prompt "clinical lab, cool palette, minimal" -o asset.json
    python generate_local_image.py --prompt "city skyline dusk" --model sdxl --size 1024x1024 -o out.json

Exit codes:
    0  success: an image was generated and embedded.
    2  usage error (bad arguments).
    3  degrade: no local runtime / weights, or generation failed. The authoring
       stage falls back to Tier 1. The manifest (if a path was given) is written
       with {"degraded": true, "reason": ...}.

All diagnostics go to stderr; the manifest is written to --out (stdout if
omitted).
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from typing import Any

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_DEGRADE = 3

DEFAULT_MAX_BYTES = 3_000_000
AI_CAVEAT = "AI-generated; may not be copyrightable"
CLI_TIMEOUT = int(os.environ.get("NEXUS_LOCAL_IMAGE_TIMEOUT", "1200"))

# Commercially-clean, locally-runnable models. Adding a model here asserts its
# license permits commercial use; anything not in this map (or not in
# COMMERCIAL_LICENSES) is rejected.
MODELS: dict[str, dict[str, Any]] = {
    "flux-schnell": {
        "repo": "black-forest-labs/FLUX.1-schnell",
        "license": "Apache-2.0",
        "pipeline": "FluxPipeline",
        "default_steps": 4,
        "label": "FLUX.1 schnell",
    },
    "sdxl": {
        "repo": "stabilityai/stable-diffusion-xl-base-1.0",
        "license": "CreativeML Open RAIL++-M",
        "pipeline": "StableDiffusionXLPipeline",
        "default_steps": 25,
        "label": "SDXL base 1.0",
    },
}
COMMERCIAL_LICENSES = {"Apache-2.0", "CreativeML Open RAIL++-M", "Open-RAIL-M"}


class DegradeError(Exception):
    """Internal signal: fall back to Tier 1 with a hint (never a hosted API)."""


def log(msg: str) -> None:
    """Write a diagnostic line to stderr (stdout stays reserved for output)."""
    print(msg, file=sys.stderr)


def parse_size(text: str) -> tuple[int, int]:
    """Parse a 'WxH' size string into (width, height)."""
    try:
        w_str, h_str = text.lower().split("x", 1)
        w, h = int(w_str), int(h_str)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"bad --size '{text}', expected WxH e.g. 1024x1024") from exc
    if w < 64 or h < 64 or w > 4096 or h > 4096:
        raise ValueError(f"--size {w}x{h} out of range (64..4096)")
    return w, h


def to_data_uri(data: bytes, mime: str = "image/png") -> str:
    """Base64-encode bytes into a self-contained data: URI."""
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def build_asset(data: bytes, prompt: str, model_label: str, license_id: str,
                width: int, height: int, max_bytes: int) -> dict[str, Any]:
    """Assemble the asset entry + Tier-3 provenance, enforcing the size cap."""
    if len(data) > max_bytes:
        raise DegradeError(
            f"generated image is {len(data)} bytes, over --max-bytes ({max_bytes}); "
            "lower --size or raise --max-bytes")
    alt = prompt.strip()[:120] or "AI-generated illustration"
    return {
        "data_uri": to_data_uri(data),
        "alt": alt,
        "width": width,
        "height": height,
        "provenance": {
            "tier": "ai",
            "model": model_label,
            "license": license_id,
            "note": AI_CAVEAT,
            "prompt": prompt,
        },
    }


def generate_via_diffusers(prompt: str, model_key: str, size: tuple[int, int],
                           steps: int | None, max_bytes: int) -> dict[str, Any]:
    """Generate with a LOCAL diffusers pipeline. Forces offline mode so no weight
    download is ever attempted; raises DegradeError when the runtime or weights
    are absent."""
    spec = MODELS[model_key]
    if spec["license"] not in COMMERCIAL_LICENSES:
        raise DegradeError(f"model '{model_key}' license '{spec['license']}' is not free-for-commercial-use")

    # Force the HF stack offline BEFORE importing it, so a missing local weight
    # degrades instead of silently downloading (which would be an outbound path).
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("DIFFUSERS_OFFLINE", "1")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

    try:
        import io  # noqa: PLC0415

        import diffusers  # noqa: PLC0415  (heavy optional dependency, lazy)
        import torch  # noqa: PLC0415
    except ImportError as exc:
        raise DegradeError(
            f"local runtime not installed ({exc}); "
            "pip install diffusers torch transformers accelerate, or set NEXUS_LOCAL_IMAGE_CMD"
        ) from exc

    pipe_cls = getattr(diffusers, spec["pipeline"], None)
    if pipe_cls is None:
        raise DegradeError(f"diffusers has no pipeline '{spec['pipeline']}'; upgrade diffusers")

    try:
        pipe = pipe_cls.from_pretrained(spec["repo"], local_files_only=True)
    except Exception as exc:  # noqa: BLE001 (any load failure -> degrade, never fatal)
        raise DegradeError(
            f"weights for {spec['repo']} are not present locally ({exc}); "
            "obtain them out-of-band (this script never downloads weights)"
        ) from exc

    device = "cuda" if getattr(torch, "cuda", None) and torch.cuda.is_available() else "cpu"
    pipe = pipe.to(device)
    width, height = size
    n_steps = steps or int(spec["default_steps"])
    result = pipe(prompt, num_inference_steps=n_steps, width=width, height=height)
    image = result.images[0]
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return build_asset(buf.getvalue(), prompt, spec["label"], spec["license"],
                       width, height, max_bytes)


def generate_via_cli(prompt: str, size: tuple[int, int], steps: int | None,
                     max_bytes: int) -> dict[str, Any]:
    """Generate with a user-configured LOCAL CLI (NEXUS_LOCAL_IMAGE_CMD). Runs
    locally via subprocess with no shell; raises DegradeError when unconfigured
    or when the command fails."""
    cmd_tmpl = os.environ.get("NEXUS_LOCAL_IMAGE_CMD", "").strip()
    if not cmd_tmpl:
        raise DegradeError("no local diffusers runtime and NEXUS_LOCAL_IMAGE_CMD is not set")

    import shlex  # noqa: PLC0415
    import subprocess  # noqa: PLC0415 (local process launch only, never a shell)
    import tempfile  # noqa: PLC0415

    width, height = size
    n_steps = steps or 20
    with tempfile.TemporaryDirectory() as tmp:
        out_png = str(Path(tmp) / "out.png")
        subs = {"prompt": prompt, "out": out_png, "width": str(width),
                "height": str(height), "steps": str(n_steps)}
        parts = [p.format(**subs) for p in shlex.split(cmd_tmpl)]
        try:
            subprocess.run(parts, check=True, timeout=CLI_TIMEOUT, shell=False,  # noqa: S603
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        except Exception as exc:  # noqa: BLE001 (any CLI failure -> degrade)
            raise DegradeError(f"local image CLI failed ({exc})") from exc
        png = Path(out_png)
        if not png.exists():
            raise DegradeError(f"local image CLI produced no output file at {out_png}")
        data = png.read_bytes()

    license_id = os.environ.get("NEXUS_LOCAL_IMAGE_LICENSE", "user-declared local model").strip()
    return build_asset(data, prompt, "local CLI (NEXUS_LOCAL_IMAGE_CMD)", license_id,
                       width, height, max_bytes)


def write_manifest(out_path: str | None, manifest: dict[str, Any]) -> None:
    text = json.dumps(manifest, indent=2, ensure_ascii=True)
    if out_path:
        Path(out_path).write_text(text, encoding="utf-8")
    else:
        print(text)


def degrade(out_path: str | None, reason: str, **extra: Any) -> int:
    """Write an empty degraded manifest, log the reason, and return the degrade code."""
    log(f"[generate_local_image] degrade: {reason}")
    manifest = {"assets": [], "degraded": True, "reason": reason}
    manifest.update(extra)
    write_manifest(out_path, manifest)
    return EXIT_DEGRADE


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Opt-in LOCAL-ONLY AI image generation (Tier 3). Never calls a hosted service.")
    parser.add_argument("--prompt", required=True, help="content-and-style-derived image prompt")
    parser.add_argument("--model", choices=sorted(MODELS), default="flux-schnell")
    parser.add_argument("--size", default="1024x1024", help="WxH, e.g. 1024x1024")
    parser.add_argument("--steps", type=int, default=None, help="inference steps (model default if omitted)")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("-o", "--out", default=None, help="manifest output path (stdout if omitted)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        size = parse_size(args.size)
    except ValueError as exc:
        log(f"[generate_local_image] {exc}")
        return EXIT_USAGE
    if args.steps is not None and args.steps < 1:
        log("[generate_local_image] --steps must be >= 1")
        return EXIT_USAGE

    # Try the local diffusers runtime first, then a configured local CLI. Any
    # failure at either stage degrades to Tier 1 - never a hosted-API fallback.
    try:
        asset = generate_via_diffusers(args.prompt, args.model, size, args.steps, args.max_bytes)
    except DegradeError as diffusers_exc:
        try:
            asset = generate_via_cli(args.prompt, size, args.steps, args.max_bytes)
        except DegradeError as cli_exc:
            return degrade(args.out, f"{diffusers_exc} | {cli_exc}",
                           prompt=args.prompt, model=args.model)

    manifest = {
        "assets": [asset],
        "degraded": False,
        "prompt": args.prompt,
        "model": asset["provenance"]["model"],
        "license": asset["provenance"]["license"],
    }
    write_manifest(args.out, manifest)
    log(f"[generate_local_image] generated 1 image with {asset['provenance']['model']}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
