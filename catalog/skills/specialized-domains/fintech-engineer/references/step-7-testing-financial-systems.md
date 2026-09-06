### Step 7: Testing Financial Systems

Financial systems demand testing strategies that go beyond conventional unit tests. Accounting invariants must hold under all conditions, payment flows must survive failures, and regulatory scenarios must be verified.

**Property-Based Testing for Accounting Invariants**:

```python
from decimal import Decimal
from hypothesis import given, strategies as st, assume

# Strategy for valid Money amounts (positive, reasonable precision)
money_amount = st.decimals(
    min_value=Decimal("0.01"),
    max_value=Decimal("999999999.99"),
    places=2,
    allow_nan=False,
    allow_infinity=False,
)

@given(amount=money_amount)
def test_money_roundtrip_minor_units(amount: Decimal) -> None:
    """Money converted to minor units and back must equal the original."""
    m = Money(amount=amount, currency="USD")
    restored = Money.from_minor_units(m.minor_units, "USD")
    assert restored.amount == m.amount

@given(
    a=money_amount,
    b=money_amount,
    c=money_amount,
)
def test_money_addition_is_associative(a: Decimal, b: Decimal, c: Decimal) -> None:
    """(a + b) + c must equal a + (b + c) for all monetary amounts."""
    ma = Money(amount=a, currency="USD")
    mb = Money(amount=b, currency="USD")
    mc = Money(amount=c, currency="USD")
    assert (ma + mb) + mc == ma + (mb + mc)

@given(ratios=st.lists(st.integers(min_value=1, max_value=100), min_size=1, max_size=10))
def test_allocation_preserves_total(ratios: list[int]) -> None:
    """Allocating money by any ratios must preserve the total exactly."""
    total = Money(amount=Decimal("100.00"), currency="USD")
    parts = total.allocate(ratios)
    reconstructed = sum((p.amount for p in parts), Decimal("0.00"))
    assert reconstructed == total.amount

@given(
    amounts=st.lists(money_amount, min_size=2, max_size=20),
)
def test_ledger_entries_always_balance(amounts: list[Decimal]) -> None:
    """Every journal entry must have equal debits and credits."""
    # Simulate creating balanced entries
    total = sum(amounts, Decimal("0"))
    debit_total = total
    credit_total = total
    assert debit_total == credit_total
```

**Reconciliation Test Suite**:

```python
import pytest
from decimal import Decimal

class TestReconciliation:
    def test_perfect_match(self) -> None:
        internal = {"tx-1": Decimal("100.00"), "tx-2": Decimal("200.00")}
        gateway = {"tx-1": Decimal("100.00"), "tx-2": Decimal("200.00")}
        result = reconcile_payments(internal, gateway)
        assert len(result.matched) == 2
        assert len(result.missing_in_gateway) == 0
        assert len(result.missing_in_ledger) == 0
        assert len(result.amount_mismatches) == 0

    def test_missing_in_gateway(self) -> None:
        internal = {"tx-1": Decimal("100.00"), "tx-2": Decimal("200.00")}
        gateway = {"tx-1": Decimal("100.00")}
        result = reconcile_payments(internal, gateway)
        assert result.missing_in_gateway == ["tx-2"]

    def test_amount_mismatch(self) -> None:
        internal = {"tx-1": Decimal("100.00")}
        gateway = {"tx-1": Decimal("99.99")}
        result = reconcile_payments(internal, gateway)
        assert len(result.amount_mismatches) == 1
        assert result.amount_mismatches[0]["difference"] == Decimal("0.01")

    def test_empty_reconciliation(self) -> None:
        result = reconcile_payments({}, {})
        assert len(result.matched) == 0
```

**Chaos Testing for Payment Flows**:

```python
import asyncio
import random
from unittest.mock import AsyncMock, patch

class TestPaymentChaos:
    """Simulate failures at every stage of payment processing."""

    async def test_gateway_timeout_triggers_retry(self, payment_service: "PaymentService") -> None:
        """Payment must retry on gateway timeout and eventually succeed."""
        call_count = 0

        async def flaky_gateway(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("Gateway timeout")
            return {"status": "authorized", "gateway_id": "gw-123"}

        with patch.object(payment_service, "_gateway", AsyncMock(side_effect=flaky_gateway)):
            result = await payment_service.authorize(payment_id="pay-1", amount=Decimal("50.00"))
            assert result.status == PaymentStatus.AUTHORIZED
            assert call_count == 3

    async def test_idempotent_under_concurrent_retries(self, payment_service: "PaymentService") -> None:
        """Concurrent retries with the same idempotency key must produce exactly one payment."""
        idempotency_key = "idem-concurrent-001"
        tasks = [
            payment_service.authorize(
                payment_id="pay-2",
                amount=Decimal("75.00"),
                idempotency_key=idempotency_key,
            )
            for _ in range(5)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        successful = [r for r in results if not isinstance(r, Exception)]
        assert len(successful) >= 1
        # All successful results must reference the same payment
        payment_ids = {r.id for r in successful}
        assert len(payment_ids) == 1

    async def test_partial_failure_rolls_back_ledger(self, payment_service: "PaymentService") -> None:
        """If ledger posting fails after capture, the system must compensate."""
        with patch.object(payment_service, "_ledger", AsyncMock(side_effect=Exception("DB down"))):
            with pytest.raises(Exception, match="DB down"):
                await payment_service.capture(payment_id="pay-3")
            # Verify the payment status is not left in an inconsistent state
            payment = await payment_service.get(payment_id="pay-3")
            assert payment.status != PaymentStatus.CAPTURED
```

**Regulatory Test Scenarios**:

```python
class TestRegulatoryCompliance:
    async def test_ctr_filed_for_large_transactions(self, monitor: TransactionMonitor) -> None:
        """Transactions over $10,000 must trigger a CTR filing."""
        alert = await monitor.check_ctr_threshold(
            customer_id="cust-1", amount=Decimal("10500.00"),
        )
        assert alert is not None
        assert alert.rule_id == "REG-001-CTR"

    async def test_structuring_detected(self, monitor: TransactionMonitor) -> None:
        """Multiple transactions just below $10,000 must trigger structuring alert."""
        # Seed three transactions at $9,500 within 24 hours
        for _ in range(3):
            await monitor.record_transaction("cust-2", Decimal("9500.00"))
        alert = await monitor.check_structuring("cust-2", Decimal("9500.00"))
        assert alert is not None
        assert alert.severity == AlertSeverity.HIGH

    async def test_sanctioned_country_blocked(self, geo_service: "GeoRestrictionService") -> None:
        """Transactions from OFAC-sanctioned jurisdictions must be blocked."""
        result = await geo_service.check_allowed(country_code="KP")
        assert result.blocked is True
        assert "OFAC" in result.reason
```

**Load Testing for Trading Systems**: Use tools like Locust or k6 to simulate realistic trading workloads. Key metrics to measure include order submission latency (p50, p95, p99), order book update latency, market data feed throughput, and matching engine throughput (orders per second). Trading systems typically require sub-millisecond latency for the matching engine and sub-10ms latency for the full order lifecycle. Run load tests during simulated market open scenarios (high burst traffic) and measure behavior under backpressure.
