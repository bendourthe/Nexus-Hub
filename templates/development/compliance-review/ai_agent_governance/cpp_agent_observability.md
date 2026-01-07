---
template_id: compliance_governance_agent_observability_cpp
template_name: AI Agent Observability - C++
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
  - compliance_frameworks/cpp_nist_ai_rmf.md
related_templates:
  - ai_agent_governance/cpp_agent_security.md
tools:
  - Prometheus C++ client
  - spdlog
tags:
  - observability
  - monitoring
  - audit-everything
  - four-pillars
  - cpp
---

# AI Agent Observability - C++

**🔍 Pillar 4: Observability (Audit Everything)**

Monitor AI agent behavior, decisions, and performance

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

**Audit Everything**: Complete visibility into AI agent operations

**Key Metrics**:
- Decision logging
- Performance monitoring
- Drift detection
- Audit trails

---

## Implementation

```cpp
#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <memory>
#include <chrono>
#include <cmath>
#include <spdlog/spdlog.h>
#include <boost/uuid/uuid.hpp>
#include <boost/uuid/uuid_generators.hpp>
#include <boost/uuid/uuid_io.hpp>

namespace ai {

struct AgentDecision {
    std::string decision_id;
    std::string agent_id;
    std::string request_id;
    std::chrono::system_clock::time_point timestamp;
    std::map<std::string, std::string> input;
    std::map<std::string, std::string> output;
    double confidence;
    std::string model_version;
};

struct DriftAlert {
    std::string alert_id;
    std::string agent_id;
    std::string alert_type;
    double drift_percentage;
    std::chrono::system_clock::time_point timestamp;
};

struct AgentMetrics {
    std::string agent_id;
    int total_requests;
    int average_latency_ms;
    double error_rate;
    double confidence_avg;
};

struct PerformanceLog {
    std::string log_id;
    std::string agent_id;
    std::string request_id;
    long latency_ms;
    bool success;
    std::chrono::system_clock::time_point timestamp;
};

class AgentObservabilityService {
private:
    std::shared_ptr<spdlog::logger> logger_;
    // std::shared_ptr<DecisionRepository> decision_repo_;
    // std::shared_ptr<AlertRepository> alert_repo_;

    std::string generate_uuid() const {
        boost::uuids::random_generator gen;
        boost::uuids::uuid id = gen();
        return boost::uuids::to_string(id);
    }

public:
    AgentObservabilityService(std::shared_ptr<spdlog::logger> logger)
        : logger_(logger) {}

    void log_decision(
        const std::string& agent_id,
        const std::string& request_id,
        const std::map<std::string, std::string>& input,
        const std::map<std::string, std::string>& output,
        double confidence)
    {
        AgentDecision decision;
        decision.decision_id = generate_uuid();
        decision.agent_id = agent_id;
        decision.request_id = request_id;
        decision.timestamp = std::chrono::system_clock::now();
        decision.input = input;
        decision.output = output;
        decision.confidence = confidence;
        decision.model_version = "1.0.0";

        // decision_repo_->save(decision);

        logger_->info(
            "Agent decision logged: agent_id={}, request_id={}, confidence={:.2f}",
            agent_id, request_id, confidence);
    }

    void detect_drift(
        const std::string& agent_id,
        double current_metric,
        double baseline_metric)
    {
        double drift_percentage = std::abs((current_metric - baseline_metric) / baseline_metric) * 100;

        if (drift_percentage > 10.0) {
            DriftAlert alert;
            alert.alert_id = generate_uuid();
            alert.agent_id = agent_id;
            alert.alert_type = "model_drift";
            alert.drift_percentage = drift_percentage;
            alert.timestamp = std::chrono::system_clock::now();

            // alert_repo_->save(alert);

            logger_->warn(
                "Model drift detected: agent_id={}, drift={:.2f}%",
                agent_id, drift_percentage);
        }
    }

    AgentMetrics get_agent_metrics(const std::string& agent_id) {
        AgentMetrics metrics;
        metrics.agent_id = agent_id;
        metrics.total_requests = 1000;
        metrics.average_latency_ms = 150;
        metrics.error_rate = 0.01;
        metrics.confidence_avg = 0.85;

        logger_->info("Agent metrics retrieved: agent_id={}", agent_id);

        return metrics;
    }

    void track_performance(
        const std::string& agent_id,
        const std::string& request_id,
        long latency_ms,
        bool success)
    {
        PerformanceLog perf_log;
        perf_log.log_id = generate_uuid();
        perf_log.agent_id = agent_id;
        perf_log.request_id = request_id;
        perf_log.latency_ms = latency_ms;
        perf_log.success = success;
        perf_log.timestamp = std::chrono::system_clock::now();

        // performance_repo_->save(perf_log);

        if (latency_ms > 1000) {
            logger_->warn(
                "High latency detected: agent_id={}, latency_ms={}",
                agent_id, latency_ms);
        }

        logger_->info(
            "Performance tracked: agent_id={}, request_id={}, latency_ms={}, success={}",
            agent_id, request_id, latency_ms, success);
    }

    void log_audit_event(
        const std::string& agent_id,
        const std::string& event_type,
        const std::string& user_id,
        const std::map<std::string, std::string>& event_data)
    {
        std::map<std::string, std::string> audit_event = {
            {"event_id", generate_uuid()},
            {"agent_id", agent_id},
            {"event_type", event_type},
            {"user_id", user_id}
        };

        // audit_repo_->save(audit_event);

        logger_->info(
            "Audit event logged: agent_id={}, event_type={}, user_id={}",
            agent_id, event_type, user_id);
    }

    double calculate_accuracy(
        const std::string& agent_id,
        const std::vector<double>& predictions,
        const std::vector<double>& actuals)
    {
        if (predictions.size() != actuals.size() || predictions.empty()) {
            return 0.0;
        }

        int correct = 0;
        for (size_t i = 0; i < predictions.size(); ++i) {
            if (std::abs(predictions[i] - actuals[i]) < 0.001) {
                ++correct;
            }
        }

        double accuracy = static_cast<double>(correct) / predictions.size();

        logger_->info(
            "Accuracy calculated: agent_id={}, accuracy={:.2f}, samples={}",
            agent_id, accuracy, predictions.size());

        return accuracy;
    }
};

} // namespace ai

// Example usage
int main() {
    auto logger = spdlog::stdout_color_mt("agent_observability");
    logger->set_level(spdlog::level::info);

    ai::AgentObservabilityService service(logger);

    std::string agent_id = "agent-123";
    std::string request_id = "req-456";

    // Log decision
    std::map<std::string, std::string> input = {
        {"transaction_amount", "1500"},
        {"merchant", "ACME Corp"}
    };
    std::map<std::string, std::string> output = {
        {"fraud_probability", "0.12"},
        {"decision", "approve"}
    };
    service.log_decision(agent_id, request_id, input, output, 0.88);

    // Track performance
    service.track_performance(agent_id, request_id, 145, true);

    // Detect drift
    service.detect_drift(agent_id, 0.75, 0.85);

    // Get metrics
    auto metrics = service.get_agent_metrics(agent_id);
    std::cout << "Total requests: " << metrics.total_requests << std::endl;
    std::cout << "Avg latency: " << metrics.average_latency_ms << " ms" << std::endl;
    std::cout << "Error rate: " << metrics.error_rate << std::endl;

    // Log audit event
    std::map<std::string, std::string> event_data = {
        {"version", "1.1.0"},
        {"change_type", "model_update"}
    };
    service.log_audit_event(agent_id, "model_update", "user789", event_data);

    // Calculate accuracy
    std::vector<double> predictions = {1.0, 0.0, 1.0, 1.0};
    std::vector<double> actuals = {1.0, 0.0, 1.0, 0.0};
    double accuracy = service.calculate_accuracy(agent_id, predictions, actuals);
    std::cout << "Accuracy: " << accuracy << std::endl;

    return 0;
}
```

---

## Success Criteria

- [ ] Decision logging operational
- [ ] Performance metrics tracked
- [ ] Drift detection functional
- [ ] Audit trails comprehensive

---

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
