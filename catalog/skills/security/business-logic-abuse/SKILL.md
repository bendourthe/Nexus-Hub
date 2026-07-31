---
name: business-logic-abuse
description: "Identify business-logic vulnerabilities that bypass intended workflows -- race conditions, TOCTOU, double-spending, workflow-state bypass, idempotency violations, check-sequence abuse -- and the concrete attacker playbooks they enable: pricing/refund abuse, coupon and promo stacking, anti-fraud and rate-limit defeat, multi-accounting, and workflow-step bypass. Requires domain knowledge of the application's business rules because these flaws do not appear in generic scanners. Use when auditing financial flows, reservation systems, multi-step workflows, or any feature with stateful invariants, or when red-teaming pricing/refund/promo logic under authorization. SKIP, do NOT use for, generic injection classes such as XSS or SQL injection (use security-review), architectural or web-app attacks such as SSRF or request smuggling (use advanced-attack-patterns), or stateless endpoint bugs (use semantic-bug-detector)."
summary_l0: "Business-logic abuse: race conditions, TOCTOU, double-spending, workflow bypass, pricing/refund abuse, anti-fraud defeat"
overview_l1: "This skill identifies business-logic vulnerabilities that generic scanners cannot find because the flaws depend on the application's own rules. Use it when auditing high-value workflows (payments, ledgers, reservations, privilege grants), reviewing state-machine implementations, or extending `/run-penetration-test --depth=deep` with domain-aware checks. Key capabilities include race-condition and TOCTOU detection at atomicity boundaries, double-spending and replay-within-window analysis, workflow-state bypass via direct-endpoint calls, idempotency-key review, check-sequence abuse, and concrete attacker playbooks -- pricing/refund abuse, coupon stacking, anti-fraud and rate-limit defeat, and workflow-step bypass -- that give each finding a business impact. The expected output is a findings table with severity, invariant violated, code reference, reproduction sketch, and remediation. Trigger phrases: business logic, race condition, TOCTOU, double-spend, idempotency, workflow bypass, pricing abuse, refund abuse, promo stacking, multi-accounting, anti-fraud bypass, WSTG-BUSL."
---

# Business-Logic Abuse

Business-logic vulnerabilities break the application's own rules: balances go negative, workflows skip required steps, requests replay inside an allowed window, two parallel operations both succeed when only one should. Generic scanners miss these because they depend on domain knowledge - what "valid" means for this app. This skill guides a domain-aware audit that elicits the rules from the operator, traces each rule through the code, and flags the atomicity, idempotency, and sequencing gaps where abuse lives.

## When to Use This Skill

Use this skill when:

- Auditing financial workflows (payments, refunds, ledgers, credit grants, promotional codes)
- Reviewing reservation or inventory systems (seats, slots, stock, quotas)
- Assessing privilege grants and role transitions (invitations, upgrades, approvals)
- Evaluating multi-step workflows where each step has preconditions
- Running `/run-penetration-test --depth=deep` (this skill powers the Business Logic & Advanced Attacks hunter)
- Investigating a specific incident that looks like "the system did something it should not have allowed"
- Red-teaming pricing, refund, promo, or anti-fraud logic under authorization (the attacker playbooks in Step 8)

Do NOT use this skill for:
- Generic vulnerability classes (XSS, SQL injection) - use `security-review` or `/run-penetration-test` standard depth.
- Architectural or web-app attack classes (SSRF, SSTI, XXE, request smuggling, IDOR) - use `advanced-attack-patterns`, the companion skill.
- Stateless endpoint bugs - use `semantic-bug-detector` or unit-test coverage instead.
- Any engagement without documented authorization, scope, and synthetic/test data - obtain them first.

**Trigger phrases**: "business logic", "race condition", "TOCTOU", "time of check time of use", "double spend", "idempotency", "workflow bypass", "state machine bug", "check then act", "workflow state", "ledger integrity", "pricing abuse", "price tampering", "refund abuse", "coupon stacking", "promo abuse", "anti-fraud bypass", "rate limit bypass", "multi-accounting", "bonus farming", "WSTG-BUSL".

## What This Skill Does

Provides a domain-aware audit procedure for business-logic flaws including:

- **Rule Elicitation**: A structured interview that surfaces high-value workflows, critical invariants, and idempotency guarantees from the operator.
- **Attack Class Coverage**: Six canonical attack classes (race conditions, TOCTOU, double-spending, workflow bypass, idempotency violations, check-sequence abuse) with indicators, example code patterns, and remediation guidance.
- **Code-Trace Procedure**: For each elicited rule, a walkthrough that maps the rule onto atomicity boundaries, state-machine transitions, and persistence guarantees.
- **Attacker Playbooks**: Concrete scenarios (pricing/refund abuse, anti-fraud and rate-limit defeat, workflow-step bypass) that turn a missing-guard finding into a demonstrated business impact - what an attacker actually does with the gap.
- **Structured Output**: A findings table schema (severity, rule violated, code reference, reproduction sketch, remediation) consumable by `/run-penetration-test` reports and security reviews.

## Instructions

### Step 1: Scope and Caveat - Elicit the Rules

**You cannot audit what you do not know.** Business logic lives in the operator's head and in the product spec, not in the code. Before reading any code, ask the operator:

1. **High-value workflows**: "What are the 3-5 workflows where a bypass would cost real money, real privilege, or real trust?" Typical answers: payment capture, refund, reservation commit, role grant, promo-code redemption, withdrawal, transfer.
2. **Critical invariants**: "What statements should always be true regardless of load, concurrency, or retries?" Examples: "balance cannot go negative," "a seat is either available or held by exactly one user," "a refund cannot exceed the original charge," "a user has at most one active subscription."
3. **Idempotency guarantees**: "Which endpoints must produce the same visible result if called twice with the same inputs?" Typical: payment submission, order creation, webhook handlers.
4. **Trust boundaries**: "Which inputs come from the user vs an internal trusted source?" Prices and quantities submitted by a client are the classic vector for workflow bypass.
5. **State transitions**: "Walk me through the state machine of each high-value workflow - what are the states, and what transitions are allowed from each?"

If the operator cannot answer these, stop and request the product spec or domain owner. **This skill produces garbage on unspecified domains.** Do not guess the rules.

### Step 2: Race Conditions

**What it is**: Two requests arrive close enough in time that their combined effect breaks an invariant. Classic case: `SELECT balance; check balance >= amount; UPDATE balance - amount;` - two requests both pass the check, both succeed, balance goes negative.

**Indicators in code**:
- Read-modify-write patterns that are not wrapped in a transaction or atomic operation.
- `if (record.locked) { ... } else { record.lock(); ... }` without a database-level lock.
- Cache-then-database patterns where the cache is read first and writes do not invalidate atomically.
- Concurrent job processing that reads pending tasks without `FOR UPDATE SKIP LOCKED` or an equivalent.

**Code-trace procedure**:
1. For each invariant elicited in Step 1, locate every code path that reads or writes the state the invariant depends on.
2. For each path, identify the atomicity boundary: where does the transaction begin and end? Is the read inside the same transaction as the write? Is the write-side lock pessimistic (`FOR UPDATE`), optimistic (version column + retry), or absent?
3. Flag any boundary where two concurrent requests could both pass the check and both commit.

**Remediation**:
- Database-enforced atomicity: `SELECT ... FOR UPDATE`, unique constraints, conditional UPDATE (`WHERE balance >= amount`), optimistic concurrency with version columns.
- Application-level locks only when database locks are infeasible - and only with an external lock service (Redis Redlock, ZooKeeper) with correctly-handled lock expiry.
- Design out the race: single-writer job queues, event sourcing with per-aggregate ordering.

### Step 3: TOCTOU (Time-of-Check / Time-of-Use)

**What it is**: A resource or permission is checked at time T1 and used at time T2; between T1 and T2 the resource changes. Distinct from race conditions: TOCTOU often involves two different subjects (a file, a permission, an external resource) rather than two concurrent requests on the same row.

**Indicators in code**:
- `os.path.exists(p)` followed by `open(p)` - the file may be replaced with a symlink between the two calls.
- `if user.has_permission('admin'): ... do_admin_action()` where the permission check and the action are not in the same transaction or permission token.
- `check_not_banned(user); send_message(user);` - the ban happens between the two calls.
- External-resource availability checks (API health, disk space) followed by use.

**Remediation**:
- Fuse check and use into a single atomic operation (e.g., open-if-not-exists file modes; `INSERT ... ON CONFLICT`; permission-bearing capability tokens carried with the action).
- Replace check-then-use with use-and-handle: attempt the operation and handle failure, rather than pre-checking.

### Step 4: Double-Spending / Replay-Within-Window

**What it is**: The same financially-meaningful request succeeds twice because the server did not have an idempotency key or the key was not enforced. Includes coupon re-use, voucher re-redemption, gift-card double-charge, and transaction replay.

**Indicators in code**:
- Payment, refund, or ledger endpoints that do not accept or require an idempotency key.
- Idempotency keys that are accepted but not stored (only logged), or stored without a uniqueness constraint.
- Idempotency key TTLs shorter than the likely client retry window.
- Coupon / voucher codes that allow multiple redemptions because the "used" flag is set after the award is granted.

**Remediation**:
- Require idempotency keys on all state-changing financial endpoints (RFC-aligned: `Idempotency-Key` header).
- Store keys in a table with a UNIQUE constraint on `(key, endpoint, tenant)` and retain at least long enough to cover client retry windows (24h typical; longer for fintech).
- For single-use artifacts (vouchers, one-time codes), set the "used" flag atomically with the award - in the same transaction, gated by a UNIQUE constraint or a `WHERE used = false` predicate.

### Step 5: Workflow-State Bypass

**What it is**: The UI walks a user through steps A -> B -> C, but each step is a separate endpoint. A malicious client POSTs directly to C, skipping A and B. The server did not check that the prerequisite state was reached.

**Indicators in code**:
- Multi-step wizards where each step endpoint trusts the client to have completed prior steps.
- Direct endpoints like `/checkout/complete` or `/account/delete/confirm` that accept a request without verifying the state-machine position.
- State stored only in the client (hidden form fields, query params) without server-side corroboration.
- Conditional rendering in the UI treated as authorization ("the button is not shown" is not "the endpoint is guarded").

**Remediation**:
- Enforce the state machine server-side: every action endpoint consults the persisted state and rejects any transition not in the allowed-from-here set.
- Represent the state machine explicitly (enum or typed state) rather than scattered booleans (`is_verified`, `has_paid`, `is_confirmed`). A typed state makes missing transition guards visible.
- Treat the UI path as untrusted. The state machine is the single source of truth.

### Step 6: Idempotency Violations

**What it is**: The same request produces different observable results on different calls, when it should produce the same result. Distinct from double-spending: here the intent is idempotency (retry safety), and the violation is that retry is not safe.

**Indicators in code**:
- Endpoints that increment a counter or allocate an ID on every call without checking for an existing result.
- Webhook handlers without dedup on `(event_id, event_version)`.
- "Create-or-update" endpoints where the update branch fails silently and the create branch runs instead.
- Side effects (emails, external API calls) performed before the idempotency-key lookup.

**Remediation**:
- Idempotency keys as the canonical dedup mechanism; store the response payload so a retry returns the same body.
- Webhook handlers: dedup on `event_id` at the boundary, before any downstream effect.
- Order side effects after the durable state change: don't send an email until the transaction commits.

### Step 7: Check-Sequence Abuse

**What it is**: The server validates input X, then acts on input Y, where X and Y are related but the relationship is not enforced. Canonical example: upload endpoint validates the uploaded file's MIME type, then saves the file using the client-supplied filename - attacker uploads `image/png` but names the file `malicious.php`.

**Indicators in code**:
- Validation and action use different input fields or different representations of the same field.
- Validation performed on a copy, with the original re-used downstream.
- Normalization happens after validation (e.g., `validate(filename); save(Path(filename).resolve())` - the `resolve()` may produce a different path).
- Multi-step validation where step 2 re-reads the input from the request rather than using the validated value from step 1.

**Remediation**:
- Validate, normalize, and act on the *same* value. Pass the validated object forward; do not re-read from the request.
- For uploads: server generates the filename; the client-supplied name is never used for storage.
- For permissions: the authorization decision must bind to the subject-verb-object tuple that the downstream handler acts on.

### Step 8: Attacker Playbooks (concrete scenarios)

Steps 2-7 are the audit *methodology*; this step is the attacker's *intent*. These playbooks are the concrete scenarios a defensive review should cite when arguing that an invariant matters - they show what an attacker actually does with a missing guard, so the finding carries a business impact, not just a code smell. Run them only inside an authorized engagement against synthetic accounts and test data; the deliverable is the control that defeats the play, not the proceeds.

#### 8a. Pricing and refund abuse

The attacker pays less than intended, or gets back more than they paid, by manipulating values the server should never trust from the client.

- **Client-set price / quantity**: the cart or order request carries `price`, `amount`, or `quantity`, and the server bills what the client sent. Substitute a lower price, a negative quantity (which can credit the account), or a zero/`0.001` unit price.
- **Currency and rounding abuse**: order in a currency where the conversion or rounding favors the attacker (charge 100 of a low-value unit, refund 100 of a high-value one), or exploit float rounding so a per-line discount rounds the total to zero.
- **Coupon / promo stacking**: apply the same single-use code twice via a race (see Step 2), stack mutually-exclusive promos the UI hides, or combine a percentage and a fixed discount so the total goes negative and becomes store credit.
- **Refund > payment**: refund a partially-consumed order in full, refund after a chargeback, refund to a different payment instrument than the one charged, or refund line items at a price higher than they were bought (price changed between purchase and refund).

```text
# Tampered order body -- the server must recompute price/total server-side
{"sku": "PRO-PLAN", "quantity": -1, "unit_price": 0.01, "currency": "XYZ", "coupons": ["SAVE50","FLAT20"]}
```

**Invariants broken**: "the customer is charged the catalog price for a non-negative quantity"; "total refunded never exceeds total captured"; "a single-use code is redeemed at most once".

**Defend**: recompute every monetary value server-side from trusted catalog/ledger data - never bill or refund a client-supplied amount; clamp quantities to a positive range; enforce single-use codes with a UNIQUE constraint set atomically with the award (Step 4); cap cumulative refunds at the captured amount in the same transaction that records the refund.

#### 8b. Anti-fraud and rate-limit defeat

The attacker defeats the controls meant to make abuse uneconomical, usually by multiplying identities or exploiting a check that is not authoritative.

- **Multi-accounting / bonus farming**: harvest new-account or referral bonuses by creating many accounts (disposable emails, plus-addressing, rotating devices) and, in the worst case, self-referral loops where one principal is both referrer and referee.
- **Velocity-limit bypass**: spread requests across accounts/IPs/devices so no single key trips the per-key limit, or exploit eventual consistency so concurrent requests each read an under-limit counter before any write lands (a race, per Step 2).
- **Check-not-authoritative**: the fraud/risk check runs asynchronously or advisory-only, so the value moves before the check completes; or the check trusts a client-supplied signal (device id, "is_trusted" flag) the attacker controls.

**Invariants broken**: "a bonus is granted at most once per real entity"; "a principal cannot exceed N actions per window"; "value does not move until the risk check clears".

**Defend**: bind limits and bonuses to an entity the attacker cannot cheaply multiply (verified payment instrument, verified phone) rather than to an email/IP; enforce limits with an atomic server-side counter (Step 2), not a client signal; make the risk check authoritative and synchronous on the value-moving path, or hold the value until it clears; reject self-referral by checking referrer != referee at grant time.

#### 8c. Workflow-step bypass (offensive)

The attacker reaches a privileged end state without passing the gates that precede it - the offensive twin of Step 5.

- **Skip the payment / verification / approval gate**: POST directly to `/checkout/complete`, `/account/verify`, or `/withdrawal/approve` from a state where the prerequisite step was never completed.
- **Replay a "success" token**: capture the confirmation token or signed "paid"/"verified" artifact from a sandbox, a prior order, or another user, and present it on a new flow.
- **State-field tampering / force-browsing**: flip a client-held `status` field to `confirmed`, or force-browse to the post-success page whose handler trusts that arrival implies completion.

```text
# Direct call to the terminal step from a non-prerequisite state
POST /api/checkout/complete   {"order_id": 5012, "state": "paid"}   # server never verified a capture
```

**Invariants broken**: "an order is fulfilled only after a successful capture"; "an account is privileged only after verification"; "a transition is allowed only from its predecessor state".

**Defend**: enforce the state machine server-side (Step 5) - every terminal action re-reads the persisted state and rejects a transition not allowed from the current state; bind success tokens to the specific order/user/flow and a server-issued nonce (so a replayed token is rejected); never trust a client-supplied `status`; treat page arrival as navigation, never as authorization.

### Step 9: Output Format

Produce findings as a table so the result is consumable by `/run-penetration-test` reports, security reviews, and downstream skills:

| Severity | Rule Violated | Attack Class | Code Reference | Reproduction Sketch | Remediation |
|----------|---------------|--------------|----------------|---------------------|-------------|
| CRITICAL | "Balance cannot go negative" | Race condition | `src/payments/debit.py:87-104` | Two concurrent POSTs to `/debit` with the same `account_id` and `amount=balance` | Wrap debit in `SELECT ... FOR UPDATE` or use conditional UPDATE `WHERE balance >= amount` |
| HIGH | "A reservation is held by exactly one user" | TOCTOU | `src/booking/hold.py:52-68` | Two users POST `/holds` for the same `slot_id` within 50ms | `INSERT ... ON CONFLICT DO NOTHING` on `(slot_id)` unique constraint; reject second insert |

Severity guidance:
- CRITICAL: invariant violation causes direct financial loss, privilege escalation to admin, or breach of multi-tenant isolation.
- HIGH: invariant violation causes data corruption or gives an attacker useful but non-terminal leverage.
- MEDIUM: invariant violation is reachable only under narrow conditions, or produces a user-visible anomaly without leverage.
- LOW: defense-in-depth gap; no realistic exploit path but the code path does not enforce the intended rule.

## Best Practices

- **Stop if the rules are not known.** Guessing invariants produces false positives and wastes trust.
- **Prefer database-enforced atomicity over application-level locking.** Databases handle crash recovery, replication, and expiry correctly; homegrown locks rarely do.
- **Represent state machines explicitly.** Scattered booleans (`is_paid`, `is_shipped`, `is_refunded`) hide missing transitions. A single `status` enum with typed transition rules makes gaps visible at review time.
- **Treat every client-supplied value as potentially hostile, even values the UI constrains.** Client constraints are not authorization.
- **Order side effects after durable state changes.** Email first, commit second is a double-send waiting to happen.
- **When multiple attack classes apply to the same endpoint, fix the deepest one first.** A fix that removes the race condition often removes the TOCTOU for free; the reverse is rarely true.

## Common Patterns

### Pattern 1: Conditional UPDATE for single-writer semantics

```sql
-- Correct: debit succeeds only if funds are available; returns affected row count
UPDATE accounts
SET balance = balance - :amount
WHERE account_id = :id AND balance >= :amount
RETURNING balance;
-- If row count = 0, debit was rejected atomically.
```

### Pattern 2: Idempotency key with uniqueness constraint

```sql
-- Idempotency key table
CREATE TABLE idempotency_keys (
    key TEXT,
    endpoint TEXT,
    tenant_id UUID,
    response_body JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (key, endpoint, tenant_id)
);
-- On second request: SELECT returns the stored response_body; no-op the side effects.
```

### Pattern 3: Server-enforced state machine

```python
# Explicit typed state with transition guards
class OrderStatus(Enum):
    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

ALLOWED_TRANSITIONS = {
    OrderStatus.DRAFT: {OrderStatus.PENDING, OrderStatus.CANCELLED},
    OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}

def transition(order: Order, to: OrderStatus) -> None:
    if to not in ALLOWED_TRANSITIONS[order.status]:
        raise WorkflowBypassError(f"{order.status} -> {to} not allowed")
    order.status = to
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The scanner came back clean, so the logic is fine" | Generic scanners only know syntax-level classes (XSS, SQL-i); they have no model of "balance cannot go negative", so a read-check-write debit race ships clean and lets balances go negative under concurrency. |
| "The UI only lets the user reach checkout after payment, so the complete endpoint is safe" | The UI path is untrusted; a client that POSTs directly to `/checkout/complete` skips the payment step entirely unless the server re-checks the persisted state-machine position. |
| "Adding an idempotency key is over-engineering for a simple payment endpoint" | Without an enforced key plus a UNIQUE constraint, a single client retry on a flaky network double-charges the customer, the exact double-spend in Step 4. |
| "I can infer the business rules from reading the code" | Code shows what the system does, not what it should do; auditing invariants you guessed produces false positives and misses the real rule the operator holds in their head, which is why Step 1 elicits rules first. |
| "We validate the price on the client, so the order total is safe" | The client is the attacker's machine; a tampered order body with a negative quantity or a 0.01 unit price (Step 8a) bills exactly what the client sent unless the server recomputes the total from trusted catalog data, which is why client-side price validation is never the control. |
| "Per-user rate limits stop bonus farming" | A limit keyed to an email or IP is defeated by creating many accounts or rotating identifiers (Step 8b); the bonus must bind to an entity the attacker cannot cheaply multiply (a verified payment instrument or phone), or the farm runs at scale under the per-key ceiling. |

## Verification

- [ ] Any attacker-playbook exercise (Step 8) ran under documented authorization against synthetic accounts and test data; no real funds or real customer data were moved
- [ ] For each CRITICAL finding, write or request a reproduction test that fails before the fix and passes after
- [ ] Confirm database-level constraints (UNIQUE, CHECK, `FOR UPDATE`) are in place, not just application-level code
- [ ] For race-condition fixes: load-test the fixed code with N >= 10 concurrent requests; confirm the invariant holds
- [ ] For workflow-bypass fixes: attempt to POST directly to the downstream endpoint from a state where it should be rejected; confirm rejection
- [ ] For idempotency fixes: replay the same request twice; confirm identical observable result
- [ ] For pricing/refund findings: confirm the server recomputes every monetary value from trusted data and caps cumulative refunds at the captured amount
- [ ] For anti-fraud findings: confirm limits/bonuses bind to an entity the attacker cannot cheaply multiply, enforced by an atomic server-side counter

## Related Skills

- [[advanced-attack-patterns]] -- companion skill; its Step 5 injection/access-control vectors and Step 1 state-desync pair with these business-logic playbooks on multi-step flows
- [[security-patch-advisor]] -- patch generation for the remediation code
- [[security-review]] -- general application security review that owns the target denominator, altitude ledger, and proven-dirty sink sweep for these playbooks
- [[authentication-patterns]] -- auth-specific invariants (one active session per user, MFA enrollment sequencing)
- [[pentest-reporting]] -- writes up the business-impact findings these playbooks produce
- [[fintech-engineer]] -- domain knowledge for financial ledger invariants
- [[semantic-bug-detector]] -- logic bugs beyond security (overlaps with this skill on race conditions)

---

**Version**: 1.1.0
**Last Updated**: June 2026

### Iterative Refinement Strategy

This skill is optimized for an iterative approach:
1. **Execute**: Elicit rules, audit each attack class, produce the findings table.
2. **Review**: Critically analyze each finding (exploitability, severity accuracy, remediation depth).
3. **Refine**: Downgrade theoretical findings; upgrade any you previously missed from under-elicited rules.
4. **Loop**: Continue until every elicited invariant has either a clean bill of health or a finding with a reproduction sketch.
