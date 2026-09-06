# Response Contract: Worked Examples

Tier-3 companion to the `agent-communication` skill. The canonical contract is [`catalog/style-guides/agent-communication.md`](../../../../style-guides/agent-communication.md), installed at `~/.nexus-hub/style-guides/agent-communication.md`. This file carries the worked examples, so the skill body stays short and the examples cost nothing until they are needed.

## Contents

1. [Placeholder discipline: three cases](#placeholder-discipline-three-cases)
2. [Error recovery: re-issuing the remaining sequence](#error-recovery-re-issuing-the-remaining-sequence)
3. [Waiting-state interim update](#waiting-state-interim-update)
4. [End-of-task report](#end-of-task-report)
5. [Plain-language substitutions](#plain-language-substitutions)

## Placeholder discipline: three cases

The rule: every command block must run exactly as pasted. A block that still contains a template token has handed the user a failing command.

### Case 1: derivable, not derived (wrong)

The agent had read `docker-compose.yml` and knew every one of these values.

```bash
docker exec -it <container-name> psql -U <db-user> -d <database>
```

Pasting this produces `bash: syntax error near unexpected token 'newline'`, because the shell reads `<` as a redirect. The user's next message is a bug report about the command rather than progress on their task.

### Case 2: derivable, derived (right)

```bash
docker exec -it nexus-db psql -U nexus -d nexus_dev
```

Nothing about the second version is less precise. The difference is who did the lookup, and only one party could.

### Case 3: genuinely unknowable, flagged (right)

An API token is not derivable from the repository or the environment. It gets a REPLACE line that names the exact token and says where to find the value.

REPLACE `YOUR_API_TOKEN` with the token from your account settings page (Settings, then Developer, then Personal access tokens).

```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" https://api.example.com/v1/status
```

Note what the REPLACE line does that a bare placeholder does not: it names the token verbatim (so a search-and-replace is unambiguous), and it gives the lookup path (so the user does not have to ask a follow-up question to proceed).

### Multi-token variant

REPLACE two values before running this:

- `YOUR_HOST` with your database hostname, shown on the instance overview page.
- `YOUR_PASSWORD` with the password from your password manager entry for that instance.

```bash
PGPASSWORD=YOUR_PASSWORD psql -h YOUR_HOST -U nexus -d nexus_prod -c 'select version();'
```

## Error recovery: re-issuing the remaining sequence

Setup: the user was given a 5-step sequence and reports that step 3 failed with `permission denied while trying to connect to the Docker daemon socket`.

### Wrong

> That is a permissions problem. Run it with `sudo` and then continue with steps 4 and 5 above.

Two failures. The fix is wrong in substance (running one command with `sudo` leaves the next one failing for the same reason), and the reader has to scroll past their own error output to find steps 4 and 5. This is where people skip a step and then report a second, unrelated failure.

### Right

> Step 3 failed because the Docker socket is owned by `root` and your user is not in the `docker` group. Here is the corrected sequence from that point:
>
> 1. Add yourself to the `docker` group: `sudo usermod -aG docker $USER` (expect: no output)
> 2. Apply the new group without logging out: `newgrp docker`
> 3. Re-run the check: `docker ps` (expect: a table header, even with no containers listed)
> 4. Start the stack: `docker compose up -d`
> 5. Confirm it is healthy: `docker compose ps` (expect: every service shows `running`)

Every remaining step is present, renumbered from 1, with expected results. The user never scrolls.

### The renumbering rule

Renumber from 1, not from N. A sequence labeled "4, 5, 6" invites the reader to hunt for steps 1 through 3, which is exactly the scrollback trip the rule exists to prevent. The new sequence is a complete instruction set, not a continuation.

## Waiting-state interim update

### Wrong

The one sentence the reader needs is the last one.

> I refactored the parity checker to hoist the invariant-section comparison out of the per-file loop, which removes a quadratic re-read of each template body and lets the digest be computed once. The seeded-divergence fixture now writes into a temporary copy instead of mutating the real tree, so the test is order-independent. I also normalized line endings before hashing, because the Windows leg was producing spurious mismatches on CRLF, and I moved the roster constant next to the required-headings list so the two stay visually adjacent for the next person who edits them. Integration tests are now running.

### Right

> **Integration tests running (full suite, about 5 minutes). No action needed; I will report the results when they finish.**
>
> Just finished: the parity checker now compares templates correctly on Windows, and its test no longer edits real files while it runs.

The detail from the wrong version is not lost. It belongs in the completion report that follows, where the reader has a result to attach it to.

## End-of-task report

### Shape

- **Completed**: what changed, plain language, 1 to 2 lines.
- **Verified**: the evidence. Results and counts. If nothing ran, say so.
- **Open**: blocked, skipped, deferred, or risky items. "Nothing outstanding" when empty.
- **Next**: the concrete next action, or that there is none.

### Worked example

> **Completed**: Added the communication style guide and its decision record, and registered the new `agent-communication` skill in the three catalog files.
>
> **Verified**: `validate` passes end to end (274 skills, 8 budgeted docs within ceiling). The trigger evals rank the new skill first on all 3 positive cases and clear the strongest negative by the default margin.
>
> **Open**: The parity gate covers 5 of the 12 instruction templates by design, so a wording drift in the other 7 would be caught only by the aggregate heading test, not byte-for-byte. Tracked as a known gap for this version.
>
> **Next**: Phase 3 rolls the compact contract section into all 12 templates and extends the parity gate.
>
> In plain terms: the rules for how the assistant talks to you now exist in one place, and every platform will pick them up on the next install.

Note the Open part. It is present, specific, and names where the risk is tracked. An absent Open section reads as "all clear", which is a claim, not an omission.

## Plain-language substitutions

| Instead of | Write |
|---|---|
| "The MT-1 gate failed." | "The check that stops a release when version numbers disagree failed." |
| "Idempotent re-invocation is safe." | "Running it again is safe and will not double up." |
| "The invariant block diverged." | "One template's wording drifted from the other four, which must stay identical." |
| "Fails open." | "When it breaks, it lets everything through instead of blocking, so a failure is silent." |
| "I hoisted the comparison out of the loop." | "It now does the comparison once instead of once per file." |

The test is not whether the short version is less precise. It is whether the reader can decide what to do next. Where precision genuinely matters, keep the term and define it in place at first use.
