# Decision: Support Pi as a distribution platform

Status: implemented - registered as integration id `pi` for v4.1.0.

## Problem

Pi (`earendil-works/pi`) is an agent harness with a coding-agent CLI, MIT-licensed and actively developed. A comparison pass against it asked what Nexus-Hub should adopt.

Most of Pi is not adoptable, and saying so plainly matters more than the list of what is. Pi is a **runtime**: an agent loop, a multi-provider LLM abstraction, a TUI renderer, session backends. Nexus-Hub is a catalog distributed into other people's runtimes. Adopting Pi's architecture would mean becoming a different product. Pi is a peer of Claude Code, not a peer of Nexus-Hub.

The adoptable finding is narrower and better: **Pi reads the same skill format Nexus-Hub already emits.** Its documentation states that it implements the `agentskills.io` specification, which `scripts/check_agentskills_conformance.py` already enforces across all 325 catalog skills. A harness Nexus-Hub does not target was already able to read its output.

## Decision

Register `pi` as a supported integration, with surfaces read from fetched first-party documentation:

| Surface | Global | Project | Source |
|---|---|---|---|
| Skills | `~/.pi/agent/skills/` | `.pi/skills/` | `packages/coding-agent/docs/skills.md` |
| Commands (prompt templates) | `~/.pi/agent/prompts/*.md` | `.pi/prompts/*.md` | `packages/coding-agent/docs/prompt-templates.md` |
| Instruction | `~/.pi/agent/AGENTS.md` | not claimed (see below) | `packages/coding-agent/docs/usage.md` |
| Behavioral lever | `defaultThinkingLevel` in `~/.pi/agent/settings.json` | `.pi/settings.json` | `packages/coding-agent/docs/settings.md` |

Three choices inside that are worth recording.

**The project instruction file is deliberately not written.** Pi reads `AGENTS.md` from the working directory and its ancestors. Codex already owns project-root `AGENTS.md`. Pi therefore receives project instructions for free, and writing the file from two integrations would create two owners of one file for zero added coverage.

**Only `defaultThinkingLevel` is seeded.** `defaultModel` is a bare model ID with no documented default, and `defaultProvider` scopes it. Pinning either would hand a fresh install a provider and model the user's credentials may not reach. Both are recorded under `omitted` with the reason, which is the failure mode the do-not-invent rule exists to prevent, and which this repository has already shipped once as the fabricated `.kimi/agent.yaml`.

**Hooks are not supported, as a capability statement rather than an omission.** Pi documents no Claude-style hook registry. Its extension surface is TypeScript modules under `.pi/extensions/`, which is executable code, and Nexus-Hub does not write executable code into a user's agent config.

Global scope is detection-gated on `~/.pi`, matching the Qwen and Windsurf precedent: a user without Pi receives nothing.

## Alternatives considered

**Do not support Pi.** Defensible on the grounds that the roster is already seventeen platforms and each one is a maintenance surface re-verified every release. Rejected because the marginal cost here is unusually low. The catalog needs no new emission format, the command bodies need no conversion, and the contract came from first-party docs in one pass.

**Point Pi at the existing Claude directories instead of writing new ones.** Pi documents a `skills` settings array that accepts `~/.claude/skills`, so this would have been nearly free. Rejected because it makes Pi's coverage depend on Claude being installed and on a settings key Nexus-Hub would have to write into the user's file to express a dependency the user did not ask for. Writing Pi's own documented directories is more honest and independently correct.

**Write the project `AGENTS.md` from the Pi integration too.** Rejected: two owners of one file, no added coverage, and a guaranteed conflict the first time the two templates diverge.

**Also write `.pi/extensions/`.** Rejected outright. That directory holds TypeScript that Pi executes.

**Pre-trust the project so `.pi/` resources load immediately.** Rejected. Pi gates project-local resources behind its own trust prompt, and writing `~/.pi/agent/trust.json` on the user's behalf would defeat a security control to make an install look tidier. The workspace writes stay inert until the user answers Pi's prompt, and the global surfaces carry the catalog in the meantime.

## Consequences

- Pi users receive the full catalog (325 skills plus one prompt template per command) with no new emission format.
- The roster is seventeen integrations; `docs/policy/platform-defaults-levers.md` counts become 14 VERIFIED / 3 UNVERIFIED / 17 total.
- Project-scope writes are inert until the user trusts the folder in Pi. This is documented in the integration module rather than worked around.
- Pi joins the per-release re-verification set owned by `platform-contract-verification`.
