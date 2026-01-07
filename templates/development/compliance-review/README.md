# Compliance & Governance Templates

**Build organization-wide security posture with strategic governance frameworks and AI agent governance**

[← Back to Main README](../../README.md)

---

## Overview

This category provides comprehensive templates for establishing, documenting, and maintaining compliance with industry standards, regulatory requirements, and AI governance best practices. Unlike reactive security reviews (found in [codebase-review/security_review](../codebase-review/security_review/)), these templates focus on **proactive governance architecture** — building the policies, controls, and monitoring systems that ensure long-term compliance and trustworthy AI deployment.

### What's Included

- **Compliance Frameworks**: SOC 2 Type II, ISO 27001, ISO 42001 (AI Management), PCI-DSS, NIST AI RMF

- **Risk Management**: Risk assessment, threat modeling, defense-in-depth strategies

- **Governance Policies**: Security policies, access control, least privilege implementations

- **Privacy Protection**: GDPR, CCPA compliance and data lifecycle management

- **Incident Response**: IR plans, breach protocols, recovery procedures

- **AI Agent Governance**: Lifecycle management, observability, agent-specific controls (4 Pillars Framework)

### Who Should Use This

- **Compliance Teams**: Building audit-ready documentation and evidence

- **Security Architects**: Designing defense-in-depth security controls

- **AI/ML Engineers**: Implementing AI agent governance and monitoring

- **CISOs & Risk Officers**: Establishing organization-wide risk management

- **DevOps/MLOps Teams**: Integrating compliance into CI/CD pipelines

- **Legal & Privacy Teams**: Ensuring GDPR, CCPA, and data protection compliance

---

## The Four Pillars of AI Agent Governance

Modern AI systems — especially agentic AI — require governance frameworks that address unique risks beyond traditional software. The **4 Pillars Framework** ([source: McKinsey](https://www.mckinsey.com/capabilities/risk-and-resilience/our-insights/deploying-agentic-ai-with-safety-and-security-a-playbook-for-technology-leaders), [Bain](https://www.bain.com/insights/building-the-foundation-for-agentic-ai-technology-report-2025/), [AWS](https://aws.amazon.com/blogs/machine-learning/advancing-ai-agent-governance-with-boomi-and-aws-a-unified-approach-to-observability-and-compliance/)) provides the foundation:

### 1. 🔄 Lifecycle Management (Separation of Duties)

**Definition**: Enables multiple teams to manage data and model changes through dev, staging, and prod environments, with version control ensuring proper review at each phase.

**Best Practice**: Separation of duties with promotion workflows and rollback capabilities.

**Key Techniques**:

- **Version Control**: Git, model registries, data versioning, schema evolution

- **CI/CD Pipelines**: Automated testing, build pipelines, deployment automation

- **Environment Management**: Dev/staging/prod isolation, containerization (Docker), infrastructure as code (Terraform)

- **Deployment Orchestration**: Blue-green deployments, canary releases, container orchestration

- **Change Management**: Pull request workflows, approval gates, rollback capabilities, feature flags

**Checklist**:
✅ Can you safely promote changes through environments with proper review and rollback capabilities?

### 2. ⚠️ Risk Management (Defense in Depth)

**Definition**: Implements multiple overlapping defense layers — PII detection, guardrails, compliance controls, and monitoring — to protect against issues from data ingestion to model performance.

**Best Practice**: Defense in depth with layered protection mechanisms.

**Key Techniques**:
- **Data Quality Monitoring**: Schema validation, drift detection, data profiling, anomaly detection

- **PII Detection**: Pattern matching, entity recognition, data classification

- **Guardrails**: Input validation, output filtering, content moderation, safety checks

- **Compliance**: Data classification, audit trails, retention policies, deletion capabilities

- **Model Validation**: Testing frameworks, bias detection, performance monitoring

**Checklist**:
✅ Do you have multiple layers of protection to catch issues before they impact production?

### 3. 🔒 Security (Least Privilege Access)

**Definition**: Ensures agents and users receive only the minimum permissions required for their role. Implemented through encryption, authentication, and granular access controls.

**Best Practice**: Least privilege access with zero-trust security model.

**Key Techniques**:
- **Authentication**: OAuth 2.0, SSO (SAML, OIDC), multi-factor authentication, service principals, API keys

- **Secrets Management**: Key vaults, credential rotation, token management

- **Access Control**: Role-based access control (RBAC), group permissions, attribute-based access

- **Data Protection**: TLS/SSL, encryption at rest, key management, data masking, tokenization

- **Network Security**: Private networks, firewalls, endpoint security

**Checklist**:
✅ Are all your data sources accessible only to authorized agents and users?

### 4. 🔍 Observability (Audit Everything)

**Definition**: Captures comprehensive logs of all system interactions — data access, model actions and predictions — enabling complete traceability and compliance reporting.

**Best Practice**: Audit everything with immutable, tamper-evident logs.

**Key Techniques**:
- **Tracing**: OTel (OpenTelemetry) standard, experiment tracking, model versioning, distributed tracing, prompt optimization

- **Logging**: Audit logs, application logs, inference logging, access logs

- **Monitoring**: Performance monitoring, cost dashboards, drift detection, uptime monitoring

- **Lineage**: Data lineage tracking, model lineage, pipeline visualization, dependency mapping

- **Alerting**: Anomaly detection, threshold alerts, performance degradation alerts, cost overrun alerts

**Checklist**:
✅ Can you trace every tool your agent used, when it ran, what data it accessed, and what it returned?

**Critical Insight**: [80% of organizations have encountered risky behaviors from AI agents](https://www.mckinsey.com/capabilities/risk-and-resilience/our-insights/deploying-agentic-ai-with-safety-and-security-a-playbook-for-technology-leaders), including improper data exposure and unauthorized system access. Robust governance is no longer optional — it's essential for 2025 and beyond.

---

## Quick Start Guide

### Step 1: Assess Your Current State

1. **Identify Compliance Requirements**:
   - Enterprise customers demanding SOC 2/ISO 27001?
   - Handling payment data (PCI-DSS)?
   - EU customers or data subjects (GDPR)?
   - California residents (CCPA)?
   - Deploying AI agents or ML models (NIST AI RMF, ISO 42001)?

2. **Evaluate Existing Controls**:
   - Run [security_review](../codebase-review/security_review/) templates first (reactive assessment)
   - Run [dependency-security-audit](../../../claude-skills-catalog/security/dependency-security-audit/SKILL.md) skill
   - Document current security posture

3. **Identify Gaps**:
   - Compare current state vs. framework requirements
   - Prioritize based on risk and business impact

### Step 2: Choose Your Framework(s)

| Framework | Use Case | Time Investment | Complexity |
|-----------|----------|-----------------|------------|
| **SOC 2 Type II** | Enterprise SaaS, customer trust | 6-8 hours | Advanced |
| **ISO 27001:2022** | Global information security | 6-8 hours | Advanced |
| **ISO 42001** | AI-specific governance | 5-7 hours | Advanced |
| **NIST AI RMF** | US federal AI systems | 4-6 hours | Intermediate |
| **PCI-DSS** | Payment card processing | 7-9 hours | Advanced |
| **GDPR** | EU data subjects | 5-7 hours | Intermediate |
| **CCPA** | California residents | 4-6 hours | Intermediate |
| **AI Agent Governance** | Agentic AI deployment | 6-8 hours | Advanced |

**Recommended Starting Point**:
- **Traditional SaaS**: Start with SOC 2 + ISO 27001

- **AI/ML Systems**: Start with NIST AI RMF + AI Agent Governance (4 Pillars)

- **Payment Processing**: Start with PCI-DSS + SOC 2

- **EU Markets**: Start with GDPR + ISO 27001

### Step 3: Implement by Pillar

For AI systems, implement governance following the 4 Pillars sequence:

1. **Security + Risk Management** (Foundation) - 2-3 weeks
   - Implement least privilege access controls
   - Deploy guardrails and PII detection
   - Set up data classification

2. **Observability** (Visibility) - 1-2 weeks
   - Deploy comprehensive logging (OTel standard)
   - Set up monitoring dashboards
   - Implement lineage tracking

3. **Lifecycle Management** (Sustainability) - 2-3 weeks
   - Establish CI/CD pipelines
   - Create environment promotion workflows
   - Implement rollback procedures

4. **Continuous Improvement** (Ongoing) - Indefinite
   - Regular audits and reviews
   - Update controls as threats evolve
   - Expand coverage to new systems

### Step 4: Document and Audit

1. **Generate Documentation**:
   - Use [documentation-generation](../documentation-generation/) templates for technical docs
   - Create policy documents using governance_policies templates
   - Generate SBOM using [sbom_generation](../documentation-generation/sbom_generation/)

2. **Collect Evidence**:
   - Screenshots of configurations
   - Logs demonstrating controls in action
   - Test results and coverage reports
   - Access control matrices

3. **Prepare for Audit**:
   - Organize evidence by control objective
   - Create control narratives
   - Document exceptions and remediations

---

## Integration with Existing Templates

### Prerequisite Templates (Run These First)

| Template | Purpose | Integration Point |
|----------|---------|-------------------|
| [security_review](../codebase-review/security_review/) | Identify vulnerabilities | Findings feed into risk assessments |
| [dependency-security-audit](../../../claude-skills-catalog/security/dependency-security-audit/SKILL.md) | CVE scanning, SBOM | Supply chain risk for compliance |
| [licensing-compliance-check](../../../claude-skills-catalog/security/licensing-compliance/SKILL.md) | License auditing | Legal compliance documentation |

### Related Templates (Use Together)

| Template | Purpose | Integration Point |
|----------|---------|-------------------|
| [tests-generation](../tests-generation/) | Comprehensive testing | Evidence of security testing controls |
| [documentation-generation](../documentation-generation/) | Technical documentation | Control documentation, runbooks |
| [codebase-cleanup](../codebase-cleanup/) | Remove vulnerabilities | Remediation following assessments |

### Workflow Example: SOC 2 Audit Preparation

```
1. security_review (Python)           → Identify vulnerabilities
2. dependency-security-audit (Skill)  → CVE scan, generate SBOM
3. licensing-compliance-check (Skill) → Verify license compliance
   ↓
4. compliance_governance/compliance_frameworks/python_soc2_compliance.md
   → Map findings to SOC 2 controls
   → Document control implementations
   → Create evidence packages
   ↓
5. compliance_governance/incident_response/python_incident_response_plan.md
   → Document breach response procedures
   → Create escalation workflows
   ↓
6. Audit-ready evidence package
```

---

## Sub-Phase Directory Structure

### 1. Compliance Frameworks

**Path**: [`compliance_frameworks/`](./compliance_frameworks/)

Comprehensive implementation guides for industry-standard compliance frameworks:

- **SOC 2 Type II**: Trust Services Criteria (Security, Availability, Confidentiality, Processing Integrity, Privacy)

- **ISO 27001:2022**: Information Security Management Systems (114 controls)

- **ISO 42001:2023**: Artificial Intelligence Management Systems (AI-specific)

- **NIST AI RMF 1.0**: AI Risk Management Framework (Govern, Map, Measure, Manage)

- **PCI-DSS v4.0**: Payment Card Industry Data Security Standard

**Time Investment**: 6-8 hours per framework
**Languages**: Python, JavaScript, Java, C#, Go, C, C++

[→ View Compliance Frameworks Templates](./compliance_frameworks/)

### 2. Risk Management

**Path**: [`risk_management/`](./risk_management/)

Implement defense-in-depth strategies with multiple protection layers:

- **Risk Assessment**: Systematic threat identification, vulnerability scoring, risk mitigation

- **Threat Modeling**: Attack surface analysis, STRIDE methodology, data flow diagrams

- **Defense in Depth**: Layered security controls, guardrails, monitoring

**Time Investment**: 4-6 hours per template
**Languages**: Python, JavaScript, Java, C#, Go, C, C++

[→ View Risk Management Templates](./risk_management/)

### 3. Governance Policies

**Path**: [`governance_policies/`](./governance_policies/)

Establish organization-wide security policies and access controls:

- **Security Policies**: Comprehensive security policy documentation, control frameworks

- **Access Control**: RBAC implementation, least privilege, zero-trust architecture

**Time Investment**: 4-5 hours per template
**Languages**: Python, JavaScript, Java, C#, Go, C, C++

[→ View Governance Policies Templates](./governance_policies/)

### 4. Privacy Protection

**Path**: [`privacy_protection/`](./privacy_protection/)

Ensure compliance with global privacy regulations:

- **GDPR Compliance**: EU General Data Protection Regulation (data subject rights, DPIAs, breach notification)

- **CCPA Compliance**: California Consumer Privacy Act (consumer rights, opt-out, data deletion)

**Time Investment**: 5-7 hours per template
**Languages**: Python, JavaScript, Java, C#, Go, C, C++

[→ View Privacy Protection Templates](./privacy_protection/)

### 5. Incident Response

**Path**: [`incident_response/`](./incident_response/)

Prepare for security incidents with documented response procedures:

- **Incident Response Plans**: Detection, containment, eradication, recovery, lessons learned

- **Breach Protocols**: Notification procedures, regulatory reporting, stakeholder communication

**Time Investment**: 4-6 hours per template
**Languages**: Python, JavaScript, Java, C#, Go, C, C++

[→ View Incident Response Templates](./incident_response/)

### 6. AI Agent Governance

**Path**: [`ai_agent_governance/`](./ai_agent_governance/)

Specialized governance for autonomous AI agents following the 4 Pillars Framework:

- **Lifecycle Management**: Version control, CI/CD for AI, environment promotion, rollback procedures

- **Agent Observability**: Comprehensive tracing (OTel), audit logging, lineage tracking, compliance reporting

- **Agent Security**: Service principal authentication, API key management, least privilege for agents

- **Agent Risk Controls**: Guardrails, PII detection, output validation, behavioral monitoring

**Time Investment**: 6-8 hours per template
**Languages**: Python, JavaScript, Java, C#, Go, C, C++ (with AI framework integrations)

[→ View AI Agent Governance Templates](./ai_agent_governance/)

---

## Success Criteria

### Compliance Metrics

- [ ] All required frameworks documented with control mappings
- [ ] Control implementation evidence collected and organized
- [ ] Policies documented and communicated to teams
- [ ] Audit-ready evidence packages created
- [ ] Regular review and update schedules established

### AI Governance Metrics (4 Pillars)

- [ ] **Lifecycle**: Can promote changes safely through dev → staging → prod with rollback
- [ ] **Risk**: Multiple defense layers operational (PII detection, guardrails, monitoring)
- [ ] **Security**: Least privilege implemented, all data sources locked down
- [ ] **Observability**: Complete audit trail of agent actions, data access, and outputs

### Technical Metrics

- [ ] Security review findings mapped to compliance controls
- [ ] Dependency vulnerabilities tracked and remediated
- [ ] License compliance verified and documented
- [ ] SBOM generated and maintained
- [ ] Incident response procedures tested (tabletop exercises)

### Organizational Metrics

- [ ] Compliance training completed for relevant teams
- [ ] Policies acknowledged and signed by employees
- [ ] Risk register maintained and reviewed quarterly
- [ ] Third-party risk assessments completed
- [ ] Continuous monitoring implemented

---

## Framework Comparison Matrix

| Framework | Focus Area | Industry | Audit Type | Renewal | AI-Specific |
|-----------|-----------|----------|------------|---------|-------------|
| **SOC 2 Type II** | Trust Services | SaaS, Cloud | Third-party | Annual | Partial (2025 updates) |
| **ISO 27001:2022** | Info Security | Global | Certification | 3-year | No (but applicable) |
| **ISO 42001:2023** | AI Management | Global | Certification | 3-year | Yes |
| **NIST AI RMF** | AI Risk | US Federal | Self/External | Ongoing | Yes |
| **PCI-DSS v4.0** | Payment Security | E-commerce | QSA | Annual | No |
| **GDPR** | Data Privacy | EU | Self/DPA | Ongoing | Partial (automated decisions) |
| **CCPA** | Consumer Privacy | California | Self/AG | Ongoing | Partial (automated decisions) |

**Key Trends for 2025**:
- SOC 2 auditors increasingly expect [AI-specific controls](https://www.soc2certification.com/blog/soc2-compliance-for-ai-ml-companies) (model security, bias testing, inference monitoring)
- ISO 27001:2022 updated with [greater emphasis on cloud security and threat intelligence](https://www.itgovernance.co.uk/blog/how-to-address-ai-security-risks-with-iso-27001)
- NIST AI RMF moving from planning to [operationalization](https://www.ispartnersllc.com/blog/nist-ai-rmf-2025-updates-what-you-need-to-know-about-the-latest-framework-changes/) in 2025
- [80% of organizations report risky AI agent behaviors](https://www.mckinsey.com/capabilities/risk-and-resilience/our-insights/deploying-agentic-ai-with-safety-and-security-a-playbook-for-technology-leaders) — governance frameworks are essential

---

## Estimated Time Investment

### By Framework (per language)

| Framework | Assessment | Implementation | Documentation | Testing | Total |
|-----------|-----------|----------------|---------------|---------|-------|
| SOC 2 Type II | 1-2 hours | 3-4 hours | 1-2 hours | 1 hour | 6-8 hours |
| ISO 27001 | 1-2 hours | 3-4 hours | 1-2 hours | 1 hour | 6-8 hours |
| ISO 42001 | 1 hour | 3-4 hours | 1-2 hours | 1 hour | 5-7 hours |
| NIST AI RMF | 1 hour | 2-3 hours | 1 hour | 1 hour | 4-6 hours |
| PCI-DSS | 2 hours | 4-5 hours | 1-2 hours | 1 hour | 7-9 hours |
| GDPR | 1-2 hours | 2-3 hours | 1-2 hours | 1 hour | 5-7 hours |
| CCPA | 1 hour | 2-3 hours | 1 hour | 1 hour | 4-6 hours |
| AI Agent Gov | 1-2 hours | 3-4 hours | 1-2 hours | 1 hour | 6-8 hours |

### Full Category Implementation

**Phased Approach** (Recommended):
- **Phase 1** (Weeks 1-4): SOC 2 + ISO 27001 + Risk Assessment = 28 hours

- **Phase 2** (Weeks 5-6): GDPR + CCPA + Incident Response = 18 hours

- **Phase 3** (Weeks 7-8): AI Agent Governance + NIST AI RMF = 14 hours

- **Phase 4** (Weeks 9-10): PCI-DSS + ISO 42001 + Policies = 20 hours

**Total**: 80 hours (10 weeks at 8 hours/week)

**Accelerated Approach** (for urgent compliance needs):
- Focus on single framework + AI governance = 12-16 hours
- Expand to additional frameworks as needed

---

## Best Practices

### 1. Start with Foundations

Don't try to implement everything at once. Prioritize:
1. **Security Review** (reactive): Identify current vulnerabilities
2. **Risk Assessment** (proactive): Understand threat landscape
3. **Primary Framework** (compliance): SOC 2 or ISO 27001
4. **AI Governance** (if applicable): 4 Pillars for AI agents

### 2. Document Everything

Compliance is about **evidence**, not just implementation:
- Screenshots of security configurations
- Log files demonstrating monitoring
- Test results showing validation
- Policy acknowledgments from teams
- Change management records

### 3. Automate Where Possible

Manual compliance doesn't scale. Automate:
- Security scanning (SAST, DAST, SCA)
- Dependency vulnerability monitoring
- Log aggregation and analysis
- Policy enforcement (pre-commit hooks, CI/CD gates)
- Compliance monitoring dashboards

### 4. Integrate with Development

Shift left on compliance:
- Security reviews in pull requests
- Compliance checks in CI/CD pipelines
- Automated testing for security controls
- Policy-as-code (OPA, Sentinel)

### 5. Prepare for Change

Frameworks evolve, regulations change:
- Version control for policy documents
- Regular review cycles (quarterly/annually)
- Subscribe to framework update notifications
- Maintain flexibility in implementations

### 6. Leverage Existing Work

Don't start from scratch:
- Use findings from [security_review](../codebase-review/security_review/) templates
- Reference [dependency-security-audit](../../../claude-skills-catalog/security/dependency-security-audit/SKILL.md) results
- Build on [documentation-generation](../documentation-generation/) outputs
- Integrate with existing [tests-generation](../tests-generation/) suites

---

## Common Pitfalls to Avoid

### ❌ Checkbox Compliance

**Problem**: Treating compliance as a one-time checklist exercise.

**Solution**: Implement continuous monitoring and regular reviews. Compliance is a journey, not a destination.

### ❌ Security Theater

**Problem**: Implementing controls that look good on paper but don't actually reduce risk.

**Solution**: Focus on defense-in-depth with multiple effective layers. Test controls regularly.

### ❌ Scope Creep

**Problem**: Trying to implement every possible framework simultaneously.

**Solution**: Start with business-critical frameworks. Expand based on customer/regulatory requirements.

### ❌ Documentation Debt

**Problem**: Implementing controls without documenting evidence.

**Solution**: Document as you implement. Retroactive documentation is painful and incomplete.

### ❌ AI Governance Blind Spots

**Problem**: Applying traditional software controls to AI without AI-specific governance.

**Solution**: Use [AI Agent Governance](./ai_agent_governance/) templates for AI-specific risks (bias, explainability, behavioral drift).

### ❌ Ignoring Third Parties

**Problem**: Focusing only on internal controls while ignoring third-party risks.

**Solution**: Conduct vendor risk assessments. Include supply chain in compliance scope.

---

## Resources and References

### Official Framework Documentation

- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework) - Official NIST AI RMF site
- [ISO 27001:2022 Standard](https://www.iso.org/standard/27001) - Information Security Management
- [ISO 42001:2023 Standard](https://www.iso.org/standard/81230.html) - AI Management Systems
- [SOC 2 Trust Services Criteria](https://www.aicpa.org/interestareas/frc/assuranceadvisoryservices/aicpasoc2report) - AICPA official guide
- [PCI Security Standards](https://www.pcisecuritystandards.org/) - PCI-DSS documentation
- [GDPR Official Text](https://gdpr-info.eu/) - EU regulation text and guidance
- [CCPA Official Site](https://oag.ca.gov/privacy/ccpa) - California Attorney General

### AI Governance Research

- [McKinsey: Agentic AI Security Playbook](https://www.mckinsey.com/capabilities/risk-and-resilience/our-insights/deploying-agentic-ai-with-safety-and-security-a-playbook-for-technology-leaders)
- [Bain: Building Foundation for Agentic AI](https://www.bain.com/insights/building-the-foundation-for-agentic-ai-technology-report-2025/)
- [AWS: AI Agent Governance](https://aws.amazon.com/blogs/machine-learning/advancing-ai-agent-governance-with-boomi-and-aws-a-unified-approach-to-observability-and-compliance/)
- [AWS: Agentic AI Security Scoping Matrix](https://aws.amazon.com/blogs/security/the-agentic-ai-security-scoping-matrix-a-framework-for-securing-autonomous-ai-systems/)
- [Medium: Four Pillars of AI Agent Governance](https://medium.com/@tahirbalarabe2/what-is-ai-agent-governance-the-four-pillars-of-ai-agent-governance-d9b045475b3e)

### Compliance Implementation Guides

- [SOC 2 Compliance for AI/ML Companies](https://www.soc2certification.com/blog/soc2-compliance-for-ai-ml-companies)
- [ISO 27001 and AI Security](https://www.itgovernance.co.uk/blog/how-to-address-ai-security-risks-with-iso-27001)
- [NIST AI RMF 2025 Updates](https://www.ispartnersllc.com/blog/nist-ai-rmf-2025-updates-what-you-need-to-know-about-the-latest-framework-changes/)
- [AI Risk Management Best Practices](https://www.superblocks.com/blog/ai-risk-management)

### Tools and Automation

- **Security Scanning**: Snyk, Dependabot, Trivy, Bandit (Python), ESLint (JS)

- **Compliance Automation**: Drata, Vanta, Secureframe, TrustCloud

- **AI Observability**: OpenTelemetry, MLflow, Weights & Biases, LangSmith

- **Policy as Code**: Open Policy Agent (OPA), HashiCorp Sentinel

- **SBOM Generation**: Syft, CycloneDX, SPDX tools

---

## Getting Help

### Internal Resources

- **Security Issues**: Start with [security_review](../codebase-review/security_review/) templates

- **Dependency Issues**: Use [dependency-security-audit](../../../claude-skills-catalog/security/dependency-security-audit/SKILL.md) skill

- **Documentation**: Leverage [documentation-generation](../documentation-generation/) templates

- **Testing**: Reference [tests-generation](../tests-generation/) for security test patterns

### External Support

- **Auditors**: Engage qualified auditors early for SOC 2/ISO 27001

- **Legal Counsel**: Consult for GDPR/CCPA compliance interpretation

- **Security Consultants**: For penetration testing and security architecture reviews

- **Framework Training**: Official courses for NIST AI RMF, ISO 27001, etc.

---

[← Back to Main README](../../README.md)
