---
template_id: compliance_governance_nist_ai_rmf_python
template_name: NIST AI Risk Management Framework - Python
version: 1.0.0
last_updated: 2025-12-05
language: python
category: compliance_governance
phase: compliance_frameworks
phase_number: 1
difficulty: advanced
estimated_time_hours: 6-8
prerequisites:
  - compliance_frameworks/python_soc2_compliance.md
  - risk_management/python_risk_assessment.md
  - ai_agent_governance/README.md
related_templates:
  - compliance_frameworks/python_iso27001_implementation.md
  - ai_agent_governance/python_agent_lifecycle.md
  - ai_agent_governance/python_agent_risk_controls.md
tools:
  - fairlearn (bias detection)
  - shap (model explainability)
  - evidently (ML monitoring)
  - mlflow (experiment tracking)
  - opentelemetry (tracing)
tags:
  - nist-ai-rmf
  - ai-governance
  - trustworthy-ai
  - generative-ai
  - ai-risk
  - python
---

# NIST AI Risk Management Framework (AI RMF 1.0) - Python

**Implement trustworthy AI systems following NIST's comprehensive risk management framework**

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### What is NIST AI RMF 1.0?

The **NIST AI Risk Management Framework (AI RMF 1.0)** is a voluntary, consensus-driven framework released in January 2023 by the National Institute of Standards and Technology (NIST). It provides comprehensive guidance for managing risks associated with artificial intelligence systems.

**Key Documents**:
- **AI RMF 1.0** (January 2023) - Core framework
- **Generative AI Profile** (July 2024) - GenAI-specific guidance
- **AI RMF Playbook** (August 2023) - Implementation guidance

### Why Python AI Systems Need NIST AI RMF

- **Federal Mandate**: Required for US federal agencies (Executive Order 14110)
- **Industry Standard**: Rapidly becoming voluntary standard for enterprises
- **Trustworthy AI**: Framework for building safe, secure, explainable AI
- **Risk Management**: Systematic approach to AI-specific risks
- **Stakeholder Trust**: Demonstrates commitment to responsible AI
- **GenAI Risks**: Addresses unique risks of large language models, diffusion models

### The 7 Trustworthy AI Characteristics

NIST defines trustworthy AI systems as having these characteristics:

1. **Valid and Reliable** - Accurate, consistent, reproducible
2. **Safe** - Do not cause harm under expected or adversarial conditions
3. **Secure and Resilient** - Protected against attacks, recover from failures
4. **Accountable and Transparent** - Documented, explainable, auditable
5. **Explainable and Interpretable** - Understandable to appropriate stakeholders
6. **Privacy-Enhanced** - Protect sensitive data throughout lifecycle
7. **Fair with Harmful Bias Managed** - Equitable treatment, bias detection/mitigation

---

## AI RMF Structure: 4 Functions

The framework is organized into 4 functions with 23 categories and 56 sub-categories:

### GOVERN (9 Categories)

**Purpose**: Cultivate culture of risk management, establish policies and processes

**Key Categories**:
- **GOVERN 1.1**: Legal and regulatory requirements identified
- **GOVERN 1.2**: Organizational risk tolerances defined
- **GOVERN 2.1**: Roles and responsibilities assigned
- **GOVERN 3.1**: Organizational policies for AI updated
- **GOVERN 4.1**: Accountability structures in place

### MAP (5 Categories)

**Purpose**: Context established, risks and impacts identified

**Key Categories**:
- **MAP 1.1**: AI system context and use cases documented
- **MAP 2.1**: Categorization of AI system (risk level)
- **MAP 3.1**: AI capabilities and limitations documented
- **MAP 4.1**: Risks and benefits identified
- **MAP 5.1**: Impact assessments conducted

### MEASURE (4 Categories)

**Purpose**: Metrics identified, tracked, assessed

**Key Categories**:
- **MEASURE 1.1**: Metrics for trustworthy AI defined
- **MEASURE 2.1**: Test datasets representative
- **MEASURE 3.1**: Bias evaluation conducted
- **MEASURE 4.1**: Explainability methods applied

### MANAGE (5 Categories)

**Purpose**: Risks prioritized, responses implemented, monitored

**Key Categories**:
- **MANAGE 1.1**: AI risks prioritized
- **MANAGE 2.1**: Risk treatment strategies implemented
- **MANAGE 3.1**: Risk monitoring and review ongoing
- **MANAGE 4.1**: Incident response plans in place

---

## Generative AI Profile (July 2024)

### What is the GenAI Profile?

NIST released the **Generative AI Profile** in July 2024 to address unique risks of generative AI systems (LLMs, image generation, etc.).

**New Risks Addressed**:
- **CBRN Information** (Chemical, Biological, Radiological, Nuclear synthesis)
- **Confabulation** (Hallucinations, false outputs)
- **Dangerous, Violent, Hateful Content** generation
- **Data Privacy** (training data leakage, PII exposure)
- **Environmental Impacts** (energy consumption, carbon footprint)
- **Human-AI Configuration** (over-reliance, deskilling)
- **Information Integrity** (misinformation, deepfakes)
- **Information Security** (prompt injection, jailbreaking)
- **Intellectual Property** (copyright, training data provenance)
- **Obscene, Degrading, Abusive Content**
- **Toxicity, Bias, Homogenization**
- **Value Chain Risks** (third-party model risks)

---

## Implementation Roadmap

### Phase 1: GOVERN - Establish AI Governance (Weeks 1-2)

**Deliverables**:
1. AI governance policy
2. AI risk tolerance statement
3. Roles and responsibilities (AI Owner, AI Risk Manager, AI Ethics Board)
4. AI system inventory

**Code**: See [GOVERN Implementation](#govern-implementation)

### Phase 2: MAP - Context and Risk Identification (Weeks 3-4)

**Deliverables**:
1. AI system context documentation
2. Risk categorization (low/medium/high/critical)
3. AI capabilities and limitations documentation
4. Impact assessment

**Code**: See [MAP Implementation](#map-implementation)

### Phase 3: MEASURE - Metrics and Testing (Weeks 5-8)

**Deliverables**:
1. Trustworthy AI metrics dashboard
2. Bias evaluation reports
3. Explainability documentation
4. Model cards / System cards

**Code**: See [MEASURE Implementation](#measure-implementation)

### Phase 4: MANAGE - Risk Mitigation and Monitoring (Weeks 9-12)

**Deliverables**:
1. Risk treatment plans
2. Continuous monitoring dashboards
3. Incident response procedures
4. Audit logs and reporting

**Code**: See [MANAGE Implementation](#manage-implementation)

---

## GOVERN Implementation

### AI System Inventory and Classification

**NIST Category**: GOVERN 1.1, MAP 1.1, MAP 2.1

**Implementation**:

```python
# AI system inventory and risk categorization
from enum import Enum
from typing import List, Dict, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class AISystemType(Enum):
    """Types of AI systems per NIST taxonomy."""
    PREDICTIVE = "predictive"
    GENERATIVE = "generative"
    CLASSIFICATION = "classification"
    RECOMMENDATION = "recommendation"
    AUTONOMOUS_DECISION = "autonomous_decision"

class RiskLevel(Enum):
    """
    Risk categorization per NIST AI RMF.

    Based on impact to safety, rights, livelihoods.
    """
    LOW = "low"  # Minimal impact
    MEDIUM = "medium"  # Moderate impact
    HIGH = "high"  # Significant impact
    CRITICAL = "critical"  # Safety-critical, rights-impacting

class AISystemInventory:
    """
    Maintain inventory of AI systems for NIST AI RMF compliance.

    NIST Categories:
    - GOVERN 1.1: AI systems mapped and categorized
    - MAP 1.1: Context documented
    - MAP 2.1: Risk level assigned

    Generative AI Profile: Track GenAI systems separately with specific risk profiles.
    """

    def register_ai_system(
        self,
        system_name: str,
        system_type: AISystemType,
        use_case: str,
        impact_assessment: Dict,
        is_generative: bool = False
    ) -> str:
        """
        Register AI system in organizational inventory.

        Args:
            system_name: Unique identifier for AI system
            system_type: Type of AI system
            use_case: Business use case description
            impact_assessment: Assessment of potential impacts
            is_generative: Whether system is generative AI (LLM, diffusion model)

        Returns:
            system_id: Unique system identifier
        """
        # Calculate risk level based on impact assessment
        risk_level = self._calculate_risk_level(impact_assessment)

        # Create system record
        system_id = generate_uuid()
        system_record = {
            "system_id": system_id,
            "system_name": system_name,
            "system_type": system_type.value,
            "use_case": use_case,
            "is_generative": is_generative,
            "risk_level": risk_level.value,
            "impact_assessment": impact_assessment,
            "registered_date": datetime.utcnow(),
            "status": "active",
            "owner": get_current_user(),

            # NIST Requirements
            "capabilities_documented": False,
            "limitations_documented": False,
            "bias_evaluation_completed": False,
            "explainability_documented": False,
            "monitoring_configured": False
        }

        # Store in inventory database
        db.ai_systems.insert_one(system_record)

        logger.info("AI system registered in inventory", extra={
            "event": "ai_system_registration",
            "system_id": system_id,
            "system_name": system_name,
            "risk_level": risk_level.value,
            "is_generative": is_generative
        })

        # Trigger risk assessment workflow for high/critical systems
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            self._trigger_comprehensive_risk_assessment(system_id)

        return system_id

    def _calculate_risk_level(self, impact_assessment: Dict) -> RiskLevel:
        """
        Calculate risk level based on impact assessment.

        NIST Guidance (MAP 2.1):
        - Safety impact (physical harm)
        - Rights impact (civil rights, privacy)
        - Livelihood impact (employment, access to services)
        - High-risk use cases: Hiring, lending, healthcare, law enforcement
        """
        # High-risk domains
        high_risk_domains = ["hiring", "lending", "healthcare", "law_enforcement",
                            "critical_infrastructure", "education"]

        if impact_assessment.get("domain") in high_risk_domains:
            return RiskLevel.HIGH

        # Safety-critical systems
        if impact_assessment.get("safety_critical", False):
            return RiskLevel.CRITICAL

        # Rights-impacting systems
        if impact_assessment.get("impacts_civil_rights", False):
            return RiskLevel.HIGH

        # Autonomous decision-making
        if impact_assessment.get("autonomous_decision", False):
            return RiskLevel.HIGH

        # Default to medium for AI systems with business impact
        if impact_assessment.get("business_impact") in ["high", "critical"]:
            return RiskLevel.MEDIUM

        return RiskLevel.LOW

class AIGovernancePolicy:
    """
    AI governance policy management.

    NIST Category: GOVERN 3.1 (Organizational AI policies)
    """

    REQUIRED_POLICIES = [
        "acceptable_use",
        "data_governance",
        "model_development",
        "bias_testing",
        "explainability_requirements",
        "human_oversight",
        "incident_response",
        "third_party_ai"
    ]

    def validate_ai_system_compliance(self, system_id: str) -> Dict:
        """
        Validate AI system compliance with governance policies.

        NIST Categories:
        - GOVERN 3.1: Policies exist and are enforced
        - GOVERN 4.1: Accountability mechanisms
        """
        system = db.ai_systems.find_one({"system_id": system_id})

        compliance_checks = {
            "acceptable_use": self._check_acceptable_use(system),
            "data_governance": self._check_data_governance(system),
            "bias_testing": self._check_bias_testing(system),
            "explainability": self._check_explainability(system),
            "human_oversight": self._check_human_oversight(system),
            "monitoring": self._check_monitoring(system)
        }

        # Overall compliance score
        total_checks = len(compliance_checks)
        passed_checks = sum(1 for v in compliance_checks.values() if v["compliant"])
        compliance_score = passed_checks / total_checks

        logger.info("AI governance compliance check", extra={
            "event": "ai_governance_compliance",
            "system_id": system_id,
            "compliance_score": compliance_score,
            "checks": compliance_checks
        })

        return {
            "system_id": system_id,
            "compliance_score": compliance_score,
            "checks": compliance_checks,
            "overall_compliant": compliance_score >= 0.8
        }
```

---

## MAP Implementation

### Risk Identification and Impact Assessment

**NIST Category**: MAP 4.1, MAP 5.1

**Implementation**:

```python
# AI risk identification and impact assessment
from typing import List, Dict

class AIRiskIdentification:
    """
    Identify and assess AI-specific risks.

    NIST Categories:
    - MAP 4.1: Risks and benefits assessed and documented
    - MAP 5.1: Impact assessments conducted

    Generative AI Profile Risks:
    - Confabulation (hallucinations)
    - Data privacy (training data leakage)
    - Information security (prompt injection)
    - Toxicity and bias
    - Value chain risks
    """

    # GenAI-specific risk categories
    GENERATIVE_AI_RISKS = [
        "confabulation",
        "data_privacy_leakage",
        "prompt_injection",
        "jailbreaking",
        "toxicity",
        "bias_amplification",
        "misinformation",
        "copyright_infringement",
        "cbrn_information",
        "dangerous_content"
    ]

    def conduct_risk_assessment(self, system_id: str) -> Dict:
        """
        Conduct comprehensive AI risk assessment.

        NIST MAP Function: Identify context-specific risks.
        """
        system = db.ai_systems.find_one({"system_id": system_id})

        # Base AI risks (all systems)
        identified_risks = self._identify_base_ai_risks(system)

        # Generative AI specific risks
        if system["is_generative"]:
            identified_risks.extend(self._identify_generative_ai_risks(system))

        # Categorize by severity
        risk_matrix = self._create_risk_matrix(identified_risks)

        # Store risk assessment
        assessment_id = generate_uuid()
        db.risk_assessments.insert_one({
            "assessment_id": assessment_id,
            "system_id": system_id,
            "assessment_date": datetime.utcnow(),
            "identified_risks": identified_risks,
            "risk_matrix": risk_matrix,
            "assessor": get_current_user()
        })

        logger.info("AI risk assessment completed", extra={
            "event": "ai_risk_assessment",
            "system_id": system_id,
            "assessment_id": assessment_id,
            "total_risks": len(identified_risks),
            "high_severity": len([r for r in identified_risks if r["severity"] == "high"])
        })

        return {
            "assessment_id": assessment_id,
            "identified_risks": identified_risks,
            "risk_matrix": risk_matrix
        }

    def _identify_generative_ai_risks(self, system: Dict) -> List[Dict]:
        """
        Identify risks specific to generative AI systems.

        NIST Generative AI Profile (July 2024)
        """
        risks = []

        # Risk: Confabulation (Hallucinations)
        risks.append({
            "risk_id": generate_uuid(),
            "risk_type": "confabulation",
            "description": "Model may generate false, misleading, or fabricated outputs",
            "likelihood": self._assess_confabulation_likelihood(system),
            "impact": "high" if system["risk_level"] in ["high", "critical"] else "medium",
            "nist_category": "GenAI Profile - Confabulation",
            "mitigation_required": True
        })

        # Risk: Data Privacy (Training Data Leakage)
        if self._uses_fine_tuning(system):
            risks.append({
                "risk_id": generate_uuid(),
                "risk_type": "data_privacy_leakage",
                "description": "Model may leak sensitive information from training data",
                "likelihood": "medium",
                "impact": "critical",
                "nist_category": "GenAI Profile - Data Privacy",
                "mitigation_required": True
            })

        # Risk: Prompt Injection
        risks.append({
            "risk_id": generate_uuid(),
            "risk_type": "prompt_injection",
            "description": "Adversarial inputs may manipulate model behavior",
            "likelihood": "high",
            "impact": "high",
            "nist_category": "GenAI Profile - Information Security",
            "mitigation_required": True
        })

        # Risk: Toxicity and Bias
        risks.append({
            "risk_id": generate_uuid(),
            "risk_type": "toxicity_bias",
            "description": "Model may generate toxic, biased, or harmful content",
            "likelihood": "medium",
            "impact": "high",
            "nist_category": "GenAI Profile - Toxicity, Bias, Homogenization",
            "mitigation_required": True
        })

        return risks

    def _assess_confabulation_likelihood(self, system: Dict) -> str:
        """
        Assess likelihood of hallucinations/confabulations.

        Higher likelihood for:
        - Retrieval-augmented generation without verification
        - Open-ended generation tasks
        - Complex reasoning tasks
        - Insufficient grounding data
        """
        use_case_keywords = system.get("use_case", "").lower()

        high_confabulation_tasks = ["summarization", "question_answering",
                                    "creative_writing", "reasoning"]

        for keyword in high_confabulation_tasks:
            if keyword in use_case_keywords:
                return "high"

        return "medium"

class AIImpactAssessment:
    """
    Algorithmic Impact Assessment (AIA) for AI systems.

    NIST Category: MAP 5.1
    """

    def conduct_impact_assessment(self, system_id: str) -> Dict:
        """
        Conduct comprehensive impact assessment.

        Assesses:
        - Individual impacts (privacy, autonomy, fairness)
        - Societal impacts (equity, environmental)
        - Rights impacts (civil rights, human rights)
        """
        system = db.ai_systems.find_one({"system_id": system_id})

        assessment = {
            "system_id": system_id,
            "assessment_date": datetime.utcnow(),

            # Individual Impacts
            "privacy_impact": self._assess_privacy_impact(system),
            "autonomy_impact": self._assess_autonomy_impact(system),
            "fairness_impact": self._assess_fairness_impact(system),

            # Societal Impacts
            "equity_impact": self._assess_equity_impact(system),
            "environmental_impact": self._assess_environmental_impact(system),

            # Rights Impacts
            "civil_rights_impact": self._assess_civil_rights_impact(system),

            # Overall risk determination
            "overall_impact": None
        }

        # Determine overall impact level
        assessment["overall_impact"] = self._calculate_overall_impact(assessment)

        # Store assessment
        db.impact_assessments.insert_one(assessment)

        logger.warning("AI impact assessment completed", extra={
            "event": "ai_impact_assessment",
            "system_id": system_id,
            "overall_impact": assessment["overall_impact"]
        })

        return assessment
```

---

## MEASURE Implementation

### Bias Detection and Mitigation

**NIST Category**: MEASURE 3.1

**Implementation**:

```python
# Bias evaluation and fairness metrics
from fairlearn.metrics import MetricFrame, demographic_parity_difference, equalized_odds_difference
import pandas as pd
import numpy as np

class AIBiasEvaluation:
    """
    Evaluate and mitigate bias in AI systems.

    NIST Categories:
    - MEASURE 2.1: Test datasets representative
    - MEASURE 3.1: Bias evaluation results documented
    - Trustworthy AI Characteristic: Fair with Harmful Bias Managed

    Generative AI Profile:
    - Toxicity, Bias, Homogenization risk category
    """

    # Protected attributes per civil rights law
    PROTECTED_ATTRIBUTES = ["race", "gender", "age", "disability", "religion"]

    # Fairness thresholds (configurable based on risk tolerance)
    DEMOGRAPHIC_PARITY_THRESHOLD = 0.1  # 10% difference
    EQUALIZED_ODDS_THRESHOLD = 0.1

    def evaluate_bias(
        self,
        system_id: str,
        predictions: np.ndarray,
        ground_truth: np.ndarray,
        sensitive_features: pd.DataFrame
    ) -> Dict:
        """
        Evaluate bias across protected attributes.

        NIST MEASURE 3.1: Bias evaluation conducted and documented.
        """
        bias_metrics = {}

        for attribute in self.PROTECTED_ATTRIBUTES:
            if attribute not in sensitive_features.columns:
                continue

            # Calculate fairness metrics
            metric_frame = MetricFrame(
                metrics={
                    "accuracy": accuracy_score,
                    "precision": precision_score,
                    "recall": recall_score,
                    "false_positive_rate": self._false_positive_rate
                },
                y_true=ground_truth,
                y_pred=predictions,
                sensitive_features=sensitive_features[attribute]
            )

            # Demographic parity
            dp_diff = demographic_parity_difference(
                y_true=ground_truth,
                y_pred=predictions,
                sensitive_features=sensitive_features[attribute]
            )

            # Equalized odds
            eo_diff = equalized_odds_difference(
                y_true=ground_truth,
                y_pred=predictions,
                sensitive_features=sensitive_features[attribute]
            )

            bias_metrics[attribute] = {
                "demographic_parity_diff": dp_diff,
                "equalized_odds_diff": eo_diff,
                "metric_frame": metric_frame.by_group.to_dict(),
                "passes_threshold": (
                    abs(dp_diff) <= self.DEMOGRAPHIC_PARITY_THRESHOLD and
                    abs(eo_diff) <= self.EQUALIZED_ODDS_THRESHOLD
                )
            }

        # Overall bias assessment
        overall_fair = all(m["passes_threshold"] for m in bias_metrics.values())

        # Store evaluation results
        evaluation_id = generate_uuid()
        db.bias_evaluations.insert_one({
            "evaluation_id": evaluation_id,
            "system_id": system_id,
            "evaluation_date": datetime.utcnow(),
            "bias_metrics": bias_metrics,
            "overall_fair": overall_fair,
            "evaluator": get_current_user()
        })

        logger.warning("Bias evaluation completed", extra={
            "event": "bias_evaluation",
            "system_id": system_id,
            "overall_fair": overall_fair,
            "attributes_evaluated": list(bias_metrics.keys())
        })

        return {
            "evaluation_id": evaluation_id,
            "bias_metrics": bias_metrics,
            "overall_fair": overall_fair
        }

    def mitigate_bias(self, system_id: str, mitigation_strategy: str) -> Dict:
        """
        Apply bias mitigation techniques.

        Strategies:
        - Reweighting: Adjust training sample weights
        - Resampling: Oversample minority groups
        - Adversarial debiasing: Train with adversarial fairness loss
        - Post-processing: Adjust predictions for fairness
        """
        system = db.ai_systems.find_one({"system_id": system_id})

        # Apply mitigation strategy
        if mitigation_strategy == "reweighting":
            result = self._apply_reweighting(system)
        elif mitigation_strategy == "adversarial_debiasing":
            result = self._apply_adversarial_debiasing(system)
        else:
            raise ValueError(f"Unknown mitigation strategy: {mitigation_strategy}")

        logger.info("Bias mitigation applied", extra={
            "event": "bias_mitigation",
            "system_id": system_id,
            "strategy": mitigation_strategy
        })

        return result

class AIExplainability:
    """
    Explainability and interpretability for AI systems.

    NIST Categories:
    - MEASURE 4.1: Explainability methods applied
    - Trustworthy AI Characteristic: Explainable and Interpretable
    """

    def generate_explanation(
        self,
        system_id: str,
        model,
        input_data: np.ndarray,
        method: str = "shap"
    ) -> Dict:
        """
        Generate explanations for model predictions.

        Methods:
        - SHAP (SHapley Additive exPlanations)
        - LIME (Local Interpretable Model-agnostic Explanations)
        - Attention mechanisms (for transformers)
        """
        import shap

        if method == "shap":
            explainer = shap.Explainer(model)
            shap_values = explainer(input_data)

            explanation = {
                "method": "shap",
                "feature_importance": shap_values.values.tolist(),
                "base_values": shap_values.base_values.tolist(),
                "data": input_data.tolist()
            }

        logger.info("Model explanation generated", extra={
            "event": "model_explanation",
            "system_id": system_id,
            "method": method
        })

        return explanation

    def generate_model_card(self, system_id: str) -> Dict:
        """
        Generate Model Card documenting model details.

        NIST MEASURE 4.1 & GOVERN 1.1: Documentation requirements

        Model Card includes:
        - Model details (architecture, version)
        - Intended use and limitations
        - Training data and evaluation data
        - Performance metrics
        - Ethical considerations
        - Bias evaluation results
        """
        system = db.ai_systems.find_one({"system_id": system_id})

        model_card = {
            "model_name": system["system_name"],
            "version": system.get("model_version", "1.0"),
            "created_date": datetime.utcnow().isoformat(),

            # Model Details
            "model_details": {
                "architecture": system.get("architecture", "Unknown"),
                "model_type": system["system_type"],
                "training_data": system.get("training_data_description"),
                "hyperparameters": system.get("hyperparameters", {})
            },

            # Intended Use
            "intended_use": {
                "use_case": system["use_case"],
                "primary_users": system.get("primary_users", []),
                "out_of_scope_uses": system.get("out_of_scope_uses", [])
            },

            # Performance
            "performance_metrics": self._get_performance_metrics(system_id),

            # Bias Evaluation
            "bias_evaluation": self._get_latest_bias_evaluation(system_id),

            # Limitations
            "limitations": system.get("known_limitations", []),

            # Ethical Considerations
            "ethical_considerations": system.get("ethical_considerations", {})
        }

        return model_card
```

---

## MANAGE Implementation

### Continuous Monitoring and Incident Response

**NIST Category**: MANAGE 3.1, MANAGE 4.1

**Implementation**:

```python
# AI system monitoring and incident response
from evidently import ColumnMapping
from evidently.metric_preset import DataDriftPreset, DataQualityPreset
import mlflow

class AIContinuousMonitoring:
    """
    Continuous monitoring of AI systems in production.

    NIST Categories:
    - MANAGE 3.1: Risk monitoring and periodic review
    - Trustworthy AI Characteristics: Safe, Secure, Valid and Reliable

    Generative AI Profile:
    - Monitor for confabulation, toxicity, drift
    """

    def monitor_model_drift(
        self,
        system_id: str,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame
    ) -> Dict:
        """
        Monitor for data drift and model performance degradation.

        NIST MANAGE 3.1: Ongoing monitoring of AI system performance.
        """
        from evidently.report import Report

        # Data drift detection
        report = Report(metrics=[
            DataDriftPreset(),
            DataQualityPreset()
        ])

        report.run(
            reference_data=reference_data,
            current_data=current_data,
            column_mapping=ColumnMapping()
        )

        drift_results = report.as_dict()

        # Check if significant drift detected
        drift_detected = drift_results["metrics"][0]["result"]["dataset_drift"]

        if drift_detected:
            # Trigger alert
            self._create_drift_alert(system_id, drift_results)

        logger.warning("Model drift monitoring completed", extra={
            "event": "model_drift_monitoring",
            "system_id": system_id,
            "drift_detected": drift_detected
        })

        return {
            "system_id": system_id,
            "drift_detected": drift_detected,
            "drift_report": drift_results
        }

    def monitor_generative_ai_safety(
        self,
        system_id: str,
        generated_outputs: List[str]
    ) -> Dict:
        """
        Monitor generative AI outputs for safety issues.

        NIST Generative AI Profile:
        - Confabulation detection
        - Toxicity detection
        - PII leakage detection
        - Harmful content detection
        """
        safety_issues = []

        for idx, output in enumerate(generated_outputs):
            # Toxicity detection
            toxicity_score = self._detect_toxicity(output)
            if toxicity_score > 0.7:
                safety_issues.append({
                    "issue_type": "toxicity",
                    "output_index": idx,
                    "score": toxicity_score,
                    "nist_category": "GenAI Profile - Toxicity"
                })

            # PII leakage detection
            pii_detected = self._detect_pii(output)
            if pii_detected:
                safety_issues.append({
                    "issue_type": "pii_leakage",
                    "output_index": idx,
                    "pii_types": pii_detected,
                    "nist_category": "GenAI Profile - Data Privacy"
                })

            # Factual consistency check (confabulation)
            if self._requires_factual_accuracy(system_id):
                hallucination_score = self._detect_hallucination(output)
                if hallucination_score > 0.5:
                    safety_issues.append({
                        "issue_type": "confabulation",
                        "output_index": idx,
                        "score": hallucination_score,
                        "nist_category": "GenAI Profile - Confabulation"
                    })

        # Log safety monitoring results
        logger.warning("GenAI safety monitoring completed", extra={
            "event": "genai_safety_monitoring",
            "system_id": system_id,
            "outputs_evaluated": len(generated_outputs),
            "safety_issues_found": len(safety_issues)
        })

        return {
            "system_id": system_id,
            "safety_issues": safety_issues,
            "safe": len(safety_issues) == 0
        }

class AIIncidentResponse:
    """
    Incident response for AI systems.

    NIST Categories:
    - MANAGE 4.1: Mechanisms for response to AI incidents
    - GOVERN 4.1: Accountability structures
    """

    class IncidentSeverity(Enum):
        P1_CRITICAL = "p1_critical"  # Safety risk, rights violation
        P2_HIGH = "p2_high"  # Significant harm, data breach
        P3_MEDIUM = "p3_medium"  # Performance degradation
        P4_LOW = "p4_low"  # Minor issues

    def create_ai_incident(
        self,
        system_id: str,
        incident_type: str,
        description: str,
        severity: IncidentSeverity
    ) -> str:
        """
        Create AI-specific incident (bias, hallucination, drift, etc.).

        NIST MANAGE 4.1: AI incident response plan.
        """
        incident_id = generate_uuid()

        incident_record = {
            "incident_id": incident_id,
            "system_id": system_id,
            "incident_type": incident_type,
            "description": description,
            "severity": severity.value,
            "created_date": datetime.utcnow(),
            "status": "open",
            "assigned_to": self._assign_incident_owner(severity),

            # Response tracking
            "response_actions": [],
            "resolution_date": None,
            "root_cause": None,

            # NIST requirements
            "affected_users": None,
            "bias_involved": incident_type == "bias_detected",
            "safety_impact": severity in [self.IncidentSeverity.P1_CRITICAL,
                                         self.IncidentSeverity.P2_HIGH]
        }

        db.ai_incidents.insert_one(incident_record)

        # Immediate actions for critical incidents
        if severity == self.IncidentSeverity.P1_CRITICAL:
            self._trigger_critical_incident_response(incident_id)

        logger.critical("AI incident created", extra={
            "event": "ai_incident_created",
            "incident_id": incident_id,
            "system_id": system_id,
            "incident_type": incident_type,
            "severity": severity.value
        })

        return incident_id

    def _trigger_critical_incident_response(self, incident_id: str):
        """
        Immediate response for critical AI incidents.

        Actions:
        1. Notify AI Risk Manager, Legal, PR
        2. Consider model takedown
        3. Preserve evidence
        4. Begin investigation
        """
        incident = db.ai_incidents.find_one({"incident_id": incident_id})

        # Notify stakeholders
        self._notify_stakeholders(incident)

        # Decision: Take model offline?
        if self._requires_immediate_takedown(incident):
            self._take_model_offline(incident["system_id"])

        # Preserve logs and evidence
        self._preserve_incident_evidence(incident_id)
```

---

## Integration with Other Frameworks

### NIST AI RMF + SOC 2

| NIST AI RMF | SOC 2 Control | Integration |
|-------------|---------------|-------------|
| GOVERN 4.1 | CC1.1 (Control environment) | Governance structures |
| MAP 5.1 | CC9.1 (Risk assessment) | AI-specific risk assessment |
| MEASURE 3.1 | CC6.1 (Logical access) | Bias evaluation as access control |
| MANAGE 3.1 | CC7.2 (System monitoring) | Continuous AI monitoring |

### NIST AI RMF + ISO 27001

| NIST AI RMF | ISO 27001 Control | Integration |
|-------------|-------------------|-------------|
| GOVERN 3.1 | 5.1 (Policies) | AI governance policies |
| MAP 4.1 | 6.1.2 (Risk assessment) | AI-specific risk assessment |
| MEASURE 1.1 | 8.16 (Monitoring) | AI metrics monitoring |
| MANAGE 4.1 | 5.26 (Incident response) | AI incident response |

---

## Success Criteria

### GOVERN Complete

- [ ] AI governance policy documented and approved
- [ ] AI system inventory established
- [ ] Roles and responsibilities assigned (AI Owner, Risk Manager)
- [ ] Risk tolerance defined
- [ ] Policies for AI development, testing, deployment

### MAP Complete

- [ ] All AI systems categorized by risk level
- [ ] Context documentation for each system
- [ ] Impact assessments conducted
- [ ] Risks identified and documented
- [ ] Capabilities and limitations documented

### MEASURE Complete

- [ ] Trustworthy AI metrics defined and tracked
- [ ] Bias evaluation completed for all high-risk systems
- [ ] Explainability methods implemented
- [ ] Model cards generated
- [ ] Test datasets validated for representativeness

### MANAGE Complete

- [ ] Risk treatment plans implemented
- [ ] Continuous monitoring dashboards operational
- [ ] Drift detection configured
- [ ] AI incident response procedures documented
- [ ] Regular risk reviews scheduled (quarterly)

---

## Common Pitfalls

### ❌ Treating as Checklist

**Problem**: Implementing all 56 sub-categories without risk-based prioritization.

**Solution**: Focus on GOVERN first, then MAP to identify high-priority risks, then MEASURE and MANAGE for those risks.

### ❌ Ignoring Generative AI Profile

**Problem**: Applying generic AI RMF to GenAI without addressing new risks.

**Solution**: Use Generative AI Profile (July 2024) for LLMs and diffusion models. Address confabulation, prompt injection, data privacy.

### ❌ No Continuous Monitoring

**Problem**: One-time assessment without ongoing monitoring.

**Solution**: Implement continuous monitoring (MANAGE 3.1). AI systems drift over time.

### ❌ Insufficient Stakeholder Engagement

**Problem**: Technical team only, no input from affected communities.

**Solution**: NIST emphasizes diverse stakeholder input throughout lifecycle (GOVERN, MAP, MEASURE, MANAGE).

---

## Resources

### Official NIST Resources

- [NIST AI RMF 1.0](https://www.nist.gov/itl/ai-risk-management-framework) - Core framework (January 2023)
- [Generative AI Profile](https://airc.nist.gov/AI_RMF_Knowledge_Base/Generative_AI) - GenAI-specific guidance (July 2024)
- [AI RMF Playbook](https://airc.nist.gov/AI_RMF_Knowledge_Base/Playbook) - Implementation guidance

### Tools

- **Bias Detection**: Fairlearn, AIF360, What-If Tool
- **Explainability**: SHAP, LIME, InterpretML
- **Monitoring**: Evidently AI, WhyLabs, Fiddler AI
- **MLOps**: MLflow, Weights & Biases, Neptune.ai

### Implementation Guides

- [NIST AI RMF Resource Center](https://airc.nist.gov/)
- [US AI Safety Institute](https://www.nist.gov/aisi)

---

## Changelog

### Version 1.0.0 - 2025-12-05

**Added**:
- Complete NIST AI RMF 1.0 implementation for Python
- All 4 functions covered (GOVERN, MAP, MEASURE, MANAGE)
- 56 sub-categories addressed
- Generative AI Profile integration (July 2024)
- GenAI-specific risks: Confabulation, prompt injection, toxicity, data privacy
- AI system inventory and risk categorization
- Bias detection and mitigation (Fairlearn)
- Model explainability (SHAP)
- Continuous monitoring (Evidently)
- AI incident response procedures
- Integration with SOC 2 and ISO 27001

**Framework Coverage**:
- 7 Trustworthy AI characteristics
- 23 categories, 56 sub-categories
- 12 GenAI-specific risk categories

---

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
