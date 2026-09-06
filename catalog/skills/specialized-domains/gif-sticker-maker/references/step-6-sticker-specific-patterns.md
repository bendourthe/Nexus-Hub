### Step 6: Sticker-Specific Patterns

Stickers require specific visual treatments: transparent backgrounds, outline strokes, caption overlays, and precise sizing for each chat platform.

**Background Removal and Outline Stroke**:

```python
from PIL import Image, ImageFilter, ImageDraw

def add_sticker_outline(
    image: Image.Image,
    stroke_width: int = 4,
    stroke_color: tuple[int, int, int, int] = (255, 255, 255, 255),
) -> Image.Image:
    """Add a solid outline stroke around the non-transparent content.

    This creates the classic sticker "die-cut" appearance with a white
    border around the subject.
    """
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # Extract the alpha channel and create a dilated mask
    alpha = image.split()[3]
    # Dilate the alpha mask by the stroke width
    dilated = alpha.copy()
    for _ in range(stroke_width):
        dilated = dilated.filter(ImageFilter.MaxFilter(3))

    # Create the stroke layer
    stroke_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    stroke_pixels = stroke_layer.load()
    alpha_pixels = alpha.load()
    dilated_pixels = dilated.load()

    for y in range(image.height):
        for x in range(image.width):
            # Stroke region: dilated but not in original alpha
            if dilated_pixels[x, y] > 128 and alpha_pixels[x, y] < 128:
                stroke_pixels[x, y] = stroke_color

    # Composite: stroke behind, original on top
    result = Image.alpha_composite(stroke_layer, image)
    return result

def remove_background_simple(
    image: Image.Image,
    threshold: int = 240,
) -> Image.Image:
    """Remove near-white backgrounds by converting to transparency.

    For production use, prefer a dedicated background removal model
    (rembg, remove.bg API, or SAM-based segmentation).
    """
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = pixels[x, y]
            if r > threshold and g > threshold and b > threshold:
                pixels[x, y] = (r, g, b, 0)
    return image
```

**Sticker Caption Overlay**:

```python
def create_sticker_with_caption(
    image: Image.Image,
    caption: str,
    font_path: str,
    font_size: int = 28,
    caption_height: int = 50,
    bg_color: tuple[int, int, int, int] = (0, 0, 0, 160),
    text_color: tuple[int, int, int, int] = (255, 255, 255, 255),
) -> Image.Image:
    """Add a semi-transparent caption bar at the bottom of a sticker."""
    # Expand canvas to accommodate caption
    new_height = image.height + caption_height
    canvas = Image.new("RGBA", (image.width, new_height), (0, 0, 0, 0))
    canvas.paste(image, (0, 0))

    # Draw caption background
    draw = ImageDraw.Draw(canvas)
    draw.rectangle(
        [(0, image.height), (image.width, new_height)],
        fill=bg_color,
    )

    # Draw caption text centered
    font = ImageFont.truetype(font_path, font_size)
    bbox = draw.textbbox((0, 0), caption, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (image.width - text_width) // 2
    text_y = image.height + (caption_height - font_size) // 2
    draw.text((text_x, text_y), caption, font=font, fill=text_color)

    return canvas
```

**Platform Export Functions**:

```python
from pathlib import Path

def export_for_telegram(
    frames: list[Image.Image],
    output_path: Path,
    duration_ms: int = 80,
) -> Path:
    """Export animated sticker for Telegram (512x512, WebM or GIF).

    Telegram animated stickers use WebM (VP9) or Lottie format.
    For GIF fallback, use standard GIF with 512x512 dimensions.
    """
    target_size = (512, 512)
    resized = [f.resize(target_size, Image.Resampling.LANCZOS) for f in frames]
    gif_path = output_path.with_suffix(".gif")
    assemble_transparent_gif(resized, gif_path, duration_ms=duration_ms)
    return gif_path

def export_for_discord(
    frames: list[Image.Image],
    output_path: Path,
    duration_ms: int = 80,
    max_size_kb: int = 256,
) -> Path:
    """Export animated emoji for Discord (128x128, under 256 KB)."""
    target_size = (128, 128)
    resized = [f.resize(target_size, Image.Resampling.LANCZOS) for f in frames]
    gif_path = output_path.with_suffix(".gif")
    assemble_gif(resized, gif_path, duration_ms=duration_ms)

    # Check size and reduce if needed
    file_size_kb = gif_path.stat().st_size / 1024
    if file_size_kb > max_size_kb:
        _reduce_gif_size(gif_path, max_size_kb)
    return gif_path

def export_for_slack(
    frames: list[Image.Image],
    output_path: Path,
    duration_ms: int = 80,
    max_size_kb: int = 128,
) -> Path:
    """Export custom emoji for Slack (128x128, under 128 KB)."""
    target_size = (128, 128)
    resized = [f.resize(target_size, Image.Resampling.LANCZOS) for f in frames]
    gif_path = output_path.with_suffix(".gif")
    assemble_gif(resized, gif_path, duration_ms=duration_ms)

    file_size_kb = gif_path.stat().st_size / 1024
    if file_size_kb > max_size_kb:
        _reduce_gif_size(gif_path, max_size_kb)
    return gif_path
```
