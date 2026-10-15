### Step 3: Set Up Service-to-Service Integration Tests

**Python (using responses library for HTTP mocking):**
```python
import responses
import pytest
from myapp.services import OrderService, PaymentGateway


class TestOrderServiceIntegration:
    """Test OrderService integration with PaymentGateway."""

    @responses.activate
    def test_place_order_calls_payment_gateway(self):
        responses.add(
            responses.POST,
            "https://payments.example.com/charge",
            json={"transaction_id": "txn_123", "status": "success"},
            status=200,
        )

        service = OrderService(
            payment_gateway_url="https://payments.example.com"
        )
        result = service.place_order(
            customer_email="alice@example.com",
            amount=99.99,
        )

        assert result.status == "confirmed"
        assert result.transaction_id == "txn_123"
        assert len(responses.calls) == 1

    @responses.activate
    def test_place_order_handles_payment_failure(self):
        responses.add(
            responses.POST,
            "https://payments.example.com/charge",
            json={"error": "insufficient_funds"},
            status=402,
        )

        service = OrderService(
            payment_gateway_url="https://payments.example.com"
        )
        result = service.place_order(
            customer_email="bob@example.com",
            amount=999999.99,
        )

        assert result.status == "payment_failed"

    @responses.activate
    def test_place_order_handles_gateway_timeout(self):
        responses.add(
            responses.POST,
            "https://payments.example.com/charge",
            body=ConnectionError("Connection timed out"),
        )

        service = OrderService(
            payment_gateway_url="https://payments.example.com"
        )
        with pytest.raises(ServiceUnavailableError):
            service.place_order(
                customer_email="carol@example.com",
                amount=50.00,
            )
```

**JavaScript (nock for HTTP mocking):**
```javascript
const nock = require("nock");
const { OrderService } = require("../src/services/orderService");

describe("OrderService integration with PaymentGateway", () => {
  afterEach(() => {
    nock.cleanAll();
  });

  test("place order calls payment gateway and confirms", async () => {
    nock("https://payments.example.com")
      .post("/charge")
      .reply(200, { transaction_id: "txn_123", status: "success" });

    const service = new OrderService({
      paymentGatewayUrl: "https://payments.example.com",
    });
    const result = await service.placeOrder("alice@example.com", 99.99);

    expect(result.status).toBe("confirmed");
    expect(result.transactionId).toBe("txn_123");
  });

  test("place order handles payment failure gracefully", async () => {
    nock("https://payments.example.com")
      .post("/charge")
      .reply(402, { error: "insufficient_funds" });

    const service = new OrderService({
      paymentGatewayUrl: "https://payments.example.com",
    });
    const result = await service.placeOrder("bob@example.com", 999999.99);

    expect(result.status).toBe("payment_failed");
  });

  test("place order throws on gateway timeout", async () => {
    nock("https://payments.example.com")
      .post("/charge")
      .replyWithError("Connection timed out");

    const service = new OrderService({
      paymentGatewayUrl: "https://payments.example.com",
    });

    await expect(service.placeOrder("carol@example.com", 50.0)).rejects.toThrow(
      "Service unavailable"
    );
  });
});
```

**Java (WireMock):**
```java
import com.github.tomakehurst.wiremock.junit5.WireMockTest;
import com.github.tomakehurst.wiremock.client.WireMock;
import org.junit.jupiter.api.Test;
import static com.github.tomakehurst.wiremock.client.WireMock.*;
import static org.junit.jupiter.api.Assertions.*;

@WireMockTest(httpPort = 8089)
class OrderServiceIntegrationTest {

    @Test
    void placeOrderCallsPaymentGateway() {
        stubFor(post(urlEqualTo("/charge"))
                .willReturn(okJson("""
                    {"transaction_id": "txn_123", "status": "success"}
                    """)));

        var service = new OrderService("http://localhost:8089");
        var result = service.placeOrder("alice@example.com",
                java.math.BigDecimal.valueOf(99.99));

        assertEquals("confirmed", result.getStatus());
        assertEquals("txn_123", result.getTransactionId());
    }

    @Test
    void placeOrderHandlesPaymentFailure() {
        stubFor(post(urlEqualTo("/charge"))
                .willReturn(aResponse()
                        .withStatus(402)
                        .withBody("""
                            {"error": "insufficient_funds"}
                            """)));

        var service = new OrderService("http://localhost:8089");
        var result = service.placeOrder("bob@example.com",
                java.math.BigDecimal.valueOf(999999.99));

        assertEquals("payment_failed", result.getStatus());
    }

    @Test
    void placeOrderHandlesGatewayTimeout() {
        stubFor(post(urlEqualTo("/charge"))
                .willReturn(aResponse()
                        .withFixedDelay(30000)));

        var service = new OrderService("http://localhost:8089");
        service.setTimeoutMs(1000);

        assertThrows(ServiceUnavailableException.class,
                () -> service.placeOrder("carol@example.com",
                        java.math.BigDecimal.valueOf(50)));
    }
}
```
