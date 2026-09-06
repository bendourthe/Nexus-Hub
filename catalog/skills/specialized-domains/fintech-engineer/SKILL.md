---
name: fintech-engineer
description: Financial technology engineering expertise for building secure, compliant payment and banking systems. Use when implementing payment processing, designing ledger systems, building trading platforms, ensuring PCI-DSS compliance in code, implementing fraud detection pipelines, or working with financial APIs and protocols.
summary_l0: "Build secure fintech systems with payment processing, ledgers, and fraud detection"
overview_l1: "This skill provides financial technology engineering expertise for building secure, compliant payment and banking systems. Use it when implementing payment processing, designing ledger systems, building trading platforms, ensuring PCI-DSS compliance in code, implementing fraud detection pipelines, or working with financial APIs and protocols. Key capabilities include payment processing implementation (Stripe, Adyen, payment gateway integration), double-entry ledger system design, trading platform architecture, PCI-DSS compliance in application code, fraud detection pipeline implementation, financial API integration (banking APIs, market data feeds), money handling patterns (decimal precision, currency conversion), and regulatory compliance (KYC/AML). The expected output is secure, compliant fintech code with proper money handling, audit trails, and regulatory compliance. Trigger phrases: fintech, payment processing, ledger system, trading platform, PCI-DSS code, fraud detection, financial API, banking system, payment gateway, KYC/AML."
---

# Fintech Engineer

Structured guidance for building financial technology systems that are correct, auditable, and compliant. Covers double-entry accounting, payment processing, money handling, regulatory compliance, fraud detection, financial API design, and testing strategies specific to financial software.

## When to Use This Skill

Use this skill for:

- Designing or implementing a double-entry ledger or accounting system
- Building payment processing flows with Stripe, Adyen, or other gateways
- Handling money and multi-currency arithmetic without floating-point errors
- Implementing KYC/AML data flows or transaction monitoring
- Building fraud detection pipelines (rule-based or ML-assisted)
- Designing idempotent financial APIs or trading system endpoints
- Writing tests that verify accounting invariants, reconciliation, or regulatory scenarios
- Ensuring PCI-DSS scope minimization in application architecture

**Trigger phrases**: "ledger", "double-entry", "payment processing", "PCI-DSS", "KYC", "AML", "fraud detection", "money handling", "currency conversion", "reconciliation", "trading platform", "FIX protocol", "idempotency key", "payment gateway", "journal entry", "chart of accounts"

## What This Skill Does

Provides fintech engineering patterns including:

- **Ledger Design**: Double-entry bookkeeping, chart of accounts, journal entries, immutable audit trails
- **Payment Processing**: State machines, gateway integration, webhook handling, retry logic, reconciliation
- **Money Handling**: Decimal precision, ISO 4217 currency codes, exchange rates, rounding rules
- **Regulatory Compliance**: KYC/AML pipelines, transaction monitoring, audit logging, data retention
- **Fraud Detection**: Velocity checks, anomaly scoring, rule engines, feature engineering
- **Financial APIs**: Idempotent endpoints, optimistic locking, rate limiting, market data feeds
- **Testing**: Property-based tests for accounting invariants, chaos testing for payments, load testing for trading

## Instructions

### Step 1: Double-Entry Ledger Design

Full walkthrough: [step-1-double-entry-ledger-design.md](references/step-1-double-entry-ledger-design.md) (load this step when you reach it).

### Step 2: Payment Processing

Full walkthrough: [step-2-payment-processing.md](references/step-2-payment-processing.md) (load this step when you reach it).

### Step 3: Money and Currency Handling

Full walkthrough: [step-3-money-and-currency-handling.md](references/step-3-money-and-currency-handling.md) (load this step when you reach it).

### Step 4: Regulatory Compliance in Code

Full walkthrough: [step-4-regulatory-compliance-in-code.md](references/step-4-regulatory-compliance-in-code.md) (load this step when you reach it).

### Step 5: Fraud Detection Patterns

Full walkthrough: [step-5-fraud-detection-patterns.md](references/step-5-fraud-detection-patterns.md) (load this step when you reach it).

### Step 6: Financial API Design

Full walkthrough: [step-6-financial-api-design.md](references/step-6-financial-api-design.md) (load this step when you reach it).

### Step 7: Testing Financial Systems

Full walkthrough: [step-7-testing-financial-systems.md](references/step-7-testing-financial-systems.md) (load this step when you reach it).

## Best Practices

- **Immutability is your audit trail**: Append-only data structures (event sourcing, journal entries) make compliance trivial and debugging possible
- **Idempotency everywhere**: Every write operation in a financial system must be safely retriable. Use idempotency keys on all API endpoints and database writes
- **Reconcile continuously**: Run reconciliation between your ledger and external systems (gateways, banks, partners) at least daily, ideally in real time
- **Fail closed, not open**: When fraud detection or compliance checks cannot run (service down, timeout), block the transaction rather than allowing it through
- **Separate concerns with the money**: Keep the ledger as a distinct service. Payment orchestration, fraud detection, and compliance monitoring are separate bounded contexts
- **Test with real numbers**: Use actual transaction amounts, currency codes, and edge cases (zero-decimal currencies like JPY, three-decimal currencies like BHD) in your test suites
- **Version your APIs**: Financial integrations are long-lived. Use versioned endpoints (`/v1/`, `/v2/`) and maintain backward compatibility for at least two major versions
- **Log everything, expose nothing**: Audit logs must capture all actions, but API responses and user-facing errors must never leak internal state, account numbers, or system details
- **Automate compliance checks**: Manual compliance processes do not scale. Encode rules as code, test them, and run them in CI alongside your application tests
- **Design for regulatory change**: Regulations change frequently. Externalize thresholds, country lists, and rule parameters into configuration rather than hardcoding them

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll use a float for the amount, the rounding is negligible" | Floating-point cannot represent 0.10 exactly, so a sum of cents drifts and the ledger fails to balance by a penny that compounds across millions of rows. Fixed-precision decimals are non-negotiable for money. |
| "The client only sends each payment once, idempotency keys are overkill" | Networks retry, users double-click, and webhooks redeliver; without an idempotency key the same charge posts twice and you refund an angry customer. Every write endpoint requires the key. |
| "If the fraud service times out, let the transaction through so we don't lose the sale" | Failing open on a compliance or fraud check is how laundered funds and chargebacks get in. The rule is fail closed: block the transaction when the check cannot run. |
| "I'll skip the daily reconciliation, the gateway and ledger always agree" | Silent divergence between your ledger and the gateway is invisible until an audit or a customer dispute surfaces it, by which point it is unfixable. Continuous reconciliation is what catches the drift the day it happens. |

## Verification

- [ ] All monetary amounts are stored as fixed-precision decimals, never floating-point
- [ ] The double-entry invariant is enforced at the database level (trigger or constraint)
- [ ] Idempotency keys are required on every write endpoint
- [ ] Webhook handlers verify signatures and process events idempotently
- [ ] Fraud and compliance checks fail closed (block) when the dependent service is unavailable
- [ ] Reconciliation runs at least daily between the internal ledger and the payment gateway
- [ ] The audit log is append-only with restricted permissions

## Related Skills

- [[architecture-design]] -- system decomposition and trade-off analysis for the bounded contexts
- [[api-design]] -- API contract design and versioning strategies for financial endpoints
- [[security-review]] -- security assessment for PCI-DSS scope and financial data paths
- [[database-design]] -- schema design for ledger and transaction data models
- [[event-driven-architecture]] -- event sourcing and CQRS for append-only audit trails

---

**Version**: 1.0.0
**Last Updated**: March 2026

### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets are not met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
