---
template_id: compliance_governance_soc2_compliance_go
template_name: SOC 2 Type II Compliance - Go
version: 1.0.0
last_updated: 2025-12-05
language: go
category: compliance_governance
phase: compliance_frameworks
phase_number: 1
difficulty: advanced
estimated_time_hours: 6-8
prerequisites:
  - compliance_frameworks/README.md
related_templates:
  - compliance_frameworks/go_iso27001_implementation.md
tools:
  - gin (web framework)
  - logrus (logging)
  - otp (TOTP)
tags:
  - soc2
  - trust-service-criteria
  - compliance
  - go
  - golang
---

# SOC 2 Type II Compliance - Go

**Implement Trust Service Criteria for Go applications**

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### Trust Service Criteria

1. **Security (CC)** - Common Criteria (required)
2. **Availability** - System uptime/performance
3. **Confidentiality** - Sensitive data protection

---

## CC6.1: Logical Access Controls

```go
package compliance

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"encoding/base64"
	"fmt"
	"io"
	"time"

	"github.com/google/uuid"
	"github.com/pquerna/otp"
	"github.com/pquerna/otp/totp"
	log "github.com/sirupsen/logrus"
)

// MFAManager handles multi-factor authentication.
// SOC 2 Control: CC6.1 - Multi-factor authentication
type MFAManager struct {
	logger *log.Logger
}

// NewMFAManager creates a new MFA manager.
func NewMFAManager(logger *log.Logger) *MFAManager {
	return &MFAManager{logger: logger}
}

// EnrollmentResponse contains MFA enrollment data.
type EnrollmentResponse struct {
	Secret          string
	QRCodeURI       string
	EncryptedSecret string
}

// EnrollUser generates MFA secret for user enrollment.
func (m *MFAManager) EnrollUser(userID, userEmail string) (*EnrollmentResponse, error) {
	key, err := totp.Generate(totp.GenerateOpts{
		Issuer:      "YourApp",
		AccountName: userEmail,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to generate TOTP key: %w", err)
	}

	secret := key.Secret()

	// Encrypt secret for storage
	encryptedSecret, err := m.encryptSecret(secret)
	if err != nil {
		return nil, fmt.Errorf("failed to encrypt secret: %w", err)
	}

	m.logger.WithFields(log.Fields{
		"event":     "mfa_enrollment",
		"userId":    userID,
		"timestamp": time.Now().UTC(),
	}).Info("MFA enrollment initiated")

	return &EnrollmentResponse{
		Secret:          secret,
		QRCodeURI:       key.URL(),
		EncryptedSecret: encryptedSecret,
	}, nil
}

// VerificationResult contains MFA verification result.
type VerificationResult struct {
	IsValid bool
	Message string
}

// VerifyToken verifies MFA token during login.
func (m *MFAManager) VerifyToken(userID, token string) *VerificationResult {
	// Retrieve encrypted secret from database
	encryptedSecret := m.getUserMFASecret(userID)

	if encryptedSecret == "" {
		m.logger.WithFields(log.Fields{
			"event":  "mfa_verification_failed",
			"userId": userID,
			"reason": "mfa_not_enabled",
		}).Warn("MFA verification failed")

		return &VerificationResult{
			IsValid: false,
			Message: "MFA not enabled",
		}
	}

	secret, err := m.decryptSecret(encryptedSecret)
	if err != nil {
		return &VerificationResult{
			IsValid: false,
			Message: "Decryption failed",
		}
	}

	isValid := totp.Validate(token, secret)

	m.logger.WithFields(log.Fields{
		"event":     "mfa_verification_attempt",
		"userId":    userID,
		"success":   isValid,
		"timestamp": time.Now().UTC(),
	}).Info("MFA verification attempt")

	if !isValid {
		m.recordFailedAttempt(userID)
	}

	return &VerificationResult{
		IsValid: isValid,
		Message: map[bool]string{true: "Verified", false: "Invalid token"}[isValid],
	}
}

func (m *MFAManager) encryptSecret(secret string) (string, error) {
	key := make([]byte, 32) // AES-256
	if _, err := io.ReadFull(rand.Reader, key); err != nil {
		return "", err
	}

	block, err := aes.NewCipher(key)
	if err != nil {
		return "", err
	}

	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return "", err
	}

	nonce := make([]byte, gcm.NonceSize())
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return "", err
	}

	ciphertext := gcm.Seal(nonce, nonce, []byte(secret), nil)
	return base64.StdEncoding.EncodeToString(ciphertext), nil
}

func (m *MFAManager) decryptSecret(encryptedSecret string) (string, error) {
	// Implementation: AES-256-GCM decryption
	return encryptedSecret, nil // Simplified
}

func (m *MFAManager) recordFailedAttempt(userID string) {
	recentAttempts := m.countRecentFailedAttempts(userID, 15)

	if recentAttempts >= 5 {
		m.logger.WithFields(log.Fields{
			"event":        "mfa_brute_force",
			"userId":       userID,
			"attemptCount": recentAttempts,
		}).Warn("Potential MFA brute force attack")

		m.lockAccount(userID, 30)
	}
}

func (m *MFAManager) countRecentFailedAttempts(userID string, minutes int) int {
	// Implementation: Query database
	return 0
}

func (m *MFAManager) lockAccount(userID string, minutes int) {
	m.logger.WithFields(log.Fields{
		"event":           "account_locked",
		"userId":          userID,
		"durationMinutes": minutes,
	}).Warn("Account locked")
}

func (m *MFAManager) getUserMFASecret(userID string) string {
	// Implementation: Retrieve from database
	return ""
}
```

## CC6.7: Encryption of Confidential Data

```go
package compliance

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"encoding/base64"
	"fmt"
	"io"
	"time"

	log "github.com/sirupsen/logrus"
)

// DataEncryptionManager handles data encryption.
// SOC 2 Control: CC6.7 - Data encryption at rest
// Standard: AES-256-GCM
type DataEncryptionManager struct {
	logger *log.Logger
}

// NewDataEncryptionManager creates a new encryption manager.
func NewDataEncryptionManager(logger *log.Logger) *DataEncryptionManager {
	return &DataEncryptionManager{logger: logger}
}

// EncryptedData contains encrypted data and metadata.
type EncryptedData struct {
	Ciphertext string
	Nonce      string
	Algorithm  string
	Context    map[string]string
}

// EncryptData encrypts sensitive data at rest.
func (d *DataEncryptionManager) EncryptData(plaintext string, context map[string]string) (*EncryptedData, error) {
	key := make([]byte, 32) // AES-256
	if _, err := io.ReadFull(rand.Reader, key); err != nil {
		return nil, fmt.Errorf("failed to generate key: %w", err)
	}

	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, fmt.Errorf("failed to create cipher: %w", err)
	}

	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, fmt.Errorf("failed to create GCM: %w", err)
	}

	nonce := make([]byte, gcm.NonceSize())
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return nil, fmt.Errorf("failed to generate nonce: %w", err)
	}

	ciphertext := gcm.Seal(nil, nonce, []byte(plaintext), nil)

	d.logger.WithFields(log.Fields{
		"event":     "data_encrypted",
		"algorithm": "AES-256-GCM",
		"context":   context,
		"timestamp": time.Now().UTC(),
	}).Info("Data encrypted")

	return &EncryptedData{
		Ciphertext: base64.StdEncoding.EncodeToString(ciphertext),
		Nonce:      base64.StdEncoding.EncodeToString(nonce),
		Algorithm:  "AES-256-GCM",
		Context:    context,
	}, nil
}

// DecryptData decrypts sensitive data.
func (d *DataEncryptionManager) DecryptData(encryptedData *EncryptedData) (string, error) {
	// Retrieve key from key management service
	key := d.retrieveKey()

	block, err := aes.NewCipher(key)
	if err != nil {
		return "", fmt.Errorf("failed to create cipher: %w", err)
	}

	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return "", fmt.Errorf("failed to create GCM: %w", err)
	}

	nonce, err := base64.StdEncoding.DecodeString(encryptedData.Nonce)
	if err != nil {
		return "", fmt.Errorf("failed to decode nonce: %w", err)
	}

	ciphertext, err := base64.StdEncoding.DecodeString(encryptedData.Ciphertext)
	if err != nil {
		return "", fmt.Errorf("failed to decode ciphertext: %w", err)
	}

	plaintext, err := gcm.Open(nil, nonce, ciphertext, nil)
	if err != nil {
		return "", fmt.Errorf("failed to decrypt: %w", err)
	}

	d.logger.WithFields(log.Fields{
		"event":     "data_decrypted",
		"context":   encryptedData.Context,
		"timestamp": time.Now().UTC(),
	}).Info("Data decrypted")

	return string(plaintext), nil
}

func (d *DataEncryptionManager) retrieveKey() []byte {
	// Implementation: Retrieve from key management service
	return make([]byte, 32)
}
```

## CC7.2: System Monitoring

```go
package compliance

import (
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	log "github.com/sirupsen/logrus"
)

// SecurityMonitoring handles security event monitoring.
// SOC 2 Control: CC7.2 - Security event logging
type SecurityMonitoring struct {
	logger                      *log.Logger
	securityEventsCounter       *prometheus.CounterVec
	authenticationAttemptsCounter *prometheus.CounterVec
}

// NewSecurityMonitoring creates a new security monitoring instance.
func NewSecurityMonitoring(logger *log.Logger) *SecurityMonitoring {
	return &SecurityMonitoring{
		logger: logger,
		securityEventsCounter: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "security_events_total",
				Help: "Total security events by type",
			},
			[]string{"event_type", "severity"},
		),
		authenticationAttemptsCounter: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "authentication_attempts_total",
				Help: "Total authentication attempts",
			},
			[]string{"result"},
		),
	}
}

// LogSecurityEvent logs a security event with structured data.
func (s *SecurityMonitoring) LogSecurityEvent(eventType, severity string, details map[string]interface{}) {
	event := make(map[string]interface{})
	for k, v := range details {
		event[k] = v
	}
	event["event"] = eventType
	event["severity"] = severity
	event["timestamp"] = time.Now().UTC()

	s.logger.WithFields(log.Fields(event)).Info("Security event")

	s.securityEventsCounter.WithLabelValues(eventType, severity).Inc()

	if severity == "critical" {
		s.sendSecurityAlert(event)
	}
}

// LogAuthenticationAttempt logs an authentication attempt.
func (s *SecurityMonitoring) LogAuthenticationAttempt(userID, result string, details map[string]interface{}) {
	event := make(map[string]interface{})
	for k, v := range details {
		event[k] = v
	}
	event["event"] = "authentication_attempt"
	event["userId"] = userID
	event["result"] = result
	event["timestamp"] = time.Now().UTC()

	s.logger.WithFields(log.Fields(event)).Info("Authentication attempt")

	s.authenticationAttemptsCounter.WithLabelValues(result).Inc()

	if result == "failure" {
		s.checkForBruteForce(userID)
	}
}

func (s *SecurityMonitoring) checkForBruteForce(userID string) {
	recentFailures := s.countRecentFailures(userID, 15)

	if recentFailures >= 5 {
		s.LogSecurityEvent("brute_force_detected", "critical", map[string]interface{}{
			"userId":       userID,
			"failureCount": recentFailures,
		})
		s.lockAccount(userID)
	}
}

func (s *SecurityMonitoring) sendSecurityAlert(event map[string]interface{}) {
	s.logger.WithFields(log.Fields(event)).Error("CRITICAL SECURITY ALERT")
	// Implementation: Integrate with PagerDuty, Slack, etc.
}

func (s *SecurityMonitoring) countRecentFailures(userID string, minutes int) int {
	// Implementation: Query database
	return 0
}

func (s *SecurityMonitoring) lockAccount(userID string) {
	s.logger.WithFields(log.Fields{
		"event":  "account_locked",
		"userId": userID,
	}).Warn("Account locked due to brute force")
}
```

---

## Success Criteria

- [ ] Multi-factor authentication enforced
- [ ] All sensitive data encrypted at rest (AES-256-GCM)
- [ ] HTTPS enforced with TLS 1.3
- [ ] Security events logged
- [ ] Failed authentication monitored

---

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
