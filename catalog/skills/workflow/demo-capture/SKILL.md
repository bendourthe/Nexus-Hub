---
name: demo-capture
description: "Capture LOCAL visual evidence of a change for a pull request - a terminal recording / GIF for CLI and TUI work, or a headless-browser screenshot for web work - written to a local docs/demos/ directory only. Make sure to use this skill whenever the user says \"record a demo\", \"capture a demo\", \"make a GIF of this\", \"screenshot the app for the PR\", \"show this working in the PR\", \"attach visual evidence\", \"demo reel\", \"record the terminal\", or otherwise wants visual proof of a change attached to a change request. It is script-first (a bundled local capture script drives asciinema / ffmpeg / a headless browser) and strictly local: it has NO upload, hosting, or approval step. SKIP, do NOT use for, generating image assets or mockups from a prompt (use creative-generation / ui-component-generation), authoring the PR description text (use pr-description-writer), running the app to verify behavior (use the run / verify skills), or any flow that uploads, hosts, or shares the captured media externally."
summary_l0: "Capture local terminal/GIF/screenshot PR evidence into docs/demos, script-first and upload-free"
overview_l1: "Captures visual evidence of a change for a pull request using LOCALLY-installed tools and writes it to a local docs/demos/ directory only - it never uploads, hosts, or shares the media (the upstream upload/approval surface is deliberately dropped). It is script-first: the bundled scripts/capture-demo.{py,ps1} probe which capture tools are present (asciinema/termtosvg for terminal recording, agg/ffmpeg for GIF conversion, a Chromium-family browser for headless web screenshots), detect the project type, and pick a capture tier (terminal-recording for CLI/TUI/API work, browser-screenshots for web work). The script degrades gracefully: when a needed tool is absent it reports which tool to install and exits 0 rather than failing. Trigger phrases: record a demo, capture a demo, make a GIF of this, screenshot the app for the PR, show this working in the PR, attach visual evidence, demo reel."
---

# Demo Capture

Attach visual proof that a change works to its pull request: a terminal recording or GIF for CLI/TUI/API work, or a headless-browser screenshot for web work. The evidence is written to a local `docs/demos/` directory and nothing is ever uploaded, hosted, or shared by this skill.

It is **script-first**: the bundled `scripts/capture-demo.py` / `scripts/capture-demo.ps1` do the work (tool detection, project-type-aware tier selection, and the actual capture). The agent runs the script, reads its JSON output, and reports what was captured or which tool to install. Everything is local and zero-outbound.

**The upload / approval / hosting step is intentionally dropped.** This skill is the local-capture half of a demo-reel workflow only. If you need to share the artifact, attach the file from `docs/demos/` to the PR by hand - the skill will never transmit it for you.

## When to Use This Skill

Use when:

- The user asks to "record a demo", "capture a demo", "make a GIF of this", or "screenshot the app for the PR".
- A pull request would be clearer with visual evidence (a CLI run, a TUI flow, a rendered web page).
- The user says "show this working in the PR", "attach visual evidence", or "demo reel".
- You have just finished a change and want to attach proof it works to the change request.

**When NOT to use:**

- Generating image assets, icons, or UI mockups from a text prompt - use [[creative-generation]] / [[ui-component-generation]].
- Writing the PR description prose - use [[pr-description-writer]].
- Running the app to confirm a fix behaves correctly (verification, not evidence capture) - use the `run` / `verify` skills.
- Any flow that uploads, hosts, or shares the captured media with an external service. This skill is local-only by design (see the Common Rationalizations table).

## Architecture (script-first)

| Step | Component | Role |
|---|---|---|
| Probe | `scripts/capture-demo.py --mode probe` / `scripts/capture-demo.ps1 -Mode probe` | Detect available tools, classify the project, recommend a capture tier; print a JSON plan. No tool is invoked. |
| Capture | `scripts/capture-demo.py --mode capture` / `scripts/capture-demo.ps1 -Mode capture` | Drive the local capture for the recommended tier into `docs/demos/`; report what was captured or skipped. |
| Present | This skill (the agent) | Tell the user which artifact was written (or which tool to install), and remind them to attach it to the PR manually. |

The `.py` and `.ps1` scripts have identical behavior (cross-platform parity rule). They import no network module and open no connection.

### Capture tiers

| Project type | Tier | Tools (any one) | Artifact |
|---|---|---|---|
| `web` | browser-screenshots | a Chromium-family browser (chromium / google-chrome / msedge) | `<slug>.png` |
| `cli`, `tui`, `api`, `generic` | terminal-recording | `asciinema` (+ `agg`/`ffmpeg` for GIF) | `<slug>.cast` (+ `<slug>.gif`) |

The script auto-detects the project type from `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `index.html`, and a `bin/` directory; override with `--type` / `-Type`.

## Instructions

### 1. Probe first

Always probe before capturing so you know which tier applies and which tools are present:

```bash
# POSIX
python catalog/skills/workflow/demo-capture/scripts/capture-demo.py --mode probe
```

```powershell
# Windows
pwsh catalog/skills/workflow/demo-capture/scripts/capture-demo.ps1 -Mode probe
```

Read the JSON plan: `project_type`, `recommended_tier`, `available_tools`, and `blocking_capabilities`. If `blocking_capabilities` is non-empty, surface the matching `install_hints` entry to the user and stop - do not pretend a capture happened.

### 2. Capture

Run capture mode for the recommended tier. For web work, point at the running app's URL; for CLI/TUI work, pass the command to record:

```bash
# POSIX - web screenshot
python catalog/skills/workflow/demo-capture/scripts/capture-demo.py --mode capture --type web --url http://localhost:3000 --name login-flow

# POSIX - terminal recording of a command
python catalog/skills/workflow/demo-capture/scripts/capture-demo.py --mode capture --type cli --cmd "mytool --help" --name help-output
```

```powershell
# Windows
pwsh catalog/skills/workflow/demo-capture/scripts/capture-demo.ps1 -Mode capture -Type web -Url http://localhost:3000 -Name login-flow
pwsh catalog/skills/workflow/demo-capture/scripts/capture-demo.ps1 -Mode capture -Type cli -Cmd "mytool --help" -Name help-output
```

The result JSON lists `captured` artifacts (path + tool) and `skipped` capabilities (reason + install hint). Artifacts land under `docs/demos/`.

### 3. Present and hand off

Tell the user which file was written under `docs/demos/` and remind them to attach it to the PR themselves - the skill does not and will not upload it. If the capture was skipped because a tool is missing, report the install hint verbatim and offer to retry after they install it.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll upload the GIF to a host and paste the link into the PR" | Out of scope and policy-prohibited. This skill is the local-capture half only; the upload/approval/hosting surface is deliberately dropped. Write the artifact to `docs/demos/` and let the user attach it. Adding an uploader introduces an outbound call and a credential the MCP Registry Policy rejects. |
| "No capture tool is installed, so I'll describe the demo in prose instead" | The script already reports which tool to install and exits 0. Surface that hint to the user; do not silently substitute a prose description for the visual evidence they asked for. |
| "I'll hand-glob and shell out to ffmpeg myself instead of running the script" | The script-first design centralizes tool detection, tier selection, and graceful degradation. Re-implementing it inline drops the degradation path and the parity guarantee. Run `capture-demo`. |
| "The capture failed, I'll just claim it succeeded" | Never. If `captured` is empty, say so and report the `skipped` reason. A fabricated success sends the user looking for an artifact that does not exist. |
| "It's a web app, I'll screenshot a remote production URL" | Capture local evidence of the change under review (typically `localhost`). The point is to prove THIS change works, not to photograph a deployed site. |

## Verification

- [ ] The probe was run first and its JSON plan was read (project type + recommended tier identified).
- [ ] Capture was driven via `scripts/capture-demo.{py,ps1}`, not by hand-invoking ffmpeg / asciinema / a browser inline.
- [ ] Every artifact reported to the user exists under `docs/demos/` (path taken from the script's `captured` list).
- [ ] When a tool was missing, the skill reported the install hint and did NOT claim a capture happened.
- [ ] No artifact was uploaded, hosted, or shared; the script made zero outbound calls.
- [ ] The user was reminded to attach the artifact to the PR manually.

## Related Skills

- [[pr-description-writer]] - writes the PR description prose; pair it with this skill, which produces the visual evidence to attach.
- [[creative-generation]] - generates image assets from a prompt; this skill captures real evidence of a running change instead.
- [[ui-component-generation]] - generates UI component code; unrelated to capturing a demo of an already-built feature.
- [[session-history]] - documents what a session did in text; this skill captures the visual proof to accompany it.
- [[shipping-and-launch]] - the broader ship workflow; demo capture is the evidence step that strengthens a PR before it merges.
