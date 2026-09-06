"""Business-logic services for orders, payments, and stock."""
import os

from db import get_session
from models import Order, OrderItem, Product

STRIPE_KEY = os.environ["STRIPE_SECRET_KEY"]
TAX_RATE = float(os.getenv("TAX_RATE", "0.2"))


def create_order(customer_id, items):
    """Create a pending order for a customer from a list of (product, qty)."""
    session = next(get_session())
    order = Order(customer_id=customer_id, status="pending")
    session.add(order)
    for product_id, quantity in items:
        session.add(
            OrderItem(order=order, product_id=product_id, quantity=quantity)
        )
    session.commit()
    return order


def charge_order(order_id):
    """Charge the order total via the payment provider and mark it paid."""
    session = next(get_session())
    order = session.query(Order).get(order_id)
    total = _order_total(session, order)
    _capture_payment(total)
    order.status = "paid"
    session.commit()
    return order


def _order_total(session, order):
    total = 0
    for item in order.items:
        product = session.query(Product).get(item.product_id)
        total += float(product.price) * item.quantity
    return total * (1 + TAX_RATE)


def _capture_payment(amount):
    """Pretend to call Stripe to capture a payment for `amount`."""
    return {"provider": "stripe", "amount": amount, "key": STRIPE_KEY[:4]}
