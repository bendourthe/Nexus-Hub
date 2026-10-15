# Condition-Based Waiting

The single most common cause of timing-dependent flakiness is waiting for a fixed duration instead of waiting for the condition you actually care about. This reference documents the pattern that replaces guessed delays with explicit condition polling, when a fixed timeout is nonetheless the correct choice, and the mistakes to avoid.

## The Core Principle

Wait for the condition, not for the clock.

A `sleep(2)` encodes a guess: "the async work will be done within two seconds." That guess is wrong in both directions. On a loaded CI runner, two seconds is not enough and the test fails intermittently. On a fast developer machine, the work finishes in 50ms and the test wastes 1950ms on every run. Multiply that waste across a suite of hundreds of tests and the fixed-delay tax dominates the run time while still being flaky.

Condition-based waiting removes the guess. Instead of sleeping for a duration, poll for the actual state change (the event fired, the row appeared, the counter reached N, the file exists) and proceed the instant it is true, failing only if a generous outer timeout elapses. The test becomes both faster (it proceeds as soon as the condition holds) and more reliable (the outer timeout absorbs runner-speed variance instead of encoding a specific machine's timing).

## Before / After

The flaky version guesses a duration:

```javascript
// FLAKY - guesses that 1000ms is "enough" for the async write
test("notification is persisted", async () => {
  await triggerNotification("user@example.com");
  await new Promise((r) => setTimeout(r, 1000)); // guess
  const row = await db.notifications.findByEmail("user@example.com");
  expect(row).toBeDefined(); // fails when the write took 1100ms
});
```

The stable version waits for the condition:

```javascript
// STABLE - proceeds the instant the row exists, fails only if it never appears
test("notification is persisted", async () => {
  await triggerNotification("user@example.com");
  const row = await waitFor(
    () => db.notifications.findByEmail("user@example.com"),
    "notification row to be persisted",
    5000 // generous outer bound, not a guess at the actual latency
  );
  expect(row).toBeDefined();
});
```

The outer bound in the stable version is not the same kind of number as the `setTimeout` in the flaky one. The flaky `1000` is an assertion about how long the work takes (and is therefore wrong on slow machines). The stable `5000` is only a failure deadline: the test never waits the full 5000ms on success, so making it generous costs nothing on the happy path while absorbing CI variance.

A reusable `waitFor` helper plus domain-specific helpers (`waitForEvent`, `waitForCount`) is bundled with this skill - see the bundled helper under `assets/` (`condition-based-waiting-example.ts`). Copy it into your test suite rather than reimplementing the polling loop in each test.

## Quick Patterns

| You want to wait for... | Poll for... | Anti-pattern it replaces |
|---|---|---|
| An event to fire | a flag/promise the handler sets, resolved by the listener | `sleep` then assert the side effect happened |
| A state transition | the object's state field equaling the target value | `sleep` proportional to the expected transition time |
| A count to be reached | `items.length === N` (or `>= N`) | `sleep` then assert the count once |
| A file to be written | the file existing and being non-empty / fully flushed | `sleep` then read the file |
| A complex/compound condition | a predicate returning true when all sub-conditions hold | a chain of `sleep`s between sub-steps |
| A row to appear in a store | a query returning the row | `sleep` then a single query |

Every row replaces a fixed delay with a predicate that the helper evaluates on an interval until it holds or the outer deadline passes.

## When an Arbitrary Timeout IS Correct

Condition-based waiting is the default, not an absolute. A fixed delay is the right tool in a narrow set of cases, and these are legitimate precisely because the duration is the thing under test:

- **Timing-behavior tests**: you are asserting that something does NOT happen before a deadline (a debounce does not fire before 300ms, a rate limiter rejects a second call within the window, a cache entry is still valid at T+59s and expired at T+61s). Here the duration is the specification, so prefer injected fake timers (`jest.useFakeTimers()`, an injected `Clock`) over real sleeps; a real sleep in a timing test is still flaky under load.
- **Deliberate throttling of a polling loop**: a small `sleep` between poll attempts inside the `waitFor` helper itself is correct - it bounds CPU use. That is the interval, not the wait.
- **Documented external constraint**: a third-party sandbox that only accepts one request per second. Even then, document why the literal number exists.

The rule of thumb: if the number answers "how long does the work take?" it is a guess and belongs in a condition poll. If the number answers "what duration am I asserting about?" it is part of the test and belongs there - ideally driven by a fake clock, not wall time.

## Common Mistakes

- **Polling without an outer timeout**: a `waitFor` with no deadline hangs forever when the condition never becomes true, turning a clear test failure into a CI timeout with no useful message. Always pass a deadline and a description so the failure says what was being waited for.
- **A timeout that is too tight**: setting the outer bound to the expected latency reintroduces the original flakiness. The deadline should be several times the worst-case expected duration, because on success it costs nothing.
- **Polling too aggressively**: a zero-interval busy loop pegs a CPU and can starve the very work you are waiting for. Use a small interval (e.g. 10-50ms) between attempts.
- **Asserting inside the poll predicate**: the predicate should return a boolean (or the awaited value), not call `expect`. An assertion that throws inside the loop turns a not-yet-true condition into a hard failure on the first attempt. Assert after `waitFor` returns.
- **Waiting on a proxy instead of the real condition**: sleeping until "the spinner disappears" when what you care about is "the data loaded" couples the test to an incidental UI detail. Poll for the condition that actually matters.
- **Keeping the sleep "just in case" alongside the poll**: a `waitFor` followed by a `sleep(500)` defeats the purpose and re-adds the tax. If the condition holds, proceed immediately.

## Related

- The flaky-test taxonomy in `flaky-test-detector/SKILL.md` (timing dependencies are category 1).
- The bundled `waitFor` helper under `assets/condition-based-waiting-example.ts`.
- `find-polluter` (bundled under `scripts/`) for the complementary problem of state pollution across test files.
