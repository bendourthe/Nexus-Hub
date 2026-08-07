# v3.16 / v3.17 Roadmap Prioritization

**Created**: 2026-08-07
**Scope**: the 12 unimplemented plans in `docs/v3/v3.16/` and `docs/v3/v3.17/`
**Purpose**: establish a priority order, classify each plan as patch or feature work, and drive a renumbering so the filenames carry the order.

---

## Why the current numbering says nothing

The existing numbers record **the order the plans were written**, not the order they should ship or the size of the change they represent. Three consequences:

1. The autonomy toggle, which changes the security posture of every install, was numbered `v3.16.0`; the one-file spec-template fix was `v3.16.6`. They sat six apart in the wrong direction.
2. Every plan is numbered as a **patch** under one minor, so the numbering cannot distinguish "fixes a broken template" from "ships a new memory subsystem". Both read as `v3.16.x`.
3. Two plans overlap on the same subsystem (the RTK adoption and the memory substrate, previously `v3.16.1` and `v3.16.2`, both touch agent memory) with no sequencing recorded, so whichever ships second inherits an undocumented merge.

## The classification used

**Patch**: fixes behavior that is already shipped and wrong, or is contained to one skill or one document. No new user-facing capability, no new subsystem, no change to what gets installed.

**Feature (minor)**: adds a capability, a subsystem, a new skill cluster, or changes what an install produces. Anything that changes the security posture is a feature regardless of diff size, because the review burden is what makes it one.

## Priority ranking

Ranked on **leverage** (does shipping this make later work cheaper or safer?), then **user-visible value**, then **containment** (can it ship without dragging other plans with it?).

The `Previously` column records the number each plan carried before this pass. It is deliberately written in backticks: an earlier automated sweep over version strings rewrote this column into the NEW numbers and made the table contradict itself, which is the same class of error the renumbering exists to prevent.

| Rank | Plan | New version | Previously | Class | Why here |
|---|---|---|---|---|---|
| 1 | spec-driven-development | `v3.15.14` | `v3.16.6` | **Patch** | It is an active defect, not an enhancement: the canonical spec template cannot express a scope boundary, so every reviewer run on a conformant spec raises a finding the template itself caused, and the skill's Verification checklist validates a rival inline template so "spec complete" is checked against the wrong thing. Users hit this today. Smallest change, highest certainty. |
| 2 | platform-defaults-config | `v3.16.0` | `v3.16.4` | **Feature** | The highest-leverage item on the list. One edit propagates to every derived artifact, and a guard fails the build on drift. Installer and registry drift is the most recurrent defect class in this repository's history, and this is the plan that makes it structurally impossible rather than caught by review. Shipping it early means the larger plans inherit the guard. |
| 3 | evals-and-selective-installation | `v3.16.1` | `v3.16.9` | **Feature** | Selective installation is the largest standing user complaint the roadmap addresses: every user installs the full catalog even though profiles, modules, and role bundles already describe smaller coherent sets. The eval half gives every later plan a way to prove it improved something. |
| 4 | agent-autonomy-toggle | `v3.17.0` | `v3.16.0` | **Feature** | High user value (removes approval friction on every platform with a verified lever) but it changes the security posture, so it wants the drift guard already in place and deserves its own release rather than riding along with others. |
| 5 | code-intelligence-hardening | `v3.18.0` | `v3.16.3` | **Feature** | Direct and measurable cost reduction on `nexus-code-search`, with a deterministic local harness to prove it. Contained to one subsystem. |
| 6 | agent-memory-substrate | `v3.18.1` | `v3.16.2` | **Feature** | A genuinely new subsystem. Ranked above its overlapping sibling because it defines the substrate; the other consumes it. |
| 7 | rtk-and-meterless | `v3.18.2` | `v3.16.1` | **Feature** | Broad and multi-part. Its memory portion overlaps the substrate plan and its eval portion overlaps the evals plan, so it should follow both and absorb what they shipped. **This plan needs a rewrite before implementation, not just a renumber.** |
| 8 | cost-effective-ci-cd | `v3.19.0` | `v3.16.8` | **Feature** | Valuable, but it touches planning, implementation, commit, branch, and release guidance at once - the widest blast radius on the list. Better once the guard and the eval harness exist. |
| 9 | interface-craft-skills | `v3.19.1` | `v3.16.5` | **Feature** | Five new skills plus a coordinating review skill. Pure catalog growth with no dependencies, which is exactly why it can wait: nothing else is blocked on it. |
| 10 | skills-craft-and-prime-agent | `v3.19.2` | `v3.17.1` | **Feature** | Skills-authoring craft plus invocation-policy metadata and a prepared marketplace listing. The marketplace listing is the highest-value part and is separable. |
| 11 | interactive-guide-redesign | `v3.20.0` | `v3.16.7` | **Feature** | Onboarding and explanation. Real value for adoption, but it describes the product rather than changing it, so it is best done when the product has stopped moving this fast. |
| 12 | presentify-scroll-scrub | `v3.20.1` | `v3.17.0` | **Feature** | An opt-in enhancement to one command. Narrowest audience on the list. |

## Two findings that are not about ordering

**The RTK/Meterless plan should not be implemented as written.** It overlaps the memory plan on provenance-backed memory and the evals plan on eval discipline. If those ship first, roughly a third of it is already done and the rest needs rebasing on what exists. Renumbering it without rewriting it sets up the same failure this repository just hit in v3.15.12, where a plan's stated premise had been overtaken by later work.

**Numbering must stop encoding authoring order.** The renumbering above fixes today's list but not the cause. The durable fix is to name plans by slug and record the target version inside the document, so a priority change is a one-line edit rather than a rename of two files plus every cross-reference.
