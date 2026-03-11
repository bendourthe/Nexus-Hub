---
description: Search the Hub catalog by keyword, category, or role to find relevant skills and workflows.
---
# Search Skills Catalog

Search the DevAI-Hub catalog to find skills, workflows, and bundles relevant to your current task.

## Instructions

You are helping the user discover relevant skills from the DevAI-Hub catalog.

### Step 1: Get the Search Query

If the user provided a query (e.g., `/search-skills security audit`), use that. Otherwise ask: "What are you trying to do? Describe your task or enter a keyword, category name, or role (e.g., 'security', 'testing', 'AI Engineer')."

### Step 2: Locate the Catalog

Read `skills.json` from the DevAI-Hub `data/` directory. Common locations:
- Relative to this command file: `../../data/skills.json`
- `~/DevAI-Hub/data/skills.json`
- A path the user specifies

If not found, ask the user for the path to the DevAI-Hub `data/skills.json`.

### Step 3: Search the Catalog

Parse the JSON and search for matches across these fields for each skill:
- `name` — exact and partial matches score highest
- `description` — keyword matches
- `category` — if the query matches a category name, return all skills in that category

Also check `data/workflows.json` for relevant workflows, and `data/bundles.json` for relevant role bundles.

**Scoring priority (highest first):**
1. Exact match on skill name
2. Query appears in skill name
3. Query appears in skill description
4. Query matches a category name
5. Query matches a bundle name

### Step 4: Present Results

Display results in three sections (omit sections with no matches):

**Matching Skills** — list up to 10 most relevant, grouped by category:
```
Category: Security
  • dependency-security-audit — Audits project dependencies for known CVEs and license issues
  • cve-reachability-analyzer — Determines whether a CVE in a dependency is actually reachable
  • ...

Category: Compliance
  • soc2-compliance — Reviews code and infrastructure for SOC2 readiness
  • ...
```

**Matching Workflows** — list workflows that include the matched skills or match the query directly:
```
Workflow: Security Audit
  Skills: dependency-security-audit → authentication-patterns → code-review-security
```

**Matching Bundle** — if the query matches a developer role:
```
Bundle: Security Specialist
  Includes: dependency-security-audit, cve-reachability-analyzer, soc2-compliance, ...
```

### Step 5: Offer to Import

Ask: "Would you like to import any of these skills into your current project? You can:
1. Type **yes** or a skill name to import specific skills
2. Type **bundle** to import the full bundle
3. Type **workflow** to see the full workflow definition
4. Press Enter to skip"

If the user wants to import, follow the same steps as `/import-skills` to copy the selected skill directories to `.claude/skills/` in the current project.

### Step 6: Suggest Related Skills

After presenting results, suggest 1-3 complementary skills the user might not have considered:

"You might also find these useful:
- **[related-skill]** — [why it complements the matched skills]"

## Tips for Effective Searches

- Use role names to get curated bundles: `AI Engineer`, `Security Specialist`, `QA Engineer`
- Use category names for full category results: `testing`, `compliance`, `infrastructure`
- Use task descriptions for semantic matching: `find memory leaks`, `generate API docs`, `review for GDPR`
- Use workflow names to see multi-skill chains: `Full Code Review`, `Security Audit`, `Release Preparation`
