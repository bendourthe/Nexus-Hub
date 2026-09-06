---
name: smart-contract-security-review
description: "Review smart contracts you are authorized to assess for reentrancy, authorization gaps, oracle manipulation, and upgrade hazards. Use this skill whenever the user says \"Solidity security review\", \"reentrancy in our contract\", \"oracle manipulation check\", or wants an audit of a contract you have permission to test. SKIP, do NOT use for, draining third-party protocols, or generic API BOLA."
summary_l0: "Review authorized smart contracts for reentrancy auth gaps and oracle risk"
overview_l1: "This skill audits in-scope contracts: reentrancy, access control, oracle and upgrade risks. Dual-use. Trigger phrases: Solidity security review, reentrancy in our contract, oracle manipulation check."
nist_csf: [ID.RA, PR.AC]
---

# Smart-Contract Security Review

The chain will faithfully run a bug at scale. Review the contract you are allowed to break, then fix it before mainnet.

## Authorization precondition

Stop. This skill is dual-use. Continue only when every item below is already true in this session:

1. A named authorizing party granted written permission for this assessment.
2. Scope is written down (assets, environments, time window, and forbidden techniques).
3. Findings will be reported to the asset owner, and leftover exploit artifacts will be removed.

If any item is missing, refuse and ask for the missing artifact. Do not continue under a lab, hypothetical, or fiction framing that is actually a live system.


## When to Use This Skill

Use this skill when:

- A Solidity/Vyper contract is about to ship
- An incident needs a contract-level hypothesis
- An upgrade proxy is in play

Do NOT use this skill when:

- The user wants to attack a live protocol they do not own
- The bug is an HTTP IDOR

**Trigger phrases**: "Solidity security review", "reentrancy in our contract", "oracle manipulation check"

## Instructions

### Step 1: Confirm chain, compiler, and permission

Mainnet fork tests against your contract, not someone else's vault.

### Step 2: Threat-model value flow

Who can mint, burn, withdraw, and upgrade. Draw it.

### Step 3: Check classic classes

Reentrancy, authorization, signed-message replay, oracle freshness, and delegatecall.

### Step 4: Test upgrades

Initializer front-running, storage layout collisions, and who holds the admin key.

### Step 5: Report with PoC on a fork

Foundry/Hardhat tests against a local fork. No mainnet exploitation.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| The protocol is immutable, so review is optional | Then bugs are immortal. Review harder. |
| A bounty is a substitute for review | Bounties find leftovers. Review is the main pass. |
| Public functions are fine if they are 'view' | View plus a callback into unsafe code is still a path. |

## Verification

- [ ] Permission to test is recorded
- [ ] Value-flow diagram exists
- [ ] PoCs run on a fork, not on victim mainnet funds

## Related Skills

- [[api-object-level-authorization-flaws]] -- authorization as a class, different substrate
- [[cryptographic-control-audit]] -- signature and replay issues overlap

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
