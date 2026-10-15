---
name: gif-sticker-maker
description: "Animated GIF and sticker creation expertise using AI image generation, video processing, and frame animation. Use when creating animated stickers, converting images to GIFs, building avatar generators, or automating visual content pipelines."
summary_l0: "Create animated GIFs and stickers with AI generation, video processing, and frame animation"
overview_l1: "This skill provides end-to-end expertise for creating animated GIFs and stickers using AI image generation, video processing, and programmatic frame animation. Use it when generating animated stickers from text prompts, converting video clips to optimized GIFs, building sprite sheet animations, creating avatar generators with expression cycles, automating visual content pipelines for chat platforms, or applying animation effects like bounce, pulse, rotate, and fade. Key capabilities include AI image generation integration, Python Pillow GIF assembly with palette optimization and transparency, ffmpeg video-to-GIF conversion with two-pass palette generation, animation techniques (tweening, easing, keyframe interpolation), sticker formatting for Telegram, Discord, Slack, and WhatsApp, and batch processing with file-size optimization. The expected output is production-ready animated GIFs and stickers that meet platform size and format requirements. Trigger phrases: animated GIF, sticker maker, GIF creation, sticker generator, sprite animation, video to GIF, avatar animation, GIF optimization, sticker pack, Pillow GIF, ffmpeg GIF."
---

# GIF and Sticker Maker

Structured guidance for creating animated GIFs and stickers using AI image generation, video processing, and programmatic frame animation. Covers the full pipeline from image generation through animation assembly to platform-specific optimization.

## When to Use This Skill

Use this skill for:

- Generating animated stickers from text prompts using AI image providers
- Converting video clips or screen recordings into optimized GIFs
- Building sprite sheet animations with tweening and easing
- Creating avatar generators with animated expression cycles
- Automating sticker pack creation for Telegram, Discord, Slack, or WhatsApp
- Applying animation effects (bounce, pulse, rotate, fade) to static images
- Optimizing GIF file sizes while preserving visual quality

**Trigger phrases**: "animated GIF", "sticker maker", "GIF creation", "sticker generator", "sprite animation", "video to GIF", "avatar animation", "animated emoji", "GIF optimization", "sticker pack", "frame animation", "Pillow GIF", "ffmpeg GIF", "animated sticker"

## What This Skill Does

Provides GIF and sticker creation patterns including:

- **Pipeline Architecture**: Image generation, frame assembly, GIF encoding, and optimization stages
- **AI Image Generation**: Provider-agnostic integration with DALL-E, Stable Diffusion, and other APIs
- **Pillow GIF Assembly**: Frame generation, palette optimization, duration control, looping, transparency
- **ffmpeg Conversion**: Video-to-GIF with two-pass palette generation, scaling, and frame rate control
- **Animation Techniques**: Sprite sheets, tweening, easing functions, keyframe interpolation, bounce/pulse/rotate effects
- **Sticker Formatting**: Transparent backgrounds, outline strokes, caption overlays, platform-specific sizing
- **Batch Processing**: Parallel generation, file size targets, color reduction, dithering, output validation

## Instructions

### Step 1: Pipeline Architecture and Tool Selection

Full walkthrough: [step-1-pipeline-architecture-and-tool-selection.md](references/step-1-pipeline-architecture-and-tool-selection.md) (load this step when you reach it).

### Step 2: AI Image Generation Integration

Full walkthrough: [step-2-ai-image-generation-integration.md](references/step-2-ai-image-generation-integration.md) (load this step when you reach it).

### Step 3: Python Pillow GIF Creation

Full walkthrough: [step-3-python-pillow-gif-creation.md](references/step-3-python-pillow-gif-creation.md) (load this step when you reach it).

### Step 4: ffmpeg Video-to-GIF Pipeline

Full walkthrough: [step-4-ffmpeg-video-to-gif-pipeline.md](references/step-4-ffmpeg-video-to-gif-pipeline.md) (load this step when you reach it).

### Step 5: Animation Techniques

Full walkthrough: [step-5-animation-techniques.md](references/step-5-animation-techniques.md) (load this step when you reach it).

### Step 6: Sticker-Specific Patterns

Full walkthrough: [step-6-sticker-specific-patterns.md](references/step-6-sticker-specific-patterns.md) (load this step when you reach it).

### Step 7: Batch Processing and Optimization

Full walkthrough: [step-7-batch-processing-and-optimization.md](references/step-7-batch-processing-and-optimization.md) (load this step when you reach it).

## Best Practices

- **Two-pass palette generation**: Always use ffmpeg's palettegen/paletteuse pipeline for video-to-GIF. Single-pass produces visibly worse color reproduction
- **Global palette for frame sequences**: When assembling GIFs from individually generated frames, compute a shared palette across all frames to prevent inter-frame color flickering
- **Transparency via disposal mode**: Set `disposal=2` (restore to background) when creating transparent GIFs; otherwise transparent regions accumulate artifacts from previous frames
- **Size budget first**: Know the platform's file size limit before generating. Working backward from 256 KB is easier than trying to compress a 2 MB GIF after the fact
- **Consistent character design**: When generating multiple frames with AI, include "character sheet" or "model sheet" in the prompt and use seeds or reference images to maintain visual consistency
- **Easing makes motion feel natural**: Never use linear interpolation for character animations. Ease-out for arrivals, ease-in for departures, ease-in-out for continuous loops
- **Test at actual display size**: Stickers that look good at 512x512 may lose important detail when displayed at 64x64 in a chat bubble
- **Looping matters**: Design animations to loop seamlessly. Use ping-pong (forward then reverse) for simple motions; match the first and last frame positions for complex animations
- **Batch with concurrency limits**: AI image generation APIs have rate limits. Use semaphores to control concurrent requests and implement exponential backoff for retries
- **Validate every output**: Automatically check file size, dimensions, frame count, and duration against platform requirements before delivering stickers

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "A single-pass ffmpeg conversion is good enough" | Single-pass GIF conversion uses a generic palette that bands gradients and bloats the file. The documented two-pass palettegen/paletteuse flow is what produces a clean palette at a fraction of the size. |
| "It loops fine in my preview, ship the sticker" | A desktop preview hides the green fringe on transparency and the visible jump at the loop seam that show up at the platform's display size. Check the alpha edges and the first/last frame match before delivery. |
| "The GIF is only a bit over the platform limit" | Telegram, Discord, Slack, and WhatsApp hard-reject stickers over their size or dimension cap, so "a bit over" means the upload fails silently. Validate against the specific platform's limit, not a guess. |
| "More frames always look smoother" | Past the platform's frame budget, extra frames just inflate the file without perceptible smoothness gains and push it over the size cap. Tune frame count to the motion, then optimize the palette. |

## Verification

- [ ] The output GIF file size is within the target platform's documented limit
- [ ] Output dimensions match the platform's recommended sticker size
- [ ] The animation loops with no visible jump between the last and first frame
- [ ] Transparent backgrounds render with no green fringe or matte artifacts
- [ ] The color palette was generated with the two-pass ffmpeg flow (palettegen + paletteuse)
- [ ] Each batch output is validated against the destination platform's format requirements

## Related Skills

- [[creative-generation]] -- image prompt engineering and creative ideation for the source frames
- [[python-expert]] -- Python patterns for the Pillow image-processing pipeline
- [[containerization]] -- Dockerizing the pipeline with ffmpeg and system dependencies
- [[async-patterns]] -- concurrency patterns for batch AI generation
- [[code-optimizer]] -- performance optimization for frame processing

---

**Version**: 1.0.0
**Last Updated**: March 2026

### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets are not met, repeat the specific implementation steps with improved context.
