---
name: ioc-enrichment-and-reputation-triage
description: "Enrich indicators of compromise and triage reputation across DNS, file hashes, URLs, and certificate fingerprints. Use this skill whenever the user says \"enrich this IOC\", \"hash reputation lookup\", \"URL triage\", \"passive DNS for this domain\", \"is this hash known malware\", or wants a first-pass verdict on a suspicious indicator. SKIP, do NOT use for, writing malware, scanning random third-party infrastructure, actor dossier writing (use threat-actor-ttp-profiling), or leak-site scraping (use ransomware-leak-site-monitoring)."
summary_l0: "Enrich IOCs and assign a documented reputation verdict with sources"
overview_l1: "This skill turns a raw indicator into a sourced reputation verdict. It covers hash, domain, URL, IP, and certificate enrichment, local cache first, then documented external lookups the user already operates. The output is a triage record with confidence, related infrastructure, and a next action, not a dump of vendor UI. Trigger phrases: enrich this IOC, hash reputation, URL triage, passive DNS, known malware hash."
mitre_attack: [T1071, T1041]
d3fend_techniques: [D3-IAA, D3-NTA]
nist_csf: [DE.CM, ID.RA]
---

# IOC Enrichment and Reputation Triage

Turn a raw indicator into a sourced reputation verdict before anyone detonates a sample or blocks a domain. The deliverable is a written triage record, not a pile of uncited screenshots.

## When to Use This Skill

Use this skill when:

- A hash, domain, URL, IP, or certificate fingerprint needs a first-pass verdict
- A detection alert includes an unknown indicator
- An incident channel asks whether a file is 'known bad'

Do NOT use this skill when:

- The user wants malware capabilities authored
- The work is long-form actor profiling
- There is no authorization to query the user's intel tools

**Trigger phrases**: "enrich this IOC", "hash reputation lookup", "URL triage", "passive DNS", "known malware hash"

## Instructions

### Step 1: Inventory the indicator and its origin

Record type, exact value, first-seen time, and the log or ticket that produced it. Reject truncated hashes and defanged URLs until they are restored with a documented transformation.

### Step 2: Search local stores before any live lookup

Query the SIEM, ticket corpus, and internal reputation cache. A hit here is higher trust than a public score and avoids leaking the indicator to a third party.

### Step 3: Run authorized enrichment

Use only intel platforms the user already operates. Capture vendor score, first-seen, related samples, and passive DNS. Write the source URL or console path next to every claim.

### Step 4: Correlate sibling indicators

Pivot to communicating IPs, dropped files, certificate serials, and registrant overlap. Stop when pivots leave the authorized scope.

### Step 5: Assign a verdict with confidence

Choose known-bad, suspicious, likely-benign, or unknown. Confidence must cite at least two independent sources or one internal confirmed incident.

### Step 6: Hand off the next action

State whether to block, monitor, detonate in a sandbox, or close. Name the owner of that action.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| The vendor score is already 100, so we can skip sources | Uncited scores cannot be replayed after the vendor changes the model; the ticket will not explain the block next week. |
| Defanging the URL is enough documentation | A defanged indicator that cannot be reconstructed is not an IOC; responders will hunt the wrong string. |
| Public lookup of a customer hash is always fine | Submitting a customer sample hash to a public service can disclose the incident to a third party. |

## Verification

- [ ] A triage record exists with indicator, type, sources, verdict, and confidence
- [ ] Every reputation claim names a source path or URL
- [ ] The next action is assigned to a named owner
- [ ] No enrichment query was sent to a service the user did not already operate

## Related Skills

- [[log-threat-hunting]] -- hunting often produces the IOC this skill enriches
- [[siem-detection-engineering]] -- a confirmed-bad IOC should become a detection, not a one-off block

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
