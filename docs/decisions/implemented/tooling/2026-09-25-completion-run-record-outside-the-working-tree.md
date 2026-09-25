# Decision: Keep the completion run record outside every working tree

Status: implemented - `check_plan_completion.py` stores one run record per repository, remote, and plan at `~/.nexus-hub/runs/<key>.json`, owner-only.

## Problem

A full `/implement` run collects every approval once, at its start, and then pushes, merges, tags, and publishes without asking again. The record of those approvals is therefore the trust root for actions that are permanent and public. It must survive the run's own git operations (branch switches, rebases, `git clean`, worktree removal at the end of the plan), must never be committed by accident, and must be hard for the agent to rewrite as a side effect of ordinary work.

## Decision

The record lives at `~/.nexus-hub/runs/<sha256(repo root, remote URL, plan path)>.json` with a 0700 directory and a 0600 file. The checker rejects any record found inside a working tree or tracked by git. Approvals are frozen by an HMAC keyed by an owner-only secret beside the records, and each approval must match text the user submitted. The full rules are in `catalog/skills/workflow/implement-phase/references/completion-contract.md`.

## Alternatives considered

**A `.nexus/` folder in the worktree.** It is discoverable and travels with the checkout. It is also deleted when the plan's worktree is removed, which happens inside the same run the record governs, and one `git add -A` away from being committed and pushed. Rejected.

**The git common directory (`.git/nexus-runs/`).** It survives worktree removal and is never committed. It is still inside the repository the agent edits, disappears with a re-clone, and on a shared checkout is visible to every worktree's session. Rejected as the primary location; the key already separates plans.

**The user's home (`~/.nexus-hub/runs/`).** Outside every checkout, survives worktree teardown, never committed, owner-only, and already the root the installer manages. It is per-machine, so a run cannot move between machines; that is accepted, because the approvals it holds were given on this machine for this checkout. Chosen.

## Consequences

- A run resumes after any git operation, including removal of the plan's own worktree.
- Records accumulate; stale records (session gone, older than 72 hours) are ignored and reported once.
- The HMAC and approval-origin rules raise the cost of widening an approval but are not a sandbox; the contract's threat model says so.
