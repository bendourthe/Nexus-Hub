# Legacy Planned Deferral Closeout

## Status

Accepted for an isolated local compatibility repair under the captured Nexus-AI v2.16 blocker 4 decision. Publication of Nexus-Hub is outside that authority. Verification and installation status are recorded in the [evidence](../../../releases/v4/v4.14/development/v2.16-closeout-compatibility-evidence.md).

## Context

A signed plan can deliberately record a trial requiring unavailable hardware while declining all model admissions. The older recording task and its published ledger body predate the canonical planned-follow-on template. Rewriting that body would destroy the preserved source evidence. Repeated full-ledger reads also exhausted the consumer member check while verifying hundreds of otherwise valid migrations.

## Alternatives considered

- Keep the newer-template-only rule: preserves strictness but cannot recognize the owner's exact older recording task.
- Rewrite the original entry to the newer template: rejected because it changes the immutable source body instead of proving the existing one.
- Increase time limits or ignore historical ledgers: rejected because neither is proof of successful closeout.
- Trust a title or current working copy: rejected because an unrelated new defect or altered body could borrow authority.
- Require frozen task identity, explicit migration binding and unchanged verified publication evidence: selected; deterministic parsing work can be reused within the same check.

## Decision

Extend the existing checker and minor-close helpers. Accept the older recording-only grammar only after reliable baseline absence and exact unique title, member, task, ledger and publication proof. Preserve original bodies, ordinary inherited migration rules, signed decline capture, native archive repair, OPEN copies and user-deferred provenance.

Cache only successful immutable-commit ledger parses and proved absence in the current repository context. Failed history remains unknown and retryable. Cache pure visibility parsing by exact text input as immutable tuples. A member's gap check reuses one local ledger snapshot, then rereads it before accepting results. Live approval, destination, publication and network results are not cached. Member20-second and minor 120-second limits remain unchanged.

## Maintainer Identity

The separately captured blocker 5 decision admits exactly Benjamin Dourthe <benjamin.dourthe@gmail.com> alongside the historical Ben Dourthe <50595044+bendourthe@users.noreply.github.com> pair in the local attribution validator. Its shared identity check covers authors, committers and identity-bearing message fields. GitHub remains a committer-only exception; unknown identities, agent attribution and mixed name/email pairs remain rejected.

Changing Git configuration to impersonate the historical pair and rewriting existing commits were rejected. Adding only the current verified pair preserves the user's actual identity and the closed allowlist. The exact reviewed patch and six additional regression cases passed all 65 attribution tests on the actual source. No hook, history, publication permission or installed runtime path changes are included.

## Consequences

This can qualify a predeclared opportunity without claiming the missing trial ran. The signed run and frozen migration bounds are unchanged. Unknown historical obligations still block full completion. No blanket archive exemption, generated closure, fabricated identifier, release or expanded cleanup authority is introduced.

The earlier v2.15 ledger conversion deliberately retained 142 legacy diagnostics across five archived ledgers. Some apparent rows are prose, some closures have narrower committed evidence, and some obligations remain unproved. The repair does not convert those diagnostics into invented obligations or silently pass them.

## Verification

The repair plan requires real local Git publication tests, negative proof boundaries, native signed capture/migration/archive/refreeze coverage, independent review, the affected compatibility matrix and native fast checks. Actual consumer measurements remain separate from hermetic tests. A quiet-host member check and truthful remaining blockers are required before claiming consumer qualification.
