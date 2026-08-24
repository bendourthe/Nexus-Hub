### Step 3: Python Pillow GIF Creation

Pillow provides full control over GIF assembly, including per-frame duration, palette optimization, transparency, and text overlays.

**Basic GIF Assembly**:

```python
from PIL import Image, ImageDraw, ImageFont, ImageSequence
from pathlib import Path
import io

def assemble_gif(
    frames: list[Image.Image],
    output_path: Path,
    duration_ms: int = 80,
    loop: int = 0,
    optimize: bool = True,
) -> Path:
    """Assemble a list of PIL Image frames into an animated GIF.

    Args:
        frames: List of PIL Image objects (same dimensions required).
        output_path: Where to save the GIF.
        duration_ms: Delay between frames in milliseconds.
        loop: Number of loops (0 = infinite).
        optimize: Enable palette optimization per frame.

    Returns:
        Path to the saved GIF.
    """
    if not frames:
        raise ValueError("At least one frame is required")

    # Ensure all frames match the first frame's dimensions
    target_size = frames[0].size
    processed = []
    for frame in frames:
        if frame.size != target_size:
            frame = frame.resize(target_size, Image.Resampling.LANCZOS)
        # Convert to palette mode for GIF compatibility
        if frame.mode != "P":
            frame = frame.convert("RGBA").convert("P", palette=Image.Palette.ADAPTIVE, colors=256)
        processed.append(frame)

    processed[0].save(
        output_path,
        save_all=True,
        append_images=processed[1:],
        duration=duration_ms,
        loop=loop,
        optimize=optimize,
    )
    return output_path
```

**Transparent GIF with Alpha Channel**:

```python
def assemble_transparent_gif(
    frames: list[Image.Image],
    output_path: Path,
    duration_ms: int = 80,
    loop: int = 0,
    transparency_color: tuple[int, int, int] = (0, 255, 0),
) -> Path:
    """Assemble a GIF with transparency support.

    GIF transparency works by designating one palette color as transparent.
    This function composites RGBA frames onto a solid color background,
    then marks that color as transparent in the palette.
    """
    processed = []
    for frame in frames:
        if frame.mode != "RGBA":
            frame = frame.convert("RGBA")

        # Create background with the transparency key color
        bg = Image.new("RGBA", frame.size, (*transparency_color, 255))
        composite = Image.alpha_composite(bg, frame)
        # Convert to palette mode
        p_frame = composite.convert("RGB").convert(
            "P", palette=Image.Palette.ADAPTIVE, colors=255,
        )
        processed.append(p_frame)

    # Find the palette index closest to our transparency color
    palette = processed[0].getpalette()
    transparency_index = _find_closest_palette_index(palette, transparency_color)

    processed[0].save(
        output_path,
        save_all=True,
        append_images=processed[1:],
        duration=duration_ms,
        loop=loop,
        transparency=transparency_index,
        disposal=2,  # Restore to background between frames
    )
    return output_path

def _find_closest_palette_index(
    palette: list[int], target: tuple[int, int, int],
) -> int:
    """Find the palette index whose RGB value is closest to target."""
    min_dist = float("inf")
    best_index = 0
    for i in range(0, len(palette), 3):
        r, g, b = palette[i], palette[i + 1], palette[i + 2]
        dist = (r - target[0]) ** 2 + (g - target[1]) ** 2 + (b - target[2]) ** 2
        if dist < min_dist:
            min_dist = dist
            best_index = i // 3
    return best_index
```

**Text Overlay on Frames**:

```python
def add_text_overlay(
    frame: Image.Image,
    text: str,
    position: str = "bottom",
    font_path: str | None = None,
    font_size: int = 24,
    text_color: tuple[int, int, int, int] = (255, 255, 255, 255),
    stroke_color: tuple[int, int, int, int] = (0, 0, 0, 255),
    stroke_width: int = 2,
    padding: int = 10,
) -> Image.Image:
    """Add a text caption to a frame with stroke outline for readability."""
    frame = frame.convert("RGBA")
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    if font_path:
        font = ImageFont.truetype(font_path, font_size)
    else:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Calculate position
    x = (frame.width - text_width) // 2
    if position == "bottom":
        y = frame.height - text_height - padding
    elif position == "top":
        y = padding
    else:
        y = (frame.height - text_height) // 2

    draw.text(
        (x, y), text, font=font, fill=text_color,
        stroke_width=stroke_width, stroke_fill=stroke_color,
    )
    return Image.alpha_composite(frame, overlay)
```

**Global Palette for Consistent Colors Across Frames**:

```python
from PIL import Image
import numpy as np

def create_global_palette(frames: list[Image.Image], max_colors: int = 256) -> Image.Image:
    """Create a single optimized palette from all frames.

    Using a global palette prevents color flickering between frames
    that can occur when each frame has its own adaptive palette.
    """
    # Concatenate all frames into one tall image for palette computation
    total_height = sum(f.size[1] for f in frames)
    combined = Image.new("RGB", (frames[0].size[0], total_height))
    y_offset = 0
    for frame in frames:
        rgb = frame.convert("RGB")
        combined.paste(rgb, (0, y_offset))
        y_offset += rgb.size[1]

    # Quantize the combined image to get a global palette
    quantized = combined.quantize(colors=max_colors, method=Image.Quantize.MEDIANCUT)
    return quantized

def apply_global_palette(
    frames: list[Image.Image], palette_image: Image.Image,
) -> list[Image.Image]:
    """Apply a precomputed global palette to all frames."""
    result = []
    for frame in frames:
        rgb = frame.convert("RGB")
        quantized = rgb.quantize(palette=palette_image, dither=Image.Dither.FLOYDSTEINBERG)
        result.append(quantized)
    return result
```
