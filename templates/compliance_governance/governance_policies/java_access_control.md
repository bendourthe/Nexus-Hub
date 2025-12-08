---
template_id: compliance_governance_access_control_java
template_name: Access Control - Java
version: 1.0.0
last_updated: 2025-12-05
language: java
category: compliance_governance
phase: governance_policies
phase_number: 3
difficulty: intermediate
estimated_time_hours: 4-6
prerequisites:
  - governance_policies/java_security_policies.md
  - compliance_frameworks/java_soc2_compliance.md
related_templates:
  - compliance_frameworks/java_iso27001_implementation.md
tools:
  - Spring Security
  - JWT (JSON Web Tokens)
tags:
  - access-control
  - rbac
  - least-privilege
  - authentication
  - authorization
  - java
---

# Access Control - Java

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

```java
package com.organization.security;

import org.springframework.stereotype.Service;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;

@Service
public class AuthenticationService {

    private static final Logger logger = LoggerFactory.getLogger(AuthenticationService.class);
    private final BCryptPasswordEncoder passwordEncoder = new BCryptPasswordEncoder(12);

    // Password policy
    private static final int PASSWORD_MIN_LENGTH = 12;
    private static final int PASSWORD_MAX_AGE_DAYS = 90;
    private static final int ACCOUNT_LOCKOUT_THRESHOLD = 5;
    private static final int LOCKOUT_DURATION_MINUTES = 30;

    public static class AuthenticationResult {
        private String sessionToken;
        private String userId;
        private Instant expiresAt;
        private boolean mfaRequired;

        // Getters and setters
        public String getSessionToken() { return sessionToken; }
        public void setSessionToken(String sessionToken) { this.sessionToken = sessionToken; }

        public String getUserId() { return userId; }
        public void setUserId(String userId) { this.userId = userId; }

        public Instant getExpiresAt() { return expiresAt; }
        public void setExpiresAt(Instant expiresAt) { this.expiresAt = expiresAt; }

        public boolean isMfaRequired() { return mfaRequired; }
        public void setMfaRequired(boolean mfaRequired) { this.mfaRequired = mfaRequired; }
    }

    public AuthenticationResult authenticate(
            String username,
            String password,
            String mfaToken) {

        // User user = userRepository.findByUsername(username).orElseThrow();

        // Simulated user retrieval
        Map<String, Object> user = new HashMap<>();
        user.put("user_id", UUID.randomUUID().toString());
        user.put("username", username);
        user.put("password_hash", passwordEncoder.encode("demo_password"));
        user.put("mfa_enabled", true);
        user.put("failed_login_attempts", 0);
        user.put("account_locked_until", null);

        // Check account locked
        if (isAccountLocked(user)) {
            logger.warn("Authentication failed: account locked - user_id={}, username={}",
                    user.get("user_id"), username);
            throw new SecurityException("Account locked due to failed login attempts");
        }

        // Verify password
        String passwordHash = (String) user.get("password_hash");
        if (!passwordEncoder.matches(password, passwordHash)) {
            recordFailedLogin((String) user.get("user_id"), "invalid_password");
            throw new SecurityException("Invalid credentials");
        }

        // Check MFA if enabled
        boolean mfaEnabled = (Boolean) user.get("mfa_enabled");
        if (mfaEnabled && (mfaToken == null || mfaToken.isEmpty())) {
            AuthenticationResult result = new AuthenticationResult();
            result.setUserId((String) user.get("user_id"));
            result.setMfaRequired(true);
            return result;
        }

        if (mfaEnabled && !verifyMFAToken((String) user.get("user_id"), mfaToken)) {
            recordFailedLogin((String) user.get("user_id"), "invalid_mfa");
            throw new SecurityException("Invalid MFA token");
        }

        // Create session
        String sessionToken = generateSessionToken();
        Instant expiresAt = Instant.now().plus(8, ChronoUnit.HOURS);

        // Reset failed login attempts
        // userRepository.resetFailedAttempts(user.get("user_id"));

        logger.info("Authentication successful: user_id={}, username={}",
                user.get("user_id"), username);

        AuthenticationResult result = new AuthenticationResult();
        result.setSessionToken(sessionToken);
        result.setUserId((String) user.get("user_id"));
        result.setExpiresAt(expiresAt);
        result.setMfaRequired(false);
        return result;
    }

    private boolean isAccountLocked(Map<String, Object> user) {
        Integer failedAttempts = (Integer) user.get("failed_login_attempts");
        if (failedAttempts != null && failedAttempts >= ACCOUNT_LOCKOUT_THRESHOLD) {
            Instant lockedUntil = (Instant) user.get("account_locked_until");
            if (lockedUntil != null && Instant.now().isBefore(lockedUntil)) {
                return true;
            }
        }
        return false;
    }

    private void recordFailedLogin(String userId, String reason) {
        // Increment failed attempt counter
        // userRepository.incrementFailedAttempts(userId);

        logger.warn("Failed login attempt: user_id={}, reason={}", userId, reason);

        // Check if should lock account
        // if (attempts >= ACCOUNT_LOCKOUT_THRESHOLD) {
        //     userRepository.lockAccount(userId, LOCKOUT_DURATION_MINUTES);
        // }
    }

    private boolean verifyMFAToken(String userId, String token) {
        // TOTP verification logic
        // Use Google Authenticator compatible library
        return true; // Simplified
    }

    private String generateSessionToken() {
        return UUID.randomUUID().toString();
    }

    public boolean validatePassword(String password) {
        if (password.length() < PASSWORD_MIN_LENGTH) {
            return false;
        }

        // Check complexity: uppercase, lowercase, digit, special char
        boolean hasUpper = password.chars().anyMatch(Character::isUpperCase);
        boolean hasLower = password.chars().anyMatch(Character::isLowerCase);
        boolean hasDigit = password.chars().anyMatch(Character::isDigit);
        boolean hasSpecial = password.chars().anyMatch(ch -> !Character.isLetterOrDigit(ch));

        return hasUpper && hasLower && hasDigit && hasSpecial;
    }
}
```

---

## RBAC Implementation

```java
package com.organization.security;

import org.springframework.stereotype.Service;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Instant;
import java.util.*;

@Service
public class RBACService {

    private static final Logger logger = LoggerFactory.getLogger(RBACService.class);

    public static class Role {
        private String roleId;
        private String roleName;
        private String description;
        private List<String> permissions;
        private Instant createdDate;

        // Getters and setters
        public String getRoleId() { return roleId; }
        public void setRoleId(String roleId) { this.roleId = roleId; }

        public String getRoleName() { return roleName; }
        public void setRoleName(String roleName) { this.roleName = roleName; }

        public List<String> getPermissions() { return permissions; }
        public void setPermissions(List<String> permissions) { this.permissions = permissions; }
    }

    public String createRole(String roleName, String description, List<String> permissions) {
        String roleId = UUID.randomUUID().toString();

        Role role = new Role();
        role.setRoleId(roleId);
        role.setRoleName(roleName);
        // role.setDescription(description);
        role.setPermissions(permissions);
        // role.setCreatedDate(Instant.now());

        // roleRepository.save(role);

        logger.info("Role created: role_id={}, role_name={}, permissions={}",
                roleId, roleName, permissions);

        return roleId;
    }

    public void assignRoleToUser(String userId, String roleId) {
        // userRoleRepository.insert(userId, roleId);

        logger.info("Role assigned: user_id={}, role_id={}", userId, roleId);
    }

    public List<String> getUserRoles(String userId) {
        // return userRoleRepository.findByUserId(userId);

        // Simulated
        return Arrays.asList("developer", "security_reviewer");
    }

    public List<String> getUserPermissions(String userId) {
        List<String> roles = getUserRoles(userId);
        Set<String> allPermissions = new HashSet<>();

        for (String roleId : roles) {
            // Role role = roleRepository.findById(roleId).orElseThrow();
            // allPermissions.addAll(role.getPermissions());

            // Simulated permissions
            if ("developer".equals(roleId)) {
                allPermissions.addAll(Arrays.asList(
                    "code:read", "code:write", "deploy:dev", "logs:read"
                ));
            } else if ("security_reviewer".equals(roleId)) {
                allPermissions.addAll(Arrays.asList(
                    "audit_logs:read", "security_reports:read", "vulnerabilities:read"
                ));
            }
        }

        logger.info("Permissions retrieved: user_id={}, permission_count={}",
                userId, allPermissions.size());

        return new ArrayList<>(allPermissions);
    }

    public boolean hasPermission(String userId, String permission) {
        List<String> permissions = getUserPermissions(userId);
        boolean hasPermission = permissions.contains(permission);

        logger.info("Permission check: user_id={}, permission={}, granted={}",
                userId, permission, hasPermission);

        return hasPermission;
    }

    public Map<String, Object> checkAccess(
            String userId,
            String resource,
            String action) {

        String requiredPermission = resource + ":" + action;
        boolean granted = hasPermission(userId, requiredPermission);

        if (!granted) {
            logger.warn("Access denied: user_id={}, resource={}, action={}",
                    userId, resource, action);
        } else {
            logger.info("Access granted: user_id={}, resource={}, action={}",
                    userId, resource, action);
        }

        Map<String, Object> result = new HashMap<>();
        result.put("user_id", userId);
        result.put("resource", resource);
        result.put("action", action);
        result.put("granted", granted);
        result.put("timestamp", Instant.now());
        return result;
    }
}
```

---

## Privileged Access Management

```java
package com.organization.security;

import org.springframework.stereotype.Service;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;

@Service
public class PrivilegedAccessService {

    private static final Logger logger = LoggerFactory.getLogger(PrivilegedAccessService.class);

    public static class PrivilegedAccessRequest {
        private String requestId;
        private String userId;
        private String privilegedRole;
        private String justification;
        private int durationHours;
        private Instant requestedAt;
        private String status; // pending, approved, denied, expired

        // Getters and setters
        public String getRequestId() { return requestId; }
        public void setRequestId(String requestId) { this.requestId = requestId; }

        public String getUserId() { return userId; }
        public void setUserId(String userId) { this.userId = userId; }

        public String getPrivilegedRole() { return privilegedRole; }
        public void setPrivilegedRole(String privilegedRole) { this.privilegedRole = privilegedRole; }

        public String getStatus() { return status; }
        public void setStatus(String status) { this.status = status; }
    }

    public String requestPrivilegedAccess(
            String userId,
            String privilegedRole,
            String justification,
            int durationHours) {

        String requestId = UUID.randomUUID().toString();

        PrivilegedAccessRequest request = new PrivilegedAccessRequest();
        request.setRequestId(requestId);
        request.setUserId(userId);
        request.setPrivilegedRole(privilegedRole);
        // request.setJustification(justification);
        // request.setDurationHours(durationHours);
        // request.setRequestedAt(Instant.now());
        request.setStatus("pending");

        // privilegedAccessRepository.save(request);

        // Notify approvers
        notifyApprovers(requestId, privilegedRole);

        logger.info("Privileged access requested: request_id={}, user_id={}, role={}",
                requestId, userId, privilegedRole);

        return requestId;
    }

    public Map<String, Object> approvePrivilegedAccess(
            String requestId,
            String approverId) {

        // PrivilegedAccessRequest request = privilegedAccessRepository.findById(requestId).orElseThrow();

        PrivilegedAccessRequest request = new PrivilegedAccessRequest();
        request.setRequestId(requestId);
        request.setUserId("user123");
        request.setPrivilegedRole("production_admin");
        request.setStatus("pending");

        if (!"pending".equals(request.getStatus())) {
            throw new IllegalStateException("Request already processed");
        }

        request.setStatus("approved");
        // request.setApprovedBy(approverId);
        // request.setApprovedAt(Instant.now());
        // request.setExpiresAt(Instant.now().plus(durationHours, ChronoUnit.HOURS));

        // privilegedAccessRepository.update(request);

        // Grant temporary role
        grantTemporaryRole(request.getUserId(), request.getPrivilegedRole(), 8);

        logger.info("Privileged access approved: request_id={}, approver_id={}",
                requestId, approverId);

        Map<String, Object> result = new HashMap<>();
        result.put("request_id", requestId);
        result.put("status", "approved");
        result.put("expires_at", Instant.now().plus(8, ChronoUnit.HOURS));
        return result;
    }

    private void grantTemporaryRole(String userId, String role, int durationHours) {
        Instant expiresAt = Instant.now().plus(durationHours, ChronoUnit.HOURS);

        // temporaryRoleRepository.insert(userId, role, expiresAt);

        logger.info("Temporary role granted: user_id={}, role={}, expires_at={}",
                userId, role, expiresAt);
    }

    private void notifyApprovers(String requestId, String privilegedRole) {
        logger.info("Notifying approvers: request_id={}, role={}", requestId, privilegedRole);
        // Email/notification logic
    }

    public void revokeExpiredAccess() {
        // List<TemporaryRole> expiredRoles = temporaryRoleRepository.findExpired();

        // for (TemporaryRole role : expiredRoles) {
        //     temporaryRoleRepository.delete(role);
        //     logger.info("Expired role revoked: user_id={}, role={}", role.getUserId(), role.getRole());
        // }

        logger.info("Expired access revocation completed");
    }
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
