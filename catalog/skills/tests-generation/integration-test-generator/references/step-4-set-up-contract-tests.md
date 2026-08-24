### Step 4: Set Up Contract Tests

**Python (Pact consumer test):**
```python
import atexit
from pact import Consumer, Provider

pact = Consumer("OrderService").has_pact_with(
    Provider("PaymentService"),
    pact_dir="./pacts",
)
pact.start_service()
atexit.register(pact.stop_service)


class TestPaymentServiceContract:
    """Consumer-side contract tests for PaymentService."""

    def test_successful_charge(self):
        expected = {"transaction_id": "txn_123", "status": "success"}

        (pact
         .given("a valid credit card")
         .upon_receiving("a charge request")
         .with_request("post", "/charge", body={
             "amount": 99.99,
             "currency": "USD",
             "customer_email": "alice@example.com",
         })
         .will_respond_with(200, body=expected))

        with pact:
            client = PaymentClient(base_url=pact.uri)
            result = client.charge(
                amount=99.99,
                currency="USD",
                customer_email="alice@example.com",
            )
            assert result["transaction_id"] == "txn_123"
```
