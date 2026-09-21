# Static source audit - nexus-hub-guide.html

**Date**: 2026-08-29
**File**: `guides/website/nexus-hub-guide.html`
**Size**: 476900 bytes, 3684 lines
**Browser**: not available. Recorded as known-gap DF-1 on the v4.2.0 ledger.

## Document contract (current)

- Single HTML file. One `<html lang="en" class="no-js">`. CSS in one `<style>` block. Behavior in inline `<script>` blocks.
- `meta name="color-scheme"` is `dark` only. `theme-color` is `#04141a`. No light tokens. No `portfolio-theme` key. No theme toggle.
- Favicons are `data:image/png;base64` (32px and 16px). Logo mark is an inline SVG symbol plus a large inline PNG inside `#nexus-mark`.
- No `<script src>`, no stylesheet `http(s)` href, no `@import`, no `font-face` URL, no `fonts.google` / cdnjs / unpkg / jsdelivr.
- User-initiated outbound: one GitHub `<a href="https://github.com/bendourthe/Nexus-Hub">`. Example download: `href="trivia-quiz.zip"` (relative, allowed).
- Installer URLs appear only as copyable command text, not as runtime fetches.

## Page ids

`home`, `foundations`, `training`, `setup`, `explore`, `plan`, `build`, `harden`, `ship`, `communicate`, `reference`.

`PAGES` in the inline script lists those eleven ids. Hash routing takes the entire `location.hash` (minus `#`) as a page id. Unknown hashes map to `home` but do not rewrite the URL. `#training/<scene>` would fail the allowlist and bounce to home. That is the Phase 2 parser bug the plan names.

## Primary navigation

Selector: `nav.nav[aria-label="Primary"]` / `#navLinks`.

| Label | `data-go` |
|---|---|
| Brand / home | `home` |
| Home | `home` |
| Installation | `setup` |
| Foundations | `foundations` |
| Training | `training` |
| Workflows | `explore` (`data-group="workflow"`) |
| Cheatsheets | `reference` |
| GitHub | external href, not `data-go` |

Installation is a primary nav item. There is no theme control. Nav `data-go` anchors have no `href`.

## Heading outline (page-level)

| Page | H1 count | Primary heading |
|---|---|---|
| home | 1 | Upgrade your agentic AI platform with an autonomous team of world experts |
| foundations | 1 | How AI actually works |
| training | 0 | Page title is an H2: Nexus-Hub, end to end, on a real example. Slide titles are H2. |
| setup | 1 | Install once, work everywhere |
| explore | 3 | Page H1 plus mock-document H1s (TaskFlow analysis, TaskFlow review) |
| plan | 2 | Page H1 plus mock plan H1 |
| build | 1 | Build the plan, one phase at a time |
| harden | 2 | Page H1 plus mock pentest H1 |
| ship | 2 | Page H1 plus mock changelog H1 (`## [0.5.0]`) |
| communicate | 1 | Capture the work, then present it |
| reference | 1 | Cheatsheet |

Element ids in the file are unique (34 ids, no duplicates). Several workflow pages use extra H1s for in-page mock artifacts.

## Hardcoded catalog and installer strings (onboarding)

These live in Home and Installation, which Phase 3 treats as onboarding:

| Location | Selector / block | String |
|---|---|---|
| Home hero | `.hero .stat-row .stat` | 252 skills, 14 commands, 22 hooks, 23 agents, 6+ AI platforms |
| Home why-it-matters | `.grid.grid-4` Depth card | 259 skills encode expert procedures |
| Home comparison | `.card` Nexus-Hub list | 252 expert skills load on demand |
| Installation banner mock | `#page-setup .term-body` | v3.10.0 (three times: banner, welcome, installed line) |

Canonical catalog at rewrite time is 328 skills / v4.1.2. Disposition: REMOVE or replace with a non-numeric source. See the content-map.

## Training slides (31)

All are `.nht .ts-slide` with `data-sec` and `data-tt`.

| # | `data-sec` | `data-tt` |
|---|---|---|
| 1 | What Nexus-Hub is | Nexus-Hub |
| 2 | What Nexus-Hub is | What it is |
| 3 | What Nexus-Hub is | Why it matters |
| 4 | How it works | Building blocks |
| 5 | How it works | Guardrails |
| 6 | How it works | The workflow |
| 7 | A real example | Meet the example |
| 8 | A real example | What it needs |
| 9 | A real example | Follow along |
| 10 | The loop, step by step | Understand: /describe |
| 11 | The loop, step by step | /describe result |
| 12 | The loop, step by step | Evaluate: /review |
| 13 | The loop, step by step | /review result |
| 14 | The loop, step by step | Decompose: /plan |
| 15 | The loop, step by step | /plan result |
| 16 | The loop, step by step | Build: /implement |
| 17 | The loop, step by step | /implement result (bugs) |
| 18 | The loop, step by step | Evaluate: /compare |
| 19 | The loop, step by step | /compare result |
| 20 | The loop, step by step | Decompose: /plan from-comparison |
| 21 | The loop, step by step | /plan from-comparison result |
| 22 | The loop, step by step | Build: /implement |
| 23 | The loop, step by step | /implement result (shuffle) |
| 24 | The loop, step by step | Harden: /test |
| 25 | The loop, step by step | /test result |
| 26 | The loop, step by step | Ship: /update |
| 27 | The loop, step by step | /update result |
| 28 | In practice | Summary |
| 29 | In practice | Document and present |
| 30 | In practice | /presentify result |
| 31 | In practice | Apply it |

Example ZIP is linked from slide 9 (`a.ts-zip[href="trivia-quiz.zip"]`).

Training is a 16:9 slide stage (`.ts-frame` / `.ts-stage` 1280x720). Controls include outline, prev/next, fullscreen. Autoplay is not present. Fullscreen is in the current UI; Phase 5 drops it as a dedicated control.

## Keyboard, focus, motion (from source)

- Page ArrowLeft / ArrowRight change `location.hash` across `PAGES`. Training page returns early so those keys do not change page while `current === "training"`.
- Disengage is only `input` and `textarea`. ContentEditable, range inputs, and role=button regions are not excluded. Focus inside `.nht` still uses training's own keys.
- `prefers-reduced-motion`: CSS sets animation/transition duration to 0.001ms and stops `.hero .mark-xl` float. Constellation still builds; `REDUCE` draws one static frame instead of looping. Typewriter terminals skip animation when REDUCE is true.
- Constellation (`#constellation`): runs on Home at opacity 0.55, reduced opacity 0.16 and stopped on other pages. No light-mode hide (there is no light mode). No `visibilitychange` pause. Resize rebuilds nodes; one listener.
- `.page { animation: fadeUp .4s }` on every page show.

## Copy integrity (install)

On `#page-setup` and `#page-reference`, `data-copy` equals the visible command text for:

- `curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash`
- `irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1 | iex`

wget is also copyable on Setup. Home has no install commands today.

## Trust notes (current gaps vs the plan)

- Fixture strings in Training are HTML markup, not JSON. Several slides use inline HTML. No `textContent` rendering path.
- No origin warning for untrusted copies (`file://` or non-GitHub / non-portfolio host).
- `localStorage` is unused. Theme cannot persist.
- Copy buttons are injected with `innerHTML` for SVG icons (not scene data). Scene data is static HTML.

## Workflow pages

Explore, plan, build, harden, ship, and communicate exist. Home "Get started" uses eight equal `.card.navcard` cells including Installation and Reference. Communicate / `/presentify` is present as the Document card (`data-go="communicate"`). Workflow copy currently uses a TaskFlow fiction, while Training uses Trivia Quiz.
