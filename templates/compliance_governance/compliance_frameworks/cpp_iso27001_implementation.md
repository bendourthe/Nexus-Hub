---
template_id: compliance_governance_iso27001_cpp
template_name: ISO 27001 Implementation - C++
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
  - iso27001
  - isms
  - information-security
  - cpp
  - modern-cpp
---

# ISO 27001:2022 Implementation - C++

**Information Security Management System for Modern C++ applications**

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### ISO 27001:2022 Structure

**4 Themes**: Organizational (37), People (8), Physical (14), Technological (34)
**Total**: 93 controls

---

## Control 5.17: Authentication Information

```cpp
#include <spdlog/spdlog.h>
#include <string>
#include <vector>
#include <algorithm>
#include <cctype>
#include <chrono>
#include <memory>

namespace iso27001 {

/**
 * Secure Authentication Manager.
 *
 * ISO 27001 Control 5.17: Authentication information
 */
class SecureAuthenticationManager {
private:
    static constexpr int PASSWORD_MIN_LENGTH = 12;
    static constexpr int PASSWORD_MAX_AGE_DAYS = 90;
    static constexpr int MAX_FAILED_ATTEMPTS = 5;

    std::shared_ptr<spdlog::logger> logger_;

public:
    struct ValidationResult {
        bool compliant;
        std::vector<std::string> violations;
    };

    explicit SecureAuthenticationManager(std::shared_ptr<spdlog::logger> logger)
        : logger_(std::move(logger)) {}

    /**
     * Validate password strength.
     *
     * ISO 27001 Control 5.17: Password policy
     */
    ValidationResult validatePasswordStrength(const std::string& password) {
        std::vector<std::string> violations;

        if (password.length() < PASSWORD_MIN_LENGTH) {
            violations.push_back("Password must be at least 12 characters");
        }

        if (!std::any_of(password.begin(), password.end(), ::isupper)) {
            violations.push_back("Password must contain uppercase letter");
        }

        if (!std::any_of(password.begin(), password.end(), ::islower)) {
            violations.push_back("Password must contain lowercase letter");
        }

        if (!std::any_of(password.begin(), password.end(), ::isdigit)) {
            violations.push_back("Password must contain number");
        }

        if (!std::any_of(password.begin(), password.end(), ::ispunct)) {
            violations.push_back("Password must contain special character");
        }

        bool compliant = violations.empty();

        if (!compliant) {
            logger_->warn("Password validation failed: violation_count={}", violations.size());
        }

        return {compliant, violations};
    }

    /**
     * Record failed login attempt.
     *
     * ISO 27001 Control 8.3: Account lockout
     */
    bool recordFailedLogin(const std::string& userId, int& failedAttempts) {
        failedAttempts++;

        logger_->warn("Failed login: user_id={}, attempts={}", userId, failedAttempts);

        if (failedAttempts >= MAX_FAILED_ATTEMPTS) {
            logger_->error("Account locked: user_id={}, attempts={}", userId, failedAttempts);
            return true; // Account locked
        }

        return false; // Account still active
    }

    /**
     * Check password expiry.
     *
     * ISO 27001 Control 5.17: Password expiration
     */
    bool checkPasswordExpiry(const std::string& userId,
                            const std::chrono::system_clock::time_point& lastChanged) {
        auto now = std::chrono::system_clock::now();
        auto age = std::chrono::duration_cast<std::chrono::hours>(now - lastChanged);
        int ageDays = age.count() / 24;

        bool expired = (ageDays >= PASSWORD_MAX_AGE_DAYS);

        if (expired) {
            logger_->warn("Password expired: user_id={}, age_days={}, max_age_days={}",
                         userId, ageDays, PASSWORD_MAX_AGE_DAYS);
        }

        return expired;
    }
};

/**
 * Security Monitor for anomaly detection.
 *
 * ISO 27001 Control 8.16: Monitoring activities
 */
class SecurityMonitor {
private:
    std::shared_ptr<spdlog::logger> logger_;

    static constexpr int FAILED_LOGINS_THRESHOLD = 5;
    static constexpr int UNUSUAL_ACCESS_TIME_START = 2; // 2 AM
    static constexpr int UNUSUAL_ACCESS_TIME_END = 5;   // 5 AM

public:
    struct Anomaly {
        std::string type;
        int count;
        std::string severity;
    };

    explicit SecurityMonitor(std::shared_ptr<spdlog::logger> logger)
        : logger_(std::move(logger)) {}

    /**
     * Detect authentication anomalies.
     */
    std::vector<Anomaly> detectAuthAnomalies(const std::string& userId,
                                             const std::vector<AuthLog>& logs) {
        std::vector<Anomaly> anomalies;

        int failedCount = 0;
        int nightAccessCount = 0;

        for (const auto& log : logs) {
            if (log.userId == userId) {
                if (!log.success) {
                    failedCount++;
                }

                auto tm = std::chrono::system_clock::to_time_t(log.timestamp);
                auto localTm = *std::localtime(&tm);
                int hour = localTm.tm_hour;

                if (hour >= UNUSUAL_ACCESS_TIME_START && hour <= UNUSUAL_ACCESS_TIME_END) {
                    nightAccessCount++;
                }
            }
        }

        if (failedCount >= FAILED_LOGINS_THRESHOLD) {
            anomalies.push_back({"excessive_failed_logins", failedCount, "high"});
            logger_->warn("Anomaly: excessive failed logins, user_id={}, count={}",
                         userId, failedCount);
        }

        if (nightAccessCount > 3) {
            anomalies.push_back({"unusual_access_time", nightAccessCount, "medium"});
            logger_->warn("Anomaly: unusual access time, user_id={}, count={}",
                         userId, nightAccessCount);
        }

        return anomalies;
    }

    struct AuthLog {
        std::string userId;
        std::chrono::system_clock::time_point timestamp;
        bool success;
        std::string ipAddress;
    };
};

} // namespace iso27001
```

---

## Success Criteria

- [ ] Password policy enforced (12+ chars, complexity)
- [ ] Account lockout after 5 failed attempts
- [ ] Password expiration after 90 days
- [ ] Authentication anomalies detected
- [ ] Modern C++ patterns (RAII, smart pointers)

---

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
