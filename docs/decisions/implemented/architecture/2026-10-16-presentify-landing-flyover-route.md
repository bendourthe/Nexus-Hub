# Decision: The landing-page fly-over film ships as an opt-in /presentify route

Status: implemented - `/presentify --flyover <url>` renders a live landing page as a 14.5-second 3D fly-over MP4, owned by `references/landing-flyover.md` in `document-to-interactive-html`, the one presentify output that is not an HTML file.

## Problem

The maintainer had a detailed creative prompt for a 3D fly-over film of a landing page (a continuous camera gliding down the page, rising overhead, and diving into the hero, which lands as a card under a two-line title), and the first production run of it on 2026-10-15 needed a page capture, a WebGL2 scene, a GPU render driver, an optical-flow check, and an audio mux. As a prompt alone, each run re-derives that pipeline from scratch, and most of the first run's time went to problems the prompt does not cover: animated diagrams capturing blank, timing that assumed a shorter page, shadows that read as halos on a dark page, a mip-level edge smear, and a motion check that misread flat regions. The harness had no home for a rendered video: the parked v4.22.1 branch P1 designs a separate code-rendered video skill, and `presentify` bans sibling `.mp4` files beside its HTML.

## Decision

The fly-over is a route of `/presentify`, selected with `--flyover <url>` and owned by `references/landing-flyover.md` in `catalog/skills/specialized-domains/document-to-interactive-html/`. The reference keeps the maintainer's brief as the canonical spec (ASCII-transliterated, with harness-neutral wording in one gotcha), and adds a role mapping for pages that lack the brief's photos or testimonial, the binding adaptations from the first run, and a checklist.

The route ships five scripts and a scene. `flyover_capture.py` probes a page and captures it with `prefers-reduced-motion: reduce`, locked, with the lifted pieces hidden and each piece alone on transparency. `assets/flyover/` holds the WebGL2 renderer and the pure camera curves, exposing scene contract `flyover-scene/1` (`window.DURATION`, `async window.seek(t)`). `flyover_render.py` serves the run folder on loopback, aborts any other request, runs the analytic curve check, and renders stills, a preview, and the final H.264 film. `flyover_motion_check.py` fits the page plane's homography per frame and fails a dip in the glide or a zoom-in. `flyover_audio.py` lands a track's gap-then-hit on the card landing at about -14 LUFS. `flyover_common.py` holds tool detection, safe ffmpeg arguments, caps, and the loopback server.

The film is the one presentify deliverable that is not an HTML file. The single-file contract and the sibling-file ban still bind every HTML output: the film is never embedded in or shipped beside one. The route adopts the parked P1 findings that apply to it: render-time network isolation in layers, a loopback-rooted server with no sandbox-weakening flags, ffmpeg run without a shell with absolute `file:` inputs, `-nostdin`, a protocol whitelist, a forced demuxer for user audio, drained stderr and timeouts, resource caps with no partial output, and browser and ffmpeg detected, never downloaded at render time.

## Alternatives considered

**A new code-rendered video skill with a thin `/film` command.** Recommended in the design discussion because it matches the parked P1 design, where one video owner serves later consumers such as `/visualize animate`. The maintainer chose the presentify route instead. The fly-over fits presentify's purpose of presenting an existing artifact (the user's own page), and the route adds no skill or command, so the catalog stays at 340 skills and 21 commands. A later P1 plan can still extract the render driver into a shared owner; the scene contract is versioned so that move does not break the scene.

**Fold it into `/visualize`.** Rejected: `inline-visualization` exists to choose the smallest script-free output and never installs dependencies or touches the network, the opposite of a GPU render pipeline.

**Keep it as a copy-paste prompt.** Rejected: every run would rebuild the pipeline and rediscover the same failures, which is the cost the first run paid.

**Node scripts copied from the first run.** Rejected: the validators do not scan `.mjs`, and a Node script inside a skill folder cannot resolve its Playwright dependency from the user's project. Python Playwright is the toolchain `ensure_render_env.py` already probes for this skill.

**Bundle the two title fonts as binary assets.** Rejected for now: fetching them at capture time, the step that is networked anyway, keeps font binaries out of the repository while the render stays offline. A missing font falls back to system fonts with a finding from `check`.

## Consequences

- `presentify` gains one opt-in route and no new skill or command, so catalog counts, registries, and installers are unchanged; both installers already copy the skill tree recursively.
- The sibling-file rationalization still holds for HTML outputs; SKILL.md's Step 10 and the reference state the exception for the film only.
- The route needs a GPU-capable browser and ffmpeg on the user's machine and an agent that can run code locally; without either it stops with an install hint or offers only a live preview.
- Browser-dependent tests route through the `render_gate` fixture; a full render is not part of CI, because it needs a GPU. The curve self-check and the scene contract are tested in a headless browser when one is present.
- Parked branch P1 remains open for the shared video owner, presentify deck export, and `/visualize animate`; when it lands, the fly-over's render driver is its first candidate to move.
