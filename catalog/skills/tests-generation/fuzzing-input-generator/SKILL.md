---
name: fuzzing-input-generator
description: Generate fuzz testing inputs for security and robustness testing using mutation-based, grammar-based, and coverage-guided fuzzing techniques. Use when testing parsers, APIs, file format handlers, network protocols, or when you need to discover crashes, hangs, and undefined behaviour through automated input generation.
summary_l0: "Generate fuzz testing inputs with mutation, grammar, and coverage-guided techniques"
overview_l1: "This skill generates fuzz testing inputs for security and robustness testing using mutation-based, grammar-based, and coverage-guided fuzzing techniques. Use it when testing parsers, APIs, file format handlers, network protocols, or when discovering crashes, hangs, and undefined behaviour through automated input generation. Key capabilities include mutation-based fuzzing (bit flipping, byte insertion, dictionary-based), grammar-based fuzzing with format-aware input generation, coverage-guided fuzzing with corpus management, crash triage and deduplication, harness design for target functions, seed corpus creation, and tool configuration (AFL++, libFuzzer, go-fuzz, Jazzer). The expected output is fuzzing harnesses, seed corpora, and crash reports with reproduction inputs. Trigger phrases: fuzzing, fuzz testing, fuzz inputs, AFL, libFuzzer, crash discovery, parser testing, protocol fuzzing, grammar fuzzing, coverage-guided fuzzing."
---

# Fuzzing Input Generator

Generate fuzz testing inputs that discover crashes, security vulnerabilities, memory corruption, hangs, and undefined behaviour by feeding malformed, unexpected, or random data to a target program. This skill covers mutation-based fuzzing, grammar-based fuzzing, coverage-guided fuzzing, and API fuzzing with practical implementations across multiple languages.

## When to Use This Skill

Use this skill when you need to:

- Test parsers, deserializers, and file format handlers against malformed input
- Discover security vulnerabilities (buffer overflows, injection, denial of service)
- Fuzz REST/GraphQL API endpoints with invalid, oversized, or malicious payloads
- Test network protocol implementations against protocol violations
- Generate corpus files for coverage-guided fuzzers (AFL, libFuzzer, Jazzer)
- Build grammar-based fuzzers that produce structurally valid but semantically twisted inputs
- Stress-test input validation and error handling paths
- Verify that a program never crashes, regardless of input

**Trigger phrases**: "fuzz test", "fuzzing", "fuzz inputs", "mutation testing inputs", "crash test", "security fuzzing", "API fuzzing", "grammar fuzzing", "coverage-guided fuzzing", "input corpus", "malformed input", "adversarial inputs"

## What This Skill Does

### Fuzzing Approaches

#### Mutation-Based Fuzzing

Start with a valid input (the seed) and apply random mutations: bit flips, byte insertions, deletions, duplications, and value substitutions. This is the simplest approach and works well when you have a corpus of valid inputs.

**Mutation operators:**
- Bit flip (single bit, adjacent bits, byte-aligned bits)
- Byte replacement (random byte, interesting values like 0x00, 0xFF, 0x7F)
- Block insertion (random bytes, copies of existing blocks)
- Block deletion (remove random byte ranges)
- Arithmetic (add/subtract small values from integers in the input)
- Dictionary substitution (replace tokens with known-interesting values)

#### Grammar-Based Fuzzing

Define the input grammar (JSON, XML, SQL, HTTP) and generate inputs that are syntactically valid but probe semantic edge cases. This is more targeted than mutation-based fuzzing and avoids wasting time on inputs that are rejected at the parser level.

#### Coverage-Guided Fuzzing

Use code coverage feedback to guide input generation toward unexplored code paths. When a mutation increases coverage, the mutated input is added to the corpus. Tools like AFL++, libFuzzer, and Jazzer implement this automatically.

#### API Fuzzing

Send malformed HTTP requests to API endpoints, testing header manipulation, body corruption, parameter injection, oversized payloads, and content-type mismatches.

### Fuzzing Pipeline

1. **Seed corpus creation**: Gather valid sample inputs that exercise basic functionality
2. **Mutation/generation**: Apply mutations or generate from grammars to create test inputs
3. **Execution**: Feed each input to the target and monitor for crashes, hangs, and unexpected behaviour
4. **Coverage tracking**: Record which code paths each input exercises
5. **Corpus management**: Retain inputs that increase coverage; discard redundant ones
6. **Crash triage**: Deduplicate crashes, identify root causes, create reproducible test cases

## Instructions

### Step 1: Build a Mutation-Based Fuzzer

Full walkthrough: [step-1-build-a-mutation-based-fuzzer.md](references/step-1-build-a-mutation-based-fuzzer.md) (load this step when you reach it).

### Step 2: Build a Grammar-Based Fuzzer

Full walkthrough: [step-2-build-a-grammar-based-fuzzer.md](references/step-2-build-a-grammar-based-fuzzer.md) (load this step when you reach it).

### Step 3: Set Up Coverage-Guided Fuzzing

Full walkthrough: [step-3-set-up-coverage-guided-fuzzing.md](references/step-3-set-up-coverage-guided-fuzzing.md) (load this step when you reach it).

### Step 4: Implement API Fuzzing

Full walkthrough: [step-4-implement-api-fuzzing.md](references/step-4-implement-api-fuzzing.md) (load this step when you reach it).

### Step 5: Manage the Input Corpus

Full walkthrough: [step-5-manage-the-input-corpus.md](references/step-5-manage-the-input-corpus.md) (load this step when you reach it).

## Best Practices

- **Start with a good seed corpus**: The quality of mutation-based fuzzing depends on the initial seeds; include valid inputs that exercise different code paths, file format features, and API operations
- **Use coverage-guided fuzzing for native code**: For C, C++, Rust, and Go targets, coverage-guided fuzzers (AFL++, libFuzzer) are dramatically more effective than blind mutation
- **Use grammar-based fuzzing for structured inputs**: Mutation of random bytes rarely produces valid SQL, JSON, or XML; grammar-based generation spends more time on semantically interesting inputs
- **Run fuzzers continuously**: Fuzzing finds more bugs with more time; run fuzzers in CI as long-running jobs (hours or days), not just as quick smoke tests
- **Triage crashes by unique stack trace**: Many crash inputs trigger the same bug; deduplicate by hashing the crash stack trace to focus on unique root causes
- **Save every crash-triggering input**: Store crash inputs in a permanent corpus so they can be used as regression tests after fixes
- **Set resource limits**: Fuzz targets should have memory limits (to catch memory exhaustion) and time limits (to catch infinite loops and hangs)
- **Separate expected errors from crashes**: A JSON parser throwing `JSONDecodeError` on malformed input is correct behaviour; a segfault or unhandled exception is a bug

## Common Pitfalls

- **Fuzzing without any seeds**: Starting from empty or random bytes wastes time; even a single valid input as a seed dramatically improves mutation-based fuzzing effectiveness
- **Ignoring timeout findings**: A fuzz input that causes the target to hang for 30 seconds is as much a bug as a crash; these often indicate algorithmic complexity attacks (ReDoS, hash collision DoS)
- **Not running long enough**: Many bugs are only found after millions of iterations; running a fuzzer for 60 seconds and declaring the code safe is misleading
- **Suppressing all exceptions**: Catching `Exception` in the fuzz target and ignoring it hides real bugs; only suppress expected error types (e.g., `JSONDecodeError`) and let unexpected exceptions propagate
- **Not minimizing crash inputs**: A 10KB crash input is hard to debug; use the fuzzer's minimization feature (e.g., `afl-tmin`) to reduce it to the smallest input that still triggers the crash
- **Fuzzing only in development**: Fuzzing should be part of CI, not just a one-time developer activity; new code introduces new bugs that fuzzing can find
- **Not testing error paths**: Fuzzing primarily exercises error handling paths; if your code lacks proper error handling, fuzzing will reveal this as crashes rather than graceful failures
- **Using production URLs for API fuzzing**: Always fuzz against local or staging environments; never send fuzz traffic to production

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Our input validation already rejects bad data, so fuzzing is redundant." | Fuzzing exercises the error-handling paths your unit tests never reach; a parser that handles every malformed case you imagined still segfaults on the byte sequence you did not, which is exactly what the fuzzer finds. |
| "Running the fuzzer for a minute showed no crashes, so the code is safe." | Coverage-guided fuzzers find deep bugs only after millions of iterations; a 60-second run barely warms the corpus and a clean result is meaningless. |
| "I will start the fuzzer from random bytes; a seed corpus is extra work." | Blind random bytes almost never form valid JSON or a valid file header, so the fuzzer wastes its budget being rejected at the front gate; one good seed multiplies effectiveness. |
| "A hang is not a crash, so I can ignore the timeout findings." | A 30-second hang on a crafted input is an algorithmic-complexity denial-of-service (ReDoS, hash-collision DoS); ignoring it ships a remotely triggerable outage. |

## Verification

- [ ] The fuzz harness builds and runs against the target without setup errors.
- [ ] A non-empty seed corpus of valid inputs exists before mutation-based fuzzing starts.
- [ ] Crash-triggering inputs are saved to a permanent corpus and minimized to the smallest reproducer.
- [ ] The harness suppresses only expected error types and lets unexpected exceptions propagate as findings.
- [ ] Fuzzing runs in CI as a long-running job with explicit memory and time limits, not a one-time smoke test.

## Related Skills

- [[edge-case-generator]] -- enumerates curated boundary inputs alongside the random inputs this skill mutates
- [[directed-test-input-generator]] -- reaches specific branches where broad fuzzing is too undirected
- [[security-review]] -- triages the vulnerabilities fuzzing surfaces (overflows, injection, DoS)
- [[bug-reproduction-test-generator]] -- turns a minimized crash input into a permanent regression test
- [[property-based-test-generator]] -- shares the generative testing mindset with explicit invariants as oracles
