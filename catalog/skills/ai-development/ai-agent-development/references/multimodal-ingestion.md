# Agent Multimodal Ingestion

How an agent takes non-text input (images, PDFs, audio, raw bytes) into a turn. This is about agent **input**; judging the quality of agent **output** is a separate concern covered by `developer-experience/ai-output-evaluation`.

## Why multimodal at the agent layer

A multimodal model can read a chart, a scanned document, or an audio clip directly. Pushing that content through the agent loop (rather than pre-transcribing it to text) preserves detail the model can reason over: layout, color, handwriting, tone. The agent layer is where the content object is assembled and attached to a turn.

## Two ingestion shapes

There are two common shapes for attaching content to a turn:

- **Direct constructor (in-memory bytes)**. When you already hold the bytes (a generated image, a downloaded file, a buffer from a request), wrap them in a content object explicitly. An image content class typically takes raw `data` (bytes), a `mime_type` (for example `image/png`), and an optional `description`. You supply the MIME type because raw bytes carry none.
- **Filesystem-path shortcut**. When the content is a file on disk, a `from_file(path)` style constructor reads the bytes and infers the MIME type from the extension, so you pass only the path.

Prefer the path shortcut for files; use the direct constructor for content you generate or receive in memory.

## Supported media families

Mainstream multimodal agents accept several families, with backend-dependent support:

- **Images** -- PNG, JPEG, WebP, and similar. The most broadly supported family.
- **PDFs / documents** -- multi-page documents, read as a unit.
- **Audio** -- clips for transcription or content analysis.
- **Video** -- the least uniformly supported; confirm before relying on it.

Which families a given turn can carry depends on the configured model backend. Confirm support for your specific model rather than assuming; an unsupported family is a turn-time error, not a load-time one.

## Mixed prompt lists

The key ergonomic pattern is the mixed prompt list: a single turn input that interleaves strings and content objects, passed as a list to the agent's chat call. For example, a list of `["Does this chart support the claim of 12% growth?", chart_image]` sends instruction and image together so the model reasons over both in one turn. Order is preserved, so you can sandwich an image between a setup sentence and a question.

## Use cases

- Analyzing a chart or diagram against a written claim or specification.
- Multi-document question answering over a set of PDFs.
- Image-plus-text review, such as checking a UI screenshot against an accessibility checklist or a security audit rubric.

## Related

- [google-antigravity-sdk multimodal example](../../google-antigravity-sdk/references/examples/multimodal.md) -- a concrete reference implementation of both ingestion shapes and the mixed prompt list.
- [pdf-document-generation SKILL.md](../../../specialized-domains/pdf-document-generation/SKILL.md) -- generating the documents an agent might later ingest.
- [docx-generation SKILL.md](../../../specialized-domains/docx-generation/SKILL.md) -- Word-document generation.
- [pptx-generation SKILL.md](../../../specialized-domains/pptx-generation/SKILL.md) -- presentation generation.
- [ai-agent-development SKILL.md](../SKILL.md) -- the parent skill.
