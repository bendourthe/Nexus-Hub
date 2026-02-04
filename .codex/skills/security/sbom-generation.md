# Skill: Generate SBOM (Software Bill of Materials)

## Description
This skill enables the AI to scan a codebase, identify dependencies across multiple programming languages, and generate a standardized SBOM.

## Capabilities

### 1. Dependency Detection
Recursively scan for manifest files:
*   **Python**: `requirements.txt`, `pyproject.toml`, `Pipfile`
*   **JavaScript/TypeScript**: `package.json`, `pnpm-lock.yaml`, `yarn.lock`
*   **Java**: `pom.xml`, `build.gradle`
*   **C#/.NET**: `*.csproj`, `packages.config`
*   **Go**: `go.mod`
*   **C++**: `conanfile.txt`, `vcpkg.json`, `CMakeLists.txt` (FetchContent)

### 2. Analysis Logic
For each manifest found:
1.  **Extract Package Name**: The library or module name.
2.  **Extract Version**: Explicit version or constraint.
3.  **Infer License**: If listed (e.g., in `package.json`), include it.
4.  **Identify Scope**: Runtime vs Dev/Test dependency.

### 3. Output Formats
The AI can output the data in:
*   **Markdown Table**: For quick human review.
*   **CycloneDX JSON**: Standard cybersecurity format (skeleton).
*   **SPDX Lite**: Simplified SPDX format.

## Instructions for AI
When invoking this skill:
1.  **Map** the file structure first.
2.  **Read** all relevant manifest files.
3.  **Synthesize** a consolidated list of unique dependencies.
4.  **Generate** the requested output format (default to Markdown Table + JSON block).


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
