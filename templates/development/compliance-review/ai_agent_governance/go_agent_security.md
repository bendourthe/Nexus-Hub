---
template_id: compliance_governance_agent_security_go
template_name: AI Agent Security - Go
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
  - governance_policies/go_access_control.md
related_templates:
  - ai_agent_governance/go_agent_risk_controls.md
tools:
  - Go standard library (crypto)
tags:
  - security
  - least-privilege
  - four-pillars
  - go
---

# AI Agent Security - Go

**🔒 Pillar 3: Security (Least Privilege)**

Secure AI agents with least privilege and input validation

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

**Least Privilege**: AI agents get minimum permissions needed

**Security Controls**:
- Input validation
- Output sanitization
- Access control
- Prompt injection prevention

---

## Implementation

```go
package ai

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"encoding/base64"
	"errors"
	"io"
	"regexp"
	"strings"

	"github.com/sirupsen/logrus"
)

const maxInputLength = 10000

var injectionPattern = regexp.MustCompile(`(?i)(ignore previous|disregard|system:|<script>)`)

type AgentSecurityService struct {
	logger *logrus.Logger
	// permissionRepo PermissionRepository
}

func NewAgentSecurityService(logger *logrus.Logger) *AgentSecurityService {
	return &AgentSecurityService{
		logger: logger,
	}
}

func (s *AgentSecurityService) ValidateInput(agentID, userInput string) (string, error) {
	if strings.TrimSpace(userInput) == "" {
		return "", errors.New("input cannot be empty")
	}

	if len(userInput) > maxInputLength {
		s.logger.WithFields(logrus.Fields{
			"agent_id": agentID,
			"length":   len(userInput),
		}).Warn("Input too long")
		return "", errors.New("input exceeds maximum length")
	}

	if injectionPattern.MatchString(userInput) {
		match := injectionPattern.FindString(userInput)
		s.logger.WithFields(logrus.Fields{
			"agent_id": agentID,
			"pattern":  match,
		}).Warn("Prompt injection detected")
		return "", errors.New("potential prompt injection detected")
	}

	s.logger.WithFields(logrus.Fields{
		"agent_id":     agentID,
		"input_length": len(userInput),
	}).Info("Input validated")

	return userInput, nil
}

func (s *AgentSecurityService) SanitizeOutput(agentID, agentOutput string) string {
	sanitized := agentOutput

	// Remove script tags
	scriptPattern := regexp.MustCompile(`(?i)<script.*?>.*?</script>`)
	sanitized = scriptPattern.ReplaceAllString(sanitized, "")

	// Remove javascript: protocol
	sanitized = strings.ReplaceAll(sanitized, "javascript:", "")

	// Remove event handlers
	eventPattern := regexp.MustCompile(`(?i)on\w+\s*=`)
	sanitized = eventPattern.ReplaceAllString(sanitized, "")

	if sanitized != agentOutput {
		s.logger.WithField("agent_id", agentID).Warn("Output sanitized")
	}

	return sanitized
}

func (s *AgentSecurityService) CheckAgentPermission(agentID, resource, action string) bool {
	requiredPermission := resource + ":" + action

	agentPermissions := s.getAgentPermissions(agentID)
	hasPermission := contains(agentPermissions, requiredPermission)

	if !hasPermission {
		s.logger.WithFields(logrus.Fields{
			"agent_id": agentID,
			"resource": resource,
			"action":   action,
		}).Warn("Permission denied")
	}

	return hasPermission
}

func (s *AgentSecurityService) getAgentPermissions(agentID string) []string {
	// In production, query from database or policy service
	return []string{
		"data:read",
		"api:call",
		"database:query",
	}
}

func (s *AgentSecurityService) ValidateAPIToken(agentID, token string) bool {
	if strings.TrimSpace(token) == "" {
		s.logger.WithField("agent_id", agentID).Warn("Empty token provided")
		return false
	}

	// In production, validate JWT or API key
	isValid := len(token) >= 32 // Simulated validation

	if !isValid {
		s.logger.WithField("agent_id", agentID).Warn("Invalid API token")
	}

	return isValid
}

func (s *AgentSecurityService) EncryptSensitiveData(agentID, sensitiveData, key string) (string, error) {
	// In production, use proper key management (e.g., AWS KMS, HashiCorp Vault)
	keyBytes := []byte(key)
	if len(keyBytes) != 32 {
		return "", errors.New("key must be 32 bytes for AES-256")
	}

	block, err := aes.NewCipher(keyBytes)
	if err != nil {
		return "", err
	}

	plaintext := []byte(sensitiveData)
	ciphertext := make([]byte, aes.BlockSize+len(plaintext))
	iv := ciphertext[:aes.BlockSize]

	if _, err := io.ReadFull(rand.Reader, iv); err != nil {
		return "", err
	}

	stream := cipher.NewCFBEncrypter(block, iv)
	stream.XORKeyStream(ciphertext[aes.BlockSize:], plaintext)

	encrypted := base64.StdEncoding.EncodeToString(ciphertext)

	s.logger.WithField("agent_id", agentID).Info("Sensitive data encrypted")

	return encrypted, nil
}

func (s *AgentSecurityService) DecryptSensitiveData(agentID, encryptedData, key string) (string, error) {
	keyBytes := []byte(key)
	if len(keyBytes) != 32 {
		return "", errors.New("key must be 32 bytes for AES-256")
	}

	ciphertext, err := base64.StdEncoding.DecodeString(encryptedData)
	if err != nil {
		return "", err
	}

	block, err := aes.NewCipher(keyBytes)
	if err != nil {
		return "", err
	}

	if len(ciphertext) < aes.BlockSize {
		return "", errors.New("ciphertext too short")
	}

	iv := ciphertext[:aes.BlockSize]
	ciphertext = ciphertext[aes.BlockSize:]

	stream := cipher.NewCFBDecrypter(block, iv)
	stream.XORKeyStream(ciphertext, ciphertext)

	s.logger.WithField("agent_id", agentID).Info("Sensitive data decrypted")

	return string(ciphertext), nil
}

func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}
```

---

## Success Criteria

- [ ] Input validation implemented
- [ ] Output sanitization operational
- [ ] Prompt injection prevention active
- [ ] Least privilege enforced

---

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
