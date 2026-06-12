# Nexus-Hub - Interactive Team Guide

`nexus-hub-guide.html` is a self-contained, interactive training guide for the software team. It walks an engineer through the full Nexus-Hub workflow on a single made-up codebase (TaskFlow), from inheriting the repo to shipping a tested, reviewed release.

## How to open and share it

The guide is a **single HTML file with zero dependencies** - no server, no network, no external assets, nothing to install.

- **To open:** double-click `nexus-hub-guide.html`. It opens in any modern browser and works fully offline via `file://`.
- **To share:** send that one file to a teammate (Slack, email, shared drive). It is the entire guide.
- **From GitHub:** the file is linked from the main [README](../../README.md). GitHub does not render HTML inline, so use the file's **Download raw file** button, then open the downloaded file in a browser.
- **No ZIP required** - but you can zip the single file if your channel prefers an archive.

This `README.md` is for maintainers; it does not need to be shared with the file.

## What's inside

A guided, page-by-page tour that mirrors a live demo:

| Page | Commands shown |
|------|----------------|
| Home | What Nexus-Hub is, why it matters, the golden-path loop |
| Setup & platforms | Install (macOS/Linux/Windows), what lands where, and the cross-platform model (Claude Code, Codex, Antigravity, Cursor, Copilot, Nexus-AI) |
| How it works | Skills (three-tier loading), hooks (live secret-block demo), governance (`/constitution` + `/spec`) |
| Onboard | `/describe` then `/review` - map and evaluate an inherited codebase |
| Plan | `/plan` from findings, and `/compare` an external repo (reverse-engineer-first) |
| Build | `/implement` a phase end-to-end with feature branches and quality gates |
| Harden | `/review security` + `pentest`, supply-chain (`deps` / `sbom` / `skill-scan`), and `/test` to 80% + CI/CD |
| Ship | `/update` docs, refactor, and the atomic `release` flow |
| Reference | Full command cheatsheet, install steps, golden-path recap |

## Navigation

- Click the top nav, the workflow cards, or the prev/next buttons at the bottom of each page.
- Use the left/right arrow keys to move between pages.
- Terminal panes animate on view; click a pane to reveal it instantly, or use the **replay** button.
- Respects `prefers-reduced-motion` (animations are disabled for users who request it).

## Editing

Everything lives in one file: CSS in the `<style>` block, content in `<section data-page="...">` blocks, behavior in the single `<script>` at the bottom. The logo is an inline SVG `<symbol id="nexus-mark">` reused via `<use>`. The simulated VS Code / terminal screenshots are pure HTML/CSS - to swap in a real screenshot later, replace a `.term` or `.vscode` block with an `<img>`.
