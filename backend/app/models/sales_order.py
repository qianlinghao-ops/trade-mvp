from sqlalchemy import Column, String, Numeric, Integer, Text, DateTime, ForeignKey, Enum, Date
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime
import uuid
import enum

class SOStatus(str, enum.Enum):
    draft = "draft"
    received = "received"
    confirmed = "confirmed"
    preparing = "preparing"
    shipped = "shipped"
    completed = "completed"
    cancelled = "cancelled"

class SalesOrder(Base):
    __tablename__ = "sales_orders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    so_number = Column(String(50), unique=True, nullable=False)
    customer_id = Column(String, ForeignKey("companies.id"), nullable=False)
    status = Column(Enum(SOStatus), default=SOStatus.draft)
    order_date = Column(Date, default=datetime.utcnow)
    delivery_date = Column(Date, nullable=True)
    total_amount = Column(Numeric(15, 2), default=0)
    currency = Column(String(10), default="JPY")
    payment_terms = Column(String(100))
    shipping_terms = Column(String(100))
    destination = Column(String(200))
    notes = Column(Text)
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Company", back_populates="sales_orders")
    items = relationship("SalesOrderItem", back_populates="sales_order", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="sales_order")

class SalesOrderItem(Base):
    __tablename__ = "sales_order_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sales_order_id = Column(String, ForeignKey("sales_orders.id"), nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=True)
    product_name = Column(String(200), nullable=False)
    sku = Column(String(50))
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False, default=0)
    amount = Column(Numeric(15, 2), nullable=False, default=0)
    unit = Column(String(20), default="個")
    notes = Column(Text)

    sales_order = relationship("SalesOrder", back_populates="items")
    product = relationship("Product", back_populates="sales_order_items")