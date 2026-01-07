---
template_id: compliance_governance_ccpa_go
template_name: CCPA Compliance - Go
version: 1.0.0
last_updated: 2025-12-05
language: go
category: compliance_governance
phase: privacy_protection
phase_number: 4
difficulty: advanced
estimated_time_hours: 4-6
prerequisites:
  - privacy_protection/README.md
related_templates:
  - compliance_frameworks/go_gdpr_compliance.md
tools:
  - logrus (logging)
tags:
  - ccpa
  - privacy
  - california
  - go
---

# CCPA Compliance - Go

**California Consumer Privacy Act for Go applications**

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

**5 Key Consumer Rights**: Right to Know, Right to Delete, Right to Opt-Out, Right to Non-Discrimination, Right to Correct

**Response Deadline**: 45 days

---

## Right to Know (CCPA §1798.100)

```go
package ccpa

import (
	"time"

	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

type CCPADataDisclosureService struct {
	logger *logrus.Logger
}

type DisclosureResponse struct {
	RequestID           string
	ConsumerID          string
	RequestDate         time.Time
	ResponseDeadline    time.Time
	CategoriesCollected []string
	BusinessPurposes    []string
	ThirdParties        []string
	SpecificPieces      map[string]interface{}
	SaleDisclosure      string
	SharingDisclosure   string
}

func NewCCPADataDisclosureService(logger *logrus.Logger) *CCPADataDisclosureService {
	return &CCPADataDisclosureService{logger: logger}
}

// ProcessRightToKnow handles consumer's right to know request.
// Must respond within 45 days (CCPA §1798.100).
func (s *CCPADataDisclosureService) ProcessRightToKnow(consumerID string) (*DisclosureResponse, error) {
	requestID := uuid.New().String()
	deadline := time.Now().UTC().Add(45 * 24 * time.Hour)

	disclosure := &DisclosureResponse{
		RequestID:        requestID,
		ConsumerID:       consumerID,
		RequestDate:      time.Now().UTC(),
		ResponseDeadline: deadline,
		CategoriesCollected: []string{
			"Identifiers (name, email, IP address)",
			"Commercial information (purchase history, browsing history)",
			"Internet or network activity (cookies, logs)",
			"Geolocation data (approximate location from IP)",
			"Inferences (preferences, characteristics)",
		},
		BusinessPurposes: []string{
			"Providing and improving services",
			"Customer support and communication",
			"Security and fraud prevention",
			"Legal compliance",
			"Marketing (with explicit consent)",
		},
		ThirdParties: []string{
			"Service providers: AWS (hosting), Stripe (payments)",
			"Analytics providers: Google Analytics (with anonymization)",
			"Security providers: Cloudflare (DDoS protection)",
		},
		SpecificPieces: map[string]interface{}{
			"profile": map[string]string{
				"name":  "User",
				"email": "user@example.com",
			},
			"account_created": "2023-01-15",
			"last_login":      "2025-12-05",
			"orders":          []interface{}{},
		},
		SaleDisclosure:    "We do not sell personal information",
		SharingDisclosure: "We share data only with service providers under contract",
	}

	s.logger.WithFields(logrus.Fields{
		"event":       "ccpa_right_to_know",
		"request_id":  requestID,
		"consumer_id": consumerID,
		"timestamp":   time.Now().UTC(),
	}).Info("CCPA right to know processed")

	return disclosure, nil
}
```

---

## Right to Delete (CCPA §1798.105)

```go
package ccpa

type CCPADeletionService struct {
	logger *logrus.Logger
}

type DeletionResult struct {
	Status       string
	RequestID    string
	Reason       string
	Exceptions   []string
	DeletionDate *time.Time
}

func NewCCPADeletionService(logger *logrus.Logger) *CCPADeletionService {
	return &CCPADeletionService{logger: logger}
}

// ProcessRightToDelete handles consumer's right to delete request.
// Must respond within 45 days. Check exceptions under §1798.105(d).
func (s *CCPADeletionService) ProcessRightToDelete(
	consumerID string,
	verificationMethod string,
) (*DeletionResult, error) {
	requestID := uuid.New().String()

	// Verify consumer identity (2-factor for sensitive data)
	if !s.verifyConsumerIdentity(consumerID, verificationMethod) {
		s.logger.WithFields(logrus.Fields{
			"event":      "deletion_verification_failed",
			"request_id": requestID,
		}).Warn("Deletion request verification failed")

		return &DeletionResult{
			Status: "Verification Failed",
			Reason: "Unable to verify consumer identity",
		}, nil
	}

	// Check for deletion exceptions (§1798.105(d))
	exceptions := s.checkDeletionExceptions(consumerID)

	if len(exceptions) > 0 {
		s.logger.WithFields(logrus.Fields{
			"event":      "deletion_denied",
			"request_id": requestID,
			"exceptions": exceptions,
		}).Warn("Deletion request denied")

		return &DeletionResult{
			Status:     "Denied",
			Reason:     "Legal obligations require data retention",
			Exceptions: exceptions,
		}, nil
	}

	// Perform deletion
	s.deleteConsumerData(consumerID, requestID)

	now := time.Now().UTC()
	s.logger.WithFields(logrus.Fields{
		"event":       "consumer_data_deleted",
		"request_id":  requestID,
		"consumer_id": consumerID,
		"timestamp":   now,
	}).Warn("Consumer data deleted")

	return &DeletionResult{
		Status:       "Completed",
		RequestID:    requestID,
		DeletionDate: &now,
	}, nil
}

func (s *CCPADeletionService) verifyConsumerIdentity(
	consumerID string,
	method string,
) bool {
	// Implement 2-factor verification for sensitive data
	return true
}

func (s *CCPADeletionService) checkDeletionExceptions(consumerID string) []string {
	var exceptions []string

	// §1798.105(d)(1): Complete transaction
	if s.hasActiveOrders(consumerID) {
		exceptions = append(exceptions, "Active orders pending completion")
	}

	// §1798.105(d)(2): Security incidents, fraud, illegal activity
	if s.hasOngoingSecurityInvestigation(consumerID) {
		exceptions = append(exceptions,
			"Ongoing security incident investigation")
	}

	// §1798.105(d)(5): Internal uses (legal obligations)
	if s.hasRecentFinancialRecords(consumerID) {
		exceptions = append(exceptions,
			"Tax and accounting retention requirement (7 years)")
	}

	// §1798.105(d)(7): Comply with legal obligation
	if s.hasLegalHold(consumerID) {
		exceptions = append(exceptions,
			"Legal hold or pending litigation")
	}

	return exceptions
}

func (s *CCPADeletionService) hasActiveOrders(consumerID string) bool {
	return false // Check database
}

func (s *CCPADeletionService) hasOngoingSecurityInvestigation(consumerID string) bool {
	return false
}

func (s *CCPADeletionService) hasRecentFinancialRecords(consumerID string) bool {
	// Check for financial records within 7-year retention period
	return false
}

func (s *CCPADeletionService) hasLegalHold(consumerID string) bool {
	return false
}

func (s *CCPADeletionService) deleteConsumerData(consumerID, requestID string) {
	// Delete from all systems:
	// - User profile
	// - Preferences
	// - Analytics data
	// - Cookies and tracking data
	//
	// Pseudonymize transaction data (retain for legal compliance)

	s.logger.WithFields(logrus.Fields{
		"event":       "data_deletion_executed",
		"consumer_id": consumerID,
		"request_id":  requestID,
	}).Warn("Data deletion executed")
}
```

---

## Right to Opt-Out of Sale (CCPA §1798.120)

```go
package ccpa

type CCPAOptOutService struct {
	logger *logrus.Logger
}

type OptOutResult struct {
	Status     string
	OptOutID   string
	OptOutDate time.Time
	Message    string
}

func NewCCPAOptOutService(logger *logrus.Logger) *CCPAOptOutService {
	return &CCPAOptOutService{logger: logger}
}

// ProcessOptOut handles consumer opt-out of sale.
// Must honor immediately (no 45-day deadline).
func (s *CCPAOptOutService) ProcessOptOut(consumerID string) (*OptOutResult, error) {
	optOutID := uuid.New().String()

	// Update consumer preferences
	s.updateOptOutPreference(consumerID, true)

	// Notify third parties (if any data sharing for monetary consideration)
	s.notifyThirdParties(consumerID)

	s.logger.WithFields(logrus.Fields{
		"event":       "consumer_opted_out",
		"opt_out_id":  optOutID,
		"consumer_id": consumerID,
		"timestamp":   time.Now().UTC(),
	}).Info("Consumer opted out of sale")

	return &OptOutResult{
		Status:     "Completed",
		OptOutID:   optOutID,
		OptOutDate: time.Now().UTC(),
		Message: "Your opt-out preference has been recorded. " +
			"We will not sell your personal information.",
	}, nil
}

// ProcessOptIn handles consumer opt-in (after previous opt-out).
// Requires affirmative consent.
func (s *CCPAOptOutService) ProcessOptIn(
	consumerID string,
	affirmativeConsentText string,
) (*OptOutResult, error) {
	optInID := uuid.New().String()

	// Record affirmative consent
	s.recordAffirmativeConsent(consumerID, affirmativeConsentText)

	// Update consumer preferences
	s.updateOptOutPreference(consumerID, false)

	s.logger.WithFields(logrus.Fields{
		"event":       "consumer_opted_in",
		"opt_in_id":   optInID,
		"consumer_id": consumerID,
		"timestamp":   time.Now().UTC(),
	}).Info("Consumer opted in to sale")

	return &OptOutResult{
		Status:     "Completed",
		OptOutID:   optInID,
		OptOutDate: time.Now().UTC(),
		Message:    "Your consent has been recorded.",
	}, nil
}

func (s *CCPAOptOutService) updateOptOutPreference(consumerID string, optedOut bool) {
	// Update database
}

func (s *CCPAOptOutService) notifyThirdParties(consumerID string) {
	// Notify any third parties about opt-out status
}

func (s *CCPAOptOutService) recordAffirmativeConsent(
	consumerID string,
	consentText string,
) {
	// Store consent with timestamp for audit
}
```

---

## HTTP Handler

```go
package ccpa

import (
	"encoding/json"
	"net/http"
)

type CCPAHandler struct {
	optOutService *CCPAOptOutService
	logger        *logrus.Logger
}

func NewCCPAHandler(
	optOutService *CCPAOptOutService,
	logger *logrus.Logger,
) *CCPAHandler {
	return &CCPAHandler{
		optOutService: optOutService,
		logger:        logger,
	}
}

// DoNotSellHandler processes "Do Not Sell My Personal Information" requests.
// POST /api/ccpa/do-not-sell
func (h *CCPAHandler) DoNotSellHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var request struct {
		ConsumerID string `json:"consumer_id"`
	}

	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	if request.ConsumerID == "" {
		http.Error(w, "Consumer ID is required", http.StatusBadRequest)
		return
	}

	result, err := h.optOutService.ProcessOptOut(request.ConsumerID)
	if err != nil {
		h.logger.WithError(err).Error("Opt-out processing failed")
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":       result.Status,
		"message":      result.Message,
		"opt_out_date": result.OptOutDate,
	})
}
```

---

## Right to Non-Discrimination (CCPA §1798.125)

```go
package ccpa

type NonDiscriminationEnforcement struct {
	logger *logrus.Logger
}

type ServiceAccessResult struct {
	AccessGranted bool
	ServiceLevel  string
	Pricing       string
	Message       string
}

func NewNonDiscriminationEnforcement(logger *logrus.Logger) *NonDiscriminationEnforcement {
	return &NonDiscriminationEnforcement{logger: logger}
}

// ValidateServiceAccess ensures consumer receives same service level
// regardless of CCPA requests. Cannot deny goods/services, charge
// different prices, or provide different quality of service.
func (e *NonDiscriminationEnforcement) ValidateServiceAccess(
	consumerID string,
	serviceType string,
) (*ServiceAccessResult, error) {
	// Check if consumer has exercised CCPA rights
	ccpaRequests := e.getCCPARequestHistory(consumerID)

	if len(ccpaRequests) > 0 {
		e.logger.WithFields(logrus.Fields{
			"event":         "consumer_with_ccpa_requests_accessing_service",
			"consumer_id":   consumerID,
			"service_type":  serviceType,
			"request_count": len(ccpaRequests),
			"timestamp":     time.Now().UTC(),
		}).Info("Consumer with CCPA requests accessing service")
	}

	// CRITICAL: Must provide same service regardless of CCPA activity
	return &ServiceAccessResult{
		AccessGranted: true,
		ServiceLevel:  "Standard",
		Pricing:       "Standard",
		Message:       "Full access granted",
	}, nil
}

func (e *NonDiscriminationEnforcement) getCCPARequestHistory(consumerID string) []string {
	return []string{}
}
```

---

## Success Criteria

- [ ] Right to Know requests processed within 45 days
- [ ] Right to Delete honored with exception handling (§1798.105(d))
- [ ] "Do Not Sell" link prominently displayed on homepage
- [ ] Opt-out mechanism operational and immediate
- [ ] Non-discrimination enforced (same pricing, service level)
- [ ] 2-factor verification for sensitive data deletion
- [ ] Third-party notification system for opt-outs
- [ ] Audit logs for all CCPA requests

---

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
