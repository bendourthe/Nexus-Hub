### Step 3: Money and Currency Handling

Floating-point arithmetic is fundamentally incompatible with financial calculations. A single rounding error can cascade through millions of transactions.

**The Decimal Rule**: Always represent money as integer minor units (cents, pence) or fixed-precision decimals. Never use `float` or `double`.

**Money Value Object** (Python):

```python
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN, InvalidOperation

# ISO 4217 currency metadata
CURRENCY_EXPONENTS: dict[str, int] = {
    "USD": 2, "EUR": 2, "GBP": 2, "JPY": 0, "BHD": 3,
    "KWD": 3, "CHF": 2, "CAD": 2, "AUD": 2, "CNY": 2,
}

@dataclass(frozen=True)
class Money:
    """Immutable value object for monetary amounts.

    Stores amount as Decimal with currency-appropriate precision.
    Uses banker's rounding (ROUND_HALF_EVEN) per ISO and financial standards.
    """
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if self.currency not in CURRENCY_EXPONENTS:
            raise ValueError(f"Unknown currency: {self.currency}")
        if not isinstance(self.amount, Decimal):
            raise TypeError("Amount must be a Decimal, not float")

    @classmethod
    def from_minor_units(cls, minor_units: int, currency: str) -> Money:
        """Create Money from integer minor units (e.g., cents)."""
        exp = CURRENCY_EXPONENTS[currency]
        amount = Decimal(minor_units) / Decimal(10 ** exp)
        return cls(amount=amount, currency=currency)

    @property
    def minor_units(self) -> int:
        """Convert to integer minor units for storage or gateway calls."""
        exp = CURRENCY_EXPONENTS[self.currency]
        return int(self.amount * Decimal(10 ** exp))

    def _check_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot operate on different currencies: {self.currency} vs {other.currency}"
            )

    def __add__(self, other: Money) -> Money:
        self._check_currency(other)
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __sub__(self, other: Money) -> Money:
        self._check_currency(other)
        return Money(amount=self.amount - other.amount, currency=self.currency)

    def __mul__(self, factor: Decimal) -> Money:
        exp = CURRENCY_EXPONENTS[self.currency]
        result = (self.amount * factor).quantize(
            Decimal(10) ** -exp, rounding=ROUND_HALF_EVEN
        )
        return Money(amount=result, currency=self.currency)

    def allocate(self, ratios: list[int]) -> list[Money]:
        """Split money by ratios without losing or gaining a cent.

        Example: Money(Decimal("100.00"), "USD").allocate([1, 1, 1])
        returns three Money objects totaling exactly $100.00.
        """
        total_ratio = sum(ratios)
        exp = CURRENCY_EXPONENTS[self.currency]
        quantize_to = Decimal(10) ** -exp

        results = []
        remainder = self.amount
        for i, ratio in enumerate(ratios):
            if i == len(ratios) - 1:
                # Last share gets the remainder to avoid rounding loss
                results.append(Money(amount=remainder, currency=self.currency))
            else:
                share = (self.amount * Decimal(ratio) / Decimal(total_ratio)).quantize(
                    quantize_to, rounding=ROUND_HALF_EVEN
                )
                results.append(Money(amount=share, currency=self.currency))
                remainder -= share

        return results
```

**Exchange Rate Management**:

```python
from datetime import date
from decimal import Decimal

@dataclass
class ExchangeRate:
    base: str          # e.g., "USD"
    quote: str         # e.g., "EUR"
    rate: Decimal      # 1 base = rate quote
    effective_date: date
    source: str        # e.g., "ECB", "Bloomberg"

class ExchangeRateService:
    def __init__(self, rate_store: "RateStore") -> None:
        self._store = rate_store

    def convert(self, money: Money, target_currency: str, as_of: date | None = None) -> Money:
        """Convert money to target currency using the rate effective on the given date."""
        if money.currency == target_currency:
            return money
        rate = self._store.get_rate(money.currency, target_currency, as_of or date.today())
        if rate is None:
            raise ValueError(f"No rate found for {money.currency}/{target_currency}")
        converted = money.amount * rate.rate
        exp = CURRENCY_EXPONENTS[target_currency]
        rounded = converted.quantize(Decimal(10) ** -exp, rounding=ROUND_HALF_EVEN)
        return Money(amount=rounded, currency=target_currency)
```

**Critical Rules for Money**:

- Never use `float` or `double` for monetary amounts. Use `Decimal` (Python), `BigDecimal` (Java/Kotlin), or integer minor units
- Always specify the rounding mode explicitly. Banker's rounding (`ROUND_HALF_EVEN`) is the financial standard
- Never add or subtract amounts in different currencies without explicit conversion
- Store exchange rates with their effective date and source for audit purposes
- Use the `allocate` pattern (not division) when splitting money to avoid rounding leakage
- Store currency codes as ISO 4217 three-letter codes, not symbols or free-text
