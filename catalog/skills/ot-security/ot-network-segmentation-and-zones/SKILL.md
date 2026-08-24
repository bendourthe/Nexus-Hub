---
name: ot-network-segmentation-and-zones
description: "Design IEC 62443 zones and conduits for OT networks, including the IT/OT DMZ. Use this skill whenever the user says \"IEC 62443 zones\", \"Purdue model segmentation\", \"OT DMZ design\", \"conduits between cells\", or wants to separate a plant from the enterprise LAN. SKIP, do NOT use for, cloud microsegmentation of Kubernetes (use network-microsegmentation-design)."
summary_l0: "Design IEC 62443 zones and conduits including the IT/OT DMZ"
overview_l1: "This skill draws zones, conduits, and a Purdue-style IT/OT DMZ that a plant can actually run. It is not a Kubernetes overlay. Trigger phrases: IEC 62443 zones, Purdue model segmentation, OT DMZ design, conduits between cells."
mitre_attack: [T0883]
d3fend_techniques: [D3-NI]
nist_csf: [PR.IR, PR.AC]
---

# OT Network Segmentation and Zones

A flat plant network turns every workstation into a blast radius. Zones are the control; firewalls are just how you enforce them.

## When to Use This Skill

Use this skill when:

- A plant is flat and connected to IT
- A project claims IEC 62443 and has no zone drawing
- A vendor wants direct VPN into a cell

Do NOT use this skill when:

- The user is segmenting a cloud VPC or a Kubernetes cluster

**Trigger phrases**: "IEC 62443 zones", "Purdue model segmentation", "OT DMZ design", "conduits between cells"

## Instructions

### Step 1: Draw the as-is Purdue levels

Level 0-1 devices, Level 2 HMI, Level 3 site servers, Level 4/5 enterprise. Mark every jump host and vendor modem.

### Step 2: Define zones by consequence, not by VLAN convenience

Safety, process, engineering, and vendor access are different zones even if they share a switch today.

### Step 3: Name conduits and their protocols

Each conduit lists allowed protocols, initiators, and whether it is event-driven or polled. 'Any any' is not a conduit.

### Step 4: Place the IT/OT DMZ

Historians, WSUS, and jump hosts live in the DMZ. User laptops do not.

### Step 5: Stage enforcement

Start with monitoring ACLs, then blocking. Coordinate with operations so a blocked conduit is not a surprise shutdown.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| VLANs without ACLs are segmentation | A VLAN is a label. Without a conduit policy it is still one broadcast philosophy. |
| The vendor needs dual-homed laptops | Vendors get a brokered jump path with MFA and session recording, not a second NIC on the process LAN. |
| IEC 62443 is paperwork | If the drawing cannot name a conduit, the certificate is fiction. |

## Verification

- [ ] Zone-and-conduit drawing exists
- [ ] Each conduit lists protocols and initiators
- [ ] IT/OT DMZ has a named jump path

## Related Skills

- [[network-microsegmentation-design]] -- that skill is IT/cloud; this one is plants
- [[ot-incident-response]] -- zones bound the IR blast radius

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
