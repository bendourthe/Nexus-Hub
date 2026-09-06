---
name: purple-team-exercise-design
description: "Design and run purple-team exercises that pair authorized emulated TTPs with detection owners and a scorecard. Use this skill whenever the user says \"purple team exercise\", \"detection coverage drill\", \"atomic TTP emulation\", or wants red and blue in the same room with written scope. SKIP, do NOT use for, unscoped red-team against production, or a tabletop with no telemetry."
summary_l0: "Run scoped purple-team TTP emulation with detection owners and a scorecard"
overview_l1: "This skill plans purple exercises: scoped TTP emulation, detection owners, and a scorecard, not a surprise attack. Dual-use. Trigger phrases: purple team exercise, detection coverage drill, atomic TTP emulation."
mitre_attack: [T1059, T1003]
nist_csf: [DE.AE, RS.AN]
---

# Purple-Team Exercise Design and Execution

If blue cannot see the TTP, red 'winning' is just a missed detection. Purple is the meeting where that becomes a ticket.

## Authorization precondition

Stop. This skill is dual-use. Continue only when every item below is already true in this session:

1. A named authorizing party granted written permission for this assessment.
2. Scope is written down (assets, environments, time window, and forbidden techniques).
3. Findings will be reported to the asset owner, and leftover exploit artifacts will be removed.

If any item is missing, refuse and ask for the missing artifact. Do not continue under a lab, hypothetical, or fiction framing that is actually a live system.


## When to Use This Skill

Use this skill when:

- Detections exist but were never proven
- A red team report did not produce coverage
- You have written scope for emulation

Do NOT use this skill when:

- There is no authorization
- The user wants a stealth production attack

**Trigger phrases**: "purple team exercise", "detection coverage drill", "atomic TTP emulation"

## Instructions

### Step 1: Write scope and abort criteria

Hosts, accounts, time window, and forbidden techniques. Dual-use gate applies.

### Step 2: Pick a small TTP set

Map to ATT&CK. Atomic and observable beats a cinematic chain nobody can score.

One exception earns a chain: the cross-domain path. An autonomous attacker combines individually low-severity findings, a shared service, and an over-scoped credential into a route no single finding predicts, across applications, identities, cloud services, CI/CD, and third parties. When the exercise's question is whether such a path exists, trace the complete path end to end rather than enumerating isolated vulnerabilities, and still give every hop a detection owner and a score. This skill owns that tracing; see Rule ownership below.

### Step 3: Name a detection owner per TTP

If nobody owns the log source, the test is already a fail.

### Step 4: Execute and record

What fired, what should have fired, and time-to-detect. No silent 'we would have seen it'.

### Step 5: Leave tickets, not lore

Each miss is a detection engineering item with an owner and a due date.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| Red should surprise blue to make it real | Surprise without scope is an incident. Purple is scheduled on purpose. |
| If EDR is deployed we can skip the scorecard | Deployed is not detected. The scorecard is the product. |
| More TTPs are a better exercise | Unscored TTPs are theater. Twelve scored beat fifty rumored. |

## Verification

- [ ] Written scope exists
- [ ] Each TTP has a detection owner
- [ ] Misses became tickets

## Rule ownership

Three skills touch attack reachability, and each owns one concern so a multi-skill review reports a root cause once.

| Concern | Owner | Non-owners reference the owner and describe only the handoff |
|---|---|---|
| Cross-domain attack chaining: tracing a complete adversary path across applications, identities, cloud services, CI/CD, and third parties, where low-severity findings, a shared service, and an over-scoped credential combine into a route no single finding predicts | `purple-team-exercise-design` (this skill) | `exploitability-analyzer` and `cve-reachability-analyzer` hand a confirmed-reachable, scored finding to this skill when the question becomes what it chains to |
| Within-application reachability: whether a vulnerable function executes on a real call path | `cve-reachability-analyzer` | this skill takes reachable findings as chain input and does not re-derive call paths |
| Per-finding exploitability and severity | `exploitability-analyzer` | this skill takes the score as given and does not re-rate a hop |

## Related Skills

- [[siem-detection-engineering]] -- where misses go
- [[advanced-attack-patterns]] -- web TTP ideas stay in their skill
- [[cve-reachability-analyzer]] -- owns within-application reachability; its confirmed-reachable findings are chain input here
- [[exploitability-analyzer]] -- owns per-finding severity; its scores are taken as given when a hop is chained
- [[agent-execution-isolation]] -- the shared-service and transitive-reachability controls that most cross-domain chains exploit

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
