# Prompting Profile: gemini-robotics-er-2-preview

**Platform**: gemini
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gemini-robotics-er-2-preview"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Gemini Robotics ER 2 Preview (gemini-robotics-er-2-preview) takes text, image, video and audio input and returns text only, with a 131,072 input token limit and a 65,536 output token limit; the Live API is not supported on this endpoint (use gemini-robotics-er-2-streaming-preview for real-time streaming). | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-robotics-er-2-preview) |
| On gemini-robotics-er-2-preview the supported features are caching, code execution, computer use, file search, function calling, Google Maps grounding, Search grounding, structured outputs, thinking and URL context; the Batch API is supported, while flex and priority inference are not. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-robotics-er-2-preview) |
| Migrate from gemini-robotics-er-1.6-preview (shut down) by replacing the model string with gemini-robotics-er-2-preview (standard) or gemini-robotics-er-2-streaming-preview (real-time Live API streaming). | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/robotics-overview) |
| For spatial outputs, ask for JSON and state the schema in the prompt; points are returned as y, x pairs (y first) normalized to 0-1000, and bounding boxes use separate keys label, y, x, y2, x2 also normalized to 0-1000. Cap result counts in the prompt, for example 'Point to no more than 10 items in the image.' | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/robotics-spatial) |
| To use agentic vision, enable code execution with tools=[{"type": "code_execution"}] and ask explicitly in the prompt for the behavior wanted, e.g. 'Please Zoom and crop the image for a clearer view', and, if an edited image is needed, 'You must return the final image to the API caller.' | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/robotics-agentic) |
| To enforce strict JSON output, state the format in the prompt and add a system_instruction such as 'Be precise. When JSON is requested, reply with ONLY that JSON (no preface, no code block).' | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/robotics-agentic) |
| For task orchestration, declare each robot tool with type, name, description and a parameters object whose parameter descriptions carry behavioral guidance; pass the tools list on every interactions.create call including follow-ups; loop by executing each function_call step, returning a function_result with call_id set to the step id and previous_interaction_id set to the prior interaction, and cap iterations (the example uses max_steps = 15). | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/robotics-orchestration) |
| In orchestration prompts, state the coordinate frame and origin in the user text, ask the model to locate objects and compute coordinates before acting, and leave sequencing to the model with an instruction like 'Call the appropriate sequence of functions to complete this operation.' | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/robotics-orchestration) |
| Best practices: use plain natural language and try synonyms if a term fails; crop or zoom on small or unclear objects; split complex tasks into one prompt per step; for high-precision tasks query several times and average spatial outputs to reduce variance. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/robotics-overview) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
