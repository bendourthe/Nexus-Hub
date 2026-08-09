# Reusable incident shapes

A shape is the abstracted, public-safe pattern behind one or more incidents. It lives here rather than in a single note when more than one incident shares it, so the pattern is stated once and each note references it.

---

## S-1: An unverified cross-platform sibling is silently non-functional

**Referenced by**: [powershell-sibling-parse-error-20260709](powershell-sibling-parse-error-20260709.md), [provenance-ledger-sibling-divergence-20260722](provenance-ledger-sibling-divergence-20260722.md)

**The shape.** When a project ships the same capability twice for two platforms (a `.sh` and a `.ps1`, a POSIX and a Windows path, a Bash and a PowerShell installer), the second copy can be broken from the day it ships and stay broken indefinitely, because nothing in the test suite executes it. The file's existence is mistaken for its function.

Two distinct failure modes fall under it, and they need different controls:

1. **It never runs at all.** A syntax or parse error means the file is dead on arrival. A test suite that skips when no interpreter is present emits no signal, and a skip reads like a pass in a green run.
2. **It runs but disagrees.** The file parses and executes, and produces different behavior from its sibling for the same input, because a platform-native API differs in a way the author did not expect. This is the harder mode: the file looks alive.

**Why the usual controls miss it.** Both modes are invisible to a suite that exercises one platform. Conditional skips hide mode 1, and a test that only asserts the primary platform's behavior hides mode 2 by never comparing the two.

**The control that works.** Assert parity mechanically rather than inferring it from the file being present:

- An **unconditional syntax gate** that fails on a parse error even when no interpreter is available to run the file. This closes mode 1 and must not be skippable, because skippability is the defect.
- A **parametrized test fixture** that runs every behavioral assertion against BOTH implementations with the same input and compares observable output and exit code. This closes mode 2, and it works by making every behavioral test double as a parity test rather than requiring a separate parity suite that someone must remember to extend.
- A **CI leg on the second platform's real interpreter and version**, not an emulation. Version matters: a difference that only appears on an older shell version is invisible to a newer one.

**What it still misses.** Parity testing proves the two implementations agree with each other. It does not prove either is correct. Two siblings can agree on the wrong behavior, and no parity gate will say so.

**Generalization.** Nothing here is specific to PowerShell. The shape applies to any dual implementation kept in step by convention rather than by assertion: a client SDK in two languages, a validator with a fast path and a reference path, a migration written both forward and backward.
