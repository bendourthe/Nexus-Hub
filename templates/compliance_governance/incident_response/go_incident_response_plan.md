---
template_id: compliance_governance_incident_response_go
template_name: Incident Response Plan - Go
version: 1.0.0
last_updated: 2025-12-05
language: go
category: compliance_governance
phase: incident_response
phase_number: 5
difficulty: intermediate
estimated_time_hours: 4-6
prerequisites:
  - compliance_frameworks/go_soc2_compliance.md
  - compliance_frameworks/go_iso27001_implementation.md
related_templates:
  - incident_response/go_breach_protocols.md
  - privacy_protection/go_gdpr_compliance.md
tools:
  - PagerDuty (alerting)
  - JIRA (incident tracking)
tags:
  - incident-response
  - security-incidents
  - cyber-incidents
  - go
---

# Incident Response Plan - Go

**6-phase incident response lifecycle implementation**

[← Back to Incident Response](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### Incident Response Lifecycle

**NIST SP 800-61**: 6-phase incident response process

1. **Preparation** - Tools, training, procedures
2. **Detection and Analysis** - Identify incidents
3. **Containment** - Stop spread
4. **Eradication** - Remove threat
5. **Recovery** - Restore operations
6. **Post-Incident** - Lessons learned

### Framework Requirements

**ISO 27001 Control 5.26**: Response to information security incidents
**SOC 2 CC7.4**: Respond to security incidents

---

## Implementation

```go
package security

import (
	"time"

	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

type IncidentSeverity string

const (
	P1Critical IncidentSeverity = "p1_critical" // System down, data breach
	P2High     IncidentSeverity = "p2_high"     // Significant impact
	P3Medium   IncidentSeverity = "p3_medium"   // Moderate impact
	P4Low      IncidentSeverity = "p4_low"      // Minor issue
)

type IncidentStatus string

const (
	Detected      IncidentStatus = "detected"
	Investigating IncidentStatus = "investigating"
	Contained     IncidentStatus = "contained"
	Eradicated    IncidentStatus = "eradicated"
	Recovered     IncidentStatus = "recovered"
	Closed        IncidentStatus = "closed"
)

var responseSLA = map[IncidentSeverity]int{
	P1Critical: 15,   // 15 minutes
	P2High:     60,   // 1 hour
	P3Medium:   240,  // 4 hours
	P4Low:      1440, // 24 hours
}

type Incident struct {
	IncidentID         string
	Title              string
	Description        string
	Severity           IncidentSeverity
	IncidentType       string
	DetectedBy         string
	DetectedDate       time.Time
	Status             IncidentStatus
	ResponseDeadline   time.Time
	IncidentCommander  string
	ResponseTeam       []string
	ContainedDate      *time.Time
	EradicatedDate     *time.Time
	RecoveredDate      *time.Time
	ClosedDate         *time.Time
	SystemsAffected    []string
	DataAffected       bool
	UsersAffectedCount int
}

type IncidentResponseService struct {
	logger *logrus.Logger
	// incidentRepo IncidentRepository
	// reviewRepo ReviewRepository
}

func NewIncidentResponseService(logger *logrus.Logger) *IncidentResponseService {
	return &IncidentResponseService{
		logger: logger,
	}
}

func (s *IncidentResponseService) CreateIncident(
	title, description string,
	severity IncidentSeverity,
	incidentType, detectedBy string) (string, error) {

	incidentID := uuid.New().String()
	responseDeadline := time.Now().UTC().Add(time.Duration(responseSLA[severity]) * time.Minute)

	incident := &Incident{
		IncidentID:       incidentID,
		Title:            title,
		Description:      description,
		Severity:         severity,
		IncidentType:     incidentType,
		DetectedBy:       detectedBy,
		DetectedDate:     time.Now().UTC(),
		Status:           Detected,
		ResponseDeadline: responseDeadline,
		ResponseTeam:     []string{},
		SystemsAffected:  []string{},
		DataAffected:     false,
		UsersAffectedCount: 0,
	}

	// s.incidentRepo.Save(incident)

	// Alert response team for critical/high severity
	if severity == P1Critical || severity == P2High {
		s.alertResponseTeam(incidentID)
	}

	s.logger.WithFields(logrus.Fields{
		"incident_id": incidentID,
		"severity":    severity,
	}).Error("Security incident created")

	return incidentID, nil
}

func (s *IncidentResponseService) ContainIncident(incidentID string, containmentActions []string) error {
	now := time.Now().UTC()

	updates := map[string]interface{}{
		"status":              Contained,
		"contained_date":      &now,
		"containment_actions": containmentActions,
	}

	// s.incidentRepo.Update(incidentID, updates)

	s.logger.WithFields(logrus.Fields{
		"incident_id": incidentID,
		"actions":     containmentActions,
	}).Warn("Incident contained")

	return nil
}

func (s *IncidentResponseService) EradicateThreat(incidentID string, eradicationActions []string) error {
	now := time.Now().UTC()

	updates := map[string]interface{}{
		"status":              Eradicated,
		"eradicated_date":     &now,
		"eradication_actions": eradicationActions,
	}

	// s.incidentRepo.Update(incidentID, updates)

	s.logger.WithField("incident_id", incidentID).Info("Threat eradicated")

	return nil
}

func (s *IncidentResponseService) RecoverSystems(incidentID string, recoveryActions []string) error {
	now := time.Now().UTC()

	updates := map[string]interface{}{
		"status":           Recovered,
		"recovered_date":   &now,
		"recovery_actions": recoveryActions,
	}

	// s.incidentRepo.Update(incidentID, updates)

	s.logger.WithField("incident_id", incidentID).Info("Systems recovered")

	return nil
}

func (s *IncidentResponseService) CloseIncident(incidentID, rootCause, lessonsLearned string) error {
	// incident, err := s.incidentRepo.GetByID(incidentID)
	// if err != nil {
	//     return err
	// }

	// Simulated incident for demonstration
	detectedDate := time.Now().UTC().Add(-48 * time.Hour)

	// Calculate metrics
	totalDurationHours := time.Since(detectedDate).Hours()

	postMortem := map[string]interface{}{
		"incident_id":           incidentID,
		"root_cause":            rootCause,
		"lessons_learned":       lessonsLearned,
		"total_duration_hours":  totalDurationHours,
		"created_date":          time.Now().UTC(),
	}

	// s.postMortemRepo.Save(postMortem)

	now := time.Now().UTC()
	updates := map[string]interface{}{
		"status":      Closed,
		"closed_date": &now,
		"root_cause":  rootCause,
	}

	// s.incidentRepo.Update(incidentID, updates)

	s.logger.WithFields(logrus.Fields{
		"incident_id":    incidentID,
		"duration_hours": totalDurationHours,
	}).Info("Incident closed")

	return nil
}

func (s *IncidentResponseService) GenerateIncidentReport(incidentID string) (map[string]interface{}, error) {
	// incident, err := s.incidentRepo.GetByID(incidentID)
	// if err != nil {
	//     return nil, err
	// }
	// postMortem, _ := s.postMortemRepo.GetByIncidentID(incidentID)

	// Simulated data for demonstration
	incident := map[string]interface{}{
		"incident_id":          incidentID,
		"title":                "Database breach detected",
		"severity":             string(P1Critical),
		"detected_date":        time.Now().UTC().Add(-48 * time.Hour),
		"closed_date":          time.Now().UTC(),
		"systems_affected":     []string{"database_server", "web_application"},
		"data_affected":        true,
		"users_affected_count": 5000,
		"containment_actions":  []string{"Revoked access", "Changed passwords"},
		"eradication_actions":  []string{"Removed malware", "Patched vulnerability"},
		"recovery_actions":     []string{"Restored from backup", "Verified integrity"},
	}

	postMortem := map[string]interface{}{
		"root_cause":       "Unpatched SQL injection vulnerability",
		"lessons_learned":  "Implement automated patching, enhance monitoring",
	}

	report := map[string]interface{}{
		"incident_id":         incidentID,
		"title":               incident["title"],
		"severity":            incident["severity"],
		"detection_date":      incident["detected_date"],
		"closure_date":        incident["closed_date"],
		"systems_affected":    incident["systems_affected"],
		"data_affected":       incident["data_affected"],
		"users_affected":      incident["users_affected_count"],
		"containment_actions": incident["containment_actions"],
		"eradication_actions": incident["eradication_actions"],
		"recovery_actions":    incident["recovery_actions"],
		"root_cause":          postMortem["root_cause"],
		"lessons_learned":     postMortem["lessons_learned"],
	}

	return report, nil
}

func (s *IncidentResponseService) ConductPostIncidentReview(
	incidentID, rootCause string,
	lessonsLearned, correctiveActions []string) (map[string]interface{}, error) {

	review := map[string]interface{}{
		"review_id":          uuid.New().String(),
		"incident_id":        incidentID,
		"review_date":        time.Now().UTC(),
		"root_cause":         rootCause,
		"lessons_learned":    lessonsLearned,
		"corrective_actions": correctiveActions,
	}

	// s.reviewRepo.Save(review)

	s.logger.WithField("incident_id", incidentID).Info("Post-incident review completed")

	return review, nil
}

func (s *IncidentResponseService) alertResponseTeam(incidentID string) {
	// In production: PagerDuty, email, SMS alerts
	s.logger.WithField("incident_id", incidentID).Error("ALERT: Critical incident created")
}

func (s *IncidentResponseService) schedulePostIncidentReview(incidentID string) {
	// In production: create calendar event
	s.logger.WithField("incident_id", incidentID).Info("Post-incident review scheduled")
}
```

---

## Success Criteria

- [ ] Incident response plan documented
- [ ] Response team identified and trained
- [ ] Incident detection mechanisms operational
- [ ] Escalation procedures defined
- [ ] Post-incident review process established

---

[← Back to Incident Response](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
