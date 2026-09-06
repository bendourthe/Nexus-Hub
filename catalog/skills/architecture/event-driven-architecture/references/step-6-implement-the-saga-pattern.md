### Step 6: Implement the Saga Pattern

**Choreography-Based Saga (event-driven)**:

```
Order Service          Payment Service        Inventory Service       Shipping Service
     │                       │                       │                       │
     │  OrderCreated         │                       │                       │
     ├──────────────────────►│                       │                       │
     │                       │  PaymentProcessed     │                       │
     │                       ├──────────────────────►│                       │
     │                       │                       │  InventoryReserved    │
     │                       │                       ├──────────────────────►│
     │                       │                       │                       │
     │                       │   If PaymentFailed    │                       │
     │  OrderCancelled  ◄────┤                       │                       │
     │                       │                       │                       │
     │                       │   If InsufficientStock│                       │
     │                       │  PaymentRefunded ◄────┤                       │
     │  OrderCancelled  ◄────┤                       │                       │
```

**Orchestrator-Based Saga (Python)**:

```python
from enum import Enum
from dataclasses import dataclass
from typing import list, Optional

class SagaStepStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"
    FAILED = "failed"

@dataclass
class SagaStep:
    name: str
    action: str          # Command to execute
    compensation: str    # Command to undo the action
    status: SagaStepStatus = SagaStepStatus.PENDING

class OrderSagaOrchestrator:
    """Orchestrates order creation across multiple services."""

    def __init__(self, command_bus, event_store):
        self.command_bus = command_bus
        self.event_store = event_store

    def define_steps(self, order_data: dict) -> list[SagaStep]:
        return [
            SagaStep(
                name="reserve_inventory",
                action="ReserveInventory",
                compensation="ReleaseInventory",
            ),
            SagaStep(
                name="process_payment",
                action="ProcessPayment",
                compensation="RefundPayment",
            ),
            SagaStep(
                name="create_shipment",
                action="CreateShipment",
                compensation="CancelShipment",
            ),
        ]

    async def execute(self, saga_id: str, order_data: dict):
        steps = self.define_steps(order_data)
        completed_steps = []

        for step in steps:
            try:
                step.status = SagaStepStatus.COMPLETED
                await self.command_bus.send(step.action, {
                    "saga_id": saga_id,
                    "order": order_data,
                })
                completed_steps.append(step)
            except Exception as e:
                # Compensate in reverse order
                step.status = SagaStepStatus.FAILED
                await self._compensate(saga_id, completed_steps, order_data)
                raise SagaFailedError(
                    f"Saga {saga_id} failed at step '{step.name}': {e}"
                )

    async def _compensate(
        self,
        saga_id: str,
        completed_steps: list[SagaStep],
        order_data: dict,
    ):
        for step in reversed(completed_steps):
            try:
                step.status = SagaStepStatus.COMPENSATING
                await self.command_bus.send(step.compensation, {
                    "saga_id": saga_id,
                    "order": order_data,
                })
                step.status = SagaStepStatus.COMPENSATED
            except Exception as comp_error:
                # Compensation failure requires manual intervention
                step.status = SagaStepStatus.FAILED
                await self._alert_manual_intervention(saga_id, step, comp_error)

class SagaFailedError(Exception):
    pass
```
