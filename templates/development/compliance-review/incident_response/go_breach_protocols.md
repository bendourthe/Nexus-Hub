---
template_id: compliance_governance_breach_protocols_go
template_name: Breach Protocols - Go
version: 1.0.0
last_updated: 2025-12-05
language: go
category: compliance_governance
phase: incident_response
phase_number: 5
difficulty: advanced
estimated_time_hours: 4-6
prerequisites:
  - incident_response/go_incident_response_plan.md
  - privacy_protection/go_gdpr_compliance.md
related_templates:
  - compliance_frameworks/go_soc2_compliance.md
tools:
  - Forensics tools
tags:
  - data-breach
  - breach-notification
  - gdpr
  - ccpa
  - go
---

# Breach Protocols - Go

**Data breach notification and response protocols (GDPR 72-hour rule)**

[← Back to Incident Response](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### Data Breach Notification Requirements

**GDPR Article 33**: Notify supervisory authority within 72 hours
**GDPR Article 34**: Notify individuals if high risk
**CCPA**: No specific timeline, but must notify "without unreasonable delay"
**State Laws**: Varies (CA requires notification without unreasonable delay)

---

## Implementation

```go
package security

import (
	"time"

	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

const gdprNotificationDeadlineHours = 72

type RiskLevel string

const (
	RiskLow      RiskLevel = "low"
	RiskMedium   RiskLevel = "medium"
	RiskHigh     RiskLevel = "high"
	RiskCritical RiskLevel = "critical"
)

type BreachNotificationService struct {
	logger *logrus.Logger
}

func NewBreachNotificationService(logger *logrus.Logger) *BreachNotificationService {
	return &BreachNotificationService{
		logger: logger,
	}
}

func (s *BreachNotificationService) AssessBreach(incidentID string) (map[string]interface{}, error) {
	// Simulated incident
	incident := map[string]interface{}{
		"incident_id":           incidentID,
		"data_affected":         true,
		"detected_date":         time.Now().UTC(),
		"users_affected_count":  5000,
		"ca_residents_affected": true,
	}

	isBreach := incident["data_affected"].(bool)

	if !isBreach {
		return map[string]interface{}{"is_breach": false}, nil
	}

	riskLevel := s.assessRiskLevel(incident)
	breachID := uuid.New().String()
	gdprDeadline := time.Now().UTC().Add(time.Duration(gdprNotificationDeadlineHours) * time.Hour)

	breachAssessment := map[string]interface{}{
		"is_breach":             true,
		"breach_id":             breachID,
		"incident_id":           incidentID,
		"detected_date":         incident["detected_date"],
		"risk_level":            string(riskLevel),
		"notify_gdpr_authority": riskLevel == RiskMedium || riskLevel == RiskHigh || riskLevel == RiskCritical,
		"notify_individuals":    riskLevel == RiskHigh || riskLevel == RiskCritical,
		"notify_ccpa":           incident["ca_residents_affected"],
		"gdpr_deadline":         gdprDeadline,
	}

	s.logger.WithFields(logrus.Fields{
		"breach_id":  breachID,
		"risk_level": riskLevel,
	}).Error("Data breach assessed")

	return breachAssessment, nil
}

func (s *BreachNotificationService) assessRiskLevel(incident map[string]interface{}) RiskLevel {
	usersAffected := incident["users_affected_count"].(int)

	if usersAffected > 10000 {
		return RiskCritical
	} else if usersAffected > 1000 {
		return RiskHigh
	} else if usersAffected > 100 {
		return RiskMedium
	}
	return RiskLow
}

func (s *BreachNotificationService) NotifyGdprAuthority(breachID string) (string, error) {
	notificationID := uuid.New().String()

	notification := map[string]interface{}{
		"notification_id":     notificationID,
		"breach_id":           breachID,
		"notification_type":   "gdpr_authority",
		"notification_date":   time.Now().UTC(),
		"nature_of_breach":    "Unauthorized access to customer database",
		"dpo_contact":         "dpo@company.com",
		"likely_consequences": "Risk of identity theft for affected individuals",
		"measures_taken":      "Database access revoked, passwords reset, monitoring enhanced",
	}

	s.sendToAuthority(notification)

	s.logger.WithField("notification_id", notificationID).Error("GDPR authority notified")

	return notificationID, nil
}

func (s *BreachNotificationService) NotifyIndividuals(breachID string) (int, error) {
	affectedCount := 5000 // Simulated

	notificationContent := `
Subject: Important Security Notice

We are writing to inform you of a data security incident.

What Happened: Unauthorized access to customer database
What Information Was Involved: Names, email addresses, account numbers
What We Are Doing: Enhanced security measures, password resets, monitoring
What You Can Do: Update your password, enable 2FA, monitor accounts

Contact: security@company.com
`

	s.logger.WithFields(logrus.Fields{
		"breach_id": breachID,
		"count":     affectedCount,
	}).Error("Individuals notified")

	_ = notificationContent

	return affectedCount, nil
}

func (s *BreachNotificationService) NotifyCcpa(breachID string) error {
	s.logger.WithField("breach_id", breachID).Info("CCPA notification initiated")
	return nil
}

func (s *BreachNotificationService) sendToAuthority(notification map[string]interface{}) {
	s.logger.Info("Sending notification to GDPR supervisory authority")
}

func (s *BreachNotificationService) GenerateBreachReport(breachID string) (map[string]interface{}, error) {
	report := map[string]interface{}{
		"report_id":          uuid.New().String(),
		"breach_id":          breachID,
		"generated_date":     time.Now().UTC(),
		"executive_summary":  "Summary of breach incident",
		"timeline":           "Detailed timeline of events",
		"impact_analysis":    "Analysis of affected systems and data",
		"response_actions":   "Actions taken to contain and remediate",
		"lessons_learned":    "Key takeaways and improvements",
	}

	s.logger.WithField("breach_id", breachID).Info("Breach report generated")

	return report, nil
}
```

---

## Success Criteria

- [ ] Breach detection mechanisms operational
- [ ] 72-hour notification workflow implemented
- [ ] Notification templates ready
- [ ] Authority contacts established
- [ ] Breach simulation conducted

---

[← Back to Incident Response](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
