# Nexus-Hub Interactive Guide and Training

This directory holds the public-facing Nexus-Hub material: the interactive guide (which includes the embedded guided tour) and the example project the tour operates on. Everything is self-contained, opens in a browser, and needs no build step. This `README.md` is for maintainers.

## Contents

| Item | What it is |
|------|-----------|
| `nexus-hub-guide.html` | The interactive guide, including the **Guided tour** page (the embedded training slide-show). The main entry point. |
| `example/trivia-quiz/` | The example app the tour operates on. |
| `example/quiz-shuffle-reference/` | A small reference implementation used as the local target for the `/compare` step. |
| `trivia-quiz.zip` | The downloadable example bundle that learners extract. |

The training is embedded directly in the guide as the **Guided tour** page: a self-contained slide-show with its own outline, prev/next, and fullscreen. The guide is the single home for both the concepts and the hands-on training, and it remains one self-contained HTML file.

## The interactive guide

`nexus-hub-guide.html` is a single HTML file with zero dependencies. No server, no network, no external assets, nothing to install.

- **To open:** double-click the file. It opens in any modern browser and works fully offline.
- **To share:** send that one file. It is the entire guide.
- **From GitHub:** the file is linked from the main [README](../../README.md). GitHub does not render HTML inline, so use the file's Download raw file button, then open it in a browser.

## The guided tour

The guide's **Guided tour** page (reachable from the top nav or the Home call-to-action) leads with what Nexus-Hub is, then walks the full workflow on the example. It is a slide-show embedded in the guide.

- **Navigate:** left and right arrows, or the on-screen arrows.
- **Outline:** the Outline button opens a panel that jumps to any slide.
- **Fullscreen:** the Fullscreen button expands the slide-show.
- **Copy:** each command slide has a Copy button for its prompt.

## The example project (Trivia Quiz)

A small vanilla HTML, CSS, and JavaScript quiz that runs by opening `example/trivia-quiz/index.html`. It works end to end but ships with two intentional bugs and no tests, plus one feature to add:

- A perfect run scores one less than the total (the score helper stops one short).
- Restart keeps the previous answers instead of clearing them.
- Feature to add: shuffle the deck on every run.

The training resolves all three with the loop. `example/quiz-shuffle-reference/` is a small reference implementation that already has the shuffle feature; it is the local target for the `/compare` step. `trivia-quiz.zip` bundles both folders plus a START-HERE note for download.

## Running the training (self-guided)

Prerequisites:

- Nexus-Hub installed so the slash commands resolve. The install is one pasted command, no prompts: `curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash` (macOS / Linux) or `irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1 | iex` (Windows).
- A modern browser to run the app.
- Node 18+ and npm (the `/test` step uses Vitest).

Setup: download `trivia-quiz.zip`, extract it, and open the app in your platform of choice (Claude Code, Codex, Cursor, or any IDE with Nexus-Hub). From the app folder, run `git init` and an initial commit, then `npm install`.

The loop, in order (each prompt is on the matching slide of the Guided tour):

1. `/describe full`
2. `/review`
3. `/plan feature` (goal: fix the two bugs from the review; one phase, no new features)
4. `/implement fix-scoring-and-restart phase-1`
5. `/compare ../quiz-shuffle-reference`
6. `/plan from-comparison docs/v0.1.0/compare-quizkit.md`
7. `/implement shuffle-the-deck phase-1`
8. `/test unit`
9. `/commit`

Troubleshooting: if a slash command does not resolve, reinstall Nexus-Hub and reload the editor. If the `/compare` step cannot find the reference, keep `quiz-shuffle-reference` next to the app (the path is `../quiz-shuffle-reference`). If Vitest is missing at the test step, run `npm install` in the app folder.

## Quick reference (the loop)

| Stage | Command | What it does |
|-------|---------|--------------|
| Understand | `/describe` | Maps a project so you can work in code you did not write |
| Evaluate | `/review` | Finds gaps, smells, and missing tests. Reports, never edits |
| Decompose | `/plan` | Turns a finding into a phased plan with a written definition of done |
| Evaluate | `/compare` | Mines an external source for ideas and writes an adoption plan, reverse-engineer first |
| Build | `/implement` | Builds one phase on a branch: code, checks, gate |
| Harden | `/test` | Drives coverage to the standard (80% by default) |
| Ship | `/update` | Commits cleanly; `/update release` runs the full release |

Reach for the narrowest scope that does the job. That single habit is most of the value.

## Editing

The guide is a single HTML file: CSS in the `<style>` block, content in `<section class="page">` blocks, behavior in the `<script>` blocks at the bottom. The Guided tour is the `#page-training` section plus a self-contained controller script; its styles and markup are all scoped (wrapped in `.nht`, classes prefixed `ts-`) so they cannot collide with the rest of the guide. The example under `example/` is plain files; edit them in place and regenerate `trivia-quiz.zip` from those folders.
