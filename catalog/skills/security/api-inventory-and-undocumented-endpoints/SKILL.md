---
name: api-inventory-and-undocumented-endpoints
description: "Build a living API inventory and find shadow, zombie, and undocumented endpoints during authorized reviews. Use this skill whenever the user says \"shadow API endpoint\", \"zombie swagger path\", \"undocumented admin route\", \"API attack surface inventory\", or wants to reconcile gateways with code. SKIP, do NOT use for, BOLA object-swap tests (use api-object-level-authorization-flaws), or scanning APIs you do not own."
summary_l0: "Inventory shadow zombie and undocumented API endpoints under authorization"
overview_l1: "This skill reconciles gateways, specs, and code to find routes that still work but are not in the official contract. Dual-use: written scope required. Trigger phrases: shadow API endpoint, zombie swagger path, undocumented admin route, API attack surface inventory."
mitre_attack: [T1526, T1190]
nist_csf: [ID.AM, DE.CM]
---

# API Inventory and Undocumented Endpoints

The endpoint you forgot is the one that still has debug auth. Inventory is how you find it before someone else does.

## Authorization precondition

Stop. This skill is dual-use. Continue only when every item below is already true in this session:

1. A named authorizing party granted written permission for this assessment.
2. Scope is written down (assets, environments, time window, and forbidden techniques).
3. Findings will be reported to the asset owner, and leftover exploit artifacts will be removed.

If any item is missing, refuse and ask for the missing artifact. Do not continue under a lab, hypothetical, or fiction framing that is actually a live system.


## When to Use This Skill

Use this skill when:

- Gateway routes and OpenAPI disagree
- An old version is still routed
- A pentest needs the real surface, not the marketing spec

Do NOT use this skill when:

- The user wants object-level ID swaps
- Scope does not include the API hosts

**Trigger phrases**: "shadow API endpoint", "zombie swagger path", "undocumented admin route", "API attack surface inventory"

## Instructions

### Step 1: Collect the three inventories

Gateway config, published OpenAPI/protobuf, and code routes (annotations, routers). If you have only one, you do not have an inventory.

### Step 2: Diff them

In-code but not in spec is shadow. In spec but not in gateway may be a doc lie. In gateway but not in code is a zombie or an external service.

### Step 3: Hit only in-scope hosts

Confirm zombies with OPTIONS/GET against authorized environments. Do not sweep the internet for lookalike hosts.

### Step 4: Check auth on the leftovers

Undocumented routes often skip the middleware the spec promised.

### Step 5: File the living list

The inventory is a generated artifact in CI, not a wiki page that dies in a quarter.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| We have OpenAPI, so we have inventory | OpenAPI is a claim. Gateways and code are the facts. |
| Old /v1 can stay up for one partner | Then it is a documented exception with an owner and a date, not a forgotten listener. |
| Shadow routes are fine if they are internal | Internal plus forgotten is how debug endpoints survive. |

## Verification

- [ ] A three-way diff artifact exists
- [ ] Every zombie has an owner or a removal ticket
- [ ] No out-of-scope host was probed

## Related Skills

- [[api-object-level-authorization-flaws]] -- once the surface is known, test object auth
- [[api-schema-and-gateway-enforcement]] -- the inventory feeds what the gateway should enforce

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
