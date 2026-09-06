# Session History - v3.16.5 Phase 6: cinematic scroll-scrub

**Date**: 2026-08-11
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.5-presentify-visual-overhaul.md](../../plans/v3.16.5-presentify-visual-overhaul.md)
**Phase**: 6 of 7 - the last feature phase; Phase 7 is the terminal gate
**Branch**: `feat/v3.16.5-presentify-visual-overhaul` (worktree)
**Model**: Opus 5. The plan recommends **frontier** at high effort; the maintainer had chosen Opus 5 for the three prior tier deltas, so that standing preference was applied rather than asking a fourth time.
**Prerequisites**: Phases 3 (the render loop that QAs a cinematic build) and 4 (the intake it wires into). Both met.
**Absorbs**: the former v3.20.1 scroll-scrub plan, in full.

## Sub-tasks completed

### 6.1 - The protocol

`references/scroll-scrub.md`, seven sections: when cinematic applies, job fidelity, the size / cost gate, the asset boundary, seam and pacing, the stills-only fallback, and accessibility. Wired into `SKILL.md` with a Step 6 bullet, four rationalization rows, a Verification item, and two Bundled Resources entries.

### 6.2 - The engine

`assets/scroll-scrub-engine.js`, ~340 lines of vanilla JS: `data:` / Blob clip loading, seam crossfade, per-section `scroll` + `linger` remapping, scroll coalesced onto one animation frame with superseded seeks dropped, iOS muted priming on first touch, and a stills-only path. Zero dependencies, `ss-` namespaced, styles injected into the caller's container. `references/interactive-features.md` gained CINEMATIC in the interactivity spectrum and a scrollytelling-catalog entry.

### 6.3 - Intake, decisions, and closure

`--interactivity cinematic` on both surfaces, the menu's fourth option with its one-line description, and the rich-level propose-then-confirm amendment. The knockout helper was DEFERRED with a reason (DF-3). The reverse-engineering matrix row was added, classifying the engine `re-full` and the protocol `skill-native`.

### 6.4 - Verification

Vendor-name gate, one cinematic stills-only build scored and rendered at both motion preferences, full suite, validators.

## The decisions that shaped it

- **Stills-only is the base mode; video is the enhancement.** Under `prefers-reduced-motion: reduce` the engine creates no video element at all - not created-and-paused, not created-muted: not created. A paused video still downloads and still decodes a frame, so only absence is a guarantee. The direction matters: a reduced-motion path added afterwards is the one that regresses, and this one is verified by a browser rather than by reading code.
- **The size gate is numeric and comes first.** Base64 inflates binary by about a third, so a 2 MB clip lands as ~2.7 MB of markup; past roughly 15-20 MB the single-file guarantee becomes a delivery problem rather than a feature. Stating clip count, projected size, key requirements, and QA-depth cost before building is what keeps "cinematic" from quietly meaning "20 MB".
- **Under `rich` it is proposed, priced, and confirmed.** A reader who asked for `rich` did not agree to a large file.
- **The upstream pipeline was dropped whole, not adapted.** Hosted generation is the Hard-No and applies to a vendor CLI exactly as to an API, so a cinematic build neither calls one nor prints one for the user to run. Also not adopted: a competing slash command, the multi-file sibling asset layout, the blank brand-industry interview, and the paid portrait chain. What was extracted is the local engine mechanics and the presentation grammar.

## The plan contradicted itself, and a grep caught it

Recorded as DF-4 because the near-miss is the instructive part.

Sub-task 6.3 says: *state explicitly there is no separate `/scroll-world` command*. Sub-task 6.4 says: *grep `catalog/` for `Monid|Higgsfield|Seedance|scroll-world` - expect zero*. Following 6.3 literally makes 6.4 fail, by naming the upstream repository in a file the installer copies to users.

The first draft of the protocol did name it. The AGENTS.md Reverse-Engineering Attribution Rule is the binding authority, so 6.4's gate wins and 6.3's intent was satisfied without the name: "There is no separate cinematic command and no separate cinematic skill - no rival slash command exists or should be created for this." A parametrized test now guards the engine, the protocol, `interactive-features.md`, `SKILL.md`, and the command file, so the next helpful sentence cannot reintroduce it.

Worth noting that the initial grep also returned 57 apparent hits, 56 of which were `emons` matching "d**emons**trate". A gate with no word boundaries is a gate nobody reads.

## What the cinematic verification build found

Sub-task 6.4 asks for one cinematic build through the render loop. It surfaced three things, which is the entire argument for the instruction:

1. **BG-3, a real checker bug**: `image-sizing` treated `"data:image" in html` as evidence of a figure, so it demanded the Phase 2 caps on any page containing an embedded image anywhere - including inside an inline `<script>` config. A cinematic page keeps its stills in that config and builds its layers at runtime, so the static file has no `<img>` and there is no figure box to cap. **Every cinematic build would have failed** for a missing cap on a figure it does not have. Fixed by requiring a real figure box; a stage layer is separately exempt on its merits, since it is a decorative `aria-hidden` backdrop for which `object-fit: cover` is correct and `contain` would letterbox the stage.
2. **A missing canvas var** in my verification page - it claimed `data-aspect="full"` without declaring `--page-max`. My page's bug, correctly caught.
3. **A horizontal overflow at 2560px** that turned out to be mine too: the page set `width:100%` AND `padding-inline` without `box-sizing: border-box`, and the default `content-box` adds padding on top of the 100%. The engine's stage clips correctly (`documentElement.scrollWidth` matched the viewport in an isolated repro), so my first assertion was wrong before the page was. Because this produces a scrollbar rather than an obviously broken layout, rule 1 of the typography contract now names the footgun in one line.

## Verification evidence

| Check | Result |
|---|---|
| New cinematic suite | 17 passed |
| Full presentify surface | 634 passed, 0 skipped |
| Lint (CI's target) | `ruff check --ignore RUF100` clean |
| Validators | all ten pass; orphan-bundle audit 0 warnings; SKILL.md 292 lines (cap 800) |
| Vendor-name gate | 0 across `catalog/` and `templates/`; attribution present only in the matrix |
| Cinematic build, scored | PASS, 0 high-severity across all 13 structural criteria |
| Cinematic build, rendered at 2560x1300 | under BOTH motion preferences: 0 video elements, 3 stills, no horizontal overflow, `aria-hidden` stage, 0 off-host requests |
| Canonical calibration fixture | unaffected, still PASS |

## Deviations from the plan

- **DF-4**: 6.3's literal instruction was not followed, because it contradicts 6.4 and the Attribution Rule. Its intent was satisfied without the vendor name.
- **DF-3**: the knockout helper is deferred rather than added, which is one of the two outcomes 6.3 explicitly permits. No call site exists, and the scope-fit gate declines a module justified only by a hypothetical extension.
- **The matrix section preamble was widened**, because it described the skill-native rows as "pure Markdown skills with zero code" and this adoption also ships a browser asset. Widened to describe that accurately rather than left to contradict the row beneath it.

## Next steps

**Phase 7, the terminal gate.** It carries the largest reconciliation load of the plan: the mandatory refactor pass, CI/CD, and a known-gaps set that now spans MT-1's location half, BG-E1, NI-4, NI-5, DF-2, DF-3, DF-4, WN-3, and WN-4 - plus the calibration fixture's final home, which every phase since Phase 1 has deferred to it. It then hands off to `/update release`; it must not tag or push.
