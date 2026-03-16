---
description: Audit the codebase against its .gitignore, identify wrongly-tracked files and missing patterns, clean up the git index, and recommend Git LFS for large binaries — then apply every fix after explicit user confirmation.
---

# Update .gitignore

Audit the repository's `.gitignore` against the actual codebase, identify tracked files that should not be in git, propose new ignore patterns tailored to the detected tech stack, optionally remove files from the git index without deleting them from disk, and recommend Git LFS for large binary assets.

This command is safe-first: it never modifies `.gitignore`, runs `git rm --cached`, or initializes LFS until the user explicitly approves the plan in Phase 8.

## Platform Invocation

| Platform | How to Invoke |
|----------|---------------|
| **Claude Code** | `/update-gitignore` |
| **Codex / Cursor / Aider** | "Audit and update .gitignore, remove wrongly-tracked files, and recommend LFS" |
| **Gemini CLI** | "Run the update-gitignore workflow to clean up git tracking for this repo" |
| **GitHub Copilot** | `#file:.claude/commands/update-gitignore.md` then: "Follow this workflow to audit and fix .gitignore" |

---

## Flags

| Flag | Behavior |
|------|----------|
| *(none)* | Analyze and write report only; never modify anything |
| `--fix` | After user confirms the plan, apply all changes |
| `--dry-run` | Explicit alias for the default (no modifications) |
| `--output <path>` | Write the report to this path. Default: `docs/git/gitignore-audit-<YYYY-MM-DD>.md` |
| `--scope <path>` | Restrict all analysis to the specified subdirectory |
| `--no-lfs` | Skip Git LFS candidate analysis |
| `--history` | Also scan git commit history for secrets ever committed (slow; opt-in only) |

---

## Severity Classification

All findings use the G0–G3 scale throughout every phase.

| Level | Alias | Meaning | Required Action |
|-------|-------|---------|-----------------|
| G0 | CRITICAL | Secrets, credentials, private keys, or tokens currently tracked in git | Remove from index immediately; purge history |
| G1 | HIGH | Build artifacts, compiled binaries, generated outputs, or dependency dirs currently tracked | Remove from index; add pattern to `.gitignore` |
| G2 | MEDIUM | IDE config, OS metadata, log files, or temp dirs tracked or dangerously unignored | Add pattern to `.gitignore` |
| G3 | LOW | Large binary files better managed with Git LFS; `.gitattributes` optimizations | Recommend `git lfs track` or attribute fix |

---

## Pre-Analysis: Collect Before Writing

Complete all analysis phases before writing a single line to the report. Accumulate findings into an internal working set, then emit the report in one pass. This prevents early sections from contradicting later discoveries.

For each finding record:

- **ID**: sequential number (G-001, G-002, …)
- **Severity**: G0 / G1 / G2 / G3
- **Category**: Secret | Build Artifact | IDE | OS Metadata | LFS Candidate | Syntax Error | Missing Pattern
- **Location**: file path (if a tracked file) or `.gitignore` file and line (if a pattern issue)
- **Description**: what the problem is and why it matters
- **Recommended Action**: concrete fix (exact pattern or command)

**Always exclude from all analysis:**

- `node_modules/`, `vendor/`, `.venv/`, `dist/`, `build/`, `target/`, `out/`
- Generated files (headers: `// generated`, `# auto-generated`, `DO NOT EDIT`)
- Binary lock files (`package-lock.json`, `yarn.lock`, `poetry.lock`, `go.sum`, `Cargo.lock`)
- Test fixture files that contain deliberate vulnerable patterns for testing — flag these explicitly, do not treat as real findings

---

## Phase 0: Resolve Scope and Mode

Check whether the user provided any flags (look at the invocation or the preceding message):

- **`--scope <path>`**: Restrict all analysis to the specified path. Note the restriction in the report header.
- **`--output <path>`**: Write the audit report to this path. Default: `docs/git/gitignore-audit-<YYYY-MM-DD>.md` where the date is today's date.
- **`--fix`**: After writing the report, enter the confirmation loop and apply approved changes.
- **`--dry-run`**: Analyze and report only; skip Phase 8 and Phase 9 entirely.
- **`--no-lfs`**: Skip Phase 5.
- **`--history`**: Execute Phase 6 (git history scan).

Create the output directory if it does not exist.

---

## Phase 1: Codebase Fingerprinting

Detect languages, frameworks, package managers, and build tools by reading manifest and config files. Look for:

| Signal File | Detected Stack |
|-------------|---------------|
| `package.json`, `.nvmrc`, `.node-version` | Node.js / npm / yarn / pnpm |
| `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile`, `uv.lock` | Python |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `*.csproj`, `*.sln`, `global.json` | .NET / C# |
| `pom.xml`, `build.gradle`, `settings.gradle` | Java / Kotlin |
| `Gemfile` | Ruby |
| `composer.json` | PHP |
| `.github/workflows/`, `Jenkinsfile`, `azure-pipelines.yml`, `.circleci/` | CI/CD pipelines |
| `Dockerfile`, `docker-compose.yml` | Docker |
| `terraform.tf`, `*.tfvars` | Terraform / IaC |
| `*.xcodeproj`, `*.pbxproj` | Xcode / iOS / macOS |

From the detected stacks, build a tailored recommended pattern list. Generic patterns (OS metadata, common IDE files, credential files) apply to every project regardless of stack.

### Standard Recommended Patterns (All Projects)

```
# OS metadata
.DS_Store
Thumbs.db
desktop.ini
ehthumbs.db
$RECYCLE.BIN/

# IDE
.idea/
.vscode/
*.suo
*.user
*.userosscache
*.sln.docstates
.vs/
nbproject/
.project
.classpath
.settings/

# Secrets and credentials
.env
.env.*
!.env.example
!.env.sample
*.pem
*.key
*.p12
*.pfx
*.cer
secrets.json
credentials.json
*_rsa
*_dsa
*_ed25519
*_ecdsa

# Logs and temp
*.log
*.tmp
*.temp
*.swp
*.swo
*~
```

---

## Phase 2: Current `.gitignore` Audit

Read all `.gitignore` files found in the repository (root and any nested). For each file:

1. Parse every non-comment, non-blank line as a pattern.
2. Compare the full list against the recommended pattern set from Phase 1.
3. Identify: **Present** (already covered), **Gap** (recommended but missing), **Redundant** (duplicated entries), **Syntax Issue** (malformed pattern).

### Syntax Issues to Flag

- Pattern intended to ignore a directory but missing the trailing `/` (e.g., `node_modules` instead of `node_modules/`)
- Negation pattern (`!`) that can never match because the parent directory is already ignored
- Glob patterns with unescaped special characters
- Windows-style path separators (`\`) in patterns

---

## Phase 3: Tracked File Analysis (Index Scan)

Run `git ls-files` to list every file currently tracked by git. For each tracked file, evaluate:

### G0 — Secret Detection Patterns

Match against:

```
# Environment files
\.env$
\.env\..*

# Key files
\.(pem|key|p12|pfx|cer|crt|jks|keystore)$

# Common credential file names
(credentials|secrets|auth|token|api.?key|password)(s)?\.(json|yaml|yml|xml|ini|cfg|conf|toml)$

# Private key headers (check file content for first line)
-----BEGIN (RSA|EC|OPENSSH|PGP|DSA) PRIVATE KEY-----

# High-entropy strings assigned to key-like variable names
(?i)(api_key|apikey|api_secret|token|secret|password|passwd|pwd|credential)\s*[=:]\s*['"]?[A-Za-z0-9+/=_\-]{20,}
```

Also flag any file with a name or extension pattern that strongly implies credential content and is not already in `.gitignore`.

### G1 — Build Artifact and Dependency Patterns

| Stack | Patterns |
|-------|----------|
| Node.js | `node_modules/`, `dist/`, `build/`, `.next/`, `.nuxt/`, `.svelte-kit/`, `.turbo/`, `*.tsbuildinfo` |
| Python | `__pycache__/`, `*.pyc`, `*.pyo`, `.eggs/`, `*.egg-info/`, `dist/`, `build/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.venv/`, `venv/`, `env/` |
| Go | `vendor/` (if not intentionally committed), compiled binaries matching the module name |
| Rust | `target/` |
| .NET | `bin/`, `obj/`, `*.dll`, `*.exe` (non-intentional), `*.nupkg` |
| Java | `target/`, `*.class`, `*.jar` (generated), `.gradle/`, `build/` |
| General | `coverage/`, `.coverage`, `htmlcov/`, `*.lcov`, `.nyc_output/` |

### G2 — IDE and OS Metadata Patterns

Any file matching the standard recommended patterns from Phase 1 that is currently tracked.

### Size Threshold

Flag any tracked file larger than 5 MB for G3 review (LFS candidate).

---

## Phase 4: Untracked File Analysis

Run `git ls-files --others --exclude-standard` to list untracked files not yet covered by `.gitignore`. Identify files that:

- Match secret patterns (G0) — critical to ignore before they are accidentally committed
- Match build/dependency patterns (G1) — should be ignored to prevent accidental commits
- Match IDE/OS patterns (G2) — nice-to-have ignores

These do not require `git rm --cached` (they are not tracked) but do require new `.gitignore` entries.

---

## Phase 5: LFS Suitability Check (skip if `--no-lfs`)

Check whether Git LFS is available: `git lfs version`. If not available, note it in the report and skip LFS recommendations.

If LFS is available, read `.gitattributes` (if it exists) to identify already-tracked LFS patterns.

From all tracked and untracked files, flag candidates for LFS tracking:

**Binary types to check:**

```
Images / Design:    *.psd  *.ai  *.sketch  *.fig  *.xcf  *.tiff  *.tif  *.bmp
Video / Audio:      *.mp4  *.mov  *.avi  *.mkv  *.webm  *.mp3  *.wav  *.flac
Archives:           *.zip  *.tar.gz  *.tgz  *.tar.bz2  *.7z  *.rar
ML / Data:          *.pkl  *.pickle  *.bin  *.onnx  *.pt  *.pth  *.weights  *.h5  *.hdf5  *.parquet  *.arrow
Compiled:           *.so  *.dylib  *.dll  *.exe  *.wasm
Documents:          *.pdf  *.docx  *.xlsx  *.pptx
```

Flag any file of these types **or** any file over 5 MB as G3 with the recommended `git lfs track` command.

---

## Phase 6: History Scan — only with `--history`

Scan git commit history for secrets ever committed (even if later removed from the working tree).

Use `git log --all --full-history --diff-filter=A --name-only --format=` to find files ever added. Cross-reference against secret patterns from Phase 3. For any hit, use `git show <commit>:<path>` to sample content and confirm the finding.

All findings in this phase are G0.

**Important:** Even if a file was deleted from a later commit, the content remains in history. Flag these for history purge.

---

## Phase 7: Report Generation

Write the report to the output path determined in Phase 0. The report must include every section below.

```markdown
# .gitignore Audit — <project name> — <YYYY-MM-DD>

**Repository:** <root path>
**Scope:** <full repo | restricted to: path>
**Mode:** <report-only | --fix>
**History scan:** <yes | no>

---

## Summary

| Severity | Count |
|----------|-------|
| G0 CRITICAL | X |
| G1 HIGH | X |
| G2 MEDIUM | X |
| G3 LOW | X |
| **Total** | **X** |

Tracked files to remove from index: X
.gitignore entries to add: Y
LFS candidates: Z

---

## Findings

| ID | Severity | Category | Location | Description | Recommended Action |
|----|----------|----------|----------|-------------|-------------------|
| G-001 | G0 | Secret | config/secrets.json | Credential file tracked in git | git rm --cached; add to .gitignore |
| ... | ... | ... | ... | ... | ... |

---

## Proposed .gitignore Additions

```gitignore
# === Build Artifacts ===
dist/
build/
...

# === IDE and Editor Files ===
.idea/
...

# === OS Metadata ===
.DS_Store
...

# === Secrets (ensure these are never committed) ===
.env
.env.*
...
```

---

## Proposed `git rm --cached` Commands

```bash
# G0 — Secrets (remove immediately)
git rm --cached config/secrets.json

# G1 — Build artifacts
git rm --cached -r dist/
git rm --cached -r node_modules/
...
```

---

## LFS Recommendations

```bash
git lfs install   # (if not already initialized)
git lfs track "*.psd"
git lfs track "*.pkl"
...
```

After running these commands, commit the updated `.gitattributes`:
```bash
git add .gitattributes
git commit -m "chore: configure Git LFS tracking"
```

---

## Manual Steps Required

### History Purge (G0 findings in history)

The following files contain sensitive data in git history. Use `git filter-repo` to permanently
remove them. **This rewrites history and requires a force-push — coordinate with all collaborators
before running.**

```bash
pip install git-filter-repo  # (one-time install)
git filter-repo --path config/secrets.json --invert-paths
git push --force-with-lease origin <branch>
```

After purging history, revoke and rotate any exposed credentials immediately.

---

## .gitignore Syntax Fixes

[List any malformed patterns found in Phase 2 with corrected versions]
```

---

## Phase 8: Confirmation (only when `--fix` is active)

Present the full proposed change plan to the user. Do not apply any changes until the user explicitly approves.

```
## Proposed Changes

### 1. .gitignore updates (Y new entries)
   [Preview of new sections to be appended]

### 2. Files to remove from git index (X files)
   [List with severity and path]

### 3. LFS tracking to configure (Z types)
   [List of git lfs track commands]

### 4. Manual steps (not automated)
   [History purge commands if any G0 history findings]

Proceed?
1. Yes — apply all changes
2. Partial — let me select which changes to apply
3. No — cancel (report has already been written)
```

Wait for explicit user approval before proceeding to Phase 9.

---

## Phase 9: Execute (only after user confirms)

Apply changes in this order:

### 9a. Update `.gitignore`

Read the current root `.gitignore` (or create it if absent). Append new entries in clearly labeled, commented sections. Preserve all existing content. Log: `✓ Added N patterns to .gitignore`.

### 9b. Remove Tracked Files from Index

For each approved G0–G2 tracked file, run `git rm --cached <path>` (removes from index, keeps on disk). For G0 findings with history, output the `git filter-repo` command but do not run it — instruct the user to execute it manually after coordinating with collaborators. Log each removal: `✓ Removed from index: <path>`.

### 9c. Configure LFS (only if user confirmed)

For each approved G3 LFS candidate:

1. Run `git lfs track "<pattern>"` to update `.gitattributes`
2. Log: `✓ LFS tracking configured: <pattern>`

After all LFS tracks are set, prompt the user to commit `.gitattributes`:

```
.gitattributes has been updated. Run:
  git add .gitattributes
  git commit -m "chore: configure Git LFS tracking"
```

---

## Phase 10: Verify

Re-run all scans from Phases 3 and 4 against the updated state.

```
## Verification Results

Files removed from index:    X / X ✓
.gitignore patterns added:   Y / Y ✓
LFS patterns configured:     Z / Z ✓

G0 files still tracked:      0 ✓
G1 files still tracked:      0 ✓

git status: [clean / N unintended changes]
```

Report any discrepancies with their file paths. If `git status` shows unexpected modifications, list them and ask the user to review before proceeding.

---

## Phase: Iterative Refinement (Loop)

After verification, re-scan for tracked files still matching ignore patterns. Perform up to **3 iterations**:

1. **Analyze**: Are any G0 or G1 files still tracked?
2. **Refine**: If yes, apply targeted `git rm --cached` calls and `.gitignore` additions for the remaining hits.
3. **Stop**: When the index scan returns zero G0/G1 findings, or after 3 iterations.

After the final iteration, report any items that could not be auto-resolved and require manual attention.

---

## Edge Cases

### Secrets with History

Do not silently purge history. History rewriting with `git filter-repo` is destructive, requires a force-push, and will break collaborators' local clones unless they re-clone or reset. Always output the command and require the user to run it manually after rotating the exposed secret.

### Files Intentionally Tracked Despite Pattern Match

Some files match ignore patterns but are intentionally committed (e.g., an `.env.example` template). Before flagging a file, check whether:
- It is negated in `.gitignore` (e.g., `!.env.example`)
- Its filename clearly signals it is a safe template or sample

If uncertain, flag it as a finding but mark it as "Confirm intentional" rather than auto-removing it.

### Nested `.gitignore` Files

If the repository contains nested `.gitignore` files (e.g., `frontend/.gitignore`), process each one independently. Do not consolidate all patterns into the root `.gitignore` — respect the directory scoping of nested ignore files.

### Non-Git Repositories

If `git ls-files` fails (no git repository), stop immediately and report:

```
Error: No git repository found at <path>.
/update-gitignore requires a git-initialized project.
Run `git init` first if you want to set up git tracking.
```

### Large Repositories

If `git ls-files` returns more than 10,000 files, warn the user that analysis may take a moment and proceed. Do not truncate the scan.

### Monorepos

If the repository contains multiple packages under a single root (e.g., `packages/`, `apps/`), apply root-level analysis for the root `.gitignore`. If the user scoped the command with `--scope <path>`, restrict analysis to that subtree and its nearest `.gitignore` ancestor.

---

## Related Commands

- `/run-security-audit` — broader security scan that includes secret detection, dependency CVEs, and auth hardening
- `/refactor-project-layout` — reorganize files into correct directories after gitignore cleanup
- `/generate-sbom` — inventory all tracked dependencies
