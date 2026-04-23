---
description: Compare the current project with an external knowledge source (Git repo, web article, or local path), producing a structured gap analysis and prioritized adoption plan saved to docs/<version>/comparison-<name>.md.
---

# Compare Project

Perform a deep comparison between the current project and an external knowledge source, then produce a structured adoption plan identifying what to bring in and how. The source can be a Git repository, a web article or blog post, or a local directory.

## Steps

### 1. Resolve Input

- Check whether the user provided an argument after the command (a URL or a local filesystem path).
- If no argument was provided, ask the user: "Please provide a source to compare against. This can be a GitHub repo URL, a web article URL, or a local filesystem path."
- Classify the input into one of three source types:

| Source Type | Detection Rule | Example |
|-------------|---------------|---------|
| **Git repository** | URL contains `github.com`, `gitlab.com`, `bitbucket.org`, or ends in `.git` | `https://github.com/org/repo` |
| **Web article** | Any other URL starting with `http://` or `https://` | `https://www.latent.space/p/reviews-dead` |
| **Local path** | Not a URL; verify the path exists on the filesystem | `/home/user/repos/other-project` |

- Extract a normalized name for the report filename:
  - **Git repo**: last segment of the URL path (e.g., `my-project` from `https://github.com/org/my-project`).
  - **Web article**: last non-empty segment of the URL path (e.g., `reviews-dead` from `https://www.latent.space/p/reviews-dead`).
  - **Local path**: directory name (e.g., `other-tool` from `/home/user/repos/other-tool`).
- Record the detected `SOURCE_TYPE` (`repo`, `article`, or `local`) for use in later steps.

### 2. Acquire the External Source

**If the input is a Git repository URL:**

- Determine the OS-appropriate temp directory (`/tmp` on macOS/Linux, `$TEMP` or `$env:TEMP` on Windows).
- Run a shallow clone to minimize download time:
  ```
  git clone --depth 1 <url> <temp-dir>/compare-<normalized-name>
  ```
- If the clone fails, inform the user clearly: "Could not clone the repository at <URL>. This may be a private repository, an invalid URL, or a network issue. You can: (1) provide a local path to an already-cloned copy, (2) provide credentials and retry, or (3) cancel."
- Record the clone path as `EXTERNAL_ROOT`.

**If the input is a web article URL:**

- Fetch the page content using the WebFetch tool or `curl`.
- Extract the readable article text, stripping navigation, ads, and boilerplate HTML.
- If the fetch fails (network error, paywall, 404, authentication required), inform the user clearly: "Could not fetch the article at <URL>. The page may require authentication, may be behind a paywall, or the URL may be invalid. You can: (1) paste the article text directly into the chat, (2) provide a different URL, or (3) cancel."
- Record the extracted text as `SOURCE_CONTENT`.

**If the input is a local path:**

- Verify the path exists and contains recognizable project files (e.g., a README, manifest file, or source directory).
- If the path does not exist or is empty, inform the user: "The path <path> does not exist or contains no recognizable project files. Please provide a valid path."
- Set `EXTERNAL_ROOT` to the provided path.

### 3. Analyze the Source and the Current Project

The analysis approach depends on the `SOURCE_TYPE`.

---

**If SOURCE_TYPE is `repo` or `local`:**

Perform a thorough inventory of both the current project (`PROJECT_ROOT`) and the external project (`EXTERNAL_ROOT`). Where possible, analyze both projects in parallel for efficiency.

For each project, collect findings across these **11 dimensions**:

| # | Dimension | What to Look For |
|---|-----------|-----------------|
| 1 | **Project Identity** | Name, description (README, CLAUDE.md, package.json, pyproject.toml), version, license |
| 2 | **Technology Stack** | Languages, frameworks, build tools, test runners, linters, package managers (from manifest files) |
| 3 | **AI Assistant Configuration** | Presence and structure of `.claude/`, `.github/copilot-instructions.md`, `.gemini/`, `.cursor/`, or equivalent. Count of skills, commands, context files, hooks |
| 4 | **Project Structure** | Top-level directory layout, organizational pattern, depth, file count |
| 5 | **Skills and Capabilities Inventory** | For DevAI-Hub-style projects: enumerate all skills by category. For non-Hub projects: infer equivalent capabilities from config files, scripts, CI workflows, instruction files |
| 6 | **Commands and Automation** | Slash commands, custom scripts, Makefiles, task runners, npm scripts |
| 7 | **CI/CD and Hooks** | GitHub Actions, GitLab CI, Jenkinsfiles, pre-commit hooks, automated checks |
| 8 | **Documentation** | README quality, API docs, architecture docs, ADRs, changelogs, guides |
| 9 | **Testing Strategy** | Test types present, coverage infrastructure, test frameworks |
| 10 | **Security Posture** | Dependency scanning, secret detection, SAST/DAST tools, security policies |
| 11 | **Developer Experience** | Setup scripts, containerization, devcontainers, environment management, onboarding guides |

---

**If SOURCE_TYPE is `article`:**

Do NOT use the 11-dimension framework. Instead, perform a two-part analysis:

**Part A: Extract insights from the article.** Read the full article text and extract every actionable insight, including:
- Techniques, methods, or patterns described
- Tools, libraries, or services recommended
- Best practices or anti-patterns identified
- Workflows or processes proposed
- Architectural or design recommendations

Number each insight and note which section of the article it comes from.

**Part B: Evaluate each insight against the current project.** For every extracted insight, determine:
- **Already implemented**: The current project already does this. Cite the specific file(s) as evidence.
- **Partially implemented**: The current project does something similar but could be improved. Cite the relevant file(s) and explain the gap.
- **Missing**: The current project does not do this at all. Explain where it could be added.
- **Not applicable**: The insight does not apply to the current project's domain, stack, or goals.

---

### 4. Compare and Classify (repo/local sources only)

> Skip this step if `SOURCE_TYPE` is `article`. The article flow handles classification in Step 3 Part B.

For each of the 11 dimensions, classify every difference into one of four buckets:

| Bucket | Meaning |
|--------|---------|
| **External-only** | Present in the external project but absent in the current project. This is an adoption candidate. |
| **Current-only** | Present in the current project but absent in the external project. This is a strength to preserve. |
| **Both present, different approach** | Both projects address this, but the approaches differ. Evaluate which is better and why. |
| **Both present, equivalent** | No meaningful difference. No action needed. |

Pay special attention to:
- Skills present in the external project but absent in the current project (by name or equivalent capability).
- Commands, hooks, or automation workflows that differ.
- Configuration patterns (context files, memory management, instruction templates) that differ.
- Documentation approaches and quality differences.

### 5. Produce the Adoption Plan

Transform the gap analysis (or the article relevance analysis) into an actionable adoption plan. Score each candidate on a value/effort matrix:

| | Low Effort | Medium Effort | High Effort |
|---|-----------|---------------|-------------|
| **High Value** | P0 (Immediate) | P1 (Short-term) | P1 (Plan it) |
| **Medium Value** | P1 (Short-term) | P2 (Medium-term) | P3 (Backlog) |
| **Low Value** | P2 (If easy) | P3 (Backlog) | Skip |

For each adoption item, document:
- **What to adopt**: The specific insight, file, pattern, tool, or configuration.
- **Source reference**: File path in the external project, or the article section/quote.
- **Target location**: Where it would go in the current project.
- **Effort**: Low / Medium / High, with a brief justification.
- **Dependencies**: Other items that must be adopted first.
- **Risk**: Any risk of adopting this (breaking changes, conflicts with existing conventions, new maintenance burden).

Do not recommend adopting everything. Curate ruthlessly. Compare function, not form (a Makefile and a justfile serve the same purpose). Preserve the current project's identity and conventions; adapt patterns rather than copying blindly.

### 6. Write the Report

**Determine the current project version:**
- Locate the `CHANGELOG` file in the project root (try `CHANGELOG.md`, `CHANGELOG`, `HISTORY.md`).
- Extract the most recent version tag.
- If no changelog, check `package.json`, `pyproject.toml`, `Cargo.toml`, or equivalent manifest.
- If no version can be determined, use `vUnknown`.

**Construct the output path:** `<project_root>/docs/<version>/comparison-<normalized-name>.md`

---

**If SOURCE_TYPE is `repo` or `local`, write the full 12-section report:**

Front matter:

```
# Cross-Project Comparison: <Current Project> vs. <External Project>

**Version**: <version>
**Generated**: <ISO 8601 timestamp>
**Analyzer**: Claude Code -- compare-project command
**External Source**: <URL or path>
**Source Type**: Repository
```

**Section 1: Executive Summary**
3-5 sentences covering: what was compared, the headline findings (how many adoption candidates, how many strengths), and the overall recommendation (adopt heavily / selectively adopt / minimal gaps / fundamentally different approach).

**Section 2: Project Profiles**
Side-by-side overview of both projects: identity, purpose, maturity, scale, technology stack.

**Section 3: Technology Stack Comparison**
Table: Layer | Current Project | External Project | Notes

**Section 4: AI Assistant Configuration Comparison**
Detailed comparison of `.claude/` (or equivalent), skills, commands, hooks, context files, instruction templates. This is the highest-signal section for DevAI-Hub-style comparisons.

**Section 5: Skills and Capabilities Gap Analysis**
- **5a. Present in External, Missing in Current** (adoption candidates, grouped by category)
- **5b. Present in Current, Missing in External** (strengths to preserve)
- **5c. Present in Both, Quality Comparison** (where one does it better)

**Section 6: Commands and Automation Comparison**
- **6a. Commands Gap** (slash commands, scripts, task runners)
- **6b. CI/CD and Hooks Gap** (automation, pre-commit, GitHub Actions)

**Section 7: Documentation and Developer Experience Comparison**
Side-by-side comparison of documentation quality, onboarding, setup scripts, and environment management.

**Section 8: Testing and Security Posture Comparison**
Coverage, frameworks, security tooling, and policy differences.

**Section 9: Structural and Architectural Differences**
Notable differences in project organization, conventions, or patterns that are worth considering but may not map to a single adoption item.

**Section 10: Adoption Plan**
Organized by priority tier (P0 through P3). Each item includes: What | Source | Target | Effort | Dependencies | Risk. Use a Markdown table for each tier.

**Section 11: Implementation Sequence**
Recommended order of adoption, accounting for dependencies. Include a Mermaid Gantt chart or flowchart if there are more than 5 adoption items.

**Section 12: Risks and Considerations**
Conflicts with existing patterns, breaking changes, maintenance burden, and any items explicitly not recommended for adoption with reasoning.

---

**If SOURCE_TYPE is `article`, write the simplified 7-section report:**

Front matter:

```
# Source Analysis: <Current Project> vs. "<Article Title>"

**Version**: <version>
**Generated**: <ISO 8601 timestamp>
**Analyzer**: Claude Code -- compare-project command
**External Source**: <URL>
**Source Type**: Web Article
```

**Section 1: Executive Summary**
3-5 sentences covering: what article was analyzed, how many actionable insights were extracted, how many are relevant to the current project, and the overall recommendation.

**Section 2: Source Overview**
Article title, author (if available), publication date (if available), topic, and key thesis in 2-3 sentences.

**Section 3: Key Insights Extracted**
Numbered list of every actionable insight from the article. Each entry includes a brief description and the article section it came from.

**Section 4: Relevance Analysis**
For each extracted insight, classify as: Already Implemented / Partially Implemented / Missing / Not Applicable. Include file path evidence for "Already Implemented" and "Partially Implemented" items. Present as a table:

| # | Insight | Status | Evidence / Notes |
|---|---------|--------|-----------------|

**Section 5: Adoption Plan**
Organized by priority tier (P0 through P3). Each item includes: What | Source (article section) | Target (where in the project) | Effort | Dependencies | Risk. Use a Markdown table for each tier.

**Section 6: Implementation Sequence**
Recommended order of adoption, accounting for dependencies.

**Section 7: Risks and Considerations**
Potential conflicts, limitations of applying article recommendations to this specific project, and any insights explicitly not recommended for adoption with reasoning.

---

### 7. Cleanup

- If a temp clone was created in Step 2, delete it: `rm -rf <temp-dir>/compare-<normalized-name>`
- Confirm to the user:
  1. The full path of the report that was written.
  2. The external source (URL or path) and its type.
  3. A headline summary: total adoption candidates found, top 3 P0 items, and overall recommendation.

### 8. Offer to Generate Implementation Plan

After cleanup, always offer to chain into `/generate-plan` so the user can immediately operationalize the adoption items without a separate command invocation.

1. **Count adoption items** by reading the Adoption Plan section (Section 10 for repo/local reports, Section 5 for article reports) of the report just written:
   - `count_p0` — rows in the P0 (Immediate) table
   - `count_p1` — rows in the P1 table
   - `count_p2` — rows in the P2 table
   - `count_p3` — rows in the P3 table
   - `total` = sum of the above

2. **Ask the user** (always; no silent threshold):

   > "The adoption plan identified **N total items** (P0: *a*, P1: *b*, P2: *c*, P3: *d*). Would you like to generate an implementation plan now?
   >
   > 1. Critical + High priority only (P0 + P1) — ***a+b*** items
   > 2. Critical + High + Medium (P0 + P1 + P2) — ***a+b+c*** items
   > 3. All items (P0 + P1 + P2 + P3) — ***N*** items
   > N. No, skip plan generation.
   >
   > Reply 1 / 2 / 3 / N."

   Substitute the actual counts. Suppress any scope option whose filtered total is zero (e.g. if `count_p2 == 0 && count_p3 == 0`, option 2 and 3 collapse into option 1).

3. **If the user answers N**: print a one-line pointer and stop:
   > "You can generate the plan later by running: `/generate-plan <full-comparison-file-path>`"

4. **If the user answers 1, 2, or 3**: invoke `/generate-plan` in the same session, passing two pieces of state:
   - The **comparison file path** as a positional argument (e.g. `docs/v0.9.7/comparison-shannon.md`).
   - The **scope-tier filter** resolved from the user's choice: `p0p1`, `p0p1p2`, or `all`.

   Hand the invocation off with an explicit directive block:
   > "Invoking `/generate-plan` in from-comparison mode. Source: `<full-comparison-file-path>`. Scope filter: `<p0p1|p0p1p2|all>`."

   This follows the existing `/setup-project` -> `/generate-plan` chaining precedent. The `/generate-plan` command recognizes the comparison-path argument via its Phase 0.5 (*From-comparison mode*) and will pre-seed the discovery interview from the Adoption Plan section, skipping questions the report already answers.

---

## Quality Checks

Before writing the report, verify the following:

- [ ] The source was successfully acquired. If not, the user received a clear error message with actionable alternatives.
- [ ] The current project was fully analyzed before any comparison was written.
- [ ] For repo/local sources: both projects were scanned across all 11 dimensions.
- [ ] For article sources: every insight was extracted and evaluated against the current project.
- [ ] Every gap or relevance claim cites specific file paths or article sections as evidence.
- [ ] Adoption items have concrete target locations, not vague suggestions.
- [ ] Effort estimates are grounded in the actual complexity observed.
- [ ] No recommendation conflicts with the current project's existing conventions without explicitly flagging the conflict.
- [ ] Temp directory was cleaned up (if applicable).

---

## Phase: Iterative Refinement (Loop)

**CRITICAL**: This is an iterative process. You cannot assume the first pass is perfect.
Perform the following refinement loop up to **3 times** (or as specified by the user):

1. **Analyze**: Review the generated report.
   - Is every section populated with evidence-backed findings?
   - Are adoption items specific and actionable?
   - Are priority assignments justified by the value/effort matrix?
2. **Refine**:
   - Fill in any gaps discovered during review.
   - Adjust priority assignments if the initial scoring was inconsistent.
   - Add missing file path or article section citations.
3. **Stop**:
   - If you are confident the report is comprehensive and actionable.
   - OR if you have reached the maximum iteration count.
