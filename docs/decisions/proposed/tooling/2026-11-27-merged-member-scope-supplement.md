# Decision: A captured decision can reconcile the unclaimed files of any merged member

Status: proposed - `record supplement-scope` gains a derived form for any merged member of a minor run, plus a read-only `record scope-gap` preview. Late admission of finished work is not added.
Date: 2026-11-27
Author: Ben Dourthe
Template: Nygard

## Problem

`python scripts/check_plan_completion.py check-minor v4.15` cannot print `MINOR COMPLETE` because the run record disagrees with what merged. The claim audit (`_historical_claim_status`) compares each merged member's change set with the claims recorded before it started.

- v4.15.6 (merge `96b682692dc313e4405a23c31bd140a3cbf5bbe9`, PR 719) changed files outside its recorded write paths. The member never held a publication start, so no coordinator paths were recorded either.
- v4.15.7 (merge `44f73e56332c60b614afaf5f2d50cb779118048c`, PR 730) carries one coordinator registry sync, `data/skills.json`. `record permit-member-paths` refuses it with `member-paths-coordinator-reserved`, and refuses any member that already merged.
- Because the audit reads `unmet`, `_merged_on_base` is false for both members and `record member-implement-start --member v4.15.8` returns `implementation-dependency-unmerged`.

The only scope repair, `supplement-scope`, is limited by its descriptor to one merge of one other minor.

## Contract answers

(a) A reviewed historical scope supplement for an already merged member is allowed in kind but not yet in extent. The contract defines the mechanism and then fixes it to one case:

> The dedicated `supplement-scope` round recognizes only the reviewed v4.14.2 contribution merged as `d2d7bff7a0c192437eddcbdb677880791ea3f501` in `bendourthe/Nexus-Hub`. [...] Other repositories, members, merges or path sets are refused. Original implementation and coordinator claims, baselines, approvals and frozen budgets remain unchanged.

Generalizing it is therefore a contract change, not a use of existing authority. The properties that make the mechanism safe do not depend on the descriptor being fixed: the round binds the record, controller, owner session and nonce, and "Only a genuine captured answer consumed under the existing native writer lease appends a signed `historical_scope_supplements` entry. Chat approval to build the repair, earlier blocker answers and free text alone cannot append it." This decision keeps all of that and replaces the fixed file list by a list the tool derives from the merge, which the maintainer reads in full before approving.

(b) Late admission of an implemented but unadmitted member is forbidden, and nothing here relaxes that. Admission is a claim made before the work exists:

> `record member-implement-start [...] --worktree WORKER --head SHA --claims FILE` admits implementation independently of release order. [...] Native validation binds [...] the proposed base [...] Every changed worker path must be owned.

and the withdraw paragraph states the consequence: "The member is admitted again later with the ordinary `record member-implement-start`, which requires the worker to be at a clean commit already merged into the target branch, so any commit that exists only on the member branch must be preserved and reapplied by the operator first." The contract already refuses retrospective permission elsewhere: "Admission checks the worker against its original scope before adding the manifest claim, so earlier unclaimed writes cannot gain retrospective permission."

Fact correction: the record shows v4.15.11 and v4.15.12 were admitted and then withdrawn (`implementation_withdrawals` is present on both, `implementation` is absent). They are not members that were never admitted. v4.15.8, v4.15.10 and v4.15.13 have no admission yet, which is normal.

The compliant route for v4.15.11 and v4.15.12 is re-admission with a fresh worker: preserve the existing branch under another name, recreate the member branch at a clean commit merged into the target, declare the claims, run `record member-implement-start`, then reapply the preserved commits. Publication then audits the reapplied files against the declared claims. No exclusion route exists for a frozen member in the current record: a minor's `excluded` list is written at creation, and the only member-level outcome the contract names is the conditional full decline defined by a plan. This decision does not invent one.

## Proposal

- `record supplement-scope` keeps its reviewed v4.14.2 form byte for byte. For every other merged member (original or amended) it takes the member version and a full 40-character merge commit.
- The merge must be a two-parent merge and the verified merge of the member's recorded pull request. A short name, `HEAD`, a wildcard, an unknown commit or a non-merge commit is refused.
- The tool derives the list: `git diff --raw` of the merge against its integration parent, minus the paths the audit already counts as claimed (recorded write paths, coordinator paths after a publication start, permitted implementation paths, verified archive-only paths and reconciled checkpoint paths).
- Unclaimed files the coordinator owns are stored and shown apart as the coordinator contribution. The review page prints a member list, a coordinator list and a count of each.
- Sensitive paths, non-regular files and an execution registry file the audit would reject are never accepted: the round refuses with `merged-scope-protected-path`. An empty gap refuses with `merged-scope-nothing-to-supplement`.
- The entry is stored in the member's existing `historical_scope_supplements` list. The writer, the signing domain and the audit read it exactly as for the reviewed form, and the audit recomputes the list from the merge on every read, so a widened or edited entry is refused.
- The audit lets a supplemented file through the coordinator-name rule (`CHANGELOG.md`, known-gaps ledgers) only when a valid captured entry names that exact file.
- `record scope-gap --minor --member --merge` is read-only. It prints the same derivation, the current audit state and a verdict, and writes nothing.

## Alternatives considered

- **Edit the record by hand.** Rejected: it is signed, and the writer refuses unsanctioned member changes.
- **Add the files to `implementation.write_paths` with `permit-member-paths`.** Rejected: that action is for unmerged members, refuses coordinator-reserved files and rewrites the original claims, which the supplement leaves unchanged.
- **Compile one more fixed descriptor per member.** Rejected: it needs a code release per merge, and the maintainer would still approve a list the author typed. Deriving the list from the merge removes the typed input.
- **Accept a caller-supplied path list checked against the diff.** Rejected: it adds an input that can only narrow or mislead, and a narrowed list leaves the audit unmet.
- **Admit v4.15.11 and v4.15.12 late over their finished branches.** Rejected: it would grant the retrospective permission the contract refuses, and "Every changed worker path must be owned" is meant to hold before the work, not after.
- **Mark the audit met for coordinator files without a record entry.** Rejected: the two members would pass with no decision from the maintainer, which is the guarantee the supplement exists to keep.

## Acceptance criteria

- `record scope-gap` for v4.15.6 and v4.15.7 lists exactly the files in `git diff` of each merge against its integration parent, minus claimed paths, and writes nothing.
- A genuinely captured decision appends one signed entry, after which the claim audit reads `met` and `record member-implement-start --member v4.15.8` no longer stops on `implementation-dependency-unmerged`.
- A wildcard, a short or symbolic merge name, a non-merge commit, a sensitive file, an empty gap, a self-approval and a replay are each refused with the record unchanged.
- The reviewed v4.14.2 supplement keeps passing its existing tests.

## Risks

- A page of 26 files is long enough to be approved without reading. The two separate lists and the per-list counts are the mitigation, and the preview lets the coordinator check it first.
- A supplement acknowledges history. It cannot show that a file was correct, only that the maintainer saw it.
- The derived route applies to any minor run, not only v4.15. The refusals and the matching-helper rule bound it, but a future misuse would show up as a supplement entry in the record history.

## Consequences

- The maintainer approves one page per member, with every file visible. For v4.15.6 that page is long, because the member changed more than its claims.
- Coordinator files are acknowledged as coordinator work. They still grant no release, archive, spending or retry authority.
- Matching helpers are required at every reader and writer boundary. An older helper cannot verify a derived entry and reads the member as unmet.
- v4.15.9 can use the same route after its pull request merges, and needs no further code.
