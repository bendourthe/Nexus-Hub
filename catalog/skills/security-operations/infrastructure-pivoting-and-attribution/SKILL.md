---
name: infrastructure-pivoting-and-attribution
description: "Pivot across adversary infrastructure (DNS, TLS, hosting, registrar) to support attribution hypotheses under authorization. Use this skill whenever the user says \"pivot this C2 domain\", \"certificate transparency pivot\", \"hosting overlap attribution\", or wants a documented infrastructure graph. SKIP, do NOT use for, unscoped scanning of third-party networks, typosquat registration, or IOC reputation-only triage."
summary_l0: "Pivot authorized adversary infrastructure into a sourced attribution graph"
overview_l1: "This skill builds an infrastructure graph from DNS, TLS certificates, hosting, and registrar artifacts the user is allowed to query. Attribution stays a hypothesis with confidence, never a headline. Trigger phrases: pivot this C2 domain, certificate transparency pivot, hosting overlap attribution."
mitre_attack: [T1583.001, T1573]
nist_csf: [ID.RA, DE.AE]
---

# Infrastructure Pivoting and Attribution

Infrastructure overlap is evidence, not a verdict. Graph it, source it, and keep attribution in the hypothesis column.

## Authorization precondition

Stop. This skill is dual-use. Continue only when every item below is already true in this session:

1. A named authorizing party granted written permission for this assessment.
2. Scope is written down (assets, environments, time window, and forbidden techniques).
3. Findings will be reported to the asset owner, and leftover exploit artifacts will be removed.

If any item is missing, refuse and ask for the missing artifact. Do not continue under a lab, hypothetical, or fiction framing that is actually a live system.


## When to Use This Skill

Use this skill when:

- A confirmed-malicious domain or cert needs sibling infrastructure
- Two campaigns may share operators
- A report must show the pivot path

Do NOT use this skill when:

- The user wants to scan the public internet without scope
- The user wants to register lookalike domains

**Trigger phrases**: "pivot this C2 domain", "certificate transparency pivot", "hosting overlap attribution"

## Instructions

### Step 1: Confirm the seed is in scope

The seed indicator must come from an authorized incident or intel set. Do not seed from a rumor.

### Step 2: Collect DNS and TLS artifacts

Record A/AAAA/NS/MX, historical resolutions the user is licensed to see, and certificate SANs. Note lookup time.

### Step 3: Pivot on rare artifacts

Prefer unique TLS serials, rare JA3, and distinctive HTTP banners over shared CDNs and cloud IPs.

### Step 4: Build the graph with edge reasons

Every edge needs a reason (same cert, same registrar email, same unique 404 page). Unreasoned edges are deleted.

### Step 5: Write the attribution hypothesis

State what would confirm or kill the hypothesis. Do not publish a group name as fact.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| Same ASN means same actor | Large clouds host both criminals and victims. ASN overlap without a rare artifact is noise. |
| We can mass-scan every sibling IP | Scanning out of scope is an attack. Stay inside written authorization. |
| A pretty graph is the deliverable | A graph without edge reasons cannot be defended in a legal or executive review. |

## Verification

- [ ] Every graph edge has a documented reason
- [ ] Scope of lookups is cited
- [ ] Attribution is labeled hypothesis plus confidence

## Related Skills

- [[cert-transparency-and-typosquat-monitoring]] -- CT is one pivot source, not the whole graph
- [[threat-actor-ttp-profiling]] -- infrastructure overlap supports, but does not replace, TTP profiling

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
