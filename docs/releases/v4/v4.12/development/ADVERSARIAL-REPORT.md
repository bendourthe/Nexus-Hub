# Adversarial verification status

Independent review status for the v4.12 attribution change, covering the checker, maintainer hook, rewrite proof and CI wiring. This is a partial record, not a clean security verdict.

**Date**: 2026-09-14. **Candidate**: `e56d0251407ec84f59d9425cf6a64dc15c3a112e`. **Reviewer**: separate GPT-5.6 reviewer. **Recorder**: implementing agent, preserving the reviewer's returned finding after its turn failed.

## Attack surface

The assigned surfaces were raw commit author/committer metadata, attribution-message fields, pending Git identities, local-hook execution, all-ref history traversal, rewrite/ref publication and the CI checkout boundary. The reviewer inspected the local 139-ref proof and the remote ref inventory. Completion of its other planned exercises is not established.

## Confirmed finding

**AF-1: Public all-ref claim exceeds writable GitHub scope.** The reviewer reported that both local mirrors contain the same 139 local refs but no GitHub pull-request refs. The remote advertises 212 read-only `refs/pull/*` in addition to 119 writable heads/tags. Force-push cannot rewrite the read-only namespace. Independently reproduced by the implementing agent's `git ls-remote --refs` inventory and verified against [GitHub's documented contract](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/checking-out-pull-requests-locally).

**Disposition**: QG-1 in the current [ledger](../known-gaps.md). Keep the local all-ref proof, but never describe a clean normal-clone result as a purge of every ref GitHub retains. The contributor-page outcome still requires direct post-publication observation. No remote mutation occurred.

## Incomplete review

The reviewer's next turn failed with `This content was flagged for possible cybersecurity risk`. The remaining independent review did not return a final report or coverage record. It was not retried through a different reviewer or treated as passed. QG-3 names the missing coverage and owner.

Final-suite stabilization later changed the existing target-manifest directory-membership guard. Its regression tests and full-profile results are functional evidence; that later correction is also outside the incomplete independent review's established coverage.

## Considered but rejected

No completed route-level refutation was returned. No rejection is invented from the implementer's existing test results. Ordinary checker and native Git/installer tests remain separate functional evidence in [last-phase evidence](last-phase-evidence.md).

## Overall assessment

**Verdict: INCOMPLETE.** One independently reported operational-scope finding; remaining hostile-input coverage unverified. Local implementation tests do not substitute for the unavailable independent review.
