from sqlalchemy import Column, String, Numeric, Integer, Text, DateTime, ForeignKey, Enum, Date
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime
import uuid, enum

class POStatus(str, enum.Enum):
    draft = "draft"
    ordered = "ordered"
    confirmed = "confirmed"
    in_transit = "in_transit"
    received = "received"
    completed = "completed"
    cancelled = "cancelled"

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    po_number = Column(String(50), unique=True, nullable=False)
    supplier_id = Column(String, ForeignKey("companies.id"), nullable=False)
    status = Column(Enum(POStatus), default=POStatus.draft)
    order_date = Column(Date, default=datetime.utcnow)
    expected_date = Column(Date, nullable=True)
    total_amount = Column(Numeric(15, 2), default=0)
    currency = Column(String(10), default="JPY")
    payment_terms = Column(String(100))
    shipping_terms = Column(String(100))
    notes = Column(Text)
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    supplier = relationship("Company", back_populates="purchase_orders")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="purchase_order")

class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    purchase_order_id = Column(String, ForeignKey("purchase_orders.id"), nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=True)
    product_name = Column(String(200), nullable=False)
    sku = Column(String(50))
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False, default=0)
    amount = Column(Numeric(15, 2), nullable=False, default=0)
    unit = Column(String(20), default="個")
    notes = Column(Text)
    purchase_order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product", back_populates="purchase_order_items")
