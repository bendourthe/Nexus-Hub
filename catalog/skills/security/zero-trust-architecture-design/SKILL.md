---
name: zero-trust-architecture-design
description: "Design a zero-trust architecture using the CISA maturity model: identity, device, network, application, and data pillars. Use this skill whenever the user says \"CISA zero trust maturity\", \"zero trust architecture\", \"beyondcorp style access\", or wants a ZT roadmap that is not a VPN replacement slogan. SKIP, do NOT use for, picking a single ZTNA vendor appliance (use ztna-broker-deployment), or plant IEC 62443 zones."
summary_l0: "Design zero-trust architecture across CISA identity device network app and data pillars"
overview_l1: "This skill drafts a CISA-aligned zero-trust program: pillars, maturity, and dependencies, without collapsing into a vendor SKU. Trigger phrases: CISA zero trust maturity, zero trust architecture, beyondcorp style access."
d3fend_techniques: [D3-NTA]
nist_csf: [PR.AA, PR.IR]
---

# Zero-Trust Architecture Design

Zero trust is five pillars and a policy engine, not a new private-access logo on the same flat network.

## When to Use This Skill

Use this skill when:

- A board asked for zero trust and received a VPN quote
- Identity, device, and network teams do not share a policy
- Maturity needs an honest baseline

Do NOT use this skill when:

- The user only wants to rack a broker
- The user wants OT cell zoning

**Trigger phrases**: "CISA zero trust maturity", "zero trust architecture", "beyondcorp style access"

## Instructions

### Step 1: Baseline each CISA pillar honestly

Traditional / advanced / optimal. Wishful 'advanced' is a finding.

### Step 2: Put identity and device before network poetry

Untrusted networks still need strong identity and health. Do not start with microseg theater.

### Step 3: Define the policy decision point

Who evaluates session, device posture, and data sensitivity. If the answer is 'the firewall team', you are not done.

### Step 4: Map application access

Private apps via a broker, public apps via identity-aware proxy. Exceptions expire.

### Step 5: Write the roadmap as dependencies

IdP hygiene before ZTNA. Asset inventory before microseg. Fund the unglamorous steps.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| Replacing VPN is zero trust | If the broker still dumps users onto the same LAN, you bought a new VPN. |
| We will microsegment first | Without identity and inventory you will paint lines on fog. |
| Optimal maturity this year | CISA optimal is a multi-year program. Lying on the heatmap is how it dies. |

## Verification

- [ ] Five-pillar baseline exists
- [ ] Policy decision point is named
- [ ] Roadmap order has dependencies

## Related Skills

- [[ztna-broker-deployment]] -- one enforcement mechanism
- [[network-microsegmentation-design]] -- network pillar details

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
