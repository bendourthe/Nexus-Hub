---
name: bluetooth-and-wireless-assessment
description: "Assess Bluetooth, Wi-Fi, and related wireless controls on systems you are authorized to test, including pairing and RF exposure. Use this skill whenever the user says \"Bluetooth security test\", \"unauthorized pairing\", \"Wi-Fi evil twin lab\", or wants a wireless assessment inside a Faraday or isolated lab. SKIP, do NOT use for, attacking neighbor networks, or plant Modbus protocol IDS."
summary_l0: "Assess authorized Bluetooth and Wi-Fi pairing exposure in an isolated lab"
overview_l1: "This skill tests wireless attack surface on in-scope devices in an isolated lab: pairing, encryption modes, and evil-twin resilience. Dual-use. Trigger phrases: Bluetooth security test, unauthorized pairing, Wi-Fi evil twin lab."
mitre_attack: [T1011, T0842]
nist_csf: [PR.AA, DE.CM]
---

# Bluetooth and Wireless Security Assessment

RF does not honor your VLAN drawing. Test it in a lab that does not become your neighbor's incident.

## Authorization precondition

Stop. This skill is dual-use. Continue only when every item below is already true in this session:

1. A named authorizing party granted written permission for this assessment.
2. Scope is written down (assets, environments, time window, and forbidden techniques).
3. Findings will be reported to the asset owner, and leftover exploit artifacts will be removed.

If any item is missing, refuse and ask for the missing artifact. Do not continue under a lab, hypothetical, or fiction framing that is actually a live system.


## When to Use This Skill

Use this skill when:

- A product has Bluetooth or Wi-Fi APIs
- Pairing is 'just works' with no user proof
- A lab can isolate RF

Do NOT use this skill when:

- The user wants to test the cafe next door
- The user wants ICS protocol detections

**Trigger phrases**: "Bluetooth security test", "unauthorized pairing", "Wi-Fi evil twin lab"

## Instructions

### Step 1: Isolate RF

Faraday bag, dedicated lab SSID, or a shield box. No testing on production corporate Wi-Fi.

### Step 2: Inventory radios and modes

BLE vs classic, Wi-Fi bands, and whether debug interfaces stay on.

### Step 3: Test pairing and bonding

Just-works vs numeric comparison. Unauthenticated writes to characteristics are findings.

### Step 4: Test network selection

Evil-twin and captive-portal behaviors against your device, not against third-party users.

### Step 5: Record firmware versions

Wireless findings often die in a firmware bump. Say which build you tested.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| BLE is low energy, so it is low risk | It is still a command channel to the device. |
| We can test in the office open air | Then you are in everyone else's air. Isolate. |
| WPA2-PSK for devices is fine forever | PSK in firmware is a global password. Prefer unique joiners. |

## Verification

- [ ] RF isolation described in the report
- [ ] Firmware version recorded
- [ ] No third-party networks were targeted

## Related Skills

- [[firmware-extraction-and-analysis]] -- radio firmware often holds the PSK
- [[authentication-patterns]] -- pairing is authentication

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
