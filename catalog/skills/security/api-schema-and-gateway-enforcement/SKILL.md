---
name: api-schema-and-gateway-enforcement
description: "Enforce API contracts at the gateway with schema validation, method allowlists, and reject-unknown-fields. Use this skill whenever the user says \"OpenAPI gateway validation\", \"reject additionalProperties\", \"protobuf allow-list methods\", \"API contract enforcement\", or wants the gateway to be the contract. SKIP, do NOT use for, object-level IDOR testing, or designing rate-limit keys."
summary_l0: "Enforce OpenAPI or protobuf contracts at the gateway including unknown fields"
overview_l1: "This skill makes the gateway the contract: methods, content types, and unknown fields die at the edge. Trigger phrases: OpenAPI gateway validation, reject additionalProperties, protobuf allow-list methods, API contract enforcement."
mitre_attack: [T1190]
d3fend_techniques: [D3-ITA]
nist_csf: [PR.DS, DE.CM]
---

# API Schema Validation and Gateway Controls

If the app parser is more generous than the spec, attackers speak a dialect your tests never used. Make the gateway as strict as the contract.

## When to Use This Skill

Use this skill when:

- Clients send fields the spec never named
- A GraphQL or REST gateway is a pass-through
- Undocumented verbs still 200

Do NOT use this skill when:

- The task is BOLA testing
- The task is rate-limit design

**Trigger phrases**: "OpenAPI gateway validation", "reject additionalProperties", "protobuf allow-list methods", "API contract enforcement"

## Instructions

### Step 1: Treat the spec as generated from code or fail CI

Hand-edited OpenAPI drifts. Generate or gate PRs on spec diffs.

### Step 2: Turn on schema validation at the edge

JSON Schema additionalProperties false, max lengths, and enum checks. Log rejects.

### Step 3: Allowlist methods and content types

A POST-only resource should 405 on PUT before the app sees it.

### Step 4: Mass-assignment is a schema bug

Unknown fields that bind to models are how isAdmin arrives. Reject them at the gateway, not in a hope.

### Step 5: Add a consumer contract test

A fixture that sends an extra field must fail the pipeline if the gateway would accept it.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| The app validates, so the gateway can be dumb | The app is one parser. Attackers will find the other one (batch jobs, older nodes). |
| additionalProperties true is more agile | It is how surprise fields become production state. |
| GraphQL introspection is fine in prod | It is a live schema leak. Disable or restrict it. |

## Verification

- [ ] Gateway rejects unknown fields in a test
- [ ] Disallowed methods return 405 at the edge
- [ ] CI fails when spec and code diverge

## Related Skills

- [[api-inventory-and-undocumented-endpoints]] -- inventory tells you what the gateway must know
- [[api-object-level-authorization-flaws]] -- schema checks do not replace object auth

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
