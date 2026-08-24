### Step 4: Regulatory Compliance in Code

Financial systems operate under strict regulatory frameworks. Compliance is not optional, and violations carry criminal penalties.

**KYC/AML Data Flow Architecture**:

```
┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│  Customer     │     │  KYC Service  │     │  Identity    │
│  Onboarding   │────>│  (Orchestrator)│────>│  Verification│
│  UI           │     │               │     │  Provider    │
└──────────────┘     └───────┬───────┘     └──────────────┘
                             │
                    ┌────────▼────────┐
                    │  Watchlist       │
                    │  Screening       │     Sanctions lists:
                    │  (OFAC, EU, UN) │     OFAC SDN, EU Consolidated,
                    └────────┬────────┘     UN Security Council
                             │
                    ┌────────▼────────┐
                    │  Risk Scoring    │     PEP databases,
                    │  Engine          │     adverse media
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Case Management │     Manual review
                    │  (Compliance     │     queue for
                    │   Officers)      │     edge cases
                    └─────────────────┘
```

**Transaction Monitoring Rules** (Python rule engine):

```python
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from enum import Enum

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class TransactionAlert:
    rule_id: str
    severity: AlertSeverity
    transaction_id: str
    customer_id: str
    description: str
    triggered_at: datetime

class TransactionMonitor:
    """Rule-based transaction monitoring for AML compliance."""

    def __init__(self, transaction_store: "TransactionStore") -> None:
        self._store = transaction_store

    async def check_structuring(
        self, customer_id: str, amount: Decimal, window_hours: int = 24,
    ) -> TransactionAlert | None:
        """Detect structuring: multiple transactions just below reporting threshold.

        US BSA requires CTR filing for transactions over $10,000.
        Structuring is breaking up transactions to avoid this threshold.
        """
        threshold = Decimal("10000.00")
        structuring_floor = Decimal("8000.00")
        since = datetime.now(timezone.utc) - timedelta(hours=window_hours)

        recent = await self._store.get_transactions(customer_id, since=since)
        below_threshold = [t for t in recent if structuring_floor <= t.amount < threshold]

        if len(below_threshold) >= 3:
            total = sum(t.amount for t in below_threshold)
            return TransactionAlert(
                rule_id="AML-001-STRUCTURING",
                severity=AlertSeverity.HIGH,
                transaction_id=below_threshold[-1].id,
                customer_id=customer_id,
                description=(
                    f"{len(below_threshold)} transactions between "
                    f"${structuring_floor} and ${threshold} within {window_hours}h, "
                    f"totaling ${total}"
                ),
                triggered_at=datetime.now(timezone.utc),
            )
        return None

    async def check_velocity(
        self, customer_id: str, amount: Decimal, window_hours: int = 1,
    ) -> TransactionAlert | None:
        """Detect unusual transaction velocity (count per time window)."""
        since = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        recent = await self._store.get_transactions(customer_id, since=since)

        # Thresholds should be configurable per customer risk tier
        if len(recent) > 10:
            return TransactionAlert(
                rule_id="AML-002-VELOCITY",
                severity=AlertSeverity.MEDIUM,
                transaction_id=recent[-1].id,
                customer_id=customer_id,
                description=f"{len(recent)} transactions in {window_hours}h exceeds velocity limit",
                triggered_at=datetime.now(timezone.utc),
            )
        return None
```

**Audit Logging Schema**:

```sql
-- Immutable audit log for all financially significant actions
CREATE TABLE audit_log (
    id              BIGSERIAL PRIMARY KEY,
    event_type      VARCHAR(100) NOT NULL,          -- e.g., "payment.captured"
    actor_id        VARCHAR(255) NOT NULL,          -- user or system identifier
    actor_type      VARCHAR(50) NOT NULL,           -- "user", "system", "api_key"
    resource_type   VARCHAR(100) NOT NULL,          -- "payment", "account", "transfer"
    resource_id     VARCHAR(255) NOT NULL,
    action          VARCHAR(50) NOT NULL,           -- "create", "update", "approve"
    changes         JSONB,                          -- before/after snapshot
    ip_address      INET,
    user_agent      TEXT,
    request_id      VARCHAR(255),                   -- correlation ID
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Append-only: revoke all UPDATE and DELETE permissions
REVOKE UPDATE, DELETE ON audit_log FROM app_user;

-- Indexes for compliance queries
CREATE INDEX idx_audit_actor ON audit_log(actor_id, created_at);
CREATE INDEX idx_audit_resource ON audit_log(resource_type, resource_id, created_at);
CREATE INDEX idx_audit_event_type ON audit_log(event_type, created_at);

-- Data retention: partition by month for efficient archival
CREATE TABLE audit_log_partitioned (
    LIKE audit_log INCLUDING ALL
) PARTITION BY RANGE (created_at);
```

**Compliance Checklist for Financial Applications**:

- Log every state change to financially significant entities with before/after snapshots
- Retain audit logs for the regulatory minimum (typically 5-7 years depending on jurisdiction)
- Implement geographic restrictions at the API gateway level (OFAC-sanctioned countries)
- Screen all customers and counterparties against sanctions lists at onboarding and periodically thereafter
- File Currency Transaction Reports (CTRs) for transactions exceeding $10,000 (US) or equivalent thresholds
- File Suspicious Activity Reports (SARs) when monitoring rules trigger and compliance review confirms suspicion
- Encrypt PII at rest and in transit; implement field-level encryption for sensitive KYC documents
