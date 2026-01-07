# Risk Management

**Implement defense-in-depth strategies with multiple protection layers**

[← Back to Compliance & Governance](../README.md) | [← Back to Main README](../../../README.md)

---

## Overview

This sub-phase provides comprehensive risk management templates implementing **Defense in Depth** — multiple overlapping security layers that protect against threats from data ingestion to model performance.

### Available Templates

1. **Risk Assessment** - Systematic threat identification, vulnerability scoring, risk mitigation
2. **Threat Modeling** - Attack surface analysis, STRIDE methodology, data flow diagrams
3. **Defense in Depth** - Layered security controls, guardrails, monitoring strategies

### The Defense in Depth Principle

**Definition**: Implements multiple, independent protection layers — PII detection, guardrails, compliance controls, and monitoring — to protect against issues from data ingestion to model performance.

**Best Practice**: Multiple overlapping defenses ensure that if one layer fails, others catch the issue.

**Key Techniques**:
- **Data Quality Monitoring**: Schema validation, drift detection, data profiling, anomaly detection

- **PII Detection**: Pattern matching, entity recognition, data classification

- **Guardrails**: Input validation, output filtering, content moderation, safety checks

- **Compliance**: Data classification, audit trails, retention policies, deletion capabilities

- **Model Validation**: Testing frameworks, bias detection, performance monitoring

**Checklist**: ✅ Do you have multiple layers of protection to catch issues before they impact production?

---

## Quick Start

### Step 1: Identify Risk Areas

**For Traditional Applications**:
- Data breaches (unauthorized access)
- Injection attacks (SQL, command, XSS)
- Authentication/authorization failures
- Cryptographic failures
- Configuration errors

**For AI/ML Systems** (Additional):
- Training data poisoning
- Model extraction attacks
- Adversarial inputs
- Bias and fairness issues
- Explainability failures
- Drift and performance degradation

### Step 2: Choose Your Template

| Language | Risk Assessment | Threat Modeling | Defense in Depth |
|----------|-----------------|-----------------|------------------|
| **Python** | [View](./python_risk_assessment.md) | [View](./python_threat_modeling.md) | [View](./python_defense_in_depth.md) |
| **JavaScript** | [View](./javascript_risk_assessment.md) | [View](./javascript_threat_modeling.md) | [View](./javascript_defense_in_depth.md) |
| **Java** | [View](./java_risk_assessment.md) | [View](./java_threat_modeling.md) | [View](./java_defense_in_depth.md) |
| **C#** | [View](./csharp_risk_assessment.md) | [View](./csharp_threat_modeling.md) | [View](./csharp_defense_in_depth.md) |
| **Go** | [View](./go_risk_assessment.md) | [View](./go_threat_modeling.md) | [View](./go_defense_in_depth.md) |
| **C** | [View](./c_risk_assessment.md) | [View](./c_threat_modeling.md) | [View](./c_defense_in_depth.md) |
| **C++** | [View](./cpp_risk_assessment.md) | [View](./cpp_threat_modeling.md) | [View](./cpp_defense_in_depth.md) |

### Step 3: Follow the Risk Management Process

1. **Identify Assets**: What needs protection? (data, models, systems, reputation)
2. **Identify Threats**: What could go wrong? (STRIDE: Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege)
3. **Assess Vulnerabilities**: Where are the weaknesses?
4. **Calculate Risk**: Likelihood × Impact = Risk Score
5. **Prioritize**: High-risk items first
6. **Mitigate**: Implement controls (defense in depth)
7. **Monitor**: Continuous risk assessment

---

## Template Deep Dives

### Risk Assessment Templates

**Purpose**: Systematic identification and prioritization of risks.

**Process**:
1. Asset inventory (data, systems, models)
2. Threat identification (internal, external, AI-specific)
3. Vulnerability assessment (code analysis, penetration testing)
4. Risk scoring (likelihood × impact matrix)
5. Risk treatment decisions (accept, mitigate, transfer, avoid)
6. Risk register maintenance

**Code Examples Include**:
- Automated vulnerability scanning
- Risk scoring algorithms
- Risk register database schemas
- Integration with security_review findings

**Time Investment**: 4-6 hours per language

**Use Cases**:
- SOC 2 CC3.2 (Identify and analyze risk)
- ISO 27001 Control 5.7 (Threat intelligence)
- NIST AI RMF Map function

### Threat Modeling Templates

**Purpose**: Understand attack vectors and design secure architectures.

**Methodologies**:
- **STRIDE**: Spoofing, Tampering, Repudiation, Information Disclosure, DoS, Elevation of Privilege

- **PASTA**: Process for Attack Simulation and Threat Analysis

- **Attack Trees**: Visual representation of attack paths

- **Data Flow Diagrams**: Map data movement and trust boundaries

**Code Examples Include**:
- Threat modeling automation
- Data flow diagram generation
- Attack surface analysis
- Trust boundary identification

**Time Investment**: 4-6 hours per language

**Use Cases**:
- Application security design
- Security architecture reviews
- Compliance documentation (SOC 2, ISO 27001)
- AI model security analysis

### Defense in Depth Templates

**Purpose**: Implement layered security controls.

**Layers**:
1. **Perimeter**: Firewalls, WAF, DDoS protection
2. **Network**: Segmentation, IDS/IPS, VPN
3. **Host**: OS hardening, anti-malware, patching
4. **Application**: Input validation, output encoding, authentication
5. **Data**: Encryption, access controls, DLP
6. **AI-Specific**: Guardrails, PII detection, bias monitoring

**Code Examples Include**:
- Input validation frameworks
- Output sanitization
- PII detection and redaction
- Guardrails for AI agents
- Rate limiting and throttling
- Content moderation

**Time Investment**: 5-7 hours per language

**Use Cases**:
- Implementing security controls for compliance
- Protecting AI/ML systems
- Preventing data breaches
- Meeting defense-in-depth requirements (NIST, ISO)

---

## Risk Management for AI/ML Systems

### Unique AI Risks

1. **Training Data Risks**
   - **Data Poisoning**: Malicious data injected into training set

   - **Data Leakage**: Sensitive information memorized by model

   - **Bias**: Historical biases perpetuated in predictions

2. **Model Risks**
   - **Model Extraction**: Stealing model via API queries

   - **Adversarial Attacks**: Crafted inputs fool the model

   - **Model Inversion**: Recovering training data from model

3. **Deployment Risks**
   - **Drift**: Model performance degrades over time

   - **Explainability**: Inability to explain decisions

   - **Fairness**: Discriminatory outcomes for protected groups

### AI Risk Mitigation Strategies

**Data Protection**:
```python
# PII detection and redaction
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def sanitize_training_data(text):
    """Remove PII from training data."""
    results = analyzer.analyze(text=text, language='en')
    anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
    return anonymized.text
```

**Guardrails**:
```python
# Input/output guardrails for AI agents
class AIGuardrails:
    def validate_input(self, user_input):
        """Validate input before sending to model."""
        if self.contains_injection_attempt(user_input):
            raise SecurityError("Potential injection attack detected")
        if self.contains_pii(user_input):
            return self.redact_pii(user_input)
        return user_input

    def validate_output(self, model_output):
        """Validate model output before returning to user."""
        if self.contains_harmful_content(model_output):
            return "I cannot provide that information."
        if self.contains_pii(model_output):
            return self.redact_pii(model_output)
        return model_output
```

**Bias Monitoring**:
```python
# Continuous bias monitoring
from fairlearn.metrics import demographic_parity_difference

def monitor_bias(predictions, protected_attributes):
    """Monitor for bias in model predictions."""
    dpd = demographic_parity_difference(
        y_true=actual_outcomes,
        y_pred=predictions,
        sensitive_features=protected_attributes
    )

    if abs(dpd) > 0.1:  # Threshold
        alert_compliance_team("Bias threshold exceeded")

    log_bias_metric("demographic_parity_difference", dpd)
```

---

## Integration with Compliance Frameworks

### SOC 2 Integration

- **CC3.2**: Risk assessment feeds control design

- **CC4.1**: Continuous monitoring of risks

- **CC7.2**: System monitoring for threats

Use risk assessment outputs to document SOC 2 control implementations.

### ISO 27001 Integration

- **Control 5.7**: Threat intelligence

- **Control 6.8**: Information security risk assessment

- **Control 8.8**: Management of technical vulnerabilities

Risk register becomes core ISMS documentation.

### NIST AI RMF Integration

- **Map Function**: Context establishment, risk identification

- **Measure Function**: Risk assessment and tracking

- **Manage Function**: Risk treatment and monitoring

Templates directly support NIST AI RMF implementation.

---

## Success Criteria

### Risk Assessment Complete

- [ ] Asset inventory created and maintained
- [ ] Threats identified (STRIDE methodology)
- [ ] Vulnerabilities assessed (security_review + pen tests)
- [ ] Risk register established with scoring
- [ ] Risk treatment plans documented
- [ ] Quarterly review scheduled

### Threat Modeling Complete

- [ ] Architecture diagrams created (data flows, trust boundaries)
- [ ] STRIDE analysis completed
- [ ] Attack trees documented
- [ ] Mitigation controls identified
- [ ] Threat model reviewed with team

### Defense in Depth Implemented

- [ ] Multiple security layers operational
- [ ] Input validation implemented
- [ ] Output sanitization configured
- [ ] PII detection active (if applicable)
- [ ] Guardrails deployed for AI agents (if applicable)
- [ ] Continuous monitoring operational

---

## Common Pitfalls

### ❌ Risk Assessment Theater

**Problem**: Creating risk register once for compliance, never updating it.

**Solution**: Quarterly reviews. Integrate with security_review workflow. Automate where possible.

### ❌ Single Point of Failure

**Problem**: Relying on one security control (e.g., only firewall).

**Solution**: Defense in depth — multiple overlapping layers. If one fails, others catch issues.

### ❌ Ignoring AI-Specific Risks

**Problem**: Applying traditional risk frameworks to AI without considering model-specific threats.

**Solution**: Use AI-specific risk assessments. Consider data poisoning, adversarial attacks, bias, drift.

### ❌ Analysis Paralysis

**Problem**: Spending months on risk assessment without implementing mitigations.

**Solution**: Start with high-risk items. Implement quick wins. Iterate.

---

## Resources

### Risk Management Frameworks

- [NIST Risk Management Framework](https://csrc.nist.gov/projects/risk-management)
- [ISO 31000 Risk Management](https://www.iso.org/iso-31000-risk-management.html)
- [FAIR Risk Analysis](https://www.fairinstitute.org/)

### Threat Modeling

- [OWASP Threat Modeling](https://owasp.org/www-community/Threat_Modeling)
- [Microsoft STRIDE](https://docs.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats)
- [PASTA Methodology](https://versprite.com/tag/pasta-threat-modeling/)

### AI-Specific Risk Resources

- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- [OWASP Machine Learning Security Top 10](https://owasp.org/www-project-machine-learning-security-top-10/)
- [Microsoft AI Risk Assessment](https://www.microsoft.com/en-us/ai/responsible-ai)

### Tools

- **Risk Assessment**: RiskLens, ServiceNow GRC, FAIR-U

- **Threat Modeling**: Microsoft Threat Modeling Tool, OWASP Threat Dragon, IriusRisk

- **AI Security**: Adversarial Robustness Toolbox (ART), Foolbox, CleverHans

- **PII Detection**: Microsoft Presidio, AWS Macie, Google DLP API

- **Bias Detection**: Fairlearn, AI Fairness 360 (AIF360), What-If Tool

---

## Time Estimates

| Template | Research | Implementation | Documentation | Total |
|----------|----------|----------------|---------------|-------|
| Risk Assessment | 1 hour | 2-3 hours | 1 hour | 4-5 hours |
| Threat Modeling | 1 hour | 2-3 hours | 1 hour | 4-5 hours |
| Defense in Depth | 1-2 hours | 3-4 hours | 1-2 hours | 5-7 hours |

**Total per language**: 13-17 hours for all 3 templates

---

[← Back to Compliance & Governance](../README.md) | [← Back to Main README](../../../README.md)
