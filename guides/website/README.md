# Nexus-Hub Interactive Guide

This directory holds the public-facing Nexus-Hub guide and the Glow Booth example the Training walkthrough operates on. Everything is self-contained, opens in a browser, and needs no build step. This `README.md` is for maintainers.

## Contents

| Item | What it is |
|---|---|
| `nexus-hub-guide.html` | Canonical interactive guide. One HTML file. The main entry point. |
| `example/training-scenes.json` | Maintainer source of truth for Training scenes. The guide inlines a verified copy. |
| `example/glow-booth/` | Example app the Training mockup reproduces. Open `index.html` from disk. |
| `example/glow-booth-shuffle-reference/` | Local `/compare` target that already has shuffled poses plus sparkle. |
| `glow-booth.zip` | Downloadable bundle learners extract. |
| `example/trivia-quiz/` | Previous example. Stays on disk. Not taught in the published guide. |

The guide is the single home for orientation, installation, Foundations, Training, and Cheatsheets. It remains one self-contained HTML file with no runtime network dependency.

## The interactive guide

`nexus-hub-guide.html` is a single HTML file with zero runtime dependencies. No server, no CDN, no remote fonts, nothing to install.

- **To open:** double-click the file. It opens in any modern browser and works fully offline. GitHub does not render HTML inline, so use Download raw file, then open the download.
- **To share:** send that one file.
- **Primary navigation:** Home, Foundations, Training, Cheatsheets. Installation is not a primary page. GitHub is an icon-only external link. Theme toggles light and dark and persists only those two values under `portfolio-theme`.

URL grammar: `#<page-id>` for pages; `#training/<scene-id>?beat=n` for Training; `#cheatsheets/<stop>` for Cheatsheets sections. Compatibility: `#reference` and `#workflows` rewrite to `#cheatsheets`; `#explore`, `#plan`, `#build`, `#harden`, `#ship`, `#communicate` rewrite to `#cheatsheets/<id>`. `#home/install` scrolls to the Home install block. Unknown page ids rewrite to Home.

## Design system (v4.2.2, refined in v4.2.3)

The design language is fixed in `docs/releases/v4/v4.2/development/guide-rebuild/design-brief.md`. The load-bearing decisions:

- **Fluid width (v4.2.3).** There is no per-text width cap. `.container`'s `--maxw` is the ONLY width constraint in the file: body copy fills the content column at every viewport. A test fails on any `max-width` in `px` or `ch` other than the present-mode stage bound, so a measure cannot creep back in. Headings use `text-wrap: balance` to shape wrapping without imposing one.
- **Copy affordance (v4.2.3).** A labelled button only where the control stands alone in a wide terminal row. Inside an inline `.cmd-cell` the button is bare - no background, no border, no label - because the host chip already draws the container and a chip inside a chip reads as a mistake. The bare variant keeps a 24px hit area, its `aria-label`, the live-region announcement, and an explicit focus ring.
- **Invocation convention (v4.2.3).** `.inv-cmd` renders a slash command in accent, `.inv-arg` its scope in plain ink, `.inv-ph` a placeholder dim italic. Used on Home, in Training's terminal, and in every Cheatsheets example. The `data-copy` payload is always the plain full string, so copy parity survives the split markup.
- **Compact rhythm.** A 4px spacing scale (`--sp-1` to `--sp-8`) with `--sec-pad: 32px` (22px under 720px). Sections are separated by an eyebrow and a heading, not by empty space.
- **Motion vocabulary.** `.reveal` elements fade and rise via one shared IntersectionObserver. Continuous motion (constellation, Foundations pulses) runs only while its scene is on screen. `prefers-reduced-motion` renders a complete static equivalent, never a crushed duration.
- **Themes.** All colors are tokens defined on `:root`, `html[data-theme="dark"]`, and `html[data-theme="light"]`. Every text style in both themes meets WCAG AA contrast, re-verified after every colour change (v4.2.3: 242 sampled styles, 0 below AA).
- **Light-mode brand chip.** In light theme the glow logo mark sits on a rounded dark chip so it reads against the light ground.

## Home

Home is a short orientation, not a catalog dump. It states what Nexus-Hub is, embeds the two canonical install commands behind OS tabs (**Windows first and default**), compares a model-only assistant to a harnessed one, shows the six-step loop, and closes with next steps.

Canonical install constants (must match `tests/guides/test_nexus_hub_guide.py`):

- Windows: `irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1 | iex`
- macOS / Linux: `curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash`

The verify step (`/skills list`, `/commands`) renders as copyable inline cells. wget, flags, and `--workspace` live in a Home disclosure and in Cheatsheets. Do not hardcode skill counts, command counts, or installer versions on Home.

There is no untrusted-origin warning box. It was removed in v4.2.2 along with `isDocumentedGuideOrigin()`; do not reintroduce either.

## Foundations

Foundations is eight scrollytelling scenes, each teaching one concept through a title-plus-subtitle lesson and a hand-authored inline SVG diagram:

1. **What Is a Model** - training precedes platform integration; a later request carries context into processing and a result comes out.
2. **What Is a Token** - one verified sentence split into tokenizer pieces, plus an illustrative image-to-token grid.
3. **What Is Prompt Engineering** - the same non-coding job shown first as a weak request and then with Goal, Material, Done, and Format.
4. **What Is an Agent Platform** - a model operating inside a host loop that can propose actions, observe results, and continue.
5. **Chatbot or Agentic Platform?** - the same request ending as guidance to apply or as checked work completed in the active work surface.
6. **What Is Context** - a finite token budget shown noisy and focused, including what can happen when it fills and why task-matched loading matters.
7. **What Is a Harness** - the model, platform loop and built-in harness, and Nexus-Hub's portable workflow layer shown as distinct nested layers.
8. **What Changes in Practice** - an honest comparison between a saved platform result and the same job with matched procedure, written gate, and durable evidence.

Hard rules: no element pins itself over the content, and there is **no toggle** between the two states - both are always visible, because a selector for something already on screen is noise. Diagram colors come from theme tokens so one markup serves both themes. Do not restore a `type="range"` hero, the station cards, the carousel, or the per-scene number badges (removed in v4.2.3 as a full line carrying no information).

**Conventions added in v4.2.3, enforced by tests:**

- **Without-then-with ordering.** Every comparison in the guide reads the less structured state first and the more structured state second - Foundations scenes 3, 5, 6, and 8, and Home's comparison. Differentiation is carried by colour across the whole lane (amber for the weaker path, accent for the stronger path), not only on the outcome badge.
- **Filled arrowheads.** `.fx-head` draws a closed filled triangle. The earlier open two-line chevron drew a single side and read as half an arrow.
- **Pulse paint order.** SVG has no `z-index`; paint order is document order. Phase 3 diagrams declare connectors first, pulses second, and node groups last, so a pulse remains above its path but behind the boxes it crosses. A test enforces the exact layer sequence.
- **Project-generic teaching language.** Explanatory copy avoids "repo", "repository", "terminal", "git", and "codebase" - a vocabulary test guards the Foundations section. Factual claims stay accurate: the hero still names the AI coding assistants, "paste into Terminal" still says Terminal because you literally do, and Cheatsheets still describes what each command really does.

## Training walkthrough

Training is an eight-step interactive walkthrough (`#nhTraining`, `[data-training-root]`) driven entirely by the scene JSON. Each step composes four things:

1. The step's intent, in second person.
2. **The interactive Glow Booth mockup** - a faithful re-implementation of `example/glow-booth/logic.js`, *including both frozen bugs*. While `booth.fixed` is false, `computeStamps` walks `captured.length - 1` (a perfect set reads 4 of 5) and Restart keeps `lastPose` on stage. Learners click it freely.
3. **The simulated terminal** - the step's command pre-filled with a Run affordance; running shows a brief working line, then reveals the reply. The command is NOT echoed a second time, because the prompt line above already shows it.
4. The artifact card and gate verdict.

Controls (reworked in v4.2.3): Previous, Next, and Restart are icon buttons in a right-aligned cluster BELOW the takeaway, each with an `aria-label`, a `title`, and a visible focus ring. Outline keeps a text label because a glyph does not carry its meaning. ArrowLeft / ArrowRight / Space advance; `f` toggles Present; Escape exits it.

**Present mode** requests fullscreen on the training root and applies a viewport overlay class either way, so a denied or unavailable Fullscreen API still presents as slides. Since v4.2.3 it FILLS the viewport: a full-height flex column where the slide grows to consume the space and the booth and terminal stretch inside it, rather than centring an in-page-sized block in an empty screen.

**Position and progress** read in plain language: `Understand . 1 of 8 . /describe full`. The progress strip is eight labelled loop stages - each names its command, the current one carries `aria-current="step"`, completed ones dim, and clicking one jumps to it. The word "beat" must not appear in the UI; it survives only as the underlying mechanism and in the `?beat=n` URL grammar, which is a compatibility contract.

URL: `#training/<scene-id>?beat=n`. Beat changes use `history.replaceState`. An unknown scene id or an out-of-range beat clamps to the nearest valid step.

Fixture strings are painted with `textContent` / `createElement` only. The Training engine assigns `innerHTML` nowhere, and a test enforces that, so the hostile fixture strings (`<img onerror>`, `</script>`) can never execute.

Eight closed scenes, hard-capped at twelve: `describe`, `review`, `plan`, `implement`, `compare`, `test`, `update`, `presentify`. Do not invent a ninth scene for the follow-on `/implement` after `/compare`; that is the same command with a different plan.

## Cheatsheets

Cheatsheets groups every command under seven **intent-named** sections - Understand and evaluate, Plan the work, Build it, Prove it, Ship and govern, Communicate, Catalog and session. The "Band 1 / Band 2" labels are gone and must not return.

Each command lists **every scope with a one-line description of what that scope does**, plus flags, an alias badge where one applies, and a Training deep link for the eight taught commands. Commands with no scopes say so explicitly.

Since v4.2.3 the scope list is a **single column** (reading across columns was the readability complaint), and every command carries a small terminal captioned "type it like this" showing a real invocation. That terminal reuses the shared `.term` chrome rather than inventing a third terminal style, and the invocation convention colours the command apart from its argument - which is what makes the ordering legible: the scope visibly follows the command instead of floating as a bare token.

A scope shown on the page must exist in that command's own file in `catalog/commands/` - `test_rendered_scopes_match_their_command_files` enforces this, so the page cannot silently rot when a command changes. Old hashes still rewrite with `replaceState`, and every `cs-<stop>` anchor resolves.

## Keyboard and reduced motion

Page-level ArrowLeft / ArrowRight move between pages when Training is not current and focus is not in a self-keyed pane (`[data-nhg-keys='self']`). Dark mode may show the constellation; light mode must not. `prefers-reduced-motion` shows every diagram in its final state, hides the motion-path pulses, and prints terminal output instantly.

## Fixture maintenance

1. Edit `example/training-scenes.json`. Keep eight scenes unless a later plan raises the cap (never above twelve). Every scene needs `title`, `intent`, `command`, `tools`, `output`, `editor`, `artifact`, `booth`, `gate`, `next_scene`, and `beats`.
2. Copy the parsed JSON into the `<script type="application/json" id="nh-training-scenes">` block. Encode a literal `</script>` inside a string as `<\/script>` so the HTML parser does not close the block.
3. Run `python -m pytest -q tests/guides/test_nexus_hub_guide.py`. The suite asserts the inline JSON equals the file after parse, that hostile fixture strings survive, and that `booth.fixed` is false before `/implement` and true after.

## Command inventory

Every file in `catalog/commands/` is either a Training scene, a Cheatsheets entry, or declined as Training with a reason. New catalog commands after this redesign do not require new Training scenes.

| Command | Placement |
|---|---|
| `/describe` | Training |
| `/review` | Training |
| `/plan` | Training |
| `/implement` | Training |
| `/compare` | Training |
| `/test` | Training |
| `/update` | Training |
| `/presentify` | Training (communicate closer) |
| `/spec` | Cheatsheets |
| `/constitution` | Cheatsheets (alias of `/spec constitution`) |
| `/setup` | Cheatsheets |
| `/skills` | Cheatsheets |
| `/commands` | Cheatsheets (alias of `/skills list`) |
| `/route` | Cheatsheets |
| `/session` | Cheatsheets |
| `/commit` | Cheatsheets (alias of `/update commit`) |
| `/memory` | Cheatsheets; declined as Training |
| `/usage` | Cheatsheets; declined as Training |
| `/research` | Cheatsheets; declined as Training |
| `/org` | Cheatsheets; declined as Training |
| `/tune-prompting` | Cheatsheets; declined as Training |

The same table is frozen in `docs/releases/v4/v4.2/development/guide-redesign-content-map.md`.

## The example project (Glow Booth)

A small vanilla HTML, CSS, and JavaScript instant-camera booth that runs by opening `example/glow-booth/index.html`. It works end to end but ships with two intentional bugs and no tests, plus one feature to add:

- A perfect set of poses awards 4/5 stamps (the stamp helper stops one short).
- Restart leaves the last pose on stage.
- Feature to add: shuffle poses plus a sparkle overlay on a full meter.

The Training scenes resolve those with the loop, and the in-guide mockup reproduces both bugs so a learner sees them before any fix. `example/glow-booth-shuffle-reference/` already has shuffle and sparkle; it is the local `/compare` target. `glow-booth.zip` bundles both folders plus a START-HERE note. Do not teach Trivia Quiz in the published guide.

## Running the training (self-guided)

Prerequisites:

- Nexus-Hub installed so the slash commands resolve. Paste one of the Home install commands above.
- A modern browser to open `index.html`.

Setup: download `glow-booth.zip`, extract it, and open the app in your platform of choice. From the app folder, run `git init` and an initial commit.

The loop, in order (each command is on the matching Training step):

1. `/describe full`
2. `/review`
3. `/plan feature`
4. `/implement` (one phase)
5. `/compare ../glow-booth-shuffle-reference` then `/plan from-comparison` as a beat of compare, not a ninth scene
6. `/test unit`
7. `/update`
8. `/presentify`

Troubleshooting: if a slash command does not resolve, reinstall Nexus-Hub and reload the editor. If `/compare` cannot find the reference, keep `glow-booth-shuffle-reference` next to the app (`../glow-booth-shuffle-reference`).

## Copy contract (canonical publication)

Canonical source: `guides/website/nexus-hub-guide.html` in this repository.

Published copy (sibling portfolio, outside this tree): `<portfolio-root>/nexus-hub/index.html`. Common local layout is `../online-portfolio/` next to Nexus-Hub. Absence of that clone does not block Nexus-Hub CI or a release.

Publication is a copy:

- Prefer a byte-identical copy of the canonical HTML.
- An allowlisted head delta such as a favicon `<link>` is acceptable if the portfolio origin still requires it.
- Maintainers copy by hand, or a later portfolio-side script may copy. This release does not add `scripts/sync-nexus-hub-guide.mjs` to the sibling repository.
- Never fetch the guide from the network to check it.

Local publication check: `python -m pytest -q tests/guides/test_nexus_hub_guide.py`. That module lives in this repo (not installer-copied). It asserts the file is self-contained, the inline Training JSON is valid, the install constants match, and the file stays under the 500 KB budget. If `NEXUS_HUB_PORTFOLIO_ROOT` is set, the suite diffs `<portfolio-root>/nexus-hub/index.html` against the canonical file and fails on unexpected drift. If the env var is unset, that leg is skipped and the rest of the suite still passes.

## Browser verification

The pytest suite parses HTML and JSON; it does not execute JavaScript. Rendered verification is a first-class step, run per phase with the local harness:

```bash
python tests/guides/tools/render_guide.py --label phase-N
```

That renders every page in both themes at 420 / 900 / 1440 px and writes PNGs under `docs/releases/v4/v4.2/development/guide-rebuild/renders/<label>/`. It needs Playwright (`pip install playwright && playwright install chromium`), which is an optional dev dependency: CI never requires it, and the harness fails with an install hint rather than a traceback. Useful flags: `--pages`, `--themes`, `--widths`, `--reduced-motion`, `--hash`.

Before a workshop or a portfolio publish, also open the file by hand and check:

- Light and dark themes, including a reload (theme must persist only `light` or `dark`)
- Reduced motion across Foundations and the Training terminal
- Home install copy on the Windows and macOS/Linux tabs, and the verify-command copy cells
- Foundations: eight scenes, correct responsive diagram variant, no pinned overlay, no comparison toggle
- Training: the booth's 4/5 bug and sticky Restart, the fix at `/implement`, the terminal, the outline, Present mode, and a mid-walkthrough URL
- Cheatsheets: every scope readable, jump nav, and a deep link such as `#cheatsheets/explore`
- Keyboard-only path through all four pages

Lighthouse Accessibility is a last-phase human bar, not a mid-plan merge gate.

## Editing

The guide is a single HTML file: CSS in the `<style>` block, content in `<section class="page">` blocks, behavior in the two `<script>` blocks at the bottom (the app shell, then the Training engine after the scene JSON). Class prefixes: `fx-` for Foundations scenes, `nht-` / `nb-` for Training and the booth, `cs-` for Cheatsheets. Scene data is `example/training-scenes.json` plus the matching inline JSON block. The example under `example/` is plain files; edit them in place and regenerate `glow-booth.zip` from those folders.
