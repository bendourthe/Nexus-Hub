---
name: threat-intel-feed-operations
description: "Operate threat-intel feeds: ingest, deduplicate, score, expire, and measure downstream detection value. Use this skill whenever the user says \"intel feed pipeline\", \"STIX TAXII ingest\", \"IOC feed hygiene\", \"expire stale indicators\", or wants to stop a noisy blocklist from paging the SOC. SKIP, do NOT use for, one-off IOC lookups (use ioc-enrichment-and-reputation-triage), or building crawlers that hit third-party sites without authorization."
summary_l0: "Run intel-feed ingest, scoring, expiry, and detection-value measurement"
overview_l1: "This skill runs the feed as a production pipeline: schema, dedup, scoring, expiry, and a feedback loop from detections. A feed that cannot expire is a false-positive engine. Trigger phrases: intel feed pipeline, STIX TAXII ingest, IOC feed hygiene, expire stale indicators."
mitre_attack: [T1071]
nist_csf: [DE.CM, ID.IM]
---

# Threat-Intel Feed Operations

Treat threat feeds as a production data pipeline with owners, SLOs, and expiry, not as a folder of forever-blocklists.

## When to Use This Skill

Use this skill when:

- A new STIX/TAXII or CSV feed is being onboarded
- The SOC is drowning in feed-sourced alerts
- Nobody can say which feed produced a block

Do NOT use this skill when:

- A single indicator needs enrichment
- The user wants an unauthorized scraper

**Trigger phrases**: "intel feed pipeline", "STIX TAXII ingest", "IOC feed hygiene", "expire stale indicators"

## Instructions

### Step 1: Define the schema and owners

Every indicator needs type, value, source, first-seen, last-seen, TLP, and an expiry rule. Name the human owner of the feed.

### Step 2: Ingest with provenance

Preserve the source object ID. If two feeds share an indicator, keep both provenances; do not collapse them into an anonymous 'intel' tag.

### Step 3: Deduplicate and score

Scoring must combine source reliability and recency. A ten-year-old hash from an unrated list is not equal to yesterday's confirmed incident.

### Step 4: Expire aggressively

Dynamic IPs and parked domains rot. If the feed has no expiry, invent a conservative one and document it.

### Step 5: Measure detection value

Track true-positive rate per feed. Disable or quarantine feeds that only produce false positives.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| More indicators are always better | An unexpiring list pages the SOC and trains analysts to ignore alerts. |
| We should keep expired indicators 'just in case' | Historical context belongs in a warehouse, not in the blocking path. |
| Vendor STIX is already clean | STIX can still carry duplicates, revoked objects, and TLP violations. |

## Verification

- [ ] Feed schema includes expiry and provenance
- [ ] A dashboard or query shows true-positive rate per feed
- [ ] At least one stale-indicator expiry job is defined

## Related Skills

- [[ioc-enrichment-and-reputation-triage]] -- the feed is the bulk path; this is not one-off triage
- [[siem-detection-engineering]] -- feed hits must be attributable in the SIEM

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
