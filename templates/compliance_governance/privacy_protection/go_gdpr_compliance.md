---
template_id: compliance_governance_gdpr_go
template_name: GDPR Compliance - Go
version: 1.0.0
last_updated: 2025-12-05
language: go
category: compliance_governance
phase: privacy_protection
phase_number: 4
difficulty: advanced
estimated_time_hours: 6-8
prerequisites:
  - privacy_protection/README.md
related_templates:
  - compliance_frameworks/go_iso27001_implementation.md
tools:
  - logrus (logging)
tags:
  - gdpr
  - privacy
  - data-protection
  - go
---

# GDPR Compliance - Go

**General Data Protection Regulation for Go applications**

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

**8 Key Rights**: Access, Rectification, Erasure, Portability, Restriction, Objection, Automated Decision-Making, Data Breach Notification

---

## Right to Access (Art. 15)

```go
package gdpr

import (
	"time"

	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

type DataSubjectAccessHandler struct {
	logger *logrus.Logger
}

type DataSubjectReport struct {
	RequestID          string
	DataSubjectID      string
	RequestDate        time.Time
	ResponseDeadline   time.Time
	PersonalData       map[string]interface{}
	ProcessingPurposes []string
	Recipients         []string
	RetentionPeriod    string
}

func NewDataSubjectAccessHandler(logger *logrus.Logger) *DataSubjectAccessHandler {
	return &DataSubjectAccessHandler{logger: logger}
}

func (h *DataSubjectAccessHandler) ProcessAccessRequest(dataSubjectID string) (*DataSubjectReport, error) {
	requestID := uuid.New().String()
	deadline := time.Now().UTC().Add(30 * 24 * time.Hour)

	report := &DataSubjectReport{
		RequestID:        requestID,
		DataSubjectID:    dataSubjectID,
		RequestDate:      time.Now().UTC(),
		ResponseDeadline: deadline,
		PersonalData: map[string]interface{}{
			"profile":      map[string]string{"name": "User", "email": "user@example.com"},
			"transactions": []interface{}{},
		},
		ProcessingPurposes: []string{
			"Providing services",
			"Improving user experience",
		},
		Recipients: []string{
			"Cloud service providers",
			"Payment processors",
		},
		RetentionPeriod: "7 years for financial records",
	}

	h.logger.WithFields(logrus.Fields{
		"event":           "gdpr_access_request",
		"request_id":      requestID,
		"data_subject_id": dataSubjectID,
		"timestamp":       time.Now().UTC(),
	}).Info("GDPR access request processed")

	return report, nil
}
```

---

## Right to Erasure (Art. 17)

```go
package gdpr

type DataErasureHandler struct {
	logger *logrus.Logger
}

type ErasureResult struct {
	Status      string
	RequestID   string
	Reason      string
	Exceptions  []string
	ErasureDate *time.Time
}

func NewDataErasureHandler(logger *logrus.Logger) *DataErasureHandler {
	return &DataErasureHandler{logger: logger}
}

func (h *DataErasureHandler) ProcessErasureRequest(dataSubjectID, justification string) (*ErasureResult, error) {
	requestID := uuid.New().String()

	// Check exceptions
	exceptions := h.checkErasureExceptions(dataSubjectID)

	if len(exceptions) > 0 {
		h.logger.WithFields(logrus.Fields{
			"event":      "erasure_denied",
			"request_id": requestID,
			"exceptions": exceptions,
		}).Warn("Erasure request denied")

		return &ErasureResult{
			Status:     "Denied",
			Reason:     "Legal obligations require data retention",
			Exceptions: exceptions,
		}, nil
	}

	// Perform erasure
	h.erasePersonalData(dataSubjectID, requestID)

	now := time.Now().UTC()
	h.logger.WithFields(logrus.Fields{
		"event":           "data_erased",
		"request_id":      requestID,
		"data_subject_id": dataSubjectID,
		"timestamp":       now,
	}).Warn("Personal data erased")

	return &ErasureResult{
		Status:      "Completed",
		RequestID:   requestID,
		ErasureDate: &now,
	}, nil
}

func (h *DataErasureHandler) checkErasureExceptions(dataSubjectID string) []string {
	var exceptions []string

	// Check legal obligations
	if h.hasLegalRetentionObligation(dataSubjectID) {
		exceptions = append(exceptions, "Legal retention obligation (7 years)")
	}

	return exceptions
}

func (h *DataErasureHandler) hasLegalRetentionObligation(dataSubjectID string) bool {
	// Check for financial records
	return false
}

func (h *DataErasureHandler) erasePersonalData(dataSubjectID, requestID string) {
	// Erase from all systems
	h.logger.WithFields(logrus.Fields{
		"event":           "erasure_executed",
		"data_subject_id": dataSubjectID,
		"request_id":      requestID,
	}).Warn("Data erasure executed")
}
```

---

## Consent Management

```go
package gdpr

type ConsentManager struct {
	logger *logrus.Logger
}

func NewConsentManager(logger *logrus.Logger) *ConsentManager {
	return &ConsentManager{logger: logger}
}

func (m *ConsentManager) RecordConsent(
	dataSubjectID, purpose string,
	consentGiven bool,
	consentText string,
) (string, error) {
	consentID := uuid.New().String()

	m.logger.WithFields(logrus.Fields{
		"event":           "consent_recorded",
		"consent_id":      consentID,
		"data_subject_id": dataSubjectID,
		"purpose":         purpose,
		"given":           consentGiven,
		"timestamp":       time.Now().UTC(),
	}).Info("Consent recorded")

	return consentID, nil
}

func (m *ConsentManager) WithdrawConsent(dataSubjectID, consentID string) error {
	m.logger.WithFields(logrus.Fields{
		"event":           "consent_withdrawn",
		"data_subject_id": dataSubjectID,
		"consent_id":      consentID,
		"timestamp":       time.Now().UTC(),
	}).Warn("Consent withdrawn")

	return nil
}
```

---

## Success Criteria

- [ ] Access requests processed within 30 days
- [ ] Right to erasure honored
- [ ] Consent management operational
- [ ] Data portability exports available

---

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
