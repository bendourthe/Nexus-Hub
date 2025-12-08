---
template_id: compliance_governance_ccpa_cpp
template_name: CCPA Compliance - C++
version: 1.0.0
last_updated: 2025-12-05
language: cpp
category: compliance_governance
phase: privacy_protection
phase_number: 4
difficulty: advanced
estimated_time_hours: 4-6
prerequisites:
  - privacy_protection/README.md
related_templates:
  - compliance_frameworks/cpp_gdpr_compliance.md
tools:
  - spdlog (logging)
tags:
  - ccpa
  - privacy
  - california
  - cpp
  - modern-cpp
---

# CCPA Compliance - C++

**California Consumer Privacy Act for Modern C++ applications**

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

**5 Key Consumer Rights**: Right to Know, Right to Delete, Right to Opt-Out, Right to Non-Discrimination, Right to Correct

**Response Deadline**: 45 days

---

## Right to Know (CCPA §1798.100)

```cpp
#include <spdlog/spdlog.h>
#include <string>
#include <vector>
#include <map>
#include <memory>
#include <chrono>
#include <optional>

namespace ccpa {

class CCPADataDisclosureService {
private:
    std::shared_ptr<spdlog::logger> logger_;
    static constexpr int RESPONSE_DEADLINE_DAYS = 45;

public:
    struct DisclosureResponse {
        std::string requestId;
        std::string consumerId;
        std::chrono::system_clock::time_point requestDate;
        std::chrono::system_clock::time_point responseDeadline;
        std::vector<std::string> categoriesCollected;
        std::vector<std::string> businessPurposes;
        std::vector<std::string> thirdParties;
        std::map<std::string, std::string> specificPieces;
        std::string saleDisclosure;
        std::string sharingDisclosure;
    };

    explicit CCPADataDisclosureService(std::shared_ptr<spdlog::logger> logger)
        : logger_(std::move(logger)) {}

    DisclosureResponse processRightToKnow(const std::string& consumerId) {
        auto now = std::chrono::system_clock::now();
        auto deadline = now + std::chrono::hours(24 * RESPONSE_DEADLINE_DAYS);

        DisclosureResponse response;
        response.requestId = "CCPA-" + std::to_string(
            std::chrono::system_clock::now().time_since_epoch().count());
        response.consumerId = consumerId;
        response.requestDate = now;
        response.responseDeadline = deadline;

        // Categories of personal information collected
        response.categoriesCollected = {
            "Identifiers (name, email, IP address)",
            "Commercial information (purchase history, browsing history)",
            "Internet or network activity (cookies, logs)",
            "Geolocation data (approximate location from IP)",
            "Inferences (preferences, characteristics)"
        };

        // Business purposes
        response.businessPurposes = {
            "Providing and improving services",
            "Customer support and communication",
            "Security and fraud prevention",
            "Legal compliance",
            "Marketing (with explicit consent)"
        };

        // Third parties
        response.thirdParties = {
            "Service providers: AWS (hosting), Stripe (payments)",
            "Analytics providers: Google Analytics (with anonymization)",
            "Security providers: Cloudflare (DDoS protection)"
        };

        // Specific pieces of personal information
        response.specificPieces = {
            {"profile", "{\"name\": \"User\", \"email\": \"user@example.com\"}"},
            {"account_created", "2023-01-15"},
            {"last_login", "2025-12-05"},
            {"orders", "[]"}
        };

        response.saleDisclosure = "We do not sell personal information";
        response.sharingDisclosure = "We share data only with service providers under contract";

        logger_->info("CCPA right to know processed: request_id={}, consumer_id={}",
                     response.requestId, consumerId);

        return response;
    }
};

} // namespace ccpa
```

---

## Right to Delete (CCPA §1798.105)

```cpp
namespace ccpa {

class CCPADeletionService {
private:
    std::shared_ptr<spdlog::logger> logger_;

public:
    struct DeletionResult {
        std::string status;
        std::string requestId;
        std::string reason;
        std::vector<std::string> exceptions;
        std::optional<std::chrono::system_clock::time_point> deletionDate;
    };

    explicit CCPADeletionService(std::shared_ptr<spdlog::logger> logger)
        : logger_(std::move(logger)) {}

    DeletionResult processRightToDelete(
        const std::string& consumerId,
        const std::string& verificationMethod) {

        auto requestId = "ERASE-" + std::to_string(
            std::chrono::system_clock::now().time_since_epoch().count());

        // Verify consumer identity (2-factor for sensitive data)
        if (!verifyConsumerIdentity(consumerId, verificationMethod)) {
            logger_->warn("Deletion verification failed: request_id={}", requestId);

            return DeletionResult{
                "Verification Failed",
                requestId,
                "Unable to verify consumer identity",
                {},
                std::nullopt
            };
        }

        // Check for deletion exceptions (§1798.105(d))
        auto exceptions = checkDeletionExceptions(consumerId);

        if (!exceptions.empty()) {
            logger_->warn("Deletion denied: request_id={}, exception_count={}",
                         requestId, exceptions.size());

            return DeletionResult{
                "Denied",
                requestId,
                "Legal obligations require data retention",
                exceptions,
                std::nullopt
            };
        }

        // Perform deletion
        deleteConsumerData(consumerId, requestId);

        logger_->warn("Consumer data deleted: request_id={}, consumer_id={}",
                     requestId, consumerId);

        return DeletionResult{
            "Completed",
            requestId,
            "",
            {},
            std::chrono::system_clock::now()
        };
    }

private:
    bool verifyConsumerIdentity(
        const std::string& consumerId,
        const std::string& method) {
        // Implement 2-factor verification for sensitive data
        return true;
    }

    std::vector<std::string> checkDeletionExceptions(const std::string& consumerId) {
        std::vector<std::string> exceptions;

        // §1798.105(d)(1): Complete transaction
        if (hasActiveOrders(consumerId)) {
            exceptions.push_back("Active orders pending completion");
        }

        // §1798.105(d)(2): Security incidents, fraud, illegal activity
        if (hasOngoingSecurityInvestigation(consumerId)) {
            exceptions.push_back("Ongoing security incident investigation");
        }

        // §1798.105(d)(5): Internal uses (legal obligations)
        if (hasRecentFinancialRecords(consumerId)) {
            exceptions.push_back("Tax and accounting retention requirement (7 years)");
        }

        // §1798.105(d)(7): Comply with legal obligation
        if (hasLegalHold(consumerId)) {
            exceptions.push_back("Legal hold or pending litigation");
        }

        return exceptions;
    }

    bool hasActiveOrders(const std::string& consumerId) {
        return false; // Check database
    }

    bool hasOngoingSecurityInvestigation(const std::string& consumerId) {
        return false;
    }

    bool hasRecentFinancialRecords(const std::string& consumerId) {
        // Check for financial records within 7-year retention period
        return false;
    }

    bool hasLegalHold(const std::string& consumerId) {
        return false;
    }

    void deleteConsumerData(const std::string& consumerId, const std::string& requestId) {
        // Delete from all systems:
        // - User profile
        // - Preferences
        // - Analytics data
        // - Cookies and tracking data
        //
        // Pseudonymize transaction data (retain for legal compliance)

        logger_->warn("Data deletion executed: consumer_id={}, request_id={}",
                     consumerId, requestId);
    }
};

} // namespace ccpa
```

---

## Right to Opt-Out of Sale (CCPA §1798.120)

```cpp
namespace ccpa {

class CCPAOptOutService {
private:
    std::shared_ptr<spdlog::logger> logger_;

public:
    struct OptOutResult {
        std::string status;
        std::string optOutId;
        std::chrono::system_clock::time_point optOutDate;
        std::string message;
    };

    explicit CCPAOptOutService(std::shared_ptr<spdlog::logger> logger)
        : logger_(std::move(logger)) {}

    OptOutResult processOptOut(const std::string& consumerId) {
        auto optOutId = "OPT-OUT-" + std::to_string(
            std::chrono::system_clock::now().time_since_epoch().count());

        // Update consumer preferences
        updateOptOutPreference(consumerId, true);

        // Notify third parties (if any data sharing for monetary consideration)
        notifyThirdParties(consumerId);

        logger_->info("Consumer opted out: opt_out_id={}, consumer_id={}",
                     optOutId, consumerId);

        return OptOutResult{
            "Completed",
            optOutId,
            std::chrono::system_clock::now(),
            "Your opt-out preference has been recorded. "
            "We will not sell your personal information."
        };
    }

    OptOutResult processOptIn(
        const std::string& consumerId,
        const std::string& affirmativeConsentText) {

        auto optInId = "OPT-IN-" + std::to_string(
            std::chrono::system_clock::now().time_since_epoch().count());

        // Record affirmative consent
        recordAffirmativeConsent(consumerId, affirmativeConsentText);

        // Update consumer preferences
        updateOptOutPreference(consumerId, false);

        logger_->info("Consumer opted in: opt_in_id={}, consumer_id={}",
                     optInId, consumerId);

        return OptOutResult{
            "Completed",
            optInId,
            std::chrono::system_clock::now(),
            "Your consent has been recorded."
        };
    }

private:
    void updateOptOutPreference(const std::string& consumerId, bool optedOut) {
        // Update database
    }

    void notifyThirdParties(const std::string& consumerId) {
        // Notify any third parties about opt-out status
    }

    void recordAffirmativeConsent(
        const std::string& consumerId,
        const std::string& consentText) {
        // Store consent with timestamp for audit
    }
};

} // namespace ccpa
```

---

## Right to Non-Discrimination (CCPA §1798.125)

```cpp
namespace ccpa {

class NonDiscriminationEnforcement {
private:
    std::shared_ptr<spdlog::logger> logger_;

public:
    struct ServiceAccessResult {
        bool accessGranted;
        std::string serviceLevel;
        std::string pricing;
        std::string message;
    };

    explicit NonDiscriminationEnforcement(std::shared_ptr<spdlog::logger> logger)
        : logger_(std::move(logger)) {}

    ServiceAccessResult validateServiceAccess(
        const std::string& consumerId,
        const std::string& serviceType) {

        // Check if consumer has exercised CCPA rights
        auto ccpaRequests = getCCPARequestHistory(consumerId);

        if (!ccpaRequests.empty()) {
            logger_->info(
                "Consumer with CCPA requests accessing service: "
                "consumer_id={}, service_type={}, request_count={}",
                consumerId, serviceType, ccpaRequests.size());
        }

        // CRITICAL: Must provide same service regardless of CCPA activity
        return ServiceAccessResult{
            true,
            "Standard",
            "Standard",
            "Full access granted"
        };
    }

private:
    std::vector<std::string> getCCPARequestHistory(const std::string& consumerId) {
        return {};
    }
};

} // namespace ccpa
```

---

## Success Criteria

- [ ] Right to Know requests processed within 45 days
- [ ] Right to Delete honored with exception handling (§1798.105(d))
- [ ] "Do Not Sell" link prominently displayed on homepage
- [ ] Opt-out mechanism operational and immediate
- [ ] Non-discrimination enforced (same pricing, service level)
- [ ] 2-factor verification for sensitive data deletion
- [ ] Third-party notification system for opt-outs
- [ ] Modern C++ patterns (RAII, smart pointers, std::optional)

---

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
