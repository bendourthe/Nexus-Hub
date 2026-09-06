# Decision: Consolidate vendor-specific source skills into vendor-neutral capabilities at about 4.3:1

Status: implemented - roughly 173 comparison-catalog topics land as 40 Nexus-Hub skills; vendor product names stay out of skill identity

## Problem

Nexus-Hub already loads `name`, `description`, `summary_l0`, and `overview_l1` for every catalog skill in every session. At 273 skills that is about 104k Tier-1 tokens. The comparison catalog is 817 skills, many of them one-vendor (a single EDR, a single cloud detection product, a single ICS protocol toolkit). A 1:1 import of the same material would add about 66k always-resident tokens, and a full 817-skill overlay would project to about 416k. That cost is paid on every session, including sessions that never touch security.

## Decision

Adopt coverage as vendor-neutral capabilities, not as one skill per vendor product. The planned ratio is about 4.3:1 (173 source topics into 40 skills). Skill names describe the job (`ics-protocol-anomaly-detection`, `android-static-app-analysis`), not a vendor SKU. Product-specific commands may appear as examples inside Instructions when they are the public name of a technique, but they are not the skill's identity and they are not a separate catalog entry.

`ot-security` and `mobile-security` exist because ICS/SCADA work and mobile-app work are not near-duplicates of `security` (AppSec) or `security-operations` (DFIR and detection). Folding them into `security-operations` would hide the trigger surface.

## Alternatives considered

- **1:1 import of the comparison topics that passed the license bar.** Rejected: about +66k Tier-1 tokens for material that is mostly vendor SKU variants of the same capability. The catalog already under-triggers when descriptions are narrow; more near-duplicate names would make routing worse, not better.
- **Keep a single `security` category and use tags for OT and mobile.** Rejected: agents match on category plus description. OT and mobile operators will not look in AppSec, and AppSec reviewers will not look in DFIR. Two categories are cheaper than a routing miss.
- **Ship vendor-specific skills only for the five most common EDRs / clouds.** Rejected: it recreates the SKU treadmill inside Nexus-Hub and still misses the long tail. A capability skill plus an example command covers the common case without a new always-loaded frontmatter block per vendor.

## Consequences

- Users who want "the CrowdStrike skill" or "the Palo Alto skill" will not find a SKU-named file. They get `endpoint-edr-detection` (existing) or the new capability that names the job.
- Tier-1 growth is bounded by the 40-skill set, not by the comparison catalog's width. Measured growth is recorded in the v3.20.1 known-gaps file if it exceeds the ~15k projection.
- Adding a vendor-named skill later is a new decision, not an obvious follow-on. This record is the thing to grep before that proposal.
