# Permission Matcher Findings (Phase 1.1)

**Plan**: [v3.17.0-agent-autonomy-toggle](../plans/v3.17.0-agent-autonomy-toggle.md), Phase 1, sub-task 1.1
**Date**: 2026-08-12
**Source**: Claude Code official permissions documentation, `https://code.claude.com/docs/en/permissions` (fetched 2026-08-12)
**Purpose**: Record the two empirical questions sub-task 1.1 requires answering before the read-only baseline can be hardened, plus the matcher behaviors that changed the shape of the fix.

## Why this document exists

Two independent auto-approve paths consume `configs/permissions/claude-permissions.json`:

- **Path one (unguarded)**: Claude Code's own native matcher reading the merged `settings.json`. No Nexus-Hub logic applies.
- **Path two (guarded)**: Nexus-Hub's `PreToolUse` hooks, `catalog/hooks/format-bash-description.py` and `catalog/hooks/format-powershell-description.py`, which return `permissionDecision: "allow"` only after applying guards the native matcher does not have.

Sub-task 1.1 hardens for path one. A pattern defended only by a path-two hook is defended only as strongly as Phase 4.1's hook-survival verification turns out, so hook guards are not treated here as a reason to retain a mutation-capable pattern.

## Finding 1: compound-command splitting - VERIFIED (MATCH)

**Question**: does the native matcher split a `;` chain the way it splits `&&` and `|`, so that `Get-ChildItem; Remove-Item x` cannot reach a bare `PowerShell(Get-ChildItem *)` pattern?

**Verdict**: VERIFIED. The matcher splits on every separator and requires each subcommand to match independently, for both shells.

Bash, quoted verbatim from the source:

> Claude Code is aware of shell operators, so a rule like `Bash(safe-cmd *)` won't give it permission to run the command `safe-cmd && other-cmd`. The recognized command separators are `&&`, `||`, `;`, `|`, `|&`, `&`, and newlines. A rule must match each subcommand independently.

PowerShell, quoted verbatim:

> Claude Code parses the PowerShell AST and checks each command in a compound command independently. Pipeline operators `|`, statement separators `;`, and on PowerShell 7+ the chain operators `&&` and `||` split a compound command into subcommands. A rule must match every subcommand for the compound command to be allowed.

**Consequence**: the `;`-chain escape is closed on the native path for both shells. `format-powershell-description.py` rejecting `;` outright is stricter than the native matcher, not a compensation for it. The two layers do not disagree; the hook is simply more conservative.

## Finding 2: output redirection - UNVERIFIED (documented silence), treated conservatively

**Question**: does a redirected command such as `echo pwned > ~/.bashrc` still match a bare `Bash(echo *)` allow rule?

**Verdict**: UNVERIFIED for explicit allow rules. Per this plan's evidence discipline, absence of evidence is recorded as UNVERIFIED rather than as absence of the behavior.

What the documentation does establish:

- Redirection operators are **not** in the enumerated separator list (`&&`, `||`, `;`, `|`, `|&`, `&`, newlines), so a redirected command is one subcommand, not two.
- A wildcard "matches any sequence of characters including spaces", so `Bash(echo *)` textually admits `echo pwned > ~/.bashrc`.
- The parser demonstrably **does** model redirects, but this is stated only for the built-in read-only command set, not for explicit allow rules. Quoted verbatim:

  > **`cd` with an output redirect**: prompts when Claude Code can't determine which directory the redirect target resolves against after the `cd` runs. A command whose only redirect target is `/dev/null`, such as `cd app; grep -r pattern . 2>/dev/null`, doesn't prompt, because `/dev/null` doesn't depend on the working directory.

- No statement exists either way about redirects under an explicit `allow` rule.

**Why this finding is load-bearing and why it is not fixed per-entry**: `> file` truncates its target regardless of what the command itself emits. `Write-Host x > f` writes nothing to the file and still truncates it. If the native matcher admits redirects under allow rules, then *every* pattern in the baseline carrying a trailing wildcard is a file-destruction primitive, and no per-entry rescoping repairs that. Redirect-admission is a global property of the matcher, not a defect of any individual entry.

The response is therefore split three ways:

1. Record the question here as the open, load-bearing item (this section).
2. Have `scripts/validate_permission_baseline.py` detect the checkable thing: a literal redirection operator appearing inside a pattern.
3. Harden per-entry against the checkable classes (mutating flags and subcommands), which do not depend on the answer.

**Suggested next step**: resolve empirically against a real Claude Code build by adding a single `Bash(echo *)` allow rule to a throwaway project config and observing whether `echo x > /tmp/probe` prompts. Tracked as a Phase 6.2 known-gaps item.

## Finding 3: the built-in read-only set (not asked for, changed the fix)

Claude Code auto-approves a built-in, non-configurable set of read-only Bash commands in every mode, with real semantic analysis rather than glob matching. Quoted verbatim:

> Claude Code recognizes a built-in set of Bash commands as read-only and runs them without a permission prompt in every mode. These include `ls`, `cat`, `echo`, `pwd`, `head`, `tail`, `grep`, `find`, `wc`, `which`, `diff`, `stat`, `du`, `cd`, and read-only forms of `git`.

That analysis is strictly better than a glob. It already prompts on the dangerous forms:

> **Unquoted globs for commands with write-capable flags**: commands with write-capable or exec-capable flags, such as `find`, `sort`, `sed`, and `git`, prompt when an unquoted glob is present, because the glob could expand to a flag like `-delete`.

> Exec wrappers such as `watch`, `setsid`, `ionice`, and `flock` always prompt and can't be auto-approved by a prefix rule like `Bash(watch *)`. The same applies to `find` with `-exec` or `-delete`: a `Bash(find *)` rule doesn't cover these forms.

**Consequence**: a Nexus-Hub glob entry for a command already in the built-in set is redundant for the safe forms and serves only to *widen* the approval beyond what the built-in analysis would grant. Removing such an entry is coverage-neutral and security-positive. This is the reasoning behind the Tier B removals in the hardening table, and it is a better fix than attempting to out-glob the parser.

## Finding 4: PowerShell alias canonicalization

Quoted verbatim:

> Common aliases are canonicalized before matching. A rule written for the cmdlet name also matches its aliases, so `PowerShell(Get-ChildItem *)` matches `gci`, `ls`, and `dir` as well. Matching is case-insensitive.

**Consequences**:

- The roughly twenty alias entries in the PowerShell block (`gci`, `gc`, `gi`, `gl`, `gm`, `gcm`, `gv`, `gps`, `gsv`, `sls`, `select`, `sort`, `group`, `measure`, `ls`, `dir`, `cat`, `type`, `pwd`, `cd`) are redundant with their cmdlet entries. They are **retained** rather than removed: canonicalization coverage may vary by Claude Code version, and removing them would risk reducing coverage, which sub-task 1.1 explicitly forbids. This is recorded as an observation only.
- `scripts/validate_permission_baseline.py` **must** canonicalize aliases before checking its denylist. A cmdlet-name-only denylist would let `PowerShell(sc *)` (alias of `Set-Content`) and `PowerShell(iex *)` (alias of `Invoke-Expression`) slip through. The validator's alias table exists for this reason.

## Finding 5: wrapper stripping and environment assignments

Quoted verbatim:

> Before matching Bash rules, Claude Code strips a fixed set of wrappers, so a rule like `Bash(npm test *)` also matches `timeout 30 npm test`. The stripped wrappers are `timeout`, `time`, `nice`, `nohup`, and `stdbuf`, plus the shell builtins `command` and `builtin`, and zsh's `noglob`.

> Bare `xargs` is also stripped, so `Bash(grep *)` matches `xargs grep pattern`. Stripping applies only when `xargs` has no flags.

**Consequences**:

- The explicit `Bash(xargs grep *)`-style entries are redundant with bare-`xargs` stripping, but are retained on the same version-safety reasoning as the PowerShell aliases.
- Environment runners are explicitly **not** stripped, and the documentation warns that `Bash(devbox run *)` would match `devbox run rm -rf .`. No such entry exists in the current baseline; the validator treats this class as a curated dual-mode list so a future addition is caught.

## Handoff to sub-task 5.3

`configs/permissions/gemini-permissions.json` ships no PowerShell or `cmd.exe` read-only set at all, so a Windows Gemini user receives a POSIX-shaped allowlist. Sub-task 1.1 rescopes existing entries and deliberately does not expand coverage, so this is recorded here and handed to sub-task 5.3 for documentation in `docs/permissions-research.md`.
