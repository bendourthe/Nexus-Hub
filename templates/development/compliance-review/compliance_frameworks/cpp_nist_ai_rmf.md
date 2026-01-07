---
template_id: compliance_governance_nist_ai_rmf_cpp
template_name: NIST AI RMF - C++
version: 1.0.0
last_updated: 2025-12-05
language: cpp
category: compliance_governance
phase: compliance_frameworks
phase_number: 1
difficulty: advanced
estimated_time_hours: 8-10
prerequisites:
  - compliance_frameworks/cpp_iso27001_implementation.md
related_templates:
  - ai_agent_governance/cpp_agent_risk_controls.md
tools:
  - spdlog (logging)
tags:
  - nist-ai-rmf
  - ai-governance
  - responsible-ai
  - cpp
  - modern-cpp
---

# NIST AI Risk Management Framework - C++

**NIST AI RMF 1.0 for Modern C++ applications**

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## GOVERN-1: AI System Inventory

```cpp
#include <spdlog/spdlog.h>
#include <string>
#include <memory>
#include <chrono>
#include <vector>
#include <algorithm>
#include <cmath>

namespace nist {

enum class AISystemType {
    TraditionalML,
    GenerativeAI,
    RecommendationSystem
};

enum class RiskLevel {
    Low,
    Medium,
    High,
    Critical
};

class AISystemRegistry {
private:
    std::shared_ptr<spdlog::logger> logger_;

public:
    explicit AISystemRegistry(std::shared_ptr<spdlog::logger> logger)
        : logger_(std::move(logger)) {}

    std::string registerAISystem(
        const std::string& systemName,
        AISystemType systemType,
        const std::string& useCase,
        bool isGenerative) {

        auto systemId = std::to_string(
            std::chrono::system_clock::now().time_since_epoch().count());

        logger_->info("AI system registered: system_id={}, type={}, is_generative={}",
                     systemId, static_cast<int>(systemType), isGenerative);

        return systemId;
    }
};

class BiasDetector {
private:
    std::shared_ptr<spdlog::logger> logger_;
    static constexpr double BIAS_THRESHOLD = 0.1;

public:
    struct BiasMetrics {
        bool biasDetected = false;
        std::map<std::string, double> demographicParityDifferences;
    };

    explicit BiasDetector(std::shared_ptr<spdlog::logger> logger)
        : logger_(std::move(logger)) {}

    BiasMetrics detectBias(
        const std::string& systemId,
        const std::vector<double>& predictions,
        const std::map<std::string, std::vector<std::string>>& sensitiveFeatures) {

        BiasMetrics metrics;

        for (const auto& [featureName, featureValues] : sensitiveFeatures) {
            auto uniqueGroups = getUniqueGroups(featureValues);
            std::map<std::string, double> groupRates;

            for (const auto& group : uniqueGroups) {
                groupRates[group] = calculatePositiveRate(predictions, featureValues, group);
            }

            auto [maxRate, minRate] = getMinMax(groupRates);
            double dpDiff = maxRate - minRate;

            metrics.demographicParityDifferences[featureName] = dpDiff;

            if (std::abs(dpDiff) > BIAS_THRESHOLD) {
                metrics.biasDetected = true;
                logger_->warn("Bias detected: system_id={}, feature={}, dp_diff={:.3f}",
                            systemId, featureName, dpDiff);
            }
        }

        return metrics;
    }

private:
    std::vector<std::string> getUniqueGroups(const std::vector<std::string>& values) {
        std::vector<std::string> unique = values;
        std::sort(unique.begin(), unique.end());
        unique.erase(std::unique(unique.begin(), unique.end()), unique.end());
        return unique;
    }

    double calculatePositiveRate(const std::vector<double>& predictions,
                                 const std::vector<std::string>& features,
                                 const std::string& group) {
        double sum = 0.0;
        int count = 0;

        for (size_t i = 0; i < features.size() && i < predictions.size(); ++i) {
            if (features[i] == group) {
                sum += predictions[i];
                count++;
            }
        }

        return count > 0 ? sum / count : 0.0;
    }

    std::pair<double, double> getMinMax(const std::map<std::string, double>& rates) {
        if (rates.empty()) return {0.0, 0.0};

        auto first = rates.begin()->second;
        double maxVal = first, minVal = first;

        for (const auto& [_, rate] : rates) {
            maxVal = std::max(maxVal, rate);
            minVal = std::min(minVal, rate);
        }

        return {maxVal, minVal};
    }
};

} // namespace nist
```

---

## Success Criteria

- [ ] AI systems registered with unique IDs
- [ ] Bias detection operational
- [ ] Demographic parity differences < 0.1
- [ ] Modern C++ patterns used (smart pointers, RAII)

---

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
