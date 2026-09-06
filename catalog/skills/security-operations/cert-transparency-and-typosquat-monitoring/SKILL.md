---
name: cert-transparency-and-typosquat-monitoring
description: "Monitor certificate-transparency logs and lookalike domains for phishing and brand-impersonation early warning. Use this skill whenever the user says \"certificate transparency monitoring\", \"typosquat watch\", \"lookalike domain alert\", \"CT log brand watch\", or wants alerts when someone mints a cert on a spoof of the company domain. SKIP, do NOT use for, registering spoof domains, attacking the lookalike, or generic IOC enrichment."
summary_l0: "Watch CT logs and lookalike domains for brand-impersonation early warning"
overview_l1: "This skill watches certificate-transparency logs and DNS for lookalike hostnames that impersonate the organization. The output is an alert with the cert, registrar clues, and a takedown path, not an offensive operation against the spoof. Trigger phrases: certificate transparency monitoring, typosquat watch, lookalike domain alert, CT log brand watch."
mitre_attack: [T1583.001, T1566]
d3fend_techniques: [D3-DNRA]
nist_csf: [DE.CM, PR.AT]
---

# Certificate Transparency and Typosquat Monitoring

Phishing infrastructure often appears in CT logs hours before the first lure. Watch the log; do not become the lookalike.

## When to Use This Skill

Use this skill when:

- A brand wants early notice of spoof certificates
- Lookalike domains keep slipping past email filters
- A takedown needs the cert as evidence

Do NOT use this skill when:

- The user wants to register the spoof 'for research'
- The user wants to exploit the spoof site

**Trigger phrases**: "certificate transparency monitoring", "typosquat watch", "lookalike domain alert", "CT log brand watch"

## Instructions

### Step 1: Build the watch patterns

Apex domains, product names, and known homograph sets. Keep Unicode confusables explicit.

### Step 2: Subscribe to CT with those patterns

Use the user's existing CT monitor or log search. Alert on issuance, not on every SAN of a public CDN.

### Step 3: Score lookalikes

Distance metrics plus registrar age plus nameserver reuse. Newly issued plus brand string is high priority.

### Step 4: Preserve evidence for takedown

Save the precert, issuer, and resolved IPs at alert time. Those records vanish.

### Step 5: Open takedown, not counter-attack

Use registrar and hoster abuse channels. Do not phish the phisher.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| We should register every lookalike ourselves | Defensive registrations are a brand decision with a budget; this skill watches, it does not squat. |
| Let's credential-harvest the spoof to see who bites | That is an offensive operation and is out of scope. |
| CT is too noisy to alert on | Pattern the brand, don't ingest the whole log into the SOC. |

## Verification

- [ ] Watch patterns are documented
- [ ] An alert includes cert evidence captured at first sight
- [ ] The runbook ends in takedown or accept-risk, not exploitation

## Related Skills

- [[infrastructure-pivoting-and-attribution]] -- a spoof cert can seed a pivot
- [[phishing-analysis-and-defense]] -- lookalikes often feed phishing lures

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
