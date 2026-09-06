"""FastAPI application exposing the shop's HTTP surface."""
import os

from fastapi import Depends, FastAPI

from db import get_session, healthcheck
from services import charge_order, create_order

app = FastAPI(title="shop-api")

CORS_ORIGINS = os.environ["CORS_ORIGINS"]
SENTRY_DSN = os.getenv("SENTRY_DSN", "")


@app.get("/health")
def health():
    """Liveness probe backed by a database round-trip."""
    return {"ok": healthcheck()}


@app.get("/customers/{customer_id}/orders")
def list_orders(customer_id: int, session=Depends(get_session)):
    """List every order belonging to a customer."""
    from models import Order

    return session.query(Order).filter_by(customer_id=customer_id).all()


@app.post("/customers/{customer_id}/orders")
def place_order(customer_id: int, items: list):
    """Create a new pending order for the customer."""
    order = create_order(customer_id, items)
    return {"order_id": order.id, "status": order.status}


@app.post("/orders/{order_id}/pay")
def pay_order(order_id: int, user=Depends(get_session)):
    """Charge a pending order and mark it paid."""
    order = charge_order(order_id)
    return {"order_id": order.id, "status": order.status}
