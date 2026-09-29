# Decision Memo -- Should Nexus-Hub open an `offensive-security` category?

**Project**: Nexus-Hub
**Version**: v3.1.0
**Plan**: [`plans/adoption-claude-red.md`](plans/adoption-claude-red.md) -- Phase 5 (Ask-First category decision)
**Source comparison**: [`comparison-claude-red.md`](comparison-claude-red.md) (Sections 9.4, 10, 13)
**Date**: 2026-06-08
**Status**: OPEN -- awaiting maintainer sign-off
**Decision owner**: Nexus-Hub maintainers (this is an `AGENTS.md` "Ask first: creating a new skill category" action; the agent must not create the category unilaterally)

## Recommendation (TL;DR)

**DEFER.** Do not open an `offensive-security` category in v3.1.0. The selective, scope-gated adoption already delivered in Phases 1-4 (re-authored AI-attack and pentest-reporting skills, plus attacker-perspective enrichment folded into the existing defensive `security` skills) captures the high-value, low-controversy portion of the external source without changing what the catalog is. Opening a standalone offensive category for `offensive-cloud` and the specialist groups is a brand-defining, maintenance-heavy, scanner-colliding step whose payoff is unproven for a software-engineering catalog. It should happen only if maintainers make a deliberate, documented decision to position Nexus-Hub as an offensive-capable catalog, and only behind the governance gates listed in the GO checklist below. Until then, keep offensive content as attacker-perspective enrichment of defensive skills, not as a standalone engagement library.

This memo does **not** create the category or any specialist skill. It is the decision artifact the Ask-First boundary requires.

## What is being decided

Phases 1-4 of the claude-red adoption folded a curated slice of offensive methodology into the existing defensive `security` category (see the plan's "Phases at a Glance"). Two buckets of external content were intentionally left out of that fold-in and routed here, to a maintainer decision:

- **`offensive-cloud`** -- cloud privilege-escalation, instance-metadata (IMDS) abuse, and persistence methodology, with partial cloud-posture-evasion framing.
- **The out-of-domain specialist groups** -- wireless (14 skills), exploit-development (6), fuzzing (4), and the IoT / mobile / Active Directory / reconnaissance singletons (5). Roughly 30 skills in total.

The question is narrow and binary: **does Nexus-Hub create a third security category, `offensive-security`, to house this content, or not?** Today the catalog splits security into two defensive categories:

- `security` -- application security (authentication, dependency/CVE analysis, exploitability, patch advice, and -- as of this plan -- attacker-perspective review enrichment).
- `security-operations` -- defensive operations (DFIR, threat hunting, detection engineering, incident response).

Offensive engagement tradecraft fits neither cleanly, which is the structural argument for a third category (comparison Section 10). The counter-argument is everything in the factor analysis below.

Out of scope for this decision (already settled by the comparison and the plan's "Items explicitly NOT adopted" appendix): the detection-evasion / weaponization group (EDR evasion, shellcode, keylogger architecture, Windows mitigations/boundaries, advanced red-team C2, initial access). That group is recommended against the core catalog on its own merits regardless of whether an `offensive-security` category exists, and is **not** part of any GO path proposed here.

## Decision factors

### 1. Brand and positioning impact

Nexus-Hub positions as a production-grade, general-purpose catalog for AI coding assistants. Its security surface is deliberately defensive: even `/review pentest` audits the user's own code rather than teaching engagement tradecraft. Shipping a standalone offensive-engagement library (wireless cracking, binary exploitation, AD attack paths, OSINT) changes the catalog's identity from "build, review, secure, and operate software" to "also attack it". That is a strategic repositioning, not an incremental skill add. It is reversible only at reputational cost once distributed across all seven installer-target platforms. The enrichment approach already shipped (attacker perspective inside defensive skills) gets most of the analytic value without the repositioning.

### 2. Maintenance burden

Offensive tradecraft tracks fast-moving CVEs, tool versions (aircrack-ng, hashcat, frida, pwntools, AFL++, BloodHound, Impacket, ScoutSuite, and similar), and platform-specific mitigations. The specialist groups total roughly 30 skills, each of which would need to stay current to remain credible. Nexus-Hub's existing 250-skill catalog is general-purpose and ages slowly; an offensive subcatalog would age fast and demand domain-specialist review the current maintainer set is not staffed for. A stale offensive skill is worse than no skill -- it teaches an agent outdated methodology against current defenses.

### 3. Scanner-collision load

Nexus-Hub's own CI gate (`nexus-skill-scanner`) is built to flag exactly the payload content offensive skills carry. Phase 2 of this plan tuned a precise producer-catalog allowlist that caps findings to MEDIUM only for trusted `catalog/skills/security/` Markdown bodies, and only for the relaxable detection classes (never the excessive-agency, exfiltration-to-external-host, or live-malware classes). A standalone `offensive-security` category would either need that allowlist extended to a new path (widening the trusted surface) or would chronically trip the gate. Either way, every offensive skill adds scanner-maintenance coupling: the allowlist scope, its regression tests, and the planted-malicious fixture all have to keep holding as the offensive content grows. The specialist groups (shellcode-adjacent exploit-dev, wireless injection, AD attack chains) collide harder than the web/auth methodology already folded in.

### 4. Dual-use governance

All candidate content is pure methodology prose with zero data-flow risk (no bundled executables, no outbound calls, no credentials), so the gating axis is dual-use posture, not network trust. Offensive methodology is legitimate for authorized pentesting, CTF, and security research, and harmful outside those contexts. Every offensive skill therefore needs authorized-engagement preconditions in its Verification section (the discipline Phases 1-4 already applied). A standalone category multiplies that governance surface and raises the question of whether the catalog should ship an authorized-use policy document (the external source ships a `SECURITY.md` for exactly this reason). The enrichment-of-defensive-skills approach keeps dual-use content framed as "what the defense must withstand", which is a defensible posture; a standalone offensive library framed as engagement tradecraft is a harder governance position.

### 5. AGENTS.md governance requirement

`AGENTS.md` lists "Creating a new skill category" under **Ask first** -- it is an explicit maintainer decision, not an agent default. The same document's "Adding a New Skill" guidance says to discuss with maintainers before creating a new category when none of the existing ones fit. This memo exists to satisfy that gate. Proceeding to create `offensive-security` without recorded maintainer sign-off would violate the governance contract, independent of the technical merits.

## Options considered

| Option | What it means | Pros | Cons |
|---|---|---|---|
| **A. DEFER (recommended)** | Keep offensive content as enrichment of defensive `security` skills; do not create a new category now. Revisit only on a deliberate maintainer decision. | No brand drift; no new maintenance subcatalog; scanner-allowlist surface stays narrow; governance-clean. Captures the high-value analytic content already (Phases 1-4). | The specialist groups (cloud/wireless/exploit-dev/fuzzing/IoT/mobile/AD/recon) stay unadopted. Acceptable: they are out-of-domain for a coding-assistant catalog. |
| **B. Open `offensive-security` now** | Create the category and begin importing `offensive-cloud` + specialist groups as re-authored skills. | Fills the offensive-domain gap; gives a clean taxonomy home for future offensive content. | Repositions the brand; ~30-skill fast-aging maintenance surface; widens the scanner trusted surface; multiplies dual-use governance; needs an authorized-use policy doc and specialist review staffing. |
| **C. Reject permanently** | Declare offensive engagement tradecraft permanently out of scope for the core catalog. | Maximum clarity. | Forecloses a future the maintainers might want; premature given the cycle just demonstrated a working fold-in pattern. DEFER preserves optionality at no cost. |

## Recommendation rationale

Option A (DEFER) dominates on every factor except domain completeness, and domain completeness is precisely the thing a software-engineering catalog does not need. The cycle has already proven the high-leverage move: re-author the attacker's perspective into the defensive skills that review and harden code, where it directly sharpens `/review security` and `/review pentest`. The remaining specialist content (RF/hardware engagement, binary exploitation, AD attack chains, OSINT) does not strengthen any software-engineering workflow Nexus-Hub serves; it would be a standalone offensive product bolted onto a coding catalog. DEFER (not reject) is the right verdict because the fold-in pattern is now established and cheap to extend later if maintainers deliberately choose to become offensive-capable -- so there is no reason to foreclose that future, and no reason to commit to it now.

If maintainers do choose Option B in the future, the cleanest path is a **separately governed offensive bundle** (its own category, its own authorized-use policy, its own scanner-allowlist scope and regression tests, and a named domain reviewer) rather than scattering offensive skills into the existing defensive category. That keeps the brand boundary explicit and the governance surface contained.

## GO / NO-GO checklist for maintainer sign-off

This is the binary gate. The agent will not create an `offensive-security` category unless a maintainer records a GO decision here and every GO precondition is satisfied.

**NO-GO (default -- DEFER):**

- [x] Offensive content remains enrichment of the existing defensive `security` skills (Phases 1-4 shipped).
- [x] No `offensive-security` category is created.
- [x] No specialist offensive skill (cloud / wireless / exploit-dev / fuzzing / IoT / mobile / AD / recon) is imported.
- [x] The decision is revisitable: this memo stays on file and the fold-in pattern is documented for future reuse.

**GO (only if maintainers deliberately choose to position Nexus-Hub as offensive-capable) -- every box must be checked before any category or skill is created:**

- [ ] A maintainer has recorded an explicit, signed decision to open `offensive-security` (name, date, rationale) in this memo.
- [ ] The repositioning (general coding catalog -> also an offensive-capable catalog) is accepted at the project-brand level and reflected in `README.md` / `AGENTS.md` positioning prose.
- [ ] A named domain owner is committed to keeping the offensive subcatalog current against fast-moving CVEs and tooling (maintenance-burden mitigation).
- [ ] An authorized-use policy document is authored and shipped, and every offensive skill carries authorized-engagement preconditions in its Verification section (dual-use governance).
- [ ] The `nexus-skill-scanner` producer-catalog allowlist scope and its regression tests are extended to the new category, with the planted-malicious fixture still scoring CRITICAL and the never-relax classes (excessive agency, exfiltration-to-external-host, live malware) unchanged.
- [ ] The detection-evasion / weaponization group remains excluded (it is out of scope for any GO path proposed here; adopting it would be a separate, harder Ask-First).
- [ ] The offensive subcatalog ships as a separately governed bundle (its own category and policy), not by scattering offensive skills into the existing defensive `security` category.
- [ ] All re-authored content follows the Reverse-Engineering Attribution Rule (generic naming; no references to the external source, its maintainer, or the upstream checklist in distributed artifacts).

## Appendix -- deferred content inventory

For reference if a future GO decision is made. None of this is adopted by this memo.

| Group | Count | Examples | Why deferred |
|---|---|---|---|
| Cloud | 1 | `offensive-cloud` (IMDS abuse, privesc, persistence, CSPM evasion) | Partial detection-evasion framing; medium scanner-collision; better served (for review) by the existing defensive cloud-posture skills. |
| Wireless | 14 | wifi, wpa2-psk, wpa3-sae, wpa-enterprise, wps, evil-twin, deauth, krack-fragattacks, bluetooth-ble, bluetooth-classic, zigbee-thread-matter, z-wave, lorawan-sub-ghz, wifi-recon | RF / hardware engagement domain; no overlap with software-engineering workflows. |
| Exploit-Dev | 6 | exploit-development, basic-exploitation, crash-analysis, mitigations, toctou, exploit-dev-course | Binary exploitation; narrow audience; weaponization-adjacent. |
| Fuzzing | 4 | fuzzing, fuzzing-course, bug-identification, vuln-classes | Partial overlap with the `bug-fixing` category; fuzzing-as-engagement is specialist. |
| IoT / Mobile / AD / Recon | 5 | iot, mobile, offensive-active-directory, osint, osint-methodology | Specialist; out-of-domain; defer to a dedicated offensive bundle if ever pursued. |

Related: [`comparison-claude-red.md`](comparison-claude-red.md) (full gap analysis and risk scorecard), [`plans/adoption-claude-red.md`](plans/adoption-claude-red.md) (the adoption plan and its NOT-adopted appendix), and the `AGENTS.md` MCP Registry Policy + "Ask first" boundary.
