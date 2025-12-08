---
template_id: compliance_governance_incident_response_cpp
template_name: Incident Response Plan - C++
version: 1.0.0
last_updated: 2025-12-05
language: cpp
category: compliance_governance
phase: incident_response
phase_number: 5
difficulty: intermediate
estimated_time_hours: 4-6
prerequisites:
  - compliance_frameworks/cpp_soc2_compliance.md
  - compliance_frameworks/cpp_iso27001_implementation.md
related_templates:
  - incident_response/cpp_breach_protocols.md
  - privacy_protection/cpp_gdpr_compliance.md
tools:
  - PagerDuty (alerting)
  - JIRA (incident tracking)
tags:
  - incident-response
  - security-incidents
  - cyber-incidents
  - cpp
---

# Incident Response Plan - C++

**6-phase incident response lifecycle implementation**

[← Back to Incident Response](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### Incident Response Lifecycle

**NIST SP 800-61**: 6-phase incident response process

1. **Preparation** - Tools, training, procedures
2. **Detection and Analysis** - Identify incidents
3. **Containment** - Stop spread
4. **Eradication** - Remove threat
5. **Recovery** - Restore operations
6. **Post-Incident** - Lessons learned

### Framework Requirements

**ISO 27001 Control 5.26**: Response to information security incidents
**SOC 2 CC7.4**: Respond to security incidents

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

enum class IncidentSeverity {
    P1Critical,  // System down, data breach
    P2High,      // Significant impact
    P3Medium,    // Moderate impact
    P4Low        // Minor issue
};

enum class IncidentStatus {
    Detected,
    Investigating,
    Contained,
    Eradicated,
    Recovered,
    Closed
};

std::string to_string(IncidentSeverity severity) {
    switch(severity) {
        case IncidentSeverity::P1Critical: return "p1_critical";
        case IncidentSeverity::P2High: return "p2_high";
        case IncidentSeverity::P3Medium: return "p3_medium";
        case IncidentSeverity::P4Low: return "p4_low";
        default: return "unknown";
    }
}

std::string to_string(IncidentStatus status) {
    switch(status) {
        case IncidentStatus::Detected: return "detected";
        case IncidentStatus::Investigating: return "investigating";
        case IncidentStatus::Contained: return "contained";
        case IncidentStatus::Eradicated: return "eradicated";
        case IncidentStatus::Recovered: return "recovered";
        case IncidentStatus::Closed: return "closed";
        default: return "unknown";
    }
}

class IncidentResponseService {
private:
    std::shared_ptr<spdlog::logger> logger_;

    static const std::map<IncidentSeverity, int> RESPONSE_SLA;

    std::string generate_uuid() const {
        boost::uuids::random_generator gen;
        boost::uuids::uuid id = gen();
        return boost::uuids::to_string(id);
    }

    void alert_response_team(const std::string& incident_id) {
        logger_->error("ALERT: Critical incident created - incident_id={}", incident_id);
    }

    void schedule_post_incident_review(const std::string& incident_id) {
        logger_->info("Post-incident review scheduled: incident_id={}", incident_id);
    }

public:
    IncidentResponseService(std::shared_ptr<spdlog::logger> logger)
        : logger_(logger) {}

    std::string create_incident(
        const std::string& title,
        const std::string& description,
        IncidentSeverity severity,
        const std::string& incident_type,
        const std::string& detected_by)
    {
        std::string incident_id = generate_uuid();
        auto response_deadline = std::chrono::system_clock::now() +
            std::chrono::minutes(RESPONSE_SLA.at(severity));

        std::map<std::string, std::string> incident = {
            {"incident_id", incident_id},
            {"title", title},
            {"description", description},
            {"severity", to_string(severity)},
            {"incident_type", incident_type},
            {"detected_by", detected_by},
            {"status", to_string(IncidentStatus::Detected)}
        };

        // incidentRepo_->save(incident);

        if (severity == IncidentSeverity::P1Critical ||
            severity == IncidentSeverity::P2High) {
            alert_response_team(incident_id);
        }

        logger_->error("Security incident created: incident_id={}, severity={}",
                      incident_id, to_string(severity));

        return incident_id;
    }

    void contain_incident(
        const std::string& incident_id,
        const std::vector<std::string>& containment_actions)
    {
        logger_->warn("Incident contained: incident_id={}, actions={}",
                     incident_id, containment_actions.size());
    }

    void eradicate_threat(
        const std::string& incident_id,
        const std::vector<std::string>& eradication_actions)
    {
        logger_->info("Threat eradicated: incident_id={}", incident_id);
    }

    void recover_systems(
        const std::string& incident_id,
        const std::vector<std::string>& recovery_actions)
    {
        logger_->info("Systems recovered: incident_id={}", incident_id);
    }

    void close_incident(
        const std::string& incident_id,
        const std::string& root_cause,
        const std::string& lessons_learned)
    {
        // Simulated incident for demonstration
        auto detected_time = std::chrono::system_clock::now() - std::chrono::hours(48);
        auto now = std::chrono::system_clock::now();

        auto duration = std::chrono::duration_cast<std::chrono::hours>(now - detected_time);
        double total_duration_hours = duration.count();

        std::map<std::string, std::string> post_mortem = {
            {"incident_id", incident_id},
            {"root_cause", root_cause},
            {"lessons_learned", lessons_learned},
            {"total_duration_hours", std::to_string(total_duration_hours)}
        };

        // postMortemRepo_->save(post_mortem);

        schedule_post_incident_review(incident_id);
        logger_->info("Incident closed: incident_id={}, duration_hours={}",
                     incident_id, total_duration_hours);
    }

    std::map<std::string, std::string> generate_incident_report(const std::string& incident_id) {
        // Simulated data for demonstration
        std::map<std::string, std::string> incident = {
            {"incident_id", incident_id},
            {"title", "Database breach detected"},
            {"severity", "p1_critical"},
            {"data_affected", "true"},
            {"users_affected_count", "5000"}
        };

        std::vector<std::string> systems_affected = {"database_server", "web_application"};
        std::vector<std::string> containment_actions = {"Revoked access", "Changed passwords"};
        std::vector<std::string> eradication_actions = {"Removed malware", "Patched vulnerability"};
        std::vector<std::string> recovery_actions = {"Restored from backup", "Verified integrity"};

        std::map<std::string, std::string> post_mortem = {
            {"root_cause", "Unpatched SQL injection vulnerability"},
            {"lessons_learned", "Implement automated patching, enhance monitoring"}
        };

        std::map<std::string, std::string> report = {
            {"incident_id", incident_id},
            {"title", incident["title"]},
            {"severity", incident["severity"]},
            {"data_affected", incident["data_affected"]},
            {"users_affected", incident["users_affected_count"]},
            {"root_cause", post_mortem["root_cause"]},
            {"lessons_learned", post_mortem["lessons_learned"]}
        };

        logger_->info("Incident report generated: incident_id={}", incident_id);

        return report;
    }

    std::map<std::string, std::string> conduct_post_incident_review(
        const std::string& incident_id,
        const std::string& root_cause,
        const std::vector<std::string>& lessons_learned,
        const std::vector<std::string>& corrective_actions)
    {
        std::map<std::string, std::string> review = {
            {"review_id", generate_uuid()},
            {"incident_id", incident_id},
            {"root_cause", root_cause}
        };

        logger_->info("Post-incident review completed: incident_id={}", incident_id);

        return review;
    }
};

const std::map<IncidentSeverity, int> IncidentResponseService::RESPONSE_SLA = {
    {IncidentSeverity::P1Critical, 15},
    {IncidentSeverity::P2High, 60},
    {IncidentSeverity::P3Medium, 240},
    {IncidentSeverity::P4Low, 1440}
};

} // namespace security

int main() {
    auto logger = spdlog::stdout_color_mt("incident_response");
    security::IncidentResponseService service(logger);

    std::string incident_id = service.create_incident(
        "Database breach detected",
        "Unauthorized access to customer database",
        security::IncidentSeverity::P1Critical,
        "data_breach",
        "security_team"
    );

    std::cout << "Incident created: " << incident_id << std::endl;

    service.contain_incident(incident_id, {"Revoked access", "Changed passwords"});
    service.eradicate_threat(incident_id, {"Removed malware", "Patched vulnerability"});
    service.recover_systems(incident_id, {"Restored from backup", "Verified integrity"});
    service.close_incident(incident_id,
                          "Unpatched SQL injection vulnerability",
                          "Implement automated patching, enhance monitoring");

    auto report = service.generate_incident_report(incident_id);
    std::cout << "Generated report for incident: " << report["incident_id"] << std::endl;
    std::cout << "Severity: " << report["severity"] << std::endl;
    std::cout << "Users affected: " << report["users_affected"] << std::endl;

    return 0;
}
```

---

## Success Criteria

- [ ] Incident response plan documented
- [ ] Response team identified and trained
- [ ] Incident detection mechanisms operational
- [ ] Escalation procedures defined
- [ ] Post-incident review process established

---

[← Back to Incident Response](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
