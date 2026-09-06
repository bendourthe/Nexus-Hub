# Asset provenance

## Generation mode

The room and harbor were generated with the built-in imagegen tool, without external image services or API calls from the guide. The full prompts below are the final prompt set. Browser canvas then resized the original PNGs and encoded WebP for the existing offline byte budget; no creative image edits were performed during encoding.

## Delivered assets

| Asset | Width | WebP bytes | Purpose |
|---|---:|---:|---|
| [room.webp](room.webp) | 820 | 27,920 | One photographic source for every camera framing |
| [harbor.webp](harbor.webp) | 600 | 26,786 | Detailed diffusion output |
| [booking-before.webp](booking-before.webp) | 480 | 6,608 | Attached application screenshot |
| [booking-after.webp](booking-after.webp) | 480 | 7,750 | Redesigned application image |

Each asset is embedded once in an SVG symbol in the canonical HTML. Repeated room views reference the same symbol. The booking images were rendered from the accompanying authored HTML files at 640 by 380 pixels, then resized and encoded as WebP; they are deliberate UI mockups rather than generated photography. The source HTML and PNG captures are retained alongside the delivery files.

## Room prompt

Create one photorealistic interior architectural photograph, landscape wide aspect 16:9. A sophisticated sunlit lived-in living room seen straight on from its entrance, wide-angle composition covering the entire room from left wall to right wall. Center: sage green fabric sofa with cream linen and rust cushions, low walnut coffee table with art books and ceramic mug on textured cream rug. Left: floor lamp with linen shade, sideboard with framed photographs, large window with sheer curtains, natural green garden outside. Right: oak bookshelf filled with clearly distinct books, framed abstract painting, leather lounge chair, tall indoor plant. Rich realistic materials, woven upholstery, wood grain, subtle shadows, natural daylight, editorial interiors magazine photography, crisp detail, believable perspective, calm warm palette. No people, no text or watermarks, no collage, no diagram, no vector or painted appearance. Keep furniture within the central 80 percent with generous scene details at both edges. This is a single coherent panorama used for a camera pan and gentle push-in; all objects must have realistic stable geometry.

Original generated PNG: `<home>/.codex/generated_images/01a06e2f-e243-7463-8ca5-f0deb66eaca5/exec-36fdf1c9-7c3b-4dac-bfd9-107ff6ac8023.png`.

## Harbor prompt

One photorealistic editorial travel photograph, landscape 16:9. A small elegant red wooden sailboat moored beside a weathered stone quay in a quiet Mediterranean harbor at golden hour, shimmering deep blue and turquoise water, detailed rope rigging and cream sails, terracotta-roofed waterfront buildings climbing a hillside, a few potted olive trees and cafe tables on the quay, distant rugged coastline. Rich realistic wood, sailcloth, stone and water textures, natural cinematic sunlight, photographic depth, believable fine detail. No people close to camera, no readable text, no logos, no watermarks, no border. Not a drawing, not illustration, not 3D low-poly. Intended to demonstrate a diffusion model producing a complex realistic image.

Original generated PNG: `<home>/.codex/generated_images/01a06e2f-e243-7463-8ca5-f0deb66eaca5/exec-b44186be-7859-4b63-a114-aff36fe2bd3f.png`.

## Representation limits

The room sequence illustrates camera framing with a pan and zoom of one photograph; it does not synthesize unseen geometry or simulate a live world model. The four architecture drawings are explanatory sketches, not exact implementations of named providers. The voice quote is the transcript of the illustrated recording, not a second typed request. The images and transcript are static teaching assets, not an active AI service.

## Teaching source

The reinforcement-learning description was checked against [OpenAI: Learning to reason with LLMs](https://openai.com/index/learning-to-reason-with-llms/), which distinguishes learning from training feedback and additional reasoning at inference. The guide retains its existing official sources for diffusion, world models, multimodal models, capability tiers and effort.
