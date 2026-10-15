---
name: ot-nerc-cip-compliance
description: "Map NERC CIP evidence to actual OT controls rather than to a folder of stale screenshots. Use this skill whenever the user says \"NERC CIP evidence\", \"CIP-007 ports and services\", \"BES cyber system inventory\", \"CIP-010 baseline\", or wants a CIP audit that matches the plant. SKIP, do NOT use for, ISO 27001 office ISMS work, or IEC 62443 zone drawings with no CIP overlay."
summary_l0: "Map NERC CIP evidence to living OT controls instead of screenshot binders"
overview_l1: "This skill turns CIP-002 through CIP-013 obligations into inventories, baselines, and monitoring that match the yard. It is not a generic ISMS. Trigger phrases: NERC CIP evidence, CIP-007 ports and services, BES cyber system inventory, CIP-010 baseline."
nist_csf: [ID.AM, ID.IM]
---

# OT Regulatory Compliance (NERC CIP)

A CIP binder that does not match the relay room is a finding waiting for an auditor. Evidence is a snapshot of a living control.

## When to Use This Skill

Use this skill when:

- A BES cyber system inventory is stale
- An audit is six months out and the baselines drifted
- Ports-and-services evidence is a spreadsheet from 2019

Do NOT use this skill when:

- The user wants a corporate ISO 27001 program
- The user wants only IEC 62443 zoning with no CIP

**Trigger phrases**: "NERC CIP evidence", "CIP-007 ports and services", "BES cyber system inventory", "CIP-010 baseline"

## Instructions

### Step 1: Rebuild the BES cyber system list from the yard

Walk panels and protective relays. Names in the CMDB that do not exist on the wall are the first finding.

### Step 2: Bind each asset to CIP requirements that actually apply

High/medium/low impact changes the obligation set. Do not copy high-impact paperwork onto a low-impact yard.

### Step 3: Make CIP-010 baselines diffable

Configs live in version control or an engineering repository. A PDF dump is not a baseline.

### Step 4: Produce CIP-007 evidence from the control

Ports and services come from the last hardened image plus an exception list, not from a one-time nmap screenshot.

### Step 5: Record compensating measures honestly

If a relay cannot run modern auth, say so and document the physical and network compensating control.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| Last year's evidence packet is still fine | Baselines drift the first time engineering pushes a settings file. Freshness is the control. |
| Nmap during the audit window is evidence | A scan is a moment. A hardened image plus change tickets is a system. |
| CIP is the same as IEC 62443 | They rhyme. They do not share evidence artifacts. Map explicitly. |

## Verification

- [ ] Inventory matches a physical walkdown sample
- [ ] Baselines are diffable artifacts
- [ ] Each compensating measure names the gap it covers

## Related Skills

- [[ot-network-segmentation-and-zones]] -- zones feed CIP electronic security perimeters
- [[security-framework-mapping]] -- use that skill for crosswalk language, this one for CIP evidence

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
