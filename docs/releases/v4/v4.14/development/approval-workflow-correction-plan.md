# Approval workflow correction

User-requested v4.14 correction, approved in the current conversation on 2026-10-19 UTC. This sidecar adds implementation work without rewriting the seven frozen member plans or their approval records.

## Goal

After one genuine plan approval, full-access sessions continue within that scope without repeated permission prompts. Manual sessions receive a concise explanation and an Approve or Decline choice through available host question tools, with an honest short-reply fallback where native capture is unavailable. Repeated observations reuse the same blocker and decision.

## Ownership

The correction uses branch `fix/v4.14-approval-flow` in a separate sibling worktree, based on integrated commit `3415ddb697d2edb03e0d1c9c4ddadfe86c708bc2`. It does not change the release candidate already under PR487. The coordinator owns commands, contracts, tracker, manifest, integration and release; the native implementation worker owns approval scripts and their regression tests. Other sessions and the primary checkout remain untouched.

## Implementation

- [x] A001 Retain a trusted host permission signal alongside genuine initial approval, with signed scope and automatic-continuation provenance. Unknown modes remain explicit.
- [x] A002 Reuse matching pending challenges and deduplicate identical open blocker conditions for both plan and minor runs. Changed conditions invalidate stale answers.
- [x] A003 Provide concise manual decision data and genuinely captured short replies; reject replay, ambiguous, stale and cross-session answers. Do not invent host callbacks or user approvals.
- [x] A004 Align /plan, /implement, /update, retained skills and the completion contract with the same authorization policy.
- [ ] A005 Exercise temporary-home native plan and minor flows, rerun affected regression and static checks after implementation, independently review the final diff, then publish and merge through develop.
- [ ] A006 Include the correction in the remaining v4.14 release sequence, adopt only a verified complete published runtime, and resume the original minor goal.

## Verification

Focused checks run during implementation; comprehensive affected approval, completion, hook and runner regressions run once on the completed correction before its single publication. Actual native flow evidence must show one initial approval, automatic in-scope continuation in trusted full access, one manual choice, unchanged repeated prompt identity and refusal of stale or reused responses. A failed test, unknown remote, tampered record or user-edit conflict cannot be declared resolved merely by automatic authorization. Spend caps and explicit exclusions remain in force.

## Limits

No host permission mode is changed. No fabricated prompt capture, signature, approval text or callback is accepted. A platform without a verified clickable receipt path is reported honestly and uses a genuine short user reply instead of an opaque copy/paste code. This work does not make green tests, merged integration, release, cleanup or minor completion optional.

Local verification and current-run adoption: [evidence](approval-workflow-correction-evidence.md). Integration and release remain open.
