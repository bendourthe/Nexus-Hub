---
name: egress-redaction
description: Detect sensitive data and apply a typed per-policy action (block, redact, hash, or pass) before any artifact crosses a trust boundary. Make sure to use this skill whenever the user wants to "redact sensitive data before sending", "PII detection", "scrub secrets from a prompt", "decide what can leave the trust boundary", or "redact before handing off to another model / agent / log", even if they only say "make sure we are not leaking anything". SKIP, do NOT use for, encrypting data at rest, network-layer DLP appliances, or compliance program design (use the compliance skills).
summary_l0: "Detect sensitive data and apply a typed block/redact/hash/pass policy before egress"
overview_l1: "This skill teaches the agent to recognize sensitive data and apply a per-category policy action before any artifact leaves a trust boundary. It provides a typed taxonomy of sensitive-data categories with one-line recognition cues, four policy actions (BLOCK, REDACT, HASH, PASS), a conservative-by-default policy table, and the core rule that a redaction decision is made per egress event, not per value: the same value may pass internally yet be redacted on a cross-model handoff, a context pack, a log line, or an external send. It generalizes the handoff egress-hygiene step from cross-model orchestration into a reusable posture. This is detection-and-policy guidance for the agent's own judgment, not a guarantee; high-assurance flows still need a programmatic DLP layer. Trigger phrases: redact sensitive data before sending, PII detection, scrub secrets from a prompt, what can leave the trust boundary, redact before handoff."
---

# Egress Redaction

Decide what is allowed to leave a trust boundary, and act on that decision before the data goes out. Every time an artifact moves from your machine to somewhere you control less (another model behind an external CLI, a context pack written for a different agent, a log sink, an outbound API call), it crosses a trust boundary, and that crossing is an egress event. This skill gives you a typed way to recognize sensitive data and a small set of policy actions to apply at each egress event. It generalizes the handoff egress-hygiene step in `[[cross-model-orchestrator]]` from a single deny-glob into a reusable taxonomy and policy. Treat it as disciplined judgment, not a guaranteed control: a high-assurance environment still needs a programmatic data-loss-prevention layer underneath this.

## When to Use This Skill

Use this skill when you need to:

- Redact sensitive data before sending an artifact to another model, agent, tool, or external service
- Detect PII, secrets, or credentials in a prompt, file, or generated output before it leaves the host
- Decide what may cross a trust boundary on a cross-model handoff, a shared context pack, or a log line
- Scrub secrets and identifiers out of an artifact while keeping its structure legible to the recipient
- Define a default redaction policy for a workflow that repeatedly hands content to an external destination

**When NOT to use this skill:**

- You need encryption of data at rest or in transit (that is a cryptography and key-management task, not redaction)
- You are configuring a network-layer DLP appliance or an enterprise data-governance program (use the `compliance` skills such as `gdpr-compliance` and `ccpa-compliance`)
- The recipient is fully local on the operator's own machine and the content never leaves the host (no egress event, so no redaction gate applies)
- You are reviewing application code for vulnerabilities generally (use `[[security-review]]`)

**Trigger phrases**: "redact sensitive data before sending", "PII detection", "scrub secrets from a prompt", "what can leave the trust boundary", "redact before handing off to another model", "make sure we are not leaking anything"

## Instructions

### Step 1: Identify the egress event

A redaction decision is anchored to a boundary crossing, not to a value sitting in memory. Before sending anything, name the egress event you are about to perform. The common ones:

- **Cross-model handoff**: passing an artifact to a second model that runs behind an external CLI or API.
- **Context pack written for another agent**: a shared file or typed-fact store another agent will read (see `[[context-pack-builder]]`).
- **Log line**: anything written to a log, because logs get shipped to aggregators, screenshots, and support tickets.
- **External send**: any outbound call to a third-party service (an HTTP request, an email, a webhook, an issue comment).

If the recipient is fully local and the content never leaves the host, there is no egress event and the gate does not apply. Reserve the redaction step for any destination that reaches a service you control less than your own machine.

### Step 2: Classify against the sensitive-data taxonomy

Scan the outbound artifact and tag every value that matches a category below. Each category has a one-line recognition cue. Scan prose as well as typed fields: sensitive data hides in free-form narrative more often than in labeled columns.

| Category | Recognition cue |
|----------|-----------------|
| Identified persons | A real person's full name tied to an account, record, or identifier |
| Postal addresses | A street address, city, and postal or ZIP code that locate a residence or site |
| Email addresses | An at-sign address that routes to a real mailbox |
| Phone numbers | A dialable number in any national or international format |
| Government and tax IDs | National ID, social-security, passport, driver-license, or tax-registration numbers |
| Payment-card and bank numbers | Card numbers, account numbers, routing numbers, or international bank account numbers |
| Secrets, API keys, and tokens | High-entropy strings, key-prefixed credentials, signed tokens, or anything labeled key, secret, or token |
| Credentials | Usernames paired with passwords, password hashes, private keys, or session cookies |
| Precise geolocation | Latitude and longitude or fine-grained coordinates that pinpoint a person or asset |
| Health and biometric data | Diagnoses, medical-record numbers, prescriptions, genetic data, or biometric templates |
| Network and device identifiers | IP and hardware addresses, device IDs, hardware serials, or persistent fingerprints |
| Authentication material in transit | One-time codes, password-reset links, or short-lived verification strings |
| Internal-only content | Unpublished source, infrastructure topology, customer lists, or anything marked confidential or internal |
| Free-form sensitive narrative | Prose that embeds any of the above or describes a person's protected attributes |

### Step 3: Choose a per-category action

Each detected value gets exactly one of four actions, chosen by what the recipient legitimately needs:

- **BLOCK**: refuse to send the value at all. The data must not cross this boundary. Use when the recipient has no legitimate need for the value and exposure is high-impact (secrets, credentials, government and payment identifiers).
- **REDACT**: replace the value with a visible typed marker such as `[redacted:email]` or `[redacted:api-key]`, so the recipient knows a value of that type was present and removed. Use when the recipient needs the artifact's structure but not the value itself.
- **HASH**: replace the value with a stable one-way hash (for example a truncated digest of the normalized value, salted per workflow) when the recipient needs to correlate occurrences of the same value across records without ever seeing it.
- **PASS**: allow the value through unchanged. Use only when the value is not sensitive in this context.

The marker and hash forms keep the artifact legible to the recipient (it can still reason about shape and correlation) while withholding the underlying data, which is what makes them better than silently dropping a field.

### Step 4: Apply the default policy, escalate on uncertainty

Start from this conservative-by-default mapping and adjust only when the recipient has a documented, legitimate need:

| Category | Default action on egress |
|----------|--------------------------|
| Identified persons | REDACT |
| Postal addresses | REDACT |
| Email addresses | REDACT (HASH if correlation is required) |
| Phone numbers | REDACT |
| Government and tax IDs | BLOCK |
| Payment-card and bank numbers | BLOCK |
| Secrets, API keys, and tokens | BLOCK |
| Credentials | BLOCK |
| Precise geolocation | REDACT |
| Health and biometric data | BLOCK |
| Network and device identifiers | HASH (REDACT if correlation is not needed) |
| Authentication material in transit | BLOCK |
| Internal-only content | REDACT (BLOCK if classified) |
| Free-form sensitive narrative | REDACT |

The governing rule for anything the taxonomy does not cleanly cover: when a value looks suspicious but is unrecognized, default to the more conservative action. The conservatism order is BLOCK over REDACT over HASH over PASS. A false BLOCK costs a clarifying round trip; a false PASS is an irreversible leak.

### Step 5: Apply per egress event, and record the decision

The same value can be safe internally and unsafe on egress, so classify on every send and every new destination rather than once per session. Practical consequences:

- A value that PASSes when an artifact stays on the host must be re-evaluated the first time that artifact crosses an external boundary.
- The first time a given destination receives project content, state in one place WHAT is being sent, WHICH destination receives it, and WHICH actions were applied, then proceed. Recording this lets later sends to the same destination in the same session reuse the decision instead of re-deriving it.
- This is detection-and-policy guidance for the agent's own judgment. It reduces leak surface; it does not guarantee zero leakage. For regulated or high-assurance data, a programmatic DLP layer must sit underneath this skill, and `[[security-review]]` should confirm that layer exists.

## Content policy vs network boundary

This skill is a content control: typed BLOCK / REDACT / HASH / PASS applied by the agent before a send. The agent can skip it, forget a destination, or be instructed not to apply it. That is expected. It is not a network boundary.

High-stakes or untrusted-tool flows need an out-of-process egress proxy that the agent cannot bypass: static destination rules, an optional LLM judge on the request, SSRF and RFC-1918 blocks, and human approval for new hosts. That architecture lives in [[agent-execution-isolation]] (`references/egress-boundary.md`). Do not copy that runbook here. Use this skill to classify what may leave; use that skill to enforce that only classified, allowed traffic can leave.

A local DLP library that the agent process loads is still in-loop. Treat it as defense-in-depth on top of this policy, not as a substitute for the proxy.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It is just going to another AI model, not a person, so redaction is overkill." | A model behind an external CLI or API ships every byte to a third-party service; the handoff is an egress event exactly like an outbound API call. An injected instruction in that model's context can also exfiltrate whatever you sent, so unredacted secrets widen the blast radius. |
| "The secret is needed for the task, so I have to include the value." | The recipient almost never needs the secret value itself; it needs to know a secret exists or to correlate it across records. A typed REDACT marker or a HASH preserves that structure while withholding the value. |
| "I already redacted this once, so later sends are fine." | Redaction is per egress event. A value that was safe internally can still leak the first time it crosses a new boundary; re-classify on every send and every new destination. |
| "Logs are internal, so PII in a log line is acceptable." | A log line is an egress event: logs flow to aggregators, screenshots, and support tickets. Treat a log sink as an external destination unless you can prove it never leaves the host. |
| "It is low-risk free-form text, not a structured field, so it is fine." | Sensitive data hides in prose (a name beside a diagnosis, an address inside a sentence). Free-form narrative is the most common redaction miss; scan prose, not just labeled fields. |

## Verification

- [ ] Every egress event in the task was named (cross-model handoff, context pack, log line, external send) before any data was sent
- [ ] Each outbound artifact was classified against the sensitive-data taxonomy, including its free-form prose
- [ ] Each detected value was assigned exactly one action (BLOCK / REDACT / HASH / PASS) per the default policy
- [ ] Any unrecognized-but-suspicious value defaulted to the more conservative action
- [ ] Redacted values carry a visible typed marker so the recipient knows a typed value was removed
- [ ] No secret, credential, government ID, or payment identifier was sent in cleartext across any external boundary
- [ ] A recipient treated as exempt was confirmed to be fully local before its handoff was skipped
- [ ] High-stakes or untrusted-tool egress is named as content-policy-only or as out-of-process-enforced; if the latter, [[agent-execution-isolation]] `references/egress-boundary.md` is the architecture, not a second copy of this taxonomy

## Related Skills

- [[cross-model-orchestrator]] - the Handoff Egress Hygiene step this skill generalizes into a typed taxonomy and policy
- [[agent-access-policy]] - the broader least-privilege access posture that redaction fits into
- [[context-pack-builder]] - typed-fact entries that may carry sensitive content across an agent boundary
- [[security-review]] - application-level review that should confirm a programmatic DLP layer exists for high-assurance flows
- [[agent-execution-isolation]] - the out-of-process egress proxy and destination policy this content control does not replace

---

**Version**: 1.0.0
**Last Updated**: June 2026
**Based on**: Egress-control, data-minimization, and handoff-hygiene patterns
