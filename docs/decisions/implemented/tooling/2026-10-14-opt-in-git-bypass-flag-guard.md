# Decision: Opt-in git bypass-flag guard

Status: implemented - an opt-in mode of `git-guardrails` blocks the flags that skip git hooks or commit signing, switched by `~/.nexus-hub/guardrails.json` with no restart, and the hook now also runs for the PowerShell tool. It is defense-in-depth with documented limits, not a security boundary.

Hook maintainers and teams that want git hooks and commit signing enforced on agent-run git commands use this record. It fixes the switch, the exhaustive table of blocked and allowed forms, the stripping and scanning rules, the limits, and the PowerShell-tool registration that the `git-guardrails.sh` and `git-guardrails.ps1` tests are generated from.

**Date**: 2026-10-14. **Source decision**: maintainer choice of the opt-in option and approval of the PowerShell-tool registration under the AGENTS.md ask-first rule for hook logic, both on 2026-10-14. **Plan**: `docs/releases/v4/v4.14/plans/v4.14.4-adoption-gate-outcomes-and-opt-in-git-guard.md`.

## Problem

Nothing stops an agent from passing `--no-verify`, `-n`, or `--no-gpg-sign` to git. A team that relies on pre-commit hooks or signed commits has the rule only as an instruction, and an instruction is the thing a long session forgets. Separately, `git-guardrails` is registered only for the Bash tool in `catalog/hooks/settings.json`, so on a host where the agent runs git through the PowerShell tool every existing block (force push, hard reset, `core.hooksPath` redirection, and the rest) is skipped.

A hook built from regular expressions over the raw command string cannot decide every spelling of a bypass. A first draft of this design claimed more than that kind of hook can deliver. The design below states what it matches, what it does not, and who can switch it off.

## Decision

**Mode.** A dedicated block runs after every existing block (the pattern loop, the persistent execution-indirection check, and the protected-branch guard). It is not added to `DANGEROUS_PATTERNS`, whose message says the user has prevented the command outright. The pattern-list blocks run first and are unchanged, so the new mode never weakens an existing block.

**Switch.** The mode is inert unless `~/.nexus-hub/guardrails.json` is a JSON object with `"block_git_bypass_flags": true` (the JSON boolean; the string `"true"` is off). The file is read on every hook run, so editing it takes effect on the next command with no restart. `NEXUS_GUARD_GIT_BYPASS=1` forces the mode on and `NEXUS_GUARD_GIT_BYPASS=0` forces it off; any other value, including unset, defers to the file. The home directory is `HOME`, then `USERPROFILE`. Both the file and the variable are read only from the hook process's own files and environment, never parsed from the command text, so `NEXUS_GUARD_GIT_BYPASS=0 git commit --no-verify` typed in a command does not switch the mode off, and typing `=1` does not switch it on.

**Failure behavior.** A missing file means off. A malformed file (not valid JSON, not an object, or empty) means off with one warning on stderr naming the file; it never crashes the hook, because a crash would block every command. A payload with no command keeps exit 0. The `.ps1` reads the file with `ConvertFrom-Json`. The `.sh` validates the file with `jq` when present, otherwise with a Python JSON parse, and only when neither yields a verdict (no interpreter, or one that is not a working Python, such as the Windows Store `python3` stub that prints an install message and exits non-zero) does it grep for the key. Every malformed file leaves the mode off; the malformed-file warning is best effort only on that last path (it catches a file that does not start with `{` or end with `}`).

**What is matched.** The hook works on a copy of the command text:

1. Heredoc bodies are stripped, except a body whose opener line names an interpreter (`bash`, `sh`, `zsh`, `pwsh`, `powershell`, `python`), which is kept and scanned as command text. A body that only writes a file (`cat > notes.md <<'EOF'`) is stripped.
2. Quoted values of `-m`, `--message`, `-F`, and `--file` (also attached to a short cluster such as `-am "text"`) are replaced by an empty string, so a commit message that mentions a flag is not a flag.
3. Line continuations (backslash or backtick before a newline) are joined, then the text is split into segments at `;`, `|`, `&`, and newlines.
4. Each segment is matched for a `git` word (optionally with a path prefix or `.exe`), then git global options (`-C <path>`, `-c <key=value>`, `--git-dir`, `--work-tree`, `--namespace`, `--exec-path`, `--super-prefix`, `--config-env`, `--no-pager`, `--paginate`, `--bare`, `-p`, `-P`, and the other documented global switches), then the subcommand, then the flag.
5. `--no-verify` is matched as any prefix of the option from `--no-v` up (git accepts unique abbreviations), `--no-gpg-sign` from `--no-g` up. The `-n` scan walks a short-option cluster left to right and stops at an option that takes an argument (`m`, `F`, `C`, `c`, `t`, `u`, `S`), so `-mn` (message `n`) and `-uno` (untracked-files mode `no`) are not `-n`. Config keys match in any letter case, as git does.

**Blocked when on.**

| Form | Examples |
|---|---|
| `--no-verify` (or a prefix from `--no-v`) on `commit`, `push`, `merge`, `rebase`, `am` | `git commit --no-verify`, `git commit -m x --no-verify`, `git push --no-verify origin main`, `git merge --no-verify topic`, `git rebase --no-verify main`, `git am --no-verify x.patch`, `git commit --no-verif -m x` |
| `-n` as a `git commit` option, alone or inside a cluster before any argument-taking letter | `git commit -n -m x`, `git commit -an -m x`, `git commit -nm x`, `git commit -sn` |
| `--no-gpg-sign` (or a prefix from `--no-g`) on `commit`, `merge`, `rebase`, `cherry-pick`, `revert` | `git commit --no-gpg-sign`, `git merge --no-gpg-sign topic`, `git cherry-pick --no-gpg-sign abc123` |
| Inline `-c commit.gpgsign=<false-like>` (and `tag.gpgsign`) on any git command; false-like is `false`, `no`, `off`, `0`, or empty, in any letter case | `git -c commit.gpgsign=false commit -m x`, `git -c COMMIT.GPGSIGN=FALSE commit -m x` |
| Persistent `git config [--global\|--local\|--system\|--worktree\|-f <file>] commit.gpgsign\|tag.gpgsign <false-like>` | `git config commit.gpgsign false`, `git config --global tag.gpgsign no`, `git config --global --replace-all Commit.GpgSign 0` |
| Any of the above with git global options before the subcommand, a path prefix, or `.exe` | `git -C repo commit -n`, `git --no-pager commit --no-verify`, `git -c core.pager=cat -C repo commit -n`, `/usr/bin/git commit -n`, `git.exe commit -n` |
| Any of the above after a separator | `git add . && git commit -n -m x` |
| Any of the above inside a heredoc fed to an interpreter | `bash <<'EOF'` with `git commit --no-verify` in the body |

**Allowed when on.**

| Form | Why |
|---|---|
| `git push -n origin main` | `-n` is dry run on push |
| `git log -n 5`, `git tag -n`, `git diff -n` | `-n` on a command other than `commit` |
| `git commit --no-edit`, `git commit --amend --no-edit` | `--no-edit` is not a bypass flag |
| `git commit -m "explain --no-verify and -n"` | the message value is stripped before matching |
| `git commit -mn` | `-m` takes the argument `n` |
| `git commit -uno -m x` | `-u` takes the argument `no` |
| `git commit -S -m x`, `git commit -am x`, `git commit -m x` | no bypass flag |
| `git config commit.gpgsign true`, `git config --get commit.gpgsign`, `git -c commit.gpgsign=true commit -m x` | the key is not set to a false-like value |
| `cat > notes.md <<'EOF'` with `--no-verify` in the body | a heredoc body that writes a file is stripped |

**Case-insensitive `core` keys (nice to have).** The existing `core.hooksPath` and `core.fsmonitor` checks, inline and persistent, now match the key in any letter case, because git reads config keys case-insensitively.

**Limits (stated in this record and in both hook headers).**

| Limit | Why it stays open |
|---|---|
| Environment-variable skips: `HUSKY=0`, `SKIP=`, `LEFTHOOK=0`, and `GIT_CONFIG_*` | They change hook or git behavior without a flag on the command |
| Git plumbing: `commit-tree`, `update-ref`, `hash-object` | They create commits and refs without running the hooks the guard protects |
| Shell aliases, wrapper scripts, and git aliases | The flag is not on the command line the hook sees |
| `bypassPermissions` mode | The existing hook contract steps aside entirely in full-access mode |
| An agent that edits `~/.nexus-hub/guardrails.json` or the hook itself | The switch lives in a file the agent may be able to write |
| A flag built at run time (variables, command substitution, `eval`), quoted as a separate word, or passed to a program that runs git later (`xargs`, `python -c`) | The hook matches text, not the argument vector git receives |
| `git config --unset commit.gpgsign` | It removes signing without setting a false-like value |
| A subtly malformed `guardrails.json` in the `.sh` with neither `jq` nor a working Python | The warning is best effort without a JSON parser; the mode still stays off |

**PowerShell-tool registration.** `catalog/hooks/settings.json` registers `git-guardrails` once for the `Bash|PowerShell` matcher, the same single-entry form the console-window guard already uses. A tool call is one tool, so the hook runs once per call. The command stays `bash .claude/hooks/git-guardrails.sh`, the invocation the existing PowerShell-tool hooks (`require-powershell-description.sh`) already use. The hook reads `tool_input.command` the same way for both tools. That registration is a protected-path edit, so it was delivered as a reviewed patch separate from the hook and test changes.

**Command extraction without jq.** The `.sh` extracted the command with a pattern that stopped at the first escaped double quote when `jq` was absent, so everything after any quoted text went unscanned, for the existing blocks as well. The extraction now accepts escaped characters inside the string. A regression test sends a destructive command after quoted text through both implementations.

**Status of the guard.** The guard is defense-in-depth, not a boundary. An agent able to write `guardrails.json` can switch it off, and the limits above stay open.

## Alternatives considered

- **Block by default with a session-wide override.** Rejected on 2026-10-14: a default block changes behavior for every installed user on upgrade, and the protected-branch guard already set the precedent that this class of check is off until a team opts in.
- **Warn only.** Rejected: an agent that has already decided to pass `--no-verify` reads a warning as information, and the hook would then report the bypass after the fact.
- **Opt-in block (chosen).** Teams that want hooks and signing enforced switch it on; everyone else sees no change.
- **Drop the idea.** Rejected: the rule exists today only as an instruction, and the cost of the opt-in mode is one dedicated block in two files.
- **Switch by environment variable alone.** Rejected: a variable set in a settings file needs a restart and is invisible to a reviewer, while a JSON file read on every run changes the next command and is easy to inspect.
- **Register the PowerShell tool as a second entry.** Rejected: two entries for one hook invite a double run and drift. One `Bash|PowerShell` matcher keeps one registration per tool.
- **Parse the command into an argument vector in both languages.** Rejected for now: a tokenizer written twice (bash and PowerShell) is a larger parity surface than the regular expressions it would replace, and the documented limits already say what a text match cannot see.

## Consequences

The following hold, and `catalog/hooks/tests/test_git_guardrails.py` proves them on both implementations:

- With no `guardrails.json`, `git commit -m x --no-verify` exits 0 in both implementations.
- After `{"block_git_bypass_flags": true}` is written to a temporary home, the same command exits 2 and the very next command is judged by the file as it is then.
- Every blocked form in the table exits 2 with the mode on and 0 with it off; every allowed form exits 0 with it on.
- `NEXUS_GUARD_GIT_BYPASS` in the hook's environment wins over the file; the same text in the command does not.
- A malformed file leaves the mode off and prints one warning naming the file.
- A PowerShell-tool payload for `git push --force` exits 2.
- `catalog/hooks/tests/test_git_guardrails.py` proves identical exit codes from `git-guardrails.sh` and `git-guardrails.ps1` for each case above.

**Costs and risks.**

- A regular expression that matches too much blocks legitimate work. The allowed table and the message-stripping rule exist to bound this, and the mode is opt-in.
- A regular expression that matches too little lets a bypass through. The limits table says so, and no claim of enforcement is made.
- The two implementations can drift. The parity fixture runs every case through both.
- Registering the hook for another tool changes behavior for every installed user on the next install; the mode that adds new blocking stays off until opted in, and the existing blocks now apply to PowerShell by design.
