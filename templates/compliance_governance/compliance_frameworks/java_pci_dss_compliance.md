---
template_id: compliance_governance_pci_dss_java
template_name: PCI-DSS v4.0 Compliance - Java
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
  - compliance_frameworks/java_iso27001_implementation.md
related_templates:
  - compliance_frameworks/java_gdpr_compliance.md
tools:
  - spring-security (authentication)
  - bouncy-castle (cryptography)
tags:
  - pci-dss
  - payment-security
  - cardholder-data
  - java
  - spring-boot
---

# PCI-DSS v4.0 Compliance - Java

**Payment Card Industry Data Security Standard for Spring Boot applications**

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### PCI-DSS v4.0 Key Requirements

**12 Requirements** for protecting cardholder data:
- Req 3: Protect stored account data
- Req 4: Protect cardholder data with strong cryptography during transmission
- Req 8: Identify users and authenticate access
- Req 10: Log and monitor all access to system components

---

## Requirement 3: Protect Stored Account Data

```java
package com.company.compliance.pci;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.time.Instant;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.regex.Pattern;

/**
 * Card Data Protection Manager for PCI-DSS compliance.
 *
 * PCI-DSS Requirement 3: Protect stored account data
 * PCI-DSS Requirement 3.3: Mask PAN when displayed
 * PCI-DSS Requirement 3.4: Render PAN unreadable
 */
@Service
public class CardDataProtectionManager {
    private static final Logger logger = LoggerFactory.getLogger(CardDataProtectionManager.class);

    private static final int GCM_TAG_LENGTH = 128;
    private static final int GCM_IV_LENGTH = 12;

    private final SecretKey masterKey;

    public CardDataProtectionManager(SecretKey masterKey) {
        this.masterKey = masterKey;
    }

    /**
     * Tokenize Primary Account Number (PAN) instead of storing.
     *
     * PCI-DSS Requirement 3.2.1: Do not store sensitive authentication data
     *
     * @param pan Primary Account Number
     * @return Token that replaces PAN
     */
    public String tokenizePAN(String pan) {
        if (!validatePAN(pan)) {
            throw new IllegalArgumentException("Invalid PAN format");
        }

        // Generate cryptographically secure token
        String token = "TKN" + UUID.randomUUID().toString().replace("-", "").substring(0, 16).toUpperCase();

        // Store token-to-PAN mapping in secure vault (HSM/external tokenization service)
        storeTokenMapping(token, pan);

        logger.info("PAN tokenized: token_prefix={}, timestamp={}",
            token.substring(0, 6), Instant.now());

        return token;
    }

    /**
     * Mask PAN for display.
     *
     * PCI-DSS Requirement 3.3: Mask PAN when displayed
     * Only first 6 and last 4 digits shown
     *
     * @param pan Primary Account Number
     * @return Masked PAN (e.g., "411111******1111")
     */
    public String maskPAN(String pan) {
        if (pan.length() < 13) {
            throw new IllegalArgumentException("PAN too short to mask");
        }

        // Show first 6 (BIN) and last 4 digits
        String masked = pan.substring(0, 6) +
                       "*".repeat(pan.length() - 10) +
                       pan.substring(pan.length() - 4);

        logger.info("PAN masked for display: masked_pan={}, timestamp={}",
            masked, Instant.now());

        return masked;
    }

    /**
     * Encrypt PAN with AES-256-GCM.
     *
     * PCI-DSS Requirement 3.4.1: Use strong cryptography
     * PCI-DSS Requirement 3.5.1: Key strength minimum 256-bit
     *
     * @param pan Primary Account Number to encrypt
     * @return Map with ciphertext, IV, and algorithm
     */
    public Map<String, String> encryptPAN(String pan) {
        if (!validatePAN(pan)) {
            throw new IllegalArgumentException("Invalid PAN format");
        }

        try {
            // Generate random IV
            byte[] iv = new byte[GCM_IV_LENGTH];
            SecureRandom random = new SecureRandom();
            random.nextBytes(iv);

            // Initialize cipher
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            GCMParameterSpec spec = new GCMParameterSpec(GCM_TAG_LENGTH, iv);
            cipher.init(Cipher.ENCRYPT_MODE, masterKey, spec);

            // Encrypt PAN
            byte[] ciphertext = cipher.doFinal(pan.getBytes(StandardCharsets.UTF_8));

            logger.info("PAN encrypted: algorithm=AES-256-GCM, timestamp={}",
                Instant.now());

            Map<String, String> result = new HashMap<>();
            result.put("ciphertext", Base64.getEncoder().encodeToString(ciphertext));
            result.put("iv", Base64.getEncoder().encodeToString(iv));
            result.put("algorithm", "AES-256-GCM");

            return result;

        } catch (Exception e) {
            logger.error("PAN encryption failed: error={}", e.getMessage());
            throw new RuntimeException("Encryption failed", e);
        }
    }

    /**
     * Decrypt PAN.
     *
     * @param encryptedData Map with ciphertext and IV
     * @return Decrypted PAN
     */
    public String decryptPAN(Map<String, String> encryptedData) {
        try {
            byte[] ciphertext = Base64.getDecoder().decode(encryptedData.get("ciphertext"));
            byte[] iv = Base64.getDecoder().decode(encryptedData.get("iv"));

            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            GCMParameterSpec spec = new GCMParameterSpec(GCM_TAG_LENGTH, iv);
            cipher.init(Cipher.DECRYPT_MODE, masterKey, spec);

            byte[] plaintext = cipher.doFinal(ciphertext);

            logger.info("PAN decrypted: timestamp={}", Instant.now());

            return new String(plaintext, StandardCharsets.UTF_8);

        } catch (Exception e) {
            logger.error("PAN decryption failed: error={}", e.getMessage());
            throw new RuntimeException("Decryption failed", e);
        }
    }

    /**
     * Create one-way hash of PAN for searching.
     *
     * PCI-DSS Requirement 3.4.1: Render PAN unreadable
     *
     * @param pan Primary Account Number
     * @return SHA-256 hash of PAN
     */
    public String hashPANForSearch(String pan) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(pan.getBytes(StandardCharsets.UTF_8));

            logger.info("PAN hashed: algorithm=SHA-256, timestamp={}",
                Instant.now());

            return Base64.getEncoder().encodeToString(hash);

        } catch (Exception e) {
            logger.error("PAN hashing failed: error={}", e.getMessage());
            throw new RuntimeException("Hashing failed", e);
        }
    }

    /**
     * Validate PAN using Luhn algorithm.
     *
     * @param pan Primary Account Number
     * @return true if valid, false otherwise
     */
    private boolean validatePAN(String pan) {
        // Remove spaces and hyphens
        pan = pan.replaceAll("[\\s-]", "");

        // Check length (13-19 digits)
        if (pan.length() < 13 || pan.length() > 19) {
            return false;
        }

        // Check all numeric
        if (!pan.matches("\\d+")) {
            return false;
        }

        // Luhn algorithm
        int sum = 0;
        boolean alternate = false;

        for (int i = pan.length() - 1; i >= 0; i--) {
            int digit = Character.getNumericValue(pan.charAt(i));

            if (alternate) {
                digit *= 2;
                if (digit > 9) {
                    digit -= 9;
                }
            }

            sum += digit;
            alternate = !alternate;
        }

        return (sum % 10 == 0);
    }

    /**
     * Store token-to-PAN mapping in secure vault.
     * Note: In production, use HSM or external tokenization service
     */
    private void storeTokenMapping(String token, String pan) {
        // This would typically interface with a secure token vault
        // For demonstration purposes only
    }
}
```

---

## Requirement 8: Multi-Factor Authentication

```java
package com.company.compliance.pci;

import dev.samstevens.totp.code.*;
import dev.samstevens.totp.qr.QrData;
import dev.samstevens.totp.qr.QrGenerator;
import dev.samstevens.totp.qr.ZxingPngQrGenerator;
import dev.samstevens.totp.secret.DefaultSecretGenerator;
import dev.samstevens.totp.time.SystemTimeProvider;
import dev.samstevens.totp.time.TimeProvider;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.HashMap;
import java.util.Map;

/**
 * PCI-DSS Authentication Manager.
 *
 * PCI-DSS Requirement 8: Identify users and authenticate access
 * PCI-DSS Requirement 8.3.6: Multi-factor authentication (MFA)
 */
@Service
public class PCIAuthenticationManager {
    private static final Logger logger = LoggerFactory.getLogger(PCIAuthenticationManager.class);

    private static final int PASSWORD_MIN_LENGTH = 12;
    private static final int PASSWORD_MAX_AGE_DAYS = 90;
    private static final int LOCKOUT_THRESHOLD = 6; // PCI-DSS 8.3.4
    private static final int LOCKOUT_DURATION_MINUTES = 30;

    /**
     * Generate MFA secret for user.
     *
     * PCI-DSS Requirement 8.3.6: MFA for admin access to CDE
     *
     * @param userId User identifier
     * @param userEmail User email
     * @return MFA secret and QR code data URI
     */
    public Map<String, String> generateMFASecret(String userId, String userEmail) {
        DefaultSecretGenerator secretGenerator = new DefaultSecretGenerator();
        String secret = secretGenerator.generate();

        // Generate QR code for easy enrollment
        QrData data = new QrData.Builder()
            .label(userEmail)
            .secret(secret)
            .issuer("PCI-DSS Application")
            .algorithm(HashingAlgorithm.SHA1)
            .digits(6)
            .period(30)
            .build();

        QrGenerator generator = new ZxingPngQrGenerator();
        byte[] imageData = generator.generate(data);
        String qrCodeDataUri = generator.getDataUriBase64(imageData);

        logger.info("MFA secret generated: userId={}, timestamp={}",
            userId, Instant.now());

        Map<String, String> result = new HashMap<>();
        result.put("secret", secret);
        result.put("qrCodeDataUri", qrCodeDataUri);

        return result;
    }

    /**
     * Verify MFA token.
     *
     * @param secret User's MFA secret
     * @param token Token from authenticator app
     * @return true if valid, false otherwise
     */
    public boolean verifyMFAToken(String secret, String token) {
        TimeProvider timeProvider = new SystemTimeProvider();
        CodeGenerator codeGenerator = new DefaultCodeGenerator();
        CodeVerifier verifier = new DefaultCodeVerifier(codeGenerator, timeProvider);

        boolean valid = verifier.isValidCode(secret, token);

        logger.info("MFA token verified: valid={}, timestamp={}",
            valid, Instant.now());

        return valid;
    }

    /**
     * Validate password complexity.
     *
     * PCI-DSS Requirement 8.3.6: Password complexity
     * - Minimum 12 characters (or 8 if system doesn't support 12)
     * - Numeric and alphabetic characters
     *
     * @param password Password to validate
     * @return Validation result with violations
     */
    public ValidationResult validatePasswordComplexity(String password) {
        var violations = new java.util.ArrayList<String>();

        // Minimum length
        if (password.length() < PASSWORD_MIN_LENGTH) {
            violations.add("Password must be at least " + PASSWORD_MIN_LENGTH + " characters");
        }

        // Contains numeric
        if (!password.matches(".*\\d.*")) {
            violations.add("Password must contain at least one number");
        }

        // Contains alphabetic
        if (!password.matches(".*[a-zA-Z].*")) {
            violations.add("Password must contain at least one letter");
        }

        // Contains uppercase
        if (!password.matches(".*[A-Z].*")) {
            violations.add("Password must contain at least one uppercase letter");
        }

        // Contains lowercase
        if (!password.matches(".*[a-z].*")) {
            violations.add("Password must contain at least one lowercase letter");
        }

        boolean isValid = violations.isEmpty();

        if (!isValid) {
            logger.warn("Password complexity validation failed: violations={}", violations);
        }

        return new ValidationResult(isValid, violations);
    }

    /**
     * Check if password has expired.
     *
     * PCI-DSS Requirement 8.3.9: Password change every 90 days
     *
     * @param userId User identifier
     * @param lastChanged When password was last changed
     * @return true if expired, false otherwise
     */
    public boolean checkPasswordExpiry(String userId, Instant lastChanged) {
        long ageDays = ChronoUnit.DAYS.between(lastChanged, Instant.now());
        boolean expired = ageDays >= PASSWORD_MAX_AGE_DAYS;

        if (expired) {
            logger.warn("Password expired: userId={}, ageDays={}, maxAgeDays={}, timestamp={}",
                userId, ageDays, PASSWORD_MAX_AGE_DAYS, Instant.now());
        }

        return expired;
    }

    public static class ValidationResult {
        private final boolean valid;
        private final java.util.List<String> violations;

        public ValidationResult(boolean valid, java.util.List<String> violations) {
            this.valid = valid;
            this.violations = violations;
        }

        public boolean isValid() { return valid; }
        public java.util.List<String> getViolations() { return violations; }
    }
}
```

---

## Requirement 10: Audit Logging

```java
package com.company.compliance.pci;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * PCI-DSS Audit Logger.
 *
 * PCI-DSS Requirement 10: Log and monitor all access
 * PCI-DSS Requirement 10.2: Implement audit trails
 */
@Service
public class PCIAuditLogger {
    private static final Logger logger = LoggerFactory.getLogger(PCIAuditLogger.class);

    public enum EventType {
        USER_ACCESS_CDE,
        PRIVILEGED_ACTION,
        ACCESS_CARDHOLDER_DATA,
        SYSTEM_CHANGE,
        AUTHENTICATION_FAILED,
        AUTHENTICATION_SUCCESS
    }

    /**
     * Log access to Cardholder Data Environment.
     *
     * PCI-DSS Requirement 10.2.1: User access to CHD
     * PCI-DSS Requirement 10.3: Record audit trail entries
     *
     * @param userId User identifier
     * @param action Action performed (read, write, delete)
     * @param resource Resource accessed
     * @param success Whether action succeeded
     * @param ipAddress Source IP address
     */
    public void logCDEAccess(String userId, String action, String resource,
                             boolean success, String ipAddress) {
        Map<String, Object> auditEntry = new HashMap<>();
        auditEntry.put("event_type", EventType.USER_ACCESS_CDE);
        auditEntry.put("timestamp", Instant.now().toString());
        auditEntry.put("user_id", userId);
        auditEntry.put("action", action);
        auditEntry.put("resource", resource);
        auditEntry.put("success", success);
        auditEntry.put("ip_address", ipAddress);
        auditEntry.put("event_id", UUID.randomUUID().toString());

        logger.warn("CDE access: {}", auditEntry);

        // Store in tamper-proof audit log
        storeAuditEntry(auditEntry);
    }

    /**
     * Log actions by privileged users.
     *
     * PCI-DSS Requirement 10.2.2: Actions by privileged users
     *
     * @param userId Administrator user ID
     * @param action Administrative action
     * @param targetSystem System affected
     * @param justification Business justification
     */
    public void logPrivilegedAction(String userId, String action,
                                    String targetSystem, String justification) {
        Map<String, Object> auditEntry = new HashMap<>();
        auditEntry.put("event_type", EventType.PRIVILEGED_ACTION);
        auditEntry.put("timestamp", Instant.now().toString());
        auditEntry.put("user_id", userId);
        auditEntry.put("action", action);
        auditEntry.put("target_system", targetSystem);
        auditEntry.put("justification", justification);
        auditEntry.put("event_id", UUID.randomUUID().toString());

        logger.warn("Privileged action: {}", auditEntry);
        storeAuditEntry(auditEntry);
    }

    /**
     * Store audit entry in tamper-proof log.
     *
     * PCI-DSS Requirement 10.5.3: Protect audit trails
     * Note: In production, use WORM storage or external SIEM
     */
    private void storeAuditEntry(Map<String, Object> entry) {
        // Store in centralized logging system
        // Use write-once-read-many (WORM) storage
        // Sign entries with cryptographic hash
    }
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
- [ ] Logs tamper-proof and retained 1 year minimum

---

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
