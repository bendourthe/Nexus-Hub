---
name: honeytoken-placement
description: "Place honeytokens and canary credentials that alert on touch without poisoning production data flows. Use this skill whenever the user says \"honeytoken\", \"canary AWS key\", \"decoy document tripwire\", or wants credentials that should never be used except by an attacker. SKIP, do NOT use for, full adversary-engagement programs (use adversary-engagement-deception), or leaking real secrets."
summary_l0: "Place canary credentials and decoy files that alert on first touch"
overview_l1: "This skill plants tripwire secrets and files that page on use, with ownership and a never-use policy for humans. Trigger phrases: honeytoken, canary AWS key, decoy document tripwire."
mitre_attack: [T1552, T1078]
d3fend_techniques: [D3-DE]
nist_csf: [DE.CM, DE.AE]
---

# Honeytoken Placement

A token nobody is allowed to use is a tripwire. A token in the production path is an outage.

## When to Use This Skill

Use this skill when:

- You want early warning of credential theft
- A share could use a decoy file
- Cloud keys keep leaking and you need a canary

Do NOT use this skill when:

- The user wants a full deception environment
- The user wants to reuse a live production key as a canary

**Trigger phrases**: "honeytoken", "canary AWS key", "decoy document tripwire"

## Instructions

### Step 1: Pick unused namespaces

Canary IAM users, DNS names, and files that production will never call.

### Step 2: Instrument the alert path

CloudTrail, DNS, and file-open auditing must page a human, not a discarded mailbox.

### Step 3: Document the never-use policy

If a developer uses the canary, it is still an incident (process failure) plus a reset.

### Step 4: Rotate after fire

A tripped token is burned. Replace it. Do not 'watch a bit longer'.

### Step 5: Do not mix with real data

Decoy documents should not contain real PII 'to look authentic'.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| A real unused access key is a better canary | Until someone scripts it into a job. Mint a dedicated canary identity. |
| We can put customer data in the decoy so attackers believe it | That is distributing customer data. Use fake records. |
| No need to alert, we will poll monthly | The value is minutes, not months. |

## Verification

- [ ] Canary identities are unused by jobs
- [ ] Alert path is tested
- [ ] Decoys contain no real PII

## Related Skills

- [[adversary-engagement-deception]] -- broader engagement
- [[ioc-enrichment-and-reputation-triage]] -- tripped tokens become IOCs

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
