---
name: network-microsegmentation-design
description: "Design identity-aware microsegmentation for data centers and cloud VPCs, not plant IEC 62443 cells. Use this skill whenever the user says \"microsegmentation policy\", \"east-west allowlist\", \"identity-based segment\", or wants to stop flat /16s between services. SKIP, do NOT use for, IEC 62443 plant zones (use ot-network-segmentation-and-zones), or ZTNA user-to-app brokers."
summary_l0: "Design east-west identity-aware microsegmentation for DC and cloud VPCs"
overview_l1: "This skill writes east-west allowlists based on workload identity, not on a forever VLAN spreadsheet. Trigger phrases: microsegmentation policy, east-west allowlist, identity-based segment."
d3fend_techniques: [D3-NI]
nist_csf: [PR.IR, DE.CM]
---

# Network Microsegmentation

North-south firewalls do not see service-to-service ransomware. East-west allowlists do, if they are based on identity.

## When to Use This Skill

Use this skill when:

- Services share a flat VPC or VLAN
- Ransomware tabletop showed unconstrained SMB
- A regulator asked for east-west controls

Do NOT use this skill when:

- The environment is a plant cell
- The user wants a user-to-app broker

**Trigger phrases**: "microsegmentation policy", "east-west allowlist", "identity-based segment"

## Instructions

### Step 1: Inventory flows from telemetry, not from memory

VPC flow logs, service mesh, or host firewalls. Guessing is how you outage.

### Step 2: Group by identity

Service accounts, mesh SPIFFE IDs, or IAM roles. IP lists rot.

### Step 3: Default-deny a slice first

One application cluster, not the whole DC. Measure breaks.

### Step 4: Cover admin protocols

SSH, RDP, WinRM, and SMB get explicit paths through a PAM or jump, not any-any inside the segment.

### Step 5: Monitor before enforce on the next slice

Repeat. Microseg is a program of slices.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| Security groups already segment us | A security group that allows 0.0.0.0/0 or the whole VPC CIDR is a VLAN with extra steps. |
| We will cut over the data center this weekend | That is how you fund the rollback. Slice it. |
| OT and IT microseg are the same drawing | Safety and cycle times are not in the VPC model. Use the OT skill there. |

## Verification

- [ ] Flow inventory exists for the first slice
- [ ] Policies refer to identities, not only IPs
- [ ] Admin protocols are not any-any

## Related Skills

- [[ot-network-segmentation-and-zones]] -- plants
- [[ztna-broker-deployment]] -- user-to-app is north-south

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
