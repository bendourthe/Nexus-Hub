### Step 1: Pipeline Architecture and Tool Selection

The GIF and sticker creation pipeline flows through four stages: content generation, frame preparation, animation assembly, and output optimization. Select tools based on your input source and quality requirements.

**Pipeline Overview**:

```
Input Source          Frame Preparation       Assembly            Optimization
-----------          -----------------       --------            ------------
AI-generated      -> Resize / crop        -> Pillow GIF      -> Color reduction
  images             Remove background       assembly            Lossy compression
                     Add outlines                                Size validation
Video clip        -> Extract frames       -> ffmpeg palette   -> Frame rate trim
                     Select key frames       generation          Dimension scaling
                     Apply filters
Sprite sheet      -> Slice into frames    -> Pillow sequence  -> Dithering
                     Apply tweening          with duration       Palette optimization
                     Easing interpolation    control
Static image      -> Duplicate + transform -> Pillow animate  -> Loop optimization
                     Apply effects            with effects       File size check
```

**Tool Selection Matrix**:

| Tool | Best For | Install | Notes |
|------|----------|---------|-------|
| Pillow (Python) | Frame-by-frame GIF assembly, text overlays, effects | `pip install Pillow` | Pure Python, cross-platform |
| ffmpeg | Video-to-GIF, scaling, frame extraction, palette gen | System package | Industry standard, CLI-based |
| ImageMagick | GIF optimization, format conversion, batch ops | System package | `convert` and `gifsicle` combo |
| sharp (Node.js) | Server-side image processing, web pipelines | `npm install sharp` | Fast, libvips-based |
| gifsicle | GIF optimization, lossy compression, frame editing | System package | Specialized GIF optimizer |
| APNG Assembler | Animated PNG for platforms that support it | System package | Lossless alternative to GIF |

**Project Scaffold**:

```python
from pathlib import Path

# Standard project layout for a sticker generation pipeline
PROJECT_LAYOUT = {
    "src/": "Pipeline source code",
    "src/generators/": "AI image generation adapters",
    "src/processors/": "Frame processing (resize, crop, effects)",
    "src/assemblers/": "GIF/APNG assembly modules",
    "src/optimizers/": "File size optimization and validation",
    "assets/sprites/": "Source sprite sheets",
    "assets/fonts/": "Fonts for text overlays",
    "output/": "Generated GIFs and stickers",
    "output/previews/": "Low-res previews for review",
    "config/": "Platform presets and generation configs",
}

# Configuration dataclass for the pipeline
from dataclasses import dataclass, field

@dataclass
class PipelineConfig:
    """Configuration for a GIF/sticker generation run."""
    output_dir: Path = Path("output")
    width: int = 512
    height: int = 512
    frame_count: int = 24
    frame_duration_ms: int = 80
    loop_count: int = 0          # 0 = infinite loop
    max_file_size_kb: int = 256
    max_colors: int = 256
    transparent_background: bool = True
    platform: str = "telegram"   # telegram, discord, slack, whatsapp
```

**Platform Presets**:

```python
PLATFORM_PRESETS: dict[str, dict] = {
    "telegram": {
        "max_size_kb": 512,
        "dimensions": (512, 512),
        "format": "webm",            # Telegram prefers WebM for animated stickers
        "fallback_format": "gif",
        "max_duration_s": 3,
        "max_fps": 30,
    },
    "discord": {
        "max_size_kb": 256,           # Standard emoji limit
        "dimensions": (128, 128),     # Emoji size; stickers can be larger
        "format": "gif",
        "max_duration_s": 5,
        "max_fps": 50,
    },
    "slack": {
        "max_size_kb": 128,           # Custom emoji limit
        "dimensions": (128, 128),
        "format": "gif",
        "max_duration_s": None,       # No strict limit
        "max_fps": 30,
    },
    "whatsapp": {
        "max_size_kb": 500,
        "dimensions": (512, 512),
        "format": "webp",             # WhatsApp uses animated WebP
        "fallback_format": "gif",
        "max_duration_s": 6,
        "max_fps": 30,
    },
    "imessage": {
        "max_size_kb": 500,
        "dimensions": (618, 618),
        "format": "gif",              # or APNG
        "max_duration_s": None,
        "max_fps": 30,
    },
}
```
