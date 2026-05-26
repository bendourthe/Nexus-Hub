# Example: Multimodal Input

Feed images, PDFs, or audio into an agent turn alongside text. There are two ingestion shapes: a filesystem path that the SDK resolves, and in-memory bytes you wrap explicitly.

## From a file path

```python
import asyncio
from google.antigravity import Agent, LocalAgentConfig, Image


async def main() -> None:
    config = LocalAgentConfig(model="gemini-3.5-flash")
    async with Agent(config) as agent:
        chart = Image.from_file("reports/q3-revenue.png")
        reply = await agent.chat(["Does this chart match a 12% YoY growth claim?", chart])
        print(reply.text)


if __name__ == "__main__":
    asyncio.run(main())
```

## From in-memory bytes

```python
from google.antigravity import Image

with open("scan.png", "rb") as fh:
    raw = fh.read()

image = Image(data=raw, mime_type="image/png", description="A scanned invoice")
reply = await agent.chat(["Extract the total amount due.", image])
```

## What to notice

- A turn input can be a list that interleaves strings and content objects in one `agent.chat(...)` call.
- `Image.from_file(path)` auto-resolves the MIME type; the in-memory shape requires you to pass `mime_type` explicitly.
- The same pattern extends to other media families (PDFs/documents, audio); which families are supported depends on the configured model backend, so confirm support for your model before relying on it.
- This is about agent **input**. Scoring or evaluating agent **output** is a different concern (the `ai-output-evaluation` skill).

## Use cases

- Analyzing a chart against a written claim.
- Multi-document question answering over PDFs.
- Image-plus-text review (for example, a UI screenshot against an accessibility checklist).

## Related

- The `ai-agent-development` skill's `multimodal-ingestion.md` reference -- the pattern in general terms.
- Back to the skill: [../../SKILL.md](../../SKILL.md).
