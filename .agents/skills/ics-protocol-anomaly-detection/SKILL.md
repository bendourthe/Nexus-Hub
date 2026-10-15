---
name: ics-protocol-anomaly-detection
description: "Detect abnormal Modbus, DNP3, and OPC-UA behavior on operational-technology networks. Use this skill whenever the user says \"Modbus function-code anomaly\", \"DNP3 outstation scan\", \"OPC-UA unauthorized method\", \"ICS protocol IDS\", or wants detections for industrial protocol abuse. SKIP, do NOT use for, IT-only NetFlow hunts, or attacking a plant you do not operate."
summary_l0: "Detect Modbus DNP3 and OPC-UA protocol abuse on OT networks"
overview_l1: "This skill writes detections for industrial protocol abuse: unexpected function codes, outstation polling, and unauthorized OPC-UA methods. It assumes a historian or span port the user already owns. Trigger phrases: Modbus function-code anomaly, DNP3 outstation scan, OPC-UA unauthorized method, ICS protocol IDS."
mitre_attack: [T0855, T0807]
nist_csf: [DE.CM, DE.AE]
---

# ICS Protocol Anomaly Detection

Industrial protocols were designed for availability, not for a hostile WAN. Detect the function codes and methods that never appear in the as-built.

## When to Use This Skill

Use this skill when:

- A plant has Modbus/DNP3/OPC-UA on a span or historian
- Engineering wants protocol IDS without breaking the process
- An incident needs protocol-level evidence

Do NOT use this skill when:

- The environment is purely enterprise IT
- The user wants to fuzz a plant they do not own

**Trigger phrases**: "Modbus function-code anomaly", "DNP3 outstation scan", "OPC-UA unauthorized method", "ICS protocol IDS"

## Instructions

### Step 1: Inventory the as-built conversations

List masters, outstations, allowed function codes, and cycle times from the engineering workstation or loop drawings. A detection without an as-built is a false-positive factory.

### Step 2: Capture in a way the process can survive

Prefer historian tags, passive TAP, or an already-approved span. Do not insert an inline IPS on a safety loop as a first move.

### Step 3: Baseline function codes and methods

For Modbus, record exception rates and writes to holding registers. For DNP3, record unsolicited responses. For OPC-UA, record method calls outside the engineering role.

### Step 4: Write high-signal alerts

Alert on writes from a new master, on function 0x10 bursts, and on OPC-UA anonymous sessions. Leave noisy polling in a dashboard, not a pager.

### Step 5: Prove with a tabletop packet

Replay a pcap from a lab or a recorded maintenance window. If the alert does not fire, the signature is theater.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| IT IDS signatures will cover Modbus | Most IT IDS treat industrial payloads as opaque TCP. Function-code awareness is the whole point. |
| We can inline-block on day one | A false positive on a safety or turbine loop is an availability incident. Detect first. |
| Any new master is automatically hostile | Vendors add jump hosts during outages. Ticketing plus allowlist change control is the control, not a silent drop. |

## Verification

- [ ] As-built conversation list exists
- [ ] Alerts name function code or OPC-UA method
- [ ] A lab or recorded pcap proved at least one signature

## Related Skills

- [[ot-network-segmentation-and-zones]] -- protocol detections belong inside zones, not as a substitute for them
- [[scada-historian-threat-detection]] -- historian integrity is the sibling telemetry source

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
