### Step 7: Batch Processing and Optimization

Automate large-scale sticker generation with parallel processing, file size optimization, and output validation.

**Batch Generation Pipeline**:

```python
import asyncio
from dataclasses import dataclass
from pathlib import Path

@dataclass
class BatchItem:
    """A single item in a batch generation job."""
    name: str
    prompt: str
    style: str = "sticker"
    animation: str = "bounce"      # bounce, pulse, rotate, shake, none

@dataclass
class BatchResult:
    """Result for a single batch item."""
    name: str
    output_path: Path | None
    file_size_kb: float
    frame_count: int
    success: bool
    error: str | None = None

async def generate_sticker_batch(
    items: list[BatchItem],
    generator: ImageGenerator,
    config: PipelineConfig,
    max_concurrent: int = 4,
) -> list[BatchResult]:
    """Generate a batch of animated stickers with concurrency control."""
    semaphore = asyncio.Semaphore(max_concurrent)
    results = []

    async def process_item(item: BatchItem) -> BatchResult:
        async with semaphore:
            try:
                # Generate base image
                request = GenerationRequest(
                    prompt=item.prompt,
                    width=config.width,
                    height=config.height,
                    style=item.style,
                )
                images = await generator.generate(request)
                if not images:
                    return BatchResult(
                        name=item.name, output_path=None,
                        file_size_kb=0, frame_count=0,
                        success=False, error="No images generated",
                    )

                # Load the generated image
                base_image = Image.open(io.BytesIO(images[0].data)).convert("RGBA")

                # Apply animation
                animation_tracks = _get_animation_tracks(item.animation)
                frames = render_animation(
                    base_image, animation_tracks,
                    frame_count=config.frame_count,
                    canvas_size=(config.width, config.height),
                )

                # Add sticker outline
                frames = [add_sticker_outline(f) for f in frames]

                # Export
                output_path = config.output_dir / f"{item.name}.gif"
                assemble_transparent_gif(
                    frames, output_path,
                    duration_ms=config.frame_duration_ms,
                )

                # Optimize
                optimize_gif(output_path, config.max_file_size_kb)

                file_size_kb = output_path.stat().st_size / 1024
                return BatchResult(
                    name=item.name,
                    output_path=output_path,
                    file_size_kb=file_size_kb,
                    frame_count=len(frames),
                    success=True,
                )
            except Exception as e:
                return BatchResult(
                    name=item.name, output_path=None,
                    file_size_kb=0, frame_count=0,
                    success=False, error=str(e),
                )

    tasks = [process_item(item) for item in items]
    results = await asyncio.gather(*tasks)
    return list(results)

def _get_animation_tracks(animation_type: str) -> list[AnimationTrack]:
    presets = {
        "bounce": bounce_animation,
        "pulse": pulse_animation,
        "rotate": rotate_animation,
        "shake": shake_animation,
        "none": lambda: [],
    }
    factory = presets.get(animation_type, bounce_animation)
    return factory()
```

**GIF Size Optimization**:

```python
import subprocess
import shutil
from pathlib import Path
from PIL import Image

def optimize_gif(
    gif_path: Path,
    target_size_kb: int,
    min_colors: int = 32,
    min_fps: int = 8,
) -> Path:
    """Iteratively reduce GIF file size to meet target.

    Optimization strategies applied in order:
    1. Reduce color count (256 -> 128 -> 64 -> 32)
    2. Reduce frame rate (drop every other frame)
    3. Reduce dimensions (scale down 10% per iteration)
    4. Apply lossy compression with gifsicle (if available)
    """
    current_size = gif_path.stat().st_size / 1024
    if current_size <= target_size_kb:
        return gif_path

    # Strategy 1: Color reduction
    for colors in [128, 64, 32]:
        if colors < min_colors:
            break
        _reduce_colors(gif_path, colors)
        if gif_path.stat().st_size / 1024 <= target_size_kb:
            return gif_path

    # Strategy 2: Frame decimation (drop alternating frames)
    _decimate_frames(gif_path)
    if gif_path.stat().st_size / 1024 <= target_size_kb:
        return gif_path

    # Strategy 3: Lossy compression with gifsicle
    if shutil.which("gifsicle"):
        for lossy_level in [30, 60, 80, 100, 150, 200]:
            _gifsicle_optimize(gif_path, lossy_level)
            if gif_path.stat().st_size / 1024 <= target_size_kb:
                return gif_path

    # Strategy 4: Scale down
    for scale_pct in [90, 80, 70, 60, 50]:
        _scale_gif(gif_path, scale_pct / 100)
        if gif_path.stat().st_size / 1024 <= target_size_kb:
            return gif_path

    return gif_path

def _reduce_colors(gif_path: Path, max_colors: int) -> None:
    """Re-quantize a GIF to fewer colors."""
    img = Image.open(gif_path)
    frames = []
    durations = []
    for frame in ImageSequence.Iterator(img):
        durations.append(frame.info.get("duration", 80))
        rgb = frame.convert("RGB")
        quantized = rgb.quantize(colors=max_colors, method=Image.Quantize.MEDIANCUT)
        frames.append(quantized)

    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=img.info.get("loop", 0),
        optimize=True,
    )

def _decimate_frames(gif_path: Path) -> None:
    """Drop every other frame and double the duration of remaining frames."""
    img = Image.open(gif_path)
    frames = []
    durations = []
    for i, frame in enumerate(ImageSequence.Iterator(img)):
        if i % 2 == 0:
            durations.append(frame.info.get("duration", 80) * 2)
            frames.append(frame.copy())

    if len(frames) < 2:
        return

    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=img.info.get("loop", 0),
        optimize=True,
    )

def _gifsicle_optimize(gif_path: Path, lossy_level: int) -> None:
    """Apply lossy compression using gifsicle."""
    tmp_path = gif_path.with_suffix(".opt.gif")
    subprocess.run(
        ["gifsicle", "-O3", f"--lossy={lossy_level}", str(gif_path), "-o", str(tmp_path)],
        capture_output=True,
    )
    if tmp_path.exists() and tmp_path.stat().st_size < gif_path.stat().st_size:
        tmp_path.replace(gif_path)
    else:
        tmp_path.unlink(missing_ok=True)

def _scale_gif(gif_path: Path, scale: float) -> None:
    """Scale all frames down by the given factor."""
    img = Image.open(gif_path)
    new_size = (int(img.width * scale), int(img.height * scale))
    frames = []
    durations = []
    for frame in ImageSequence.Iterator(img):
        durations.append(frame.info.get("duration", 80))
        resized = frame.resize(new_size, Image.Resampling.LANCZOS)
        frames.append(resized)

    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=img.info.get("loop", 0),
        optimize=True,
    )
```

**Output Validation**:

```python
from dataclasses import dataclass
from pathlib import Path
from PIL import Image, ImageSequence

@dataclass
class ValidationResult:
    """Result of validating a generated GIF/sticker."""
    valid: bool
    file_size_kb: float
    dimensions: tuple[int, int]
    frame_count: int
    duration_ms: int
    errors: list[str]
    warnings: list[str]

def validate_output(
    gif_path: Path,
    platform: str = "telegram",
) -> ValidationResult:
    """Validate a generated GIF against platform requirements."""
    preset = PLATFORM_PRESETS.get(platform, PLATFORM_PRESETS["telegram"])
    errors: list[str] = []
    warnings: list[str] = []

    file_size_kb = gif_path.stat().st_size / 1024

    img = Image.open(gif_path)
    dimensions = img.size
    frame_count = 0
    total_duration_ms = 0
    for frame in ImageSequence.Iterator(img):
        frame_count += 1
        total_duration_ms += frame.info.get("duration", 80)

    # Check file size
    max_kb = preset["max_size_kb"]
    if file_size_kb > max_kb:
        errors.append(f"File size {file_size_kb:.1f} KB exceeds {platform} limit of {max_kb} KB")

    # Check dimensions
    expected = preset["dimensions"]
    if dimensions != expected:
        warnings.append(f"Dimensions {dimensions} differ from {platform} recommended {expected}")

    # Check duration
    max_duration_s = preset.get("max_duration_s")
    if max_duration_s and total_duration_ms / 1000 > max_duration_s:
        errors.append(f"Duration {total_duration_ms / 1000:.1f}s exceeds {platform} limit of {max_duration_s}s")

    # Check frame count (too few = choppy, too many = large file)
    if frame_count < 4:
        warnings.append(f"Only {frame_count} frames; animation may appear choppy")
    if frame_count > 100:
        warnings.append(f"{frame_count} frames is excessive; consider decimating")

    return ValidationResult(
        valid=len(errors) == 0,
        file_size_kb=file_size_kb,
        dimensions=dimensions,
        frame_count=frame_count,
        duration_ms=total_duration_ms,
        errors=errors,
        warnings=warnings,
    )
```
