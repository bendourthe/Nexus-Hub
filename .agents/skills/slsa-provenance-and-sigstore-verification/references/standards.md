# Framework standards for slsa-provenance-and-sigstore-verification

## MITRE D3FEND D3-SCI

- Framework: MITRE D3FEND.
- Why this skill declares it: Build Provenance Verification (SLSA/Sigstore) uses this identifier as a teaching hook, not as a complete coverage claim.
- Source: https://d3fend.mitre.org/technique/D3-SCI/

## NIST CSF 2.0 PR.DS

- Framework: NIST CSF 2.0.
- Why this skill declares it: Build Provenance Verification (SLSA/Sigstore) uses this identifier as a teaching hook, not as a complete coverage claim.
- Source: https://csrc.nist.gov/publications/detail/cswp/29/final

## NIST CSF 2.0 ID.SC

- Framework: NIST CSF 2.0.
- Why this skill declares it: Build Provenance Verification (SLSA/Sigstore) uses this identifier as a teaching hook, not as a complete coverage claim.
- Source: https://csrc.nist.gov/publications/detail/cswp/29/final

---

## OWASP Top 10 for Agentic Applications (2026)

Identifiers verified 2026-09-07 against the OWASP source. The full ten-entry set with official titles lives in `catalog/skills/security/security-framework-mapping/references/standards.md`; only the identifiers this skill is tagged with are explained below.

### ASI04 -- Agentic Supply Chain Vulnerabilities

- Framework: OWASP Top 10 for Agentic Applications, 2026 edition.
- Why this skill maps to it: Verifies SLSA provenance and Sigstore signatures before an image or binary is admitted, so an artifact an agent will execute or depend on is checked at admit time rather than trusted by origin.
- Source: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
