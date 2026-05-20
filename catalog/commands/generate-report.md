---
description: Generate a professional Word (.docx) or PowerPoint (.pptx) report from one or more Markdown files, using a template from the project or global templates directory.
---

# Generate Report Command

Generate a professional Word document or PowerPoint presentation from one or more Markdown files. The command discovers available templates (preserving branded title pages, logos, headers, footers, and margins), analyzes your content for optimal structure, and produces a formatted report saved to the project's `docs/<version>/` directory. If diagrams are found, a companion PPTX with editable shapes is also generated.

**BEFORE WRITING ANY CONTENT**: Read the style guide at `catalog/style-guides/generate-report.md` in the project root (or `~/.nexus-hub/style-guides/generate-report.md` for global installs). This guide contains concrete examples of good vs. bad output and the target metrics you must hit. The style guide is reference content, not a slash command - it lives outside `catalog/commands/` so it does not surface in the slash menu.

## Phase 1: Resolve Input Files

**CRITICAL RULE**: You MUST get explicit user confirmation on the file list before proceeding. NEVER silently auto-discover files and proceed without asking. The user decides what goes into the report.

**SCOPE BOUNDARY**: Only consider files inside the current project directory (`<project_root>`). NEVER reference, read, or use files from outside the project directory (e.g., `reports/` directories at a parent level, previously generated documents, templates from other projects). If a file path resolves outside the project root, reject it.

**NO REFERENCE DOCUMENTS**: This command generates a NEW document from scratch based solely on the user's selected input files. NEVER search for or reference previously generated reports, "target" documents, or existing output documents as a basis or comparison for the new report. Each invocation is independent.

Determine what content to include in the report:

1. **If file path(s) were provided after the command invocation** (e.g., the user typed a filename like `analysis.md` or multiple files like `analysis.md review.md`):
   - Verify each file exists relative to the project root.
   - If a file does not exist, search the project for it (check `docs/`, subdirectories).
   - Present the resolved file list and **ask the user to confirm** before proceeding:
     > "I found the following files to include in the report:
     > 1. `docs/analysis.md`
     > 2. `docs/findings.md`
     >
     > Include all of these? [Y]es / [E]dit list / [C]ancel"

2. **If no files were provided**:
   - Scan the project directory for Markdown documentation files (check `docs/`, `README.md`, and common documentation subdirectories).
   - Present the discovered files as **suggestions** and ask the user to select:
     > "I found the following Markdown files in the project:
     >
     > `docs/`:
     >   1. architecture-overview.md (45 KB)
     >   2. requirements-analysis.md (32 KB)
     >   3. implementation-notes.md (28 KB)
     >
     > `root`:
     >   4. README.md (2 KB)
     >
     > Which files should I include in the report? Enter numbers (e.g., `1 2 3`), a directory path, or type file paths manually:"
   - **Wait for the user to respond.** Do NOT proceed until the user has explicitly selected files.
   - If a directory was given, use the Glob tool to find all `*.md` files within it (non-recursive).
   - Present the final resolved file list and ask for confirmation before proceeding.

3. **Validate inputs**:
   - All files must exist and be readable.
   - All files must be inside the project root directory. Reject any paths that resolve outside it.
   - Supported input formats: `.md` (Markdown). If non-Markdown files are specified, inform the user that only Markdown is currently supported.

## Phase 2: Discover and Select Template

**CRITICAL RULE**: You MUST always present the template-source gate first and then list templates from the chosen source. NEVER auto-select a template without asking, even if only one bundled template is found.

### Step 2.1: Gate - generic (bundled) or custom?

Ask the user this binary question FIRST. As of v0.9.7, the installer no longer prompts for custom template imports at install time; the generic templates are always bundled at `~/.nexus-hub/templates/documentation/`, and custom templates are selected by path here.

```
Which template source should I use?
  [G] Generic  - use a template bundled with Nexus-Hub (recommended for most reports)
  [C] Custom   - specify the full path to your own .docx or .pptx template

Select [G]eneric / [C]ustom (default: G):
```

- **Wait for the user to respond.** Do NOT proceed until the user answers.
- If the answer is `G` / `Generic` / empty (default): continue to Step 2.2 (Generic picker).
- If the answer is `C` / `Custom`: continue to Step 2.3 (Custom path).

### Step 2.2: Generic picker (default)

Scan for bundled / project templates in this priority order:

1. `<project_root>/.claude/templates/documentation/` (project-specific, version-controlled; optional)
2. `~/.nexus-hub/templates/documentation/` (installed by the Nexus-Hub installer; always present on a standard install)

Merge the two lists, deduplicating by filename (project-level wins on conflict). Present them numerically:

```
Available generic templates:
Word (.docx):
  1. generic-word-report-template.docx (global)
  2. branded-report-template.docx (global)
PowerPoint (.pptx):
  3. Presentation Template.pptx (global)

[0] No template (blank document)

Which template should I use? Enter a number:
```

- Wait for the user to respond.
- If the user enters `0`, generate a blank-style document (no template base).
- If no templates are found at either path, inform the user that Nexus-Hub's bundled templates are missing (suggest re-running the installer) and offer to proceed with a blank document or fall back to Step 2.3 (Custom path).

### Step 2.3: Custom path

Prompt the user:

```
Enter the full path to your template file (.docx or .pptx):
```

- Validate that the path exists and is a file, and that the extension is `.docx` or `.pptx`. If either check fails, report the problem and re-prompt (or offer to fall back to Step 2.2).
- Tilde (`~`) and relative paths are resolved against the current working directory; drag-and-drop surrounding quotes are stripped.
- The custom template is NOT copied into `~/.nexus-hub/templates/documentation/` - it is used in place. Re-running `/generate-report` will prompt again; if the user expects the template to persist for future runs, they can manually copy it into the global templates directory.

### Template file-extension determines output format

The selected template's file extension determines the output format:
- `.docx` template produces a Word document
- `.pptx` template produces a PowerPoint presentation
- Blank (Step 2.2 option `[0]`) defaults to `.docx`.

## Phase 3: Determine Version and Output Path

1. **Detect the project version** using the same logic as the `analyze-codebase` command:
   - Read the `CHANGELOG.md` in the project root. Extract the most recent version tag (e.g., `v0.6.2`).
   - If no changelog, check `package.json`, `pyproject.toml`, `Cargo.toml` for a version field.
   - If no version can be determined, use `vUnknown`.

2. **Construct the output path** based on the template type:
   - For `.docx`: `<project_root>/docs/<version>/reports/<ReportTitle>.docx`
   - For `.pptx`: `<project_root>/docs/<version>/presentations/<ReportTitle>.pptx`
   - `<ReportTitle>` is derived from the first H1 heading found in the input files, sanitized for filesystem use (spaces replaced with underscores, special characters removed). Falls back to the first input filename stem if no H1 is found.

3. **Create the output directory** if it does not exist.

4. **Handle existing output**:
   - If a file already exists at the output path, ask:
     > "A report already exists at this path. [O]verwrite / [R]ename with timestamp / [C]ancel?"
   - If Rename: append `_YYYYMMDD_HHMMSS` before the extension.

## Phase 4: Content Analysis and Synthesis

**CRITICAL**: This is the most important phase. You must do the intellectual work of merging, deduplicating, and restructuring content BEFORE passing anything to the script. The script is a mechanical formatter, not a content editor. Do NOT skip or rush this phase.

**SCOPE RULE**: Your ONLY source material is the files the user selected in Phase 1. Do NOT reference, quote, or draw content from any other files in the project (e.g., previously generated reports in `reports/` directories, `_merged.md` files from past runs, or output `.docx`/`.pptx` files). The report must be generated entirely from the user's selected input files. Each report generation is a fresh, independent synthesis.

**MANDATORY**: Before starting, read the style guide at `catalog/style-guides/generate-report.md`. It contains concrete good-vs-bad examples, target metrics, and the self-check checklist you must verify against.

### Step 4.1: Read All Input Files

Read every resolved input file completely. Hold all content in working memory.

### Step 4.2: Content Inventory

For each file, identify and track:
- All H1 headings (document titles)
- All H2 headings (major section names)
- Executive summaries, introductions, or overview sections
- All Markdown tables (lines starting with `|`)
- All Mermaid diagram blocks (fenced with ` ```mermaid `)
- All `---` separator lines (these will be removed)

Identify which sections appear in multiple files (duplicates). For example, if three files each have an "Executive Summary", note this overlap explicitly.

### Step 4.3: Synthesize a Single Merged Markdown Document

Write a NEW Markdown document from scratch. Do NOT concatenate the original files. Instead, synthesize a clean, structured report. Follow the style guide patterns exactly.

**Document structure (fixed sections, then intelligent content):**

The report has a fixed skeleton (the bookend sections) and a flexible body (the detailed content sections). You decide how many body sections to create and what to name them based on the source material.

**Fixed opening sections (mandatory, in this exact order):**

1. **Document Purpose** (H1): 1-2 paragraphs explaining scope, intended audience, and document structure. Follow with a metadata table (Authors, Date, Project, Version). This MUST be the first H1 in the merged Markdown. If missing, the output is invalid.

2. **Executive Summary** (H1): One opening paragraph summarizing the key findings or themes. Then one H2 per major topic area covered in the body. Each H2 is a single paragraph (3-5 sentences) with key metrics or takeaways. Total: 300-500 words. Self-contained (a reader should understand the report's conclusions from this section alone). See style guide for good vs. bad examples.

**Flexible body sections (you determine the structure):**

3. **[Topic-Specific Name]** (H1, repeated as needed): Analyze the source files and identify the major themes, topics, or logical groupings. Create one H1 section per major theme. Use numbered H2 sections within each H1 for subtopics. The number of body H1 sections, their names, and their internal structure should be driven entirely by the content of the source files.

   Guidelines for body sections:
   - Aim for 3-7 body H1 sections (fewer for focused reports, more for broad ones).
   - Each H1 should represent a distinct major topic or narrative arc.
   - Use descriptive, topic-specific names (e.g., "Architecture Overview", "Security Findings", "Implementation Roadmap", "Market Analysis", "Clinical Protocol", "Budget Forecast") based on what the source material actually covers.
   - Each H1 should have 3-10 numbered H2 subsections.
   - Order the H1 sections in a logical reading flow: context first, then analysis, then recommendations or actions.

**Fixed closing sections (mandatory, in this exact order):**

4. **Conclusion** (H1): 1-3 paragraphs summarizing the key takeaways, overall assessment, and recommended next steps. This should not introduce new information, only synthesize what was covered in the body.

5. **Appendices** (H1, optional): Reference material, glossary, detailed inventories, schema catalogs. Keep brief (bullet lists or small tables). Omit entirely if no appendix material is warranted.

6. **References** (H1, optional): If the source material cites external documents, standards, papers, or URLs, compile them here in academic format. Use numbered references with `[1]`, `[2]`, etc. in the body text, and list the full citations in this section. Omit entirely if no external references exist in the source material.

**Writing rules** (see style guide for detailed examples):

- Every H1 and H2 section MUST open with 1-3 sentences of prose context. Never start with a table, list, or sub-heading.
- Tables: max 15 rows, max 5 columns. Preceded by context sentence and followed by takeaway sentence.
- Bullet lists preferred over comma-separated inline lists. Use for checklists, features, verification items.
- Numbered lists for sequential steps. Each step gets a bold title, sub-steps, and verification criteria.
- Paragraphs: 3-5 sentences max. Never cram 8+ items into one sentence.
- Every analytical claim must cite a concrete metric.
- Never present implementation steps as a summary table. Use `### Step N:` format with objective, sub-steps, and verification.
- Do NOT include a `# Table of Contents` heading. The script handles this automatically. Including one causes a duplicate TOC.
- Target length: 800-1200 lines. If over 1500, you are content-dumping.
- Include `[Figure N: Title]` placeholders on their own lines with a caption sentence.
- **Inline code formatting** (CRITICAL): Use backtick formatting for ALL technical terms: filenames (`main.py`), directories (`src/services/`), packages (`express`), ports (`:8080`), config files (`docker-compose.yml`), table names (`orders`), CLI commands, class names, function names, and environment variables. The script renders backticks as monospace Courier New. See the style guide for examples.
- **Directory trees**: When presenting repository or file structures, use a fenced code block with tree-drawing characters (├── │ └──) or simple indentation. NEVER render directory trees as flat bullet lists. See the style guide for examples.
- **Template awareness**: The merged markdown must NOT duplicate content that already exists as placeholders in the template. The script automatically clears template placeholder content and replaces it with your markdown. Your merged markdown should contain all sections (including "Document's Purpose", "Executive Summary", etc.); the script handles deduplication.
- **Pre-TOC content** (CRITICAL when using a template): If the template has content that should appear BEFORE the Table of Contents (e.g., a "Document's Purpose" section), wrap that content in `<!-- PRE-TOC -->` markers in your merged markdown. The script will render this content before the TOC, and all remaining content after the TOC. Example:
  ```markdown
  <!-- PRE-TOC -->
  # Document's Purpose
  This report presents a comprehensive assessment of the platform...
  <!-- /PRE-TOC -->

  # Executive Summary
  [rest of report content appears after the TOC]
  ```
  If the template has no pre-TOC sections, omit the markers entirely.

### Step 4.4: Plan and Write the Figures Manifest

#### Step 4.4a: Figure Planning (CRITICAL)

Before writing any JSON, analyze your merged markdown content and decide what figures would add the most value. Figures should visualize the report's key concepts, not just repeat text as boxes.

**Figure planning process:**

1. **Scan the merged markdown** for content that benefits from visualization: architecture descriptions, process flows, directory structures, comparisons, timelines, tool evaluations, testing strategies, dependency maps.

2. **Select 5-8 figures** from the following taxonomy. Match each figure type to content actually present in the report:

   | Figure Category | Layout Type | Use When Report Discusses... |
   |----------------|-------------|-------------------------------|
   | System Architecture | `layered` | Services, infrastructure, tech stack, deployment |
   | Data Pipeline / ETL | `flow` | Data processing, ingestion, DAGs, transformations |
   | CI/CD Pipeline | `flow` | Deployment, testing stages, quality gates |
   | Repository Structure | `tree` | Codebase organization, file layout, modules |
   | Before/After Comparison | `dual_panel` | Proposed changes, migration plans, refactoring |
   | Hexagonal / Clean Architecture | `hub_spoke` | Decoupling, ports & adapters, plugin patterns |
   | Implementation Roadmap | `flow` | Phased recommendations with timelines, steps |
   | Test Strategy | `layered` | Testing approach, coverage layers, tools |
   | Tool/Technology Evaluation | `hub_spoke` | Technology assessment, keep/replace decisions |
   | Dependency / Integration Map | `hub_spoke` | External integrations, API connections |

3. **For each selected figure, mine the source content** for specific, domain-relevant details to populate box labels. Extract: service names, port numbers, DAG names, table names, tool versions, file counts, line counts, metrics, percentages, durations, specific commands, specific file paths.

**Content mining examples (CRITICAL, follow these):**

BAD box labels (generic, could apply to any project):
- "Service 1", "Database", "Processing", "Validation", "Output"

GOOD box labels (mined from actual source content):
- "API Gateway\n:8080", "PostgreSQL 16\n24 tables", "RabbitMQ\n12 queues", "ESLint + Prettier\nstrict mode", "45-75 days\n18 steps"

For EVERY box, ask: "Does this label contain a specific name, number, or metric from the source documents?" If not, go back to the source and find the real detail.

#### Step 4.4b: Write the Figures JSON

Write a JSON file at: `<output_directory>/<ReportTitle>_figures.json`

**IMPORTANT**: The script auto-computes all layout positions. You only specify the logical structure (what boxes exist, what connects to what, what layout type). Do NOT specify `x`, `y`, `width`, or `height` coordinates. The script handles positioning.

For each figure, create an entry with:
- `figure_number`: Integer
- `title`: Short descriptive title
- `subtitle` (optional): Additional context line (e.g., "v2.4.0 | Cloud-Native | 5 Services")
- `layout_type`: One of `"layered"`, `"flow"`, `"tree"`, `"hub_spoke"`, `"dual_panel"`
- `mermaid_source` (optional): The raw Mermaid code for reference

**Optional fields on individual boxes:**
- `annotation`: Short callout text rendered as a badge near the box (e.g., "BLOCKING", "95% duplicate", "P0 Security")
- `severity`: `"P0"` (red badge), `"P1"` (orange), `"P2"` (yellow), `"P3"` (gray). Auto-colors the annotation badge.
- `color_intent`: Semantic color instead of hardcoded hex. Values: `"essential"` (green), `"remove"` (red), `"risky"` (orange), `"neutral"` (gray), `"info"` (blue), `"success"` (green), `"phase"` (teal). The script maps these to professional color palettes. Use `color_intent` when the color carries meaning (e.g., a tool marked for removal should be `"remove"`, not an arbitrary red hex).

**For `layered` layout** (system architecture with horizontal tiers):
```json
{
  "figure_number": 1,
  "title": "Current Platform Architecture",
  "subtitle": "v2.4.0 | Cloud-Native Microservices | 5 Layers",
  "layout_type": "layered",
  "layers": [
    {
      "label": "Client Layer",
      "color": "#EBF0F5",
      "boxes": [
        {"id": "spa", "label": "React SPA\n:3000"},
        {"id": "mobile", "label": "React Native\niOS + Android"},
        {"id": "admin", "label": "Admin Panel\n:3001"}
      ]
    },
    {
      "label": "API Layer",
      "color": "#EAF2F2",
      "boxes": [
        {"id": "gateway", "label": "API Gateway\n:8080"},
        {"id": "auth", "label": "Auth Service\n:8081"},
        {"id": "graphql", "label": "GraphQL BFF\n:4000"}
      ]
    },
    {
      "label": "Services",
      "color": "#F5F0E8",
      "boxes": [
        {"id": "orders", "label": "Order Service\n:8090"},
        {"id": "inventory", "label": "Inventory Svc\n:8091"},
        {"id": "notifications", "label": "Notification Svc\n:8092"},
        {"id": "worker", "label": "Background Worker"}
      ]
    },
    {
      "label": "Data Layer",
      "color": "#ECF3EE",
      "boxes": [
        {"id": "postgres", "label": "PostgreSQL 16\n:5432"},
        {"id": "redis", "label": "Redis 7.2\n:6379"},
        {"id": "s3", "label": "Object Storage\nS3-compatible"}
      ]
    },
    {
      "label": "Infrastructure",
      "color": "#F0ECF3",
      "boxes": [
        {"id": "k8s", "label": "Kubernetes\n3 namespaces"},
        {"id": "ci", "label": "GitHub Actions\n12 workflows"},
        {"id": "monitoring", "label": "Prometheus\n+ Grafana"}
      ]
    }
  ],
  "arrows": [
    {"from": "spa", "to": "gateway", "label": "REST"},
    {"from": "gateway", "to": "orders"},
    {"from": "orders", "to": "postgres", "label": "SQL"},
    {"from": "worker", "to": "redis"}
  ]
}
```

**For `flow` layout** (left-to-right pipeline):
```json
{
  "figure_number": 2,
  "title": "Order Processing Pipeline",
  "subtitle": "Checkout to Fulfillment | 5 Stages",
  "layout_type": "flow",
  "boxes": [
    {"id": "checkout", "label": "Checkout\nCart Validation"},
    {"id": "payment", "label": "Payment\nStripe API"},
    {"id": "confirm", "label": "Confirmation\nEmail + Receipt"},
    {"id": "fulfill", "label": "Fulfillment\nWarehouse API"},
    {"id": "ship", "label": "Shipping\nTracking Update"}
  ],
  "arrows": [
    {"from": "checkout", "to": "payment"},
    {"from": "payment", "to": "confirm"},
    {"from": "confirm", "to": "fulfill"},
    {"from": "fulfill", "to": "ship"}
  ]
}
```

**For `flow` layout with multi-row grouping** (branching workflows):
```json
{
  "figure_number": 3,
  "title": "CI/CD Deployment Pipeline",
  "subtitle": "Code Commit to Production Release",
  "layout_type": "flow",
  "rows": [
    {"label": "Build & Test", "box_ids": ["commit", "build", "test"]},
    {"label": "Deploy", "box_ids": ["staging", "approval", "production"]}
  ],
  "boxes": [
    {"id": "commit", "label": "Git Push\nPR Merge to main"},
    {"id": "build", "label": "Docker Build\nMulti-stage image"},
    {"id": "test", "label": "Test Suite\n340 tests, lint"},
    {"id": "staging", "label": "Staging Deploy\nk8s namespace"},
    {"id": "approval", "label": "Manual Approval\nQA Sign-off"},
    {"id": "production", "label": "Production\nRolling Update"}
  ],
  "arrows": [
    {"from": "commit", "to": "build"},
    {"from": "build", "to": "test"},
    {"from": "staging", "to": "approval"},
    {"from": "approval", "to": "production"}
  ]
}
```
When `rows` is present, the script arranges boxes in deliberate horizontal rows stacked vertically with a drop connector between rows. Use this for workflows that have distinct phases (e.g., ingestion phase → processing phase). If `rows` is absent, the standard single-row flow is used.

**For `tree` layout** (hierarchical structure):
```json
{
  "figure_number": 4,
  "title": "Repository Structure",
  "subtitle": "my-project/ | 82 Files | 3 Problem Areas",
  "layout_type": "tree",
  "boxes": [
    {"id": "root", "label": "my-project/"},
    {"id": "services", "label": "services/\n4 microservices", "parent_id": "root"},
    {"id": "packages", "label": "packages/\nShared libraries", "parent_id": "root"},
    {"id": "infra", "label": "infra/\nTerraform + k8s", "parent_id": "root"},
    {"id": "docs", "label": "docs/\nADRs + guides", "parent_id": "root", "annotation": "Outdated", "severity": "P2"},
    {"id": "gateway", "label": "api-gateway/\n32 files", "parent_id": "services"},
    {"id": "tests", "label": "tests/\n340 test cases", "parent_id": "services"},
    {"id": "order_svc", "label": "order-service/\n4,200 lines", "parent_id": "services", "annotation": "Needs Splitting", "severity": "P1"}
  ]
}
```

**For `hub_spoke` layout** (central system + adapters or evaluation):
```json
{
  "figure_number": 5,
  "title": "Dependency Evaluation",
  "subtitle": "16 Dependencies Assessed | 3 for Replacement",
  "layout_type": "hub_spoke",
  "boxes": [
    {"id": "core", "label": "Application Core\nv2.4.0"},
    {"id": "essential", "label": "Essential (11)\nPostgreSQL, Redis, Nginx", "color_intent": "essential"},
    {"id": "replaceable", "label": "Replace (3)\nLegacy ORM, Cron, FTP", "color_intent": "risky"},
    {"id": "audit", "label": "Needs Audit (1)\nSearch cluster", "color_intent": "risky"},
    {"id": "remove", "label": "Unused (1)\nDeprecated logger", "color_intent": "remove"},
    {"id": "savings", "label": "Est. Savings\n2GB RAM, 3 containers", "color_intent": "info"}
  ],
  "arrows": [
    {"from": "core", "to": "essential"},
    {"from": "core", "to": "replaceable"},
    {"from": "core", "to": "audit"},
    {"from": "core", "to": "remove"},
    {"from": "core", "to": "savings"}
  ]
}
```

**For `dual_panel` layout** (side-by-side comparison):
```json
{
  "figure_number": 7,
  "title": "Architecture Evolution",
  "subtitle": "Current Monolith → Proposed Microservices",
  "layout_type": "dual_panel",
  "panel_labels": ["Current State", "Proposed State"],
  "left_layers": [
    {"label": "Monolithic", "boxes": [
      {"id": "mono_api", "label": "Single Express App\nAll routes in one process"},
      {"id": "mono_db", "label": "Shared Database\nDirect SQL everywhere"},
      {"id": "mono_deploy", "label": "VM Deployment\nManual releases"}
    ]}
  ],
  "right_layers": [
    {"label": "Modular", "boxes": [
      {"id": "services", "label": "Domain Services\nBounded contexts"},
      {"id": "db_per_svc", "label": "DB per Service\nOwned schemas"},
      {"id": "k8s_deploy", "label": "Kubernetes\nCI/CD pipelines"}
    ]}
  ]
}
```

**Layout-specific complexity limits:**

| Layout | Max Boxes | Max Arrows | Notes |
|--------|-----------|------------|-------|
| `layered` | 25 | 10 | 4-6 layers × 3-5 boxes per layer |
| `flow` | 10 | 9 | Sequential readability; use multi-row for 6+ |
| `tree` | 20 | 0 | Hierarchy via `parent_id`, no explicit arrows |
| `hub_spoke` | 9 | 8 | 1 hub + up to 8 spokes |
| `dual_panel` | 16 per panel | 8 | Two vertical stacks |

- Box labels: max 35 characters per line (use `\n` for line breaks, max 2 lines per box).
- Arrow labels: max 15 characters. Omit for obvious connections.

**Diversity rule**: When generating 5+ figures, use at least 3 different layout_types AND at least 3 different figure categories from the taxonomy. A report with 7 flow diagrams and no variety feels monotonous.

**Color guidance:**
- Layer bands: `#EBF0F5` (blue), `#EAF2F2` (teal), `#F5F0E8` (amber), `#ECF3EE` (green), `#F0ECF3` (purple)
- Prefer `color_intent` over hardcoded hex when the color carries semantic meaning.
- The script auto-colors flow boxes and hub/spoke diagrams with professional palettes when no explicit color is set.
- NEVER use saturated primary colors (#FF0000, #0000FF, #00FF00).

If no Mermaid diagrams were found and the content doesn't warrant figures, write an empty array `[]`. However, for substantial reports (3+ source files), you should generate at least 5-8 figures that illustrate the key concepts even if the source files lack Mermaid diagrams.

**CRITICAL**: Every figure in the manifest MUST have populated `boxes` (for flow/tree/hub_spoke) or `layers` with non-empty `boxes` arrays (for layered). Figures with empty boxes/layers produce blank slides and will be filtered out by the script. If a diagram concept cannot be expressed using the supported layout types (layered, flow, tree, hub_spoke, dual_panel), omit it from the manifest entirely rather than including an empty or malformed entry.

### Step 4.5: Write the Merged Markdown File

Save the synthesized document from Step 4.3 to: `<output_directory>/<ReportTitle>_merged.md`

### Step 4.6: Self-Check (MANDATORY)

**Before proceeding to generation, verify your output against the style guide checklist.** Count the following in your merged markdown:

1. **H1 headings**: Should be 5-9 (Document Purpose + Executive Summary + 3-5 body sections + Conclusion + optional Appendices/References). If not, restructure.
2. **H2 headings per H1**: Should be 3-8 per body section. If <3, the section lacks depth. If >10, break it into two H1 sections.
3. **Tables**: Should be 10-20 total. If >25, rewrite some as prose. If 0, add strategic tables.
4. **Bullet points** (lines starting with `- ` or `* `): Should be 80-200 total, minimum 50. If <50, convert prose lists to bullet lists.
5. **Total lines**: Should be 800-1200. If >1500, you are content-dumping. Cut aggressively.
6. **Figure placeholders**: Should be 5-8 for substantial reports.
7. **No `# Table of Contents`**: Must not appear in the markdown.
8. **No duplicate H1/H2 headings**: Each heading text must be unique.
9. **Section openings**: Spot-check 5 H2 sections. Each must start with prose, not a table/list.

**If ANY check fails, fix the merged markdown and figures JSON NOW, before calling the script.**

### Step 4.7: Present the Synthesis Plan and TOC Preview

Show the user a summary AND the expected Table of Contents before proceeding. This allows the user to verify the document structure before generation begins.

1. Parse the merged markdown for all H1, H2, and H3 headings.
2. Format as a hierarchical numbered tree with proper indentation.
3. Present both the metrics summary and the TOC:

> "I have synthesized the content from [M] source files into a single merged report:
>
> **Metrics:**
> - **Title**: [detected title]
> - **Subtitle**: [detected subtitle]
> - **H1/H2/H3 sections**: [N]/[N]/[N]
> - **Tables**: [N] (target: 10-20)
> - **Bullet points**: [N] (target: 50+)
> - **Figures**: [N] figures across [N] layout types
> - **Total lines**: [N] (target: 800-1200)
> - **Template**: [template name]
>
> **Table of Contents (Preview):**
> ```
> 1. Document Purpose
> 2. Executive Summary
>    2.1. [Topic Area 1]
>    2.2. [Topic Area 2]
>    2.3. [Topic Area N]
> 3. [Body Section 1]
>    3.1. [Subtopic]
>    3.2. [Subtopic]
> 4. [Body Section 2]
>    4.1. [Subtopic]
>    ...
> N. Conclusion
> ```
>
> Does this structure look good?
> [Y]es, generate now / [E]dit the structure / [C]ancel"

4. **If user chooses [E]dit**: Ask which sections to modify, then loop back to Step 4.3. Maximum 3 edit iterations.
5. **If user chooses [Y]es**: Proceed to Phase 5.

## Phase 5: Generate the Documents

Call the Python report generator script with the SINGLE merged file from Step 4.5. **Never pass the original input files directly.**

**Template-awareness rules (CRITICAL when a template is selected):**

- The script preserves the template's title page, logo, headers, footers, and color scheme automatically.
- The script detects if the template already contains a Table of Contents and will skip inserting a duplicate.
- Content wrapped in `<!-- PRE-TOC -->` / `<!-- /PRE-TOC -->` markers is rendered BEFORE the TOC. All other content is rendered after the TOC. Use this for template sections like "Document's Purpose" that precede the Table of Contents.
- The merged Markdown content (after the PRE-TOC block, if any) should start directly with the first H1 section without any frontmatter.

### Word Document:

```bash
python ~/.nexus-hub/scripts/generate_report.py \
  --type generic-word \
  --md-files "<output_directory>/<ReportTitle>_merged.md" \
  --title "<title>" \
  --subtitle "<subtitle>" \
  --header-subtitle "<short_subtitle>" \
  --template "<template_path>" \
  --figures-json "<output_directory>/<ReportTitle>_figures.json" \
  --output "<output_path>"
```

**Subtitle rules**:
- `--subtitle`: Full subtitle for the title page (can be longer, e.g., "Comprehensive Platform Assessment & Enhancement Plan").
- `--header-subtitle`: SHORT version for page headers (max 60 chars, e.g., "Platform Assessment & Enhancement Plan"). If omitted, falls back to `--subtitle`.
- If the subtitle exceeds 80 characters, you MUST provide a shorter `--header-subtitle`.

This produces both the Word document AND a companion `<ReportTitle>_Figures.pptx` in the same directory (if the figures manifest is non-empty).

### For PowerPoint output (if a .pptx template was selected):

```bash
python ~/.nexus-hub/scripts/generate_report.py \
  --type generic-pptx \
  --md-files "<output_directory>/<ReportTitle>_merged.md" \
  --title "<title>" \
  --subtitle "<subtitle>" \
  --template "<template_path>" \
  --output "<output_path>"
```

### Path resolution:

- On Windows, expand `~` to `%USERPROFILE%` (e.g., `C:\Users\<username>\.nexus-hub\scripts\generate_report.py`).
- On macOS/Linux, `~` expands normally.
- If the script is not found at the global location, check the project's own `scripts/generate_report.py` as a fallback (for development use within the Nexus-Hub repo itself).

### Error handling:

- If Python is not available: inform the user that Python 3 is required.
- If `python-docx` is not installed: inform the user to run `pip install python-docx`.
- If `python-pptx` is not installed (and PPTX output was requested): inform the user to run `pip install python-pptx`.
- Capture stderr from the script and present any errors clearly to the user.

## Phase 6: Confirm Output and Next Steps

After successful generation, confirm:

1. **Word document path** (or PowerPoint path).
2. **Companion figures PPTX path** (if figures were generated).
3. **Merged Markdown source path** (`_merged.md`, useful for review or re-generation).
4. **Template used** (or "built-in default style" if none).
5. **Sections included** (count of H2 headings in the merged document).
6. **Figures extracted** (count of figures and layout types used).
7. **Version detected** and how it was determined.
8. **Validation results**: Report any warnings from the script's validation output.

Present next steps:

```
What would you like to do next?
1. Open the Word report
2. Open the companion figures file
3. Generate with a different template
4. Generate with different files
5. Regenerate with modifications
6. Done
```

- **Option 1/2**: On Windows, run `start "<path>"`. On macOS, use `open "<path>"`. On Linux, use `xdg-open "<path>"`.
- Do not take any action until the user selects an option.

## Phase 7: Iterative Quality Verification (Loop)

**CRITICAL**: Run this quality gate checklist after EACH generation attempt. If any check fails, fix the merged markdown and/or figures JSON and regenerate. Maximum **3 iterations**.

### Quality Gate Checklist

**1. Template fidelity** (if a template was selected):
- Does the Word output preserve the template's branding (logo, header/footer styling)?
- Is the title page intact with images and formatting from the template?
- Is the first body heading (e.g., "Document's Purpose") present if the template included one?

**2. Single Table of Contents**:
- The merged markdown must NOT contain `# Table of Contents`.
- If the output Word document has multiple TOC sections, remove the heading from the markdown and regenerate.

**3. Writing quality (spot-check 3 random H2 sections)**:
- Does each section open with prose context (not a table or list)?
- Do analytical claims cite concrete metrics?

**4. Figure quality (visual review + validation output)**:

The figure review process has two stages: programmatic validation (stderr warnings) and visual review (image inspection).

**Stage A: Programmatic validation**
- Read stderr from the generation script. Look for `[WARNING]` lines.
- Apply remediation patterns for any warnings found:

| Warning Type | Fix |
|---|---|
| `box_overlap` | Reduce boxes per layer, add an extra layer, or increase layer spacing |
| `text_fit` | Add `\n` line breaks to the label, or abbreviate (DB, API, Auth, Svc) |
| `arrow_collision` | Reorder boxes within the layer so source and target are closer together |
| `space_utilization` (low) | Add detail boxes with content mined from the source documents |
| `font_size` (at minimum) | Shorten the label or split across two lines with `\n` |

**Stage B: Visual review (CRITICAL)**
After generating the companion PPTX, export slides as images for visual inspection:

```bash
python ~/.nexus-hub/scripts/generate_report.py \
  --type companion-pptx \
  --figures-json "<figures_json_path>" \
  --title "<title>" \
  --output "<output_path>" \
  --export-images
```

The script outputs PNG or PDF paths to stderr. For each exported image:
1. **View the image** using the Read tool (it supports image files).
2. **Assess visually**: Is the text readable? Do arrows cross boxes? Is spacing balanced? Does the figure represent its intended content well?
3. **If issues found**: Edit the figures JSON to fix them, then regenerate with `--export-images` again.
4. **Max 3 visual review iterations** per figure set.

Visual quality checklist for each figure:
- Text in all boxes is readable (no truncation, no overflow)
- Arrows route cleanly between boxes without crossing intermediate boxes
- Boxes are evenly spaced with no large empty gaps
- The figure accurately represents the concept described in the report
- Color coding is consistent and meaningful
- Labels use concise text (15-20 chars per line, `\n` for line breaks)

**5. Completeness**:
- Does the merged document contain all unique content from every input file?
- Do `[Figure N:]` placeholders match the figures manifest JSON?

**6. Stop condition**: If all checks pass (including zero figure warnings), or if you have reached the maximum iteration count (3), stop.
