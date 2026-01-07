---
template_id: compliance_governance_agent_risk_controls_cpp
template_name: AI Agent Risk Controls - C++
version: 1.0.0
last_updated: 2025-12-05
language: cpp
category: compliance_governance
phase: ai_agent_governance
phase_number: 5
difficulty: advanced
estimated_time_hours: 4-6
prerequisites:
  - ai_agent_governance/cpp_agent_lifecycle.md
  - risk_management/cpp_risk_assessment.md
related_templates:
  - ai_agent_governance/cpp_agent_security.md
tools:
  - Circuit Breaker pattern
tags:
  - risk-management
  - defense-in-depth
  - four-pillars
  - cpp
---

# AI Agent Risk Controls - C++

**⚠️ Pillar 2: Risk Management (Defense in Depth)**

Implement risk controls for AI agent operations

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

**Defense in Depth**: Multiple layers of risk controls

**Risk Controls**:
- Rate limiting
- Circuit breakers
- Confidence thresholds
- Human-in-the-loop

---

## Implementation

```cpp
#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <memory>
#include <chrono>
#include <algorithm>
#include <spdlog/spdlog.h>
#include <boost/uuid/uuid.hpp>
#include <boost/uuid/uuid_generators.hpp>
#include <boost/uuid/uuid_io.hpp>

namespace ai {

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

const double CONFIDENCE_THRESHOLD = 0.7;
const int RATE_LIMIT_PER_MINUTE = 60;

struct RiskAssessment {
    std::string agent_id;
    RiskLevel risk_level;
    bool requires_human_review;
    std::vector<std::string> risk_factors;
    double confidence;
};

struct CircuitBreaker {
    std::string agent_id;
    std::string status; // "open" or "closed"
    std::string reason;
    std::chrono::system_clock::time_point activated_at;
};

struct ThresholdResult {
    bool approved;
    std::string reason;
    bool requires_review;
    double confidence;
};

class AgentRiskControlsService {
private:
    std::shared_ptr<spdlog::logger> logger_;
    // std::shared_ptr<CircuitBreakerRepository> circuit_breaker_repo_;

    std::string generate_uuid() const {
        boost::uuids::random_generator gen;
        boost::uuids::uuid id = gen();
        return boost::uuids::to_string(id);
    }

    int get_request_count(const std::string& user_id) const {
        // In production, query last minute request count from cache/database
        return 45; // Simulated
    }

public:
    AgentRiskControlsService(std::shared_ptr<spdlog::logger> logger)
        : logger_(logger) {}

    bool check_rate_limit(const std::string& agent_id, const std::string& user_id) {
        int request_count = get_request_count(user_id);

        if (request_count >= RATE_LIMIT_PER_MINUTE) {
            logger_->warn("Rate limit exceeded: agent_id={}, user_id={}, count={}",
                         agent_id, user_id, request_count);
            return false;
        }

        return true;
    }

    RiskAssessment evaluate_decision_risk(
        const std::string& agent_id,
        const std::map<std::string, double>& decision,
        double confidence)
    {
        RiskAssessment assessment;
        assessment.agent_id = agent_id;
        assessment.risk_level = RiskLevel::Low;
        assessment.requires_human_review = false;
        assessment.confidence = confidence;

        // Check confidence threshold
        if (confidence < CONFIDENCE_THRESHOLD) {
            assessment.risk_level = RiskLevel::High;
            assessment.requires_human_review = true;
            assessment.risk_factors.push_back("Low confidence score");
        }

        // Check financial impact
        auto it = decision.find("financial_impact");
        if (it != decision.end() && it->second > 10000.0) {
            assessment.risk_level = RiskLevel::Critical;
            assessment.requires_human_review = true;
            assessment.risk_factors.push_back("High financial impact");
        }

        // Check PII access
        auto pii_it = decision.find("accesses_pii");
        if (pii_it != decision.end() && pii_it->second > 0) {
            if (assessment.risk_level == RiskLevel::Low) {
                assessment.risk_level = RiskLevel::Medium;
            }
            assessment.risk_factors.push_back("Accesses PII data");
        }

        if (assessment.requires_human_review) {
            logger_->warn("Decision requires human review: agent_id={}, risk_level={}",
                         agent_id, to_string(assessment.risk_level));
        }

        return assessment;
    }

    void enable_circuit_breaker(const std::string& agent_id, const std::string& reason) {
        CircuitBreaker cb;
        cb.agent_id = agent_id;
        cb.status = "open";
        cb.reason = reason;
        cb.activated_at = std::chrono::system_clock::now();

        // circuit_breaker_repo_->save(cb);

        logger_->error("Circuit breaker activated: agent_id={}, reason={}",
                      agent_id, reason);
    }

    bool check_circuit_breaker(const std::string& agent_id) {
        // In production, query circuit breaker state from repository
        // Return false if circuit is open (agent disabled), true if closed
        return true; // Simulated - circuit closed
    }

    ThresholdResult apply_confidence_threshold(
        const std::string& agent_id,
        double confidence,
        const std::map<std::string, double>& decision)
    {
        ThresholdResult result;

        if (confidence < CONFIDENCE_THRESHOLD) {
            logger_->warn("Confidence below threshold: agent_id={}, confidence={:.2f}, threshold={:.2f}",
                         agent_id, confidence, CONFIDENCE_THRESHOLD);

            result.approved = false;
            result.reason = "Confidence below threshold";
            result.requires_review = true;
            result.confidence = confidence;
            return result;
        }

        result.approved = true;
        result.reason = "";
        result.requires_review = false;
        result.confidence = confidence;
        return result;
    }

    bool requires_human_approval(
        const std::string& agent_id,
        const std::string& action_type)
    {
        static const std::vector<std::string> high_risk_actions = {
            "delete",
            "transfer_funds",
            "modify_permissions"
        };

        bool requires_approval = std::find(
            high_risk_actions.begin(),
            high_risk_actions.end(),
            action_type
        ) != high_risk_actions.end();

        if (requires_approval) {
            logger_->warn("High-risk action requires approval: agent_id={}, action_type={}",
                         agent_id, action_type);
        }

        return requires_approval;
    }

    void log_risk_decision(
        const std::string& agent_id,
        const RiskAssessment& assessment,
        bool approved)
    {
        std::string log_id = generate_uuid();

        // In production, save to risk decision repository

        logger_->info("Risk decision logged: agent_id={}, approved={}",
                     agent_id, approved);
    }
};

} // namespace ai

// Example usage
int main() {
    auto logger = spdlog::stdout_color_mt("agent_risk_controls");
    logger->set_level(spdlog::level::info);

    ai::AgentRiskControlsService service(logger);

    std::string agent_id = "agent-123";
    std::string user_id = "user-456";

    // Check rate limit
    bool within_limit = service.check_rate_limit(agent_id, user_id);
    std::cout << "Within rate limit: " << within_limit << std::endl;

    // Evaluate decision risk
    std::map<std::string, double> decision = {
        {"financial_impact", 15000.0},
        {"accesses_pii", 1.0}
    };
    auto assessment = service.evaluate_decision_risk(agent_id, decision, 0.65);
    std::cout << "Risk level: " << to_string(assessment.risk_level) << std::endl;
    std::cout << "Requires human review: " << assessment.requires_human_review << std::endl;
    std::cout << "Risk factors:" << std::endl;
    for (const auto& factor : assessment.risk_factors) {
        std::cout << "  - " << factor << std::endl;
    }

    // Apply confidence threshold
    auto threshold_result = service.apply_confidence_threshold(agent_id, 0.65, decision);
    std::cout << "Approved: " << threshold_result.approved << std::endl;
    if (!threshold_result.approved) {
        std::cout << "Reason: " << threshold_result.reason << std::endl;
    }

    // Check if action requires approval
    bool requires_approval = service.requires_human_approval(agent_id, "transfer_funds");
    std::cout << "Requires approval for transfer_funds: " << requires_approval << std::endl;

    requires_approval = service.requires_human_approval(agent_id, "read_data");
    std::cout << "Requires approval for read_data: " << requires_approval << std::endl;

    // Enable circuit breaker
    service.enable_circuit_breaker(agent_id, "Error rate exceeds threshold");

    // Check circuit breaker
    bool circuit_closed = service.check_circuit_breaker(agent_id);
    std::cout << "Circuit breaker closed: " << circuit_closed << std::endl;

    // Log risk decision
    service.log_risk_decision(agent_id, assessment, false);

    return 0;
}
```

---

## Success Criteria

- [ ] Rate limiting operational
- [ ] Confidence thresholds enforced
- [ ] Human-in-the-loop triggers functional
- [ ] Circuit breakers implemented

---

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
