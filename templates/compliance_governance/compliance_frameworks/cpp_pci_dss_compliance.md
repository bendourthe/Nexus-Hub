---
template_id: compliance_governance_pci_dss_cpp
template_name: PCI-DSS v4.0 Compliance - C++
version: 1.0.0
last_updated: 2025-12-05
language: cpp
category: compliance_governance
phase: compliance_frameworks
phase_number: 1
difficulty: advanced
estimated_time_hours: 8-10
prerequisites:
  - compliance_frameworks/cpp_soc2_compliance.md
related_templates:
  - risk_management/cpp_risk_assessment.md
tools:
  - OpenSSL (cryptography)
  - spdlog (logging)
tags:
  - pci-dss
  - payment-security
  - cardholder-data
  - cpp
  - modern-cpp
---

# PCI-DSS v4.0 Compliance - C++

**Payment Card Industry Data Security Standard for Modern C++ applications**

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### PCI-DSS v4.0 Requirements

**12 Core Requirements** for protecting payment card data with modern C++17/20.

---

## Requirement 3: Protect Stored Account Data

```cpp
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <spdlog/spdlog.h>
#include <memory>
#include <vector>
#include <string>
#include <stdexcept>
#include <algorithm>
#include <chrono>

/**
 * Card Data Protection Manager for PCI-DSS compliance.
 *
 * PCI-DSS Requirement 3: Protect stored account data
 * PCI-DSS Requirement 3.3: Mask PAN when displayed
 * PCI-DSS Requirement 3.4: Render PAN unreadable
 */

namespace pci {

struct EncryptedData {
    std::vector<unsigned char> ciphertext;
    std::vector<unsigned char> iv;
    std::vector<unsigned char> tag;
    std::string algorithm;

    EncryptedData() : algorithm("AES-256-GCM") {}
};

class CardDataProtectionManager {
private:
    static constexpr size_t AES_256_KEY_SIZE = 32;
    static constexpr size_t AES_GCM_IV_SIZE = 12;
    static constexpr size_t AES_GCM_TAG_SIZE = 16;
    static constexpr size_t PAN_MIN_LENGTH = 13;
    static constexpr size_t PAN_MAX_LENGTH = 19;

    std::shared_ptr<spdlog::logger> logger_;
    std::vector<unsigned char> master_key_;

    // RAII wrapper for EVP_CIPHER_CTX
    class CipherContext {
    public:
        CipherContext() : ctx_(EVP_CIPHER_CTX_new()) {
            if (!ctx_) {
                throw std::runtime_error("Failed to create cipher context");
            }
        }

        ~CipherContext() {
            if (ctx_) {
                EVP_CIPHER_CTX_free(ctx_);
            }
        }

        EVP_CIPHER_CTX* get() { return ctx_; }

        // Delete copy operations
        CipherContext(const CipherContext&) = delete;
        CipherContext& operator=(const CipherContext&) = delete;

        // Allow move operations
        CipherContext(CipherContext&& other) noexcept : ctx_(other.ctx_) {
            other.ctx_ = nullptr;
        }

        CipherContext& operator=(CipherContext&& other) noexcept {
            if (this != &other) {
                if (ctx_) {
                    EVP_CIPHER_CTX_free(ctx_);
                }
                ctx_ = other.ctx_;
                other.ctx_ = nullptr;
            }
            return *this;
        }

    private:
        EVP_CIPHER_CTX* ctx_;
    };

public:
    explicit CardDataProtectionManager(
        std::shared_ptr<spdlog::logger> logger,
        const std::vector<unsigned char>& master_key)
        : logger_(std::move(logger)), master_key_(master_key) {

        if (master_key_.size() != AES_256_KEY_SIZE) {
            throw std::invalid_argument("Master key must be 32 bytes for AES-256");
        }

        OpenSSL_add_all_algorithms();
    }

    /**
     * Mask PAN for display.
     *
     * PCI-DSS Requirement 3.3: Mask PAN when displayed
     * Only first 6 and last 4 digits shown
     */
    std::string maskPAN(const std::string& pan) {
        if (pan.length() < PAN_MIN_LENGTH || pan.length() > PAN_MAX_LENGTH) {
            throw std::invalid_argument("Invalid PAN length");
        }

        // Show first 6 (BIN) and last 4 digits
        std::string masked = pan.substr(0, 6) +
                           std::string(pan.length() - 10, '*') +
                           pan.substr(pan.length() - 4);

        logger_->info("PAN masked for display: masked_pan={}, timestamp={}",
                     masked,
                     std::chrono::system_clock::now().time_since_epoch().count());

        return masked;
    }

    /**
     * Encrypt PAN with AES-256-GCM.
     *
     * PCI-DSS Requirement 3.4.1: Use strong cryptography
     * PCI-DSS Requirement 3.5.1: Key strength minimum 256-bit
     */
    EncryptedData encryptPAN(const std::string& pan) {
        if (!validatePAN(pan)) {
            throw std::invalid_argument("Invalid PAN format");
        }

        EncryptedData encrypted;

        // Generate random IV
        encrypted.iv.resize(AES_GCM_IV_SIZE);
        if (RAND_bytes(encrypted.iv.data(), AES_GCM_IV_SIZE) != 1) {
            throw std::runtime_error("Failed to generate IV");
        }

        // Create cipher context
        CipherContext ctx;

        // Initialize encryption
        if (EVP_EncryptInit_ex(ctx.get(), EVP_aes_256_gcm(), nullptr,
                              master_key_.data(), encrypted.iv.data()) != 1) {
            throw std::runtime_error("Failed to initialize encryption");
        }

        // Allocate buffer for ciphertext
        encrypted.ciphertext.resize(pan.size() + EVP_CIPHER_block_size(EVP_aes_256_gcm()));

        // Encrypt PAN
        int len = 0;
        if (EVP_EncryptUpdate(ctx.get(), encrypted.ciphertext.data(), &len,
                             reinterpret_cast<const unsigned char*>(pan.data()),
                             pan.size()) != 1) {
            throw std::runtime_error("Failed to encrypt data");
        }

        int ciphertext_len = len;

        // Finalize encryption
        if (EVP_EncryptFinal_ex(ctx.get(), encrypted.ciphertext.data() + len, &len) != 1) {
            throw std::runtime_error("Failed to finalize encryption");
        }

        ciphertext_len += len;
        encrypted.ciphertext.resize(ciphertext_len);

        // Get authentication tag
        encrypted.tag.resize(AES_GCM_TAG_SIZE);
        if (EVP_CIPHER_CTX_ctrl(ctx.get(), EVP_CTRL_GCM_GET_TAG, AES_GCM_TAG_SIZE,
                               encrypted.tag.data()) != 1) {
            throw std::runtime_error("Failed to get authentication tag");
        }

        logger_->info("PAN encrypted: algorithm={}, length={}, timestamp={}",
                     encrypted.algorithm, ciphertext_len,
                     std::chrono::system_clock::now().time_since_epoch().count());

        return encrypted;
    }

    /**
     * Decrypt PAN.
     */
    std::string decryptPAN(const EncryptedData& encrypted) {
        // Create cipher context
        CipherContext ctx;

        // Initialize decryption
        if (EVP_DecryptInit_ex(ctx.get(), EVP_aes_256_gcm(), nullptr,
                              master_key_.data(), encrypted.iv.data()) != 1) {
            throw std::runtime_error("Failed to initialize decryption");
        }

        // Allocate buffer for plaintext
        std::vector<unsigned char> plaintext(encrypted.ciphertext.size());

        // Decrypt ciphertext
        int len = 0;
        if (EVP_DecryptUpdate(ctx.get(), plaintext.data(), &len,
                             encrypted.ciphertext.data(),
                             encrypted.ciphertext.size()) != 1) {
            throw std::runtime_error("Failed to decrypt data");
        }

        int plaintext_len = len;

        // Set expected authentication tag
        if (EVP_CIPHER_CTX_ctrl(ctx.get(), EVP_CTRL_GCM_SET_TAG, AES_GCM_TAG_SIZE,
                               const_cast<unsigned char*>(encrypted.tag.data())) != 1) {
            throw std::runtime_error("Failed to set authentication tag");
        }

        // Finalize decryption (verifies authentication tag)
        int ret = EVP_DecryptFinal_ex(ctx.get(), plaintext.data() + len, &len);

        if (ret <= 0) {
            throw std::runtime_error("Decryption failed: authentication tag verification failed");
        }

        plaintext_len += len;
        plaintext.resize(plaintext_len);

        logger_->info("PAN decrypted: length={}, timestamp={}",
                     plaintext_len,
                     std::chrono::system_clock::now().time_since_epoch().count());

        return std::string(reinterpret_cast<const char*>(plaintext.data()), plaintext.size());
    }

    /**
     * Validate PAN using Luhn algorithm.
     */
    bool validatePAN(const std::string& pan) const {
        // Check length
        if (pan.length() < PAN_MIN_LENGTH || pan.length() > PAN_MAX_LENGTH) {
            return false;
        }

        // Check all numeric
        if (!std::all_of(pan.begin(), pan.end(), ::isdigit)) {
            return false;
        }

        // Luhn algorithm
        int sum = 0;
        bool alternate = false;

        for (auto it = pan.rbegin(); it != pan.rend(); ++it) {
            int digit = *it - '0';

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
};

} // namespace pci
```

---

## Requirement 8: Password Validation

```cpp
#include <string>
#include <vector>
#include <algorithm>
#include <cctype>
#include <chrono>

namespace pci {

class PCIAuthenticationManager {
private:
    static constexpr int PASSWORD_MIN_LENGTH = 12;
    static constexpr int PASSWORD_MAX_AGE_DAYS = 90;

    std::shared_ptr<spdlog::logger> logger_;

public:
    struct ValidationResult {
        bool valid;
        std::vector<std::string> violations;
    };

    explicit PCIAuthenticationManager(std::shared_ptr<spdlog::logger> logger)
        : logger_(std::move(logger)) {}

    /**
     * Validate password complexity.
     *
     * PCI-DSS Requirement 8.3.6: Password complexity
     * - Minimum 12 characters
     * - Numeric and alphabetic characters
     */
    ValidationResult validatePasswordComplexity(const std::string& password) {
        std::vector<std::string> violations;

        // Check minimum length
        if (password.length() < PASSWORD_MIN_LENGTH) {
            violations.push_back("Password must be at least 12 characters");
        }

        // Check for numeric
        if (!std::any_of(password.begin(), password.end(), ::isdigit)) {
            violations.push_back("Password must contain at least one number");
        }

        // Check for alphabetic
        if (!std::any_of(password.begin(), password.end(), ::isalpha)) {
            violations.push_back("Password must contain at least one letter");
        }

        // Check for uppercase
        if (!std::any_of(password.begin(), password.end(), ::isupper)) {
            violations.push_back("Password must contain at least one uppercase letter");
        }

        // Check for lowercase
        if (!std::any_of(password.begin(), password.end(), ::islower)) {
            violations.push_back("Password must contain at least one lowercase letter");
        }

        bool valid = violations.empty();

        if (!valid) {
            logger_->warn("Password complexity validation failed: violation_count={}",
                         violations.size());
        }

        return ValidationResult{valid, violations};
    }

    /**
     * Check if password has expired.
     *
     * PCI-DSS Requirement 8.3.9: Password change every 90 days
     */
    bool checkPasswordExpiry(const std::string& user_id,
                            const std::chrono::system_clock::time_point& last_changed) {
        auto now = std::chrono::system_clock::now();
        auto age = std::chrono::duration_cast<std::chrono::hours>(now - last_changed);
        int age_days = age.count() / 24;

        bool expired = (age_days >= PASSWORD_MAX_AGE_DAYS);

        if (expired) {
            logger_->warn("Password expired: user_id={}, age_days={}, max_age_days={}",
                         user_id, age_days, PASSWORD_MAX_AGE_DAYS);
        }

        return expired;
    }
};

} // namespace pci
```

---

## Success Criteria

- [ ] PAN never stored in clear text
- [ ] PAN masked when displayed (first 6, last 4 only)
- [ ] AES-256-GCM encryption with RAII resource management
- [ ] Exception-safe operations
- [ ] Modern C++ idioms (smart pointers, RAII, move semantics)
- [ ] Password complexity enforced (12+ chars)
- [ ] Passwords expire after 90 days
- [ ] Luhn algorithm validates PAN format

---

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
