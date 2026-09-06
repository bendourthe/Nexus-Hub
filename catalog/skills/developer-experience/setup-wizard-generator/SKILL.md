---
name: setup-wizard-generator
description: Generate an interactive, resumable shell wizard for human-only sequences - provisioning infrastructure, entering credentials or CI secrets, walking a third-party dashboard, or executing a one-off migration or cutover. Use whenever the user says "walk me through setting up", "guide me through the dashboard", "interactive setup script", "help me do the manual steps", "resumable wizard", or needs a script that presents one human step at a time, waits for confirmation, and validates an observable outcome. SKIP - automated setup the agent can run itself (use setup-project or the init-* skills); grilling the user about a design (use design-interview); a stakeholder questionnaire (use decision-questionnaire). The agent adapts the bundled templates and does not run privileged or secret-bearing steps itself.
summary_l0: "Generate a resumable human-only setup wizard with bash and PowerShell templates"
overview_l1: "Produces an interactive wizard for steps only a human can perform. One step at a time, explain what and why, wait for confirmation, validate an observable (file, command, env var), resume from a state file after interruption. Ship and adapt scripts/wizard-template.sh plus the mandatory scripts/wizard-template.ps1. The agent never runs privileged steps or echoes secrets. SKIP automated setup the agent can execute. Trigger phrases: walk me through setting up, guide me through the dashboard, interactive setup script, help me do the manual steps."
category: developer-experience
---

# Setup Wizard Generator

Generate an interactive, resumable shell wizard for sequences a human must perform: provisioning, credentials, CI secrets, third-party dashboards, one-off cutovers. The wizard presents one step at a time, explains what to do and why, waits for confirmation, validates an observable outcome where possible, and resumes after interruption from a state file.

Adapt the bundled templates. Do not run privileged steps, paste secrets into the log, or replace [[setup-project]] / the `init-*` skills for work the agent can execute itself.

## When to Use This Skill

Use when:

- The remaining work is human-only (a console click, a secret the agent must not see, a vendor dashboard).
- The user asks for a walkthrough, guided setup, or interactive script they can re-run after a drop.
- A cutover needs a checklist that validates "done" instead of hoping the operator remembered.

**When NOT to use:**

- The agent can run the setup (package install, file write, git init). That is [[setup-project]] or the matching `init-*` skill.
- The user wants to be interviewed about a design. That is [[design-interview]].
- The blocker is a decision for someone who is not in the session. That is [[decision-questionnaire]].

## Instructions

### 1. List only human-only steps

Write the step list first. Drop any step the agent can do with tools. If the list becomes empty, stop and use [[setup-project]] instead.

Each kept step needs:

- An id (`kebab-case`)
- What the human does
- Why it is required
- An observable check (file exists, command exits 0, env var is set) or an explicit "no machine check; human confirms"

### 2. Adapt the templates, do not invent a third runtime

Copy and edit:

- `scripts/wizard-template.sh` - bash, `#!/usr/bin/env bash`, `set -euo pipefail`
- `scripts/wizard-template.ps1` - matching PowerShell 5.1-safe sibling

Both must stay in the same directory, share step ids, share the state-file format, and share exit codes. Follow `catalog/rules/bash/code-style.md` and `catalog/rules/bash/security.md`: no `eval`, quote expansions, never echo secrets, `set +x` around secret-bearing lines.

The agent writes the adapted scripts to the path the user named (default `scripts/setup-wizard.sh` plus `scripts/setup-wizard.ps1`). It does not execute them.

### 3. Resume via the state file

Default state path: `.wizard-state` in the working directory (override with `WIZARD_STATE_FILE`). Format: one completed step id per line, `#` comments allowed. On start, skip ids already listed. On success of a step, append that id. Deleting the file restarts the wizard.

Do not store secrets in the state file.

### 4. Per-step loop

For each remaining step:

1. Print the title, the why, and the exact human action.
2. Wait for confirmation (`Enter` to continue, or a typed value when the step must capture a non-secret token).
3. Run the observable check. On failure, print what was expected, leave the step unmarked, and exit non-zero so a resume retries it.
4. On success, append the step id to the state file and continue.

### 5. Privileged and secret steps

The generated wizard may *prompt* the human to paste a secret into a local env var or a secrets store. It must not print that value, write it to the state file, or pass it on the process command line. The agent that authored the wizard must not ask the human to paste the secret into the chat.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I will just run the cloud login myself; it is faster than a wizard." | Cloud login is privileged and often secret-bearing. The agent running it puts credentials in the session log. Ship the wizard; the human runs it. |
| "A Markdown checklist is enough." | Checklists do not resume, do not validate, and do not have a PowerShell sibling. The failure mode is a half-applied cutover. |
| "The bash template is enough; Windows users can install Git Bash." | v3.15.6+ requires a `.ps1` sibling with matching behavior. A missing sibling is silent non-coverage on Windows. |
| "I will `eval` the user's extra flags so the wizard stays flexible." | `eval` is forbidden. Pass extra flags as quoted arguments or a known allowlist. |
| "setup-project already bootstraps repos, so this skill is redundant." | setup-project is agent-runnable project scaffolding. This skill is for steps the agent must not run. |

## Verification

- [ ] Adapted `scripts/wizard-template.sh` and `scripts/wizard-template.ps1` exist at the output paths and share step ids and the state-file format.
- [ ] The bash script starts with `#!/usr/bin/env bash` and `set -euo pipefail`; it contains no `eval`.
- [ ] The PowerShell script parses under PowerShell 5.1 (`powershell -NoProfile -Command "& { $null = [System.Management.Automation.Language.Parser]::ParseFile('scripts/setup-wizard.ps1', [ref]$null, [ref]$errs); if ($errs) { $errs; exit 1 } }"`).
- [ ] Deleting the state file and re-running starts at the first step; a completed id is skipped on resume.
- [ ] Failed observable checks exit non-zero and do not append the step id.
- [ ] No secret is echoed, logged, or written to the state file.
- [ ] The agent did not execute privileged steps itself.

## Related Skills

- [[setup-project]] - agent-runnable repo bootstrap; use that when no human-only step remains
- `init-python-project` / `init-javascript-project` / `init-java-project` / `init-csharp-project` - language scaffolds the agent can run
- [[design-interview]] - interview about a design, not a setup walkthrough
- [[decision-questionnaire]] - async questions for an absent stakeholder
- `catalog/rules/bash/security.md` - the hard guardrails the generated bash must obey
- `scripts/wizard-template.sh` and `scripts/wizard-template.ps1` - the templates this skill adapts
