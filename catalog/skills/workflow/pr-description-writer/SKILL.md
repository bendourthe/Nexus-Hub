---
name: pr-description-writer
description: "Produce a reviewer-friendly pull request description for any code change. Make sure to use this skill whenever the user mentions PR description, pull request description, draft PR, document code changes, merge request description, change summary for review, MR description, or asks for help writing the body of a pull request before opening it. SKIP: commit message generation (use `code-commit-workflow`), release notes (use `release-notes-writer`), changelog generation (use `/generate-changelog`)."
summary_l0: "Author reviewer-friendly PR descriptions with summary, how-to-test, risk, and reviewer notes"
overview_l1: "This skill produces a pull request description that a reviewer can read in 60-90 seconds and walk away knowing what changed, why, how to test it, what the risk is, and what the author wants reviewed. It enforces a fixed 8-section output (Title, Summary, Changes Made, Screenshots, How to Test, Testing Checklist, Risk and Rollout, Reviewer Notes), with a 72-character imperative-mood title, a per-PR-type tailoring (feature / bugfix / refactor / docs / chore), and explicit risk-and-rollout language for anything that touches data, migrations, or production behavior. Use it whenever a PR is about to open and the author wants the description to support the review rather than substitute for it. Trigger phrases: PR description, pull request description, draft PR, merge request description, document code changes."
---

# PR Description Writer

Produce a reviewer-friendly pull request description for a code change. The output is designed to be read by a reviewer in 60-90 seconds, after which the reviewer knows:

1. What the PR does (one sentence).
2. Why the PR exists (the business or technical motivation).
3. How to test it (a step-by-step the reviewer can actually run).
4. What the risk and rollout plan are.
5. What the author specifically wants reviewed.

The PR description is the reviewer's entry point. A good description shortens review time; a vague description forces the reviewer to reverse-engineer the change from the diff.

This skill is opinionated on four points: the **title is 72 characters or less in imperative mood**; the **How-to-Test section is reviewer-runnable** (not "run the test suite"); the **Risk and Rollout section is mandatory** for anything touching production behavior, data, or migrations; and the **Reviewer Notes section explicitly directs attention** so the reviewer reads the right files first.

## When to Use This Skill

Use this skill for:

- Drafting the body of a PR before opening it.
- Rewriting a stub PR description after the PR has been opened with just a title.
- Standardizing PR descriptions across a team that has variable practice.
- Tailoring the description to PR type (feature, bugfix, refactor, docs, chore) -- the structure adapts to the type.

**Trigger phrases**: "PR description", "pull request description", "MR description", "merge request description", "draft PR", "document code changes", "change summary for review", "open this PR".

### When NOT to use this skill

- **Commit message generation** -- use `code-commit-workflow` or the `/generate-commit-message` command. A commit message describes one commit; a PR description describes the PR's full set of commits and the rationale.
- **Release notes** -- use `release-notes-writer`. Release notes are user-facing; PR descriptions are reviewer-facing.
- **Changelog generation** -- use the `/generate-changelog` command. The changelog is the project-level history; the PR description is the per-PR artifact.

## What This Skill Does

Produces a PR description with eight sections.

| Section | Required? | Length | Purpose |
|---|---|---|---|
| Title | Yes | <=72 chars | Imperative mood, type-prefixed if the team uses conventional commits |
| Summary | Yes | 1-3 sentences | What and why, in plain language |
| Changes Made | Yes | Bullets | What changed, grouped by component or theme |
| Screenshots / Demo | If UI | Image / link | Visual change evidence |
| How to Test | Yes | Numbered steps | Reviewer-runnable procedure |
| Testing Checklist | Yes | Bullets | Self-test the author already ran |
| Risk and Rollout | Yes if production-touching | Paragraph + bullets | Blast radius, rollback plan, feature flag |
| Reviewer Notes | Yes if non-trivial | Paragraph | What to look at first, what to ignore |

## Instructions

### Step 1: Gather the Required Inputs

Before writing, collect:

- **What changed** -- the file list and a one-line summary of each meaningful change.
- **Why it changed** -- the motivation (ticket link, customer request, internal initiative, bug ID).
- **How to test it** -- the procedure the author ran locally to verify the change.
- **Risk level** -- the author's assessment (low / medium / high), with the reasoning.
- **PR type** -- feature / bugfix / refactor / docs / chore / breaking. Picks the tailored output structure.

If any of these are missing, ask. A PR description authored without "why" or "risk" is a stub.

### Step 2: Author the Title

The title rules:

- **Imperative mood** -- "Add", "Fix", "Refactor", not "Added" or "Adding".
- **<=72 characters** including the prefix.
- **Type prefix if the team uses conventional commits** -- `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`, `test:`, `ci:`, `perf:`. If the team does not use prefixes, skip them.
- **Specific** -- "Fix race condition in checkout-cart concurrent writes" beats "Fix race condition" beats "Bug fix".
- **No trailing period.**
- **ASCII-only** -- no em-dashes, en-dashes, curly quotes, or ellipsis characters. Use hyphens and `...` instead.

Examples:

- `feat(checkout): add idempotency-key support to /checkout/submit` (66 chars, type-prefixed).
- `Fix race condition in checkout-cart concurrent-write path` (57 chars, no prefix).
- `Refactor auth middleware to remove duplicated token-parsing code` (66 chars, no prefix).

If the meaningful title would exceed 72 characters, the PR is probably doing too much; consider splitting.

### Step 3: Write the Summary

The Summary is 1-3 sentences in plain language. It answers two questions:

- **What does this PR do?** (one sentence).
- **Why?** (one or two sentences, including a ticket link if applicable).

Avoid restating the diff. The reviewer can see the diff; the Summary explains the change at the level the diff cannot.

Example:

> Adds idempotency-key support to the checkout submission endpoint so retried requests do not create duplicate orders. Closes ENG-4012. The implementation uses a Postgres unique index on `(idempotency_key, customer_id)` with a 24-hour retention sweep.

### Step 4: List the Changes Made

The Changes Made section is bullets, grouped by component or theme. Each bullet is one line.

```
Changes Made:
- API: added Idempotency-Key header parsing in CheckoutController.submit
- Database: migration 20260519_120000_add_idempotency_keys.sql adds the unique index
- Repo: added retention sweep job in BackgroundJobs::IdempotencyKeySweeper
- Tests: 6 new tests in tests/integration/test_checkout_idempotency.py
- Docs: README "Checkout API" section updated with the new header
```

Group by component when the PR touches several layers; group by theme when the PR is more behavioral than structural.

### Step 5: Add Screenshots or a Demo (UI changes only)

If the PR touches user-facing UI, include:

- A before screenshot or a "no before, this is new UI" note.
- An after screenshot.
- Optionally, a short screen-capture link.

If the PR has no UI surface, this section is omitted.

### Step 6: Write the How-to-Test Section

The How-to-Test section is step-by-step instructions a reviewer can actually run. The rules:

- **Each step is a concrete action**, not "set up your environment".
- **Each step states the expected result**, not just the action.
- **Commands are copy-pasteable**, not described.
- **Setup is referenced**, not re-stated. If the project has a `CONTRIBUTING.md` with setup instructions, link it.
- **Wrong**: "Run the test suite." Right: ``pytest tests/integration/test_checkout_idempotency.py -v`` (expected: 6 passed).

Example:

```
How to Test:
1. Check out the branch and run pip install -r requirements-dev.txt.
2. Apply the migration: alembic upgrade head. Expected: "Migration 20260519_120000 applied".
3. Run the new integration tests: pytest tests/integration/test_checkout_idempotency.py -v.
   Expected: 6 passed in <5 seconds.
4. Manual: with the dev server running, send two POSTs to /checkout/submit with the same Idempotency-Key header.
   Expected: the second response returns the same order_id as the first; no duplicate row in the orders table.
```

### Step 7: Fill the Testing Checklist

The Testing Checklist is the author's self-test. Each item is a binary check the author ran before opening the PR.

```
Testing Checklist:
- [x] Unit tests pass locally (pytest -q)
- [x] Integration tests pass locally
- [x] Linter passes (ruff check .)
- [x] Type-check passes (mypy --strict src/checkout/)
- [x] Manual smoke test in dev environment
- [ ] Load test (deferred -- not applicable for this change)
```

A box that is checked is a statement that the author ran the check. An unchecked box must explain why (deferred, not applicable, requires reviewer environment).

### Step 8: Write the Risk and Rollout Section (mandatory for production-touching PRs)

This section is required for any PR that:

- Modifies database schema or runs a migration.
- Modifies production-running code paths (not test-only, not docs-only).
- Adds or modifies a feature flag.
- Changes external API contracts.

The section answers four questions:

1. **Blast radius** -- if this PR is wrong, what breaks? Which users, which services, which features?
2. **Rollout plan** -- how does this deploy? All-at-once, canary, dual-write, feature flag?
3. **Rollback plan** -- if it fails, how do we undo? What is the rollback duration?
4. **Risk level** -- low / medium / high, with the reasoning.

Example:

```
Risk and Rollout:
Blast radius: affects only /checkout/submit; failure surface is "duplicate orders may be created
during retries" (i.e. degraded back to current behavior, not worse).
Rollout: merge -> auto-deploy to staging -> canary 10% in prod for 30 minutes -> full rollout if 
error rate stable.
Rollback: revert the deploy via helm rollback checkout <prev-rev>; the migration is additive (new
index) so no schema rollback is needed.
Risk: low (additive change, no behavioral regression possible if the new header is absent).
```

For docs-only / chore PRs that do not touch production behavior, this section may be omitted.

### Step 9: Write the Reviewer Notes

The Reviewer Notes section directs the reviewer's attention. The author knows where the interesting decisions are; the reviewer does not.

The rules:

- **State what to look at first.** "The main reviewable surface is `src/checkout/idempotency.py` lines 40-90 (the unique-key dedup logic)."
- **State what to ignore.** "The 200-line diff in `tests/fixtures/` is auto-generated fixture data; do not review line-by-line."
- **State open questions.** "Open question: should the retention sweep be a separate cron, or piggyback on the existing nightly-cleanup job? Currently a separate cron; happy to change."
- **State known caveats.** "Known caveat: this change does not handle the edge case where a customer changes account mid-retry; that is tracked separately in ENG-4013."

The Reviewer Notes section is the difference between a 90-minute review and a 30-minute review.

### Step 10: Tailor by PR Type

The eight sections above are the default. Trim or expand by type:

| PR type | Notes |
|---|---|
| Feature | Full structure. Risk-and-Rollout is mandatory. |
| Bugfix | Full structure. Add a "Root cause" line in Summary; link to the bug ticket. Risk-and-Rollout is mandatory if the fix changes behavior. |
| Refactor | Skip Screenshots. Risk-and-Rollout mandatory if any production path is touched. Reviewer Notes is doubly important (refactors hide behavioral changes). |
| Docs | Skip Risk-and-Rollout, Testing Checklist becomes "Spell-check, link-check, render preview". Title prefix `docs:`. |
| Chore (deps bumps, CI config) | Risk-and-Rollout mandatory for dependency bumps; state the upstream changelog link. |
| Breaking change | Add an explicit "BREAKING CHANGE:" section in the body, immediately after Summary, naming the contract that breaks and the migration path. |

## Optional Pattern: Building the Risk and Testing Sections from an Audit Trail

When the change went through a recorded review-and-fix process -- the review findings, the fixes applied in response, and the re-check results are all available as a trail -- the Risk-and-Rollout and How-to-Test / Testing-Checklist sections can be built deterministically from that trail instead of authored freehand. This is an optional enrichment for when such a trail exists; it does not replace the eight-section structure above.

Render the fix history as an **issue-then-fix-then-verification narrative**, not a flat chronological log. For each finding that was fixed, state three things in order:

1. The issue -- what the review found, and where.
2. The fix -- the change applied in response.
3. The outcome -- either the successful re-check that closed it, or the findings still open after that fix.

This gives a reviewer direct visibility into what was found, what changed in response, and how many attempts a fix took before it held, working from the same trail the author did rather than from a summary of it.

The payoff is trust: a PR body derived from a real audit trail is harder to inflate and easier to verify than authored prose, and it surfaces the follow-on fixes the original change missed (the ones the review caught). When no such trail exists, author the Risk and Testing sections normally per Steps 6 and 8.

See [[intent-based-review]] and [[multi-agent-code-review]] for the review process that produces the trail, and [[verification-before-completion]] for the evidence each re-check should carry.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The diff explains itself" | The diff explains what; it does not explain why. The reviewer can read the diff but cannot read the author's mind. The 60 seconds the author spends writing the Summary saves the reviewer 600 seconds of reverse-engineering. |
| "Reviewers can just run the tests" | "Run the tests" is not a testing procedure; it is a wish. The reviewer who has not set up the test environment, or who is reviewing on the train, or who is doing a logic review without execution, needs concrete instructions or a clear statement of what the tests cover. |
| "It's a tiny change, no description needed" | Tiny changes are where bugs hide. A one-line PR with no description still benefits from a one-sentence Summary, a Risk-and-Rollout line ("trivial, no risk"), and a What-to-Look-At pointer. Total cost: 30 seconds. Total benefit: reviewer does not have to ask. |
| "The commit message has everything" | Commit messages describe individual commits. The PR description describes the PR. They overlap (especially for single-commit PRs) but are not interchangeable: the PR description includes the How-to-Test, the Reviewer Notes, and the Risk-and-Rollout, which do not belong in a commit message. |
| "Risk-and-Rollout is overkill for backend changes" | Backend changes are where Risk-and-Rollout matters most. A UI tweak is visible; a backend race condition is not. The reviewer who is not deep in the call path needs the author's risk assessment to know what to scrutinize. |
| "Reviewer Notes is just author hand-holding" | Reviewer Notes is the highest-leverage section. It is the author saying "review this, ignore that, here's the open question I want you to weigh in on". Reviewers consistently rate PRs with Reviewer Notes as faster and easier than PRs without. |

## Verification

Before opening the PR (or before requesting review on an existing PR), walk this binary checklist. Every item must be true.

- [ ] Title is imperative mood and <=72 characters.
- [ ] Title uses ASCII-only punctuation (no em-dashes, en-dashes, curly quotes, ellipsis chars).
- [ ] Summary is 1-3 sentences and answers both "what" and "why".
- [ ] Summary links the bug / feature / ticket if applicable.
- [ ] Changes Made section lists the meaningful changes grouped by component or theme.
- [ ] Screenshots / Demo section is present if and only if the PR has UI changes.
- [ ] How to Test section has step-by-step reviewer instructions with expected results, not "run the tests".
- [ ] Testing Checklist is filled; checked boxes reflect actual self-tests; unchecked boxes are explained.
- [ ] Risk-and-Rollout is present for any PR that touches production code paths, data, migrations, or feature flags.
- [ ] Reviewer Notes is present for any non-trivial PR; states what to read first, what to ignore, and any open questions.
- [ ] If the PR is a breaking change, an explicit "BREAKING CHANGE:" section names the contract and the migration path.
- [ ] No AI-attribution language or AI-signed-off footer.

If any item is false, do not request review. Fix the description.

## Related Skills

- [[code-commit-workflow]] -- atomic commit hygiene and conventional commit messages. The PR may contain multiple commits authored via this skill; the PR description is a separate higher-level artifact.
- [[code-quality]] -- code review focused on quality, SOLID, complexity. A reviewer who reads a good description will spend more time on code-quality concerns rather than on understanding what changed.
- [[intent-based-review]] -- review by checking acceptance criteria. The PR description's How-to-Test section and Reviewer Notes are the entry point for intent-based review.
- [[release-notes-writer]] -- user-facing release notes. PR descriptions feed into release notes; the two artifacts are not the same.
- `/generate-changelog` (command) -- project-level changelog from git history. Well-formed PR descriptions improve the quality of auto-generated changelogs.
