---
name: api-rate-limit-and-abuse-detection
description: "Design and test API rate limits, burst controls, and credential-stuffing or scraping abuse detections under authorization. Use this skill whenever the user says \"API rate limit bypass\", \"credential stuffing on login API\", \"scraper throttling\", \"429 vs 401 masking\", or wants abuse controls that do not lock out real users. SKIP, do NOT use for, BOLA tests, or running stuffing against a site you do not own."
summary_l0: "Design and test API rate limits and stuffing or scraping abuse controls"
overview_l1: "This skill puts measurable limits on login, search, and expensive endpoints, then tests bypasses (header rotation, distributed sources) only in scope. Trigger phrases: API rate limit bypass, credential stuffing on login API, scraper throttling, 429 vs 401 masking."
mitre_attack: [T1110, T1499]
nist_csf: [PR.DS, DE.CM]
---

# API Rate Limiting and Abuse Detection

A limit nobody can measure is not a limit. Abuse controls must name the dimension they meter and the user they must not strand.

## Authorization precondition

Stop. This skill is dual-use. Continue only when every item below is already true in this session:

1. A named authorizing party granted written permission for this assessment.
2. Scope is written down (assets, environments, time window, and forbidden techniques).
3. Findings will be reported to the asset owner, and leftover exploit artifacts will be removed.

If any item is missing, refuse and ask for the missing artifact. Do not continue under a lab, hypothetical, or fiction framing that is actually a live system.


## When to Use This Skill

Use this skill when:

- Login or OTP endpoints have no throttle
- A partner API is being scraped
- Rate-limit bypass is in the pentest scope

Do NOT use this skill when:

- The user wants to stuff credentials at a third party
- The bug is object-level authorization

**Trigger phrases**: "API rate limit bypass", "credential stuffing on login API", "scraper throttling", "429 vs 401 masking"

## Instructions

### Step 1: Name the expensive verbs

Auth, password reset, search, export, and LLM-backed endpoints. Limits belong there first.

### Step 2: Pick a dimension you can key

Account, IP, device, and API key are different keys. Shared NAT requires more than IP.

### Step 3: Fail closed for auth, fail soft for reads

Auth endpoints return the same timing and message on miss. Search can degrade with 429 and a Retry-After.

### Step 4: Test in-scope bypasses

Header spoofing, IPv6 dual-stack, and key rotation. Document what the control still catches.

### Step 5: Watch the false-lockout budget

A good control pages on stuffing, not on a conference NAT. Keep a break-glass path.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| CAPTCHA on everything is a rate limit | CAPTCHA is a friction tax and fails accessibility. Meter first. |
| We return 401 on lockout so attackers know to stop | That is an oracle. Uniform responses plus server-side counters. |
| CDN WAF defaults are enough | Defaults do not know your OTP endpoint. Measure it. |

## Verification

- [ ] Each expensive verb has a named meter key
- [ ] Auth responses do not oracle lockout
- [ ] Bypass tests stayed in scope

## Related Skills

- [[api-object-level-authorization-flaws]] -- throttling is not authorization
- [[identity-threat-detection]] -- stuffing detections often land in identity telemetry

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
