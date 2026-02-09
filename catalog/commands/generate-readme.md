---
description: Analyze the codebase structure, dependencies, and key files to generate a production-quality README.md with standardized sections.
---

# Generate README Command

Analyze the codebase structure, dependencies, and key files to generate a comprehensive, production-quality README.md following modern documentation best practices.

## Phase 1: Codebase Analysis

1.  **Activate Skill**: `documentation/user-documentation`

2.  **Detect Project Type**:
    *   Scan for dependency manifests to identify the primary language(s) and framework(s):
        *   `package.json` (Node.js/JavaScript/TypeScript)
        *   `requirements.txt` / `pyproject.toml` / `setup.py` / `Pipfile` (Python)
        *   `pom.xml` / `build.gradle` (Java)
        *   `go.mod` (Go)
        *   `Cargo.toml` (Rust)
        *   `*.csproj` / `*.sln` (C#/.NET)
        *   `composer.json` (PHP)
        *   `Gemfile` (Ruby)
    *   Parse the manifest to extract: project name, version, description, scripts/commands, and key dependencies.

3.  **Map Directory Structure**:
    *   Use Glob to identify key folders: `src/`, `lib/`, `app/`, `docs/`, `tests/`, `test/`, `config/`, `scripts/`, `public/`, `static/`, `migrations/`, `api/`.
    *   Generate a directory tree (top 2 levels) for the Architecture section.

4.  **Check Existing Documentation**:
    *   Look for: `README.md`, `CONTRIBUTING.md`, `LICENSE`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`.
    *   If a `README.md` already exists, read it and note which sections are present and which are missing.

5.  **Scan Configuration & Infrastructure**:
    *   Find: `.env.example`, `.env.sample`, `docker-compose.yml`, `Dockerfile`, `Makefile`.
    *   Check for CI/CD: `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `.circleci/`, `azure-pipelines.yml`.
    *   Check for linters/formatters: `.eslintrc*`, `.prettierrc*`, `pyproject.toml [tool.black]`, `.editorconfig`.

6.  **Identify Entry Points**:
    *   Find main files: `main.*`, `index.*`, `app.*`, `server.*`, `cli.*`, `manage.py`.
    *   Look for CLI commands, API routers, or exported modules.
    *   Check `package.json` scripts, `Makefile` targets, or `pyproject.toml [tool.poetry.scripts]`.

7.  **Detect Special Features**:
    *   Databases: Look for ORM configs, migration folders, database connection files.
    *   APIs: Look for route definitions, OpenAPI/Swagger specs, GraphQL schemas.
    *   Microservices: Look for `docker-compose.yml` with multiple services, service directories.
    *   ML/Data: Look for model files, notebooks (`*.ipynb`), data pipeline configs.
    *   Auth: Look for auth middleware, OAuth configs, JWT utilities.

## Phase 2: README Generation

Using the analysis from Phase 1, generate a README.md with the following structure. **Adapt sections based on project type** (e.g., skip Deployment for a library, skip API docs for a CLI tool, skip Docker for projects without containers).

````markdown
# [Project Name]
[One-line compelling tagline based on project purpose]

> [Brief 1-2 sentence value proposition]
> [What problem does this solve?]

---

## Quick Start

[Provide the absolute fastest way to get started, aim for under 5 steps]

### Prerequisites
- [List required software, versions, accounts]

### Installation
```bash
# Step 1: Clone
git clone [repo-url]
cd [project-name]

# Step 2: Install dependencies
[language-specific install command]

# Step 3: Configure
[copy .env.example or config setup]

# Step 4: Run
[start command]
```

### Verification
[How to verify it's working, e.g., "Visit http://localhost:3000"]

---

## Table of Contents
- [About](#about)
- [Features](#features)
- [Architecture](#architecture)
- [Usage](#usage)
- [Configuration](#configuration)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

---

## About

[2-3 paragraph description covering:]
- What is this project?
- Why was it built?
- Who is it for?
- What makes it unique or better?

### Built With
[Generate technology badges from detected dependencies using shields.io]
![Language](https://img.shields.io/badge/[language]-[color]?style=for-the-badge&logo=[logo]&logoColor=white)

---

## Features

- **[Feature 1]**: [Description extracted from code analysis]
- **[Feature 2]**: [Description]
- **[Feature 3]**: [Description]

---

## Architecture

[High-level overview of system architecture: patterns, layers, data flow]

### Project Structure
```
[Auto-generated directory tree, top 2 levels, with brief annotations]
project-name/
├── src/              # Source code
│   ├── api/          # API route handlers
│   ├── models/       # Data models
│   └── utils/        # Shared utilities
├── tests/            # Test suite
├── docs/             # Documentation
├── config/           # Configuration files
└── scripts/          # Build and deployment scripts
```

---

## Usage

[Common use cases with examples]

### Basic Usage
```bash
[Primary command or code example]
```

### API Reference (if applicable)
[Key endpoints, methods, or exported functions]

### CLI Commands (if applicable)
| Command | Description |
|---------|-------------|
| `[cmd]` | [What it does] |

---

## Configuration

[How to configure the application]

### Environment Variables
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `[VAR]`  | [Purpose]   | [value] | Yes/No   |

### Configuration Files
[Reference any config files and their key options]

---

## Development

### Local Setup
```bash
[Steps to set up development environment]
```

### Code Style
[Linting, formatting tools, and conventions detected]

### Branch Strategy
[If detectable from CI/CD config or CONTRIBUTING.md]

---

## Testing

```bash
[How to run tests]
```

[Mention test framework, coverage tools, and any test categories detected]

---

## Deployment

[Production deployment instructions, adapt based on detected infrastructure:]
- **Docker**: Include `docker build` and `docker-compose up` commands if Dockerfile found
- **Cloud**: Reference detected CI/CD pipelines
- **Manual**: Step-by-step production setup if no automation detected

---

## Contributing

[If CONTRIBUTING.md exists, reference it. Otherwise, provide standard guidelines:]
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

## License

[Detect from LICENSE file. If not found, note "No license file detected" and recommend adding one.]
````

### Section Adaptation Rules

Apply these rules to keep the README relevant:

*   **Libraries/Packages**: Emphasize Installation, API Reference, and Usage. Skip Deployment.
*   **Web Applications**: Emphasize Quick Start, Configuration, and Deployment. Include API docs if backend.
*   **CLI Tools**: Emphasize Installation, CLI Commands table, and Usage examples. Skip Architecture if simple.
*   **APIs/Microservices**: Emphasize Architecture, API Reference, Configuration, and Deployment.
*   **Data/ML Projects**: Include a Data section covering data sources, model training, and pipeline steps.
*   **Monorepos**: Add a Packages/Services section listing each sub-project with its purpose.

### Badge Generation Reference

Generate shields.io badges based on detected technologies:

| Technology | Badge URL Pattern |
|-----------|-------------------|
| Python | `https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54` |
| JavaScript | `https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E` |
| TypeScript | `https://img.shields.io/badge/typescript-%23007ACC.svg?style=for-the-badge&logo=typescript&logoColor=white` |
| React | `https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB` |
| Node.js | `https://img.shields.io/badge/node.js-6DA55F?style=for-the-badge&logo=node.js&logoColor=white` |
| Go | `https://img.shields.io/badge/go-%2300ADD8.svg?style=for-the-badge&logo=go&logoColor=white` |
| Rust | `https://img.shields.io/badge/rust-%23000000.svg?style=for-the-badge&logo=rust&logoColor=white` |
| Java | `https://img.shields.io/badge/java-%23ED8B00.svg?style=for-the-badge&logo=openjdk&logoColor=white` |
| C# | `https://img.shields.io/badge/c%23-%23239120.svg?style=for-the-badge&logo=csharp&logoColor=white` |
| Docker | `https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white` |
| PostgreSQL | `https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white` |
| MongoDB | `https://img.shields.io/badge/MongoDB-%234ea94b.svg?style=for-the-badge&logo=mongodb&logoColor=white` |
| Redis | `https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white` |

## Phase 3: Output

1.  **Check for Existing README**:
    *   If `README.md` exists, ask the user:
        > "A README.md already exists. Would you like me to: (A) Overwrite it, (B) Save as README_GENERATED.md for comparison, or (C) Merge missing sections into the existing file?"
    *   If no README exists, write directly to `README.md`.

2.  **Write the File**:
    *   Save the generated content to the chosen filename in the project root.

3.  **Present Summary**:
    *   Output a brief summary in the chat listing:
        *   Detected project type and technologies
        *   Sections included (and any sections intentionally omitted with reason)
        *   File path where the README was saved
        *   Suggestions for manual additions (e.g., screenshots, diagrams, specific usage examples)


## Phase: Iterative Refinement (Loop)

**CRITICAL**: This is an iterative process. You cannot assume the first pass is perfect.
Perform the following refinement loop up to **3 times** (or as specified by the user's input, e.g., "5 iterations"):

1.  **Analyze**: Look at the generated output.
    *   Is it complete?
    *   Are there any obvious errors?
    *   Does it meet the user's requirements?
    *   Are the detected technologies and features accurate?
    *   Is the Quick Start section actually actionable (not just placeholders)?
2.  **Refine**:
    *   Fix any issues found.
    *   Replace placeholder text with concrete, project-specific content.
    *   Ensure all code examples are syntactically correct for the detected language.
    *   Verify badge URLs render correctly.
3.  **Stop**:
    *   If you are confident the result is excellent.
    *   OR if you have reached the maximum iteration count.
