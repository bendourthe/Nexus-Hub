### Step 5: Fraud Detection Patterns

Fraud detection in financial systems requires a layered approach combining real-time rules, velocity checks, and ML-based anomaly detection.

**Rule-Based Detection Engine**:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class FraudSignal:
    rule_name: str
    score: float          # 0.0 to 1.0
    reason: str

class FraudRule(ABC):
    @abstractmethod
    async def evaluate(self, transaction: "Transaction", context: "FraudContext") -> FraudSignal | None:
        ...

class HighAmountRule(FraudRule):
    """Flag transactions significantly above the customer's historical average."""

    async def evaluate(self, transaction: "Transaction", context: "FraudContext") -> FraudSignal | None:
        avg = await context.get_average_amount(transaction.customer_id, days=90)
        if avg and transaction.amount > avg * Decimal("5"):
            return FraudSignal(
                rule_name="high_amount",
                score=min(float(transaction.amount / avg) / 10, 1.0),
                reason=f"Amount ${transaction.amount} is {transaction.amount / avg:.1f}x the 90-day average",
            )
        return None

class GeoVelocityRule(FraudRule):
    """Flag transactions from geographically impossible locations."""

    async def evaluate(self, transaction: "Transaction", context: "FraudContext") -> FraudSignal | None:
        last_location = await context.get_last_transaction_location(transaction.customer_id)
        if last_location is None:
            return None
        distance_km = haversine(last_location, transaction.location)
        time_delta_hours = (transaction.timestamp - last_location.timestamp).total_seconds() / 3600
        if time_delta_hours > 0:
            speed_kmh = distance_km / time_delta_hours
            if speed_kmh > 1000:  # faster than commercial aircraft
                return FraudSignal(
                    rule_name="geo_velocity",
                    score=0.9,
                    reason=f"Impossible travel: {distance_km:.0f}km in {time_delta_hours:.1f}h ({speed_kmh:.0f} km/h)",
                )
        return None

class FraudEngine:
    """Evaluate all fraud rules and aggregate signals into a decision."""

    def __init__(self, rules: list[FraudRule], threshold: float = 0.7) -> None:
        self._rules = rules
        self._threshold = threshold

    async def evaluate(self, transaction: "Transaction", context: "FraudContext") -> tuple[bool, list[FraudSignal]]:
        signals = []
        for rule in self._rules:
            signal = await rule.evaluate(transaction, context)
            if signal:
                signals.append(signal)

        # Aggregate: use max score (or weighted average for more sophistication)
        max_score = max((s.score for s in signals), default=0.0)
        is_fraudulent = max_score >= self._threshold
        return is_fraudulent, signals
```

**Feature Engineering for ML Fraud Models**:

```python
from decimal import Decimal

async def compute_fraud_features(
    customer_id: str,
    transaction: "Transaction",
    store: "TransactionStore",
) -> dict[str, float]:
    """Compute features for an ML fraud detection model.

    Features are organized by time window and aggregation type.
    """
    features: dict[str, float] = {}

    for window_name, hours in [("1h", 1), ("24h", 24), ("7d", 168), ("30d", 720)]:
        recent = await store.get_transactions(customer_id, hours_back=hours)

        features[f"txn_count_{window_name}"] = len(recent)
        features[f"txn_total_{window_name}"] = float(sum(t.amount for t in recent))
        features[f"txn_avg_{window_name}"] = (
            float(sum(t.amount for t in recent) / len(recent)) if recent else 0.0
        )
        features[f"txn_max_{window_name}"] = float(max((t.amount for t in recent), default=0))
        features[f"unique_merchants_{window_name}"] = len({t.merchant_id for t in recent})
        features[f"unique_countries_{window_name}"] = len({t.country for t in recent})

    # Transaction-level features
    features["amount"] = float(transaction.amount)
    features["is_international"] = 1.0 if transaction.country != "US" else 0.0
    features["hour_of_day"] = transaction.timestamp.hour
    features["day_of_week"] = transaction.timestamp.weekday()

    return features
```

**False Positive Management**: Every fraud detection system produces false positives. Design your system with a review queue, customer friction budget (maximum number of challenges per time window), and feedback loops that retrain rules based on analyst decisions. Track precision, recall, and false positive rate as operational metrics.
