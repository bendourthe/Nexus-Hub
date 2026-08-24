---
name: adversary-engagement-deception
description: "Design adversary-engagement and deception environments using MITRE Engage-style objectives, not random honeypots. Use this skill whenever the user says \"MITRE Engage deception\", \"adversary engagement\", \"high-interaction honeypot program\", or wants a deception campaign with goals and safety rails. SKIP, do NOT use for, planting a single canary key (use honeytoken-placement), or attacking back."
summary_l0: "Design MITRE Engage-style deception campaigns with goals and safety rails"
overview_l1: "This skill plans deception as a campaign: Engage objectives, breadcrumbs, high-interaction traps, and legal/safety rails. Trigger phrases: MITRE Engage deception, adversary engagement, high-interaction honeypot program."
mitre_attack: [T1200, T1584]
nist_csf: [DE.CM, ID.RA]
---

# Deception and Adversary Engagement

A honeypot without an objective is a toy that might become an attack platform. Engagement is planned or it is negligence.

## When to Use This Skill

Use this skill when:

- Leadership wants deception beyond canaries
- You need to learn TTPs without touching real data
- Legal has asked what 'engagement' means

Do NOT use this skill when:

- The user only needs a canary AWS key
- The user wants to hack back

**Trigger phrases**: "MITRE Engage deception", "adversary engagement", "high-interaction honeypot program"

## Instructions

### Step 1: Write the Engage-style objective

Collect, detect, or deny. If you cannot pick one, you are not ready.

### Step 2: Isolate the environment

No path from honeypot to production. Egress allowlists. Assume compromise of the bait.

### Step 3: Seed breadcrumbs on purpose

Docs and tokens that point into the deception net, not into finance shares.

### Step 4: Instrument for TTP capture

PCAPs, command logs, and malware drops. This is the product.

### Step 5: Legal and safety sign-off

Hack-back, sinkholing third parties, and malware redistribution are out of bounds unless counsel says otherwise in writing.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| We will just put a Windows VM on the internet | That is a spam cannon and a liability. Isolate it. |
| Engagement means we scan the attacker | That is likely an attack on someone else's compromised box. Collect on your bait. |
| Canaries are the same program | Canaries detect. Engagement studies. Different controls. |

## Verification

- [ ] Written objective exists
- [ ] No production route from the bait
- [ ] Counsel signed the rules of engagement

## Related Skills

- [[honeytoken-placement]] -- tripwires vs campaigns
- [[purple-team-exercise-design]] -- deception data can feed purple tests

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
