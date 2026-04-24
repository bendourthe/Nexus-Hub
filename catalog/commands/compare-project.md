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

**Section 9: Security and Risk Assessment** (MANDATORY - gates Section 11 adoption recommendations)

Every adoption exercise must evaluate data-flow and trust risk before producing a plan. Section 9 has four subsections. Reference the `AGENTS.md` MCP Registry Policy decision tree throughout.

- **9.1 Threat Model Comparison** - Side-by-side table covering: new runtime dependencies introduced, outbound-call destinations at runtime, credentials / API keys required, whether source code / prompts / query text leaves the local machine, whether a new commercial relationship with a third party is required. Columns: Dimension | Current Project | External Project | Adoption delta.

- **9.2 Per-Item Risk Scorecard** - For each adoption candidate listed in Section 5 (Skills and Capabilities Gap Analysis), assign a risk tier (None / Low / Medium / High) with a one-sentence justification. Items rated High in this table are gated on Section 9.3's reverse-engineering viability before they can appear in Section 11 (Adoption Plan). Columns: Item | Risk tier | Justification.

- **9.3 Reverse-Engineering Viability Analysis** - For each adoption candidate, classify under the MCP Registry Policy decision tree (from `AGENTS.md`):
  - `re-full` - fully reverse-engineerable into a local internal artifact with no loss of function
  - `re-partial` - partially reverse-engineerable; ship what's local, document the gap
  - `skill-native` - achievable by instructing the agent's own LLM; replace with a skill, not an MCP or external integration
  - `vendor-intrinsic` - the third party IS the intended data destination; rebuild-as-internal only improves audit posture and may be deferred
  - `drop-outright` - no local equivalent possible; not worth the trust cost

  Columns: Item | Classification | Internal deliverable (if any) | Effort estimate | Rationale.

- **9.4 Recommendation Ordering** - Rank all adoption candidates in this order before they appear in Section 11:
  1. `skill-native` items first (ship zero-code replacements immediately)
  2. `re-full` and `re-partial` items next (build internal equivalents under `extensions/` or as new skills)
  3. `vendor-intrinsic` items only when all three conditions hold (intrinsic destination AND non-RE'able AND extremely worth it), justified inline
  4. `drop-outright` items go to Section 13's N-item list (not adopted)

  This ordering IS the adoption plan. Section 11's priority tiers (P0/P1/P2/P3) operate within the Section 9.4 order, not across it.

**Section 10: Structural and Architectural Differences**
Notable differences in project organization, conventions, or patterns that are worth considering but may not map to a single adoption item.

**Section 11: Adoption Plan**
Organized per Section 9.4's ordering, then by priority tier (P0 through P3) within each RE bucket. Each item includes: What | Source | Target | Effort | Dependencies | Risk. Use a Markdown table for each bucket.

**Section 12: Implementation Sequence**
Recommended order of adoption, accounting for dependencies AND Section 9.4's RE-first ordering. Include a Mermaid Gantt chart or flowchart if there are more than 5 adoption items.

**Section 13: Risks and Considerations**
Conflicts with existing patterns, breaking changes, maintenance burden, and items explicitly not recommended for adoption with reasoning. Add a **"Items explicitly NOT recommended for adoption (security / policy reasons)"** N-item block (N1, N2, ...) for every candidate classified as `drop-outright` in Section 9.3 or that failed the MCP Registry Policy check. Reference the policy by name for each rejection.

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

**Section 5: Adoption Plan (preliminary)**
Organized by priority tier (P0 through P3). Each item includes: What | Source (article section) | Target (where in the project) | Effort | Dependencies | Risk. This is preliminary - the ordering is finalized in Section 6 after the security assessment.

**Section 6: Security and Risk Assessment** (MANDATORY - gates Section 7 adoption recommendations)

Article sources can describe patterns that still introduce third-party data processors, new outbound calls, or credential sprawl when implemented. Evaluate each insight from Section 3 against the MCP Registry Policy in `AGENTS.md`:

- For each insight, classify per the decision tree: `re-full` / `re-partial` / `skill-native` / `vendor-intrinsic` / `drop-outright`.
- Re-order the Section 5 plan per this ordering: `skill-native` wins first, then `re-full` / `re-partial` builds, then `vendor-intrinsic` (only if all three conditions hold), then `drop-outright` goes to Section 8's N-item list.

Columns: # | Insight | RE Classification | Internal deliverable | Risk tier (None / Low / Medium / High) | Rationale.

**Section 7: Implementation Sequence**
Recommended order of adoption, accounting for dependencies AND Section 6's RE-first ordering.

**Section 8: Risks and Considerations**
Potential conflicts, limitations of applying article recommendations to this specific project, and insights explicitly not recommended for adoption with reasoning. Add an N-item block for every `drop-outright` classification from Section 6.

---

### 7. Cleanup

- If a temp clone was created in Step 2, delete it: `rm -rf <temp-dir>/compare-<normalized-name>`
- Confirm to the user:
  1. The full path of the report that was written.
  2. The external source (URL or path) and its type.
  3. A headline summary: total adoption candidates found, top 3 P0 items, and overall recommendation.

### 8. Offer to Generate Implementation Plan

After cleanup, always offer to chain into `/generate-plan` so the user can immediately operationalize the adoption items without a separate command invocation. The handoff is gated on Section 9's (repo/local) or Section 6's (article) Security and Risk Assessment having been completed, and always passes the `reverse-engineer-first=true` flag so the generated plan sequences phases per the RE-first ordering rather than raw P-tier.

1. **Count adoption items** by reading the Adoption Plan section (Section 11 for repo/local reports, Section 5 for article reports) of the report just written:
   - `count_p0` - rows in the P0 (Immediate) table
   - `count_p1` - rows in the P1 table
   - `count_p2` - rows in the P2 table
   - `count_p3` - rows in the P3 table
   - `total` = sum of the above

   Also count from Section 9 (repo/local) or Section 6 (article) the number of items in each RE bucket: `re_skill_native`, `re_full`, `re_partial`, `re_vendor_intrinsic`, `re_drop_outright`. Surface these counts in the prompt so the user understands what kind of plan they are about to generate.

2. **Ask the user** (always; no silent threshold):

   > "The adoption plan identified **N total items** (P0: *a*, P1: *b*, P2: *c*, P3: *d*). Reverse-engineering breakdown: *re_skill_native* skill-native, *re_full*/*re_partial* reverse-engineerable into internal code, *re_vendor_intrinsic* vendor-intrinsic adoptions (justified in Section 9), *re_drop_outright* dropped (not adopted).
   >
   > Would you like to generate an implementation plan now? The generated plan will sequence phases in **reverse-engineer-first order**: skill-native replacements first, then internal RE builds, then vendor-intrinsic adoptions (with justification), then drops go to an out-of-scope appendix. This is the MCP Registry Policy default and cannot be disabled.
   >
   > 1. Critical + High priority only (P0 + P1) - ***a+b*** items
   > 2. Critical + High + Medium (P0 + P1 + P2) - ***a+b+c*** items
   > 3. All items (P0 + P1 + P2 + P3) - ***N*** items
   > N. No, skip plan generation.
   >
   > Reply 1 / 2 / 3 / N."

   Substitute the actual counts. Suppress any scope option whose filtered total is zero.

3. **If the user answers N**: print a one-line pointer and stop:
   > "You can generate the plan later by running: `/generate-plan <full-comparison-file-path>`"

4. **If the user answers 1, 2, or 3**: invoke `/generate-plan` in the same session, passing three pieces of state:
   - The **comparison file path** as a positional argument (e.g. `docs/v0.9.7/comparison-shannon.md`).
   - The **scope-tier filter** resolved from the user's choice: `p0p1`, `p0p1p2`, or `all`.
   - The **`reverse-engineer-first=true`** flag, always set. The generated plan will sequence phases per Section 9.4's ordering (repo/local) or Section 6's re-ordering (article), not raw P-tier.

   Hand the invocation off with an explicit directive block:
   > "Invoking `/generate-plan` in from-comparison mode. Source: `<full-comparison-file-path>`. Scope filter: `<p0p1|p0p1p2|all>`. Reverse-engineer-first: true."

   This follows the existing `/setup-project` -> `/generate-plan` chaining precedent. The `/generate-plan` command recognizes the comparison-path argument via its Phase 0.5 (*From-comparison mode*) and reads the RE-first flag to sequence phases per the MCP Registry Policy decision tree. References: [AGENTS.md](../AGENTS.md) MCP Registry Policy; [docs/v1.0.0/mcp-reverse-engineering-matrix.md](../../docs/v1.0.0/mcp-reverse-engineering-matrix.md) for classification precedent.

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
- [ ] **Section 9 (repo/local) or Section 6 (article) Security and Risk Assessment is present and populated.** Every adoption candidate from Section 5 has a Section 9.2 risk tier AND a Section 9.3 RE classification. Section 9.4 ordering is used to structure Section 11. Reports missing Section 9 / Section 6 fail this check.
- [ ] **MCP Registry Policy is cited** when any adoption candidate implies a new outbound call, new API key, new third-party data processor, or new runtime dependency. The policy from `AGENTS.md` is referenced by name in the Rationale column of Section 9.3.
- [ ] **N-item block in Section 13 (repo/local) or Section 8 (article)** lists every `drop-outright` classification with a policy-grounded rejection reason.

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
