# Presentation intake contract

This reference owns presentation option resolution for `/presentify`, direct HTML-skill calls, and saved handbook maintenance. The skill body owns source extraction, design direction, page verbosity, imagery consent and visual QA; `dual-view-handbooks.md` owns the two-view output and coverage contract. `scripts/resolve_presentation.py` returns resolved values, provenance, pending questions and compatibility notes without reading source documents or generating an artifact.

## Resolve once, retain through retries

Resolve each axis from current explicit instructions/flags, then current-session answers, then approved project settings. Ask only what remains unknown. Preserve supplied references, content intent, source coverage, motion, imagery boundaries, brand tokens, reading theme and logical-slide budget in the retained design record. Unrelated remembered preferences never authorize new imagery or network use. Automated maintenance supplies saved policies and stays local/offline.

Call the resolver with a JSON object containing `explicit`, `session` and `project` option objects. Keys use underscores, for example `presentation_theme`. Its CLI takes `--input <json-path>` and optional `--non-interactive`; output is JSON on stdout. `pending` means questions remain, not permission to generate. `conflict` is a nonzero exit requiring resolution of the named contradiction. Keep the result and only ask its pending axes as part of the existing intake. This is deterministic routing evidence; the native host must still load and follow the skill.

## Question batches

The initial batch contains unresolved design direction, scrolling canvas, interactivity, additional imagery and inclusion. Design direction remains Corporate & Professional, Creative & Expressive, Technical & Precise, Surprise me or free text. The canvas choices are Full-width scrolling site, Standard scrolling column, Portrait scrolling canvas and free text. There is no separate deck output-format choice.

| Axis | Question | Choices |
|---|---|---|
| Inclusion | Include Presentation Mode on the title page and global top menu? | Yes (recommended); No |
| Theme, only after Yes | Which theme should presentation mode use? | Light theme only; Dark theme only; Random light/dark mix (recommended) |
| Depth, in the same conditional follow-up | How much of the main page should presentation mode cover? | Concise and compact; Balanced (recommended); Deep dive: the entire main-page content |

Theme and depth are one conditional batch, with supplied axes removed. A missing-depth-only follow-up asks only depth; missing-theme-only asks only theme. Changing Yes to No cancels pending theme/depth questions and deck authoring. An unanswered interactive question never becomes Yes through elapsed time.

The content-derived Round 2 remains after extraction: three named color schemes plus Other, each with a cited content signal and 5-swatch preview, together with the independent page-verbosity choice. `--theme` or approved `tokens.json` resolves the palette; `--verbosity` resolves page coverage. Retain already answered choices rather than restarting either round.

## Flags, defaults and compatibility

- `--presentation yes|no` binds inclusion. No overrides legacy `--nav slides`, theme and depth flags with a short inapplicable-option note; the reading page is still produced and checked.
- `--presentation-theme light|dark|mixed` and `--presentation-depth concise|balanced|deep-dive` each imply Yes when no explicit inclusion value exists. Each suppresses only its own question. Mixed themes are resolved once during authoring with a saved seed and assignment per stable slide ID; build/check/Replay/navigation never reroll them. `save_themes` in the resolver preserves prior ID assignments and rejects an inconsistent saved mix rather than silently restyling it.
- Legacy `--nav slides`, `using slide navigation`, and `as slides` are inclusion aliases with a migration note. Legacy `--nav scroll` only binds reading start, not No. Existing deep links can open an enabled deck without requesting fullscreen. Existing single-mode files remain valid legacy inputs.
- `--layout full|standard|portrait|description` controls only the scrolling canvas. `--mode auto|deck|report|compile` still describes source organization. Neither changes presentation depth or its source-slide ceiling.
- `--verbosity distilled|balanced|comprehensive` controls source-to-page coverage. Deck depth controls page-to-deck coverage independently. Explicit complete-source intent binds comprehensive reading and deep-dive presentation; a contradictory current explicit choice must be resolved and recorded. Concise omissions have reasons, balanced maps each major topic, and deep dive maps every substantive unit/state.
- Non-interactive new output defaults to Yes, mixed themes and balanced depth, with page verbosity independently balanced. Approved project settings, including an applicable opt-out, take precedence over defaults. Invalid option values produce a usage note and leave that axis unresolved interactively or use the documented fallback non-interactively; invalid values never silently disable presentation.
- Imagery remains `none|stock|ai|both`, with `procedural` -> `none` and `auto`/`mix` -> `both`. Procedural visuals are the always-on baseline; the old none meant no visuals, while the current none means no additional imagery. Stock/local AI remain opt-in and consent-gated. Every automatic handbook refresh and non-interactive run stays fully offline, without new stock fetches or hosted generation.

## Verify dispatch against output

Persist the resolver result before authoring; copy resolved inclusion/theme/depth to the retained model and generate its explicit storyboard/coverage map. The final DOM, embedded handbook record and scorer must agree. Enabled output has a complete reading page, one deck, two correctly named global entry controls, and every recorded slide/theme. Disabled output has no deck runtime, deck payload or entry controls; the absence guard still runs and remaining deck checks are N/A. Test all nine enabled theme/depth combinations, alias/No precedence, saved-answer retries, complete-source conflicts and page-only output. Static text/dispatch checks are routing evidence only; browser tests and installed native authoring runs supply the separate behavioral evidence.
