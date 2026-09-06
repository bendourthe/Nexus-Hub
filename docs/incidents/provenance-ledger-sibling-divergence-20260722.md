# Incident: the provenance-ledger PowerShell sibling parsed, ran, and disagreed with its Bash counterpart

**Date**: 2026-07-22 (v3.15.6)
**Audience**: Nexus-Hub maintainers touching `catalog/hooks/` or either installer / owning skill: [[incident-postmortem]]

## Summary

`catalog/hooks/provenance-ledger.ps1` shipped alongside `provenance-ledger.sh` and, unlike the earlier `session-summary.ps1` case, it parsed and ran. It simply produced different output from its sibling for the same input, in two independent ways:

1. **A byte-order mark.** `Add-Content -Encoding utf8` emits a UTF-8 BOM on Windows PowerShell 5.1, so the ledger the PowerShell path wrote was not byte-identical to the one the Bash path wrote. Downstream readers of an append-only ledger do not expect a BOM to appear mid-file.
2. **Filename escaping.** `sha256sum` escapes filenames containing backslashes, which is the ordinary case on Windows. The two implementations therefore recorded the same file under different names.

Neither was reachable by the test suite as it stood, because the suite exercised the POSIX implementation only. The PowerShell half was present, executable, and wrong.

## Public-Safe Shape

This is shape [S-1: An unverified cross-platform sibling is silently non-functional](shapes.md#s-1-an-unverified-cross-platform-sibling-is-silently-non-functional), failure mode 2 (it runs but disagrees).

Two lessons this instance contributes to the shape:

**A "reasonable-looking equivalent" is where the divergence hides.** Both defects came from choosing the API whose name most resembled the Bash behavior rather than the one whose output matched it. `-Encoding utf8` reads like "write UTF-8"; on 5.1 it means "write UTF-8 with a BOM". The safer instinct is to pick the native API that gives explicit control over the observable (`[System.IO.File]::WriteAllText` with `UTF8Encoding($false)`) rather than the one whose name matches the intent.

**Version is part of the platform.** The BOM behavior is specific to Windows PowerShell 5.1. A CI leg running only a newer PowerShell would have passed while every 5.1 user got a different file. Testing "on Windows" is not the same as testing on the interpreter version users actually have.

## Durable fix

| Fix | Link |
|---|---|
| Exit-code and behavior parity asserted mechanically: hook tests use a `run` fixture parametrized over both implementations, so every behavioral assertion doubles as a parity assertion rather than parity needing its own suite someone must remember to extend | [`catalog/hooks/tests/test_provenance_ledger.py`](../../catalog/hooks/tests/test_provenance_ledger.py) |
| A Windows PowerShell 5.1 CI leg that runs the suite on the interpreter version where the divergence actually appeared | [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) (the `tests-windows` job) |
| The sibling-authoring guidance written into the canonical agent guidance: prefer the native equivalent over emulating shell mechanics, with the BOM and `[Console]::IsInputRedirected` cases named explicitly, plus the rule that a sibling may diverge only in the safe direction (warn or block MORE, never less) | [`AGENTS.md`](../../AGENTS.md) (Adding or Modifying a Hook) |

**What this would catch on a recurrence**: any behavioral or exit-code disagreement between a `.sh` and its `.ps1` for the same input, on the interpreter version where such disagreements arise, as a side effect of writing an ordinary behavioral test.

**What it still misses**: agreement is not correctness. The parametrized fixture proves the two implementations do the same thing; it cannot tell you that thing is right. It also only covers hooks that have tests at all - a sibling pair with no behavioral test gets the parse gate from the first incident and nothing more.
