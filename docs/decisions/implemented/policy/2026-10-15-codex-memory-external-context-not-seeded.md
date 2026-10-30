# Decision: Codex Memory External-Context Exclusion Is Recorded, Not Seeded

Status: implemented - `memories.disable_on_external_context` is recorded in the Codex `omitted` map and recommended by `prompt-injection-defense`, but Nexus-Hub does not seed it.

Maintainers deciding whether to seed a Codex memory key, and agents reading `prompt-injection-defense`, read this. It records why the exclusion is advice and not an installed default.

**Date**: 2026-10-15 (design interview, question 1). **Release**: v4.14.5.

## Problem

OpenAI Codex Memories is off by default and, when a user turns it on, summarizes threads in the background into a store Codex injects into later sessions. A thread that used an MCP tool or a web search can therefore carry returned text, including credentials, into that store. Codex documents `memories.disable_on_external_context` (default `false`) to keep such threads out of memory generation, and the vendor redacts secrets only best-effort. Nexus-Hub could seed the setting, recommend it, or ignore it, and the choice changes what an installer writes into a user's `~/.codex/config.toml`.

## Decision

- **Record, do not seed.** `memories.disable_on_external_context`, together with `features.memories`, `memories.extract_model`, `memories.consolidation_model`, and `memories.min_rate_limit_remaining_percent`, sits in the Codex `omitted` map of `configs/platform-defaults.json` with a one-sentence reason each, and the `### codex - VERIFIED` section of `docs/policy/platform-defaults-levers.md` records each with its vendor URL, date, and documented default.
- **Recommend where the risk is taught.** `catalog/skills/security/prompt-injection-defense/SKILL.md` names a host memory store as a persistence channel and recommends the exclusion with its limit. The memory contract's host-generated store class (`docs/policy/memory-substrate-contract.md`) governs how an agent treats injected host memory.
- **Guard the decision.** The omitted-key guard (`2026-10-15-omitted-defaults-are-never-seeded.md`) fails a test if the key is ever declared under Codex `settings`.

## Alternatives considered

Rejected alternative: seed `true` on install and upgrade. It would reach existing users silently, a trusted project's `.codex/config.toml` can undo it, and an existing `false` set by the user would win silently, so the protection would be present in the file and absent in effect.

Rejected alternative: seed it only when `features.memories` is already on. The seeder's `merge_missing` cannot express a conditional, and the rule would miss a user who enables Memories after install.

Rejected alternative: a `nexus-hub doctor` warning when Memories is on and the exclusion is absent or false. Not rejected on merit: parked as a follow-on known gap, because it needs its own plan and follows the `diagnose_org_knowledge` pattern in `scripts/lib/integrations/lifecycle.py`.

Rejected alternative: do nothing. The channel and the vendor's partial mitigation would stay unnamed anywhere in Nexus-Hub.

## Consequences

- **Reduces, does not remove.** The exclusion keeps out only threads that used MCP tools, web search, or tool search (the page's list is illustrative, "such as"). Shell fetches, files from a cloned repository, and subagent output are not covered, so `prompt-injection-defense` says so and the contract treats injected memory as untrusted regardless.
- **The user stays in control.** Nothing changes on any machine: no value is seeded, no file is written, and a user who wants the exclusion sets it in their own configuration or the desktop control ("Allow memories from tool-assisted chats").
- **Revisiting needs a record.** Seeding the key later means removing it from `omitted` in the same edit with a new decision record, which the guard enforces.
- **Open follow-on.** The doctor warning is unbuilt, so a user who enables Memories without the exclusion gets no prompt from Nexus-Hub today.
