---
name: ransomware-leak-site-monitoring
description: "Monitor ransomware leak sites and victim-name dumps for early warning without paying actors or spreading stolen data. Use this skill whenever the user says \"watch ransomware leak sites\", \"victim name monitoring\", \"is our company on a leak blog\", or wants a defensive leak-site watch process. SKIP, do NOT use for, negotiating with actors, downloading victim data, or celebrating criminal content."
summary_l0: "Watch leak blogs for victim-name early warning without spreading stolen data"
overview_l1: "This skill sets up a defensive watch on ransomware name-and-shame blogs: collection, victim matching, and escalation. It forbids downloading stolen data and forbids paying or negotiating. Trigger phrases: watch ransomware leak sites, victim name monitoring, leak blog."
mitre_attack: [T1486, T1657]
nist_csf: [DE.CM, RS.CO]
mitre_f3: [F1005]
---

# Ransomware Leak-Site Monitoring

A leak blog is an extortion channel. Watch names for early warning; do not become a distribution node for stolen data.

## When to Use This Skill

Use this skill when:

- The org wants early warning if its name appears
- A sector watch list is required for leadership
- IR wants confirmation that a rumor matches a public listing

Do NOT use this skill when:

- The user wants to download leaked files
- The user wants negotiation scripts

**Trigger phrases**: "watch ransomware leak sites", "victim name monitoring", "leak blog"

## Instructions

### Step 1: Define the watch list

Legal names, product names, and common misspellings. Keep it in an access-controlled file.

### Step 2: Collect listings, not loot

Record post titles, timestamps, and screenshots of the name. Never fetch the stolen archive.

### Step 3: Match with a human confirm

Automated string match plus a human check before paging executives. Homographs and partial matches are common.

### Step 4: Escalate through IR, not Twitter

If matched, open an incident and preserve the listing evidence. Do not amplify the actor's post.

### Step 5: Retire stale watches

Actors rebrand. Review the source list quarterly and drop dead mirrors.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| We should download the leak to confirm | Possession of stolen data can itself be a legal and ethical failure. Names are enough for early warning. |
| Posting the listing internally is harmless | Re-hosting extortion content spreads it. Link to the ticket, not the loot. |
| Paying for early removal is a monitoring tactic | Payment is a business decision outside this skill and funds crime. |

## Verification

- [ ] Watch list is access-controlled
- [ ] Runbook forbids downloading archives
- [ ] A match produces an IR ticket, not a public post

## Related Skills

- [[ransomware-incident-response]] -- a confirmed listing may start IR
- [[ioc-enrichment-and-reputation-triage]] -- listed negotiation domains still need IOC handling

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
