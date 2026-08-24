### Step 5: Animation Techniques

Create animations programmatically using sprite sheets, tweening, easing functions, and keyframe interpolation.

**Easing Functions**:

```python
import math

def ease_linear(t: float) -> float:
    return t

def ease_in_quad(t: float) -> float:
    return t * t

def ease_out_quad(t: float) -> float:
    return t * (2 - t)

def ease_in_out_quad(t: float) -> float:
    if t < 0.5:
        return 2 * t * t
    return -1 + (4 - 2 * t) * t

def ease_in_cubic(t: float) -> float:
    return t * t * t

def ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3

def ease_out_bounce(t: float) -> float:
    if t < 1 / 2.75:
        return 7.5625 * t * t
    elif t < 2 / 2.75:
        t -= 1.5 / 2.75
        return 7.5625 * t * t + 0.75
    elif t < 2.5 / 2.75:
        t -= 2.25 / 2.75
        return 7.5625 * t * t + 0.9375
    else:
        t -= 2.625 / 2.75
        return 7.5625 * t * t + 0.984375

def ease_out_elastic(t: float) -> float:
    if t == 0 or t == 1:
        return t
    return 2 ** (-10 * t) * math.sin((t - 0.075) * (2 * math.pi) / 0.3) + 1

EASING_FUNCTIONS = {
    "linear": ease_linear,
    "ease-in": ease_in_quad,
    "ease-out": ease_out_quad,
    "ease-in-out": ease_in_out_quad,
    "ease-in-cubic": ease_in_cubic,
    "ease-out-cubic": ease_out_cubic,
    "bounce": ease_out_bounce,
    "elastic": ease_out_elastic,
}
```

**Keyframe Animation System**:

```python
from dataclasses import dataclass
from PIL import Image

@dataclass
class Keyframe:
    """A single keyframe defining a property value at a specific time."""
    time: float          # 0.0 to 1.0 (normalized)
    value: float
    easing: str = "linear"

@dataclass
class AnimationTrack:
    """A sequence of keyframes for one property (x, y, scale, rotation, opacity)."""
    property_name: str
    keyframes: list[Keyframe]

    def evaluate(self, t: float) -> float:
        """Interpolate the property value at normalized time t (0.0 to 1.0)."""
        if not self.keyframes:
            return 0.0
        if t <= self.keyframes[0].time:
            return self.keyframes[0].value
        if t >= self.keyframes[-1].time:
            return self.keyframes[-1].value

        # Find the surrounding keyframes
        for i in range(len(self.keyframes) - 1):
            k0 = self.keyframes[i]
            k1 = self.keyframes[i + 1]
            if k0.time <= t <= k1.time:
                local_t = (t - k0.time) / (k1.time - k0.time)
                easing_fn = EASING_FUNCTIONS.get(k0.easing, ease_linear)
                eased_t = easing_fn(local_t)
                return k0.value + (k1.value - k0.value) * eased_t

        return self.keyframes[-1].value

def render_animation(
    source: Image.Image,
    tracks: list[AnimationTrack],
    frame_count: int,
    canvas_size: tuple[int, int],
) -> list[Image.Image]:
    """Render an animation by evaluating tracks at each frame."""
    frames = []
    for i in range(frame_count):
        t = i / max(frame_count - 1, 1)
        props = {track.property_name: track.evaluate(t) for track in tracks}

        canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        transformed = _apply_transform(
            source,
            x=props.get("x", 0),
            y=props.get("y", 0),
            scale=props.get("scale", 1.0),
            rotation=props.get("rotation", 0),
            opacity=props.get("opacity", 1.0),
        )
        # Center the transformed image on the canvas with offset
        paste_x = (canvas_size[0] - transformed.width) // 2 + int(props.get("x", 0))
        paste_y = (canvas_size[1] - transformed.height) // 2 + int(props.get("y", 0))
        canvas.paste(transformed, (paste_x, paste_y), transformed)
        frames.append(canvas)

    return frames

def _apply_transform(
    img: Image.Image,
    x: float = 0,
    y: float = 0,
    scale: float = 1.0,
    rotation: float = 0,
    opacity: float = 1.0,
) -> Image.Image:
    """Apply scale, rotation, and opacity transforms to an image."""
    if scale != 1.0:
        new_size = (int(img.width * scale), int(img.height * scale))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    if rotation != 0:
        img = img.rotate(-rotation, expand=True, resample=Image.Resampling.BICUBIC)
    if opacity < 1.0:
        img = img.convert("RGBA")
        r, g, b, a = img.split()
        a = a.point(lambda p: int(p * opacity))
        img = Image.merge("RGBA", (r, g, b, a))
    return img
```

**Common Animation Presets**:

```python
def bounce_animation(amplitude: float = 20, cycles: int = 2) -> list[AnimationTrack]:
    """Create a vertical bounce animation."""
    keyframes = []
    for i in range(cycles * 2 + 1):
        t = i / (cycles * 2)
        value = 0 if i % 2 == 0 else -amplitude
        keyframes.append(Keyframe(time=t, value=value, easing="ease-out"))
    return [AnimationTrack(property_name="y", keyframes=keyframes)]

def pulse_animation(min_scale: float = 0.9, max_scale: float = 1.1) -> list[AnimationTrack]:
    """Create a pulsing scale animation."""
    return [AnimationTrack(
        property_name="scale",
        keyframes=[
            Keyframe(time=0.0, value=1.0, easing="ease-in-out"),
            Keyframe(time=0.25, value=max_scale, easing="ease-in-out"),
            Keyframe(time=0.5, value=1.0, easing="ease-in-out"),
            Keyframe(time=0.75, value=min_scale, easing="ease-in-out"),
            Keyframe(time=1.0, value=1.0, easing="ease-in-out"),
        ],
    )]

def rotate_animation(degrees: float = 360) -> list[AnimationTrack]:
    """Create a full rotation animation."""
    return [AnimationTrack(
        property_name="rotation",
        keyframes=[
            Keyframe(time=0.0, value=0, easing="linear"),
            Keyframe(time=1.0, value=degrees, easing="linear"),
        ],
    )]

def shake_animation(intensity: float = 5, frequency: int = 8) -> list[AnimationTrack]:
    """Create a horizontal shake animation."""
    keyframes = [Keyframe(time=0.0, value=0, easing="linear")]
    for i in range(1, frequency + 1):
        t = i / (frequency + 1)
        direction = 1 if i % 2 == 0 else -1
        decay = 1 - (i / frequency)  # Decay over time
        keyframes.append(Keyframe(time=t, value=intensity * direction * decay, easing="linear"))
    keyframes.append(Keyframe(time=1.0, value=0, easing="linear"))
    return [AnimationTrack(property_name="x", keyframes=keyframes)]
```

**Sprite Sheet Slicer**:

```python
def slice_sprite_sheet(
    sheet: Image.Image,
    columns: int,
    rows: int,
    frame_count: int | None = None,
) -> list[Image.Image]:
    """Slice a sprite sheet into individual frames.

    Args:
        sheet: The full sprite sheet image.
        columns: Number of columns in the grid.
        rows: Number of rows in the grid.
        frame_count: Total frames to extract (None = all cells).
    """
    frame_width = sheet.width // columns
    frame_height = sheet.height // rows
    total = frame_count or (columns * rows)

    frames = []
    for i in range(total):
        col = i % columns
        row = i // columns
        if row >= rows:
            break
        box = (
            col * frame_width,
            row * frame_height,
            (col + 1) * frame_width,
            (row + 1) * frame_height,
        )
        frames.append(sheet.crop(box))
    return frames
```
