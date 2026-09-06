---
name: ot-incident-response
description: "Run incident response on operational-technology systems without causing an unsafe process state. Use this skill whenever the user says \"OT incident response\", \"PLC ransomware\", \"plant cyber event\", \"do not trip the turbine\", or wants an IR plan that operations will actually follow. SKIP, do NOT use for, enterprise-only ransomware IR (use ransomware-incident-response)."
summary_l0: "Respond to OT cyber incidents without creating an unsafe process state"
overview_l1: "This skill runs IR where availability and safety beat forensic purity: isolate conduits, preserve what you can, and never 'reboot the PLC to clean it' during a run. Trigger phrases: OT incident response, PLC ransomware, plant cyber event, do not trip the turbine."
mitre_attack: [T0829, T0813]
nist_csf: [RS.MI, RS.CO]
---

# OT Incident Response

The first IR instinct on IT (isolate and reimage) can kill a process. OT response is coordinated with operations, or it is just another incident.

## When to Use This Skill

Use this skill when:

- A plant has a suspected cyber event
- A PLC or HMI behaves against the as-built
- IT IR wants to pull a cable in a running mill

Do NOT use this skill when:

- The incident is email/IT ransomware with no process connection

**Trigger phrases**: "OT incident response", "PLC ransomware", "plant cyber event", "do not trip the turbine"

## Instructions

### Step 1: Establish the operations liaison first

No packet capture is worth a surprise trip. Name the operator who can approve isolation.

### Step 2: Classify process risk

Safety instrumented systems, environmental permits, and product quality have different abort criteria. Write them down.

### Step 3: Contain by conduit, not by pulling every plug

Disable a vendor VPN or a compromised engineering workstation before you consider stopping a cell.

### Step 4: Preserve without halting

Copy HMI configs, historian windows, and PLC project files. Avoid forcing PLCs into stop unless operations orders it.

### Step 5: Recover to a known engineering baseline

Reload from signed project archives, not from 'the last laptop that worked'. Document every force and override you clear.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| Reimage is always the fastest clean | Reimaging an HMI mid-batch can leave the process unattended. Time isolation with operations. |
| Air-gap means we do not need IR | USB, vendors, and historians still enter. Pretending otherwise delays the first call. |
| Safety systems are out of cyber scope | If a cyber event can influence a setpoint that safety must catch, it is in scope. |

## Verification

- [ ] Operations liaison is named in the ticket
- [ ] Containment action is mapped to a conduit
- [ ] No PLC stop occurred without operations approval

## Related Skills

- [[ransomware-incident-response]] -- IT ransomware playbooks do not automatically apply to PLCs
- [[ot-network-segmentation-and-zones]] -- zones are the containment units

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
