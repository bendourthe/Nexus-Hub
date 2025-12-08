---
template_id: compliance_governance_iso27001_go
template_name: ISO 27001 Implementation - Go
version: 1.0.0
last_updated: 2025-12-05
language: go
category: compliance_governance
phase: compliance_frameworks
phase_number: 1
difficulty: advanced
estimated_time_hours: 8-10
prerequisites:
  - compliance_frameworks/go_soc2_compliance.md
related_templates:
  - risk_management/go_risk_assessment.md
tools:
  - bcrypt (password hashing)
  - logrus (logging)
tags:
  - iso27001
  - isms
  - information-security
  - go
---

# ISO 27001:2022 Implementation - Go

**Information Security Management System for Go applications**

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### ISO 27001:2022 Structure

**4 Themes**: Organizational (37), People (8), Physical (14), Technological (34)
**Total**: 93 controls

---

## Control 5.15: Access Control

```go
package iso27001

import (
	"errors"
	"time"

	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

// PrivilegedAccessManager handles JIT access elevation.
//
// ISO 27001 Control 5.15: Access control
// ISO 27001 Control 5.16: Identity management
type PrivilegedAccessManager struct {
	logger *logrus.Logger
}

const maxElevationHours = 8

type PrivilegeLevel string

const (
	PrivilegeLevelStandard   PrivilegeLevel = "standard"
	PrivilegeLevelElevated   PrivilegeLevel = "elevated"
	PrivilegeLevelAdmin      PrivilegeLevel = "admin"
	PrivilegeLevelSuperAdmin PrivilegeLevel = "superadmin"
)

type PrivilegeRequest struct {
	RequestID      string
	UserID         string
	RequestedLevel PrivilegeLevel
	Justification  string
	ExpiresAt      time.Time
}

// NewPrivilegedAccessManager creates a new access manager.
func NewPrivilegedAccessManager(logger *logrus.Logger) *PrivilegedAccessManager {
	return &PrivilegedAccessManager{logger: logger}
}

// RequestPrivilegeElevation requests temporary privilege elevation.
func (m *PrivilegedAccessManager) RequestPrivilegeElevation(
	userID string,
	requestedLevel PrivilegeLevel,
	justification string,
	durationHours int,
) (string, error) {
	if durationHours > maxElevationHours {
		return "", errors.New("maximum elevation period is 8 hours")
	}

	requestID := uuid.New().String()
	expiresAt := time.Now().UTC().Add(time.Duration(durationHours) * time.Hour)

	m.logger.WithFields(logrus.Fields{
		"event":         "privilege_elevation_request",
		"request_id":    requestID,
		"user_id":       userID,
		"level":         requestedLevel,
		"duration":      durationHours,
		"justification": justification,
		"timestamp":     time.Now().UTC(),
	}).Warn("Privilege elevation requested")

	return requestID, nil
}

// ApproveElevation approves a privilege elevation request.
func (m *PrivilegedAccessManager) ApproveElevation(requestID, approverID string) error {
	m.logger.WithFields(logrus.Fields{
		"event":       "privilege_elevation_approved",
		"request_id":  requestID,
		"approver_id": approverID,
		"timestamp":   time.Now().UTC(),
	}).Warn("Privilege elevation approved")

	return nil
}
```

---

## Control 5.17: Authentication Information

```go
package iso27001

import (
	"errors"
	"regexp"

	"golang.org/x/crypto/bcrypt"
)

// SecureAuthenticationManager handles password policies.
//
// ISO 27001 Control 5.17: Authentication information
type SecureAuthenticationManager struct {
	logger *logrus.Logger
}

const (
	passwordMinLength    = 12
	passwordHistorySize  = 5
	bcryptCost          = 12
)

type ValidationResult struct {
	Compliant  bool
	Violations []string
}

// NewSecureAuthenticationManager creates a new authentication manager.
func NewSecureAuthenticationManager(logger *logrus.Logger) *SecureAuthenticationManager {
	return &SecureAuthenticationManager{logger: logger}
}

// ValidatePasswordStrength validates password complexity.
func (m *SecureAuthenticationManager) ValidatePasswordStrength(password string) ValidationResult {
	var violations []string

	if len(password) < passwordMinLength {
		violations = append(violations, "Password must be at least 12 characters")
	}

	if matched, _ := regexp.MatchString(`[A-Z]`, password); !matched {
		violations = append(violations, "Password must contain uppercase letter")
	}

	if matched, _ := regexp.MatchString(`[a-z]`, password); !matched {
		violations = append(violations, "Password must contain lowercase letter")
	}

	if matched, _ := regexp.MatchString(`[0-9]`, password); !matched {
		violations = append(violations, "Password must contain number")
	}

	if matched, _ := regexp.MatchString(`[!@#$%^&*(),.?":{}|<>]`, password); !matched {
		violations = append(violations, "Password must contain special character")
	}

	compliant := len(violations) == 0

	if !compliant {
		m.logger.WithFields(logrus.Fields{
			"event":      "password_validation_failed",
			"violations": violations,
			"timestamp":  time.Now().UTC(),
		}).Warn("Password validation failed")
	}

	return ValidationResult{
		Compliant:  compliant,
		Violations: violations,
	}
}

// HashPassword hashes password with bcrypt.
func (m *SecureAuthenticationManager) HashPassword(password string) (string, error) {
	hash, err := bcrypt.GenerateFromPassword([]byte(password), bcryptCost)
	if err != nil {
		return "", err
	}
	return string(hash), nil
}

// VerifyPassword verifies password against hash.
func (m *SecureAuthenticationManager) VerifyPassword(password, hash string) error {
	return bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
}
```

---

## Success Criteria

- [ ] Privileged access requires justification and approval
- [ ] Temporary privileges auto-revoked after expiration
- [ ] Password policy enforced (12+ chars, complexity)
- [ ] BCrypt password hashing with cost factor 12
- [ ] Account lockout after 5 failed attempts
- [ ] Security monitoring detects anomalies

---

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
