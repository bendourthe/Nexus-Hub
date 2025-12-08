---
template_id: compliance_governance_agent_risk_controls_go
template_name: AI Agent Risk Controls - Go
version: 1.0.0
last_updated: 2025-12-05
language: go
category: compliance_governance
phase: ai_agent_governance
phase_number: 5
difficulty: advanced
estimated_time_hours: 4-6
prerequisites:
  - ai_agent_governance/go_agent_lifecycle.md
  - risk_management/go_risk_assessment.md
related_templates:
  - ai_agent_governance/go_agent_security.md
tools:
  - go-circuitbreaker
tags:
  - risk-management
  - defense-in-depth
  - four-pillars
  - go
---

# AI Agent Risk Controls - Go

**⚠️ Pillar 2: Risk Management (Defense in Depth)**

Implement risk controls for AI agent operations

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

**Defense in Depth**: Multiple layers of risk controls

**Risk Controls**:
- Rate limiting
- Circuit breakers
- Confidence thresholds
- Human-in-the-loop

---

## Implementation

```go
package ai

import (
	"time"

	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

type RiskLevel string

const (
	RiskLow      RiskLevel = "low"
	RiskMedium   RiskLevel = "medium"
	RiskHigh     RiskLevel = "high"
	RiskCritical RiskLevel = "critical"
)

const (
	confidenceThreshold = 0.7
	rateLimitPerMinute  = 60
)

type AgentRiskControlsService struct {
	logger *logrus.Logger
	// circuitBreakerRepo CircuitBreakerRepository
}

func NewAgentRiskControlsService(logger *logrus.Logger) *AgentRiskControlsService {
	return &AgentRiskControlsService{
		logger: logger,
	}
}

func (s *AgentRiskControlsService) CheckRateLimit(agentID, userID string) bool {
	requestCount := s.getRequestCount(userID)

	if requestCount >= rateLimitPerMinute {
		s.logger.WithFields(logrus.Fields{
			"agent_id": agentID,
			"user_id":  userID,
			"count":    requestCount,
		}).Warn("Rate limit exceeded")
		return false
	}

	return true
}

func (s *AgentRiskControlsService) EvaluateDecisionRisk(
	agentID string,
	decision map[string]interface{},
	confidence float64) map[string]interface{} {

	riskLevel := RiskLow
	requiresHumanReview := false
	riskFactors := []string{}

	// Check confidence threshold
	if confidence < confidenceThreshold {
		riskLevel = RiskHigh
		requiresHumanReview = true
		riskFactors = append(riskFactors, "Low confidence score")
	}

	// Check financial impact
	if financialImpact, ok := decision["financial_impact"].(float64); ok {
		if financialImpact > 10000 {
			riskLevel = RiskCritical
			requiresHumanReview = true
			riskFactors = append(riskFactors, "High financial impact")
		}
	}

	// Check sensitive data access
	if accessesPII, ok := decision["accesses_pii"].(bool); ok && accessesPII {
		if riskLevel == RiskLow {
			riskLevel = RiskMedium
		}
		riskFactors = append(riskFactors, "Accesses PII data")
	}

	riskAssessment := map[string]interface{}{
		"agent_id":              agentID,
		"risk_level":            string(riskLevel),
		"requires_human_review": requiresHumanReview,
		"risk_factors":          riskFactors,
		"confidence":            confidence,
	}

	if requiresHumanReview {
		s.logger.WithFields(logrus.Fields{
			"agent_id":   agentID,
			"risk_level": riskLevel,
		}).Warn("Decision requires human review")
	}

	return riskAssessment
}

func (s *AgentRiskControlsService) EnableCircuitBreaker(agentID, reason string) {
	s.logger.WithFields(logrus.Fields{
		"agent_id": agentID,
		"reason":   reason,
	}).Error("Circuit breaker activated")

	circuitBreaker := map[string]interface{}{
		"agent_id":     agentID,
		"status":       "open",
		"reason":       reason,
		"activated_at": time.Now().UTC(),
	}

	// s.circuitBreakerRepo.Save(circuitBreaker)
}

func (s *AgentRiskControlsService) CheckCircuitBreaker(agentID string) bool {
	// In production, query circuit breaker state from repository
	// Return false if circuit is open (agent disabled)
	return true
}

func (s *AgentRiskControlsService) ApplyConfidenceThreshold(
	agentID string,
	confidence float64,
	decision map[string]interface{}) map[string]interface{} {

	if confidence < confidenceThreshold {
		s.logger.WithFields(logrus.Fields{
			"agent_id":  agentID,
			"confidence": confidence,
			"threshold":  confidenceThreshold,
		}).Warn("Confidence below threshold")

		return map[string]interface{}{
			"approved":       false,
			"reason":         "Confidence below threshold",
			"requires_review": true,
			"confidence":     confidence,
		}
	}

	return map[string]interface{}{
		"approved":   true,
		"confidence": confidence,
	}
}

func (s *AgentRiskControlsService) getRequestCount(userID string) int {
	// In production, query last minute request count from cache/database
	return 45 // Simulated
}

func (s *AgentRiskControlsService) RequiresHumanApproval(
	agentID string,
	action map[string]interface{}) bool {

	requiresApproval := false

	// High-risk actions always require approval
	if actionType, ok := action["action_type"].(string); ok {
		highRiskActions := map[string]bool{
			"delete":             true,
			"transfer_funds":     true,
			"modify_permissions": true,
		}

		if highRiskActions[actionType] {
			requiresApproval = true
			s.logger.WithFields(logrus.Fields{
				"agent_id":    agentID,
				"action_type": actionType,
			}).Warn("High-risk action requires approval")
		}
	}

	return requiresApproval
}

func (s *AgentRiskControlsService) LogRiskDecision(
	agentID string,
	riskAssessment map[string]interface{},
	approved bool) {

	decisionLog := map[string]interface{}{
		"log_id":          uuid.New().String(),
		"agent_id":        agentID,
		"risk_assessment": riskAssessment,
		"approved":        approved,
		"timestamp":       time.Now().UTC(),
	}

	// s.riskDecisionRepo.Save(decisionLog)

	s.logger.WithFields(logrus.Fields{
		"agent_id": agentID,
		"approved": approved,
	}).Info("Risk decision logged")
}
```

---

## Success Criteria

- [ ] Rate limiting operational
- [ ] Confidence thresholds enforced
- [ ] Human-in-the-loop triggers functional
- [ ] Circuit breakers implemented

---

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
