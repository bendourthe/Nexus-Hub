---
template_id: compliance_governance_agent_security_csharp
template_name: AI Agent Security - C#
version: 1.0.0
last_updated: 2025-12-05
language: csharp
category: compliance_governance
phase: ai_agent_governance
phase_number: 5
difficulty: advanced
estimated_time_hours: 4-6
prerequisites:
  - ai_agent_governance/csharp_agent_lifecycle.md
  - governance_policies/csharp_access_control.md
related_templates:
  - ai_agent_governance/csharp_agent_risk_controls.md
tools:
  - ASP.NET Core Security
tags:
  - security
  - least-privilege
  - four-pillars
  - csharp
---

# AI Agent Security - C#

**🔒 Pillar 3: Security (Least Privilege)**

Secure AI agents with least privilege and input validation

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

**Least Privilege**: AI agents get minimum permissions needed

**Security Controls**:
- Input validation
- Output sanitization
- Access control
- Prompt injection prevention

---

## Implementation

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Organization.AI
{
    public class AgentSecurityService
    {
        private readonly ILogger<AgentSecurityService> _logger;
        private const int MaxInputLength = 10000;
        private static readonly Regex InjectionPattern = new Regex(
            @"(ignore previous|disregard|system:|<script>)",
            RegexOptions.IgnoreCase | RegexOptions.Compiled);

        public AgentSecurityService(ILogger<AgentSecurityService> logger)
        {
            _logger = logger;
        }

        public string ValidateInput(string agentId, string userInput)
        {
            if (string.IsNullOrWhiteSpace(userInput))
            {
                throw new ArgumentException("Input cannot be empty");
            }

            if (userInput.Length > MaxInputLength)
            {
                _logger.LogWarning(
                    "Input too long: agent_id={AgentId}, length={Length}",
                    agentId, userInput.Length);
                throw new ArgumentException("Input exceeds maximum length");
            }

            var match = InjectionPattern.Match(userInput);
            if (match.Success)
            {
                _logger.LogWarning(
                    "Prompt injection detected: agent_id={AgentId}, pattern={Pattern}",
                    agentId, match.Value);
                throw new SecurityException("Potential prompt injection detected");
            }

            _logger.LogInformation(
                "Input validated: agent_id={AgentId}, input_length={Length}",
                agentId, userInput.Length);

            return userInput;
        }

        public string SanitizeOutput(string agentId, string agentOutput)
        {
            var sanitized = agentOutput;

            // Remove script tags
            sanitized = Regex.Replace(sanitized, @"<script.*?>.*?</script>", "", RegexOptions.IgnoreCase);

            // Remove javascript: protocol
            sanitized = sanitized.Replace("javascript:", "", StringComparison.OrdinalIgnoreCase);

            // Remove event handlers
            sanitized = Regex.Replace(sanitized, @"on\w+\s*=", "", RegexOptions.IgnoreCase);

            if (sanitized != agentOutput)
            {
                _logger.LogWarning("Output sanitized: agent_id={AgentId}", agentId);
            }

            return sanitized;
        }

        public bool CheckAgentPermission(string agentId, string resource, string action)
        {
            var requiredPermission = $"{resource}:{action}";

            var agentPermissions = GetAgentPermissions(agentId);
            var hasPermission = agentPermissions.Contains(requiredPermission);

            if (!hasPermission)
            {
                _logger.LogWarning(
                    "Permission denied: agent_id={AgentId}, resource={Resource}, action={Action}",
                    agentId, resource, action);
            }

            return hasPermission;
        }

        private List<string> GetAgentPermissions(string agentId)
        {
            // In production, query from database or policy service
            return new List<string>
            {
                "data:read",
                "api:call",
                "database:query"
            };
        }

        public async Task<bool> ValidateApiTokenAsync(string agentId, string token)
        {
            if (string.IsNullOrWhiteSpace(token))
            {
                _logger.LogWarning("Empty token provided: agent_id={AgentId}", agentId);
                return false;
            }

            // In production, validate JWT or API key
            var isValid = token.Length >= 32; // Simulated validation

            if (!isValid)
            {
                _logger.LogWarning(
                    "Invalid API token: agent_id={AgentId}",
                    agentId);
            }

            return await Task.FromResult(isValid);
        }

        public string EncryptSensitiveData(string agentId, string sensitiveData)
        {
            // In production, use proper encryption (AES-256)
            var encrypted = Convert.ToBase64String(
                System.Text.Encoding.UTF8.GetBytes(sensitiveData));

            _logger.LogInformation(
                "Sensitive data encrypted: agent_id={AgentId}",
                agentId);

            return encrypted;
        }

        public string DecryptSensitiveData(string agentId, string encryptedData)
        {
            // In production, use proper decryption
            var decrypted = System.Text.Encoding.UTF8.GetString(
                Convert.FromBase64String(encryptedData));

            _logger.LogInformation(
                "Sensitive data decrypted: agent_id={AgentId}",
                agentId);

            return decrypted;
        }
    }

    public class SecurityException : Exception
    {
        public SecurityException(string message) : base(message) { }
    }
}
```

---

## Success Criteria

- [ ] Input validation implemented
- [ ] Output sanitization operational
- [ ] Prompt injection prevention active
- [ ] Least privilege enforced

---

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
