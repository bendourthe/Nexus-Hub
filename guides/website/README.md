# Nexus-Hub Interactive Guide

This directory holds the public-facing Nexus-Hub guide and the Glow Booth example the Training slideshow operates on. Everything is self-contained, opens in a browser, and needs no build step. This `README.md` is for maintainers.

## Contents

| Item | What it is |
|---|---|
| `nexus-hub-guide.html` | Canonical interactive guide. One HTML file. The main entry point. |
| `example/training-scenes.json` | Maintainer source of truth for Training scenes. The guide inlines a verified copy. |
| `example/glow-booth/` | Example app the Training hero shows. Open `index.html` from disk. |
| `example/glow-booth-shuffle-reference/` | Local `/compare` target that already has Shuffle poses plus sparkle. |
| `glow-booth.zip` | Downloadable bundle learners extract. |
| `example/trivia-quiz/` | Previous example. Stays on disk. Not taught in the published guide. |

The guide is the single home for orientation, installation, Foundations, Training, and Cheatsheets. It remains one self-contained HTML file with no runtime network dependency.

## The interactive guide

`nexus-hub-guide.html` is a single HTML file with zero runtime dependencies. No server, no CDN, no remote fonts, nothing to install.

- **To open:** double-click the file. It opens in any modern browser and works fully offline. GitHub does not render HTML inline, so use Download raw file, then open the download.
- **To share:** send that one file.
- **Primary navigation:** Home, Foundations, Training, Cheatsheets. Installation is not a primary page. GitHub is an external link. Theme toggles light and dark and persists only those two values under `portfolio-theme`.

URL grammar: `#<page-id>` for pages; `#training/<scene-id>?beat=n` for Training; `#cheatsheets/<stop>` for Cheatsheets sections. Compatibility: `#reference` and `#workflows` rewrite to `#cheatsheets`; `#explore`, `#plan`, `#build`, `#harden`, `#ship`, `#communicate` rewrite to `#cheatsheets/<id>`. `#home/install` scrolls to the Home install block. Unknown page ids rewrite to Home.

## Home

Home is a short orientation, not a catalog dump. It states what Nexus-Hub is, compares a model-only assistant to a harnessed one, and embeds the two canonical install commands behind OS tabs.

Canonical install constants (must match `tests/guides/test_nexus_hub_guide.py`):

- macOS / Linux: `curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash`
- Windows: `irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1 | iex`

Home also shows platform reachability (which hosts expose slash commands, and the first verify step) and a six-node ribbon: Map and evaluate, Plan, Build, Harden, Ship, Communicate. wget, flags, and `--workspace` live in a Home disclosure and in Cheatsheets. Do not hardcode skill counts, command counts, or installer versions on Home.

## Foundations

Foundations teaches prompt, context, harness, and loop engineering as four visual stations. A user-initiated two-state control compares "Model alone" with "Model with Nexus-Hub" on the Glow Booth stamp bug. Both states stay in the markup for no-JS and reduced motion. The handoff is `#training` (the Training page), not a scene URL. Do not restore a `type="range"` hero.

## Training slideshow

Training is a slideshow (`#nhTraining`, `.ts-slide`). The hero is Glow Booth transforming (`#nhBoothHero`). File and IDE panes live behind **Peek at the files**, not as the default grid. Eight closed scenes, hard-capped at twelve: `describe`, `review`, `plan`, `implement`, `compare`, `test`, `update`, `presentify`. Intro or outro slides count toward the cap and must not add a ninth command.

Controls:

- Previous, Next, Reset, Outline, Copy command
- ArrowLeft / ArrowRight / Space step beats while the Training page is showing
- Home / End jump to the first or last scene
- Swipe on the booth hero on touch devices
- Escape closes the outline
- Keys disengage inside `[data-nhg-keys='self']` panes (editor, files, assistant, terminal, and the Foundations comparison)
- No autoplay, no speed control, no fullscreen control

URL: `#training/<scene-id>?beat=n`. Beat changes use `history.replaceState`. Scene jumps use `location.hash`. Invalid scene or beat clamps to `describe` beat 0.

Fixture strings are painted with `textContent` / `createElement` only. Do not assign scene JSON through `innerHTML`. Booth hero states are allowlisted in script, never taken from JSON as HTML.

## Cheatsheets

Cheatsheets is one page with three bands: the six-stop loop, the command argument table (real flags from `catalog/commands/`), then extra notes only when they are not a repeat of Training. Primary nav is Home, Foundations, Training, Cheatsheets. Old hashes `#reference`, `#workflows`, `#explore`, `#plan`, `#build`, `#harden`, `#ship`, and `#communicate` rewrite with `replaceState`.

## Keyboard and reduced motion

Page-level ArrowLeft / ArrowRight move between allowlisted pages when Training is not the current page and focus is not in a self-keyed pane. Dark mode may show the constellation; light mode must not. `prefers-reduced-motion` keeps comparison states static and does not run constellation animation.

## Fixture maintenance

1. Edit `example/training-scenes.json`. Keep eight scenes unless a later plan raises the cap (never above twelve).
2. Copy the parsed JSON into the `<script type="application/json" id="nh-training-scenes">` block. Encode a literal `</script>` in a string as `<\/script>` so the HTML parser does not close the block.
3. Run `python -m pytest -q tests/guides/test_nexus_hub_guide.py`. The suite asserts the inline JSON equals the file after parse, and that hostile fixture strings (`<img onerror>`, `</script>`) survive.

Do not invent a ninth Training scene for a follow-on `/implement` after `/compare`. That is the same command with a different plan.

## Command inventory

Every file in `catalog/commands/` is either a Training scene, a Cheatsheets row, or declined as Training with a reason. New catalog commands after this redesign do not require new Training scenes.

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
- Feature to add: Shuffle poses plus a sparkle overlay on a full meter.

The Training scenes resolve those with the loop. `example/glow-booth-shuffle-reference/` already has shuffle and sparkle; it is the local `/compare` target. `glow-booth.zip` bundles both folders plus a START-HERE note. Do not teach Trivia Quiz in the published guide.

## Running the training (self-guided)

Prerequisites:

- Nexus-Hub installed so the slash commands resolve. Paste one of the Home install commands above.
- A modern browser to open `index.html`.

Setup: download `glow-booth.zip`, extract it, and open the app in your platform of choice. From the app folder, run `git init` and an initial commit.

The loop, in order (each prompt is on the matching Training slide):

1. `/describe full`
2. `/review`
3. `/plan feature`
4. `/implement` (one phase)
5. `/compare ../glow-booth-shuffle-reference` then `/plan from-comparison` as a beat of compare or plan, not a ninth scene
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

Local publication check: `python -m pytest -q tests/guides/test_nexus_hub_guide.py`. That module lives in this repo (not installer-copied). It asserts the file is self-contained, the inline Training JSON is valid, and the install constants match. If `NEXUS_HUB_PORTFOLIO_ROOT` is set, the suite diffs `<portfolio-root>/nexus-hub/index.html` against the canonical file and fails on unexpected drift. If the env var is unset, that leg is skipped and the rest of the suite still passes.

## Browser verification

Automated tests parse HTML and JSON. They do not execute JavaScript in a browser. Before a workshop or a portfolio publish, open the file locally and check:

- Light and dark themes, including a reload (theme must persist only `light` or `dark`)
- Reduced motion
- Home install copy on macOS/Linux and Windows tabs
- Foundations four stations and the two-state comparison (not a range slider)
- All eight Training slides, including the booth hero, peek, outline, copy, and a mid-tour URL
- Keyboard-only path through Home, Foundations, Training, and Cheatsheets
- `file://` boot (untrusted-origin warning stays visible)

Lighthouse Accessibility is a last-phase human bar, not a mid-plan merge gate.

## Editing

The guide is a single HTML file: CSS in the `<style>` block, content in `<section class="page">` blocks, behavior in the `<script>` blocks at the bottom. Training styles use the `ts-` and `wb-` prefixes. Scene data is `example/training-scenes.json` plus the matching inline JSON block. The example under `example/` is plain files; edit them in place and regenerate `glow-booth.zip` from those folders.
