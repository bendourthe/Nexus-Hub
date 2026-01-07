---
template_id: compliance_governance_soc2_compliance_c
template_name: SOC 2 Type II Compliance - C
version: 1.0.0
last_updated: 2025-12-05
language: c
category: compliance_governance
phase: compliance_frameworks
phase_number: 1
difficulty: advanced
estimated_time_hours: 6-8
prerequisites:
  - compliance_frameworks/README.md
related_templates:
  - compliance_frameworks/c_iso27001_implementation.md
tools:
  - OpenSSL (cryptography)
  - syslog (logging)
tags:
  - soc2
  - trust-service-criteria
  - compliance
  - c
  - embedded
---

# SOC 2 Type II Compliance - C

**Implement Trust Service Criteria for C applications**

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### Trust Service Criteria

1. **Security (CC)** - Common Criteria (required)
2. **Confidentiality** - Sensitive data protection

**Note**: C implementations focus on cryptography and secure memory handling

---

## CC6.7: Encryption of Confidential Data

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <openssl/err.h>
#include <syslog.h>
#include <time.h>

/**
 * Data encryption manager for protecting confidential data.
 * SOC 2 Control: CC6.7 - Data encryption at rest
 * Standard: AES-256-GCM
 */

#define AES_256_KEY_SIZE 32
#define AES_GCM_IV_SIZE 12
#define AES_GCM_TAG_SIZE 16

typedef struct {
    unsigned char *ciphertext;
    size_t ciphertext_len;
    unsigned char iv[AES_GCM_IV_SIZE];
    unsigned char tag[AES_GCM_TAG_SIZE];
} encrypted_data_t;

/**
 * Encrypt sensitive data at rest.
 *
 * @param plaintext Data to encrypt
 * @param plaintext_len Length of plaintext
 * @param key Encryption key (32 bytes for AES-256)
 * @param encrypted Output encrypted data structure
 * @return 1 on success, 0 on failure
 */
int encrypt_data(const unsigned char *plaintext, size_t plaintext_len,
                const unsigned char *key, encrypted_data_t *encrypted) {
    EVP_CIPHER_CTX *ctx;
    int len;
    int ciphertext_len;

    // Initialize OpenSSL
    OpenSSL_add_all_algorithms();
    ERR_load_crypto_strings();

    // Generate random IV
    if (RAND_bytes(encrypted->iv, AES_GCM_IV_SIZE) != 1) {
        syslog(LOG_ERR, "Failed to generate IV");
        return 0;
    }

    // Create and initialize context
    if (!(ctx = EVP_CIPHER_CTX_new())) {
        syslog(LOG_ERR, "Failed to create cipher context");
        return 0;
    }

    // Initialize encryption operation with AES-256-GCM
    if (EVP_EncryptInit_ex(ctx, EVP_aes_256_gcm(), NULL, key, encrypted->iv) != 1) {
        syslog(LOG_ERR, "Failed to initialize encryption");
        EVP_CIPHER_CTX_free(ctx);
        return 0;
    }

    // Allocate buffer for ciphertext
    encrypted->ciphertext = malloc(plaintext_len + EVP_CIPHER_block_size(EVP_aes_256_gcm()));
    if (!encrypted->ciphertext) {
        syslog(LOG_ERR, "Failed to allocate ciphertext buffer");
        EVP_CIPHER_CTX_free(ctx);
        return 0;
    }

    // Encrypt plaintext
    if (EVP_EncryptUpdate(ctx, encrypted->ciphertext, &len, plaintext, plaintext_len) != 1) {
        syslog(LOG_ERR, "Failed to encrypt data");
        free(encrypted->ciphertext);
        EVP_CIPHER_CTX_free(ctx);
        return 0;
    }
    ciphertext_len = len;

    // Finalize encryption
    if (EVP_EncryptFinal_ex(ctx, encrypted->ciphertext + len, &len) != 1) {
        syslog(LOG_ERR, "Failed to finalize encryption");
        free(encrypted->ciphertext);
        EVP_CIPHER_CTX_free(ctx);
        return 0;
    }
    ciphertext_len += len;

    // Get authentication tag
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_GET_TAG, AES_GCM_TAG_SIZE, encrypted->tag) != 1) {
        syslog(LOG_ERR, "Failed to get authentication tag");
        free(encrypted->ciphertext);
        EVP_CIPHER_CTX_free(ctx);
        return 0;
    }

    encrypted->ciphertext_len = ciphertext_len;

    // Log encryption event
    syslog(LOG_INFO, "Data encrypted: algorithm=AES-256-GCM, length=%zu, timestamp=%ld",
           ciphertext_len, time(NULL));

    EVP_CIPHER_CTX_free(ctx);
    return 1;
}

/**
 * Decrypt sensitive data.
 *
 * @param encrypted Encrypted data structure
 * @param key Decryption key (32 bytes for AES-256)
 * @param plaintext Output buffer for plaintext
 * @param plaintext_len Output plaintext length
 * @return 1 on success, 0 on failure
 */
int decrypt_data(const encrypted_data_t *encrypted, const unsigned char *key,
                unsigned char **plaintext, size_t *plaintext_len) {
    EVP_CIPHER_CTX *ctx;
    int len;
    int ret;

    // Create and initialize context
    if (!(ctx = EVP_CIPHER_CTX_new())) {
        syslog(LOG_ERR, "Failed to create cipher context");
        return 0;
    }

    // Initialize decryption operation
    if (EVP_DecryptInit_ex(ctx, EVP_aes_256_gcm(), NULL, key, encrypted->iv) != 1) {
        syslog(LOG_ERR, "Failed to initialize decryption");
        EVP_CIPHER_CTX_free(ctx);
        return 0;
    }

    // Allocate buffer for plaintext
    *plaintext = malloc(encrypted->ciphertext_len);
    if (!*plaintext) {
        syslog(LOG_ERR, "Failed to allocate plaintext buffer");
        EVP_CIPHER_CTX_free(ctx);
        return 0;
    }

    // Decrypt ciphertext
    if (EVP_DecryptUpdate(ctx, *plaintext, &len, encrypted->ciphertext,
                         encrypted->ciphertext_len) != 1) {
        syslog(LOG_ERR, "Failed to decrypt data");
        free(*plaintext);
        EVP_CIPHER_CTX_free(ctx);
        return 0;
    }
    *plaintext_len = len;

    // Set expected authentication tag
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_TAG, AES_GCM_TAG_SIZE,
                           (void *)encrypted->tag) != 1) {
        syslog(LOG_ERR, "Failed to set authentication tag");
        free(*plaintext);
        EVP_CIPHER_CTX_free(ctx);
        return 0;
    }

    // Finalize decryption (verifies authentication tag)
    ret = EVP_DecryptFinal_ex(ctx, *plaintext + len, &len);

    if (ret > 0) {
        *plaintext_len += len;
        syslog(LOG_INFO, "Data decrypted: length=%zu, timestamp=%ld",
               *plaintext_len, time(NULL));
    } else {
        syslog(LOG_ERR, "Decryption failed: authentication tag verification failed");
        free(*plaintext);
        *plaintext = NULL;
    }

    EVP_CIPHER_CTX_free(ctx);
    return ret > 0;
}

/**
 * Securely wipe memory containing sensitive data.
 *
 * @param ptr Pointer to memory to wipe
 * @param len Length of memory to wipe
 */
void secure_wipe(void *ptr, size_t len) {
    volatile unsigned char *p = ptr;
    while (len--) {
        *p++ = 0;
    }
}

/**
 * Free encrypted data structure and wipe sensitive data.
 *
 * @param encrypted Encrypted data structure to free
 */
void free_encrypted_data(encrypted_data_t *encrypted) {
    if (encrypted->ciphertext) {
        secure_wipe(encrypted->ciphertext, encrypted->ciphertext_len);
        free(encrypted->ciphertext);
        encrypted->ciphertext = NULL;
    }
    secure_wipe(encrypted->iv, AES_GCM_IV_SIZE);
    secure_wipe(encrypted->tag, AES_GCM_TAG_SIZE);
}

/**
 * Example usage demonstrating encryption/decryption.
 */
int main(void) {
    // Open syslog
    openlog("soc2_compliance", LOG_PID | LOG_CONS, LOG_USER);

    // Generate encryption key (in production: use key management service)
    unsigned char key[AES_256_KEY_SIZE];
    if (RAND_bytes(key, AES_256_KEY_SIZE) != 1) {
        syslog(LOG_ERR, "Failed to generate encryption key");
        closelog();
        return 1;
    }

    // Sample plaintext
    const char *plaintext_str = "Sensitive customer data";
    const unsigned char *plaintext = (const unsigned char *)plaintext_str;
    size_t plaintext_len = strlen(plaintext_str);

    // Encrypt data
    encrypted_data_t encrypted = {0};
    if (!encrypt_data(plaintext, plaintext_len, key, &encrypted)) {
        syslog(LOG_ERR, "Encryption failed");
        secure_wipe(key, AES_256_KEY_SIZE);
        closelog();
        return 1;
    }

    syslog(LOG_INFO, "Encryption successful: ciphertext_len=%zu", encrypted.ciphertext_len);

    // Decrypt data
    unsigned char *decrypted = NULL;
    size_t decrypted_len = 0;

    if (!decrypt_data(&encrypted, key, &decrypted, &decrypted_len)) {
        syslog(LOG_ERR, "Decryption failed");
        free_encrypted_data(&encrypted);
        secure_wipe(key, AES_256_KEY_SIZE);
        closelog();
        return 1;
    }

    syslog(LOG_INFO, "Decryption successful: plaintext_len=%zu", decrypted_len);

    // Verify decrypted data matches original
    if (decrypted_len == plaintext_len &&
        memcmp(decrypted, plaintext, plaintext_len) == 0) {
        syslog(LOG_INFO, "Decryption verification: SUCCESS");
    } else {
        syslog(LOG_ERR, "Decryption verification: FAILED");
    }

    // Clean up
    secure_wipe(decrypted, decrypted_len);
    free(decrypted);
    free_encrypted_data(&encrypted);
    secure_wipe(key, AES_256_KEY_SIZE);

    closelog();
    return 0;
}
```

---

## Compilation

```bash
gcc -o soc2_compliance c_soc2_compliance.c -lssl -lcrypto
```

---

## Success Criteria

- [ ] All sensitive data encrypted at rest (AES-256-GCM)
- [ ] Secure memory wiping implemented
- [ ] Authentication tags verified on decryption
- [ ] Security events logged to syslog
- [ ] Key management integrated

---

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
