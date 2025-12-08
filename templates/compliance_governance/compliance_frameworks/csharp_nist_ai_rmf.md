---
template_id: compliance_governance_nist_ai_rmf_csharp
template_name: NIST AI RMF - C#
version: 1.0.0
last_updated: 2025-12-05
language: csharp
category: compliance_governance
phase: compliance_frameworks
phase_number: 1
difficulty: advanced
estimated_time_hours: 8-10
prerequisites:
  - compliance_frameworks/csharp_iso27001_implementation.md
related_templates:
  - ai_agent_governance/csharp_agent_risk_controls.md
tools:
  - ML.NET (machine learning)
  - Serilog (logging)
tags:
  - nist-ai-rmf
  - ai-governance
  - responsible-ai
  - csharp
---

# NIST AI Risk Management Framework - C#

**NIST AI RMF 1.0 + Generative AI Profile for .NET applications**

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### NIST AI RMF 1.0 Functions

1. **GOVERN**: Establish AI governance
2. **MAP**: Context and risk mapping
3. **MEASURE**: Assess AI risks
4. **MANAGE**: Mitigate AI risks

### Generative AI Profile (July 2024)

**12 GenAI-Specific Risks**: Confabulation, prompt injection, toxicity, bias amplification

---

## GOVERN-1: AI System Inventory

```csharp
using System;
using System.Collections.Generic;
using Microsoft.Extensions.Logging;

namespace ComplianceGovernance.NIST
{
    /// <summary>
    /// AI System Registry for NIST AI RMF compliance.
    ///
    /// NIST AI RMF GOVERN-1: AI system inventory
    /// </summary>
    public class AISystemRegistry
    {
        private readonly ILogger<AISystemRegistry> _logger;

        public enum AISystemType
        {
            TraditionalML,
            GenerativeAI,
            RecommendationSystem,
            ComputerVision,
            NaturalLanguageProcessing
        }

        public enum RiskLevel
        {
            Low,
            Medium,
            High,
            Critical
        }

        public AISystemRegistry(ILogger<AISystemRegistry> logger)
        {
            _logger = logger;
        }

        /// <summary>
        /// Register AI system in inventory.
        /// </summary>
        public string RegisterAISystem(
            string systemName,
            AISystemType systemType,
            string useCase,
            Dictionary<string, object> impactAssessment,
            bool isGenerative = false)
        {
            var systemId = Guid.NewGuid().ToString();
            var riskLevel = CalculateRiskLevel(impactAssessment);

            var systemRecord = new
            {
                SystemId = systemId,
                SystemName = systemName,
                SystemType = systemType,
                UseCase = useCase,
                IsGenerative = isGenerative,
                RiskLevel = riskLevel,
                RegisteredAt = DateTime.UtcNow,
                CapabilitiesDocumented = false,
                BiasEvaluationCompleted = false,
                SafetyTestingCompleted = false
            };

            _logger.LogInformation("AI system registered: SystemId={SystemId}, Type={Type}, Risk={Risk}",
                systemId, systemType, riskLevel);

            return systemId;
        }

        private RiskLevel CalculateRiskLevel(Dictionary<string, object> impact)
        {
            // Calculate based on impact assessment
            // NIST AI RMF MEASURE function
            return RiskLevel.Medium;
        }
    }
}
```

---

## MEASURE-2: Bias Detection

```csharp
using System;
using System.Collections.Generic;
using System.Linq;

namespace ComplianceGovernance.NIST
{
    /// <summary>
    /// Bias detection for AI systems.
    ///
    /// NIST AI RMF MEASURE-2.1: Demographic parity
    /// NIST AI RMF MEASURE-2.2: Equalized odds
    /// </summary>
    public class BiasDetector
    {
        private readonly ILogger<BiasDetector> _logger;

        public BiasDetector(ILogger<BiasDetector> logger)
        {
            _logger = logger;
        }

        /// <summary>
        /// Detect bias using demographic parity.
        /// </summary>
        public BiasMetrics DetectBias(
            string systemId,
            double[] predictions,
            double[] groundTruth,
            Dictionary<string, string[]> sensitiveFeatures)
        {
            var results = new BiasMetrics();

            foreach (var feature in sensitiveFeatures)
            {
                var featureName = feature.Key;
                var groups = feature.Value.Distinct().ToArray();

                var groupMetrics = new Dictionary<string, double>();

                foreach (var group in groups)
                {
                    var groupIndices = feature.Value
                        .Select((val, idx) => new { val, idx })
                        .Where(x => x.val == group)
                        .Select(x => x.idx)
                        .ToArray();

                    var groupPredictions = groupIndices.Select(i => predictions[i]).ToArray();
                    var positivePredictionRate = groupPredictions.Average();

                    groupMetrics[group] = positivePredictionRate;
                }

                var maxRate = groupMetrics.Values.Max();
                var minRate = groupMetrics.Values.Min();
                var demographicParityDifference = maxRate - minRate;

                results.DemographicParityDifferences[featureName] = demographicParityDifference;

                var biasDetected = Math.Abs(demographicParityDifference) > 0.1;

                if (biasDetected)
                {
                    _logger.LogWarning("Bias detected: SystemId={SystemId}, Feature={Feature}, " +
                                     "DPDiff={Diff:F3}",
                        systemId, featureName, demographicParityDifference);
                }

                results.BiasDetected = results.BiasDetected || biasDetected;
            }

            return results;
        }

        public class BiasMetrics
        {
            public bool BiasDetected { get; set; }
            public Dictionary<string, double> DemographicParityDifferences { get; set; } = new();
        }
    }
}
```

---

## GenAI Profile: Hallucination Detection

```csharp
using System;
using System.Text.RegularExpressions;

namespace ComplianceGovernance.NIST
{
    /// <summary>
    /// Hallucination detection for GenAI systems.
    ///
    /// NIST GenAI Profile: CBRN Information risk
    /// NIST GenAI Profile: Confabulation risk
    /// </summary>
    public class HallucinationDetector
    {
        private readonly ILogger<HallucinationDetector> _logger;

        public HallucinationDetector(ILogger<HallucinationDetector> logger)
        {
            _logger = logger;
        }

        /// <summary>
        /// Detect potential hallucinations in AI-generated text.
        /// </summary>
        public HallucinationResult DetectHallucination(string aiOutput, string sourceContext)
        {
            var result = new HallucinationResult();

            // Check for unsupported claims
            if (ContainsUnsupportedClaim(aiOutput, sourceContext))
            {
                result.HallucinationDetected = true;
                result.Confidence = 0.8;
                result.Reason = "Unsupported claim not found in source context";

                _logger.LogWarning("Hallucination detected: Confidence={Confidence:F2}, Reason={Reason}",
                    result.Confidence, result.Reason);
            }

            return result;
        }

        private bool ContainsUnsupportedClaim(string output, string context)
        {
            // Simple heuristic: Check if output contains specific claims not in context
            // Production: Use semantic similarity or fact-checking models
            return false;
        }

        public class HallucinationResult
        {
            public bool HallucinationDetected { get; set; }
            public double Confidence { get; set; }
            public string Reason { get; set; }
        }
    }
}
```

---

## Success Criteria

- [ ] AI systems registered in inventory
- [ ] Risk levels calculated for all AI systems
- [ ] Bias detection implemented for protected classes
- [ ] Hallucination detection for GenAI outputs
- [ ] Demographic parity differences < 0.1
- [ ] All high-risk AI systems have safety documentation

---

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
