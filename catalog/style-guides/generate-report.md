# Report Writing Style Guide

This file is the quality reference for the `generate-report` command. Every merged markdown produced by that command MUST follow the patterns in this guide. Read this file completely before writing any content.

## Target Document Metrics

For a report synthesized from 3-7 source files covering a substantial topic:

| Metric | Target Range | Hard Limit |
|--------|-------------|------------|
| H1 headings | 5-9 | Never exceed 10 |
| H2 headings per H1 | 3-8 | Never exceed 10 |
| H3 headings per H2 | 0-5 | Never exceed 6 |
| Total tables | 10-20 | Never exceed 25 |
| Table rows per table | 3-12 | Never exceed 15 |
| Table columns | 2-5 | Never exceed 6 |
| Bullet points (total) | 80-200 | Minimum 50 |
| Prose paragraphs | 60-120 | -- |
| Total lines | 800-1200 | Never exceed 1500 |
| Figures | 5-8 | Minimum 4 for substantial reports |

**If your merged markdown exceeds any hard limit, fix it before proceeding.**

---

## Heading Hierarchy Template

The report has a fixed skeleton (opening and closing sections) and a flexible body. You determine the body sections based on the source material.

```
# Document Purpose                        ← Always first. 1-2 paragraphs + metadata table.
# Executive Summary                       ← Self-contained overview. 300-500 words total.
  ## [Topic Area 1]                       ← One H2 per body section, summarizing each
  ## [Topic Area 2]
  ## [Topic Area N]
# [Body Section 1: Topic-Specific Name]   ← Deep dive. 3-10 H2 subsections.
  ## 1. [Subtopic]
  ## 2. [Subtopic]
  ## N. [Subtopic]                        ← Numbered H2s within each section
# [Body Section 2: Topic-Specific Name]
  ## 1. [Subtopic]
  ## ...
# [Body Section N: Topic-Specific Name]   ← As many body sections as the content warrants
  ## 1. [Subtopic]
  ## ...
# Conclusion                              ← Summarize takeaways and next steps
# Appendices                              ← Optional. Brief reference material only.
  ## Appendix A: [Topic]
  ## Appendix B: [Topic]
# References                              ← Optional. Academic format with [N] inline citations.
```

The number and names of body H1 sections are entirely driven by the source material. A codebase review might have "Architecture Overview", "Security Findings", "Test Coverage", "Remediation Plan". A market analysis might have "Industry Landscape", "Competitive Analysis", "Growth Strategy". A clinical protocol might have "Study Design", "Endpoints", "Statistical Methods". Let the content dictate the structure.

---

## Writing Style: Good vs. Bad Examples

### Executive Summary

**BAD** (content dumping, single dense paragraph):
```
The Greenfield Supply Chain Optimization Initiative is a multi-year,
cross-functional program spanning 14 regional warehouses, 3 distribution
hubs, 42 logistics partners, 8 ERP integration points, 3 forecasting
models, and approximately 200 KPI dashboards across the North American
and European operations. The overall assessment is NEEDS_IMPROVEMENT: the
supply chain is operationally capable and delivers acceptable service levels,
but carries inventory inefficiencies, demand forecasting gaps, and partner
onboarding bottlenecks that must be resolved before the Q3 expansion.
```
Problems: Too many metrics crammed into one sentence. No structure. Hard to scan.

**GOOD** (concise, scannable, metrics woven into narrative):
```
The Greenfield Supply Chain Optimization Initiative covers 14 regional
warehouses and 3 distribution hubs supporting North American and European
operations. It currently manages 42 logistics partners, 8 ERP integration
points, and approximately 200 KPI dashboards. The supply chain is
operationally capable, but inventory inefficiencies and forecasting gaps
must be resolved before the planned Q3 expansion.
```
Why it works: One scope sentence, one metrics sentence, one verdict sentence. Three sentences, each with a clear job.

### Topic Summaries (inside Executive Summary)

Each H2 in the Executive Summary should correspond to a body section and summarize its key findings in a single paragraph.

**BAD**:
```
## Operational Performance

The warehouses operate across 14 locations with various performance
levels. The assessment found multiple issues including inefficiencies,
delays, and quality concerns that need to be addressed.
```
Problems: Vague ("multiple"), no specific counts, no severity breakdown.

**GOOD**:
```
## Operational Performance

The assessment identified 22 findings: 3 critical bottlenecks in
order fulfillment, 7 high-priority inventory discrepancies, 8 medium
process improvement opportunities, and 4 low-priority cosmetic issues.
Fulfillment times average 4.2 days (target: 2.5 days), with the
eastern hub accounting for 68% of delays due to a manual picking
process and outdated WMS integration.
```
Why it works: Specific counts per severity. Names the critical issues. Quantifies the problem.

### Section Openings

**BAD** (starts directly with a table):
```
## 2. Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Backend | Python/Flask | 3.10/2.3 |
| Frontend | Vue.js | 3.4 |
...
```

**GOOD** (context paragraph first, then table):
```
## 2. Technology Stack

The platform is built on a modern cloud-native stack with containerized
deployment. The following table summarizes the core components, their
versions, and their roles in the system architecture.

| Component | Technology | Version | Role |
|-----------|-----------|---------|------|
| Backend | Python/Flask | 3.10/2.3 | REST API and business logic |
| Frontend | Vue.js | 3.4 | Single-page application UI |
| Queue | RabbitMQ | 3.12 | Async task orchestration |
| Database | PostgreSQL | 16.1 | Primary relational storage |

The technology choices reflect current best practices for scalable
web platforms, with strong typing support and container-first deployment.
PostgreSQL 16 provides both relational integrity and JSON support for
semi-structured data.
```
Why it works: Context sentence before table. Table has ≤6 columns. Takeaway paragraph after table.

### Tables vs. Prose

**BAD** (everything is a table):
```
## Service Descriptions

| Service | Port | Framework | Purpose | Files | Lines |
|---------|------|-----------|---------|-------|-------|
| api-gateway | 8080 | Express | Routing | 32 | 8500 |
| auth-svc | 8081 | NestJS | Auth | 18 | 4200 |
| worker | 8082 | Bull | Jobs | 12 | 3100 |
| db-primary | 5432 | PostgreSQL | Storage | 6 | 900 |
| cache | 6379 | Redis | Caching | 2 | 300 |
```

**GOOD** (prose analysis with strategic table):
```
## 1. Platform Structure

The system is organized as a containerized microservices application.
Five services collaborate to handle authentication, request routing,
background processing, and data persistence.

| Service | Technology | Port | Primary Responsibility |
|---------|-----------|------|----------------------|
| api-gateway | Express 4.18 | :8080 | Request routing and middleware |
| auth-svc | NestJS 10.3 | :8081 | Authentication and authorization |
| worker | Bull/Redis | :8082 | Background job processing |
| db-primary | PostgreSQL 16 | :5432 | Primary data storage |
| cache | Redis 7.2 | :6379 | Session cache and rate limiting |

The api-gateway is the largest component (32 files, ~8,500 lines),
handling all inbound traffic and middleware chains. The worker service
processes long-running tasks asynchronously via Bull queues.

[Figure 1: Current Platform Architecture]
```
Why it works: Opening context. Focused table (4 columns, 5 rows). Analytical follow-up. Figure reference.

### Implementation Steps

**BAD** (steps as table rows):
```
| Step | Action | Effort |
|------|--------|--------|
| 1 | Fix authentication bypass | 2h |
| 2 | Upgrade dependencies | 1h |
| 3 | Add input validation | 4h |
```

**GOOD** (steps as structured subsections):
```
### Step 1: Fix Critical Security Findings

**Objective**: Resolve the 2 critical findings that pose immediate risk
to data integrity and access control.

1. **Authentication bypass in `auth_middleware.js`**: Replace the custom
   token verification on lines 84-97 with the standard JWT library
   validation. Add expiry and audience checks.

2. **Unvalidated redirect**: Add an allowlist of valid redirect URLs
   in `config/routes.js`. Reject any redirect target not matching the
   allowlist pattern.

**Verification**: Run the security test suite (`npm run test:security`).
Both critical findings should show as resolved.

**Estimated effort**: 3 hours.
```
Why it works: Bold objective. Numbered sub-steps with file paths. Verification criteria. Effort estimate.

---

## Figure Design Patterns

When writing the figures manifest, choose the layout_type that best matches the content. The key to high-quality figures is **content mining**: extract specific names, metrics, and details from the source documents.

### Pattern 1: Layered Architecture (`layout_type: "layered"`)
Use for: System architecture with horizontal tiers (UI, API, data, infrastructure), test strategy pyramids, technology stacks.
Structure: 4-6 layers, each with 2-5 boxes. Boxes in same layer are peers.
Include a subtitle line with version and summary context.
Target: 15-25 boxes across all layers for a rich architecture overview.

**BAD box labels** (generic):
```json
{"id": "svc1", "label": "Service 1"},
{"id": "db", "label": "Database"}
```

**GOOD box labels** (mined from source):
```json
{"id": "gateway", "label": "API Gateway\n:8080"},
{"id": "postgres", "label": "PostgreSQL 16\n24 tables"}
```

### Pattern 2: Linear Flow (`layout_type: "flow"`)
Use for: Data pipelines, CI/CD stages, ETL processes, implementation roadmaps.
Structure: 3-8 sequential boxes flowing left-to-right. Keep labels short (1-2 words + detail on second line).
For workflows with distinct phases, use `rows` to create multi-row layouts (see Multi-Row Flows below).
For roadmaps, include duration/effort in each box label.

**BAD** (roadmap with no timeline):
```json
{"id": "phase1", "label": "Phase 1"},
{"id": "phase2", "label": "Phase 2"}
```

**GOOD** (roadmap with specific details):
```json
{"id": "security", "label": "Security Fixes\nSteps 1-2, 1.5 days", "color_intent": "remove"},
{"id": "bugs", "label": "Bug Fixes\nStep 3, 3-5 days", "color_intent": "risky"},
{"id": "optimize", "label": "Optimization\nSteps 7-11, 10-13 days", "color_intent": "phase"}
```

### Pattern 3: Directory Tree (`layout_type: "tree"`)
Use for: Repository structure, file organization, org charts, hierarchical breakdowns.
Structure: Root node at top, children below. Use `parent_id` to define hierarchy.
Use `annotation` + `severity` to call out problem areas.
Target: 10-20 nodes for a meaningful tree.

**GOOD** (annotated tree with problems called out):
```json
{"id": "monolith", "label": "order_service.py\n4,200 lines", "parent_id": "services", "annotation": "Needs Splitting", "severity": "P1"},
{"id": "legacy", "label": "legacy_adapter/\n3 files", "parent_id": "services", "annotation": "Deprecated", "severity": "P2"}
```

### Pattern 4: Hub and Spoke (`layout_type: "hub_spoke"`)
Use for: Central system with adapters, hexagonal architecture, tool evaluation matrices, dependency maps.
Structure: Central box + 4-8 surrounding boxes. The hub should be larger and prominently labeled.
Use `color_intent` on spokes to convey evaluation results (essential, remove, risky).

**GOOD** (tool evaluation with semantic colors):
```json
{"id": "essential", "label": "Essential (8)\nPostgreSQL, Redis, Nginx", "color_intent": "essential"},
{"id": "replace", "label": "Replace (2)\nLegacy ORM, FTP sync", "color_intent": "risky"},
{"id": "remove", "label": "Unused (1)\nMonitoring stack", "color_intent": "remove"}
```

### Pattern 5: Dual Panel (`layout_type: "dual_panel"`)
Use for: Before/after comparisons, current vs. proposed, client vs. server.
Structure: Two groups of boxes separated by a vertical divider. Each panel can have its own layers.
Add `panel_labels` to title each side (e.g., "Current State" vs. "Proposed State").
Show specific changes, not vague descriptions.

### Annotations and Callouts

Use the `annotation` field on boxes to highlight issues, metrics, or status labels. Combine with `severity` to auto-color the badge.

| Severity | Badge Color | Use For |
|----------|-------------|---------|
| `P0` | Red | Critical blockers, security issues, showstoppers |
| `P1` | Orange | High-priority problems, major technical debt |
| `P2` | Yellow | Medium issues, improvement opportunities |
| `P3` | Gray | Low priority, informational, nice-to-have |

**Example**: A tree or architecture figure where problem areas are annotated:
```json
{"id": "auth", "label": "auth_middleware.js\n450 lines", "annotation": "Auth Bypass", "severity": "P0"},
{"id": "config", "label": "config/routes.js", "annotation": "Open Redirect", "severity": "P0"},
{"id": "legacy", "label": "legacy_adapter.py", "annotation": "Deprecated API", "severity": "P1"}
```

### Semantic Color Intent

Use `color_intent` instead of hardcoded hex colors when the color conveys meaning. This ensures consistent, professional rendering.

| Intent | Meaning | Example Use |
|--------|---------|-------------|
| `essential` | Keep, core, healthy | Essential tools in evaluation |
| `remove` | Delete, deprecated, dangerous | Tools marked for removal |
| `risky` | Needs attention, warning | Components needing audit |
| `neutral` | Background, no emphasis | Standard boxes |
| `info` | Informational, data | Metrics boxes, savings |
| `success` | Completed, passing | Quality gates that pass |
| `phase` | Timeline phase, step | Roadmap phases |

### Multi-Row Flow Diagrams

For workflows with distinct phases (e.g., intake → processing → delivery), use the `rows` field to create intentional multi-row layouts instead of relying on automatic wrapping.

**When to use**: Workflows where boxes naturally group into 2-3 phases, branching pipelines, processes with a vertical handoff between stages.

**Structure**: Define `rows` as an array of `{label, box_ids}` objects. The script distributes each row's boxes horizontally and stacks rows vertically with automatic drop connectors.

```json
{
  "layout_type": "flow",
  "rows": [
    {"label": "Data Collection", "box_ids": ["ingest", "validate", "parse"]},
    {"label": "Analysis & Output", "box_ids": ["analyze", "report", "archive"]}
  ],
  "boxes": [
    {"id": "ingest", "label": "File Intake\nCSV/Excel Upload"},
    {"id": "validate", "label": "Schema Check\nFormat Validation"},
    {"id": "parse", "label": "Parser\nColumn Mapping"},
    {"id": "analyze", "label": "Analysis Engine\nStatistical Summary"},
    {"id": "report", "label": "Report Builder\nPDF Generation"},
    {"id": "archive", "label": "Archive\nStorage + Backup"}
  ],
  "arrows": [
    {"from": "ingest", "to": "validate"},
    {"from": "validate", "to": "parse"},
    {"from": "analyze", "to": "report"},
    {"from": "report", "to": "archive"}
  ]
}
```

### Diversity Rule
When generating 5+ figures, use at least 3 different layout_types AND at least 3 different figure categories from the taxonomy (architecture, pipeline, tree, evaluation, roadmap, comparison). A report with 7 flow diagrams and no variety feels monotonous. Mix architecture (layered), process (flow), structure (tree), evaluation (hub_spoke), and comparison (dual_panel) diagrams.

---

## Inline Code Formatting

Use backtick formatting (`` ` ``) for all technical terms. The script renders backtick text as monospace (Courier New), which makes technical content scannable and professional.

**Apply backticks to**: filenames, directory names, CLI commands, package names, class/function names, port numbers, config files, environment variables, database table names, and any text that would appear in code or a terminal.

**BAD** (no code formatting):
```
The api-gateway service runs Express on port 8080. Configuration lives in
docker-compose.yml and the main entry point is server.js. The worker writes
to the jobs table in PostgreSQL.
```

**GOOD** (backtick formatting for technical terms):
```
The `api-gateway` service runs `Express` on port `:8080`. Configuration
lives in `docker-compose.yml` and the main entry point is `server.js`. The
worker writes to the `jobs` table in PostgreSQL.
```

---

## Directory Tree Formatting

When presenting repository structures or file hierarchies, **always** use a fenced code block with tree-drawing characters (or simple indentation). Never render directory trees as flat bullet lists.

**BAD** (flat bullet list, no hierarchy visible):
```
- my-project/
- services/ (microservices)
- api/ (REST endpoints)
- tests/ (test suites)
- infra/ (deployment configs)
```

**GOOD** (fenced code block with tree characters):
````
```
my-project/
├── services/                # Microservices root
│   ├── api-gateway/         # Request routing, middleware
│   ├── auth-svc/            # Authentication + authorization
│   └── worker/              # Background job processing
├── packages/                # Shared libraries
│   ├── db-client/           # Database connection pool
│   └── logger/              # Structured logging
├── infra/                   # Infrastructure as Code
└── tests/                   # Integration test suites
```
````

If tree-drawing characters (├── │ └──) are awkward, simple indented text in a code block also works:
````
```
my-project/
    services/                # Microservices
        api-gateway/         # Routing + middleware
        auth-svc/            # Auth service
        worker/              # Background jobs
    packages/                # Shared libraries
    infra/                   # IaC definitions
```
````

---

## Figure Label Optimization

Box labels in figures should be concise to ensure readable font sizes. The rendering engine scales fonts down as labels get longer: labels up to 20 characters render at 10pt, 21 to 30 characters at 9pt, and anything longer at the 8pt minimum. To keep labels in the largest tier:

- **Target 15 to 20 characters per line.** Use `\n` for manual line breaks when a label has two logical parts.
- **Prefer short names with context on a second line**: `Auth Service\nPort :443` rather than `Authentication Service running on port 443`.
- **Use abbreviations where unambiguous**: `DB`, `API`, `Auth`, `Config`, `Svc`, `Msg`, `Queue`.
- **Move details to annotations or arrow labels** instead of cramming them into the box label.

---

## Self-Check Checklist

Before calling the generation script, verify your merged markdown against these criteria:

1. **Heading count**: Count H1, H2, H3. Compare to target ranges above.
2. **Table count**: Count tables (lines starting with `|`). Must be ≤25 total.
3. **Bullet count**: Count lines starting with `- ` or `* `. Must be ≥50.
4. **Section openings**: Spot-check 5 random H2 sections. Each must start with 1-3 sentences of prose (not a table, list, or sub-heading).
5. **Table size**: No table should exceed 15 rows or 6 columns.
6. **Figure count**: Count `[Figure N:` placeholders. Must be ≥4 for substantial reports.
7. **No TOC heading**: The merged markdown must NOT contain `# Table of Contents`.
8. **No duplicate headings**: No two H1 or H2 headings should have the same text.
9. **Length check**: Total line count should be 800-1200. If >1500, you are content-dumping.
10. **Prose density**: Skim the document. If it looks like a wall of tables and lists with minimal prose, rewrite the densest sections as analytical paragraphs.
