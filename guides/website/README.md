# Nexus-Hub Interactive Guide

This directory holds the public-facing Nexus-Hub guide and the Trivia Quiz example the Training workbench operates on. Everything is self-contained, opens in a browser, and needs no build step. This `README.md` is for maintainers.

## Contents

| Item | What it is |
|---|---|
| `nexus-hub-guide.html` | Canonical interactive guide. One HTML file. The main entry point. |
| `example/training-scenes.json` | Maintainer source of truth for Training scenes. The guide inlines a verified copy. |
| `example/trivia-quiz/` | Example app the workbench shows. |
| `example/quiz-shuffle-reference/` | Local `/compare` target that already has deck shuffle. |
| `trivia-quiz.zip` | Downloadable bundle learners extract. |

The guide is the single home for orientation, installation, Foundations, Training, the six workflow pages, and Reference. It remains one self-contained HTML file with no runtime network dependency.

## The interactive guide

`nexus-hub-guide.html` is a single HTML file with zero runtime dependencies. No server, no CDN, no remote fonts, nothing to install.

- **To open:** double-click the file. It opens in any modern browser and works fully offline. GitHub does not render HTML inline, so use Download raw file, then open the download.
- **To share:** send that one file.
- **Primary navigation:** Home, Foundations, Training, Workflows, Reference. Installation is not a primary page. GitHub is an external link. Theme toggles light and dark and persists only those two values under `portfolio-theme`.

URL grammar: `#<page-id>` for pages; `#training/<scene-id>?beat=n` for Training. `#home/install` scrolls to the Home install block. Unknown page ids rewrite to Home.

## Home

Home is a short orientation, not a catalog dump. It states what Nexus-Hub is, compares a model-only assistant to a harnessed one, and embeds the two canonical install commands behind OS tabs.

Canonical install constants (must match `tests/guides/test_nexus_hub_guide.py`):

- macOS / Linux: `curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash`
- Windows: `irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1 | iex`

Home also shows platform reachability (which hosts expose slash commands, and the first verify step) and a six-node ribbon: Map and evaluate, Plan, Build, Harden, Ship, Communicate. wget, flags, and `--workspace` live in a Home disclosure and in Reference. Do not hardcode skill counts, command counts, or installer versions on Home.

## Foundations

Foundations teaches one distinction: the model is the brain; the agent or platform is the hands; Nexus-Hub is the experience layer (workflows, skills, and guardrails). A user-initiated range slider compares "Model alone" with "Model with Nexus-Hub". Both states stay in the markup for no-JS and reduced motion. The handoff is `#training` (the Training page), not a scene URL.

## Training workbench

Training is one IDE workbench (`#nhWorkbench`), not a slide deck. Eight closed scenes, hard-capped at ten: `describe`, `review`, `plan`, `implement`, `compare`, `test`, `update`, `presentify`.

Controls:

- Previous, Next, Reset, Outline, Copy command
- ArrowLeft / ArrowRight / Space step beats while the Training page is showing
- Escape closes the outline
- Keys disengage inside `[data-nhg-keys='self']` panes (editor, files, assistant, terminal, and the Foundations slider)
- No autoplay, no speed control, no fullscreen control

URL: `#training/<scene-id>?beat=n`. Beat changes use `history.replaceState`. Scene jumps use `location.hash`. Invalid scene or beat clamps to `describe` beat 0.

Fixture strings are painted with `textContent` / `createElement` only. Do not assign scene JSON through `innerHTML`.

## Keyboard and reduced motion

Page-level ArrowLeft / ArrowRight move between allowlisted pages when Training is not the current page and focus is not in a self-keyed pane. Dark mode may show the constellation; light mode must not. `prefers-reduced-motion` keeps comparison states static and does not run constellation animation.

## Fixture maintenance

1. Edit `example/training-scenes.json`. Keep eight scenes unless a later plan raises the cap (never above ten).
2. Copy the parsed JSON into the `<script type="application/json" id="nh-training-scenes">` block. Encode a literal `</script>` in a string as `<\/script>` so the HTML parser does not close the block.
3. Run `python -m pytest -q tests/guides/test_nexus_hub_guide.py`. The suite asserts the inline JSON equals the file after parse, and that hostile fixture strings (`<img onerror>`, `</script>`) survive.

Do not invent a ninth Training scene for a follow-on `/implement` after `/compare`. That is the same command with a different plan.

## Command inventory

Every file in `catalog/commands/` is either a Training scene, a Reference row, or declined as Training with a reason. New catalog commands after this redesign do not require new Training scenes.

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
| `/spec` | Reference |
| `/constitution` | Reference (alias of `/spec constitution`) |
| `/setup` | Reference |
| `/skills` | Reference |
| `/commands` | Reference (alias of `/skills list`) |
| `/route` | Reference |
| `/session` | Reference |
| `/commit` | Reference (alias of `/update commit`) |
| `/memory` | Reference; declined as Training |
| `/usage` | Reference; declined as Training |
| `/research` | Reference; declined as Training |
| `/org` | Reference; declined as Training |
| `/tune-prompting` | Reference; declined as Training |

The same table is frozen in `docs/releases/v4/v4.2/development/guide-redesign-content-map.md`.

## The example project (Trivia Quiz)

A small vanilla HTML, CSS, and JavaScript quiz that runs by opening `example/trivia-quiz/index.html`. It works end to end but ships with two intentional bugs and no tests, plus one feature to add:

- A perfect run scores one less than the total (the score helper stops one short).
- Restart keeps the previous answers instead of clearing them.
- Feature to add: shuffle the deck on every run.

The Training scenes resolve those with the loop. `example/quiz-shuffle-reference/` already has shuffle; it is the local `/compare` target. `trivia-quiz.zip` bundles both folders plus a START-HERE note.

## Running the training (self-guided)

Prerequisites:

- Nexus-Hub installed so the slash commands resolve. Paste one of the Home install commands above.
- A modern browser to run the app.
- Node 18+ and npm (the `/test` step uses Vitest).

Setup: download `trivia-quiz.zip`, extract it, and open the app in your platform of choice. From the app folder, run `git init` and an initial commit, then `npm install`.

The loop, in order (each prompt is on the matching workbench scene):

1. `/describe full`
2. `/review`
3. `/plan feature`
4. `/implement` (one phase)
5. `/compare ../quiz-shuffle-reference` then `/plan from-comparison` as a beat of compare or plan, not a ninth scene
6. `/test unit`
7. `/update`
8. `/presentify`

Troubleshooting: if a slash command does not resolve, reinstall Nexus-Hub and reload the editor. If `/compare` cannot find the reference, keep `quiz-shuffle-reference` next to the app (`../quiz-shuffle-reference`). If Vitest is missing, run `npm install` in the app folder.

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
- Foundations slider
- All eight Training scenes, including outline, copy, and a mid-tour URL
- Keyboard-only path through Home, Foundations, Training, one workflow page, and Reference
- `file://` boot (untrusted-origin warning stays visible)

Lighthouse Accessibility is a last-phase human bar, not a mid-plan merge gate.

## Editing

The guide is a single HTML file: CSS in the `<style>` block, content in `<section class="page">` blocks, behavior in the `<script>` blocks at the bottom. Training styles use the `wb-` prefix. Scene data is `example/training-scenes.json` plus the matching inline JSON block. The example under `example/` is plain files; edit them in place and regenerate `trivia-quiz.zip` from those folders.
