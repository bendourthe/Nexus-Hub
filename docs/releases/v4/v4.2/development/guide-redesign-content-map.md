# Guide redesign content map

**Date**: 2026-08-29
**Source markup**: `guides/website/nexus-hub-guide.html`
**Plans**: `docs/releases/v4/v4.2/plans/v4.2.0-interactive-guide-redesign.md` (historical; unpublished) and `docs/releases/v4/v4.2/plans/v4.2.1-guide-visual-education.md` (current)
**Baseline**: `docs/releases/v4/v4.2/development/guide-redesign-baseline/`

This file is the working contract for Phases 2-6. Frozen tables below are copied from the plan. Do not paraphrase the inherit/reject table into "use presentify".

**Status (2026-08-29)**: The v4.2.0 tables in this file remain as historical contract. They are **superseded** by the dated **v4.2.1** section at the end of this file. Implement Phases 2-6 of `v4.2.1-guide-visual-education` from that section only. Do not treat the v4.2.0 rejections of `nav=slides` or cinematic *patterns* as the current freeze. Those two rows were un-frozen with limits in v4.2.1.

Disposition values: KEEP, MERGE, MOVE TO DISCLOSURE, REMOVE.

Primary navigation after Phase 2: Home, Foundations, Training, Workflows, Reference. Installation is not a primary page. GitHub stays as an external control. Theme control is added in Phase 2.

Canonical non-numeric source for catalog scale: the live `data/skills.json` / installer, never a hardcoded count in onboarding copy. Hardcoded `252`, `259`, `14 commands`, `22 hooks`, `23 agents`, and `v3.10.0` are REMOVE from Home and Installation.

## Home ribbon (frozen)

The six workflow pages stay explore, plan, build, harden, ship, and communicate. The Home preview has exactly those six nodes:

| Home node | Commands shown | `data-go` target |
|---|---|---|
| Map and evaluate | `/describe`, `/review` | `explore` |
| Plan | `/plan` | `plan` |
| Implement | `/implement` | `build` |
| Harden | `/test` | `harden` |
| Ship | `/update` | `ship` |
| Document | `/presentify` | `communicate` |

Do not invent a seventh "review" page. Do not drop communicate when collapsing the old understand-review-plan-implement-test-ship ribbon.

## Command inventory (frozen)

Copied from the plan. Every file in `catalog/commands/` is placed once. Verified 2026-08-29 against `catalog/commands/*.md` (21 files). No catalog command file is missing from this table. New catalog commands that land after the plan is confirmed do not require new Training scenes.

| Command | Placement | Reason |
|---|---|---|
| `/describe` | Training scene | Daily loop start |
| `/review` | Training scene | Daily loop |
| `/plan` | Training scene | Daily loop. Beats may show model routing and the local-commit / no-push-until-final contract |
| `/implement` | Training scene | Daily loop. Beats may show `in-full` versus phase-by-phase |
| `/compare` | Training scene | Daily loop. Beats include `/plan from-comparison` |
| `/test` | Training scene | Daily loop |
| `/update` | Training scene | Daily loop. Beats include release gated on green integration |
| `/presentify` | Training scene (communicate closer) | Already in the live guide; the visitor should see the durable HTML artifact |
| `/spec` | Reference; optional beat inside `/plan` | Not a Trivia Quiz scene |
| `/constitution` | Reference as alias of `/spec constitution` | Permanent alias |
| `/setup` | Reference | Post-install project bootstrap, not the workbench loop |
| `/skills` | Reference | Catalog discovery; first verify step after install |
| `/commands` | Reference as alias of `/skills list` | Permanent alias |
| `/route` | Reference; optional beat inside `/plan` and `/implement` | Not a standalone scene |
| `/session` | Reference | Session hygiene, including `/session history` |
| `/commit` | Reference as alias of `/update commit` | Permanent alias |
| `/memory` | Reference; declined as Training | Maintenance, not first-contact |
| `/usage` | Reference; declined as Training | Host-specific usage limits |
| `/research` | Reference; declined as Training | Adjacent to compare, not this example |
| `/org` | Reference; declined as Training | Optional organization-knowledge layer |
| `/tune-prompting` | Reference; declined as Training | Specialist calibration |

Closed Training set: eight scenes, hard cap ten. Scene order: describe, review, plan, implement, compare, test, update, presentify.

Current Reference (`#page-reference`) lists every catalog command. Phase 6 added `/org`, `/tune-prompting`, and explicit alias rows for `/commit`, `/commands`, and `/constitution`. Training remains the closed eight-scene set.

## Presentify inherit / reject (frozen)

`/presentify` is a document-to-site authoring command. This guide is a durable, portfolio-aligned first-contact product. They share a file contract and fight on visual identity. Phase 2 motion and Phase 5 Training must follow this table.

| Capability | Guide use | Reason |
|---|---|---|
| `nav=scroll` | Inherit for Home, Foundations, Workflows, Reference | Those pages are a scrolling field guide |
| `nav=slides` as the page model | Reject | Training is leaving a 31-slide deck. Viewport-fitted slides recreate it |
| `applyState(scene, beat)` idempotence, fragment beats, key-disengage inside interactive regions, `replaceState` for autoplay ticks | Inherit into the Training controller | Keyboard next/prev and deep links need snapshots, not a second deck runtime |
| Rich before/after or pinned graphic | Inherit for Foundations only, user-initiated | Phase 4 comparison is a range slider or toggle, not scroll-scrub |
| Cinematic / `scroll-scrub-engine.js` / video clips | Reject | A camera fly-through destroys stable IDE spatial orientation. Size-gated clips blow the single-file budget. Reduced motion deletes the effect |
| `design_seed` uniqueness / entropy | Reject | The guide must match the portfolio, not look new every generation |
| html-output-conventions, hallmark-design, visual-QA viewports | Inherit | Offline, no CDN, reduced-motion static equivalents. Workshop QA may substitute 1920 projector + 390 phone for the 2560 leg, and must keep a 25px computed-style floor for workbench text at 1920x1080 |
| `/presentify` as a taught command | Keep and update | Workflow communicate and the Training closer. Mention `--nav scroll\|slides` and `--interactivity restrained\|balanced\|rich\|cinematic` in Reference, not as this page's runtime |

Rejected for this HTML file: cinematic motion, `nav=slides` as the page model, `design_seed`, and `scroll-scrub-engine.js`. Foundations "scrub" means a user-initiated range slider or toggle.

## URL grammar (frozen, implemented in two steps)

One composed encoding:

- Page: `#<page-id>` from an allowlist. Unknown page id maps to `home` and rewrites the URL.
- Training: `#training/<scene-id>` with beat as a non-history query (`?beat=<n>`) or an equivalent that uses `history.replaceState` for beat ticks. `history.pushState` only for user-initiated page or scene jumps.
- `#training` without a scene id is valid after Phase 2 and loads Training at scene 1 beat 0 once scenes exist.
- Unknown scene id, NaN, negative, or beat past the last beat clamps to scene 1 beat 0, rewrites the URL, and renders a complete snapshot. Scenes are full snapshots, not deltas, so a cold mid-tour URL is coherent.
- Page router owns page id. Training owns scene and beat only while the page is `training`. ArrowLeft / ArrowRight / Space never both change page and scene.
- Deck/scene keys disengage when focus is in the editor, terminal, file tree, or the Foundations slider (`event.target` containment). Escape returns focus to the page or workbench chrome.
- Phase 2 implements page routing and `#training`. Phase 4's handoff is `#training`, not a scene URL. Phase 5 adds scene id and beat.

Allowlisted page ids after Phase 3: `home`, `foundations`, `training`, `explore`, `plan`, `build`, `harden`, `ship`, `communicate`, `reference`. Phase 3 removed `setup` from markup and `PAGES`. `#home/install` scrolls to the Home install block without adding a page id.

Phase 2 parser must take the first hash segment only (`#training/describe` is page `training`, not an unknown id).

## Trust boundary (public HTML)

- Fixture strings render with `textContent` / `createTextNode`. No `innerHTML` for scene data.
- Inline JSON lives in `<script type="application/json">` with `</script>` encoded. The Trivia Quiz `index.html` already contains `</script>`; that string is a required fixture test.
- `portfolio-theme` accepts only `light` or `dark` before apply or write. Wrap `localStorage` in try/catch; on failure fall back to `prefers-color-scheme` and still render. Theme sharing with the portfolio works only on the same https origin; `file://` must still boot.
- Install copy payload is a JS/HTML constant equal to the visible command and to `curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash` or `irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1 | iex`. Tests assert `data-copy === textContent ===` those constants.
- If `location.origin` is not the documented GitHub or portfolio host (including `file://`), show a persistent warning that copy-paste installers from this copy are untrusted. Do not hide the host inside overflow.

Documented hosts for the warning allowlist (Phase 3): `https://bendourthe.github.io` (or the live GitHub Pages host of the portfolio), `https://github.com`, and `https://raw.githubusercontent.com` are not the guide origin; the guide origin is the GitHub Pages site that serves the copied HTML, commonly the portfolio host, plus local `http://127.0.0.1` / `http://localhost` for maintainer preview. `file://` always shows the warning.

## Token-role table (placeholder for Phase 2)

Phase 2 records the mapped semantic roles here so later portfolio CSS drift has a refresh step. Do not build a theme compiler.

| Role | Light | Dark | Notes |
|---|---|---|---|
| page background | `#f3f1ea` | `#07141a` | Softened off-white / near-black. Attribute `html[data-theme]`. |
| elevated surface | `#fffdf8` | `#0c1f26` | |
| navigation | `rgba(243,241,234,.94)` | `rgba(7,20,26,.92)` | `--nav-bg` |
| border | `#c9c3b2` | `#1e4550` | |
| primary text | `#1c2a2e` | `#dce8eb` | Not `#000` on `#fff` |
| secondary text | `#4a5c61` | `#9bb0b6` | |
| accent | `#0f6f66` | `#2dd4bf` | Solid, no gradient text |
| focus | `#0f6f66` | `#5eead4` | `:focus-visible` |
| success | `#1f7a4c` | `#4ade80` | |
| warning | `#9a6b12` | `#e2b336` | |
| danger | `#b42318` | `#e07070` | |
| terminal background | `#1c2a2e` | `#07171d` | Terminal stays dark in both themes |
| terminal text | `#dce8eb` | `#cfe9ee` | |

Refresh this table if the portfolio CSS tokens drift. There is no theme compiler.

---

## Dispositions by page

### Home (`#page-home`)

Learning purpose after Phase 3: what Nexus-Hub is, what it adds versus a raw model, how to install it, which platforms run the commands, and the six-node next step. Installation within one scroll. Training within one action.

| Block | Current selector / heading | Disposition | Destination | Learning purpose |
|---|---|---|---|---|
| Centered hero + gradient H1 | `.hero`, `h1 .gtext` | MERGE | Short left-aligned definition. Drop "world experts" cadence. | First sentence: harness, not a model. |
| Hero CTAs | `.btn-row` Get started / Get trained / Explore workflows | MERGE | Get started scrolls to Home install. Get trained -> `#training`. Explore -> Workflows. | Primary path. |
| Pill stats | `.stat-row` 252 / 14 / 22 / 23 / 6+ | REMOVE | None. Catalog counts are not onboarding copy. | Stale proof. |
| What it is | `h2` One catalog, installed into every assistant | MERGE | Opening two-paragraph definition. | Catalog + installer + platforms. |
| Five building blocks table | `.card` Commands/Skills/Hooks/Agents/Rules | MOVE TO DISCLOSURE | Home one-liner plus Reference. | Vocabulary, not the first screen. |
| Four benefit cards | `.grid.grid-4` Consistency/Depth/Safety/Governance | MERGE | Compact comparison columns. Depth's "259 skills" REMOVE. | What it adds, without a card row. |
| Two-column difference | Raw prompting vs Nexus-Hub cards | MERGE | Same comparison. "252 expert skills" REMOVE. | Repository-backed claims only. |
| Favorite commands | `h2` Your favorite commands, leveled up | REMOVE | Training and Reference already teach commands. | Duplicate. |
| The Nexus-Hub loop | `h2` The Nexus-Hub loop | MERGE | Six-node Home ribbon (frozen table). | Map to workflow pages. |
| Three pillars | Procedures / Guardrails / Aligned to your rules | MERGE | "What it adds" comparison: reusable procedures, deterministic enforcement, team consistency. | Not a third restatement. |
| Get started 8-card grid | `.card.navcard` including Installation and Reference | MERGE | Six-node ribbon + next-action links (Training, Workflows, Reference). Installation card REMOVE. Communicate KEEP. | Must not drop `/presentify`. |
| Page progress / prev-next | `[data-progress]`, `[data-pagenav]` | MERGE | Phase 2 shell. Do not walk Installation as a page. | |

### Installation (`#page-setup`)

| Block | Current | Disposition | Destination | Learning purpose |
|---|---|---|---|---|
| Primary nav item Installation | `#navLinks a[data-go="setup"]` | REMOVE | Not a primary page. | |
| `PAGES` entry `setup` | inline script | REMOVE | After migrating remaining detail. | |
| `data-go="setup"` elsewhere | Home CTA, navcards | REMOVE | Retarget to Home install or Reference. | No orphaned setup routes. |
| One-command curl / irm | `.cmd-line[data-copy]` | MOVE | Home installation component. Payload must stay exact. | Install in one scroll. |
| wget fallback | second macOS/Linux line | MOVE TO DISCLOSURE | Home "Need another option?" or Reference. | |
| Open a terminal / OS cards | `.choice-cards` | MOVE TO DISCLOSURE | Short Home sentence or Reference. | |
| Welcome banner / v3.10.0 mock | installer terminal mock | REMOVE | Version strings must not be hardcoded. Keep a non-versioned "what the installer does" sentence. | |
| No questions / global / platforms / edits stay safe | four cards | MERGE | One Home sentence: copies the catalog, wires detected assistants, preserves user edits. | |
| Conflict prompt / `--yes` | re-install callout | MOVE TO DISCLOSURE | Reference advanced flags. | |
| What those add-ons do | Auto-approve, CCU, Skill Discovery, commit-msg | MOVE TO DISCLOSURE | Reference. | |
| What lands where | `~/.nexus-hub/` vs per-tool config | MOVE TO DISCLOSURE | Reference. | |
| Verify it worked | currently on Setup | MERGE | Home or adjacent: first verify is `/skills list` or `/commands`. | Platform reachability beat. |
| Keep it current | upgrade note | MOVE TO DISCLOSURE | Reference. | |
| One catalog, every platform | platform list | MERGE | Scannable Home or Reference block: Claude Code, Codex, Cursor, Gemini/Antigravity, Copilot; OpenCode caveat (no slash surface). | Workshop attendees on Cursor/OpenCode. |
| Advanced `--workspace` / `--platforms` | body copy | MOVE TO DISCLOSURE | Reference. | |

### Foundations (`#page-foundations`)

| Block | Current | Disposition | Destination | Learning purpose |
|---|---|---|---|---|
| Page keep | `#page-foundations` | KEEP | Rewritten in Phase 4. | Model vs harness. |
| H1 How AI actually works | | MERGE | Model, agent/platform, harness. | Three roles. |
| Two questions / two ladders | capability ladder + engineering disciplines | MOVE TO DISCLOSURE | "Go deeper" glossary. | Supporting concepts. |
| Model -> reasoning -> agent | including animated terminals | MERGE | Three-role model. Terminal typewriter MOVE or REMOVE (decorative). | Brain / hands. |
| Prompt -> context -> harness | including before/after terminals | MERGE | Harness as experience. Before/after becomes the Phase 4 slider, user-initiated, not cinematic. | |
| Nexus-Hub is harness engineering | building-block cards | MERGE | Concrete software example per role. | Nexus-Hub does not retrain the model. |
| Recap "Say each one in a sentence" | | MOVE TO DISCLOSURE | Glossary. | |
| Raw agent vs agent on Nexus-Hub cards | | MERGE | Slider states. | Causal attribution. |
| Handoff | none today | KEEP (new) | `#training` only. No scene id until Phase 5. | |

### Training (`#page-training`)

Page KEEP as the IDE workbench host. `.nht` / `.ts-slide` 31-slide stage REMOVE as the page model. Fullscreen control REMOVE (Later). Autoplay remains out of scope.

| Slide | `data-tt` | Disposition | Destination |
|---|---|---|---|
| 1 | Nexus-Hub | REMOVE | Covered by Home + Foundations. |
| 2 | What it is | REMOVE | Home definition. |
| 3 | Why it matters | REMOVE | Home comparison. |
| 4 | Building blocks | MOVE TO DISCLOSURE | Reference / Foundations glossary. |
| 5 | Guardrails | MERGE | Optional beat inside `/implement` or `/test` (hooks as a gate). |
| 6 | The workflow | MERGE | Scene order is the workflow. |
| 7 | Meet the example | MERGE | Workbench chrome + scene 1 file tree (Trivia Quiz). |
| 8 | What it needs | MERGE | `/describe` and `/review` beats (bugs + shuffle). |
| 9 | Follow along | MERGE | Home/Training aside: download `trivia-quiz.zip`. KEEP the ZIP link. |
| 10-11 | /describe + result | MERGE | Scene `describe`. |
| 12-13 | /review + result | MERGE | Scene `review`. |
| 14-15 | /plan + result | MERGE | Scene `plan`. |
| 16-17 | /implement + result (bugs) | MERGE | Scene `implement` beats 0-n (fix scoring and restart). |
| 18-19 | /compare + result | MERGE | Scene `compare`. |
| 20-21 | /plan from-comparison + result | MERGE | Beat inside scene `compare` (not a ninth scene). |
| 22-23 | /implement + result (shuffle) | MERGE | Later beats of scene `implement` or a second implement beat cluster still inside the one `implement` scene. Prefer: `implement` shows bugfix; shuffle lands as the last beats of `implement` after compare? Plan order is describe, review, plan, implement, compare, test, update, presentify. Shuffle implement currently happens AFTER compare. Put shuffle in `compare` last beats plus a note that `/implement` runs again, OR keep shuffle as beats at the end of `implement` after a compare callback. **Decision**: scene `implement` covers the first `/implement` (bugs). Scene `compare` includes `/plan from-comparison` and a beat that the next `/implement` (shuffle) is run the same way. Do not add a ninth scene. Shuffle file changes appear in `compare` artifact / file_state as the adopted outcome, with `test` verifying both. |
| 24-25 | /test + result | MERGE | Scene `test`. |
| 26-27 | /update + result | MERGE | Scene `update`. |
| 28 | Summary | REMOVE | Workbench outline plus Home ribbon. |
| 29-30 | Document and present / presentify result | MERGE | Scene `presentify`. |
| 31 | Apply it | REMOVE | Foundations handoff already sent the visitor here; Home next actions cover "use it on your repo". |

### Workflow pages

| Page | Disposition | Notes |
|---|---|---|
| explore | KEEP | Map `/describe` + `/review`. TaskFlow fiction may remain; Training is Trivia Quiz. Do not drop the page. |
| plan | KEEP | `/plan`, `/compare` mention OK. |
| build | KEEP | `/implement`. |
| harden | KEEP | `/test`. |
| ship | KEEP | `/update`. |
| communicate | KEEP | `/presentify`. Required by the Home ribbon. |

Phase 2 restyles the shell around these pages. This plan does not rewrite their TaskFlow copy unless a later phase needs a fixture fix.

### Reference (`#page-reference`)

| Block | Disposition | Notes |
|---|---|---|
| Nav label Cheatsheets | MERGE | Rename to Reference. |
| Golden path flow | MERGE | Align to six nodes including communicate. Current flow skips communicate. |
| Command cheatsheet tables | KEEP | Add `/org`, `/tune-prompting`, explicit alias rows. |
| Getting started install commands | KEEP as secondary | Canonical copy lives on Home; keep matching constants. "Full walkthrough on the Setup page" REMOVE. |
| First five minutes | MERGE | `/skills list` as first verify. |

---

## Training scene schema

Maintainer source of truth: `guides/website/example/training-scenes.json` (Phase 5). Published HTML inlines a verified copy in `<script type="application/json" id="nh-training-scenes">`.

### Workbench panes (one reusable shell)

- Repository explorer (changed-file states)
- Editor / diff / Markdown artifact / test view
- Assistant conversation (slash command, narration, tool events)
- Terminal / test output
- Artifact preview
- Command timeline
- Human decision gate

Controls in scope for Phase 5: previous, next, reset, outline, copy, reduced-motion static. Out of scope: autoplay, speed, fullscreen, workshop/self-guided dual modes.

`applyState(scene, beat)` is idempotent: given the same `(sceneId, beatIndex)` it renders the same complete snapshot whether the entry was next, previous, outline jump, back/forward, or a cold URL. It does not depend on the previous beat. Scenes are snapshots, not deltas.

`next_scene` is the following scene id (or null on the last scene). It is not a playback beat. Beats are the ordered `beats` array. `next_step` as a field name is forbidden to avoid colliding those meanings; use `gate.prompt` for the human decision and `next_scene` for the following scene.

### Schema fields

Each scene object:

| Field | Type | Meaning |
|---|---|---|
| `id` | string | One of: describe, review, plan, implement, compare, test, update, presentify |
| `stage` | string | Short stage label (Understand, Evaluate, ...) |
| `intent` | string | One-sentence visitor takeaway |
| `command` | string | Slash command shown, e.g. `/describe full` |
| `prompt` | string | User-visible prompt text (copyable) |
| `assistant_events` | array | Narration lines; render via textContent |
| `tool_events` | array | Tool names + one-line purpose |
| `file_state` | object | Snapshot: `{ path, status: unchanged\|changed\|added\|deleted, excerpt? }[]`. Excerpts plus paths into `guides/website/example/`. Do not inline a full tree per scene. |
| `editor_state` | object | `{ path, mode: source\|diff\|markdown\|test, body }` |
| `terminal_state` | object | `{ lines: string[] }` |
| `artifact` | object | `{ path, kind, summary }` durable output |
| `gate` | object | `{ name, status: pass\|fail\|hold, prompt }` quality gate |
| `next_scene` | string or null | Next scene id |
| `duration` | number | Presentation-only hint in ms; ignored under reduced motion; never starts a timer in Phase 5 |
| `beats` | array | Ordered beats |

Each beat:

| Field | Type | Meaning |
|---|---|---|
| `index` | number | 0-based |
| `claim` | string | Prose claim for this beat |
| `panes` | string[] | Which panes change (`explorer`, `editor`, `assistant`, `terminal`, `artifact`, `timeline`, `gate`) |
| `takeaway` | string | One-line takeaway |
| `overrides` | object | Optional field patches applied on top of the scene snapshot for this beat. `applyState` still returns a full snapshot. |

Hostile strings (`<img onerror>`, `</script>`) in any string field must render as literal text.

### Trivia Quiz mapping (eight scenes)

Example truth: `guides/website/example/trivia-quiz/` (score helper stops one short; restart keeps answers; shuffle is the feature to add). Compare target: `guides/website/example/quiz-shuffle-reference/`. Download: `guides/website/trivia-quiz.zip`.

| id | command | Artifact | Human decides | Why next follows | Pane changes (summary) |
|---|---|---|---|---|---|
| describe | `/describe full` | `docs/.../analysis.md` (or example-relative path shown in the scene) | Accept the map; do not edit yet | You cannot review what you have not mapped | explorer highlights tree; editor shows report; assistant runs describe; terminal lists scan; gate: report exists; next_scene review |
| review | `/review` | review report; findings: score-off-by-one, restart leak, missing tests, no shuffle | Confirm findings; pick a fix scope | Findings become a plan, not a drive-by edit | editor report; terminal tools; gate: findings listed; next_scene plan |
| plan | `/plan feature` | plan file, one phase, local-commit / no-push-until-final, optional `/route` beat | Approve phase 1 scope (bugs only, no shuffle yet) | Implementation is per phase | editor plan; timeline; gate: DoD written; next_scene implement |
| implement | `/implement` (bugfix phase) | `logic.js` score + restart fixes; tests added as the phase requires | GO/NO-GO on the phase; no push | Compare is how shuffle is sourced, not guessed | explorer changed files; editor diff; terminal checks; gate: phase commit local; next_scene compare |
| compare | `/compare ../quiz-shuffle-reference` | comparison report; beat: `/plan from-comparison`; shuffle adoption | Adopt shuffle from the reference, reverse-engineer first | Test the combined result | editor comparison; artifact plan-from-comparison; next_scene test |
| test | `/test unit` | Vitest run, coverage to threshold | Accept coverage or extend | Ship only after tests | terminal test output; gate: pass + coverage; next_scene update |
| update | `/update` | changelog / commit / release gated on green integration | Release or stop | Communicate the result | editor changelog; gate: green integration; next_scene presentify |
| presentify | `/presentify` | self-contained HTML briefing | Hand the HTML to a stakeholder | Tour ends | artifact preview of HTML; gate: file exists; next_scene null |

No scene depends on live AI or network. Simulated timing is presentation-only and must not run under `prefers-reduced-motion` or when `document.hidden`.

### `applyState(scene, beat)` contract

```
applyState(sceneId, beatIndex) -> snapshot
```

- Resolves scene from the JSON array by `id`. Missing / unknown -> scene 1 (`describe`) beat 0, URL rewrite.
- Clamps beat to `[0, beats.length-1]`.
- Builds a full snapshot from the scene object plus that beat's `overrides`.
- Writes every pane from the snapshot (including panes that did not change).
- Uses `textContent` / `createTextNode` for all fixture strings.
- Does not call `innerHTML` with scene data.
- Does not `pushState` for beat ticks.
- Returns the snapshot so tests and the live region can describe it.

---

## Phase ownership

| Concern | Owner |
|---|---|
| Page shell, theme, page hash, constellation | Phase 2 |
| Home copy, install, ribbon, untrusted-origin warning | Phase 3 |
| Foundations roles + slider + `#training` handoff | Phase 4 |
| JSON fixtures, workbench, scene/beat URL | Phase 5 |
| README, publication check, product-currency | Phase 6 |
| Human QA, Lighthouse a11y, workshop study | Phase 7 |

## Catalog command verification (T003)

Listed from `catalog/commands/` on 2026-08-29: `commit`, `commands`, `compare`, `constitution`, `describe`, `implement`, `memory`, `org`, `plan`, `presentify`, `research`, `review`, `route`, `session`, `setup`, `skills`, `spec`, `test`, `tune-prompting`, `update`, `usage`. Each has a row in the frozen inventory. No extra Training scene added.

---

# v4.2.1 contract (dated 2026-08-29)

**Plan**: `docs/releases/v4/v4.2/plans/v4.2.1-guide-visual-education.md`
**Supersedes**: every v4.2.0 freeze in this file that conflicts with the tables below, especially `nav=slides` reject, cinematic reject, Training-as-workbench, Trivia Quiz as the taught example, and Workflows plus Reference as separate primary pages.
**Do not re-litigate**: Cheatsheets as the merged tab name; Glow Booth as the taught example; the closed eight-command Training set; the single-file offline contract; no CDN; no video; no copy of `scroll-scrub-engine.js`.

A later agent can implement Phases 2-6 from this section without the chat transcript. Copy the tables; do not paraphrase them into "use presentify".

## Presentify inherit / reject (v4.2.1)

v4.2.0 rejected `nav=slides` as the Training page model and rejected cinematic motion for this HTML file. v4.2.1 un-freezes both, with limits.

| Capability | Guide use | Reason |
|---|---|---|
| `nav=scroll` | Inherit for Home, Foundations, Cheatsheets | Those pages remain a scrolling field guide |
| `nav=slides` inside Training only | Inherit with a cap | Maintainer asked to keep slideshow capability. Whole-site slide routing stays rejected |
| `applyState(scene, beat)` idempotence, fragment beats, key-disengage, `replaceState` for beat ticks | Inherit | Cold URLs must render a full snapshot |
| Rich before/after, pinned graphic, click-to-swap visual states | Inherit for Foundations | Replace the range slider as the hero comparison |
| Scroll-driven / cinematic *patterns* (pinned stage, progress-linked illustration, reveal) | Inherit for Home and Foundations | User asked for presentify-like motion. CSS/JS only. No video. One loop maximum |
| Copying `scroll-scrub-engine.js` or embedding video clips | Reject | Size, offline budget, and reduced-motion deletion of video |
| `design_seed` uniqueness / entropy | Reject | The guide must still match the portfolio, not look new every generation |
| html-output-conventions, hallmark-design, visual-QA viewports | Inherit | Offline, no CDN, reduced-motion static equivalents |
| `/presentify` as a taught command | Keep | Cheatsheets lists `--nav` and `--interactivity` flags. Training closer still produces the HTML artifact |

**Cinematic means**: local CSS and JS that update illustration states from scroll progress (pinned or sticky stages, reveal classes, progress-linked SVG frames). It does **not** mean copying `scroll-scrub-engine.js`. It does **not** mean `<video>` clips, hosted media, or a camera fly-through. Under `prefers-reduced-motion: reduce`, show the completed frames with no motion.

**`nav=slides` means**: previous/next (and optional Home/End, swipe) change Training slides only while the page is `training` and focus is not inside an interactive region. Arrow keys never change the primary page. Whole-site slide routing stays rejected.

## Visual QA ledger (ten closed defects)

These are closed defects from maintainer screenshots dated 2026-08-29, not suggestions. Phase 2 clears items 1-6. Phase 3 clears item 7. Phase 4 clears items 8-9. Phase 5 clears item 10. Phase 7 human testing re-checks all ten.

1. Sticky header must be opaque in both themes (no constellation bleeding through).
2. GitHub control is icon-only.
3. Theme control is sun/moon, default dark.
4. Copy control is at the right end of the terminal box.
5. Light-theme terminals are light, including the copy chip.
6. Light-theme wordmark is readable (Nexus is not white on beige).
7. Home loop nodes are not a row of rigid squared boxes.
8. Foundations comparison is not a range slider plus two plain text columns.
9. Foundations is not three identical text cards as the educational core.
10. Training is not a text-heavy IDE workbench as the default view.

## Nav and Cheatsheets IA

Primary nav: **Home, Foundations, Training, Cheatsheets**. Installation is not a primary page. GitHub is an external icon control. Theme is a sun/moon toggle.

The merged tab is named **Cheatsheets**. Not Workflows. Not Reference.

Cheatsheets has three bands, in this order:

1. Loop overview (the same six stops as Home: Map and evaluate, Plan, Implement, Harden, Ship, Communicate). Visual, not a second squared ribbon.
2. Command cheatsheet with **real** arguments from `catalog/commands/*.md`. Do not invent flags.
3. Extra workflow notes only when they add something Training does not already show; otherwise link to the Training scene.

Home ribbon versus Cheatsheets (commands shown on Home stay the same; deep links retarget):

| Home node | Commands shown | Deep link |
|---|---|---|
| Map and evaluate | `/describe`, `/review` | `#cheatsheets/explore` or Training describe |
| Plan | `/plan` | `#cheatsheets/plan` |
| Implement | `/implement` | `#cheatsheets/build` |
| Harden | `/test` | `#cheatsheets/harden` |
| Ship | `/update` | `#cheatsheets/ship` |
| Communicate | `/presentify` | `#cheatsheets/communicate` |

Do not invent a seventh review page. Do not drop communicate. The ribbon CTA may open Training at that command's slide when the teaching is already on Training; Cheatsheets holds the argument table.

## Command inventory (unchanged placement, Cheatsheets replaces Reference)

Copied from the v4.2.1 plan. New catalog commands that land after this plan is confirmed do not require new Training scenes. Cheatsheets inherits every row that v4.2.0 put in Reference.

| Command | Placement | Reason |
|---|---|---|
| `/describe` | Training scene | Daily loop start |
| `/review` | Training scene | Daily loop |
| `/plan` | Training scene | Daily loop |
| `/implement` | Training scene | Daily loop |
| `/compare` | Training scene | Daily loop |
| `/test` | Training scene | Daily loop |
| `/update` | Training scene | Daily loop |
| `/presentify` | Training scene (communicate closer) | Visitor sees the durable HTML artifact |
| `/spec` | Cheatsheets | Optional beat inside `/plan` |
| `/constitution` | Cheatsheets as alias of `/spec constitution` | Permanent alias |
| `/setup` | Cheatsheets | Post-install bootstrap |
| `/skills` | Cheatsheets | First verify step after install |
| `/commands` | Cheatsheets as alias of `/skills list` | Permanent alias |
| `/route` | Cheatsheets | Optional beat inside `/plan` and `/implement` |
| `/session` | Cheatsheets | Session hygiene |
| `/commit` | Cheatsheets as alias of `/update commit` | Permanent alias |
| `/memory` | Cheatsheets; declined as Training | Maintenance |
| `/usage` | Cheatsheets; declined as Training | Host-specific |
| `/research` | Cheatsheets; declined as Training | Adjacent to compare |
| `/org` | Cheatsheets; declined as Training | Optional org layer |
| `/tune-prompting` | Cheatsheets; declined as Training | Specialist calibration |

Closed Training set: eight scenes, hard cap **twelve** slides (v4.2.0 said ten; v4.2.1 raises the cap so an intro or outro can exist without a ninth command). Scene order: describe, review, plan, implement, compare, test, update, presentify. Intro or outro slides count toward the cap and must not add a ninth command.

## URL grammar and compatibility rewrites

- Pages: `home`, `foundations`, `training`, `cheatsheets`. Unknown page id maps to `home` and rewrites the URL.
- Compatibility rewrites (`replaceState`, no extra history): `#reference` and `#workflows` to `#cheatsheets`. `#explore`, `#plan`, `#build`, `#harden`, `#ship`, `#communicate` to `#cheatsheets/<id>` when those were page ids, or to Cheatsheets plus the matching section id.
- Training: `#training/<scene-id>` with optional `?beat=<n>` via `replaceState`. `#training` loads slide 1.
- ArrowLeft / ArrowRight / Space on Training change slides only while the page is `training` and focus is not inside an interactive region. They never change the primary page.
- `#home/install` still scrolls to `#nhg-install`.

Allowlisted `data-go` after Phase 6: `home`, `foundations`, `training`, `cheatsheets`, plus Cheatsheets section ids used as `cheatsheets/explore` (or equivalent that the router accepts). Workflow page sections `page-explore` through `page-communicate` and `page-reference` are removed from primary nav and from `PAGES`.

Trust boundary is unchanged from v4.2.0: `textContent` / `createTextNode` for fixture strings; inline JSON in `<script type="application/json">` with `</script>` encoded; `portfolio-theme` accepts only `light` or `dark`; wrap `localStorage` in try/catch; no runtime CDN, fonts, analytics, or fetch.

## Glow Booth spec

Published teaching uses **Glow Booth**, not Trivia Quiz. No quiz copy. No Trivia Quiz branding in the published guide. Keep `guides/website/example/trivia-quiz/` on disk until Phase 7 confirms nothing published still points at it.

### Files

| Path | Role |
|---|---|
| `guides/website/example/glow-booth/index.html` | Self-contained booth. Open from disk. No bundler. |
| `guides/website/example/glow-booth/` CSS/JS as needed | Same folder. Vanilla only. No CDN. |
| `guides/website/example/glow-booth-shuffle-reference/` | Local `/compare` target that already has Shuffle poses plus sparkle-stamp overlay. |
| `guides/website/glow-booth.zip` | Downloadable bundle. Point the guide download link here in Phase 5. |
| `guides/website/example/trivia-quiz/` | Stay on disk. Do not teach it. |

### Product (frozen)

Glow Booth is a tiny vanilla HTML/CSS/JS instant-camera booth: a large live-looking stage, a film-strip of poses, and stamp counts.

**Frozen defects** (the buggy starting app):

1. Off-by-one stamps: a perfect set of poses awards **4/5** stamps.
2. Restart leak: the last pose remains visible after Restart.

**Frozen fun feature** (after the fix, taught via `/compare` then a second `/implement` beat that must not become a ninth scene): Shuffle poses plus a sparkle-stamp overlay.

### Training scene map (eight scenes, hero is the booth stage)

Hero view is the booth transforming. Assistant / file / terminal content lives behind an optional "Peek at the files" disclosure.

| id | command | Booth hero | Bugs / feature shown | Peek (optional) | Why next follows |
|---|---|---|---|---|---|
| describe | `/describe` | Full booth: stage, five pose slots, stamp meter reading 4 on a perfect set | Both bugs visible as the current app | describe report | You cannot review what you have not mapped |
| review | `/review` | Callouts on the stamp meter (4/5) and the ghost pose after Restart | Findings listed | review report | Findings become a plan |
| plan | `/plan` | Same booth, overlay of the two bug fixes (not shuffle yet) | Scope: stamps + restart only | plan file | Implementation is per phase |
| implement | `/implement` | After GO: stamp meter 5/5, Restart clears the last pose | Bugs fixed | diffs | Compare is how shuffle is sourced |
| compare | `/compare` | Side-by-side or swap: current booth vs reference with Shuffle + sparkle | Adopt shuffle + sparkle; beat `/plan from-comparison`; the follow-up `/implement` is a beat, not a ninth scene | comparison report | Test the combined result |
| test | `/test` | Booth still visual; tests pass | Coverage on stamp math and restart | test output | Ship only after tests |
| update | `/update` | Changelog overlay on the booth chrome | Release gated on green integration | changelog | Communicate the result |
| presentify | `/presentify` | Durable HTML briefing of the booth story | presentify HTML | Tour ends |

Shuffle after compare stays inside the closed eight-scene set (compare beats plus the note that `/implement` runs again). Do not add a ninth scene.

No autoplay. Hard cap twelve slides. Prefer eight visual slides with beats rather than a 31-slide text deck.

## Four Foundations stations

Lead with a visual stack, then four interactive stations. Model / platform / harness remain a **visual layer stack**, not three identical essays. Trivia Quiz must not appear in Foundations copy.

Layer stack (pictures first):

1. **Model** (brain): the language model.
2. **Platform** (hands): the agent that can read files and run tools.
3. **Harness** (experience): reusable procedures, hooks, and gates around that agent.

Four stations (visible without opening a `<details>` dump). Each: short title, one sentence, original inline SVG or CSS illustration the user can click/tap for a before/after on Glow Booth.

| Station | One-line definition | Glow Booth worked example |
|---|---|---|
| Prompt engineering | Wording one request. | Same booth, two prompts: a vague "fix it" versus a specific "the stamp meter counts 4 on a perfect set". |
| Context engineering | Choosing what the model sees. | Booth files in vs out of context: `app.js` stamp helper included or omitted. |
| Harness engineering | Reusable procedures, hooks, and gates. | `/review` then `/plan` then `/implement` as a saved path, not a one-off chat. |
| Loop engineering | The repeating six-stop working method. | Map and evaluate through Communicate on this booth. |

Comparison (replaces `#nhgHarnessRange`): visual two-state control of "model alone" versus "model with Nexus-Hub" on the Glow Booth stamp bug. Both states stay in the DOM for no-JS and screen readers. Not a `type="range"` hero. Not two plain methodology columns. Causal attribution stays fair (not a straw man). Keys used by Training disengage when this control is focused. Handoff to `#training` (page hash, no scene id in the Foundations CTA). The exact heading `Now watch the experience layer work` may stay or become a shorter equivalent that still links to `#training`.

## Token-role updates Phase 2 must apply

The v4.2.0 token table left `--nav-bg` translucent and terminal tokens dark in light theme. Phase 2 must:

| Role | Light (required) | Dark | Notes |
|---|---|---|---|
| navigation | solid (no alpha), e.g. `#f3f1ea` | solid, e.g. `#07141a` | Opaque sticky header. Not `rgba(..., .92)` / `.94`. |
| wordmark "Nexus" | `var(--ink)` | `var(--ink)` | Never hardcoded `#fff` on `.wordmark b`. Hub may stay `var(--accent)` if contrast holds. |
| terminal background | light surface | dark terminal OK | Light theme must not reuse `#1c2a2e` / `#07171d`. |
| terminal text | dark ink on the light terminal | light ink | |
| copy chip | light-theme chip on the light terminal | may stay dark-on-dark | Pin to the **right edge of the terminal panel**, not inside `code[data-copy]`. |

Default with no `portfolio-theme` key is **dark**. Persist only `light` or `dark`.

## Tests that invert in v4.2.1

Do not change `tests/guides/test_nexus_hub_guide.py` in Phase 1. Focused tests must still pass against unmodified v4.2.0 markup. Phase 2+ rewrites the assertions below rather than xfailing them forever.

| Current test | Why it inverts | Replacement assertion (one sentence) | First rewrite phase |
|---|---|---|---|
| `test_training_workbench_is_not_a_slide_deck` | Requires `#nhWorkbench` and forbids `.ts-slide`. | Training has a slide/stage runtime (previous/next, eight scene ids, cap of twelve) and the default view is not an IDE workbench grid. | 5 |
| `test_hostile_fixture_strings_are_present_for_textcontent` | Requires `els.editor.textContent` as the workbench renderer. | Hostile strings remain in JSON; peek/editor text (when present) is assigned with `textContent`, not `innerHTML`. | 5 |
| `test_foundations_has_user_initiated_comparison` | Requires `type="range"` / `nhgHarnessRange`. | Primary comparison is not `type="range"`; a visual two-state control exists; `scroll-scrub-engine` is still absent. | 4 |
| `test_foundations_three_roles` | Treats three role cards as the educational core. | Visible (not collapsed-details-only) labels exist for prompt engineering, context engineering, harness engineering, and loop engineering. | 4 |
| `test_foundations_comparison_states_are_static_in_markup` | Requires `#nhgRawPane`, `#nhgHubPane`, and `data-nhg-keys="self"`. | Both comparison states remain in markup; those range-slider ids are not required. | 4 |
| `test_foundations_handoff_is_training_page_hash` | Exact heading `Now watch the experience layer work`. | A `#training` (not `#training/`) handoff remains; the heading may be that string or a shorter equivalent. | 4 |
| `test_no_installation_in_primary_nav` | Only forbids Installation; still allows Workflows and Reference. | Primary nav includes Cheatsheets and does not include Installation, Workflows, or Reference as primary labels. | 6 |
| `test_every_catalog_command_is_training_reference_or_declined` | Splits on `id="page-reference"`. | Rename and point the lookup at Cheatsheets markup (plus README / this content map). | 6 |
| `test_internal_data_go_targets_exist` | Treats `explore`/`plan`/`build`/`harden`/`ship`/`communicate` as page ids. | After Phase 6 those ids must resolve as Cheatsheets sections or Training, not missing `page-*` sections. | 6 (selectors may need a Phase 3 update if Home `data-go` changes first) |
| `test_home_has_six_node_preview_including_communicate` | Asserts `data-go="communicate"` and the six workflow ids on Home. | Keep six nodes, `Map and evaluate`, communicate, and `/presentify`; update selectors if class names change, not the six-stop contract. | 3 |
| `test_example_zip_link_present` | Requires `trivia-quiz.zip`. | If the download href changes, require `glow-booth.zip` (or the documented zip name) instead. | 5 |
| `test_website_readme_matches_redesign` | Documents Trivia Quiz, workbench, Installation-is-not-a-page, and Workflows/Reference. | README matches Cheatsheets, Glow Booth, slideshow Training, and still forbids a 31-slide deck, autoplay, and hardcoded catalog counts. | 5-6 |
| `test_theme_toggle_exists` / `test_github_is_user_initiated_not_a_script` | Too weak for the screenshot defects. | Add: GitHub is icon-only with accessible name; theme is sun/moon; default-dark when storage is empty; `.wordmark b` is not hardcoded `#fff`; copy button is not a descendant of `code[data-copy]`; light-theme `--term-bg` is not the dark-theme near-black. | 2 |

Tests that **must keep passing** without invert (unless a selector-only update is required): `test_one_html_document`, `test_ids_are_unique`, `test_no_runtime_cdn_font_script_or_image`, `test_portfolio_theme_allowlisted`, `test_page_url_hash_uses_first_segment`, `test_reduced_motion_pauses_constellation`, `test_home_contains_both_canonical_install_commands`, `test_home_install_copy_payload_equals_visible_text`, `test_no_stale_setup_route_in_markup`, `test_onboarding_has_no_hardcoded_catalog_counts`, `test_training_scenes_are_data_driven_json`, `test_every_scene_exposes_gate_and_next_scene`, `test_script_close_in_fixture_does_not_break_document`, `test_inline_scenes_match_example_json`, `test_publication_check_self_contained_and_offline`, `test_optional_portfolio_copy_when_env_set`.

## Phase ownership (v4.2.1)

| Concern | Owner |
|---|---|
| Opaque nav, icon GitHub, sun/moon, wordmark, copy layout, light terminals | Phase 2 |
| Home loop graphic (six stops, `Map and evaluate`) | Phase 3 |
| Four-station Foundations, visual comparison, scroll/cinematic *patterns* | Phase 4 |
| Glow Booth app, zip, Training slideshow, scene JSON | Phase 5 |
| Cheatsheets merge, hash redirects, README | Phase 6 |
| Trivia Quiz published-reference sweep, evidence, publication | Phase 7 |

## Token reminder for later agents

- Do not import video.
- Do not copy `scroll-scrub-engine.js`.
- Do not keep Trivia Quiz in published teaching copy.
- Do not invent command flags.
- Do not author GitHub Actions in Phases 1-6.
- Do not push, open a pull request, or start remote CI until Phase 7 with explicit approval.
