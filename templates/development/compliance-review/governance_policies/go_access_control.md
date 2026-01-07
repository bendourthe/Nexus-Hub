---
template_id: compliance_governance_access_control_go
template_name: Access Control - Go
version: 1.0.0
last_updated: 2025-12-05
language: go
category: compliance_governance
phase: governance_policies
phase_number: 3
difficulty: intermediate
estimated_time_hours: 4-6
prerequisites:
  - governance_policies/go_security_policies.md
  - compliance_frameworks/go_soc2_compliance.md
related_templates:
  - compliance_frameworks/go_iso27001_implementation.md
tools:
  - JWT-Go
  - logrus (logging)
tags:
  - access-control
  - rbac
  - least-privilege
  - authentication
  - authorization
  - go
---

# Access Control - Go

**🔒 Pillar 3: Security (Least Privilege)**

Implement role-based access control (RBAC) and least privilege access

[← Back to Governance Policies](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

**Access Control** ensures only authorized users can access resources.

**Framework Requirements**:
- **ISO 27001 Control 5.15**: Access control policy
- **SOC 2 CC6.1**: Logical access controls
- **SOC 2 CC6.2**: Multi-factor authentication

---

## Authentication Implementation

```go
package security

import (
	"errors"
	"time"

	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
	"golang.org/x/crypto/bcrypt"
)

const (
	PasswordMinLength         = 12
	PasswordMaxAgeDays        = 90
	AccountLockoutThreshold   = 5
	LockoutDurationMinutes    = 30
	BcryptCost                = 12
)

type AuthenticationResult struct {
	SessionToken string
	UserID       string
	ExpiresAt    time.Time
	MfaRequired  bool
}

type AuthenticationService struct {
	logger *logrus.Logger
}

func NewAuthenticationService(logger *logrus.Logger) *AuthenticationService {
	return &AuthenticationService{logger: logger}
}

func (s *AuthenticationService) Authenticate(
	username, password, mfaToken string,
) (*AuthenticationResult, error) {

	// user, err := s.userRepository.GetByUsername(username)

	// Simulated user retrieval
	hashedPassword, _ := bcrypt.GenerateFromPassword([]byte("demo_password"), BcryptCost)
	user := map[string]interface{}{
		"user_id":               uuid.New().String(),
		"username":              username,
		"password_hash":         string(hashedPassword),
		"mfa_enabled":           true,
		"failed_login_attempts": 0,
		"account_locked_until":  (*time.Time)(nil),
	}

	// Check account locked
	if s.isAccountLocked(user) {
		s.logger.WithFields(logrus.Fields{
			"event":     "authentication_failed",
			"reason":    "account_locked",
			"user_id":   user["user_id"],
			"username":  username,
			"timestamp": time.Now().UTC(),
		}).Warn("Authentication failed: account locked")

		return nil, errors.New("account locked due to failed login attempts")
	}

	// Verify password
	passwordHash := user["password_hash"].(string)
	if err := bcrypt.CompareHashAndPassword([]byte(passwordHash), []byte(password)); err != nil {
		s.recordFailedLogin(user["user_id"].(string), "invalid_password")
		return nil, errors.New("invalid credentials")
	}

	// Check MFA if enabled
	mfaEnabled := user["mfa_enabled"].(bool)
	if mfaEnabled && mfaToken == "" {
		return &AuthenticationResult{
			UserID:      user["user_id"].(string),
			MfaRequired: true,
		}, nil
	}

	if mfaEnabled && !s.verifyMFAToken(user["user_id"].(string), mfaToken) {
		s.recordFailedLogin(user["user_id"].(string), "invalid_mfa")
		return nil, errors.New("invalid MFA token")
	}

	// Create session
	sessionToken := uuid.New().String()
	expiresAt := time.Now().UTC().Add(8 * time.Hour)

	// Reset failed login attempts
	// s.userRepository.ResetFailedAttempts(user["user_id"].(string))

	s.logger.WithFields(logrus.Fields{
		"event":      "authentication_successful",
		"user_id":    user["user_id"],
		"username":   username,
		"expires_at": expiresAt,
		"timestamp":  time.Now().UTC(),
	}).Info("Authentication successful")

	return &AuthenticationResult{
		SessionToken: sessionToken,
		UserID:       user["user_id"].(string),
		ExpiresAt:    expiresAt,
		MfaRequired:  false,
	}, nil
}

func (s *AuthenticationService) isAccountLocked(user map[string]interface{}) bool {
	failedAttempts := user["failed_login_attempts"].(int)
	if failedAttempts >= AccountLockoutThreshold {
		lockedUntil := user["account_locked_until"].(*time.Time)
		if lockedUntil != nil && time.Now().UTC().Before(*lockedUntil) {
			return true
		}
	}
	return false
}

func (s *AuthenticationService) recordFailedLogin(userID, reason string) {
	// s.userRepository.IncrementFailedAttempts(userID)

	s.logger.WithFields(logrus.Fields{
		"event":     "failed_login_attempt",
		"user_id":   userID,
		"reason":    reason,
		"timestamp": time.Now().UTC(),
	}).Warn("Failed login attempt")

	// Check if should lock account
	// if attempts >= AccountLockoutThreshold {
	//     s.userRepository.LockAccount(userID, LockoutDurationMinutes)
	// }
}

func (s *AuthenticationService) verifyMFAToken(userID, token string) bool {
	// TOTP verification logic
	// Use pquerna/otp or similar library
	return true // Simplified
}

func (s *AuthenticationService) ValidatePassword(password string) bool {
	if len(password) < PasswordMinLength {
		return false
	}

	// Check complexity: uppercase, lowercase, digit, special char
	var hasUpper, hasLower, hasDigit, hasSpecial bool
	for _, ch := range password {
		switch {
		case ch >= 'A' && ch <= 'Z':
			hasUpper = true
		case ch >= 'a' && ch <= 'z':
			hasLower = true
		case ch >= '0' && ch <= '9':
			hasDigit = true
		case !((ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z') || (ch >= '0' && ch <= '9')):
			hasSpecial = true
		}
	}

	return hasUpper && hasLower && hasDigit && hasSpecial
}
```

---

## RBAC Implementation

```go
package security

import (
	"time"

	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

type Role struct {
	RoleID      string
	RoleName    string
	Description string
	Permissions []string
	CreatedDate time.Time
}

type RBACService struct {
	logger *logrus.Logger
}

func NewRBACService(logger *logrus.Logger) *RBACService {
	return &RBACService{logger: logger}
}

func (s *RBACService) CreateRole(
	roleName, description string,
	permissions []string,
) (string, error) {

	roleID := uuid.New().String()

	role := Role{
		RoleID:      roleID,
		RoleName:    roleName,
		Description: description,
		Permissions: permissions,
		CreatedDate: time.Now().UTC(),
	}

	// err := s.roleRepository.Insert(role)

	s.logger.WithFields(logrus.Fields{
		"event":       "role_created",
		"role_id":     roleID,
		"role_name":   roleName,
		"permissions": permissions,
		"timestamp":   time.Now().UTC(),
	}).Info("Role created")

	return roleID, nil
}

func (s *RBACService) AssignRoleToUser(userID, roleID string) error {
	// err := s.userRoleRepository.Insert(userID, roleID)

	s.logger.WithFields(logrus.Fields{
		"event":     "role_assigned",
		"user_id":   userID,
		"role_id":   roleID,
		"timestamp": time.Now().UTC(),
	}).Info("Role assigned")

	return nil
}

func (s *RBACService) GetUserRoles(userID string) ([]string, error) {
	// return s.userRoleRepository.FindByUserID(userID)

	// Simulated
	roles := []string{"developer", "security_reviewer"}
	return roles, nil
}

func (s *RBACService) GetUserPermissions(userID string) ([]string, error) {
	roles, err := s.GetUserRoles(userID)
	if err != nil {
		return nil, err
	}

	permissionSet := make(map[string]bool)

	for _, roleID := range roles {
		// role, err := s.roleRepository.GetByID(roleID)
		// for _, perm := range role.Permissions {
		//     permissionSet[perm] = true
		// }

		// Simulated permissions
		if roleID == "developer" {
			for _, perm := range []string{"code:read", "code:write", "deploy:dev", "logs:read"} {
				permissionSet[perm] = true
			}
		} else if roleID == "security_reviewer" {
			for _, perm := range []string{"audit_logs:read", "security_reports:read", "vulnerabilities:read"} {
				permissionSet[perm] = true
			}
		}
	}

	permissions := make([]string, 0, len(permissionSet))
	for perm := range permissionSet {
		permissions = append(permissions, perm)
	}

	s.logger.WithFields(logrus.Fields{
		"event":            "permissions_retrieved",
		"user_id":          userID,
		"permission_count": len(permissions),
		"timestamp":        time.Now().UTC(),
	}).Info("Permissions retrieved")

	return permissions, nil
}

func (s *RBACService) HasPermission(userID, permission string) (bool, error) {
	permissions, err := s.GetUserPermissions(userID)
	if err != nil {
		return false, err
	}

	hasPermission := false
	for _, perm := range permissions {
		if perm == permission {
			hasPermission = true
			break
		}
	}

	s.logger.WithFields(logrus.Fields{
		"event":      "permission_check",
		"user_id":    userID,
		"permission": permission,
		"granted":    hasPermission,
		"timestamp":  time.Now().UTC(),
	}).Info("Permission check")

	return hasPermission, nil
}

func (s *RBACService) CheckAccess(
	userID, resource, action string,
) (map[string]interface{}, error) {

	requiredPermission := resource + ":" + action
	granted, err := s.HasPermission(userID, requiredPermission)
	if err != nil {
		return nil, err
	}

	if !granted {
		s.logger.WithFields(logrus.Fields{
			"event":     "access_denied",
			"user_id":   userID,
			"resource":  resource,
			"action":    action,
			"timestamp": time.Now().UTC(),
		}).Warn("Access denied")
	} else {
		s.logger.WithFields(logrus.Fields{
			"event":     "access_granted",
			"user_id":   userID,
			"resource":  resource,
			"action":    action,
			"timestamp": time.Now().UTC(),
		}).Info("Access granted")
	}

	return map[string]interface{}{
		"user_id":   userID,
		"resource":  resource,
		"action":    action,
		"granted":   granted,
		"timestamp": time.Now().UTC(),
	}, nil
}
```

---

## Privileged Access Management

```go
package security

import (
	"errors"
	"time"

	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

type PrivilegedAccessRequest struct {
	RequestID      string
	UserID         string
	PrivilegedRole string
	Justification  string
	DurationHours  int
	RequestedAt    time.Time
	Status         string // pending, approved, denied, expired
	ApprovedBy     string
	ApprovedAt     *time.Time
	ExpiresAt      *time.Time
}

type PrivilegedAccessService struct {
	logger *logrus.Logger
}

func NewPrivilegedAccessService(logger *logrus.Logger) *PrivilegedAccessService {
	return &PrivilegedAccessService{logger: logger}
}

func (s *PrivilegedAccessService) RequestPrivilegedAccess(
	userID, privilegedRole, justification string,
	durationHours int,
) (string, error) {

	requestID := uuid.New().String()

	request := PrivilegedAccessRequest{
		RequestID:      requestID,
		UserID:         userID,
		PrivilegedRole: privilegedRole,
		Justification:  justification,
		DurationHours:  durationHours,
		RequestedAt:    time.Now().UTC(),
		Status:         "pending",
	}

	// err := s.privilegedAccessRepository.Insert(request)

	// Notify approvers
	s.notifyApprovers(requestID, privilegedRole)

	s.logger.WithFields(logrus.Fields{
		"event":      "privileged_access_requested",
		"request_id": requestID,
		"user_id":    userID,
		"role":       privilegedRole,
		"timestamp":  time.Now().UTC(),
	}).Info("Privileged access requested")

	return requestID, nil
}

func (s *PrivilegedAccessService) ApprovePrivilegedAccess(
	requestID, approverID string,
) (map[string]interface{}, error) {

	// request, err := s.privilegedAccessRepository.GetByID(requestID)

	request := PrivilegedAccessRequest{
		RequestID:      requestID,
		UserID:         "user123",
		PrivilegedRole: "production_admin",
		DurationHours:  8,
		Status:         "pending",
	}

	if request.Status != "pending" {
		return nil, errors.New("request already processed")
	}

	request.Status = "approved"
	request.ApprovedBy = approverID
	now := time.Now().UTC()
	request.ApprovedAt = &now
	expiresAt := now.Add(time.Duration(request.DurationHours) * time.Hour)
	request.ExpiresAt = &expiresAt

	// err := s.privilegedAccessRepository.Update(request)

	// Grant temporary role
	s.grantTemporaryRole(request.UserID, request.PrivilegedRole, request.DurationHours)

	s.logger.WithFields(logrus.Fields{
		"event":       "privileged_access_approved",
		"request_id":  requestID,
		"approver_id": approverID,
		"timestamp":   time.Now().UTC(),
	}).Info("Privileged access approved")

	return map[string]interface{}{
		"request_id": requestID,
		"status":     "approved",
		"expires_at": expiresAt,
	}, nil
}

func (s *PrivilegedAccessService) grantTemporaryRole(
	userID, role string,
	durationHours int,
) {
	expiresAt := time.Now().UTC().Add(time.Duration(durationHours) * time.Hour)

	// s.temporaryRoleRepository.Insert(userID, role, expiresAt)

	s.logger.WithFields(logrus.Fields{
		"event":      "temporary_role_granted",
		"user_id":    userID,
		"role":       role,
		"expires_at": expiresAt,
		"timestamp":  time.Now().UTC(),
	}).Info("Temporary role granted")
}

func (s *PrivilegedAccessService) notifyApprovers(requestID, privilegedRole string) {
	s.logger.WithFields(logrus.Fields{
		"event":      "approvers_notified",
		"request_id": requestID,
		"role":       privilegedRole,
		"timestamp":  time.Now().UTC(),
	}).Info("Notifying approvers")
	// Email/notification logic
}

func (s *PrivilegedAccessService) RevokeExpiredAccess() error {
	// expiredRoles, err := s.temporaryRoleRepository.FindExpired()

	// for _, role := range expiredRoles {
	//     s.temporaryRoleRepository.Delete(role)
	//     s.logger.WithFields(logrus.Fields{
	//         "event": "expired_role_revoked",
	//         "user_id": role.UserID,
	//         "role": role.Role,
	//     }).Info("Expired role revoked")
	// }

	s.logger.WithFields(logrus.Fields{
		"event":     "expired_access_revocation_completed",
		"timestamp": time.Now().UTC(),
	}).Info("Expired access revocation completed")

	return nil
}
```

---

## Success Criteria

- [ ] Authentication system implemented
- [ ] Multi-factor authentication operational
- [ ] RBAC model deployed
- [ ] Privileged access management functional
- [ ] Access reviews scheduled
- [ ] Audit logging comprehensive

---

[← Back to Governance Policies](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
