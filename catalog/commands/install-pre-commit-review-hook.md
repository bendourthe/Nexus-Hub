---
description: Install an opt-in git pre-commit hook in the current repository that pipes every staged diff through one of the supported AI CLIs (claude / gemini / codex / opencode) for review of hardcoded secrets, debug artifacts, and unfinished TODOs. Auto-detects which CLI is available; user picks if multiple. Cross-platform.
---

# Install Pre-Commit Review Hook (Multi-Platform)

Wire up `.git/hooks/pre-commit` in the **current working directory's** repository so that every `git commit` pipes the staged diff through an AI CLI for a quick review of hardcoded secrets, debug artifacts (console.log, print, debugger), unfinished TODOs, and large commented-out code blocks.

This command supports four AI CLIs, each with its own hook script. **No platform depends on any other.** The user's primary AI agent (Claude Code, Gemini / Antigravity, Codex, OpenCode) ships with a matching hook that calls only its own CLI; pick the one matching the CLI you already have installed and configured.

| AI Platform | Hook script | CLI required |
|---|---|---|
| Claude Code | `claude-diff-review.sh` | `claude -p` |
| Gemini / Antigravity | `gemini-diff-review.sh` | `gemini -p` |
| Codex (OpenAI) | `codex-diff-review.sh` | `codex exec` |
| OpenCode | `opencode-diff-review.sh` | `opencode run` |

**Cursor and GitHub Copilot are not supported** by this command. Cursor has no public headless CLI, and GitHub Copilot's `gh copilot suggest` / `gh copilot explain` are targeted to single-command synthesis, not arbitrary diff review. Users on those platforms can either install one of the four supported CLIs as a side dependency, or skip this command and rely on CI-side review instead.

This is **opt-in**. The hook never installs automatically — running this command is the only way to enable it for a given repository. Bypass paths and a diff-size cap are baked into every variant so the hook never permanently blocks a legitimate commit.

## Arguments

- `--platform=<name>` (optional): force a specific platform. One of `claude`, `gemini`, `codex`, `opencode`. If omitted, the command auto-detects.
- `--force` (optional): skip the existing-hook detection check and overwrite without asking. Backup is still written.

Example invocations:

```text
/install-pre-commit-review-hook
/install-pre-commit-review-hook --platform=gemini
/install-pre-commit-review-hook --platform=codex --force
```

## Steps

1. **Verify the working directory is inside a git repository.** Run `git rev-parse --git-dir`. If it fails, stop and tell the user to `cd` into the target repo first.

2. **Parse arguments.** Extract `--platform=<name>` (validate against the four supported names) and `--force` from the user's invocation.

3. **Detect available CLIs on PATH.** Run `command -v claude`, `command -v gemini`, `command -v codex`, `command -v opencode` (one each). Build a list of which are present.

    - **If the user passed `--platform=<name>`:** verify that CLI is on PATH. If not, ask whether to proceed anyway (the hook will print a non-fatal warning on every commit until the CLI is installed) or abort.
    - **If exactly one CLI is detected and no `--platform` flag:** use it; tell the user which one was auto-selected.
    - **If multiple CLIs are detected and no `--platform` flag:** ask the user which to use. List the detected ones with their hook script names. Wait for explicit choice.
    - **If zero CLIs are detected and no `--platform` flag:** stop and tell the user to install one of the four CLIs first, or pass `--platform=<name>` explicitly to install the hook anyway (it will print a non-fatal warning on every commit until the matching CLI appears on PATH).

4. **Locate the hook source.** All four hook scripts ship under:

    - Linux/macOS: `$HOME/.nexus-hub/hooks/<platform>-diff-review.sh`
    - Windows: `$env:USERPROFILE\.nexus-hub\hooks\<platform>-diff-review.sh`

    Where `<platform>` is one of `claude`, `gemini`, `codex`, `opencode` (the platform selected in step 3). If absent, stop and tell the user to run the Nexus-Hub installer first.

5. **Detect existing pre-commit hook.** Read `.git/hooks/pre-commit` (relative to the repo root returned by `git rev-parse --show-toplevel`).

    - **If the file does not exist**: skip to step 6.
    - **If the file exists AND `--force` was passed**: write a backup to `.git/hooks/pre-commit.nexus-backup-<timestamp>` and continue.
    - **If the file exists AND contains the line `# claude-diff-review.sh`, `# gemini-diff-review.sh`, `# codex-diff-review.sh`, or `# opencode-diff-review.sh`** (the marker comment from a Nexus-Hub hook): tell the user that a Nexus-Hub hook is already installed (and which platform), and ask whether to replace it with the newly selected platform's hook or abort.
    - **If the file exists AND does NOT contain any Nexus-Hub marker**: this is a third-party / user-authored pre-commit hook. Show the first ~30 lines of the existing file to the user, then ask which option they want:
        1. **Replace** the existing hook with the Nexus-Hub hook. Back up the original to `.git/hooks/pre-commit.nexus-backup-<timestamp>` first.
        2. **Abort** (do nothing).
        3. **Chain manually**: do not modify the file; print instructions for the user to edit it themselves so the existing hook runs, then the Nexus-Hub hook runs (or vice versa). Sample wrapper provided in the Manual Chaining section below.

        Wait for explicit user choice before proceeding. Never overwrite a non-Nexus-Hub pre-commit hook silently.

6. **Install the hook.** Copy the chosen platform's hook source to `.git/hooks/pre-commit` and make it executable:

    ```bash
    cp "$HOME/.nexus-hub/hooks/<platform>-diff-review.sh" .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
    ```

    PowerShell equivalent:

    ```powershell
    Copy-Item "$env:USERPROFILE\.nexus-hub\hooks\<platform>-diff-review.sh" -Destination ".git\hooks\pre-commit" -Force
    # Git for Windows runs hooks via its bundled bash; no chmod equivalent needed.
    ```

    Substitute `<platform>` with the platform name selected in step 3.

7. **Smoke-test the hook.** Run `bash .git/hooks/pre-commit </dev/null` and confirm exit code 0 (no staged diff = no review). If the hook errors, troubleshoot before declaring success.

8. **Print usage and bypass paths.** Tell the user exactly:

    ```text
    Pre-commit hook installed (platform: <platform>).

    What it does:
        Pipes `git diff --cached` through the <platform> CLI on every `git commit`.
        Looks for: hardcoded secrets, console.logs / print / debugger statements,
        unfinished TODOs, and large blocks of commented-out code.
        Verdict BLOCK (clear credentials) refuses the commit with exit code 1.
        Verdict WARN (debug / TODO) prints findings but allows the commit.
        Verdict PASS or any error: silent allow (fail-open).

    Per-commit bypass:
        NEXUS_DIFF_REVIEW_DISABLE=1 git commit -m "..."
        git commit -n -m "..."     (--no-verify; skips ALL pre-commit hooks)

    Diff-size cap (default 50 KB; raise to allow larger commits):
        NEXUS_DIFF_REVIEW_MAX_BYTES=204800 git commit -m "..."

    Switch to a different platform:
        rm .git/hooks/pre-commit
        /install-pre-commit-review-hook --platform=<other-platform>

    Disable for this repo:
        rm .git/hooks/pre-commit
    ```

## Manual chaining wrapper (for step 5 option 3)

If the user chose "chain manually" because they have a pre-existing pre-commit hook, give them this wrapper to save as `.git/hooks/pre-commit` (substituting `<platform>` for the chosen one):

```bash
#!/usr/bin/env bash
# Combined pre-commit: existing hook, then Nexus-Hub diff-review.
set -e

# Run the original hook (rename it first to .git/hooks/pre-commit.original).
if [ -x ".git/hooks/pre-commit.original" ]; then
    .git/hooks/pre-commit.original
fi

# Then run the Nexus-Hub review hook for the chosen platform.
"$HOME/.nexus-hub/hooks/<platform>-diff-review.sh"
```

## Verification

- [ ] `.git/hooks/pre-commit` exists in the target repository.
- [ ] The file is executable on Linux/macOS (`stat -c '%a' .git/hooks/pre-commit` shows at least `755`); Git for Windows ignores POSIX permissions.
- [ ] `bash .git/hooks/pre-commit </dev/null` exits 0.
- [ ] The first few lines of the installed hook contain a marker comment of the form `# <platform>-diff-review.sh - opt-in git pre-commit hook (Nexus-Hub).` (so a future re-run of this command can detect the platform and offer to switch / re-install cleanly).
- [ ] If a non-Nexus-Hub pre-commit hook existed, a backup file `.git/hooks/pre-commit.nexus-backup-<timestamp>` exists in the same directory.

## Why per-platform hooks instead of one CLI-detecting hook?

Two reasons. First, **independence:** a Gemini user should not be forced to install Claude CLI (or vice versa) just to get pre-commit review. Each hook script depends on exactly one CLI binary and prints a clear non-fatal warning if that binary is missing. Second, **predictability:** which CLI runs at commit time is a security-relevant choice (different vendors, different data-handling policies, different on-call rotations). Pinning the platform at install time makes the choice explicit and visible in the hook's marker comment, rather than implicit and dependent on whatever happens to be on PATH today.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I already have `secret-scan.sh` as a Claude Code PreToolUse hook, so this is redundant." | `secret-scan.sh` only fires when **Claude Code itself** writes a file; it sees nothing when the same repo is edited via Cursor, Copilot, the terminal, or a teammate's machine. The git pre-commit hook fires on every `git commit` regardless of who or what authored the change, so the two layers cover disjoint surfaces. |
| "I'll install hooks for all four platforms so they all get reviewed." | Git pre-commit allows only one `.git/hooks/pre-commit` file. Installing multiple Nexus-Hub hook variants in the same repo is not supported by this command. If you genuinely want multi-platform review, chain them manually using the wrapper script above. |
| "The hook will block my commit during a merge / rebase, breaking my workflow." | All four hook variants explicitly skip when `MERGE_HEAD`, `CHERRY_PICK_HEAD`, `REBASE_HEAD`, or any rebase state directory exists. Merge / cherry-pick / rebase commits are never reviewed; only author-curated commits are. |
| "Every commit will now cost API tokens regardless of which CLI I picked." | The default 50 KB diff cap means the hook skips with a warning on truly large diffs (the most token-expensive case). For typical commits (~5-15 KB of diff), the per-commit token cost is roughly 3-8k input + ~200 output tokens with whichever provider you selected. Adjust `NEXUS_DIFF_REVIEW_MAX_BYTES` to control this. |

## Related Skills and Commands

- `secret-scan.sh` (Claude Code PreToolUse hook, ships installed) — regex-based secret detection at write-time. Complementary to this command for Claude Code users.
- `pre-commit-checklist` skill — broader pre-commit setup including linting, formatting, and tests.
- `code-commit-workflow` skill — conventional-commit message format and atomic-commit guidance.
