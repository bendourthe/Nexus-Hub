---
template_id: compliance_governance_iso27001_java
template_name: ISO 27001 Implementation - Java
version: 1.0.0
last_updated: 2025-12-05
language: java
category: compliance_governance
phase: compliance_frameworks
phase_number: 1
difficulty: advanced
estimated_time_hours: 8-10
prerequisites:
  - compliance_frameworks/java_soc2_compliance.md
related_templates:
  - risk_management/java_risk_assessment.md
tools:
  - spring-security (security)
  - spring-boot-actuator (monitoring)
tags:
  - iso27001
  - isms
  - information-security
  - java
  - spring-boot
---

# ISO 27001:2022 Implementation - Java

**Information Security Management System for Spring Boot applications**

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### ISO 27001:2022 Structure

**4 Themes**: Organizational (37), People (8), Physical (14), Technological (34)
**Total**: 93 controls

### Implementation Approach

Focus on **Technological Controls** implementable in Java/Spring Boot

---

## Control 8.2: Privileged Access Rights

```java
package com.company.compliance.access;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import java.time.Instant;
import java.time.Duration;
import java.util.UUID;

/**
 * Privileged Access Manager with Just-In-Time (JIT) access.
 *
 * ISO 27001 Control 8.2: Privileged access management
 */
@Service
public class PrivilegedAccessManager {
    private static final Logger logger = LoggerFactory.getLogger(PrivilegedAccessManager.class);
    private static final int MAX_ELEVATION_HOURS = 8;

    public enum PrivilegeLevel {
        STANDARD, ELEVATED, ADMIN, SUPERADMIN
    }

    /**
     * Request temporary privilege elevation.
     *
     * @param userId User requesting elevation
     * @param requestedLevel Privilege level requested
     * @param justification Business justification
     * @param durationHours Duration in hours (max 8)
     * @return Request ID
     */
    public String requestPrivilegeElevation(String userId, PrivilegeLevel requestedLevel,
                                           String justification, int durationHours) {
        if (durationHours > MAX_ELEVATION_HOURS) {
            throw new IllegalArgumentException("Maximum elevation period is 8 hours");
        }

        String requestId = UUID.randomUUID().toString();
        Instant expiresAt = Instant.now().plus(Duration.ofHours(durationHours));

        logger.warn("Privilege elevation requested: requestId={}, userId={}, level={}, " +
                   "duration={}h, justification={}, timestamp={}",
            requestId, userId, requestedLevel, durationHours, justification, Instant.now());

        // Store request in database
        // Notify approvers

        return requestId;
    }

    /**
     * Approve privilege elevation request.
     *
     * @param requestId Request identifier
     * @param approverId Approver user ID
     * @return Approval status
     */
    public ApprovalResult approveElevation(String requestId, String approverId) {
        // Retrieve request from database
        // Grant temporary privileges
        // Set expiration timer

        logger.warn("Privilege elevation approved: requestId={}, approverId={}, timestamp={}",
            requestId, approverId, Instant.now());

        return new ApprovalResult(true, "Approved", Instant.now().plus(Duration.ofHours(4)));
    }

    /**
     * Automatically revoke expired privileges.
     */
    public void revokeExpiredPrivileges() {
        // Query database for expired privileges
        // Revoke automatically

        logger.info("Expired privileges revoked: timestamp={}", Instant.now());
    }

    public static class ApprovalResult {
        private final boolean approved;
        private final String message;
        private final Instant expiresAt;

        public ApprovalResult(boolean approved, String message, Instant expiresAt) {
            this.approved = approved;
            this.message = message;
            this.expiresAt = expiresAt;
        }

        public boolean isApproved() { return approved; }
        public String getMessage() { return message; }
        public Instant getExpiresAt() { return expiresAt; }
    }
}
```

## Control 8.5: Secure Authentication

```java
package com.company.compliance.auth;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import java.util.regex.Pattern;

/**
 * Secure authentication manager.
 *
 * ISO 27001 Control 8.5: Password protection
 */
@Service
public class SecureAuthenticationManager {
    private static final int BCRYPT_STRENGTH = 12;
    private final BCryptPasswordEncoder passwordEncoder;

    public SecureAuthenticationManager() {
        this.passwordEncoder = new BCryptPasswordEncoder(BCRYPT_STRENGTH);
    }

    /**
     * Validate password strength.
     *
     * ISO 27001 Control 8.5: Password policy
     */
    public ValidationResult validatePasswordStrength(String password) {
        if (password.length() < 12) {
            return new ValidationResult(false, "Password must be at least 12 characters");
        }

        if (!Pattern.compile("[A-Z]").matcher(password).find()) {
            return new ValidationResult(false, "Must contain uppercase letter");
        }

        if (!Pattern.compile("[a-z]").matcher(password).find()) {
            return new ValidationResult(false, "Must contain lowercase letter");
        }

        if (!Pattern.compile("[0-9]").matcher(password).find()) {
            return new ValidationResult(false, "Must contain number");
        }

        if (!Pattern.compile("[!@#$%^&*(),.?\":{}|<>]").matcher(password).find()) {
            return new ValidationResult(false, "Must contain special character");
        }

        return new ValidationResult(true, "Password meets requirements");
    }

    /**
     * Hash password with bcrypt.
     */
    public String hashPassword(String password) {
        return passwordEncoder.encode(password);
    }

    /**
     * Verify password against hash.
     */
    public boolean verifyPassword(String password, String hash) {
        return passwordEncoder.matches(password, hash);
    }

    public static class ValidationResult {
        private final boolean valid;
        private final String message;

        public ValidationResult(boolean valid, String message) {
            this.valid = valid;
            this.message = message;
        }

        public boolean isValid() { return valid; }
        public String getMessage() { return message; }
    }
}
```

---

## Success Criteria

- [ ] Privileged access requires justification and approval
- [ ] Temporary privileges auto-revoked after expiration
- [ ] Password policy enforced (12+ chars, complexity)
- [ ] Account lockout after 5 failed attempts
- [ ] Configuration changes audited
- [ ] Authentication anomalies detected

---

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
