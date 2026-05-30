/**
 * condition-based-waiting-example.ts
 *
 * A copy-in polling helper that replaces `sleep`-based flakiness with
 * condition-based waiting. This is an EXAMPLE to copy into your test suite, not
 * a published package: it has zero runtime dependencies and uses only the
 * standard `setTimeout`, so it drops into any Node or browser test runner.
 *
 * WHY this exists
 * ---------------
 * A `setTimeout(resolve, 1000)` encodes a guess: "the async work finishes
 * within one second." That guess is wrong in both directions. On a loaded CI
 * runner one second is not enough and the test fails intermittently; on a fast
 * developer machine the work finishes in 50ms and the test wastes 950ms on
 * every run. Condition-based waiting removes the guess: poll for the actual
 * state change and proceed the instant it holds, failing only if a generous
 * outer deadline elapses.
 *
 * The outer `timeoutMs` is NOT the same kind of number as the sleep it
 * replaces. The sleep is an assertion about how long the work takes (and is
 * therefore wrong on slow machines). The deadline is only a failure bound: on
 * success the helper returns immediately, so making the deadline generous costs
 * nothing on the happy path while absorbing runner-speed variance.
 *
 * See `../references/condition-based-waiting.md` for the full pattern, the
 * quick-patterns table, and the narrow cases where a fixed delay IS correct.
 */

/**
 * Poll `probe` on an interval until it returns a "ready" value, then return that
 * value. A value is "ready" when it is not `null`, `undefined`, or `false`, so a
 * probe can return either a boolean (condition met) or the awaited payload
 * itself (e.g. the row that finally appeared).
 *
 * Design rules baked in (each one is a flakiness footgun avoided):
 *  - There is always an outer deadline. A poll with no deadline turns a clear
 *    test failure into a CI hang with no useful message.
 *  - The interval is small but non-zero. A zero-interval busy loop pegs a CPU
 *    and can starve the very work being waited for.
 *  - Probe exceptions are swallowed during polling (a not-yet-ready resource
 *    often throws) and surfaced only in the timeout message. Assert AFTER
 *    `waitFor` returns, never inside the probe.
 *
 * @param probe        Returns the value to test, or a promise of it. Return the
 *                     payload when ready, or a falsy value to keep waiting.
 * @param description  Human-readable name of what is being awaited; appears in
 *                     the timeout error so failures are self-explaining.
 * @param timeoutMs    Failure deadline. Set it to several times the worst-case
 *                     expected duration - on success it costs nothing.
 * @param intervalMs   Delay between poll attempts. Bounds CPU use; 25ms is a
 *                     sensible default for most test workloads.
 */
export async function waitFor<T>(
  probe: () => T | Promise<T>,
  description: string,
  timeoutMs = 5_000,
  intervalMs = 25,
): Promise<NonNullable<T>> {
  const deadline = Date.now() + timeoutMs;
  let lastError: unknown;

  while (Date.now() < deadline) {
    try {
      const value = await probe();
      if (value !== null && value !== undefined && (value as unknown) !== false) {
        return value as NonNullable<T>;
      }
    } catch (error) {
      // A resource that is not ready yet often throws (connection refused, row
      // not found). Remember the last error for the timeout message; do not let
      // it fail the test on the first attempt.
      lastError = error;
    }
    await delay(intervalMs);
  }

  const suffix = lastError === undefined ? "" : ` Last probe error: ${String(lastError)}`;
  throw new Error(`Timed out after ${timeoutMs}ms waiting for ${description}.${suffix}`);
}

/**
 * Wait until a named event fires on an EventEmitter-like object and return the
 * arguments it was emitted with. Replaces `sleep` then "assert the handler ran".
 *
 * The listener is registered with `once`, so it self-removes after the first
 * emission. The captured arguments become the "ready" value the poll waits for.
 */
export function waitForEvent(
  emitter: { once(eventName: string, listener: (...args: unknown[]) => void): void },
  eventName: string,
  timeoutMs = 5_000,
): Promise<readonly unknown[]> {
  let fired: readonly unknown[] | null = null;
  emitter.once(eventName, (...args: unknown[]) => {
    fired = args;
  });
  return waitFor(() => fired, `event "${eventName}" to fire`, timeoutMs);
}

/**
 * Wait until a collection reaches (or exceeds) `expected` items and return the
 * collection. Replaces `sleep` then "assert the count once" - which fails when
 * the last item lands a few milliseconds after the guessed delay.
 */
export function waitForCount<T>(
  read: () => readonly T[] | Promise<readonly T[]>,
  expected: number,
  timeoutMs = 5_000,
): Promise<readonly T[]> {
  return waitFor(
    async () => {
      const items = await read();
      return items.length >= expected ? items : null;
    },
    `collection to reach ${expected} item(s)`,
    timeoutMs,
  );
}

/**
 * Wait until `read` reports the target state and return it. Replaces a `sleep`
 * sized to the "expected transition time" with a poll on the actual state field.
 */
export function waitForState<S>(
  read: () => S | Promise<S>,
  target: S,
  timeoutMs = 5_000,
): Promise<NonNullable<S>> {
  return waitFor(
    async () => {
      const current = await read();
      return current === target ? current : null;
    },
    `state to become ${String(target)}`,
    timeoutMs,
  );
}

/** Resolve after `ms` milliseconds. Used only to throttle the poll loop. */
function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/*
 * Usage example (the flaky-then-stable contrast from the reference):
 *
 *   // FLAKY - guesses that 1000ms is "enough" for the async write
 *   await triggerNotification("user@example.com");
 *   await new Promise((r) => setTimeout(r, 1000));
 *   expect(await db.notifications.findByEmail("user@example.com")).toBeDefined();
 *
 *   // STABLE - proceeds the instant the row exists, fails only if it never does
 *   await triggerNotification("user@example.com");
 *   const row = await waitFor(
 *     () => db.notifications.findByEmail("user@example.com"),
 *     "notification row to be persisted",
 *     5_000,
 *   );
 *   expect(row).toBeDefined();
 */
