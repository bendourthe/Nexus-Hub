---
template_id: compliance_governance_pci_dss_go
template_name: PCI-DSS v4.0 Compliance - Go
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
  - governance_policies/go_access_control.md
tools:
  - crypto (standard library)
  - pquerna/otp (TOTP)
tags:
  - pci-dss
  - payment-security
  - cardholder-data
  - go
---

# PCI-DSS v4.0 Compliance - Go

**Payment Card Industry Data Security Standard for Go applications**

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### PCI-DSS v4.0 Requirements

**12 Core Requirements** for protecting payment card data in Go applications.

---

## Requirement 3: Protect Stored Account Data

```go
package pci

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

// CardDataProtectionManager handles PAN encryption and tokenization.
//
// PCI-DSS Requirement 3: Protect stored account data
// PCI-DSS Requirement 3.3: Mask PAN when displayed
// PCI-DSS Requirement 3.4: Render PAN unreadable
type CardDataProtectionManager struct {
	masterKey []byte
	logger    *logrus.Logger
}

// EncryptedData contains encrypted PAN components.
type EncryptedData struct {
	Ciphertext string `json:"ciphertext"`
	Nonce      string `json:"nonce"`
	Algorithm  string `json:"algorithm"`
}

// NewCardDataProtectionManager creates a new manager instance.
func NewCardDataProtectionManager(masterKey []byte, logger *logrus.Logger) (*CardDataProtectionManager, error) {
	if len(masterKey) != 32 {
		return nil, errors.New("master key must be 256 bits (32 bytes)")
	}

	return &CardDataProtectionManager{
		masterKey: masterKey,
		logger:    logger,
	}, nil
}

// TokenizePAN tokenizes Primary Account Number instead of storing.
//
// PCI-DSS Requirement 3.2.1: Do not store sensitive authentication data
func (m *CardDataProtectionManager) TokenizePAN(pan string) (string, error) {
	if !m.validatePAN(pan) {
		return "", errors.New("invalid PAN format")
	}

	// Generate cryptographically secure token
	token := fmt.Sprintf("TKN%s", strings.ReplaceAll(uuid.New().String(), "-", "")[:16])
	token = strings.ToUpper(token)

	// Store token-to-PAN mapping in secure vault (HSM/external tokenization service)
	m.storeTokenMapping(token, pan)

	m.logger.WithFields(logrus.Fields{
		"event":        "pan_tokenized",
		"token_prefix": token[:6],
		"timestamp":    time.Now().UTC(),
	}).Info("PAN tokenized")

	return token, nil
}

// MaskPAN masks PAN for display.
//
// PCI-DSS Requirement 3.3: Mask PAN when displayed
// Only first 6 and last 4 digits shown
func (m *CardDataProtectionManager) MaskPAN(pan string) (string, error) {
	if len(pan) < 13 {
		return "", errors.New("PAN too short to mask")
	}

	// Show first 6 (BIN) and last 4 digits
	masked := pan[:6] + strings.Repeat("*", len(pan)-10) + pan[len(pan)-4:]

	m.logger.WithFields(logrus.Fields{
		"event":      "pan_masked",
		"masked_pan": masked,
		"timestamp":  time.Now().UTC(),
	}).Info("PAN masked for display")

	return masked, nil
}

// EncryptPAN encrypts PAN with AES-256-GCM.
//
// PCI-DSS Requirement 3.4.1: Use strong cryptography
// PCI-DSS Requirement 3.5.1: Key strength minimum 256-bit
func (m *CardDataProtectionManager) EncryptPAN(pan string) (*EncryptedData, error) {
	if !m.validatePAN(pan) {
		return nil, errors.New("invalid PAN format")
	}

	block, err := aes.NewCipher(m.masterKey)
	if err != nil {
		return nil, fmt.Errorf("failed to create cipher: %w", err)
	}

	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, fmt.Errorf("failed to create GCM: %w", err)
	}

	// Generate random nonce
	nonce := make([]byte, gcm.NonceSize())
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return nil, fmt.Errorf("failed to generate nonce: %w", err)
	}

	// Encrypt PAN
	ciphertext := gcm.Seal(nil, nonce, []byte(pan), nil)

	m.logger.WithFields(logrus.Fields{
		"event":     "pan_encrypted",
		"algorithm": "AES-256-GCM",
		"timestamp": time.Now().UTC(),
	}).Info("PAN encrypted")

	return &EncryptedData{
		Ciphertext: base64.StdEncoding.EncodeToString(ciphertext),
		Nonce:      base64.StdEncoding.EncodeToString(nonce),
		Algorithm:  "AES-256-GCM",
	}, nil
}

// DecryptPAN decrypts PAN.
func (m *CardDataProtectionManager) DecryptPAN(encrypted *EncryptedData) (string, error) {
	block, err := aes.NewCipher(m.masterKey)
	if err != nil {
		return "", fmt.Errorf("failed to create cipher: %w", err)
	}

	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return "", fmt.Errorf("failed to create GCM: %w", err)
	}

	ciphertext, err := base64.StdEncoding.DecodeString(encrypted.Ciphertext)
	if err != nil {
		return "", fmt.Errorf("failed to decode ciphertext: %w", err)
	}

	nonce, err := base64.StdEncoding.DecodeString(encrypted.Nonce)
	if err != nil {
		return "", fmt.Errorf("failed to decode nonce: %w", err)
	}

	plaintext, err := gcm.Open(nil, nonce, ciphertext, nil)
	if err != nil {
		m.logger.WithFields(logrus.Fields{
			"event":     "decryption_failed",
			"error":     err.Error(),
			"timestamp": time.Now().UTC(),
		}).Error("PAN decryption failed")
		return "", fmt.Errorf("decryption failed: %w", err)
	}

	m.logger.WithFields(logrus.Fields{
		"event":     "pan_decrypted",
		"timestamp": time.Now().UTC(),
	}).Info("PAN decrypted")

	return string(plaintext), nil
}

// HashPANForSearch creates one-way hash of PAN for searching.
//
// PCI-DSS Requirement 3.4.1: Render PAN unreadable
func (m *CardDataProtectionManager) HashPANForSearch(pan string) string {
	hash := sha256.Sum256([]byte(pan))

	m.logger.WithFields(logrus.Fields{
		"event":     "pan_hashed",
		"algorithm": "SHA-256",
		"timestamp": time.Now().UTC(),
	}).Info("PAN hashed")

	return hex.EncodeToString(hash[:])
}

// validatePAN validates PAN using Luhn algorithm.
func (m *CardDataProtectionManager) validatePAN(pan string) bool {
	// Remove spaces and hyphens
	re := regexp.MustCompile(`[\s-]`)
	pan = re.ReplaceAllString(pan, "")

	// Check length (13-19 digits)
	if len(pan) < 13 || len(pan) > 19 {
		return false
	}

	// Check all numeric
	if _, err := strconv.Atoi(pan); err != nil {
		return false
	}

	// Luhn algorithm
	sum := 0
	alternate := false

	for i := len(pan) - 1; i >= 0; i-- {
		digit, _ := strconv.Atoi(string(pan[i]))

		if alternate {
			digit *= 2
			if digit > 9 {
				digit -= 9
			}
		}

		sum += digit
		alternate = !alternate
	}

	return sum%10 == 0
}

func (m *CardDataProtectionManager) storeTokenMapping(token, pan string) {
	// This would typically interface with a secure token vault
	// For demonstration purposes only
}
```

---

## Requirement 8: Multi-Factor Authentication

```go
package pci

import (
	"errors"
	"regexp"
	"time"

	"github.com/pquerna/otp/totp"
	"github.com/sirupsen/logrus"
)

// PCIAuthenticationManager handles authentication and password policies.
//
// PCI-DSS Requirement 8: Identify users and authenticate access
// PCI-DSS Requirement 8.3.6: Multi-factor authentication (MFA)
type PCIAuthenticationManager struct {
	logger *logrus.Logger
}

const (
	passwordMinLength      = 12
	passwordMaxAgeDays     = 90
	lockoutThreshold       = 6  // PCI-DSS 8.3.4
	lockoutDurationMinutes = 30
)

// MFAEnrollmentResponse contains MFA enrollment data.
type MFAEnrollmentResponse struct {
	Secret           string `json:"secret"`
	ProvisioningURI  string `json:"provisioning_uri"`
}

// NewPCIAuthenticationManager creates a new authentication manager.
func NewPCIAuthenticationManager(logger *logrus.Logger) *PCIAuthenticationManager {
	return &PCIAuthenticationManager{logger: logger}
}

// GenerateMFASecret generates MFA secret for user.
//
// PCI-DSS Requirement 8.3.6: MFA for admin access to CDE
func (m *PCIAuthenticationManager) GenerateMFASecret(userID, userEmail string) (*MFAEnrollmentResponse, error) {
	key, err := totp.Generate(totp.GenerateOpts{
		Issuer:      "PCI-DSS Application",
		AccountName: userEmail,
	})
	if err != nil {
		return nil, err
	}

	m.logger.WithFields(logrus.Fields{
		"event":     "mfa_secret_generated",
		"user_id":   userID,
		"timestamp": time.Now().UTC(),
	}).Info("MFA secret generated")

	return &MFAEnrollmentResponse{
		Secret:          key.Secret(),
		ProvisioningURI: key.URL(),
	}, nil
}

// VerifyMFAToken verifies MFA token.
func (m *PCIAuthenticationManager) VerifyMFAToken(secret, token string) bool {
	valid := totp.Validate(token, secret)

	m.logger.WithFields(logrus.Fields{
		"event":     "mfa_token_verified",
		"valid":     valid,
		"timestamp": time.Now().UTC(),
	}).Info("MFA token verified")

	return valid
}

// ValidatePasswordComplexity validates password complexity.
//
// PCI-DSS Requirement 8.3.6: Password complexity
// - Minimum 12 characters
// - Numeric and alphabetic characters
func (m *PCIAuthenticationManager) ValidatePasswordComplexity(password string) (bool, []string) {
	var violations []string

	if len(password) < passwordMinLength {
		violations = append(violations, fmt.Sprintf("Password must be at least %d characters", passwordMinLength))
	}

	if matched, _ := regexp.MatchString(`\d`, password); !matched {
		violations = append(violations, "Password must contain at least one number")
	}

	if matched, _ := regexp.MatchString(`[a-zA-Z]`, password); !matched {
		violations = append(violations, "Password must contain at least one letter")
	}

	if matched, _ := regexp.MatchString(`[A-Z]`, password); !matched {
		violations = append(violations, "Password must contain at least one uppercase letter")
	}

	if matched, _ := regexp.MatchString(`[a-z]`, password); !matched {
		violations = append(violations, "Password must contain at least one lowercase letter")
	}

	isValid := len(violations) == 0

	if !isValid {
		m.logger.WithFields(logrus.Fields{
			"event":      "password_validation_failed",
			"violations": violations,
			"timestamp":  time.Now().UTC(),
		}).Warn("Password complexity validation failed")
	}

	return isValid, violations
}

// CheckPasswordExpiry checks if password has expired.
//
// PCI-DSS Requirement 8.3.9: Password change every 90 days
func (m *PCIAuthenticationManager) CheckPasswordExpiry(userID string, lastChanged time.Time) bool {
	ageDays := int(time.Since(lastChanged).Hours() / 24)
	expired := ageDays >= passwordMaxAgeDays

	if expired {
		m.logger.WithFields(logrus.Fields{
			"event":       "password_expired",
			"user_id":     userID,
			"age_days":    ageDays,
			"max_age_days": passwordMaxAgeDays,
			"timestamp":   time.Now().UTC(),
		}).Warn("Password expired")
	}

	return expired
}
```

---

## Success Criteria

- [ ] PAN never stored in clear text
- [ ] PAN masked when displayed (first 6, last 4 only)
- [ ] AES-256-GCM encryption for stored PAN
- [ ] TLS 1.2+ for data transmission
- [ ] MFA enforced for CDE access
- [ ] Password complexity enforced (12+ chars)
- [ ] Passwords expire after 90 days
- [ ] Account lockout after 6 failed attempts
- [ ] All CDE access logged with audit trail

---

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
