# Decision: Remove legacy instruction blocks only with per-span, per-file-state consent

Status: proposed - installers report exact-match leftover spans every run, back up first, and remove a span only when the next run carries its consent token

## Problem

Installs before the managed-marker merge wrote the whole instruction template and skill index straight into shared files such as `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md`. Later installs added the managed block below that text instead of replacing it, so these files now carry two skill indexes. On one development machine, about 10000 estimated tokens per file (a third of each) is a stale copy of the catalog, loaded into every session (see `docs/releases/v4/v4.13/development/rendered-context-baseline.md`). The leftover sits in a file the user owns and may have edited between the old lines. The installer cannot tell a leftover line from the same text the user typed, and deleting a user's line is the one outcome a harness must never cause silently.

## Proposal

1. **Exact-match detection from a generated fingerprint set.** `scripts/build_legacy_fingerprints.py` hashes every line any release shipped in an instruction template or skill index (placeholders rendered with every historical default). `scripts/lib/installer/legacy_instruction_block.py` reports a candidate span only outside the managed markers, in a region that holds the historical skill-index heading and a `**Total:` line, as a run of at least three matching lines. Every non-matching line is kept and splits the run. A match is evidence, not proof of authorship.
2. **Reports on every run.** Every install through a marker-merged writer (`instruction_merge.merge_instruction`, the single owner all six writers route through) reports each candidate's file, line range, estimated token cost, and removal diff. It also prints a consent token computed after every writer finished, so the token matches the file's final bytes.
3. **Per-run consent bound to the span.** A span is removed only when the install carries `--remove-legacy-instructions=<consent-sha256>`, where the token hashes the resolved path, the whole-file hash, the span's byte offsets, and its content. A token cannot authorize a second file with identical text, and it stops working the moment the file changes. `--yes` never implies consent. A token that matches no current span is refused by name and removes nothing.
4. **Verified backups first.** Before any write, the current bytes are kept once under `~/.nexus-hub/state/backups/<sha256>.<name>` (owner-only), re-read, and hash-verified. If no verified backup exists, removal is skipped. Backups are never rotated, overwritten, or deleted by the installer, and teardown does not track them.
5. **One snapshot, one write.** Removal and the managed-block refresh are rendered from the same snapshot, under a per-target lock shared by cooperating installers. The on-disk hash is re-checked immediately before one atomic replacement, and a detected concurrent change refuses the write. Line endings, BOM, and every byte outside the removed spans are preserved.

**Why the v4.13.1 edit guard does not apply.** The edit guard is an agent-side hook that intercepts an AI agent's own Write and Edit tool calls, so an agent cannot overwrite a user's edits. The installer is not an agent tool call. It is a user-run program, and the user's consent token is the direct equivalent of the guard's "confirm before overwriting user content" rule. Routing the installer through the guard would give no protection the token does not already give, and would make removal depend on whichever agent runtime happens to be installed.

## Alternatives considered

- **Report only, never remove.** Safest, but the stale index stays in every session forever and users must hand-edit a 300-line block. The measured cost (a third of the file) is too large to leave as a manual chore when exact consent makes removal safe.
- **Interactive prompt during install.** Installs are deliberately no-prompt (`--yes`, CI, and the one-line bootstrap run unattended), and a prompt cannot show a 300-line diff usefully in a terminal. A prompt answered by habit is also weaker consent than a token copied from a report the user read.
- **A standing environment variable (for example `NEXUS_HUB_REMOVE_LEGACY=1`).** One setting would authorize every future removal in every file, including spans that did not exist when the user decided. That is the opposite of consent bound to what the user saw.
- **Region-based removal (delete everything above the managed markers that looks like an old install).** Simple, but it deletes user lines interleaved with the leftover. The observed layout on the development machine has exactly such kept lines, so this fails on the first real file.

## Acceptance criteria

- Every marker-merged writer routes through `merge_instruction`; a guard test fails when a direct `merge_marker_section` call is added under `scripts/lib/integrations/`.
- An install without a token leaves every byte outside the managed block unchanged, and it writes a verified backup and a report with the token and diff.
- An install with the token removes exactly that span in one atomic write, and every other byte (including CRLF and BOM) is preserved.
- A stale token, a token from another file, a missing backup, or a concurrent change removes nothing.
- Teardown and repeated installs leave every backup in place.

## Risks

- **An uncooperative writer.** A program that ignores the lock can change the file between the final hash check and the atomic replacement, and no portable primitive closes that window. The verified pre-write backup is the recovery path, and the report names it.
- **A user line identical to shipped text.** It can fall inside a candidate span. The user sees it in the diff before copying the token; nothing is removed without that step.
- **Backup growth.** Content addressing stores each distinct file state once. The installer never deletes backups, so a user who installs very often accumulates copies until they remove them by hand.
