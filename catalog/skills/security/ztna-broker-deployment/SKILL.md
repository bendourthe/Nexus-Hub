---
name: ztna-broker-deployment
description: "Deploy an identity-aware access broker for private applications without bridging users onto the whole LAN. Use this skill whenever the user says \"ZTNA broker\", \"identity-aware proxy for private apps\", \"replace VPN with per-app access\", or wants a broker that terminates to an app, not a subnet. SKIP, do NOT use for, CISA-wide architecture (use zero-trust-architecture-design), or OT jump hosts."
summary_l0: "Deploy a per-app identity-aware broker instead of LAN-wide VPN"
overview_l1: "This skill deploys ZTNA so a user session reaches one application after identity and device checks, not a /16. Trigger phrases: ZTNA broker, identity-aware proxy for private apps, replace VPN with per-app access."
nist_csf: [PR.AA, PR.IR]
---

# ZTNA Access-Broker Deployment

If the broker's next hop is a subnet, you installed a VPN with extra SAML. Terminate to the app.

## When to Use This Skill

Use this skill when:

- VPN dump-to-LAN is the current remote access
- A private web app should not be on the public internet
- Device posture should gate a specific app

Do NOT use this skill when:

- The user wants a five-pillar strategy document
- The user wants a plant engineering jump server

**Trigger phrases**: "ZTNA broker", "identity-aware proxy for private apps", "replace VPN with per-app access"

## Instructions

### Step 1: List applications, not networks

Each private app gets a connector. Users get entitlements per app.

### Step 2: Integrate identity and device posture

IdP groups plus a device signal. A stolen password without the device fails.

### Step 3: Put connectors on a stick network

The connector reaches the app; the user never receives a route to the rest of the LAN.

### Step 4: Log at the broker

Who, which app, from which device. These logs are your VPN-replacement evidence.

### Step 5: Retire split-tunnel exceptions with dates

Every remaining VPN path has an owner and an end date.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| Users will complain if they cannot RDP anywhere | Then RDP is an application with its own broker path and MFA, not a LAN gift. |
| The connector should be dual-homed on the user LAN | That recreates hairpin trust. Keep it app-adjacent. |
| We can skip device posture until phase 2 | Then a stolen session cookie from a malware-ridden PC is still in. Start with a coarse posture. |

## Verification

- [ ] Access is per-app in the broker config
- [ ] Users do not receive RFC1918 routes
- [ ] Broker logs identify user, device, and app

## Related Skills

- [[zero-trust-architecture-design]] -- program context
- [[authentication-patterns]] -- IdP integration patterns

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
