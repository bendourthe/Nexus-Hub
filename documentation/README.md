# Documentation Templates

Design a complete narrative for your project—from inline docstrings to compliance-grade SBOMs—using the six linked phases in this directory.

---

## Quick navigation
- [Start here](#start-here)
- [Phase overview](#phase-overview)
- [Recommended paths](#recommended-paths)
- [Phase details](#phase-details)
- [Compliance toolkit](#compliance-toolkit)
- [Keep docs healthy](#keep-docs-healthy)
- [Support](#support)

---

## Start here
1. Pick your language folder (Python today) and open the phase prompt you need.
2. Paste the prompt into your AI assistant, gather the requested context, and generate the draft.
3. Review and edit for tone, accuracy, and audience fit before publishing.
4. Repeat for the remaining phases to keep documentation consistent end-to-end.

**Tip:** Keep docstrings and comments in sync with code changes first—later phases rely on them.

---

## Phase overview
| Phase | Focus | Primary outcome | Prompt |
| --- | --- | --- | --- |
| 1 | Docstrings | Complete inline documentation with parameters, returns, and examples | [Python](docstrings/python_docstrings.md) |
| 2 | Comments | High-signal code annotations explaining intent and trade-offs | [Python](comments/python_comments.md) |
| 3 | User docs | README, quick-start, and troubleshooting content for end users | [Python](user_docs/python_user_docs.md) |
| 4 | Technical docs | Architecture, decisions, data flows, and deployment runbooks | [Python](technical_docs/python_technical_docs.md) |
| 5 | API docs | Endpoint reference with authentication, examples, and error handling | [Python](api_docs/python_api_docs.md) |
| 6 | SBOM & compliance | CycloneDX/SPDX inventory plus NTIA/EU CRA reporting notes | [Python](sbom/python_sbom.md) |

---

## Recommended paths
| Goal | Run these phases | Time estimate |
| --- | --- | --- |
| ⚡ Essentials for prototypes | 1 → 2 → 3 | ~3–5 h |
| 🎯 Production-ready docs | 1 → 2 → 3 → 4 → 5 | ~6–10 h |
| 🛡️ Regulated release / OSS | 1 → 6 → 3 → 4 → 5 → 2 | ~12–16 h |

*Reorder phases when you already have strong coverage—just keep docstrings (1) and SBOM (6) current before major releases.*

---

## Phase details

### Phase 1 – Docstrings
- Apply consistent style (Google, NumPy, or Sphinx) across modules.
- Document parameters, return values, raises, and usage examples.
- Flag TODOs for missing context so downstream docs stay honest.
- **Prompt:** [Python docstrings](docstrings/python_docstrings.md)

### Phase 2 – Strategic comments
- Capture intent, design decisions, and performance notes—never restate the code.
- Mark risks (`TODO`, `FIXME`, `NOTE`) with owners and due dates.
- Keep comments brief; link to design docs when context spans multiple files.
- **Prompt:** [Python comments](comments/python_comments.md)

### Phase 3 – User documentation
- Refresh the project README, quick-start, and FAQ with current workflows.
- Add task-oriented guides and troubleshooting steps for support teams.
- Provide upgrade notes when breaking changes land.
- **Prompt:** [Python user docs](user_docs/python_user_docs.md)

### Phase 4 – Technical documentation
- Map architecture, data flows, and component responsibilities.
- Record key decisions, alternatives considered, and trade-offs.
- Include deployment, rollback, and operational runbook guidance.
- **Prompt:** [Python technical docs](technical_docs/python_technical_docs.md)

### Phase 5 – API documentation
- List every public endpoint, payload schema, success/failure codes, and auth requirements.
- Supply runnable request/response examples and SDK snippets.
- Note rate limits, versioning strategy, and deprecation timelines.
- **Prompt:** [Python API docs](api_docs/python_api_docs.md)

### Phase 6 – SBOM & compliance
- Generate CycloneDX or SPDX manifests with tooling noted in the prompt.
- Track license obligations, vulnerabilities, and remediation owners.
- Summarize NTIA/EU CRA checkpoints, including attestation artifacts.
- **Prompt:** [Python SBOM](sbom/python_sbom.md)

---

## Compliance toolkit
- Automate manifests with `cyclonedx-bom`, `syft`, or `pip-licenses` as guided.
- Store SBOM outputs under `docs/sbom/` with version tags for auditing.
- Link security reports (SAST/DAST) and vendor attestations to Phase 6 deliverables.
- Keep a changelog of documentation updates alongside code releases.

---

## Keep docs healthy
- Add documentation tasks to definition-of-done for every feature.
- Include doc coverage in code reviews—especially comments, README updates, and API examples.
- Schedule quarterly audits for accessibility, terminology, and tooling drift.
- Pair SBOM regeneration with dependency upgrades to avoid stale inventories.

---

## Support
- Need the bigger picture? Start at the [repository root](../README.md).
- Looking for prompts for other practices? Explore [system prompts](../system_prompts/README.md) or [test development templates](../test_development/README.md).
- Questions or suggestions? Share feedback with your documentation lead so we can improve the templates.

*Last updated: October 2025*  
*Current templates: Python (6 phases complete)*
