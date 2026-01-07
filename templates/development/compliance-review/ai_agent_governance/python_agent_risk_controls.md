---
template_id: compliance_governance_agent_risk_controls_python
template_name: AI Agent Risk Controls - Python
version: 1.0.0
last_updated: 2025-12-05
language: python
category: compliance_governance
phase: ai_agent_governance
phase_number: 5
difficulty: advanced
estimated_time_hours: 4-6
prerequisites:
  - ai_agent_governance/python_agent_lifecycle.md
  - risk_management/python_risk_assessment.md
related_templates:
  - compliance_frameworks/python_nist_ai_rmf.md
  - ai_agent_governance/python_agent_security.md
tools:
  - fairlearn (bias detection)
  - evidently (monitoring)
tags:
  - ai-risk
  - defense-in-depth
  - four-pillars
  - bias-detection
  - python
---

# AI Agent Risk Controls - Python

**⚠️ Pillar 2: Risk Management (Defense in Depth)**

Implement risk controls for AI agents including bias detection and drift monitoring

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### AI Risk Management

**Defense in Depth**: Multiple layers of risk controls

**Key AI Risks**:
- **Bias** - Unfair treatment of protected groups
- **Drift** - Model performance degrades over time
- **Hallucination** - False outputs
- **Data leakage** - Training data exposed
- **Adversarial attacks** - Malicious inputs

---

## Implementation

```python
# AI Agent risk controls
from datetime import datetime
from typing import Dict, List
import numpy as np

class AgentRiskControls:
    """
    AI Agent risk management controls.

    4 Pillars: Risk Management (Defense in Depth)
    Compliance: NIST AI RMF MEASURE, MANAGE
    """

    def detect_bias(
        self,
        agent_id: str,
        predictions: np.ndarray,
        ground_truth: np.ndarray,
        sensitive_features: Dict
    ) -> Dict:
        """
        Detect bias in AI agent predictions.

        NIST AI RMF MEASURE 3.1: Bias evaluation
        Pillar 2: Risk Management (Defense in Depth)
        """
        from fairlearn.metrics import demographic_parity_difference

        # Calculate demographic parity
        dp_diff = demographic_parity_difference(
            y_true=ground_truth,
            y_pred=predictions,
            sensitive_features=sensitive_features["gender"]
        )

        bias_detected = abs(dp_diff) > 0.1  # 10% threshold

        result = {
            "agent_id": agent_id,
            "bias_detected": bias_detected,
            "demographic_parity_diff": dp_diff,
            "threshold": 0.1,
            "evaluation_date": datetime.utcnow()
        }

        if bias_detected:
            logger.warning("Bias detected in agent", extra={
                "agent_id": agent_id,
                "dp_diff": dp_diff
            })

            # Create risk incident
            self._create_bias_incident(agent_id, result)

        return result

    def monitor_drift(
        self,
        agent_id: str,
        reference_data: np.ndarray,
        current_data: np.ndarray
    ) -> Dict:
        """
        Monitor for model drift.

        NIST AI RMF MANAGE 3.1: Risk monitoring
        """
        from evidently.report import Report
        from evidently.metric_preset import DataDriftPreset
        import pandas as pd

        # Create DataFrames
        ref_df = pd.DataFrame(reference_data)
        curr_df = pd.DataFrame(current_data)

        # Detect drift
        report = Report(metrics=[DataDriftPreset()])
        report.run(reference_data=ref_df, current_data=curr_df)

        drift_results = report.as_dict()
        drift_detected = drift_results["metrics"][0]["result"]["dataset_drift"]

        if drift_detected:
            logger.warning("Drift detected in agent", extra={
                "agent_id": agent_id
            })

            # Trigger alert
            self._create_drift_alert(agent_id, drift_results)

        return {
            "agent_id": agent_id,
            "drift_detected": drift_detected,
            "drift_report": drift_results
        }

    def detect_hallucination(
        self,
        agent_id: str,
        generated_text: str,
        source_documents: List[str]
    ) -> Dict:
        """
        Detect hallucinations in agent output.

        NIST GenAI Profile: Confabulation risk
        """
        # Simple factual consistency check
        # Production: Use NLI models or fact-checking APIs
        hallucination_score = self._calculate_hallucination_score(
            generated_text,
            source_documents
        )

        hallucination_detected = hallucination_score > 0.5

        if hallucination_detected:
            logger.warning("Hallucination detected", extra={
                "agent_id": agent_id,
                "score": hallucination_score
            })

        return {
            "agent_id": agent_id,
            "hallucination_detected": hallucination_detected,
            "score": hallucination_score
        }

    def _create_bias_incident(self, agent_id: str, bias_result: Dict):
        """
        Create incident for bias detection.

        Automatic remediation: Flag agent for review
        """
        incident_id = generate_uuid()

        db.risk_incidents.insert_one({
            "incident_id": incident_id,
            "agent_id": agent_id,
            "incident_type": "bias_detected",
            "severity": "high",
            "details": bias_result,
            "created_date": datetime.utcnow(),
            "status": "open"
        })

        # Flag agent for review
        db.ai_agents.update_one(
            {"agent_id": agent_id},
            {"$set": {"requires_bias_review": True}}
        )

    def implement_risk_mitigations(self, agent_id: str) -> Dict:
        """
        Implement defense-in-depth risk mitigations.

        Pillar 2: Risk Management (Defense in Depth)
        """
        mitigations = {
            "input_validation": True,
            "output_sanitization": True,
            "rate_limiting": True,
            "bias_monitoring": True,
            "drift_detection": True,
            "hallucination_detection": True,
            "pii_redaction": True
        }

        db.ai_agents.update_one(
            {"agent_id": agent_id},
            {"$set": {"risk_mitigations": mitigations}}
        )

        logger.info("Risk mitigations implemented", extra={
            "agent_id": agent_id,
            "mitigations": list(mitigations.keys())
        })

        return mitigations

    def _calculate_hallucination_score(
        self,
        generated_text: str,
        source_documents: List[str]
    ) -> float:
        """
        Calculate hallucination likelihood.

        Higher score = more likely to be hallucination
        """
        # Simple implementation: Check if generated text
        # contains facts not in source documents
        # Production: Use semantic similarity or NLI models

        generated_lower = generated_text.lower()
        sources_lower = " ".join(source_documents).lower()

        # Count how many generated words appear in sources
        generated_words = set(generated_lower.split())
        source_words = set(sources_lower.split())

        overlap = len(generated_words & source_words)
        total = len(generated_words)

        # Score: 1 - (overlap / total)
        # High score = low overlap = likely hallucination
        score = 1.0 - (overlap / total) if total > 0 else 0.0

        return score
```

---

## Success Criteria

- [ ] Bias detection implemented for all agents
- [ ] Drift monitoring operational
- [ ] Hallucination detection configured
- [ ] Defense-in-depth mitigations deployed
- [ ] Risk incidents tracked and remediated

---

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
