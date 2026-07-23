"""ORM models for the shop service (SQLAlchemy declarative)."""
from sqlalchemy import Column, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from db import Base


class Customer(Base):
    """A registered customer who can place orders."""

    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    name = Column(String)
    orders = relationship("Order", back_populates="customer")


class Product(Base):
    """A sellable product with a price and stock level."""

    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    sku = Column(String, unique=True)
    title = Column(String)
    price = Column(Numeric)
    stock = Column(Integer)


class Order(Base):
    """A customer order composed of one or more line items."""

    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    status = Column(String)
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    """A single product line within an order."""

    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    order = relationship("Order", back_populates="items")
    product = relationship("Product")
