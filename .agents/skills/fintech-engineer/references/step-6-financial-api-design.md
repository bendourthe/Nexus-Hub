### Step 6: Financial API Design

Financial APIs require stronger guarantees than typical web APIs: idempotency, optimistic locking, precise error semantics, and careful rate limiting.

**Idempotent API Pattern**:

```python
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from decimal import Decimal
import hashlib
import json

app = FastAPI()

class TransferRequest(BaseModel):
    from_account: str
    to_account: str
    amount: Decimal
    currency: str
    description: str

class TransferResponse(BaseModel):
    transfer_id: str
    status: str
    idempotency_key: str

@app.post("/v1/transfers", response_model=TransferResponse)
async def create_transfer(
    request: TransferRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    idempotency_store: "IdempotencyStore" = Depends(get_idempotency_store),
    transfer_service: "TransferService" = Depends(get_transfer_service),
) -> TransferResponse:
    """Create a transfer with idempotency guarantee.

    The Idempotency-Key header ensures that retrying the same request
    produces the same result without executing the transfer twice.
    """
    # Check for existing result with this key
    existing = await idempotency_store.get(idempotency_key)
    if existing:
        # Verify the request body matches the original
        request_hash = hashlib.sha256(request.model_dump_json().encode()).hexdigest()
        if existing["request_hash"] != request_hash:
            raise HTTPException(
                status_code=422,
                detail="Idempotency-Key reused with different request body",
            )
        return TransferResponse(**existing["response"])

    # Execute the transfer
    result = await transfer_service.execute(request)

    # Store the result keyed by idempotency key (TTL: 24 hours)
    await idempotency_store.put(
        idempotency_key,
        {
            "request_hash": hashlib.sha256(request.model_dump_json().encode()).hexdigest(),
            "response": result.model_dump(),
        },
        ttl_seconds=86400,
    )
    return result
```

**Optimistic Locking for Account Updates**:

```sql
-- Accounts table with version column for optimistic locking
ALTER TABLE accounts ADD COLUMN version INTEGER NOT NULL DEFAULT 0;

-- Update with version check (application must retry on conflict)
UPDATE accounts
SET balance = balance - $1,
    version = version + 1,
    updated_at = NOW()
WHERE id = $2 AND version = $3;
-- If affected_rows == 0, the account was modified concurrently: retry
```

**Rate Limiting for Trading APIs**:

```python
import time
from collections import defaultdict

class SlidingWindowRateLimiter:
    """Per-user rate limiter using a sliding window counter.

    Financial APIs require strict rate limiting to prevent market
    manipulation and ensure fair access during high-volatility periods.
    """

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self._max = max_requests
        self._window = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, user_id: str) -> bool:
        now = time.monotonic()
        cutoff = now - self._window

        # Remove expired entries
        self._requests[user_id] = [
            t for t in self._requests[user_id] if t > cutoff
        ]

        if len(self._requests[user_id]) >= self._max:
            return False

        self._requests[user_id].append(now)
        return True
```

**WebSocket Market Data Feed**:

```python
import asyncio
import json
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class MarketQuote:
    symbol: str
    bid: Decimal
    ask: Decimal
    timestamp: float
    sequence: int      # monotonically increasing for gap detection

class MarketDataFeed:
    """WebSocket market data publisher with sequence numbers for gap detection."""

    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue]] = {}
        self._sequences: dict[str, int] = {}

    async def publish(self, quote: MarketQuote) -> None:
        self._sequences[quote.symbol] = quote.sequence
        queues = self._subscribers.get(quote.symbol, set())
        message = json.dumps({
            "type": "quote",
            "symbol": quote.symbol,
            "bid": str(quote.bid),
            "ask": str(quote.ask),
            "timestamp": quote.timestamp,
            "sequence": quote.sequence,
        })
        for queue in queues:
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                pass  # slow consumer; drop message, client detects gap via sequence

    def subscribe(self, symbol: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._subscribers.setdefault(symbol, set()).add(queue)
        return queue
```

**FIX Protocol Basics**: The Financial Information eXchange (FIX) protocol is the standard for electronic trading communication. FIX messages are tag-value pairs delimited by SOH (0x01). Key message types include NewOrderSingle (D), ExecutionReport (8), OrderCancelRequest (F), and MarketDataRequest (V). Modern implementations use QuickFIX libraries rather than hand-parsing FIX messages. When integrating with FIX counterparties, implement session-level heartbeats, sequence number tracking, and message gap fill to ensure reliable delivery.
