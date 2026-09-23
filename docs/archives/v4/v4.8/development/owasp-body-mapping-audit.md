# OWASP body-mapping audit - v4.8 WN-F

**Date**: 2026-09-23. **Scope**: 15 `owasp_agentic`-tagged skills, 24 declared identifiers on merged `develop` at `61be98de`. **Source**: [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) and its linked 57-page 2026 document. This is a manual snapshot, not an automated semantic proof or a claim that future edits remain covered.

Each row compares the declared identifier and its `references/standards.md` rationale with an actionable instruction in the skill body. The OWASP document still lists ASI01 through ASI10 with the titles used by the catalog. No tag was added or removed in this audit.

| Skill | Declared ASI IDs | Body action supporting the mapping | Verdict |
|---|---|---|---|
| `ai-billing-safeguards` | ASI10 | Enforce session and task caps; terminate a runaway loop on breach. | Supported |
| `agent-access-policy` | ASI02, ASI03 | Default-deny tool actions; scope file and capability grants to least privilege. | Supported |
| `agent-orchestration-primitives` | ASI07, ASI08 | Use explicit node contracts; verify upstream results before fan-out and version shared state. | Supported |
| `label-gated-agent-pipelines` | ASI07, ASI09 | Accept only pipeline-authored stage handoffs; require a maintainer label for each advance. | Supported |
| `loop-engineering` | ASI10 | Require an iteration cap, command-derived exit, and checker-owned termination. | Supported |
| `agentic-endpoint-hardening` | ASI02, ASI05 | Inventory agent-writable configuration that trusted tools later execute across the sandbox seam. | Supported |
| `honeytoken-placement` | ASI10 | Page a human on first touch of a never-used canary and treat the trip as an incident. | Supported |
| `agent-execution-isolation` | ASI02, ASI03, ASI05, ASI07 | Minimize in-loop tools, broker credentials outside the agent, confine execution, and scope shared writable paths per session. | Supported |
| `ai-agent-governance` | ASI10 | Check process evidence and require human review of learning that alters goal measurement. | Supported |
| `ai-attack-patterns` | ASI01, ASI02, ASI06 | Test goal hijack, tool abuse, and retrieval-path poisoning under authorization and translate findings to defenses. | Supported |
| `agent-memory` | ASI06 | Require source provenance for writes; supersede and roll back poisoned facts via the append-only chain. | Supported |
| `prompt-injection-defense` | ASI01 | Treat fetched content and handoffs as data, not instruction authority. | Supported |
| `egress-redaction` | ASI03 | Block credentials and authentication material before an egress boundary. | Supported |
| `skill-security-scan` | ASI04 | Adjudicate scanner findings and assign an install verdict before admitting an external skill. | Supported |
| `slsa-provenance-and-sigstore-verification` | ASI04 | Require signatures and provenance attestations before admitting an executable artifact. | Supported |

**Residual risk**: A passing validator proves ID shape and the existence of a rationale, not that the body still teaches it. A later body edit can silently invalidate any row. The release workflow now calls `security-framework-mapping` for a fresh manual review and requires an unverified verdict to remain visible rather than being counted as coverage.
