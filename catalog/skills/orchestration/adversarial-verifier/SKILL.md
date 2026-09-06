---
name: adversarial-verifier
description: Act as a "breaker" agent that actively tries to break another agent's implementation by generating adversarial inputs, edge cases, attack vectors, and contract violations. Produces ADVERSARIAL-REPORT.md as an independent verification artifact. Use after implementation and standard verification to stress-test code before merge.
summary_l0: "Stress-test implementations with adversarial inputs, edge cases, and attack vectors"
overview_l1: "This skill acts as a breaker agent that actively tries to break another agent's implementation by generating adversarial inputs, edge cases, attack vectors, and contract violations. Use it after implementation and standard verification to stress-test code before merge, when validating security-critical code, or when high-confidence correctness is required. Key capabilities include adversarial input generation, boundary condition exploration, security attack vector testing, contract and invariant violation detection, race condition provocation, resource exhaustion testing, and independent verification report generation. The expected output is an ADVERSARIAL-REPORT.md with categorized findings including discovered vulnerabilities, edge case failures, and contract violations with reproduction steps. Trigger phrases: adversarial testing, break the code, stress test, edge cases, attack vectors, security testing, contract violations, adversarial verification."
---

# Adversarial Verifier

Act as an adversarial "breaker" agent whose sole purpose is to find ways to break an implementation. Unlike standard code review (which evaluates quality) or standard verification (which checks acceptance criteria), this skill instructs the agent to actively attack the implementation by generating adversarial inputs, exploiting edge cases, probing security boundaries, and violating assumed contracts. Every confirmed vulnerability must be backed by a concrete failing test or equivalent observed execution evidence; a candidate blocked only by an unobservable layer remains `needs-live-validation` rather than being rejected.

## When to Use This Skill

Use this skill when:

- An implementation has passed standard review and verification but the change is high-stakes
- You want independent adversarial testing before merging security-sensitive, payment, or data pipeline code
- You are using a multi-model orchestration workflow and want a fifth "breaker" phase after verification
- The implementation handles user input, external data, or untrusted sources
- You want to stress-test AI-generated code that passed acceptance criteria but may have blind spots

**Trigger phrases**: "adversarial verification", "break this code", "red team the implementation", "stress test", "find vulnerabilities", "breaker agent", "attack this code", "adversarial testing", "try to break it"

## What This Skill Does

- **Attack Surface Analysis**: Identifies all entry points, inputs, and trust boundaries in the implementation
- **Adversarial Input Generation**: Creates inputs designed to trigger crashes, incorrect output, or unexpected behavior
- **Edge Case Exploitation**: Probes boundary conditions, off-by-one errors, overflow/underflow, and empty/null inputs
- **Security Probing**: Tests for injection, authentication bypass, authorization flaws, and data exposure
- **Contract Violation**: Attempts to violate assumed preconditions, invariants, and postconditions
- **Proof-of-Failure Tests**: Every finding must include a concrete test that fails against the current implementation
- **Independent Artifact**: Produces ADVERSARIAL-REPORT.md that stands alone for audit

## Instructions

### Step 1: Map the Attack Surface

Read the implementation and identify all entry points where external input enters the system.

**Attack Surface Inventory:**

```markdown
## Attack Surface

| # | Entry Point | Input Source | Trust Level | Data Type |
|---|------------|-------------|-------------|-----------|
| E-1 | [function/endpoint] | [user input / API / file / env var] | [untrusted / semi-trusted / trusted] | [string / int / JSON / binary] |
| E-2 | ... | ... | ... | ... |
```

Prioritize entry points by trust level (untrusted first) and data complexity (structured input like JSON/XML is more attack-prone than simple integers).

### Step 2: Generate Adversarial Inputs

For each entry point, generate inputs across these attack categories:

| Category | Technique | Example Inputs |
|----------|-----------|----------------|
| **Boundary values** | Min, max, zero, negative, overflow | `0`, `-1`, `2^31-1`, `2^63`, `""`, `[]` |
| **Type confusion** | Wrong types, coercion traps | `"123"` where int expected, `NaN`, `Infinity`, `null` |
| **Injection** | SQL, command, template, path traversal | `'; DROP TABLE--`, `$(whoami)`, `{{7*7}}`, `../../etc/passwd` |
| **Encoding** | Unicode, null bytes, overlong UTF-8 | `\x00`, `\uFEFF`, `%00`, mojibake sequences |
| **Size extremes** | Empty, very large, deeply nested | Empty string, 10MB payload, 1000-level nested JSON |
| **Concurrency** | Race conditions, double-submit | Parallel identical requests, rapid state toggles |
| **State manipulation** | Invalid state transitions, replay | Expired tokens, reused nonces, out-of-order operations |
| **Resource exhaustion** | Algorithmic complexity attacks | Regex backtracking inputs, hash collision payloads |

### Step 3: Write Proof-of-Failure Tests

For every runnable adversarial candidate, write a concrete test that demonstrates the failure. **A confirmed finding without a failing test or equivalent observed execution evidence is not confirmed.** When the exact test cannot run because a deciding layer is outside the observable scope, retain the candidate as `needs-live-validation` with the safe validation receipt required by `[[pentest-reporting]]`.

```python
# Example: proof-of-failure test for boundary value bug
def test_adversarial_negative_payment_amount():
    """
    Adversarial finding AF-1: process_payment does not validate
    negative amounts, allowing balance to increase on payment.
    """
    user = create_test_user(balance=100)
    # This should raise ValidationError but currently succeeds
    result = process_payment(user, amount=-50)
    # BUG: balance is now 150 instead of raising an error
    assert user.balance == 150  # demonstrates the bug exists
```

```javascript
// Example: proof-of-failure test for injection vulnerability
test("adversarial: SQL injection in search query", () => {
  const maliciousInput = "'; DROP TABLE users; --";
  // This should sanitize input but currently passes it through
  const query = buildSearchQuery(maliciousInput);
  // BUG: raw input is interpolated into SQL
  expect(query).toContain("DROP TABLE");  // demonstrates the vulnerability
});
```

**Test naming convention**: prefix all adversarial tests with `test_adversarial_` (Python) or `adversarial:` (JavaScript) to distinguish them from standard tests.

### Step 4: Verify the Verifier

Each proof-of-failure test must actually fail when run against the current implementation. A passing test makes the candidate eligible for refutation review; it does not automatically prove the vulnerability absent, because the test may cover only one input route or may rely on an unobserved control.

**Verification protocol:**

1. Run each adversarial test individually
2. Record whether it passes or fails
3. Classify each finding:

| Test Result | Finding Classification | Action |
|------------|----------------------|--------|
| Test FAILS (as expected) | **Confirmed vulnerability** | Include in report with P0/P1/P2 severity |
| Test PASSES | **Refutation candidate** | Apply Steps 4.1 and 4.2; reject only on observed, route-complete evidence |
| Test ERRORS (cannot run) | **Inconclusive** | Fix and re-run; if an unobservable layer is the blocker, use `needs-live-validation` |

### Step 4.1: Apply the Refutation-Validity Taxonomy

A refutation kills a finding, so it carries the finding's own proof burden. Accept a refutation only when its reason is observable in the artifacts or an authorized run.

| Verdict | Refutation claim | Required basis |
|---------|------------------|----------------|
| **VALID** | The cited code does not perform the behavior claimed | Point to the actual instruction, branch, or data flow that contradicts the claim |
| **VALID** | The entry point is not attacker-reachable | Show the observable build and default-configuration evidence that excludes the path |
| **VALID** | A mitigating check blocks the behavior | Point to the check in code or runtime evidence the verifier can inspect |
| **VALID** | The behavior is designed under the established trust model | Cite the established trust-boundary artifact and show the implementation conforms to it |
| **INVALID** | "The framework probably handles it", "authorization is presumably upstream", or "a real server would validate this" | An unobserved layer is an assumption, not a refutation; the test exists because that layer might be insecure |
| **INVALID** | "The component is not loaded", "it requires non-default configuration", or "it is behind a flag" without checking | Reachability and gating claims require build and default-configuration evidence before they can kill a finding |

Assuming an unobserved layer is secure is the single most common false negative in adversarial review. When that layer is the only remaining barrier, assign `needs-live-validation`, never `rejected` or an understated Low rating, and use `[[pentest-reporting]]` for the required safe test, vulnerable response, safe response, and potential severity.

A capability that ships enabled by default is in scope even when its packaging makes it look optional. A reachability claim must inspect what the observable default build loads, not infer behavior from a module name or directory layout.

Hold both error directions in view. This procedure is tuned to challenge false positives, but once a verifier enters refute mode, dismissing a real high-impact finding as theoretical becomes the easier failure. A panel may move a candidate to `needs-live-validation` without consensus; rejection requires a majority whose votes each point to an observed reason.

### Step 4.2: Satisfy the Rejection Proof Burden

Before assigning `rejected`, enumerate the sink's actual input sources and prove the counter-hypothesis across every applicable route. Check URL path, query string, request body, cookie, header, decoded blob, and any additional source visible in the implementation. A mitigation that blocks one delivery route does not establish that the sink is safe through the others, so a single-route non-reproduction is not a refutation.

Every rejection record MUST contain:

1. A reason-specific **counter-hypothesis**: the concrete proposition that, if proven, kills the finding.
2. The sink's **actual input-source inventory**, derived from the implementation rather than copied from a generic checklist.
3. A **per-route result** for every source: either an executed check with observed evidence or a reasoned `not-applicable` tied to the code path.
4. When reachability or gating is the counter-hypothesis, the **build and default-configuration evidence** that establishes it.

A bare route list proves only that routes were named; it does not prove any check ran. False rejection is the costliest review error because it silently erases a real bug, while false confirmation stays visible and can be retested.

### Step 5: Classify Severity

For each confirmed finding:

| Severity | Criteria | Examples |
|----------|----------|---------|
| **P0 - Critical** | Data loss, security breach, system crash | SQL injection, auth bypass, unhandled exception in payment path |
| **P1 - High** | Incorrect output, data corruption, DoS potential | Boundary value producing wrong result, integer overflow, algorithmic complexity attack |
| **P2 - Medium** | Degraded behavior, information leakage, edge case mishandling | Error message exposing internals, null input causing unhelpful error, locale-dependent behavior |
| **P3 - Low** | Cosmetic, non-exploitable edge case | Unicode display issue, harmless type coercion, unnecessary precision loss |

### Step 6: Produce the Adversarial Report

Generate ADVERSARIAL-REPORT.md as an independent artifact:

```markdown
# Adversarial Verification Report

**Implementation**: [feature/PR description]
**Breaker Agent**: [model name]
**Date**: [timestamp]
**Scope**: [files and functions tested]

## Attack Surface Summary

| Entry Points Analyzed | Adversarial Inputs Generated | Tests Written | Confirmed Findings |
|----------------------|-----------------------------|--------------|--------------------|
| [count] | [count] | [count] | [count] |

## Confirmed Findings

### AF-1: [Title] (P0 - Critical)
**Entry Point**: [function/endpoint]
**Attack Category**: [injection / boundary / etc.]
**Description**: [what the vulnerability is and why it matters]
**Proof Test**: `test_adversarial_[name]` in `tests/adversarial/test_[module].py`
**Test Result**: FAILS (vulnerability confirmed)
**Suggested Fix**: [specific remediation]

### AF-2: [Title] (P1 - High)
...

## Rejected Findings (Observed Refutations)

| # | Counter-Hypothesis | Actual Input Sources | Per-Route Results | Observed Kill Evidence |
|---|--------------------|----------------------|-------------------|------------------------|
| RJ-1 | [reason-specific proposition] | [implementation-derived routes] | [executed result or reasoned N/A per route] | [artifact/build/config/runtime evidence] |

## Needs Live Validation

| # | Unobserved Layer | Minimal Safe Test | Vulnerable vs. Safe Response | Potential Severity |
|---|------------------|-------------------|------------------------------|--------------------|
| LV-1 | [deciding layer] | [exact authorized request, command, or test] | [both expected outcomes] | [band and score] |

## Untested Areas

| Area | Reason Not Tested | Risk |
|------|------------------|------|
| [area] | [reason] | [low/medium/high] |

## Overall Assessment

**Verdict**: PASS / FAIL / CONDITIONAL PASS
**Confirmed Vulnerabilities**: [count by severity]
**Recommendation**: [merge / fix and re-test / reject]
```

## Best Practices

- **Run adversarial verification after standard verification**: the breaker agent should attack code that already passes acceptance criteria, not code that is still under development
- **Use a different model for the breaker**: if the implementation was written by Claude Sonnet, use Claude Opus or Codex as the breaker to reduce blind-spot overlap
- **Every confirmed finding needs failing evidence**: use a failing test or equivalent observed execution; when a deciding layer cannot be run, keep the candidate pending with a `needs-live-validation` receipt
- **Reject only with an observed, route-complete record**: a passing test is useful negative evidence for that route, not automatic proof that the whole finding is false
- **Time-box adversarial verification**: diminishing returns set in quickly; 30-45 minutes is usually sufficient for a single feature's adversarial review
- **Focus on untrusted inputs first**: start with user-facing entry points and external data sources before testing internal interfaces
- **Do not fix the code**: the breaker's job is to find and report, not to fix; fixing is a separate step that should be done by the implementer or a different agent

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It passed code review and the acceptance tests, so it is safe to merge." | Acceptance tests check the happy path the author imagined; a single empty-array or negative-length input the author never considered can still crash production. Adversarial verification exists to find the inputs nobody planned for. |
| "I will just eyeball the code for edge cases instead of writing failing tests." | An opinion that "this might overflow" is noise without a reproduction. Only a test that actually fails against the current implementation proves the bug and survives the next refactor. |
| "The same agent that wrote the code can break it." | Authors share their own blind spots; the breaker should be a different model so the assumptions baked into the implementation are not silently re-baked into the attack. |
| "Documenting the inputs I tested and found safe is wasted effort." | The rejection record is what lets a reviewer trust the verdict; without observed per-route evidence, a PASS is indistinguishable from "I did not look very hard." |
| "The unseen server probably rejects this, so the finding is theoretical." | Probable security is not observed security; when the unseen layer is the only barrier, preserve the candidate as `needs-live-validation` with the exact safe test instead of silently erasing it. |
| "One route passed, so the sink is safe." | Inputs often reach the same sink through path, query, body, cookie, header, or decoded data; one passing route says nothing about the untested routes, so rejection requires a per-route result. |

## Verification

- [ ] `ADVERSARIAL-REPORT.md` exists and lists every entry point from the Attack Surface inventory
- [ ] Each confirmed finding includes a concrete test that fails against the current implementation
- [ ] Each rejected finding states a reason-specific counter-hypothesis backed by an observed reason
- [ ] Each rejected finding inventories the sink's actual input sources and records an executed result or reasoned `not-applicable` for every route
- [ ] Each reachability or gating rejection cites observable build and default-configuration evidence
- [ ] Each candidate blocked only by an unobservable layer is `needs-live-validation` with the receipt required by `[[pentest-reporting]]`
- [ ] A verifier panel rejected no finding without a majority pointing to observed reasons
- [ ] The report ends with an explicit verdict: PASS, FAIL, or CONDITIONAL PASS
- [ ] No code was modified by the breaker agent (find-and-report only)

## Related Skills

- [[functional-verification]] - owns normal real-boundary exercise and its evidence record; this skill owns hostile inputs and adversarial findings.
- [[cross-model-orchestrator]] - Multi-model workflow where breaker is the fifth role
- [[intent-based-review]] - Criteria-based review that the breaker complements
- [[edge-case-generator]] - Generate edge cases (used as a sub-technique by this skill)
- [[fuzzing-input-generator]] - Generate fuzz inputs (used as a sub-technique)
- [[exploitability-analyzer]] - Analyze whether a found vulnerability is exploitable
- [[security-review]] - Broader security review covering architecture and dependencies
- [[mutation-testing]] - Test whether tests catch injected faults (related but distinct goal)

---

**Version**: 1.0.0
**Last Updated**: March 2026
**Based on**: Adversarial testing patterns, red team methodologies, Swiss Cheese verification model
