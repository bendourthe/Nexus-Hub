### Step 2: AI Image Generation Integration

Integrate with AI image generation providers using a provider-agnostic adapter pattern. This allows swapping providers without changing the pipeline logic.

**Provider Adapter Interface**:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

@dataclass
class GenerationRequest:
    """Provider-agnostic image generation request."""
    prompt: str
    negative_prompt: str = ""
    width: int = 512
    height: int = 512
    num_images: int = 1
    style: str = "sticker"        # sticker, pixel-art, cartoon, chibi, funko
    seed: int | None = None       # For reproducibility

@dataclass
class GeneratedImage:
    """Result from an image generation provider."""
    data: bytes
    width: int
    height: int
    provider: str
    seed: int | None = None
    metadata: dict = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}

class ImageGenerator(ABC):
    """Abstract adapter for AI image generation providers."""

    @abstractmethod
    async def generate(self, request: GenerationRequest) -> list[GeneratedImage]:
        """Generate images from a text prompt."""
        ...

    @abstractmethod
    async def check_health(self) -> bool:
        """Verify the provider is accessible and quota is available."""
        ...
```

**OpenAI DALL-E Adapter**:

```python
import httpx
import base64

class DallEGenerator(ImageGenerator):
    """Adapter for OpenAI DALL-E image generation."""

    def __init__(self, api_key: str, model: str = "dall-e-3") -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = "https://api.openai.com/v1"

    async def generate(self, request: GenerationRequest) -> list[GeneratedImage]:
        prompt = self._build_sticker_prompt(request)
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self._base_url}/images/generations",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "prompt": prompt,
                    "n": request.num_images,
                    "size": f"{request.width}x{request.height}",
                    "response_format": "b64_json",
                },
            )
            response.raise_for_status()
            data = response.json()

        results = []
        for item in data["data"]:
            image_bytes = base64.b64decode(item["b64_json"])
            results.append(GeneratedImage(
                data=image_bytes,
                width=request.width,
                height=request.height,
                provider="dall-e",
                metadata={"revised_prompt": item.get("revised_prompt", "")},
            ))
        return results

    def _build_sticker_prompt(self, request: GenerationRequest) -> str:
        style_modifiers = STYLE_PROMPT_MODIFIERS.get(request.style, "")
        return f"{request.prompt}. {style_modifiers}"

    async def check_health(self) -> bool:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self._base_url}/models",
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
            return response.status_code == 200
```

**Stable Diffusion Adapter** (local or API-based):

```python
class StableDiffusionGenerator(ImageGenerator):
    """Adapter for Stable Diffusion (via local Automatic1111 or Stability AI API)."""

    def __init__(self, base_url: str, api_key: str | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    async def generate(self, request: GenerationRequest) -> list[GeneratedImage]:
        prompt = self._build_sticker_prompt(request)
        headers = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload = {
            "prompt": prompt,
            "negative_prompt": request.negative_prompt or DEFAULT_NEGATIVE_PROMPT,
            "width": request.width,
            "height": request.height,
            "num_inference_steps": 30,
            "guidance_scale": 7.5,
            "batch_size": request.num_images,
        }
        if request.seed is not None:
            payload["seed"] = request.seed

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self._base_url}/sdapi/v1/txt2img",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        results = []
        for img_b64 in data["images"]:
            image_bytes = base64.b64decode(img_b64)
            results.append(GeneratedImage(
                data=image_bytes,
                width=request.width,
                height=request.height,
                provider="stable-diffusion",
                seed=data.get("parameters", {}).get("seed"),
            ))
        return results

    def _build_sticker_prompt(self, request: GenerationRequest) -> str:
        style_modifiers = STYLE_PROMPT_MODIFIERS.get(request.style, "")
        return f"{request.prompt}, {style_modifiers}"

    async def check_health(self) -> bool:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self._base_url}/sdapi/v1/options")
            return response.status_code == 200

DEFAULT_NEGATIVE_PROMPT = (
    "blurry, low quality, watermark, signature, text, deformed, "
    "ugly, duplicate, morbid, mutilated, extra fingers, extra limbs"
)
```

**Style Prompt Modifiers**:

```python
STYLE_PROMPT_MODIFIERS: dict[str, str] = {
    "sticker": (
        "die-cut sticker design, white outline border, flat illustration style, "
        "vibrant colors, simple clean background, high contrast, vector art feel"
    ),
    "chibi": (
        "chibi anime style, cute proportions, large head small body, expressive eyes, "
        "kawaii aesthetic, pastel colors, clean linework, sticker-ready"
    ),
    "funko": (
        "Funko Pop vinyl figure style, large round head, small body, black bead eyes, "
        "no mouth or small simple mouth, glossy plastic look, collectible figure"
    ),
    "pixel-art": (
        "pixel art style, 32x32 grid snapped, limited color palette, retro game aesthetic, "
        "crisp pixel edges, no anti-aliasing, nostalgic 8-bit feel"
    ),
    "cartoon": (
        "cartoon illustration, bold outlines, cel-shaded, bright saturated colors, "
        "expressive character, clean vector style, animation-ready"
    ),
    "emoji": (
        "emoji style, simple geometric shapes, flat design, universal expression, "
        "circular framing, high readability at small sizes, bold colors"
    ),
    "watercolor": (
        "watercolor painting style, soft edges, translucent color washes, "
        "artistic texture, hand-painted feel, organic shapes"
    ),
}
```

**Prompt Engineering Tips for Sticker Generation**:

- Always include "sticker design" or "die-cut sticker" to signal the intended format
- Specify "transparent background" or "white background" explicitly for clean extraction
- Add "no text" to the negative prompt unless the sticker intentionally contains words
- Use "centered composition" to keep the subject within the sticker boundary
- For animated sequences, prompt for consistent character design across frames by specifying "character sheet" or "expression sheet" styles
- Include the target emotion or action clearly: "waving hello", "laughing", "thumbs up"
