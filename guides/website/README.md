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

## Design system (v4.2.2)

The design language is fixed in `docs/releases/v4/v4.2/development/guide-rebuild/design-brief.md`. The load-bearing decisions:

- **Shared measure.** `--measure: 700px` caps the hero H1 *and* its lead paragraphs, so the title and the copy under it wrap on the same width.
- **Compact rhythm.** A 4px spacing scale (`--sp-1` to `--sp-8`) with `--sec-pad: 32px` (22px under 720px). Sections are separated by an eyebrow and a heading, not by empty space.
- **Motion vocabulary.** `.reveal` elements fade and rise via one shared IntersectionObserver. Continuous motion (constellation, Foundations pulses) runs only while its scene is on screen. `prefers-reduced-motion` renders a complete static equivalent, never a crushed duration.
- **Themes.** All colors are tokens defined on `:root`, `html[data-theme="dark"]`, and `html[data-theme="light"]`. Every text style in both themes meets WCAG AA contrast (verified in Phase 6 across 217 sampled styles).
- **Light-mode brand chip.** In light theme the glow logo mark sits on a rounded dark chip so it reads against the light ground.

## Home

Home is a short orientation, not a catalog dump. It states what Nexus-Hub is, embeds the two canonical install commands behind OS tabs (**Windows first and default**), compares a model-only assistant to a harnessed one, shows the six-step loop, and closes with next steps.

Canonical install constants (must match `tests/guides/test_nexus_hub_guide.py`):

- Windows: `irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1 | iex`
- macOS / Linux: `curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash`

The verify step (`/skills list`, `/commands`) renders as copyable inline cells. wget, flags, and `--workspace` live in a Home disclosure and in Cheatsheets. Do not hardcode skill counts, command counts, or installer versions on Home.

There is no untrusted-origin warning box. It was removed in v4.2.2 along with `isDocumentedGuideOrigin()`; do not reintroduce either.

## Foundations

Foundations is five scrollytelling scenes, each teaching one concept with one hand-authored inline SVG diagram:

1. **The model** - text in, text out, and what it cannot do.
2. **The platform** - the agent loop, with a pulse travelling model to repo and back.
3. **Context** - a focused context window and a noisy one, side by side under one "same model" chip.
4. **The harness** - Skills, Commands, Hooks, and Gates snapping around the loop as guardrail arcs.
5. **One task, two runs** - the same task run raw (fading chat bubble) and harnessed (hook, gate, tested commit).

Hard rules: no element pins itself over the content, and there is **no toggle** between "model alone" and "model with Nexus-Hub" - both states are always visible, because a selector for something already on screen is noise. Diagram colors come from theme tokens so one markup serves both themes. Do not restore a `type="range"` hero, the station cards, or the carousel.

## Training walkthrough

Training is an eight-step interactive walkthrough (`#nhTraining`, `[data-training-root]`) driven entirely by the scene JSON. Each step composes four things:

1. The step's intent, in second person.
2. **The interactive Glow Booth mockup** - a faithful re-implementation of `example/glow-booth/logic.js`, *including both frozen bugs*. While `booth.fixed` is false, `computeStamps` walks `captured.length - 1` (a perfect set reads 4 of 5) and Restart keeps `lastPose` on stage. Learners click it freely.
3. **The simulated terminal** - the step's command pre-filled with a Run affordance; running types the echo then reveals the output lines.
4. The artifact card and gate verdict.

Controls: Previous, Next, Restart, Outline, and Present. ArrowLeft / ArrowRight / Space step beats; `f` toggles Present; Escape exits it. **Present mode** requests fullscreen on the training root and applies a viewport overlay class either way, so a denied or unavailable Fullscreen API still presents as slides.

URL: `#training/<scene-id>?beat=n`. Beat changes use `history.replaceState`. An unknown scene id or an out-of-range beat clamps to the nearest valid step.

Fixture strings are painted with `textContent` / `createElement` only. The Training engine assigns `innerHTML` nowhere, and a test enforces that, so the hostile fixture strings (`<img onerror>`, `</script>`) can never execute.

Eight closed scenes, hard-capped at twelve: `describe`, `review`, `plan`, `implement`, `compare`, `test`, `update`, `presentify`. Do not invent a ninth scene for the follow-on `/implement` after `/compare`; that is the same command with a different plan.

## Cheatsheets

Cheatsheets groups every command under seven **intent-named** sections - Understand and evaluate, Plan the work, Build it, Prove it, Ship and govern, Communicate, Catalog and session. The "Band 1 / Band 2" labels are gone and must not return.

Each command lists **every scope with a one-line description of what that scope does**, plus flags, an alias badge where one applies, a copyable invocation, and a Training deep link for the eight taught commands. Commands with no scopes say so explicitly.

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
- Foundations: five scenes, no pinned overlay, no comparison toggle
- Training: the booth's 4/5 bug and sticky Restart, the fix at `/implement`, the terminal, the outline, Present mode, and a mid-walkthrough URL
- Cheatsheets: every scope readable, jump nav, and a deep link such as `#cheatsheets/explore`
- Keyboard-only path through all four pages

Lighthouse Accessibility is a last-phase human bar, not a mid-plan merge gate.

## Editing

The guide is a single HTML file: CSS in the `<style>` block, content in `<section class="page">` blocks, behavior in the two `<script>` blocks at the bottom (the app shell, then the Training engine after the scene JSON). Class prefixes: `fx-` for Foundations scenes, `nht-` / `nb-` for Training and the booth, `cs-` for Cheatsheets. Scene data is `example/training-scenes.json` plus the matching inline JSON block. The example under `example/` is plain files; edit them in place and regenerate `glow-booth.zip` from those folders.
