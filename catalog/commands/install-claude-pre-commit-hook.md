---
description: Install an opt-in git pre-commit hook in the current repository that pipes every staged diff through `claude -p` to catch hardcoded secrets, debug artifacts, and unfinished TODOs before they enter version control. Cross-platform.
---

# Install Claude Pre-Commit Review Hook

Wire up `.git/hooks/pre-commit` in the **current working directory's** repository so that every `git commit` runs the staged diff through Claude Code CLI (`claude -p`) for a quick LLM review of hardcoded secrets, debug artifacts (console.log, print, debugger), unfinished TODOs, and large commented-out code blocks.

This is **opt-in**. The hook never installs automatically — running this command is the only way to enable it for a given repository. Bypass paths and a diff-size cap are baked in so the hook never permanently blocks a legitimate commit.

## When to Use

Run this command **once per repository** where you want a pre-commit Claude review.

Good fits:
- Long-lived application repos where credential leaks are expensive (paid services, customer data).
- Repos with mixed authorship (humans + multiple AI agents) where the regex-only `secret-scan.sh` Claude Code hook can be bypassed by editing through Cursor / Copilot / a terminal editor.
- Solo projects where you want a self-imposed review pass before commit.

Skip for:
- Repos where every commit is reviewed by a teammate before merge (the GitHub PR review covers the same ground).
- Repos with extremely high commit frequency (~50+/day) where the per-commit ~2-10s latency adds up. Use a CI-time scan instead.

## Prerequisites

1. **Claude Code CLI installed and on PATH.** The hook shells out to `claude -p`. Verify with `claude --version`.
2. **DevAI-Hub installed.** The hook source must exist at `~/.devai-hub/hooks/claude-diff-review.sh` (Linux/macOS) or `%USERPROFILE%\.devai-hub\hooks\claude-diff-review.sh` (Windows). If absent, run the DevAI-Hub installer first (`bash scripts/installer.sh` or `powershell scripts/installer.ps1`).
3. **Working directory is inside a git repository.** The command operates on `.git/hooks/pre-commit` of the CWD's repo.

## Steps

1. **Verify the working directory is inside a git repository.** Run `git rev-parse --git-dir`. If it fails, stop and tell the user to `cd` into the target repo first.

2. **Locate the hook source.** Check that the source script exists:
    - Linux/macOS: `$HOME/.devai-hub/hooks/claude-diff-review.sh`
    - Windows: `$env:USERPROFILE\.devai-hub\hooks\claude-diff-review.sh`

    If absent, stop and tell the user to run the DevAI-Hub installer first.

3. **Verify Claude CLI is available.** Run `claude --version`. If the command is not found, warn the user that the hook will print a non-fatal warning on every commit until Claude Code CLI is installed, and ask whether to continue.

4. **Detect existing pre-commit hook.** Read `.git/hooks/pre-commit` (relative to the repo root returned by `git rev-parse --show-toplevel`).

    - **If the file does not exist**: skip to step 5.
    - **If the file exists AND contains the line `# claude-diff-review.sh`** (the marker comment from the DevAI-Hub hook): tell the user the hook is already installed and exit cleanly. Do not overwrite.
    - **If the file exists AND does NOT contain that marker**: this is a third-party / user-authored pre-commit hook. Show the first ~30 lines of the existing file to the user, then ask which option they want:
        1. **Replace** the existing hook with the DevAI-Hub hook. Back up the original to `.git/hooks/pre-commit.devai-backup-<timestamp>` first.
        2. **Abort** (do nothing).
        3. **Chain manually**: do not modify the file; print instructions for the user to edit it themselves so the existing hook runs, then the DevAI-Hub hook runs (or vice versa). Sample wrapper provided in step 6 of this document.

        Wait for explicit user choice before proceeding. Never overwrite a non-DevAI-Hub pre-commit hook silently.

5. **Install the hook.** Copy the source script to `.git/hooks/pre-commit` and make it executable:

    ```bash
    cp "$HOME/.devai-hub/hooks/claude-diff-review.sh" .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
    ```

    PowerShell equivalent:

    ```powershell
    Copy-Item "$env:USERPROFILE\.devai-hub\hooks\claude-diff-review.sh" -Destination ".git\hooks\pre-commit" -Force
    # Git for Windows runs hooks via its bundled bash; no chmod equivalent needed.
    ```

6. **Smoke-test the hook.** Run `bash .git/hooks/pre-commit </dev/null` and confirm exit code 0 (no staged diff = no review). If the hook errors, troubleshoot before declaring success.

7. **Print usage and bypass paths.** Tell the user exactly:

    ```text
    Pre-commit hook installed.

    What it does:
        Pipes `git diff --cached` through `claude -p` on every `git commit`.
        Looks for: hardcoded secrets, console.logs / print / debugger statements,
        unfinished TODOs, and large blocks of commented-out code.
        Verdict BLOCK (clear credentials) refuses the commit with exit code 1.
        Verdict WARN (debug / TODO) prints findings but allows the commit.
        Verdict PASS or any error: silent allow (fail-open).

    Per-commit bypass:
        DEVAI_DIFF_REVIEW_DISABLE=1 git commit -m "..."
        git commit -n -m "..."     (--no-verify; skips ALL pre-commit hooks)

    Diff-size cap (default 50 KB; raise to allow larger commits):
        DEVAI_DIFF_REVIEW_MAX_BYTES=204800 git commit -m "..."

    Disable for this repo:
        rm .git/hooks/pre-commit
    ```

## Manual chaining wrapper (for step 4 option 3)

If the user chose "chain manually" because they have a pre-existing pre-commit hook, give them this wrapper to save as `.git/hooks/pre-commit`:

```bash
#!/usr/bin/env bash
# Combined pre-commit: existing hook, then DevAI-Hub claude-diff-review.
set -e

# Run the original hook (rename it first to .git/hooks/pre-commit.original).
if [ -x ".git/hooks/pre-commit.original" ]; then
    .git/hooks/pre-commit.original
fi

# Then run the DevAI-Hub review hook.
"$HOME/.devai-hub/hooks/claude-diff-review.sh"
```

## Verification

- [ ] `.git/hooks/pre-commit` exists in the target repository.
- [ ] The file is executable on Linux/macOS (`stat -c '%a' .git/hooks/pre-commit` shows at least `755`); Git for Windows ignores POSIX permissions.
- [ ] `bash .git/hooks/pre-commit </dev/null` exits 0.
- [ ] The first few lines of the installed hook contain the comment `# claude-diff-review.sh - opt-in git pre-commit hook (DevAI-Hub).` (so a future re-run of this command detects it as already-installed).
- [ ] If a non-DevAI-Hub pre-commit hook existed, a backup file `.git/hooks/pre-commit.devai-backup-<timestamp>` exists in the same directory.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I already have `secret-scan.sh` as a Claude Code PreToolUse hook, so this is redundant." | `secret-scan.sh` only fires when **Claude Code** writes a file; it sees nothing when the same repo is edited via Cursor, Copilot, the terminal, or a teammate's machine. The git pre-commit hook fires on every `git commit` regardless of who or what authored the change, so the two layers cover disjoint surfaces. |
| "I'll just run `git commit -n` whenever the hook is annoying." | Reaching for `-n` to bypass a real BLOCK is exactly how secrets reach `origin`. Reach for `DEVAI_DIFF_REVIEW_DISABLE=1` only when you are confident the verdict is wrong; the env var is logged in your shell history (so the bypass is auditable) and only affects one commit. |
| "The hook will block my commit during a merge / rebase, breaking my workflow." | The hook explicitly skips when `MERGE_HEAD`, `CHERRY_PICK_HEAD`, `REBASE_HEAD`, or any rebase state directory exists. Merge / cherry-pick / rebase commits are never reviewed; only author-curated commits are. |
| "Every commit will now cost API tokens." | The default 50 KB diff cap means the hook skips with a warning on truly large diffs (the most token-expensive case). For typical commits (~5-15 KB of diff), the per-commit token cost is ~3-8k input + ~200 output tokens. Adjust `DEVAI_DIFF_REVIEW_MAX_BYTES` to control this. |

## Related Skills and Commands

- `secret-scan.sh` (Claude Code PreToolUse hook, ships installed) — regex-based secret detection at write-time. Complementary to this command.
- `pre-commit-checklist` skill — broader pre-commit setup including linting, formatting, and tests.
- `code-commit-workflow` skill — conventional-commit message format and atomic-commit guidance.
