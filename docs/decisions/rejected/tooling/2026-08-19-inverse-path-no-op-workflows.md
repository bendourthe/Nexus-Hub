# Decision: Emit required check names from inverse-path no-op workflows

Status: rejected - it makes every required check satisfiable without ever running it, so the gate reports green on exactly the changes it was configured to inspect

## Problem

A required status check whose workflow is path-filtered stays Pending forever on a change the filter excludes, which makes the protected branch unmergeable. `ci.yml` excluded `docs/**`, so nine of its ten required contexts never reported on a docs-only pull request; `doc-colocation.yml` included only `docs/**` and `catalog/skills/**`, so `colocation` never reported on a code-only one. Six pull requests merged on 2026-08-19 could not satisfy their own required set.

The path filters exist for a real reason: running the full matrix, including a 10x-billed macOS leg, on a documentation typo is waste worth avoiding.

## Proposal

Keep every existing path filter exactly as it is, and add a companion workflow for each one whose trigger uses the **inverse** path set. The companion declares jobs with the identical names as the real workflow, and each job's only step exits 0 immediately.

For `ci.yml`, whose triggers exclude `docs/**`, add `ci-docs-noop.yml` triggered on `paths: ['docs/**']` declaring `validate`, `shellcheck`, `bootstrap`, `tests`, `install-smoke`, and `installer-smoke` as no-op jobs. For `doc-colocation.yml`, add a companion triggered on everything except `docs/**` and `catalog/skills/**` declaring a no-op `colocation`.

Exactly one of each pair therefore triggers for any given change, so every required context always reports, and the expensive work still only runs when the real workflow's paths match. No existing filter changes, no job is renamed, and no branch-protection edit is needed.

## Alternatives considered

- **Move path scoping from the workflow trigger to a job-level `if:`.** This is the alternative that won. A skipped job reports Success while an untriggered workflow reports nothing, so the same scoping becomes safe once it moves inside a workflow that always starts.
- **Un-gate the expensive jobs entirely.** Correct but costly: roughly 6.3 billed minutes on every docs-only pull request against 1.38 for the design that won.
- **Remove the offending contexts from the required set.** Rejected: it deletes the gate instead of repairing it.
- **Adopt merge queues.** Rejected: heavy platform machinery for a configuration bug, and it does not fix a zero-file back-merge either.
- **Do nothing and keep bypassing.** Rejected: a gate that is routinely bypassed stops being read as a gate at all.

## Risks

- **The gate reports green without inspecting anything.** This is the fatal one. A no-op `validate` on a docs-only pull request satisfies branch protection while running none of the validators, and `docs/policy/**`, `docs/incidents/**`, and `docs/decisions/**` are validator INPUT that several guards read. The pull requests most likely to hit the no-op are precisely the ones carrying the files those guards exist to check. The proposal turns "unmergeable" into "merged unchecked", which is a strictly worse failure because it is silent.
- **Two filter sets must stay exact complements forever.** Every re-inclusion added to a real workflow's filter needs a matching exclusion in its companion. `ci.yml` had already accumulated four such re-inclusions (`docs/policy/**`, `docs/v*/*/development/*.md`, `docs/incidents/**`, `docs/decisions/**`) across four separate versions, each added because a guard read that path. Any drift between the pair yields either a double-run or a gap where neither workflow triggers, and the gap is invisible.
- **The job names become duplicated across files.** A rename must land in both, and the failure of forgetting is a required context that stops existing.
- **It does not fix the zero-file case.** A pull request with no changed files matches no path filter, inverse or otherwise, so `#50` and `#55` would still need an administrator merge.
- **Roughly doubles the workflow surface** for no capability, which is the shape `AGENTS.md`'s scope-fit rule declines: production structure added for a design possibility rather than a shipped behavior.
