# Guide redesign content map

**Date**: 2026-08-29
**Source markup**: `guides/website/nexus-hub-guide.html`
**Plan**: `docs/releases/v4/v4.2/plans/v4.2.0-interactive-guide-redesign.md`
**Baseline**: `docs/releases/v4/v4.2/development/guide-redesign-baseline/`

This file is the working contract for Phases 2-6. Frozen tables below are copied from the plan. Do not paraphrase the inherit/reject table into "use presentify".

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

Current Reference (`#page-reference`) already lists most of these. `/org` and `/tune-prompting` are absent from the live cheatsheet and must be added as Reference rows in Phase 6 (product-currency gate). `/commit`, `/commands`, and `/constitution` appear as aliases in prose; keep them as explicit rows.

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

Allowlisted page ids after Phase 3: `home`, `foundations`, `training`, `explore`, `plan`, `build`, `harden`, `ship`, `communicate`, `reference`. `setup` is removed from `PAGES` after migrating still-useful install detail.

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

| Role | Light (to fill in Phase 2) | Dark (to fill in Phase 2) | Notes |
|---|---|---|---|
| page background | | | softened off-white / near-black |
| elevated surface | | | |
| navigation | | | |
| border | | | |
| primary text | | | |
| secondary text | | | |
| accent | | | cyan/teal from the portfolio constellation, not gradient text |
| focus | | | |
| success | | | |
| warning | | | |
| danger | | | |
| terminal background | | | |
| terminal text | | | |

Current file uses dark-only `--bg-*`, `--ink*`, `--cyan`, `--teal`, `--grad`. `--grad` as text fill is REMOVE.

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
