---
template_id: compliance_governance_pci_dss_c
template_name: PCI-DSS v4.0 Compliance - C
version: 1.0.0
last_updated: 2025-12-05
language: c
category: compliance_governance
phase: compliance_frameworks
phase_number: 1
difficulty: advanced
estimated_time_hours: 8-10
prerequisites:
  - compliance_frameworks/c_soc2_compliance.md
related_templates:
  - risk_management/c_risk_assessment.md
tools:
  - OpenSSL (cryptography)
  - syslog (logging)
tags:
  - pci-dss
  - payment-security
  - cardholder-data
  - c
---

# PCI-DSS v4.0 Compliance - C

**Payment Card Industry Data Security Standard for C applications**

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### PCI-DSS v4.0 Requirements

**12 Core Requirements** for protecting payment card data in C applications.

---

## Requirement 3: Protect Stored Account Data

```c
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <openssl/sha.h>
#include <string.h>
#include <stdio.h>
#include <syslog.h>
#include <time.h>

#define AES_256_KEY_SIZE 32
#define AES_GCM_IV_SIZE 12
#define AES_GCM_TAG_SIZE 16
#define PAN_MIN_LENGTH 13
#define PAN_MAX_LENGTH 19

/**
 * Card Data Protection Manager for PCI-DSS compliance.
 *
 * PCI-DSS Requirement 3: Protect stored account data
 * PCI-DSS Requirement 3.3: Mask PAN when displayed
 * PCI-DSS Requirement 3.4: Render PAN unreadable
 */

typedef struct {
    unsigned char ciphertext[256];
    size_t ciphertext_len;
    unsigned char iv[AES_GCM_IV_SIZE];
    unsigned char tag[AES_GCM_TAG_SIZE];
    char algorithm[32];
} encrypted_data_t;

/**
 * Mask PAN for display.
 *
 * PCI-DSS Requirement 3.3: Mask PAN when displayed
 * Only first 6 and last 4 digits shown
 */
int mask_pan(const char *pan, char *masked, size_t masked_size) {
    size_t pan_len = strlen(pan);

    if (pan_len < PAN_MIN_LENGTH || pan_len > PAN_MAX_LENGTH) {
        return -1;
    }

    if (masked_size < pan_len + 1) {
        return -1;
    }

    // Show first 6 (BIN) and last 4 digits
    memcpy(masked, pan, 6);
    memset(masked + 6, '*', pan_len - 10);
    memcpy(masked + pan_len - 4, pan + pan_len - 4, 4);
    masked[pan_len] = '\0';

    syslog(LOG_INFO, "PAN masked for display: masked_pan=%s, timestamp=%ld",
           masked, time(NULL));

    return 0;
}

/**
 * Encrypt PAN with AES-256-GCM.
 *
 * PCI-DSS Requirement 3.4.1: Use strong cryptography
 * PCI-DSS Requirement 3.5.1: Key strength minimum 256-bit
 */
int encrypt_pan(const char *pan, const unsigned char *key, encrypted_data_t *encrypted) {
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) {
        return -1;
    }

    // Generate random IV
    if (RAND_bytes(encrypted->iv, AES_GCM_IV_SIZE) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        return -1;
    }

    // Initialize encryption
    if (EVP_EncryptInit_ex(ctx, EVP_aes_256_gcm(), NULL, key, encrypted->iv) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        return -1;
    }

    // Encrypt PAN
    int len;
    size_t pan_len = strlen(pan);

    if (EVP_EncryptUpdate(ctx, encrypted->ciphertext, &len,
                         (unsigned char *)pan, pan_len) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        return -1;
    }

    encrypted->ciphertext_len = len;

    // Finalize encryption
    if (EVP_EncryptFinal_ex(ctx, encrypted->ciphertext + len, &len) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        return -1;
    }

    encrypted->ciphertext_len += len;

    // Get authentication tag
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_GET_TAG, AES_GCM_TAG_SIZE,
                           encrypted->tag) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        return -1;
    }

    strcpy(encrypted->algorithm, "AES-256-GCM");

    EVP_CIPHER_CTX_free(ctx);

    syslog(LOG_INFO, "PAN encrypted: algorithm=AES-256-GCM, timestamp=%ld",
           time(NULL));

    return 0;
}

/**
 * Decrypt PAN.
 */
int decrypt_pan(const encrypted_data_t *encrypted, const unsigned char *key,
                char *plaintext, size_t plaintext_size) {
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) {
        return -1;
    }

    // Initialize decryption
    if (EVP_DecryptInit_ex(ctx, EVP_aes_256_gcm(), NULL, key, encrypted->iv) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        return -1;
    }

    // Decrypt ciphertext
    int len;
    unsigned char temp[256];

    if (EVP_DecryptUpdate(ctx, temp, &len, encrypted->ciphertext,
                         encrypted->ciphertext_len) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        return -1;
    }

    int plaintext_len = len;

    // Set expected authentication tag
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_TAG, AES_GCM_TAG_SIZE,
                           (void *)encrypted->tag) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        return -1;
    }

    // Finalize decryption (verifies authentication tag)
    int ret = EVP_DecryptFinal_ex(ctx, temp + len, &len);

    EVP_CIPHER_CTX_free(ctx);

    if (ret <= 0) {
        syslog(LOG_ERR, "PAN decryption failed: authentication tag verification failed");
        return -1;
    }

    plaintext_len += len;

    if (plaintext_size < (size_t)plaintext_len + 1) {
        return -1;
    }

    memcpy(plaintext, temp, plaintext_len);
    plaintext[plaintext_len] = '\0';

    // Securely wipe temporary buffer
    memset(temp, 0, sizeof(temp));

    syslog(LOG_INFO, "PAN decrypted: timestamp=%ld", time(NULL));

    return plaintext_len;
}

/**
 * Create one-way hash of PAN for searching.
 *
 * PCI-DSS Requirement 3.4.1: Render PAN unreadable
 */
int hash_pan_for_search(const char *pan, unsigned char *hash) {
    SHA256_CTX sha256;

    if (SHA256_Init(&sha256) != 1) {
        return -1;
    }

    if (SHA256_Update(&sha256, pan, strlen(pan)) != 1) {
        return -1;
    }

    if (SHA256_Final(hash, &sha256) != 1) {
        return -1;
    }

    syslog(LOG_INFO, "PAN hashed: algorithm=SHA-256, timestamp=%ld",
           time(NULL));

    return 0;
}

/**
 * Validate PAN using Luhn algorithm.
 */
int validate_pan(const char *pan) {
    size_t len = strlen(pan);

    // Check length (13-19 digits)
    if (len < PAN_MIN_LENGTH || len > PAN_MAX_LENGTH) {
        return 0;
    }

    // Check all numeric
    for (size_t i = 0; i < len; i++) {
        if (pan[i] < '0' || pan[i] > '9') {
            return 0;
        }
    }

    // Luhn algorithm
    int sum = 0;
    int alternate = 0;

    for (int i = len - 1; i >= 0; i--) {
        int digit = pan[i] - '0';

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
 * Securely wipe memory containing sensitive data.
 */
void secure_wipe(void *ptr, size_t len) {
    volatile unsigned char *p = ptr;
    while (len--) {
        *p++ = 0;
    }
}
```

---

## Requirement 8: Password Validation

```c
#include <string.h>
#include <ctype.h>
#include <time.h>

#define PASSWORD_MIN_LENGTH 12
#define PASSWORD_MAX_AGE_DAYS 90

/**
 * Validate password complexity.
 *
 * PCI-DSS Requirement 8.3.6: Password complexity
 * - Minimum 12 characters
 * - Numeric and alphabetic characters
 */
int validate_password_complexity(const char *password, char *violations[], int *violation_count) {
    *violation_count = 0;

    size_t len = strlen(password);

    // Check minimum length
    if (len < PASSWORD_MIN_LENGTH) {
        violations[(*violation_count)++] = "Password must be at least 12 characters";
    }

    // Check for numeric
    int has_digit = 0;
    int has_upper = 0;
    int has_lower = 0;

    for (size_t i = 0; i < len; i++) {
        if (isdigit(password[i])) has_digit = 1;
        if (isupper(password[i])) has_upper = 1;
        if (islower(password[i])) has_lower = 1;
    }

    if (!has_digit) {
        violations[(*violation_count)++] = "Password must contain at least one number";
    }

    if (!has_upper) {
        violations[(*violation_count)++] = "Password must contain at least one uppercase letter";
    }

    if (!has_lower) {
        violations[(*violation_count)++] = "Password must contain at least one lowercase letter";
    }

    int is_valid = (*violation_count == 0);

    if (!is_valid) {
        syslog(LOG_WARNING, "Password complexity validation failed: violation_count=%d",
               *violation_count);
    }

    return is_valid;
}

/**
 * Check if password has expired.
 *
 * PCI-DSS Requirement 8.3.9: Password change every 90 days
 */
int check_password_expiry(const char *user_id, time_t last_changed) {
    time_t now = time(NULL);
    int age_days = (int)((now - last_changed) / (24 * 60 * 60));

    int expired = (age_days >= PASSWORD_MAX_AGE_DAYS);

    if (expired) {
        syslog(LOG_WARNING, "Password expired: user_id=%s, age_days=%d, max_age_days=%d",
               user_id, age_days, PASSWORD_MAX_AGE_DAYS);
    }

    return expired;
}
```

---

## Success Criteria

- [ ] PAN never stored in clear text
- [ ] PAN masked when displayed (first 6, last 4 only)
- [ ] AES-256-GCM encryption for stored PAN
- [ ] Secure memory wiping for sensitive data
- [ ] Password complexity enforced (12+ chars)
- [ ] Passwords expire after 90 days
- [ ] Luhn algorithm validates PAN format
- [ ] All operations logged to syslog

---

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
