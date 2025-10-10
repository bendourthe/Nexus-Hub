# JavaScript Context Analysis

## Objective
Establish comprehensive understanding of the JavaScript project before conducting detailed code review. This phase gathers context about purpose, architecture, dependencies, and current state to inform all subsequent review activities.

## Output Directory Structure

All outputs should be saved in organized directories:

```
review/context_analysis/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `review/context_analysis/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Analysis Checklist

### Project Understanding
- [ ] Project purpose and target audience identified
- [ ] Core features and use cases documented
- [ ] Development stage assessed (prototype, production, legacy)
- [ ] Key stakeholders and maintainers identified
- [ ] Project documentation reviewed (README, CONTRIBUTING, docs/)

### Architecture & Structure
- [ ] Entry points and main modules mapped
- [ ] Module organization evaluated (CommonJS vs ES6 modules)
- [ ] Design patterns identified (MVC, Redux, component-based, etc.)
- [ ] Configuration management approach documented
- [ ] Environment-specific settings catalogued

### Dependency Analysis
- [ ] Direct dependencies listed with versions (package.json)
- [ ] Development dependencies separated from production
- [ ] Outdated packages identified
- [ ] Security vulnerabilities in dependencies checked
- [ ] License compatibility verified

### Build & Deployment
- [ ] Build process documented (webpack, rollup, parcel, vite)
- [ ] Test execution approach understood
- [ ] CI/CD pipelines identified (GitHub Actions, GitLab CI, Jenkins)
- [ ] Deployment targets documented (Node.js, browser, serverless)
- [ ] Environment variables and secrets management reviewed

### Codebase Metrics
- [ ] Lines of code measured (total, per module)
- [ ] Cyclomatic complexity assessed
- [ ] Module coupling and cohesion evaluated
- [ ] Code duplication percentage calculated
- [ ] Comment density analyzed

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# JavaScript Project Context Analysis

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="review/context_analysis"
```

Create the required subdirectories:
```bash
mkdir -p ${OUTPUT_DIR}/templates
mkdir -p ${OUTPUT_DIR}/assets
mkdir -p ${OUTPUT_DIR}/exports
```

**Directory Structure:**
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Throughout this prompt:**
- All generated files should be saved with the `${OUTPUT_DIR}/` prefix
- Examples:
  - Reports and documentation → `${OUTPUT_DIR}/exports/report.md`
  - Template files → `${OUTPUT_DIR}/templates/template.yaml`
  - Diagrams and images → `${OUTPUT_DIR}/assets/diagram.png`

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

## Analysis Protocol

Please perform a comprehensive context analysis of this JavaScript project following this protocol:

## Phase 1: Project Discovery

1. **Identify Project Fundamentals**
   - Read and summarize README.md and primary documentation
   - Determine project purpose, target audience, and key features
   - Identify development stage (prototype/production/legacy)
   - List primary maintainers and stakeholders
   - Determine runtime environment (Node.js version, browser targets)

2. **Map Repository Structure**
   - Identify all source directories (src/, lib/, app/, etc.)
   - Locate test directories and test frameworks used
   - Find configuration files (package.json, tsconfig.json, .babelrc, etc.)
   - Document documentation locations (docs/, wiki, external)
   - Identify build output directories (dist/, build/, public/)

## Phase 2: Architecture Understanding

1. **Entry Points & Core Modules**
   - Identify main entry points (index.js, main.js, server.js, etc.)
   - Map core business logic modules
   - Document public API surface
   - Identify internal vs external interfaces
   - Determine if using TypeScript or plain JavaScript

2. **Design Patterns & Architecture**
   - Identify architectural style (SPA, SSR, microservices, monorepo)
   - Document design patterns in use (Observer, Factory, Singleton, etc.)
   - Assess framework usage (React, Vue, Angular, Express, Fastify)
   - Map data flow through the application
   - Identify state management approach (Redux, MobX, Context, Zustand)
   - Document configuration and settings management

3. **Module System & Dependencies**
   - Identify module system (CommonJS, ES6 modules, or mixed)
   - Create dependency graph between internal modules
   - Identify circular dependencies
   - Assess module coupling (tight/loose)
   - Evaluate separation of concerns

## Phase 3: Dependency Analysis

1. **Dependency Inventory**
   ```bash
   # List all dependencies
   npm list --all

   # View production dependencies only
   npm list --prod

   # View dependency tree
   npm ls
   ```
   - List all dependencies from package.json
   - Separate production vs development dependencies
   - Document Node.js version requirements (engines field)
   - Identify platform-specific dependencies

2. **Dependency Health Check**
   ```bash
   # Check for outdated packages
   npm outdated

   # Check for security vulnerabilities
   npm audit

   # Get detailed vulnerability report
   npm audit --json

   # Check for deprecated packages
   npm-check
   ```

3. **License & Compatibility**
   ```bash
   # Check licenses
   npx license-checker --summary

   # Detailed license report
   npx license-checker --json > ${OUTPUT_DIR}/exports/licenses.json
   ```
   - List licenses for all dependencies
   - Flag potential license conflicts
   - Identify deprecated or unmaintained packages

## Phase 4: Build & Deployment

1. **Build System**
   - Document build configuration (webpack.config.js, rollup.config.js, etc.)
   - Identify build tools (webpack, rollup, parcel, vite, esbuild)
   - Review package.json scripts (build, start, dev, etc.)
   - Check for build optimization (minification, tree-shaking, code splitting)
   - Assess transpilation setup (Babel, TypeScript)

2. **Test Infrastructure**
   - Identify testing frameworks (Jest, Mocha, Jasmine, Vitest, Cypress)
   - Document test execution commands
   - Review test configuration files (jest.config.js, .mocharc.json)
   - Assess test organization (unit, integration, e2e)
   - Check for test utilities and mocking libraries

3. **CI/CD Pipeline**
   - Locate CI/CD configuration (.github/workflows, .gitlab-ci.yml, etc.)
   - Document automated checks (linting, testing, security scans)
   - Review deployment automation
   - Identify quality gates and merge requirements
   - Check for automated npm publish workflows

4. **Environment Management**
   - Document environment variables and configuration
   - Review secrets management approach
   - Identify environment-specific settings (dev/staging/prod)
   - Check for .env files or environment documentation
   - Review configuration libraries (dotenv, config, etc.)

## Phase 5: Codebase Metrics

1. **Size & Complexity Metrics**
   ```bash
   # Lines of code
   find src -name "*.js" -o -name "*.ts" | xargs wc -l

   # Using cloc for detailed breakdown
   npx cloc src/

   # Cyclomatic complexity
   npx complexity-report src/

   # Or use escomplex
   npx escomplex src/**/*.js
   ```

2. **Quality Indicators**
   ```bash
   # ESLint static analysis
   npx eslint src/ --format json --output-file eslint-report.json

   # Check for code duplication
   npx jscpd src/
   ```
   - Calculate code-to-comment ratio
   - Measure average function/method length
   - Identify large files (>500 lines)
   - Count TODO/FIXME/HACK comments

3. **Bundle Size Analysis** (for frontend projects)
   ```bash
   # Webpack bundle analyzer
   npx webpack-bundle-analyzer dist/stats.json

   # Or use source-map-explorer
   npx source-map-explorer dist/*.js
   ```

## Phase 6: Documentation Review

1. **Code Documentation**
   - Assess JSDoc coverage (functions, classes, modules)
   - Review JSDoc format and completeness
   - Check TypeScript type annotations coverage (if applicable)
   - Evaluate inline comment quality

2. **Project Documentation**
   - Review README completeness
   - Check for CONTRIBUTING.md
   - Assess CHANGELOG.md or release notes
   - Review API documentation (if applicable)
   - Check for architecture decision records (ADR)

## Phase 7: JavaScript-Specific Analysis

1. **Language Features**
   - Identify ECMAScript version target (ES5, ES6/ES2015, ES2020, etc.)
   - Check for modern JavaScript features usage (async/await, destructuring, etc.)
   - Assess TypeScript adoption (if applicable)
   - Review use of strict mode

2. **Frontend-Specific** (if applicable)
   - Identify UI framework/library (React, Vue, Angular, Svelte)
   - Check bundler configuration
   - Review CSS approach (CSS-in-JS, modules, preprocessors)
   - Assess accessibility considerations
   - Check browser compatibility targets

3. **Backend-Specific** (if applicable)
   - Identify Node.js framework (Express, Fastify, Koa, NestJS)
   - Review middleware architecture
   - Check database integration approach
   - Assess API design (REST, GraphQL, gRPC)
   - Review authentication/authorization approach

## Output Format

Please provide a comprehensive context report with the following structure:

### Executive Summary
- **Project Name**: [name]
- **Purpose**: [1-2 sentence description]
- **Stage**: [prototype/production/legacy]
- **Runtime**: [Node.js version / Browser targets]
- **Language**: [JavaScript / TypeScript]
- **Architecture**: [SPA/SSR/API/Full-stack]

### Project Structure
```
project/
├── [key directories and their purposes]
├── [entry points]
├── [configuration files]
└── [build output]
```

### Architecture Overview
- **Framework**: [React/Vue/Express/etc.]
- **Module System**: [CommonJS/ES6/Mixed]
- **Design Patterns**: [patterns identified]
- **State Management**: [Redux/Context/etc.]
- **Build Tool**: [webpack/vite/etc.]
- **Key Dependencies**: [critical external packages]

### Dependency Summary
| Package | Version | Purpose | Status | Security |
|---------|---------|---------|--------|----------|
| [name] | [version] | [usage] | [current/outdated] | [safe/vulnerable] |

### Build & Deployment
- **Build System**: [tool and configuration]
- **Bundle Size**: [size in KB/MB]
- **Test Framework**: [Jest/Mocha/etc.]
- **CI/CD**: [platform and key workflows]
- **Deployment**: [target environments]

### Codebase Metrics
- **Total Lines**: [number] (excluding tests and node_modules)
- **JavaScript**: [lines] / **TypeScript**: [lines]
- **Average Complexity**: [cyclomatic complexity score]
- **Bundle Size**: [production bundle size]
- **Duplication**: [percentage]
- **Documentation**: [JSDoc/comment coverage %]

### Key Findings
1. **Strengths**: [positive observations]
2. **Concerns**: [potential issues to investigate]
3. **Dependencies**: [outdated or vulnerable packages]
4. **Documentation**: [gaps or areas needing improvement]
5. **Performance**: [bundle size concerns, if applicable]

### Recommendations for Review Focus
Based on this context, the following review areas should be prioritized:
1. [Area 1] - [reason]
2. [Area 2] - [reason]
3. [Area 3] - [reason]

### Next Steps
- [ ] Proceed with code quality review
- [ ] Conduct security audit (especially if vulnerable dependencies found)
- [ ] Perform performance analysis (bundle size, runtime performance)
- [ ] Review test coverage and quality

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p ${OUTPUT_DIR}/context_analysis/analysis_scripts
mkdir -p ${OUTPUT_DIR}/context_analysis/supporting_data
```

**Save files as follows**:

- Main report → `review/context_analysis/context_analysis_report.md`

- Findings data → `review/context_analysis/context_analysis_findings.json`

- Analysis scripts → `review/context_analysis/analysis_scripts/`

- Supporting data → `review/context_analysis/supporting_data/`

## Notes
- Save this context report - it will inform all subsequent review phases
- Flag any critical issues discovered during context gathering
- Update dependency vulnerabilities before detailed code review
- Use this as baseline for measuring improvement over time
- For TypeScript projects, include type coverage analysis
- For frontend projects, consider Lighthouse audit for initial performance baseline
~~~
---

## Verify Directory Structure

After completing all phases, verify the output structure:

```bash
tree ${OUTPUT_DIR}
```

Expected structure:
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates and scripts
├── assets/            # Images, diagrams, supplementary files
└── exports/           # Final publishable artifacts and reports
```

**Verification checklist:**
- [ ] All directories created successfully
- [ ] All files saved in correct subdirectories
- [ ] No files created in repository root
- [ ] Directory structure matches expected layout
