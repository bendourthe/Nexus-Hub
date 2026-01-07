# Compliance Frameworks

**Comprehensive implementation guides for industry-standard compliance frameworks**

[← Back to Compliance & Governance](../README.md) | [← Back to Main README](../../../README.md)

---

## Overview

This sub-phase provides detailed, language-specific templates for implementing and documenting compliance with major regulatory and industry frameworks. Each template includes control mappings, code-level implementations, evidence collection guidance, and audit preparation checklists.

### Available Frameworks

1. **SOC 2 Type II** - Trust Services Criteria for SaaS/Cloud providers
2. **ISO 27001:2022** - Information Security Management Systems (114 controls)
3. **ISO 42001:2023** - Artificial Intelligence Management Systems (NEW for 2025)
4. **NIST AI RMF 1.0** - AI Risk Management Framework (4 functions: Govern, Map, Measure, Manage)
5. **PCI-DSS v4.0** - Payment Card Industry Data Security Standard

---

## Framework Comparison

| Framework | Primary Focus | Target Industry | Certification Required | AI-Specific | Time Investment |
|-----------|--------------|-----------------|------------------------|-------------|-----------------|
| **SOC 2 Type II** | Trust & Security | SaaS, Cloud Services | Yes (Auditor) | Partial (2025) | 6-8 hours |
| **ISO 27001:2022** | Information Security | Global/All Industries | Yes (Certification Body) | No (but applicable) | 6-8 hours |
| **ISO 42001:2023** | AI Management | AI/ML Systems | Yes (Certification Body) | Yes | 5-7 hours |
| **NIST AI RMF 1.0** | AI Risk Management | US Federal/All | No (Voluntary) | Yes | 4-6 hours |
| **PCI-DSS v4.0** | Payment Security | E-commerce, Retail | Yes (QSA) | No | 7-9 hours |

---

## Quick Start

### Step 1: Identify Your Requirements

**Ask yourself:**
- Do enterprise customers require SOC 2 reports?
- Are you pursuing international markets (ISO 27001)?
- Are you building AI/ML systems (ISO 42001, NIST AI RMF)?
- Do you process payment cards (PCI-DSS)?
- What does your sales team hear most from prospects?

**Common Combinations:**
- **Early-stage SaaS**: SOC 2 Type II

- **Enterprise SaaS**: SOC 2 + ISO 27001

- **AI/ML SaaS**: SOC 2 + NIST AI RMF + ISO 42001

- **E-commerce**: PCI-DSS + SOC 2

- **Global Enterprise**: ISO 27001 + ISO 42001 (if AI)

### Step 2: Run Prerequisites

Before starting compliance implementation, gather current security posture:

1. **Security Review**: Run [security_review](../../codebase-review/security_review/) for your language
2. **Dependency Audit**: Run [dependency-security-audit](../../../../claude-skills-catalog/security/dependency-security-audit/SKILL.md) skill
3. **License Check**: Run [licensing-compliance](../../../../claude-skills-catalog/security/licensing-compliance/SKILL.md) skill

These findings will feed into your compliance documentation.

### Step 3: Choose Your Language Template

Select the template matching your primary codebase language:

| Language | SOC 2 | ISO 27001 | ISO 42001 | NIST AI RMF | PCI-DSS |
|----------|-------|-----------|-----------|-------------|---------|
| **Python** | [View](./python_soc2_compliance.md) | [View](./python_iso27001_implementation.md) | [View](./python_iso42001_ai_management.md) | [View](./python_nist_ai_rmf.md) | [View](./python_pci_dss_compliance.md) |
| **JavaScript** | [View](./javascript_soc2_compliance.md) | [View](./javascript_iso27001_implementation.md) | [View](./javascript_iso42001_ai_management.md) | [View](./javascript_nist_ai_rmf.md) | [View](./javascript_pci_dss_compliance.md) |
| **Java** | [View](./java_soc2_compliance.md) | [View](./java_iso27001_implementation.md) | [View](./java_iso42001_ai_management.md) | [View](./java_nist_ai_rmf.md) | [View](./java_pci_dss_compliance.md) |
| **C#** | [View](./csharp_soc2_compliance.md) | [View](./csharp_iso27001_implementation.md) | [View](./csharp_iso42001_ai_management.md) | [View](./csharp_nist_ai_rmf.md) | [View](./csharp_pci_dss_compliance.md) |
| **Go** | [View](./go_soc2_compliance.md) | [View](./go_iso27001_implementation.md) | [View](./go_iso42001_ai_management.md) | [View](./go_nist_ai_rmf.md) | [View](./go_pci_dss_compliance.md) |
| **C** | [View](./c_soc2_compliance.md) | [View](./c_iso27001_implementation.md) | [View](./c_iso42001_ai_management.md) | [View](./c_nist_ai_rmf.md) | [View](./c_pci_dss_compliance.md) |
| **C++** | [View](./cpp_soc2_compliance.md) | [View](./cpp_iso27001_implementation.md) | [View](./cpp_iso42001_ai_management.md) | [View](./cpp_nist_ai_rmf.md) | [View](./cpp_pci_dss_compliance.md) |

### Step 4: Follow the Template

Each template follows this structure:

1. **Overview** - Framework purpose, scope, business value
2. **Compliance Requirements** - Control objectives mapped to language-specific implementations
3. **Code-Level Implementation** - Concrete code examples for each control
4. **Documentation Requirements** - Policy templates and evidence artifacts
5. **Risk Assessment** - Threat modeling specific to framework
6. **Audit Preparation** - Evidence collection checklist
7. **Continuous Monitoring** - Ongoing compliance maintenance
8. **Cross-References** - Links to related templates

---

## Framework Deep Dives

### SOC 2 Type II

**Purpose**: Demonstrate trust and security controls to enterprise customers.

**Trust Services Criteria (TSC)**:
- **Security (CC)**: Common Criteria - foundational controls

- **Availability (A)**: System uptime and performance

- **Confidentiality (C)**: Protection of confidential information

- **Processing Integrity (PI)**: Complete, valid, accurate, timely processing

- **Privacy (P)**: Collection, use, retention, disclosure, disposal of PI

**Key Changes for AI/ML Systems (2025)**:
- Model security controls (protection against extraction attacks)
- Bias testing and fairness monitoring
- Inference logging and audit trails
- Training data protection and lineage
- Automated decision documentation

**Audit Process**: 3-12 months observation period, annual renewal

**Languages**: [Python](./python_soc2_compliance.md) | [JavaScript](./javascript_soc2_compliance.md) | [Java](./java_soc2_compliance.md) | [C#](./csharp_soc2_compliance.md) | [Go](./go_soc2_compliance.md) | [C](./c_soc2_compliance.md) | [C++](./cpp_soc2_compliance.md)

### ISO 27001:2022

**Purpose**: Establish comprehensive Information Security Management System (ISMS).

**Control Categories (114 controls across 4 themes)**:
- **Organizational Controls** (37 controls): Policies, organizational structure, HR security

- **People Controls** (8 controls): Before, during, and after employment

- **Physical Controls** (14 controls): Physical security, equipment security

- **Technological Controls** (34 controls): Access control, cryptography, development security

**New in 2022 Version**:
- Threat intelligence (Control 5.7)
- Information security for cloud services (Control 5.23)
- ICT readiness for business continuity (Control 5.30)
- Web filtering (Control 8.23)

**Certification Process**: Gap analysis → Implementation → Internal audit → Certification audit → 3-year cycle

**Languages**: [Python](./python_iso27001_implementation.md) | [JavaScript](./javascript_iso27001_implementation.md) | [Java](./java_iso27001_implementation.md) | [C#](./csharp_iso27001_implementation.md) | [Go](./go_iso27001_implementation.md) | [C](./c_iso27001_implementation.md) | [C++](./cpp_iso27001_implementation.md)

### ISO 42001:2023 (NEW)

**Purpose**: First international standard for AI Management Systems (AIMS).

**Key Focus Areas**:
- **Ethical AI**: Transparency, fairness, accountability in AI operations

- **Risk Management**: AI-specific risk identification and mitigation

- **Data Governance**: Training data quality, lineage, and protection

- **Model Lifecycle**: Development, deployment, monitoring, decommissioning

- **Human Oversight**: Human-in-the-loop requirements and escalation

**Control Objectives**:
- AI system design and development controls
- Data management for AI
- Model validation and testing
- Bias detection and mitigation
- Explainability and transparency
- Continuous monitoring and improvement

**Unique Value**: Demonstrates commitment to responsible AI beyond just security.

**Certification Process**: Similar to ISO 27001, NEW standard launched 2023

**Languages**: [Python](./python_iso42001_ai_management.md) | [JavaScript](./javascript_iso42001_ai_management.md) | [Java](./java_iso42001_ai_management.md) | [C#](./csharp_iso42001_ai_management.md) | [Go](./go_iso42001_ai_management.md) | [C](./c_iso42001_ai_management.md) | [C++](./cpp_iso42001_ai_management.md)

### NIST AI RMF 1.0

**Purpose**: Voluntary framework for managing AI risks (US-focused but globally applicable).

**Four Functions**:
1. **GOVERN** (16 sub-categories): Cultivate AI risk management culture, policies, processes
2. **MAP** (17 sub-categories): Context establishment, risk identification, categorization
3. **MEASURE** (12 sub-categories): Assess, analyze, track AI risks
4. **MANAGE** (11 sub-categories): Prioritize, respond to, monitor AI risks

**Key Characteristics**:
- Voluntary (not regulatory)
- Technology-neutral
- Use- and sector-agnostic
- Focuses on trustworthy AI characteristics

**Generative AI Profile** (July 2024): Specific guidance for GAI systems

**Implementation**: Self-assessment with optional third-party validation

**Languages**: [Python](./python_nist_ai_rmf.md) | [JavaScript](./javascript_nist_ai_rmf.md) | [Java](./java_nist_ai_rmf.md) | [C#](./csharp_nist_ai_rmf.md) | [Go](./go_nist_ai_rmf.md) | [C](./c_nist_ai_rmf.md) | [C++](./cpp_nist_ai_rmf.md)

### PCI-DSS v4.0

**Purpose**: Secure payment card data (cardholder data and sensitive authentication data).

**12 Requirements across 6 Goals**:
1. **Build and Maintain Secure Network** (Req 1-2): Firewalls, secure configurations
2. **Protect Account Data** (Req 3-4): Encryption at rest/transit, strong cryptography
3. **Maintain Vulnerability Management** (Req 5-6): Anti-malware, secure development
4. **Implement Strong Access Control** (Req 7-9): Need-to-know, unique IDs, physical access
5. **Regularly Monitor and Test** (Req 10-11): Logging, security testing
6. **Maintain Information Security Policy** (Req 12): Policies, awareness, incident response

**Key Changes in v4.0** (March 2022):
- Customized approach (flexibility in meeting requirements)
- Enhanced authentication methods
- Targeted risk analyses
- Phased implementation through March 2025

**Validation**: Annual assessment by Qualified Security Assessor (QSA) or Self-Assessment Questionnaire (SAQ)

**Languages**: [Python](./python_pci_dss_compliance.md) | [JavaScript](./javascript_pci_dss_compliance.md) | [Java](./java_pci_dss_compliance.md) | [C#](./csharp_pci_dss_compliance.md) | [Go](./go_pci_dss_compliance.md) | [C](./c_pci_dss_compliance.md) | [C++](./cpp_pci_dss_compliance.md)

---

## Implementation Workflow

### Phase 1: Gap Analysis (Week 1)

1. **Run Security Assessments**:
   ```bash
   # Run security review
   Use: security_review/{language}_security_review.md

   # Run dependency audit
   Use: dependency-security-audit skill

   # Run license check
   Use: licensing-compliance-check skill
   ```

2. **Document Current Controls**:
   - What security controls are already implemented?
   - What logging/monitoring exists?
   - What policies are documented?
   - What evidence is available?

3. **Identify Gaps**:
   - Compare current state vs. framework requirements
   - Prioritize by risk and business impact
   - Estimate remediation effort

### Phase 2: Implementation (Weeks 2-5)

4. **Follow Language-Specific Template**:
   - Work through each control section
   - Implement code-level security patterns
   - Configure monitoring and logging
   - Document policies and procedures

5. **Collect Evidence**:
   - Screenshots of configurations
   - Log exports demonstrating controls
   - Test results (security tests, penetration tests)
   - Policy acknowledgments
   - Change management records

6. **Cross-Reference Integration**:
   - Link security_review findings to control implementations
   - Use dependency-security-audit results for supply chain controls
   - Reference tests_generation suites for testing controls

### Phase 3: Documentation (Week 6)

7. **Create Control Documentation**:
   - Control narrative descriptions
   - Evidence matrices
   - Data flow diagrams
   - Network architecture diagrams

8. **Prepare Audit Package**:
   - Organized evidence by control
   - Control matrices
   - Policies and procedures
   - Test results and validation

### Phase 4: Audit and Certification (Weeks 7-12)

9. **Internal Readiness Assessment**:
   - Conduct mock audit
   - Identify missing evidence
   - Remediate final gaps

10. **External Audit** (SOC 2, ISO 27001, PCI-DSS):
    - Engage qualified auditor/assessor
    - Provide evidence package
    - Respond to audit findings
    - Remediate exceptions

11. **Certification** (ISO 27001, ISO 42001):
    - Submit to certification body
    - Stage 1 audit (documentation review)
    - Stage 2 audit (on-site assessment)
    - Receive certification

---

## Evidence Collection Checklist

### Common Evidence Types (All Frameworks)

- [ ] **Screenshots**:
  - Security configurations (MFA, password policies, encryption)
  - Access control settings (RBAC, least privilege)
  - Monitoring dashboards (logging, alerting)
  - Backup configurations

- [ ] **Logs**:
  - Authentication logs (successful/failed logins)
  - Authorization logs (access attempts)
  - Change logs (code deployments, config changes)
  - Security event logs (WAF blocks, IDS alerts)

- [ ] **Test Results**:
  - Vulnerability scan reports
  - Penetration test reports
  - Security test execution results
  - Code coverage reports

- [ ] **Documentation**:
  - Security policies (approved, dated, signed)
  - System architecture diagrams
  - Data flow diagrams
  - Network diagrams
  - Incident response plans

- [ ] **Records**:
  - Employee security training completion
  - Policy acknowledgments
  - Vendor risk assessments
  - Change management tickets
  - Incident response records

### Framework-Specific Evidence

**SOC 2**:
- [ ] Description of the system (boundaries, components)
- [ ] Control matrix mapping TSC to controls
- [ ] Management assertions
- [ ] Vendor management documentation

**ISO 27001**:
- [ ] Statement of Applicability (SoA)
- [ ] Risk assessment and treatment plan
- [ ] ISMS scope document
- [ ] Internal audit reports
- [ ] Management review minutes

**ISO 42001** (AI-specific):
- [ ] AI system inventory and risk classification
- [ ] Model development documentation
- [ ] Training data documentation and lineage
- [ ] Bias testing results
- [ ] Explainability documentation
- [ ] Human oversight procedures

**NIST AI RMF**:
- [ ] AI RMF implementation playbook
- [ ] Function-specific documentation (Govern, Map, Measure, Manage)
- [ ] Trustworthy characteristics assessment
- [ ] Risk tracking and mitigation records

**PCI-DSS**:
- [ ] Network segmentation evidence
- [ ] Cardholder Data Environment (CDE) documentation
- [ ] Quarterly vulnerability scans (Approved Scanning Vendor)
- [ ] Annual penetration test report
- [ ] PCI-DSS v4.0 Self-Assessment Questionnaire (SAQ) if applicable

---

## Success Criteria

### Implementation Metrics

- [ ] All applicable framework controls documented
- [ ] Code-level implementations complete for language
- [ ] Evidence collected and organized by control
- [ ] Policies documented and communicated to teams
- [ ] Continuous monitoring configured

### Audit Readiness Metrics

- [ ] Gap analysis complete with 0 critical gaps
- [ ] Evidence package organized and accessible
- [ ] Control narratives written and reviewed
- [ ] Mock audit completed with findings remediated
- [ ] Audit/certification scheduled

### Ongoing Compliance Metrics

- [ ] Quarterly reviews scheduled
- [ ] Continuous monitoring dashboards operational
- [ ] Incident response procedures tested
- [ ] Employee training completion >95%
- [ ] Vendor risk assessments current

---

## Common Pitfalls

### ❌ Starting Too Late

**Problem**: Attempting to achieve compliance weeks before customer deadline.

**Solution**: Start 6-12 months before certification needed. SOC 2 Type II requires 3-12 months observation.

### ❌ Treating as One-Time Project

**Problem**: Implementing controls, getting certified, then neglecting maintenance.

**Solution**: Compliance is continuous. Implement ongoing monitoring and quarterly reviews.

### ❌ Copy-Paste Documentation

**Problem**: Generic policies copied from templates without customization.

**Solution**: Customize all documentation to reflect actual implementations. Auditors will test alignment.

### ❌ Missing AI-Specific Controls

**Problem**: Applying traditional software controls to AI/ML systems without addressing AI-specific risks.

**Solution**: Use ISO 42001, NIST AI RMF templates. Address bias, explainability, model security, data lineage.

### ❌ Inadequate Evidence

**Problem**: Implementing controls without collecting evidence during observation period.

**Solution**: Document everything as you go. Screenshots, logs, test results, training records.

---

## Resources

### Official Documentation

- [SOC 2 Trust Services Criteria](https://www.aicpa.org/interestareas/frc/assuranceadvisoryservices/aicpasoc2report) - AICPA official guide
- [ISO 27001:2022](https://www.iso.org/standard/27001) - ISO official standard
- [ISO 42001:2023](https://www.iso.org/standard/81230.html) - AI Management Systems standard
- [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework) - Official framework site
- [PCI Security Standards](https://www.pcisecuritystandards.org/) - Official PCI-DSS documentation

### Implementation Guides

- [SOC 2 for AI/ML Companies](https://www.soc2certification.com/blog/soc2-compliance-for-ai-ml-companies)
- [ISO 27001 and AI](https://www.itgovernance.co.uk/blog/how-to-address-ai-security-risks-with-iso-27001)
- [NIST AI RMF Playbook](https://www.nist.gov/itl/ai-risk-management-framework/nist-ai-rmf-playbook)
- [PCI-DSS v4.0 Summary of Changes](https://www.pcisecuritystandards.org/documents/PCI-DSS-v3-2-1-to-v4-0-Summary-of-Changes-r1.pdf)

---

[← Back to Compliance & Governance](../README.md) | [← Back to Main README](../../../README.md)
