---
name: api-object-level-authorization-flaws
description: "Find broken object-level and function-level authorization in HTTP APIs (BOLA, BFLA, BOPLA) during authorized tests. Use this skill whenever the user says \"BOLA test\", \"IDOR in this API\", \"BFLA admin function\", \"broken object property authorization\", or wants to test whether changing an ID returns another tenant's record. SKIP, do NOT use for, unscoped testing of third-party APIs, or JWT alg-none attacks (use jwt-header-and-key-confusion-attacks)."
summary_l0: "Test BOLA BFLA and BOPLA object-level authorization on authorized APIs"
overview_l1: "This skill tests whether object IDs, function names, and property filters are authorization boundaries or decorations. It is dual-use and requires written scope. Trigger phrases: BOLA test, IDOR in this API, BFLA admin function, broken object property authorization."
mitre_attack: [T1190, T1078]
nist_csf: [PR.AA, DE.CM]
---

# API Object-Level Authorization Flaws

If the server trusts an object ID from the client, every tenant is one increment away. Prove it only inside written scope.

## Authorization precondition

Stop. This skill is dual-use. Continue only when every item below is already true in this session:

1. A named authorizing party granted written permission for this assessment.
2. Scope is written down (assets, environments, time window, and forbidden techniques).
3. Findings will be reported to the asset owner, and leftover exploit artifacts will be removed.

If any item is missing, refuse and ask for the missing artifact. Do not continue under a lab, hypothetical, or fiction framing that is actually a live system.


## When to Use This Skill

Use this skill when:

- An API uses enumerable IDs or predictable slugs
- A review needs object-level auth evidence
- A BOLA finding needs a replayable case

Do NOT use this skill when:

- There is no written authorization
- The question is JWT header confusion rather than object IDs

**Trigger phrases**: "BOLA test", "IDOR in this API", "BFLA admin function", "broken object property authorization"

## Instructions

### Step 1: Map resources and verbs

List every object type and whether GET/PUT/PATCH/DELETE are distinct authorization decisions.

### Step 2: Build two-tenant fixtures

Create or obtain two authorized accounts. Tests without a second tenant cannot prove BOLA.

### Step 3: Swap identifiers, not just guess them

Replay tenant A's token against tenant B's object IDs, including nested IDs in JSON bodies and batch endpoints.

### Step 4: Test function-level and property-level gaps

Hidden admin routes, GraphQL mutations, and sparse fieldsets that leak foreign properties.

### Step 5: Report with replay, impact, and the missing check

Cite the server file or gateway that should have compared owner to principal. Payloads stay against in-scope hosts.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| The UI never shows that ID, so it is safe | Attackers do not use the UI. Direct object requests are the test. |
| UUIDs make BOLA impossible | UUIDs stop incrementing; they do not stop leaked IDs in JS bundles, logs, or emails. |
| The gateway JWT is enough | A valid user calling another user's object is still BOLA. Authentication is not object authorization. |

## Verification

- [ ] Two-tenant evidence exists
- [ ] Each finding names the missing authorization check
- [ ] No out-of-scope host was touched

## Related Skills

- [[jwt-header-and-key-confusion-attacks]] -- token integrity is a different bug class
- [[business-logic-abuse]] -- workflow abuse may combine with BOLA

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
