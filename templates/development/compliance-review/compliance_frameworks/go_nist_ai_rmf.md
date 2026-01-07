---
template_id: compliance_governance_nist_ai_rmf_go
template_name: NIST AI RMF - Go
version: 1.0.0
last_updated: 2025-12-05
language: go
category: compliance_governance
phase: compliance_frameworks
phase_number: 1
difficulty: advanced
estimated_time_hours: 8-10
prerequisites:
  - compliance_frameworks/go_iso27001_implementation.md
related_templates:
  - ai_agent_governance/go_agent_risk_controls.md
tools:
  - gonum (numerical computing)
  - logrus (logging)
tags:
  - nist-ai-rmf
  - ai-governance
  - responsible-ai
  - go
---

# NIST AI Risk Management Framework - Go

**NIST AI RMF 1.0 + Generative AI Profile for Go applications**

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

**4 Functions**: GOVERN, MAP, MEASURE, MANAGE
**Generative AI Profile**: 12 GenAI-specific risks

---

## GOVERN-1: AI System Inventory

```go
package nist

import (
	"time"

	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

type AISystemType string

const (
	TraditionalML          AISystemType = "traditional_ml"
	GenerativeAI           AISystemType = "generative_ai"
	RecommendationSystem   AISystemType = "recommendation"
)

type RiskLevel string

const (
	RiskLevelLow      RiskLevel = "low"
	RiskLevelMedium   RiskLevel = "medium"
	RiskLevelHigh     RiskLevel = "high"
	RiskLevelCritical RiskLevel = "critical"
)

type AISystemRegistry struct {
	logger *logrus.Logger
}

func NewAISystemRegistry(logger *logrus.Logger) *AISystemRegistry {
	return &AISystemRegistry{logger: logger}
}

func (r *AISystemRegistry) RegisterAISystem(
	systemName string,
	systemType AISystemType,
	useCase string,
	isGenerative bool,
) (string, error) {
	systemID := uuid.New().String()

	r.logger.WithFields(logrus.Fields{
		"event":        "ai_system_registered",
		"system_id":    systemID,
		"system_type":  systemType,
		"is_generative": isGenerative,
		"timestamp":    time.Now().UTC(),
	}).Info("AI system registered")

	return systemID, nil
}
```

---

## MEASURE-2: Bias Detection

```go
package nist

import (
	"math"
)

type BiasDetector struct {
	logger *logrus.Logger
}

type BiasMetrics struct {
	BiasDetected                   bool
	DemographicParityDifferences  map[string]float64
}

func NewBiasDetector(logger *logrus.Logger) *BiasDetector {
	return &BiasDetector{logger: logger}
}

func (d *BiasDetector) DetectBias(
	systemID string,
	predictions []float64,
	sensitiveFeatures map[string][]string,
) BiasMetrics {
	metrics := BiasMetrics{
		DemographicParityDifferences: make(map[string]float64),
	}

	for featureName, featureValues := range sensitiveFeatures {
		// Calculate demographic parity
		groups := unique(featureValues)
		groupRates := make(map[string]float64)

		for _, group := range groups {
			rate := calculatePositivePredictionRate(predictions, featureValues, group)
			groupRates[group] = rate
		}

		maxRate, minRate := findMinMax(groupRates)
		dpDiff := maxRate - minRate

		metrics.DemographicParityDifferences[featureName] = dpDiff

		if math.Abs(dpDiff) > 0.1 {
			metrics.BiasDetected = true
			d.logger.WithFields(logrus.Fields{
				"event":      "bias_detected",
				"system_id":  systemID,
				"feature":    featureName,
				"dp_diff":    dpDiff,
			}).Warn("Bias detected")
		}
	}

	return metrics
}

func unique(slice []string) []string {
	keys := make(map[string]bool)
	var list []string
	for _, entry := range slice {
		if _, value := keys[entry]; !value {
			keys[entry] = true
			list = append(list, entry)
		}
	}
	return list
}

func calculatePositivePredictionRate(predictions []float64, features []string, group string) float64 {
	var sum float64
	var count int
	for i, feature := range features {
		if feature == group {
			sum += predictions[i]
			count++
		}
	}
	if count == 0 {
		return 0
	}
	return sum / float64(count)
}

func findMinMax(m map[string]float64) (float64, float64) {
	var max, min float64
	first := true
	for _, v := range m {
		if first {
			max, min = v, v
			first = false
			continue
		}
		if v > max {
			max = v
		}
		if v < min {
			min = v
		}
	}
	return max, min
}
```

---

## Success Criteria

- [ ] AI systems registered in inventory
- [ ] Risk levels calculated
- [ ] Bias detection operational
- [ ] Demographic parity differences < 0.1

---

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
