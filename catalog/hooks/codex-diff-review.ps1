# codex-diff-review.ps1 - opt-in git pre-commit hook (Nexus-Hub).
# Pipes the staged diff through `codex -p` (OpenAI Codex CLI) for an LLM
# review of hardcoded secrets, debug artifacts, unfinished TODOs, and large
# commented-out code blocks.
#
# Independent of the Claude / Gemini / OpenCode variants - calls the Codex CLI only.
#
# PowerShell parity for codex-diff-review.sh: same bypass paths, same diff cap,
# same prompt, same PASS / WARN / BLOCK contract and exit codes.
#
# Install (PowerShell):
#   /install-pre-commit-review-hook --platform=codex
#
# Per-commit bypass:
#   $env:NEXUS_DIFF_REVIEW_DISABLE=1; git commit -m "..."
#   git commit -n -m "..."   (--no-verify; skips ALL pre-commit hooks)
#
# Diff-size cap (default 50 KB, raise to allow larger commits):
#   $env:NEXUS_DIFF_REVIEW_MAX_BYTES=204800; git commit -m "..."

$ErrorActionPreference = "Continue"

# --- Bypass paths --------------------------------------------------------
if ($env:NEXUS_DIFF_REVIEW_DISABLE -eq "1") {
    exit 0
}

# Skip during merge / cherry-pick / rebase: the staged diff is not author-curated
# and re-reviewing inherited code would block legitimate merges.
$gitDir = (git rev-parse --git-dir 2>$null)
if ($gitDir) {
    $mergeMarkers = @(
        (Join-Path $gitDir "MERGE_HEAD"),
        (Join-Path $gitDir "CHERRY_PICK_HEAD"),
        (Join-Path $gitDir "REBASE_HEAD")
    )
    foreach ($marker in $mergeMarkers) {
        if (Test-Path $marker) { exit 0 }
    }
    if ((Test-Path (Join-Path $gitDir "rebase-merge")) -or (Test-Path (Join-Path $gitDir "rebase-apply"))) {
        exit 0
    }
}

# --- Locate codex CLI ---------------------------------------------------
$cliCmd = Get-Command codex -ErrorAction SilentlyContinue
if (-not $cliCmd) {
    Write-Host "[codex-diff-review] WARNING: codex CLI not found on PATH; skipping review." -ForegroundColor Yellow
    Write-Host "[codex-diff-review] Install OpenAI Codex CLI (https://github.com/openai/codex) or set NEXUS_DIFF_REVIEW_DISABLE=1 to silence this warning." -ForegroundColor Yellow
    exit 0
}

# --- Get staged diff -----------------------------------------------------
$diff = (git diff --cached --no-color 2>$null)
if ([string]::IsNullOrEmpty($diff)) {
    exit 0
}

# --- Cap diff size -------------------------------------------------------
$maxBytes = if ($env:NEXUS_DIFF_REVIEW_MAX_BYTES) { [int]$env:NEXUS_DIFF_REVIEW_MAX_BYTES } else { 51200 }
$diffBytes = [System.Text.Encoding]::UTF8.GetByteCount($diff)
if ($diffBytes -gt $maxBytes) {
    Write-Host "[codex-diff-review] WARNING: staged diff is $diffBytes bytes (cap=$maxBytes); skipping review." -ForegroundColor Yellow
    Write-Host "[codex-diff-review] Raise the cap with `$env:NEXUS_DIFF_REVIEW_MAX_BYTES=N or commit fewer files at a time." -ForegroundColor Yellow
    exit 0
}

# --- Build review prompt -------------------------------------------------
$prompt = @'
You are a strict pre-commit reviewer for a staged git diff. Inspect ONLY the lines added in this diff (lines starting with `+` excluding the `+++` file headers). Look for:

1. Hardcoded credentials: API keys, tokens, passwords, private keys, connection strings with embedded secrets. Any value that looks credential-shaped on a literal assignment.
2. Debug artifacts that look unintentional in production code: console.log / console.debug / console.error, print() / println() / fmt.Println, debugger;, alert(), pdb.set_trace, dd() / dump() / var_dump.
3. Unfinished work newly added in this diff: TODO / FIXME / XXX / HACK comments without ticket references or owner, AND bare placeholder values like "todo", "fixme", "tbd", "xxx", "lorem ipsum".
4. Commented-out code blocks larger than 3 contiguous lines.

Respond on the FIRST LINE in EXACTLY this format and nothing else:

VERDICT: PASS

or

VERDICT: WARN

or

VERDICT: BLOCK

Then a blank line, then concise findings under 200 words. Use file:line references where possible.

Use BLOCK only for clear hardcoded credentials. Use WARN for debug artifacts, unfinished TODOs, or large commented-out blocks. Use PASS otherwise.

Default to PASS for: documentation-only diffs, lockfiles (package-lock.json, poetry.lock, go.sum), generated code, test fixtures with obvious dummy values ("password123", "test@example.com"), and config templates that explicitly mark placeholder values ("REPLACE_ME", "<your-key-here>").

Diff follows:

'@

# --- Run codex (fail-open on any error) ------------------------------------
$response = $null
try {
    $response = $diff | codex -p $prompt 2>$null
} catch {
    $response = $null
}
if ([string]::IsNullOrWhiteSpace($response)) {
    Write-Host "[codex-diff-review] WARNING: codex CLI returned no output; allowing commit." -ForegroundColor Yellow
    exit 0
}

# --- Parse verdict -------------------------------------------------------
$verdictLine = ($response -split "`n" | Where-Object { $_ -match '^VERDICT:' } | Select-Object -First 1)
$verdict = if ($verdictLine) { ($verdictLine -replace '^VERDICT:\s*', '').Trim() } else { "" }

switch ($verdict) {
    "PASS" {
        exit 0
    }
    "WARN" {
        Write-Host "[codex-diff-review] WARN:" -ForegroundColor Yellow
        $response -split "`n" | Select-Object -Skip 1 | ForEach-Object { Write-Host $_ }
        Write-Host ""
        Write-Host "[codex-diff-review] Commit allowed; review the warnings above and consider amending." -ForegroundColor Yellow
        exit 0
    }
    "BLOCK" {
        Write-Host "[codex-diff-review] BLOCK:" -ForegroundColor Red
        $response -split "`n" | Select-Object -Skip 1 | ForEach-Object { Write-Host $_ }
        Write-Host ""
        Write-Host "[codex-diff-review] Commit refused. Fix the issue, or bypass this commit with: `$env:NEXUS_DIFF_REVIEW_DISABLE=1; git commit ..." -ForegroundColor Red
        exit 1
    }
    default {
        Write-Host "[codex-diff-review] WARNING: unparseable verdict from codex (expected PASS|WARN|BLOCK); allowing commit." -ForegroundColor Yellow
        exit 0
    }
}
