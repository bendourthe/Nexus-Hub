---
template_id: compliance_governance_risk_assessment_python
template_name: Risk Assessment - Python
version: 1.0.0
last_updated: 2025-12-05
language: python
category: compliance_governance
phase: risk_management
phase_number: 2
difficulty: intermediate
estimated_time_hours: 4-6
prerequisites:
  - compliance_frameworks/python_soc2_compliance.md
  - compliance_frameworks/python_iso27001_implementation.md
related_templates:
  - risk_management/python_threat_modeling.md
  - compliance_frameworks/python_nist_ai_rmf.md
  - ai_agent_governance/python_agent_risk_controls.md
tools:
  - numpy (risk calculations)
  - pandas (risk data analysis)
  - matplotlib (risk visualization)
tags:
  - risk-assessment
  - risk-management
  - defense-in-depth
  - compliance
  - python
---

# Risk Assessment - Python

**⚠️ Pillar 2: Risk Management (Defense in Depth)**

Conduct comprehensive risk assessments following ISO 27001, NIST AI RMF, and SOC 2 requirements

[← Back to Risk Management](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### What is Risk Assessment?

**Risk Assessment** is the systematic process of identifying, analyzing, and evaluating risks to an organization's information assets. It forms the foundation of risk management and is required by multiple compliance frameworks.

**Risk Formula**: `Risk = Likelihood × Impact`

### Framework Requirements

**ISO 27001 Clause 6.1.2**: Risk assessment required
- Identify risks to confidentiality, integrity, availability
- Assess likelihood and impact
- Determine risk levels

**SOC 2 CC9.1**: Risk assessment process
- Identify potential threats
- Evaluate severity of risks
- Update risk assessment periodically

**NIST AI RMF MAP Function**: Context and risk identification
- MAP 4.1: Risks and benefits assessed
- MAP 5.1: Impact assessments conducted

### Risk Assessment Process

1. **Asset Identification** - What needs protection?
2. **Threat Identification** - What can go wrong?
3. **Vulnerability Identification** - What weaknesses exist?
4. **Risk Analysis** - Likelihood × Impact = Risk Level
5. **Risk Evaluation** - Compare against risk appetite
6. **Risk Treatment** - Accept, mitigate, transfer, avoid

---

## Implementation Roadmap

### Phase 1: Asset Inventory (Week 1)

**Deliverables**:
1. Information asset inventory
2. Asset classification (criticality)
3. Asset owners assigned
4. Dependencies mapped

**Code**: See [Asset Management](#asset-management-implementation)

### Phase 2: Threat and Vulnerability Identification (Week 2)

**Deliverables**:
1. Threat catalog
2. Vulnerability scan results
3. Threat-vulnerability mapping
4. Attack surface analysis

**Code**: See [Threat Identification](#threat-identification-implementation)

### Phase 3: Risk Analysis (Week 3)

**Deliverables**:
1. Risk scoring methodology
2. Likelihood assessment
3. Impact assessment
4. Risk matrix
5. Risk register

**Code**: See [Risk Analysis](#risk-analysis-implementation)

### Phase 4: Risk Treatment (Week 4)

**Deliverables**:
1. Risk treatment decisions
2. Risk treatment plan
3. Residual risk acceptance
4. Continuous monitoring plan

**Code**: See [Risk Treatment](#risk-treatment-implementation)

---

## Asset Management Implementation

### Information Asset Inventory

**ISO 27001 Control 5.9**: Inventory of information and assets

**Implementation**:

```python
# Information asset inventory and classification
from enum import Enum
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AssetType(Enum):
    """Types of information assets."""
    DATA = "data"  # Databases, files, datasets
    APPLICATION = "application"  # Software systems
    INFRASTRUCTURE = "infrastructure"  # Servers, networks
    DEVICE = "device"  # Endpoints, mobile devices
    PEOPLE = "people"  # Personnel with access
    AI_MODEL = "ai_model"  # ML models
    API = "api"  # API endpoints

class Confidentiality(Enum):
    """Confidentiality classification."""
    PUBLIC = 1
    INTERNAL = 2
    CONFIDENTIAL = 3
    RESTRICTED = 4

class Criticality(Enum):
    """Business criticality."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class AssetInventory:
    """
    Maintain inventory of information assets.

    Risk Management: Defense in Depth
    Compliance: ISO 27001 Control 5.9, SOC 2 CC9.1
    """

    def register_asset(
        self,
        asset_name: str,
        asset_type: AssetType,
        description: str,
        owner: str,
        confidentiality: Confidentiality,
        integrity_requirement: Criticality,
        availability_requirement: Criticality,
        dependencies: List[str] = None
    ) -> str:
        """
        Register information asset in inventory.

        CIA Triad assessment:
        - Confidentiality: How sensitive?
        - Integrity: How accurate must it be?
        - Availability: How available must it be?
        """
        asset_id = generate_uuid()

        # Calculate overall criticality (max of CIA)
        overall_criticality = max(
            confidentiality.value,
            integrity_requirement.value,
            availability_requirement.value
        )

        asset_record = {
            "asset_id": asset_id,
            "asset_name": asset_name,
            "asset_type": asset_type.value,
            "description": description,
            "owner": owner,

            # CIA Triad classification
            "confidentiality": confidentiality.value,
            "integrity_requirement": integrity_requirement.value,
            "availability_requirement": availability_requirement.value,
            "overall_criticality": overall_criticality,

            # Dependencies
            "dependencies": dependencies or [],

            # Metadata
            "registered_date": datetime.utcnow(),
            "last_reviewed": datetime.utcnow(),
            "status": "active"
        }

        db.assets.insert_one(asset_record)

        logger.info("Asset registered", extra={
            "event": "asset_registration",
            "asset_id": asset_id,
            "asset_name": asset_name,
            "criticality": overall_criticality
        })

        return asset_id

    def calculate_asset_value(self, asset_id: str) -> float:
        """
        Calculate asset value for risk assessment.

        Value based on:
        - Replacement cost
        - Business impact if lost
        - Regulatory fines if breached
        - Reputation damage
        """
        asset = db.assets.find_one({"asset_id": asset_id})

        # Base value from criticality
        criticality_values = {
            1: 10000,    # Low
            2: 50000,    # Medium
            3: 250000,   # High
            4: 1000000   # Critical
        }

        base_value = criticality_values.get(asset["overall_criticality"], 50000)

        # Multiply by data volume (if applicable)
        if asset["asset_type"] == AssetType.DATA.value:
            record_count = asset.get("record_count", 1000)
            base_value *= (record_count / 1000)

        # Multiply by number of dependencies (cascade effects)
        dependency_multiplier = 1 + (len(asset["dependencies"]) * 0.2)
        asset_value = base_value * dependency_multiplier

        logger.info("Asset value calculated", extra={
            "asset_id": asset_id,
            "asset_value": asset_value,
            "criticality": asset["overall_criticality"]
        })

        return asset_value
```

---

## Threat Identification Implementation

### Threat Modeling

**NIST AI RMF MAP 4.1**: Threats identified

**Implementation**:

```python
# Threat identification and cataloging
from typing import List, Dict

class ThreatCategory(Enum):
    """STRIDE threat categories."""
    SPOOFING = "spoofing"
    TAMPERING = "tampering"
    REPUDIATION = "repudiation"
    INFORMATION_DISCLOSURE = "information_disclosure"
    DENIAL_OF_SERVICE = "denial_of_service"
    ELEVATION_OF_PRIVILEGE = "elevation_of_privilege"

class ThreatSource(Enum):
    """Sources of threats."""
    EXTERNAL_ATTACKER = "external_attacker"
    INSIDER_MALICIOUS = "insider_malicious"
    INSIDER_ACCIDENTAL = "insider_accidental"
    NATURAL_DISASTER = "natural_disaster"
    TECHNICAL_FAILURE = "technical_failure"
    AI_SYSTEM = "ai_system"  # AI-specific threats

class ThreatCatalog:
    """
    Catalog of threats to information assets.

    Risk Management: Defense in Depth
    Frameworks: STRIDE, NIST AI RMF
    """

    # Common threats for different asset types
    THREAT_DATABASE = {
        AssetType.DATA: [
            {
                "threat_name": "Unauthorized Data Access",
                "threat_category": ThreatCategory.INFORMATION_DISCLOSURE,
                "threat_source": ThreatSource.EXTERNAL_ATTACKER,
                "description": "Attacker gains unauthorized access to sensitive data",
                "attack_vectors": ["SQL injection", "Broken authentication", "API exploitation"]
            },
            {
                "threat_name": "Data Exfiltration",
                "threat_category": ThreatCategory.INFORMATION_DISCLOSURE,
                "threat_source": ThreatSource.INSIDER_MALICIOUS,
                "description": "Insider copies sensitive data to external location",
                "attack_vectors": ["USB drives", "Cloud storage", "Email"]
            },
            {
                "threat_name": "Ransomware",
                "threat_category": ThreatCategory.DENIAL_OF_SERVICE,
                "threat_source": ThreatSource.EXTERNAL_ATTACKER,
                "description": "Malware encrypts data, demands ransom",
                "attack_vectors": ["Phishing", "Drive-by download", "RDP exploitation"]
            }
        ],

        AssetType.AI_MODEL: [
            {
                "threat_name": "Model Poisoning",
                "threat_category": ThreatCategory.TAMPERING,
                "threat_source": ThreatSource.EXTERNAL_ATTACKER,
                "description": "Attacker manipulates training data to corrupt model",
                "attack_vectors": ["Data injection", "Label flipping", "Backdoor insertion"]
            },
            {
                "threat_name": "Model Extraction",
                "threat_category": ThreatCategory.INFORMATION_DISCLOSURE,
                "threat_source": ThreatSource.EXTERNAL_ATTACKER,
                "description": "Attacker recreates model through API queries",
                "attack_vectors": ["Query-based extraction", "Model stealing"]
            },
            {
                "threat_name": "Adversarial Examples",
                "threat_category": ThreatCategory.TAMPERING,
                "threat_source": ThreatSource.EXTERNAL_ATTACKER,
                "description": "Crafted inputs cause model misclassification",
                "attack_vectors": ["Evasion attacks", "Perturbation"]
            },
            {
                "threat_name": "Prompt Injection",
                "threat_category": ThreatCategory.ELEVATION_OF_PRIVILEGE,
                "threat_source": ThreatSource.EXTERNAL_ATTACKER,
                "description": "Malicious prompts manipulate LLM behavior",
                "attack_vectors": ["Direct injection", "Indirect injection via data"]
            }
        ]
    }

    def identify_threats(self, asset_id: str) -> List[Dict]:
        """
        Identify threats applicable to asset.

        Returns list of potential threats based on asset type.
        """
        asset = db.assets.find_one({"asset_id": asset_id})

        # Get threats for asset type
        asset_type = AssetType(asset["asset_type"])
        threats = self.THREAT_DATABASE.get(asset_type, [])

        # Store threat-asset mappings
        identified_threats = []

        for threat in threats:
            threat_id = generate_uuid()

            threat_record = {
                "threat_id": threat_id,
                "asset_id": asset_id,
                "threat_name": threat["threat_name"],
                "threat_category": threat["threat_category"].value,
                "threat_source": threat["threat_source"].value,
                "description": threat["description"],
                "attack_vectors": threat["attack_vectors"],
                "identified_date": datetime.utcnow()
            }

            db.threats.insert_one(threat_record)
            identified_threats.append(threat_record)

        logger.info("Threats identified", extra={
            "event": "threat_identification",
            "asset_id": asset_id,
            "threats_count": len(identified_threats)
        })

        return identified_threats

class VulnerabilityScanner:
    """
    Identify vulnerabilities in systems.

    Integration with vulnerability scanners (Nessus, Qualys, etc.)
    """

    def scan_vulnerabilities(self, asset_id: str) -> List[Dict]:
        """
        Scan asset for vulnerabilities.

        Returns CVEs and severity scores (CVSS).
        """
        asset = db.assets.find_one({"asset_id": asset_id})

        # Simulate vulnerability scan results
        # In production: integrate with Nessus, Qualys, OpenVAS, etc.
        vulnerabilities = [
            {
                "vulnerability_id": "CVE-2024-12345",
                "severity": "high",
                "cvss_score": 8.5,
                "description": "SQL injection vulnerability",
                "affected_component": asset["asset_name"],
                "remediation": "Apply security patch 2024-01"
            }
        ]

        # Store vulnerabilities
        for vuln in vulnerabilities:
            vuln["asset_id"] = asset_id
            vuln["scan_date"] = datetime.utcnow()
            db.vulnerabilities.insert_one(vuln)

        logger.info("Vulnerability scan completed", extra={
            "event": "vulnerability_scan",
            "asset_id": asset_id,
            "vulnerabilities_found": len(vulnerabilities)
        })

        return vulnerabilities
```

---

## Risk Analysis Implementation

### Risk Scoring and Prioritization

**ISO 27001 Clause 6.1.2(d)**: Analyze information security risks

**Implementation**:

```python
# Risk analysis and scoring
import numpy as np
import pandas as pd

class Likelihood(Enum):
    """Likelihood of threat occurrence."""
    RARE = 1         # <5% annual probability
    UNLIKELY = 2     # 5-25%
    POSSIBLE = 3     # 25-50%
    LIKELY = 4       # 50-75%
    ALMOST_CERTAIN = 5  # >75%

class Impact(Enum):
    """Impact if threat materializes."""
    INSIGNIFICANT = 1  # <$10K loss
    MINOR = 2          # $10K-$100K
    MODERATE = 3       # $100K-$500K
    MAJOR = 4          # $500K-$1M
    SEVERE = 5         # >$1M

class RiskLevel(Enum):
    """Resulting risk level."""
    LOW = "low"        # Risk score 1-6
    MEDIUM = "medium"  # Risk score 7-12
    HIGH = "high"      # Risk score 13-18
    CRITICAL = "critical"  # Risk score 19-25

class RiskAnalysis:
    """
    Analyze and score information security risks.

    Risk Management: Defense in Depth
    Formula: Risk = Likelihood × Impact
    """

    def assess_likelihood(
        self,
        threat_id: str,
        asset_id: str,
        existing_controls: List[str]
    ) -> Likelihood:
        """
        Assess likelihood of threat occurring.

        Factors:
        - Threat source capability
        - Threat source motivation
        - Vulnerability severity
        - Existing controls effectiveness
        """
        threat = db.threats.find_one({"threat_id": threat_id})
        asset = db.assets.find_one({"asset_id": asset_id})
        vulnerabilities = list(db.vulnerabilities.find({"asset_id": asset_id}))

        # Base likelihood from threat source
        source_likelihood = {
            ThreatSource.EXTERNAL_ATTACKER.value: 4,  # Likely
            ThreatSource.INSIDER_MALICIOUS.value: 2,  # Unlikely
            ThreatSource.INSIDER_ACCIDENTAL.value: 3,  # Possible
            ThreatSource.NATURAL_DISASTER.value: 1,   # Rare
            ThreatSource.TECHNICAL_FAILURE.value: 3,  # Possible
            ThreatSource.AI_SYSTEM.value: 3           # Possible
        }.get(threat["threat_source"], 3)

        # Adjust for vulnerabilities (increase likelihood)
        high_severity_vulns = sum(1 for v in vulnerabilities if v.get("cvss_score", 0) >= 7.0)
        if high_severity_vulns > 0:
            source_likelihood = min(source_likelihood + 1, 5)

        # Adjust for existing controls (decrease likelihood)
        control_reduction = min(len(existing_controls) * 0.5, 2)
        final_likelihood = max(source_likelihood - control_reduction, 1)

        likelihood = Likelihood(int(final_likelihood))

        logger.info("Likelihood assessed", extra={
            "threat_id": threat_id,
            "asset_id": asset_id,
            "likelihood": likelihood.name
        })

        return likelihood

    def assess_impact(self, threat_id: str, asset_id: str) -> Impact:
        """
        Assess impact if threat materializes.

        Factors:
        - Asset value
        - Asset criticality
        - Regulatory fines
        - Reputation damage
        """
        threat = db.threats.find_one({"threat_id": threat_id})
        asset = db.assets.find_one({"asset_id": asset_id})

        # Asset value
        asset_value = AssetInventory().calculate_asset_value(asset_id)

        # Base impact from threat category
        category_impact = {
            ThreatCategory.INFORMATION_DISCLOSURE.value: 4,  # Major (GDPR fines)
            ThreatCategory.DENIAL_OF_SERVICE.value: 3,      # Moderate (downtime)
            ThreatCategory.TAMPERING.value: 4,              # Major (data integrity)
            ThreatCategory.ELEVATION_OF_PRIVILEGE.value: 5, # Severe (full compromise)
            ThreatCategory.SPOOFING.value: 3,               # Moderate
            ThreatCategory.REPUDIATION.value: 2             # Minor
        }.get(threat["threat_category"], 3)

        # Adjust for asset criticality
        if asset["overall_criticality"] == 4:  # Critical
            category_impact = min(category_impact + 1, 5)

        # Financial impact mapping
        if asset_value > 1000000:
            financial_impact = Impact.SEVERE
        elif asset_value > 500000:
            financial_impact = Impact.MAJOR
        elif asset_value > 100000:
            financial_impact = Impact.MODERATE
        elif asset_value > 10000:
            financial_impact = Impact.MINOR
        else:
            financial_impact = Impact.INSIGNIFICANT

        # Take maximum of category and financial impact
        final_impact = Impact(max(category_impact, financial_impact.value))

        logger.info("Impact assessed", extra={
            "threat_id": threat_id,
            "asset_id": asset_id,
            "impact": final_impact.name,
            "asset_value": asset_value
        })

        return final_impact

    def calculate_risk(
        self,
        threat_id: str,
        asset_id: str,
        existing_controls: List[str] = None
    ) -> Dict:
        """
        Calculate risk score.

        Risk = Likelihood × Impact
        """
        if existing_controls is None:
            existing_controls = []

        # Assess likelihood and impact
        likelihood = self.assess_likelihood(threat_id, asset_id, existing_controls)
        impact = self.assess_impact(threat_id, asset_id)

        # Calculate risk score
        risk_score = likelihood.value * impact.value

        # Determine risk level
        if risk_score >= 19:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 13:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 7:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        risk_analysis = {
            "risk_id": generate_uuid(),
            "threat_id": threat_id,
            "asset_id": asset_id,
            "likelihood": likelihood.name,
            "likelihood_value": likelihood.value,
            "impact": impact.name,
            "impact_value": impact.value,
            "risk_score": risk_score,
            "risk_level": risk_level.value,
            "existing_controls": existing_controls,
            "assessed_date": datetime.utcnow()
        }

        # Store in risk register
        db.risk_register.insert_one(risk_analysis)

        logger.warning("Risk calculated", extra={
            "event": "risk_calculation",
            "risk_id": risk_analysis["risk_id"],
            "risk_level": risk_level.value,
            "risk_score": risk_score
        })

        return risk_analysis

class RiskMatrix:
    """
    Generate risk matrix (heat map) for visualization.
    """

    def generate_risk_matrix(self) -> pd.DataFrame:
        """
        Create 5x5 risk matrix.

        Rows: Impact (1-5)
        Columns: Likelihood (1-5)
        Cells: Risk Level
        """
        matrix = np.zeros((5, 5), dtype=int)

        for likelihood in range(1, 6):
            for impact in range(1, 6):
                risk_score = likelihood * impact
                matrix[5-impact, likelihood-1] = risk_score  # Invert y-axis

        # Convert to DataFrame
        df = pd.DataFrame(
            matrix,
            index=['Severe', 'Major', 'Moderate', 'Minor', 'Insignificant'],
            columns=['Rare', 'Unlikely', 'Possible', 'Likely', 'Almost Certain']
        )

        return df

    def plot_risk_positions(self, risk_register: List[Dict]):
        """
        Plot risks on matrix.

        Requires matplotlib for visualization.
        """
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(10, 8))

        # Plot each risk
        for risk in risk_register:
            likelihood = risk["likelihood_value"]
            impact = risk["impact_value"]
            risk_level = risk["risk_level"]

            # Color by risk level
            colors = {
                "low": "green",
                "medium": "yellow",
                "high": "orange",
                "critical": "red"
            }

            ax.scatter(likelihood, impact, s=200, c=colors[risk_level], alpha=0.6)

        ax.set_xlim(0, 6)
        ax.set_ylim(0, 6)
        ax.set_xlabel('Likelihood')
        ax.set_ylabel('Impact')
        ax.set_title('Risk Matrix')
        ax.grid(True)

        plt.tight_layout()
        plt.savefig('risk_matrix.png')
        logger.info("Risk matrix generated: risk_matrix.png")
```

---

## Risk Treatment Implementation

### Risk Treatment Strategies

**ISO 27001 Clause 6.1.3**: Risk treatment

**Implementation**:

```python
# Risk treatment planning
class RiskTreatmentOption(Enum):
    """Risk treatment options."""
    MITIGATE = "mitigate"  # Implement controls to reduce risk
    ACCEPT = "accept"      # Accept risk within tolerance
    TRANSFER = "transfer"  # Insurance, outsourcing
    AVOID = "avoid"        # Eliminate activity causing risk

class RiskTreatment:
    """
    Define risk treatment strategies.

    Risk Management: Defense in Depth
    ISO 27001 Clause 6.1.3: Risk treatment required
    """

    # Risk appetite (configurable per organization)
    RISK_APPETITE = {
        "low": "acceptable",
        "medium": "review_required",
        "high": "must_mitigate",
        "critical": "must_mitigate"
    }

    def determine_treatment(self, risk_id: str) -> RiskTreatmentOption:
        """
        Determine appropriate risk treatment.

        Decision based on risk level and risk appetite.
        """
        risk = db.risk_register.find_one({"risk_id": risk_id})
        risk_level = risk["risk_level"]

        appetite_decision = self.RISK_APPETITE.get(risk_level)

        if appetite_decision == "acceptable":
            return RiskTreatmentOption.ACCEPT
        elif appetite_decision == "must_mitigate":
            return RiskTreatmentOption.MITIGATE
        else:
            # Review required - default to mitigate
            return RiskTreatmentOption.MITIGATE

    def create_treatment_plan(
        self,
        risk_id: str,
        treatment_option: RiskTreatmentOption,
        proposed_controls: List[str],
        owner: str,
        target_completion_date: datetime
    ) -> str:
        """
        Create risk treatment plan.

        ISO 27001 Clause 6.1.3(e): Risk treatment plan required
        """
        risk = db.risk_register.find_one({"risk_id": risk_id})
        plan_id = generate_uuid()

        treatment_plan = {
            "plan_id": plan_id,
            "risk_id": risk_id,
            "treatment_option": treatment_option.value,
            "proposed_controls": proposed_controls,
            "owner": owner,
            "target_completion_date": target_completion_date,
            "status": "planned",
            "created_date": datetime.utcnow(),

            # Residual risk (estimated after treatment)
            "residual_risk_level": self._estimate_residual_risk(risk, proposed_controls)
        }

        db.risk_treatment_plans.insert_one(treatment_plan)

        logger.info("Risk treatment plan created", extra={
            "event": "risk_treatment_plan",
            "plan_id": plan_id,
            "risk_id": risk_id,
            "treatment": treatment_option.value
        })

        return plan_id

    def _estimate_residual_risk(self, risk: Dict, proposed_controls: List[str]) -> str:
        """
        Estimate residual risk after controls implemented.

        Assume each control reduces likelihood by 1 level.
        """
        current_likelihood = risk["likelihood_value"]
        likelihood_reduction = min(len(proposed_controls), current_likelihood - 1)

        residual_likelihood = current_likelihood - likelihood_reduction
        residual_impact = risk["impact_value"]  # Impact stays same

        residual_score = residual_likelihood * residual_impact

        if residual_score >= 19:
            return "critical"
        elif residual_score >= 13:
            return "high"
        elif residual_score >= 7:
            return "medium"
        else:
            return "low"

    def accept_residual_risk(self, plan_id: str, approver: str, justification: str):
        """
        Accept residual risk (after controls implemented).

        ISO 27001 Clause 6.1.3(f): Obtain risk acceptance from risk owners
        """
        plan = db.risk_treatment_plans.find_one({"plan_id": plan_id})

        acceptance = {
            "plan_id": plan_id,
            "risk_id": plan["risk_id"],
            "residual_risk_level": plan["residual_risk_level"],
            "approver": approver,
            "justification": justification,
            "accepted_date": datetime.utcnow()
        }

        db.risk_acceptances.insert_one(acceptance)

        logger.warning("Residual risk accepted", extra={
            "event": "risk_acceptance",
            "plan_id": plan_id,
            "approver": approver,
            "residual_risk": plan["residual_risk_level"]
        })
```

---

## Risk Reporting

### Executive Risk Dashboard

**SOC 2 CC9.1**: Communicate risk assessment results

**Implementation**:

```python
# Risk reporting and dashboards
class RiskReporting:
    """
    Generate risk reports for stakeholders.

    Audience:
    - Executive: High-level risk summary
    - Risk Committee: Detailed risk register
    - Auditors: Compliance evidence
    """

    def generate_executive_summary(self) -> Dict:
        """
        Executive risk summary.

        High-level view of risk landscape.
        """
        # Get all current risks
        risks = list(db.risk_register.find())

        # Count by risk level
        risk_counts = {
            "critical": sum(1 for r in risks if r["risk_level"] == "critical"),
            "high": sum(1 for r in risks if r["risk_level"] == "high"),
            "medium": sum(1 for r in risks if r["risk_level"] == "medium"),
            "low": sum(1 for r in risks if r["risk_level"] == "low")
        }

        # Top risks (critical + high)
        top_risks = [r for r in risks if r["risk_level"] in ["critical", "high"]]
        top_risks_sorted = sorted(top_risks, key=lambda x: x["risk_score"], reverse=True)[:10]

        # Treatment status
        treatment_plans = list(db.risk_treatment_plans.find())
        treatment_status = {
            "planned": sum(1 for p in treatment_plans if p["status"] == "planned"),
            "in_progress": sum(1 for p in treatment_plans if p["status"] == "in_progress"),
            "completed": sum(1 for p in treatment_plans if p["status"] == "completed")
        }

        summary = {
            "report_date": datetime.utcnow().isoformat(),
            "total_risks": len(risks),
            "risk_breakdown": risk_counts,
            "top_10_risks": [
                {
                    "risk_id": r["risk_id"],
                    "threat": db.threats.find_one({"threat_id": r["threat_id"]})["threat_name"],
                    "asset": db.assets.find_one({"asset_id": r["asset_id"]})["asset_name"],
                    "risk_level": r["risk_level"],
                    "risk_score": r["risk_score"]
                }
                for r in top_risks_sorted
            ],
            "treatment_status": treatment_status
        }

        return summary

    def export_risk_register(self, format: str = "csv") -> str:
        """
        Export complete risk register.

        For auditors and detailed analysis.
        """
        risks = list(db.risk_register.find())

        # Enrich with asset and threat details
        enriched_risks = []
        for risk in risks:
            threat = db.threats.find_one({"threat_id": risk["threat_id"]})
            asset = db.assets.find_one({"asset_id": risk["asset_id"]})

            enriched_risks.append({
                "Risk ID": risk["risk_id"],
                "Asset": asset["asset_name"],
                "Threat": threat["threat_name"],
                "Likelihood": risk["likelihood"],
                "Impact": risk["impact"],
                "Risk Score": risk["risk_score"],
                "Risk Level": risk["risk_level"],
                "Assessed Date": risk["assessed_date"].isoformat()
            })

        # Convert to DataFrame and export
        df = pd.DataFrame(enriched_risks)

        if format == "csv":
            filename = f"risk_register_{datetime.utcnow().strftime('%Y%m%d')}.csv"
            df.to_csv(filename, index=False)
        elif format == "excel":
            filename = f"risk_register_{datetime.utcnow().strftime('%Y%m%d')}.xlsx"
            df.to_excel(filename, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Risk register exported: {filename}")
        return filename
```

---

## Success Criteria

### Asset Inventory Complete

- [ ] All information assets identified and cataloged
- [ ] Asset owners assigned
- [ ] CIA classification completed
- [ ] Asset dependencies mapped
- [ ] Asset values calculated

### Risk Assessment Complete

- [ ] Threats identified for all critical assets
- [ ] Vulnerabilities scanned and documented
- [ ] Risk analysis completed (likelihood × impact)
- [ ] Risk register populated and maintained
- [ ] Risk matrix generated

### Risk Treatment Planned

- [ ] Treatment decisions for all high/critical risks
- [ ] Risk treatment plans created
- [ ] Control implementations scheduled
- [ ] Residual risks accepted by risk owners
- [ ] Continuous monitoring established

### Compliance Evidence

- [ ] Risk assessment documentation (ISO 27001 6.1.2)
- [ ] Risk treatment plan (ISO 27001 6.1.3)
- [ ] Risk acceptance records
- [ ] Periodic risk review schedule (quarterly)
- [ ] Executive risk reports

---

## Common Pitfalls

### ❌ Static Risk Assessment

**Problem**: Conducting risk assessment once and never updating.

**Solution**: Continuous risk monitoring. Reassess quarterly or when significant changes occur.

### ❌ Ignoring Residual Risk

**Problem**: Implementing controls without assessing residual risk.

**Solution**: Always calculate and accept residual risk after controls implemented.

### ❌ No Risk Ownership

**Problem**: Risks identified but no one responsible for mitigation.

**Solution**: Assign risk owners for every risk. Owner accountable for treatment.

### ❌ Overcomplicating Analysis

**Problem**: Complex quantitative models that are hard to maintain.

**Solution**: Start with qualitative (Low/Medium/High). Add quantitative analysis for critical risks only.

---

## Resources

### Risk Assessment Frameworks

- [NIST SP 800-30](https://csrc.nist.gov/publications/detail/sp/800-30/rev-1/final) - Risk assessment guide
- [ISO 27005:2022](https://www.iso.org/standard/80585.html) - Information security risk management
- [FAIR (Factor Analysis of Information Risk)](https://www.fairinstitute.org/) - Quantitative risk analysis

### Tools

- **Vulnerability Scanners**: Nessus, Qualys, OpenVAS
- **Risk Management**: RiskLens, ServiceNow GRC, LogicManager
- **Threat Intelligence**: MITRE ATT&CK, threat feeds

---

## Changelog

### Version 1.0.0 - 2025-12-05

**Added**:
- Complete risk assessment implementation for Python
- Asset inventory and classification (CIA Triad)
- Threat identification (STRIDE, MITRE ATT&CK)
- Vulnerability scanning integration
- Risk analysis (Likelihood × Impact)
- Risk matrix and heat map generation
- Risk treatment planning
- Risk register management
- Executive risk reporting

**Framework Coverage**:
- ISO 27001 Clause 6.1.2 (Risk assessment)
- ISO 27001 Clause 6.1.3 (Risk treatment)
- SOC 2 CC9.1 (Risk assessment process)
- NIST AI RMF MAP Function

---

[← Back to Risk Management](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
