### Step 4: ffmpeg Video-to-GIF Pipeline

ffmpeg produces higher quality GIFs from video sources than most other tools. The two-pass palette generation technique is essential for good results.

**Two-Pass Palette Generation** (the gold standard for ffmpeg GIF quality):

```bash
#!/usr/bin/env bash
set -euo pipefail

# Pass 1: Generate an optimized palette from the video content
ffmpeg -i input.mp4 \
    -vf "fps=15,scale=480:-1:flags=lanczos,palettegen=stats_mode=diff" \
    -y palette.png

# Pass 2: Use the palette to encode the GIF
ffmpeg -i input.mp4 -i palette.png \
    -lavfi "fps=15,scale=480:-1:flags=lanczos [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=5" \
    -y output.gif
```

**Python Wrapper for ffmpeg**:

```python
import subprocess
import shutil
from pathlib import Path

class FfmpegGifConverter:
    """Convert video files to optimized GIFs using ffmpeg two-pass encoding."""

    def __init__(self) -> None:
        if not shutil.which("ffmpeg"):
            raise RuntimeError("ffmpeg not found in PATH")

    def convert(
        self,
        input_path: Path,
        output_path: Path,
        fps: int = 15,
        width: int = 480,
        start_time: float | None = None,
        duration: float | None = None,
        dither: str = "bayer",
        bayer_scale: int = 5,
    ) -> Path:
        """Convert a video file to an optimized GIF.

        Args:
            input_path: Source video file.
            output_path: Destination GIF file.
            fps: Target frame rate.
            width: Target width (-1 preserves aspect ratio for height).
            start_time: Start offset in seconds (None = beginning).
            duration: Duration in seconds (None = full video).
            dither: Dithering algorithm (bayer, floyd_steinberg, sierra2).
            bayer_scale: Bayer dither scale (0-5, lower = more dithering).
        """
        palette_path = output_path.with_suffix(".palette.png")
        input_args = self._build_input_args(input_path, start_time, duration)
        filter_base = f"fps={fps},scale={width}:-1:flags=lanczos"

        try:
            # Pass 1: palette generation
            self._run_ffmpeg([
                *input_args,
                "-vf", f"{filter_base},palettegen=stats_mode=diff",
                "-y", str(palette_path),
            ])

            # Pass 2: GIF encoding with palette
            self._run_ffmpeg([
                *input_args,
                "-i", str(palette_path),
                "-lavfi", (
                    f"{filter_base} [x]; "
                    f"[x][1:v] paletteuse=dither={dither}:bayer_scale={bayer_scale}"
                ),
                "-y", str(output_path),
            ])
        finally:
            palette_path.unlink(missing_ok=True)

        return output_path

    def _build_input_args(
        self, input_path: Path, start_time: float | None, duration: float | None,
    ) -> list[str]:
        args = []
        if start_time is not None:
            args.extend(["-ss", str(start_time)])
        args.extend(["-i", str(input_path)])
        if duration is not None:
            args.extend(["-t", str(duration)])
        return args

    def _run_ffmpeg(self, args: list[str]) -> None:
        result = subprocess.run(
            ["ffmpeg", *args],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr[-500:]}")
```

**Common ffmpeg Filter Recipes**:

```bash
# Crop to square (center crop)
ffmpeg -i input.mp4 \
    -vf "crop=min(iw\,ih):min(iw\,ih)" \
    -y cropped.mp4

# Speed up 2x (for creating fast loops)
ffmpeg -i input.mp4 \
    -vf "setpts=0.5*PTS" \
    -y fast.mp4

# Reverse playback (for ping-pong loops)
ffmpeg -i input.mp4 \
    -vf "reverse" \
    -y reversed.mp4

# Concatenate forward + reverse for seamless loop
ffmpeg -i input.mp4 -i reversed.mp4 \
    -filter_complex "[0:v][1:v]concat=n=2:v=1:a=0" \
    -y pingpong.mp4

# Extract frames as PNGs for manual editing
ffmpeg -i input.mp4 \
    -vf "fps=10" \
    frames/frame_%04d.png

# Reassemble edited frames into GIF
ffmpeg -framerate 10 -i frames/frame_%04d.png \
    -vf "palettegen" -y palette.png
ffmpeg -framerate 10 -i frames/frame_%04d.png -i palette.png \
    -lavfi "paletteuse" -y output.gif
```
