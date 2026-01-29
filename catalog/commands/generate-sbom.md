# Generate SBOM Command

Analyze the codebase and generate a comprehensive Software Bill of Materials (SBOM).

## Usage
Run this command to inventory all external dependencies, libraries, and modules used in the project.

## Steps
1.  **Activate Skill**: `security/sbom-generation`
2.  **Scan**: Perform a deep traversal of the repository to find dependency manifests (package.json, requirements.txt, etc.).
3.  **Analyze**: Extract component names, versions, and licenses.
4.  **Report**:
    *   Provide a **Human-Readable Summary** (Markdown Table).
    *   Generate a **Machine-Readable Artifact** (JSON block in CycloneDX or SPDX format).

## Output File
Ask the user if they want to save the output to `stb-sbom.json` or `sbom.md`.
