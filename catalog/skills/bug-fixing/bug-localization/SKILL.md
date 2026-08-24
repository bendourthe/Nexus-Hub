---
name: bug-localization
description: Pinpoint bug locations using stack traces, error logs, code flow analysis, spectrum-based fault localization, and bisection techniques. Use when debugging failures, analyzing stack traces, tracing error origins, or narrowing down faulty code regions.
summary_l0: "Pinpoint bug locations using stack traces, log correlation, and fault localization"
overview_l1: "This skill systematically pinpoints the exact location of bugs in a codebase using stack trace analysis, error log correlation, code flow tracing, spectrum-based fault localization, and bisection techniques. Use it when determining which file or function contains a bug, analyzing stack traces to find the true origin of an exception, correlating log entries to identify behavioral divergence, applying statistical fault localization (Tarantula, Ochiai) to test results, using git bisect to narrow down the offending commit, or tracing data flow to where values become incorrect. Key capabilities include bottom-up and top-down stack trace reading, log timeline reconstruction, SBFL suspiciousness scoring, delta debugging, and code flow invariant checking. The expected output is a precise fault location report with file, line, and root cause explanation. Trigger phrases: find the bug, localize the fault, where is the bug, trace the error, analyze stack trace, which commit broke, bisect the failure, fault localization."
---

# Bug Localization

Systematically pinpoint the exact location of bugs in a codebase using a combination of stack trace analysis, error log correlation, code flow tracing, spectrum-based fault localization, and bisection techniques. This skill transforms vague symptoms into precise file-and-line identification.

## When to Use This Skill

Use this skill when you need to:

- Determine which file, class, or function contains a bug based on an error report
- Analyze stack traces to find the true origin of an exception (not just where it surfaced)
- Correlate multiple log entries to identify the point where behavior diverges from expectations
- Apply statistical fault localization techniques (Tarantula, Ochiai) to test suite results
- Use git bisect or delta debugging to narrow down the commit or change that introduced a defect
- Trace data flow through a system to find where values become incorrect
- Identify the root cause when an error manifests far from its origin

**Trigger phrases**: "find the bug", "localize the fault", "where is the bug", "trace the error", "analyze stack trace", "narrow down the issue", "which commit broke", "bisect the failure", "fault localization"

## What This Skill Does

### Methodology Overview

Bug localization follows a structured narrowing process that moves from broad symptom identification to precise fault location. The methodology combines multiple complementary techniques, each suited to different types of information available.

### Technique 1: Stack Trace Analysis

Stack traces are the most direct signal for localization. The skill teaches you to read them bottom-up (for languages where the root cause appears at the bottom) or top-down (for languages where it appears at the top), identify framework frames versus application frames, and distinguish the "caused by" chain to find the originating fault.

### Technique 2: Log Correlation

When stack traces are unavailable or insufficient, correlating log entries across time and components reveals the divergence point. This technique uses timestamps, request IDs, and contextual markers to reconstruct the execution timeline and identify where expected behavior stopped.

### Technique 3: Spectrum-Based Fault Localization (SBFL)

SBFL techniques use test execution data to statistically rank program elements by their suspiciousness. Elements executed primarily by failing tests (and rarely by passing tests) receive high suspiciousness scores. The two most effective formulas are Tarantula and Ochiai.

### Technique 4: Code Flow Tracing

When statistical methods are not applicable (for example, when there is only one failing test), manual or tool-assisted code flow tracing follows data from input to the point of failure, checking invariants at each step.

### Technique 5: Delta Debugging and Bisection

When a bug was introduced by a recent change, bisection (via git bisect or manual binary search) efficiently identifies the exact commit. Delta debugging extends this to isolate the minimal change within a commit that triggers the failure.

## Instructions

### Step 1: Gather and Classify Symptoms

Full walkthrough: [step-1-gather-and-classify-symptoms.md](references/step-1-gather-and-classify-symptoms.md) (load this step when you reach it).

### Step 2: Analyze Stack Traces

Full walkthrough: [step-2-analyze-stack-traces.md](references/step-2-analyze-stack-traces.md) (load this step when you reach it).

### Step 3: Correlate Log Entries

Full walkthrough: [step-3-correlate-log-entries.md](references/step-3-correlate-log-entries.md) (load this step when you reach it).

### Step 4: Apply Spectrum-Based Fault Localization

Full walkthrough: [step-4-apply-spectrum-based-fault-localization.md](references/step-4-apply-spectrum-based-fault-localization.md) (load this step when you reach it).

### Step 5: Use Git Bisect for Regression Localization

Full walkthrough: [step-5-use-git-bisect-for-regression-localization.md](references/step-5-use-git-bisect-for-regression-localization.md) (load this step when you reach it).

### Step 6: Apply Delta Debugging

Full walkthrough: [step-6-apply-delta-debugging.md](references/step-6-apply-delta-debugging.md) (load this step when you reach it).

## Best Practices

- Always start with the cheapest technique first: reading the error message and stack trace carefully costs nothing and often suffices.
- Filter out framework and library frames before analyzing stack traces; focus on your application code.
- When correlating logs, use structured logging with request IDs so that you can reconstruct per-request timelines across distributed systems.
- Combine SBFL with manual inspection: suspiciousness scores are a ranking aid, not a guarantee. Examine the top 5-10 elements manually.
- Automate git bisect with a reliable test script. A flaky test will produce incorrect bisect results.
- Document the localization process and findings so that future developers facing similar symptoms can reuse the approach.
- For intermittent bugs, collect data from multiple failure instances before attempting localization; a single instance may be misleading.
- Keep your test suite healthy: SBFL accuracy depends on having a diverse set of passing and failing tests with varied coverage patterns.

## Common Pitfalls

- **Reading stack traces from the wrong end.** Python tracebacks show the most recent call last (bottom is the fault point), while Java and JavaScript show the most recent call first (top is the fault point). Confusing this wastes significant time.
- **Stopping at the symptom instead of the cause.** A NullPointerException at line 42 does not mean line 42 is buggy; the null value may have been introduced hundreds of lines earlier. Always trace back to where the incorrect value originated.
- **Ignoring "Caused by" chains.** In Java and similar languages, the root cause is at the end of the "Caused by" chain. Fixing the outermost exception without examining the root cause leads to superficial patches.
- **Trusting SBFL scores blindly.** A suspiciousness score of 1.0 does not guarantee that the element is faulty. It means the element is statistically correlated with failure, which may be coincidental.
- **Running git bisect with a flaky test.** If the test intermittently passes on the bad commit, bisect will produce incorrect results. Verify that the test reliably fails on the known-bad commit before starting.
- **Over-relying on a single technique.** No single localization method works for every bug type. Use stack trace analysis, log correlation, SBFL, and bisection as complementary tools, not alternatives.
- **Neglecting to check environment differences.** A bug that manifests in CI but not locally may be caused by environment differences (timezone, locale, file system permissions) rather than code logic errors. Always compare environments before deep-diving into code.
- **Failing to reproduce before localizing.** Attempting to localize a bug you cannot consistently reproduce leads to speculation. Establish a reliable reproduction first, then apply localization techniques.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I can find the bug faster by reading the code than by following a systematic process" | Intuition-based debugging that skips stack trace analysis and log correlation is effective only for familiar code; for unfamiliar or complex code, it routinely fixes the symptom at the wrong layer and leaves the root cause intact. |
| "The stack trace shows line 42 is the problem, so I'll fix line 42" | Stack traces show where the exception was raised, not where the incorrect value originated; the null pointer at line 42 was introduced at line 8 where the object was constructed with a missing required field. |
| "git bisect takes too long for simple regressions" | `git bisect` with an automated test script bisects a 1,000-commit history in 10 iterations (log2(1000)); manual inspection of the same history can take hours and introduces confirmation bias. |
| "SBFL scores are too academic for practical debugging" | Tarantula suspiciousness scoring requires only a passing test suite and a failing test; it has been shown to localize the fault to the top-5 candidates in 70% of real-world bugs, making it faster than random code reading. |
| "Environment differences can't cause code logic bugs" | Timezone, locale, and filesystem permission differences have caused real-world production bugs that appeared only in CI or only in specific regions; eliminating environmental hypotheses first prevents hours of misguided code investigation. |

## Verification

- [ ] Bug is reproducible with a deterministic reproduction script or test case before any localization begins
- [ ] Stack trace analyzed from the correct end (bottom for Python, top for Java/JavaScript) and the true fault origin identified
- [ ] At least two localization techniques applied (e.g., stack trace + log correlation, or SBFL + bisect) and results cross-checked
- [ ] Fault location documented with exact file, line, and root cause explanation (not just symptom description)
- [ ] Reproduction test added or identified that fails at the fault location and passes after the fix

## Related Skills

- [[bug-reproduction-test-generator]] -- builds the deterministic reproduction this skill requires before localizing
- [[bug-to-patch-generator]] -- consumes the localized fault location to generate a targeted fix
- [[regression-root-cause-analyzer]] -- takes over when bisect points to a regression-introducing commit
- [[git-bisect-assistant]] -- automates the bisection technique in Step 5
- [[debug-with-logs]] -- adds strategic logging to support the log-correlation technique in Step 3
