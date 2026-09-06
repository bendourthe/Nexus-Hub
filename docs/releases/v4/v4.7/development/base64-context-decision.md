# Decision Note - Does the base64 asset pipeline return encoded data into model context?

**Plan**: `docs/releases/v4/v4.7/plans/v4.7.0-adoption-model-behavior-and-distribution-integrity.md`, sub-task 3.2 (T012)
**Date**: 2026-09-05
**Read**: `catalog/skills/specialized-domains/document-to-interactive-html/SKILL.md` (steps 3 to 9), `references/extraction-runbook.md`, `references/content-model.md`, `scripts/extract_content.py`, `scripts/build_presentation.py`, `scripts/visual_qa_score.py`

## Outcome

**Option (b) holds**: encoded data can return to context on two paths, and both are closed with guidance rather than a pipeline change, so the offline self-contained output guarantee is untouched.

## The asset path, end to end

1. **Read and encode.** `scripts/extract_content.py` reads each raster (`base64.b64encode` at lines 275 and 2148) and writes an `image` block `{ "type": "image", "data_uri": "data:image/<subtype>;base64,...", ... }` into `model.json` (`references/content-model.md` line 85 to 87; `references/extraction-runbook.md` line 64). The encoding happens inside a script; nothing enters context here.
2. **Write.** `scripts/build_presentation.py` (the optional plain baseline, Step 7) reads `model.json` and the template (`model_path.open` line 707, `read_text` line 722) and writes the URIs into the HTML. Script only.
3. **Verify.** `scripts/visual_qa_score.py` reads the generated `.html` (`Path(path).read_text` line 1678) to score structure. Script only. Step 9's render loop reads the page in a browser and produces screenshots; screenshots are what the agent looks at.

## The two paths that DO bring payloads into context

- **Authoring (Step 6, the PRIMARY path).** The skill tells the agent to author the page "from the enriched content model". An agent that reads `model.json` with a file-read tool pulls every `data_uri` into its context, and an agent that pastes those URIs into the authored page emits them through its output. This is exactly the documented trigger class: a tool (the extractor) returning base64 into model context.
- **Verification (Step 8).** "grep for external `http(s)` / `cdn` references" is safe, but an agent that reads the generated `.html` wholesale to check it re-ingests every payload it just wrote.

Neither path is required by the design. The extractor already isolates payloads in one field, and the builder already copies them programmatically.

## What changes

Guidance in the skill, no code: Step 3 gains a BINARY rule to inspect the model through a projection that replaces each `data_uri` with its MIME type and length, to refer to images by section and block index, to copy URIs into the output with a script rather than through the conversation, and never to read the generated `.html` back wholesale (Step 8 uses `grep` and the bundled scripts; Step 9 uses screenshots). Two Verification items pin it. The offline guarantee (every asset embedded, zero external requests) is unchanged, because it is satisfied by embedding, not by the agent reading what was embedded.

## Why not option (a) or (c)

Not (a): the write-only claim holds for the scripts but not for the agent's own reads, and the skill's primary path is agent-authored. Not (c): the paths are visible in the skill text and the scripts; no instrumentation was needed.
