---
template_id: compliance_governance_breach_protocols_cpp
template_name: Breach Protocols - C++
version: 1.0.0
last_updated: 2025-12-05
language: cpp
category: compliance_governance
phase: incident_response
phase_number: 5
difficulty: advanced
estimated_time_hours: 4-6
prerequisites:
  - incident_response/cpp_incident_response_plan.md
  - privacy_protection/cpp_gdpr_compliance.md
related_templates:
  - compliance_frameworks/cpp_soc2_compliance.md
tools:
  - Forensics tools
tags:
  - data-breach
  - breach-notification
  - gdpr
  - ccpa
  - cpp
---

# Breach Protocols - C++

**Data breach notification and response protocols (GDPR 72-hour rule)**

[← Back to Incident Response](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### Data Breach Notification Requirements

**GDPR Article 33**: Notify supervisory authority within 72 hours
**GDPR Article 34**: Notify individuals if high risk
**CCPA**: No specific timeline, but must notify "without unreasonable delay"
**State Laws**: Varies (CA requires notification without unreasonable delay)

---

## Implementation

```cpp
#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <memory>
#include <chrono>
#include <spdlog/spdlog.h>
#include <boost/uuid/uuid.hpp>
#include <boost/uuid/uuid_generators.hpp>
#include <boost/uuid/uuid_io.hpp>

namespace security {

const int GDPR_NOTIFICATION_DEADLINE_HOURS = 72;

enum class RiskLevel {
    Low,
    Medium,
    High,
    Critical
};

std::string to_string(RiskLevel level) {
    switch(level) {
        case RiskLevel::Low: return "low";
        case RiskLevel::Medium: return "medium";
        case RiskLevel::High: return "high";
        case RiskLevel::Critical: return "critical";
        default: return "unknown";
    }
}

class BreachNotificationService {
private:
    std::shared_ptr<spdlog::logger> logger_;

    std::string generate_uuid() const {
        boost::uuids::random_generator gen;
        boost::uuids::uuid id = gen();
        return boost::uuids::to_string(id);
    }

    RiskLevel assess_risk_level(int users_affected) const {
        if (users_affected > 10000) return RiskLevel::Critical;
        if (users_affected > 1000) return RiskLevel::High;
        if (users_affected > 100) return RiskLevel::Medium;
        return RiskLevel::Low;
    }

    void send_to_authority(const std::map<std::string, std::string>& notification) {
        logger_->info("Sending notification to GDPR supervisory authority");
    }

public:
    BreachNotificationService(std::shared_ptr<spdlog::logger> logger)
        : logger_(logger) {}

    std::map<std::string, std::string> assess_breach(const std::string& incident_id) {
        // Simulated incident data
        bool data_affected = true;
        int users_affected_count = 5000;
        bool ca_residents_affected = true;

        if (!data_affected) {
            return {{"is_breach", "false"}};
        }

        RiskLevel risk_level = assess_risk_level(users_affected_count);
        std::string breach_id = generate_uuid();
        auto gdpr_deadline = std::chrono::system_clock::now() +
            std::chrono::hours(GDPR_NOTIFICATION_DEADLINE_HOURS);

        std::map<std::string, std::string> breach_assessment = {
            {"is_breach", "true"},
            {"breach_id", breach_id},
            {"incident_id", incident_id},
            {"risk_level", to_string(risk_level)},
            {"notify_gdpr_authority",
             (risk_level == RiskLevel::Medium ||
              risk_level == RiskLevel::High ||
              risk_level == RiskLevel::Critical) ? "true" : "false"},
            {"notify_individuals",
             (risk_level == RiskLevel::High ||
              risk_level == RiskLevel::Critical) ? "true" : "false"},
            {"notify_ccpa", ca_residents_affected ? "true" : "false"}
        };

        logger_->error("Data breach assessed: breach_id={}, risk_level={}",
                      breach_id, to_string(risk_level));

        return breach_assessment;
    }

    std::string notify_gdpr_authority(const std::string& breach_id) {
        std::string notification_id = generate_uuid();

        std::map<std::string, std::string> notification = {
            {"notification_id", notification_id},
            {"breach_id", breach_id},
            {"notification_type", "gdpr_authority"},
            {"nature_of_breach", "Unauthorized access to customer database"},
            {"dpo_contact", "dpo@company.com"},
            {"likely_consequences", "Risk of identity theft for affected individuals"},
            {"measures_taken", "Database access revoked, passwords reset, monitoring enhanced"}
        };

        send_to_authority(notification);

        logger_->error("GDPR authority notified: notification_id={}", notification_id);

        return notification_id;
    }

    int notify_individuals(const std::string& breach_id) {
        int affected_count = 5000; // Simulated

        std::string notification_content = R"(
Subject: Important Security Notice

We are writing to inform you of a data security incident.

What Happened: Unauthorized access to customer database
What Information Was Involved: Names, email addresses, account numbers
What We Are Doing: Enhanced security measures, password resets, monitoring
What You Can Do: Update your password, enable 2FA, monitor accounts

Contact: security@company.com
)";

        logger_->error("Individuals notified: breach_id={}, count={}",
                      breach_id, affected_count);

        return affected_count;
    }

    void notify_ccpa(const std::string& breach_id) {
        logger_->info("CCPA notification initiated: breach_id={}", breach_id);
    }

    std::map<std::string, std::string> generate_breach_report(const std::string& breach_id) {
        std::map<std::string, std::string> report = {
            {"report_id", generate_uuid()},
            {"breach_id", breach_id},
            {"executive_summary", "Summary of breach incident"},
            {"timeline", "Detailed timeline of events"},
            {"impact_analysis", "Analysis of affected systems and data"},
            {"response_actions", "Actions taken to contain and remediate"},
            {"lessons_learned", "Key takeaways and improvements"}
        };

        logger_->info("Breach report generated: breach_id={}", breach_id);

        return report;
    }
};

} // namespace security

int main() {
    auto logger = spdlog::stdout_color_mt("breach_protocols");
    security::BreachNotificationService service(logger);

    std::string incident_id = "incident-123";
    auto assessment = service.assess_breach(incident_id);

    std::cout << "Breach ID: " << assessment["breach_id"] << std::endl;
    std::cout << "Risk Level: " << assessment["risk_level"] << std::endl;

    if (assessment["notify_gdpr_authority"] == "true") {
        std::string notification_id = service.notify_gdpr_authority(assessment["breach_id"]);
        std::cout << "GDPR Notification ID: " << notification_id << std::endl;
    }

    if (assessment["notify_individuals"] == "true") {
        int count = service.notify_individuals(assessment["breach_id"]);
        std::cout << "Individuals notified: " << count << std::endl;
    }

    auto report = service.generate_breach_report(assessment["breach_id"]);
    std::cout << "Breach Report ID: " << report["report_id"] << std::endl;

    return 0;
}
```

---

## Success Criteria

- [ ] Breach detection mechanisms operational
- [ ] 72-hour notification workflow implemented
- [ ] Notification templates ready
- [ ] Authority contacts established
- [ ] Breach simulation conducted

---

[← Back to Incident Response](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
