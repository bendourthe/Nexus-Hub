---
template_id: compliance_governance_gdpr_cpp
template_name: GDPR Compliance - C++
version: 1.0.0
last_updated: 2025-12-05
language: cpp
category: compliance_governance
phase: privacy_protection
phase_number: 4
difficulty: advanced
estimated_time_hours: 6-8
prerequisites:
  - privacy_protection/README.md
related_templates:
  - compliance_frameworks/cpp_iso27001_implementation.md
tools:
  - spdlog (logging)
tags:
  - gdpr
  - privacy
  - data-protection
  - cpp
  - modern-cpp
---

# GDPR Compliance - C++

**General Data Protection Regulation for Modern C++ applications**

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Right to Access & Erasure

```cpp
#include <spdlog/spdlog.h>
#include <string>
#include <vector>
#include <map>
#include <memory>
#include <chrono>

namespace gdpr {

class DataSubjectAccessHandler {
private:
    std::shared_ptr<spdlog::logger> logger_;
    static constexpr int RESPONSE_DEADLINE_DAYS = 30;

public:
    struct DataSubjectReport {
        std::string requestId;
        std::string dataSubjectId;
        std::chrono::system_clock::time_point requestDate;
        std::chrono::system_clock::time_point responseDeadline;
        std::map<std::string, std::string> personalData;
        std::vector<std::string> processingPurposes;
        std::vector<std::string> recipients;
        std::string retentionPeriod;
    };

    explicit DataSubjectAccessHandler(std::shared_ptr<spdlog::logger> logger)
        : logger_(std::move(logger)) {}

    DataSubjectReport processAccessRequest(const std::string& dataSubjectId) {
        auto now = std::chrono::system_clock::now();
        auto deadline = now + std::chrono::hours(24 * RESPONSE_DEADLINE_DAYS);

        DataSubjectReport report;
        report.requestId = "GDPR-" + std::to_string(
            std::chrono::system_clock::now().time_since_epoch().count());
        report.dataSubjectId = dataSubjectId;
        report.requestDate = now;
        report.responseDeadline = deadline;
        report.personalData = {
            {"profile", "name: User, email: user@example.com"},
            {"transactions", "[]"}
        };
        report.processingPurposes = {
            "Providing services",
            "Improving user experience"
        };
        report.recipients = {
            "Cloud service providers",
            "Payment processors"
        };
        report.retentionPeriod = "7 years for financial records";

        logger_->info("GDPR access request processed: request_id={}, data_subject_id={}",
                     report.requestId, dataSubjectId);

        return report;
    }
};

class DataErasureHandler {
private:
    std::shared_ptr<spdlog::logger> logger_;

public:
    struct ErasureResult {
        std::string status;
        std::string requestId;
        std::string reason;
        std::vector<std::string> exceptions;
        std::optional<std::chrono::system_clock::time_point> erasureDate;
    };

    explicit DataErasureHandler(std::shared_ptr<spdlog::logger> logger)
        : logger_(std::move(logger)) {}

    ErasureResult processErasureRequest(const std::string& dataSubjectId,
                                       const std::string& justification) {
        auto requestId = "ERASE-" + std::to_string(
            std::chrono::system_clock::now().time_since_epoch().count());

        auto exceptions = checkErasureExceptions(dataSubjectId);

        if (!exceptions.empty()) {
            logger_->warn("Erasure denied: request_id={}, exception_count={}",
                         requestId, exceptions.size());

            return ErasureResult{
                "Denied",
                requestId,
                "Legal obligations require data retention",
                exceptions,
                std::nullopt
            };
        }

        erasePersonalData(dataSubjectId, requestId);

        logger_->warn("Personal data erased: request_id={}, data_subject_id={}",
                     requestId, dataSubjectId);

        return ErasureResult{
            "Completed",
            requestId,
            "",
            {},
            std::chrono::system_clock::now()
        };
    }

private:
    std::vector<std::string> checkErasureExceptions(const std::string& dataSubjectId) {
        std::vector<std::string> exceptions;

        if (hasLegalRetentionObligation(dataSubjectId)) {
            exceptions.push_back("Legal retention obligation (7 years)");
        }

        return exceptions;
    }

    bool hasLegalRetentionObligation(const std::string& dataSubjectId) {
        return false; // Check for financial records
    }

    void erasePersonalData(const std::string& dataSubjectId, const std::string& requestId) {
        logger_->warn("Data erasure executed: data_subject_id={}, request_id={}",
                     dataSubjectId, requestId);
    }
};

class ConsentManager {
private:
    std::shared_ptr<spdlog::logger> logger_;

public:
    explicit ConsentManager(std::shared_ptr<spdlog::logger> logger)
        : logger_(std::move(logger)) {}

    std::string recordConsent(const std::string& dataSubjectId,
                             const std::string& purpose,
                             bool consentGiven,
                             const std::string& consentText) {
        auto consentId = "CONSENT-" + std::to_string(
            std::chrono::system_clock::now().time_since_epoch().count());

        logger_->info("Consent recorded: consent_id={}, purpose={}, given={}",
                     consentId, purpose, consentGiven);

        return consentId;
    }

    void withdrawConsent(const std::string& dataSubjectId, const std::string& consentId) {
        logger_->warn("Consent withdrawn: data_subject_id={}, consent_id={}",
                     dataSubjectId, consentId);
    }
};

} // namespace gdpr
```

---

## Success Criteria

- [ ] Access requests processed within 30 days
- [ ] Erasure honored with exception handling
- [ ] Consent management with withdrawal
- [ ] Modern C++ patterns (RAII, smart pointers, std::optional)

---

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
