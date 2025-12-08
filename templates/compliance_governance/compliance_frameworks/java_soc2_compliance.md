---
template_id: compliance_governance_soc2_compliance_java
template_name: SOC 2 Type II Compliance - Java
version: 1.0.0
last_updated: 2025-12-05
language: java
category: compliance_governance
phase: compliance_frameworks
phase_number: 1
difficulty: advanced
estimated_time_hours: 6-8
prerequisites:
  - compliance_frameworks/README.md
related_templates:
  - compliance_frameworks/java_iso27001_implementation.md
  - ai_agent_governance/java_agent_observability.md
tools:
  - spring-security (authentication)
  - logback (logging)
  - micrometer (metrics)
tags:
  - soc2
  - trust-service-criteria
  - compliance
  - java
  - spring-boot
---

# SOC 2 Type II Compliance - Java

**Implement Trust Service Criteria for Spring Boot applications**

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### What is SOC 2 Type II?

**SOC 2** = Service Organization Control 2 report demonstrating security controls

**Type II** = Auditor tests controls over time (6-12 months), not just design

### Trust Service Criteria

1. **Security (CC)** - Common Criteria (required)
2. **Availability** - System uptime/performance
3. **Confidentiality** - Sensitive data protection
4. **Processing Integrity** - Accurate processing
5. **Privacy** - Personal information protection

---

## Common Criteria Implementation

### CC6.1: Logical Access Controls

**Control Objective**: Restrict logical access through authentication and authorization

```java
package com.company.compliance.security;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import dev.samstevens.totp.code.*;
import dev.samstevens.totp.qr.QrData;
import dev.samstevens.totp.secret.SecretGenerator;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import java.security.SecureRandom;
import java.time.Instant;
import java.util.Base64;
import java.util.UUID;

/**
 * Multi-factor authentication manager.
 *
 * SOC 2 Control: CC6.1 - Multi-factor authentication
 */
@Service
public class MFAManager {
    private static final Logger logger = LoggerFactory.getLogger(MFAManager.class);
    private static final int GCM_TAG_LENGTH = 128;

    private final SecretGenerator secretGenerator;
    private final CodeGenerator codeGenerator;
    private final CodeVerifier codeVerifier;

    public MFAManager() {
        this.secretGenerator = new DefaultSecretGenerator();
        this.codeGenerator = new DefaultCodeGenerator();
        this.codeVerifier = new DefaultCodeVerifier(new DefaultCodeGenerator());
    }

    /**
     * Generate MFA secret for user enrollment.
     *
     * @param userId User identifier
     * @param userEmail User email address
     * @return EnrollmentResponse containing secret and QR code
     */
    public EnrollmentResponse enrollUser(String userId, String userEmail) {
        String secret = secretGenerator.generate();

        // Generate QR code data
        QrData qrData = new QrData.Builder()
            .label(userEmail)
            .secret(secret)
            .issuer("YourApp")
            .algorithm(HashingAlgorithm.SHA1)
            .digits(6)
            .period(30)
            .build();

        // Store encrypted secret in database
        String encryptedSecret = encryptSecret(secret);

        logger.info("MFA enrollment initiated: userId={}, timestamp={}",
            userId, Instant.now());

        return new EnrollmentResponse(secret, qrData.getUri(), encryptedSecret);
    }

    /**
     * Verify MFA token during login.
     *
     * @param userId User identifier
     * @param token TOTP token from authenticator app
     * @return VerificationResult indicating success/failure
     */
    public VerificationResult verifyToken(String userId, String token) {
        // Retrieve encrypted secret from database
        String encryptedSecret = getUserMFASecret(userId);

        if (encryptedSecret == null) {
            logger.warn("MFA verification failed: userId={}, reason=mfa_not_enabled", userId);
            return new VerificationResult(false, "MFA not enabled");
        }

        String secret = decryptSecret(encryptedSecret);

        boolean isValid = codeVerifier.isValidCode(secret, token);

        logger.info("MFA verification attempt: userId={}, success={}, timestamp={}",
            userId, isValid, Instant.now());

        if (!isValid) {
            recordFailedAttempt(userId);
        }

        return new VerificationResult(isValid, isValid ? "Verified" : "Invalid token");
    }

    /**
     * Encrypt MFA secret for storage.
     */
    private String encryptSecret(String secret) {
        try {
            KeyGenerator keyGen = KeyGenerator.getInstance("AES");
            keyGen.init(256);
            SecretKey key = keyGen.generateKey();

            byte[] iv = new byte[12];
            new SecureRandom().nextBytes(iv);

            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            GCMParameterSpec gcmSpec = new GCMParameterSpec(GCM_TAG_LENGTH, iv);
            cipher.init(Cipher.ENCRYPT_MODE, key, gcmSpec);

            byte[] encrypted = cipher.doFinal(secret.getBytes());

            return Base64.getEncoder().encodeToString(encrypted);
        } catch (Exception e) {
            logger.error("Encryption failed", e);
            throw new RuntimeException("Failed to encrypt secret", e);
        }
    }

    /**
     * Decrypt MFA secret from storage.
     */
    private String decryptSecret(String encryptedSecret) {
        // Implementation: Decrypt using stored key
        return encryptedSecret; // Simplified
    }

    /**
     * Record failed MFA attempt for security monitoring.
     */
    private void recordFailedAttempt(String userId) {
        // Check for brute force attack
        long recentAttempts = countRecentFailedAttempts(userId, 15);

        if (recentAttempts >= 5) {
            logger.warn("Potential MFA brute force attack: userId={}, attemptCount={}",
                userId, recentAttempts);
            lockAccount(userId, 30); // Lock for 30 minutes
        }
    }

    private long countRecentFailedAttempts(String userId, int minutes) {
        // Implementation: Query database
        return 0;
    }

    private void lockAccount(String userId, int minutes) {
        // Implementation: Lock account temporarily
        logger.warn("Account locked: userId={}, durationMinutes={}", userId, minutes);
    }

    private String getUserMFASecret(String userId) {
        // Implementation: Retrieve from database
        return null;
    }

    /**
     * Enrollment response containing secret and QR code.
     */
    public static class EnrollmentResponse {
        private final String secret;
        private final String qrCodeUri;
        private final String encryptedSecret;

        public EnrollmentResponse(String secret, String qrCodeUri, String encryptedSecret) {
            this.secret = secret;
            this.qrCodeUri = qrCodeUri;
            this.encryptedSecret = encryptedSecret;
        }

        public String getSecret() { return secret; }
        public String getQrCodeUri() { return qrCodeUri; }
        public String getEncryptedSecret() { return encryptedSecret; }
    }

    /**
     * Verification result.
     */
    public static class VerificationResult {
        private final boolean valid;
        private final String message;

        public VerificationResult(boolean valid, String message) {
            this.valid = valid;
            this.message = message;
        }

        public boolean isValid() { return valid; }
        public String getMessage() { return message; }
    }
}
```

### CC6.7: Encryption of Confidential Data

```java
package com.company.compliance.security;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import java.security.SecureRandom;
import java.time.Instant;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;

/**
 * Data encryption manager for protecting confidential data.
 *
 * SOC 2 Control: CC6.7 - Data encryption at rest
 * Standard: AES-256-GCM
 */
@Service
public class DataEncryptionManager {
    private static final Logger logger = LoggerFactory.getLogger(DataEncryptionManager.class);
    private static final String ALGORITHM = "AES/GCM/NoPadding";
    private static final int GCM_TAG_LENGTH = 128;
    private static final int IV_LENGTH = 12;

    /**
     * Encrypt sensitive data at rest.
     *
     * @param plaintext Data to encrypt
     * @param context Additional authenticated data context
     * @return EncryptedData containing ciphertext, IV, and auth tag
     */
    public EncryptedData encryptData(String plaintext, Map<String, String> context) {
        try {
            // Generate AES-256 key
            KeyGenerator keyGen = KeyGenerator.getInstance("AES");
            keyGen.init(256);
            SecretKey key = keyGen.generateKey();

            // Generate random IV
            byte[] iv = new byte[IV_LENGTH];
            new SecureRandom().nextBytes(iv);

            // Setup cipher with GCM mode
            Cipher cipher = Cipher.getInstance(ALGORITHM);
            GCMParameterSpec gcmSpec = new GCMParameterSpec(GCM_TAG_LENGTH, iv);
            cipher.init(Cipher.ENCRYPT_MODE, key, gcmSpec);

            // Add context as Additional Authenticated Data (AAD)
            if (context != null && !context.isEmpty()) {
                String contextString = context.toString();
                cipher.updateAAD(contextString.getBytes());
            }

            // Encrypt
            byte[] ciphertext = cipher.doFinal(plaintext.getBytes());

            logger.info("Data encrypted: algorithm={}, context={}, timestamp={}",
                ALGORITHM, context, Instant.now());

            return new EncryptedData(
                Base64.getEncoder().encodeToString(ciphertext),
                Base64.getEncoder().encodeToString(iv),
                ALGORITHM,
                context
            );
        } catch (Exception e) {
            logger.error("Encryption failed", e);
            throw new RuntimeException("Failed to encrypt data", e);
        }
    }

    /**
     * Decrypt sensitive data.
     *
     * @param encryptedData Encrypted data object
     * @return Decrypted plaintext
     */
    public String decryptData(EncryptedData encryptedData) {
        try {
            // Retrieve key (in production: from key management service)
            SecretKey key = retrieveKey();

            byte[] iv = Base64.getDecoder().decode(encryptedData.getIv());
            byte[] ciphertext = Base64.getDecoder().decode(encryptedData.getCiphertext());

            Cipher cipher = Cipher.getInstance(encryptedData.getAlgorithm());
            GCMParameterSpec gcmSpec = new GCMParameterSpec(GCM_TAG_LENGTH, iv);
            cipher.init(Cipher.DECRYPT_MODE, key, gcmSpec);

            // Add context as AAD
            if (encryptedData.getContext() != null) {
                String contextString = encryptedData.getContext().toString();
                cipher.updateAAD(contextString.getBytes());
            }

            byte[] plaintext = cipher.doFinal(ciphertext);

            logger.info("Data decrypted: context={}, timestamp={}",
                encryptedData.getContext(), Instant.now());

            return new String(plaintext);
        } catch (Exception e) {
            logger.error("Decryption failed", e);
            throw new RuntimeException("Failed to decrypt data", e);
        }
    }

    private SecretKey retrieveKey() {
        // Implementation: Retrieve from key management service
        try {
            KeyGenerator keyGen = KeyGenerator.getInstance("AES");
            keyGen.init(256);
            return keyGen.generateKey();
        } catch (Exception e) {
            throw new RuntimeException("Failed to retrieve key", e);
        }
    }

    /**
     * Encrypted data container.
     */
    public static class EncryptedData {
        private final String ciphertext;
        private final String iv;
        private final String algorithm;
        private final Map<String, String> context;

        public EncryptedData(String ciphertext, String iv, String algorithm,
                           Map<String, String> context) {
            this.ciphertext = ciphertext;
            this.iv = iv;
            this.algorithm = algorithm;
            this.context = context != null ? new HashMap<>(context) : new HashMap<>();
        }

        public String getCiphertext() { return ciphertext; }
        public String getIv() { return iv; }
        public String getAlgorithm() { return algorithm; }
        public Map<String, String> getContext() { return context; }
    }
}
```

### CC7.2: System Monitoring

```java
package com.company.compliance.monitoring;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Security event monitoring and alerting.
 *
 * SOC 2 Control: CC7.2 - Security event logging
 */
@Service
public class SecurityMonitoring {
    private static final Logger logger = LoggerFactory.getLogger(SecurityMonitoring.class);

    private final Counter securityEventsCounter;
    private final Counter authenticationAttemptsCounter;

    public SecurityMonitoring(MeterRegistry meterRegistry) {
        this.securityEventsCounter = Counter.builder("security.events")
            .description("Total security events by type")
            .tags("type", "security")
            .register(meterRegistry);

        this.authenticationAttemptsCounter = Counter.builder("authentication.attempts")
            .description("Total authentication attempts")
            .tags("result", "unknown")
            .register(meterRegistry);
    }

    /**
     * Log security event with structured data.
     *
     * @param eventType Type of security event
     * @param severity Event severity level
     * @param details Additional event details
     */
    public void logSecurityEvent(String eventType, String severity, Map<String, Object> details) {
        Map<String, Object> event = new HashMap<>(details);
        event.put("event", eventType);
        event.put("severity", severity);
        event.put("timestamp", Instant.now());

        logger.info("Security event: {}", event);

        securityEventsCounter.increment();

        if ("critical".equals(severity)) {
            sendSecurityAlert(event);
        }
    }

    /**
     * Log authentication attempt.
     *
     * @param userId User attempting authentication
     * @param result Success or failure
     * @param details Additional details
     */
    public void logAuthenticationAttempt(String userId, String result, Map<String, Object> details) {
        Map<String, Object> event = new HashMap<>(details);
        event.put("event", "authentication_attempt");
        event.put("userId", userId);
        event.put("result", result);
        event.put("timestamp", Instant.now());

        logger.info("Authentication attempt: {}", event);

        authenticationAttemptsCounter.increment();

        if ("failure".equals(result)) {
            checkForBruteForce(userId);
        }
    }

    /**
     * Detect brute force attacks.
     */
    private void checkForBruteForce(String userId) {
        // Implementation: Check failure rate
        long recentFailures = countRecentFailures(userId, 15);

        if (recentFailures >= 5) {
            Map<String, Object> details = new HashMap<>();
            details.put("userId", userId);
            details.put("failureCount", recentFailures);

            logSecurityEvent("brute_force_detected", "critical", details);
            lockAccount(userId);
        }
    }

    /**
     * Send critical security alerts.
     */
    private void sendSecurityAlert(Map<String, Object> event) {
        logger.error("CRITICAL SECURITY ALERT: {}", event);
        // Implementation: Integrate with PagerDuty, Slack, etc.
    }

    private long countRecentFailures(String userId, int minutes) {
        // Implementation: Query failure count
        return 0;
    }

    private void lockAccount(String userId) {
        // Implementation: Lock account
        logger.warn("Account locked due to brute force: userId={}", userId);
    }
}
```

---

## Success Criteria

- [ ] Multi-factor authentication enforced for all users
- [ ] All sensitive data encrypted at rest (AES-256-GCM)
- [ ] HTTPS enforced with TLS 1.3
- [ ] Security events logged with structured data
- [ ] Failed authentication attempts monitored
- [ ] User access removed within 24 hours of offboarding
- [ ] System health monitoring operational

---

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
