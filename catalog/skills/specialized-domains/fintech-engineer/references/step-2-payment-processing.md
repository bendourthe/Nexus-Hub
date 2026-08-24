### Step 2: Payment Processing

Payment flows require careful state management, idempotent operations, and reconciliation against external gateways.

**Payment State Machine**:

```
                    ┌──────────┐
                    │ created  │
                    └────┬─────┘
                         │ authorize()
                    ┌────▼─────┐
              ┌─────│ pending  │─────┐
              │     └────┬─────┘     │
    timeout() │          │ confirm() │ fail()
              │     ┌────▼─────┐     │
              │     │ authorized│    │
              │     └────┬─────┘     │
              │          │ capture() │
              │     ┌────▼─────┐     │
              │     │ captured │     │
              │     └────┬─────┘     │
              │          │           │
              │   refund()│          │
              │     ┌────▼─────┐     │
              │     │ refunded │     │
              │     └──────────┘     │
              │                      │
              │  ┌──────────┐        │
              └──► expired  │        │
                 └──────────┘        │
                 ┌──────────┐        │
                 │  failed  │◄───────┘
                 └──────────┘
```

**Payment State Machine Implementation** (Python):

```python
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

class PaymentStatus(Enum):
    CREATED = "created"
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    REFUNDED = "refunded"
    EXPIRED = "expired"
    FAILED = "failed"

VALID_TRANSITIONS: dict[PaymentStatus, set[PaymentStatus]] = {
    PaymentStatus.CREATED:    {PaymentStatus.PENDING, PaymentStatus.EXPIRED},
    PaymentStatus.PENDING:    {PaymentStatus.AUTHORIZED, PaymentStatus.FAILED, PaymentStatus.EXPIRED},
    PaymentStatus.AUTHORIZED: {PaymentStatus.CAPTURED, PaymentStatus.EXPIRED},
    PaymentStatus.CAPTURED:   {PaymentStatus.REFUNDED},
    PaymentStatus.REFUNDED:   set(),
    PaymentStatus.EXPIRED:    set(),
    PaymentStatus.FAILED:     set(),
}

@dataclass
class Payment:
    id: str
    amount: Decimal
    currency: str
    status: PaymentStatus = PaymentStatus.CREATED
    gateway_id: str | None = None
    idempotency_key: str | None = None
    events: list[dict] = field(default_factory=list)

    def transition_to(self, new_status: PaymentStatus, reason: str = "") -> None:
        if new_status not in VALID_TRANSITIONS[self.status]:
            raise ValueError(
                f"Invalid transition: {self.status.value} -> {new_status.value}"
            )
        old_status = self.status
        self.status = new_status
        self.events.append({
            "from": old_status.value,
            "to": new_status.value,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
```

**Stripe Webhook Handler with Idempotent Processing**:

```python
import hmac
import hashlib
import json
from typing import Any

def verify_stripe_signature(payload: bytes, sig_header: str, secret: str) -> bool:
    """Verify Stripe webhook signature to prevent spoofed events."""
    parts = dict(pair.split("=", 1) for pair in sig_header.split(","))
    timestamp = parts["t"]
    expected_sig = parts["v1"]
    signed_payload = f"{timestamp}.".encode() + payload
    computed = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, expected_sig)

async def handle_stripe_webhook(
    event: dict[str, Any],
    payment_repo: "PaymentRepository",
    ledger: "LedgerService",
    processed_events: "IdempotencyStore",
) -> None:
    """Process a Stripe webhook event idempotently."""
    event_id = event["id"]

    # Idempotency: skip already-processed events
    if await processed_events.exists(event_id):
        return

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "payment_intent.succeeded":
        payment = await payment_repo.find_by_gateway_id(data["id"])
        if payment and payment.status == PaymentStatus.AUTHORIZED:
            payment.transition_to(PaymentStatus.CAPTURED, reason="stripe_webhook")
            await payment_repo.save(payment)
            # Post ledger entries: debit cash, credit receivable
            await ledger.post_payment_capture(payment)

    elif event_type == "payment_intent.payment_failed":
        payment = await payment_repo.find_by_gateway_id(data["id"])
        if payment and payment.status in (PaymentStatus.PENDING, PaymentStatus.AUTHORIZED):
            payment.transition_to(PaymentStatus.FAILED, reason=data.get("last_payment_error", {}).get("message", "unknown"))
            await payment_repo.save(payment)

    # Mark event as processed after successful handling
    await processed_events.store(event_id)
```

**Reconciliation Pattern**:

```python
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class ReconciliationResult:
    matched: list[str]
    missing_in_gateway: list[str]    # in our ledger but not in gateway
    missing_in_ledger: list[str]     # in gateway but not in our ledger
    amount_mismatches: list[dict]

def reconcile_payments(
    internal_records: dict[str, Decimal],
    gateway_records: dict[str, Decimal],
) -> ReconciliationResult:
    """Compare internal ledger records against payment gateway records.

    Keys are payment/transaction IDs; values are amounts.
    """
    matched = []
    amount_mismatches = []

    all_ids = set(internal_records.keys()) | set(gateway_records.keys())
    missing_in_gateway = []
    missing_in_ledger = []

    for txn_id in all_ids:
        internal = internal_records.get(txn_id)
        gateway = gateway_records.get(txn_id)

        if internal is None:
            missing_in_ledger.append(txn_id)
        elif gateway is None:
            missing_in_gateway.append(txn_id)
        elif internal == gateway:
            matched.append(txn_id)
        else:
            amount_mismatches.append({
                "id": txn_id,
                "internal": internal,
                "gateway": gateway,
                "difference": internal - gateway,
            })

    return ReconciliationResult(
        matched=matched,
        missing_in_gateway=missing_in_gateway,
        missing_in_ledger=missing_in_ledger,
        amount_mismatches=amount_mismatches,
    )
```

**PCI-DSS Scope Minimization**: Never store raw card numbers in your systems. Use Stripe Elements, Adyen Drop-in, or similar client-side tokenization so that card data never touches your servers. This keeps your application out of PCI-DSS scope entirely (SAQ A or SAQ A-EP instead of SAQ D).
