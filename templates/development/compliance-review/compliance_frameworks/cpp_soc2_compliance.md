---
template_id: compliance_governance_soc2_compliance_cpp
template_name: SOC 2 Type II Compliance - C++
version: 1.0.0
last_updated: 2025-12-05
language: cpp
category: compliance_governance
phase: compliance_frameworks
phase_number: 1
difficulty: advanced
estimated_time_hours: 6-8
prerequisites:
  - compliance_frameworks/README.md
related_templates:
  - compliance_frameworks/cpp_iso27001_implementation.md
tools:
  - OpenSSL (cryptography)
  - spdlog (logging)
tags:
  - soc2
  - trust-service-criteria
  - compliance
  - cpp
  - modern-cpp
---

# SOC 2 Type II Compliance - C++

**Implement Trust Service Criteria for C++ applications**

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### Trust Service Criteria

1. **Security (CC)** - Common Criteria (required)
2. **Confidentiality** - Sensitive data protection

**Implementation**: Modern C++17/20 with RAII and smart pointers

---

## CC6.7: Encryption of Confidential Data

```cpp
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <spdlog/spdlog.h>
#include <memory>
#include <vector>
#include <string>
#include <stdexcept>
#include <cstring>
#include <chrono>

/**
 * Data encryption manager for protecting confidential data.
 * SOC 2 Control: CC6.7 - Data encryption at rest
 * Standard: AES-256-GCM
 */

namespace compliance {

class EncryptedData {
public:
    std::vector<unsigned char> ciphertext;
    std::vector<unsigned char> iv;
    std::vector<unsigned char> tag;
    std::string algorithm;

    EncryptedData() : algorithm("AES-256-GCM") {}
};

class DataEncryptionManager {
private:
    static constexpr size_t AES_256_KEY_SIZE = 32;
    static constexpr size_t AES_GCM_IV_SIZE = 12;
    static constexpr size_t AES_GCM_TAG_SIZE = 16;

    std::shared_ptr<spdlog::logger> logger_;

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
    explicit DataEncryptionManager(std::shared_ptr<spdlog::logger> logger)
        : logger_(std::move(logger)) {
        // Initialize OpenSSL
        OpenSSL_add_all_algorithms();
    }

    /**
     * Encrypt sensitive data at rest.
     *
     * @param plaintext Data to encrypt
     * @param key Encryption key (32 bytes for AES-256)
     * @return Encrypted data structure
     */
    EncryptedData encryptData(const std::string& plaintext,
                             const std::vector<unsigned char>& key) {
        if (key.size() != AES_256_KEY_SIZE) {
            throw std::invalid_argument("Key must be 32 bytes for AES-256");
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
                              key.data(), encrypted.iv.data()) != 1) {
            throw std::runtime_error("Failed to initialize encryption");
        }

        // Allocate buffer for ciphertext
        encrypted.ciphertext.resize(plaintext.size() + EVP_CIPHER_block_size(EVP_aes_256_gcm()));

        // Encrypt plaintext
        int len = 0;
        if (EVP_EncryptUpdate(ctx.get(), encrypted.ciphertext.data(), &len,
                             reinterpret_cast<const unsigned char*>(plaintext.data()),
                             plaintext.size()) != 1) {
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

        // Log encryption event
        logger_->info("Data encrypted: algorithm={}, length={}, timestamp={}",
                     encrypted.algorithm, ciphertext_len,
                     std::chrono::system_clock::now().time_since_epoch().count());

        return encrypted;
    }

    /**
     * Decrypt sensitive data.
     *
     * @param encrypted Encrypted data structure
     * @param key Decryption key (32 bytes for AES-256)
     * @return Decrypted plaintext
     */
    std::string decryptData(const EncryptedData& encrypted,
                          const std::vector<unsigned char>& key) {
        if (key.size() != AES_256_KEY_SIZE) {
            throw std::invalid_argument("Key must be 32 bytes for AES-256");
        }

        // Create cipher context
        CipherContext ctx;

        // Initialize decryption
        if (EVP_DecryptInit_ex(ctx.get(), EVP_aes_256_gcm(), nullptr,
                              key.data(), encrypted.iv.data()) != 1) {
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

        // Log decryption event
        logger_->info("Data decrypted: length={}, timestamp={}",
                     plaintext_len,
                     std::chrono::system_clock::now().time_since_epoch().count());

        return std::string(reinterpret_cast<const char*>(plaintext.data()), plaintext.size());
    }

    /**
     * Generate cryptographically secure random key.
     *
     * @return 32-byte AES-256 key
     */
    static std::vector<unsigned char> generateKey() {
        std::vector<unsigned char> key(AES_256_KEY_SIZE);
        if (RAND_bytes(key.data(), AES_256_KEY_SIZE) != 1) {
            throw std::runtime_error("Failed to generate key");
        }
        return key;
    }
};

} // namespace compliance

/**
 * Example usage demonstrating encryption/decryption.
 */
int main() {
    // Initialize logger
    auto logger = spdlog::stdout_color_mt("soc2_compliance");
    logger->set_level(spdlog::level::info);

    try {
        // Create encryption manager
        compliance::DataEncryptionManager encryptionMgr(logger);

        // Generate encryption key
        auto key = compliance::DataEncryptionManager::generateKey();

        // Sample plaintext
        std::string plaintext = "Sensitive customer data";

        // Encrypt data
        auto encrypted = encryptionMgr.encryptData(plaintext, key);
        logger->info("Encryption successful: ciphertext_len={}", encrypted.ciphertext.size());

        // Decrypt data
        std::string decrypted = encryptionMgr.decryptData(encrypted, key);
        logger->info("Decryption successful: plaintext_len={}", decrypted.size());

        // Verify decrypted data matches original
        if (decrypted == plaintext) {
            logger->info("Decryption verification: SUCCESS");
        } else {
            logger->error("Decryption verification: FAILED");
            return 1;
        }

    } catch (const std::exception& e) {
        logger->error("Error: {}", e.what());
        return 1;
    }

    return 0;
}
```

---

## Compilation

```bash
g++ -std=c++17 -o soc2_compliance cpp_soc2_compliance.cpp -lssl -lcrypto -lfmt -lpthread
```

---

## Success Criteria

- [ ] All sensitive data encrypted at rest (AES-256-GCM)
- [ ] RAII ensures proper resource cleanup
- [ ] Authentication tags verified on decryption
- [ ] Modern C++ best practices followed
- [ ] Exception safety guaranteed

---

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
