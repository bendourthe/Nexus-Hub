# Decision: Frozen v4.15 native compatibility

Status: implemented - Exact compatibility and captured permission actions preserve the existing signed v4.15 run; final qualification, delivery and genuine live activation have separate gates.

## Problem

The approved v4.15 run freezes five plan hashes, task targets, worker claims, publication starts and aggregate limits. Some historical targets name an earlier version tree, while several verification tasks legitimately leave their target unchanged. Required manifest and handbook artifacts also need exact coordinator permissions that ordinary publication start cannot append after a member has started. The v4.15.4 profile read reservation otherwise conflicts with an earlier member's profile work.

Changing plan text, rewriting claims or manufacturing old-path files would replace the approved meaning instead of verifying the intended work. The repair must retain the existing native capture, signing, lease, archive and ordered publication boundaries.

## Decision

Use the existing helpers with a repository/minor/member/hash/task/target descriptor for exactly 36 reviewed task aliases. Only verified full-parent authority enables aliases; ordinary projections carry no authority. Genuine task work remains mandatory, and archive-only changes cannot satisfy implementation tasks.

Use a fixed `qualify-task` producer for the four reviewed unchanged-target cases. It executes the prescribed repository gates in a complete committed snapshot and seals source, semantic comparison, reports and producer identity outside the repository. A sealed incomplete latest receipt precedes snapshot and gate execution. Current-source reads reject hidden Git index flags and stale or malformed proof. Historical reuse requires independently verified publication and archive provenance. The comparison's structure and references are checked mechanically; the coordinator still owns the actual semantic review.

Use separate captured `permit-outputs` and `correct-ci-read` actions. The former grants only displayed literal manifest and handbook artifacts after checking the original scope. It preserves an existing ordered coordinator prefix or remains dormant until ordinary member start. The latter affects only v4.15.4's exact `scripts/ci/profiles.py` reservation at the compiled checkpoint, preserves its raw implementation claims and restores all original reads at ordered publication start. The later integrated candidate must satisfy final CI verification.

Windows gates receive atomic job membership at process creation, noninherited job ownership, an explicit inherited handle list and kill-on-close cleanup. POSIX gates retain an unreaped leader until owned process-group cleanup; abrupt supervisor death on POSIX has no equivalent containment claim. These mechanisms use the standard library and introduce no dependency or generic authorization framework.

## Alternatives considered

| Option | Benefit | Cost and decision |
|---|---|---|
| Rewrite or refreeze the plans and original claims | Ordinary predicates could read corrected targets directly | Changes frozen approved identity and original grants; rejected |
| Add dummy historical paths or accept unsigned success reports | Small local implementation | Does not establish genuine task work or trustworthy current gate execution; rejected |
| Add a generic alias, command or permission framework | Reusable for later releases | Broadens the trust boundary beyond the reviewed tuples and artifact classes; rejected |
| Keep the existing helpers unchanged | Avoids maintenance and new qualification | Leaves the approved run unable to represent truthful completion and required exact outputs; rejected |
| Add bounded compatibility to existing native owners | Preserves original authority while enabling exact reviewed cases | Adds version-specific maintenance and full qualification obligations; selected |

## Consequences

The original signed run, claims, starts, release order and limits remain intact. New live permissions still require genuine native captured decisions after qualified helper delivery. Implementing the helpers, rendering a page or using disposable test captures grants no live authority.

The bounded descriptor and detached receipts add maintenance cost. Final repository validation, actual installer and target-OS evidence, the actual gate producer exercise, independent review, protected integration and exact helper delivery remain necessary. The package does not publish the unmerged v4.15.4 feature implementation or establish minor completion.

The existing [completion contract](../../../../catalog/skills/workflow/implement-phase/references/completion-contract.md) owns the operational protocol. The release-scoped [qualification record](../../../releases/v4/v4.15/development/v4.15-native-compatibility-qualification.md) owns actual results and unresolved gates.
