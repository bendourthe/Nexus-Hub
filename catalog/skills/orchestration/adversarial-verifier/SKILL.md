---
name: adversarial-verifier
description: Act as a "breaker" agent that actively tries to break another agent's implementation by generating adversarial inputs, edge cases, attack vectors, and contract violations. Produces ADVERSARIAL-REPORT.md as an independent verification artifact. Use after implementation and standard verification to stress-test code before merge.
summary_l0: "Stress-test implementations with adversarial inputs, edge cases, and attack vectors"
overview_l1: "This skill acts as a breaker agent that actively tries to break another agent's implementation by generating adversarial inputs, edge cases, attack vectors, and contract violations. Use it after implementation and standard verification to stress-test code before merge, when validating security-critical code, or when high-confidence correctness is required. Key capabilities include adversarial input generation, boundary condition exploration, security attack vector testing, contract and invariant violation detection, race condition provocation, resource exhaustion testing, and independent verification report generation. The expected output is an ADVERSARIAL-REPORT.md with categorized findings including discovered vulnerabilities, edge case failures, and contract violations with reproduction steps. Trigger phrases: adversarial testing, break the code, stress test, edge cases, attack vectors, security testing, contract violations, adversarial verification."
---

# Adversarial Verifier

Act as an adversarial "breaker" agent whose sole purpose is to find ways to break an implementation. Unlike standard code review (which evaluates quality) or standard verification (which checks acceptance criteria), this skill instructs the agent to actively attack the implementation by generating adversarial inputs, exploiting edge cases, probing security boundaries, and violating assumed contracts. Every claimed vulnerability must be backed by a concrete failing test.

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

For every adversarial finding, write a concrete test that demonstrates the failure. **A finding without a failing test is not a finding.**

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

Each proof-of-failure test must actually fail when run against the current implementation. If a test passes (meaning the "vulnerability" does not exist), the finding is automatically demoted.

**Verification protocol:**

1. Run each adversarial test individually
2. Record whether it passes or fails
3. Classify each finding:

| Test Result | Finding Classification | Action |
|------------|----------------------|--------|
| Test FAILS (as expected) | **Confirmed vulnerability** | Include in report with P0/P1/P2 severity |
| Test PASSES (vulnerability does not exist) | **False positive** | Demote; include in report as "tested, not vulnerable" |
| Test ERRORS (cannot run) | **Inconclusive** | Fix the test and re-run; do not include unrunnable tests |

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

## False Positives (Tested, Not Vulnerable)

| # | Attack | Entry Point | Test | Result |
|---|--------|------------|------|--------|
| FP-1 | [attack type] | [entry point] | [test name] | PASSES (not vulnerable) |

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
- **Every finding needs a failing test**: opinions without proof are noise; a test that fails against the implementation is the only accepted evidence
- **Classify false positives explicitly**: documenting what you tested and found safe is as valuable as finding vulnerabilities; it builds confidence in the implementation
- **Time-box adversarial verification**: diminishing returns set in quickly; 30-45 minutes is usually sufficient for a single feature's adversarial review
- **Focus on untrusted inputs first**: start with user-facing entry points and external data sources before testing internal interfaces
- **Do not fix the code**: the breaker's job is to find and report, not to fix; fixing is a separate step that should be done by the implementer or a different agent

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It passed code review and the acceptance tests, so it is safe to merge." | Acceptance tests check the happy path the author imagined; a single empty-array or negative-length input the author never considered can still crash production. Adversarial verification exists to find the inputs nobody planned for. |
| "I will just eyeball the code for edge cases instead of writing failing tests." | An opinion that "this might overflow" is noise without a reproduction. Only a test that actually fails against the current implementation proves the bug and survives the next refactor. |
| "The same agent that wrote the code can break it." | Authors share their own blind spots; the breaker should be a different model so the assumptions baked into the implementation are not silently re-baked into the attack. |
| "Documenting the inputs I tested and found safe is wasted effort." | The false-positive log is what lets a reviewer trust the verdict; without it, a PASS is indistinguishable from "I did not look very hard." |

## Verification

- [ ] `ADVERSARIAL-REPORT.md` exists and lists every entry point from the Attack Surface inventory
- [ ] Each confirmed finding includes a concrete test that fails against the current implementation
- [ ] Inputs tested and found safe are recorded in the False Positives section
- [ ] The report ends with an explicit verdict: PASS, FAIL, or CONDITIONAL PASS
- [ ] No code was modified by the breaker agent (find-and-report only)

## Related Skills

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
