# gh CLI Auth + Rate-Limit Runbook

Reference for the `[[tasks-to-issues]]` skill. One-page runbook for setting up `gh` auth and handling GitHub's secondary rate limit on issue creation.

## Authentication

### First-time setup

```sh
gh auth login
```

Choose the GitHub host (`github.com` for the default service), the protocol (`HTTPS` recommended for non-SSO users; `SSH` if your org enforces SSO and you already have an SSH key registered), and authenticate via web browser. The CLI writes the token to `~/.config/gh/hosts.yml` (or the equivalent on Windows: `%APPDATA%\GitHub CLI\hosts.yml`).

Verify:

```sh
gh auth status
```

Expected output:

```
github.com
  ✓ Logged in to github.com account <user> (oauth_token)
  - Active account: true
  - Git operations protocol: https
  - Token: gho_*****
  - Token scopes: 'gist', 'read:org', 'repo', 'workflow'
```

The `repo` scope is the only mandatory one for `/tasks-to-issues`. If `repo` is missing, re-run `gh auth refresh -s repo`.

### Git-credential helper

Run once after `gh auth login` so subsequent `git push` / `git pull` operations against the same remote use the cached token:

```sh
gh auth setup-git
```

This configures `git config --global credential.https://github.com.helper '!gh auth git-credential'`. After this, `git` uses the same OAuth token that `gh` holds.

### Multiple accounts

```sh
gh auth login --hostname github.com --git-protocol https --web --user <user1>
gh auth login --hostname github.com --git-protocol https --web --user <user2>
gh auth switch --user <user2>
```

The active account is the one used by all subsequent `gh` calls until the next `gh auth switch`.

## Rate Limits

### Primary rate limit

Authenticated users get 5000 REST API requests per hour. Each `gh issue create` consumes one REST call. The skill's sequential execution means a plan with 100 tasks consumes 100 calls -- well under the hourly cap.

### Secondary rate limit (the one that bites)

GitHub silently enforces a per-resource secondary rate limit on issue creation: roughly 20 issues per minute and a stricter burst threshold of 5 issues in a 5-second window. The exact thresholds are not published and they change.

The skill's sequential execution avoids the burst threshold but can still hit the per-minute cap on plans with more than 20 tasks. When this happens, `gh issue create` returns an HTTP 403 with `secondary rate limit` in the body. The skill stops the loop on first failure (exit code 4) and surfaces the error.

**Remediation when you hit the secondary rate limit**:

1. Wait at least 60 seconds.
2. Re-run `/tasks-to-issues`. The idempotency markers `[gh#<num>]` in the source file ensure already-filed tasks are skipped, so the run resumes from the failure point.
3. For very large plans (>50 tasks), split the run into batches: file the first half, wait a minute, file the second half. The skill's idempotency already handles this -- you just run the same command twice with a wait in between.

### Diagnosing rate-limit hits

```sh
gh api rate_limit --jq '.resources.core'
```

Returns the current core REST API usage. The `resources.core.remaining` field shows how many calls you have left this hour. The `resources.code_search` and `resources.graphql` fields are separate buckets and do not apply to issue creation.

The secondary rate limit is not surfaced by `gh api rate_limit` -- there is no public way to query it. The only signal is the 403 response from `gh issue create`.

## Recommended Label Pre-Creation

`/tasks-to-issues` does not auto-create labels. If a label is missing in the repo, `gh issue create` warns and the issue is created without the missing label. Pre-create the four labels the skill uses before your first run:

```sh
gh label create nexus-hub --color 8B4FFF --description "Filed by Nexus-Hub /tasks-to-issues"
gh label create spec-kit-task --color 6F42C1 --description "Spec-driven development task"
gh label create parallel --color 0E8A16 --description "Safe to work in parallel"
gh label create user-story-1 --color 0366D6 --description "Belongs to User Story 1 (P1)"
gh label create user-story-2 --color 5319E7 --description "Belongs to User Story 2 (P2)"
gh label create user-story-3 --color B60205 --description "Belongs to User Story 3 (P3)"
```

Add more `user-story-N` labels as your plans grow. The colors above are suggestions, not requirements -- the skill never sets or reads colors.

## Auditing After a Run

After a `/tasks-to-issues` run completes, audit the new issues:

```sh
gh issue list --label "spec-kit-task" --state open --limit 100
```

Cross-reference the printed issue URLs against the `[gh#<num>]` markers in the source `tasks.md` / `plan.md` to confirm 1:1 coverage. If the counts diverge, run:

```sh
grep -E '^- \[ \] T[0-9]+' <source-file> | grep -c '\[gh#'
```

This counts how many task lines have an idempotency marker. The number should match the open `spec-kit-task` issues filed since the last clean run.

## Related Files

- `[[tasks-to-issues]]` SKILL.md -- skill body that consumes this runbook.
- `catalog/commands/tasks-to-issues.md` -- command file that orchestrates the flow.
- `catalog/skills/workflow/tasks-to-issues/scripts/tasks-to-issues.sh` and `.ps1` -- helper scripts.
